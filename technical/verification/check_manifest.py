#!/usr/bin/env python3
"""Verify SHA256SUMS.txt: every listed file exists and matches, and no file is unlisted.

    python technical/verification/check_manifest.py [--root REPO_ROOT]

The manifest lists every file of the repository except itself (and VCS/cache directories), in the
form `<sha256>  <relative path>`. Exit status 0 = verified, 1 = mismatch, missing or unlisted file.
"""
import argparse
import hashlib
import sys
from pathlib import Path

SKIP = {".git", "__pycache__", ".pytest_cache"}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    root = Path(ap.parse_args().root).resolve()
    manifest = root / "SHA256SUMS.txt"
    listed = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            listed[rel] = digest
    bad, missing = [], []
    for rel, digest in listed.items():
        p = root / rel
        if not p.is_file():
            missing.append(rel)
        elif sha(p) != digest:
            bad.append(rel)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and not (set(p.relative_to(root).parts) & SKIP) and p.name != "SHA256SUMS.txt"
              and p.suffix != ".pyc"}
    unlisted = sorted(actual - set(listed))
    for rel in bad:
        print("MISMATCH:", rel)
    for rel in missing:
        print("MISSING :", rel)
    for rel in unlisted:
        print("UNLISTED:", rel)
    if bad or missing or unlisted:
        print(f"MANIFEST VIOLATION: {len(bad)} mismatched, {len(missing)} missing, {len(unlisted)} unlisted")
        return 1
    print(f"MANIFEST VERIFIED: {len(listed)} files match SHA256SUMS.txt; no unlisted files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
