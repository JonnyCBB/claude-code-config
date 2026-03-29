---
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

Tip: You can also invoke this command with a ticket file directly: `/create_plan ~/.claude/thoughts/$USER/tickets/eng_1234.md`
For deeper analysis, try: `/create_plan think deeply about ~/.claude/thoughts/$USER/tickets/eng_1234.md`
```

Then wait for the user's input.

## Process Steps

### Step 1: Context Gathering & Initial Analysis

1. **Read all mentioned content (e.g. files, webpages) immediately and FULLY**:
   - Ticket files (e.g., `~/.claude/thoughts/$USER/tickets/eng_1234.md`)
   - Research documents
   - Related implementation plans
   - Any JSON/data files mentioned
   - **IMPORTANT**: Use the Read tool WITHOUT limit/offset parameters to read entire files (unless the user explicitly states otherwise (e.g. the file might be too large))
   - **CRITICAL**: DO NOT spawn sub-tasks before reading these files yourself in the main context
   - **NEVER** read files partially - if a file is mentioned, read it completely (unless directed otherwise)

2. **Spawn initial research tasks to gather context**:
   Before asking the user any questions, use specialized agents to research in parallel:
   - Use the **codebase-explorer** agent to find all files related to the ticket/task and understand how the current implementation works
   - If relevant, use the **thoughts-explorer** agent to find and analyze any existing thoughts documents about this feature
   - Use the **web-search-researcher** agent for external documentation and resources

   These agents will:
   - Find relevant source files, configs, and tests
   - Identify the specific directories to focus on (e.g., if WUI is mentioned, they'll focus on humanlayer-wui/)
   - Trace data flow and key functions
   - Return detailed explanations with file:line references
   - Find relevant documentation and conversations

2b. **Check for operational context**:

- If an operational context document is provided (as a file path argument), read it fully
- If no operational context is provided AND the task references specific service/component names:
  - Note to user: "This task involves [service]. Consider gathering production data for operational context."
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
   - Document each autonomous decision:
     ```
     Autonomous Decision [N]:
     Question: [what you would have asked]
     Decision: [what you chose]
     Principle applied: [which decision principle guided this choice]
     Rationale: [why this is the best choice given available evidence]
     ```
   - Proceed directly to Step 2 (Domain Detection) with these decisions

### Step 2: Detect Domains for Specialized Research

After initial codebase research completes, analyze findings for domain-specific patterns.

**Scan the ticket, research findings, and codebase for domain patterns:**

| Domain              | Patterns Found | Expert Agent             | Include in Research? |
| ------------------- | -------------- | ------------------------ | -------------------- |
| Data Annotations    | [matches]      | data-annotation-reviewer | Yes/No               |
| ML Pipelines        | [matches]      | ml-pipeline-reviewer     | Yes/No               |
| RCS/Experimentation | [matches]      | experimentation-expert   | Yes/No               |

**Output for user:**

```
## Domains Detected for Planning

Based on ticket and codebase analysis:
- ✓ [Domain]: Found "[pattern]" → Will include [agent-name] in research
- ✗ [Domain]: Not detected
```

**Spawn domain experts in parallel with standard research agents:**

For each detected domain, spawn the corresponding expert with this prompt:

```
Provide [DOMAIN] expertise for planning this implementation:

## Task Context
{{TICKET_SUMMARY}}

## Codebase Findings
{{INITIAL_RESEARCH_FINDINGS}}

## Research Focus
- Identify [DOMAIN]-specific considerations for this task
- Suggest [DOMAIN] patterns and approaches to follow
- Highlight [DOMAIN] risks, constraints, or best practices
- Reference [DOMAIN] documentation and examples
- Note any [DOMAIN]-specific testing requirements
```

Include domain expert findings in the plan's research section.

**Required: Agent Type Verification**

After detecting domains, create an explicit agent contract:

```
## Agent Type Verification

Based on the domains detected above, I will spawn the following agents:

**Standard research agents:**
- codebase-explorer
- thoughts-explorer (if applicable)
- web-search-researcher (if applicable)

**Domain-based agents** (added based on detection):
- [For each domain with "Yes": [Domain] → [agent-name]]

**Full agent list:**
1. [agent-1]
2. [agent-2]
...

Total agents to spawn: [N]

⚠️ This list is my CONTRACT.
```

Reference: See `commands/shared/agent-verification-pattern.md` for the full pattern.

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

Reference: See `commands/shared/agent-verification-pattern.md` for the full pattern.

3. **Spawn parallel sub-tasks for comprehensive research**:
   - Create multiple Task agents to research different aspects concurrently
   - Use the right agent for each type of research:

   **For codebase investigation:**
   - **codebase-explorer** - To find files, understand implementation details, and find similar features to model after (specify "where is X?", "how does X work?", or "show me examples of X" in the prompt)

   **For external documentation and resources:**
   - **web-search-researcher** - To find:
     - Official documentation for open-source libraries or external APIs
     - Best practices and patterns for technologies used in the task

   **For historical context:**
   - **thoughts-explorer** - To find and analyze any research, plans, or decisions about this area

   Each agent knows how to:
   - Find the right files and code patterns
   - Identify conventions and patterns to follow
   - Look for integration points and dependencies
   - Return specific file:line references
   - Find tests and examples

   **MANDATORY (run in parallel with above): Search for existing reusable patterns**

   As part of the parallel sub-task spawning, ALWAYS include a dedicated task to find existing abstractions:
   - Use **codebase-explorer** with prompts like:
     - "Find all abstract classes, interfaces, or base classes related to [component type]"
     - "Find what classes extend or implement the same interface as [similar existing feature]"
     - "Search for `abstract class`, `interface`, `Protocol`, `trait` in [relevant directory]"

   **What to look for:**
   - Abstract classes that handle boilerplate (e.g., `AbstractGrpcTool`, `BaseHandler`)
   - Interfaces that define contracts for the type of component you're building
   - Existing implementations that can be modeled after
   - Factory patterns, builder patterns, or other design patterns in use

   **If reusable patterns are found:**
   - Document them explicitly in your findings
   - Evaluate if the new implementation should extend/implement them
   - If the existing pattern conflicts with a prior research doc's approach, flag this for discussion

4. **Wait for ALL sub-tasks to complete** before proceeding

5. **Present findings and design options**:

   ```
   Based on my research, here's what I found:

   **Current State:**
   - [Key discovery about existing code]
   - [Pattern or convention to follow]

   **Design Options:**
   1. [Option A] - [pros/cons]
   2. [Option B] - [pros/cons]

   **Open Questions:**
   - [Technical uncertainty]
   - [Design decision needed]

   Which approach aligns best with your vision?
   ```

   **If in NON_INTERACTIVE mode:**
   - Do NOT present design options to the user
   - Evaluate each option using decision-principles (safety → evidence → simplicity → scope)
   - Select the best option and document the decision (same format as Step 1 autonomous decisions)
   - Proceed directly to Step 4 (Plan Structure)

**Apply Decision Principles**: When evaluating design options and resolving open questions,
reference the `decision-principles` skill (`~/.claude/skills/decision-principles/SKILL.md`).
Follow the decision workflow: safety → evidence → simplicity → scope → latency → precedent.
Use principles to make recommendations rather than deferring all choices to the user.

### Step 4: Plan Structure Development

Once aligned on approach:

1. **Create initial plan outline**:

   ```
   Here's my proposed plan structure:

   ## Overview
   [1-2 sentence summary]

   ## Implementation Phases:
   1. [Phase name] - [what it accomplishes]
   2. [Phase name] - [what it accomplishes]
   3. [Phase name] - [what it accomplishes]

   Does this phasing make sense? Should I adjust the order or granularity?
   ```

2. **Get feedback on structure** before writing details

   **If in NON_INTERACTIVE mode:**
   - Skip presenting the structure for feedback
   - Proceed directly to Step 5 (Detailed Plan Writing)

### Step 5: Detailed Plan Writing

After structure approval:

1. **Write the plan** to `~/.claude/thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX-description.md`
   - Format: `YYYY-MM-DD-ENG-XXXX-description.md` where:
     - YYYY-MM-DD is today's date
     - ENG-XXXX is the ticket number (omit if no ticket)
     - description is a brief kebab-case description
   - Examples:
     - With ticket: `2025-01-08-ENG-1478-parent-child-tracking.md`
     - Without ticket: `2025-01-08-improve-error-handling.md`
2. **Use this template structure**:

````markdown
# [Feature/Task Name] Implementation Plan

## Overview

[Brief description of what we're implementing and why]

## Current State Analysis

[What exists now, what's missing, key constraints discovered]

## Desired End State

[A Specification of the desired end state after this plan is complete, and how to verify it]

### Key Discoveries:

- [Important finding with file:line reference]
- [Pattern to follow]
- [Constraint to work within]

## What We're NOT Doing

[Explicitly list out-of-scope items to prevent scope creep]

## Implementation Approach

[High-level strategy and reasoning]

## Operational Context

{{Populated from the operational context document. If no operational context was gathered, state:
"No operational context gathered — task does not involve a specific service."}}

### Service Health Baseline

[from ops context document]

### Dependency Constraints

[from ops context document — dependency table with headroom analysis]

### Capacity Assessment

[from ops context document — resource utilization]

### Risk Factors

[from ops context document — risk assessment]

### How Operational Context Informs This Plan

[Agent uses the decision-mapping table to explain which operational constraints
affect specific phases of the plan]

## Existing Patterns Analysis

**REQUIRED**: Document existing abstractions/patterns that were considered for this implementation.

### Patterns Found:

| Pattern                         | Location                | Usage Count       | Applicable? |
| ------------------------------- | ----------------------- | ----------------- | ----------- |
| [Abstract class/Interface name] | `path/to/file.ext:line` | X existing usages | Yes/No      |
| ...                             | ...                     | ...               | ...         |

### Decision:

- **Will use**: [Pattern name] because [reason]
- **Will NOT use**: [Pattern name] because [reason - e.g., doesn't fit our use case because X]

### Deviation from Prior Research (if applicable):

> **Note**: The research document `~/.claude/thoughts/shared/research/YYYY-MM-DD-xxx.md` proposed [approach X],
> but based on pattern analysis, this plan uses [approach Y] instead because [reason].
>
> Key differences:
>
> - Research proposed: [original approach]
> - This plan uses: [new approach leveraging existing pattern]
> - Rationale: [why the pattern-based approach is better]

---

## Phase 1: [Descriptive Name]

### Overview

[What this phase accomplishes]

### Changes Required:

#### 1. [Component/File Group]

**File**: `path/to/file.ext`
**Changes**: [Summary of changes]

```[language]
// Specific code to add/modify
```

#### Proposed directory structure chnages

```
<TOP_LEVEL_DIR>/
├── <SECOND_LEVEL_DIR_1>/
│   └── <NEW_FILE_1>                          # NEW: <description of changes>
├── <SECOND_LEVEL_DIR_1>/
│   └── <NEW_FILE_2>                          # NEW: <description of changes>
└── <MODIFIED_FILE>                           # MODIFIED: <description of changes>
│
...
```

### Success Criteria:

#### Automated Verification:

- [ ] Type checking passes: <COMMAND_FOR_RUNNING_TYPE_CHECKING> e.g. `mypy`
- [ ] Linting passes: <COMMAND_FOR_RUNNING_TYPE_CHECKING> if applicable e.g. `flake8`, `ruff lint`
- [ ] Tests pass: <COMMAND_FOR_RUNNING_TESTS> e.g. `mvn test`, `sbt test`
- [ ] Formatting: <COMMAND_FOR_RUNNING_FORMATTING> e.g. `mvn fmt:format`, `sbt scalafmtAll`

#### Manual Verification:

- [ ] Feature works as expected when tested via UI
- [ ] Performance is acceptable under load
- [ ] Edge case handling verified manually
- [ ] No regressions in related features

---

## Phase 2: [Descriptive Name]

[Similar structure with both automated and manual success criteria...]

---

## Testing Strategy

### Unit Tests:

- [What to test]
- [Key edge cases]

### Integration Tests:

- [End-to-end scenarios]

### Manual Testing Steps:

1. [Specific step to verify feature]
2. [Another verification step]
3. [Edge case to test manually]

## Performance Considerations

[Any performance implications or optimizations needed]

## Migration Notes

[If applicable, how to handle existing data/systems]

## References

- Original ticket: [Link to actual Jira ticket if given otherwise link to ticket in `~/.claude/thoughts` directory] `~/.claude/thoughts/$USER/tickets/eng_XXXX.md`
- Related research: `~/.claude/thoughts/shared/research/[relevant].md`
- Similar implementation: `[file:line]`
````

### Step 6: Sync and Review

**If in NON_INTERACTIVE mode:**

- Write the plan to the standard path (`~/.claude/thoughts/shared/plans/YYYY-MM-DD-description.md`)
- Append the `## Autonomous Decisions` section documenting all decisions made during planning
- Do NOT ask for review or iterate
- The plan is final

**If in interactive mode (default):**

1. **Present the draft plan location**:
   - Create `~/.claude/thoughts/shared/plans/` directory if it doesn't exist already.

   ```
   I've created the initial implementation plan at:
   `~/.claude/thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX-description.md`

   Please review it and let me know:
   - Are the phases properly scoped?
   - Are the success criteria specific enough?
   - Any technical details that need adjustment?
   - Missing edge cases or considerations?
   ```

2. **Iterate based on feedback** - be ready to:
   - Add missing phases
   - Adjust technical approach
   - Clarify success criteria (both automated and manual)
   - Add/remove scope items

3. **Continue refining** until the user is satisfied

## Important Guidelines

1. **Be Skeptical**:
   - Question vague requirements
   - Identify potential issues early
   - Ask "why" and "what about"
   - Don't assume - verify with code

2. **Be Interactive**:
   - Don't write the full plan in one shot
   - Get buy-in at each major step
   - Allow course corrections
   - Work collaboratively

3. **Be Thorough**:
   - Read all context files COMPLETELY before planning
   - Research actual code patterns using parallel sub-tasks
   - Include specific file paths and line numbers
   - Write measurable success criteria with clear automated vs manual distinction

4. **Be Practical**:
   - Focus on incremental, testable changes
   - Consider migration and rollback
   - Think about edge cases
   - Include "what we're NOT doing"

5. **Track Progress**:
   - Use TodoWrite to track planning tasks
   - Update todos as you complete research
   - Mark planning tasks complete when done

6. **No Open Questions in Final Plan**:
   - If you encounter open questions during planning, STOP
   - Research or ask for clarification immediately
   - Do NOT write the plan with unresolved questions
   - The implementation plan must be complete and actionable
   - Every decision must be made before finalizing the plan

7. **Leverage Existing Patterns**:
   - ALWAYS search for abstract classes, interfaces, and base classes before designing new components
   - If an existing pattern has 3+ usages, prefer extending it over creating something new
   - If your approach differs from a prior research doc due to pattern discovery, document this explicitly
   - The "Existing Patterns Analysis" section is REQUIRED in every implementation plan

8. **Use Operational Context**:
   - When operational context is available, reference it when designing phases
   - Verify latency budget: current P99 + new call P99 < upstream timeout
   - Check error budget headroom before choosing deployment strategy
   - Adjust resource requests if current utilization is high

## Success Criteria Guidelines

**Always separate success criteria into two categories:**

1. **Automated Verification** (can be run by execution agents):
   - Commands that can be run: `make test`, `sbt scalafmtAll`, etc.
   - Specific files that should exist
   - Code compilation/type checking
   - Automated test suites

2. **Manual Verification** (requires human testing):
   - UI/UX functionality
   - Performance under real conditions
   - Edge cases that are hard to automate
   - User acceptance criteria

**Format example:**

```markdown
### Success Criteria:

#### Automated Verification:

- [ ] Database migration runs successfully: `make migrate`
- [ ] All unit tests pass: `go test ./...`
- [ ] No linting errors: `golangci-lint run`
- [ ] API endpoint returns 200: `curl localhost:8080/api/new-endpoint`

#### Manual Verification:

- [ ] New feature appears correctly in the UI
- [ ] Performance is acceptable with 1000+ items
- [ ] Error messages are user-friendly
- [ ] Feature works correctly on mobile devices
```

## Common Patterns

### For Database Changes:

- Start with schema/migration
- Add store methods
- Update business logic
- Expose via API
- Update clients

### For New Features:

- Research existing patterns first
- Start with data model
- Build backend logic
- Add API endpoints
- Implement UI last

### For Refactoring:

- Document current behavior
- Plan incremental changes
- Maintain backwards compatibility
- Include migration strategy

## Sub-task Spawning Best Practices

When spawning research sub-tasks:

1. **Spawn multiple tasks in parallel** for efficiency
2. **Each task should be focused** on a specific area
3. **Provide detailed instructions** including:
   - Exactly what to search for
   - Which directories to focus on
   - What information to extract
   - Expected output format
4. **Be EXTREMELY specific about directories**:
   - Never use generic terms like when more specific terms are available
   - Include the full path context in your prompts
5. **Specify read-only tools** to use
6. **Request specific file:line references** in responses
7. **Wait for all tasks to complete** before synthesizing
8. **Verify sub-task results**:
   - If a sub-task returns unexpected results, spawn follow-up tasks
   - Cross-check findings against the actual codebase
   - Don't accept results that seem incorrect

Example of spawning multiple tasks:

```python
# Spawn these tasks concurrently:
tasks = [
    Task("Research database schema", db_research_prompt),
    Task("Find API patterns", api_research_prompt),
    Task("Investigate UI components", ui_research_prompt),
    Task("Check test patterns", test_research_prompt)
]
```

## Example Interaction Flow

```
User: /implementation_plan
Assistant: I'll help you create a detailed implementation plan...

User: We need to add parent-child tracking for Claude sub-tasks. See ~/.claude/thoughts/$USER/tickets/eng_1478.md
Assistant: Let me read that ticket file completely first...

[Reads file fully]

Based on the ticket, I understand we need to track parent-child relationships for Claude sub-task events in the hld daemon. Before I start planning, I have some questions...

[Interactive process continues...]
```
