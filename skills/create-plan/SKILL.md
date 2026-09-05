---
name: create-plan
description: Create detailed implementation plans through an interactive, iterative process. Use when the user needs to plan a feature, refactor, or technical task before implementation.
argument-hint: [file-path] [--non-interactive]
---

# Implementation Plan

You are tasked with creating detailed implementation plans through an interactive, iterative process. You should be skeptical, thorough, and work collaboratively with the user to produce high-quality technical specifications.

## Mode Detection

Parse `$ARGUMENTS` for flags and input:

- If `$ARGUMENTS` contains `--non-interactive`: Set NON_INTERACTIVE mode
  - A file path argument is REQUIRED (the research document or ticket to plan from)
  - Skip all interactive gates:
    - Skip "Initial Response" default message (Step 1)
    - Skip "informed questions" (Step 1.5) — use best judgment instead
    - Skip "design options" presentation (Step 3.5) — choose the best option using decision-principles
    - Skip "plan structure feedback" (Step 4.2) — proceed with the structure
    - Skip "sync and review" loop (Step 6) — write the plan and finish
  - Use `~/.claude/skills/decision-principles/SKILL.md` for all autonomous decisions
  - Log decisions made autonomously in a `## Autonomous Decisions` section at the end of the plan
- If `$ARGUMENTS` does not contain `--non-interactive`: Behave exactly as before (interactive mode)

## Initial Response

**If in NON_INTERACTIVE mode:**

- Skip the default message
- Read the provided file path immediately and FULLY
- Begin the research process directly (proceed to Step 1: Context Gathering)

When this command is invoked:

1. **Check if parameters were provided**:
   - If a file path or ticket reference was provided as a parameter, skip the default message
   - Immediately read any provided files FULLY
   - Begin the research process

2. **If no parameters provided**, respond with:

```
I'll help you create a detailed implementation plan. Let me start by understanding what we're building.

Please provide:
1. The task/ticket description (or reference to a ticket file)
2. Any relevant context, constraints, or specific requirements
3. Links to related research or previous implementations

I'll analyze this information and work with you to create a comprehensive plan.

Tip: You can also invoke this skill with a ticket file directly: `/create-plan ~/.claude/thoughts/$USER/tickets/eng_1234.md`
For deeper analysis, try: `/create-plan think deeply about ~/.claude/thoughts/$USER/tickets/eng_1234.md`
```

Then wait for the user's input.

## Process Steps

### Step 1: Context Gathering & Initial Analysis

1. **Read all mentioned content (e.g. files, webpages) immediately and FULLY**:
   - Ticket files (e.g., `~/.claude/thoughts/$USER/tickets/eng_1234.md`)
   - Research documents
   - Related implementation plans
   - Any JSON/data files mentioned
   - **IMPORTANT**: Use the Read tool WITHOUT limit/offset parameters to read entire files (unless the user explicitly states otherwise)
   - **CRITICAL**: DO NOT spawn sub-tasks before reading these files yourself in the main context
   - **NEVER** read files partially - if a file is mentioned, read it completely (unless directed otherwise)

2. **Spawn initial research tasks to gather context**:
   Before asking the user any questions, use specialized agents to research in parallel:
   - Use the **codebase-explorer** agent to find all files related to the ticket/task and understand how the current implementation works
   - If relevant, use the **thoughts-explorer** agent to find and analyze any existing thoughts documents about this feature
   - Use the **web-search-researcher** agent if:
     - The task references internal tools, libraries, or infrastructure
     - Linked documents need authenticated access (Google Docs, Slides, etc.)
     - Slack discussions might provide relevant context or decisions
     - Examples in other internal repos might inform the approach
   - Use the **web-search-researcher** agent for external documentation and resources when there is no internal equivalent, or to supplement web-search-researcher findings with official docs

2b. **Check for operational context**:

- If an operational context document is provided (as a file path argument), read it fully
- If no operational context is provided AND the task references specific service/component names:
  - Gather what you can from the repo (dashboards config, SLO definitions, runbooks) and state explicitly what you could not establish
- If the task does not involve specific services (e.g., pure refactoring, documentation), skip operational context gathering

3. **Read all files identified by research tasks**:
   - After research tasks complete, read ALL files they identified as relevant
   - Read them FULLY into the main context
   - This ensures you have complete understanding before proceeding

4. **Analyze and verify understanding**:
   - Cross-reference the ticket requirements with actual code
   - Identify any discrepancies or misunderstandings
   - Note assumptions that need verification
   - Determine true scope based on codebase reality

5. **Present informed understanding and focused questions**:

   ```
   Based on the ticket and my research of the codebase, I understand we need to [accurate summary].

   I've found that:
   - [Current implementation detail with file:line reference]
   - [Relevant pattern or constraint discovered]
   - [Potential complexity or edge case identified]

   Questions that my research couldn't answer:
   - [Specific technical question that requires human judgment]
   - [Business logic clarification]
   - [Design preference that affects implementation]
   ```

   Only ask questions that you genuinely cannot answer through code investigation.

   **If in NON_INTERACTIVE mode:**
   - Do NOT present questions to the user
   - For each question you would have asked, apply decision-principles to choose the best answer
   - Document each autonomous decision
   - Proceed directly to Step 2 (Domain Detection) with these decisions

### Step 2: Detect Domains for Specialized Research

After initial codebase research completes, analyze findings for domain-specific patterns.

**Scan the ticket, research findings, and codebase for domain patterns:**

Follow the detection procedure in `skills/shared-references/domain-agent-registry.md` — check file names/paths against file triggers first, then check content for strong and corroborating signals.

**Output for user:**

```
## Domains Detected for Planning

Based on ticket and codebase analysis:
- ✓ [Domain]: Found "[pattern]" → Will include [agent-name] in research
- ✗ [Domain]: Not detected
```

**Spawn domain experts in parallel with standard research agents.**

**Required: Agent Type Verification**

After detecting domains, create an explicit agent contract.
Reference: See `skills/shared-references/agent-verification-pattern.md` for the full pattern.

### Step 3: Research & Discovery

After getting initial clarifications:

1. **If the user corrects any misunderstanding**:
   - DO NOT just accept the correction
   - Spawn new research tasks to verify the correct information
   - Read the specific files/directories they mention
   - Only proceed once you've verified the facts yourself

2. **Create a research todo list** using TodoWrite to track exploration tasks

**REQUIRED: Pre-Spawn Verification**

Before spawning, output verification table matching contract. If skipping any agent, provide reason and inform user.
Reference: See `skills/shared-references/agent-verification-pattern.md` for the full pattern.

3. **Spawn parallel sub-tasks for comprehensive research**:
   - Create multiple Task agents to research different aspects concurrently
   - Use the right agent for each type of research:

   **For codebase investigation:**
   - **codebase-explorer** - To find files, understand implementation details, and find similar features

   **For internal documentation and context:**
   - **web-search-researcher** - To find internal docs, implementations, and Slack discussions

   **For external documentation and resources:**
   - **web-search-researcher** - To find official docs, best practices, and upstream docs

   **For historical context:**
   - **thoughts-explorer** - To find and analyze any research, plans, or decisions about this area

   **MANDATORY (run in parallel with above): Search for existing reusable patterns**

   As part of the parallel sub-task spawning, ALWAYS include a dedicated task to find existing abstractions:
   - Use **codebase-explorer** with prompts like:
     - "Find all abstract classes, interfaces, or base classes related to [component type]"
     - "Find what classes extend or implement the same interface as [similar existing feature]"

   **If reusable patterns are found:**
   - Document them explicitly in your findings
   - Evaluate if the new implementation should extend/implement them
   - If the existing pattern conflicts with a prior research doc's approach, flag this for discussion

4. **Wait for ALL sub-tasks to complete** before proceeding

5. **Present findings and design options**:

   **If in NON_INTERACTIVE mode:**
   - Do NOT present design options to the user
   - Evaluate each option using decision-principles (safety → evidence → simplicity → scope)
   - Select the best option and document the decision
   - Proceed directly to Step 4 (Plan Structure)

**Apply Decision Principles**: When evaluating design options and resolving open questions,
reference the `decision-principles` skill (`~/.claude/skills/decision-principles/SKILL.md`).

### Step 4: Plan Structure Development

Once aligned on approach:

1. **Create initial plan outline**
2. **Get feedback on structure** before writing details

   **If in NON_INTERACTIVE mode:**
   - Skip presenting the structure for feedback
   - Proceed directly to Step 5 (Detailed Plan Writing)

### Step 5: Detailed Plan Writing

After structure approval:

1. **Write the plan** to `~/.claude/thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX-description.md`
2. **Use the standard template structure** with:
   - Overview
   - Current State Analysis
   - Desired End State
   - What We're NOT Doing
   - Implementation Approach
   - Operational Context
   - Existing Patterns Analysis (REQUIRED)
   - Phased implementation with Success Criteria (Automated + Manual)
   - Testing Strategy
   - Performance Considerations
   - Migration Notes
   - References

### Step 6: Sync and Review

**If in NON_INTERACTIVE mode:**

- Write the plan to the standard path
- Append the `## Autonomous Decisions` section
- The plan is final

**If in interactive mode (default):**

1. **Present the draft plan location**
2. **Iterate based on feedback**
3. **Continue refining** until the user is satisfied

## Important Guidelines

1. **Be Skeptical**: Question vague requirements, identify potential issues early
2. **Be Interactive**: Don't write the full plan in one shot, get buy-in at each step
3. **Be Thorough**: Read all context files COMPLETELY, include specific file:line references
4. **Be Practical**: Focus on incremental, testable changes
5. **Track Progress**: Use TodoWrite to track planning tasks
6. **No Open Questions in Final Plan**: Research or ask for clarification immediately
7. **Leverage Existing Patterns**: ALWAYS search for abstract classes, interfaces, and base classes before designing
8. **Use Operational Context**: Reference it when designing phases

## Success Criteria Guidelines

Always separate success criteria into:

1. **Automated Verification** (commands, tests, type checking, linting)
2. **Manual Verification** (UI, performance, edge cases, acceptance criteria)

## Common Patterns

### For Database Changes:

- Start with schema/migration → store methods → business logic → API → clients

### For New Features:

- Research patterns first → data model → backend → API → UI

### For Refactoring:

- Document current behavior → incremental changes → backwards compatibility → migration
