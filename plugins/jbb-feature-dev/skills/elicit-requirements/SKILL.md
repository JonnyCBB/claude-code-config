---
name: elicit-requirements
description: >
  Gather requirements through structured questioning before research or planning.
  Asks human-only questions that automated research cannot answer (business motivation,
  acceptance criteria, scope tradeoffs, success metrics). Spawns context-gathering agents
  when artifacts are provided. Uses wave-based depth progression and relentless tree-walking
  until shared understanding is reached.
  Use when starting a new feature, before /research-problem or /implement-change.
  Trigger phrases: (1) "elicit requirements" (2) "gather requirements" (3) "requirements interview"
  (4) "what are we building" (5) "deep dive requirements" (6) "grill me"
  (7) "scope this feature" (8) "define requirements".
  Outputs to ~/.claude/thoughts/shared/requirements/.
---

# Requirements Elicitation

Gather human-only context through structured questioning, supported by targeted automated
research when uncertainty surfaces during the interview. The primary job is to ask questions
that codebase-explorer, web-search-researcher, and thoughts-explorer cannot answer — but
when the user is unsure or a recommendation has no grounding, spawn research mid-interview to
discover which human-only questions still need asking (see Mid-Interview Research Triggers in
`../shared-references/elicit-shared-patterns.md`).

## Mode Detection

Parse `$ARGUMENTS` for flags and input:

- `--non-interactive`: Skip interview and summary confirmation. Read input, research discoverable
  gaps, write requirements with unconfirmed assumptions.
- File path argument: Read the file as the initial task description.
- No flags: Proceed to Step 1.

## Step 1: Assess Input & Maybe Skip

1. Read any provided file (ticket, research doc, goal description) FULLY.
2. If the user provides links (Slack, Google Docs, Jira), use ToolSearch to discover
   relevant MCP tools and fetch that context.
3. **Skip heuristic**: If the input has a clear objective, relevant context, at least two
   acceptance criteria, and scope boundaries, skip only questions it answers. If scope
   posture (MVP, complete, or ambitious) was not chosen, still ask Step 3's scope
   question. Check for unanswered consequential choices (see `## Outcomes and Decision
   Authority` in the shared reference); ask those in Step 4 before Step 5. If none
   remain, tell the user why you're skipping redundant questions and proceed to Step 5. Never skip summary
   confirmation in interactive mode.
4. Otherwise proceed to Step 2. In non-interactive mode, research supplied artifacts
   where useful, then write without asking for answers or confirmation.

## Step 2: Context Sprint (Optional)

Scan the user's input for actionable artifacts that are relevant to their question.
If no relevant artifacts are found, skip directly to Step 3.

### Entity Detection and Spawning Rules

For the artifact → agent dispatch table and spawning rules, see `../shared-references/elicit-shared-patterns.md` (`## Agent Dispatch`). Standard variant: only spawn when artifacts are detected AND relevant — this step is OPTIONAL.

**Agent delivery resilience**: Subagents may go idle without delivering results (known Claude Code issue). If an agent sends an `idle_notification` without content: (1) prompt it via SendMessage using its agent ID (not name), (2) if still no delivery, respawn once, (3) if respawn fails, gather data directly or document the gap.

### Context Integration

Use findings to update Step 1's skip check (objective, components, acceptance
criteria, scope boundaries), ground category preambles and questions in specifics
(e.g. observed p99 latency), and activate Step 4's domain dimensions via
`shared-references/domain-agent-registry.md`. In Step 4, surface conflicts with
user claims as observations, not proof from potentially stale indexes. Skip
reconciliation if no agents ran.

### What NOT to Do

See `../shared-references/elicit-shared-patterns.md` (`## Agent Dispatch` → `### What NOT to do`).

_Non-interactive: run Context Sprint if artifacts are detected; skip otherwise._

## Context-Sharing Protocol

The interview should build shared understanding collaboratively. Apply this protocol
throughout Steps 3 and 4 so the user always knows what the agent understands.

### Before a category of questions (Category Preamble)

Before asking questions in a new dimension, present (1) your current running mental model and (2) what gap this category fills.

```
**My understanding so far:** [2-4 sentences]

**What I'd like to clarify next — [Category Name]:** [1-2 sentences on why it matters]
```

### After a category of questions (Category Wrap-Up)

After completing a dimension, present what you learned and the updated mental model.

```
**What I gathered from [Category Name]:**
- [Key insight 1]
- [Key insight 2]

**Updated understanding:** [2-4 sentences — revised model]
```

### Recommended-answer principle (per question)

Every interview question carries the agent's best guess, grounded in evidence already gathered (Step 1 input, Context Sprint, codebase). Users confirm or correct; they don't draft from scratch.

Phrasing template: "Based on [ticket / Context Sprint finding / code at file:line], I'd suggest [X] — does this match?" With `AskUserQuestion`: option A gets "(Recommended)" appended.

Anti-anchoring: cite grounding (or classify as genuinely open if none), invite dissent in phrasing, and pause if the user rubber-stamps multiple answers in a row.

_Non-interactive mode: Skip this protocol entirely — there is no human to share context with._

## Step 3: Premise Challenge & Scope Mode

Two AskUserQuestion calls, asked sequentially. Follow the Context-Sharing Protocol throughout.
Before the premise challenge, present your initial understanding from Steps 1-2 and explain
that you want to validate the problem framing before diving into details.
After both questions, present a category wrap-up summarizing what you learned about the
problem's validity and scope posture.

**First — Premise challenge**: Before diving into details, validate the problem is worth solving.
Read `references/question-categories.md` for the premise challenge dimension.
Ask one question using AskUserQuestion with options. Lead with your recommendation.
**Skip if**: Bug fix with clear repro steps, or ticket with documented stakeholder sign-off.

**Second — Scope mode**: Ask the user to choose their scope posture.
Options: A) MVP — minimum that ships value B) Complete — full scope, make it bulletproof
C) Ambitious — go beyond the ask if it creates a better outcome.
Do not treat supplied scope boundaries as a choice of scope posture; ask unless the
owner already chose one.

_Non-interactive: skip this step. Default to provisional MVP scope mode with
`scope_mode_confirmed: false`; document it as an assumption, not an owner choice._

## Step 4: Clarifying Questions

Read `references/question-categories.md` for question dimensions, wave assignments, and
domain detection.

Work through questions in wave order:

**Wave 1 (Foundational)**: Core understanding — motivation, acceptance criteria, success
metrics, scope. These establish the baseline understanding of the problem.

**Wave 2 (Nuances)**: Situational depth — edge cases, non-functional requirements,
deployment strategy, historical context. These refine the baseline with operational detail.

**Wave 3 (Deep/Domain)**: Domain-specific — activated based on domain detection signals
from both the task description AND Context Sprint findings (Step 2). Only ask dimensions
relevant to detected domains.

Between waves, recap what was learned and your updated understanding using the
Context-Sharing Protocol. Walk every branch within a wave, resolving dependencies
and exploring conditions ("it depends", "unless", "except when") before moving on.
Cover all applicable dimensions before advancing. Use category preambles and
wrap-ups at each new dimension or major branch; recap each resolved dimension.
Use AskUserQuestion for structured options, or free-form conversation when
options would be artificial.

- Apply the Recommended-answer principle (see Context-Sharing Protocol) to every question.
  Skip the recommendation only for questions where you have no grounding evidence.
- Apply `../shared-references/elicit-shared-patterns.md` (`## Outcomes and Decision Authority`):
  ask why a named technique matters before making it a constraint, and ask the owner about
  consequential decisions even when the effect is invisible to users.
- **Research on demand** — when the user signals uncertainty on a research-answerable
  question, when a recommendation has no grounding, or when an answer opens a new branch an
  agent could resolve, spawn research per `../shared-references/elicit-shared-patterns.md`
  (`## Mid-Interview Research Triggers`) rather than immediately recording an ASSUMPTION.
  Findings expand the design tree; do not end the wave until newly-revealed branches are
  explored.
- **Terminology sharpening** — When a term is ambiguous, pause to disambiguate. Apply the
  trigger rule: "Am I confused about which of two things the user means, or am I just
  unfamiliar with the word?" Only the former triggers a pause. Example: "You said 'account'
  — do you mean the Customer account or the User account? Those are different."
  - Record resolved forks in the output doc's optional `## Terminology` section.
  - For jargon you don't recognise but aren't confused about: do NOT pause. Note it as
    `UNKNOWN_TERM: <term>` in the output doc's optional `## Unknown Terms` section (and
    in the Assumptions section for non-interactive mode). `/research-problem` will resolve
    these downstream.
- **Stress-test scenarios** — When a Wave 2 edge-case answer is vague ("handle failures
  gracefully", "usually works"), invent concrete scenarios and ask the user to adjudicate.
  Seed scenarios from Context Sprint findings when possible (real states, not
  hypotheticals). Each scenario carries a recommended resolution per the Recommended-answer
  principle. Use judgment on how many to invent — enough to resolve the vagueness, not so
  many that you create contrived scope creep.

**Exit condition**: Do NOT end the interview on your own. Continue asking questions until
you believe you have enough context to write a complete requirements document with no gaps.
Even then, you MUST proceed to Step 5 (Mutual Understanding Confirmation) — only the user's
explicit confirmation ends the interview.

_Non-interactive: skip this step. Mark unresolved consequential choices as unconfirmed
assumptions; do not turn every missing interview dimension into an assumed requirement._

## Step 5: Mutual Understanding Confirmation

The interview ends only when the user explicitly confirms shared understanding.

1. Summarize the outcome, scope, observable success, consequential decisions (including
   invisible ones), and unresolved assumptions in plain language. Distinguish owner
   answers from researched facts and reversible agent choices.
2. Ask via AskUserQuestion: "Does this capture your intent accurately? Are there any
   gaps or misunderstandings?" If they identify gaps, ask targeted follow-ups and
   re-confirm the updated understanding. Proceed to Step 6 only on explicit confirmation.

_Non-interactive: skip this step._

## Step 6: Write Requirements Document

1. Read `references/output-template.md` for the document structure.
2. Create `~/.claude/thoughts/shared/requirements/` directory if it doesn't exist.
3. Generate filename: `YYYY-MM-DD-<kebab-case-description>-requirements.md`
4. Write the requirements document with YAML frontmatter and all applicable sections.
   If terminology forks were resolved during Step 4, include the optional `## Terminology`
   section. If unfamiliar jargon was noted as `UNKNOWN_TERM`, include the optional
   `## Unknown Terms` section (and mirror the markers in the Assumptions section for
   non-interactive mode).
5. Populate sections from interview answers and sourced findings; set
   `scope_mode_confirmed` to match whether the owner chose the scope. In non-interactive
   mode, mark unanswered consequential choices as unconfirmed assumptions, not owner
   decisions.

## Step 7: Suggest Next Step

See `../shared-references/elicit-shared-patterns.md` (`## Suggest Next Step`).

## Reference Files

- **`references/question-categories.md`** — Read in Steps 3 and 4. Contains question
  dimensions with wave assignments, example patterns, domain detection signals, and skip
  conditions. These are guidance dimensions, not fixed questions — adapt wording to the
  specific feature. Domain examples (Backend/Data/ML) can be extended to any domain using
  the generation pattern.
- **`references/output-template.md`** — Read in Step 6. Contains the requirements document
  template with YAML frontmatter and section structure. Compatible with the
  claude-agent-orchestrator interview.py output format.
