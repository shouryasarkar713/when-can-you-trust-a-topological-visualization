# Verification status

Technical record of what was run for this release, in which environment, with which outcome, which earlier evidence was
reused instead of re-run, and what was not run. The report, slides and Q&A contain no part of this history.

Contemporaneous version-control history was not maintained during the project. The repository is organized retrospectively for
reproducibility and release; its commit history should not be interpreted as evidence of the original design or analysis
chronology.

## Environment

Windows 11 (10.0.26300), Python 3.12.13, fresh virtual environments: `.venv` with `technical/scikit-tda-trust/requirements.txt`,
`requirements-dev.txt` and `requirements-verify.txt` (tests, evidence verifier), `.venv-tools` additionally with Playwright
and the installed Chrome 156 (browser tests, document generation). Freezes and installation log: `env/`. The earlier
Linux run (Python 3.12.15) differs only in unpinned transitive packages. Nothing in this repository was run on macOS or on a Linux
distribution in this release; Linux results exist only from the original computation of the results.

## Defects found by the audit and how they were fixed

| Item | Finding | Resolution | Evidence |
|---|---|---|---|
| Test side effect | `test_layouts_are_deterministic_across_rebuild` rebuilt the explorer inside the repository and rewrote `explorer_data.json`, `build_report.json` and `viewer/index.html` (all listed in the baseline or release checksums) | `build_viewer.py` gained `--out-dir` (default unchanged) and writes atomically (temporary siblings, removed in `finally`); the determinism test now builds twice into two temporary directories and compares the builds with each other, with the saved data (build time stripped) and with the data inlined in the saved HTML; new `TestRepositoryIsNotModified` hashes the whole repository around successful, failing and write-failing rebuilds | `extensions/mapper_explorer/tests/test_explorer.py` (23 tests); `reference/root_cause_original_failure/` (reproduction on the unmodified archive) |
| Mutation by a baseline test | `test_real_record_validates` wrote `results/e3/inspection_summary.*` into the repository, changing hash-listed files; the stability manifest test then failed | `conftest.py`: that output goes to a temporary directory; every repository file is tracked and any change made by a test is reverted, hash-verified, and fails the test; the session exit status is forced to 1 on any residual difference | `tests/test_isolation_regression.py` (14 tests) |
| Runner | the earlier runner wrote its logs into the package, did not distinguish skipped from non-executable suites, and did not detect changes to the tree | `scripts/run_all_tests.py`: logs to a temporary directory (explicit `--log-dir` must be empty and outside the tree), whole-tree hash before and after, one outcome per suite (PASS, FAIL, INTENTIONAL SKIP, DEPENDENCY MISSING, COULD NOT EXECUTE, MISSING SUITE), exit status 0 only if every required stage passed, read-only comparison with `reference/test_results.json` | `reference/runner_selftest.md`; `reference/test_run/` |
| Baseline accounting | the manifest lists 145 files; 17 are not part of this release | see next section | `extensions/BASELINE_RELEASE_EXCLUSIONS.json`; `reference/test_run/baseline_manifest_after_tests.log` |
| Weather null-control wording; clusterer-scale wording | earlier phrasing overstated both | corrected in report, slides, notes, Q&A, figure titles and configuration | `verify_evidence.py` derives the quoted ranges from the result files |

## Baseline manifest: what is verified and what is not distributed

`extensions/BASELINE_MANIFEST.json` is byte-identical to the one in the submitted archive and lists 145 files.

- Original archive, original verifier: **145/145 byte-identical**.
- This repository, `verify_baseline_unchanged.py`: **128/145 present and byte-identical; 17 intentionally not distributed**.
  Not claimed anywhere: "145/145 in this repository".
- The 17 not distributed are declared with their SHA-256 and a reason in `BASELINE_RELEASE_EXCLUSIONS.json`: sixteen original course
  report and presentation files with their generators (superseded by `submission/`), and the original package-level `.gitignore`,
  which ignored the project's own source directories (`audit/`, `configs/`, `src/`, `tests/`, ...) and would make git skip any
  new file there. If any of the 17 is present, it must still match its hash; a missing file that is not declared, or a changed
  file, fails the check. With the original `.gitignore` restored in a scratch copy the same check reports 129/145 verified.

## What was run for this release

| Check | Result |
|---|---|
| `python scripts/run_all_tests.py --package-root ../.. --browser` (Windows, Python 3.12.13) | exit 0; 192 collected: `tests` 86, meteorology 44, explorer 23, stability 29, controls 10; 0 failed, 0 skipped; baseline manifest check passed; `verify_env.py` 38/38 in a temporary copy; offline explorer browser test passed (222 of 222 checks); 323 files hashed before and after, identical. Logs: `reference/test_run/`, converted by `make_test_results.py` into `reference/test_results.{json,md}` |
| Isolation and runner regression tests | 14 of 14 passed (`reference/runner_selftest.md`) |
| Explorer suite | 23 passed; a snapshot of the whole repository (327 files) was identical before and after, three consecutive runs |
| `verify_evidence.py` | 262 of 262 checks, 79 derived facts (includes the repository URL in the Markdown, DOCX relationship and PDF link annotations, and the version-control disclosure) |
| Stock KeplerMapper HTML export, cold cache, network disabled | draws nothing (`d3 is not defined`; 0 circles, 0 lines): `reference/kmapper_html_offline_test.json` |
| Report DOCX and PDF | regenerated from the Markdown with the existing workflow (Word automation) after an editorial revision (evidence tags and cover legend removed, internal paths and test-log detail moved to this directory, limitations consolidated, figure layout tightened, then letter-number labels such as G1-G6 and T01-T13 and unexpanded abbreviations replaced by descriptive wording); 30 PDF pages rendered and every page inspected; link annotations to the repository present in the PDF, hyperlink relationships in the DOCX. No experiment was re-run for the revision: no code, input, parameter or result of the experiments changed. The test suites were re-run on a fresh clone of the revised repository (see the commit history) |

## Earlier evidence reused, not re-run in this release

The experimental pipelines (E1, E2, E3 stimuli, weather preprocessing and analysis, seasonality check, Mapper and persistence
resampling, leave-one-year-out, explorer build, controls D1–D5) were recomputed from raw inputs in the verification run that
preceded this release, and compared file by file with the packaged results: `reference/compare/compare_*.json`. Those files record
the comparison as it was made and are reused here. No experimental algorithm, input, parameter or result changed in this release; the
changes are limited to the explorer builder's output-directory option (the byte-for-byte output is unchanged and is checked by the
determinism test against the saved data), the test infrastructure, the documentation and the report text. In the comparison, structural
outputs, diagrams, graphs and counts agree; figures are pixel-identical (apart from the counted exceptions); only wall-clock fields, the
hash of an array archive, CRLF-dependent hashes and floating-point round-off of at most 8.9·10⁻¹⁵ differ. The control experiments (five
result files) are identical.

A second, throwaway recomputation was started during release preparation and stopped on the author's instruction after 12 of 19 scripts
(all exit 0) because nothing relevant had changed. It ran in a temporary copy, wrote nothing to this repository, and is not used as
evidence.

## Not run / not verified

- Cross-implementation check of ripser against GUDHI; browsers other than Chrome; operating systems other than Windows 11 in this
  release (the original results were computed on Linux); a participant study.
- The order of design and analysis cannot be verified from time stamps or from this repository's history.
- Literature items consulted at abstract level only, and bibliographic details inherited from the earlier research ledger, are listed in
  `REFERENCE_VERIFICATION.md`. Crossref/URL checks (`reference_check_crossref.json`, `reference_url_check.json`) were made earlier and not
  repeated in this release.
- PDF export and slide rendering depend on Microsoft Word and PowerPoint; the generated files are included.
- The 17 baseline-manifest files not distributed (above).
