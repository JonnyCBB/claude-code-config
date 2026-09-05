#!/usr/bin/env bash
# Asserts content properties of references/exemplars.md.

F="$SKILL_DIR/references/exemplars.md"

assert_contains "$F" "^# .*Exemplar" "title heading present"
assert_contains "$F" "Good answer|Good:" "good-answer marker present"
assert_contains "$F" "Vague answer|Vague:" "vague-answer marker present"
assert_contains "$F" "[Mm]otivation|[Pp]roblem" "exemplar covers motivation/problem dimension"
assert_contains "$F" "[Aa]cceptance" "exemplar covers acceptance criteria dimension"
assert_contains "$F" "[Ee]dge [Cc]ase|[Ff]ailure" "exemplar covers edge cases/failure dimension"
assert_contains "$F" "[Ss]uccess|[Mm]etric" "exemplar covers success/metric dimension"
assert_contains "$F" "[Ss]cope" "exemplar covers scope dimension"
# Exemplars MUST contrast quality, not just length — assert at least one pair where the
# vague answer is long but shallow.
assert_contains "$F" "long but shallow|verbose but vague|fluffy" "exemplars distinguish length from depth"
