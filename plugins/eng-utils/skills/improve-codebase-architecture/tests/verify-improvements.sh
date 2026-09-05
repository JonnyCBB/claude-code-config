#!/usr/bin/env bash
# Verify improve-codebase-architecture skill improvements are correctly applied.
# Usage: bash tests/verify-improvements.sh
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILS=0
PASSES=0

assert_contains() {
  local file="$1" pattern="$2" desc="$3"
  if grep -qE -- "$pattern" "$file"; then
    PASSES=$((PASSES+1))
    echo "  PASS: $desc"
  else
    FAILS=$((FAILS+1))
    echo "  FAIL: $desc (pattern not found in $file: $pattern)"
  fi
}

assert_not_contains() {
  local file="$1" pattern="$2" desc="$3"
  if ! grep -qE -- "$pattern" "$file"; then
    PASSES=$((PASSES+1))
    echo "  PASS: $desc"
  else
    FAILS=$((FAILS+1))
    echo "  FAIL: $desc (pattern unexpectedly present in $file: $pattern)"
  fi
}

# === Prior round assertions (2026-04-27) ===

# Task 1.1: friction-patterns.md
F="$SKILL_DIR/references/friction-patterns.md"
assert_contains "$F" "### The Deletion Test" "Deletion Test heading present"
assert_contains "$F" "Imagine deleting the module" "Deletion Test quote present"
assert_contains "$F" "complecting|Complecting" "Complecting term present"
assert_contains "$F" "complectere" "Complecting Latin etymology cited"
assert_contains "$F" "padding the implementation" "Module Depth Score caveat present"
assert_contains "$F" "[Tt]he Deletion Test" "Module Depth Score caveat references Deletion Test"

# Task 1.2: dependency-categories.md
F="$SKILL_DIR/references/dependency-categories.md"
assert_contains "$F" "Two-Adapter Rule|Two-adapter rule" "Two-Adapter Rule heading present"
assert_contains "$F" "[Oo]ne adapter.*hypothetical seam" "Two-Adapter quote part 1 present"
assert_contains "$F" "[Tt]wo adapters.*real seam" "Two-Adapter quote part 2 present"
assert_contains "$F" "internal seam" "Internal seam concept present"
assert_contains "$F" "external seam" "External seam concept present"

# Task 1.3: proposal-template.md
F="$SKILL_DIR/references/proposal-template.md"
assert_contains "$F" "Operational Boundaries" "Operational Boundaries section in template"
assert_contains "$F" "always[- ]do|Always-do|Always do" "always-do bullet present"
assert_contains "$F" "ask[- ]first|Ask-first|Ask first" "ask-first bullet present"
assert_contains "$F" "never[- ]touch|Never-touch|Never touch" "never-touch bullet present"

# === 2026-07-03 round: rename + HTML+crit + citation ===

# Renamed from refactor-architecture: the skill name and its output directory
# must both have moved, with no trace of the old name left behind.
F="$SKILL_DIR/SKILL.md"
assert_contains "$F" "name: improve-codebase-architecture" "SKILL.md frontmatter uses new name"
assert_not_contains "$F" "name: refactor-architecture" "SKILL.md frontmatter no longer uses old name"
assert_contains "$F" "improve-codebase-architecture-proposals" "SKILL.md references new output directory"

# Candidates and designs are presented as HTML reviewed through crit, with a
# read-back of the reviewer's comments, from one shared presentation section.
assert_contains "$F" "HTML.crit|html.*crit|crit.*preview" "SKILL.md references HTML+crit presentation"
assert_contains "$F" "crit preview" "SKILL.md includes crit preview command"
assert_contains "$F" "crit comments --json" "SKILL.md includes crit comments read-back command"
assert_contains "$F" "Presenting Candidates and Designs" "SKILL.md has shared presentation section"

# crit is not assumed present: the skill checks for it and falls back to
# AskUserQuestion, and it stays usable in a non-interactive context.
assert_contains "$F" "which crit" "SKILL.md checks crit availability"
assert_contains "$F" "fallback|Fallback" "SKILL.md documents fallback behavior"
assert_contains "$F" "non-interactive" "SKILL.md handles non-interactive context"

# Phase 2 AUQ (fallback path)
assert_contains "$F" "AskUserQuestion" "Phase 2 references AskUserQuestion"
assert_contains "$F" "Which refactoring candidate" "Phase 2 question text present"
assert_contains "$F" "Candidates" "Phase 2 header chip 'Candidates' present"
assert_contains "$F" "multiSelect: true" "Phase 2 multiSelect flag present"
assert_contains "$F" "Skip refactor" "Phase 2 'Skip refactor' option present"

# Phase 3 AUQ (fallback path)
assert_contains "$F" "before spawning|render.*before.*spawn" "Phase 3 pre-spawn framing instruction present"
assert_contains "$F" "Which interface design" "Phase 3 design AUQ question present"
assert_contains "$F" "Hybrid" "Phase 3 'Hybrid' option present"
assert_contains "$F" "[Cc]onvergence shortcut|all.*agents converge" "Phase 3 convergence shortcut present"

# Phase 4 proposal AUQ
assert_contains "$F" "Ready to write the proposal" "Phase 4 question text present"
assert_contains "$F" "Adjust interface" "Phase 4 'Adjust interface' option present"
assert_contains "$F" "Adjust diagrams" "Phase 4 'Adjust diagrams' option present"

# The proposal template writes to the renamed output directory and names the
# renamed skill, with no reference to the old ones.
F="$SKILL_DIR/references/proposal-template.md"
assert_contains "$F" "improve-codebase-architecture-proposals" "proposal-template.md references new output directory"
assert_not_contains "$F" "refactor-proposals" "proposal-template.md no longer references old output directory"
assert_contains "$F" "improve-codebase-architecture" "proposal-template.md references new skill name"

# The friction-patterns reference cites its source paper by arXiv id, title and
# the specific concept borrowed, so the claim can be checked.
F="$SKILL_DIR/references/friction-patterns.md"
assert_contains "$F" "2604.13108" "friction-patterns.md cites arXiv 2604.13108"
assert_contains "$F" "Formal Architecture Descriptors" "friction-patterns.md cites paper title"
assert_contains "$F" "Navigation Primitives" "friction-patterns.md cites Navigation Primitives"

echo
echo "Results: $PASSES passed, $FAILS failed."
exit "$FAILS"
