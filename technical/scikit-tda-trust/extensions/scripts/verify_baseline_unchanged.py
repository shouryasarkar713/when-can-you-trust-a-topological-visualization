#!/usr/bin/env python3
"""Verify the baseline preservation contract: every file recorded in
extensions/BASELINE_MANIFEST.json that is part of this repository must be byte-identical.

Files that the manifest lists but that are intentionally NOT distributed (earlier course
deliverables) are declared in extensions/BASELINE_RELEASE_EXCLUSIONS.json. They are reported
separately and are never silently ignored: an excluded file that unexpectedly exists must still
match its hash, and a file missing without a declared exclusion is a violation.

Usage: python extensions/scripts/verify_baseline_unchanged.py
Exit status: 0 = verified, 1 = violation (changed or undeclared-missing file).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "extensions" / "BASELINE_MANIFEST.json"
EXCLUSIONS = REPO_ROOT / "extensions" / "BASELINE_RELEASE_EXCLUSIONS.json"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    excluded = {}
    if EXCLUSIONS.exists():
        ex = json.loads(EXCLUSIONS.read_text(encoding="utf-8"))
        excluded = {e["path"]: e for e in ex["excluded"]}
    changed, missing, not_distributed, verified = [], [], [], 0
    for entry in man["files"]:
        p = REPO_ROOT / entry["path"]
        if not p.exists():
            (not_distributed if entry["path"] in excluded else missing).append(entry["path"])
            continue
        if sha256_file(p) != entry["sha256"]:
            changed.append(entry["path"])
        else:
            verified += 1
    n = len(man["files"])
    unknown = [k for k in excluded if k not in {e["path"] for e in man["files"]}]
    if not changed and not missing and not unknown:
        msg = f"BASELINE PRESERVATION VERIFIED: {verified}/{n} manifest files present and byte-identical"
        if not_distributed:
            msg += f"; {len(not_distributed)} intentionally not distributed (declared in {EXCLUSIONS.name})"
        print(msg + ".")
        return 0
    print("BASELINE PRESERVATION VIOLATION:")
    for p in missing:
        print(f"  MISSING (no declared exclusion): {p}")
    for p in changed:
        print(f"  CHANGED: {p}")
    for p in unknown:
        print(f"  EXCLUSION NOT IN MANIFEST: {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
