#!/usr/bin/env bash
# Wave 3: orchestrator dispatch rewrites.

PLUGIN_ROOT="$(cd "$TESTS_DIR/../.." && pwd)"
SKILLS_DIR="$PLUGIN_ROOT/skills"

OLD_AGENTS_REGEX='python-test-reviewer|python-code-simplification-reviewer|typescript-test-reviewer|typescript-code-simplification-reviewer'

# Wave-3 file list (per plan §Phase 3).
ORCHESTRATORS=(
  "$SKILLS_DIR/polish-code/SKILL.md"
  "$SKILLS_DIR/code-review/SKILL.md"
  "$SKILLS_DIR/implement-plan-tdd/SKILL.md"
  "$SKILLS_DIR/implement-plan-tdd/references/wave-execution-guide.md"
  "$SKILLS_DIR/create-plan-tdd/SKILL.md"
  "$SKILLS_DIR/research-problem/references/agent-guide.md"
)

for f in "${ORCHESTRATORS[@]}"; do
  assert_file_exists "$f" "$(basename $(dirname $f))/$(basename $f) present"
  assert_not_contains "$f" "$OLD_AGENTS_REGEX" "$(basename $(dirname $f))/$(basename $f) no old agent refs"
done

# 3.3 specifics: code-review/SKILL.md has the combined-invocation fallback.
CR="$SKILLS_DIR/code-review/SKILL.md"
assert_contains "$CR" "Combined-invocation fallback" "code-review has Combined-invocation fallback section"
assert_contains "$CR" "issue #7406" "code-review references issue #7406"

# CHANGE_SCOPE DRY guard (Iter-2 Arch M-1): the canonical sentence must NOT
# appear anywhere outside code-review-modes/SKILL.md (was failing post-Wave-1
# because tidy/SKILL.md and auto-tidy/SKILL.md still contained it; the merged
# polish-code/SKILL.md must NOT reintroduce the canonical sentence — it
# delegates to code-review-modes/SKILL.md instead).
AGENTS_DIR="$PLUGIN_ROOT/agents"
change_scope_other_hits=$(grep -rE "ONLY recommend tests for code that was ADDED or MODIFIED" \
  "$AGENTS_DIR" "$SKILLS_DIR" --exclude-dir=tests 2>/dev/null \
  | grep -v "code-review-modes/SKILL.md" | wc -l | tr -d ' ')
assert_equals "0" "$change_scope_other_hits" "CHANGE_SCOPE canonical sentence ONLY in code-review-modes/SKILL.md (post-Wave-3)"

# Phase 3 aggregate validator pass.
SCRIPTS_DIR="$PLUGIN_ROOT/scripts"
if python3 "$SCRIPTS_DIR/validate_consolidation.py" --task 3 >/dev/null 2>&1; then
  pass "validate_consolidation.py --task 3 PASS"
else
  fail "validate_consolidation.py --task 3 FAIL"
fi
