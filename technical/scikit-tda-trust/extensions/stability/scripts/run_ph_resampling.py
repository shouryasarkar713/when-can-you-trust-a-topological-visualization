#!/usr/bin/env python3
"""Stage 4 Part B — persistence-diagram resampling stability (synthetic data).

Design (per Stage-4 authorization):
  * Datasets: the EXISTING seeded generators (annulus, figure-eight, no-loop
    blob) with their current configs/shapes.yaml parameters and ground-truth
    definitions — regenerated and verified byte-identical to the baseline E1
    saved point clouds before use.
  * 30 deterministic 80%-without-replacement subsamples per shape; the seed
    AND the sorted sampling indices are stored for every replicate.
  * Reference diagrams: the baseline E1 full-data diagrams
    (results/e1/{shape}_ph_dgms.npz) computed with the pinned ripser
    configuration (maxdim=1).
  * Per replicate and per homology dimension (H0 and H1 kept separate):
    bottleneck and Wasserstein distances to the reference (pinned persim
    0.4.1 API), prominent persistence values, and the pre-specified
    persistence-gap diagnostic for the shape's construction.
  * Numerical outputs are saved BEFORE any figure exists.

DOCUMENTED DEPENDENCE (interpretation guard): the full-data reference
overlaps each 80% subsample by construction. The distances below are
DESCRIPTIVE resampling-stability quantities, not independent validation and
not unbiased estimates of generalization error. The spread of the 30
distances is a variability band, NOT a formal confidence set; no hypothesis
test is performed (a diagram distance is a metric value, not a test
statistic with a null distribution — see README.md).

Essential-class handling: persim's bottleneck/wasserstein drop points with
non-finite death (the essential H0 class) from both diagrams before
computing distances; this is recorded in the output metadata.

RESUMABILITY: each replicate is checkpointed to
results/_ph_partial_{shape}.json (the sandbox limits single-process wall
time, so the run may need several invocations). Re-invoking the script
skips completed replicates; when every configured shape is complete, the
partial files are merged into results/ph_resampling.json and removed.

Usage: python extensions/stability/scripts/run_ph_resampling.py [--shape S]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

EXT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXT_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))

from ripser import ripser  # noqa: E402
from persim import bottleneck as ps_bottleneck  # noqa: E402
from persim import wasserstein as ps_wasserstein  # noqa: E402

from src.pipeline import gap_ratio, h1_persistences  # noqa: E402
from src.shapes import GROUND_TRUTH_H1_RANK, make_shape  # noqa: E402

RESULTS = EXT_ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)  # independent-rebuild fix: fresh trees lack the dir
E1_DATA = REPO_ROOT / "results" / "e1" / "data"
E1_DGMS = REPO_ROOT / "results" / "e1"


def subsample_indices(n: int, size: int, seed: int) -> np.ndarray:
    """Deterministic sorted without-replacement subsample of range(n)."""
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(n, size=size, replace=False))


def finite_classes(dgm: np.ndarray) -> np.ndarray:
    """Rows of a diagram with finite death (drops the essential class)."""
    return dgm[np.isfinite(dgm[:, 1])]


def reference_diagnostics(ref_dgms: dict, rank: int | None) -> dict:
    ref_pers = h1_persistences(ref_dgms[1])
    diag = {
        "H1_classes": int(len(ref_dgms[1])),
        "H0_finite_classes": int(len(finite_classes(ref_dgms[0]))),
        "H1_top3_persistence": [round(float(x), 4) for x in ref_pers[:3]],
    }
    r1 = gap_ratio(ref_pers, 1)
    diag["gap_ratio_r1"] = round(r1, 3) if r1 is not None else None
    if rank is not None:
        rk = gap_ratio(ref_pers, rank)
        diag[f"gap_ratio_r{rank}_at_ground_truth_rank"] = (
            round(rk, 3) if rk is not None else None)
    return diag


def run_shape(shape: str, cfg: dict, shapes_cfg: dict) -> dict:
    """Run (or resume) all replicates for one shape; returns its result block."""
    rs, ph_cfg = cfg["resampling"], cfg["ph"]
    n_rep = int(rs["n_replicates"])
    frac = float(rs["fraction"])
    seed_base = int(rs["seed_base"])
    partial_path = RESULTS / f"_ph_partial_{shape}.json"

    params = shapes_cfg["shapes"][shape]
    X = make_shape(shape, params)
    saved = np.load(E1_DATA / f"{shape}.npy")
    if not np.allclose(X, saved, rtol=0.0, atol=1e-12):  # independent-rebuild: libm trig differs by 1 ULP across platforms
        raise SystemExit(
            f"BUILD ERROR: regenerated {shape} differs from the baseline "
            "E1 saved point cloud — refusing to proceed (the experiment "
            "must reuse the existing datasets).")
    ref_npz = np.load(E1_DGMS / f"{shape}_ph_dgms.npz")
    ref_dgms = {0: ref_npz["H0"], 1: ref_npz["H1"]}
    rank = GROUND_TRUTH_H1_RANK[shape]
    n = len(X)
    size = int(round(frac * n))

    if partial_path.exists():
        block = json.loads(partial_path.read_text())
        print(f"{shape}: resuming — {len(block['replicates'])}/{n_rep} replicates done")
    else:
        block = {
            "n_full": n, "subsample_size": size,
            "ground_truth_h1_rank": rank,
            "reference_diagnostics": reference_diagnostics(ref_dgms, rank),
            "replicates": [], "runtime_s_cumulative": 0.0,
        }
    reps = block["replicates"]

    if len(reps) < n_rep:
        print(f"{shape}: n={n}, subsample size={size}, ground-truth H1 rank={rank}")
    for i in range(len(reps), n_rep):
        t_rep = time.perf_counter()
        seed = seed_base + int(rs["seed_offsets"][shape]) + i
        idx = subsample_indices(n, size, seed)
        t0 = time.perf_counter()
        dgms = ripser(X[idx], maxdim=int(ph_cfg["maxdim"]))["dgms"]
        t_ripser = time.perf_counter() - t0

        rec: dict = {
            "rep": i,
            "seed": int(seed),
            "indices": [int(v) for v in idx],
            "n_points": size,
            "ripser_time_s": round(t_ripser, 4),
            "distances": {},
            "diagnostics": {},
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # essential-class drops, documented
            for dim in (0, 1):
                d_res, d_ref = dgms[dim], ref_dgms[dim]
                rec["distances"][f"H{dim}"] = {
                    "n_finite_resample": int(len(finite_classes(d_res))),
                    "n_finite_reference": int(len(finite_classes(d_ref))),
                }
                for metric in ph_cfg["metrics"]:
                    t0 = time.perf_counter()
                    if metric == "bottleneck":
                        val = float(ps_bottleneck(d_res, d_ref))
                    elif metric == "wasserstein":
                        val = float(ps_wasserstein(d_res, d_ref))
                    else:
                        raise SystemExit(f"BUILD ERROR: unknown metric {metric!r}")
                    rec["distances"][f"H{dim}"][metric] = {
                        "value": round(val, 6),
                        "time_s": round(time.perf_counter() - t0, 4),
                    }

        pers = h1_persistences(dgms[1])
        diag = {
            "H1_classes": int(len(dgms[1])),
            "H0_finite_classes": int(len(finite_classes(dgms[0]))),
            "H1_top3_persistence": [round(float(x), 4) for x in pers[:3]],
        }
        r1 = gap_ratio(pers, 1)
        diag["gap_ratio_r1"] = round(r1, 3) if r1 is not None else None
        if rank is not None:
            rk = gap_ratio(pers, rank)
            diag[f"gap_ratio_r{rank}_at_ground_truth_rank"] = (
                round(rk, 3) if rk is not None else None)
            diag["ground_truth_h1_rank"] = rank
        rec["diagnostics"] = diag
        reps.append(rec)
        block["runtime_s_cumulative"] = round(
            block["runtime_s_cumulative"] + time.perf_counter() - t_rep, 2)
        partial_path.write_text(json.dumps(block, indent=1))  # checkpoint

    # rename the accumulated checkpoint runtime into its final key
    block["runtime_s_total"] = block.pop("runtime_s_cumulative", 0.0)
    return block


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--shape", choices=["annulus", "figure_eight", "blob"],
                    help="run a single shape only (resume support)")
    args = ap.parse_args()

    t_start = time.perf_counter()
    cfg = yaml.safe_load((EXT_ROOT / "configs" / "stability.yaml").read_text())
    shapes_cfg = yaml.safe_load((REPO_ROOT / "configs" / "shapes.yaml").read_text())
    rs, ph_cfg = cfg["resampling"], cfg["ph"]

    meta = {
        "step": "run_ph_resampling",
        "config": {
            "n_replicates": int(rs["n_replicates"]),
            "fraction": float(rs["fraction"]),
            "seed_base": int(rs["seed_base"]),
            "seed_offsets": {k: int(v) for k, v in rs["seed_offsets"].items()},
            "seed_rule": "seed(shape, rep i) = seed_base + seed_offsets[shape] + i",
            "sampling": "without replacement, sorted indices stored per replicate",
            "ripser_maxdim": int(ph_cfg["maxdim"]),
            "metrics": list(ph_cfg["metrics"]),
            "homology_dims": [int(d) for d in ph_cfg["homology_dims"]],
            "gap_diagnostics": ph_cfg["gap_diagnostics"],
            "reference": "baseline E1 full-data diagrams (results/e1/{shape}_ph_dgms.npz)",
        },
        "reference_overlap_guard": (
            "The full-data reference OVERLAPS each 80% subsample: distances "
            "are descriptive resampling stability, not independent validation "
            "and not an unbiased generalization estimate. The spread of the 30 "
            "distances is a variability band, not a formal confidence set."),
        "methodology_note_metric_vs_test": (
            "Bottleneck and Wasserstein distances are METRICS between "
            "persistence diagrams. Reporting their values across resamples "
            "is NOT a statistical hypothesis test: there is no null "
            "distribution, no p-value, and no rejection region anywhere in "
            "this extension."),
        "essential_class_handling": (
            "persim 0.4.1 bottleneck/wasserstein drop points with non-finite "
            "death times (the essential H0 class) from both diagrams before "
            "computing distances; distances concern finite classes only."),
    }

    shapes_to_run = [args.shape] if args.shape else list(cfg["shapes"])
    for shape in shapes_to_run:
        run_shape(shape, cfg, shapes_cfg)

    # merge when every configured shape is complete
    complete = {}
    for shape in cfg["shapes"]:
        p = RESULTS / f"_ph_partial_{shape}.json"
        if not p.exists():
            continue
        block = json.loads(p.read_text())
        if len(block["replicates"]) == int(rs["n_replicates"]):
            block["runtime_s_total"] = block.pop("runtime_s_cumulative", 0.0)
            complete[shape] = block
    if len(complete) == len(cfg["shapes"]):
        out = {"created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               **meta, "shapes": complete,
               "runtime_note": ("wall-clock accumulated across resumable "
                                "invocations; per-replicate ripser and "
                                "distance timings are recorded individually")}
        (RESULTS / "ph_resampling.json").write_text(json.dumps(out, indent=1))
        for shape in complete:
            (RESULTS / f"_ph_partial_{shape}.json").unlink()
        print(f"MERGED -> {RESULTS / 'ph_resampling.json'}")
        return 0
    print("partial progress saved; re-invoke to continue remaining shapes/replicates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
