#!/usr/bin/env python3
"""Extension A step 1 — fetch GSOD station-years + ONI index with provenance.

Downloads the pre-specified station-years from the official NOAA NCEI GSOD
access directory and (optionally) the ONI index from NOAA PSL, then writes a
provenance record: source URLs, retrieval timestamps (UTC), HTTP status,
byte sizes, SHA-256 checksums, observed row counts, date coverage, and
schema observations. Raw files are stored under data_provenance/raw/ and are
never modified afterwards; processed data lives elsewhere.

Determinism note: this script performs NETWORK I/O; it is the only
non-deterministic step in the extension. Everything downstream is
deterministic given the raw files. Re-running with --skip-download-existing
makes it idempotent.

Usage:
  python extensions/meteorology/scripts/fetch_gsod.py [--skip-download-existing]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

EXT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXT_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402  (baseline pin pyyaml==6.0.3)

RAW_DIR = EXT_ROOT / "data_provenance" / "raw"
PROV_PATH = EXT_ROOT / "data_provenance" / "provenance.json"

USER_AGENT = "scikit-tda-trust-extension/1.0 (research use; course project)"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, skip_existing: bool) -> dict:
    """Download one file, return provenance record."""
    record = {"url": url}
    if dest.exists() and skip_existing:
        record["downloaded_this_run"] = False
    else:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        t0 = datetime.now(timezone.utc)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
                record["http_status"] = int(resp.status)
        except urllib.error.HTTPError as e:
            record["http_status"] = int(e.code)
            record["error"] = str(e)
            return record
        t1 = datetime.now(timezone.utc)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        record["retrieved_utc"] = t0.strftime("%Y-%m-%dT%H:%M:%SZ")
        record["download_duration_s"] = round((t1 - t0).total_seconds(), 2)
        record["downloaded_this_run"] = True
    record["bytes"] = dest.stat().st_size
    record["sha256"] = sha256_file(dest)
    return record


def inspect_gsod_csv(path: Path) -> dict:
    """Observed schema + coverage facts for one station-year file."""
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        cols = list(reader.fieldnames or [])
        rows = list(reader)
    dates = sorted(r["DATE"] for r in rows)
    station_ids = sorted({r["STATION"] for r in rows})
    lats = sorted({r["LATITUDE"] for r in rows})
    lons = sorted({r["LONGITUDE"] for r in rows})
    names = sorted({r["NAME"] for r in rows})
    return {
        "columns": cols,
        "n_rows": len(rows),
        "station_ids": station_ids,
        "latitudes": lats,
        "longitudes": lons,
        "names": names,
        "first_date": dates[0] if dates else None,
        "last_date": dates[-1] if dates else None,
        "n_unique_dates": len(set(dates)),
        "n_duplicate_date_rows": len(dates) - len(set(dates)),
        "sentinels_observed": {
            f: sum(1 for r in rows if r.get(f, "").strip() in ("9999.9", "999.9", "99.99"))
            for f in ("TEMP", "DEWP", "SLP", "STP", "VISIB", "WDSP", "MXSPD", "GUST", "PRCP", "SNDP")
        },
    }


def inspect_oni(path: Path, sentinel: float) -> dict:
    """Observed facts for the PSL ONI fixed-width file."""
    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    # Header lines are those not starting with a 4-digit year.
    data_lines = [ln for ln in lines if ln.split()[0][:4].isdigit()]
    years = sorted({int(ln.split()[0]) for ln in data_lines})
    n_values = 0
    n_missing = 0
    for ln in data_lines:
        for tok in ln.split()[1:]:
            try:
                v = float(tok)
            except ValueError:
                continue
            n_values += 1
            if abs(v - sentinel) < 1e-6:
                n_missing += 1
    return {
        "n_header_or_note_lines": len(lines) - len(data_lines),
        "n_data_lines": len(data_lines),
        "years": [years[0], years[-1]] if years else [],
        "n_monthly_values": n_values,
        "n_missing_sentinel_values": n_missing,
        "text_head": lines[:2],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-download-existing", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load((EXT_ROOT / "configs" / "weather.yaml").read_text())
    station = cfg["station"]["id"]
    years = cfg["source"]["years"]

    provenance = {
        "provenance_version": 1,
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset": "NOAA Global Summary of the Day (GSOD), access directory",
        "station": cfg["station"],
        "readme_url": cfg["source"]["readme_url"],
        "requested_range": cfg["source"]["requested_range"],
        "files": {},
        "notes": [
            "Raw files under data_provenance/raw/ are immutable inputs; the "
            "deterministic preprocessing step never writes here.",
            "Units observed in the fetched schema (2026-10-22): TEMP/DEWP/MAX/MIN "
            "degrees Fahrenheit, SLP/STP millibars, WDSP/MXSPD/GUST knots, "
            "VISIB miles, PRCP inches, SNDP inches; missing sentinels 9999.9 "
            "(temp/pressure fields), 999.9 (wind/visibility/snow), 99.99 "
            "(precipitation). Sentinels confirmed present in the fetched data "
            "(see per-file sentinels_observed).",
            "GSOD summary data are intended for free and unrestricted use in "
            "research and education (archive readme; WMO Resolution 40 "
            "context).",
        ],
    }

    total_rows = 0
    for year in years:
        url = cfg["source"]["url_template"].format(year=year, station=station)
        dest = RAW_DIR / f"gsod_{station}_{year}.csv"
        rec = fetch(url, dest, args.skip_download_existing)
        if dest.exists():
            rec["inspection"] = inspect_gsod_csv(dest)
            total_rows += rec["inspection"]["n_rows"]
        provenance["files"][f"gsod_{station}_{year}.csv"] = rec

    # ONI (descriptive context only)
    if cfg["oni"]["enabled"]:
        url = cfg["oni"]["url"]
        dest = RAW_DIR / "oni.data"
        rec = fetch(url, dest, args.skip_download_existing)
        if dest.exists():
            rec["inspection"] = inspect_oni(dest, float(cfg["oni"]["missing_sentinel"]))
            rec["role"] = (
                "DESCRIPTIVE CONTEXT ONLY — no ENSO hypothesis test; see "
                "power_statement in configs/weather.yaml"
            )
        provenance["files"]["oni.data"] = rec

    provenance["total_gsod_rows_observed"] = total_rows
    provenance["expected_total_rows"] = sum(cfg["schema"]["expected_rows_per_year"].values())

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROV_PATH.write_text(json.dumps(provenance, indent=2) + "\n")

    ok = True
    for fname, rec in provenance["files"].items():
        status = rec.get("http_status", "cached")
        print(f"{fname}: {status}, {rec.get('bytes', '?')} bytes")
        insp = rec.get("inspection", {})
        if "n_rows" in insp:
            dup = insp["n_duplicate_date_rows"]
            print(f"  rows={insp['n_rows']} unique_dates={insp['n_unique_dates']} "
                  f"dup_rows={dup} range={insp['first_date']}..{insp['last_date']}")
            if dup:
                ok = False
    print(f"Total GSOD rows: {total_rows} (expected {provenance['expected_total_rows']})")
    if total_rows != provenance["expected_total_rows"]:
        print("WARNING: observed row count differs from expected; investigate before preprocessing.")
        ok = False
    print(f"Provenance written: {PROV_PATH}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
