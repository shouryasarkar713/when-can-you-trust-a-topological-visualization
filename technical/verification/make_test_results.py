#!/usr/bin/env python3
"""Convert a test-run summary (written by scripts/run_all_tests.py) into test_results.json / .md.

    python make_test_results.py --summary RUN_DIR/summary.json --out-dir OUT_DIR

Both paths are explicit: nothing is read from or written to a default location, so a routine run can
never overwrite the reference evidence in technical/verification/reference/. The numbers are copied
from the runner's junit-derived counts and exit codes; nothing is typed by hand.
"""
import argparse
import json
import re
from pathlib import Path


def tidy(text):
    """Drop the machine-specific 'Evidence: <temp path>' tail that verify_env.py prints."""
    return re.sub(r"\s*Evidence:.*$", "", text or "")

ap = argparse.ArgumentParser()
ap.add_argument("--summary", required=True)
ap.add_argument("--out-dir", required=True)
a = ap.parse_args()
summ = json.loads(Path(a.summary).read_text(encoding="utf-8"))
out_dir = Path(a.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)
suites, other = [], []
tp = tf = ts = 0
for st in summ["steps"]:
    if st.get("kind") == "pytest":
        c = st.get("counts") or {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
        passed = c["tests"] - c["failures"] - c["errors"] - c["skipped"]
        suites.append({"dir": st["step"], "result": f"{passed} passed", "passed": passed,
                       "failed": c["failures"] + c["errors"], "skipped": c["skipped"],
                       "exit_code": st["exit_code"], "outcome": st.get("outcome"), "step_result": st["result"]})
        tp += passed
        tf += c["failures"] + c["errors"]
        ts += c["skipped"]
    else:
        other.append({"cmd": st["step"], "exit_code": st["exit_code"], "outcome": st.get("outcome"), "result": tidy(st["result"])})
out = {"run_started_utc": summ["started_utc"], "run_finished_utc": summ["finished_utc"], "python": summ["python"],
       "platform": summ["platform"], "command": "python scripts/run_all_tests.py", "overall": summ["overall"],
       "suites": suites, "total_passed": tp, "total_failed": tf, "total_skipped": ts, "other_checks": other}
(out_dir / "test_results.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
md = [f"# Test and check results\n\nRun: {summ['started_utc']} → {summ['finished_utc']} · Python {summ['python']} · "
      f"{summ['platform']}\n\nCommand: `python scripts/run_all_tests.py` (from `technical/scikit-tda-trust`) — overall "
      f"**{summ['overall']}**\n\n| Suite | Result | Exit code |\n|---|---|---|\n"]
for s in suites:
    md.append(f"| `{s['dir']}` | {s['result']} ({s['failed']} failed, {s['skipped']} skipped) | {s['exit_code']} |\n")
md.append(f"\nTotal: **{tp} passed, {tf} failed, {ts} skipped**.\n\n| Step | Exit code | Result |\n|---|---|---|\n")
for o in other:
    md.append(f"| {o['cmd']} | {o['exit_code']} | {o['result']} |\n")
(out_dir / "test_results.md").write_text("".join(md), encoding="utf-8")
print(out["overall"], tp, tf, ts)
