---
name: interview
description: >
  Gather requirements through structured interview before research or planning.
  Asks human-only questions that automated research cannot answer (business motivation,
  acceptance criteria, scope tradeoffs, success metrics). Uses relentless tree-walking
  until shared understanding is reached and the user explicitly confirms.
  Use when starting a new feature, before /research-problem or /create-plan-tdd.
  Trigger phrases: (1) "interview" (2) "gather requirements" (3) "clarify requirements"
  (4) "what are we building" (5) "requirements interview" (6) "grill me"
  (7) "thorough interview" (8) "deep dive requirements".
  Outputs to ~/.claude/thoughts/shared/requirements/.
---

# Requirements Interview

Gather human-only context through structured questioning before automated research begins.
Only ask questions that codebase-explorer and /operational-context
cannot answer.

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
   skip to Step 5 (write requirements directly). Tell the user what you found and why
   you're skipping the interview.
4. If information is insufficient, proceed to Step 2.

## Context-Sharing Protocol

The interview should build shared understanding collaboratively. Apply this protocol
throughout Steps 2 and 3 so the user always knows what the agent understands.

### Before a category of questions (Category Preamble)

Before asking questions in a new dimension or category, present:

1. **Current understanding** — A brief summary of what you understand so far about the
   problem, requirements, and context. This is your running mental model. For the first
   category, this comes from the input (Step 1). For subsequent categories, it incorporates
   answers from previous categories.
2. **What this category aims to clarify** — Explain what gap in understanding this category
   of questions will fill, and how the answers will help shape the implementation.

Format:

```
**My understanding so far:**
[2-4 sentences summarizing current understanding of the problem]

**What I'd like to clarify next — [Category Name]:**
[1-2 sentences explaining what information this line of questioning will provide
and why it matters for the implementation]
```

### After a category of questions (Category Wrap-Up)

After completing questions in a dimension, present:

1. **What I learned** — Summarize the key information gathered from this category's answers
2. **Updated understanding** — Present your updated mental model incorporating the new information

Format:

```
**What I gathered from [Category Name]:**
- [Key insight 1]
- [Key insight 2]

**Updated understanding:**
[2-4 sentences — your revised mental model of the problem and requirements]
```

_Non-interactive mode: Skip this protocol entirely — there is no human to share context with._

## Step 2: Premise Challenge & Scope Mode

Two AskUserQuestion calls, asked sequentially. Follow the Context-Sharing Protocol throughout.
Before the premise challenge, present your initial understanding from Step 1 and explain
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

## Step 3: Clarifying Questions

Read `references/question-categories.md` for question dimensions and domain detection.

Interview relentlessly about every aspect of this plan. Walk down each branch of the
design tree, resolving dependencies between decisions one-by-one. When an answer reveals
conditions or complexity ("it depends", "unless", "except when"), explore each condition
before moving on. Periodically check coverage against the dimension list in
`references/question-categories.md` — if a whole dimension is untouched, pivot there.
If a question can be answered by exploring the codebase, explore it instead. Continue
until all discovered branches are resolved AND all applicable dimensions have been covered.

Follow the Context-Sharing Protocol. Apply category preambles and wrap-ups when pivoting
to a new dimension or major branch of the design tree. When a dimension is fully resolved,
summarize what you learned before moving on.

Use AskUserQuestion with structured options when pre-defined options exist. Fall back to
free-form conversation for genuinely open-ended questions where options would be artificial.

**Exit condition**: Do NOT end the interview on your own. Continue asking questions until
you believe you have enough context to write a complete requirements document with no gaps.
Even then, you MUST proceed to Step 4 (Mutual Understanding Confirmation) — only the user's
explicit confirmation ends the interview.

_Non-interactive: skip this step. For each missing dimension, write an ASSUMPTION marker._

## Step 4: Mutual Understanding Confirmation

Before writing the requirements document, confirm that you and the user have reached shared
understanding. This is the ONLY way the interview ends — the user must explicitly confirm.

1. **Present your understanding** — Summarize the problem, scope, acceptance criteria, key
   decisions, and any domain-specific requirements in a concise format.
2. **Ask for confirmation** via AskUserQuestion: "Does this capture your intent accurately?
   Are there any gaps or misunderstandings?"
3. **If the user confirms** — proceed to Step 5.
4. **If the user identifies gaps** — ask targeted follow-up questions to close those gaps,
   then present your updated understanding and re-confirm. Repeat until the user explicitly
   confirms that the understanding is sufficient.

_Non-interactive: skip this step._

## Step 5: Write Requirements Document

1. Read `references/output-template.md` for the document structure.
2. Create `~/.claude/thoughts/shared/requirements/` directory if it doesn't exist.
3. Generate filename: `YYYY-MM-DD-<kebab-case-description>-requirements.md`
4. Write the requirements document with YAML frontmatter and all applicable sections.
5. Populate sections from interview answers (or assumptions in non-interactive mode).

## Step 6: Suggest Next Step

State the file path and suggest the next command:

```
Requirements saved to: [full path]

Next steps:
- Run `/research-problem [path]` to research the codebase and external context
- Run `/create-plan-tdd [path]` to create an implementation plan directly
- Run `/operational-context [component]` if you need production metrics first
```

## Reference Files

- **`references/question-categories.md`** — Read in Steps 2 and 3. Contains question
  dimensions with example patterns, domain detection signals, and skip conditions. These
  are guidance dimensions, not fixed questions — adapt wording to the specific feature.
  Domain examples (Backend/Data/ML) can be extended to any domain using the generation pattern.
- **`references/output-template.md`** — Read in Step 5. Contains the requirements document
  template with YAML frontmatter and section structure. Compatible with the
  claude-agent-orchestrator interview.py output format.
