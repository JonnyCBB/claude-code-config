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

You are tasked with conducting comprehensive research across the codebase and beyond to
answer user questions by spawning parallel sub-agents and synthesizing their findings.

## Core Principle: Document and Explain What Exists

Your role is to document and explain the codebase as it currently exists:

- Describe what exists, where it exists, how it works, and how components interact
- Focus on creating a technical map/documentation of the existing system
- Suggest improvements, root cause analysis, or enhancements only when the user explicitly requests them
- Keep recommendations and critiques out of scope unless asked

## Agent Delivery Resilience

Claude Code has a known family of bugs where subagents go idle without delivering their
results (GitHub Issues #61547, #54323, #29163, #47930). Agents may complete their work
but the output is silently dropped by the harness. This affects both tool-equipped agents
(permission gate stalls) and tool-less evaluator agents (SubagentStop output drop).

**Standard recovery procedure** — apply whenever an agent sends an `idle_notification`
with `idleReason: "available"` but no content message:

1. **Wait briefly** — the agent may deliver shortly after the idle signal.
2. **Prompt via SendMessage** using the agent's **bare name**. The composite
   `name@session-id` form is rejected outright (`to must be a bare teammate name --
there is only one team per session`). Names keep working after an agent completes;
   fall back to the raw `agentId` from the spawn result only when the agent is unnamed
   or a newer agent has taken its name.
3. **If still no delivery after 1 prompt**: gather the data directly (read the files,
   run the searches yourself) and document the agent non-delivery in the research
   methodology section. Do NOT self-evaluate or self-review as a substitute — respawn
   the agent or document the gap.

**Prevention heuristics** (reduce but do not eliminate non-delivery):

- Prefer agents with `subagent_type` over bare `model` overrides — `subagent_type`
  agents have more reliable tool permission handling.
- When spawning more than 5 agents, consider sequential batches rather than a single
  parallel batch — parallel Agent calls can cascade-fail (GitHub Issue #57037).
- Agents with direct tool access (Grep, Read, gh) tend to deliver more reliably than agents
  doing only local file reads.

## Initial Setup

When this command is invoked, respond with:

```
I'm ready to research the problem. Please provide your research question or area of
interest, and I'll analyze it thoroughly by exploring relevant components and connections.
```

Then wait for the user's research query.

## Mode Detection

Parse `$ARGUMENTS` for flags and input:

- If `$ARGUMENTS` contains `--non-interactive`: Set NON_INTERACTIVE mode
  - Skip all user confirmation steps (Step 2 confirmation, Step 14 follow-up, Step 15 loop)
  - Auto-accept the research plan
  - Proceed directly through all steps without waiting for user input
  - The remaining arguments (after removing `--non-interactive`) are the research query
- If `$ARGUMENTS` does not contain `--non-interactive`: Behave as interactive mode (default)
- If `$ARGUMENTS` contains a file path (e.g., `~/.claude/thoughts/...`): Read that file as the research query input

## Steps to Follow After Receiving the Research Query

### Step 1: Read Mentioned Files First

- If the user mentions specific files (tickets, docs, JSON, etc.), read them FULLY first
- Google docs should also be read into the main context using the google-drive MCP tool
- **IMPORTANT**: Use the Read tool WITHOUT limit/offset parameters to read entire files
  UNLESS the user has given explicit instructions not to read a file in its entirety
- Read these files yourself in the main context before spawning any sub-tasks
- This ensures you have full context before decomposing the research

### Step 2: Analyze and Decompose the Research Question

Read `references/plan-templates.md` for all formatting templates, the research plan file
spec, and the example decomposition.

Produce the following sections (using the templates from the reference file):

- **Research Questions** -- list all specific questions with assigned agent types
- **Assumptions** -- explicit, implicit, and constraints
- **Success Criteria** -- checklist of what constitutes a complete answer
- **Scope** -- in-scope and explicitly out-of-scope
- **Research Context** -- known starting points, prior knowledge, previous research
- **Research Execution Plan** -- dependency analysis table, execution batches, context
  to pass between batches. Default to parallelism when uncertain.
- **Domain Expert Check** -- MANDATORY cross-reference of every research question against
  the Domain Expert Table in `references/agent-guide.md`. Determines whether to use a
  domain expert as primary researcher (Step 3) and/or as verifier (Step 7). Use the
  template from `references/plan-templates.md`.
- **Agent Type Verification** -- accountability list of all agent types to spawn
- **Complexity Classification** -- classify research as Simple/Medium/Complex to determine
  review scope in Step 7. Use the template from `references/plan-templates.md`.

- **Interactive mode** (MUST follow exactly):
  1. Output the **full research plan** directly in your text response to the user --
     every section listed above (Research Questions, Assumptions, Success Criteria,
     Scope, Research Context, Research Execution Plan, Domain Expert Check, Agent Type
     Verification, Complexity Classification), rendered verbatim in the Claude Code UI.
  2. Do **NOT** summarize, abbreviate, or collapse sections. Do **NOT** write the plan
     to a file in interactive mode -- the user reviews it in the UI, not on disk.
  3. After the plan text, call the **`AskUserQuestion`** tool to ask whether the user
     wants to proceed as-is or request changes. Offer clear options such as
     "Proceed with this plan", "Request changes", or "Cancel".
  4. **Wait for the user's response via AskUserQuestion before proceeding to Step 3.**
     If the user requests changes, revise the plan (still fully in the UI) and ask
     again via AskUserQuestion.
- **NON_INTERACTIVE mode**:
  1. Save the complete plan to
     `~/.claude/thoughts/shared/research_plans/YYYY-MM-DD-description-plan.md` with YAML
     frontmatter (status: `approved`).
  2. Skip confirmation; proceed directly to Step 3.

### Step 3: Spawn Sub-Agent Tasks

Read `references/agent-guide.md` for agent selection rules, domain expert table,
pre-spawn verification format, and batch execution rules.

Key points:

- Before spawning, output a **Pre-Spawn Verification Table** cross-checking planned
  agent types from Research Questions against what you are about to spawn
- Execute batches in sequence; spawn agents within each batch in parallel
- Wait for each batch to complete before spawning the next
- Pass discovered context (key findings, terminology, file paths) from earlier batches
  to later batch prompts as "Prior Findings"
- You MAY combine closely related questions into a single agent if efficient -- tell the
  user which questions you combined and why
- Remind all agents they are documentarians, not evaluators
- **Agent delivery resilience** (see "Agent Delivery Resilience" section above):
  - Prefer `subagent_type` agents over bare `model` overrides for reliable delivery
  - When using SendMessage to recover a stalled agent, address it by its **bare name**;
    the `name@session-id` form is rejected
  - When spawning more than 5 agents in a single batch, consider splitting into
    sequential sub-batches of 3-5 to reduce cascade-failure risk
  - Record each spawned agent's name (and its id as a fallback) so recovery via
    SendMessage is possible

### Post-Research Step Tracking (Steps 4-13)

After all research agents complete, create tasks for each post-research step using the
`TaskCreate` tool. These tasks provide external state visible in the Claude Code UI and
ensure the model is reminded of remaining work.

**Create all tasks immediately** after Step 3 agents are spawned:

1. `TaskCreate(subject: "Step 4: Validate agent completion", activeForm: "Validating agents")`
2. `TaskCreate(subject: "Step 5: Synthesize findings", activeForm: "Synthesizing findings")`
3. `TaskCreate(subject: "Step 6: Completeness review", activeForm: "Evaluating completeness")`
4. `TaskCreate(subject: "Step 7: Review phase", activeForm: "Running review")`
5. `TaskCreate(subject: "Step 8: Grounding pass", activeForm: "Grounding claims")`
6. `TaskCreate(subject: "Step 9: Synthesis revision", activeForm: "Revising synthesis")`
7. `TaskCreate(subject: "Pre-Document Gate", activeForm: "Verifying artifacts")`
8. `TaskCreate(subject: "Steps 10-13: Write research document", activeForm: "Writing document")`

**At each step**: Call `TaskUpdate(taskId, status: "in_progress")` when starting and
`TaskUpdate(taskId, status: "completed")` when done. If skipping a step (e.g., Step 7
for Simple complexity), update with `completed` and note the reason in the description.

**Before starting any step**, call `TaskList` to verify the previous step's task shows
`completed`. If the previous step is still `pending` or `in_progress`, STOP and complete
it first. A pending task after the previous task is completed is a signal that you are
about to skip it — STOP and execute it instead.

### Steps 4-6: Validate, Synthesize, and Iterate

Read `references/verification-and-iteration.md` for validation checklists, pre-synthesis
verification, completeness review format, iteration rules, and state machine diagram.

**Step 4 -- Wait and Validate Agent Completion:**

- Wait for all agents in the current batch to return results
- Show a Step 4 Validation Checklist cross-checking agent commitments from Step 2
- Re-spawn any failed agents with adjusted prompts
- Extract context for next batch; spawn next batch if the execution plan requires it
- After ALL research agents complete, the synthesis and validation tasks (created in Post-Research Step Tracking) are ready to begin

**Step 5 -- Synthesize Findings:**

- Run pre-synthesis agent verification (committed vs. actually spawned)
- Compile all sub-agent results; prioritize live codebase over historical context
- Connect findings across components; include file paths and line numbers
- Answer the user's questions with concrete evidence
- **Draft a `## Candidate Open Questions` section inside the synthesis.** Every gap you
  noticed but did not close goes here, phrased as a question. This is a work list for Step 8,
  not a disclosure — an entry becomes a real Open Question in the final document only after
  Step 8 classifies it UNRESOLVABLE or SKIP with a qualifying reason. Drafting it here rather
  than at document-writing time is the whole point: it must exist before the last verification
  gate, or it never gets examined. See `references/grounding-pass.md`
  `## What Legitimately Stays Open`.
- **Persist the synthesis to a file before any downstream dispatch.** Write it to
  `$SCRATCHPAD/synthesis-iter-<N>.md`, or to
  `~/.claude/thoughts/shared/research/.drafts/<slug>-synthesis.md` when it needs to
  survive compaction. Record the absolute path — Steps 6, 7 and 8 pass that path rather
  than the text.

**Why the synthesis becomes a file:** a path is verifiable; an interpolation is not. When
the synthesis is passed inline it can arrive as an unsubstituted token, and the receiving
agent's only honest move is to refuse. That happened five times across two sessions, each
costing a full review pass — and those refusals were the only thing preventing a
fabricated PROCEED verdict.

**Pre-dispatch check (applies to every agent spawned in Steps 6, 7 and 8):** before
spawning, grep the assembled prompt for unsubstituted template tokens — `{{...}}`,
`$..._PLACEHOLDER$`, or bracketed section stubs. If any remain, do not spawn; fix the
prompt first. Never instruct an agent to assume it has content that is not literally in
its prompt, and treat a reviewer that refuses for missing input as behaving correctly —
it is reporting a real defect in the dispatch, not failing its task.

**Step 6 -- Research Completeness Review (Iterative Loop):**

- Spawn a dedicated evaluator sub-agent (model: sonnet, no tools) to judge completeness
- Pass it: the research plan (Step 2), the contents of the Step 5 synthesis file, and prior
  evaluation (if iteration 2+). This evaluator has no tools, so it cannot Read the path —
  the contents must be inlined, which makes Step 5's pre-dispatch check mandatory here:
  verify the interpolation actually happened before spawning
- The evaluator is a separate agent because models reliably skew positive when grading
  their own work — a standalone evaluator with a mildly skeptical disposition catches gaps
  that self-evaluation misses
- **Evaluator delivery resilience**: If the evaluator goes idle without delivering
  (sends `idle_notification` but no content message), prompt it via SendMessage using
  its **bare name**. If it still does not deliver after 1 prompt, respawn once
  with the same prompt. If the respawn also fails, note the evaluator non-delivery in
  the document and proceed to Step 7 where independent reviewers will catch issues. The
  orchestrator MUST NEVER perform self-evaluation as a substitute for Step 6 —
  self-evaluation defeats the entire purpose of independent review.
- Display the evaluator's verdict verbatim; act on the Decision field (PROCEED or ITERATE)
- If ITERATE, create new tasks for the iteration (new agent tasks, new synthesis task, new validation task) via `TaskCreate`, then return to Step 3 with the evaluator's gap list
- Iterate per the materiality-filtered round bound in `references/verification-and-iteration.md`'s
  Maximum Iterations Rule; document remaining material gaps as Open Questions
- See `references/verification-and-iteration.md` for evaluator prompt template and
  orchestrator handoff protocol

### Step 7: Research Review Phase

Read `references/review-personas.md` for persona definitions, complexity-based selection
criteria, review prompt template, synthesis format, iteration mechanism, and auto-approve
threshold.

- **Simple complexity**: Skip this step. Proceed directly to Step 8 (grounding pass).
- **Medium complexity**: Spawn Gap Analyst + Devil's Advocate + Source Critic (3 reviewers).
- **Complex**: Spawn all 5 generic reviewers (Gap Analyst, Devil's Advocate, Source Critic,
  Coherence Reviewer, Scope Guardian).

For the rules on when the review phase may be skipped, see `references/review-personas.md` (`## Skipping the Review Phase`).

**Additionally**, if the Domain Expert Check in Step 2 flagged a domain expert for
verification, spawn the **Domain Expert Verifier** alongside the generic reviewers. The
domain expert verifier uses the matching expert agent type from the Domain Expert Table
(e.g., `ml-pipeline-reviewer` for ML training research). It runs in parallel with the
generic reviewers but uses the default model (not sonnet) since verification requires
reading and reasoning about code. See the Domain Expert Verifier persona in
`references/review-personas.md` for the prompt template.

**Process:**

1. Spawn selected reviewer agents in parallel (model: sonnet for generic reviewers,
   default model for domain expert verifier). Pass each reviewer: the research plan
   (questions, success criteria, assumptions from Step 2) and the **absolute path** to the
   Step 5 synthesis file, instructing it to Read that path (inline the contents only for
   tool-less reviewers, and verify the interpolation before spawning — see Step 5's
   pre-dispatch check). Record each reviewer's **name** from the spawn result for recovery.
2. **Track reviewer delivery**: As reviewers complete, note which delivered findings
   and which went idle without content. If a reviewer goes idle (sends
   `idle_notification` but no content message), prompt it via SendMessage using its
   bare name. If it still does not deliver after 1 prompt, respawn once. Do NOT
   self-evaluate any dimension — respawn or document the gap. Note unresponsive
   reviewers in the review methodology section.
3. Collect and synthesize feedback from all delivered reviews using the Review
   Synthesis Format.
4. Address "Must Address" items by revising the synthesized findings.
5. Re-run review if needed, per `references/review-personas.md`'s updated Iteration
   Mechanism (which itself points to `references/verification-and-iteration.md`'s round bound).
6. Auto-approve when: zero "Must Address" + zero disagreements + at most 2 "Should Consider."
7. Proceed to Step 8 (grounding pass).

- **Interactive mode**: Present review synthesis to user; iterate collaboratively.
- **NON_INTERACTIVE mode**: spawn the multi-persona reviewer sub-agents per the selection
  rules above (mandatory — self-review is NEVER a substitute for sub-agent spawning, even
  in non-interactive mode). Run a single review iteration only. Auto-resolve "Must Address"
  items; document "Should Consider" items as advisory notes. Complexity-based skips at
  `references/review-personas.md ## Skipping the Review Phase` remain valid; the
  non-interactive flag does NOT add new skip authority. Token cost is NOT a valid skip
  justification.

**Review-phase status tracking**: The document template includes a `review_phase_status`
frontmatter field. Set it to `completed` when the review phase ran (any complexity), or
`skipped_simple_complexity` when Step 7 was legitimately skipped due to Simple complexity
classification. This field is the authoritative signal used by the orchestrator's
review-phase enforcement check — heading-based evidence is a fallback.

### Step 8: Grounding Pass (Iterative, Verified)

Read `references/grounding-pass.md` for the heuristic table, classification rules, both
agent prompt templates, and the bounding rules.

After review (or review skip for Simple complexity), a **Grounding Agent** and a separate
**Verification Agent** iterate together until every material, objectively-verifiable
uncertainty **and every candidate Open Question** is resolved (or correctly classified
UNRESOLVABLE/SKIP), or a round bound is reached. This mirrors Step 6's design: models skew
positive grading their own work, so a standalone Verification Agent checks the Grounding
Agent's report rather than the Grounding Agent's own self-check being the only gate.

This is the last gate before the document is written. Anything not worked here reaches the
reader unexamined — which is how answerable questions have historically ended up in finished
documents' Open Questions sections.

1. Spawn the **Grounding Agent** with four labeled inputs: the synthesized findings (from
   Step 5, revised after Step 7 review if applicable); Step 6's per-question `Needs
Verification` assessment; the **`## Candidate Open Questions` list** from the Step 5
   synthesis plus any gap the Step 7 reviewers demanded be documented; and — from the second
   iteration onward — the prior Verification Agent's gap list. It uses the detection
   heuristics to identify resolvable uncertainties, classifies every uncertainty and every
   candidate question RESOLVABLE / UNRESOLVABLE / SKIP, resolves the RESOLVABLE ones, and
   reports results with a self-check table.
2. Spawn the **Verification Agent** (model: haiku, no tools) with the same
   findings/flags plus the Grounding Agent's report. It checks for unactioned
   resolutions, coverage gaps, and miscategorization against the Materiality Filter, then
   returns an evidence-worded PROCEED/ITERATE decision.
3. **Loop**: If ITERATE and the Grounding Iteration Bound hasn't been reached, respawn
   the Grounding Agent with the Verification Agent's gap list, then respawn the
   Verification Agent again. If PROCEED, or the bound is reached, proceed to Step 9.
4. **Never substitute self-verification** for the Verification Agent — see
   `references/grounding-pass.md`'s `## Grounding Loop: Orchestrator Handoff Protocol`
   for the full procedure, delivery-resilience handling, and the `## Grounding Iteration
Bound` (distinct from the Grounding Agent's own internal Per-Attempt round bound — do
   not restate either number here, so this mention and the canonical definitions cannot
   drift independently).
5. On any resolution error (MCP failure, command failure, 404, timeout): skip and
   document the attempt and error. Never retry a failed attempt.

The grounding loop runs identically in both interactive and non-interactive modes —
empirical resolution and verification are action, not interaction.

### Step 9: Synthesis Revision

After the grounding loop reaches PROCEED (or exhausts the Grounding Iteration Bound),
review the final iteration's grounding results and revise the synthesized findings.

1. Read all grounding results from the final grounding iteration's report
2. For each successfully resolved uncertainty:
   - Replace the uncertain claim with the grounded finding
   - Check if the change affects recommendations, conclusions, or tier classifications
   - If yes, update those dependent statements
3. For each failed resolution attempt, or gap still open when the Grounding Iteration
   Bound was reached:
   - Replace the uncertainty marker with an annotation: "Attempted: [action].
     Result: [error]. Remains unresolved." or "Skipped: [reason] — Grounding Iteration
     Bound reached."
4. This is a lightweight revision pass — only update sections that reference grounded
   findings. Do NOT re-open Step 2's research questions or spawn new research agents. DO
   route a follow-on question back into the grounding loop when applying a result creates
   one that is material and one action away (see `references/grounding-pass.md`
   `### How to Revise`, item 4).
5. **Bounding**: Single revision pass, no fixed time bound — the only cutoff is a stall,
   handled via this skill's standard idle/recovery ladder (see
   `references/grounding-pass.md` `### Bounding`). No re-review by personas — grounding
   results, confirmed by the Verification Agent, are empirical facts, not prose claims.
6. After revision, proceed to Step 10 (metadata gathering).

### Pre-Document Gate

The general rule in Post-Research Step Tracking already stops you here if the Step 9 task
isn't `completed`. This gate adds the one check that rule can't cover: a task can show
`completed` while the artifact it produced is no longer in your context (e.g., dropped by
compaction on a long research run). Before writing the document:

1. **Verify these artifacts are actually present in your context** (not just recalled as
   having happened):
   - [ ] Synthesis text from Step 5 (compiled findings with file paths and evidence)
   - [ ] Evaluator verdict from Step 6 (PROCEED, or ITERATE with max iterations reached)
   - [ ] Review results from Step 7 (review synthesis, or documented skip for Simple)
   - [ ] Grounding agent results from Step 8 (resolution attempts and outcomes)
   - [ ] Revised synthesis from Step 9 (with grounding corrections applied)
   - [ ] Every candidate Open Question carries a Step 8 classification, and every
         UNRESOLVABLE/SKIP one names a qualifying reason from `## What Legitimately Stays
Open`. An unclassified question, or one whose own text names the instrument that would
         settle it, means Step 8 did not finish — return to Step 8 rather than writing it up.

2. If ANY artifact is missing, STOP and return to the incomplete step. Do NOT proceed
   to document generation with missing artifacts.

3. Mark the Pre-Document Gate task as `completed` via `TaskUpdate`.

### Steps 10-13: Generate the Research Document

Read `references/document-template.md` for the metadata gathering script, file naming
conventions, research document template, GitHub permalink rules, and MCP call
documentation format.

- Gather metadata: run the metadata script; create the research directory if it doesn't exist.
- Generate the research document: write to `~/.claude/thoughts/shared/research/YYYY-MM-DD-description.md` using the template from the reference file, populated with actual values from metadata and synthesized findings.
- Add GitHub permalinks: if on main/master or commit is pushed, replace local file references with `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`.
- Include MCP calls: document the queries, sources, and descriptions from any aika search, codesearch, or web research so findings can be reproduced.

### Step 14: Sync and Present Findings

- Write the output to the `~/.claude/thoughts` directory
- Present a concise summary of findings to the user with key file references
- **Interactive mode**: Ask "Would you like to ask follow-up questions or do you need
  any clarifications?"
- **NON_INTERACTIVE mode**: Skip the follow-up prompt. The research is complete.

### Step 15: Handle Follow-Up Questions (Interactive Mode Only)

- **NON_INTERACTIVE mode**: Skip this step entirely.
- If the user has follow-up questions, append to the same research document
- Update frontmatter fields `last_updated`, `last_updated_by`, and add `last_updated_note`
- Add a new section: `## Follow-up Research [timestamp]`
- Spawn new sub-agents as needed for additional investigation
- Continue updating the document and syncing
- Continue the loop until the user explicitly confirms the research is complete

## Important Notes

- **Path handling**: Preserve the exact directory structure within `~/.claude/thoughts/` (e.g., keep a per-user subdirectory as that same subdirectory, not `shared/`).
- **Fresh research**: Always run fresh research -- never rely solely on existing research documents.
- **Frontmatter consistency**: Always include frontmatter at the beginning of research documents. Use snake_case for multi-word field names. Update frontmatter when adding follow-up research.

## Reference Files

| Reference                                  | Consumed in                                                              |
| ------------------------------------------ | ------------------------------------------------------------------------ |
| `references/plan-templates.md`             | Step 2 (research plan formatting templates)                              |
| `references/agent-guide.md`                | Steps 2-3 (agent selection, pre-spawn verification, domain expert table) |
| `references/verification-and-iteration.md` | Steps 4-6 (validation, completeness review, iteration loop)              |
| `references/review-personas.md`            | Step 7 (reviewer personas, skip rules, review prompt template)           |
| `references/grounding-pass.md`             | Steps 8-9 (grounding pass heuristics, agent prompt, synthesis revision)  |
| `references/document-template.md`          | Steps 10-13 (metadata script, document template, permalinks, MCP calls)  |
