#!/usr/bin/env bash
# Asserts content properties of references/escalation-and-authority.md.

F="$SKILL_DIR/references/escalation-and-authority.md"

assert_contains "$F" "^# .*Escalation" "title heading present"
assert_contains "$F" "[Aa]uthority" "Authority Rules section present"
assert_contains "$F" "ask when.*UX|user.s mental model" "decide-vs-ask heuristic from research Q2.6"
assert_contains "$F" "Technical Assumptions" "references the doc's Technical Assumptions section"
assert_contains "$F" "Escalation Triggers|Vague Answer" "escalation section present"
assert_contains "$F" "two|2|second" "escalation triggers after N (2) vague answers"
assert_contains "$F" "let.s back up|back up and talk" "pivot phrasing from research Q1.6 Bolt pattern"
assert_contains "$F" "Reversibility" "decisions-log shape includes Reversibility field"
assert_contains "$F" "Why" "decisions-log shape includes Why field"
