---
name: implement-plan-tdd
description: >
  Execute TDD-aware implementation plans with wave-based execution. Spawns
  one implementer agent per task enforcing red-green-refactor with verbatim
  failing-test evidence. Tasks parallelize only when their file sets are
  disjoint; the full test suite runs once per wave. Trigger phrases:
  (1) "implement TDD plan" (2) "execute TDD plan" (3) "implement-plan-tdd"
  (4) "run the TDD plan". Use when the user has a plan from create-plan-tdd
  and wants to execute it.
---

# Implement TDD Plan

Execute TDD-aware implementation plans produced by `create-plan-tdd`. Orchestrates
wave-based execution using one implementer agent per task — red→green→refactor
inside a single agent, with verbatim failing-test evidence required — plus an
optional final code quality review step.

## Mode Detection

Parse `$ARGUMENTS` for `--non-interactive` flag and plan path.

- **Non-interactive** (`--non-interactive`): plan path is required. Handle mismatches autonomously -- log each to `~/.claude/thoughts/shared/implementation_mismatches/YYYY-MM-DD-description.md`, use `${CLAUDE_PLUGIN_ROOT}/skills/decision-principles/SKILL.md` for resolutions. Continue without stopping.
- **Interactive** (default): stop on mismatches and present to user with options. Wait for response before continuing.
- **No arguments**: prompt user for a plan path.
- **`--scoping-doc <path>`** (optional): Path to a scoping document from `/map-feature-to-plans`. When provided and the scoping doc specifies "Stacked PRs" strategy, the orchestrator creates chained branches (one per plan) instead of merging all work onto a single branch. Without this flag, all behavior is unchanged.
- **`--skip-final-review`** (optional): Skip Steps 6-7 (final code quality review and guideline compliance). Pass this when a calling pipeline (e.g., `/orchestrate-feature-dev`) runs `/simplify` and `/code-review` on the cumulative diff afterwards — running both duplicates the work. Standalone invocations should omit it.

## Step 1: Load Plan and Validate

1. Read the plan file completely (no limit/offset parameters)
2. Validate plan has required TDD sections: Wave Analysis, Wave 0, at least one Phase with RED/GREEN/REFACTOR tasks. If missing sections, STOP and report.
3. Read the original ticket and all files mentioned in the plan -- read fully, no limit/offset
4. **Load requirements document (if referenced)**: Check the plan's `## References` section for a link to a requirements document. If found, read it fully and extract all non-negotiable constraints:
   - `## Constraints` section — all MUST/MUST NOT items
   - `## Acceptance Criteria` — items with behavioral invariants (e.g., "both run in parallel", "does NOT add sequential latency")
   - `## Scope` — items marked "Not needed" (negative constraints — things that must NOT be implemented)
   - `## Non-Functional Requirements` — latency budgets, execution patterns

   Store these as the `{{REQUIREMENTS_CONSTRAINTS_BLOCK}}` for injection into all agent and review prompts (see `references/tdd-agent-prompts.md` Section 5). If no requirements doc is referenced, set `{{REQUIREMENTS_CONSTRAINTS_BLOCK}}` to empty string.

5. Check for existing checkmarks (`- [x]`) to support resume -- trust completed work, pick up from first unchecked item
6. Create a todo list to track progress through waves and tasks

## Step 2: Stacked Branch Setup

**Skip this step if `--scoping-doc` was not provided or the scoping doc strategy is not "Stacked PRs".**

1. Read the scoping document fully
2. Parse the `### Branch Chain` table under `## PR Strategy`:
   - Extract each row's Plan, Branch Name, and Base Branch columns
   - Validate the table has at least 2 rows (stacking requires multiple plans)
3. Identify which plan THIS invocation is executing (match by plan name from the `--plan` argument or the plan file's title against the Branch Chain table)
4. Set the merge target variable for this plan:

   ```bash
   # Set explicitly — do NOT infer from git branch --show-current
   target_branch="<branch-name>"  # from Branch Chain table
   ```

5. Create the branch for this plan:

   ```bash
   git checkout <base-branch>
   git checkout -b "$target_branch"
   ```

6. Record git config for downstream skills:

   ```bash
   # gh CLI reads this for automatic --base detection
   git config branch."$target_branch".gh-merge-base <base-branch>
   # rebase-stack (Plan B) reads this for --onto after squash merge
   git config branch."$target_branch".stackBaseCommit $(git rev-parse <base-branch>)
   ```

   **Why `stackBaseCommit` is included here**: Plan B (rebase-stack) explicitly depends on Plan A establishing this config value. The scoping document's dependency chain assumes Plan A records both git config values at branch creation time so Plan B can consume them. Deferring to Plan B would require it to also modify implement-plan-tdd, breaking the clean plan boundary.

7. Pass `target_branch` to the stacked-branch procedure in `references/merge-strategy.md`. All subsequent work (Wave 0, Wave N execution) is committed on `target_branch` instead of `main`.

**Per-plan orchestration**: When executing multiple plans from a scoping document, the orchestrator repeats Steps 2-7 for each plan in Branch Chain order. Plan-level execution is sequential (plan 1 finishes before plan 2 starts). Wave-level parallelism within each plan is fully preserved.

**Backwards compatibility**: If `--scoping-doc` is not provided, skip this step entirely. The merge target defaults to `main` (current behavior).

## Step 3: Domain and Language Detection

1. Follow the detection procedure in `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` (file triggers first, then strong signals, then corroborating signals). Identify which domain experts are relevant (e.g., ML pipelines, infrastructure).
2. Detect languages using `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md`. This determines test file patterns, test frameworks, and the single language expert agent (e.g., `python-expert`, `typescript-expert`) used for both implementation (`mode=implement`) and review (`mode=test-review`, `mode=code-style-review`) in later steps.
3. Present detected domains and languages to user:

   ```
   ## Domains Detected in Plan
   - [Domain]: Found "[pattern]" -> [agent-name] available for guidance

   ## Languages Detected
   - [Language]: Test framework [X], test runner [Y]
   ```

4. These selections inform agent types and reviewers in Steps 5 and 6.

## Step 4: Wave 0 Execution (Test Infrastructure)

Execute Wave 0 tasks **sequentially in the main context** -- no subagents. Test infrastructure setup is typically small and benefits from direct orchestrator control.

1. Implement each Wave 0 task (test dependencies, runner config, shared fixtures, stub tests)
2. Run verification commands from the plan's Wave 0 Success Criteria
3. **STOP if Wave 0 verification fails** -- there is no point proceeding without working test infrastructure. Report the failure and wait for resolution.
4. Mark Wave 0 checkboxes in the plan file using Edit

## Step 5: Wave N Execution Loop

For each wave (1, 2, 3, ...) repeat the following:

1. **Parse tasks** in this wave from the plan
2. **Select agent type** for each task based on domain/language detection (see `references/wave-execution-guide.md`)
3. **Extract guidelines**: if the plan has a "## Coding Guidelines" section, prepare the `{{GUIDELINES_CONTEXT_BLOCK}}` for agent prompts per `references/tdd-agent-prompts.md` Section 4
4. **Agent Verification**: create an explicit agent contract per `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md`
5. **Pre-Spawn Verification**: output verification table matching contract before spawning

   **Agent delivery resilience**: Subagents may go idle without delivering results (known Claude Code issue). If an agent sends an `idle_notification` without content: (1) prompt it via SendMessage using its agent ID (not name), (2) if still no delivery, respawn once, (3) if respawn fails, document the gap and halt the wave. When spawning 5+ implementer agents, consider sequential sub-batches to reduce cascade-failure risk.

6. **Implementation phase (one implementer agent per task)**:
   - Determine ordering from the plan's File Overlap Matrix: tasks whose write sets are fully disjoint MAY run in parallel; tasks that write to any common file run sequentially. When in doubt, run sequentially.
   - Spawn one implementer agent per task (see `references/tdd-agent-prompts.md` for the prompt template). For code tasks the agent executes red→green→refactor internally: write the failing test, run it, capture the verbatim failing output, implement minimally to green, refactor per the plan, and include verbatim RED and GREEN evidence in its report. Non-code tasks (docs, templates, config with no runtime behavior) skip TDD and verify against the task's success criteria instead.
   - Parallel implementer agents run **targeted tests only** (their task's run commands) — never the full suite. The full suite runs once per wave in the integration check below. This caps CPU load and prevents cross-task test noise.
   - Wait for ALL in-flight implementer agents to complete before the integration check.
   - **Check agent statuses** (see `references/tdd-agent-prompts.md` Section 7): for each implementer, read its STATUS report:
     - DONE: verify the report contains verbatim failing-test (RED) evidence for code tasks — a code-task report without it is treated as DONE_WITH_CONCERNS (major). Otherwise proceed.
     - DONE_WITH_CONCERNS (minor): log concerns, proceed, present concerns at end
     - DONE_WITH_CONCERNS (major): STOP in interactive mode and present concerns; in non-interactive mode log to mismatch file and apply decision-principles
     - BLOCKED: STOP wave execution, present blocking reason to user (includes unexpected-pass reports — see `references/wave-execution-guide.md` Section 4)
     - NEEDS_CONTEXT: provide requested context and re-dispatch the implementer for that task

7. **Integration check**: run the full test suite from the main working directory
   - If integration check passes: proceed
   - If integration check fails in interactive mode: STOP, present failure, wait for guidance
   - If integration check fails in non-interactive mode: log mismatch, attempt resolution using decision-principles

8. **Spec compliance review**: after integration check passes, verify the wave's implementation matches the plan (see `references/spec-compliance-prompt.md`):
   - Spawn a spec compliance agent with the wave's planned tasks, expected files, and actual git diff
   - If verdict is PASS: proceed silently
   - If verdict is WARN: log warnings, proceed, present at final summary
   - If verdict is FAIL: stop in interactive mode (present findings); log and halt in non-interactive mode

9. **Mark wave checkboxes** in the plan file using Edit
10. **Proceed to next wave**

**IMPORTANT**: red-before-green is enforced INSIDE each implementer agent via mandatory verbatim failing-test evidence — not by separate agents. Same-file tasks never run concurrently, and no implementer runs the full test suite while sibling tasks are in flight.

## Step 6: Final Code Quality Review

**Skip Steps 6-7 entirely if `--skip-final-review` was passed** — the calling pipeline runs `/simplify` and `/code-review` on the cumulative diff afterwards, and running both duplicates the work.

1. For each detected language, spawn the single language expert agent from `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md` (Expert Agent column) twice in parallel: once with `mode=test-review` and once with `mode=code-style-review`. The same agent (e.g., `python-expert`) handles both framings via its `code-review-modes` skill.
2. **Include `{{REQUIREMENTS_CONSTRAINTS_BLOCK}}` in each reviewer's prompt** so reviewers know which patterns are non-negotiable and must not be "simplified" away
3. Each reviewer examines the changes made during implementation for its language
4. Synthesize reviewer feedback across all languages
5. **Interactive**: present feedback to user, apply only approved changes
6. **Non-interactive**: apply all suggested changes, log each in the mismatch file under a `## Code Quality Changes` section

## Step 7: Guideline Compliance

1. Use the built-in **Explore** agent (`subagent_type: Explore`) to find coding standards/guidelines files (e.g., CONTRIBUTING.md, .editorconfig, style guides, CLAUDE.md rules)
2. Compare implemented code with discovered guidelines and identify conflicts
3. **Interactive**: present conflicts with proposed fixes, wait for user approval before applying
4. **Non-interactive**: apply all guideline fixes autonomously, log each change to the mismatch file under a `## Guideline Changes` section
5. Run automated success criteria after any guideline changes to verify no regressions

## Step 8: Post-Review Requirements Guard

After Steps 6 and 7 may have modified code, verify that no requirements constraint was violated. **Skip this step if no requirements document was loaded in Step 1, or if Steps 6-7 were skipped via `--skip-final-review`** (no post-review changes to guard).

1. Record the post-implementation commit hash before Steps 6-7 begin (the commit after the last wave's integration check passed). Compare against the current state: `git diff {{POST_IMPL_COMMIT}}..HEAD`
2. For each file changed by Steps 6-7, check whether the change alters behavior that a requirements constraint protects. Focus on:
   - Execution patterns (parallel vs. sequential, async vs. sync)
   - Architectural constraints (service boundaries, no new dependencies)
   - Performance invariants (latency budgets, no added latency on critical path)
   - Scope constraints (features marked "Not needed" must remain absent)
3. If a behavioral change violates a requirements constraint:
   - **Interactive**: STOP, show the specific constraint and the specific change that violates it. Ask user whether to revert the change or accept the deviation with documented rationale.
   - **Non-interactive**: REVERT the specific change that violates the constraint. Log the attempted change and the revert reason to the mismatch file.
4. If no violations are found, proceed silently.

## Step 9: Final Verification

1. Run the full test suite one final time
2. Run all automated success criteria from the plan's "Desired End State" > "Verification Criteria" > "Automated" section
3. Optionally invoke the `verify-implementation` skill for comprehensive evidence generation if available
4. Present summary:
   ```
   ## Implementation Summary
   - Tasks completed: [N/N]
   - Tests passing: [test count]
   - Files modified: [list]
   - Mismatches encountered: [N] (see mismatch log if any)
   ```

## Step 10: Completion

1. Mark plan status as implemented (add `**Status**: Implemented` to plan header)
2. Present final summary with next steps:
   - Manual testing items from the plan's manual verification criteria
   - Code review recommendations
   - Commit and PR creation
3. **Interactive**: ask if user wants to commit the changes
4. **Non-interactive**: implementation is complete, output summary and exit

## Guidelines

- **Requirements are non-negotiable** -- if a requirements document was loaded in Step 1, its constraints override all other considerations including code style preferences and simplification suggestions. No agent, reviewer, or refactoring step may violate a requirements constraint. When in doubt, preserve the behavior specified in the requirements.
- **Plan is the spec** -- implement what it says, not your interpretation. Code specifications in the plan are binding.
- **TDD is non-negotiable for code tasks** -- red before green, always, inside each implementer agent. Never write implementation before the failing test exists and has been run; the verbatim failing-test output in the agent report is the required evidence. Non-code tasks (docs, templates) skip TDD.
- **Fresh context per agent** -- never reuse agent context across tasks. Each agent starts clean.
- **No same-file parallelism** -- tasks that write to a common file never run concurrently; parallel agents run targeted tests only. (Per-task worktree isolation was removed in 0.9.0 after repeatedly misfiring in orchestrated runs.)
- **Mismatch handling** -- stop and ask in interactive mode; log, resolve, and continue in non-interactive mode.
- **Thin orchestrator** -- delegate implementation to subagents, keep the main context lean and focused on coordination.
- **Resume-safe** -- checkmarks in the plan track progress. A resumed run picks up from the first unchecked item.
- **Escalation over silence** -- agents report DONE_WITH_CONCERNS when unsure rather than silently completing questionable work. Minor concerns auto-continue and accumulate for end-of-run presentation; major concerns halt execution. Bad work is worse than no work.

## Reference Files

- **`references/wave-execution-guide.md`** -- Read when executing waves (Steps 4-5). Contains plan parsing, agent selection logic, Wave 0 and Wave N execution details, progress tracking, error handling.
- **`references/tdd-agent-prompts.md`** -- Read when spawning implementer agents (Step 5). Contains the implementer prompt template, domain/language customization hooks, and prompt composition flow.
- **`references/merge-strategy.md`** -- Read during stacked-branch setup (Step 2). Contains branch targeting and git config recording for stacked PRs.
- **`references/spec-compliance-prompt.md`** -- Read when running spec compliance review (Step 5). Contains the adversarial review prompt template, severity classification, and orchestrator integration guide.

## Shared Registries (by path)

- `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` -- domain detection patterns and expert agents
- `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md` -- language detection, test file patterns, single language expert agents (used for both `mode=implement` and review modes)
- `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md` -- agent contract and verification checkpoints
