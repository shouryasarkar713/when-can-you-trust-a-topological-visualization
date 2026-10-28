#!/usr/bin/env bash
# Clean-copy / fresh-environment reproducibility test (task T12).
#
# Procedure (every step logged with its exit status):
#   1. Export a CLEAN COPY of the current source state.
#      NOTE ON "clean clone": git commits are not permitted in this
#      workspace, so `git clone` would only contain the last commit, not
#      the current working tree. The task instruction allows "a separate
#      clean clone or clean exported copy" — we export the CURRENT working
#      tree with rsync, excluding environments and caches (.venv,
#      __pycache__, .pytest_cache, *.pyc) and the repro log itself.
#   2. Create a FRESH virtual environment with Python 3.12 in the copy.
#   3. Install the pinned dependencies (documented procedure).
#   4. Run environment verification, the test suite, E1, E2, and the
#      figure regeneration IN THE COPY.
#   5. Compare the copy's outputs against the reference run
#      (scripts/compare_runs.py) from the reference repository.
#
# Usage: scripts/clean_clone_test.sh [target_dir]
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-$REPO_ROOT/../scikit-tda-trust-cleanclone}"
LOG_DIR="$REPO_ROOT/results/repro"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/clean_clone_test.log"

step() { echo; echo "=== [$(date -u '+%H:%M:%S')] $1 ==="; }
status() { echo "    exit status: $1"; }

{
step "Clean-copy reproducibility test started: $(date -u)"
echo "Reference : $REPO_ROOT"
echo "Candidate : $TARGET"
echo "Python    : $(python3.12 --version 2>&1)"

step "1. Export clean copy of the current source state"
rm -rf "$TARGET"
mkdir -p "$TARGET"
# NOTE: results/repro/comparison_report.json IS exported (it is part of the
# repository state and the capability matrix cites it); only the live log is
# excluded because it is being written during the rsync.
rsync -a \
  --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' \
  --exclude='*.pyc' --exclude='clean_clone_test.log' \
  "$REPO_ROOT/" "$TARGET/"
status $?

step "2. Fresh virtual environment (Python 3.12) in the candidate copy"
( cd "$TARGET" && python3.12 -m venv .venv )
status $?

step "3. Install pinned dependencies (documented procedure)"
( cd "$TARGET" && .venv/bin/pip install --upgrade pip -q \
    && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt -q )
status $?

step "3b. Record environment of the candidate"
( cd "$TARGET" && .venv/bin/python --version \
    && .venv/bin/python -c "import importlib.metadata as md; \
print({p: md.version(p) for p in ['ripser','persim','kmapper','scikit-learn','numpy','scipy','matplotlib','networkx']})" )
status $?

step "4a. Environment verification in the candidate"
( cd "$TARGET" && .venv/bin/python scripts/verify_env.py )
status $?

step "4b. Test suite in the candidate"
( cd "$TARGET" && .venv/bin/python -m pytest tests/ -q )
status $?

step "4c. E1 pipeline in the candidate"
( cd "$TARGET" && .venv/bin/python scripts/run_e1_audit.py )
status $?

step "4d. E2 pipeline (24-cell grid + sanity control) in the candidate"
( cd "$TARGET" && .venv/bin/python scripts/run_e2_sensitivity.py )
status $?

step "4e. Figure regeneration from saved results in the candidate"
( cd "$TARGET" && .venv/bin/python src/figures.py --all )
status $?

step "4f. E3 inspection MATERIALS regeneration in the candidate"
( cd "$TARGET" && .venv/bin/python scripts/run_e3_readability.py )
status $?

step "4g. E3 inspection-record analysis in the candidate (authored record,"
echo "      rsync-copied verbatim; the analyzer only validates + summarizes)"
( cd "$TARGET" && .venv/bin/python scripts/analyze_e3_inspection.py )
status $?

step "5. Compare candidate outputs against the reference run"
( cd "$REPO_ROOT" && .venv/bin/python scripts/compare_runs.py \
    --candidate "$TARGET" )
CMP=$?
status $CMP

step "Summary"
echo "Comparison exit status: $CMP (0 = all structural outputs identical)"
echo "Report: $REPO_ROOT/results/repro/comparison_report.json"
echo "NOTE: this is a clean EXPORTED SOURCE COPY test (rsync of the working"
echo "tree), not a git clone — git commits are not permitted in this"
echo "workspace, so a clone would miss the current source state (D-8)."
if [ $CMP -ne 0 ]; then
  echo "RESULT: REPRODUCIBILITY TEST FAILED — inspect the report."
else
  echo "RESULT: clean-copy rerun structurally identical to the reference."
fi
} 2>&1 | tee "$LOG"

# Propagate the comparison result as the script's exit status
grep -q "Comparison exit status: 0" "$LOG"
