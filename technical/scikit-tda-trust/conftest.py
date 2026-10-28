"""Repository-level pytest configuration shared by every suite.

1. ISOLATION. The E3 analyzer test that validates the real inspection record writes
   `results/e3/inspection_summary.{json,md}` as a side effect. Those two files belong to the
   preserved baseline (hash-listed in extensions/BASELINE_MANIFEST.json), so the test is
   redirected to write into a pytest temporary directory instead (the test module is not edited).

2. GUARD. Every file listed in the baseline manifest is checked after every test (cheap stat
   comparison, re-hash on change). If a test mutates one, the exact original bytes are restored
   in a `finally` path, the restoration is verified by hash, and the offending test FAILS with the
   file names. The result therefore cannot depend on test ordering.

3. SESSION SUMMARY. At the end of the session the guard re-hashes all manifest files; any
   difference makes the pytest exit status non-zero.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent
MANIFEST = REPO / "extensions" / "BASELINE_MANIFEST.json"

_STATE: dict = {"bytes": {}, "stat": {}, "sha": {}, "violations": []}


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pytest_sessionstart(session):
    if not MANIFEST.exists():
        return
    for entry in json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]:
        p = REPO / entry["path"]
        if p.exists():
            data = p.read_bytes()
            _STATE["bytes"][entry["path"]] = data
            _STATE["sha"][entry["path"]] = entry["sha256"]
            st = p.stat()
            _STATE["stat"][entry["path"]] = (st.st_size, st.st_mtime_ns)


def _check_and_restore() -> list[str]:
    changed = []
    for rel, (size, mtime) in _STATE["stat"].items():
        p = REPO / rel
        try:
            st = p.stat()
            same_stat = (st.st_size, st.st_mtime_ns) == (size, mtime)
            if same_stat:
                continue
            if _sha(p.read_bytes()) == _STATE["sha"][rel]:
                _STATE["stat"][rel] = (st.st_size, st.st_mtime_ns)
                continue
        except FileNotFoundError:
            pass
        changed.append(rel)
    for rel in changed:
        p = REPO / rel
        try:
            p.write_bytes(_STATE["bytes"][rel])
        finally:
            ok = p.exists() and _sha(p.read_bytes()) == _STATE["sha"][rel]
            if not ok:
                _STATE["violations"].append(f"RESTORE FAILED: {rel}")
            st = p.stat()
            _STATE["stat"][rel] = (st.st_size, st.st_mtime_ns)
    return changed


@pytest.fixture(autouse=True)
def _baseline_guard(request):
    yield
    changed = _check_and_restore()
    if changed:
        _STATE["violations"].extend(f"mutated by {request.node.nodeid}: {c}" for c in changed)
        pytest.fail("test mutated baseline-manifest file(s) (restored): " + ", ".join(changed), pytrace=False)


@pytest.fixture(autouse=True)
def _isolate_e3_analyzer(request, tmp_path_factory, monkeypatch):
    """Send the real-record analyzer output to a temp directory instead of results/e3."""
    mod = request.module
    if not mod.__name__.endswith("test_e3_inspection") or not hasattr(mod, "run_analyzer"):
        return
    original = mod.run_analyzer
    out_root = tmp_path_factory.mktemp("e3_real_out")

    def wrapped(record, config):
        cfg = yaml.safe_load(Path(config).read_text(encoding="utf-8"))
        if not Path(cfg["paths"]["results_e3"]).is_absolute():
            cfg["paths"]["results_e3"] = str(out_root / "results" / "e3")
            tmp_cfg = out_root / "e3_config_isolated.yaml"
            tmp_cfg.write_text(yaml.safe_dump(cfg), encoding="utf-8")
            return original(record, tmp_cfg)
        return original(record, config)
    monkeypatch.setattr(mod, "run_analyzer", wrapped)


def pytest_sessionfinish(session, exitstatus):
    if not _STATE["sha"]:
        return
    final = []
    for rel, sha in _STATE["sha"].items():
        p = REPO / rel
        if not p.exists() or _sha(p.read_bytes()) != sha:
            final.append(rel)
    if final or _STATE["violations"]:
        tr = session.config.pluginmanager.get_plugin("terminalreporter")
        if tr:
            tr.write_line("BASELINE GUARD: " + "; ".join(_STATE["violations"] + final), red=True)
        session.exitstatus = 1
