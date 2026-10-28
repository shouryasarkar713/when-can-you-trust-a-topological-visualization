"""The stored E3 summary must equal the summary regenerated from the stored inspection record
(newline-normalised); regeneration happens in a temporary directory, never in the repository."""
import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent


def test_stored_summary_equals_regenerated(tmp_path):
    cfg = yaml.safe_load((REPO / "configs" / "e3_readability.yaml").read_text(encoding="utf-8"))
    cfg["paths"]["results_e3"] = str(tmp_path / "results" / "e3")
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    res = subprocess.run([sys.executable, str(REPO / "scripts" / "analyze_e3_inspection.py"),
                          "--config", str(cfg_path),
                          "--record", str(REPO / "e3_inspection" / "inspection_record.csv")],
                         capture_output=True, text=True, cwd=str(REPO))
    assert res.returncode == 0, res.stderr
    new = tmp_path / "results" / "e3"
    for name in ("inspection_summary.json", "inspection_summary.md"):
        a = (REPO / "results" / "e3" / name).read_bytes().replace(b"\r\n", b"\n")
        b = (new / name).read_bytes().replace(b"\r\n", b"\n")
        if name.endswith(".json"):
            assert json.loads(a) == json.loads(b)
        else:
            assert a == b
