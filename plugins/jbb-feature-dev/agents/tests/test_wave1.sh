#!/usr/bin/env bash
# Wave 1: 9 parallel new-artifact invariants.
#
# 1.1: code-review-modes/SKILL.md
# 1.2: 2 verbatim schema files
# 1.5-1.6: 2 {language}-expert agent files
# 1.7: code-style-common/test-anti-patterns.md additions
# 1.8: 2 per-language testing-patterns pointer stubs

PLUGIN_ROOT="$(cd "$TESTS_DIR/../.." && pwd)"
SKILLS_DIR="$PLUGIN_ROOT/skills"
AGENTS_DIR="$PLUGIN_ROOT/agents"
SCRIPTS_DIR="$PLUGIN_ROOT/scripts"

# === 1.1: code-review-modes/SKILL.md ===
SKILL_MD="$SKILLS_DIR/code-review-modes/SKILL.md"
assert_file_exists "$SKILL_MD" "code-review-modes/SKILL.md present"
for heading in "## Plan Mode" "## Implement Mode" "## Test-Review Mode" "## Code-Style-Review Mode" "## Deep-Analysis Mode"; do
  assert_contains "$SKILL_MD" "$heading" "code-review-modes defines section: $heading"
done
assert_contains "$SKILL_MD" "Precedence" "code-review-modes precedence section present"
assert_contains "$SKILL_MD" "deep-analysis" "code-review-modes mentions deep-analysis"
assert_contains "$SKILL_MD" "caller-explicit-only" "code-review-modes deep-analysis precedence rule (Arch-4)"
assert_contains "$SKILL_MD" "default mode" "code-review-modes default-mode rule"
assert_contains "$SKILL_MD" "## CHANGE_SCOPE" "CHANGE_SCOPE inlined as section (Simp-S2)"
assert_contains "$SKILL_MD" "ONLY recommend tests for code that was ADDED or MODIFIED" "CHANGE_SCOPE canonical rule preserved"
assert_contains "$SKILL_MD" "specific line ranges" "CHANGE_SCOPE detail preserved"

# CHANGE_SCOPE DRY guard (Iter-2 Arch M-1): canonical sentence must NOT appear
# anywhere outside code-review-modes/SKILL.md.
change_scope_other_hits=$(grep -rE "ONLY recommend tests for code that was ADDED or MODIFIED" \
  "$AGENTS_DIR" "$SKILLS_DIR" --exclude-dir=tests 2>/dev/null \
  | grep -v "code-review-modes/SKILL.md" | wc -l | tr -d ' ')
assert_equals "0" "$change_scope_other_hits" "CHANGE_SCOPE canonical sentence ONLY in code-review-modes/SKILL.md"

# === 1.2: 2 verbatim schema files ===
for lang in python typescript; do
  SCHEMA="$SKILLS_DIR/code-review-modes/schemas/${lang}.md"
  assert_file_exists "$SCHEMA" "schemas/${lang}.md present"
  assert_contains "$SCHEMA" "## Test-Review Schema" "schemas/${lang}.md has Test-Review Schema section"
  assert_contains "$SCHEMA" "## Code-Style-Review Schema" "schemas/${lang}.md has Code-Style-Review Schema section"
  assert_not_contains "$SCHEMA" "TEST_NEEDED" "schemas/${lang}.md no underscore-form TEST_NEEDED (Arch-7)"
  assert_not_contains "$SCHEMA" "REDUNDANT_TEST" "schemas/${lang}.md no underscore-form REDUNDANT_TEST"
  assert_not_contains "$SCHEMA" "QUALITY_ISSUE" "schemas/${lang}.md no underscore-form QUALITY_ISSUE"
  assert_contains "$SCHEMA" "TEST NEEDED" "schemas/${lang}.md preserves TEST NEEDED block (space-form)"
  assert_contains "$SCHEMA" "REDUNDANT TEST" "schemas/${lang}.md preserves REDUNDANT TEST block (space-form)"
  assert_contains "$SCHEMA" "QUALITY ISSUE" "schemas/${lang}.md preserves QUALITY ISSUE block (space-form)"
  assert_contains "$SCHEMA" "^ISSUE" "schemas/${lang}.md preserves ISSUE block in code-style schema"
done

# Run verbatim helper across all schemas.
if python3 "$SCRIPTS_DIR/verbatim_preserved.py" --check-all >/dev/null 2>&1; then
  pass "verbatim_preserved.py --check-all PASS"
else
  fail "verbatim_preserved.py --check-all reported a failure"
fi

# === 1.5-1.6: 2 {language}-expert agent files (delegated to validator) ===
for agent in python-expert typescript-expert; do
  assert_file_exists "$AGENTS_DIR/${agent}.md" "${agent}.md present"
done
if python3 "$SCRIPTS_DIR/validate_consolidation.py" --task 1.5 >/dev/null 2>&1; then
  pass "validate_consolidation.py --task 1.5 (python-expert) PASS"
else
  fail "validate_consolidation.py --task 1.5 (python-expert) FAIL"
fi
if python3 "$SCRIPTS_DIR/validate_consolidation.py" --task 1.6 >/dev/null 2>&1; then
  pass "validate_consolidation.py --task 1.6 (typescript-expert) PASS"
else
  fail "validate_consolidation.py --task 1.6 (typescript-expert) FAIL"
fi

# === 1.7: test-anti-patterns.md additions ===
ANTI="$SKILLS_DIR/code-style-common/test-anti-patterns.md"
assert_file_exists "$ANTI" "test-anti-patterns.md present"
assert_contains "$ANTI" "## Anti-Pattern 8: Missing Feature Assertion" "Anti-Pattern 8 (Missing Feature Assertion) added"
assert_contains "$ANTI" "MissingFeatureAssertion" "MissingFeatureAssertion sub-type"
assert_contains "$ANTI" "TestNameAssertionMismatch" "TestNameAssertionMismatch rule (Skill DRY single source)"
assert_contains "$ANTI" "VagueNaming" "VagueNaming rule (Skill DRY single source)"
assert_contains "$ANTI" "MissingContext" "MissingContext rule (Skill DRY single source)"
assert_contains "$ANTI" "is_ai_overview" "lifted Java domain example present"

# === 1.8: 2 testing-patterns pointer stubs ===
PYTHON_TP="$SKILLS_DIR/python-code-style/testing-patterns.md"
TS_TP="$SKILLS_DIR/typescript-code-style/testing-patterns.md"

assert_file_exists "$PYTHON_TP" "python testing-patterns.md present"
assert_contains "$PYTHON_TP" "code-style-common/test-anti-patterns.md" "python stub points to canonical (Skill DRY)"
assert_contains "$PYTHON_TP" "pytest" "python stub has pytest example"

assert_file_exists "$TS_TP" "typescript testing-patterns.md present"
assert_contains "$TS_TP" "code-style-common/test-anti-patterns.md" "typescript stub points to canonical"
assert_contains "$TS_TP" "RTL|Vitest|@testing-library" "typescript stub has RTL/Vitest example"


# Phase 1 aggregate validator pass.
if python3 "$SCRIPTS_DIR/validate_consolidation.py" --task 1 >/dev/null 2>&1; then
  pass "validate_consolidation.py --task 1 aggregate PASS"
else
  fail "validate_consolidation.py --task 1 aggregate FAIL"
fi
