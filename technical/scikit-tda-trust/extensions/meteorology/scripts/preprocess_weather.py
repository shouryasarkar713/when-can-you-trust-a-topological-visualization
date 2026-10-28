#!/usr/bin/env python3
"""Extension A step 2 — deterministic preprocessing of the fetched GSOD raw files.

Pipeline (fully deterministic given the immutable raw files):
  1. Load + concatenate the six station-year CSVs.
  2. Validate: schema columns, station identity, per-year row counts, date
     uniqueness / calendar completeness / coverage.
  3. Sentinel -> NaN (documented per-field sentinels), then unit conversions.
  4. Missingness report (per field, with longest consecutive runs).
  5. Primary analysis cloud: TEMP/DEWP/SLP, drop days with any missing
     primary feature (no imputation), z-score. Sensitivity cloud:
     +WDSP (Rev2 spec), documented day drops.
  6. Seasonal PH series: TEMP (degC, z-scored), full date range.
  7. ONI monthly values -> per-day descriptive phase labels (context only).
  8. Save: cleaned CSV, analysis NPZ, preprocessing report JSON (+ SHA-256
     checksums of every output).

Writes ONLY under extensions/meteorology/{results,data_provenance}/processed.
Usage: python extensions/meteorology/scripts/preprocess_weather.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

EXT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXT_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(EXT_ROOT / "wx"))

from weather_lib import (  # noqa: E402
    CONVERTED_COLUMNS,
    METEOROLOGICAL_SEASON,
    SENTINELS,
    UNIT_CONVERSIONS,
    missingness_report,
    oni_phase,
    parse_gsod_value,
    parse_oni,
    convert_units,
    validate_dates,
)

RAW_DIR = EXT_ROOT / "data_provenance" / "raw"
PROC_DIR = EXT_ROOT / "data_provenance" / "processed"
RESULTS_DIR = EXT_ROOT / "results"
NUMERIC_FIELDS = ["TEMP", "DEWP", "SLP", "STP", "VISIB", "WDSP", "MXSPD",
                  "GUST", "MAX", "MIN", "PRCP", "SNDP"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_raw(years: list[int], station: str) -> list[dict]:
    rows = []
    for y in years:
        path = RAW_DIR / f"gsod_{station}_{y}.csv"
        with open(path, newline="") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                rows.append(r)
    return rows


def main() -> int:
    cfg = yaml.safe_load((EXT_ROOT / "configs" / "weather.yaml").read_text())
    station = cfg["station"]["id"]
    years = cfg["source"]["years"]
    prov = json.loads((EXT_ROOT / "data_provenance" / "provenance.json").read_text())

    report: dict = {"step": "preprocess_weather", "deterministic": True,
                    "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "inputs": {}}

    # ---- 1. load
    rows = load_raw(years, station)
    report["n_raw_rows"] = len(rows)

    # ---- 2. validate
    schema_cols = list(rows[0].keys())
    report["schema"] = {
        "observed_columns": schema_cols,
        "expected_numeric_fields_present": all(f in schema_cols for f in NUMERIC_FIELDS),
    }
    station_ids = sorted({r["STATION"] for r in rows})
    names = sorted({r["NAME"].strip() for r in rows})
    lats = sorted({r["LATITUDE"] for r in rows})
    report["station_identity"] = {
        "station_ids": station_ids, "names": names, "latitudes": lats,
        "matches_config": station_ids == [station],
    }
    per_year_counts = {}
    for y in years:
        yc = sum(1 for r in rows if r["DATE"].startswith(str(y)))
        per_year_counts[str(y)] = {
            "observed": yc, "expected": cfg["schema"]["expected_rows_per_year"][y]}
    report["per_year_row_counts"] = per_year_counts

    dates = [r["DATE"] for r in rows]
    date_facts = validate_dates(dates, "2019-01-01", "2024-12-31")
    report["date_validation"] = date_facts

    problems = []
    if not report["schema"]["expected_numeric_fields_present"]:
        problems.append("schema columns missing numeric fields")
    if not report["station_identity"]["matches_config"]:
        problems.append(f"unexpected station ids: {station_ids}")
    for y, c in per_year_counts.items():
        if c["observed"] != c["expected"]:
            problems.append(f"row count mismatch {y}: {c['observed']} != {c['expected']}")
    if not date_facts["ok"]:
        problems.append(f"date validation failed: {date_facts}")
    if problems:
        report["status"] = "FAILED_VALIDATION"
        report["problems"] = problems
        (RESULTS_DIR / "weather_preprocessing_report.json").write_text(json.dumps(report, indent=2))
        print("VALIDATION FAILED:", problems)
        return 1

    # ---- 3. sentinels -> NaN + unit conversion
    frame = {"DATE": np.array(dates), "STATION": np.array([r["STATION"] for r in rows])}
    sentinel_hits = {f: 0 for f in NUMERIC_FIELDS}
    for f in NUMERIC_FIELDS:
        vals = np.empty(len(rows))
        for i, r in enumerate(rows):
            v = parse_gsod_value(r[f], f)
            if not np.isfinite(v):
                sentinel_hits[f] += 1
            vals[i] = convert_units(f, v)
        frame[f] = vals
    report["sentinel_hits_per_field"] = sentinel_hits
    report["unit_conversions_applied"] = {f: UNIT_CONVERSIONS[f][0] for f in NUMERIC_FIELDS
                                          if f in UNIT_CONVERSIONS}

    # cross-check sentinel counts against the provenance inspection
    prov_sent = {}
    for fname, rec in prov["files"].items():
        if "sentinels_observed" in rec.get("inspection", {}):
            for k, v in rec["inspection"]["sentinels_observed"].items():
                prov_sent[k] = prov_sent.get(k, 0) + v
    diffs = {f: {"preprocessing_exact": sentinel_hits[f], "provenance_string_match": prov_sent.get(f, 0)}
             for f in NUMERIC_FIELDS if sentinel_hits[f] != prov_sent.get(f, 0)}
    report["sentinel_crosscheck_vs_provenance"] = {
        "preprocessing": sentinel_hits, "provenance_inspection": prov_sent,
        "diffs": diffs,
        "match": not diffs,
        "diff_explanation": (
            "The provenance inspector string-matches ANY sentinel-family value "
            "(9999.9/999.9/99.99) in any field; the preprocessing applies each "
            "field's DOCUMENTED sentinel only. Diffs therefore mark values from "
            "another field's sentinel family — see data_quality_observations."
        ) if diffs else None,
    }

    # ---- 3b. data-quality observations (explicit, not silent)
    report["data_quality_observations"] = {
        "STP_excluded": {
            "finding": ("STP (station pressure) is systematically corrupted in "
                        "this station's files: 94.8% of values are below 900 hPa "
                        "(median 12.4 hPa) at a station whose elevation (42.7 m) "
                        "implies ~1008 hPa; only 5.2% lie in the physically "
                        "plausible 950-1050 hPa range."),
            "decision": "STP is EXCLUDED from every analysis; values are kept in "
                        "the cleaned CSV for transparency only.",
        },
        "SLP_ambiguous_2020_12_01": {
            "finding": ("SLP on 2020-12-01 reads 999.9 — the wind/visibility "
                        "sentinel value, not the documented SLP sentinel "
                        "(9999.9). Neighboring days: 1010.4 (Nov 30), 1011.9 "
                        "(Dec 2); a ~10 mb dip between them is consistent with a "
                        "passing winter storm, so the value is also "
                        "meteorologically plausible as a real reading."),
            "decision": ("Treated as VALID data per the official schema (only "
                         "9999.9 is the documented SLP sentinel). Impact if the "
                         "alternative reading were taken: the primary cloud "
                         "would lose 1 of 2188 days (0.046%)."),
        },
    }

    # ---- 4. missingness
    report["missingness"] = missingness_report(frame, NUMERIC_FIELDS)

    # ---- 5. primary + sensitivity clouds
    primary = cfg["preprocessing"]["primary_features"]
    sens = cfg["preprocessing"]["sensitivity_features"]
    prim_nan = np.zeros(len(rows), dtype=bool)
    for f in primary:
        prim_nan |= ~np.isfinite(frame[f])
    sens_nan = np.zeros(len(rows), dtype=bool)
    for f in sens:
        sens_nan |= ~np.isfinite(frame[f])

    kept_prim = ~prim_nan
    kept_sens = ~sens_nan
    Xp_raw = np.column_stack([frame[f][kept_prim] for f in primary])
    Xs_raw = np.column_stack([frame[f][kept_sens] for f in sens])
    mu_p, sd_p = Xp_raw.mean(0), Xp_raw.std(0)
    Xp = (Xp_raw - mu_p) / sd_p
    mu_s, sd_s = Xs_raw.mean(0), Xs_raw.std(0)
    Xs = (Xs_raw - mu_s) / sd_s

    report["primary_cloud"] = {
        "features": primary,
        "n_days_kept": int(kept_prim.sum()),
        "n_days_dropped": int(prim_nan.sum()),
        "fraction_dropped": round(float(prim_nan.mean()), 5),
        "dropped_dates": [d for d, k in zip(dates, prim_nan) if k],
        "scaling_means_raw_units": [round(float(m), 3) for m in mu_p],
        "scaling_sds_raw_units": [round(float(s), 3) for s in sd_p],
    }
    report["sensitivity_cloud"] = {
        "features": sens,
        "n_days_kept": int(kept_sens.sum()),
        "n_days_dropped": int(sens_nan.sum()),
        "fraction_dropped": round(float(sens_nan.mean()), 5),
        "dropped_winters_note": "includes all of Jan-Feb 2019 (59 consecutive days)",
        "season_counts_kept": {},
    }
    months_kept = [int(d[5:7]) for d, k in zip(dates, kept_sens) if k]
    for m in months_kept:
        s = METEOROLOGICAL_SEASON[m]
        report["sensitivity_cloud"]["season_counts_kept"][s] = \
            report["sensitivity_cloud"]["season_counts_kept"].get(s, 0) + 1
    months_all = [int(d[5:7]) for d in dates]
    season_counts_all = {}
    for m in months_all:
        s = METEOROLOGICAL_SEASON[m]
        season_counts_all[s] = season_counts_all.get(s, 0) + 1
    report["sensitivity_cloud"]["season_counts_full"] = season_counts_all

    # ---- 6. seasonal PH series (TEMP, complete)
    temp_c = frame["TEMP"]  # already degC
    temp_z = (temp_c - temp_c.mean()) / temp_c.std()
    report["ph_series"] = {
        "feature": "TEMP", "units_after_conversion": "degC then z-score",
        "n_days": int(len(temp_z)), "n_missing": int((~np.isfinite(temp_c)).sum()),
        "date_range": [dates[0], dates[-1]],
    }

    # ---- 7. seasons + ONI
    seasons = np.array([METEOROLOGICAL_SEASON[int(d[5:7])] for d in dates])
    oni_info = {"enabled": False}
    oni_values_day = np.full(len(dates), np.nan)
    oni_phase_day = np.array(["Unknown"] * len(dates), dtype=object)
    if cfg["oni"]["enabled"]:
        oni_text = (RAW_DIR / "oni.data").read_text()
        parsed = parse_oni(oni_text, float(cfg["oni"]["missing_sentinel"]))
        el = float(cfg["oni"]["el_nino_threshold"])
        la = float(cfg["oni"]["la_nina_threshold"])
        n_matched = 0
        for i, d in enumerate(dates):
            y, m = int(d[:4]), int(d[5:7])
            if (y, m) in parsed["values"]:
                oni_values_day[i] = parsed["values"][(y, m)]
                oni_phase_day[i] = oni_phase(parsed["values"][(y, m)], el, la)
                n_matched += 1
        oni_info = {
            "enabled": True, "role": "DESCRIPTIVE CONTEXT ONLY (no hypothesis test)",
            "power_statement": " ".join(cfg["oni"]["power_statement"].split()),
            "oni_years": parsed["years"], "n_days_matched": n_matched,
            "phase_counts": {p: int((oni_phase_day == p).sum())
                             for p in ("ElNino", "Neutral", "LaNina", "Unknown")},
            "note": "Phase labels use the ONI value with CPC +/-0.5 thresholds, "
                    "not the 5-consecutive-season episode definition.",
        }
    report["oni"] = oni_info
    report["season_counts"] = {s: int((seasons == s).sum())
                               for s in ("DJF", "MAM", "JJA", "SON")}

    # ---- 8. save outputs
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # cleaned CSV (all converted fields, NaN for missing)
    cleaned_path = PROC_DIR / "gsod_72505394728_2019-2024_clean.csv"
    with open(cleaned_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(CONVERTED_COLUMNS)
        for i in range(len(rows)):
            r = rows[i]
            out = [r["STATION"], r["DATE"], r["LATITUDE"], r["LONGITUDE"],
                   r["ELEVATION"], r["NAME"].strip()]
            for f in NUMERIC_FIELDS:
                v = frame[f][i]
                out.append("" if not np.isfinite(v) else f"{v:.3f}")
            w.writerow(out)

    # analysis NPZ
    npz_path = PROC_DIR / "weather_analysis.npz"
    np.savez_compressed(
        npz_path,
        dates=np.array(dates),
        seasons=seasons,
        oni_value=oni_values_day,
        oni_phase=oni_phase_day,
        X_primary=Xp, primary_features=np.array(primary),
        primary_dates=np.array([d for d, k in zip(dates, kept_prim) if k]),
        primary_seasons=seasons[kept_prim],
        primary_oni_phase=oni_phase_day[kept_prim],
        X_sensitivity=Xs, sensitivity_features=np.array(sens),
        sensitivity_dates=np.array([d for d, k in zip(dates, kept_sens) if k]),
        sensitivity_seasons=seasons[kept_sens],
        temp_c=temp_c, temp_z=temp_z,
    )

    report["outputs"] = {
        "cleaned_csv": {"path": str(cleaned_path.relative_to(REPO_ROOT)),
                        "sha256": sha256_file(cleaned_path),
                        "bytes": cleaned_path.stat().st_size},
        "analysis_npz": {"path": str(npz_path.relative_to(REPO_ROOT)),
                         "sha256": sha256_file(npz_path),
                         "bytes": npz_path.stat().st_size},
    }
    report["status"] = "OK"
    (RESULTS_DIR / "weather_preprocessing_report.json").write_text(json.dumps(report, indent=2) + "\n")

    # console summary
    print(f"rows={len(rows)}  primary_cloud={Xp.shape} (dropped {int(prim_nan.sum())})  "
          f"sensitivity_cloud={Xs.shape} (dropped {int(sens_nan.sum())})")
    print(f"PH series TEMP: {len(temp_z)} days, missing={int((~np.isfinite(temp_c)).sum())}")
    print(f"ONI matched days: {oni_info.get('n_days_matched', 0)}; phases: {oni_info.get('phase_counts')}")
    print(f"Outputs: {cleaned_path.name}, {npz_path.name}")
    print(f"Report: {RESULTS_DIR / 'weather_preprocessing_report.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
