---
name: elicit-requirements-friendly
description: >
  Gather requirements through a friendly, story-based, one-question-at-a-time interview
  designed for non-technical users (and technical users in unfamiliar domains). Forks
  elicit-requirements with the same output schema so /research-problem and /implement-change
  work unchanged. Aggressively frontloads references (screenshots, links, brand colors),
  spawns context agents to fill technical gaps the user can't, and translates jargon
  inline. Always thorough — walks every branch of the design tree in friendly tone.
  Trigger phrases: (1) "elicit requirements" (friendly variant) (2) "interview me"
  (3) "non-technical" (4) "intake" (5) "PRD" (6) "friendly" requirements interview.
  Outputs to ~/.claude/thoughts/shared/requirements/.
---

# Friendly Requirements Elicitation

Gather requirements through a one-question-at-a-time, story-based interview. Share the
standard variant's output schema and decision rules; keep the conversation in the user's
language.

## Mode Detection

Parse `$ARGUMENTS` for flags and input:

- `--non-interactive`: read supplied references without asking for more (Step 1), run
  relevant context research (Step 2), then write the document (Step 6).
  Skip Steps 3-5; mark unanswered consequential decisions as unconfirmed assumptions.
- File path argument: read the file as the initial task description (alongside any pasted
  links, screenshots, or other artifacts).
- No flags: proceed to Step 1.

## Step 1: Aggressive Frontload

In interactive mode, first ask for the references the user has:

- Screenshots, sketches, or photos of paper notes
- Links — Slack threads, Jira tickets, Google Docs, web URLs, PDF specs, anything
- Brand colors, logos, example apps that match the "vibe"
- Names of people, teams, or systems involved

Use `ToolSearch` to discover the right MCP tool for each link type (Slack MCP for Slack,
Atlassian MCP for Jira, Google Workspace MCP for Google Docs, WebFetch for web URLs). Read every
artifact **fully** before proceeding — fetch the full content, not just the title or
preview.

If the user has nothing to share, continue to Step 2. In non-interactive mode, read
supplied references and proceed without a question.

## Step 2: Autonomous Context Sprint

Spawn context-gathering agents aggressively. The friendly variant compensates for users
who cannot fill technical gaps themselves — the agent must do that work without leaning
on the user.

Detect actionable artifacts in the input and the Step 1 references, then spawn the agents listed in `../shared-references/elicit-shared-patterns.md` (`## Agent Dispatch`). Friendly-variant policy: spawn aggressively, not optionally. **Agent delivery resilience**: if an agent sends an `idle_notification` without content, prompt it via SendMessage using its agent ID (not name); if still no delivery, respawn once; if respawn fails, gather data directly or document the gap. Use the findings to:

- Record existing codebase behavior as sourced facts in `## Context`, not as new agent
  decisions in `## Technical Assumptions`.
- Reconcile any contradictions between what the user said and what the code or docs show
  by surfacing the contradiction politely in Step 4 ("the code shows X but you mentioned
  Y — which is right?").
- Skip questions the agent now has confident answers to.

Do **not** dump raw agent output on the user. Summarize sourced findings concisely in
`## Context`.

## Step 3: Soft Premise Check

One `AskUserQuestion`, asked gently. Goal: validate the problem is real before drilling.

Ask: "Is this a recurring annoyance, a preventive idea, or a one-time wish?"

Options (lead with the agent's best guess labeled "(Recommended)"):

- A) Recurring annoyance — happens regularly and we want it gone
- B) Preventive idea — hasn't bitten us yet but we'd like to get ahead of it
- C) One-time wish — just for this specific situation

Skip Step 3 if the supplied evidence already answers it (for example, a ticket with
reproduction steps and a stakeholder request). Cite the evidence in `## Context` rather
than treating it as a silent decision.

The friendly variant deliberately avoids confrontational premise phrasing. This is a Soft
Premise Check, not a "your problem might not be worth solving" challenge.

## Step 4: Friendly Interview

This is the heart of the skill. Mechanics:

- **One question per message.** Ask about one information need, not several subquestions
  joined in a sentence. Wait for the answer, summarize what you heard, then ask the next.
- Use `AskUserQuestion` with structured options whenever they exist. Label option A
  "(Recommended)" with the agent's best guess grounded in evidence (Step 1 input, Step 2
  context, codebase finding). Cite the grounding in the question stem.
- For open-ended questions, draw from `references/question-bank.md` Story Prompts (Top
  10). These are story-based ("Tell me about the last time…") rather than opinion-based
  ("What do you want…"). Stories beat opinions.
- When asking an open-ended question, paste the matching pair from `references/exemplars.md`
  inline so the user sees what good and vague look like for that dimension. Adapt the
  example to the user's scenario; do not imply its invented details happened to them.
- For non-functional concerns, use the user-language NFR probes from
  `references/question-bank.md` ("How long would feel too long?" instead of "what is
  your latency budget?").
- **Show a running spec recap every 3-5 questions.** Read it back in the user's words,
  not yours. ("So far I'm hearing: a page where customers see their orders, with status
  badges, default view of the last 30 days.")
- **Translate jargon inline.** Use the jargon translation table in
  `references/question-bank.md`. If you must use a technical term, translate it on first
  use and parenthesize the technical term once for the record.
- **Decision authority.** Follow `../shared-references/elicit-shared-patterns.md`
  (`## Outcomes and Decision Authority`). Ask about consequential choices even when
  invisible, and ask why a named technique matters before making it required.
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

In interactive mode, continue until you can describe the outcome without consequential
gaps, then proceed to Step 5. Only explicit owner confirmation ends the interview.

## Step 5: Mutual Understanding Confirmation

In interactive mode, confirm shared understanding before writing. Do not claim
confirmation in non-interactive mode.

1. Present your understanding of the outcome, scope, observable success, consequential
   decisions (including invisible ones), unresolved assumptions, and any domain-specific
   requirements in the user's plain language, not GIVEN/WHEN/THEN. Distinguish their
   choices from researched facts and reversible agent choices.
2. Ask explicit confirmation via `AskUserQuestion`: "Does this capture your intent
   accurately? Are there any gaps or misunderstandings?"
3. If the user confirms, proceed to Step 6.
4. If the user identifies gaps, ask targeted follow-ups, then re-present and re-confirm.
   Repeat until the user explicitly confirms.

Present reversible agent choices in the summary for correction, not as owner approvals.
Ask targeted questions about consequential choices before seeking summary confirmation.

## Step 6: Write Requirements Document

1. Read `references/output-template.md` for the document structure.
2. Create `~/.claude/thoughts/shared/requirements/` if it does not exist.
3. Generate filename: `YYYY-MM-DD-<kebab-case-description>-requirements.md`
4. Synthesize the conversational outcomes into observable acceptance scenarios; the user
   need not learn GIVEN/WHEN/THEN or choose an implementation route.
5. Include only necessary reversible choices in `## Technical Assumptions` with their
   reason and reversibility. In non-interactive mode, mark unanswered consequential
   decisions as unconfirmed assumptions with basis, confidence, owner if known, and
   what changes if wrong. If scope mode was not supplied, use provisional MVP and
   mark `scope_mode_confirmed: false` in frontmatter, and record it as an unconfirmed
   assumption, not an owner choice.
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
- **`references/escalation-and-authority.md`** — Concrete authority and vague-answer
  pivot examples. Read in Step 4.
- **`references/output-template.md`** — Pointer to the shared document schema. Read in
  Step 6.
