#!/usr/bin/env python3
"""Run every required test suite and verification step; exit non-zero on ANY problem.

    python scripts/run_all_tests.py [--log-dir DIR] [--package-root DIR] [--suite PATH ...]

Steps (in this order):
  1. each pytest suite in its own pytest invocation (the suites' conftest/test packages share
     module names, so they cannot be collected together);
  2. baseline manifest verification, immediately after the suites;
  3. environment verification (scripts/verify_env.py) executed in a TEMPORARY COPY of the
     repository, because that script rewrites results/env/* (baseline files);
  4. evidence verification (technical/verification/verify_evidence.py) when a package root is found.

A run FAILS if any step returns non-zero, a suite directory is missing, a suite collects zero tests,
or any test is skipped (allowed skips: none). Real exit codes, collected counts and log names go
to <log-dir>/summary.json; the process exit code is 1 on failure and 0 only if every step passed.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SUITES = ["tests", "extensions/meteorology/tests", "extensions/mapper_explorer/tests",
                  "extensions/stability/tests", "extensions/controls/tests"]


def run(cmd, cwd, log: Path, timeout=3600):
    with open(log, "w", encoding="utf-8", errors="replace") as fh:
        fh.write("$ " + " ".join(map(str, cmd)) + "\n\n")
        fh.flush()
        try:
            p = subprocess.run(cmd, cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT, timeout=timeout,
                               env={**os.environ, "PYTHONUTF8": "1"})
            return p.returncode
        except subprocess.TimeoutExpired:
            fh.write("\nTIMEOUT\n")
            return 124


def junit_counts(xml: Path):
    if not xml.exists():
        return None
    root = ET.parse(xml).getroot()
    s = root if root.tag == "testsuite" else root.find("testsuite")
    return {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-dir", default=None)
    ap.add_argument("--package-root", default=None)
    ap.add_argument("--suite", action="append", default=None)
    ap.add_argument("--skip-env", action="store_true")
    ap.add_argument("--skip-evidence", action="store_true")
    a = ap.parse_args()
    suites = a.suite or DEFAULT_SUITES
    # package root = the directory that contains submission/ and technical/ (REPO is technical/scikit-tda-trust)
    pkg = Path(a.package_root) if a.package_root else next(
        (c for c in (REPO.parent.parent,) if (c / "technical" / "verification" / "verify_evidence.py").exists()), None)
    log_dir = Path(a.log_dir) if a.log_dir else (
        (pkg / "technical" / "verification" / "logs" / "latest_test_run") if pkg else REPO / ".test_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    summary = {"started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "python": sys.version.split()[0], "platform": platform.platform(), "steps": []}
    failed = []

    for s in suites:
        sp = Path(s) if Path(s).is_absolute() else REPO / s
        name = "pytest_" + s.replace("/", "_").replace("\\", "_").replace(":", "")
        step = {"step": s, "kind": "pytest", "log": name + ".log"}
        if not sp.exists():
            step.update(exit_code=None, result="FAIL: MISSING suite directory")
            failed.append(s)
            summary["steps"].append(step)
            continue
        xml = log_dir / (name + ".xml")
        if xml.exists():
            xml.unlink()
        rc = run([sys.executable, "-m", "pytest", str(sp), "-q", "-p", "no:cacheprovider", "-rs",
                  f"--junitxml={xml}"], REPO, log_dir / (name + ".log"))
        c = junit_counts(xml)
        step.update(exit_code=rc, counts=c)
        problems = []
        if rc != 0:
            problems.append(f"exit code {rc}")
        if c is None:
            problems.append("no junit report")
        else:
            if c["tests"] == 0:
                problems.append("zero tests collected")
            if c["skipped"]:
                problems.append(f"{c['skipped']} skipped")
            if c["failures"] or c["errors"]:
                problems.append(f"{c['failures']} failed, {c['errors']} errors")
        step["result"] = "PASS" if not problems else "FAIL: " + "; ".join(problems)
        if problems:
            failed.append(s)
        summary["steps"].append(step)

    rc = run([sys.executable, str(REPO / "extensions" / "scripts" / "verify_baseline_unchanged.py")], REPO,
             log_dir / "baseline_manifest_after_tests.log")
    summary["steps"].append({"step": "baseline manifest (immediately after the suites)", "kind": "script",
                             "exit_code": rc, "result": "PASS" if rc == 0 else "FAIL"})
    if rc:
        failed.append("baseline manifest")

    if not a.skip_env:
        with tempfile.TemporaryDirectory(prefix="sciviz_envcheck_") as td:
            cp = Path(td) / "repo"
            shutil.copytree(REPO, cp, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".test_logs"))
            rc = run([sys.executable, str(cp / "scripts" / "verify_env.py")], cp, log_dir / "verify_env.log")
        txt = (log_dir / "verify_env.log").read_text(encoding="utf-8", errors="replace")
        tail = [l for l in txt.splitlines() if "checks passed" in l]
        summary["steps"].append({"step": "scripts/verify_env.py (temporary copy)", "kind": "script",
                                 "exit_code": rc, "result": ("PASS " + (tail[-1] if tail else "")) if rc == 0 else "FAIL"})
        if rc:
            failed.append("verify_env")

    if pkg and not a.skip_evidence and (pkg / "technical" / "verification" / "verify_evidence.py").exists():
        missing = []
        for mod in ("docx", "pptx", "pymupdf", "numpy"):
            try:
                __import__(mod)
            except ImportError:
                missing.append(mod)
        if missing:
            print("evidence verification needs: " + ", ".join(missing) + "  ->  pip install -r requirements-verify.txt")
        out_json = log_dir / "evidence_verification.json"
        rc = run([sys.executable, str(pkg / "technical" / "verification" / "verify_evidence.py"), "--root", str(pkg),
                  "--out", str(out_json)], Path(tempfile.gettempdir()), log_dir / "verify_evidence.log")
        lines = (log_dir / "verify_evidence.log").read_text(encoding="utf-8", errors="replace").splitlines()
        res = [l for l in lines if "checks passed" in l]
        summary["steps"].append({"step": "verify_evidence.py", "kind": "script", "exit_code": rc,
                                 "result": ("PASS " + res[-1]) if rc == 0 else "FAIL"})
        if rc:
            failed.append("verify_evidence")
    else:
        summary["steps"].append({"step": "verify_evidence.py", "kind": "script", "exit_code": None,
                                 "result": "NOT RUN (skipped or package root not found)"})

    tot = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for st in summary["steps"]:
        for k, v in (st.get("counts") or {}).items():
            tot[k] += v
    summary["totals"] = tot
    summary["failed_steps"] = failed
    summary["overall"] = "PASS" if not failed else "FAIL"
    summary["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (log_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for st in summary["steps"]:
        print(f"{st['result']:<64} {st['step']}")
    print(f"OVERALL: {summary['overall']}  (collected {tot['tests']}, failed {tot['failures']}, "
          f"errors {tot['errors']}, skipped {tot['skipped']})")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
