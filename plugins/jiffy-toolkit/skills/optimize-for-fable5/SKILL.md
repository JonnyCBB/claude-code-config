---
name: optimize-for-fable5
description: >
  Analyzes a prompt, skill directory, or CLAUDE.md file and proposes specific
  changes to optimize it for Claude Fable 5. Scans for 14 documented behavioral
  deltas: overly prescriptive instructions, reasoning extraction refusal risks,
  gold-plating triggers, missing action boundaries, turn-ending issues, effort
  level defaults, and more. Each suggestion cites official Anthropic guidance.
  Includes a Fable 5 Migration Risks section assessing reasoning_extraction
  refusal, turn-ending, and unrequested action risks. Use when adapting prompts
  or skills for Claude Fable 5, migrating from Claude 4 to Fable 5, reviewing
  whether existing instructions are Fable 5-compatible, or when the user says
  "optimize for fable", "adapt this for fable 5", "fable 5 migration", or
  "make this work better on fable". Do not use for general prompt review,
  Opus 5 optimization (use optimize-for-opus5), or skill triggering
  optimization (use skill-creator).
when_to_use: >
  Use when the user wants to adapt a prompt, skill, or context file specifically
  for Claude Fable 5. Also trigger on "optimize for fable", "migrate to fable 5",
  "fable 5 compatible", "rewrite for fable", or any request to make instructions
  work better on Fable 5 specifically.
---

# Optimize for Fable 5

Analyze a prompt, skill, or context file and propose changes that align with
Claude Fable 5's documented behavioral profile. Every suggestion traces to
Anthropic's official guidance.

## Core Principle: Simplify, Don't Prescribe

Fable 5 follows instructions with strong fidelity — so strong that overly
prescriptive multi-step procedures actually degrade output quality. A brief
goal statement is as effective as a detailed procedure. The skill's job is to
simplify where safe, add safety rails where Fable 5 has known failure modes,
and preserve hard constraints that must stay literal.

Anthropic's own finding: "Skills developed for prior models are often too
prescriptive for Claude Fable 5 and can degrade output quality."

Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

## Input

Accept one of:

- A **prompt string** (inline text or a file path to read)
- A **skill directory path** (reads SKILL.md + all references/)
- A **CLAUDE.md file path**

If the user provides a path, read the file(s) fully before analysis. For skill
directories, read SKILL.md first, then every file under references/.

## Workflow

1. **Read the input** fully into context.

2. **Read the behavioral delta checklist** at `references/fable5-deltas.md`.
   This is your analysis framework — every finding must trace to a checklist
   item.

3. **Scan the input** section by section against the checklist. For each match:

   a. **Report each instance separately** — if the same checklist pattern
   (e.g., "verbose instructions") appears in 3 different places, that's 3
   findings, not 1. Each instance may need a different rewrite and the user
   needs to see each location.

   b. **Classify the rule** as one of:
   - **Stylistic** — a convention, preference, or prescriptive procedure
     that Fable 5 handles better with brief, goal-oriented framing. Safe
     to simplify.
   - **Compliance-enforced** — a hard constraint tied to CI validators,
     API contracts, security policies, legal requirements, or safety rules.
     Must stay literal regardless of target model.

   c. **Check for self-contradictions** — does the input's own text violate
   the rule it states? Flag these — they make the rule impossible to follow.

   d. **Propose a change** (for stylistic) or **flag for preservation** (for
   compliance-enforced). Every proposal includes the exact text to change,
   a specific rewrite, and the official Anthropic source URL.

   e. **Add a "verify before applying" note** when classification is
   uncertain — e.g., a rule that could be either stylistic or
   compliance-enforced depending on whether a linter actually enforces it.

4. **Check for missing patterns** — some checklist items are about what the
   input _should have but doesn't_ (action boundaries, turn-ending checks,
   grounded progress claims). Flag these as additions.

5. **Assess Fable 5 migration risks** — three specific failure modes that
   need explicit evaluation regardless of checklist matches.

6. **Generate the report** using the output format below.

## Output Format

Use this exact structure:

```
## Fable 5 Optimization Report

### Summary

[N] patterns found across [M] sections.
- [X] prescriptive patterns recommended for simplification
- [Y] compliance-enforced rules flagged for preservation
- [Z] missing safety rails recommended for addition

### Fable 5 Migration Risks

These three risks are assessed for every input, regardless of other findings:

#### reasoning_extraction refusal risk
- **Status**: [HIGH / LOW / NONE]
- **Found**: [exact quotes of any "show reasoning", "explain your thinking",
  "think step by step in your response", reflection, or introspection
  instructions — or "No matching instructions found"]
- **Impact**: Triggers the reasoning_extraction refusal category on Fable 5,
  causing elevated fallbacks to Claude Opus 4.8
- **Fix**: [specific removal or rewrite]

#### Turn-ending risk
- **Status**: [HIGH / MEDIUM / LOW]
- **Assessment**: [based on how tool-heavy the input's workflow is — more
  tool calls = higher risk of Fable 5 ending a turn with a statement of
  intent instead of issuing the tool call]
- **Fix**: Add "Before ending your turn, check your last paragraph. If it
  is a plan or a promise about work you have not done, do that work now
  with tool calls." (if not already present)

#### Unrequested action risk
- **Status**: [HIGH / MEDIUM / LOW]
- **Assessment**: [based on how clearly the input defines action boundaries —
  vague scope = higher risk of Fable 5 taking unrequested actions]
- **Fix**: Add explicit "do X, do not do Y" boundaries (if not already present)

### Findings

#### 1. [Pattern name from checklist] (Priority: High/Medium/Low)

- **Found in**: [section name or line reference]
- **Original text**: "[exact quote]"
- **Classification**: Stylistic / Compliance-enforced
- **Issue**: [one sentence — why this is suboptimal for Fable 5]
- **Suggested change**: [specific rewrite with context]
  OR **Preserve**: [rationale for keeping as-is]
- **Source**: [URL to official Anthropic guidance]

[...repeat for each finding...]

### Patterns Not Found

The following checklist items were checked but no matching patterns were found
in the input:

- [Checklist item]: Not present in input
[...for each non-matching item...]

### Effort Level Recommendation

[Based on the input's use case, recommend a specific effort level (not just
"use high") with reasoning tied to the task shape. Note that lower effort on
Fable 5 often exceeds xhigh on prior models. If the input specifies xhigh,
recommend a sweep procedure.]

### Applying These Findings

[Order findings by highest leverage first. When one fix resolves multiple
findings (e.g., simplifying a prescriptive procedure also removes the
verbose instructions and anti-laziness it contained), state those
dependencies so the user doesn't apply redundant fixes.]

1. [Fix X] (resolves findings N, M, and part of K)
2. [Fix Y]
...
```

## Priority Assignment

- **High**: Patterns that cause measurable quality degradation or migration
  failure (reasoning_extraction triggers, overly prescriptive procedures,
  anti-laziness instructions)
- **Medium**: Patterns that waste tokens or reduce effectiveness
  (verbose instructions, worked examples, missing boundaries)
- **Low**: Patterns worth updating but not urgently
  (effort defaults, token thresholds, send_to_user guidance)

## What This Skill Does NOT Do

- Rewrite the entire input — it produces a report with targeted suggestions
- Evaluate whether the input _should exist_ (use context-and-skills-standards)
- Optimize skill triggering descriptions (use skill-creator)
- Adapt for Opus 5 (use optimize-for-opus5 — different checklist, opposite
  directionality on several items)
- Run the rewritten prompt to verify behavioral improvement (that's a separate
  step the user performs after applying changes)

## Reference

Read `references/fable5-deltas.md` for the full behavioral delta checklist
with official source URLs and rationale for each item.
