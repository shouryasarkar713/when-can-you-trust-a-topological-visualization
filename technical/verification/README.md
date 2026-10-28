# Verification materials

Everything that checks the project's claims lives here. Run all commands from `technical/scikit-tda-trust` unless noted.

| File / folder | Purpose |
|---|---|
| `verify_evidence.py` | Re-derives every numeric claim of the report, slides and Q&A from the saved result files (facts in `facts.py`, hand-checked claims in `claims_manual.json`) and checks them against the Markdown, DOCX and PDF editions, the slides and their notes, figures, citations, links, the pinned environment, the repository URL and the version-control disclosure. `python technical/verification/verify_evidence.py --root . [--out FILE] [--write-register]` (from the repository root). It writes nothing unless `--out` is given (JSON result) or `--write-register` is given (rewrites `claims_register.json` next to the script; use only to record a new release). |
| `check_manifest.py` | Verifies `SHA256SUMS.txt` (every file listed, no unlisted file). |
| `make_test_results.py` | Converts a runner `summary.json` into `test_results.json` / `.md`; both paths are explicit arguments. |
| `compare_trees.py` | Compares a regenerated tree with the shipped one file by file (JSON by content with volatile fields listed, arrays exactly, PNG by pixel) and reports every difference with its magnitude. |
| `explorer_offline_test.py`, `kmapper_html_offline_test.py` | Cold-cache, network-disabled browser tests (Playwright + Chrome): the offline explorer (222 checks) and the stock KeplerMapper HTML export (draws nothing offline). |
| `check_references.py` | Reference checks against Crossref (network). Results: `reference_check_crossref.json`, `reference_url_check.json`, `REFERENCE_VERIFICATION.md`. |
| `env/` | Environment record: pip freezes and creation log of the verified Windows run. |
| `reference/` | **Immutable reference evidence** of the recorded verification run (see below). |
| `VERIFICATION_STATUS.md` | What was run, in which environment, with which outcome, and what was not run. |
| `requirements_matrix.md`, `research_ledger.*`, `code_audit_findings.*`, `claims_manual.json`, `claims_register.json` | Requirements traceability, literature and code-audit records, and the claims register. `code_audit_findings.*` documents defects found in the original code audit, including failures; they are kept deliberately. |

## Detail behind the report's verification summary (Sections 11.2 and 11.3)

The report states the verification outcome briefly; the supporting detail is here.

**Test suites** (recorded run, `reference/test_results.json`, Windows 11, Python 3.12.13): core `tests` 86 passed (including the 14
isolation and runner regression tests), `extensions/meteorology/tests` 44, `extensions/mapper_explorer/tests` 23 (including the
repository-unchanged regression tests), `extensions/stability/tests` 29, `extensions/controls/tests` 10: 192 passed, 0 failed,
0 skipped. The same run passed `verify_env.py` (38 of 38 assertions, in a temporary copy), the baseline manifest check, the offline
explorer browser test (222 of 222 checks) and the whole-tree before/after hash comparison.

**Runner behaviour.** `scripts/run_all_tests.py` returns exit status 0 only if every required stage passed. It fails on a failing
suite, a missing suite directory, a suite that collects no tests, a suite that cannot execute (for example a missing dependency),
an unexpected change anywhere in the protected tree, and, unless `--allow-intentional-skips` is given, any skipped test. Each
suite is reported as PASS, FAIL, INTENTIONAL SKIP, DEPENDENCY MISSING, COULD NOT EXECUTE or MISSING SUITE. The runner's own
behaviour is tested by `tests/test_isolation_regression.py` (`reference/runner_selftest.md`).

**Checksum manifests.** `SHA256SUMS.txt` (checked by `check_manifest.py`) lists every file of the repository except itself.
`extensions/BASELINE_MANIFEST.json` (checked by `extensions/scripts/verify_baseline_unchanged.py`) records the 145 files of the
preserved core results; 128 are present and byte-identical in this repository and 17 are intentionally not distributed and are
declared with hashes and reasons in `extensions/BASELINE_RELEASE_EXCLUSIONS.json` (in the original archive all 145 verify).
`verify_evidence.py` re-derives the numerical claims of the report, slides and Q&A from the result files and checks them against
the Markdown, DOCX and PDF editions.

**Cross-platform comparison** (results computed on Linux, regenerated on Windows 11; `reference/compare/compare_*.json`; text after
newline normalisation, JSON by parsed content with wall-clock fields listed separately, arrays element by element, figures pixel by
pixel). Core experiments (results, audit, E3, figures, configurations): 64 files identical, 34 figures pixel-identical, 3 files
differ (`annulus.npy` and `figure_eight.npy`, at most 2.2·10⁻¹⁶, a last-digit difference in the trigonometric library; wall-clock
stage times in `e1_audit.json`). Weather study: 30 files identical, 12 figures pixel-identical, 3 differ (PCA coordinates and
embedding, round-off at most 8.9·10⁻¹⁵; a recorded hash of an array archive, zip metadata). Resampling study: 15 identical,
9 figures pixel-identical, 0 differ. Explorer: 11 identical, 3 differ only in hashes and byte counts of source files that Windows
writes with CRLF line endings (parsed content identical). Control experiments: 5 identical. All persistence diagrams, graphs and
counts agree.

## Immutable reference evidence vs fresh results

`reference/` is the evidence of the run recorded for this release: `test_results.{json,md}`, the raw `test_run/` logs and
junit reports, `compare/` (regenerated-vs-shipped comparisons), `explorer_offline_test/`, `kmapper_html_offline_test.json`,
`runner_selftest.md`, `evidence_verification.json`, and `root_cause_original_failure/` (reproduction of the test-side-effect
defect on the original archive). These files are listed in `SHA256SUMS.txt`.

A routine `python scripts/run_all_tests.py` never writes here. It writes to a temporary directory (or an explicit, empty
`--log-dir` outside the repository), hashes the whole tree before and after, and compares fresh per-suite counts with
`reference/test_results.json` without modifying it. Counts that differ are reported in the fresh `summary.json`
(`reference_comparison`); `--strict-reference` turns a difference into a failure.

To record a new reference run deliberately:

```bash
python scripts/run_all_tests.py --package-root ../.. --log-dir /path/outside/repo/new_run --browser --browser-python /path/to/playwright/python
python ../verification/make_test_results.py --summary /path/outside/repo/new_run/summary.json --out-dir /path/outside/repo/new_run
# then copy the files you intend to replace into reference/ yourself and regenerate SHA256SUMS.txt
```
