---
name: create-plan-tdd
description: >
  Create TDD-aware implementation plans with wave-based parallelism and multi-persona
  review. Follows Red-Green-Refactor methodology per task, groups tasks into dependency-based
  waves for parallel execution, and validates plans through 4 specialized reviewer personas
  before finalization. Trigger phrases (1) "create a TDD plan" (2) "plan with tests first"
  (3) "create-plan-tdd" (4) "TDD implementation plan" (5) "test-driven plan". Use when the
  user wants a plan that enforces test-first development, needs wave-based parallelization
  of implementation tasks, or wants built-in plan review by specialized personas.
---

# TDD Implementation Plan

Create detailed implementation plans through an interactive, iterative process using
Test-Driven Development methodology. Tasks follow Red-Green-Refactor cycles, are grouped
into dependency-based waves for parallel execution, and are validated by specialized
reviewer personas.

## Mode Detection

Parse `$ARGUMENTS` for flags and input:

- `--non-interactive` flag: skip all interactive gates, use `${CLAUDE_PLUGIN_ROOT}/skills/decision-principles/SKILL.md` for autonomous decisions, log them in `## Autonomous Decisions` at plan end
- File path argument: read immediately and begin
- No arguments: prompt user (see Initial Response)

## Initial Response

**Non-interactive**: skip prompt, read provided file, begin Step 1.

If a file path or ticket reference was provided, read it FULLY and begin.

If no parameters provided, respond with:

```
I'll help you create a TDD implementation plan. Let me start by understanding what we're building.

Please provide:
1. The task/ticket description (or reference to a ticket file)
2. Any relevant context, constraints, or specific requirements
3. Links to related research or previous implementations

I'll analyze this, design a wave-based TDD plan, and run it through multi-persona review.
```

Then wait for user input.

## Step 1: Context Gathering & Initial Analysis

1. **Read all mentioned files FULLY** (tickets, research docs, related plans, data files). Use Read without limit/offset. Read files yourself before spawning agents.

2. **Spawn initial research agents in parallel**:
   - **codebase-explorer**: find files related to the task, understand current implementation
   - **thoughts-explorer**: find existing thoughts documents about this feature (if applicable)
   - **web-search-researcher**: external documentation and resources (if applicable)
   - **test-pattern-researcher** (TDD-specific): search for existing test patterns, frameworks, fixtures, helpers, CI test commands, and test infrastructure (conftest.py, test utilities, shared fixtures, test base classes)

2b. **Check for operational context**:

- If an operational context document is provided (as a file path argument), read it fully
- If no operational context is provided AND the task references specific service/component names:
  - Note to user: "This task involves [service]. Consider gathering operational context for production data."
- If the task does not involve specific services (e.g., pure refactoring, documentation), skip

3. **Read all files identified by research agents** FULLY into main context.

4. **Analyze and verify understanding**: cross-reference requirements with code, identify discrepancies, note assumptions.

5. **Present understanding and focused questions**:

   ```
   Based on the ticket and my research, I understand we need to [summary].

   I've found:
   - [Current implementation detail with file:line reference]
   - [Test infrastructure available: frameworks, fixtures, helpers]
   - [Relevant pattern or constraint]

   Questions my research couldn't answer:
   - [Specific question requiring human judgment]
   ```

   Only ask questions you genuinely cannot answer through investigation. _Non-interactive: apply decision-principles for autonomous answers, document each decision, proceed to Step 2._

## Step 2: Domain & Language Detection

After initial research completes, analyze findings for domain and language patterns.

**Language detection** (TDD-specific): Detect languages using `${CLAUDE_PLUGIN_ROOT}/commands/shared/language-agent-registry.md`. This identifies test file patterns, test reviewers, and test frameworks for each language in scope.

**Agent Type Verification**: Create explicit agent contract per `${CLAUDE_PLUGIN_ROOT}/commands/shared/agent-verification-pattern.md`. Include both standard research agents and language-based test agents.

## Step 3: Research & Discovery

1. **Pre-Spawn Verification**: output verification table matching contract per agent-verification-pattern.

2. **Spawn parallel agents for comprehensive research**:
   - Standard agents (codebase-explorer, thoughts-explorer, web-search-researcher) as warranted
   - Domain experts for each detected domain
   - **Mandatory TDD agents**:
     - Search for existing test patterns (test frameworks, fixture conventions, assertion styles, mocking approaches)
     - Find existing test infrastructure (conftest.py, test utilities, shared fixtures, test base classes, test factories)
     - Identify CI test commands and test configuration
   - **Mandatory pattern search**: find existing abstractions (abstract classes, interfaces, base classes) for reuse
   - **Mandatory guideline discovery**: search for coding standards/guidelines files (CONTRIBUTING.md, .editorconfig, style guides, CLAUDE.md rules, lint configs) in the target repo. Summarize findings for inclusion in the plan's "Coding Guidelines" section.

3. **Wait for ALL agents to complete**.

4. **Present findings and design options**:

   ```
   **Current State:** [discoveries]
   **Test Infrastructure:** [frameworks, fixtures, helpers found]
   **Design Options:**
   1. [Option A] - [pros/cons]
   2. [Option B] - [pros/cons]

   **Recommended**: [option] because [rationale per decision-principles]
   ```

   _Non-interactive: auto-select best option using decision-principles, document decision, proceed to Step 4._

## Step 4: Wave Analysis & TDD Strategy

Analyze task dependencies to identify parallelizable groups and design the TDD approach.

See `references/wave-analysis-guide.md` for detailed wave analysis instructions.

Key activities:

1. **Define complete file structure** -- map ALL new and modified files with purpose, responsibility, and interface description. This constrains task decomposition (see `## File Structure` in plan template)
2. List all implementation tasks from the design, mapping each to files in the file structure
3. Map dependencies between tasks
4. Design **Wave 0** (test infrastructure) -- shared fixtures, helpers, base classes needed before any feature work
5. Group remaining tasks into waves where tasks within a wave have no mutual dependencies
6. For each task, define the RED/GREEN/REFACTOR cycle
7. Present wave structure to user for approval

_Non-interactive: proceed with analysis, no approval gate._

## Step 5: Plan Structure Development

Present wave-based outline with TDD structure:

```
## Overview
[1-2 sentence summary]

## Waves:
- Wave 0: Test Infrastructure - [N tasks] - shared fixtures and helpers
- Wave 1: [Theme] - [N tasks] - [TDD cycle summary]
- Wave 2: [Theme] - [N tasks] - [TDD cycle summary]

Does this phasing make sense? Should I adjust?
```

Get feedback on structure. _Non-interactive: proceed directly to Step 6._

## Step 6: Detailed Plan Writing

Write plan to `~/.claude/thoughts/shared/plans/YYYY-MM-DD-description.md`.

Use the template from `references/plan-template.md`. The plan includes:

- Wave analysis and dependency graph
- Wave 0 (test infrastructure setup)
- Operational Context section (populated from ops context document, or "N/A — not service-specific")
- Per-task RED/GREEN/REFACTOR cycles with specific test cases, implementation approach, and refactoring targets
- Parallelization plan showing which tasks can run concurrently
- Existing patterns analysis (required)
- Success criteria split into automated and manual verification

The plan template must include:

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

[How operational constraints affect specific waves and tasks in the TDD plan]

Create `~/.claude/thoughts/shared/plans/` if it does not exist.

## Step 7: Plan Review Loop

Run multi-persona review to validate the plan before finalization.

See `references/review-personas.md` for persona definitions and selection criteria.

1. **Classify the plan**: determine scope (small/medium/large), risk (low/medium/high), and type (new feature/refactor/migration/infrastructure)

2. **Select reviewers** based on classification. Always include the TDD Methodology reviewer. Add others based on plan characteristics.

3. **Spawn reviewer agents in parallel**. Each reviewer evaluates the plan from their perspective and returns categorized feedback:
   - **Must Address**: issues that would cause the plan to fail or violate TDD principles
   - **Should Consider**: improvements that would strengthen the plan
   - **Minor**: style, wording, or optional enhancements

4. **Synthesize feedback** across all reviewers. Deduplicate overlapping concerns.

5. **Iterate**:
   - Revise plan to address all "Must Address" items
   - Re-run review on revised sections (max 3 iterations)
   - Auto-approve when no "Must Address" items remain

_Non-interactive: single review pass, auto-resolve feedback using decision-principles, document resolutions._

_Interactive: present synthesized feedback to user, iterate collaboratively on revisions._

## Step 8: Sync and Review

**Non-interactive**: plan is final after review loop. Append `## Autonomous Decisions` section. Done.

**Interactive**:

1. Present plan location and review results
2. Iterate based on user feedback (adjust phases, refine TDD cycles, modify waves)
3. Continue until user is satisfied

## Guidelines

- **Be skeptical**: question vague requirements, verify with code, identify issues early
- **Be interactive**: get buy-in at each step, allow course corrections (in interactive mode)
- **Be thorough**: read all context completely, research actual code patterns, include file:line references
- **Be practical**: incremental testable changes, consider migration and rollback
- **No open questions in final plan**: research or ask immediately, never leave unresolved questions
- **Leverage existing patterns**: search for abstract classes and interfaces before designing new components
- **Tests before code**: every task starts with RED (failing test), not implementation
- **Vertical slices**: each task delivers a complete test+implementation unit
- **Wave 0 first**: always establish shared test infrastructure before feature waves
- **Use operational context**: When available, verify latency budget (current P99 + new call P99 < upstream timeout), check error budget headroom before choosing deployment strategy, adjust resource requests if utilization is high

## Reference Files

- **`references/plan-template.md`** -- Read when writing the plan (Step 6). Contains the full TDD plan template with wave structure, per-task RED/GREEN/REFACTOR sections, and parallelization plan format.
- **`references/review-personas.md`** -- Read when running the review loop (Step 7). Defines the 4 reviewer personas, their selection criteria, feedback format, and iteration rules.
- **`references/wave-analysis-guide.md`** -- Read when doing wave analysis (Step 4). Contains dependency mapping methodology, Wave 0 design patterns, and wave grouping heuristics.

## Shared Registries (by path)

- `${CLAUDE_PLUGIN_ROOT}/commands/shared/language-agent-registry.md` -- language detection, test file patterns, test reviewers
- `${CLAUDE_PLUGIN_ROOT}/commands/shared/agent-verification-pattern.md` -- agent contract and verification checkpoints
