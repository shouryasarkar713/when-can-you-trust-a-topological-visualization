"""Tests for the E3 single-observer inspection pipeline.

Covers:
  * the inspection-record analyzer's VALIDATION logic on synthetic records
    in a temp directory (accepts a complete record; rejects incomplete,
    duplicate, wrong-category, and bad-evidence-path records);
  * the REAL repository artifacts, when present: the authored record
    validates against the manifest, the summary exists and is consistent
    with the record, and no participant-study artifacts remain.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
ANALYZER = REPO / "scripts" / "analyze_e3_inspection.py"
E3_DIR = REPO / "e3_inspection"

CATEGORIES = ["clearly_apparent", "ambiguous", "visually_obscured",
              "not_represented"]


def run_analyzer(record: Path, config: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ANALYZER), "--config", str(config),
         "--record", str(record)],
        capture_output=True, text=True, cwd=str(REPO))


@pytest.fixture()
def synthetic_e3_env(tmp_path):
    """A minimal but structurally faithful copy of the E3 layout."""
    e3 = tmp_path / "e3_inspection"
    e3.mkdir()
    (e3 / "stimuli").mkdir()
    manifest_items = []
    for i in range(1, 4):
        sid = f"S{i:02d}"
        (e3 / "stimuli" / f"{sid}.png").write_bytes(b"fake")
        manifest_items.append({
            "stimulus_id": sid, "task_id": "T1", "shape": "x", "view": "diagram",
            "question": f"Q{i}?", "expected_property": "Yes",
            "basis": "construction", "source_files": [],
            "rendering": {"mapper_layout": None, "dpi": 150,
                          "figsize": [4.6, 4.6]},
        })
    (e3 / "stimulus_manifest.json").write_text(json.dumps({
        "record_columns": ["task_id", "stimulus_id", "question",
                           "expected_property", "visible_cues",
                           "observer_interpretation", "assessment",
                           "matches_expected", "misleading_cues",
                           "evidence_files", "explanation_and_limitation"],
        "items": manifest_items}, indent=2))
    (e3 / "scoring_key.csv").write_text("stimulus_id\n")
    # absolute paths so the analyzer (which joins REPO / path) is redirected
    # into the temp tree; pathlib joining an absolute path replaces the base
    cfg = {
        "paths": {"e3_dir": str(e3), "results_e1": str(tmp_path / "e1"),
                  "results_e3": str(tmp_path / "results" / "e3")},
    }
    cfg_path = tmp_path / "e3_cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))
    return tmp_path, e3, manifest_items, cfg_path


def write_record(path: Path, rows: list[dict]) -> None:
    cols = ["task_id", "stimulus_id", "question", "expected_property",
            "visible_cues", "observer_interpretation", "assessment",
            "matches_expected", "misleading_cues", "evidence_files",
            "explanation_and_limitation"]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def good_row(item: dict, **over) -> dict:
    row = {
        "task_id": item["task_id"], "stimulus_id": item["stimulus_id"],
        "question": item["question"],
        "expected_property": item["expected_property"],
        "visible_cues": "cues", "observer_interpretation": "interp",
        "assessment": "clearly_apparent", "matches_expected": "yes",
        "misleading_cues": "", "evidence_files": "e3_inspection/stimuli/"
        f"{item['stimulus_id']}.png",
        "explanation_and_limitation": "note",
    }
    row.update(over)
    return row


def test_analyzer_accepts_complete_record(synthetic_e3_env):
    tmp_path, e3, items, cfg = synthetic_e3_env
    # evidence paths must exist relative to REPO -> use a real repo file
    rows = [good_row(it, evidence_files="README.md") for it in items]
    record = tmp_path / "inspection_record.csv"
    write_record(record, rows)
    res = run_analyzer(record, cfg)
    assert res.returncode == 0, res.stderr + res.stdout
    summary = json.loads((tmp_path / "results" / "e3" /
                          "inspection_summary.json").read_text())
    assert summary["n_records"] == 3
    assert summary["assessment_counts_overall"] == {"clearly_apparent": 3}
    assert "single observer" in summary["label"]
    assert "NOT conducted" in summary["label"]
    # no accuracy-style metric FIELDS anywhere in the summary (the honest
    # disclaimers must and do contain the words "accuracy"/"participant")
    txt = json.dumps(summary).lower()
    for banned_field in ('"fraction_correct"', '"n_correct"',
                         '"median_confidence"', '"accuracy":',
                         '"mean_response"'):
        assert banned_field not in txt
    assert "not measured human accuracy" in txt


def test_analyzer_rejects_incomplete_record(synthetic_e3_env):
    tmp_path, e3, items, cfg = synthetic_e3_env
    rows = [good_row(it, evidence_files="README.md") for it in items[:-1]]
    record = tmp_path / "inspection_record.csv"
    write_record(record, rows)
    res = run_analyzer(record, cfg)
    assert res.returncode != 0
    assert "incomplete" in res.stderr


def test_analyzer_rejects_bad_category_and_match(synthetic_e3_env):
    tmp_path, e3, items, cfg = synthetic_e3_env
    rows = [good_row(it, assessment="kinda_clear",
                     evidence_files="README.md") for it in items]
    record = tmp_path / "inspection_record.csv"
    write_record(record, rows)
    assert run_analyzer(record, cfg).returncode != 0
    rows = [good_row(it, matches_expected="maybe",
                     evidence_files="README.md") for it in items]
    write_record(record, rows)
    assert run_analyzer(record, cfg).returncode != 0


def test_analyzer_rejects_missing_evidence_path(synthetic_e3_env):
    tmp_path, e3, items, cfg = synthetic_e3_env
    rows = [good_row(it, evidence_files="no/such/file.png") for it in items]
    record = tmp_path / "inspection_record.csv"
    write_record(record, rows)
    res = run_analyzer(record, cfg)
    assert res.returncode != 0
    assert "does not exist" in res.stderr


def test_analyzer_rejects_duplicate_rows(synthetic_e3_env):
    tmp_path, e3, items, cfg = synthetic_e3_env
    rows = [good_row(it, evidence_files="README.md") for it in items]
    rows.append(good_row(items[0], evidence_files="README.md"))
    record = tmp_path / "inspection_record.csv"
    write_record(record, rows)
    res = run_analyzer(record, cfg)
    assert res.returncode != 0
    assert "duplicate" in res.stderr


# ------------------------------------------------------- real artifacts

@pytest.mark.skipif(not (E3_DIR / "inspection_record.csv").exists(),
                    reason="real E3 inspection record not present")
class TestRealInspectionArtifacts:
    def test_real_record_validates(self):
        res = run_analyzer(E3_DIR / "inspection_record.csv",
                           REPO / "configs" / "e3_readability.yaml")
        assert res.returncode == 0, res.stderr
        assert "VALIDATION PASSED: 13/13" in res.stdout

    def test_real_record_and_summary_consistent(self):
        summary = json.loads((REPO / "results" / "e3" /
                              "inspection_summary.json").read_text())
        with open(E3_DIR / "inspection_record.csv") as fh:
            rows = [r for r in csv.DictReader(
                ln for ln in fh if not ln.startswith("#"))]
        assert summary["n_records"] == len(rows) == 13
        from collections import Counter
        cats = Counter(r["assessment"].strip() for r in rows)
        assert summary["assessment_counts_overall"] == dict(cats)
        matches = Counter(r["matches_expected"].strip().lower() for r in rows)
        assert summary["matches_expected_counts_overall"] == dict(matches)
        # every assessment is a legal category
        assert set(cats) <= set(CATEGORIES)

    def test_no_participant_artifacts_remain(self):
        """The participant study was NOT conducted: nothing may imitate it."""
        assert not (REPO / "pilot").exists()
        leftovers = sorted(p.name for p in E3_DIR.glob("response_sheet_*"))
        assert leftovers == [], f"participant sheets remain: {leftovers}"
        assert not (E3_DIR / "order_manifest.csv").exists()
        assert not (E3_DIR / "responses_TEMPLATE.csv").exists()
        assert not (REPO / "scripts" / "analyze_e3_responses.py").exists()

    def test_protocol_and_methods_note_exist(self):
        for doc in ("PROTOCOL.md", "METHODS_NOTE.md"):
            text = (E3_DIR / doc).read_text().lower()
            assert "not conducted" in text or "not\nconducted" in text or \
                "was not conducted" in text
        # the methods note must acknowledge the fallback and observer bias
        mn = (E3_DIR / "METHODS_NOTE.md").read_text().lower()
        assert "fallback" in mn
        assert "bias" in mn
