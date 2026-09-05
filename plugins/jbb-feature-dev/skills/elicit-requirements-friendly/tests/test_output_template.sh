#!/usr/bin/env bash
# Asserts content properties of references/output-template.md.

F="$SKILL_DIR/references/output-template.md"

# Sections inherited from elicit-requirements (downstream contract)
assert_contains "$F" "## Objective" "Objective section in template"
assert_contains "$F" "## Context" "Context section in template"
assert_contains "$F" "## Scope" "Scope section in template"
assert_contains "$F" "## Acceptance Criteria" "Acceptance Criteria section in template"
assert_contains "$F" "## Success Criteria" "Success Criteria section in template"
assert_contains "$F" "## Constraints" "Constraints section in template"
assert_contains "$F" "## References" "References section in template"
assert_contains "$F" "GIVEN .* WHEN .* THEN|GIVEN.*\\n.*WHEN.*\\n.*THEN|GIVEN \\[" "GIVEN/WHEN/THEN preserved"
assert_contains "$F" "scope_mode" "frontmatter retains scope_mode"

# New section unique to friendly variant
assert_contains "$F" "## Technical Assumptions" "Technical Assumptions section added"
assert_contains "$F" "Decision:" "Technical Assumptions uses decisions-log shape — Decision field"
assert_contains "$F" "Why:" "Technical Assumptions uses decisions-log shape — Why field"
assert_contains "$F" "Reversibility:" "Technical Assumptions uses decisions-log shape — Reversibility field"

# Friendly variant should NOT include the UNKNOWN_TERM mechanic for user terms (research §Drop)
assert_not_contains "$F" "UNKNOWN_TERM:" "UNKNOWN_TERM mechanic dropped in friendly variant"
