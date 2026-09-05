#!/usr/bin/env bash
# Test runner for the agent-deck pre-close guard.
#
# Usage:  bash hooks/tests/run-tests.sh
#
# The exit code IS the number of failing modules, matching the convention in
# plugins/jbb-feature-dev/agents/tests/lib/assertions.sh.
#
# Two deliberate properties, both because this repo has produced several checks
# that could only ever pass:
#
#   1. Finding ZERO test modules is a FAILURE, not a pass. Without this, a
#      mistyped glob or a moved directory exits 0 and every later gate becomes
#      vacuous while still looking green.
#   2. EXPECT_BOOTSTRAP_RED=1 makes the bootstrap module fail on purpose, which
#      must produce a non-zero exit. That proves this runner can report a
#      failure at all. Precedent: elicit-requirements-friendly/tests/verify-skill.sh.

set -uo pipefail
TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAILS=0
COUNT=0
OUT="$(mktemp -t preclose-test-out.XXXXXX)"
trap 'rm -f "$OUT"' EXIT

shopt -s nullglob
for module in "$TESTS_DIR"/test_*.py; do
  COUNT=$((COUNT + 1))
  name="$(basename "$module")"
  if python3 "$module" >"$OUT" 2>&1; then
    echo "  PASS: $name"
  else
    FAILS=$((FAILS + 1))
    echo "  FAIL: $name"
    sed 's/^/        /' "$OUT"
  fi
done

echo
if [ "$COUNT" -eq 0 ]; then
  echo "Results: NO TEST MODULES FOUND in $TESTS_DIR - treating as failure."
  echo "A test runner that finds nothing must not report success."
  exit 1
fi
if [ "$FAILS" -eq 0 ]; then
  echo "Results: $COUNT module(s) passed."
else
  echo "Results: $FAILS of $COUNT module(s) failed."
fi
exit "$FAILS"
