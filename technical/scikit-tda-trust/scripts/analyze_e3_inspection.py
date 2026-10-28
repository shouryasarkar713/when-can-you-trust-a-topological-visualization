#!/usr/bin/env python3
"""E3 — validate and summarize the COMPLETED single-observer inspection record.

Reads the authored record (e3_inspection/inspection_record.csv, columns per
e3_inspection/stimulus_manifest.json: record_columns) plus the internal
scoring key, VALIDATES it, and writes a descriptive summary to
results/e3/inspection_summary.{json,md}.

VALIDATION (loud failures — the script never repairs or invents content):
  * exactly one record row per manifest item (all 13 present, none extra)
  * task_id / stimulus_id / question match the manifest
  * expected_property matches the pre-specified key
  * assessment in {clearly_apparent, ambiguous, visually_obscured,
    not_represented}; matches_expected in {yes, no, partial}
  * visible_cues / observer_interpretation / explanation_and_limitation
    non-empty
  * every evidence_files path exists in the repository

SUMMARY (descriptive only, honest labels everywhere):
  * per task x representation: counts of assessment categories and of
    matches_expected — reported as RECORDED INSPECTION JUDGMENTS of a single
    observer, never as measured human accuracy
  * the recorded misleading cues / rendering problems, verbatim
  * the standing limitations (single observer; invested author; possible
    observer bias and retrospective interpretation)

This script contains no approval gate: the participant study was NOT
conducted (constraint change 2026-10-22) and no participant data exist. The
output is labeled a structured task-based inspection by a single observer —
an artifact-readability analysis, never a human-participant study.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent

CATEGORIES = ["clearly_apparent", "ambiguous", "visually_obscured",
              "not_represented"]
MATCH_VALUES = ["yes", "no", "partial"]

LIMITATIONS = [
    "single observer; the observer is the invested author who designed the "
    "datasets and had seen the E1/E2 computational results beforehand",
    "observer bias and retrospective interpretation are possible and "
    "acknowledged; expected properties were pre-specified from construction, "
    "which limits but does not eliminate bias",
    "the evidence concerns the produced artifacts and one observer's reading "
    "of them — NOT how a population of users would interpret them",
    "no timing, no confidence ratings, no inferential statistics; no "
    "participant data exist for this experiment",
    "judgments from different tasks are not comparable (task-specific design)",
]


def die(msg: str) -> None:
    print(f"ERROR [analyze_e3_inspection]: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config",
                    default=str(REPO / "configs" / "e3_readability.yaml"))
    ap.add_argument("--record",
                    default=str(REPO / "e3_inspection" / "inspection_record.csv"))
    args = ap.parse_args()

    with open(args.config) as fh:
        cfg = yaml.safe_load(fh)
    e3_dir = REPO / cfg["paths"]["e3_dir"]
    out_dir = REPO / cfg["paths"]["results_e3"]
    out_dir.mkdir(parents=True, exist_ok=True)
    record_path = Path(args.record)

    if not record_path.exists():
        die(f"inspection record not found: {record_path}. The record is an "
            "AUTHORED document (the completed worksheet); this script only "
            "validates and summarizes it — it never creates observations.")

    manifest = json.loads((e3_dir / "stimulus_manifest.json").read_text())
    if not manifest.get("items"):
        die("stimulus manifest is empty — run scripts/run_e3_readability.py "
            "first.")
    by_sid = {m["stimulus_id"]: m for m in manifest["items"]}
    columns = manifest.get("record_columns")
    if not columns:
        die("manifest lacks record_columns — regenerate the materials.")

    with open(record_path) as fh:
        rows = [r for r in csv.DictReader(
            ln for ln in fh if not ln.startswith("#"))]
    if not rows:
        die("inspection record is empty.")

    # ------------------------------------------------------------- validate
    seen: dict[str, dict] = {}
    for r in rows:
        sid = (r.get("stimulus_id") or "").strip()
        if sid not in by_sid:
            die(f"unknown stimulus_id {sid!r} (not in the manifest)")
        if sid in seen:
            die(f"duplicate record row for {sid}")
        seen[sid] = r

    missing = sorted(set(by_sid) - set(seen))
    if missing:
        die(f"record is incomplete — no row for: {', '.join(missing)} "
            f"(expected {len(by_sid)} rows, found {len(seen)})")

    for sid, r in sorted(seen.items()):
        m = by_sid[sid]
        if (r.get("task_id") or "").strip() != m["task_id"]:
            die(f"task_id mismatch for {sid}: record says {r.get('task_id')!r}, "
                f"manifest says {m['task_id']!r}")
        if " ".join((r.get("question") or "").split()) != \
                " ".join(m["question"].split()):
            die(f"question mismatch for {sid} (record vs manifest)")
        if " ".join((r.get("expected_property") or "").split()) != \
                " ".join(str(m["expected_property"]).split()):
            die(f"expected_property mismatch for {sid}: record says "
                f"{r.get('expected_property')!r}, key says "
                f"{m['expected_property']!r}")
        for field in ("visible_cues", "observer_interpretation",
                      "explanation_and_limitation"):
            if not (r.get(field) or "").strip():
                die(f"{field} is empty for {sid}")
        if (r.get("assessment") or "").strip() not in CATEGORIES:
            die(f"assessment for {sid} must be one of {CATEGORIES}, got "
                f"{r.get('assessment')!r}")
        if (r.get("matches_expected") or "").strip().lower() not in \
                MATCH_VALUES:
            die(f"matches_expected for {sid} must be one of {MATCH_VALUES}, "
                f"got {r.get('matches_expected')!r}")
        ev = (r.get("evidence_files") or "").strip()
        if not ev:
            die(f"evidence_files is empty for {sid}")
        for p in [p.strip() for p in ev.split(";") if p.strip()]:
            if not (REPO / p).exists():
                die(f"evidence file does not exist for {sid}: {p}")

    # -------------------------------------------------------------- summarize
    per_cell: dict[tuple, dict] = defaultdict(
        lambda: {"n": 0, "assessment": Counter(), "matches": Counter(),
                 "items": []})
    misleading: list[dict] = []
    for sid, r in sorted(seen.items()):
        m = by_sid[sid]
        cell = per_cell[(m["task_id"], m["view"])]
        cell["n"] += 1
        cell["assessment"][(r["assessment"] or "").strip()] += 1
        cell["matches"][(r["matches_expected"] or "").strip().lower()] += 1
        cell["items"].append({
            "stimulus_id": sid,
            "assessment": (r["assessment"] or "").strip(),
            "matches_expected": (r["matches_expected"] or "").strip().lower(),
            "observer_interpretation": r["observer_interpretation"].strip(),
            "misleading_cues": (r.get("misleading_cues") or "").strip(),
            "explanation_and_limitation":
                r["explanation_and_limitation"].strip(),
        })
        if (r.get("misleading_cues") or "").strip():
            misleading.append({"stimulus_id": sid, "task_id": m["task_id"],
                               "view": m["view"],
                               "misleading_cues":
                                   r["misleading_cues"].strip()})

    total_assessment = Counter()
    total_matches = Counter()
    for cell in per_cell.values():
        total_assessment.update(cell["assessment"])
        total_matches.update(cell["matches"])

    label = ("structured task-based inspection by a single observer "
             "(pre-specified fallback; participant study NOT conducted)")
    summary = {
        "label": label,
        "n_records": len(seen),
        "counting_rule": (
            "Counts describe RECORDED INSPECTION JUDGMENTS of one observer "
            "against pre-specified expected properties. They are NOT "
            "measured human accuracy, NOT population-level readability, and "
            "NOT statistically significant. Computational metrics cited in "
            "the basis fields (persistences, gap ratios, component counts, "
            "cycle-basis lengths) come from saved results and are separate "
            "from these inspection judgments."),
        "assessment_counts_overall": dict(total_assessment),
        "matches_expected_counts_overall": dict(total_matches),
        "per_task_representation": {
            f"{task}/{view}": {
                "n_records": cell["n"],
                "assessment_counts": dict(cell["assessment"]),
                "matches_expected_counts": dict(cell["matches"]),
                "items": cell["items"],
            } for (task, view), cell in sorted(per_cell.items())
        },
        "recorded_misleading_cues": misleading,
        "limitations": LIMITATIONS,
    }

    out_json = out_dir / "inspection_summary.json"
    out_md = out_dir / "inspection_summary.md"
    out_json.write_text(json.dumps(summary, indent=2))

    lines = [
        "# E3 Inspection Summary — " + label,
        "",
        f"- Inspection records: {len(seen)} (one per stimulus, fixed order "
        "S01..S13; single observer = the project author)",
        "- " + summary["counting_rule"],
        "",
        "| Task | Representation | n | clearly_apparent | ambiguous | "
        "visually_obscured | not_represented | matches: yes/partial/no |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for (task, view), cell in sorted(per_cell.items()):
        a = cell["assessment"]
        lines.append(
            f"| {task} | {view} | {cell['n']} | {a.get('clearly_apparent', 0)} "
            f"| {a.get('ambiguous', 0)} | {a.get('visually_obscured', 0)} "
            f"| {a.get('not_represented', 0)} | "
            f"{cell['matches'].get('yes', 0)}/"
            f"{cell['matches'].get('partial', 0)}/"
            f"{cell['matches'].get('no', 0)} |")
    lines += [
        "",
        f"Overall (single-observer inspection result): "
        f"{dict(total_assessment)}; matches_expected: {dict(total_matches)}.",
        "",
        "## Recorded misleading cues / rendering problems",
    ]
    if misleading:
        for mrec in misleading:
            lines.append(f"- **{mrec['stimulus_id']} ({mrec['task_id']}, "
                         f"{mrec['view']})**: {mrec['misleading_cues']}")
    else:
        lines.append("- none recorded")
    lines += ["", "## Limitations"] + [f"- {l}" for l in LIMITATIONS] + [
        "",
        "Labeled everywhere as a single-observer inspection — never as a "
        "human-participant study.",
    ]
    out_md.write_text("\n".join(lines) + "\n")

    print("\n".join(lines))
    print(f"\nVALIDATION PASSED: {len(seen)}/{len(by_sid)} records complete "
          "and consistent with the manifest.")
    print(f"Wrote {out_json}\nWrote {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
