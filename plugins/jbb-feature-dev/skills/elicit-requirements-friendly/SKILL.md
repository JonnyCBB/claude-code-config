---
name: elicit-requirements-friendly
description: >
  Gather requirements through a friendly, story-based, one-question-at-a-time interview
  designed for non-technical users (and technical users in unfamiliar domains). Forks
  elicit-requirements with the same output schema so /research-problem and /create-plan-tdd
  work unchanged. Aggressively frontloads references (screenshots, links, brand colors),
  spawns context agents to fill technical gaps the user can't, and translates jargon
  inline. Always thorough — walks every branch of the design tree in friendly tone.
  Trigger phrases: (1) "elicit requirements" (friendly variant) (2) "interview me"
  (3) "non-technical" (4) "intake" (5) "PRD" (6) "friendly" requirements interview.
  Outputs to ~/.claude/thoughts/shared/requirements/.
---

# Friendly Requirements Elicitation

Gather requirements through a friendly, story-based interview designed for users who do not
speak the language of software engineering. The skill preserves the output schema of
`elicit-requirements` exactly so downstream tools (`/research-problem`, `/create-plan-tdd`)
work without modification — what changes is the **interaction style**, not the artifact.

Differences from the standard `elicit-requirements` skill:

- One question per message (no batching), with structured options when possible.
- Story-based prompts ("Tell me about the last time…") instead of opinion-based prompts
  ("What do you want…").
- Inline good-vs-vague exemplars when asking open-ended questions, so users learn what
  depth lands without being lectured about specificity.
- Running spec recap every 3-5 questions in the user's own words.
- Inline jargon translation — the agent translates **its** technical terms for the user
  rather than asking the user to learn them.
- After two vague answers in a row on the same dimension, pivot to "let's back up" instead
  of drilling further.
- Decision-authority rule: ask only when the answer changes the user's mental model of the
  product; decide silently and record in `## Technical Assumptions` otherwise.
- Always thorough — no depth flag, no early exit. The friendly tone makes thoroughness
  bearable; thoroughness gives the user every chance to nail their requirements down.

## Mode Detection

Parse `$ARGUMENTS` for flags and input:

- `--non-interactive`: skip the interview entirely. Read input, identify gaps, write
  requirements with ASSUMPTION/CONFIDENCE/IF-WRONG markers and populate `## Technical
Assumptions` with every decision the agent had to make alone.
- File path argument: read the file as the initial task description (alongside any pasted
  links, screenshots, or other artifacts).
- No flags: proceed to Step 1.

## Step 1: Aggressive Frontload

The first message asks for **every reference the user has** before any interview begins.
Concretely, ask the user for:

- Screenshots, sketches, or photos of paper notes
- Links — Slack threads, Jira tickets, Google Docs, web URLs, PDF specs, anything
- Brand colors, logos, example apps that match the "vibe"
- Names of people, teams, or systems involved

Use `ToolSearch` to discover the right MCP tool for each link type (Slack MCP for Slack,
Atlassian MCP for Jira, GDrive MCP for Google Docs, WebFetch for web URLs). Read every
artifact **fully** before proceeding — fetch the full content, not just the title or
preview.

If the user has nothing to share, that is a valid answer. Continue to Step 2.

## Step 2: Autonomous Context Sprint

Spawn context-gathering agents aggressively. The friendly variant compensates for users
who cannot fill technical gaps themselves — the agent must do that work without leaning
on the user.

Detect actionable artifacts in the input and the Step 1 references, then spawn the agents listed in `../shared-references/elicit-shared-patterns.md` (`## Agent Dispatch`). Friendly-variant policy: spawn aggressively, not optionally. **Agent delivery resilience**: if an agent sends an `idle_notification` without content, prompt it via SendMessage using its agent ID (not name); if still no delivery, respawn once; if respawn fails, gather data directly or document the gap. Use the findings to:

- Pre-fill the `## Technical Assumptions` section with decisions the codebase has already
  made on the user's behalf (existing patterns, conventions, libraries in use).
- Reconcile any contradictions between what the user said and what the code or docs show
  by surfacing the contradiction politely in Step 4 ("the code shows X but you mentioned
  Y — which is right?").
- Skip questions the agent now has confident answers to.

Do **not** dump raw agent output on the user. Summarize concisely or save it for the
`## Technical Assumptions` section.

## Step 3: Soft Premise Check

One `AskUserQuestion`, asked gently. Goal: validate the problem is real before drilling.

Ask: "Is this a recurring annoyance, a preventive idea, or a one-time wish?"

Options (lead with the agent's best guess labeled "(Recommended)"):

- A) Recurring annoyance — happens regularly and we want it gone
- B) Preventive idea — hasn't bitten us yet but we'd like to get ahead of it
- C) One-time wish — just for this specific situation

Skip Step 3 entirely if Step 1 input was rich enough that the answer is obvious from the
artifacts (a Jira ticket with reproduction steps and a stakeholder request, for example).
This skip is silent — the agent records the inferred answer in `## Technical Assumptions`
rather than burning a question.

The friendly variant deliberately avoids confrontational premise phrasing. This is a Soft
Premise Check, not a "your problem might not be worth solving" challenge.

## Step 4: Friendly Interview

This is the heart of the skill. Mechanics:

- **One question per message.** Never batch. Wait for the answer, summarize what you
  heard, then ask the next.
- Use `AskUserQuestion` with structured options whenever they exist. Label option A
  "(Recommended)" with the agent's best guess grounded in evidence (Step 1 input, Step 2
  context, codebase finding). Cite the grounding in the question stem.
- For open-ended questions, draw from `references/question-bank.md` Story Prompts (Top
  10). These are story-based ("Tell me about the last time…") rather than opinion-based
  ("What do you want…"). Stories beat opinions.
- When asking an open-ended question, paste the matching pair from `references/exemplars.md`
  inline so the user sees what good and vague look like for that dimension. This teaches
  depth without lecturing.
- For non-functional concerns, use the user-language NFR probes from
  `references/question-bank.md` ("How long would feel too long?" instead of "what is
  your latency budget?").
- **Show a running spec recap every 3-5 questions.** Read it back in the user's words,
  not yours. ("So far I'm hearing: a page where customers see their orders, with status
  badges, default view of the last 30 days.")
- **Translate jargon inline.** Use the jargon translation table in
  `references/question-bank.md`. If you must use a technical term, translate it on first
  use and parenthesize the technical term once for the record.
- **Decision-authority rule.** Ask the user only when the answer changes the user's
  mental model of the product (UX-affecting choices). Decide silently when the choice
  affects only implementation. Record every silent decision in the `## Technical
Assumptions` section using the decisions-log shape from
  `references/escalation-and-authority.md` (Decision / Why / Reversibility).
- **Escalation: after two vague answers in a row** on the same dimension, pivot to "let's
  back up" — read the spec back, ask the user to describe what they're picturing, and
  restart the dimension with a fresh story prompt. See `references/escalation-and-authority.md`
  for the full pivot routine.
- **Always thorough.** No depth flag, no early exit. Walk every branch of the design tree
  ("it depends" / "unless" / "except when") in friendly tone. Friendly thoroughness is
  the whole point — give the user every chance to nail it down.
- **Research on demand.** When the user signals uncertainty on a research-answerable
  question, when a recommendation has no grounding, or when an answer opens a new branch
  an agent could resolve, spawn research per `../shared-references/elicit-shared-patterns.md`
  (`## Mid-Interview Research Triggers`) rather than recording an assumption. Findings
  expand the design tree; do not end the wave until newly-revealed branches are explored.

Continue until you believe you can write a complete requirements document with no gaps.
Then proceed to Step 5 — only the user's explicit confirmation ends the interview.

## Step 5: Mutual Understanding Confirmation

Before writing the document, confirm shared understanding. This is the **only** stopping
criterion — there is no quality grade, no automatic exit, no completeness rubric.

1. Present your understanding of the problem, scope, acceptance criteria (in the user's
   plain-language form, not GIVEN/WHEN/THEN), key technical assumptions, and any
   domain-specific requirements.
2. Ask explicit confirmation via `AskUserQuestion`: "Does this capture your intent
   accurately? Are there any gaps or misunderstandings?"
3. If the user confirms, proceed to Step 6.
4. If the user identifies gaps, ask targeted follow-ups, then re-present and re-confirm.
   Repeat until the user explicitly confirms.

Do **not** present the `## Technical Assumptions` entries as questions; present them as a
summary list and invite the user to flag any that are wrong. The intent is rubber-stamp,
not interrogation.

## Step 6: Write Requirements Document

1. Read `references/output-template.md` for the document structure.
2. Create `~/.claude/thoughts/shared/requirements/` if it does not exist.
3. Generate filename: `YYYY-MM-DD-<kebab-case-description>-requirements.md`
4. Populate every applicable section. Synthesize the conversational acceptance-criteria
   answers silently into GIVEN/WHEN/THEN form — the downstream contract requires it but
   the user never had to learn the syntax.
5. Populate the new `## Technical Assumptions` section with one entry per silent decision
   the agent made during Steps 1-4. Use the Decision / Why / Reversibility shape. Err
   toward more entries rather than fewer — every choice the user did not weigh in on
   belongs here.
6. Write to `~/.claude/thoughts/shared/requirements/YYYY-MM-DD-<kebab>-requirements.md`.

## Step 7: Suggest Next Step

See `../shared-references/elicit-shared-patterns.md` (`## Suggest Next Step`).

## Reference Files

- **`references/question-bank.md`** — Top 10 verbatim story prompts, NFR probes in
  user-language, and the jargon translation table. Read in Step 4 when picking which
  question to ask.
- **`references/exemplars.md`** — Good-vs-vague answer pairs, one per question dimension.
  Surface inline in Step 4 whenever asking an open-ended question, so the user sees what
  depth lands.
- **`references/escalation-and-authority.md`** — Decision-authority heuristic (ask vs
  decide silently), vague-answer escalation triggers, "let's back up" pivot routine, and
  the decisions-log shape for `## Technical Assumptions` entries. Read in Steps 4 and 6.
- **`references/output-template.md`** — Requirements document template. Inherits the
  schema from `elicit-requirements/references/output-template.md` and adds `## Technical
Assumptions`. Read in Step 6.
