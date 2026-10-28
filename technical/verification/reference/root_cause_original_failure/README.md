# Root cause of the earlier test-status contradiction

An untouched extraction of the previously supplied archive was used. Running only `tests/test_e3_inspection.py`
(exit 0, `step1_e3_tests.log`) and then `extensions/scripts/verify_baseline_unchanged.py`
(exit 1, `step2_manifest_after_e3_tests.log`) reproduces the failure: the test `test_real_record_validates` runs
`scripts/analyze_e3_inspection.py` against the real configuration, which writes
`results/e3/inspection_summary.json` and `.md` inside the repository. On Windows the files are written in text mode
with CRLF line endings (274 CRLF, no bare LF in the JSON), so their SHA-256 no longer matches the manifest. Any
later manifest check — including the stability suite's `test_baseline_manifest_unchanged` — then fails, which made
the stability result depend on test order.

Fix (new files only; no manifest-listed file edited): `conftest.py` redirects the analyzer output of that test to a
temporary directory, guards every manifest file after every test (restore by hash-verified byte copy, test fails if a
file was mutated), and fails the session on any residual difference; `tests/test_e3_summary_reproducible.py` checks the
stored summary against a regenerated one in a temporary directory. `scripts/run_all_tests.py` runs every suite and
returns a non-zero status on any failure.
