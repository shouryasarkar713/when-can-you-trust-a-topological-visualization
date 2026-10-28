# Test and check results

Run: 2026-10-28T14:22:53+00:00 → 2026-10-28T14:27:48+00:00 · Python 3.12.13 · Windows-11-10.0.26300-SP0

Command: `python scripts/run_all_tests.py` (from `technical/scikit-tda-trust`) — overall **PASS**

| Suite | Result | Exit code |
|---|---|---|
| `tests` | 86 passed (0 failed, 0 skipped) | 0 |
| `extensions/meteorology/tests` | 44 passed (0 failed, 0 skipped) | 0 |
| `extensions/mapper_explorer/tests` | 23 passed (0 failed, 0 skipped) | 0 |
| `extensions/stability/tests` | 29 passed (0 failed, 0 skipped) | 0 |
| `extensions/controls/tests` | 10 passed (0 failed, 0 skipped) | 0 |

Total: **192 passed, 0 failed, 0 skipped**.

| Step | Exit code | Result |
|---|---|---|
| baseline manifest (immediately after the suites) | 0 | PASS |
| scripts/verify_env.py (temporary copy) | 0 | PASS 38/38 checks passed. |
| explorer offline browser test | 0 | PASS |
| protected tree unchanged by the run | 0 | PASS (323 files identical before/after) |
