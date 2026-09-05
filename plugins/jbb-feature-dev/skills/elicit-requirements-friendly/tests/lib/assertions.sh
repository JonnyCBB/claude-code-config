#!/usr/bin/env bash
# Shared assertion helpers for elicit-requirements-friendly skill tests.
# Sourced by tests/verify-skill.sh and the per-file test_*.sh scripts.

PASSES=${PASSES:-0}
FAILS=${FAILS:-0}

assert_contains() {
  local file="$1" pattern="$2" desc="$3"
  if grep -qE -- "$pattern" "$file" 2>/dev/null; then
    PASSES=$((PASSES+1))
    echo "  PASS: $desc"
  else
    FAILS=$((FAILS+1))
    echo "  FAIL: $desc (pattern not found in $file: $pattern)"
  fi
}

assert_not_contains() {
  local file="$1" pattern="$2" desc="$3"
  if ! grep -qE -- "$pattern" "$file" 2>/dev/null; then
    PASSES=$((PASSES+1))
    echo "  PASS: $desc"
  else
    FAILS=$((FAILS+1))
    echo "  FAIL: $desc (pattern unexpectedly present in $file: $pattern)"
  fi
}

summary() {
  echo
  echo "Results: $PASSES passed, $FAILS failed."
  exit "$FAILS"
}
