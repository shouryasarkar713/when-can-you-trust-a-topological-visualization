"""Regression tests for the test-isolation and verification-runner contract.

They run the real `scripts/run_all_tests.py` and the real repository `conftest.py` against small
throw-away repositories built in a pytest temporary directory, so they never touch this repository.

Contract under test
  * the guard in conftest.py fails a test that modifies/creates/removes a repository file, reverts the
    change, and makes the session exit non-zero;
  * the runner reports one distinct outcome per suite (PASS, FAIL, INTENTIONAL SKIP, DEPENDENCY MISSING,
    COULD NOT EXECUTE, MISSING SUITE) and exits non-zero for every outcome except PASS
    (INTENTIONAL SKIP only with --allow-intentional-skips);
  * a suite that mutates the protected tree fails the run even though its own tests pass;
  * the runner refuses to write logs into the protected tree or into a non-empty directory;
  * a clean run leaves the protected tree byte-identical.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
RUNNER = REPO / "scripts" / "run_all_tests.py"
CONFTEST = REPO / "conftest.py"

SUITES = {
    "s_pass": "def test_a():\n    assert True\n",
    "s_fail": "def test_a():\n    assert False\n",
    "s_skip": "import pytest\n\n@pytest.mark.skip(reason='intentionally skipped')\ndef test_a():\n    pass\n",
    "s_dep_skip": "import pytest\n\ndef test_a():\n    pytest.importorskip('module_that_is_not_installed_xyz')\n",
    "s_dep_import": "import module_that_is_not_installed_xyz\n\ndef test_a():\n    pass\n",
    "s_empty": "x = 1\n",
    "s_mutates": ("from pathlib import Path\n\ndef test_a():\n"
                  "    (Path(__file__).resolve().parents[1] / 'stray_output.txt').write_text('side effect')\n"),
}


def _mini_repo(root: Path) -> Path:
    repo = root / "mini"
    for name, body in SUITES.items():
        (repo / name).mkdir(parents=True)
        (repo / name / f"test_{name}.py").write_text(body, encoding="utf-8")
    (repo / "data.txt").write_text("reference data", encoding="utf-8")
    return repo


def _run_runner(repo: Path, log_dir: Path, *suites: str, extra=()):
    cmd = [sys.executable, str(RUNNER), "--repo-root", str(repo), "--log-dir", str(log_dir),
           "--skip-baseline", "--skip-env", "--skip-evidence", *extra]
    for s in suites:
        cmd += ["--suite", s]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    summary = json.loads((log_dir / "summary.json").read_text(encoding="utf-8")) if (log_dir / "summary.json").exists() else None
    return p, summary


def _outcome(summary, suite):
    return next(s for s in summary["steps"] if s["step"] == suite)["outcome"]


@pytest.fixture()
def mini(tmp_path):
    return _mini_repo(tmp_path), tmp_path / "logs"


def test_runner_passes_clean_suite_and_leaves_tree_identical(mini):
    repo, logs = mini
    before = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    p, s = _run_runner(repo, logs, "s_pass")
    assert p.returncode == 0, p.stdout + p.stderr
    assert s["overall"] == "PASS" and _outcome(s, "s_pass") == "PASS"
    after = {p_.relative_to(repo).as_posix(): p_.read_bytes() for p_ in repo.rglob("*")
             if p_.is_file() and "__pycache__" not in p_.parts}
    assert before == after


def test_runner_fails_on_failing_suite(mini):
    repo, logs = mini
    p, s = _run_runner(repo, logs, "s_pass", "s_fail")
    assert p.returncode == 1
    assert _outcome(s, "s_fail") == "FAIL" and _outcome(s, "s_pass") == "PASS"
    assert s["overall"] == "FAIL"


def test_intentional_skip_is_distinct_and_fails_by_default(mini):
    repo, logs = mini
    p, s = _run_runner(repo, logs, "s_skip")
    assert p.returncode == 1
    assert _outcome(s, "s_skip") == "INTENTIONAL SKIP"


def test_intentional_skip_accepted_only_when_allowed(mini):
    repo, logs = mini
    p, s = _run_runner(repo, logs, "s_skip", extra=["--allow-intentional-skips"])
    assert p.returncode == 0, p.stdout
    assert _outcome(s, "s_skip") == "INTENTIONAL SKIP"


@pytest.mark.parametrize("suite", ["s_dep_skip", "s_dep_import"])
def test_missing_dependency_is_not_an_intentional_skip(mini, suite):
    repo, logs = mini
    # fails even when intentional skips are allowed
    p, s = _run_runner(repo, logs, suite, extra=["--allow-intentional-skips"])
    assert p.returncode == 1
    assert _outcome(s, suite) == "DEPENDENCY MISSING"


def test_suite_with_no_tests_could_not_execute(mini):
    repo, logs = mini
    p, s = _run_runner(repo, logs, "s_empty")
    assert p.returncode == 1
    assert _outcome(s, "s_empty") == "COULD NOT EXECUTE"


def test_missing_suite_directory_fails(mini):
    repo, logs = mini
    p, s = _run_runner(repo, logs, "s_pass", "no_such_suite")
    assert p.returncode == 1
    assert _outcome(s, "no_such_suite") == "MISSING SUITE"


def test_suite_that_mutates_the_tree_fails_the_run(mini):
    repo, logs = mini
    p, s = _run_runner(repo, logs, "s_mutates")
    assert p.returncode == 1
    assert _outcome(s, "s_mutates") == "PASS"  # the test itself passed ...
    integ = next(x for x in s["steps"] if x["kind"] == "integrity")
    assert integ["outcome"] == "FAIL" and "stray_output.txt" in integ["result"]  # ... the tree check did not
    assert "created: stray_output.txt" in s["tree_integrity"]["changes"]


def test_missing_required_step_fails(mini):
    repo, logs = mini
    cmd = [sys.executable, str(RUNNER), "--repo-root", str(repo), "--log-dir", str(logs), "--suite", "s_pass",
           "--skip-env", "--skip-evidence"]  # baseline verifier does not exist in the mini repo
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    assert p.returncode == 1
    s = json.loads((logs / "summary.json").read_text(encoding="utf-8"))
    assert any("baseline" in st["step"] and not st["ok"] for st in s["steps"])


def test_runner_refuses_nonempty_or_in_tree_log_dir(mini):
    repo, logs = mini
    logs.mkdir()
    (logs / "keep.log").write_text("existing evidence", encoding="utf-8")
    p, _ = _run_runner(repo, logs, "s_pass")
    assert p.returncode == 2 and "not empty" in p.stderr
    assert (logs / "keep.log").read_text(encoding="utf-8") == "existing evidence"
    p, _ = _run_runner(repo, repo / "logs_inside", "s_pass")
    assert p.returncode == 2 and "inside the protected tree" in p.stderr
    assert not (repo / "logs_inside").exists()


def test_comparison_with_reference_never_modifies_it(mini, tmp_path):
    repo, logs = mini
    ref = tmp_path / "reference_test_results.json"
    ref.write_text(json.dumps({"suites": [{"dir": "s_pass", "passed": 5, "failed": 0, "skipped": 0}]}), encoding="utf-8")
    before = ref.read_bytes()
    p, s = _run_runner(repo, logs, "s_pass", extra=["--reference", str(ref)])
    assert p.returncode == 0
    assert s["reference_comparison"]["identical_counts"] is False
    assert ref.read_bytes() == before
    p, _ = _run_runner(repo, tmp_path / "logs2", "s_pass", extra=["--reference", str(ref), "--strict-reference"])
    assert p.returncode == 1


# ---- guard in conftest.py -------------------------------------------------------------------------

GUARD_TESTS = textwrap.dedent('''
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent

    def test_modifies_existing():
        (ROOT / "tracked.txt").write_text("changed")

    def test_creates_new():
        (ROOT / "new_file.txt").write_text("new")

    def test_deletes_existing():
        (ROOT / "other.txt").unlink()

    def test_innocent():
        assert (ROOT / "tracked.txt").read_text() == "original"
''')


def test_repository_guard_fails_reverts_and_sets_exit_status(tmp_path):
    work = tmp_path / "guarded"
    work.mkdir()
    shutil.copy(CONFTEST, work / "conftest.py")
    (work / "tracked.txt").write_text("original", encoding="utf-8")
    (work / "other.txt").write_text("keep me", encoding="utf-8")
    (work / "test_probe.py").write_text(GUARD_TESTS, encoding="utf-8")
    p = subprocess.run([sys.executable, "-B", "-m", "pytest", "test_probe.py", "-q", "-p", "no:cacheprovider"],
                       cwd=work, capture_output=True, text=True, timeout=300)
    assert p.returncode != 0
    # each offending test is reported as a teardown ERROR naming the file; the innocent test still passes
    assert "3 errors" in p.stdout and "test modified the repository (reverted)" in p.stdout, p.stdout
    assert "REPOSITORY GUARD" in p.stdout
    # reverted: the tree is as it was before the probe
    assert (work / "tracked.txt").read_text(encoding="utf-8") == "original"
    assert (work / "other.txt").read_text(encoding="utf-8") == "keep me"
    assert not (work / "new_file.txt").exists()


def test_repository_guard_is_silent_for_clean_tests(tmp_path):
    work = tmp_path / "guarded_clean"
    work.mkdir()
    shutil.copy(CONFTEST, work / "conftest.py")
    (work / "tracked.txt").write_text("original", encoding="utf-8")
    (work / "test_clean.py").write_text(
        "def test_x(tmp_path):\n    (tmp_path / 'scratch.txt').write_text('ok')\n", encoding="utf-8")
    p = subprocess.run([sys.executable, "-B", "-m", "pytest", "test_clean.py", "-q", "-p", "no:cacheprovider"],
                       cwd=work, capture_output=True, text=True, timeout=300)
    assert p.returncode == 0, p.stdout
