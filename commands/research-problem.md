# Research Problem

You are tasked with conducting comprehensive research across the codebase and beyond to answer user questions by spawning parallel sub-agents and synthesizing their findings.

## Your role: Document and explain the codebase as it exists today
- Do not suggest improvements or changes unless the user explicitly asks for them
- Do not perform root cause analysis unless the user explicitly asks for them
- Do not propose future enhancements unless the user explicitly asks for them
- Do not critique the implementation or identify problems
- Do not recommend refactoring, optimization, or architectural changes
- Only describe what exists, where it exists, how it works, and how components interact
- You are creating a technical map/documentation of the existing system

## Initial Setup:

When this command is invoked, respond with:
```
I'm ready to research the problem. Please provide your research question or area of interest, and I'll analyze it thoroughly by exploring relevant components and connections.
```

Then wait for the user's research query.

## Steps to follow after receiving the research query:

1. **Read any directly mentioned files first:**
   - If the user mentions specific files (tickets, docs, JSON, etc.), read them fully first
   - Use the Read tool without limit/offset parameters to read entire files unless the user has given explicit instructions not to read a file in its entirety
   - Read these files yourself in the main context before spawning any sub-tasks
   - This ensures you have full context before decomposing the research.

2. **Analyze and decompose the research question:**
   - **Consider the research problem carefully from multiple angles**
   - **Write out all sections below in your response text for the user to see**
   - Format the output clearly in the terminal:

   ```
   ## Research Questions

   To answer "[user's question]", I need to investigate:

   1. [Question 1] → Will use [subagent-type]
   2. [Question 2] → Will use [subagent-type]
   3. [Question 3] → Will use [subagent-type]
   ...

   ## Research Assumptions

   **Explicit Assumptions:**
   - [Assumptions directly stated or clearly implied in the user's question]
   - [Technology, framework, or version assumptions (e.g., "Assuming Python 3.8+")]
   - [Scope assumptions (e.g., "Focusing on production code, excluding tests")]
   - [Environment assumptions (e.g., "Assuming deployment to AWS")]

   **Implicit Assumptions:**
   - [Assumptions about codebase structure or organization]
   - [Assumptions about what's relevant vs irrelevant to the question]
   - [Assumptions about the user's knowledge level or goals]
   - [Assumptions about current vs historical state]

   **⚠️ If any assumptions are incorrect, please clarify now before I proceed.**

   ## Research Scope

   **In Scope:**
   - [Specific components, modules, or areas to investigate]
   - [Layers or tiers (e.g., "backend API layer only")]
   - [Time period if relevant (e.g., "current implementation", "last 6 months of changes")]
   - [Specific file types or patterns (e.g., "*.py files in src/")]

   **Out of Scope:**
   - [Components or areas that won't be investigated]
   - [Rationale for exclusions (e.g., "legacy v1 API - deprecated")]
   - [Related but separate concerns (e.g., "performance optimization - separate topic")]

   ## Success Criteria

   This research will be considered complete when:
   - [ ] [Specific question X is answered with concrete code evidence and file references]
   - [ ] [Component Y is documented with architecture explanation]
   - [ ] [Connections/data flow between A and B are mapped and explained]
   - [ ] [All integration points with Z are identified and documented]
   ...

   ## Known Constraints

   **Access Limitations:**
   - [e.g., "No access to production logs or runtime data, only source code"]
   - [e.g., "Cannot access private/internal documentation beyond codebase"]

   **Knowledge Gaps:**
   - [e.g., "May need external documentation for third-party library X"]
   - [e.g., "Historical context may be limited to git history and thoughts/"]

   **Research Limits:**
   - [e.g., "Maximum 2 iteration loops per research-problem protocol"]
   - [e.g., "Focusing on documentation, not performance testing"]

   **Tool/Technology Limitations:**
   - [e.g., "Can only analyze static code, not runtime behavior"]
   - [e.g., "External API documentation may be incomplete or outdated"]

   ## Research Context

   **Known starting points** (extracted from your question):
   - [File/component explicitly mentioned, e.g., "`AuthService.java` - mentioned in question"]
   - [System/feature mentioned, e.g., "Authentication flow - specified as focus area"]
   - [Or: "None explicitly mentioned - will discover through research"]

   **Prior knowledge assumed** (what you appear to already understand):
   - [Inferred knowledge, e.g., "Familiar with OAuth flow based on question framing"]
   - [Domain familiarity, e.g., "Understands the difference between authentication and authorization"]
   - [Or: "Assuming standard domain familiarity; will explain system-specific details"]

   **Previous research** (if any):
   - [Link to existing research docs if found in thoughts/shared/research/]
   - [Related investigations, e.g., "See thoughts/shared/research/2024-12-01-auth-flow.md for related work"]
   - [Or: "No prior research found on this topic"]
   ```

   - **For each assumption, reflect on:**
     - Is this something the user explicitly stated?
     - Is this something I inferred from the question or context?
     - Could this assumption be wrong, and would that change my approach?

   - For each question identified, determine:
     - What type of information is needed (codebase, internal docs/tools, external resources)
     - Which subagent type would be most appropriate to answer it
     - What specific areas or components to investigate

   - Create a research plan using TodoWrite to track all subtasks with **GRANULAR agent-level tracking**:
     - **Specific agent spawn tasks** (e.g., "Spawn codebase-locator for deployment", "Spawn codebase-analyzer for deployment files")
     - For codebase research, create separate todos for locator and analyzer phases
     - **Do not add synthesis task to the TODO list yet** - it will be added in step 3.5 after all initial agents complete
     - **Pattern for iterative research TODO structure:**
       ```
       Phase 1 Research Tasks:
       - Research question 1 with agent X (pending → in_progress → completed)
       - Research question 2 with agent Y (pending → in_progress → completed)
       - Spawn codebase-locator for question 3 (pending → in_progress → completed)
       [After locator completes in step 3.5]
       - Spawn codebase-analyzer for question 3 (pending → in_progress → completed)
       [After ALL agents complete in step 3.5]
       - Synthesis attempt 1 (pending → in_progress → completed)
       - Validation iteration 1 (pending → in_progress → completed)
       [If gaps found in step 5]
       Phase 2 Research Tasks:
       - Additional research for gap 1 (pending → in_progress → completed)
       [After new agents complete]
       - Synthesis attempt 2 (pending → in_progress → completed)
       - Validation iteration 2 (pending → in_progress → completed)
       ```

   **Agent Type Accounting**
   - At the end of Step 2, after listing all sections above, create an accountability list:
   ```
   ## Agent Type Verification

   Based on the questions above, I will spawn the following agent types:
   - codebase-locator (questions 1, 3)
   - codebase-analyzer (questions 1, 3) - will spawn in Batch 2 after locators complete
   - web-search-researcher (question 2)
   - codebase-pattern-finder (question 4)

   Total unique agent types: 4
   ```
   - **This list becomes your contract**: all agent types listed here should be spawned before synthesis
   - If you skip any agent type, you are breaking the contract and the research will be incomplete

   - **After presenting all sections above (Questions, Assumptions, Research Context, Scope, Success Criteria, Constraints, and Agent Type Verification), explicitly ask the user:**

     **Review and Confirmation**

     Do these look correct?
     - Questions to investigate
     - Assumptions (explicit, implicit, constraints)
     - Research context (starting points, prior knowledge, previous research)
     - Success criteria
     - Scope boundaries (in/out)
     - Agent types to spawn

     Should I adjust anything before proceeding?

   - **Wait for the user to respond before proceeding to Step 3.** Do not continue until the user explicitly confirms the research plan is acceptable or provides adjustments.

3. **Spawn parallel sub-agent tasks for comprehensive research (BATCH 1):**
   - **For each question identified in step 2, spawn at least one appropriate subagent to answer it**
   - **Combining questions**: You may combine multiple related questions into a single subagent if:
     - The questions are closely related and can be answered by the same source/agent type
     - It's more efficient than spawning separate agents
     - **Tell the user which questions you're combining and why**
       Example: "Combining questions 1 & 2 into external-repo-explorer since both involve search-api video detection"
   - Create multiple Task agents to research different aspects concurrently
   - Select the most appropriate agent type for each question based on these specialized agents:

   **For codebase research (Sequential, not parallel):**
   - **Do not spawn codebase-locator and codebase-analyzer in parallel**
   - **Batch 1 Pattern**: Spawn all non-codebase agents in parallel first, along with codebase-locator agents
     - web-search-researcher agents
     - codebase-locator agents (to find WHERE files are)
     - thoughts-locator agents
   - **Batch 2 Pattern** (handled in step 3.5): After Batch 1 completes, spawn codebase-analyzer agents
     - codebase-analyzer agents (to understand HOW code works)
     - codebase-pattern-finder agents (to find usage examples)
     - thoughts-analyzer agents
   - **Reasoning**: Locator must find files before analyzer can explain them. This is a sequential dependency, not parallel work.
   - Update TODO list: Mark Batch 1 agent tasks as "in_progress" when spawning

  **For thoughts directory:**
   - Use the **thoughts-locator** agent to discover what documents exist about the topic
   - Use the **thoughts-analyzer** agent to extract key insights from specific documents (only the most relevant ones)
   - If the **thoughts** directory doesn't exist in the root directory then create it.

   All agents are documentarians, not critics. They will describe what exists without suggesting improvements or identifying issues.

   **For external (outside the codebase) research (e.g. documentation, web search):**
   - Use the **web-search-researcher** agent for external documentation and resources
   - When using the **web-search-researcher** agent, instruct it to return LINKS with its findings, and please INCLUDE those links in your final report

   The key is to use these agents intelligently:
   - Start with locator agents to find what exists
   - Then use analyzer agents on the most promising findings to document how they work
   - Run multiple agents in parallel when they're searching for different things
   - Each agent knows its job - just tell it what you're looking for
   - Don't write detailed prompts about HOW to search - the agents already know
   - Remind agents they are documenting, not evaluating or improving

   **Example of question decomposition and subagent assignment:**

   User question: "How do we handle automerge for dependency bot PRs?"

   Questions to answer:
   1. What automerge configurations exist in this repository? → **codebase-analyzer**
   2. What automerge patterns do similar repos use? → **codebase-pattern-finder**
   3. What external tools (Renovate, Dependabot) support automerge? → **web-search-researcher**

   Result: Spawn 3 subagents in parallel, each focused on one specific question.

3.5. **Checkpoint - Wait for Batch 1 agents and spawn Batch 2 if needed:**
   - **Wait**: Do not proceed until all Batch 1 agents return results
   - Verify you have results from every agent you spawned in step 3
   - If any agent failed or returned no output, re-spawn with adjusted prompt
   - Update TODO list: mark all Batch 1 agent tasks as "completed"

   **Step 3.5 Validation Checklist (output this to user):**

   Before proceeding to synthesis, verify all of the following and show this checklist to the user:

   ```
   ## Step 3.5 Validation Checklist

   Reviewing agent commitments from Step 2 against actual agents spawned:

   □ For each question in Step 2 that mentioned "codebase-locator THEN codebase-analyzer":
     - Did locator find files? If YES → codebase-analyzer is required (spawn in Batch 2)
     - Have I spawned or planned the analyzer agent? If NO → Pause and add it now

   □ For each question that mentioned "codebase-pattern-finder":
     - Have I spawned the pattern-finder agent? If NO → Pause and spawn it now

   □ For each question that mentioned other Batch 2 agents (thoughts-analyzer, etc.):
     - Have I spawned all mentioned agents? If NO → Pause and spawn them now

   □ Cross-check against Agent Type Verification from Step 2:
     - All agent types listed there must be spawned before synthesis
     - Count: [X agent types listed, Y agent types spawned]
     - If X ≠ Y: Pause and spawn missing agents

   **If any checkbox is unchecked, do not proceed to synthesis.**
   ```

   **Batch 2 Spawning Decision (Codebase-Analyzer Agents):**

   If you mentioned "codebase-locator THEN codebase-analyzer" in Step 2, apply this decision tree:

   **Rule 1: If locator found files → spawn analyzer by default**
   - The fact that locator provided code snippets does not eliminate the need for analyzer
   - Locator's job: Find WHERE files are
   - Analyzer's job: Explain HOW the code works (architecture, data flow, patterns)
   - These are different objectives

   **Rule 2: Analyzer can only be skipped if both conditions are true:**
   1. Locator output already includes comprehensive HOW analysis (not just code listings)
   2. You explicitly tell the user you're skipping it and why

   **Transparency requirement**:
   - If skipping analyzer: Tell the user before proceeding:
     ```
     "The codebase-locator output for [question] provides sufficient HOW analysis to answer
     the question without needing a separate codebase-analyzer agent. The locator explained
     [brief summary of what was explained]. I will skip the analyzer agent for this question."
     ```
   - If spawning analyzer: Add new TODO items and mark as "pending"

   **Default action: When in doubt, spawn the analyzer. Over-researching is better than under-researching.**

   **Spawn Batch 2 (codebase-analyzer agents):**
   - Based on the decision tree above, spawn analyzer agents as needed
   - Mark these new tasks as "in_progress" in the TODO list
   - Wait for Batch 2 agents to complete
   - Mark Batch 2 tasks as "completed" when done

   **Only after all research agents complete (Batch 1 + Batch 2):**
   - Add "Synthesize findings from all sub-agents" task to TODO list
   - Mark synthesis task as "pending" (NOT in_progress yet)
   - Add "Validate research completeness (iteration 1)" task as "pending"
   - Proceed to step 4

4. **Synthesize findings from all sub-agents:**

   **Pre-synthesis verification:**

   ```
   ## Pre-Synthesis Agent Verification

   Checking that all committed agent types have been spawned:

   From Step 2 Agent Type Verification:
   - Agent types committed: [List from Step 2]
   - Total: X agent types

   Agents actually spawned:
   - [List all agent types actually spawned across Batch 1 + Batch 2]
   - Total: Y agent types

   ✓ Verification: X = Y? [YES/NO]

   If NO: Return to Step 3 and spawn missing agent types.
   If YES: Proceed with synthesis.
   ```

   **Verification rules:**
   - Count: Agent types mentioned in Step 2 = Agent types actually spawned
   - If counts don't match: Pause, identify missing agents, spawn them
   - Do not proceed to synthesis with incomplete research

   - **Only start synthesis when all agents from current research phase are complete**
   - **Do not synthesize partial results if you plan to spawn more agents**
   - All agent tasks in TODO list should be "completed" before synthesis starts
   - Mark synthesis task as "in_progress" in TODO list now
   - Compile all sub-agent results (codebase, thoughts and external documentation findings)
   - Prioritize live codebase and latest documentation findings as primary source of truth
   - Use thoughts/ findings as supplementary historical context
   - Connect findings across different components
   - Include specific file paths and line numbers for reference
   - Verify all thoughts/ paths are correct (e.g., thoughts/jbrooksbartlett/ not thoughts/shared/ for personal files)
   - Highlight patterns, connections, and architectural decisions
   - Answer the user's specific questions with concrete evidence
   - Mark synthesis task as "completed" in TODO list after synthesis is done
   - **Do not proceed to step 5 until synthesis is marked completed**

5. **Reflect and validate research completeness (iterative loop):**
   - **This step should be visible to the user**
   - **Output a "Research Completeness Review" section that shows your analysis**
   - Mark validation task as "in_progress" in TODO list
   - Review the questions identified in step 2 against the synthesized findings from step 4

   **Output this section for the user to see:**
   ```
   ## Research Completeness Review (Iteration N of 2)

   Reviewing whether all questions from Step 2 have been adequately answered:

   ✅ Question 1: [Question text]
      Status: ADEQUATELY ANSWERED / NEEDS MORE INFO
      Evidence: [Brief summary of what was found OR what's missing]

   ✅ Question 2: [Question text]
      Status: ADEQUATELY ANSWERED / NEEDS MORE INFO
      Evidence: [Brief summary of what was found OR what's missing]

   ... (for each question)

   **Decision:**
   - [ ] All questions adequately answered → Proceeding to Step 6 (metadata gathering)
   - [ ] Missing information detected → Will spawn additional subagents and repeat Steps 3-5

   **If missing information:**
   Missing information needed:
   1. [Specific gap identified]
   2. [Specific gap identified]

   Additional subagents to spawn:
   1. [subagent-type] to answer: [specific question about the gap]
   2. [subagent-type] to answer: [specific question about the gap]
   ```

   - For EACH question from step 2, evaluate:
     - Do the subagent findings provide sufficient information to answer this question?
     - Are there gaps, ambiguities, or missing details?
     - Would the user be satisfied with the answer based on current information?

   - **If all questions are adequately answered:**
     - Mark validation task as "completed" in TODO list
     - Proceed to step 6 (metadata gathering)

   - **If any questions are inadequately answered:**
     - Mark validation task as "completed" in TODO list
     - **Update TODO list before spawning new agents:**
       - Remove or mark synthesis task as "needs revision" (do not leave it as "completed")
       - Add new agent spawn tasks with status "pending"
       - Add new synthesis task with status "pending" (for next iteration)
       - Add new validation task with status "pending" (for next iteration)
     - Identify exactly what information is still missing
     - Determine which additional subagents need to be spawned to fill the gaps
     - **Return to Step 3**: Spawn new targeted subagents to gather missing information
     - **Return to Step 3.5**: Wait for new agents to complete
     - **Return to Step 4**: Re-synthesize with all findings (old + new)
     - **Return to Step 5**: Validate again with new iteration number

   - **Maximum 2 iterations**: After completing the steps 3→4→5 loop twice total, proceed to step 6 even if some gaps remain (document them as "Open Questions")
   - **Only proceed to step 6 when:**
     - All questions from step 2 are adequately answered, OR
     - You have completed 2 iterations of the research loop
   - Track iteration count and display it in the "Research Completeness Review" header

6. **Gather metadata for the research document:**
   - Run the following script to generate metadata:
        ```bash
        #!/usr/bin/env bash
        set -euo pipefail

        # Collect metadata
        DATETIME_TZ=$(date '+%Y-%m-%d %H:%M:%S %Z')
        FILENAME_TS=$(date '+%Y-%m-%d_%H-%M-%S')

        if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        REPO_ROOT=$(git rev-parse --show-toplevel)
        REPO_NAME=$(basename "$REPO_ROOT")
        GIT_BRANCH=$(git branch --show-current 2>/dev/null || git rev-parse --abbrev-ref HEAD)
        GIT_COMMIT=$(git rev-parse HEAD)
        else
        REPO_ROOT=""
        REPO_NAME=""
        GIT_BRANCH=""
        GIT_COMMIT=""
        fi

        # Print similar to the individual command outputs
        echo "Current Date/Time (TZ): $DATETIME_TZ"
        [ -n "$GIT_COMMIT" ] && echo "Current Git Commit Hash: $GIT_COMMIT"
        [ -n "$GIT_BRANCH" ] && echo "Current Branch Name: $GIT_BRANCH"
        [ -n "$REPO_NAME" ] && echo "Repository Name: $REPO_NAME"
        echo "Timestamp For Filename: $FILENAME_TS"
        ```
   - Create the `thoughts/shared/research/` directory if it doesn't exist
   - Filename: `thoughts/shared/research/YYYY-MM-DD-description.md`
     - Format: `YYYY-MM-DD-description.md` where:
       - YYYY-MM-DD is today's date
       - description is a brief kebab-case description of the research topic
     - Example: `2025-01-08-authentication-flow.md`

7. **Generate research document:**
   - Use the metadata gathered in step 6
   - Structure the document with YAML frontmatter followed by content:
     ```markdown
     ---
     date: [Current date and time with timezone in ISO format]
     researcher: [Researcher name from thoughts status]
     git_commit: [Current commit hash]
     branch: [Current branch name]
     repository: [Repository name]
     topic: "[User's Question/Topic]"
     tags: [research, codebase, tools, libraries, relevant-component-names]
     status: complete
     last_updated: [Current date in YYYY-MM-DD format]
     last_updated_by: [Researcher name]
     ---

     # Research: [User's Question/Topic]

     **Date**: [Current date and time with timezone from step 4]
     **Researcher**: [Researcher name from thoughts status]
     **Git Commit**: [Current commit hash from step 4]
     **Branch**: [Current branch name from step 4]
     **Repository**: [Repository name]

     ## Research Question
     [Original user query]

     ## Summary
     [High-level documentation of what was found, answering the user's question by describing what exists]

     ## Detailed Findings

     ### [Component/Area 1]
     - Description of what exists ([file.ext:line](link))
     - How it connects to other components
     - Current implementation details (without evaluation)

     ### [Component/Area 2]
     ...

     ## Code References
     - `path/to/file.py:123` - Description of what's there
     - `another/file.ts:45-67` - Description of the code block

     ## Architecture Documentation
     [Current patterns, conventions, and design implementations found in the codebase]

     ## Historical Context (from thoughts/)
     [Relevant insights from thoughts/ directory with references]
     - `thoughts/shared/something.md` - Historical decision about X
     - `thoughts/jbrooksbartlett/notes.md` - Past exploration of Y

     ## Related Research
     [Links to other research documents in thoughts/shared/research/]

     ## Open Questions
     [Any areas that need further investigation]
     ```

8. **Add GitHub permalinks (if applicable):**
   - Check if on main branch or if commit is pushed: `git branch --show-current` and `git status`
   - If on main/master or pushed, generate GitHub permalinks:
     - Get repo info: `gh repo view --json owner,name`
     - Create permalinks: `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`
   - Replace local file references with permalinks in the document

9. **Sync and present findings:**
   - Write the output to the `thoughts` directory (it should already exist from an earlier step)
   - Present a concise summary of findings to the user
   - Include key file references for easy navigation
   - **MANDATORY:** After creating the plan file, ask the user: "Would you like to ask follow-up questions or do you need any clarifications?"

10. **Handle follow-up questions:**
   - If the user has follow-up questions, append to the same research document
   - Update the frontmatter fields `last_updated` and `last_updated_by` to reflect the update
   - Add `last_updated_note: "Added follow-up research for [brief description]"` to frontmatter
   - Add a new section: `## Follow-up Research [timestamp]`
   - Spawn new sub-agents as needed for additional investigation
   - Continue updating the document and syncing

## Iteration Loop Structure

This section clarifies how the iterative research loop works across steps 3, 4, and 5.

**Initial research phase (Iteration 0):**
1. Step 2: Identify questions and create initial TODO list
2. Step 3: Spawn Batch 1 agents (mark as "in_progress")
3. Step 3.5: Wait for Batch 1 to complete (mark as "completed"), spawn Batch 2 if needed, wait for completion
4. Step 3.5: Add synthesis and validation tasks to TODO list (both "pending")
5. Step 4: Mark synthesis as "in_progress", synthesize findings, mark as "completed"
6. Step 5: Mark validation as "in_progress", validate completeness

**If all questions adequately answered (Iteration 0 success):**
1. Step 5: Mark validation as "completed"
2. Step 6: Proceed to metadata gathering

**If gaps found (Iteration N, where N = 1 or 2):**
1. Step 5: Mark validation as "completed"
2. Step 5: **Update TODO list:**
   - Mark or remove previous synthesis task (it needs revision with new data)
   - Add new agent spawn tasks (status: "pending")
   - Add new synthesis task for iteration N (status: "pending")
   - Add new validation task for iteration N (status: "pending")
3. Step 3 (repeat): Spawn new agents to fill gaps (mark as "in_progress")
4. Step 3.5 (repeat): Wait for new agents to complete (mark as "completed")
5. Step 4 (repeat): Mark synthesis iteration N as "in_progress", re-synthesize with all findings (old + new), mark as "completed"
6. Step 5 (repeat): Mark validation iteration N as "in_progress", validate again
7. If still gaps and N < 2: Repeat from step 3
8. If N = 2 or all questions answered: Proceed to step 6

**Rules:**
- Synthesis can only start when all current-phase agents are completed
- Validation can only start when synthesis is completed
- New agents can only spawn after validation identifies gaps
- Maximum 2 iterations total (iteration 0, 1)

## State Machine for Research Flow

Visual representation of the research process state transitions:

```
┌─────────────────────────┐
│ Questions Identified    │
│ (Step 2)                │
└────────────┬────────────┘
             │
             │ Create TODO: agents as "pending"
             │ Do not add synthesis yet
             v
┌─────────────────────────┐
│ Spawn Agents (Step 3)   │◄────────────────┐
│ Mark agents "in_progress"│                 │
└────────────┬────────────┘                  │
             │                                │
             v                                │
┌─────────────────────────┐                  │
│ All Agents Complete?    │                  │
│ (Step 3.5 Checkpoint)   │                  │
└────────────┬────────────┘                  │
             │ No: wait                       │
             │ Yes: mark "completed"          │
             v                                │
┌─────────────────────────┐                  │
│ Need Batch 2 Analyzers? │                  │
│ (Step 3.5)              │                  │
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
│ "in_progress" (Step 4)  │                  │
└────────────┬────────────┘                  │
             │                                │
             v                                │
┌─────────────────────────┐                  │
│ Synthesize Results      │                  │
│ (Step 4)                │                  │
└────────────┬────────────┘                  │
             │                                │
             │ Mark "completed"               │
             v                                │
┌─────────────────────────┐                  │
│ Mark Validation         │                  │
│ "in_progress" (Step 5)  │                  │
└────────────┬────────────┘                  │
             │                                │
             v                                │
┌─────────────────────────┐                  │
│ Validate Completeness   │                  │
│ (Step 5)                │                  │
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
│Generate   │  │Update TODO:             │  │
│Document   │  │- Mark validation done   │  │
│(Step 6)   │  │- Remove/revise synthesis│  │
│           │  │- Add new agent tasks    │  │
│           │  │- Add new synthesis task │  │
│           │  │- Add new validation task│──┘
│           │  │Mark new agents "pending"│
└───────────┘  └─────────────────────────┘
                Increment iteration N
                Return to "Spawn Agents"
```

**Key State Transitions:**
- `pending` → `in_progress` → `completed` for each task
- Synthesis stays `pending` until all agents are `completed`
- If gaps found, new iteration creates new pending tasks
- Synthesis is not marked `completed` if gaps require more research

## Important notes:
- Always use parallel Task agents to maximize efficiency and minimize context usage
- Always run fresh research - never rely solely on existing research documents
- The thoughts/ directory provides historical context to supplement live findings
- Focus on finding concrete file paths and line numbers for developer reference
- Research documents should be self-contained with all necessary context
- Each sub-agent prompt should be specific and focused on read-only documentation operations
- Document cross-component connections and how systems interact
- Include temporal context (when the research was conducted)
- Link to GitHub when possible for permanent references
- Keep the main agent focused on synthesis, not deep file reading
- Have sub-agents document examples and usage patterns as they exist
- Explore all of thoughts/ directory, not just research subdirectory
- You and all sub-agents are documentarians, not evaluators
- Continue the clarification loop in Step 10 from above until the user explicitly confirms the research is complete
- Document what IS, not what SHOULD BE
- Only describe the current state of the codebase and/or the tool/library
- **File reading**: Read mentioned files fully (no limit/offset) before spawning sub-tasks (unless otherwise instructed)
- **Step ordering**: Follow the numbered steps exactly
  - Read mentioned files first before spawning sub-tasks (step 1)
  - Wait for all sub-agents to complete before synthesizing (step 4)
  - Validate research completeness before proceeding (step 5 - may loop back to step 3)
  - Gather metadata before writing the document (step 6 before step 7)
  - Avoid writing the research document with placeholder values
- **Path handling**:
  - Avoid changing jbrooksbartlett/ to shared/ or vice versa - preserve the exact directory structure
  - This ensures paths are correct for editing and navigation
- **Frontmatter consistency**:
  - Always include frontmatter at the beginning of research documents
  - Keep frontmatter fields consistent across all research documents
  - Update frontmatter when adding follow-up research
  - Use snake_case for multi-word field names (e.g., `last_updated`, `git_commit`)
  - Tags should be relevant to the research topic and components studied
