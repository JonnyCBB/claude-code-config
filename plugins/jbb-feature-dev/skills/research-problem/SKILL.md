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
findings into a document.

## Core Principle: Document What Exists

Describe what exists, where, how it works, and how components interact. Suggest
improvements, root causes, or critiques **only** when the user explicitly asks.

## NO STEP IS OPTIONAL

Every step below runs on every invocation. There is no complexity tier, mode flag, time
pressure, or token budget that removes one, and **your own judgement that a step's work is
already covered is not grounds for skipping it** — that judgement is exactly what the step
exists to check.

Why this is stated so bluntly: the steps most often dropped are the three that grade the
work (the completeness evaluation, the persona review, the grounding pass), and when they
are run late their findings routinely change the document's conclusions. A step whose later
execution changes the answer was never optional. You are also the worst-placed judge of
whether your own output needs checking, which is why every one of those three steps is
performed by a **separate agent** rather than by you.

Three consequences, all mandatory:

1. **A skipped step is never recorded as `completed`.** If a step genuinely cannot run, the
   run stops and you say so. Recording a skip and a completion identically destroys the only
   signal anyone has.
2. **Every step writes a row in the Step Ledger** of the finished document (see
   `references/document-template.md`). The ledger is the audit trail: without it, a skipped
   step is invisible until someone re-runs the step and the conclusions move.
3. **Self-substitution is never permitted** for the Step 6 evaluator, the Step 7 reviewers,
   or the Step 8 verification agent. If an agent will not deliver, follow Agent Delivery
   Resilience below — which ends in a recorded failure, not in you doing its job.

## Agent Delivery Resilience

Claude Code has a known family of bugs where subagents go idle without delivering results
(GitHub Issues #61547, #54323, #29163, #47930). The agent may finish while the harness
silently drops its output. This hits both tool-equipped agents (permission gate stalls) and
judges that use no tools (SubagentStop output drop).

**The recovery ladder** — apply whenever an agent sends an `idle_notification` with
`idleReason: "available"` but no content message. This is the canonical statement; later
steps point here rather than restating it.

1. **Wait briefly.** The agent may deliver just after the idle signal.
2. **Prompt via `SendMessage` using the agent's bare name.** The composite
   `name@session-id` form is rejected outright (`to must be a bare teammate name -- there
   is only one team per session`). Names keep working after an agent completes; fall back to
   the raw `agentId` from the spawn result only when the agent is unnamed, or when a newer
   agent has taken its name.
3. **Respawn once** with the same prompt.
4. **If it still has not delivered**, record in the Step Ledger: the agent's name, that two
   attempts were made, and what is consequently missing. Then gather what you can directly
   (read the files, run the searches). **Never** self-evaluate, self-review or self-verify in
   its place.

Record every spawned agent's name (and its id as a fallback) so step 2 is possible at all.

**Prevention** (reduces, does not eliminate): prefer `subagent_type` over bare `model`
overrides; split batches larger than 5 into sequential sub-batches of 3-5, since parallel
Agent calls can cascade-fail (Issue #57037); agents using MCP tools deliver more reliably
than agents doing only local file reads.

## Initial Setup

If a query is supplied, start Step 1. Ask and wait only when no query is supplied.

## Mode Detection

Parse `$ARGUMENTS`. `--non-interactive` sets NON_INTERACTIVE mode; the remaining arguments
are the query. A file path in `$ARGUMENTS` is read as the query input.

NON_INTERACTIVE removes **only** the three places a human is asked something: the Step 2
confirmation, the Step 14 follow-up prompt, and Step 15. It grants no other authority. In
particular it does not reduce the review phase, and token cost is never a skip justification.

## Step 1: Read Mentioned Files First

The coordinator reads mentioned sources fully, continuing any truncated output. Use
verified callable document reads for Google Docs. Parent isolation applies only when the
invoking workflow requires it, not from messaging ancestry. In an isolated workflow,
preflight a supported full-input delivery route before Step 3; do not ingest protected
sources into the parent or invent file-input parameters. If no compliant route works, hold
before research dispatch.

## Step 2: Analyze and Decompose

Read `references/plan-templates.md` for every template named here.

Produce: **Research Questions** (each with its assigned agent type) · **Assumptions**
(explicit, implicit, constraints) · **Success Criteria** · **Scope** (in and explicitly out)
· **Research Context** (known starting points, prior knowledge, previous research) ·
**Research Execution Plan** (dependency table, batches, context to pass between them;
default to parallel when unsure) · **Domain Expert Check** (mandatory cross-reference of
every question against the Domain Expert Table in `references/agent-guide.md`, deciding
researcher and/or verifier use) · **Agent Type Verification** · **Complexity
Classification**.

Complexity sets **how many** reviewers run in Step 7, never **whether** Step 7 runs.

- **Interactive**: output the full plan in your text response — every section, verbatim, not
  summarized, not collapsed, not written to a file. Then call **`AskUserQuestion`** offering
  "Proceed with this plan" / "Request changes" / "Cancel", and **wait**. On "Request changes",
  revise in the UI and ask again.
- **NON_INTERACTIVE**: save the complete plan to
  `~/.claude/thoughts/shared/research_plans/YYYY-MM-DD-description-plan.md` with frontmatter
  `status: approved`, then proceed.

## Step 3: Spawn Sub-Agent Tasks

Read `references/agent-guide.md` for selection rules, the Domain Expert Table, the
pre-spawn verification format, and batch rules.

**At least one research agent is spawned on every run.** Research means sending someone to
look for what you did not think to read. If Step 2 left every question classified Direct,
that classification is the defect — return to it. Having read the files in Step 1 is not a
substitute for this step, and "the questions are already answered" is the self-assessment
Steps 6-8 exist to test.

- Before research dispatch, preflight Claude-native full-input delivery. If the invoking
  workflow requires parent isolation, also verify its input and output-exposure rules. Hold
  if unsupported; never invent runtime parameters.
- Output the **Pre-Spawn Verification Table** before any spawn, copying the planned agent
  type from **Research Questions** (the source of truth), not from a downstream summary.
- Run batches in sequence, agents within a batch in parallel; wait for each batch, then pass
  its discovered findings, terminology and file paths into the next as "Prior Findings".
- You may combine closely related questions into one agent — say which and why.
- Tell every agent to document by default and permit evidence-backed evaluation only when
  explicitly requested within scope.
- Apply **Agent Delivery Resilience** to every agent spawned here.

## Post-Research Step Tracking (Steps 4-13)

Immediately after the Step 3 spawns, create one task per remaining step with `TaskCreate`:
Step 4 validate · Step 5 synthesize · Step 6 completeness review · Step 7 review phase ·
Step 8 grounding pass · Step 9 synthesis revision · Pre-Document Gate · Steps 10-13 write
the document.

Mark each `in_progress` when you start it and `completed` when it is done. **`completed`
means the step's work happened.** It is never used to clear a step you did not perform — see
the strictness rule above, consequence 1.

Before starting any step, call `TaskList`. If the previous step is still `pending` or
`in_progress`, stop and finish it. A pending task sitting behind a completed one is the
signal that you are about to skip something.

## Step 4: Validate Agent Completion

Read `references/verification-and-iteration.md`.

Wait for every agent in the batch. Show the Step 4 Validation Checklist matching each
Step 2 question-to-role assignment to delivered reports and evidence. Equal counts do not
prove coverage. Apply bounded delivery recovery; missing mandatory delivery keeps the
checkpoint incomplete. Extract context and spawn the next batch when coverage permits.

## Step 5: Synthesize Findings

Run pre-synthesis verification against delivered assignment evidence, not spawn counts.
Compile results using direct sources appropriate to each claim. Connect findings across
components with file paths and line numbers. Answer the user's questions with concrete
evidence.

**Draft a `## Candidate Open Questions` section inside the synthesis.** Every gap you
noticed but did not close goes here as a question. This is a work list for Step 8, not a
disclosure: an entry becomes a real Open Question only after Step 8 classifies it
UNRESOLVABLE or SKIP with a qualifying reason. It has to exist *before* the last
verification gate or it never gets examined.

**Persist the synthesis to a file before any downstream dispatch** — `$SCRATCHPAD/synthesis-iter-<N>.md`,
or `~/.claude/thoughts/shared/research/.drafts/<slug>-synthesis.md` when it must survive
compaction. Record the absolute path. Persona reviewers may read it; judges (Step 6 evaluator,
Step 8 verification agent) must receive the complete contents through verified inline prompt delivery. Paths alone are
not delivery. Unsubstituted inline tokens previously caused five missing-input refusals
across two sessions, so inspect the actual assembled input rather than trusting interpolation.

Keep stable IDs for requested questions, success criteria, scoped claims (including
unmarked claims), evaluator flags, reviewer gaps, candidates, and follow-ons. Preserve IDs
through revisions; link new items to their originating IDs. Maintain cumulative evidence,
errors, classifications, superseding corrections, and verification outcomes.

The parent owns one cumulative run-budget ledger: completeness rounds, persona-review
rounds, grounding pairs, per-invocation item attempts, and any user budget. Use the canonical
bounds in the reference files. Renewed checks consume remaining counters; handoffs,
corrections, and delivery recovery never reset them. An exhausted required counter stops
execution with an incomplete draft checkpoint, not a completed document.

**Pre-dispatch check, for every agent spawned in Steps 6, 7 and 8:** grep the assembled
prompt for unsubstituted input tokens — `{{...}}`, `$..._PLACEHOLDER$`, bracketed input
stubs. Replace input stubs before spawning; retain intentional output-format fields as format
instructions, not missing inputs. Never tell an agent to assume it has content that is
not literally in its prompt. A reviewer that refuses for missing input is behaving
correctly — it is reporting a real defect in your dispatch.

## Step 6: Research Completeness Review

Read `references/verification-and-iteration.md` for the evaluator prompt template and
handoff protocol.

Spawn a dedicated evaluator sub-agent (model: sonnet). Pass it the Step 2 research
plan, the **contents** of the Step 5 synthesis file, the cumulative ID/budget ledgers, the
canonical materiality policy, and the prior evaluation from iteration 2 onward. Instruct it
not to use any tool and to judge only the supplied input. It need not have an empty tool
roster; no agent type does. Record its tool-use count in the Step Ledger and note any use
beyond the result hand-back. If complete inline delivery cannot be established, hold the gate.

Display the evaluator's verdict verbatim and act on its Decision field. On ITERATE, create
the new iteration's tasks via `TaskCreate` and return to Step 3 with its gap list. Iterate
per the Maximum Iterations Rule in `references/verification-and-iteration.md`. Remaining
material evidence gaps require an incomplete checkpoint with IDs, attempts, evidence, and
next actions. Bounds stop execution, not pass gates.

## Step 7: Research Review Phase

Read `references/review-personas.md` for the personas, the prompt template, the synthesis
format, and the auto-approve threshold.

**This step runs at every complexity.** Complexity chooses the roster:

| Complexity | Reviewers |
| ---------- | --------- |
| Simple     | Gap Analyst + Devil's Advocate |
| Medium     | + Source Critic |
| Complex    | + Coherence Reviewer + Scope Guardian |

**Additionally**, if Step 2's Domain Expert Check flagged an expert for verification, spawn
the **Domain Expert Verifier** alongside them, using the matching expert type from the
Domain Expert Table. It runs in parallel but on the default model, not sonnet, because
verification means reading and reasoning about code.

1. Spawn the selected reviewers in parallel (sonnet for the generic personas). Pass each the
   Step 2 plan and the **absolute path** to the Step 5 synthesis file, instructing it to Read
   that path. Check the interpolation first. Record each reviewer's name for recovery.
2. Apply **Agent Delivery Resilience** per reviewer. Missing mandatory delivery blocks
   approval after bounded recovery; self-review cannot replace it. Save an incomplete
   checkpoint with the missing assignments and evidence.
3. Synthesize all delivered feedback using the Review Synthesis Format.
4. Revise the findings to address every "Must Address" item.
5. Return substantive fixes to affected independent reviewers and completeness evaluation
   when changed reasoning requires it, within remaining cumulative round counters. A local
   correction alone does not establish independent acceptance.
6. Auto-approve at zero "Must Address", zero disagreements, at most two "Should Consider".

- **Interactive**: present the review synthesis to the user and iterate collaboratively.
- **NON_INTERACTIVE**: remove human prompts, not checks. Return substantive "Must Address"
  fixes to affected independent reviewers within the remaining round budget. Carry accepted
  "Should Consider" items into the document's Advisory Notes section.

Set the document's `review_phase_status` frontmatter field to `completed`. This is the
authoritative signal the orchestrator's review-phase enforcement check reads.

## Step 8: Grounding Pass

Read `references/grounding-pass.md` for the heuristic table, classification rules, both
agent prompt templates, and the bounding rules.

A **Grounding Agent** and a separate **Verification Agent** iterate until every material,
objectively-verifiable uncertainty **and every candidate Open Question** is resolved or
correctly classified UNRESOLVABLE/SKIP with a qualifying reason, or the Grounding Iteration
Bound is reached.

This is the last gate before the document is written. Anything not worked here reaches the
reader unexamined — which is how answerable questions have historically ended up in finished
documents' Open Questions sections.

1. Spawn the **Grounding Agent** with four labeled inputs: the synthesized findings (Step 5,
   as revised by Step 7); Step 6's per-question `Needs Verification` assessment; the
   `## Candidate Open Questions` list plus any gap the Step 7 reviewers demanded be
   documented; and, from iteration 2 onward, the prior Verification Agent's gap list.
   Include the cumulative ID/evidence and run-budget ledgers and expand all canonical policy
   blocks required by `references/grounding-pass.md` in both agents' delivered prompts.
2. Spawn the **Verification Agent** (model: haiku) with the same findings and flags
   plus the complete cumulative grounding evidence. Instruct it not to use any tool; verify
   full input delivery and record its tool-use count as for Step 6. It judges supplied evidence, not empirical reproduction.
3. On ITERATE within the remaining bound, respawn both with the gap list. Only a current
   independent PROCEED permits Step 9. At the bound, save an incomplete draft checkpoint.
4. Apply **Agent Delivery Resilience** to each agent independently. Missing grounding or
   verification delivery blocks Step 8 completion and Step 9. Earlier reports and self-checks
   cannot replace a current independent verdict; record missing IDs, attempts, and next actions.
5. Classify resolution failures and follow the canonical Per-Attempt Bounding Rules in
   `references/grounding-pass.md`. Use supported timeouts; never repeat unchanged failures,
   retry mutations, or retry uncertain outcomes.

This loop runs identically in both modes — empirical resolution is action, not interaction.

## Step 9: Synthesis Revision

Read `references/grounding-pass.md` (`## Synthesis Revision Instructions (Step 9)`).

1. Read the cumulative grounding ledger and current independent verdict, not only the final
   iteration's gap report.
2. For each resolved uncertainty, replace the uncertain claim with the grounded finding, then
   check whether that changes any recommendation, conclusion or tier classification — and
   update those too.
3. For each failed resolution attempt or blocked item whose supported UNRESOLVABLE/SKIP
   classification permits completion under the current independent PROCEED verdict,
   annotate: "Attempted: [action]. Result: [error]. Remains unresolved." or
   "Skipped: [verified qualifying reason]". Bound exhaustion never qualifies;
   material gaps retain an incomplete checkpoint.
4. Update dependent requested answers and recommendations. Ground material follow-ons
   answerable through authorized, available evidence within remaining budget; several safe
   reads may form one attempt. Do not silently expand scope.
5. Substantively changed requested answers, scoped factual descriptions, conclusions,
   recommendations, or tiers return to completeness evaluation and affected persona review
   of changed reasoning/evidence. Do not re-review cosmetic edits or unchanged observations.
   Keep artifacts incomplete until required checks pass; no counter resets.

## Pre-Document Gate

The `TaskList` rule already stops you if Step 9 is not `completed`. This gate adds the check
that rule cannot make: a task can read `completed` while the artifact it produced has fallen
out of your context, dropped by compaction on a long run.

Confirm each of these is **actually present in your context**, not merely remembered as
having happened:

- [ ] Step 5 synthesis text (findings with paths and evidence)
- [ ] Step 6 evaluator verdict
- [ ] Step 7 review synthesis
- [ ] Step 8 grounding results and the Verification Agent's decision
- [ ] Step 9 revised synthesis
- [ ] Every candidate Open Question carries a Step 8 classification, and every
      UNRESOLVABLE/SKIP one names a qualifying reason from
      `references/grounding-pass.md` `## What Legitimately Stays Open`

Unclassified questions block completion. Named instruments require attempts or verified
access, safety, scope, or budget constraints. Inaccessibility can justify blocked
classification; budget-limited material evidence still requires an incomplete checkpoint.
Return unfinished work to Step 8 rather than publishing it as complete.

If any artifact is missing, return to that step. Do not generate the document without it.

## Steps 10-13: Generate the Research Document

Read `references/document-template.md` for the metadata script, naming, the document
template including the **Step Ledger**, permalink rules, and the MCP call format.

- **Step 10**: run the metadata script; create the research directory if absent.
- **Step 11**: write `~/.claude/thoughts/shared/research/YYYY-MM-DD-description.md` from the
  template, populated with real metadata and findings — including a complete Step Ledger.
- **Step 12**: if on main/master or the commit is pushed, replace local file references with
  `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`.
- **Step 13**: document the queries, sources and descriptions behind any internal search, code search or
  web research so findings can be reproduced.

## Step 14: Present Findings

Present a concise summary with key file references.

- **Interactive**: ask whether the user wants follow-ups or clarifications.
- **NON_INTERACTIVE**: the research is complete.

## Step 15: Handle Follow-Up Questions (Interactive Only)

Skipped entirely in NON_INTERACTIVE mode. Otherwise: append to the same document, update
`last_updated`, `last_updated_by` and `last_updated_note`, add a
`## Follow-up Research [timestamp]` section, spawn new sub-agents as needed, and continue
until the user confirms the research is complete.

## Important Notes

- **Path handling**: preserve the exact structure within `~/.claude/thoughts/` — keep
  a per-user directory such as `<username>/` as `<username>/`, not `shared/`.
- **Fresh research**: always research afresh; never rely solely on an existing document.
- **Frontmatter**: always present, snake_case field names, updated on follow-ups.

## Reference Files

| Reference                                  | Consumed in                                                              |
| ------------------------------------------ | ------------------------------------------------------------------------ |
| `references/plan-templates.md`             | Step 2 (plan formatting templates)                                       |
| `references/agent-guide.md`                | Steps 2-3 (agent selection, pre-spawn verification, domain expert table) |
| `references/verification-and-iteration.md` | Steps 4-6 (validation, completeness review, iteration bound)             |
| `references/review-personas.md`            | Step 7 (personas, review prompt template, auto-approve)                  |
| `references/grounding-pass.md`             | Steps 8-9 (heuristics, both agent prompts, synthesis revision)           |
| `references/document-template.md`          | Steps 10-13 (metadata, document template, Step Ledger, permalinks)       |
