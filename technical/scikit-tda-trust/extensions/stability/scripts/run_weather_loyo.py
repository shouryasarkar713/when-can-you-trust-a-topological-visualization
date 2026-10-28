#!/usr/bin/env python3
"""Stage 4 Part D — weather leave-one-calendar-year-out (LOYO) sensitivity.

SOURCE OF UNCERTAINTY REPRESENTED (chosen before implementation): whether the
seasonal-cycle persistent-hology result depends disproportionately on ONE
observed calendar year of the six available (2019-2024). Individual days are
NOT resampled as if independent — daily temperature is strongly
autocorrelated, and the sliding-window embedding couples days across 210-630
day spans, so day-level resampling or year-block bootstrap concatenation
would create artificial delay windows at block boundaries. LOYO with
gap-safe windows avoids both artifacts.

Method:
  * For each fold year Y: retain all days NOT in Y; re-z-score TEMP within
    the retained days (r_k gap ratios are invariant to this affine
    rescaling; dominant-H1 persistence is reported in retained-series
    z-units and is not compared to full-data z-units without noting it).
  * The retained days form contiguous calendar blocks (1 block when Y is
    2019 or 2024; 2 blocks otherwise). Every sliding-window embedding is
    built STRICTLY WITHIN one block: a window [i, i+(d-1)*tau] never crosses
    the gap created by the omitted year. The number of windows lost to the
    gap is recorded.
  * All six documented seasonal-embedding configurations from
    extensions/meteorology/configs/weather.yaml are run per fold with the
    pinned ripser configuration (maxdim=1); tau=60, d=8 is the pre-specified
    reference.

STATUS OF THE RESULTS: a SENSITIVITY ANALYSIS on six years of single-station
data — not a population-level climate claim, not a formal confidence
interval, and not a hypothesis test. Six years is a limited basis for
inference; each fold trains nothing and selects nothing (no parameter is
retuned after inspecting folds).

RESUMABILITY: each completed fold is checkpointed to
results/_loyo_partial.json; re-invoking the script skips completed folds
(the sandbox limits single-process wall time). When all six folds are done,
the partial file is merged into results/weather_loyo.json and removed.

Usage: python extensions/stability/scripts/run_weather_loyo.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

EXT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXT_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "extensions" / "meteorology" / "wx"))

from ripser import ripser  # noqa: E402
from weather_lib import seasonal_ph_diagnostics, sliding_window_embedding  # noqa: E402

RESULTS = EXT_ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)  # independent-rebuild fix: fresh trees lack the dir
WX_NPZ = REPO_ROOT / "extensions" / "meteorology" / "data_provenance" / "processed" / "weather_analysis.npz"
WX_CFG = REPO_ROOT / "extensions" / "meteorology" / "configs" / "weather.yaml"


def contiguous_blocks(ordinals: np.ndarray) -> list[tuple[int, int]]:
    """[start, end] index pairs of calendar-consecutive day runs."""
    blocks = []
    start = 0
    for i in range(1, len(ordinals)):
        if ordinals[i] != ordinals[i - 1] + 1:
            blocks.append((start, i - 1))
            start = i
    blocks.append((start, len(ordinals) - 1))
    return blocks


def main() -> int:
    cfg = yaml.safe_load((EXT_ROOT / "configs" / "stability.yaml").read_text())
    wx = yaml.safe_load(WX_CFG.read_text())
    sw = wx["seasonal_ph"]
    loyo = cfg["weather_loyo"]
    years = [int(y) for y in loyo["years"]]

    data = np.load(WX_NPZ, allow_pickle=True)
    dates = [str(d) for d in data["dates"]]
    temp_c = np.asarray(data["temp_c"], dtype=float)
    import datetime as dt
    ordinals = np.array([dt.date.fromisoformat(d).toordinal() for d in dates])
    year_arr = np.array([int(d[:4]) for d in dates])

    if len(dates) != len(temp_c):
        raise SystemExit("BUILD ERROR: dates/temp length mismatch in weather NPZ.")

    out: dict = {
        "step": "run_weather_loyo",
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": {
            "years": years,
            "zscore_scope": str(loyo["zscore_scope"]),
            "embedding_gap_rule": str(loyo["embedding_gap_rule"]),
            "sweep": [dict(c) for c in sw["sweep"]],
            "reference_config": f"tau{sw['reference']['tau']}_d{sw['reference']['d']}",
            "ripser_maxdim": int(sw["maxdim"]),
            "series": str(sw["series"]),
        },
        "uncertainty_represented": (
            "Dependence of the seasonal-cycle PH result on a single observed "
            "calendar year. Days are NOT resampled independently (strong "
            "autocorrelation + embedding windows span 210-630 days); no block "
            "bootstrap concatenation is used (it would create artificial "
            "delay windows at block boundaries)."),
        "status_guard": (
            "SENSITIVITY ANALYSIS on six years of single-station data: not a "
            "population-level climate claim, not a formal confidence "
            "interval, not a hypothesis test. No parameter is retuned after "
            "inspecting folds."),
        "interpretation_guard": (
            "A dominant H1 class evidences recurrent quasi-periodic structure "
            "of the embedded series at the studied scale; it is NOT proof of "
            "a simple closed physical climate trajectory (same wording rule "
            "as the meteorology extension)."),
        "folds": {},
    }

    # full-data reference values (saved results, not recomputed)
    full_res = json.loads(
        (REPO_ROOT / "extensions" / "meteorology" / "results" /
         "weather_analysis_results.json").read_text())
    out["full_data_reference"] = {
        k: {"n_points": v["n_points"],
            "dominant_H1_persistence": v["dominant_H1_persistence"],
            "gap_ratio_r1": v["gap_ratio_r1"]}
        for k, v in full_res["seasonal_ph"]["sweep"].items()
    }

    partial_path = RESULTS / "_loyo_partial.json"
    partial = {"folds": {}}
    if partial_path.exists():
        partial = json.loads(partial_path.read_text())
        print(f"resuming — folds done: {sorted(partial['folds'])}")

    for fold_year in years:
        if str(fold_year) in partial["folds"]:
            continue
        retained = year_arr != fold_year
        n_ret = int(retained.sum())
        n_drop = int((~retained).sum())
        # z-score TEMP within the retained days (documented choice)
        vals = temp_c[retained]
        mu, sd = float(vals.mean()), float(vals.std(ddof=0))
        z = (vals - mu) / sd

        r_ord = ordinals[retained]
        blocks = contiguous_blocks(r_ord)
        block_desc = [{
            "start_date": dates[int(np.flatnonzero(retained)[a])],
            "end_date": dates[int(np.flatnonzero(retained)[b])],
            "length_days": int(b - a + 1),
        } for a, b in blocks]

        configs_out = {}
        for conf in sw["sweep"]:
            tau, d = int(conf["tau"]), int(conf["d"])
            span = (d - 1) * tau
            embs = []
            actual_windows = 0
            for a, b in blocks:
                # windows fully inside this block only — never cross the gap
                emb = sliding_window_embedding(z[a:b + 1], tau, d,
                                               stride=int(sw["stride"]))
                embs.append(emb)
                actual_windows += int(emb.shape[0])
            # windows a GAP-FREE retained series of n_ret days would produce,
            # minus the windows actually produced within blocks
            hypothetical_windows = max(0, n_ret - span)
            windows_lost = hypothetical_windows - actual_windows
            emb = np.vstack(embs) if embs else np.empty((0, d))
            if emb.shape[0] == 0:
                configs_out[f"tau{tau}_d{d}"] = {
                    "tau": tau, "d": d, "span_days": span, "status": "EMPTY"}
                continue
            t0 = time.perf_counter()
            dgms = ripser(emb, maxdim=int(sw["maxdim"]))["dgms"]
            t_rip = time.perf_counter() - t0
            diag = seasonal_ph_diagnostics(dgms)
            configs_out[f"tau{tau}_d{d}"] = {
                "tau": tau, "d": d, "span_days": span,
                "span_over_annual_period": round(span / 365.25, 3),
                "n_points": int(emb.shape[0]),
                "n_windows_lost_to_gap": int(windows_lost),
                "status": "OK",
                "ripser_time_s": round(t_rip, 3),
                **diag,
            }
            print(f"  fold -{fold_year} tau={tau} d={d}: n={emb.shape[0]} "
                  f"(lost {windows_lost} to gap) dom={diag['dominant_H1_persistence']} "
                  f"r_1={diag['gap_ratio_r1']} ({t_rip:.1f}s)")

        fold_block = {
            "omitted_year": fold_year,
            "n_retained_days": n_ret,
            "n_omitted_days": n_drop,
            "zscore_retained_mean_c": round(mu, 4),
            "zscore_retained_sd_c": round(sd, 4),
            "n_blocks": len(blocks),
            "blocks": block_desc,
            "configs": configs_out,
        }
        partial["folds"][str(fold_year)] = fold_block
        partial_path.write_text(json.dumps(partial, indent=1))  # checkpoint

    out["folds"] = partial["folds"]
    out["runtime_note"] = ("wall-clock accumulated across resumable "
                           "invocations; per-config ripser timings are "
                           "recorded individually")
    (RESULTS / "weather_loyo.json").write_text(json.dumps(out, indent=1))
    partial_path.unlink()
    print(f"saved {RESULTS / 'weather_loyo.json'} "
          f"({len(out['folds'])} folds)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
