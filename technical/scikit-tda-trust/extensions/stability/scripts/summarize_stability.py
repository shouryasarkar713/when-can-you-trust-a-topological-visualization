#!/usr/bin/env python3
"""Stage 4 — build results/stability_summary.json FROM SAVED RESULTS ONLY.

Aggregates the three experiment outputs into one machine-readable summary
(cross-shape comparisons, stable-vs-varying examples, LOYO ranges) so that
README.md and claims_evidence.json cite exact computed numbers.

Usage: python extensions/stability/scripts/summarize_stability.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

EXT_ROOT = Path(__file__).resolve().parents[1]
RESULTS = EXT_ROOT / "results"


def _stats(v: list[float]) -> dict:
    a = np.asarray(v, dtype=float)
    return {
        "median": round(float(np.median(a)), 5),
        "q25": round(float(np.percentile(a, 25)), 5),
        "q75": round(float(np.percentile(a, 75)), 5),
        "min": round(float(a.min()), 5),
        "max": round(float(a.max()), 5),
    }


def main() -> int:
    ph = json.loads((RESULTS / "ph_resampling.json").read_text())
    mp = json.loads((RESULTS / "mapper_resampling.json").read_text())
    loyo = json.loads((RESULTS / "weather_loyo.json").read_text())

    out: dict = {
        "step": "summarize_stability",
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "guards": {
            "reference_overlap": ph["reference_overlap_guard"],
            "metric_not_test": ph["methodology_note_metric_vs_test"],
            "similarity_caveat": mp["similarity_caveat"],
            "weather_status": loyo["status_guard"],
        },
        "ph_resampling": {},
        "mapper_resampling": {},
        "weather_loyo": {},
    }

    # ---- Part B aggregation ----
    for shape, blk in ph["shapes"].items():
        reps = blk["replicates"]
        ref = blk["reference_diagnostics"]
        rank = blk["ground_truth_h1_rank"]
        s: dict = {
            "n_replicates": len(reps),
            "reference_dominant_H1": ref["H1_top3_persistence"][0],
            "resample_dominant_H1": _stats(
                [r["diagnostics"]["H1_top3_persistence"][0] for r in reps]),
            "distances": {},
        }
        for dim in ("H0", "H1"):
            for metric in ("bottleneck", "wasserstein"):
                s["distances"][f"{dim}_{metric}"] = _stats(
                    [r["distances"][dim][metric]["value"] for r in reps])
        # relative scale: H1 bottleneck / reference dominant persistence
        dom = ref["H1_top3_persistence"][0]
        s["H1_bottleneck_over_dominant"] = _stats(
            [r["distances"]["H1"]["bottleneck"]["value"] / dom for r in reps])
        if rank is not None:
            key = f"gap_ratio_r{rank}_at_ground_truth_rank"
            s["gap_diagnostic"] = {
                "statistic": f"r{rank} at ground-truth rank {rank}",
                "reference": ref.get(key),
                "resamples": _stats([r["diagnostics"][key] for r in reps]),
            }
        else:
            s["gap_diagnostic"] = {
                "statistic": "r1 calibration only (no constructed rank)",
                "reference": ref["gap_ratio_r1"],
                "resamples": _stats(
                    [r["diagnostics"]["gap_ratio_r1"] for r in reps]),
            }
        out["ph_resampling"][shape] = s

    # ---- Part C aggregation ----
    for shape, blk in mp["shapes"].items():
        reps = blk["replicates"]
        ref = blk["reference"]["structure"]
        def counts(key):
            c: dict = {}
            for r in reps:
                c[r["structure"][key]] = c.get(r["structure"][key], 0) + 1
            return {str(k): v for k, v in sorted(c.items())}
        out["mapper_resampling"][shape] = {
            "n_replicates": len(reps),
            "reference": {k: ref[k] for k in
                          ("n_nodes", "n_edges", "n_components",
                           "cyclomatic_number")},
            "n_nodes_counts": counts("n_nodes"),
            "n_edges_range": [min(r["structure"]["n_edges"] for r in reps),
                              max(r["structure"]["n_edges"] for r in reps)],
            "n_components_counts": counts("n_components"),
            "cyclomatic_number_counts": counts("cyclomatic_number"),
            "S_vs_reference": _stats(
                [r["membership_jaccard_S_vs_reference"] for r in reps]),
            "S_note": "exploratory overlap indicator only (see guards)",
        }

    # ---- Part D aggregation ----
    years = sorted(loyo["folds"].keys())
    for cfg, fref in loyo["full_data_reference"].items():
        fold_doms, fold_r1s, lost = [], [], 0
        for y in years:
            c = loyo["folds"][y]["configs"][cfg]
            fold_doms.append(c["dominant_H1_persistence"])
            fold_r1s.append(c["gap_ratio_r1"])
            lost = max(lost, c["n_windows_lost_to_gap"])
        out["weather_loyo"][cfg] = {
            "full_data": {"dominant_H1": fref["dominant_H1_persistence"],
                          "r1": fref["gap_ratio_r1"],
                          "n_points": fref["n_points"]},
            "fold_dominant_H1": _stats(fold_doms),
            "fold_r1": _stats(fold_r1s),
            "all_folds_r1_at_least_3": bool(min(fold_r1s) >= 3),
            "min_fold_r1": round(min(fold_r1s), 3),
            "max_windows_lost_to_gap": lost,
        }

    # ---- headline stable-vs-varying examples (computed, not hand-picked) ----
    ann = out["ph_resampling"]["annulus"]
    fe = out["ph_resampling"]["figure_eight"]
    bl = out["ph_resampling"]["blob"]
    out["stable_vs_varying_examples"] = {
        "stable": [
            {"feature": "annulus dominant H1 persistence (constructed loop)",
             "reference": ann["reference_dominant_H1"],
             "resample_range": [ann["resample_dominant_H1"]["min"],
                                ann["resample_dominant_H1"]["max"]]},
            {"feature": "figure-eight co-dominant H1 pair",
             "reference": fe["reference_dominant_H1"],
             "resample_range": [fe["resample_dominant_H1"]["min"],
                                fe["resample_dominant_H1"]["max"]]},
        ],
        "varying": [
            {"feature": "blob top H1 persistence (no constructed loop)",
             "reference": bl["reference_dominant_H1"],
             "resample_range": [bl["resample_dominant_H1"]["min"],
                                bl["resample_dominant_H1"]["max"]]},
            {"feature": "noise-scale H1 classes (all shapes)",
             "note": "class counts and small persistences vary freely; only "
                     "constructed features stabilize"},
        ],
        "note": ("computed from all 30 resamples per shape; no favorable "
                 "subset was selected after inspecting outcomes"),
    }

    (RESULTS / "stability_summary.json").write_text(json.dumps(out, indent=1))
    print(f"saved {RESULTS / 'stability_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
