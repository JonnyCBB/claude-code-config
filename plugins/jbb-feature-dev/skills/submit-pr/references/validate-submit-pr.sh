#!/usr/bin/env bash
# Validates all /submit-pr skill artifacts.
# Usage: bash validate-submit-pr.sh [--wave N]
# Exit 0 = all checks pass, Exit 1 = failures found
set -euo pipefail

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PLUGIN_DIR="$(cd "$SKILL_DIR/../.." && pwd)"
REFS="$SKILL_DIR/references"
QUICK_VALIDATE="${HOME}/.claude/skills/skill-creator/scripts/quick_validate.py"

FAILURES=0
WAVE=2  # Default: full validation

# Parse --wave argument
while [[ $# -gt 0 ]]; do
  case "$1" in
    --wave)
      WAVE="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

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

not_exists() {
  if [ -d "$1" ]; then
    echo "FAIL: Directory should not exist: $1"
    FAILURES=$((FAILURES + 1))
  else
    echo "PASS: Directory does not exist: $1"
  fi
}

echo "=== Wave $WAVE Validation ==="
echo ""

# --- Wave 0: Self-test ---
if [ "$WAVE" -ge 0 ]; then
  echo "--- Wave 0: Script self-test ---"
  if [ -x "$0" ] || [ -f "${BASH_SOURCE[0]}" ]; then
    echo "PASS: Validation script exists"
  else
    echo "FAIL: Validation script not found"
    FAILURES=$((FAILURES + 1))
  fi
fi

# --- Wave 1: Reference file existence ---
if [ "$WAVE" -ge 1 ]; then
  echo ""
  echo "--- Wave 1: Reference files ---"
  exists "$REFS/pr-description-template.md"
  exists "$REFS/diagram-generation.md"
  exists "$REFS/collapsible-format.md"
  exists "$REFS/jira-integration.md"
  exists "$REFS/build-monitoring.md"
  exists "$REFS/slack-notifications.md"
fi

# --- Wave 2: Full validation ---
if [ "$WAVE" -ge 2 ]; then
  echo ""
  echo "--- Wave 2: SKILL.md validation ---"
  exists "$SKILL_DIR/SKILL.md"

  # Run quick_validate.py if available
  if [ -f "$QUICK_VALIDATE" ]; then
    echo ""
    echo "Running quick_validate.py..."
    if python3 "$QUICK_VALIDATE" "$SKILL_DIR" 2>&1; then
      echo "PASS: quick_validate.py passed"
    else
      echo "FAIL: quick_validate.py failed"
      FAILURES=$((FAILURES + 1))
    fi
  else
    echo "WARN: quick_validate.py not found at $QUICK_VALIDATE, skipping"
  fi

  # Check SKILL.md references each reference file
  echo ""
  echo "--- Wave 2: SKILL.md cross-references ---"
  check "$SKILL_DIR/SKILL.md" "references/pr-description-template.md"
  check "$SKILL_DIR/SKILL.md" "references/diagram-generation.md"
  check "$SKILL_DIR/SKILL.md" "references/collapsible-format.md"
  check "$SKILL_DIR/SKILL.md" "references/jira-integration.md"
  check "$SKILL_DIR/SKILL.md" "references/build-monitoring.md"
  check "$SKILL_DIR/SKILL.md" "references/slack-notifications.md"

  # Check SKILL.md has required sections
  echo ""
  echo "--- Wave 2: SKILL.md sections ---"
  check "$SKILL_DIR/SKILL.md" "## Phase 1"
  check "$SKILL_DIR/SKILL.md" "## Phase 2"
  check "$SKILL_DIR/SKILL.md" "## Phase 3"
  check "$SKILL_DIR/SKILL.md" "## Reference Files"
  check "$SKILL_DIR/SKILL.md" "## Arguments"

  # Check integration points
  echo ""
  echo "--- Wave 2: Integration ---"
  check "$PLUGIN_DIR/README.md" "/submit-pr"
  check "$PLUGIN_DIR/.claude-plugin/plugin.json" "submit-pr"

  # Check old pr-description directory does NOT exist
  not_exists "$PLUGIN_DIR/skills/pr-description"

  # Check for stale pr-description references (exclude this script)
  echo ""
  echo "--- Wave 2: Stale references ---"
  # Look for stale references to the old skill (skill name, skill path, or slash command)
  # but exclude the legitimate reference file name "pr-description-template.md"
  STALE=$(grep -rn "pr-description" "$PLUGIN_DIR/" --include="*.md" --include="*.json" --include="*.sh" 2>/dev/null \
    | grep -v "references/validate-submit-pr.sh" \
    | grep -v "pr-description-template" \
    || true)
  # Extract just the filenames for display
  STALE=$(echo "$STALE" | grep -v "^$" | cut -d: -f1 | sort -u || true)
  if [ -z "$STALE" ]; then
    echo "PASS: No stale pr-description references found"
  else
    echo "FAIL: Stale pr-description references found in:"
    echo "$STALE"
    FAILURES=$((FAILURES + 1))
  fi
fi

echo ""
echo "=== Summary ==="
if [ "$FAILURES" -eq 0 ]; then
  echo "ALL CHECKS PASSED"
else
  echo "$FAILURES CHECK(S) FAILED"
fi
exit $(( FAILURES > 0 ? 1 : 0 ))
