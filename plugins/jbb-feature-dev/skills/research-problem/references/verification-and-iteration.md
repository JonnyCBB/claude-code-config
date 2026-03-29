# Verification, Synthesis, and Iteration for Steps 4-6

Checklists, verification formats, and iteration rules for the research execution loop.
Read this file when Steps 4-6 instruct you to `Read references/verification-and-iteration.md`.

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
- Add "Synthesize findings from all sub-agents" task to TODO list as "pending"
- Add "Validate research completeness (iteration 1)" task as "pending"
- Proceed to step 5

## Pre-Synthesis Agent Verification

Before starting synthesis, run this verification:

```
## Pre-Synthesis Agent Verification

Checking that all committed agent types have been spawned:

From Step 2 Agent Type Verification:
- Agent types committed: [List from Step 2]
- Total: X agent types

Agents actually spawned:
- [List all agent types actually spawned across Batch 1 + Batch 2]
- Total: Y agent types

Verification: X = Y? [YES/NO]

If NO: STOP. Return to Step 3 and spawn missing agent types.
If YES: Proceed with synthesis.
```

**BLOCKER RULES:**
- Count: Agent types mentioned in Step 2 = Agent types actually spawned
- If counts don't match: STOP immediately, identify missing agents, spawn them
- Do NOT proceed to synthesis with incomplete research

## Synthesis Instructions (Step 5)

- Start synthesis only when all agents from the current research phase are complete
- Avoid synthesizing partial results if you plan to spawn more agents
- All agent tasks in TODO list should be "completed" before synthesis starts
- Mark synthesis task as "in_progress" in TODO list now
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
- Mark synthesis task as "completed" in TODO list after synthesis is done
- Proceed to step 6 only after synthesis is marked completed

## Research Completeness Review (Step 6)

Output this section for the user to see:

```
## Research Completeness Review (Iteration N of 2)

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

Question 2: [Question text]
   Status: ADEQUATELY ANSWERED / NEEDS MORE INFO
   Evidence: [Brief summary of what was found OR what's missing]
   Confidence: [High/Medium/Low from agent's Confidence Assessment]

... (for each question)

**Decision:**
- [ ] All questions adequately answered AND all success criteria met -> Proceeding to Step 7
- [ ] Missing information detected -> Will spawn additional subagents and repeat Steps 3-6

**If missing information:**
Missing information needed:
1. [Specific gap identified]
2. [Specific gap identified]

Additional subagents to spawn:
1. [subagent-type] to answer: [specific question about the gap]
2. [subagent-type] to answer: [specific question about the gap]
```

## Completeness Evaluation Criteria

For EACH question from step 2, evaluate:
- Do the subagent findings provide sufficient information to answer this question?
- Are there gaps, ambiguities, or missing details?
- Would the user be satisfied with the answer based on current information?

## Adequate Answer Flow

If ALL questions are adequately answered AND all success criteria are met:
- Mark validation task as "completed" in TODO list
- Proceed to Step 7 (review phase)
- Note: For Simple complexity research, Step 7 may be skipped — proceed to Step 8 (metadata gathering)

## Inadequate Answer Flow

If ANY questions are inadequately answered:
- Mark validation task as "completed" in TODO list
- **Update TODO list before spawning new agents:**
  - Remove or mark synthesis task as "needs revision" (DO NOT leave it as "completed")
  - Add new agent spawn tasks with status "pending"
  - Add new synthesis task with status "pending" (for next iteration)
  - Add new validation task with status "pending" (for next iteration)
- Identify exactly what information is still missing
- Determine which additional subagents need to be spawned to fill the gaps
- **RETURN TO STEP 3**: Spawn new targeted subagents to gather missing information
- **RETURN TO STEP 4**: Wait for new agents to complete
- **RETURN TO STEP 5**: RE-SYNTHESIZE with ALL findings (old + new)
- **RETURN TO STEP 6**: Validate again with new iteration number

## Maximum Iterations Rule

- Maximum 2 iterations total. After completing the steps 3->4->5->6 loop twice, proceed to step 7 even if some gaps remain (document them as "Open Questions")
- Only proceed to step 7 when all questions are adequately answered OR you have completed 2 iterations
- Track iteration count and display it in the "Research Completeness Review" header

## Iteration Loop Structure

**Initial research phase (Iteration 0):**
1. Step 2: Identify questions and create initial TODO list
2. Step 3: Spawn Batch 1 agents (mark as "in_progress")
3. Step 4: WAIT for Batch 1 to complete (mark as "completed"), spawn Batch 2 if needed, wait for completion
4. Step 4: Add synthesis and validation tasks to TODO list (both "pending")
5. Step 5: Mark synthesis as "in_progress", synthesize findings, mark as "completed"
6. Step 6: Mark validation as "in_progress", validate completeness

**If all questions adequately answered (Iteration 0 success):**
1. Step 6: Mark validation as "completed"
2. Step 7: Proceed to metadata gathering

**If gaps found (Iteration N, where N = 1 or 2):**
1. Step 6: Mark validation as "completed"
2. Step 6: Update TODO list (mark/remove previous synthesis, add new agent/synthesis/validation tasks)
3. Step 3 (repeat): Spawn new agents to fill gaps (mark as "in_progress")
4. Step 4 (repeat): WAIT for new agents to complete (mark as "completed")
5. Step 5 (repeat): RE-SYNTHESIZE with ALL findings (old + new), mark as "completed"
6. Step 6 (repeat): Validate again with new iteration number
7. If still gaps and N < 2: Repeat from step 3
8. If N = 2 or all questions answered: Proceed to step 7

**Critical rules:**
- Synthesis can ONLY start when ALL current-phase agents are completed
- Validation can ONLY start when synthesis is completed
- New agents can ONLY spawn after validation identifies gaps
- Maximum 2 iterations total (iteration 0, 1)

## State Machine for Research Flow

```
┌─────────────────────────┐
│ Questions Identified    │
│ (Step 2)                │
└────────────┬────────────┘
             │
             │ Create TODO: agents as "pending"
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
│Spawn      │  │Add synthesis to TODO    │  │
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
│ Validate Completeness   │                  │
│ (Step 6)                │                  │
└────────────┬────────────┘                  │
             │                                │
             v                                │
      ┌──────┴──────┐                        │
      │  Complete?  │                        │
      └──────┬──────┘                        │
             │                                │
        Yes  │  No: Gaps found                │
             │  AND iteration < 2             │
             │                                │
      ┌──────┴────────┐                      │
      │               │                      │
      v               v                      │
┌───────────┐  ┌─────────────────────────┐  │
│Review     │  │Update TODO:             │  │
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
