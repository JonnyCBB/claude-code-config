#!/bin/bash
# Verification Script: [DESCRIPTION]
# Generated: [DATE]
# Plan: [PLAN_PATH]
#
# Run this script to reproduce all verification checks.
# Each check prints its description and expected outcome before executing.

set -euo pipefail

PASS_COUNT=0
FAIL_COUNT=0
TOTAL_COUNT=0
FAILURES=()

# Run a single verification check
# Usage: run_check "Description of what this verifies" "Expected outcome" <command...>
run_check() {
  local description="$1"
  local expected="$2"
  shift 2

  TOTAL_COUNT=$((TOTAL_COUNT + 1))
  echo ""
  echo "─── CHECK $TOTAL_COUNT: $description"
  echo "    Expected: $expected"

  if output=$("$@" 2>&1); then
    echo "    ✓ PASS: $description"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "    ✗ FAIL: $description — Expected: $expected"
    echo "    Output: $output"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAILURES+=("CHECK $TOTAL_COUNT: $description")
  fi
}

# --- Checks ---

# Example checks (replace with actual checks):

# run_check \
#   "SKILL.md exists at expected path" \
#   "File exists and is non-empty" \
#   test -s ${CLAUDE_PLUGIN_ROOT}/skills/verify/SKILL.md

# run_check \
#   "SKILL.md has valid YAML frontmatter" \
#   "Frontmatter contains name: verify" \
#   grep -q "^name: verify" ${CLAUDE_PLUGIN_ROOT}/skills/verify/SKILL.md

# run_check \
#   "No references to deleted validate-plan command" \
#   "Zero matches for validate.plan in commands/" \
#   bash -c '[ $(grep -r "validate.plan" ${CLAUDE_PLUGIN_ROOT}/commands/ --include="*.md" -l 2>/dev/null | wc -l) -eq 0 ]'

# --- Summary ---

echo ""
echo "═══════════════════════════════════"
echo " VERIFICATION SUMMARY"
echo "═══════════════════════════════════"
echo " Total:  $TOTAL_COUNT"
echo " Passed: $PASS_COUNT"
echo " Failed: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -gt 0 ]; then
  echo " FAILED CHECKS:"
  for f in "${FAILURES[@]}"; do
    echo "   - $f"
  done
  echo ""
  echo " VERDICT: FAIL"
  exit 1
else
  echo " VERDICT: PASS"
  exit 0
fi
