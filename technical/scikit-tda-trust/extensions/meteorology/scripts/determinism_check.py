#!/usr/bin/env python3
"""Extension A determinism check — re-run the deterministic pipeline stages
and verify every output is structurally identical.

Comparison semantics (baseline convention: wall-clock timings are the only
environment-dependent outputs):
  - JSON results: compared after removing the known-volatile fields
    (created_utc timestamps and *_time_s wall-clock timings).
  - NPZ / NPY: exact byte comparison.
  - PNG figures: exact byte comparison (pixel-identical).
  - CSV outputs: exact byte comparison.

Usage: python extensions/meteorology/scripts/determinism_check.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXT.parents[1]
RESULTS = EXT / "results"
PROC = EXT / "data_provenance" / "processed"
FIGS = EXT / "figures"

VOLATILE_KEYS = {"created_utc", "time_s", "ripser_time_s", "embedding_time_s"}


def strip_volatile(obj):
    if isinstance(obj, dict):
        return {k: strip_volatile(v) for k, v in obj.items() if k not in VOLATILE_KEYS}
    if isinstance(obj, list):
        return [strip_volatile(v) for v in obj]
    return obj


def structural_hash(path: Path) -> str:
    h = hashlib.sha256()
    if path.suffix == ".json":
        data = strip_volatile(json.loads(path.read_text()))
        h.update(json.dumps(data, sort_keys=True).encode())
    else:
        h.update(path.read_bytes())
    return h.hexdigest()


def snapshot() -> dict:
    snap = {}
    for base in (RESULTS, PROC, FIGS):
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix in (".json", ".npz", ".npy", ".png", ".csv"):
                snap[str(p.relative_to(EXT))] = structural_hash(p)
    return snap


def main() -> int:
    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = Path(sys.executable)  # Stage-3 fallback: run under the
        # interpreter that launched the check if the in-repo venv is absent.
    before = snapshot()

    for script in ("preprocess_weather.py", "run_weather_analysis.py",
                   "seasonality_check.py", "render_weather_figures.py"):
        r = subprocess.run([str(venv_python), str(EXT / "scripts" / script)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"RE-RUN FAILED: {script}\n{r.stdout}\n{r.stderr}")
            return 1

    after = snapshot()
    if before == after:
        print(f"DETERMINISM CHECK PASSED: {len(after)} output files structurally "
              f"identical after full re-run (JSON volatile fields: "
              f"{sorted(VOLATILE_KEYS)}; figures pixel-identical).")
        return 0

    print("DETERMINISM CHECK FAILED — differences:")
    keys = set(before) | set(after)
    for k in sorted(keys):
        if before.get(k) != after.get(k):
            print(f"  {k}: {before.get(k, 'MISSING')} -> {after.get(k, 'MISSING')}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
