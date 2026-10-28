#!/usr/bin/env python3
"""Experiment 2 — Mapper parameter-sensitivity grid (blueprint Section 4.2).

Phase-2 scope: BOTH primary shapes (annulus + figure-eight; 12 cells each,
24 cells total) plus the no-loop blob sanity control at two diagnostic
settings. Per cell this script measures: node/edge/component counts,
cyclomatic number, cycle-basis length statistics, membership-overlap
similarity to the pre-specified reference cell, and runtime. It also runs
the determinism control (identical-membership rerun of the reference cell)
per primary shape.

Outputs (no expected outcomes are hard-coded here; everything is measured):
  results/e2/e2_sensitivity.json  — full per-cell records incl. memberships
  results/e2/e2_sensitivity.csv   — compact per-cell numeric table
  results/e2/e2_blob_sanity.json  — no-loop control: graph stats + H1 calibration

Figures are rendered SEPARATELY from these saved results by src/figures.py.
"""
from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
import time
from importlib import metadata as md
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from shapes import make_shape, GROUND_TRUTH_H1_RANK  # noqa: E402
from pipeline import (  # noqa: E402
    MAPPER_CYCLES_CAVEAT, compute_ph, mapper_run, mapper_structure_stats,
    graph_to_jsonable, ph_summary)
from similarity import (  # noqa: E402
    SIMILARITY_CAVEAT, memberships_equal, memberships_from_graph, similarity)

CSV_COLUMNS = ["shape", "n_cubes", "perc_overlap", "n_nodes", "n_edges",
               "n_components", "cyclomatic_number", "max_basis_cycle_length",
               "mean_basis_cycle_length", "similarity_to_reference", "time_s"]


def die(msg: str) -> None:
    print(f"ERROR [run_e2_sensitivity]: {msg}", file=sys.stderr)
    sys.exit(1)


def load_yaml(path: Path) -> dict:
    if not path.exists():
        die(f"config not found: {path}")
    with open(path) as fh:
        return yaml.safe_load(fh)


def run_shape(shape_name: str, shape_cfg: dict, cfg: dict) -> dict:
    grid = cfg["grid"]
    ref = cfg["reference_cell"]
    consts = cfg["constants"]

    n_cubes_list = grid["n_cubes"]
    overlap_list = grid["perc_overlap"]
    if not n_cubes_list or not overlap_list:
        die("grid lists must be non-empty (n_cubes, perc_overlap).")
    if (ref["n_cubes"] not in n_cubes_list
            or ref["perc_overlap"] not in overlap_list):
        die(f"reference cell ({ref['n_cubes']}, {ref['perc_overlap']}) "
            "is not inside the configured grid.")

    X = make_shape(shape_name, shape_cfg)

    t0 = time.perf_counter()
    ref_graph = mapper_run(X, ref["n_cubes"], ref["perc_overlap"],
                           seed=consts["kmeans_seed"],
                           n_clusters=consts["kmeans_n_clusters"])
    ref_memberships = memberships_from_graph(ref_graph)
    ref_build_s = time.perf_counter() - t0

    cells = []
    for nc in n_cubes_list:
        for po in overlap_list:
            t0 = time.perf_counter()
            graph = mapper_run(X, nc, po, seed=consts["kmeans_seed"],
                               n_clusters=consts["kmeans_n_clusters"])
            elapsed = time.perf_counter() - t0
            stats = mapper_structure_stats(graph)
            stats["n_cubes"] = int(nc)
            stats["perc_overlap"] = float(po)
            stats["similarity_to_reference"] = round(
                similarity(memberships_from_graph(graph), ref_memberships), 4)
            stats["time_s"] = round(elapsed, 4)
            stats["is_reference"] = (nc == ref["n_cubes"]
                                     and po == ref["perc_overlap"])
            stats["graph"] = graph_to_jsonable(graph)
            cells.append(stats)

    control = {"requested": bool(cfg.get("controls", {}).get("determinism", False))}
    if control["requested"]:
        rerun = mapper_run(X, ref["n_cubes"], ref["perc_overlap"],
                           seed=consts["kmeans_seed"],
                           n_clusters=consts["kmeans_n_clusters"])
        rerun_m = memberships_from_graph(rerun)
        control["memberships_identical"] = memberships_equal(ref_memberships,
                                                             rerun_m)
        control["similarity_rerun"] = round(
            similarity(ref_memberships, rerun_m), 6)
        if not control["memberships_identical"] or control["similarity_rerun"] != 1.0:
            die("determinism control FAILED: identical-parameter rerun "
                "produced different node memberships. Do not proceed to "
                "sensitivity interpretation; investigate the environment.")

    return {
        "shape": shape_name,
        "n_points": int(len(X)),
        "shape_params": shape_cfg,
        "lens": consts["lens"],
        "clusterer": (f"KMeans(n_clusters={consts['kmeans_n_clusters']}, "
                      f"random_state={consts['kmeans_seed']}, n_init=10)"),
        "reference_cell": {"n_cubes": ref["n_cubes"],
                           "perc_overlap": ref["perc_overlap"],
                           "build_time_s": round(ref_build_s, 4)},
        "cells": cells,
        "determinism_control": control,
    }


def run_sanity_control(shapes_cfg: dict, cfg: dict) -> dict | None:
    """No-loop blob sanity control at the configured diagnostic settings.

    NOT a third 12-cell sweep: each configured cell answers a specific
    question (see configs/e2_sensitivity.yaml). The H1 calibration shows
    the persistence diagram correctly reports NO dominant class on this
    data, while the Mapper graph may still contain short noise-scale
    cycles — the critical distinction recorded in MAPPER_CYCLES_CAVEAT.
    """
    sc = cfg.get("sanity_control")
    if not sc:
        return None
    name = sc["shape"]
    if name not in (shapes_cfg.get("shapes") or {}):
        die(f"sanity_control shape '{name}' not defined in shapes.yaml")
    consts = cfg["constants"]
    X = make_shape(name, shapes_cfg["shapes"][name])

    out = {
        "shape": name,
        "n_points": int(len(X)),
        "shape_params": shapes_cfg["shapes"][name],
        "purpose": (
            "Sanity control at diagnostic settings only (not a full sweep): "
            "does the no-loop dataset produce Mapper-graph cycles that a "
            "naive reader could misread as topological loops, while its H1 "
            "diagram correctly shows no dominant class?"),
        "mapper_cycles_caveat": MAPPER_CYCLES_CAVEAT,
        "cells": [],
    }

    if sc.get("h1_calibration", False):
        ph = ph_summary(X, maxdim=1,
                        h1_rank=GROUND_TRUTH_H1_RANK.get(name))
        dgms = compute_ph(X, maxdim=1)["dgms"]
        out["h1_calibration"] = {
            **ph,
            "H1_diagram": [[round(float(b), 6), round(float(d), 6)]
                           for b, d in dgms[1]],
            "reading": (
                "Construction implies NO dominant H1 class; gap ratios are "
                "calibration values only (R-1). Compare with the graph-cycle "
                "statistics below — this is the cycles-vs-loops contrast."),
        }

    for cell in sc["cells"]:
        nc, po = int(cell["n_cubes"]), float(cell["perc_overlap"])
        t0 = time.perf_counter()
        graph = mapper_run(X, nc, po, seed=consts["kmeans_seed"],
                           n_clusters=consts["kmeans_n_clusters"])
        elapsed = time.perf_counter() - t0
        stats = mapper_structure_stats(graph)
        stats["n_cubes"] = nc
        stats["perc_overlap"] = po
        stats["time_s"] = round(elapsed, 4)
        stats["question"] = (
            "reference setting: cycles on no-loop data?" if (nc, po) == (10, 0.35)
            else "extreme setting (the annulus-fragmentation cell)")
        stats["graph"] = graph_to_jsonable(graph)
        out["cells"].append(stats)

    return out


def _environment_meta() -> dict:
    """Package/python versions recorded so the run is reproducible."""
    pkgs = {}
    for pkg in ["ripser", "persim", "kmapper", "scikit-learn", "numpy",
                "scipy", "matplotlib", "networkx"]:
        try:
            pkgs[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            pkgs[pkg] = "NOT INSTALLED"
    return {"python": platform.python_version(),
            "platform": platform.platform(),
            "packages": pkgs}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default=str(REPO / "configs" / "e2_sensitivity.yaml"),
                    help="path to e2_sensitivity.yaml")
    ap.add_argument("--shapes-config",
                    default=str(REPO / "configs" / "shapes.yaml"),
                    help="path to shapes.yaml")
    args = ap.parse_args()

    cfg = load_yaml(Path(args.config))
    shapes_cfg = load_yaml(Path(args.shapes_config))

    shape_names = cfg.get("shapes") or []
    if not shape_names:
        die("'shapes' list is empty in the E2 config.")
    missing = [s for s in shape_names if s not in (shapes_cfg.get("shapes") or {})]
    if missing:
        die(f"shapes {missing} not defined in shapes.yaml")

    results = {
        "meta": {
            "script": "scripts/run_e2_sensitivity.py",
            "config": str(Path(args.config).relative_to(REPO)),
            "contrast_cell_pre_specified": cfg.get("contrast_cell"),
            "contrast_note": (
                "contrast_cell is PER SHAPE; null entries auto-select in the "
                "figure step by the documented rule: among non-reference "
                "cells maximize (|delta n_components|, |delta cyclomatic|, "
                "1 - S) lexicographically"),
            "mapper_cycles_caveat": MAPPER_CYCLES_CAVEAT,
            "similarity_caveat": SIMILARITY_CAVEAT,
            "similarity_definition": (
                "S(G1,G2) = 1/2 * [mean_{n in N1} max_{m in N2} J(n,m) + "
                "symmetric term], J = membership Jaccard. Corrected property: "
                "S=1 iff the two graphs have the same set of DISTINCT "
                "membership sets (node multiplicities and edges may differ). "
                "Not a metric; not normalized across resolutions."),
            "cyclomatic_number_definition": (
                "cyclomatic_number = E - V + C (edges - vertices + connected "
                "components): the number of independent cycles in the graph. "
                "Computed on the kmapper graph via networkx; see "
                "mapper_cycles_caveat before reading it as topology."),
            "expected_cells_per_shape": len(cfg["grid"]["n_cubes"])
            * len(cfg["grid"]["perc_overlap"]),
            "resolved": {
                "shapes": shape_names,
                "grid": cfg["grid"],
                "reference_cell": cfg["reference_cell"],
                "constants": cfg["constants"],
                "sanity_control": cfg.get("sanity_control"),
            },
            "environment": _environment_meta(),
        },
        "shapes": [],
    }

    for name in shape_names:
        print(f"--- E2 grid: {name} "
              f"({len(cfg['grid']['n_cubes']) * len(cfg['grid']['perc_overlap'])} cells) ---")
        results["shapes"].append(run_shape(name, shapes_cfg["shapes"][name], cfg))

    sanity = run_sanity_control(shapes_cfg, cfg)
    if sanity is not None:
        print(f"--- E2 sanity control: {sanity['shape']} "
              f"({len(sanity['cells'])} diagnostic cells) ---")

    out_dir = REPO / cfg["paths"]["results_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "e2_sensitivity.json"
    results["sanity_control"] = sanity
    json_path.write_text(json.dumps(results, indent=2))

    if sanity is not None:
        sanity_path = out_dir / f"e2_{sanity['shape']}_sanity.json"
        sanity_path.write_text(json.dumps(sanity, indent=2))
        print(f"Wrote {sanity_path}")

    csv_path = out_dir / "e2_sensitivity.csv"
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for shape_res in results["shapes"]:
            for cell in shape_res["cells"]:
                w.writerow({"shape": shape_res["shape"],
                            "n_cubes": cell["n_cubes"],
                            "perc_overlap": cell["perc_overlap"],
                            **{k: cell.get(k) for k in CSV_COLUMNS[3:]}})
    print(f"\nWrote {json_path}\nWrote {csv_path}")

    # quick console summary (measured, not expected)
    for shape_res in results["shapes"]:
        comps = sorted({c["n_components"] for c in shape_res["cells"]})
        cycs = sorted({c["cyclomatic_number"] for c in shape_res["cells"]})
        sims = [c["similarity_to_reference"] for c in shape_res["cells"]]
        ctrl = shape_res["determinism_control"]
        print(f"{shape_res['shape']}: components observed {comps}; "
              f"cyclomatic observed {cycs}; "
              f"similarity range {min(sims):.3f}-{max(sims):.3f}; "
              f"determinism control: "
              f"{'identical' if ctrl.get('memberships_identical') else 'FAILED'}")
    if sanity:
        cal = sanity.get("h1_calibration", {})
        print(f"sanity ({sanity['shape']}): H1 r_1 calibration="
              f"{cal.get('gap_ratio_r1_calibration')}; graph cells: "
              + "; ".join(
                  f"({c['n_cubes']},{c['perc_overlap']})={c['n_components']}cc/"
                  f"{c['cyclomatic_number']}cyc/maxlen{c['max_basis_cycle_length']}"
                  for c in sanity["cells"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
