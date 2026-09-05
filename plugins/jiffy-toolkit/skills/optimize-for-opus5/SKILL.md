---
name: optimize-for-opus5
description: >
  Analyzes a prompt, skill directory, or CLAUDE.md file and proposes specific
  changes to optimize it for Claude Opus 5. Scans for 12 documented behavioral
  deltas: over-verification triggers, scope expansion risks, delegation patterns,
  emphasis vs hard-constraint classification, effort level defaults, reasoning
  instructions, and more. Each suggestion cites official Anthropic guidance.
  Distinguishes stylistic rules (safe to convert to judgment) from
  compliance-enforced constraints (must stay literal). Use when adapting prompts
  or skills for Claude Opus 5, migrating from Claude 4 to Opus 5, reviewing
  whether existing instructions are Opus 5-compatible, or when the user says
  "optimize for opus", "adapt this for opus 5", "opus 5 migration", or
  "make this work better on opus". Do not use for general prompt review,
  Fable 5 optimization (use optimize-for-fable5), or skill triggering
  optimization (use skill-creator).
when_to_use: >
  Use when the user wants to adapt a prompt, skill, or context file specifically
  for Claude Opus 5. Also trigger on "optimize for opus", "migrate to opus 5",
  "opus 5 compatible", "rewrite for opus", or any request to make instructions
  work better on Opus 5 specifically.
---

# Optimize for Opus 5

Analyze a prompt, skill, or context file and propose changes that align with
Claude Opus 5's documented behavioral profile. Every suggestion traces to
Anthropic's official guidance.

## Core Principle: Reallocate Emphasis

The Claude 5 shift is **rules to judgment** — not "remove all emphasis."
Anthropic's own Opus 5 system prompt retains NEVER, MUST NOT, and
`<critical_*>` tags for genuine hard constraints. The skill's job is to
distinguish stylistic rules (convert to judgment) from compliance-enforced
constraints (preserve as-is), not to strip emphasis indiscriminately.

Source: https://platform.claude.com/docs/en/release-notes/system-prompts

## Input

Accept one of:

- A **prompt string** (inline text or a file path to read)
- A **skill directory path** (reads SKILL.md + all references/)
- A **CLAUDE.md file path**

If the user provides a path, read the file(s) fully before analysis. For skill
directories, read SKILL.md first, then every file under references/.

## Workflow

1. **Read the input** fully into context.

2. **Read the behavioral delta checklist** at `references/opus5-deltas.md`.
   This is your analysis framework — every finding must trace to a checklist
   item.

3. **Scan the input** section by section against the checklist. For each match:

   a. **Report each instance separately** — if the same checklist pattern
   (e.g., "rigid rules without rationale") appears in 3 different places,
   that's 3 findings, not 1. Each instance may need a different rewrite and
   the user needs to see each location.

   b. **Classify the rule** as one of:
   - **Stylistic** — a convention, preference, or emphasis pattern that
     Opus 5 handles better with judgment-based framing. Safe to convert.
   - **Compliance-enforced** — a hard constraint tied to CI validators,
     API contracts, security policies, legal requirements, or safety rules.
     Must stay literal regardless of target model.

   c. **Check for self-contradictions** — does the input's own text violate
   the rule it states? (e.g., "NEVER use abbreviations" while using "p99"
   elsewhere). Flag these — they make the rule impossible to follow literally.

   d. **Propose a change** (for stylistic) or **flag for preservation** (for
   compliance-enforced). Every proposal includes the exact text to change,
   a specific rewrite, and the official Anthropic source URL.

   e. **Add a "verify before applying" note** when classification is
   uncertain — e.g., a rule that could be either stylistic or
   compliance-enforced depending on whether a linter actually enforces it.

4. **Check for missing patterns** — some checklist items are about what the
   input _should have but doesn't_ (scope constraints, delegation caps). Flag
   these as additions.

5. **Generate the report** using the output format below.

## Output Format

Use this exact structure:

```
## Opus 5 Optimization Report

### Summary

[N] patterns found across [M] sections.
- [X] stylistic rules recommended for conversion to judgment
- [Y] compliance-enforced rules flagged for preservation
- [Z] missing patterns recommended for addition

### Findings

#### 1. [Pattern name from checklist] (Priority: High/Medium/Low)

- **Found in**: [section name or line reference]
- **Original text**: "[exact quote]"
- **Classification**: Stylistic / Compliance-enforced
- **Issue**: [one sentence — why this is suboptimal for Opus 5]
- **Suggested change**: [specific rewrite with context]
  OR **Preserve**: [rationale for keeping as-is]
- **Source**: [URL to official Anthropic guidance]

[...repeat for each finding...]

### Patterns Not Found

The following checklist items were checked but no matching patterns were found
in the input (this confirms analysis coverage, not that the input is perfect):

- [Checklist item]: Not present in input
[...for each non-matching item...]

### Effort Level Recommendation

[Based on the input's use case, recommend a specific effort level (not just
"use high") with reasoning tied to the task shape. If the input specifies
xhigh from the 4.7/4.8 era, recommend a sweep procedure.]

### Applying These Findings

[Order findings by highest leverage first. When one fix resolves multiple
findings (e.g., deleting a verification step also removes the delegation
and duplication it contained), state those dependencies so the user
doesn't apply redundant fixes.]

1. [Fix X] (resolves findings N, M, and part of K)
2. [Fix Y]
...
```

## Priority Assignment

- **High**: Patterns that cause measurable quality degradation on Opus 5
  (over-verification, anti-laziness, reasoning tag leakage)
- **Medium**: Patterns that waste tokens or reduce effectiveness
  (duplicated instructions, upfront context dumps, worked examples)
- **Low**: Patterns worth updating but not urgently
  (effort defaults, token threshold recounting)

## What This Skill Does NOT Do

- Rewrite the entire input — it produces a report with targeted suggestions
- Evaluate whether the input _should exist_ (use context-and-skills-standards)
- Optimize skill triggering descriptions (use skill-creator)
- Adapt for Fable 5 (use optimize-for-fable5 — different checklist, opposite
  directionality on several items)
- Run the rewritten prompt to verify behavioral improvement (that's a separate
  step the user performs after applying changes)

## Reference

Read `references/opus5-deltas.md` for the full behavioral delta checklist with
official source URLs and rationale for each item.
