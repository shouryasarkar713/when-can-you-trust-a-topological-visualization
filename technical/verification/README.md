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
