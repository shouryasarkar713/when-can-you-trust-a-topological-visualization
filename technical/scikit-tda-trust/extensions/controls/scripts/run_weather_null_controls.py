#!/usr/bin/env python3
"""Extension D2 — matched null controls for the weather sliding-window embedding.

Controls (same embedding code, same six (tau, d) configs, same ripser call as Extension A):
  raw       the z-scored daily TEMP series (re-computed here as an internal cross-check)
  anomaly   TEMP minus a least-squares annual climatology (intercept + n_harmonics sin/cos pairs
            of period 365.25 d), re-z-scored
  shuffle   random permutations of the z-scored TEMP series (reference config only)
Reports dominant H1 persistence and r_1 = p1/p2 for each. Numbers only.

Usage: python extensions/controls/scripts/run_weather_null_controls.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

EXT = Path(__file__).resolve().parents[1]
REPO = EXT.parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "extensions" / "meteorology" / "wx"))

from src.pipeline import compute_ph  # noqa: E402
from weather_lib import seasonal_ph_diagnostics, sliding_window_embedding  # noqa: E402

NPZ = REPO / "extensions" / "meteorology" / "data_provenance" / "processed" / "weather_analysis.npz"


def zscore(x):
    x = np.asarray(x, float)
    return (x - x.mean()) / x.std()


def annual_climatology_fit(x, period, n_harm):
    t = np.arange(len(x), dtype=float)
    cols = [np.ones_like(t)]
    for h in range(1, n_harm + 1):
        cols += [np.sin(2 * np.pi * h * t / period), np.cos(2 * np.pi * h * t / period)]
    A = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(A, x, rcond=None)
    fit = A @ beta
    return fit, float(1 - np.var(x - fit) / np.var(x))


def run_one(series, tau, d):
    emb = sliding_window_embedding(series, tau, d, stride=1)
    t0 = time.perf_counter()
    ph = compute_ph(emb, maxdim=1)
    diag = seasonal_ph_diagnostics(ph["dgms"])
    return {"tau": tau, "d": d, "n_points": int(emb.shape[0]),
            "H1_classes": diag["H1_classes"],
            "H1_top3_persistence": diag["H1_top3_persistence"],
            "dominant_H1_persistence": diag["dominant_H1_persistence"],
            "gap_ratio_r1": diag["gap_ratio_r1"],
            "ripser_time_s": round(time.perf_counter() - t0, 2)}


def main() -> int:
    cfg = yaml.safe_load((EXT / "configs" / "controls.yaml").read_text())["weather_null_controls"]
    data = np.load(NPZ, allow_pickle=True)
    temp_c = np.asarray(data["temp_c"], float)
    temp_z = zscore(temp_c)
    saved_z = np.asarray(data["temp_z"], float)
    out = {"design": "D2 weather null controls",
           "n_days": int(len(temp_z)),
           "temp_z_matches_saved_array_max_abs": float(np.max(np.abs(temp_z - saved_z))),
           "config": cfg}
    fit, r2 = annual_climatology_fit(temp_z, cfg["annual_period_days"], int(cfg["n_harmonics"]))
    anom = zscore(temp_z - fit)
    out["annual_harmonic_fit_R2"] = round(r2, 5)
    out["raw"], out["anomaly"] = {}, {}
    for c in cfg["configs"]:
        key = f"tau{c['tau']}_d{c['d']}"
        out["raw"][key] = run_one(temp_z, c["tau"], c["d"])
        out["anomaly"][key] = run_one(anom, c["tau"], c["d"])
        print(key, "raw r1", out["raw"][key]["gap_ratio_r1"], "dom", out["raw"][key]["dominant_H1_persistence"],
              "| anomaly r1", out["anomaly"][key]["gap_ratio_r1"], "dom", out["anomaly"][key]["dominant_H1_persistence"],
              flush=True)
    sh = cfg["shuffle"]
    out["shuffle"] = {"config": sh["config"], "n_shuffles": sh["n_shuffles"], "replicates": []}
    for i in range(int(sh["n_shuffles"])):
        rng = np.random.default_rng(int(sh["base_seed"]) + i)
        perm = rng.permutation(len(temp_z))
        res = run_one(temp_z[perm], sh["config"]["tau"], sh["config"]["d"])
        res["seed"] = int(sh["base_seed"]) + i
        out["shuffle"]["replicates"].append(res)
        print("shuffle", i, res["gap_ratio_r1"], res["dominant_H1_persistence"], flush=True)
    r1 = [r["gap_ratio_r1"] for r in out["shuffle"]["replicates"]]
    dom = [r["dominant_H1_persistence"] for r in out["shuffle"]["replicates"]]
    out["shuffle"]["summary"] = {"r1_min_max": [min(r1), max(r1)], "dominant_min_max": [min(dom), max(dom)],
                                 "n_with_r1_ge_3": int(sum(1 for v in r1 if v >= 3))}
    (EXT / "results").mkdir(exist_ok=True)
    (EXT / "results" / "weather_null_controls.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
