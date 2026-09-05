# Verification, Synthesis, and Iteration for Steps 4-6

Checklists, verification formats, and iteration rules for the research execution loop.
Read this file when Steps 4-6 instruct you to `Read references/verification-and-iteration.md`.

## Table of Contents

- [Step 4 Validation Checklist](#step-4-validation-checklist)
- [Post-Agent-Completion Rules](#post-agent-completion-rules)
- [Synthesis Instructions (Step 5)](#synthesis-instructions-step-5)
- [Research Completeness Review (Step 6)](#research-completeness-review-step-6)
- [Evaluator Sub-Agent](#evaluator-sub-agent)
- [Completeness Review Format](#completeness-review-format)
- [Completeness Evaluation Criteria](#completeness-evaluation-criteria)
- [Adequate Answer Flow](#adequate-answer-flow)
- [Inadequate Answer Flow](#inadequate-answer-flow)
- [Maximum Iterations Rule](#maximum-iterations-rule)
- [State Machine for Research Flow](#state-machine-for-research-flow)

---

## Step 4 Validation Checklist

Before proceeding to synthesis, verify ALL of the following and show this checklist to the user:

```
## Step 4 Validation Checklist

Reviewing agent commitments from Step 2 against actual agents spawned:

- For each question that mentioned "codebase-explorer":
  - Have I spawned the codebase-explorer agent? If NO -> STOP and spawn it now

- Cross-check against Agent Type Verification from Step 2:
  - All agent types listed there must be spawned before synthesis
  - Count: [X agent types listed, Y agent types spawned]
  - If X != Y: STOP and spawn missing agents

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
- Prioritize live codebase and latest documentation findings as primary source of truth
- Use ~/.claude/thoughts/ findings as supplementary historical context
- Connect findings across different components
- Include specific file paths and line numbers for reference
- Verify all ~/.claude/thoughts/ paths are correct
- Highlight patterns, connections, and architectural decisions
- Identify specific service/component names mentioned in findings (for operational-context recommendation)
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

Step 6 uses a dedicated evaluator sub-agent instead of self-evaluation because models
reliably skew positive when grading their own work — a standalone evaluator with a mildly
skeptical disposition catches gaps that self-evaluation misses.

### Evaluator Prompt Template

Pass this prompt to the evaluator sub-agent (model: sonnet, no tools):

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

## Instructions

Produce your evaluation using EXACTLY this format:

### Success Criteria Evaluation
- [ ] Criterion 1: [MET/NOT MET] — Evidence: [brief summary]
... (for each criterion from the research plan)

### Assumption Validation
- Assumption 1: [CONFIRMED/INVALIDATED/UNCERTAIN] — [brief evidence]
... (for each assumption from the research plan)

### Per-Question Assessment

Question 1: [Question text]
   Status: ADEQUATELY ANSWERED / NEEDS MORE INFO
   Evidence: [Brief summary of what was found OR what's missing]
   Confidence: [High/Medium/Low]
   Needs Verification: [YES/NO — flag YES if claims about tool behavior, API responses,
   or configuration effects have not been empirically verified. Do NOT attempt verification
   yourself — flag it for the grounding pass (Step 8).]

... (for each question from the research plan)

### Decision

PROCEED — all questions adequately answered AND all success criteria met
OR
ITERATE — a NEEDS MORE INFO gap exists that is material (resolving it could change a
conclusion, recommendation, or tier classification — apply the Materiality Filter from
`references/grounding-pass.md`'s `## Materiality Filter` section). A NEEDS MORE INFO gap
that is not material does not justify ITERATE — note it as an Open Question instead.

[If ITERATE:]
Missing information needed:
1. [Specific gap identified] — [why it is material]

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
- **Input**: research plan (Step 2) + synthesized findings (Step 5) + prior evaluation
  (iteration 2+ only)

## Completeness Review Format

Output this section for the user to see:

```
## Research Completeness Review (Iteration N of 4)

### Success Criteria Evaluation
Evaluating success criteria from Step 2:
- [ ] Criterion 1: [MET/NOT MET] — Evidence: [brief summary]
- [ ] Criterion 2: [MET/NOT MET] — Evidence: [brief summary]
... (for each criterion)

### Assumption Validation
- Assumption 1: [CONFIRMED/INVALIDATED/UNCERTAIN] — [brief evidence]
- Assumption 2: [CONFIRMED/INVALIDATED/UNCERTAIN] — [brief evidence]

### Per-Question Assessment
Reviewing whether all questions from Step 2 have been adequately answered:

Question 1: [Question text]
   Status: ADEQUATELY ANSWERED / NEEDS MORE INFO
   Evidence: [Brief summary of what was found OR what's missing]
   Confidence: [High/Medium/Low from agent's Confidence Assessment]
   Needs Verification: [YES/NO — flag YES when evidence describes tool behavior,
   API responses, or configuration effects that have not been empirically verified]

Question 2: [Question text]
   Status: ADEQUATELY ANSWERED / NEEDS MORE INFO
   Evidence: [Brief summary of what was found OR what's missing]
   Confidence: [High/Medium/Low from agent's Confidence Assessment]
   Needs Verification: [YES/NO — flag YES when evidence describes tool behavior,
   API responses, or configuration effects that have not been empirically verified]

... (for each question)

### Decision

PROCEED — all questions adequately answered AND all success criteria met
OR
ITERATE — a NEEDS MORE INFO gap exists that is material (see the Materiality Filter in
`references/grounding-pass.md`). Non-material gaps are documented as Open Questions instead.

[If ITERATE:]
Missing information needed:
1. [Specific gap identified] — [why it is material]

Additional subagents to spawn:
1. [subagent-type] to answer: [specific question about the gap]
```

## Completeness Evaluation Criteria

For EACH question from step 2, evaluate:

- Do the subagent findings provide sufficient information to answer this question?
- Are there gaps, ambiguities, or missing details?
- Would the user be satisfied with the answer based on current information?
- For findings that describe tool behavior, API responses, or configuration effects: the evaluator flags `Needs Verification: YES` in the Per-Question Assessment. The evaluator does not attempt verification itself (it has no tools). Verification is resolved in Step 8 (grounding pass), where the grounding agent can use the explicit flags alongside its existing detection heuristics.

## Adequate Answer Flow

If ALL questions are adequately answered AND all success criteria are met:

- Call `TaskUpdate` to mark the Step 6 task as `completed`
- Proceed to Step 7 (review phase)
- Note: For Simple complexity research, Step 7 may be skipped — proceed to Step 8 (grounding pass)

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

- Maximum 4 rounds. Continue iterating only while a remaining gap passes the Materiality
  Filter defined in `references/grounding-pass.md`'s `## Materiality Filter` section (would
  addressing it change a conclusion, recommendation, or tier classification). At 4 rounds,
  stop regardless of remaining material gaps and document them as "Open Questions" (same
  fallback as before).
- This is the single canonical location for the round bound — other steps (Step 6/7 in
  `SKILL.md`, the Iteration Mechanism in `references/review-personas.md`) point here rather
  than re-stating the number, to avoid two independently-hardcoded values drifting apart.
- Only proceed to step 7 when all questions are adequately answered, no remaining gap passes
  the Materiality Filter, OR you have completed 4 rounds
- Track iteration count and display it in the "Research Completeness Review" header

## State Machine for Research Flow

```
┌─────────────────────────┐
│ Questions Identified    │
│ (Step 2)                │
└────────────┬────────────┘
             │
             │ TaskCreate: agents as "pending"
             │ DO NOT add synthesis yet
             v
┌─────────────────────────┐
│ Spawn Agents (Step 3)   │◄────────────────┐
│ Mark agents "in_progress"│                 │
└────────────┬────────────┘                  │
             │                                │
             v                                │
┌─────────────────────────┐                  │
│ All Agents Complete?    │                  │
│ (Step 4 Checkpoint)     │                  │
└────────────┬────────────┘                  │
             │ No: wait                       │
             │ Yes: mark "completed"          │
             v                                │
┌─────────────────────────┐                  │
│ Need Batch 2 Analyzers? │                  │
│ (Step 4)                │                  │
└────────────┬────────────┘                  │
             │                                │
         Yes │  No                            │
             │                                │
      ┌──────┴────────┐                      │
      │               │                      │
      v               v                      │
┌───────────┐  ┌─────────────────────────┐  │
│Spawn      │  │TaskCreate: synthesis    │  │
│Batch 2    │  │Mark "pending"           │  │
│Wait       │  └────────────┬────────────┘  │
└─────┬─────┘               │                │
      │                     │                │
      └──────────┬──────────┘                │
                 │                            │
                 v                            │
┌─────────────────────────┐                  │
│ Mark Synthesis          │                  │
│ "in_progress" (Step 5)  │                  │
└────────────┬────────────┘                  │
             │                                │
             v                                │
┌─────────────────────────┐                  │
│ Synthesize Results      │                  │
│ (Step 5)                │                  │
└────────────┬────────────┘                  │
             │                                │
             │ Mark "completed"               │
             v                                │
┌─────────────────────────┐                  │
│ Mark Validation         │                  │
│ "in_progress" (Step 6)  │                  │
└────────────┬────────────┘                  │
             │                                │
             v                                │
┌─────────────────────────┐                  │
│ Spawn Evaluator         │                  │
│ Sub-Agent (Step 6)      │                  │
│ model: sonnet, no tools │                  │
│ Input: plan + synthesis │                  │
│ + prior eval (iter 2+)  │                  │
└────────────┬────────────┘                  │
             │                                │
             v                                │
┌─────────────────────────┐                  │
│ Evaluator Returns       │                  │
│ Verdict                 │                  │
└────────────┬────────────┘                  │
             │                                │
             v                                │
┌─────────────────────────┐                  │
│ Orchestrator Displays   │                  │
│ Verdict & Acts on       │                  │
│ Decision                │                  │
└────────────┬────────────┘                  │
             │                                │
             v                                │
      ┌──────┴──────┐                        │
      │  Complete?  │                        │
      └──────┬──────┘                        │
             │                                │
        Yes  │  No: Material gaps found       │
             │  AND iteration < 4             │
             │                                │
      ┌──────┴────────┐                      │
      │               │                      │
      v               v                      │
┌───────────┐  ┌─────────────────────────┐  │
│Review     │  │TaskUpdate/TaskCreate:   │  │
│Phase      │  │- Mark validation done   │  │
│(Step 7)   │  │- Remove/revise synthesis│  │
│           │  │- Add new agent tasks    │  │
│           │  │- Add new synthesis task │  │
│           │  │- Add new validation task│──┘
│           │  │Mark new agents "pending"│
└───────────┘  └─────────────────────────┘
                Increment iteration N
                RETURN to "Spawn Agents"
```

**Key State Transitions:**

- `pending` -> `in_progress` -> `completed` for each task
- Synthesis stays `pending` until ALL agents are `completed`
- If gaps found, new iteration creates new pending tasks
- Synthesis is NOT marked `completed` if gaps require more research
