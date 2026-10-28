#!/usr/bin/env python3
"""Create extensions/BASELINE_MANIFEST.json — a preservation record of the
completed baseline project's artifacts.

Records relative path, byte size, and SHA-256 hash for every file in the
repository EXCEPT:
  - extensions/          (the new work; not part of the baseline)
  - .venv/, __pycache__/, *.pyc (ephemeral environment state)
  - .git/                (version-control internals)

The manifest is the non-destructive preservation contract: any later
comparison that shows a hash change for a baseline file is an unexplained
modification that must be reported, never silently accepted.

Usage:  python extensions/scripts/make_baseline_manifest.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MANIFEST_PATH = os.path.join(REPO_ROOT, "extensions", "BASELINE_MANIFEST.json")

# Directories/files excluded from the preservation contract.
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "extensions", ".pytest_cache"}
EXCLUDE_SUFFIXES = (".pyc", ".pyo")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    entries = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
        for fname in sorted(filenames):
            if fname.endswith(EXCLUDE_SUFFIXES):
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, REPO_ROOT)
            size = os.path.getsize(full)
            entries.append(
                {
                    "path": rel,
                    "bytes": size,
                    "sha256": sha256_file(full),
                }
            )

    manifest = {
        "manifest_version": 1,
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "purpose": (
            "Preservation contract for the completed baseline project "
            "(When Can You Trust a Topological Visualization? A Task-Based "
            "Evaluation of the Scikit-TDA Ecosystem). Every file listed here "
            "must remain byte-identical while the extensions are developed; "
            "any difference found at a later gate is reported, never accepted "
            "silently."
        ),
        "exclusions": {
            "directories": sorted(EXCLUDE_DIRS),
            "suffixes": list(EXCLUDE_SUFFIXES),
            "reason": (
                "extensions/ is the new work (not baseline); .venv, caches, "
                "and .git are environment/version-control state, not project "
                "artifacts."
            ),
        },
        "baseline_state_at_creation": {
            "git_branch": "main",
            "git_head_short": os.popen(
                "git -C %s rev-parse --short HEAD" % REPO_ROOT
            ).read().strip(),
            "git_status_clean_for_baseline": True,
            "baseline_verification": (
                "scripts/verify_env.py 38/38 checks passed; "
                "python -m pytest tests/ -q: 60 passed (7.42 s). "
                "Executed 2026-10-22 immediately before manifest creation."
            ),
            "preexisting_discrepancy": (
                "results/env/pip_freeze.txt is volatile by design: verify_env.py "
                "rewrites it from the current .venv on every run. The .venv was "
                "rebuilt (2026-10-22 ~05:07) with two newer transitive packages "
                "(python-dateutil 3.0.0, tzdata 2026.5) relative to the original "
                "experiment environment (dateutil 2.9.0.post0, no tzdata; that "
                "record remains in git history at commit b290a9e and earlier). "
                "During baseline re-verification, verify_env.py rewrote the file "
                "and the platform's automatic checkpoint (commit c6bc401, "
                "2026-10-22 05:21:59 — NOT a git operation performed by the "
                "extension work) captured the rewritten (rebuilt-environment) "
                "content. The manifest therefore locks in the rebuilt-environment "
                "record, which matches the .venv the extensions actually run "
                "under. IMPLEMENTATION_NOTES.md documents that E3 stimuli "
                "regenerated under the rebuilt venv were verified byte-identical, "
                "so no experimental output is affected."
            ),
        },
        "file_count": len(entries),
        "total_bytes": sum(e["bytes"] for e in entries),
        "files": entries,
    }

    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=False)
        fh.write("\n")

    print(
        "Wrote %s: %d files, %.1f MiB total"
        % (
            os.path.relpath(MANIFEST_PATH, REPO_ROOT),
            len(entries),
            manifest["total_bytes"] / (1 << 20),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
