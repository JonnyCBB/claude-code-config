# Wave Analysis Guide

This guide provides detailed instructions for dependency analysis and wave grouping. It is used during Step 4 of the create-plan-tdd skill to group tasks into parallelizable waves so that multiple developers (or agents) can work simultaneously without conflicts.

---

## 1. Building the Dependency Graph

The goal is to construct a Directed Acyclic Graph (DAG) where each node is a task and each edge represents a dependency relationship ("Task A must complete before Task B can start").

### Dependency Categories

Examine every pair of tasks for the following types of dependencies:

- **File dependencies**: Task B modifies a file that Task A creates or modifies. B depends on A.
- **Data dependencies**: Task B reads data or output that Task A produces. B depends on A.
- **API dependencies**: Task B calls an API endpoint that Task A implements. B depends on A.
- **Test dependencies**: Task B's tests import fixtures, utilities, or helpers created by Task A. B depends on A.

### Construction Steps

1. **List all tasks with their input and output files.** For each task, record:
   - Files it creates (new files)
   - Files it modifies (existing files)
   - Files it reads (imports, references, test fixtures)
2. **For each pair of tasks (X, Y), check**: Do the outputs of X appear in the inputs of Y? If yes, draw a directed edge from X to Y.
3. **Check the reverse direction** as well: Do the outputs of Y appear in the inputs of X? If yes, draw an edge from Y to X.
4. **Verify acyclicity.** If you discover a cycle (A depends on B depends on A), one of the tasks must be split into smaller sub-tasks to break the cycle.
5. **The result is a DAG** — a directed acyclic graph of task dependencies.

### Cross-Reference with File Structure

Before finalizing the dependency graph, cross-reference against the plan's `## File Structure` section:

1. **Coverage check**: Every file listed in the File Structure section must appear in at least one task's "Files Touched" column. If a file has no task, either add a task or remove the file from the structure.
2. **Scope check**: If a task creates or modifies files NOT listed in the File Structure section, flag it. Either add the file to the structure (with justification) or remove the unplanned work from the task.
3. **Responsibility check**: If a task touches files whose stated responsibilities in the File Structure section don't align with the task's purpose, investigate — this may indicate a task boundary problem.

---

## 2. Dependency Types

### Hard Dependency

Task B MUST complete after Task A. This applies when:

- Task B reads or modifies files that Task A creates
- Task B's tests depend on Task A's implementation (e.g., importing a class Task A defines)
- Task B extends or implements an interface that Task A introduces
- Task B's compilation or test execution would fail without Task A's output

### Soft Dependency

Task B BENEFITS from Task A completing first but is NOT blocked. This applies when:

- Task B could use a utility that Task A creates, but could also inline the logic
- Task B references a pattern established by Task A, but could independently implement its own version
- Task A provides a "nice to have" optimization or shared abstraction that Task B could work without

### Rules

1. Only hard dependencies affect wave assignment.
2. Soft dependencies are noted in the plan documentation but do not constrain parallelization.
3. When in doubt, treat a dependency as hard. This is the safer choice — incorrect parallelization causes merge conflicts and broken builds, while unnecessary serialization only costs time.

---

## 3. Wave Grouping Algorithm

### Step-by-Step Process

**Step 1 — Assign Wave 0 (Test Infrastructure)**

Wave 0 always contains test infrastructure tasks only. No implementation tasks go in Wave 0. Contents include:

- Test framework configuration
- Shared fixtures and test utilities
- Stub test files to verify the framework works
- CI verification commands

**Step 2 — Identify Root Tasks (Wave 1)**

Root tasks are tasks with NO hard dependencies other than Wave 0 infrastructure. These form Wave 1 because they can all start immediately after Wave 0 completes.

**Step 3 — Topological Sort for Remaining Waves**

For each remaining task, assign it to a wave using this formula:

```
wave(task) = max(wave(dep) for dep in hard_deps(task)) + 1
```

In plain language: a task's wave number is one greater than the highest wave number among all of its hard dependencies. Continue until every task is assigned to a wave.

**Step 4 — Validate No Intra-Wave Conflicts**

Within each wave, verify that no two tasks write to the same file. If two tasks in the same wave both write to the same file, move one of them to the next wave (prefer moving the task with fewer downstream dependents).

**Step 5 — Optimize Wave Count**

If a task could validly be placed in Wave 2 or Wave 3 (i.e., all its hard dependencies are satisfied by Wave 1), prefer the earlier wave. This maximizes parallelism and reduces the total number of sequential waves.

### Worked Notation

Given tasks T1 through T5 with hard dependencies:

```
hard_deps(T1) = {}           -> wave(T1) = 0 + 1 = 1
hard_deps(T2) = {}           -> wave(T2) = 0 + 1 = 1
hard_deps(T3) = {T1}         -> wave(T3) = max(1) + 1 = 2
hard_deps(T4) = {T1, T2}     -> wave(T4) = max(1, 1) + 1 = 2
hard_deps(T5) = {T3}         -> wave(T5) = max(2) + 1 = 3
```

Result: Wave 1 = {T1, T2}, Wave 2 = {T3, T4}, Wave 3 = {T5}

---

## 4. File Overlap Detection

Use a matrix format to detect conflicts between tasks in the same wave. List every file touched by any task and mark whether each task Writes (W) or Reads (R) that file.

### Matrix Format

```
File Overlap Matrix:
                    | Task A | Task B | Task C | Task D |
src/model.py        |   W    |   R    |   W    |        |
src/service.py      |        |   W    |        |   W    |
tests/test_model.py |   W    |        |   W    |        |
```

Legend:
- **W** = task writes (creates or modifies) this file
- **R** = task reads (imports or references) this file

### Conflict Rules

| Same-wave combination     | Verdict              | Action                                              |
|---------------------------|----------------------|-----------------------------------------------------|
| Two tasks both Write (W/W) | **CONFLICT**         | Move one task to the next wave                      |
| One Writes, one Reads (W/R) | **POTENTIAL CONFLICT** | Check if the read depends on that specific write. If yes, it is a hard dependency and they cannot be in the same wave. If no (the file already exists and the write is additive), it may be safe. |
| Two tasks both Read (R/R)  | **NO CONFLICT**      | Safe to keep in the same wave                       |

### How to Build the Matrix

1. For each task, list every file path it will create, modify, or read.
2. Create rows for each unique file path.
3. Fill in W or R for each task.
4. Scan each row for same-wave conflicts using the rules above.

---

## 5. Parallelization Safety Checklist

Before finalizing wave assignments, verify that ALL of the following conditions are true for every pair of tasks within the same wave:

- [ ] No shared writable files between the tasks
- [ ] No data dependencies between the tasks (neither reads the other's output)
- [ ] No API dependencies between the tasks (neither calls an endpoint the other implements)
- [ ] No shared test fixtures being modified (reading shared fixtures is OK; writing to them is not)
- [ ] No database schema changes that affect both tasks
- [ ] No shared configuration files being modified by both tasks

If ANY condition fails for a pair of tasks, they cannot be in the same wave. Move one to a later wave.

---

## 6. Wave 0 Design

Wave 0 is a dedicated wave for test infrastructure. It must complete before any implementation wave begins. No implementation code goes in Wave 0.

### What Goes in Wave 0

1. **Test framework configuration**: Any setup needed for the test runner to work. Examples:
   - `pytest.ini` or `conftest.py` for Python
   - `jest.config.js` or `jest.setup.ts` for JavaScript/TypeScript
   - `build.sbt` test settings for Scala
   - Test-specific Gradle or Maven configuration
2. **Shared fixtures**: Test data, mock objects, factory functions, and builders that multiple tasks will use. These go here because implementation tasks should be able to import them immediately.
3. **Stub test files**: Empty or minimal test files with the correct directory structure. Their purpose is to verify that the test framework discovers and runs tests in the expected locations.
4. **CI verification**: A command (or set of commands) to run that proves tests execute correctly, even when all tests are stubs.

### Wave 0 Success Criteria

All of the following must be true before moving to Wave 1:

- [ ] Test framework runs successfully (no configuration errors)
- [ ] Stub tests pass (exit code 0)
- [ ] Shared fixtures are importable and accessible from test files
- [ ] The CI verification command exits with code 0

### Wave 0 Task Template

```
Task 0: Test Infrastructure Setup

Files to create/modify:
  - <test framework config file(s)>
  - <shared fixtures directory and files>
  - <stub test files>

Verification command:
  <command to run all tests, expecting 0 failures>

Acceptance criteria:
  - Test runner executes without errors
  - All stub tests pass
  - Shared fixtures are importable from any test file
```

---

## 7. Example Wave Analysis

This section walks through a complete wave analysis for a concrete scenario.

### Scenario

Building a user notification feature with 5 implementation tasks:

| Task | Description                                      |
|------|--------------------------------------------------|
| A    | Create notification model + tests                |
| B    | Create notification service (uses model) + tests |
| C    | Create email sender (standalone) + tests         |
| D    | Create notification API endpoint (uses service and email sender) + tests |
| E    | Create notification preferences (uses model) + tests |

### Step 1 — List Inputs and Outputs

| Task | Creates (W)                                    | Reads (R)                                |
|------|------------------------------------------------|------------------------------------------|
| A    | `src/models/notification.py`, `tests/test_notification_model.py` | (none beyond Wave 0 fixtures) |
| B    | `src/services/notification_service.py`, `tests/test_notification_service.py` | `src/models/notification.py` |
| C    | `src/services/email_sender.py`, `tests/test_email_sender.py` | (none beyond Wave 0 fixtures) |
| D    | `src/api/notification_endpoint.py`, `tests/test_notification_endpoint.py` | `src/services/notification_service.py`, `src/services/email_sender.py` |
| E    | `src/models/notification_preferences.py`, `tests/test_notification_preferences.py` | `src/models/notification.py` |

### Step 2 — Identify Hard Dependencies

| Dependent | Depends On | Reason                                                |
|-----------|------------|-------------------------------------------------------|
| B         | A          | Service imports and uses the notification model       |
| D         | B          | Endpoint imports and uses the notification service    |
| D         | C          | Endpoint imports and uses the email sender            |
| E         | A          | Preferences model references the notification model   |

Dependency graph:

```
A ----> B ----> D
 \              ^
  \---> E      /
               /
C -------------
```

### Step 3 — Apply Wave Formula

```
hard_deps(A) = {}        -> wave(A) = 0 + 1 = 1
hard_deps(C) = {}        -> wave(C) = 0 + 1 = 1
hard_deps(B) = {A}       -> wave(B) = max(1) + 1 = 2
hard_deps(E) = {A}       -> wave(E) = max(1) + 1 = 2
hard_deps(D) = {B, C}    -> wave(D) = max(2, 1) + 1 = 3
```

### Step 4 — File Overlap Check

Check tasks within the same wave for file conflicts.

**Wave 1 tasks: A, C**

```
File Overlap Matrix (Wave 1):
                                          | Task A | Task C |
src/models/notification.py                |   W    |        |
src/services/email_sender.py              |        |   W    |
tests/test_notification_model.py          |   W    |        |
tests/test_email_sender.py               |        |   W    |
```

No overlapping writes. Wave 1 is safe.

**Wave 2 tasks: B, E**

```
File Overlap Matrix (Wave 2):
                                              | Task B | Task E |
src/services/notification_service.py          |   W    |        |
src/models/notification_preferences.py        |        |   W    |
src/models/notification.py                    |   R    |   R    |
tests/test_notification_service.py            |   W    |        |
tests/test_notification_preferences.py        |        |   W    |
```

No overlapping writes. Both tasks read `src/models/notification.py` but neither writes it (Task A wrote it in Wave 1). R/R is no conflict. Wave 2 is safe.

**Wave 3 tasks: D (only one task)**

No intra-wave conflict possible with a single task.

### Step 5 — Final Wave Structure

```
Wave 0: Test Infrastructure
  - pytest configuration (conftest.py, pytest.ini)
  - Shared fixtures (mock notification data, test factories)
  - Stub test files for all 5 test modules
  - Verification: `pytest --collect-only` exits 0

Wave 1: Task A (notification model), Task C (email sender)
  - Independent, no shared files
  - Can be developed in parallel

Wave 2: Task B (notification service), Task E (notification preferences)
  - Both depend on Task A (Wave 1) only
  - No shared writable files
  - Can be developed in parallel

Wave 3: Task D (notification API endpoint)
  - Depends on Task B (Wave 2) and Task C (Wave 1)
  - Must wait for Wave 2 to complete
```

### Dependency Summary Table

| Task | Wave | Hard Dependencies | Soft Dependencies |
|------|------|-------------------|-------------------|
| 0    | 0    | (none)            | (none)            |
| A    | 1    | Task 0            | (none)            |
| C    | 1    | Task 0            | (none)            |
| B    | 2    | Task A            | (none)            |
| E    | 2    | Task A            | (none)            |
| D    | 3    | Task B, Task C    | (none)            |

Total waves (excluding Wave 0): 3
Maximum parallelism: 2 tasks (in Waves 1 and 2)

---

## Quick Reference

### Wave Assignment Formula

```
wave(task) = max(wave(dep) for dep in hard_deps(task)) + 1
```

If a task has no hard dependencies (other than Wave 0), its wave is 1.

### Conflict Detection Summary

| Situation                          | Same Wave? |
|------------------------------------|------------|
| No shared files                    | OK         |
| Both read same file                | OK         |
| One writes, other reads same file  | Check dependency direction |
| Both write same file               | NOT OK — move one to later wave |

### Checklist Before Finalizing Waves

1. Every task is assigned to exactly one wave.
2. No task appears before all of its hard dependencies.
3. No two tasks in the same wave write to the same file.
4. Wave 0 contains only test infrastructure, no implementation.
5. Tasks are placed in the earliest valid wave to maximize parallelism.
6. The parallelization safety checklist passes for every same-wave pair.
