# Wave Execution Guide

This guide provides detailed mechanics for executing waves from a TDD plan. It is referenced by `implement-plan-tdd` SKILL.md Steps 3-4.

**Related references**:

- Plan format: `${CLAUDE_PLUGIN_ROOT}/skills/create-plan-tdd/references/plan-template.md`
- Wave design: `${CLAUDE_PLUGIN_ROOT}/skills/create-plan-tdd/references/wave-analysis-guide.md`
- Domain agents: `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md`
- Language agents: `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md`
- Verification pattern: `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md`

---

## 1. Parsing Tasks from a TDD Plan

The plan follows the template defined in `create-plan-tdd/references/plan-template.md`. The orchestrator must parse three sections to build its execution model: the dependency table, the per-task RED/GREEN/REFACTOR details, and the agent selection table.

### Extracting Wave Assignments from the Dependency Table

The dependency table lives under `## Wave Analysis > ### Dependency Table`. It is a markdown table with four columns:

```
| Task | Depends On | Files Touched | Wave Assignment |
|------|-----------|---------------|-----------------|
| 0.1: [Test infrastructure setup] | None | `test config files` | Wave 0 |
| 1.1: [Task name] | Wave 0 | `path/to/file_a.ext`, `path/to/test_a.ext` | Wave 1 |
```

**Parsing rules**:

1. Locate the heading `### Dependency Table` (an H3 under the `## Wave Analysis` H2).
2. Read each row after the header separator (`|------|`).
3. Extract the **Task** column value. The task ID is the prefix before the colon (e.g., `1.1`, `2.3`). The first digit is the wave number; the second is the task index within that wave.
4. Extract the **Wave Assignment** column value (e.g., `Wave 0`, `Wave 1`). Use this as the authoritative wave number -- do not infer it solely from the task ID prefix, since plans may have been manually adjusted.
5. Extract the **Files Touched** column value. Split on commas to get the list of file paths. Strip backticks.
6. Extract the **Depends On** column value. This lists prerequisite tasks or waves. Use this to validate execution ordering.

### Extracting Per-Task RED/GREEN/REFACTOR Details

Each task's implementation details live in Phase sections. The markdown structure is:

````
## Phase N: [Wave N Name]

### Task N.M: [Task Name]

**Wave**: N

#### RED -- Write failing test

**Test file**: `path/to/test_file.ext`
**Behavior**: [Description]
**Expected failure**: `[Error text]`
**Run**:
```bash
[test command]
````

#### GREEN -- Make it pass

**File**: `path/to/implementation.ext`
**Changes**: [Description]
**Run**: `[test command]` -- should pass

#### REFACTOR -- Clean up

**Focus**: [Description]
**Constraint**: All tests must remain green
**Run**:

```bash
[full test suite command]
```

```

**Parsing rules**:

1. Locate each `## Phase N:` heading. The number N corresponds to the wave number.
2. Within each Phase, locate each `### Task N.M:` heading.
3. Within each Task, locate the three sub-sections by their H4 headings:
   - `#### RED -- Write failing test` -- extract `**Test file**`, `**Behavior**`, `**Expected failure**`, and the `**Run**` command.
   - `#### GREEN -- Make it pass` -- extract `**File**`, `**Changes**`, and the `**Run**` command.
   - `#### REFACTOR -- Clean up` -- extract `**Focus**`, `**Constraint**`, and the `**Run**` command.
4. Code blocks within each section contain the literal test or implementation code to write.

### Reading the Agent Selection Table

The agent selection table lives under `## Parallelization Plan > ### Agent Selection`:

```

| Task | Agent Type           | Rationale                   |
| ---- | -------------------- | --------------------------- |
| 0.1  | infrastructure agent | Sets up test framework      |
| 1.1  | backend agent        | Core service implementation |

```

**Parsing rules**:

1. Locate the heading `### Agent Selection` (an H3 under `## Parallelization Plan`).
2. Read each row. The **Task** column matches task IDs from the dependency table.
3. The **Agent Type** column specifies the plan author's recommended agent. This feeds into the agent selection decision tree (Section 2).

### Reading the File Overlap Matrix

The file overlap matrix lives under `## Wave Analysis > ### File Overlap Matrix`:

```

| File                 | Task 1.1 | Task 1.2 | Task 2.1 |
| -------------------- | -------- | -------- | -------- |
| `path/to/file_a.ext` | W        | -        | W        |

```

**Parsing rules**:

1. Locate the heading `### File Overlap Matrix`.
2. Read each row. The **File** column is the file path (strip backticks).
3. Each task column contains `W` (write), `R` (read only), or `-` (not touched).
4. Before executing a wave, validate: no two tasks **within the same wave** both have `W` for the same file. If they do, this is an intra-wave conflict that should have been resolved at plan time. If found at execution time, STOP and report to the user.

---

## 2. Agent Selection Logic

For each task, select the appropriate agent using this decision tree. The goal is to compose a final agent configuration that combines domain expertise, language awareness, and any plan-specified overrides.

### Decision Tree

```

For each task:

1. Check domain-agent-registry
   - Follow the detection procedure in
     ${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md
     (file triggers first, then strong signals, then corroborating signals)
   - If a domain match is found -> note the domain expert agent
     (e.g., `ml-pipeline-reviewer` for ML training code)

2. Check language-agent-registry
   - Identify file extensions for the task's files
   - Look up the language in
     ${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md
   - Read the `Expert Agent` column for each detected language
     (e.g., `typescript-expert` for .ts files, `python-expert` for .py)
   - Spawn that single agent per language with mode framing matching the
     work: `mode=implement` for implementer agents (the language expert
     writes idiomatic code, not only reviews it); `mode=test-review` or
     `mode=code-style-review` when reviewing the diff

3. Check plan's Agent Selection table
   - If the plan specifies an agent type for this task -> use that as the
     primary agent type
   - The plan's recommendation takes precedence over auto-detection when
     there is a conflict

4. Fallback
   - If no domain match, no language match, and no plan specification ->
     use `general-purpose` agent

```

### Composing the Final Agent Type

The final agent receives context from all applicable sources:

- **Primary agent type**: From the plan's Agent Selection table (Step 3), or from domain detection (Step 1) if the plan does not specify.
- **Language context**: Always included. The agent prompt should reference the language-specific test patterns and idioms from the language-agent-registry. For example, a Java implementer should know about JUnit 5 patterns; a Python implementer should know about pytest patterns.
- **Domain context**: Included when detected. The agent prompt should reference domain-specific best practices. For example, an ML pipeline agent should know that domain's test-harness patterns.

**Do not duplicate** the contents of the registries into agent prompts. Instead, reference them:
- `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` for domain detection patterns and expert agents
- `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md` for language detection, test file patterns, and reviewer agents

### Agent Verification

Before spawning agents for a wave, apply the verification pattern from `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md`:

1. Output the **Agent Type Verification** contract listing all agents to spawn.
2. Output the **Pre-Spawn Verification Table** cross-checking the contract against actual Task calls.
3. After all agents complete, output the **Pre-Synthesis Verification Checkpoint** confirming all contracted agents ran.

---

## 3. Wave 0 Execution (Detail)

Wave 0 establishes the test infrastructure. It is always sequential and always runs in the main context (no subagents). No implementation code is written in Wave 0.

### Execution Steps

1. **Create test configuration files**
   - Add or update the test framework config (e.g., `pytest.ini`, `jest.config.js`, Maven Surefire plugin config).
   - Add test dependencies to the build file if not already present.
   - Set up test source directories if they do not exist.

2. **Create shared fixtures**
   - Write shared test helpers, fixtures, factories, and mocks listed in the plan's `## Wave 0: Test Infrastructure > ### Shared Fixtures and Test Utilities` section.
   - Place them in locations importable by all test files.

3. **Create stub tests**
   - Write the stub test file(s) specified in the plan's `### Stub Test File` section.
   - These are minimal tests that verify the framework is working (e.g., `test_stub_passes` that asserts `True`).

4. **Run verification**
   - Execute the CI verification command from the plan's `### CI Verification` section.
   - This command must exit with code 0.

### Verification Criteria

All of the following must pass before proceeding to Wave 1:

- Test runner exits with code 0 (no configuration errors).
- Shared fixtures are importable from test files (no import errors).
- Stub tests are discovered and pass (the test runner finds and runs them).
- The CI verification command from the plan succeeds.

### Failure Handling

If Wave 0 verification fails: **STOP**. No subsequent wave can proceed without working test infrastructure. The orchestrator must:

1. Report the exact failure (command output, error message, exit code).
2. In interactive mode: present the failure to the user and wait for guidance.
3. In non-interactive mode: log the failure and halt execution. Do not attempt to proceed to Wave 1.

Wave 0 failure is not retryable by simply re-running -- it typically indicates a configuration problem that requires human diagnosis (wrong test framework version, missing dependency, incorrect directory structure).

---

## 4. Wave N Execution (Detail)

Waves 1 through N spawn **one implementer agent per task**. Each implementer executes red→green→refactor internally (see `tdd-agent-prompts.md` Section 1). TDD discipline is enforced by evidence, not agent separation: every code-task report must contain the verbatim failing-test output captured BEFORE implementation began (RED_EVIDENCE), and the orchestrator rejects code-task reports without it.

### Parallelism Rules

1. Consult the File Overlap Matrix (Section 1). Tasks whose write sets are fully disjoint MAY run in parallel; tasks sharing any written file run sequentially. When the matrix is missing or ambiguous, run sequentially.
2. Parallel implementers run **targeted tests only** (their task's run commands). The full suite runs once per wave in the integration check. This caps CPU load and prevents cross-task noise from concurrent full-suite runs.
3. All work happens in the main working directory on the target branch — there are no per-task worktrees or merges. Implementer agents do NOT commit; the orchestrator (or the calling pipeline's `/commit` stage) owns git operations, because concurrent commits from parallel agents to a shared branch are race-prone.

### Execution Flow

1. Assemble each implementer's prompt per `tdd-agent-prompts.md` Section 6.
2. Spawn the current flight of implementers (parallel only where the rules above allow).
3. Wait for all in-flight implementers to complete. Collect STATUS reports; verify RED_EVIDENCE on code tasks.
4. Act on statuses per the protocol (`tdd-agent-prompts.md` Section 7 and SKILL.md Step 5).
5. **Inter-wave integration check**: run the full test suite from the main working directory (command from the plan's `## Testing Strategy` section or the most recent Phase's success criteria). All tests must pass — this wave's and every previous wave's. If any fail, see Section 6 (Error Handling).
6. After the integration check passes, the orchestrator MAY create a checkpoint commit on the target branch for rollback granularity, then proceed to the next wave.

### Handling Unexpected Test Outcomes

#### Test Passes Unexpectedly (before implementation)

If an implementer's new test passes before any implementation exists, the behavior is already implemented or the test is wrong. The implementer stops immediately — no implementation — and reports BLOCKED with the unexpected-pass output. The orchestrator should:

- Check whether existing code already implements the behavior. If so, the task may be redundant -- mark it as skipped and note why.
- Check whether the test is incorrect (testing the wrong thing). If so, fix the test specification and re-dispatch the implementer.
- In interactive mode: present the situation to the user for a decision.
- In non-interactive mode: log the mismatch; if the behavior verifiably already exists, mark the task complete-by-existing-code and continue.

#### Test Still Fails After Implementation

If an implementer cannot make its test pass, it reports BLOCKED with the actual failure output. The orchestrator should:

- Check the agent's implementation against the plan's specification. Did the agent follow the plan correctly?
- Retry once with additional context (e.g., include the test's full error output in the retry prompt).
- If the retry also fails:
  - In interactive mode: present the failure to the user with the test output and the agent's implementation attempt.
  - In non-interactive mode: log the failure, mark the task as failed, and continue with remaining tasks in the wave if they are independent. Do NOT proceed to the next wave if the failed task has downstream dependents.

---

## 5. Progress Tracking

The orchestrator must track progress at three levels: TodoWrite items, plan checkboxes, and context management.

### TodoWrite Mirroring

Use `TodoWrite` to maintain a live view of wave and task status. Structure the todos to mirror the wave hierarchy:

```

- Wave 0: Test Infrastructure [completed/in_progress/pending]
  - Task 0.1: Test framework setup [completed/in_progress/pending]
- Wave 1: [Wave Name] [completed/in_progress/pending]
  - Task 1.1: [Name] [completed/in_progress/pending]
  - Task 1.2: [Name] [completed/in_progress/pending]
- Wave 2: [Wave Name] [completed/in_progress/pending]
  ...

```

Update todo status at these checkpoints:
- When a wave starts: mark wave as `in_progress`.
- When an implementer agent completes: mark the corresponding task.
- When all tasks in a wave complete and integration tests pass: mark wave as `completed`.
- When a task fails: mark it with a note explaining the failure.

### Plan Checkbox Updates

After each wave completes successfully, update the plan file's checkboxes using `Edit`:

1. Locate the `### Phase N Success Criteria` section for the completed wave.
2. Change `- [ ]` to `- [x]` for each criterion that has been verified.
3. Also update the `## Desired End State > ### Verification Criteria` checkboxes as they become satisfied.

### Maintaining a Thin Orchestrator

The main context (orchestrator) should NOT accumulate implementation details. It should track only:

- Which wave is currently executing.
- Which tasks have completed, failed, or been skipped.
- Integration test results (pass/fail + summary, not full output).
- Agent spawn/completion status.

Implementation details (code written, test output, refactoring decisions) live in each implementer agent's own context. The orchestrator reads only the structured report from each agent (STATUS, CONCERNS, RED/GREEN evidence, FILES_CHANGED), not the full work log. This keeps the orchestrator's context window focused on coordination rather than filling up with code.

---

## 6. Error Handling

### Agent Timeout or Crash

If an agent does not complete within a reasonable time or crashes:

1. **Retry once**: Spawn a new agent for the same task with the same inputs. Include a note that this is a retry.
2. **If retry also fails**: Log the failure as a mismatch. Mark the task as failed in the todo list.
3. **Impact assessment**: Check whether downstream tasks in later waves depend on this task. If they do, those tasks cannot proceed. If they do not, the remaining waves can continue without this task's output.

### Test Failure During Integration Check

When the full test suite fails during a wave's integration check:

- **Interactive mode**: Stop execution. Present the failing test(s) and the task(s) whose changes plausibly introduced the failure. Ask the user whether to attempt automatic resolution, manually fix, or roll back the wave (to the previous checkpoint commit, if one exists).
- **Non-interactive mode**: Log the failure with full test output. Attempt resolution by:
  1. Identifying which test(s) fail and which task's changes introduced the failure (use the implementers' FILES_CHANGED reports).
  2. Spawning a fix agent to address the specific failure.
  3. If the fix agent succeeds, re-run the integration check.
  4. If the fix agent fails, halt execution and report the unresolved failure.

### Same-File Parallelism Violation

Two tasks that ran in parallel must never both modify the same file — the File Overlap Matrix gates parallelism. If post-hoc evidence shows it happened anyway (overlapping FILES_CHANGED reports, or `git status` attribution during the integration check):

1. **Log it as a wave analysis bug**: The plan's file overlap matrix was incorrect or incomplete.
2. **STOP execution**: Do not attempt automatic reconciliation — the file may interleave both tasks' edits incoherently.
3. **Present to user**: Show the affected files, the tasks that wrote to them, and the file overlap matrix entry that should have caught this.
4. **Resolution path**: The user (or orchestrator, if instructed) must either:
   - Restore the affected files to the last good state (checkpoint commit or pre-wave state) and re-run the two tasks sequentially.
   - Fix the plan to move one task to a later wave, then re-run.
```
