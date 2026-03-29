#!/usr/bin/env bash
# Validates all /code-review artifacts exist and contain required content.
# Usage: validate-review-artifacts.sh
# Exit 0 = all checks pass, Exit 1 = failures found
set -euo pipefail
BASE="${HOME}/.claude"
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

# --- Frontmatter check helper ---
has_frontmatter() {
  local count
  count=$(grep -c "^---" "$1" 2>/dev/null || echo 0)
  if [ "$count" -ge 2 ]; then
    echo "PASS: '$1' has YAML frontmatter"
  else
    echo "FAIL: '$1' missing YAML frontmatter (need two --- delimiters)"
    FAILURES=$((FAILURES + 1))
  fi
}

# --- Minimum content size helper (agent files should be substantive) ---
min_lines() {
  local lines
  lines=$(wc -l < "$1" 2>/dev/null || echo 0)
  if [ "$lines" -ge "$2" ]; then
    echo "PASS: '$1' has $lines lines (min $2)"
  else
    echo "FAIL: '$1' has $lines lines (expected min $2)"
    FAILURES=$((FAILURES + 1))
  fi
}

# --- New agents ---
for agent in bug-catcher security-reviewer review-calibrator review-deduplicator; do
  exists "$BASE/agents/${agent}.md"
  has_frontmatter "$BASE/agents/${agent}.md"
  check "$BASE/agents/${agent}.md" "^name: ${agent}"
  check "$BASE/agents/${agent}.md" "^tools:"
  check "$BASE/agents/${agent}.md" "^model:"
  min_lines "$BASE/agents/${agent}.md" 30
done

# --- Modified agent ---
exists "$BASE/agents/general-code-reviewer.md"
has_frontmatter "$BASE/agents/general-code-reviewer.md"

# --- Shared references ---
for ref in false-positive-guidance position-anchoring severity-rubric comment-format finding-schema; do
  exists "$BASE/skills/code-review/references/${ref}.md"
done

# --- Skill ---
exists "$BASE/skills/code-review/SKILL.md"
check "$BASE/skills/code-review/SKILL.md" "bug-catcher"
check "$BASE/skills/code-review/SKILL.md" "security-reviewer"
check "$BASE/skills/code-review/SKILL.md" "review-calibrator"
check "$BASE/skills/code-review/SKILL.md" "review-deduplicator"
check "$BASE/skills/code-review/SKILL.md" "general-code-reviewer"
check "$BASE/skills/code-review/SKILL.md" "Phase 4"

# --- Deprecated command ---
check "$BASE/commands/pr-review.md" "DEPRECATED"

exit $(( FAILURES > 0 ? 1 : 0 ))
