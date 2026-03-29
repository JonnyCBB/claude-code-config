#!/bin/bash
# Verification Script: Live Service Testing Enhancement
# Generated: 2026-03-18

set -euo pipefail

SKILL_DIR="$HOME/.claude/skills/verify-implementation"

PASS_COUNT=0
FAIL_COUNT=0
TOTAL_COUNT=0
FAILURES=()

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
    echo "    ✗ FAIL: $description -- Expected: $expected"
    echo "    Output: $output"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAILURES+=("CHECK $TOTAL_COUNT: $description")
  fi
}

# === Task 1.1: live-testing-guide.md existence and structure ===

run_check \
  "live-testing-guide.md exists" \
  "File exists at references/live-testing-guide.md" \
  test -f "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md has Service Startup section" \
  "Contains '## Service Startup' or '# Service Startup'" \
  grep -q "Service Startup" "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md has Auth Pre-Flight section" \
  "Contains auth pre-flight check documentation" \
  grep -q -i "auth.*pre-flight\|pre-flight.*auth\|Authentication Prerequisites" "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md has Scenario Generation section" \
  "Contains scenario generation heuristics" \
  grep -q "Scenario Generation\|Test Scenario" "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md has Request Construction section" \
  "Contains request construction patterns" \
  grep -q "Request Construction" "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md has Response Validation section" \
  "Contains response validation rules" \
  grep -q "Response Validation" "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md has Result Formatting section" \
  "Contains result formatting templates" \
  grep -q "Result Formatting" "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md documents gcloud ADC login" \
  "Contains gcloud auth application-default" \
  grep -q "gcloud auth application-default" "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md documents service account impersonation" \
  "Contains serviceauth.serviceAccountEmail" \
  grep -q "serviceAccountEmail" "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md documents standard ports" \
  "Contains port 5990 reference" \
  grep -q "5990" "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md documents health check readiness" \
  "Contains grpc.health.v1.Health/Check" \
  grep -q "grpc.health.v1.Health" "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md documents scenario matrix categories" \
  "Contains Happy path, Full input, Feature toggle categories" \
  bash -c 'grep -q "Happy path" "$1" && grep -q "Full input" "$1" && grep -q "Feature toggle" "$1"' _ "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md documents Before/After scenarios" \
  "Contains Before/After scenario category" \
  grep -q "Before/After" "$SKILL_DIR/references/live-testing-guide.md"

run_check \
  "live-testing-guide.md documents objective alignment" \
  "Contains objective alignment in scenario generation" \
  grep -q -i "objective.*alignment\|objective" "$SKILL_DIR/references/live-testing-guide.md"

# === Task 1.2: SKILL.md updates ===

run_check \
  "SKILL.md has Step 8: Live Service Testing" \
  "Contains '## Step 8: Live Service Testing'" \
  grep -q "## Step 8:.*Live Service Testing" "$SKILL_DIR/SKILL.md"

run_check \
  "SKILL.md has 11 steps total" \
  "Contains Step 11" \
  grep -q "## Step 11:" "$SKILL_DIR/SKILL.md"

run_check \
  "SKILL.md Step 5 references Step 8 for Backend API" \
  "Step 5 section mentions Step 8 or Live Service Testing" \
  bash -c 'awk "/## Step 5:/,/## Step 6:/" "$1" | grep -q "Step 8\|Live Service Testing"' _ "$SKILL_DIR/SKILL.md"

run_check \
  "SKILL.md Step 6 has Live Service Testing in strategy table" \
  "Verification Strategy table includes Live Service Testing row" \
  grep -q "Live Service Testing.*Backend API\|Live Service Testing" "$SKILL_DIR/SKILL.md"

run_check \
  "SKILL.md Step 8 references live-testing-guide.md" \
  "Step 8 contains reference to live-testing-guide.md" \
  grep -q "live-testing-guide.md" "$SKILL_DIR/SKILL.md"

run_check \
  "SKILL.md Step 9 is Execute Verification Examples (renumbered from 8)" \
  "Step 9 contains verification examples content" \
  grep -q "## Step 9:.*Verification Examples\|## Step 9:.*Execute Verification" "$SKILL_DIR/SKILL.md"

run_check \
  "SKILL.md Step 10 is Generate Evidence Document (renumbered from 9)" \
  "Step 10 contains evidence document content" \
  grep -q "## Step 10:.*Evidence Document\|## Step 10:.*Generate Evidence" "$SKILL_DIR/SKILL.md"

run_check \
  "SKILL.md Step 11 is Report Results (renumbered from 10)" \
  "Step 11 contains report results content" \
  grep -q "## Step 11:.*Report Results\|## Step 11:.*Report" "$SKILL_DIR/SKILL.md"

run_check \
  "SKILL.md Reference Files section lists live-testing-guide.md" \
  "Reference Files section includes live-testing-guide.md" \
  grep -q "live-testing-guide.md" "$SKILL_DIR/SKILL.md"

# === Task 1.3: domain-strategies.md updates ===

run_check \
  "domain-strategies.md no longer says 'Assumes the service is already running'" \
  "String 'Assumes the service is already running' is absent" \
  bash -c '! grep -q "Assumes the service is already running" "$1"' _ "$SKILL_DIR/references/domain-strategies.md"

run_check \
  "domain-strategies.md references live-testing-guide.md" \
  "Contains reference to live-testing-guide.md" \
  grep -q "live-testing-guide.md" "$SKILL_DIR/references/domain-strategies.md"

# === Task 1.4: output-template.md updates ===

run_check \
  "output-template.md has Live Service Testing Results section" \
  "Contains '## Live Service Testing Results'" \
  grep -q "Live Service Testing Results" "$SKILL_DIR/references/output-template.md"

run_check \
  "output-template.md has scenario summary table" \
  "Contains Scenario and Key Input Variations columns" \
  grep -q "Scenario.*Key Input Variations\|Key Input Variations" "$SKILL_DIR/references/output-template.md"

run_check \
  "output-template.md has expandable details pattern" \
  "Contains <details> HTML tag for expandable scenarios" \
  grep -q "<details>" "$SKILL_DIR/references/output-template.md"

run_check \
  "output-template.md scenario details include Objective field" \
  "Contains Objective field in scenario template" \
  grep -q "Objective" "$SKILL_DIR/references/output-template.md"

# === Summary ===

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
