#!/usr/bin/env bash
# Wave 0 harness sanity check.
# Asserts the skill's anchor files exist. Coupled to skill structure, not template content,
# so it remains stable across Wave 1 / Wave 2 changes.

assert_file_exists "$SKILL_DIR/SKILL.md" "submit-pr SKILL.md exists"
assert_file_exists "$SKILL_DIR/references/pr-description-template.md" "pr-description-template.md exists"
