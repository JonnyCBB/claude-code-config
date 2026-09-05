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
- `--contract <path>` flag: path to a validation contract (`verification-contract.md`). When provided, each task must include a `fulfills` field mapping to contract assertion IDs, and a Coverage Matrix Check runs after plan writing to ensure every assertion is claimed by at least one task. If not provided, `fulfills` fields and the Coverage Matrix are omitted.
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

2. Agent spawning happens in Step 3 — use this step to read mentioned files fully and form initial questions before domain detection runs.

2b. **Check for operational context**:

- If an operational context document is provided (as a file path argument), read it fully
- If no operational context is provided AND the task references specific service/component names:
  - Spawn the `web-search-researcher` agent for the identified service(s)
  - OR note to user: "This task involves [service]. Running /operational-context to gather production data."
- If the task does not involve specific services (e.g., pure refactoring, documentation), skip

3. **Read all files identified by research agents** FULLY into main context.

4. **Analyze and verify understanding**: cross-reference requirements with code, identify discrepancies, note assumptions.

5. **Present understanding and focused questions**:

   First, output the context summary directly in the Claude Code UI:

   ```
   Based on the ticket and my research, I understand we need to [summary].

   I've found:
   - [Current implementation detail with file:line reference]
   - [Test infrastructure available: frameworks, fixtures, helpers]
   - [Relevant pattern or constraint]
   ```

   Then, for each question you genuinely cannot answer through investigation, prefer
   `AskUserQuestion` over free-form prompts:
   - **Discrete alternatives** (A vs B, yes/no, pick-one-of-N): use `AskUserQuestion`
     - `question`: the clarification phrased as a question ending in `?`
     - `header`: short tag (max 12 chars)
     - `options`: 2-4 entries, each with a `label` (1-5 words) and a one-sentence
       `description` of the tradeoff. Do NOT add "Other" manually — the tool surfaces it
       automatically as the free-text escape hatch.
   - **Genuinely open-ended** (e.g., "What's the acceptance threshold?"): use a plain
     text prompt, or rely on the auto-provided "Other" option on a related
     `AskUserQuestion` call.
   - You may batch up to 4 independent questions in a single `AskUserQuestion` call.
     Do not batch questions whose options depend on earlier answers — ask those
     sequentially.

   Only ask questions you genuinely cannot answer through investigation. _Non-interactive: apply decision-principles for autonomous answers, document each decision, proceed to Step 2._

## Step 2: Domain & Language Detection

After initial research completes, analyze findings for domain and language patterns.

**Domain detection**: Follow the detection procedure in `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` (file triggers first, then strong signals, then corroborating signals). Present detected domains to user.

**Language detection** (TDD-specific): Detect languages using `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md`. This identifies test file patterns, test reviewers, and test frameworks for each language in scope.

**Agent Type Verification**: Create explicit agent contract per `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md`. Include both standard research agents, domain agents, and language-based test agents.

## Step 3: Research & Discovery

1. **Pre-Spawn Verification (mandatory)**: Fill in the Spawn? and Justification columns below for the current task. **Default = spawn all.** Skipping requires written justification naming specific evidence in input files that makes the agent's work redundant — "input research is comprehensive" is NOT sufficient, because these agents look for things research authors cannot (recent file changes, prior plan precedents, codebase guideline files, reusable test infrastructure, language-specific simplifications). **Auto mode does not relax this** — if you find yourself reasoning "in auto mode, moving straight to X," stop and run the step.

   **Pipeline research reuse**: when the input is a plan outline produced by `/map-feature-to-plans` accompanied by a research document from `/research-problem` (and optionally a design decision doc), the Justification column may skip `codebase-explorer`, `thoughts-explorer`, `web-search-researcher`, or `web-search-researcher` by citing the specific artifact section that covers that agent's scope for THIS plan (e.g., "research doc § Current Implementation maps every file in this plan's Files list"). A valid citation names a document and section heading; a blanket "research is thorough" remains insufficient, and an agent whose scope is only partially covered still spawns. This provision never applies to the agents that look for what research authors do not record: test-pattern-researcher, the mandatory pattern search, and the mandatory guideline discovery always spawn; domain and language experts follow the Step 2 detection results as usual. The Step 7 review loop is unaffected. Downstream `/code-review` and validation stages remain the safety net for anything reuse misses.

   **Agent delivery resilience**: Subagents may go idle without delivering results (known Claude Code issue). If an agent sends an `idle_notification` without content: (1) prompt it via SendMessage using its agent ID (not name), (2) if still no delivery, respawn once, (3) if respawn fails, gather data directly or document the gap.

   | Agent                                    | Standard scope                                                                                 | Spawn? | Justification if skipping |
   | ---------------------------------------- | ---------------------------------------------------------------------------------------------- | ------ | ------------------------- |
   | codebase-explorer                        | Files related to the task; current implementation                                              | Yes/No | …                         |
   | thoughts-explorer                        | Existing thoughts docs about this feature                                                      | Yes/No | …                         |
   | web-search-researcher                  | internal tools, libraries, authenticated docs, Slack context                           | Yes/No | …                         |
   | web-search-researcher                    | External documentation and resources                                                           | Yes/No | …                         |
   | test-pattern-researcher (TDD)            | Test frameworks, fixtures, helpers, CI test commands, conftest.py, test base classes           | Yes/No | …                         |
   | Domain experts (per detected domain)     | Domain-specific patterns, idioms, gotchas (one row per domain detected in Step 2)              | Yes/No | …                         |
   | Language experts (per detected language) | Per-language design advice + simplification patterns (one row per language)                    | Yes/No | …                         |
   | Pattern search (mandatory)               | Existing abstractions (abstract classes, interfaces, base classes) for reuse                   | Yes/No | …                         |
   | Guideline discovery (mandatory)          | Coding standards files (CONTRIBUTING.md, .editorconfig, style guides, CLAUDE.md, lint configs) | Yes/No | …                         |

   Then spawn every agent marked Yes. The contract format follows `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md`.

2. **Spawn parallel agents for comprehensive research** based on the verification table above:
   - Standard agents (codebase-explorer, thoughts-explorer, web-search-researcher, web-search-researcher) as warranted
   - Domain experts for each detected domain
   - **Language experts for each detected language**: Read `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md` and look up the **Expert Agent** for each language detected in Step 2. Spawn the corresponding `{language}-expert` (e.g., `python-expert`, `typescript-expert`) in plan mode (loading code style + deep-analysis skills) to advise on per-language design choices for the planned tasks. Skip when generic planning suffices and the task is not language-specific.
   - **Mandatory TDD agents**:
     - Search for existing test patterns (test frameworks, fixture conventions, assertion styles, mocking approaches)
     - Find existing test infrastructure (conftest.py, test utilities, shared fixtures, test base classes, test factories)
     - Identify CI test commands and test configuration
   - **Mandatory pattern search**: find existing abstractions (abstract classes, interfaces, base classes) for reuse
   - **Mandatory guideline discovery**: search for coding standards/guidelines files (CONTRIBUTING.md, .editorconfig, style guides, CLAUDE.md rules, lint configs) in the target repo. Summarize findings for inclusion in the plan's "Coding Guidelines" section.

3. **Wait for ALL agents to complete**.

   **Design decision doc check**: If one of the input files is a design decision document
   (from `/design-approach` — identifiable by `design_method` in YAML frontmatter and
   location in `~/.claude/thoughts/shared/feature_designs/`), use its chosen approach
   and constraints directly. Skip the design options presentation below and proceed to Step 4
   with the pre-chosen approach. Carry forward the "Constraints for Downstream Planning"
   section as hard constraints on the plan.

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
7. **Map contract assertions to tasks** (when `--contract` is provided): For each task, record which contract assertion IDs it satisfies in a `**Fulfills**: VAL-API-001, VAL-API-002` field. Coverage completeness is checked in Step 6.
8. Present wave structure to user for approval via `AskUserQuestion` (interactive mode):
   - First render the wave outline (Wave 0 + feature waves, with task counts, themes,
     and dependency notes) directly in the Claude Code UI.
   - Then call `AskUserQuestion`:
     - `question`: `"Does this wave structure work? Ready to write the detailed plan?"`
     - `header`: `"Waves"` (max 12 chars)
     - `options`:
       - label: `"Proceed"`, description: `"Wave structure is good; move on to plan writing"`
       - label: `"Adjust waves"`, description: `"Regroup or reorder the waves before continuing"`
       - label: `"Adjust tasks"`, description: `"Change the tasks within waves before continuing"`
   - If the user selects an "Adjust" option (or "Other"), revise the wave structure and
     re-ask via `AskUserQuestion` until approved.

_Non-interactive: proceed with analysis, no approval gate._

## Step 5: Plan Structure Development

**Interactive mode**:

1. Render the wave-based outline with TDD structure directly in the Claude Code UI:

   ```
   ## Overview
   [1-2 sentence summary]

   ## Waves:
   - Wave 0: Test Infrastructure - [N tasks] - shared fixtures and helpers
   - Wave 1: [Theme] - [N tasks] - [TDD cycle summary]
   - Wave 2: [Theme] - [N tasks] - [TDD cycle summary]
   ```

2. Call `AskUserQuestion` to gate progression to Step 6:
   - `question`: `"Does this plan structure make sense? Ready to write the detailed plan?"`
   - `header`: `"Structure"` (max 12 chars)
   - `options`:
     - label: `"Proceed"`, description: `"Structure looks good; write the detailed TDD plan"`
     - label: `"Adjust phases"`, description: `"Regroup or rename the waves before writing"`
     - label: `"Adjust overview"`, description: `"Revise the summary before writing"`

3. If the user selects an "Adjust" option (or "Other"), revise the outline and re-ask
   via `AskUserQuestion` until approved.

_Non-interactive: proceed directly to Step 6._

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

**Coverage Matrix Check** (when `--contract` is provided): After writing the plan, verify that every assertion ID in the validation contract appears in at least one task's `fulfills` field. Produce a `### Contract Coverage Matrix` section (see `references/plan-template.md`) listing each assertion, which task(s) claim it, and its coverage status. If any assertion is uncovered (no task claims it), flag it as a planning gap with an `UNCOVERED` status -- either add a task to cover it or document why coverage is not achievable. The Coverage Matrix is informational: it surfaces gaps for the plan reviewer rather than blocking plan completion.

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

**Non-interactive mode**: spawn the multi-persona reviewer sub-agents (mandatory — self-review is NEVER a substitute for sub-agent spawning, even in `--non-interactive` mode). Run a single iteration only (no loop). Auto-resolve "Must Address" items via `decision-principles`; document each resolution in the produced plan's `## Autonomous Decisions § Review Synthesis` section. Token cost is NOT a valid skip justification.

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
- **TDD applies to code only**: Do NOT create RED/GREEN/REFACTOR cycles for documentation tasks (markdown files, READMEs, skill definitions, workflow templates). Documentation tasks should be planned as direct write/edit tasks without test phases. Only apply TDD to files that produce testable runtime behavior.
- **Wave 0 first**: always establish shared test infrastructure before feature waves
- **Use operational context**: When available, verify latency budget (current P99 + new call P99 < upstream timeout), check error budget headroom before choosing deployment strategy, adjust resource requests if utilization is high

## Reference Files

- **`references/plan-template.md`** -- Read when writing the plan (Step 6). Contains the full TDD plan template with wave structure, per-task RED/GREEN/REFACTOR sections, and parallelization plan format.
- **`references/review-personas.md`** -- Read when running the review loop (Step 7). Defines the 4 reviewer personas, their selection criteria, feedback format, and iteration rules.
- **`references/wave-analysis-guide.md`** -- Read when doing wave analysis (Step 4). Contains dependency mapping methodology, Wave 0 design patterns, and wave grouping heuristics.

## Shared Registries (by path)

- `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` -- domain detection patterns and expert agents
- `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md` -- language detection, test file patterns, test reviewers
- `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md` -- agent contract and verification checkpoints
