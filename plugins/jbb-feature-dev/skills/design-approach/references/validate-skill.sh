#!/usr/bin/env bash
# Validates all /design-approach skill artifacts.
# Usage: bash validate-skill.sh
# Exit 0 = all checks pass, Exit 1 = failures found
set -euo pipefail
BASE="${HOME}/.claude/plugins/jbb-feature-dev"
SKILL="$BASE/skills/design-approach"
FAILURES=0

check() {
  if ! grep -q "$2" "$1" 2>/dev/null; then
    echo "FAIL: '$1' missing '$2'"
    FAILURES=$((FAILURES + 1))
  else
    echo "PASS: '$1' contains '$2'"
  fi
}

exists() {
  if [ ! -f "$1" ]; then
    echo "FAIL: File not found: $1"
    FAILURES=$((FAILURES + 1))
  else
    echo "PASS: File exists: $1"
  fi
}

has_frontmatter() {
  local count
  count=$(grep -c "^---" "$1" 2>/dev/null || echo 0)
  if [ "$count" -ge 2 ]; then
    echo "PASS: '$1' has YAML frontmatter"
  else
    echo "FAIL: '$1' missing YAML frontmatter"
    FAILURES=$((FAILURES + 1))
  fi
}

min_lines() {
  local lines
  if [ ! -f "$1" ]; then lines=0; else lines=$(wc -l < "$1"); fi
  if [ "$lines" -ge "$2" ]; then
    echo "PASS: '$1' has $lines lines (min $2)"
  else
    echo "FAIL: '$1' has $lines lines (expected min $2)"
    FAILURES=$((FAILURES + 1))
  fi
}

echo "=== SKILL.md ==="
exists "$SKILL/SKILL.md"
has_frontmatter "$SKILL/SKILL.md"
check "$SKILL/SKILL.md" "^name: design-approach"
check "$SKILL/SKILL.md" "tension"
check "$SKILL/SKILL.md" "architect"
check "$SKILL/SKILL.md" "comparison"
check "$SKILL/SKILL.md" "non-interactive"
check "$SKILL/SKILL.md" "AskUserQuestion"
check "$SKILL/SKILL.md" "feature_designs"
check "$SKILL/SKILL.md" "decision-principles"
check "$SKILL/SKILL.md" "agent-verification-pattern"
min_lines "$SKILL/SKILL.md" 150

echo ""
echo "=== Reference Files ==="
exists "$SKILL/references/tension-analysis-guide.md"
check "$SKILL/references/tension-analysis-guide.md" "Category A"
check "$SKILL/references/tension-analysis-guide.md" "Category E"
min_lines "$SKILL/references/tension-analysis-guide.md" 50

exists "$SKILL/references/architect-output-format.md"
check "$SKILL/references/architect-output-format.md" "requirements compliance"
min_lines "$SKILL/references/architect-output-format.md" 30

exists "$SKILL/references/comparison-template.md"
check "$SKILL/references/comparison-template.md" "recommendation"
min_lines "$SKILL/references/comparison-template.md" 30

exists "$SKILL/references/decision-document-template.md"
check "$SKILL/references/decision-document-template.md" "feature_designs"
check "$SKILL/references/decision-document-template.md" "rejected"
min_lines "$SKILL/references/decision-document-template.md" 30

echo ""
echo "=== Pipeline Integration ==="
check "$BASE/skills/research-problem/references/document-template.md" \
  "Design Exploration Recommendation"
check "$BASE/skills/research-problem/references/document-template.md" \
  "design-approach"
check "$BASE/skills/create-plan-tdd/SKILL.md" "design decision"

echo ""
echo "=== Summary ==="
if [ "$FAILURES" -eq 0 ]; then
  echo "ALL CHECKS PASSED"
else
  echo "$FAILURES CHECK(S) FAILED"
fi
exit $(( FAILURES > 0 ? 1 : 0 ))
