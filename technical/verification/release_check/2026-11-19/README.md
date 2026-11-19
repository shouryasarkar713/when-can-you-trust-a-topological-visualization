# Release check, 19 November 2026

Run of the final working tree (after the radius-aware component-separated layout fix of the offline explorer (11 new layout regression tests, rebuilt viewer, new screenshots and figure captions)) before this record and `SHA256SUMS.txt` were added. It is separate from the historical reference
run in `../../reference/` (28 October 2026) and from the earlier record in `../2026-11-18/`, both left unchanged. The suites now collect 203 tests (explorer 34) instead of 192 because 11 layout regression tests were added, so the per-suite counts differ from the historical reference by design. The scientific experiments were not re-run; the existing test
suites and verification tools were.

- **Started / finished (UTC):** 2026-11-19T04:25:32+00:00 / 2026-11-19T04:31:50+00:00
- **Environment:** Windows-11-10.0.26300-SP0, Python 3.12.13 (pinned virtual environment); Playwright and Chrome 156 in a second virtual environment for the browser test
- **Command** (from `technical/scikit-tda-trust`): `python scripts/run_all_tests.py --package-root ../.. --browser --browser-python <python with Playwright> --reference ../verification/reference/test_results.json`
- **Exit status:** 0 (overall PASS)
- **Tests collected:** 203; failed 0; errors 0; skipped 0

| Suite | Passed | Exit code | Outcome |
|---|---|---|---|
| `tests` | 86 | 0 | PASS |
| `extensions/meteorology/tests` | 44 | 0 | PASS |
| `extensions/mapper_explorer/tests` | 34 | 0 | PASS |
| `extensions/stability/tests` | 29 | 0 | PASS |
| `extensions/controls/tests` | 10 | 0 | PASS |

| Other stage | Exit code | Outcome |
|---|---|---|
| baseline manifest (immediately after the suites) | 0 | PASS |
| scripts/verify_env.py (temporary copy) | 0 | PASS |
| verify_evidence.py | 0 | PASS |
| explorer offline browser test | 0 | PASS |
| protected tree unchanged by the run | 0 | PASS |

The environment check (`verify_env.py`, 38 of 38 assertions) ran in a temporary copy. The explorer browser test is the separate
`--browser` stage. The tree-integrity stage hashed 413 files before and after the run and found no change.
The comparison with the historical reference counts reports the intended difference (explorer 34 instead of 23). The evidence verifier ran inside the run and passed.
Raw logs, junit reports and `summary.json` are in `run/`.

## Limits
Windows 11 and Chrome only; no macOS or Linux run in this check. The verifier covers registered claims only (see `../../VERIFICATION_SUMMARY.md`).
