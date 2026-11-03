#!/usr/bin/env bash
# Shared assertion helpers for language-expert consolidation tests.
# Sourced by verify-agents.sh and per-wave test_wave*.sh scripts.

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

assert_file_exists() {
  local file="$1" desc="${2:-file exists: $1}"
  if [[ -f "$file" ]]; then
    PASSES=$((PASSES+1))
    echo "  PASS: $desc"
  else
    FAILS=$((FAILS+1))
    echo "  FAIL: $desc (file not found: $file)"
  fi
}

assert_file_absent() {
  local file="$1" desc="${2:-file absent: $1}"
  if [[ ! -e "$file" ]]; then
    PASSES=$((PASSES+1))
    echo "  PASS: $desc"
  else
    FAILS=$((FAILS+1))
    echo "  FAIL: $desc (file unexpectedly present: $file)"
  fi
}

assert_equals() {
  local expected="$1" actual="$2" desc="${3:-values equal}"
  if [[ "$expected" == "$actual" ]]; then
    PASSES=$((PASSES+1))
    echo "  PASS: $desc"
  else
    FAILS=$((FAILS+1))
    echo "  FAIL: $desc (expected '$expected', got '$actual')"
  fi
}

pass() {
  PASSES=$((PASSES+1))
  echo "  PASS: ${1:-(unnamed)}"
}

fail() {
  FAILS=$((FAILS+1))
  echo "  FAIL: ${1:-(unnamed)}"
}

summary() {
  echo
  echo "Results: $PASSES passed, $FAILS failed."
  exit "$FAILS"
}
