#!/usr/bin/env bash
# Asserts content properties of references/question-bank.md.
# Sourced by tests/verify-skill.sh — relies on $SKILL_DIR and assertion helpers.

F="$SKILL_DIR/references/question-bank.md"

assert_contains "$F" "^# .*Question" "title heading present"
assert_contains "$F" "Story Prompts|Top 10" "Top 10 / Story Prompts section heading"
assert_contains "$F" "Tell me about the last time" "Q1 verbatim from research"
assert_contains "$F" "What did you actually do next" "Q2 verbatim from research"
assert_contains "$F" "hardest or most frustrating" "Q3 verbatim"
assert_contains "$F" "What have you already tried" "Q4 verbatim"
assert_contains "$F" "Walk me through your current workaround" "Q5 verbatim"
assert_contains "$F" "I need something different" "Q6 verbatim"
assert_contains "$F" "almost stopped you from switching" "Q7 verbatim"
assert_contains "$F" "If we met again in 3 months" "Q8 verbatim"
assert_contains "$F" "weirdest or worst version" "Q9 verbatim"
assert_contains "$F" "what problem would that solve" "Q10 verbatim"
assert_contains "$F" "NFR Probes|Non-Functional" "NFR probes section"
assert_contains "$F" "How long would feel too long" "performance probe"
assert_contains "$F" "normal day vs\\. a bad day|normal day vs a bad day" "scale probe"
assert_contains "$F" "Who feels the pain" "reliability probe"
assert_contains "$F" "phone, screen reader" "accessibility probe"
assert_contains "$F" "absolutely shouldn't see" "privacy probe"
assert_contains "$F" "Jargon Translation|Translation Table" "jargon translation section"
assert_contains "$F" "acceptance criteria" "jargon table includes acceptance criteria translation"
