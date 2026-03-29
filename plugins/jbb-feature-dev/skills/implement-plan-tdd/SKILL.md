---
name: implement-plan-tdd
description: >
  Execute TDD-aware implementation plans with wave-based parallel agents and
  worktree isolation. Spawns separate RED and GREEN agents per task for strict
  TDD enforcement. Uses hybrid merge strategy (worktree isolation + no-overlap
  guarantee). Trigger phrases: (1) "implement TDD plan" (2) "execute TDD plan"
  (3) "implement-plan-tdd" (4) "run the TDD plan". Use when the user has a
  plan from create-plan-tdd and wants to execute it with parallel TDD agents.
---

# Implement TDD Plan

Execute TDD-aware implementation plans produced by `create-plan-tdd`. Orchestrates
wave-based parallel execution using separate RED and GREEN agents per task, worktree
isolation (Strategy C hybrid), and a final code quality review step.

## Mode Detection

Parse `$ARGUMENTS` for `--non-interactive` flag and plan path.

- **Non-interactive** (`--non-interactive`): plan path is required. Handle mismatches autonomously -- log each to `~/.claude/thoughts/shared/implementation_mismatches/YYYY-MM-DD-description.md`, use `${CLAUDE_PLUGIN_ROOT}/skills/decision-principles/SKILL.md` for resolutions. Continue without stopping.
- **Interactive** (default): stop on mismatches and present to user with options. Wait for response before continuing.
- **No arguments**: prompt user for a plan path.

## Step 1: Load Plan and Validate

1. Read the plan file completely (no limit/offset parameters)
2. Validate plan has required TDD sections: Wave Analysis, Wave 0, at least one Phase with RED/GREEN/REFACTOR tasks. If missing sections, STOP and report.
3. Read the original ticket and all files mentioned in the plan -- read fully, no limit/offset
4. **Discover domain skills**: Check available skills (both project-level and user-level)
   for any that describe APIs, services, or domain concepts referenced in the plan. If a
   skill's description matches the systems or technologies being implemented, read its full
   content. Pass relevant domain knowledge (API schemas, known gotchas, naming conventions,
   architectural patterns) to RED/GREEN agents so they can write accurate tests and correct
   implementations. Also note available MCP servers for use in Step 7 verification.
5. Check for existing checkmarks (`- [x]`) to support resume -- trust completed work, pick up from first unchecked item
6. Create a todo list to track progress through waves and tasks

## Step 2: Language Detection

1. Detect languages using `${CLAUDE_PLUGIN_ROOT}/commands/shared/language-agent-registry.md`. This determines test file patterns, test frameworks, test reviewers, and code simplification reviewers for later steps.
2. Present detected languages to user:

   ```
   ## Languages Detected
   - [Language]: Test framework [X], test runner [Y]
   ```

3. These selections inform agent types and reviewers in Steps 4 and 5.

## Step 3: Wave 0 Execution (Test Infrastructure)

Execute Wave 0 tasks **sequentially in the main context** -- no subagents. Test infrastructure setup is typically small and benefits from direct orchestrator control.

1. Implement each Wave 0 task (test dependencies, runner config, shared fixtures, stub tests)
2. Run verification commands from the plan's Wave 0 Success Criteria
3. **STOP if Wave 0 verification fails** -- there is no point proceeding without working test infrastructure. Report the failure and wait for resolution.
4. Mark Wave 0 checkboxes in the plan file using Edit

## Step 4: Wave N Execution Loop

For each wave (1, 2, 3, ...) repeat the following:

1. **Parse tasks** in this wave from the plan
2. **Select agent type** for each task based on domain/language detection (see `references/wave-execution-guide.md`)
3. **Extract guidelines**: if the plan has a "## Coding Guidelines" section, prepare the `{{GUIDELINES_CONTEXT_BLOCK}}` for agent prompts per `references/tdd-agent-prompts.md` Section 4b
4. **Agent Verification**: create an explicit agent contract per `${CLAUDE_PLUGIN_ROOT}/commands/shared/agent-verification-pattern.md`
5. **Pre-Spawn Verification**: output verification table matching contract before spawning

6. **RED phase (parallel across tasks)**:
   - Spawn one RED agent per task in parallel with `isolation: "worktree"`
   - Each RED agent writes failing tests only (see `references/tdd-agent-prompts.md` for prompt templates)
   - Wait for ALL RED agents in the wave to complete
   - **Check agent statuses** (see `references/tdd-agent-prompts.md` Section 6): for each RED agent, read its STATUS report:
     - DONE: proceed to merge
     - DONE_WITH_CONCERNS (minor): log concerns, proceed to merge, present concerns at end
     - DONE_WITH_CONCERNS (major): STOP in interactive mode and present concerns; in non-interactive mode log to mismatch file and apply decision-principles
     - BLOCKED: STOP wave execution, present blocking reason to user
     - NEEDS_CONTEXT: provide requested context and re-dispatch the RED agent for that task
   - Merge all RED worktree branches sequentially into main branch (see `references/merge-strategy.md`)

7. **GREEN phase (parallel across tasks)**:
   - Spawn one GREEN agent per task in parallel with `isolation: "worktree"`
   - Each GREEN agent writes minimal implementation to make its tests pass, then runs REFACTOR within the same worktree
   - Wait for ALL GREEN agents in the wave to complete
   - **Check agent statuses** (see `references/tdd-agent-prompts.md` Section 6): for each GREEN agent, read its STATUS report:
     - DONE: proceed to merge
     - DONE_WITH_CONCERNS (minor): log concerns, proceed to merge, present concerns at end
     - DONE_WITH_CONCERNS (major): STOP in interactive mode and present concerns; in non-interactive mode log to mismatch file and apply decision-principles
     - BLOCKED: STOP wave execution, present blocking reason to user
     - NEEDS_CONTEXT: provide requested context and re-dispatch the GREEN agent for that task
   - Merge all GREEN worktree branches sequentially into main branch (see `references/merge-strategy.md`)

8. **Integration check**: run the full test suite from the main working directory
   - If integration check passes: proceed
   - If integration check fails in interactive mode: STOP, present failure, wait for guidance
   - If integration check fails in non-interactive mode: log mismatch, attempt resolution using decision-principles

9. **Spec compliance review**: after integration check passes, verify the wave's implementation matches the plan (see `references/spec-compliance-prompt.md`):
   - Spawn a spec compliance agent with the wave's planned tasks, expected files, and actual git diff
   - If verdict is PASS: proceed silently
   - If verdict is WARN: log warnings, proceed, present at final summary
   - If verdict is FAIL: stop in interactive mode (present findings); log and halt in non-interactive mode

10. **Mark wave checkboxes** in the plan file using Edit
11. **Proceed to next wave**

**IMPORTANT**: RED and GREEN are sequential within a task (GREEN depends on RED's tests), but tasks within a wave are parallel. For a wave with 3 tasks: spawn 3 RED agents in parallel, wait and merge, then spawn 3 GREEN agents in parallel, wait and merge.

## Step 5: Final Code Quality Review

1. Spawn language-specific code simplification reviewers from `${CLAUDE_PLUGIN_ROOT}/commands/shared/language-agent-registry.md` -- one per detected language
2. Each reviewer examines the changes made during implementation for its language
3. Synthesize reviewer feedback across all languages
4. **Interactive**: present feedback to user, apply only approved changes
5. **Non-interactive**: apply all suggested changes, log each in the mismatch file under a `## Code Quality Changes` section

## Step 6: Guideline Compliance

1. Use the built-in **Explore** agent (`subagent_type: Explore`) to find coding standards/guidelines files (e.g., CONTRIBUTING.md, .editorconfig, style guides, CLAUDE.md rules)
2. Compare implemented code with discovered guidelines and identify conflicts
3. **Interactive**: present conflicts with proposed fixes, wait for user approval before applying
4. **Non-interactive**: apply all guideline fixes autonomously, log each change to the mismatch file under a `## Guideline Changes` section
5. Run automated success criteria after any guideline changes to verify no regressions

## Step 7: Final Verification

1. Run the full test suite one final time
2. Run all automated success criteria from the plan's "Desired End State" > "Verification Criteria" > "Automated" section
3. If MCP servers are available for systems affected by the implementation (databases,
   orchestration platforms, deployment targets), use them to verify the implementation
   against live state where appropriate (e.g., confirm schema compatibility, check service
   health, validate deployment configuration)
4. Optionally invoke the `verify-implementation` skill for comprehensive evidence generation if available
5. Present summary:
   ```
   ## Implementation Summary
   - Tasks completed: [N/N]
   - Tests passing: [test count]
   - Files modified: [list]
   - Mismatches encountered: [N] (see mismatch log if any)
   ```

## Step 8: Completion

1. Mark plan status as implemented (add `**Status**: Implemented` to plan header)
2. Present final summary with next steps:
   - Manual testing items from the plan's manual verification criteria
   - Code review recommendations
   - Commit and PR creation
3. **Interactive**: ask if user wants to commit the changes
4. **Non-interactive**: implementation is complete, output summary and exit

## Guidelines

- **Plan is the spec** -- implement what it says, not your interpretation. Code specifications in the plan are binding.
- **TDD is non-negotiable** -- RED before GREEN, always. Never write implementation before the failing test exists and is merged.
- **Fresh context per agent** -- never reuse agent context across tasks. Each agent starts clean.
- **Worktree isolation for all parallel work** -- every parallel agent runs in its own worktree to prevent file conflicts.
- **Mismatch handling** -- stop and ask in interactive mode; log, resolve, and continue in non-interactive mode.
- **Thin orchestrator** -- delegate implementation to subagents, keep the main context lean and focused on coordination.
- **Resume-safe** -- checkmarks in the plan track progress. A resumed run picks up from the first unchecked item.
- **Escalation over silence** -- agents report DONE_WITH_CONCERNS when unsure rather than silently completing questionable work. Minor concerns auto-continue and accumulate for end-of-run presentation; major concerns halt execution. Bad work is worse than no work.

## Reference Files

- **`references/wave-execution-guide.md`** -- Read when executing waves (Steps 3-4). Contains plan parsing, agent selection logic, Wave 0 and Wave N execution details, progress tracking, error handling.
- **`references/tdd-agent-prompts.md`** -- Read when spawning RED/GREEN/REFACTOR agents (Step 4). Contains prompt templates, domain/language customization hooks, and prompt composition flow.
- **`references/merge-strategy.md`** -- Read when merging worktree branches (Step 4). Contains Strategy C hybrid merge procedure, pre-merge checks, conflict handling, rollback, and worktree naming.
- **`references/spec-compliance-prompt.md`** -- Read when running spec compliance review (Step 4). Contains the adversarial review prompt template, severity classification, and orchestrator integration guide.

## Shared Registries (by path)

- `${CLAUDE_PLUGIN_ROOT}/commands/shared/language-agent-registry.md` -- language detection, test file patterns, test reviewers
- `${CLAUDE_PLUGIN_ROOT}/commands/shared/agent-verification-pattern.md` -- agent contract and verification checkpoints
