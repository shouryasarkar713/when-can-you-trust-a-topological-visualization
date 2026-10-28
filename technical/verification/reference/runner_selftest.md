# Runner and repository-guard self-test

Source: `tests/test_isolation_regression.py`, executed inside the `tests` suite of the recorded run (`test_run/pytest_tests.xml`). Each test drives the real `scripts/run_all_tests.py` or `conftest.py` against a throw-away repository.

| Test | Outcome |
|---|---|
| `test_runner_passes_clean_suite_and_leaves_tree_identical` | passed |
| `test_runner_fails_on_failing_suite` | passed |
| `test_intentional_skip_is_distinct_and_fails_by_default` | passed |
| `test_intentional_skip_accepted_only_when_allowed` | passed |
| `test_missing_dependency_is_not_an_intentional_skip[s_dep_skip]` | passed |
| `test_missing_dependency_is_not_an_intentional_skip[s_dep_import]` | passed |
| `test_suite_with_no_tests_could_not_execute` | passed |
| `test_missing_suite_directory_fails` | passed |
| `test_suite_that_mutates_the_tree_fails_the_run` | passed |
| `test_missing_required_step_fails` | passed |
| `test_runner_refuses_nonempty_or_in_tree_log_dir` | passed |
| `test_comparison_with_reference_never_modifies_it` | passed |
| `test_repository_guard_fails_reverts_and_sets_exit_status` | passed |
| `test_repository_guard_is_silent_for_clean_tests` | passed |

14 of 14 passed.
