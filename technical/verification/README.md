# Verification materials

Everything that checks the project's claims lives here. Run all commands from `technical/scikit-tda-trust` unless noted.

| File / folder | Purpose |
|---|---|
| `verify_evidence.py` | Re-derives the 126 registered numerical facts of `facts.py` and `facts_slides.py` from the saved result files and checks each against the documents named in its `where` field (report Markdown, DOCX and PDF; slide text including table cells; slide notes; Q&A; the main-talk narration length and the supplementary divider). It also checks, for the report, that every Markdown paragraph and heading appears in the DOCX and PDF, and checks figures, citations, links, the pinned environment, the repository URL and the version-control disclosure. `claims_manual.json` holds curated, manually reviewed claims (M* entries); these are **not** re-derived by `verify_evidence.py`. Numerical claims that are not registered in `facts.py` are outside the automatic numerical-claim checks. `python technical/verification/verify_evidence.py --root . [--out FILE] [--write-register]` (from the repository root). It writes nothing unless `--out` is given (JSON result) or `--write-register` is given (rewrites `claims_register.json` next to the script; use only to record a new release). |
| `audit_coverage.py` | Lists, for every registered fact, the documents that contain its value but are not named in its `where` list, and registered documents that lack it. The latest audit found only the short values of F001 ("13") and F005 ("24") unregistered in some documents; these values also occur in unrelated contexts, so they remain manual checks, and a bare numeric text match is not proof of semantic agreement. |
| `release_check/` | Dated records of full verification runs of a release (command, environment, counts, per-suite logs, JUnit reports, summary, environment check, evidence verification, offline browser test); `release_check/2026-11-18/` is the current release run. Separate from the historical `reference/`. |
| `check_manifest.py` | Verifies `SHA256SUMS.txt` (every file listed, no unlisted file). |
| `make_test_results.py` | Converts a runner `summary.json` into `test_results.json` / `.md`; both paths are explicit arguments. |
| `compare_trees.py` | Compares a regenerated tree with the shipped one file by file (JSON by content with volatile fields listed, arrays exactly, PNG by pixel) and reports every difference with its magnitude. |
| `explorer_offline_test.py`, `kmapper_html_offline_test.py` | Cold-cache, network-disabled browser tests (Playwright + Chrome): the offline explorer (222 checks) and the stock KeplerMapper HTML export (draws nothing offline). |
| `explorer_layout_browser_test.py` | Offline browser test of the explorer's native and component-separated renderings on eight representative saved cells (weather (20, 0.35) first): no external requests or console messages, layout switching, identical statistics, identical node and edge counts and radii in both renderings, no overlapping circles and no clipping in the separated drawing, export with provenance. `python technical/verification/explorer_layout_browser_test.py <viewer index.html> <out.json>`. |
| `check_references.py` | Reference checks against Crossref (network). Results: `reference_check_crossref.json`, `reference_url_check.json`, `REFERENCE_VERIFICATION.md`. |
| `env/` | Environment record: pip freezes and creation log of the verified Windows run. |
| `reference/` | **Immutable historical reference evidence**: the run of 28 October 2026 and the baseline for `--strict-reference` (see below). |
| `VERIFICATION_SUMMARY.md` | What was verified, in which environment, with which outcome, and what was not verified. |
| `claims_manual.json`, `claims_register.json` | Claims that cannot be derived mechanically (with their evidence) and the register of all claims checked by the verifier. |

## Detail behind the report's verification summary (Sections 11.2 and 11.3)

The report states the verification outcome briefly; the supporting detail is here.

**Test suites** (historical run of 28 October 2026, `reference/test_results.json`, Windows 11, Python 3.12.13; the run of 18 November 2026 in `release_check/2026-11-18/` gives the same counts; the run of 19 November 2026 in `release_check/2026-11-19/` collects 203 tests because 11 explorer layout tests were added): core `tests` 86 passed (including the 14
isolation and runner regression tests), `extensions/meteorology/tests` 44, `extensions/mapper_explorer/tests` 23 (34 in the run of 19 November 2026, which adds 11 layout regression tests; including the
repository-unchanged regression tests), `extensions/stability/tests` 29, `extensions/controls/tests` 10: 192 passed (203 in the run of 19 November 2026), 0 failed,
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
`verify_evidence.py` re-derives the 126 registered facts (`facts.py`, `facts_slides.py`) from the result files and checks them against the documents named in
each fact's `where` field; unregistered numerical claims are not checked automatically.

**Cross-platform comparison** (results computed on Linux, regenerated on Windows 11; `reference/compare/compare_*.json`; text after
newline normalisation, JSON by parsed content with wall-clock fields listed separately, arrays element by element, figures pixel by
pixel). Core experiments (results, audit, E3, figures, configurations): 64 files identical, 34 figures pixel-identical, 3 files
differ (`annulus.npy` and `figure_eight.npy`, at most 2.2·10⁻¹⁶, a last-digit difference in the trigonometric library; wall-clock
stage times in `e1_audit.json`). Weather study: 30 files identical, 12 figures pixel-identical, 3 differ (PCA coordinates and
embedding, round-off at most 8.9·10⁻¹⁵; a recorded hash of an array archive, zip metadata). Resampling study: 15 identical,
9 figures pixel-identical, 0 differ. Explorer: 11 identical, 3 differ only in hashes and byte counts of source files that Windows
writes with CRLF line endings (parsed content identical). Control experiments: 5 identical. All persistence diagrams, graphs and
counts agree.

## Historical reference evidence and current release evidence

`reference/` is the **historical** evidence of the run of 28 October 2026: `test_results.{json,md}`, the raw `test_run/` logs and
junit reports, `compare/` (regenerated-vs-shipped comparisons), `explorer_offline_test/`, `kmapper_html_offline_test.json`,
`runner_selftest.md` and `evidence_verification.json`. It is immutable, listed in `SHA256SUMS.txt`, and `reference/test_results.json`
is the baseline against which `--strict-reference` compares fresh per-suite counts.

`release_check/2026-11-19/` is the dated evidence of the **current release run** of 19 November 2026 (`release_check/2026-11-18/` is the earlier run of the previous day, kept unchanged): its README, the per-suite logs,
JUnit reports, `summary.json`, the environment check, the evidence verification and the offline browser test. The current result
(203 tests; the explorer suite has 34 tests instead of 23 because layout regression tests were added) differs from the historical baseline counts by exactly those 11 tests; the two records are different runs. `--strict-reference` therefore no longer applies to the current tree and was not used for it.

A routine `python scripts/run_all_tests.py` never writes to either folder. It writes to a temporary directory (or an explicit, empty
`--log-dir` outside the repository), hashes the whole tree before and after, and compares fresh per-suite counts with
`reference/test_results.json` without modifying it. Counts that differ are reported in the fresh `summary.json`
(`reference_comparison`); `--strict-reference` turns a difference into a failure.

To record a new reference run deliberately:

```bash
python scripts/run_all_tests.py --package-root ../.. --log-dir /path/outside/repo/new_run --browser --browser-python /path/to/playwright/python
python ../verification/make_test_results.py --summary /path/outside/repo/new_run/summary.json --out-dir /path/outside/repo/new_run
# then copy the files you intend to replace into reference/ yourself and regenerate SHA256SUMS.txt
```
