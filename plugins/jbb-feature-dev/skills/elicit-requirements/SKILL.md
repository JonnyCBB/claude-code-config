---
name: elicit-requirements
description: >
  Gather requirements through structured questioning before research or planning.
  Asks human-only questions that automated research cannot answer (business motivation,
  acceptance criteria, scope tradeoffs, success metrics). Spawns context-gathering agents
  when artifacts are provided. Uses wave-based depth progression and relentless tree-walking
  until shared understanding is reached.
  Use when starting a new feature, before /research-problem or /create-plan-tdd.
  Trigger phrases: (1) "elicit requirements" (2) "gather requirements" (3) "requirements interview"
  (4) "what are we building" (5) "deep dive requirements" (6) "grill me"
  (7) "scope this feature" (8) "define requirements".
  Outputs to ~/.claude/thoughts/shared/requirements/.
---

# Requirements Elicitation

Gather human-only context through structured questioning, supported by targeted automated
research when uncertainty surfaces during the interview. The primary job is to ask questions
that codebase-explorer, web-search-researcher, web-search-researcher, and /operational-context cannot answer — but
when the user is unsure or a recommendation has no grounding, spawn research mid-interview to
discover which human-only questions still need asking (see Mid-Interview Research Triggers in
`../shared-references/elicit-shared-patterns.md`).

## Mode Detection

Parse `$ARGUMENTS` for flags and input:

- `--non-interactive`: Skip interview entirely. Read input, identify gaps, write requirements
  with ASSUMPTION/CONFIDENCE/IF-WRONG markers.
- File path argument: Read the file as the initial task description.
- No flags: Proceed to Step 1.

## Step 1: Assess Input & Maybe Skip

1. Read any provided file (ticket, research doc, goal description) FULLY.
2. If the user provides links (Slack, Google Docs, Jira), use ToolSearch to discover
   relevant MCP tools and fetch that context.
3. **Skip heuristic**: If the input already contains (a) clear objective, (b) context about
   which components/files, (c) at least 2 acceptance criteria, and (d) scope boundaries —
   skip to Step 6 (write requirements directly). Tell the user what you found and why
   you're skipping the interview.
4. If information is insufficient, proceed to Step 2.

## Step 2: Context Sprint (Optional)

Scan the user's input for actionable artifacts that are relevant to their question.
If no relevant artifacts are found, skip directly to Step 3.

### Entity Detection and Spawning Rules

For the artifact → agent dispatch table and spawning rules, see `../shared-references/elicit-shared-patterns.md` (`## Agent Dispatch`). Standard variant: only spawn when artifacts are detected AND relevant — this step is OPTIONAL.

**Agent delivery resilience**: Subagents may go idle without delivering results (known Claude Code issue). If an agent sends an `idle_notification` without content: (1) prompt it via SendMessage using its agent ID (not name), (2) if still no delivery, respawn once, (3) if respawn fails, gather data directly or document the gap.

### Context Integration

Feed gathered context into the interview in five ways:

1. **Enhanced Skip Heuristic** — agent findings may satisfy the Step 1 skip criteria (objective + components + acceptance criteria + scope boundaries).
2. **Informed Category Preambles** — fold research findings into the Context-Sharing Protocol preambles ("Based on my research, [component X] uses [pattern Y]…").
3. **Targeted Question Generation** — replace generic dimension questions with specifics discovered during research (e.g. cite the actual p99 latency instead of asking "any latency budget?").
4. **Domain Auto-Detection** — if domains match the procedure in `shared-references/domain-agent-registry.md`, auto-activate the corresponding question dimensions in Step 4.
5. **Contradiction Reconciliation** — during Step 4, surface conflicts between user claims and Context Sprint findings ("the code shows X but you said Y — which is right?"). Skip if Context Sprint did not spawn agents; frame findings as observations to guard against stale-index false positives.

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

_Non-interactive: skip this step. Default to MVP scope mode. Document as assumption._

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

Between waves, run a synthesis checkpoint using the Context-Sharing Protocol's category
wrap-up format. Summarize what was learned, present your updated understanding, then
proceed to the next wave.

Interview relentlessly within each wave. Walk down each branch of the design tree,
resolving dependencies one-by-one. When an answer reveals conditions or complexity
("it depends", "unless", "except when"), explore each condition before moving on.
Continue until all discovered branches are resolved AND all applicable dimensions in the
current wave have been covered before moving to the next wave.

Follow the Context-Sharing Protocol. Apply category preambles and wrap-ups when pivoting
to a new dimension or major branch of the design tree. When a dimension is fully resolved,
summarize what you learned before moving on.

Use AskUserQuestion with structured options when pre-defined options exist. Fall back to
free-form conversation for genuinely open-ended questions where options would be artificial.

- Apply the Recommended-answer principle (see Context-Sharing Protocol) to every question.
  Skip the recommendation only for questions where you have no grounding evidence.
- **Research on demand** — when the user signals uncertainty on a research-answerable
  question, when a recommendation has no grounding, or when an answer opens a new branch an
  agent could resolve, spawn research per `../shared-references/elicit-shared-patterns.md`
  (`## Mid-Interview Research Triggers`) rather than immediately recording an ASSUMPTION.
  Findings expand the design tree; do not end the wave until newly-revealed branches are
  explored.
- If Context Sprint produced findings, reconcile user statements against them as they
  come up (see Step 2, Contradiction Reconciliation mode).
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

_Non-interactive: skip this step. For each missing dimension, write an ASSUMPTION marker._

## Step 5: Mutual Understanding Confirmation

Before writing the requirements document, confirm that you and the user have reached shared
understanding. This is the ONLY way the interview ends — the user must explicitly confirm.

1. **Present your understanding** — Summarize the problem, scope, acceptance criteria, key
   decisions, and any domain-specific requirements in a concise format.
2. **Ask for confirmation** via AskUserQuestion: "Does this capture your intent accurately?
   Are there any gaps or misunderstandings?"
3. **If the user confirms** — proceed to Step 6.
4. **If the user identifies gaps** — ask targeted follow-up questions to close those gaps,
   then present your updated understanding and re-confirm. Repeat until the user explicitly
   confirms that the understanding is sufficient.

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
5. Populate sections from interview answers (or assumptions in non-interactive mode).

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
