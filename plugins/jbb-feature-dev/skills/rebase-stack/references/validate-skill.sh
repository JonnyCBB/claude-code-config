#!/usr/bin/env bash
# Validates all /rebase-stack skill artifacts.
# Usage: bash validate-skill.sh
# Exit 0 = all checks pass, Exit 1 = failures found
set -euo pipefail
BASE="${HOME}/.claude/plugins/jbb-feature-dev"
SKILL="$BASE/skills/rebase-stack"
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

# === SKILL.md ===
echo "=== SKILL.md ==="
exists "$SKILL/SKILL.md"
has_frontmatter "$SKILL/SKILL.md"
check "$SKILL/SKILL.md" "^name: rebase-stack"
check "$SKILL/SKILL.md" "Use when"
# Structural: arguments, mode detection, reference file pointers
check "$SKILL/SKILL.md" "scoping-doc"
check "$SKILL/SKILL.md" "non-interactive"
check "$SKILL/SKILL.md" "references/cascade-rebase.md"
check "$SKILL/SKILL.md" "references/conflict-handling.md"
# Functional: key git commands/concepts that must be documented
check "$SKILL/SKILL.md" "rebase --onto"
check "$SKILL/SKILL.md" "force-with-lease"
check "$SKILL/SKILL.md" "Branch Chain"
min_lines "$SKILL/SKILL.md" 120

# === cascade-rebase.md ===
echo ""
echo "=== cascade-rebase.md ==="
exists "$SKILL/references/cascade-rebase.md"
# Functional: key git commands that must be documented
check "$SKILL/references/cascade-rebase.md" "rebase --onto"
check "$SKILL/references/cascade-rebase.md" "update-refs"
check "$SKILL/references/cascade-rebase.md" "force-with-lease"
check "$SKILL/references/cascade-rebase.md" "stackBaseCommit"
check "$SKILL/references/cascade-rebase.md" "git config"
# Cross-reference to sibling
check "$SKILL/references/cascade-rebase.md" "conflict-handling.md"
min_lines "$SKILL/references/cascade-rebase.md" 80

# === conflict-handling.md ===
echo ""
echo "=== conflict-handling.md ==="
exists "$SKILL/references/conflict-handling.md"
# Functional: key git commands and concepts
check "$SKILL/references/conflict-handling.md" "REBASE_HEAD"
check "$SKILL/references/conflict-handling.md" "rebase --abort"
check "$SKILL/references/conflict-handling.md" "rebase --continue"
# Structural: both modes documented
check "$SKILL/references/conflict-handling.md" "interactive"
check "$SKILL/references/conflict-handling.md" "non-interactive"
min_lines "$SKILL/references/conflict-handling.md" 60

# === Plugin validators ===
echo ""
echo "=== Plugin validators ==="
echo "Run separately:"
echo "  python3 $BASE/scripts/validate_skill_descriptions.py"
echo "  python3 ~/.claude/skills/skill-creator/scripts/quick_validate.py $SKILL/"

echo ""
echo "=== Summary ==="
if [ "$FAILURES" -eq 0 ]; then
  echo "ALL CHECKS PASSED"
else
  echo "$FAILURES CHECK(S) FAILED"
fi
exit $(( FAILURES > 0 ? 1 : 0 ))
