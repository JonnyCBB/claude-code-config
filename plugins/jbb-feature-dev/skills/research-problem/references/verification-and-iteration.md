# Verification, Synthesis, and Iteration for Steps 4-6

Checklists, verification formats, and iteration rules for the research execution loop.
Read this file when Steps 4-6 instruct you to `Read references/verification-and-iteration.md`.

## Table of Contents

- [Step 4 Validation Checklist](#step-4-validation-checklist)
- [Post-Agent-Completion Rules](#post-agent-completion-rules)
- [Synthesis Instructions (Step 5)](#synthesis-instructions-step-5)
- [Research Completeness Review (Step 6)](#research-completeness-review-step-6)
- [Evaluator Sub-Agent](#evaluator-sub-agent)
- [Completeness Evaluation Criteria](#completeness-evaluation-criteria)
- [Adequate Answer Flow](#adequate-answer-flow)
- [Inadequate Answer Flow](#inadequate-answer-flow)
- [Maximum Iterations Rule](#maximum-iterations-rule)

---

## Step 4 Validation Checklist

Before proceeding to synthesis, verify ALL of the following and show this checklist to the user:

```
## Step 4 Validation Checklist

Reviewing Step 2 question-to-role assignments against delivered evidence:

- Match every stable question ID and assigned role from Step 2 to a delivered report and
  its evidence. Include approved Direct-question answers separately.
- Verify the actual agent type, task ID, artifact, source coverage, and unresolved IDs for
  each assignment. Equal planned/spawned counts do not prove assignment coverage or delivery.
- Stop if no researcher delivers. A zero-delivery run is never valid, even when counts match.
  Revisit questions classified Direct only because the coordinator already read something.
- Apply SKILL.md's bounded delivery recovery to missing assignments. If mandatory delivery
  remains missing, save an incomplete checkpoint; do not substitute self-review.

**If any checkbox is unchecked, return and complete missing items before synthesis.**
```

## Post-Agent-Completion Rules

ONLY AFTER all research agents complete:

- The "Step 5: Synthesize findings" and "Step 6: Completeness review" tasks (created in Post-Research Step Tracking) are now ready to begin
- Call `TaskUpdate` to mark "Step 5: Synthesize findings" as `in_progress`
- Proceed to Step 5

## Synthesis Instructions (Step 5)

- Start synthesis only when all agents from the current research phase are complete
- Avoid synthesizing partial results if you plan to spawn more agents
- Call `TaskList` — verify all research agent tasks show `completed` before synthesis starts
- Call `TaskUpdate` to mark the Step 5 task as `in_progress` (if not already done)
- Compile all sub-agent results (codebase, thoughts and external documentation findings)
- Choose direct sources for each claim: live systems for state, code for implementation,
  original records for decisions, and public sources for external facts
- Use ~/.claude/thoughts/ findings as supplementary historical context
- Connect findings across different components
- Include specific file paths and line numbers for reference
- Verify all ~/.claude/thoughts/ paths are correct
- Highlight patterns, connections, and architectural decisions
- Answer the user's specific questions with concrete evidence
- **Validate assumptions from Step 2**: For each assumption listed in the research plan:
  - CONFIRMED: Evidence supports the assumption
  - INVALIDATED: Evidence contradicts the assumption — note impact on findings
  - UNCERTAIN: No evidence either way — note in Open Questions
- If any assumption is INVALIDATED and it materially changes the research scope,
  flag this in the completeness review (Step 6) as requiring re-research
- **Handle contradictions between agent findings**: When agents return conflicting information:
  1. Document both positions with their evidence and source tiers
  2. If one is backed by higher-tier sources, note that explicitly
  3. If both are equally supported, present both as "Competing Findings" in the synthesis
  4. Do NOT silently choose one interpretation — contradictions must be visible
- Call `TaskUpdate` to mark the Step 5 task as `completed`
- Proceed to Step 6 only after the Step 5 task is marked `completed`

## Research Completeness Review (Step 6)

## Evaluator Sub-Agent

### Evaluator Prompt Template

Pass this prompt to the evaluator sub-agent (model: sonnet). The prompt tells it not to use
tools; its tool roster need not be empty. Deliver the full plan, synthesis, cumulative
ID/budget ledgers, and the canonical `## Materiality Filter` text from
`references/grounding-pass.md` inline. Expand policy blocks; file paths do not deliver
policy to a judge that must not read files. Check the assembled prompt for missing or truncated input.

```
You are the Completeness Evaluator for a research document. Your job is to judge whether
the synthesized research findings adequately answer every question in the research plan.

You are a separate agent from the one that produced these findings. This separation exists
because models reliably skew positive when grading their own work — a standalone evaluator
with a skeptical disposition catches gaps that self-evaluation misses.

## Disposition

When evidence for a question is ambiguous or incomplete, default to NEEDS MORE INFO rather
than ADEQUATELY ANSWERED. It is better to trigger one more research iteration than to let
inadequate findings proceed to documentation.

## Research Plan

[RESEARCH_PLAN — questions, success criteria, assumptions from Step 2]

## Synthesized Findings

[SYNTHESIZED_FINDINGS from Step 5]

[IF ITERATION 2+:]
## Prior Evaluation (Iteration N-1)

[PRIOR_EVALUATION — your output from the previous iteration, so you can verify whether
identified gaps have been addressed]
[/IF]

## Cumulative Ledgers

[CUMULATIVE_LEDGERS — stable IDs, assignments, evidence, classifications, corrections,
prior outcomes, and remaining run-budget counters]

## Materiality Filter

[MATERIALITY_FILTER — the complete canonical section from references/grounding-pass.md,
verbatim, not a paraphrase or path]

## Instructions

Assess only the complete supplied evidence. Do not retrieve sources or call tools. Reject
missing input; report evidence limits. This verdict checks supplied evidence, not independent
empirical reproduction. Match question, criterion, claim, and flag IDs to evidence; list
missing, duplicate, or substituted IDs. Counts are secondary. Retain IDs in every output row
and assign stable IDs to new gaps and Needs Verification flags.

Produce your evaluation using EXACTLY this format:

### Success Criteria Evaluation
- [ ] Criterion [stable criterion ID]: [MET/NOT MET] — Evidence: [linked claim/source IDs and brief summary]
... (for each criterion from the research plan)

### Assumption Validation
- Assumption 1: [CONFIRMED/INVALIDATED/UNCERTAIN] — [brief evidence]
... (for each assumption from the research plan)

### Per-Question Assessment

Question [stable question ID]: [Question text]
   Status: ADEQUATELY ANSWERED / NEEDS MORE INFO
   Evidence: [Brief summary of what was found OR what's missing]
   Confidence: [High/Medium/Low]
   Needs Verification: [YES/NO — flag YES if claims about tool behavior, API responses,
   or configuration effects have not been empirically verified. Do NOT attempt verification
   yourself — flag it for the grounding pass (Step 8).]
   Verification flag ID: [stable ID linked to the question, claim, and required evidence]

... (for each question from the research plan)

### Decision

PROCEED — all questions adequately answered AND all success criteria met
OR
ITERATE — a NEEDS MORE INFO gap passes the supplied canonical Materiality Filter, or
required decisive evidence is missing or self-reported only. A non-material gap does not
justify ITERATE; record its ID and limit for Step 8 classification instead.

[If ITERATE:]
Missing information needed:
1. [stable gap ID and originating IDs] [Specific gap identified] — [why it is material]

Additional subagents to spawn:
1. [subagent-type] to answer: [specific question about the gap]
```

### Orchestrator Handoff Protocol

After spawning the evaluator and receiving its verdict:

1. **Display**: Output the evaluator's verdict verbatim (no editing, no summarizing)
2. **Parse**: Read the Decision field — it starts with either "PROCEED" or "ITERATE"
3. **If PROCEED**: Call `TaskUpdate` to mark the Step 6 task as `completed`. Proceed to Step 7.
4. **If ITERATE**: Call `TaskUpdate` to mark the Step 6 task as `completed`. Create new
   tasks via `TaskCreate`: new agent tasks (pending), new synthesis task (pending), new
   validation task (pending). Increment iteration counter. Return to Step 3 with the
   evaluator's "Additional subagents to spawn" list.
5. **Task ownership**: All task state mutations are the orchestrator's responsibility.
   The evaluator only returns a verdict — it never modifies task state.

### Spawning Instructions

- **Model**: sonnet
- **Tools**: none — the evaluator receives only text, no file access, no MCP tools, no
  codebase exploration
- **Input**: full research plan + synthesis + canonical materiality + cumulative ID/evidence
  and budget ledgers + prior evaluation (iteration 2+ only), delivered inline

## Displaying the Verdict

Output the evaluator's verdict verbatim under the header
`## Research Completeness Review (Iteration N of 4)`. The body is the evaluator's own
output — it already carries the required format, because its prompt above specifies it.
Do not re-render, re-order or summarize it.

## Completeness Evaluation Criteria

For EACH question from step 2, evaluate:

- Do the subagent findings provide sufficient information to answer this question?
- Are there gaps, ambiguities, or missing details?
- Would the user be satisfied with the answer based on current information?
- For findings that describe tool behavior, API responses, or configuration effects: the evaluator flags `Needs Verification: YES` in the Per-Question Assessment. The evaluator does not attempt verification itself (it is told not to use tools). Verification is resolved in Step 8 (grounding pass), where the grounding agent can use the explicit flags alongside its existing detection heuristics.

## Adequate Answer Flow

If ALL questions are adequately answered AND all success criteria are met:

- Call `TaskUpdate` to mark the Step 6 task as `completed`
- Proceed to Step 7. The review phase runs at every complexity; complexity chooses the
  reviewer roster, never whether the phase happens.

## Inadequate Answer Flow

If ANY questions are inadequately answered:

- Call `TaskUpdate` to mark the Step 6 task as `completed`
- **Create new tasks via `TaskCreate` before spawning new agents:**
  - Create new agent tasks with descriptive subjects (status: pending by default)
  - Create "Synthesis iteration N" task (pending)
  - Create "Validation iteration N" task (pending)
- Identify exactly what information is still missing
- Determine which additional subagents need to be spawned to fill the gaps
- **RETURN TO STEP 3**: Spawn new targeted subagents to gather missing information
- **RETURN TO STEP 4**: Wait for new agents to complete
- **RETURN TO STEP 5**: RE-SYNTHESIZE with ALL findings (old + new)
- **RETURN TO STEP 6**: Validate again with new iteration number

## Maximum Iterations Rule

- Maximum 4 rounds for completeness and, separately, for persona review. Continue only
  while required gaps pass the canonical Materiality Filter in
  `references/grounding-pass.md`. Bounds stop execution, not pass gates: remaining material
  evidence gaps or blocking review items require an incomplete draft checkpoint with IDs,
  attempts, evidence, and next actions, not a completed document.
- This is the single canonical location for the round bound — other steps (Step 6/7 in
  `SKILL.md`, the Iteration Mechanism in `references/review-personas.md`) point here rather
  than re-stating the number, to avoid two independently-hardcoded values drifting apart.
- Proceed to Step 7 only after an independent PROCEED with no remaining material gap.
  Missing mandatory delivery blocks approval after SKILL.md's bounded recovery.
- Track both round counters in the parent's cumulative run-budget ledger and display the
  completeness count in the "Research Completeness Review" header. Substantive revisions
  return to completeness and affected reviewers using remaining counters, never new budgets.
