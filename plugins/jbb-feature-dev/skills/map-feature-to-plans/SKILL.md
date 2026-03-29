---
name: map-feature-to-plans
description: >
  Analyze a research document for a single feature and determine whether it should be
  split into multiple implementation plans. Produces plan outlines with file lists,
  dependency graph, execution waves, and adaptive PR strategy. Use after research
  completes and before create-plan-tdd. Outputs "single plan" (no-op) when splitting
  is unnecessary. Trigger phrases (1) "feature to plans" (2) "split into plans"
  (3) "split feature for implementation" (4) "how many plans" (5) "plan from feature".
  Outputs to ~/.claude/thoughts/shared/scoping/.
---

# Map Feature to Plans

Analyze a research document for a single feature and determine whether it needs to be
split into multiple implementation plans. Each output plan outline feeds directly into
`create-plan-tdd` -- no further research needed.

## Step 0: Validate Input Level

Before proceeding, check whether this document is at the right abstraction level for
tactical scoping.

**This skill is appropriate when** the document describes a single feature with enough
technical detail to estimate files, LOC, and dependencies.

**This skill may not be appropriate when** the document:

- Describes multiple independent subsystems or features
- Contains user stories spanning different user journeys
- Has no file-level detail or implementation analysis
- Reads like a PRD, RFC, or epic rather than a research output

If the input looks like a multi-feature initiative, inform the user:
"This document appears to describe multiple independent features or subsystems rather
than a single researched feature. You may want to use the `break-down-initiative` skill
first, which breaks high-level initiatives into separate features — each with its own
research step — before tactical plan splitting."

_Non-interactive: log the observation and proceed if only 1 feature/subsystem is present.
Otherwise, raise an escalation._

## Mode Detection

Parse `$ARGUMENTS` for flags and input:

- `--non-interactive`: Auto-approve all decisions using `~/.claude/skills/decision-principles/SKILL.md`. Log each decision. File path (research doc) is REQUIRED.
- File path argument: read the research document immediately and begin Step 1.
- No arguments: ask user for the research document path.

## Step 1: Load Research Document

Read the research document FULLY (no limit/offset). Extract:

- Components and files that will be changed
- Independent subsystems identified in the research
- Complexity signals (file count, estimated LOC, domain crossings)
- Risk factors (auth, payments, data migrations, public API changes)

## Step 2: Apply Splitting Criteria

Read `references/splitting-criteria.md` for the tactical splitting criteria with
quantitative thresholds.

Apply these automated heuristics in order:

1. **Size check**: estimated changes >600 LOC or >10 files -> flag for splitting
2. **Domain check**: changes cross >2 domain boundaries -> flag for splitting
3. **Dependency check**: build a dependency graph of the changes
4. **Context budget**: plan would exceed ~50% context window (~100K tokens) -> flag
5. **Risk check**: high-risk components present -> isolate into separate plan

**If no criteria trigger**: output is "single plan" -- the map-feature-to-plans step is a no-op
pass-through. Write a minimal scoping document noting the decision and proceed.

## Step 3: Produce Plan Outlines

For each plan, produce:

- **Plan name** and scope description
- **Files list**: which files will be touched
- **Estimated LOC**
- **Dependencies** on other plans

Then determine:

- **Wave 0 need**: shared test infrastructure gets its own plan ONLY when multiple
  plans depend on it. If only one plan needs test setup, keep it internal to that plan.
- **Execution waves**: group independent plans for parallel execution, sequence
  dependent plans
- **PR strategy**: read `references/pr-strategy.md` for adaptive thresholds

## Step 4: Interactive Review

Present the scoping document to the user. Ask about:

- Are the plan boundaries correct?
- Are the dependencies between plans accurate?
- Do the wave assignments make sense?
- Is the PR strategy appropriate?

Iterate until user approves.

_Non-interactive: auto-approve using decision-principles, log decisions._

## Step 5: Write Scoping Document

Read `references/output-template.md` for the document structure.

1. Create `~/.claude/thoughts/shared/scoping/` directory if it does not exist.
2. Generate filename: `YYYY-MM-DD-<kebab-case-description>.md`
3. Write the scoping document with YAML frontmatter and all sections.

## Step 6: Suggest Next Steps

For each plan outline, suggest the next command:

```
Plan 0 (test infrastructure): /create-plan-tdd "Plan 0 outline"
Plan 1 (feature slice A): /create-plan-tdd "Plan 1 outline" (after Plan 0)
Plan 2 (feature slice B): /create-plan-tdd "Plan 2 outline" (parallel with Plan 1)
```

## Guidelines

- **Uses opus model** for the map-feature-to-plans analysis (complex reasoning about dependencies)
- **Implementation failures trigger re-scoping** -- if a plan fails during implementation,
  re-run map-feature-to-plans with the failure context to produce revised plan outlines
- **Single plan is the common case** -- most features fit in one plan. The map-feature-to-plans
  step should be a fast no-op for simple features.
- **Each plan must be independently verifiable** -- tests, lint, build must pass after
  each plan is implemented

## Reference Files

- **`references/splitting-criteria.md`** -- Read in Step 2. Contains quantitative
  splitting thresholds (LOC, file count, context budget) with source citations.
- **`references/output-template.md`** -- Read in Step 5. Contains the scoping document
  template with plan outlines, dependency graph, and PR strategy sections.
- **`references/pr-strategy.md`** -- Read in Step 3. Contains the adaptive PR strategy
  decision table (<500 single, 500-1500 stacked, >1500 re-scope) with defect detection data.
