#!/usr/bin/env bash
# Wave 5: cleanup invariants.
# - old per-language reviewer agent files deleted
# - Master grep clean
# - Full validator passes

PLUGIN_ROOT="$(cd "$TESTS_DIR/../.." && pwd)"
AGENTS_DIR="$PLUGIN_ROOT/agents"
SKILLS_DIR="$PLUGIN_ROOT/skills"
SCRIPTS_DIR="$PLUGIN_ROOT/scripts"

OLD_AGENTS=(
  python-test-reviewer
  python-code-simplification-reviewer
  typescript-test-reviewer
  typescript-code-simplification-reviewer
)

for a in "${OLD_AGENTS[@]}"; do
  assert_file_absent "$AGENTS_DIR/${a}.md" "${a}.md deleted"
done

# Master grep clean (excludes agents/tests/ and scripts/).
MASTER_GREP_REGEX='python-test-reviewer|python-code-simplification-reviewer|typescript-test-reviewer|typescript-code-simplification-reviewer'
hits=$(grep -rE "$MASTER_GREP_REGEX" "$AGENTS_DIR" "$SKILLS_DIR" --exclude-dir=tests --exclude-dir=scripts 2>/dev/null | wc -l | tr -d ' ')
assert_equals "0" "$hits" "master grep clean (excludes tests/ and scripts/)"

# Full validator pass.
if python3 "$SCRIPTS_DIR/validate_consolidation.py" --task all >/dev/null 2>&1; then
  pass "validate_consolidation.py --task all PASS"
else
  fail "validate_consolidation.py --task all FAIL"
fi
