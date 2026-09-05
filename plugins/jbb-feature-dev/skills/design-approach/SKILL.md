---
name: design-approach
description: >
  Multi-architect design exploration before planning. Spawns competing architect agents
  with different perspectives to generate genuinely different approaches, presents them
  in a comparison document, then facilitates interactive discussion where the user explores
  tradeoffs and makes key design decisions. Output is a design decision document that
  constrains downstream planning. Trigger phrases (1) "design approach" (2) "explore design
  options" (3) "compare approaches" (4) "design-approach" (5) "architect exploration"
  (6) "design before plan". Use when research reveals multiple viable approaches and the
  user wants to evaluate options before creating an implementation plan.
argument-hint: "[research-doc-path] [--requirements=path] [--non-interactive]"
---

# Design Approach

This skill orchestrates multi-architect design exploration by spawning competing architect
agents with different perspectives, synthesizing their outputs into a comparison document,
and facilitating structured decision-making to produce a design decision document that
constrains downstream planning.

## Mode Detection

Parse `$ARGUMENTS` before doing any other work:

- Detect `--non-interactive` flag: if present, set `NON_INTERACTIVE=true`
- Detect `--requirements=<path>`: if present, capture as `REQUIREMENTS_PATH`
- Remaining positional argument (if any): treat as `RESEARCH_DOC_PATH`

In non-interactive mode, skip all AskUserQuestion prompts and use automated decision
logic throughout. Document every auto-selected decision in the output.

## Step 1: Input Reading

**If `RESEARCH_DOC_PATH` is provided:**

- Read the research document fully via Read tool (no limit or offset)
- If `REQUIREMENTS_PATH` is also provided, read the requirements document fully

**If no arguments are provided and mode is interactive:**

- Prompt the user: "Please provide the path to your research document, or describe the
  feature/task you want to explore design approaches for."
- Accept either a file path (read it) or a free-text task description

**If non-interactive and no research doc path:**

- Skip prompt
- Proceed with any provided files or an empty research context

At the end of this step you should have: research doc content (or task description),
and optionally requirements doc content.

## Step 2: Tension and Settlement Analysis

Read `references/tension-analysis-guide.md` in full before scanning — including the
Settlement Detection and Cross-Reference Rule sections.

This step produces TWO outputs: a list of **settled decisions** (constraints) and a list
of **open tensions** (design space). Both are used in later steps.

### Step 2a: Tension Scanning

Scan the research doc content for architectural tension signals using the five detection
categories defined in the guide:

- **Category A: Explicit Structural Markers** — Open Questions sections, Advisory Notes,
  ranked options tables, comparison matrices, priority matrices with "Requires Design Work"
- **Category B: Linguistic Signals** — "X vs Y", "could be done via X or Y",
  "tradeoff between A and B", "open question" inline, "Partial fix", numbered alternatives
- **Category C: Structural Ambiguity Patterns** — Competing Findings, conditional
  recommendations ("If X do A; if Y do B"), scope boundary debates, untested territory flags
- **Category D: Absent-Signal Indicators** — No decisions despite complete research,
  Open Questions without Resolved counterparts, comparison tables without recommendation row
- **Category E: Quantitative Thresholds** — >=2 approach-level open questions,
  > =1 comparison table without clear winner, >=2 "X vs Y" phrases, >=3 Advisory Notes

Count and classify each detected tension. Record the list with the signal that triggered it.

### Step 2b: Settlement Detection

Scan the research doc for decisions already made using the settlement categories:

- **Category S1: Explicit Exclusions** — "No skill action needed", "not in scope",
  "skip entirely", "delegate to X", "Automatic" in integration tables
- **Category S2: Single-Option Conclusions** — Recommendations not listed in Open Questions,
  "should use X" / "must use X" with no unresolved caveats
- **Category S3: Absent From Scope** — Features never mentioned in proposed structure
  or action list, features only appearing as something another tool handles

Record each settled decision with the section/line that establishes it.

### Step 2c: Cross-Reference

Apply the Cross-Reference Rule from the tension analysis guide:

For each detected tension from Step 2a, check if any settlement signal from Step 2b
contradicts it. If a tension signal is contradicted by a more specific settlement
elsewhere in the document, reclassify it as a settled decision.

Present both lists:

```
## Settled Decisions (constraints for all architects)
- [Decision]: [What was settled] — Source: [section/line reference]

## Open Tensions (where architects may diverge)
1. [Tension]: [What is unresolved] — Signals: [categories that triggered it]
```

### Step 2d: Tension Count Evaluation

Count only the **open tensions** (not settled decisions) for the threshold check.

**If fewer than 2 open tensions found:**

- Interactive: use `AskUserQuestion` with the following structure:
  - question: `"Only N open tension(s) found (plus M settled decisions). How should we proceed?"`
  - header: `"Low tension"` (max 12 chars)
  - options:
    - label: `"Fallback trio"`, description: `"Spawn architects with Minimal Changes / Clean Architecture / Pragmatic Balance"`
    - label: `"Skip to plan"`, description: `"Exit design-approach and go straight to /create-plan-tdd"`
- Non-interactive: write a minimal design decision doc to
  `~/.claude/thoughts/shared/feature_designs/` noting "no significant tensions identified —
  design approach not required" and exit immediately

**If 2 or more open tensions found:**

- Derive architect perspectives from the dominant open tensions only
- Each perspective should embody a coherent philosophy that resolves the tensions differently
- Perspectives must NOT propose alternatives to settled decisions
- Present both the settled decisions and the open tensions to the user (interactive mode)
- Non-interactive: auto-proceed with the derived perspectives

## Step 3: Architect Perspective Confirmation

Present the derived perspectives to the user. If no research doc was provided or tensions
are unclear, use the fallback trio:

1. **Minimal Changes** — extend existing systems with the smallest possible surface area
2. **Clean Architecture** — prioritise long-term maintainability and clear domain boundaries
3. **Pragmatic Balance** — find the fastest path to value without incurring significant debt

**Variable agent count** based on open tension count (not settled decisions):

- 2 open tensions → 2 architect agents
- 3 open tensions → 3 architect agents
- 4 or more open tensions → 4 architect agents (maximum)

Do not spawn more than 4 agents.

**Agent delivery resilience**: Subagents may go idle without delivering results (known Claude Code issue). If an agent sends an `idle_notification` without content: (1) prompt it via SendMessage using its agent ID (not name), (2) if still no delivery, respawn once, (3) if respawn fails, gather data directly or document the gap.

In interactive mode, use `AskUserQuestion` to confirm the perspectives and agent count. List
the proposed perspectives in the `question` field, then offer structured options:

- question: `"We'll explore the design with N architect agents using these perspectives: [list]. Proceed?"`
- header: `"Perspectives"` (max 12 chars)
- options:
  - label: `"Proceed"`, description: `"Spawn N agents with these perspectives as-is"`
  - label: `"Adjust"`, description: `"Revise one or more perspectives before spawning"`

If the user selects "Adjust", follow up with a free-text question about which perspective to
change. The user can also select the auto-provided "Other" option to describe a fully
different set of perspectives in their own words.

Non-interactive: auto-confirm with derived or fallback perspectives.

## Step 4: Architect Agent Spawning

Before spawning, perform pre-spawn verification per
`${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md`.

Create a verification table listing each agent, its assigned perspective, and the inputs
it will receive. Confirm the table is complete before spawning.

Use the Agent tool to spawn `general-purpose` agents. Spawn all architect agents in
**parallel** for speed — do not wait for one to finish before starting the next.

Each agent receives in its prompt:

- The full research document content (or task description)
- The requirements document content, if available
- The **settled decisions list** from Step 2 — framed as hard constraints that the agent
  must NOT re-open or propose alternatives to
- The **open tensions list** from Step 2 — framed as the design space where the agent's
  perspective applies
- Their assigned architect perspective (name and philosophy)
- The output format instructions from `references/architect-output-format.md`
  (which includes the settled decisions and open tensions sections in the prompt template)
- Instruction to stay within their assigned perspective and not hedge toward other approaches

Use the user's default model per
`${CLAUDE_PLUGIN_ROOT}/skills/shared-references/model-selection-guide.md`.

Wait for ALL architect agents to complete before proceeding.

After all agents complete, perform a pre-synthesis verification checkpoint:

- Confirm each agent produced output
- Flag any agent that returned an empty or error response
- If more than half the agents failed, abort and report the error to the user

### Step 4b: Settlement Compliance Validation

After all agents complete and before proceeding to comparison, validate each architect's
output against the settled decisions list from Step 2:

For each architect output, check:

- Does the architect propose any feature, component, or design choice that contradicts
  a settled decision?
- Does the architect include scope items that were explicitly excluded?

If violations are found:

- **Strip the violating proposals** from the architect's output before comparison
- Log each violation in a table:

```
## Settlement Violations Detected

| Architect | Violation | Settled Decision | Action |
|-----------|-----------|-----------------|--------|
| [Name] | Proposed X | Research doc settled: "No action needed for X" | Stripped from output |
```

- Present the violations table to the user (interactive mode) so they are aware
- Non-interactive: log violations and proceed with stripped outputs

This step ensures that no architect's maximalist perspective can re-introduce features
the research doc already ruled out.

## Step 5: Convergence Check

Compare all architect outputs:

- **Convergent** = same component structure AND same key design decisions across all agents
- Minor naming differences (e.g., `UserService` vs `user-service`) do NOT count as divergence
- If all agents converged: declare "strong consensus" and proceed directly to Step 8
  with a convergence shortcut (skip Steps 6 and 7)
- If any meaningful divergence exists on component structure or key decisions: proceed
  to Step 6

## Step 6: Comparison Document

Read `references/comparison-template.md` before synthesising.

Synthesise the architect outputs into a structured comparison document:

- One section per approach (1-2 pages equivalent per approach)
- Highlight where approaches agree and where they diverge
- Include a recommendation section with clear rationale
- If a requirements document was provided, include a requirements compliance summary
  showing which approaches satisfy all requirements and which deviate

Present the comparison document to the user in full (interactive mode).

Non-interactive: auto-proceed with the recommended approach and document the rationale.

## Step 7: Interactive Discussion

For each key design decision where the architect agents diverged, ask the user via
`AskUserQuestion`. Structure each call as:

- `question`: the decision, phrased as a clear question ending in `?`
- `header`: a short tag (max 12 chars, e.g. `"Consistency"`, `"Storage"`, `"Auth"`)
- `options`: 2-4 entries, each with a `label` (1-5 words) and a `description` that
  compresses the tradeoff into one tight sentence

Example `AskUserQuestion` call for a single decision:

```
question:  "How should we handle data consistency between services?"
header:    "Consistency"
options:
  - label: "Event sourcing"
    description: "Strong audit trail; higher implementation complexity"
  - label: "Saga pattern"
    description: "Eventual consistency; simpler to implement and operate"
  - label: "Sync calls"
    description: "Strong consistency; tight coupling and cascading failure risk"
```

Formatting constraints:

- Maximum 4 options per question. If a decision has more candidates, drop the weakest two
  or group variants under a single label.
- Do NOT add an "Other" option manually — the tool surfaces it automatically and it acts
  as the free-text escape hatch.
- You may batch up to 4 independent decisions in a single `AskUserQuestion` call (one entry
  per decision). Do not batch decisions that depend on each other — ask those sequentially
  so later options can reflect the earlier selection.

After each decision, narrow the solution space and continue to the next divergent decision.

**If the user selects "Other" on a decision:**

- Treat the user's free-text answer as a `user-alternative` for that decision
- Capture it along with any stated rationale
- Proceed with that as the chosen option for that decision

**If the user selects "Other" on every decision (rejects all proposed approaches):**

- Treat the combined user-alternative answers as the chosen approach
- If the free-text answers are too sparse to act on, follow up with a plain-text
  clarification prompt before writing the design decision document

**Requirements compliance check:**

- After each user selection, verify it does not violate any requirement in the
  requirements document (if provided)
- If a violation is detected, flag it immediately via `AskUserQuestion`:
  - `question`: `"Your selection may conflict with requirement X. How do you want to proceed?"`
  - `header`: `"Req conflict"`
  - options:
    - label: `"Proceed"`, description: `"Accept the deviation; document rationale and risk"`
    - label: `"Reconsider"`, description: `"Go back and pick a different option for this decision"`

**Non-interactive mode:**

- Auto-select decisions per
  `${CLAUDE_PLUGIN_ROOT}/skills/decision-principles/SKILL.md`
- Document each auto-selected decision with rationale in the output
- Apply requirements compliance check and flag any violations in the output

## Step 8: Design Decision Document

Read `references/decision-document-template.md` before writing.

Create the output directory if it does not exist:
`~/.claude/thoughts/shared/feature_designs/`

Write the design decision document to:
`~/.claude/thoughts/shared/feature_designs/YYYY-MM-DD-<short-description>.md`

The document must include:

- **Overview** — one paragraph summarising the chosen approach
- **Key Decisions** — each divergent decision, chosen option, and rationale
- **Rejected Alternatives** — brief summary of why each other approach was not chosen
- **Constraints for Downstream Planning** — explicit list of decisions that planning
  must respect (e.g., "Must use event sourcing for order state changes")
- **Requirements Deviations** — any chosen option that deviates from a stated requirement,
  with rationale and acknowledged risk
- **Architect Perspectives Explored** — list of the perspectives that were evaluated

**Non-interactive mode:** append an `## Autonomous Decisions` section listing every
decision made automatically and the decision-principles rule that guided it.

After writing, present the document location to the user and suggest the next step:
`/create-plan-tdd [design-doc-path] [research-doc-path]`

## Cross-References

- `${CLAUDE_PLUGIN_ROOT}/skills/decision-principles/SKILL.md` — used in Step 7 non-interactive auto-selection
- `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md` — agent contract and pre-spawn verification
- `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/model-selection-guide.md` — model selection for spawned agents
- `references/tension-analysis-guide.md` — tension scanning categories and scoring (Step 2)
- `references/architect-output-format.md` — output format instructions for architect agents (Step 4)
- `references/comparison-template.md` — template for synthesising architect outputs (Step 6)
- `references/decision-document-template.md` — template for the final design decision document (Step 8)

## Requirements Constraints

This skill enforces the following non-negotiable constraints:

- Naming follows jbb-feature-dev conventions: verb-noun kebab-case
- Supports `--non-interactive` mode for pipeline use (all interactive prompts have automated fallbacks)
- Uses the Agent tool for spawning architect agents — no external processes
- Architect agents run in parallel for speed (never sequentially)
- Uses shared infrastructure: agent-verification-pattern.md and decision-principles SKILL.md
- Does NOT build shared multi-architect infrastructure with /improve-codebase-architecture
- Maximum of 4 architect agents spawned per run
- Comparison document is limited to 1-2 pages per approach
- Decision tree interaction uses AskUserQuestion with structured numbered options
