"""Repository-level pytest configuration shared by every suite.

Purpose: a test run must leave the repository exactly as it found it.

1. ISOLATION. The E3 analyzer test that validates the real inspection record would write
   `results/e3/inspection_summary.{json,md}` into the repository; it is redirected to a pytest
   temporary directory (the preserved test module itself is not edited). The explorer rebuild test
   passes `--out-dir` to the builder for the same reason.

2. GUARD (defence in depth, not a substitute for isolation). Every file of the repository is
   tracked by (size, mtime) and re-hashed when its stat changes; files created by a test are
   detected too. After each test, any difference is
     - reverted (original bytes written back / created file removed) in a `finally` block,
     - verified by hash, and
     - reported by FAILING the offending test with the file names.
   Files listed in extensions/BASELINE_MANIFEST.json are additionally re-hashed at session end.
   The result therefore cannot depend on test ordering.

3. The session exit status is forced to 1 if any repository file differs at the end of the session.
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
SKIP_PARTS = {"__pycache__", ".pytest_cache", ".git"}

_STATE: dict = {"bytes": {}, "stat": {}, "sha": {}, "violations": [], "manifest": {}}


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _iter_files():
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_PARTS]
        for f in files:
            p = Path(root) / f
            if p.suffix == ".pyc":
                continue
            yield p


def pytest_sessionstart(session):
    for p in _iter_files():
        rel = p.relative_to(REPO).as_posix()
        data = p.read_bytes()
        _STATE["bytes"][rel] = data
        _STATE["sha"][rel] = _sha(data)
        st = p.stat()
        _STATE["stat"][rel] = (st.st_size, st.st_mtime_ns)
    if MANIFEST.exists():
        for entry in json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]:
            _STATE["manifest"][entry["path"]] = entry["sha256"]


def _check_and_revert() -> list[str]:
    changed: list[str] = []
    current = {}
    for p in _iter_files():
        current[p.relative_to(REPO).as_posix()] = p
    for rel, (size, mtime) in _STATE["stat"].items():
        p = REPO / rel
        try:
            st = p.stat()
            if (st.st_size, st.st_mtime_ns) == (size, mtime):
                continue
            if _sha(p.read_bytes()) == _STATE["sha"][rel]:
                _STATE["stat"][rel] = (st.st_size, st.st_mtime_ns)
                continue
        except FileNotFoundError:
            pass
        changed.append("modified/removed: " + rel)
    added = sorted(set(current) - set(_STATE["stat"]))
    changed.extend("created: " + rel for rel in added)
    for entry in changed:
        kind, rel = entry.split(": ", 1)
        p = REPO / rel
        try:
            if kind == "created":
                p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(_STATE["bytes"][rel])
        finally:
            if kind == "created":
                ok = not p.exists()
            else:
                ok = p.exists() and _sha(p.read_bytes()) == _STATE["sha"][rel]
                if p.exists():
                    st = p.stat()
                    _STATE["stat"][rel] = (st.st_size, st.st_mtime_ns)
            if not ok:
                _STATE["violations"].append("REVERT FAILED: " + entry)
    return changed


@pytest.fixture(autouse=True)
def _repository_guard(request):
    yield
    changed = _check_and_revert()
    if changed:
        _STATE["violations"].extend(f"{request.node.nodeid}: {c}" for c in changed)
        pytest.fail("test modified the repository (reverted): " + "; ".join(changed), pytrace=False)


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
    final = [rel for rel, sha in _STATE["sha"].items()
             if not (REPO / rel).exists() or _sha((REPO / rel).read_bytes()) != sha]
    bad_manifest = []
    for rel, sha in _STATE["manifest"].items():
        p = REPO / rel
        if p.exists() and _sha(p.read_bytes()) != sha:
            bad_manifest.append(rel)
    if final or bad_manifest or _STATE["violations"]:
        tr = session.config.pluginmanager.get_plugin("terminalreporter")
        if tr:
            tr.write_line("REPOSITORY GUARD: " + "; ".join(_STATE["violations"] + final + bad_manifest), red=True)
        session.exitstatus = 1
