# Verification summary

What was verified for this repository, in which environment, and what was not verified. Commands to repeat each check are in
`README.md` in this directory. The current release check is `release_check/2026-11-18/`; the historical reference run of
28 October 2026 in `reference/` is kept unchanged.

## Environment

Windows 11 (10.0.26300), Python 3.12.13, in two virtual environments: one with the pinned packages of
`technical/scikit-tda-trust/requirements.txt`, `requirements-dev.txt` and `requirements-verify.txt` (tests and the evidence
verifier), and one that also has Playwright and Chrome 156 (browser tests and document generation). Package freezes and the
installation log are in `env/`. The original experimental results were computed on Linux (Python 3.12.15); the two environments
differ only in unpinned transitive packages. Nothing was run on macOS or on a Linux distribution as part of this verification.

## Test-integrity design

Tests must leave the repository exactly as they found it, so that checksum-protected results cannot change as a side effect of a
test run.

- `conftest.py` tracks every file of the repository during a test session. A test that changes, creates or removes a file is
  failed, the change is reverted and verified by hash, and the session exit status is forced to 1 on any residual difference.
- `extensions/mapper_explorer/scripts/build_viewer.py` accepts `--out-dir` and writes atomically; the explorer determinism test
  builds twice into temporary directories and compares the builds; further tests show that successful, failing and write-failing
  rebuilds leave the repository unchanged.
- `scripts/run_all_tests.py` writes its logs to a temporary directory (an explicit `--log-dir` must be empty and outside the
  repository), hashes the whole tree before and after, assigns each suite one outcome (PASS, FAIL, INTENTIONAL SKIP, DEPENDENCY
  MISSING, COULD NOT EXECUTE or MISSING SUITE) and exits non-zero unless every required stage passed. Its behaviour is tested in
  `tests/test_isolation_regression.py` (`reference/runner_selftest.md`).

## Baseline manifest

`extensions/BASELINE_MANIFEST.json` lists 145 files of the core results. `verify_baseline_unchanged.py` reports **128/145 present and
byte-identical; 17 intentionally not distributed**, each declared with its SHA-256 and a reason in
`extensions/BASELINE_RELEASE_EXCLUSIONS.json` (sixteen original course report and presentation files with their generators, and the
original package-level `.gitignore`). A declared file that is present must still match its hash; an undeclared missing file or a
changed file fails the check.

## Release check of 19 November 2026

`python scripts/run_all_tests.py --package-root ../.. --browser` on the working tree after the explorer layout fix: exit 0; 203 collected
(`tests` 86, meteorology 44, explorer 34, stability 29, controls 10), 0 failed, 0 skipped; baseline manifest check passed;
`verify_env.py` 38/38 in a temporary copy; offline explorer browser test (222/222 checks) as the separate `--browser` stage; evidence
verifier 310/310 checks with 126 derived facts; 413 files identical before and after the run. The explorer suite has 11 more tests than
in the historical reference run and in the release run of 18 November 2026 (`release_check/2026-11-18/`, 192 tests, kept unchanged) because
layout regression tests were added; `--strict-reference` was therefore not used. Logs, summary and exact command: `release_check/2026-11-19/`.
That record also holds `explorer_layout_browser_test.json`, the offline browser test of both renderings on eight saved cells.
This run precedes the addition of the record and of `SHA256SUMS.txt`. Afterwards only documentation text and the derivation of the test-count facts were changed (the counts now
derive from the latest release record); the evidence verifier (310/310 checks, 126 derived facts), the coverage audit and
`check_manifest.py` were rerun on the final tree and on a fresh extraction of the release archive.

Between the 18 November run and this one the report's Figure 7.2 caption and Section 9.5 runtime wording were corrected, a supplementary
runtime slide and three runtime facts were added, all 48 speaker notes were rewritten as spoken narration (main talk 2,337 words, 18.0 minutes
at 130 words per minute; checked by the verifier's notes-consistency and length checks, with the wording read through by hand), and the
component-separated rendering of the explorer was made radius-aware (report Figures 8.1 to 8.3 and the repository screenshots were captured again).

## What the evidence verifier checks and what it does not

`verify_evidence.py` is automatic only for what is registered in `facts.py`.

- **Re-derived from saved results:** each fact in `facts.py` and `facts_slides.py` (126, of which 33 register the numbers and table rows of the expanded slides) is computed from the result files and the derived string is
  searched, after removing whitespace and table markup, in every document named in the fact's `where` list (report Markdown, DOCX
  and PDF; slide text; Q&A Markdown, DOCX and PDF). A fact fails if its value is missing from a named document.
  `claims_register.json` is generated from the same table; do not edit it by hand.
- **Document coverage:** `audit_coverage.py` lists the opposite case: documents that contain a fact's value but are not named in its
  `where` list. After the registrations made for this release, the only such entries are the bare counts "13" (tasks) and "24"
  (cells), which are too short to register as text matches (F001, F005); they are manual checks.
- **Also checked automatically:** every Markdown paragraph and heading of the report appears in the DOCX and PDF; embedded slide
  notes equal `Speaker_Notes.md`; slide notes are 30–200 words and the main-talk narration (slides before the supplementary divider) is 10–12.5 minutes at 130 words per minute; slide tables are read cell by cell; no stale or history wording; figures, citations and links; the
  repository URL in the Markdown, DOCX relationship and PDF link annotation; environment pins.
- **Not automated:** numbers drawn inside figure images; numbers in the slides, notes or Q&A that are not in `facts.py` (for example
  the 1.00–1.75 blob range is registered, but wording such as "13/30" is matched only through the registered phrase); the meaning
  of a number in context (a text match does not prove the number is used in the same sense); and the
  visual layout of slides, which was inspected by eye in the Word and PowerPoint renderings.
- **Manual checks of this release:** all 48 slides rendered with PowerPoint at 1600×900 and read individually (a few at higher resolution); the report and Q&A PDFs were re-exported with Word and only the report page with Figure 7.8 was re-read (the full page-by-page read of both documents precedes the small wording changes of the last two passes);
  the DOCX and PDF page counts (Word reports 36 pages for the report, and the contents page and Appendix A page agree).

## Earlier regeneration of the pipelines

The experimental pipelines were regenerated once from raw inputs and compared file by file (`reference/compare/compare_*.json`):
structural outputs, diagrams, graphs and counts identical; figures pixel-identical; only wall-clock fields, an archive-metadata
hash, line-ending-dependent hashes and floating-point round-off of at most 8.9·10⁻¹⁵ differ. No experimental code, input,
parameter or result has changed since; later releases re-ran the tests and verifier only.

## Not verified

- Cross-implementation check of ripser against GUDHI; browsers other than Chrome; operating systems other than Windows 11 in this
  verification; a participant study.
- The order of design and analysis cannot be verified from time stamps or from this repository's history.
- Literature items consulted at abstract or program-page level only are listed in `REFERENCE_VERIFICATION.md`.
- PDF export and slide rendering depend on Microsoft Word and PowerPoint; LibreOffice paginates the report differently (35 pages in
  one reviewer's render) and was not used for the submitted files.
- The 17 baseline-manifest files that are not distributed.
