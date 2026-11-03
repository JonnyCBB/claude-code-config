#!/usr/bin/env bash
# Wave 2: registry surgery + workflow audit invariants.
#
# 2.1 language-agent-registry.md collapsed to 4-col with Expert Agent column
# 2.2 domain-agent-registry.md present

PLUGIN_ROOT="$(cd "$TESTS_DIR/../.." && pwd)"
SHARED_REF="$PLUGIN_ROOT/skills/shared-references"

# === 2.1: language-agent-registry.md ===
LANG_REG="$SHARED_REF/language-agent-registry.md"
assert_file_exists "$LANG_REG" "language-agent-registry.md present"
assert_contains "$LANG_REG" "Expert Agent" "language registry has 'Expert Agent' column heading"
for new in python-expert typescript-expert; do
  assert_contains "$LANG_REG" "$new" "language registry references $new"
done
for old in python-test-reviewer python-code-simplification-reviewer typescript-test-reviewer typescript-code-simplification-reviewer; do
  assert_not_contains "$LANG_REG" "$old" "language registry no longer references $old"
done

# === 2.2: domain-agent-registry.md ===
DOM_REG="$SHARED_REF/domain-agent-registry.md"
assert_file_exists "$DOM_REG" "domain-agent-registry.md present"

# Phase 2 aggregate validator pass.
SCRIPTS_DIR="$PLUGIN_ROOT/scripts"
if python3 "$SCRIPTS_DIR/validate_consolidation.py" --task 2 >/dev/null 2>&1; then
  pass "validate_consolidation.py --task 2 PASS"
else
  fail "validate_consolidation.py --task 2 FAIL"
fi
