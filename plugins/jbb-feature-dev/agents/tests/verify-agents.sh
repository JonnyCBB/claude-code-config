#!/usr/bin/env bash
# Entry point for language-expert consolidation tests.
# Usage: bash agents/tests/verify-agents.sh [--wave N]
#
# Discovers tests/test_wave*.sh siblings and sources each (or only the matching
# wave when --wave is supplied). Sourcing lets the per-file scripts share
# PASSES/FAILS counters from lib/assertions.sh.
#
# Per-task RED isolation in this harness:
#   1. Add a new assertion to test_wave<N>.sh BEFORE doing the GREEN edit.
#   2. Run: bash agents/tests/verify-agents.sh --wave <N>
#   3. The new assertion will fail (RED). Implement GREEN. Re-run; assertion passes.
#
# Bootstrap-RED (corrected per plan TDD-1):
#   - Default path: harness runs sanity assertion that PASSES (proves harness works).
#   - EXPECT_BOOTSTRAP_RED=1: sentinel triggers a deliberate FAIL (proves harness
#     reports failures, not silently zeros PASSES).
#
# nullglob ensures an empty match is not treated as a literal.
set -uo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assertions.sh
source "$TESTS_DIR/lib/assertions.sh"

WAVE="all"
if [[ "${1:-}" == "--wave" && -n "${2:-}" ]]; then
  WAVE="$2"
fi

# Bootstrap-RED sentinel — proves the harness can record a failure.
# Default path (no env var) records a sanity PASS instead.
if [[ "${EXPECT_BOOTSTRAP_RED:-0}" == "1" ]]; then
  fail "bootstrap-RED sentinel: deliberate FAIL (verifies harness reports failures)"
else
  pass "harness sanity"
fi

if [[ "$WAVE" == "all" ]]; then
  if python3 "$TESTS_DIR/../../scripts/_lib/tests/test_frontmatter.py"; then
    pass "_lib/tests/test_frontmatter.py PASS"
  else
    fail "_lib/tests/test_frontmatter.py FAIL"
  fi
fi

shopt -s nullglob

target_glob="$TESTS_DIR/test_wave*.sh"
if [[ "$WAVE" != "all" ]]; then
  case "$WAVE" in
    *)       target_glob="$TESTS_DIR/test_wave${WAVE}.sh" ;;
  esac
fi

found_any=0
for test_file in $target_glob; do
  [[ -f "$test_file" ]] || continue
  found_any=1
  echo "Running ${test_file##*/}..."
  # shellcheck source=/dev/null
  source "$test_file"
done

if [[ "$WAVE" != "all" && "$found_any" == "0" ]]; then
  fail "no test file matching --wave $WAVE"
fi

summary
