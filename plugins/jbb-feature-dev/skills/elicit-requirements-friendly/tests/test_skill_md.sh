#!/usr/bin/env bash
# Asserts content properties of SKILL.md.

F="$SKILL_DIR/SKILL.md"

# Frontmatter — required for skill discovery
assert_contains "$F" "^---$" "YAML frontmatter delimiters"
assert_contains "$F" "^name: elicit-requirements-friendly$" "skill name correct"
assert_contains "$F" "^description:" "description field present"
# Trigger phrases (research §Synthesis — must be discoverable)
assert_contains "$F" "elicit requirements" "trigger phrase 1"
assert_contains "$F" "interview me" "trigger phrase 2"
assert_contains "$F" "non-technical" "trigger phrase 3"
assert_contains "$F" "intake" "trigger phrase 4"
assert_contains "$F" "PRD" "trigger phrase 5"
assert_contains "$F" "friendly" "trigger phrase 6"

# Step structure — 7 steps
assert_contains "$F" "## Step 1" "Step 1 present"
assert_contains "$F" "## Step 2" "Step 2 present"
assert_contains "$F" "## Step 3" "Step 3 present"
assert_contains "$F" "## Step 4" "Step 4 present"
assert_contains "$F" "## Step 5" "Step 5 present"
assert_contains "$F" "## Step 6" "Step 6 present"
assert_contains "$F" "## Step 7" "Step 7 present"

# Step 1 — frontload references
assert_contains "$F" "[Ff]rontload|screenshots, links" "Step 1 frontloads references"
assert_contains "$F" "Slack|Jira|Google Docs" "Step 1 fetches links via MCP"

# Step 2 — autonomous Context Sprint (agents are dispatched via the shared table, not named inline)
assert_contains "$F" "elicit-shared-patterns.md" "Step 2 spawns context agents via shared dispatch table"

# Step 3 — soft premise
assert_contains "$F" "recurring annoyance|one-off|one-time wish" "Step 3 uses soft premise phrasing"
assert_not_contains "$F" "what happens if we do nothing" "confrontational phrasing dropped"

# Step 4 — friendly interview mechanics
assert_contains "$F" "[Oo]ne question" "one-question-at-a-time pacing"
assert_contains "$F" "AskUserQuestion" "uses AskUserQuestion for structured options"
assert_contains "$F" "Recommended" "labels recommended option"
assert_contains "$F" "running.*spec|spec recap|recap every" "shows running recap"
assert_contains "$F" "translate.*term|jargon" "translates technical terms inline"
assert_contains "$F" "let.s back up|two vague answers" "escalation pivot referenced"
assert_contains "$F" "Authority|decide silently|user.s mental model" "decision-authority rule referenced"
assert_contains "$F" "thorough|every.*branch|always thorough" "always thorough — no early exit"

# Step 5 — Mutual confirmation as ONLY stopping criterion
assert_contains "$F" "Mutual.*Confirmation|explicit.*confirmation" "Step 5 mutual confirmation"
assert_not_contains "$F" "scorecard|/60" "no quality scorecard"

# Step 6 — write doc using output-template
assert_contains "$F" "references/output-template" "Step 6 references output-template.md"
assert_contains "$F" "Technical Assumptions" "Step 6 mentions Technical Assumptions section"
assert_contains "$F" "thoughts/shared/requirements" "Step 6 writes to requirements directory"

# Step 7 — suggest next step
assert_contains "$F" "/research-problem" "Step 7 suggests /research-problem"
assert_contains "$F" "/create-plan-tdd" "Step 7 suggests /create-plan-tdd"

# Reference Files section links each Wave 1 reference
assert_contains "$F" "references/question-bank.md" "links question-bank.md"
assert_contains "$F" "references/exemplars.md" "links exemplars.md"
assert_contains "$F" "references/escalation-and-authority.md" "links escalation-and-authority.md"
assert_contains "$F" "references/output-template.md" "links output-template.md"

# Mode flags — inherited from existing skill
assert_contains "$F" "Non-interactive|--non-interactive" "non-interactive mode supported"

# Confrontational mechanics dropped (research §Drop)
assert_not_contains "$F" "Premise Challenge" "Premise Challenge phrasing dropped (replaced with soft variant)"
assert_not_contains "$F" "UNKNOWN_TERM" "UNKNOWN_TERM mechanic dropped"
