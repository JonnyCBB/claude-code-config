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
  - Skip all user confirmation steps (Step 2 confirmation, Step 12 follow-up, Step 13 loop)
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
- **Agent Type Verification** -- accountability list of all agent types to spawn
- **Complexity Classification** -- classify research as Simple/Medium/Complex to determine
  review scope in Step 7. Use the template from `references/plan-templates.md`.

Save the complete plan to `~/.claude/thoughts/shared/research_plans/YYYY-MM-DD-description-plan.md`
with YAML frontmatter (status: `approved` in non-interactive, `pending-approval` in interactive).

- **Interactive mode**: Present the plan and ask the user for confirmation. **Wait for
  explicit approval before proceeding to Step 3.**
- **NON_INTERACTIVE mode**: Skip confirmation, proceed directly to Step 3.

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

### Steps 4-6: Validate, Synthesize, and Iterate

Read `references/verification-and-iteration.md` for validation checklists, pre-synthesis
verification, completeness review format, iteration rules, and state machine diagram.

**Step 4 -- Wait and Validate Agent Completion:**

- Wait for all agents in the current batch to return results
- Show a Step 4 Validation Checklist cross-checking agent commitments from Step 2
- Re-spawn any failed agents with adjusted prompts
- Extract context for next batch; spawn next batch if the execution plan requires it
- After ALL research agents complete, add synthesis and validation tasks to TODO list

**Step 5 -- Synthesize Findings:**

- Run pre-synthesis agent verification (committed vs. actually spawned)
- Compile all sub-agent results; prioritize live codebase over historical context
- Connect findings across components; include file paths and line numbers
- Answer the user's questions with concrete evidence

**Step 6 -- Research Completeness Review (Iterative Loop):**

- For each question from Step 2, evaluate whether findings are sufficient
- Show a "Research Completeness Review (Iteration N of 2)" section to the user
- If all questions are adequately answered, proceed to Step 7
- If gaps remain, spawn targeted agents and repeat Steps 3-6
- **Maximum 2 iterations** of the 3-4-5-6 loop; after that, document gaps as Open Questions

### Step 7: Research Review Phase

Read `references/review-personas.md` for persona definitions, complexity-based selection
criteria, review prompt template, synthesis format, iteration mechanism, and auto-approve
threshold.

- **Simple complexity**: Skip this step. Proceed directly to Step 8.
- **Medium complexity**: Spawn Gap Analyst + Devil's Advocate + Source Critic (3 reviewers).
- **Complex**: Spawn all 5 reviewers (Gap Analyst, Devil's Advocate, Source Critic,
  Coherence Reviewer, Scope Guardian).

**Process:**

1. Spawn selected reviewer agents in parallel (model: sonnet). Pass each reviewer:
   the research plan (questions, success criteria, assumptions from Step 2) and the
   synthesized findings from Step 5.
2. Collect and synthesize feedback using the Review Synthesis Format.
3. Address "Must Address" items by revising the synthesized findings.
4. Re-run review if needed (max 2 iterations).
5. Auto-approve when: zero "Must Address" + zero disagreements + at most 2 "Should Consider."
6. Proceed to Step 8 (metadata gathering).

- **Interactive mode**: Present review synthesis to user; iterate collaboratively.
- **NON_INTERACTIVE mode**: Single review pass; auto-resolve "Must Address" items;
  document "Should Consider" items as advisory notes.

### Steps 8-11: Generate the Research Document

Read `references/document-template.md` for the metadata gathering script, file naming
conventions, research document template, GitHub permalink rules, and MCP call
documentation format.

**Step 8 -- Gather Metadata:** Run the metadata script; create the research directory
if it doesn't exist.

**Step 9 -- Generate Research Document:** Write the document to
`~/.claude/thoughts/shared/research/YYYY-MM-DD-description.md` using the template from
the reference file, populated with actual values from metadata and synthesized findings.

**Step 10 -- Add GitHub Permalinks:** If on main/master or commit is pushed, replace
local file references with `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`.

**Step 11 -- Include MCP Calls:** Document the queries, sources, and descriptions from
any web research so findings can be reproduced.

### Step 12: Sync and Present Findings

- Write the output to the `~/.claude/thoughts` directory
- Present a concise summary of findings to the user with key file references
- **Interactive mode**: Ask "Would you like to ask follow-up questions or do you need
  any clarifications?"
- **NON_INTERACTIVE mode**: Skip the follow-up prompt. The research is complete.

### Step 13: Handle Follow-Up Questions (Interactive Mode Only)

- **NON_INTERACTIVE mode**: Skip this step entirely.
- If the user has follow-up questions, append to the same research document
- Update frontmatter fields `last_updated`, `last_updated_by`, and add `last_updated_note`
- Add a new section: `## Follow-up Research [timestamp]`
- Spawn new sub-agents as needed for additional investigation
- Continue updating the document and syncing
- Continue the loop until the user explicitly confirms the research is complete

## Important Notes

- **Execution plan**: Follow the sequenced execution plan from Step 2; run independent
  questions in parallel but sequence dependent questions to pass context forward
- **Parallelism vs sequencing**: Default to parallelism when dependency is unclear; only
  sequence when earlier answers clearly improve later queries
- **File reading**: Always read mentioned files FULLY (no limit/offset) before spawning
  sub-tasks unless the user instructs otherwise
- **Ordering**: Follow the numbered steps in sequence. Read files first (Step 1), wait
  for all agents before synthesizing (Step 5), validate before proceeding (Step 6),
  run the review phase (Step 7) before gathering metadata. Skip Step 7 for Simple complexity.
  Gather metadata before writing (Step 8 before Step 9). Write with actual values, not
  placeholders.
- **Path handling**: Preserve the exact directory structure within ~/.claude/thoughts/
- **Frontmatter consistency**: Always include frontmatter at the beginning of research
  documents. Use snake_case for multi-word field names. Update frontmatter when adding
  follow-up research.
- You and all sub-agents are documentarians, not evaluators. Document what IS, not what
  SHOULD BE.
- Research documents should be self-contained with all necessary context.
- Always run fresh research -- never rely solely on existing research documents.

## Reference Files

- **`references/plan-templates.md`** -- Read in Step 2. Contains formatting templates for
  research questions, assumptions, success criteria, scope, execution plan, agent type
  verification, research plan file spec, and example decomposition.
- **`references/agent-guide.md`** -- Read in Step 3. Contains agent selection rules,
  pre-spawn verification table, batch execution rules, domain expert table, and agent
  usage tips.
- **`references/verification-and-iteration.md`** -- Read in Steps 4-6. Contains validation
  checklists, pre-synthesis verification, completeness review format, iteration rules,
  state machine diagram, assumption validation, and contradiction handling.
- **`references/review-personas.md`** -- Read in Step 7. Contains 5 reviewer personas
  (Gap Analyst, Devil's Advocate, Source Critic, Coherence Reviewer, Scope Guardian),
  complexity-based selection criteria, review prompt template, iteration mechanism,
  and auto-approve threshold.
- **`references/document-template.md`** -- Read in Steps 8-11. Contains metadata gathering
  script, file naming conventions, research document template, GitHub permalink rules,
  and MCP call documentation format.
