#!/usr/bin/env python3
"""Verify the baseline preservation contract: every file recorded in
extensions/BASELINE_MANIFEST.json must be byte-identical.

Usage: python extensions/scripts/verify_baseline_unchanged.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "extensions" / "BASELINE_MANIFEST.json"


def main() -> int:
    man = json.loads(MANIFEST.read_text())
    changed, missing = [], []
    for entry in man["files"]:
        p = REPO_ROOT / entry["path"]
        if not p.exists():
            missing.append(entry["path"])
            continue
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != entry["sha256"]:
            changed.append(entry["path"])

    n = len(man["files"])
    if not changed and not missing:
        print(f"BASELINE PRESERVATION VERIFIED: {n}/{n} files byte-identical "
              f"to the manifest.")
        return 0
    print("BASELINE PRESERVATION VIOLATION:")
    for p in missing:
        print(f"  MISSING: {p}")
    for p in changed:
        print(f"  CHANGED: {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
