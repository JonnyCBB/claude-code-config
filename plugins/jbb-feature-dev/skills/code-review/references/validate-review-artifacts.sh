#!/usr/bin/env bash
# Validates all /code-review artifacts exist and contain required content.
# Usage: validate-review-artifacts.sh
# Exit 0 = all checks pass, Exit 1 = failures found
set -euo pipefail
# Resolve BASE to the plugin root (works whether invoked from repo root or absolutely)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="$(cd "$SCRIPT_DIR/../../.." && pwd)"
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
for agent in bug-catcher security-reviewer review-calibrator review-deduplicator laidx-reviewer; do
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
check "$BASE/skills/code-review/SKILL.md" "laidx-reviewer"
check "$BASE/skills/code-review/SKILL.md" "general-code-reviewer"
check "$BASE/skills/code-review/SKILL.md" "Phase 4"

# --- Deprecated skill (lives at repo root, not in plugin) ---
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
check "$REPO_ROOT/skills/pr-review/SKILL.md" "DEPRECATED"

# --- Gap closure: new agents ---
for agent in repo-rules-reviewer quality-checker; do
  exists "$BASE/agents/${agent}.md"
  has_frontmatter "$BASE/agents/${agent}.md"
  check "$BASE/agents/${agent}.md" "^name: ${agent}"
  check "$BASE/agents/${agent}.md" "^tools:"
  check "$BASE/agents/${agent}.md" "^model:"
  min_lines "$BASE/agents/${agent}.md" 30
done

# --- Gap closure: new reference ---
exists "$BASE/skills/code-review/references/quality-check-dimensions.md"
check "$BASE/skills/code-review/references/quality-check-dimensions.md" "Coverage"
check "$BASE/skills/code-review/references/quality-check-dimensions.md" "Depth"
check "$BASE/skills/code-review/references/quality-check-dimensions.md" "Actionability"
check "$BASE/skills/code-review/references/quality-check-dimensions.md" "Accuracy"
check "$BASE/skills/code-review/references/quality-check-dimensions.md" "Noise"
check "$BASE/skills/code-review/references/quality-check-dimensions.md" "Factual"

# --- Gap 1: repo-rules-reviewer content ---
check "$BASE/agents/repo-rules-reviewer.md" "GOSLING.md"
check "$BASE/agents/repo-rules-reviewer.md" "coding guidelines"
check "$BASE/agents/repo-rules-reviewer.md" "severity.*bypass\|bypass.*severity"
check "$BASE/agents/repo-rules-reviewer.md" "CONTRIBUTING"

# --- Gap 4: quality-checker content ---
check "$BASE/agents/quality-checker.md" "coverage"
check "$BASE/agents/quality-checker.md" "actionability"
check "$BASE/agents/quality-checker.md" "single-pass"

# --- Gap 6: calibrator executable verification ---
check "$BASE/agents/review-calibrator.md" "executable"
check "$BASE/agents/review-calibrator.md" "grep"

# --- Gap 5: deduplicator prior comment tracking ---
check "$BASE/agents/review-deduplicator.md" "prior review"
check "$BASE/agents/review-deduplicator.md" "agree.*disagree\|Agree.*Disagree"

# --- SKILL.md gap references ---
check "$BASE/skills/code-review/SKILL.md" "repo-rules-reviewer"
check "$BASE/skills/code-review/SKILL.md" "quality-checker"
check "$BASE/skills/code-review/SKILL.md" "GOSLING.md"
check "$BASE/skills/code-review/SKILL.md" "gosling.yaml\|code-review.yaml"
check "$BASE/skills/code-review/SKILL.md" "incremental"
check "$BASE/skills/code-review/SKILL.md" "50K token\|large PR"
check "$BASE/skills/code-review/SKILL.md" "quality-check-dimensions"

exit $(( FAILURES > 0 ? 1 : 0 ))
