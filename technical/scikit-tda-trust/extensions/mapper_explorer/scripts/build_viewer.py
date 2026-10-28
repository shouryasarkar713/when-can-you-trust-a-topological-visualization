#!/usr/bin/env python3
"""Extension B (Stage 3) — build the Mapper sensitivity explorer viewer.

Reads ONLY saved experiment outputs (never recomputes Mapper or persistent
homology) and emits a fully self-contained, offline HTML viewer:

  viewer/index.html          single file: template + ALL data inlined
                             (opens from file:// with no server, no CDN,
                             no network access of any kind)
  data/explorer_data.json    the same data as a standalone JSON artifact
  results/build_report.json  what was embedded, from where, with checksums

Data sources (all precomputed):
  results/e2/e2_sensitivity.json                       annulus + figure-eight grids
  results/e2/e2_blob_sanity.json                       no-loop blob control (2 cells)
  extensions/meteorology/results/weather_mapper_results.json   weather grid + doy lens
  extensions/meteorology/results/weather_analysis_results.json weather PH metadata
  results/e1/data/{annulus,figure_eight,blob}.npy      point clouds
  extensions/meteorology/results/weather_pca_coords.npy        weather 2-D PCA cloud
  results/e1/{...}_ph_dgms.npz                         persistence diagrams
  extensions/meteorology/results/weather_state_space_dgms.npz
  extensions/meteorology/results/weather_seasonal_ph_dgms.npz (reference config)

Layouts are computed here (deterministic, seeded, same conventions as the
project figures) and embedded as coordinates; the viewer never recomputes a
layout, so switching the rendering cannot modify graph structure.

Usage: python extensions/mapper_explorer/scripts/build_viewer.py
           [--repo-root PATH]   (default: the repository containing this file)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import warnings
from pathlib import Path

import networkx as nx
import numpy as np

EXT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO_ROOT = EXT_ROOT.parents[1]
sys.path.insert(0, str(DEFAULT_REPO_ROOT))
from src.figures import component_separated_layout  # noqa: E402

SCHEMA_VERSION = "1.0.0"

CAVEATS = {
    "S": (
        "The membership-Jaccard S score is an EXPLORATORY overlap indicator "
        "(symmetric mean of best membership-Jaccard matches against the "
        "pre-specified reference cell), not a metric and not a canonical "
        "Mapper graph similarity; it is greedy, edge-blind, and not normalized "
        "for node count. Read it only beside component counts and the graphs "
        "themselves; never use it alone to rank cover resolutions."
    ),
    "cycles": (
        "A Mapper graph cycle is NOT automatically a true persistent loop in "
        "the data: the no-loop blob control produces short noise-scale graph "
        "cycles while its H1 persistence diagram correctly shows no dominant "
        "class. Cycle length and scale context distinguish loop-like structure "
        "from noise."
    ),
    "connected": (
        "A visually connected graph is NOT automatically the correct "
        "interpretation of the underlying dataset, and a fragmented graph is "
        "not automatically wrong: both are consequences of the cover "
        "resolution and overlap shown in the metadata panel."
    ),
    "no_participant_study": (
        "This viewer makes parameter-dependent structural changes INSPECTABLE "
        "side-by-side with provenance. The project has no participant study, "
        "so nothing here claims improved human readability in general."
    ),
}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(msg: str) -> None:
    print(f"BUILD ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def _graph_from_json(gj: dict) -> nx.Graph:
    G = nx.Graph()
    for name, members in gj["nodes"].items():
        G.add_node(name, members=members)
    for a, others in gj["links"].items():
        for b in others:
            G.add_edge(a, b)
    return G


def _normalize_layout(pos: dict) -> dict:
    """Map layout coordinates into [0.06, 0.94]^2 (rendering only)."""
    if not pos:
        return {}
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    sx = (x1 - x0) or 1.0
    sy = (y1 - y0) or 1.0
    return {
        n: [round(0.06 + 0.88 * (p[0] - x0) / sx, 5),
            round(0.06 + 0.88 * (p[1] - y0) / sy, 5)]
        for n, p in pos.items()
    }


def _cell_id(n_cubes, perc_overlap) -> str:
    po = f"{perc_overlap:.2f}".rstrip("0").rstrip(".") or "0"
    return f"nc{n_cubes}_po{po}"


def _dgm_pairs(arr: np.ndarray) -> list:
    """Rounded [birth, death] pairs; inf deaths capped for display."""
    out = []
    finite = arr[np.isfinite(arr)]
    cap = float(finite.max()) * 1.05 if len(finite) else 1.0
    for b, d in arr:
        if np.isfinite(d):
            out.append([round(float(b), 4), round(float(d), 4)])
        else:  # third element 1 flags an essential class (death = inf) drawn at the display cap
            out.append([round(float(b), 4), round(cap, 4), 1])
    return out


def _ph_summary(dim1: np.ndarray, dim0: np.ndarray, k: int | None) -> dict:
    """PH summary computed at build time from the SAVED diagram.
    k = the ground-truth rank for synthetic shapes (annulus 1, figure-eight 2,
    None for controls); r_k = p_k / p_{k+1} follows the project convention."""
    pers = np.sort((dim1[:, 1] - dim1[:, 0]))[::-1]
    top3 = [round(float(p), 4) for p in pers[:3]] if len(pers) else []
    if k is not None and len(pers) >= k + 1 and pers[k] > 0:
        gap = round(float(pers[k - 1] / pers[k]), 3)
        gap_label = f"r_{k}"
    else:
        gap = None
        gap_label = f"r_{k}" if k is not None else "r_1"
    return {
        "H0_classes": int(dim0.shape[0]),
        "H1_classes": int(dim1.shape[0]),
        "H1_top3_persistence": top3,
        "gap_ratio": gap,
        "gap_ratio_label": gap_label,
        "note": (f"gap ratio {gap_label} = p_{k or 1} / p_{(k or 1) + 1} over H1 "
                 "persistences, computed at build time from the SAVED diagram; "
                 "the rank k is known from the synthetic construction of each "
                 "dataset (annulus k=1, figure-eight k=2, controls: none); the "
                 "r >= 3 prominence threshold is the project's stated "
                 "convention, not a theorem."),
    }


def _cell_payload(cell: dict, is_reference: bool,
                  S: float | None, reference_stats: dict | None) -> dict:
    """Normalize one saved cell (E2 top-level stats and weather nested
    'structure' stats both supported) into the viewer payload."""
    st = cell.get("structure", cell)   # E2: stats at top level; weather: nested
    gj = cell["graph"]
    G = _graph_from_json(gj)
    if G.number_of_nodes() != st["n_nodes"] or G.number_of_edges() != st["n_edges"]:
        fail(f"saved graph disagrees with saved structure stats for cell "
             f"({cell['n_cubes']}, {cell['perc_overlap']})")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # benign np.where guard
        pos_native = _normalize_layout(dict(nx.spring_layout(G, seed=42)))
        pos_sep = _normalize_layout(component_separated_layout(G, seed=42))
    structure = {k: st[k] for k in (
        "n_nodes", "n_edges", "n_components", "cyclomatic_number",
        "max_basis_cycle_length", "mean_basis_cycle_length")}
    payload = {
        "id": _cell_id(cell["n_cubes"], cell["perc_overlap"]),
        "n_cubes": cell["n_cubes"],
        "perc_overlap": cell["perc_overlap"],
        "is_reference": is_reference,
        "similarity_to_reference_S": S,
        "structure": structure,
        "graph": {"nodes": gj["nodes"], "links": gj["links"]},
        "layout_native": pos_native,
        "layout_separated": pos_sep,
    }
    if reference_stats is not None and not is_reference:
        payload["delta_vs_reference"] = {
            "d_nodes": st["n_nodes"] - reference_stats["n_nodes"],
            "d_edges": st["n_edges"] - reference_stats["n_edges"],
            "d_components": st["n_components"] - reference_stats["n_components"],
            "d_cyclomatic": st["cyclomatic_number"] - reference_stats["cyclomatic_number"],
        }
    else:
        payload["delta_vs_reference"] = None
    return payload


def build(repo_root: Path) -> dict:
    e2 = repo_root / "results" / "e2" / "e2_sensitivity.json"
    blob = repo_root / "results" / "e2" / "e2_blob_sanity.json"
    wx_m = (repo_root / "extensions" / "meteorology" / "results"
            / "weather_mapper_results.json")
    wx_a = (repo_root / "extensions" / "meteorology" / "results"
            / "weather_analysis_results.json")
    sources = {"e2_sensitivity.json": e2, "e2_blob_sanity.json": blob,
               "weather_mapper_results.json": wx_m,
               "weather_analysis_results.json": wx_a}
    for name, p in sources.items():
        if not p.exists():
            fail(f"required input artifact not found: {name} at {p} — "
                 f"run the baseline E2 experiment and the Extension A "
                 f"pipeline before building the viewer")

    e2j = json.loads(e2.read_text())
    blobj = json.loads(blob.read_text())
    wxmj = json.loads(wx_m.read_text())
    wxaj = json.loads(wx_a.read_text())

    provenance = {name: {"path": str(p.relative_to(repo_root)),
                         "bytes": p.stat().st_size,
                         "sha256": sha256_of(p)}
                  for name, p in sources.items()}

    datasets = {}

    # ---------- synthetic shapes (E2 grids) ----------
    for shape in e2j["shapes"]:
        ref = shape["reference_cell"]
        ref_id = _cell_id(ref["n_cubes"], ref["perc_overlap"])
        ref_cell = next(c for c in shape["cells"]
                        if c["n_cubes"] == ref["n_cubes"]
                        and c["perc_overlap"] == ref["perc_overlap"])
        ref_stats = {"n_nodes": ref_cell["n_nodes"], "n_edges": ref_cell["n_edges"],
                     "n_components": ref_cell["n_components"],
                     "cyclomatic_number": ref_cell["cyclomatic_number"]}
        cloud = np.load(repo_root / "results" / "e1" / "data" / f"{shape['shape']}.npy")
        dg = np.load(repo_root / "results" / "e1" / f"{shape['shape']}_ph_dgms.npz")
        cells = []
        for c in shape["cells"]:
            cells.append(_cell_payload(
                c,
                is_reference=(c is ref_cell),
                S=c.get("similarity_to_reference"),
                reference_stats=ref_stats))
        known = {"annulus": "one dominant H1 class (ground-truth loop)",
                 "figure_eight": "two dominant H1 classes (ground-truth loops)"}[
            shape["shape"]]
        datasets[shape["shape"]] = {
            "label": {"annulus": "Annulus (synthetic — known loop)",
                      "figure_eight": "Figure-eight (synthetic — two loops)"}[
                shape["shape"]],
            "tier": "synthetic (baseline E2 parameter grid)",
            "n_points": shape["n_points"],
            "lens": shape["lens"],
            "clusterer": shape["clusterer"],
            "seed": 42,
            "reference_cell": ref_id,
            "point_cloud": [[round(float(x), 4), round(float(y), 4)]
                            for x, y in cloud],
            "ph_diagram": {"H0": _dgm_pairs(dg["H0"]), "H1": _dgm_pairs(dg["H1"])},
            "ph_summary": _ph_summary(dg["H1"], dg["H0"],
                                      k=1 if shape["shape"] == "annulus" else 2),
            "ph_note": (f"Vietoris-Rips PH of the {shape['n_points']}-point cloud "
                        f"(saved diagram, baseline E1): expected {known}."),
            "cells": cells,
        }

    # ---------- no-loop blob control (sanity cells) ----------
    ref_cell = blobj["cells"][0]
    ref_id = _cell_id(ref_cell["n_cubes"], ref_cell["perc_overlap"])
    ref_stats = {"n_nodes": ref_cell["n_nodes"], "n_edges": ref_cell["n_edges"],
                 "n_components": ref_cell["n_components"],
                 "cyclomatic_number": ref_cell["cyclomatic_number"]}
    cloud = np.load(repo_root / "results" / "e1" / "data" / "blob.npy")
    dg = np.load(repo_root / "results" / "e1" / "blob_ph_dgms.npz")
    blob_cells = []
    for c in blobj["cells"]:
        p = _cell_payload(c, is_reference=(c is ref_cell), S=None,
                          reference_stats=ref_stats)
        p["question"] = c.get("question")
        blob_cells.append(p)
    datasets["blob"] = {
        "label": "No-loop blob (synthetic control)",
        "tier": "synthetic control (baseline E2 sanity check, diagnostic cells only)",
        "n_points": blobj["n_points"],
        "lens": e2j["shapes"][0]["lens"],
        "clusterer": e2j["shapes"][0]["clusterer"],
        "seed": 42,
        "reference_cell": ref_id,
        "point_cloud": [[round(float(x), 4), round(float(y), 4)]
                        for x, y in cloud],
        "ph_diagram": {"H0": _dgm_pairs(dg["H0"]), "H1": _dgm_pairs(dg["H1"])},
        "ph_summary": _ph_summary(dg["H1"], dg["H0"], k=None),
        "ph_note": ("No-loop control: the H1 diagram has NO dominant class "
                    "(top-3 persistences are noise-scale), yet Mapper graph "
                    "cycles still appear — the cycles-vs-loops trap this "
                    "viewer exists to make visible."),
        "cells": blob_cells,
    }

    # ---------- weather (Extension A grid + day-of-year lens variant) ----------
    ref_id = wxmj["reference_cell"]
    ref_cell = wxmj["cells"][ref_id]
    ref_stats = {"n_nodes": ref_cell["structure"]["n_nodes"],
                 "n_edges": ref_cell["structure"]["n_edges"],
                 "n_components": ref_cell["structure"]["n_components"],
                 "cyclomatic_number": ref_cell["structure"]["cyclomatic_number"]}
    pca = np.load(repo_root / "extensions" / "meteorology" / "results"
                  / "weather_pca_coords.npy")
    ss = np.load(repo_root / "extensions" / "meteorology" / "results"
                 / "weather_state_space_dgms.npz")
    seas = np.load(repo_root / "extensions" / "meteorology" / "results"
                   / "weather_seasonal_ph_dgms.npz")
    ref_sw = wxaj["seasonal_ph"]["reference"]
    wx_cells = []
    for key, c in wxmj["cells"].items():
        p = _cell_payload(c, is_reference=(key == ref_id),
                          S=c.get("membership_jaccard_S_vs_reference"),
                          reference_stats=ref_stats)
        p["id"] = key
        wx_cells.append(p)
    doy = wxmj["day_of_year"]
    doy_cell = {
        "id": "doy_nc10_po0.35",
        "n_cubes": int(doy["cell"].split("_")[0][2:]),
        "perc_overlap": 0.35,
        "is_reference": False,
        "lens_variant": "day-of-year (normalized)",
        "lens_variant_note": doy["note"],
        "similarity_to_reference_S": None,
        "structure": doy["structure"],
        "graph": {"nodes": doy["graph"]["nodes"], "links": doy["graph"]["links"]},
        "layout_native": None,   # filled below
        "layout_separated": None,
        "delta_vs_reference": None,
    }
    G = _graph_from_json(doy["graph"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        doy_cell["layout_native"] = _normalize_layout(dict(nx.spring_layout(G, seed=42)))
        doy_cell["layout_separated"] = _normalize_layout(component_separated_layout(G, seed=42))
    ss_stats = wxaj["state_space_ph"]
    sw_stats = wxaj["seasonal_ph"]["sweep"][ref_sw]
    datasets["weather"] = {
        "label": "NY Central Park daily weather cloud (GSOD 2019-2024)",
        "tier": "real data (Extension A parameter grid)",
        "n_points": int(pca.shape[0]),
        "lens": "PCA-1 on the z-scored TEMP/DEWP/SLP cloud (unsupervised)",
        "clusterer": "KMeans(n_clusters=2, random_state=42, n_init=10)",
        "seed": 42,
        "reference_cell": ref_id,
        "point_cloud": [[round(float(x), 4), round(float(y), 4)]
                        for x, y in pca],
        "ph_diagram": {
            "state_space": {"H0": _dgm_pairs(ss["dgm0"]), "H1": _dgm_pairs(ss["dgm1"])},
            "seasonal_reference": {"H0": _dgm_pairs(seas[f"{ref_sw}_dgm0"]),
                                   "H1": _dgm_pairs(seas[f"{ref_sw}_dgm1"])},
        },
        "ph_summary": {
            "state_space": {
                "H1_classes": ss_stats["H1_classes"],
                "dominant_H1_persistence": ss_stats["dominant_H1_persistence"],
                "gap_ratio_r1": ss_stats["gap_ratio_r1"],
                "note": ("state-space cloud (TEMP/DEWP/SLP): NO dominant H1 "
                         "class — the negative representation contrast; the "
                         "annual signal lives in temporal organization, not "
                         "static daily-state geometry."),
            },
            "seasonal_reference": {
                "config": ref_sw,
                "span_days": sw_stats["span_days"],
                "H1_classes": sw_stats["H1_classes"],
                "dominant_H1_persistence": sw_stats["dominant_H1_persistence"],
                "gap_ratio_r1": sw_stats["gap_ratio_r1"],
                "note": ("sliding-window embedding (tau=60, d=8, span 420 d) of "
                         "the z-scored daily TEMP series: ONE dominant H1 "
                         "class — consistent with recurrent seasonal or "
                         "quasi-periodic structure, not proof of a simple "
                         "closed physical climate trajectory."),
            },
        },
        "ph_note": ("Two computed-PH views from Extension A: the 3-D state-space "
                    "cloud (no dominant loop) and the reference sliding-window "
                    "embedding of the TEMP series (one dominant H1 class). "
                    "These are different constructions of the same daily "
                    "observations."),
        "cells": wx_cells + [doy_cell],
    }

    data = {
        "schema_version": SCHEMA_VERSION,
        "built_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "viewer_title": "Mapper sensitivity explorer — saved results only",
        "caveats": CAVEATS,
        "provenance": provenance,
        "datasets": datasets,
    }
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    args = ap.parse_args()
    repo_root = args.repo_root.resolve()
    if not repo_root.exists():
        fail(f"repository root does not exist: {repo_root}")

    data = build(repo_root)

    out_json = EXT_ROOT / "data" / "explorer_data.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(data, indent=1) + "\n")

    template = (EXT_ROOT / "viewer" / "template.html").read_text()
    inline = json.dumps(data, separators=(",", ":"))
    if "/*__EXPLORER_DATA__*/" not in template:
        fail("viewer/template.html is missing the /*__EXPLORER_DATA__*/ placeholder")
    html = template.replace("/*__EXPLORER_DATA__*/", inline)
    out_html = EXT_ROOT / "viewer" / "index.html"
    out_html.write_text(html)

    report = {
        "built_utc": data["built_utc"],
        "schema_version": SCHEMA_VERSION,
        "outputs": {
            "viewer/index.html": {"bytes": out_html.stat().st_size,
                                  "sha256": sha256_of(out_html)},
            "data/explorer_data.json": {"bytes": out_json.stat().st_size,
                                        "sha256": sha256_of(out_json)},
        },
        "sources": data["provenance"],
        "dataset_cell_counts": {k: len(v["cells"]) for k, v in data["datasets"].items()},
    }
    (EXT_ROOT / "results").mkdir(parents=True, exist_ok=True)
    (EXT_ROOT / "results" / "build_report.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print(f"viewer built: {out_html} "
          f"({out_html.stat().st_size/1e6:.2f} MB, "
          f"{sum(len(v['cells']) for v in data['datasets'].values())} cells "
          f"across {len(data['datasets'])} datasets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
