# Verification summary

What was verified for this repository, in which environment, and what was not verified. Commands to repeat each check are in
`README.md` in this directory.

## Environment

Windows 11, Python 3.12.13, in two virtual environments: one with the pinned packages of
`technical/scikit-tda-trust/requirements.txt`, `requirements-dev.txt` and `requirements-verify.txt` (tests and the evidence
verifier), and one that also has Playwright and Chrome 156 (browser tests and document generation). Package freezes and the
installation log are in `env/`. The original experimental results were computed on Linux (Python 3.12.15); the two environments
differ only in unpinned transitive packages. Nothing was run on macOS or on a Linux distribution as part of this verification.

## Test-integrity design

Tests must leave the repository exactly as they found it, so that checksum-protected results cannot change as a side effect of a
test run.

- `conftest.py` tracks every file of the repository during a test session. A test that changes, creates or removes a file is
  failed, the change is reverted and verified by hash, and the session exit status is forced to 1 on any residual difference. The
  analyzer test that validates the E3 inspection record writes to a temporary directory.
- `extensions/mapper_explorer/scripts/build_viewer.py` accepts `--out-dir` and writes atomically. The explorer determinism test
  builds twice into temporary directories and compares the two builds with each other, with the saved data (build time excluded) and
  with the data inlined in the saved HTML. Further tests show that successful, failing and write-failing rebuilds leave the
  repository unchanged.
- `scripts/run_all_tests.py` writes its logs to a temporary directory (an explicit `--log-dir` must be empty and outside the
  repository), hashes the whole tree before and after, assigns each suite one outcome (PASS, FAIL, INTENTIONAL SKIP, DEPENDENCY
  MISSING, COULD NOT EXECUTE or MISSING SUITE) and exits non-zero unless every required stage passed. Its behaviour is tested in
  `tests/test_isolation_regression.py` (`reference/runner_selftest.md`).

## Baseline manifest

`extensions/BASELINE_MANIFEST.json` lists 145 files of the core results. `verify_baseline_unchanged.py` reports **128/145 present and
byte-identical; 17 intentionally not distributed**. The 17 are declared with their SHA-256 and a reason in
`extensions/BASELINE_RELEASE_EXCLUSIONS.json`: sixteen original course report and presentation files with their generators, and the
original package-level `.gitignore`, which ignored the project's own source directories and would make git skip new files there. A
declared file that is present must still match its hash; an undeclared missing file or a changed file fails the check.

## Checks performed

| Check | Result |
|---|---|
| `python scripts/run_all_tests.py --package-root ../.. --browser` | exit 0; 192 collected (`tests` 86, meteorology 44, explorer 23, stability 29, controls 10); 0 failed, 0 skipped; baseline manifest check passed; `verify_env.py` 38/38 in a temporary copy; offline explorer browser test 222/222; 351 files identical before and after the run. Logs: `reference/test_run/`, converted by `make_test_results.py` into `reference/test_results.{json,md}` |
| Runner and guard regression tests | 14 of 14 passed (`reference/runner_selftest.md`) |
| `verify_evidence.py` | all checks passed; 79 numerical claims re-derived from the result files and matched against the Markdown, DOCX and PDF report, the slides, speaker notes and Q&A; repository link and version-control disclosure present |
| `check_manifest.py` | every file of `SHA256SUMS.txt` matches; no unlisted file |
| Stock KeplerMapper HTML export, cold cache, network disabled | draws nothing (`d3 is not defined`; 0 circles, 0 lines): `reference/kmapper_html_offline_test.json` |
| Regeneration of the pipelines from raw inputs, compared file by file | `reference/compare/compare_*.json`: structural outputs, diagrams, graphs and counts identical; figures pixel-identical; only wall-clock fields, an archive-metadata hash, line-ending-dependent hashes and floating-point round-off of at most 8.9·10⁻¹⁵ differ |
| Report, slides and Q&A | rendered to PDF with Microsoft Word and PowerPoint and inspected page by page |

The experimental pipelines were regenerated once from raw inputs (comparison files above). No experimental code, input, parameter or
result has changed since; the later checks above were repeated on the final files.

## Not verified

- Cross-implementation check of ripser against GUDHI; browsers other than Chrome; operating systems other than Windows 11 in this
  verification; a participant study.
- The order of design and analysis cannot be verified from time stamps or from this repository's history.
- Literature items consulted at abstract or program-page level only are listed in `REFERENCE_VERIFICATION.md`.
- PDF export and slide rendering depend on Microsoft Word and PowerPoint; the generated files are included.
- The 17 baseline-manifest files that are not distributed.
