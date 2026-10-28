#!/usr/bin/env python3
"""Stage 4 — render every stability figure FROM SAVED RESULTS ONLY.

No recomputation: reads extensions/stability/results/*.json and the pinned
baseline inputs; every figure is reproducible from stored outputs.

Figures:
  1  ph_resampling_dists.png          — distance distributions per shape/dim/metric
  2  ph_resampling_persistence.png    — top-3 H1 persistences across resamples
  3  ph_resampling_cross_shape.png    — cross-shape H1 bottleneck comparison
  4  mapper_resampling_structure.png  — structure stats across resamples (3x4)
  5  mapper_resampling_graphs_{shape}.png — reference + 6 resamples (native layout)
  6  mapper_resampling_layouts.png    — native vs component-separated (max-deviation rep)
  7  weather_loyo.png                 — LOYO dominant H1 + r_1 per config

Every caption embeds the required interpretation guards (reference overlap,
variability-band-not-CI, metric-not-test, S exploratory, cycles caveat,
parameter-vs-input distinction, sensitivity-not-claim).

Usage: python extensions/stability/scripts/render_stability_figures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

EXT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXT_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.figures import component_separated_layout  # noqa: E402 (baseline reuse)

RESULTS = EXT_ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)  # independent-rebuild fix: fresh trees lack the dir
FIGS = EXT_ROOT / "figures"
FIGS.mkdir(parents=True, exist_ok=True)  # independent-rebuild fix
CONFIG_LABEL = {
    "tau30_d8": "τ=30,d=8 (210d)", "tau45_d9": "τ=45,d=9 (360d)",
    "tau52_d8": "τ=52,d=8 (364d)", "tau60_d8": "τ=60,d=8 (420d, ref)",
    "tau73_d6": "τ=73,d=6 (365d)", "tau90_d8": "τ=90,d=8 (630d)",
}
CAPTIONS: dict[str, str] = {}


def _save(fig, name, caption):
    path = FIGS / name
    fig.savefig(path, dpi=150)
    plt.close(fig)
    CAPTIONS[name] = caption
    print(f"  {name}")
    return path


def _graph_from_saved(nodes: dict, links: dict) -> nx.Graph:
    G = nx.Graph()
    for name, members in nodes.items():
        G.add_node(name, members=members)
    for a, others in links.items():
        for b in others:
            G.add_edge(a, b)
    return G


def _draw_graph(ax, nodes: dict, links: dict, title: str, separated=False,
                seed: int = 42):
    G = _graph_from_saved(nodes, links)
    if separated:
        pos = component_separated_layout(G, seed=seed)
    else:
        pos = nx.spring_layout(G, seed=seed)
    sizes = [40 + 560 * (len(m) / max(1, max(len(v) for v in nodes.values())))
             for m in nodes.values()]
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.35, width=1.1)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=sizes, node_color="#7fb3d5",
                           edgecolors="black", linewidths=0.4)
    ax.margins(x=0.14, y=0.14)  # keep nodes at extreme layout positions visible
    ax.set_title(title, fontsize=8)
    ax.axis("off")


def fig_ph_dists(ph: dict):
    shapes = list(ph["shapes"].keys())
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.2), constrained_layout=True)
    for ci, shape in enumerate(shapes):
        reps = ph["shapes"][shape]["replicates"]
        for ri, metric in enumerate(("bottleneck", "wasserstein")):
            ax = axes[ri, ci]
            for k, dim in enumerate(("H0", "H1")):
                v = [r["distances"][dim][metric]["value"] for r in reps]
                x = np.full(len(v), k) + np.random.default_rng(7 + k).uniform(
                    -0.13, 0.13, len(v))
                ax.scatter(x, v, s=14, alpha=0.65,
                           color="#1f77b4" if dim == "H0" else "#d62728",
                           label=dim if ci == 0 and ri == 0 else None,
                           zorder=2)
                ax.hlines(np.median(v), k - 0.22, k + 0.22, color="black", lw=1.6,
                          zorder=3)
            ax.set_xticks([0, 1])
            ax.set_xticklabels(["H0", "H1"])
            if ci == 0:
                ax.set_ylabel(metric)
            if ri == 0:
                ax.set_title(shape.replace("_", " "), fontsize=10)
            if ci == 2 and ri == 0:
                ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0),
                          fontsize=8, framealpha=0.9)
    fig.suptitle("Resample-to-reference diagram distances — 30 x 80% subsamples "
                 "per shape (black bar = median)", fontsize=11)
    _save(fig, "ph_resampling_dists.png",
          "Distance distributions between each 80%-subsample persistence "
          "diagram and the FULL-DATA reference diagram (30 deterministic "
          "subsamples per shape; H0 and H1 kept separate; bottleneck and "
          "Wasserstein, pinned persim 0.4.1; essential class dropped by persim). "
          "DESCRIPTIVE resampling stability only: the full-data reference "
          "OVERLAPS every subsample, so these are not independent validation; "
          "the spread is a variability band, NOT a confidence set; a diagram "
          "distance is a metric value, not a hypothesis test. Note the H0 "
          "Wasserstein scale is structurally inflated: every subsample has "
          "exactly 399 finite H0 classes vs 499 in the reference, and each "
          "unmatched short class adds transport cost (the bottleneck, a max, "
          "is not affected this way).")


def fig_ph_persistence(ph: dict):
    shapes = list(ph["shapes"].keys())
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.8), constrained_layout=True)
    for ax, shape in zip(axes, shapes):
        blk = ph["shapes"][shape]
        reps = blk["replicates"]
        ref = blk["reference_diagnostics"]["H1_top3_persistence"]
        reps_sorted = sorted(reps, key=lambda r: r["rep"])
        x = [r["rep"] for r in reps_sorted]
        for j, c in zip(range(3), ("#1f77b4", "#ff7f0e", "#7f7f7f")):
            y = [r["diagnostics"]["H1_top3_persistence"][j]
                 for r in reps_sorted]
            ax.plot(x, y, "o", ms=3.5, color=c, alpha=0.8,
                    label=f"p{j+1} (resample)" if True else None)
            ax.hlines(ref[j], -1, 30, color=c, ls="--", lw=1.0, alpha=0.9)
        ax.set_xlabel("resample index")
        ax.set_ylabel("H1 persistence")
        ax.set_title(shape.replace("_", " "), fontsize=10)
        ax.set_xlim(-1, 30)
    axes[0].legend(loc="upper left", bbox_to_anchor=(1.45, 1.0), fontsize=8,
                   framealpha=0.9)
    fig.suptitle("Top-3 H1 persistences across resamples "
                 "(dashed = full-data reference)", fontsize=11)
    _save(fig, "ph_resampling_persistence.png",
          "Prominent H1 persistence values across the 30 resamples per shape "
          "(solid = resample values, dashed = full-data reference). STABLE "
          "features: the annulus dominant loop persistence (1.44-1.58 around "
          "the reference 1.496) and the figure-eight co-dominant pair "
          "(p1 0.458-0.511, reference 0.481) vary far less than their own "
          "scale. VARYING features: the blob's top persistences (no "
          "constructed loop; top H1 persistence swings 0.092-0.181 around "
          "0.140) and all noise-scale classes — these have no coherent "
          "structure to stabilize. Descriptive stability only; not a "
          "confidence set and not a hypothesis test.")


def fig_ph_cross_shape(ph: dict):
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.9), constrained_layout=True)
    shapes = list(ph["shapes"].keys())
    for ax, mode in zip(axes, ("absolute", "relative")):
        data, labels = [], []
        for shape in shapes:
            blk = ph["shapes"][shape]
            reps = blk["replicates"]
            bn = [r["distances"]["H1"]["bottleneck"]["value"] for r in reps]
            if mode == "absolute":
                data.append(bn)
            else:
                dom = blk["reference_diagnostics"]["H1_top3_persistence"][0]
                data.append([v / dom for v in bn])
            labels.append(shape.replace("_", " "))
        bp = ax.boxplot(data, tick_labels=labels, showfliers=True,
                        patch_artist=True, widths=0.5)
        for patch in bp["boxes"]:
            patch.set_facecolor("#aec7e8")
            patch.set_alpha(0.8)
        ax.set_title("absolute" if mode == "absolute" else
                     "relative: distance / dominant persistence", fontsize=10)
        ax.grid(axis="y", alpha=0.3)
    fig.suptitle("Cross-shape comparison — H1 bottleneck distance to the "
                 "full-data reference\n(right panel: descriptive scale "
                 "normalization by each shape's reference dominant H1 "
                 "persistence)", fontsize=11)
    _save(fig, "ph_resampling_cross_shape.png",
          "Cross-shape comparison of H1 bottleneck distances to the full-data "
          "reference (30 resamples per shape; boxes = quartiles, whiskers = "
          "range). LEFT: absolute distances. RIGHT: distances divided by each "
          "shape's reference dominant H1 persistence — a descriptive scale "
          "normalization, not a statistic. The two loop-constructed shapes sit "
          "at 2-4% of their dominant persistence; the no-loop blob sits at "
          "~34% of its (noise-scale) top persistence: diagrams of a "
          "constructed feature are proportionally far more stable under "
          "subsampling than diagrams with no constructed feature. Descriptive "
          "only — the reference overlaps each subsample, and no hypothesis "
          "test is performed.")


def fig_mapper_structure(mp: dict):
    stats = [("n_nodes", "nodes"), ("n_edges", "edges"),
             ("n_components", "connected components"),
             ("cyclomatic_number", "cyclomatic number E-V+C")]
    shapes = list(mp["shapes"].keys())
    fig, axes = plt.subplots(3, 4, figsize=(12.5, 8.2), constrained_layout=True)
    for ri, shape in enumerate(shapes):
        blk = mp["shapes"][shape]
        reps = blk["replicates"]
        ref = blk["reference"]["structure"]
        for ci, (key, label) in enumerate(stats):
            ax = axes[ri, ci]
            v = [r["structure"][key] for r in reps]
            x = np.arange(len(v)) + np.random.default_rng(11).uniform(
                -0.18, 0.18, len(v))
            ax.scatter(x, v, s=13, alpha=0.65, color="#1f77b4", zorder=2)
            ax.hlines(ref[key], -1, 30, color="#d62728", lw=1.5,
                      linestyles="--", zorder=3)
            ax.set_title(f"{shape.replace('_', ' ')} — {label}", fontsize=9)
            ax.set_xlim(-1, 30)
            ax.set_xticks([0, 10, 20, 29])
            if ri == 2:
                ax.set_xlabel("resample index")
    fig.suptitle("Mapper structure statistics across 30 input subsamples at "
                 "FIXED parameters (10, 0.35) — dashed red = full-data "
                 "reference", fontsize=11)
    _save(fig, "mapper_resampling_structure.png",
          "Mapper input-sampling stability: structure statistics of the 30 "
          "resample graphs at the FIXED reference parameters (n_cubes=10, "
          "overlap=0.35, PCA-1 lens, KMeans k=2 seed 42) — this is NOT the "
          "baseline E2 parameter sweep (same data, different parameters); "
          "here the data varies and the parameters do not. Node count is 20 "
          "in every resample of every shape (2 x n_cubes — the same "
          "uninformative pattern as baseline E2, now shown on the input axis). "
          "Edges, components and the cyclomatic number (E - V + C: number of "
          "independent graph cycles; graph cycles are NOT automatically "
          "topological loops) do vary: the annulus reference graph's cycles "
          "(cyc=2) disappear (cyc=0) in 13/30 resamples, the figure-eight "
          "2-component reading holds in 24/30, and the no-loop blob is the "
          "most variable (cyc 1-6, components 1-3). The custom "
          "membership-Jaccard S is NOT shown here because it is an "
          "exploratory overlap indicator, not a structural stability measure.")


def fig_mapper_graphs(mp: dict, n_show: int = 6):
    for shape, blk in mp["shapes"].items():
        ref = blk["reference"]
        reps = sorted(blk["replicates"], key=lambda r: r["rep"])[:n_show]
        fig, axes = plt.subplots(2, 4, figsize=(13.5, 6.6),
                                 constrained_layout=True)
        rs = ref["structure"]
        _draw_graph(axes[0, 0], ref["memberships_global"], ref["links"],
                    f"REFERENCE full data\n{rs['n_nodes']}n {rs['n_edges']}e "
                    f"{rs['n_components']}c cyc={rs['cyclomatic_number']}")
        for k, r in enumerate(reps):
            s = r["structure"]
            ax = axes.flat[k + 1]
            _draw_graph(ax, r["memberships_global"], r["links"],
                        f"rep {r['rep']} (seed {r['seed']})\n"
                        f"{s['n_nodes']}n {s['n_edges']}e "
                        f"{s['n_components']}c cyc={s['cyclomatic_number']}")
        for k in range(len(reps) + 1, 8):
            axes.flat[k].axis("off")
        fig.suptitle(f"{shape.replace('_', ' ')} — Mapper graphs at FIXED "
                     f"parameters (10, 0.35): full-data reference + first "
                     f"{n_show} of 30 input subsamples (spring layout seed 42)",
                     fontsize=11)
        _save(fig, f"mapper_resampling_graphs_{shape}.png",
              f"Small multiples for {shape}: the full-data reference Mapper "
              "graph and the first 6 of the 30 input subsamples, all at the "
              "FIXED reference parameters (10, 0.35, PCA-1 lens, KMeans k=2 "
              "seed 42). Node size = membership count (global point "
              "identities). The graph layout is a RENDERING choice (spring "
              "layout, seed 42) — structural comparisons must use the "
              "statistics and memberships, not pixel positions. This is "
              "input-sampling variation, distinct from baseline E2 parameter "
              "sensitivity. Mapper graph cycles are not automatically "
              "topological loops (baseline caveat); compare with "
              "ph_resampling_persistence.png, where the underlying H1 "
              "features remain stable.")


def fig_mapper_layouts(mp: dict):
    fig, axes = plt.subplots(3, 2, figsize=(9.0, 12.0),
                             constrained_layout=True)
    for ri, (shape, blk) in enumerate(mp["shapes"].items()):
        ref = blk["reference"]["structure"]
        # resample whose component count deviates most from the reference
        reps = max(blk["replicates"],
                   key=lambda r: abs(r["structure"]["n_components"]
                                     - ref["n_components"]))
        s = reps["structure"]
        _draw_graph(axes[ri, 0], reps["memberships_global"], reps["links"],
                    f"{shape.replace('_', ' ')} rep {reps['rep']} — native "
                    f"layout\n{s['n_nodes']}n {s['n_edges']}e "
                    f"{s['n_components']}c cyc={s['cyclomatic_number']}")
        _draw_graph(axes[ri, 1], reps["memberships_global"], reps["links"],
                    f"same graph — component-separated layout",
                    separated=True)
    fig.suptitle("Rendering choice, not structure: the same resample graphs "
                 "under native vs component-separated layouts", fontsize=11)
    _save(fig, "mapper_resampling_layouts.png",
          "For each shape, the resample whose connected-component count "
          "deviates most from the reference, rendered twice: native spring "
          "layout and component-separated layout (baseline renderer, seed "
          "42). The GRAPH is identical in both panels — only the rendering "
          "changes (the same distinction the Mapper explorer makes with its "
          "layout toggle). Layout is a reading aid: a visually connected "
          "drawing is not by itself a correct interpretation, and graph "
          "cycles are not automatically topological loops.")


def fig_weather_loyo(loyo: dict):
    cfgs = ["tau30_d8", "tau45_d9", "tau52_d8", "tau60_d8", "tau73_d6",
            "tau90_d8"]
    years = sorted(loyo["folds"].keys())
    xlabels = ["full data"] + [f"-{y}" for y in years]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3), constrained_layout=True)
    colors = plt.cm.viridis(np.linspace(0, 0.92, len(cfgs)))
    for ax, key, ylab in ((axes[0], "dominant_H1_persistence",
                           "dominant H1 persistence (retained-series z-units)"),
                          (axes[1], "gap_ratio_r1", "gap ratio $r_1$")):
        for ci, cfg in enumerate(cfgs):
            y = [loyo["full_data_reference"][cfg][key]]
            for yr in years:
                y.append(loyo["folds"][yr]["configs"][cfg][key])
            ax.plot(xlabels, y, "o-", ms=4, lw=1.2, color=colors[ci],
                    label=CONFIG_LABEL[cfg])
        if key == "gap_ratio_r1":
            ax.axhline(3, color="gray", ls="--", lw=0.9)
            ax.text(0.02, 3.08, "$r_1$ = 3 convention", fontsize=7,
                    color="gray", transform=ax.get_yaxis_transform())
            ax.set_ylim(0, 9)
        ax.set_ylabel(ylab)
        ax.set_xlabel("fold (omitted calendar year)")
        ax.tick_params(axis="x", labelsize=8)
    axes[1].legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8,
                   framealpha=0.9)
    fig.suptitle("Leave-one-calendar-year-out sensitivity — seasonal-cycle PH "
                 "per embedding configuration", fontsize=11)
    _save(fig, "weather_loyo.png",
          "Leave-one-calendar-year-out sensitivity of the seasonal-cycle "
          "persistent-homology result (Central Park daily TEMP, 2019-2024). "
          "Each line is one of the six documented embedding configurations; "
          "'full data' is the saved full-series result; each fold omits one "
          "calendar year, re-z-scores the retained days, and builds sliding "
          "windows that NEVER cross the gap created by the omitted year "
          "(mid-series folds therefore lose 210-630 windows, recorded in "
          "weather_loyo.json). FINDING: every fold x configuration retains a "
          "dominant H1 class with r_1 >= 4.38 (convention line at 3) — the "
          "result does not depend disproportionately on any single observed "
          "year. This is a SENSITIVITY ANALYSIS on six years of single-station "
          "data: not a population-level climate claim, not a formal "
          "confidence interval, not a hypothesis test; a dominant H1 class "
          "is consistent with recurrent quasi-periodic structure of the "
          "embedded series, not proof of a simple closed physical climate "
          "trajectory. r_1 is invariant to the per-fold re-z-scoring; "
          "dominant persistence is shown in retained-series z-units.")


def main() -> int:
    FIGS.mkdir(exist_ok=True)
    ph = json.loads((RESULTS / "ph_resampling.json").read_text())
    mp = json.loads((RESULTS / "mapper_resampling.json").read_text())
    loyo = json.loads((RESULTS / "weather_loyo.json").read_text())

    fig_ph_dists(ph)
    fig_ph_persistence(ph)
    fig_ph_cross_shape(ph)
    fig_mapper_structure(mp)
    fig_mapper_graphs(mp)
    fig_mapper_layouts(mp)
    fig_weather_loyo(loyo)

    (FIGS / "captions.json").write_text(json.dumps(CAPTIONS, indent=1))
    print(f"Rendered {len(CAPTIONS)} figures + captions.json into {FIGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
