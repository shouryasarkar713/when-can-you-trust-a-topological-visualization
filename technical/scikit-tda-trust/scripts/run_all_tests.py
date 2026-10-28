#!/usr/bin/env python3
"""Run every required test suite and verification step; exit non-zero on ANY problem.

    python scripts/run_all_tests.py [--log-dir DIR] [--package-root DIR] [--suite PATH ...]
                                    [--allow-intentional-skips] [--browser] [--reference FILE]

A routine run never writes inside the repository or the package:
  * logs, junit reports, summary.json and the evidence-verifier output go to --log-dir, which must be
    new or empty and must lie OUTSIDE the tree being protected (default: a fresh temporary directory
    whose path is printed);
  * the whole protected tree (the package root, or the repository when no package root exists) is
    hashed before and after the run; any added, removed or changed file is reported and fails the run;
  * pytest runs with bytecode and cache writing disabled; verify_env.py (which rewrites results/env/*)
    runs in a temporary copy that is removed in a `finally` block, also on failure.

Steps, in order: every pytest suite (separate invocation each: the suites share module names), the
baseline manifest check, environment verification, evidence verification, optional offline-browser test
(--browser), tree-integrity check, optional comparison with the immutable reference results.

Each pytest suite gets exactly one outcome:
  PASS                 ran, all passed
  FAIL                 ran, at least one test failed
  INTENTIONAL SKIP     ran; some tests skipped with an explicit reason that is not a missing dependency.
                       Counts as a failure unless --allow-intentional-skips is given.
  DEPENDENCY MISSING   a test was skipped (importorskip) or collection failed because a module is not
                       installed: the suite did NOT execute as required; always a failure.
  COULD NOT EXECUTE    pytest crashed, timed out, produced no report, collected zero tests, or hit an
                       internal/usage error; always a failure.
  MISSING SUITE        the suite directory does not exist; always a failure.

The process exit code is 0 only if every required step passed; otherwise 1.
"""
from __future__ import annotations

import argparse
import hashlib
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
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git"}
DEP_MARKERS = ("could not import", "no module named", "modulenotfounderror", "importerror")


def run(cmd, cwd, log: Path, timeout=3600):
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    with open(log, "w", encoding="utf-8", errors="replace") as fh:
        fh.write("$ " + " ".join(map(str, cmd)) + "\n\n")
        fh.flush()
        try:
            return subprocess.run(cmd, cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT, timeout=timeout,
                                  env=env).returncode
        except subprocess.TimeoutExpired:
            fh.write("\nTIMEOUT\n")
            return 124
        except OSError as exc:
            fh.write(f"\nCOULD NOT START: {exc}\n")
            return 127


def snapshot(root: Path) -> dict[str, str]:
    snap = {}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            p = Path(dirpath) / f
            if p.suffix == ".pyc":
                continue
            snap[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return snap


def diff_snapshots(before: dict, after: dict) -> list[str]:
    out = [f"changed: {k}" for k in sorted(before) if k in after and before[k] != after[k]]
    out += [f"removed: {k}" for k in sorted(set(before) - set(after))]
    out += [f"created: {k}" for k in sorted(set(after) - set(before))]
    return out


def read_junit(xml: Path):
    """Return (counts, skip_reasons, error_messages) or None when the report is missing/unreadable."""
    if not xml.exists():
        return None
    try:
        root = ET.parse(xml).getroot()
    except ET.ParseError:
        return None
    s = root if root.tag == "testsuite" else root.find("testsuite")
    if s is None:
        return None
    counts = {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
    skips, errs = [], []
    for tc in s.iter("testcase"):
        for sk in tc.findall("skipped"):
            skips.append((sk.get("message") or sk.text or "").strip())
        for er in list(tc.findall("error")) + list(tc.findall("failure")):
            errs.append(((er.get("message") or "") + " " + (er.text or "")).strip())
    return counts, skips, errs


def classify(rc, junit, allow_skips: bool):
    """Return (outcome, ok, details) for one pytest invocation."""
    if rc == 124:
        return "COULD NOT EXECUTE", False, ["timeout"]
    if junit is None:
        return "COULD NOT EXECUTE", False, [f"no readable junit report (exit code {rc})"]
    c, skips, errs = junit
    if c["tests"] == 0:
        return "COULD NOT EXECUTE", False, ["zero tests collected"]
    dep = [m for m in skips if any(k in m.lower() for k in DEP_MARKERS)]
    dep_err = [m for m in errs if any(k in m.lower() for k in DEP_MARKERS)]
    if dep or dep_err:
        names = sorted({m[:80] for m in dep + dep_err})
        return "DEPENDENCY MISSING", False, ["missing dependency: " + "; ".join(names)]
    if rc in (2, 3, 4, 5):
        return "COULD NOT EXECUTE", False, [f"pytest exit code {rc} (interrupted/internal/usage/no tests)"]
    if c["failures"] or c["errors"] or rc != 0:
        return "FAIL", False, [f"{c['failures']} failed, {c['errors']} errors, exit code {rc}"]
    if c["skipped"]:
        return "INTENTIONAL SKIP", allow_skips, [f"{c['skipped']} skipped: " + "; ".join(sorted(set(skips)))[:200]]
    return "PASS", True, []


def compare_to_reference(summary: dict, ref_path: Path) -> dict:
    """Compare fresh per-suite counts with the immutable reference; never writes to the reference."""
    ref = json.loads(ref_path.read_text(encoding="utf-8"))
    ref_by = {s["dir"]: (s["passed"], s["failed"], s["skipped"]) for s in ref.get("suites", [])}
    rows, differs = [], False
    for st in summary["steps"]:
        if st.get("kind") != "pytest":
            continue
        c = st.get("counts") or {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
        fresh = (c["tests"] - c["failures"] - c["errors"] - c["skipped"], c["failures"] + c["errors"], c["skipped"])
        exp = ref_by.get(st["step"])
        same = exp == fresh
        differs |= not same
        rows.append({"suite": st["step"], "reference": exp, "fresh": fresh, "same": same})
    return {"reference_file": str(ref_path), "reference_run_started_utc": ref.get("run_started_utc"),
            "identical_counts": not differs, "suites": rows, "note": "(passed, failed, skipped)"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", default=None, help="new or empty directory outside the protected tree (default: temp)")
    ap.add_argument("--package-root", default=None)
    ap.add_argument("--repo-root", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--suite", action="append", default=None)
    ap.add_argument("--allow-intentional-skips", action="store_true")
    ap.add_argument("--skip-baseline", action="store_true")
    ap.add_argument("--skip-env", action="store_true")
    ap.add_argument("--skip-evidence", action="store_true")
    ap.add_argument("--browser", action="store_true", help="also run the offline browser test (needs Playwright + Chrome)")
    ap.add_argument("--browser-python", default=sys.executable,
                    help="interpreter with Playwright installed, used for --browser (default: this interpreter)")
    ap.add_argument("--reference", default=None, help="reference test_results.json to compare against (default: package reference)")
    ap.add_argument("--strict-reference", action="store_true", help="fail if fresh counts differ from the reference")
    a = ap.parse_args()

    repo = Path(a.repo_root).resolve() if a.repo_root else REPO
    suites = a.suite or DEFAULT_SUITES
    pkg = Path(a.package_root).resolve() if a.package_root else next(
        (c for c in (repo.parent.parent,) if (c / "technical" / "verification" / "verify_evidence.py").exists()), None)
    protected = pkg if pkg else repo

    made_temp_log = a.log_dir is None
    log_dir = Path(a.log_dir).resolve() if a.log_dir else Path(tempfile.mkdtemp(prefix="sciviz_testrun_"))
    try:
        log_dir.relative_to(protected)
        print(f"REFUSED: --log-dir {log_dir} is inside the protected tree {protected}; "
              f"a normal run must not write there.", file=sys.stderr)
        return 2
    except ValueError:
        pass
    if log_dir.exists() and any(log_dir.iterdir()):
        print(f"REFUSED: --log-dir {log_dir} is not empty; the runner never overwrites existing logs.", file=sys.stderr)
        return 2
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"logs: {log_dir}")

    summary = {"started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "python": sys.version.split()[0], "platform": platform.platform(), "steps": []}
    failed: list[str] = []
    before = snapshot(protected)

    def add(step):
        summary["steps"].append(step)
        if not step.get("ok", True):
            failed.append(step["step"])

    for s in suites:
        sp = Path(s) if Path(s).is_absolute() else repo / s
        name = "pytest_" + s.replace("/", "_").replace("\\", "_").replace(":", "")
        step = {"step": s, "kind": "pytest", "log": name + ".log"}
        if not sp.exists():
            step.update(exit_code=None, outcome="MISSING SUITE", ok=False, result="FAIL: MISSING SUITE (directory not found)")
            add(step)
            continue
        xml = log_dir / (name + ".xml")
        rc = run([sys.executable, "-B", "-m", "pytest", str(sp), "-q", "-p", "no:cacheprovider", "-rs",
                  f"--junitxml={xml}"], repo, log_dir / (name + ".log"))
        junit = read_junit(xml)
        outcome, ok, details = classify(rc, junit, a.allow_intentional_skips)
        step.update(exit_code=rc, counts=junit[0] if junit else None, outcome=outcome, ok=ok,
                    result=("PASS" if outcome == "PASS" else ("OK: " if ok else "FAIL: ") + outcome +
                            (" (" + "; ".join(details) + ")" if details else "")))
        add(step)

    if not a.skip_baseline:
        verifier = repo / "extensions" / "scripts" / "verify_baseline_unchanged.py"
        if verifier.exists():
            rc = run([sys.executable, "-B", str(verifier)], repo, log_dir / "baseline_manifest_after_tests.log")
            ok, res = rc == 0, "PASS" if rc == 0 else "FAIL"
        else:
            rc, ok, res = None, False, "FAIL: baseline verifier script missing"
        add({"step": "baseline manifest (immediately after the suites)", "kind": "script", "exit_code": rc,
             "outcome": "PASS" if ok else "FAIL", "ok": ok, "result": res})

    if not a.skip_env:
        envscript = repo / "scripts" / "verify_env.py"
        if envscript.exists():
            td = tempfile.mkdtemp(prefix="sciviz_envcheck_")
            try:
                cp = Path(td) / "repo"
                shutil.copytree(repo, cp, ignore=shutil.ignore_patterns(*SKIP_DIRS))
                rc = run([sys.executable, "-B", str(cp / "scripts" / "verify_env.py")], cp, log_dir / "verify_env.log")
            finally:
                shutil.rmtree(td, ignore_errors=True)
            txt = (log_dir / "verify_env.log").read_text(encoding="utf-8", errors="replace")
            tail = [l for l in txt.splitlines() if "checks passed" in l]
            ok = rc == 0
            res = ("PASS " + (tail[-1] if tail else "")) if ok else "FAIL"
        else:
            rc, ok, res = None, False, "FAIL: scripts/verify_env.py missing"
        add({"step": "scripts/verify_env.py (temporary copy)", "kind": "script", "exit_code": rc,
             "outcome": "PASS" if ok else "FAIL", "ok": ok, "result": res})

    if not a.skip_evidence:
        ev = pkg / "technical" / "verification" / "verify_evidence.py" if pkg else None
        if ev is None or not ev.exists():
            add({"step": "verify_evidence.py", "kind": "script", "exit_code": None, "outcome": "COULD NOT EXECUTE",
                 "ok": False, "result": "FAIL: COULD NOT EXECUTE (package root with technical/verification not found)"})
        else:
            missing = []
            for mod in ("docx", "pptx", "pymupdf", "numpy"):
                try:
                    __import__(mod)
                except ImportError:
                    missing.append(mod)
            if missing:
                add({"step": "verify_evidence.py", "kind": "script", "exit_code": None, "outcome": "DEPENDENCY MISSING",
                     "ok": False, "result": "FAIL: DEPENDENCY MISSING (" + ", ".join(missing) +
                     "; pip install -r requirements-verify.txt)"})
            else:
                rc = run([sys.executable, "-B", str(ev), "--root", str(pkg), "--out", str(log_dir / "evidence_verification.json")],
                         Path(tempfile.gettempdir()), log_dir / "verify_evidence.log")
                lines = (log_dir / "verify_evidence.log").read_text(encoding="utf-8", errors="replace").splitlines()
                res = [l for l in lines if "checks passed" in l]
                add({"step": "verify_evidence.py", "kind": "script", "exit_code": rc,
                     "outcome": "PASS" if rc == 0 else "FAIL", "ok": rc == 0,
                     "result": ("PASS " + (res[-1] if res else "")) if rc == 0 else "FAIL"})

    if a.browser:
        viewer = repo / "extensions" / "mapper_explorer" / "viewer" / "index.html"
        bt = pkg / "technical" / "verification" / "explorer_offline_test.py" if pkg else None
        if bt is None or not bt.exists() or not viewer.exists():
            add({"step": "explorer offline browser test", "kind": "script", "exit_code": None,
                 "outcome": "COULD NOT EXECUTE", "ok": False, "result": "FAIL: COULD NOT EXECUTE (test script or viewer missing)"})
        else:
            out = log_dir / "explorer_offline_test"
            out.mkdir()
            rc = run([a.browser_python, "-B", str(bt), str(viewer), str(repo), str(out)], Path(tempfile.gettempdir()),
                     log_dir / "explorer_offline_test.log")
            rj = out / "explorer_offline_test.json"
            ok = rc == 0 and rj.exists()
            add({"step": "explorer offline browser test", "kind": "script", "exit_code": rc,
                 "outcome": "PASS" if ok else "COULD NOT EXECUTE" if not rj.exists() else "FAIL", "ok": ok,
                 "result": "PASS" if ok else "FAIL (see explorer_offline_test.log)"})

    after = snapshot(protected)
    changes = diff_snapshots(before, after)
    summary["tree_integrity"] = {"protected_tree": str(protected), "files_hashed": len(after), "changes": changes}
    add({"step": "protected tree unchanged by the run", "kind": "integrity", "exit_code": 0 if not changes else 1,
         "outcome": "PASS" if not changes else "FAIL", "ok": not changes,
         "result": "PASS " + f"({len(after)} files identical before/after)" if not changes else
         "FAIL: " + "; ".join(changes[:8]) + (" ..." if len(changes) > 8 else "")})

    ref_path = Path(a.reference) if a.reference else (
        pkg / "technical" / "verification" / "reference" / "test_results.json" if pkg else None)
    if ref_path is not None and ref_path.exists():
        cmp_ = compare_to_reference(summary, ref_path)
        summary["reference_comparison"] = cmp_
        if a.strict_reference and not cmp_["identical_counts"]:
            add({"step": "counts equal reference results", "kind": "comparison", "exit_code": 1, "outcome": "FAIL",
                 "ok": False, "result": "FAIL: fresh counts differ from the reference"})
    else:
        summary["reference_comparison"] = None

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
        print(f"{st['result'][:100]:<100} {st['step']}")
    rc_cmp = summary.get("reference_comparison")
    if rc_cmp:
        print("reference counts: " + ("identical" if rc_cmp["identical_counts"] else
              "DIFFER (informational; see summary.json reference_comparison)"))
    print(f"OVERALL: {summary['overall']}  (collected {tot['tests']}, failed {tot['failures']}, "
          f"errors {tot['errors']}, skipped {tot['skipped']})  logs: {log_dir}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
