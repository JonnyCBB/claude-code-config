---
name: break-down-initiative
description: >
  Decompose a PRD, RFC, epic, or high-level initiative into independently-executable
  feature outlines using vertical slices. Each feature gets its own research pipeline run.
  Use when the input is too large or too high-level for a single research/plan cycle.
  Trigger phrases (1) "break down initiative" (2) "break down epic" (3) "split into features"
  (4) "break down PRD" (5) "PRD to features" (6) "break this down".
  Outputs to ~/.claude/thoughts/shared/decomposition/.
---

# Break Down Initiative

Break a high-level document (PRD, RFC, epic, initiative) into independently-executable
feature outlines using vertical slices. Each output feature feeds into its own full
pipeline run (research -> map-feature-to-plans -> plan -> implement).

## Step 0: Validate Input Level

Before proceeding, check whether this document is at the right abstraction level for
strategic decomposition.

**This skill is appropriate when** the document describes WHAT to build — user stories,
requirements, business goals, multiple subsystems or features.

**This skill may not be appropriate when** the document:

- Contains file paths, code references, or implementation details
- Describes a single well-understood feature with technical analysis
- Is the output of a research step (has frontmatter with `type: research`)
- Focuses on HOW to build rather than WHAT to build

If the input looks like a single-feature research document, inform the user:
"This document appears to describe a single well-understood feature with implementation
details rather than a high-level initiative with multiple features. You may want to use
the `map-feature-to-plans` skill instead, which splits a single researched feature into
implementation plans."

_Non-interactive: log the observation and proceed if the document has >=2 distinct
subsystems/features. Otherwise, output a single-feature pass-through._

## Mode Detection

Parse `$ARGUMENTS` for flags and input:

- `--non-interactive`: Auto-approve all decisions using `~/.claude/skills/decision-principles/SKILL.md`. Log each decision. File path argument is REQUIRED.
- File path argument: read the document immediately and begin Step 1.
- No arguments: ask user for the document path or paste content.

## Step 1: Load Input

Read the PRD/RFC/epic document FULLY (no limit/offset). If the user provides URLs
(Google Docs, Jira, Slack), use ToolSearch to discover relevant MCP tools and fetch
the content.

Identify from the document:

- User stories or requirements listed
- Stated goals and non-goals
- Any existing decomposition hints (sections, phases, milestones)

## Step 2: Explore Codebase

Spawn a **codebase-explorer** agent to understand the current architecture, components,
and domain boundaries in the target repository.

The codebase knowledge helps identify which integration layers each vertical slice must
cross. **Slice by user value, NOT by code module.** The architecture informs the slicing
but does not drive it -- a feature should never be "refactor the database layer" (horizontal).

_Non-interactive: proceed automatically after agent completes._

## Step 3: Draft Vertical Slices

Read `references/splitting-criteria.md` for the strategic splitting criteria.

For each identified feature, produce an outline:

- **Title**: short descriptive name
- **Description**: 2-3 sentences describing end-to-end behavior (not layer-by-layer)
- **Type**: HITL (needs human decision before implementation) or AFK (fully automatable)
- **Blocked by**: which other features must complete first
- **User stories covered**: which requirements from the source document this addresses
- **Estimated complexity**: trivial / small / standard (informs pipeline path)

Prefer many thin slices over few thick ones. Prefer AFK over HITL where possible.

_Non-interactive: draft slices and proceed to Step 5._

## Step 4: Interactive Quiz

Present the proposed breakdown as a numbered list showing title, type, blocked-by,
and user stories for each feature.

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the dependency relationships correct?
- Should any features be merged or split further?
- Are the correct features marked as HITL vs AFK?

Iterate until the user approves the breakdown.

_Non-interactive: skip this step. Auto-approve using decision-principles, log decisions._

## Step 5: Write Decomposition Document

Read `references/output-template.md` for the document structure.

1. Create `~/.claude/thoughts/shared/decomposition/` directory if it does not exist.
2. Generate filename: `YYYY-MM-DD-<kebab-case-description>.md`
3. Write the decomposition document with YAML frontmatter and all sections.

## Step 6: Suggest Next Steps

For each feature outline, suggest the next pipeline command:

```
Feature 1 [AFK]: /research-problem "Feature 1 description"
Feature 2 [HITL]: Needs human decision on [X] before research
Feature 3 [AFK]: /research-problem "Feature 3 description" (blocked by Feature 1)
```

## Guidelines

- **Vertical slices, not horizontal layers** -- each feature cuts through all integration
  layers end-to-end (schema, API, UI, tests). Never "all database work" as one feature.
- **Prefer many thin features** over few thick ones
- **Prefer AFK over HITL** -- only mark HITL when a genuine human decision is needed
  (architectural choice, vendor selection, design review)
- **Each feature must be independently demoable or verifiable**
- **Map dependencies explicitly** -- if Feature B needs Feature A's API, say so

## Reference Files

- **`references/splitting-criteria.md`** -- Read in Step 3. Contains 4-5 strategic
  splitting criteria with concrete examples for PRD-to-feature decomposition.
- **`references/output-template.md`** -- Read in Step 5. Contains the decomposition
  document template with YAML frontmatter and section structure.
