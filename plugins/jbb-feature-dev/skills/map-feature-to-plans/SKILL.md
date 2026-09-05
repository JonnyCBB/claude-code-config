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

**Single plan is the default outcome.** Every additional plan costs a full planning pass,
a strictly-sequential implementation pass, and per-plan research overhead downstream. When
the evidence is ambiguous, do not split.

Apply these automated heuristics in order:

1. **Size check** (soft flag): estimated changes >2000 LOC or >25 files -> flag. A size
   flag alone never forces a split — it needs a corroborating signal: a domain crossing
   (check 2), a risk trigger (check 5), or a verifiability failure (a slice that cannot be
   independently tested/built — see `references/splitting-criteria.md` section 4).
2. **Domain check**: changes cross >2 domain boundaries -> flag for splitting
3. **Dependency check**: build a dependency graph of the changes
4. **Context budget** (hard trigger): plan material would exceed ~75% of the planning
   model's context window -> must split. Count tokens with the current model's tokenizer
   (Sonnet 5's tokenizer yields ~30% more tokens than Sonnet 4.x estimates for the same text).
5. **Risk check** (hard trigger): high-risk components present -> isolate into separate plan

**If no hard trigger fires and no soft flag is corroborated**: output is "single plan" -- the
map-feature-to-plans step is a no-op pass-through. Write a minimal scoping document noting
the decision and proceed.

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

## Step 4: DAG Review Loop

After producing the candidate scoping doc in Step 3, run a multi-persona review pass to validate the DAG before the user-facing Step 5 review.

See `references/review-personas.md` for persona definitions, selection criteria, prompt template, synthesis format, iteration rules, and auto-approve threshold.

1. **Classify the candidate scoping doc**: count plans (1 / 2-3 / 4+) and assess risk (low / medium / high based on whether risk-class artifacts appear in any plan).

2. **Select reviewers** per the selection grid in `references/review-personas.md`. For any multi-plan case, all 4 reviewers (Over-Splitting Skeptic, Dependency Auditor, Risk Isolator, Requirements Tracer) fire in parallel. For the single-plan no-op case, fire 2 (Over-Splitting Skeptic + Requirements Tracer) to verify the no-op decision is correct.

3. **Spawn the selected reviewer agents in parallel** (4 for multi-plan, 2 for the single-plan no-op per the selection grid in step 2) using the prompt template from `references/review-personas.md`. Pass each the requirements doc, research doc, and candidate scoping doc.

   **Agent delivery resilience**: Subagents may go idle without delivering results (known Claude Code issue). If an agent sends an `idle_notification` without content: (1) prompt it via SendMessage using its agent ID (not name), (2) if still no delivery, respawn once, (3) if respawn fails, gather data directly or document the gap.

4. **Synthesize feedback** across all reviewers using the format in `references/review-personas.md`. Categorize each item as Must Address, Should Consider, Minor, or Points of Disagreement.

5. **Iterate**:
   - Revise the candidate scoping doc to resolve all Must Address items.
   - Re-run the review on the revised doc.
   - Maximum 3 iterations. Auto-approve when zero Must Address + zero Disagreement + ≤2 Should Consider.
   - If Must Address items persist after 3 iterations, surface them in Step 5 (Interactive Review) for user decision.

**Non-interactive mode**: spawn the selected reviewer sub-agents (mandatory — self-review is NEVER a substitute for sub-agent spawning, even in `--non-interactive` mode). Run a single iteration only. Auto-resolve all Must Address items via `decision-principles`; document each resolution in the produced scoping doc's `## Autonomous Decisions § Review Synthesis` section. Note Should Consider items as advisory comments. Token cost is NOT a valid skip justification.

## Step 5: Interactive Review

Present the scoping document to the user. Ask about:

- Are the plan boundaries correct?
- Are the dependencies between plans accurate?
- Do the wave assignments make sense?
- Is the PR strategy appropriate?

Iterate until user approves.

_Non-interactive: auto-approve using decision-principles, log decisions._

## Step 6: Write Scoping Document

Read `references/output-template.md` for the document structure.

1. Create `~/.claude/thoughts/shared/scoping/` directory if it does not exist.
2. Generate filename: `YYYY-MM-DD-<kebab-case-description>.md`
3. Write the scoping document with YAML frontmatter and all sections.

## Step 7: Suggest Next Steps

For each plan outline, suggest the next command:

```
Plan 0 (test infrastructure): /create-plan-tdd "Plan 0 outline"
Plan 1 (feature slice A): /create-plan-tdd "Plan 1 outline" (after Plan 0)
Plan 2 (feature slice B): /create-plan-tdd "Plan 2 outline" (parallel with Plan 1)
```

## Guidelines

- **Model**: the analysis runs on the invoking context's model — the `sonnet` stage wrapper in the orchestrator pipeline (see the orchestrator's stage table); the dependency-DAG output is backstopped by the Step 4 reviewers
- **Implementation failures trigger re-scoping** -- if a plan fails during implementation,
  re-run map-feature-to-plans with the failure context to produce revised plan outlines
- **Single plan is the common case** -- most features fit in one plan. The map-feature-to-plans
  step should be a fast no-op for simple features.
- **Each plan must be independently verifiable** -- tests, lint, build must pass after
  each plan is implemented

## Reference Files

- **`references/splitting-criteria.md`** -- Read in Step 2. Contains quantitative
  splitting thresholds (LOC, file count, context budget) with source citations.
- **`references/review-personas.md`** -- Read in Step 4. Defines the 4 reviewer personas
  (Over-Splitting Skeptic, Dependency Auditor, Risk Isolator, Requirements Tracer),
  selection grid, prompt template, synthesis format, max-iteration cap, and auto-approve threshold.
- **`references/output-template.md`** -- Read in Step 6. Contains the scoping document
  template with plan outlines, dependency graph, and PR strategy sections.
- **`references/pr-strategy.md`** -- Read in Step 3. Contains the adaptive PR strategy
  decision table (<500 single, 500-1500 stacked, >1500 re-scope) with defect detection data.
