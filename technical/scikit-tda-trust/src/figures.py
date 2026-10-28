"""Report figures, rendered ONLY from saved results (no recomputation).

Numeric results are produced by scripts/run_*.py into results/; this module
re-renders every E2 figure (and the E1 readability comparison) from those
stored artifacts, so figures never depend on notebooks or on rerunning
experiments (blueprint Sections 7 and 9).

Renderers used (documented per figure; an E1 capability-audit datum):
  * native  — km.draw_matplotlib(layout='kk'), i.e. networkx
              kamada_kawai_layout on the FULL graph. Deterministic, but it
              places disconnected components in one coordinate frame with no
              inter-component repulsion, so components can overlap.
  * custom  — component-separated spring layout (networkx): each connected
              component gets its own seeded spring_layout, and components are
              translated to non-overlapping horizontal bands; node area is
              proportional to cluster membership. This changes ONLY the
              drawing, never the graph structure (nodes/links are untouched).

Usage:
    python src/figures.py --e2 results/e2/e2_sensitivity.json
    python src/figures.py --all
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from pipeline import MAPPER_CYCLES_CAVEAT  # noqa: E402
from similarity import SIMILARITY_CAVEAT  # noqa: E402

NATIVE_RENDERER = "native km.draw_matplotlib(layout='kk')"
CUSTOM_RENDERER = ("custom component-separated spring layout "
                   "(networkx.spring_layout seed=42, per component)")


def _load(path: Path) -> dict:
    if not path.exists():
        print(f"ERROR [figures]: results file not found: {path}\n"
              "Run the corresponding experiment script first "
              "(see README 'Run').", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def _graph_from_json(graph_json: dict) -> "nx.Graph":
    import kmapper as km
    return km.to_networkx({"nodes": graph_json["nodes"],
                           "links": graph_json["links"]})


# ---------------------------------------------------------------- renderers

def _draw_mapper_on_ax(graph_json: dict, ax, title: str) -> str:
    """Draw a Mapper graph (from saved nodes/links) onto an axes.

    NATIVE renderer first; falls back to a seeded networkx spring layout.
    Returns the method used (recorded honestly).
    """
    import kmapper as km
    graph = {"nodes": graph_json["nodes"], "links": graph_json["links"]}
    try:
        km.draw_matplotlib(graph, ax=ax, layout="kk")
        method = NATIVE_RENDERER
    except Exception as exc:  # noqa: BLE001 - fallback is a recorded finding
        G = km.to_networkx(graph)
        sizes = [max(12.0, len(v) / 3.0) for v in graph["nodes"].values()]
        pos = nx.spring_layout(G, seed=42)
        nx.draw_networkx(G, pos, node_size=sizes, with_labels=False,
                         node_color="tab:orange", ax=ax, width=0.6)
        ax.set_axis_off()
        method = f"networkx fallback (draw_matplotlib failed: {type(exc).__name__})"
    ax.set_title(title, fontsize=10)
    return method


def component_separated_layout(G: "nx.Graph", seed: int = 42,
                               band_margin: float = 0.35):
    """Custom analytical layout: components in disjoint horizontal bands.

    For each connected component: spring_layout on the component subgraph
    (seeded, deterministic), then translate the component so the bands
    [i, i + 1 - band_margin] on the y axis hold one component each, centered
    on its own centroid and rescaled to a common height. Node positions
    change; the GRAPH STRUCTURE (nodes, edges) is untouched.

    DETERMINISM (defect found by the clean-copy test, fixed 2026-10-22):
    networkx's subgraph view iterates its node FILTER SET when the
    component is small (2*len(comp) < len(G)); a Python set of string node
    names has process-dependent order (hash randomization), which made the
    per-component spring layout non-deterministic ACROSS PROCESSES (three
    figures differed pixel-wise in the clean-copy run). Fix: rebuild each
    component subgraph with an explicitly SORTED node order and sort
    components by (-size, sorted node names). Verified by
    tests/test_outputs.py::test_component_layout_process_deterministic.
    """
    pos = {}
    comps = sorted(nx.connected_components(G),
                   key=lambda c: (-len(c), sorted(c)))
    for i, comp in enumerate(comps):
        sub = nx.Graph()
        sub.add_nodes_from(sorted(comp, key=str))
        sub.add_edges_from(G.edges(comp))
        p = nx.spring_layout(sub, seed=seed)
        pts = np.array([p[n] for n in sub.nodes()])
        pts -= pts.mean(axis=0)                       # center on centroid
        span = pts.max(axis=0) - pts.min(axis=0)
        scale = np.where(span > 1e-12, (1.0 - band_margin) / 2.0 / span, 1.0)
        pts = pts * scale                              # fit into band height
        pts[:, 1] += i + 0.5                           # band i on the y axis
        pos.update({n: pts[k] for k, n in enumerate(sub.nodes())})
    return pos


def _draw_mapper_component_separated(graph_json: dict, ax, title: str) -> str:
    """Draw a Mapper graph with the custom component-separated layout.

    Node area is proportional to cluster membership (the native renderer
    uses a uniform heuristic size — a recorded capability difference).
    """
    G = _graph_from_json(graph_json)
    pos = component_separated_layout(G, seed=42)
    sizes = [max(30.0, 8.0 * len(v)) for v in graph_json["nodes"].values()]
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]
    comp_of = {}
    for i, comp in enumerate(sorted(nx.connected_components(G),
                                    key=lambda c: (-len(c), sorted(c)))):
        for n in comp:
            comp_of[n] = i % len(colors)
    nx.draw_networkx_edges(G, pos, ax=ax, width=0.6, alpha=0.6)
    nx.draw_networkx_nodes(G, pos, node_size=sizes, ax=ax,
                           node_color=[comp_of[n] for n in G.nodes()],
                           edgecolors="white", linewidths=0.5)
    ax.set_axis_off()
    ax.set_title(title, fontsize=10)
    return CUSTOM_RENDERER


def _mapper_graph_caption_stats(cell: dict) -> str:
    return (f"nodes={cell['n_nodes']} edges={cell['n_edges']} "
            f"components={cell['n_components']} "
            f"cycles(cyclomatic)={cell['cyclomatic_number']} "
            f"longest basis cycle={cell['max_basis_cycle_length']}\n"
            f"S vs reference={cell['similarity_to_reference']:.2f}")


def _contrast_for_shape(shape_res: dict, pre: dict | None):
    """Resolve the contrast cell for one shape.

    Order: (1) per-shape pre-specified entry from the config echo; (2) the
    documented auto-selection rule — among non-reference cells maximize
    lexicographically (|delta n_components|, |delta cyclomatic_number|,
    1 - similarity), i.e. the cell whose STRUCTURE differs most from the
    reference. Excludes the reference cell itself.
    """
    cells = shape_res["cells"]
    ref = (shape_res["reference_cell"]["n_cubes"],
           shape_res["reference_cell"]["perc_overlap"])
    contrast = None
    if isinstance(pre, dict):
        entry = pre.get(shape_res["shape"])
        if entry and entry.get("n_cubes") is not None:
            contrast = (entry["n_cubes"], entry["perc_overlap"])
            if contrast not in {(c["n_cubes"], c["perc_overlap"]) for c in cells}:
                print(f"WARNING [figures]: pre-specified contrast cell "
                      f"{contrast} for {shape_res['shape']} not in grid; "
                      "auto-selecting.", file=sys.stderr)
                contrast = None
    if contrast is None or contrast == ref:
        ref_cell = next(c for c in cells if (c["n_cubes"],
                                             c["perc_overlap"]) == ref)
        ranked = sorted(
            (c for c in cells if (c["n_cubes"], c["perc_overlap"]) != ref),
            key=lambda c: (-abs(c["n_components"] - ref_cell["n_components"]),
                           -abs(c["cyclomatic_number"]
                                - ref_cell["cyclomatic_number"]),
                           c["similarity_to_reference"]))
        best = ranked[0]
        contrast = (best["n_cubes"], best["perc_overlap"])
    return ref, contrast


# ---------------------------------------------------------------- E2 figures

def e2_summary_figure(results_path: Path, out_dir: Path) -> list[Path]:
    """Grid overview: components, cyclomatic number, similarity per cell."""
    R = _load(results_path)
    written = []
    for shape_res in R["shapes"]:
        cells = shape_res["cells"]
        ncs = sorted({c["n_cubes"] for c in cells})
        pos = sorted({c["perc_overlap"] for c in cells})
        by_cell = {(c["n_cubes"], c["perc_overlap"]): c for c in cells}
        ref = (shape_res["reference_cell"]["n_cubes"],
               shape_res["reference_cell"]["perc_overlap"])

        panels = (("n_components", "%d", "Connected components", "Blues"),
                  ("cyclomatic_number", "%d",
                   "Cyclomatic number  E − V + C", "Purples"),
                  ("similarity_to_reference", "%.2f",
                   "Membership overlap S vs reference", "Greens"))
        fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.0),
                                 constrained_layout=True)
        for ax, (key, fmt, label, cmap) in zip(axes, panels):
            M = np.full((len(ncs), len(pos)), np.nan)
            for i, nc in enumerate(ncs):
                for j, po in enumerate(pos):
                    M[i, j] = by_cell[(nc, po)][key]
            im = ax.imshow(M, cmap=cmap, aspect="auto", vmin=0)
            for i in range(len(ncs)):
                for j in range(len(pos)):
                    txt = fmt % M[i, j]
                    ax.text(j, i, txt, ha="center", va="center", fontsize=9,
                            color="white" if M[i, j] > np.nanmax(M) * 0.6
                            else "black")
                    if (ncs[i], pos[j]) == ref:
                        ax.text(j, i - 0.32, "REF", ha="center", va="center",
                                fontsize=7, color="crimson", fontweight="bold")
            ax.set_xticks(range(len(pos)), [f"{p:.2f}" for p in pos])
            ax.set_yticks(range(len(ncs)), [str(n) for n in ncs])
            ax.set_xlabel("perc_overlap")
            ax.set_ylabel("n_cubes")
            ax.set_title(label, fontsize=10)
            fig.colorbar(im, ax=ax, shrink=0.85)
        fig.suptitle(
            f"E2 parameter sensitivity — {shape_res['shape']} "
            f"(n={shape_res['n_points']}, seed={shape_res['shape_params'].get('seed')}, "
            f"lens={shape_res['lens']})", fontsize=11)
        out = out_dir / f"e2_sensitivity_summary_{shape_res['shape']}.png"
        fig.savefig(out, dpi=150)
        plt.close(fig)
        written.append(out)

        # caption file: caveats must travel with the figure
        cap = out_dir / f"e2_sensitivity_summary_{shape_res['shape']}.caption.txt"
        cap.write_text(
            f"E2 sensitivity summary for {shape_res['shape']} (24-cell grid; "
            "12 shown per shape). LEFT: connected-component count per cover "
            "parameter cell (networkx). MIDDLE: cyclomatic number E − V + C, "
            "the count of independent graph cycles (see caveat). RIGHT: "
            "membership-overlap S vs the pre-specified reference cell (REF). "
            f"{SIMILARITY_CAVEAT} {MAPPER_CYCLES_CAVEAT} "
            "Interpretation rests primarily on the component counts, cycle "
            "statistics, and representative panels, not on S alone.\n")
        written.append(cap)
    return written


def e2_representative_panels(results_path: Path, out_dir: Path) -> list[Path]:
    """Reference cell vs contrast cell, rendered with the NATIVE renderer."""
    R = _load(results_path)
    written = []
    pre = R["meta"].get("contrast_cell_pre_specified")
    for shape_res in R["shapes"]:
        ref, contrast = _contrast_for_shape(shape_res, pre)
        picks = {"Reference cell": ref, "Contrast cell": contrast}
        fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.6), constrained_layout=True)
        methods = []
        for ax, (label, key) in zip(axes, picks.items()):
            c = next(x for x in shape_res["cells"]
                     if (x["n_cubes"], x["perc_overlap"]) == key)
            m = _draw_mapper_on_ax(
                c["graph"], ax,
                f"{label}\nn_cubes={key[0]}, perc_overlap={key[1]:.2f}")
            methods.append(m)
            ax.set_xlabel(_mapper_graph_caption_stats(c), fontsize=8)
        fig.suptitle(
            f"E2 representative Mapper graphs — {shape_res['shape']}: "
            "reference vs structurally most-different cell", fontsize=11)
        out = out_dir / f"e2_representative_panels_{shape_res['shape']}.png"
        fig.savefig(out, dpi=150)
        plt.close(fig)
        written.append(out)

        cap = out_dir / f"e2_representative_panels_{shape_res['shape']}.caption.txt"
        stable_c = next(x for x in shape_res["cells"]
                        if (x["n_cubes"], x["perc_overlap"]) == ref)
        unst_c = next(x for x in shape_res["cells"]
                      if (x["n_cubes"], x["perc_overlap"]) == contrast)
        cap.write_text(
            f"Representative reference-vs-contrast cells for "
            f"{shape_res['shape']}. Reference "
            f"({ref[0]}, {ref[1]:.2f}): {stable_c['n_components']} "
            f"component(s), cyclomatic {stable_c['cyclomatic_number']}, "
            f"longest basis cycle {stable_c['max_basis_cycle_length']}. "
            f"Contrast ({contrast[0]}, {contrast[1]:.2f}): "
            f"{unst_c['n_components']} component(s), cyclomatic "
            f"{unst_c['cyclomatic_number']}, longest basis cycle "
            f"{unst_c['max_basis_cycle_length']} — the structural reading a "
            "user draws differs between these cells (interpretation "
            "instability). Which cell is the 'stable' reading is a "
            "data-construction question, recorded in "
            "results/e2/e2_interpretation_notes.md. "
            f"Renderers: {methods[0]} / {methods[1]}. {MAPPER_CYCLES_CAVEAT}\n")
        written.append(cap)
    return written


def e2_readability_comparison(results_path: Path, out_dir: Path) -> list[Path]:
    """Native vs component-separated rendering of the REFERENCE-cell graph.

    E1 readability finding: the native kk layout places disconnected
    components in one frame with no inter-component repulsion, so they can
    overlap. Side-by-side at the reference cell (the pre-specified analysis
    setting). Quantitative layout-overlap statistics live in
    results/e1/layout_overlap.json (scripts/measure via run_e1_audit.py).
    """
    R = _load(results_path)
    written = []
    for shape_res in R["shapes"]:
        ref = (shape_res["reference_cell"]["n_cubes"],
               shape_res["reference_cell"]["perc_overlap"])
        c = next(x for x in shape_res["cells"]
                 if (x["n_cubes"], x["perc_overlap"]) == ref)
        fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.6), constrained_layout=True)
        m1 = _draw_mapper_on_ax(
            c["graph"], axes[0],
            f"Native renderer\nn_cubes={ref[0]}, perc_overlap={ref[1]:.2f}")
        m2 = _draw_mapper_component_separated(
            c["graph"], axes[1],
            "Custom component-separated layout\n(same graph structure)")
        axes[0].set_xlabel(_mapper_graph_caption_stats(c), fontsize=8)
        axes[1].set_xlabel(_mapper_graph_caption_stats(c), fontsize=8)
        fig.suptitle(
            f"E1/E2 readability — {shape_res['shape']} reference cell: "
            "native vs component-separated rendering", fontsize=11)
        out = out_dir / f"e2_readability_{shape_res['shape']}.png"
        fig.savefig(out, dpi=150)
        plt.close(fig)
        written.append(out)

        cap = out_dir / f"e2_readability_{shape_res['shape']}.caption.txt"
        cap.write_text(
            f"Readability comparison for the {shape_res['shape']} reference "
            f"cell ({ref[0]}, {ref[1]:.2f}). LEFT: {m1} — the native layout "
            "computes one kamada-kawai layout for the WHOLE graph and uses "
            "uniform node sizes, so disconnected components are not "
            "guaranteed to be visually separated. RIGHT: custom "
            "component-separated layout (networkx spring_layout seed=42 per "
            "component, translated to disjoint horizontal bands; node area "
            "proportional to membership). The GRAPH STRUCTURE is identical "
            "in both panels — only the drawing differs; this is a rendering "
            "capability finding, not a change to Mapper's mathematical "
            "output. See results/e1/layout_overlap.json for measured "
            f"component-overlap statistics. {c['n_components']} component(s), "
            f"cyclomatic {c['cyclomatic_number']}.\n")
        written.append(cap)
    return written


def e2_blob_sanity_figure(sanity_path: Path, out_dir: Path) -> list[Path]:
    """No-loop control: Mapper graphs (2 diagnostic cells) + H1 diagram."""
    if not sanity_path.exists():
        return []
    S = _load(sanity_path)
    cells = S["cells"]
    fig, axes = plt.subplots(1, len(cells) + 1, figsize=(4.2 * (len(cells) + 1), 4.4),
                             constrained_layout=True)
    methods = []
    for ax, c in zip(axes[:-1], cells):
        m = _draw_mapper_on_ax(
            c["graph"], ax,
            f"Mapper, no-loop blob\nn_cubes={c['n_cubes']}, "
            f"perc_overlap={c['perc_overlap']:.2f}")
        methods.append(m)
        ax.set_xlabel(
            f"components={c['n_components']} cycles(cyclomatic)="
            f"{c['cyclomatic_number']} longest basis cycle="
            f"{c['max_basis_cycle_length']}", fontsize=8)

    # H1 diagram from the SAVED calibration data (no recomputation)
    from persim import plot_diagrams
    dgm = np.array(S["h1_calibration"]["H1_diagram"], dtype=float)
    plot_diagrams([dgm], ax=axes[-1], title="H1 persistence diagram, no-loop blob")
    r1 = S["h1_calibration"].get("gap_ratio_r1_calibration")
    axes[-1].set_xlabel(
        f"top3 persistence="
        f"{S['h1_calibration'].get('H1_top3_persistence')}, r_1={r1} "
        "(calibration)", fontsize=8)

    fig.suptitle("E2 sanity control — no-loop blob: graph cycles vs H1 evidence",
                 fontsize=11)
    out = out_dir / f"e2_sanity_{S['shape']}.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)

    cap = out_dir / f"e2_sanity_{S['shape']}.caption.txt"
    cap.write_text(
        f"Sanity control on the no-loop blob at two diagnostic settings "
        "(NOT a full sweep). LEFT/MIDDLE: Mapper graphs — note the short "
        "noise-scale graph cycles (see per-panel longest-basis-cycle "
        "lengths). RIGHT: the H1 persistence diagram from the SAME data "
        f"(top-3 persistences {S['h1_calibration'].get('H1_top3_persistence')}, "
        f"r_1 calibration {r1}) shows NO dominant class, as the construction "
        "implies. CRITICAL DISTINCTION: a cycle in the constructed Mapper "
        "graph does not automatically imply a genuine topological loop in "
        "the underlying data — cycle LENGTH and scale context distinguish "
        "loop-like structure (compare the annulus reference cell's long "
        "16-node basis cycle) from these short noise cycles. "
        f"Renderers: {' / '.join(methods)}; H1 diagram via persim "
        f"plot_diagrams from saved results. {MAPPER_CYCLES_CAVEAT}\n")
    return [out, cap]


# ---------------------------------------------------------------- E1 figures

def e1_readability_comparison_figure(results_dir: Path, out_dir: Path,
                                     overlap_path: Path | None = None) -> list[Path]:
    """Native vs component-separated rendering for every E1 shape.

    Loads the SAVED per-shape memberships (results/e1/*_mapper_memberships.json,
    reference settings) — no recomputation. Overlap statistics from
    results/e1/layout_overlap.json are cited in the captions when present.
    """
    written = []
    overlap = _load(overlap_path) if (overlap_path and overlap_path.exists()) else None
    shapes = ["annulus", "figure_eight", "blob", "three_blobs"]
    for name in shapes:
        mpath = results_dir / f"{name}_mapper_memberships.json"
        if not mpath.exists():
            continue
        graph_json = json.loads(mpath.read_text())
        G = _graph_from_json(graph_json)
        n_comp = nx.number_connected_components(G)

        fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.6), constrained_layout=True)
        m1 = _draw_mapper_on_ax(graph_json, axes[0], "Native renderer")
        m2 = _draw_mapper_component_separated(
            graph_json, axes[1], "Custom component-separated layout")
        for ax in axes:
            ax.set_xlabel(f"components={n_comp}", fontsize=8)
        fig.suptitle(
            f"E1 readability — {name} Mapper graph (reference settings): "
            "native vs component-separated rendering", fontsize=11)
        out = out_dir / f"{name}_readability_native_vs_separated.png"
        fig.savefig(out, dpi=150)
        plt.close(fig)

        ov_txt = ""
        if overlap:
            entry = overlap.get(name, {})
            m = entry.get("native_kk")
            if m:
                ov_txt = (f"Measured overlap (native kk layout, "
                          f"results/e1/layout_overlap.json): max component "
                          f"bounding-box IoU={m.get('max_component_bbox_iou')}, "
                          f"fraction of inter-component node pairs closer "
                          f"than the median intra-component nearest-neighbour "
                          f"distance={m.get('inter_close_fraction')}. "
                          f"Custom layout max IoU="
                          f"{entry.get('component_separated', {}).get('max_component_bbox_iou')}.")

        cap = out_dir / f"{name}_readability_native_vs_separated.caption.txt"
        cap.write_text(
            f"Native vs custom rendering of the SAME Mapper graph for "
            f"{name} (reference settings, memberships loaded from "
            f"results/e1/{name}_mapper_memberships.json). LEFT: {m1} — one "
            "kamada-kawai layout for the whole graph, uniform node sizes, "
            "no inter-component repulsion. RIGHT: custom component-separated "
            "layout — per-component seeded spring layouts in disjoint "
            "horizontal bands, node area proportional to membership. The "
            "graph structure (nodes, edges, components) is IDENTICAL; only "
            f"the drawing differs. {ov_txt} This is a rendering-capability "
            "finding about the workflow, not a change to Mapper's "
            "mathematical output.\n")
        written += [out, cap]
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--e2", default=str(REPO / "results" / "e2" / "e2_sensitivity.json"),
                    help="path to e2 results JSON")
    ap.add_argument("--all", action="store_true", help="render every figure "
                    "whose results file exists")
    args = ap.parse_args()

    written: list[Path] = []
    e2_path = Path(args.e2)
    if args.all or e2_path.exists():
        out_dir = REPO / "figures" / "e2"
        out_dir.mkdir(parents=True, exist_ok=True)
        written += e2_summary_figure(e2_path, out_dir)
        written += e2_representative_panels(e2_path, out_dir)
        written += e2_readability_comparison(e2_path, out_dir)
        written += e2_blob_sanity_figure(
            REPO / "results" / "e2" / "e2_blob_sanity.json", out_dir)
        written += e1_readability_comparison_figure(
            REPO / "results" / "e1", REPO / "figures" / "e1",
            REPO / "results" / "e1" / "layout_overlap.json")

    if not written:
        print("No results files found — run experiments first (README 'Run').",
              file=sys.stderr)
        return 1
    for p in written:
        print(f"Wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
