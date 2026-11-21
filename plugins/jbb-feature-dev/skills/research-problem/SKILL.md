---
name: research-problem
description: >
  Conduct comprehensive research across the codebase and beyond by spawning parallel
  sub-agents and synthesizing their findings into a research document. Supports interactive
  mode (default) with user confirmation checkpoints, and non-interactive mode for pipeline
  use. Outputs research documents to ~/.claude/thoughts/shared/research/. Trigger phrases:
  (1) "research" (2) "investigate" (3) "explore how" (4) "document how"
  (5) "research problem".
argument-hint: "[query] [--non-interactive]"
---

# Research Problem

Answer the user's research question by spawning parallel sub-agents and synthesizing their
findings into a document. Describe what exists, where, how it works, and how components
interact. Suggest improvements, root causes or critiques only when the user asks.

## Every step runs

Every step below runs on every invocation. No complexity tier, mode flag, time pressure or
token budget removes one, and your judgement that a step's work is already covered is not
grounds for skipping it: that judgement is what the step checks. The steps most often dropped
are the three that grade the work (Steps 6, 7 and 8), and when they run late their findings
routinely change the conclusions.

- A step that did not run is never recorded as `completed`. If it cannot run, stop and say so.
- Every step writes a row in the document's **Step Ledger** (`references/document-template.md`),
  including any deviation, in plain words.
- The Step 6 evaluator, Step 7 reviewers and Step 8 verification agent are separate agents.
  You never do their job. If one will not deliver, follow Agent Delivery Resilience below,
  which ends in a recorded failure, not in self-substitution.

## Run ledger and stopping

You own one run ledger for the whole run. It holds a stable ID for every question, success
criterion, claim, evaluator flag, reviewer gap, candidate Open Question and follow-on; the
evidence, errors and classification for each; and the round counters (completeness rounds,
persona-review rounds, grounding iterations). The bounds live in the reference files, each
stated once. Revisions, handoffs and delivery recovery never reset a counter.

A bound stops the run; it never passes a gate. When a required counter runs out, or a
material gap needs evidence you cannot get, save the draft as an **incomplete checkpoint**:
the open IDs, what was attempted, the evidence, and the next action. Do not write it up as a
completed document.

"Material" always means the Materiality Filter in `references/grounding-pass.md`. Agents
collect evidence through reads only: they do not send messages, mutate records, connect
servers or change settings.

## Agent Delivery Resilience

Subagents sometimes go idle without delivering: the agent finishes but the harness drops its
output. This hits tool-using agents and no-tool judges alike. When an agent sends an
`idle_notification` with `idleReason: "available"` and no content:

1. Wait briefly. It may deliver just after the idle signal.
2. Prompt it via `SendMessage` with its **bare name**. The `name@session-id` form is rejected
   (`to must be a bare teammate name -- there is only one team per session`). Use the raw
   `agentId` only when the agent is unnamed or a newer agent has taken its name.
3. Respawn once with the same prompt.
4. If it still has not delivered, record in the Step Ledger the agent's name, the two
   attempts, and what is missing. Gather what you can directly, but never self-evaluate,
   self-review or self-verify in its place.

Record every spawned agent's name and id. Split batches larger than 5 into sequential
sub-batches of 3-5: parallel Agent calls can cascade-fail.

## Mode Detection

Parse `$ARGUMENTS`. `--non-interactive` sets NON_INTERACTIVE mode; the rest is the query. A
file path in `$ARGUMENTS` is read as the query input. With no query, ask for one and wait.

NON_INTERACTIVE removes only the three places a human is asked something: the Step 2
confirmation, the Step 14 follow-up prompt, and Step 15. It removes no check.

## Step 1: Read Mentioned Files First

Read every mentioned source in full, continuing any truncated output. Read Google Docs with
the document-read tools.

## Step 2: Analyze and Decompose

Read `references/plan-templates.md`. Produce: Research Questions (each with its agent type),
Assumptions, Success Criteria, Scope, Research Context, Research Execution Plan, Domain Expert
Check (against the table in `references/agent-guide.md`), Agent Type Verification, and
Complexity Classification. Complexity sets how many reviewers run in Step 7, never whether
Step 7 runs.

- **Interactive**: output the full plan in your response, every section, not summarized and
  not written to a file. Then call `AskUserQuestion` ("Proceed with this plan" / "Request
  changes" / "Cancel") and wait. On "Request changes", revise and ask again.
- **NON_INTERACTIVE**: save the plan to
  `~/.claude/thoughts/shared/research_plans/YYYY-MM-DD-description-plan.md` with frontmatter
  `status: approved`, then proceed.

## Step 3: Spawn Sub-Agent Tasks

Read `references/agent-guide.md`. At least one research agent is spawned on every run. If
Step 2 left every question Direct, the classification is the defect: return to it. Having read
the files in Step 1 does not replace this step.

- Output the Pre-Spawn Verification Table before any spawn.
- Run batches in sequence, agents within a batch in parallel. Pass each batch's findings,
  terminology and file paths into the next as "Prior Findings".
- You may combine closely related questions into one agent; say which and why.
- Tell every agent to document by default, and to evaluate only when the user asked.

Then create one task per remaining step with `TaskCreate` (Steps 4-9, the Pre-Document Gate,
Steps 10-13). Mark each `in_progress` when you start and `completed` only when its work
happened. Before starting a step, call `TaskList`: a pending task behind a completed one means
you are about to skip something.

## Step 4: Validate Agent Completion

Read `references/verification-and-iteration.md`. Wait for every agent in the batch; an agent
still running means the batch is not done. Show the Step 4 Validation Checklist. Then spawn
the next batch, if the plan has one.

## Step 5: Synthesize Findings

Follow the synthesis instructions in `references/verification-and-iteration.md`. Answer each
question with file paths, line numbers and direct sources.

Draft a `## Candidate Open Questions` section inside the synthesis: every gap you noticed but
did not close, phrased as a question. It is the work list for Step 8. An entry reaches the
document as an Open Question only after Step 8 classifies it UNRESOLVABLE or SKIP.

Write the synthesis to `$SCRATCHPAD/synthesis-iter-<N>.md`, or to
`~/.claude/thoughts/shared/research/.drafts/<slug>-synthesis.md` when it must survive
compaction, before any downstream dispatch. Persona reviewers get the path. The Step 6
evaluator and the Step 8 verification agent use no tools, so they get the full text inline.
Wrap the inlined synthesis and grounding report in `<pasted_content>` tags; keep the
instructions and policy sections outside them.

**Before every Step 6, 7 or 8 spawn**, grep the assembled prompt for unsubstituted input
tokens (`{{...}}`, `$..._PLACEHOLDER$`, bracketed input stubs) and fill them. Unsubstituted
tokens caused five missing-input refusals across two sessions. Never tell an agent to assume
content that is not in its prompt. A reviewer that refuses for missing input is reporting a
real defect in your dispatch.

## Step 6: Research Completeness Review

Read `references/verification-and-iteration.md` for the evaluator prompt and the iteration
rules. Spawn the evaluator (model: sonnet), told not to use tools. Record its tool-use count in
the Step Ledger. Display its verdict verbatim and act on its Decision: on ITERATE, create the
iteration's tasks and return to Step 3 with its gap list.

## Step 7: Research Review Phase

Read `references/review-personas.md`. This step runs at every complexity:

| Complexity | Reviewers |
| ---------- | --------- |
| Simple     | Gap Analyst + Devil's Advocate |
| Medium     | + Source Critic |
| Complex    | + Coherence Reviewer + Scope Guardian |

If Step 2 flagged a domain expert for verification, also spawn the Domain Expert Verifier on
the default model (it reads code).

1. Spawn the reviewers in parallel (model: sonnet) with the plan and the absolute path to the
   synthesis file.
2. Synthesize the delivered feedback in the Review Synthesis Format.
3. Revise the findings to address every Must Address item.
4. Auto-approve at zero Must Address, zero disagreements, and at most two Should Consider.

- **Interactive**: present the review synthesis and iterate with the user.
- **NON_INTERACTIVE**: carry accepted Should Consider items into the Advisory Notes section.

Set the document's `review_phase_status` frontmatter to `completed` only after the required
reviews pass. The orchestrator's review-phase enforcement check reads this field.

## Step 8: Grounding Pass

Read `references/grounding-pass.md`. A Grounding Agent and a separate Verification Agent
iterate until every material uncertainty and every candidate Open Question is resolved or
classified UNRESOLVABLE or SKIP with a qualifying reason. This is the last gate before the
document: anything not worked here reaches the reader unexamined.

1. Spawn the Grounding Agent with the synthesis (as revised in Step 7), Step 6's
   `Needs Verification` flags, the Candidate Open Questions plus any gap a Step 7 reviewer
   asked to document, and from iteration 2 the verifier's gap list.
2. Spawn the Verification Agent (model: haiku), told not to use tools, with the same inputs
   plus the grounding report. Record its tool-use count.
3. On ITERATE, respawn both with the gap list. Only a current PROCEED permits Step 9.

This loop runs the same way in both modes: grounding is action, not interaction.

## Step 9: Synthesis Revision

Apply the grounding results per `## Synthesis Revision Instructions (Step 9)` in
`references/grounding-pass.md`. A revision that changes a requested answer, conclusion,
recommendation or tier goes back to the Step 6 evaluator, and to any Step 7 reviewer whose
Must Address item it touches. Cosmetic edits do not. If you do not re-run a check, say so in
the Step Ledger.

## Pre-Document Gate

A task can read `completed` while the artifact it produced has fallen out of your context
through compaction. Confirm each of these is actually present in your context:

- [ ] Step 5 synthesis (findings with paths and evidence)
- [ ] Step 6 verdict (PROCEED)
- [ ] Step 7 review synthesis, with no blocking items
- [ ] Step 8 grounding results and the Verification Agent's PROCEED
- [ ] Step 9 revised synthesis
- [ ] Every candidate Open Question has a Step 8 classification, and every UNRESOLVABLE or
      SKIP one names a reason from `## What Legitimately Stays Open` in
      `references/grounding-pass.md`

If any is missing, return to that step.

## Steps 10-13: Generate the Research Document

Read `references/document-template.md`.

- **Step 10**: gather the metadata; create the research directory if absent.
- **Step 11**: write `~/.claude/thoughts/shared/research/YYYY-MM-DD-description.md` from the
  template, with a complete Step Ledger.
- **Step 12**: if on main/master or the commit is pushed, replace local file references with
  `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`.
- **Step 13**: list the queries and sources behind any internal search, code search or web research so
  the findings can be reproduced.

## Step 14: Present Findings

Give the answer to each research question in one or two sentences, with the key file
references and the document path.

- **Interactive**: ask whether the user wants follow-ups or clarifications.
- **NON_INTERACTIVE**: the research is complete.

## Step 15: Handle Follow-Up Questions (Interactive Only)

Append to the same document: update `last_updated`, `last_updated_by` and
`last_updated_note`, add a `## Follow-up Research [timestamp]` section, and spawn sub-agents
as needed. Continue until the user confirms the research is complete.

## Notes

- Preserve the exact path structure within `~/.claude/thoughts/`: keep a per-user directory
  such as `<username>/` as `<username>/`, not `shared/`.
- Always research afresh; never rely only on an existing research document.
