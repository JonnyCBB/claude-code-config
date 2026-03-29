# [Feature Name] Implementation Plan

**Date**: YYYY-MM-DD
**Ticket**: [TICKET-NNN](link) *(optional)*
**Author**: Agent-generated via create-plan-tdd skill
**Location**: `~/.claude/thoughts/shared/plans/YYYY-MM-DD-description.md`

---

## Overview

{{Brief description of what we are implementing and why. 2-4 sentences covering the motivation, the user-facing or system-facing outcome, and the TDD approach we will follow.}}

---

## Current State Analysis

{{Describe the existing code landscape relevant to this feature. Include file:line references for every claim.}}

| Artifact | Path | Relevance |
|----------|------|-----------|
| [Existing module] | `path/to/file.ext:L##` | [Why it matters] |
| [Test infrastructure] | `path/to/test_config.ext` | [Current test setup] |
| [Related feature] | `path/to/related.ext:L##` | [How it connects] |

**Key Discoveries**:
- {{Discovery 1 with `file:line` reference}}
- {{Discovery 2 with `file:line` reference}}
- {{Discovery 3 with `file:line` reference}}

---

## Desired End State

{{Describe what the system looks like when this plan is fully implemented.}}

**Specification**:
- {{Behavior 1}}
- {{Behavior 2}}
- {{Behavior 3}}

**Verification Criteria**:

*Automated*:
- [ ] {{Automated check 1 — e.g., all new unit tests pass}}
- [ ] {{Automated check 2 — e.g., integration test suite green}}
- [ ] {{Automated check 3 — e.g., lint/type-check passes}}

*Manual*:
- [ ] {{Manual check 1 — e.g., feature works end-to-end in staging}}
- [ ] {{Manual check 2 — e.g., error case handled gracefully}}

---

## What We're NOT Doing

- {{Explicit exclusion 1 — e.g., "No migration of legacy data"}}
- {{Explicit exclusion 2 — e.g., "No UI changes in this plan"}}
- {{Explicit exclusion 3 — e.g., "Performance optimization deferred to follow-up"}}

---

## Implementation Approach

{{High-level description of the TDD + wave strategy. Explain why tasks are grouped into waves, how RED/GREEN/REFACTOR cycles work within each task, and how Wave 0 sets the foundation.}}

**Strategy Summary**:
1. **Wave 0** establishes test infrastructure so every subsequent wave can run tests immediately.
2. Tasks within a wave are independent and can execute in parallel.
3. Each task follows a strict RED -> GREEN -> REFACTOR cycle.
4. Waves execute sequentially; all tasks in Wave N must complete before Wave N+1 starts.

---

## Existing Patterns Analysis

{{Search the codebase for reusable abstractions before writing new code. Document what you find.}}

| Pattern | Location | Usage Count | Applicable? |
|---------|----------|-------------|-------------|
| [Abstract class / interface] | `path/to/pattern.ext` | N usages | Yes / No — [reason] |
| [Test base class / fixture] | `path/to/test_base.ext` | N usages | Yes / No — [reason] |
| [Utility / helper] | `path/to/util.ext` | N usages | Yes / No — [reason] |

**Decisions**:
- {{Which patterns we will reuse and why}}
- {{Which patterns we will NOT reuse and why}}

**Deviations from Prior Research**:
- {{If the approach differs from a prior research doc, explain why here. If no prior research, state "N/A".}}

---

## Coding Guidelines

{{Search the target repo for coding standards and guidelines. Document what you find.}}

| Source | Location | Key Rules |
|--------|----------|-----------|
| [CONTRIBUTING.md] | `path/to/CONTRIBUTING.md` | [Summarize key rules] |
| [.editorconfig] | `.editorconfig` | [Summarize settings] |
| [CLAUDE.md] | `CLAUDE.md` | [Summarize relevant instructions] |
| [Lint config] | `path/to/lint_config` | [Summarize key rules] |

{{If no guidelines found, state: "No repo-specific coding guidelines discovered."}}

**Key constraints for implementation agents:**
- {{Constraint 1 derived from guidelines — e.g., "Use 4-space indentation per .editorconfig"}}
- {{Constraint 2 — e.g., "All public methods must have Javadoc per CONTRIBUTING.md"}}
- {{Constraint 3 — e.g., "No wildcard imports per CLAUDE.md"}}

---

## File Structure

{{Map ALL files that will be created or modified BEFORE decomposing into tasks. This section constrains task decomposition — tasks are designed to produce these files, not the other way around.}}

### New Files

| File Path | Purpose | Responsibility | Interface |
|-----------|---------|---------------|-----------|
| `path/to/new_file.ext` | {{Why this file exists}} | {{Single responsibility}} | {{Public methods/exports}} |

### Modified Files

| File Path | Current Responsibility | Planned Changes | Growth Estimate |
|-----------|----------------------|-----------------|-----------------|
| `path/to/existing.ext` | {{What it does now}} | {{What changes}} | {{+N lines}} |

### File Structure Principles

- Each file has **one clear responsibility** with a well-defined interface
- New files should be **small and focused** — prefer many small files over few large ones
- Tasks in the Wave Analysis MUST map to files listed here — flag any task that creates files not in this structure

---

## Wave Analysis

### Dependency Table

| Task | Depends On | Files Touched | Wave Assignment |
|------|-----------|---------------|-----------------|
| 0.1: [Test infrastructure setup] | None | `test config files` | Wave 0 |
| 1.1: [Task name] | Wave 0 | `path/to/file_a.ext`, `path/to/test_a.ext` | Wave 1 |
| 1.2: [Task name] | Wave 0 | `path/to/file_b.ext`, `path/to/test_b.ext` | Wave 1 |
| 2.1: [Task name] | 1.1 | `path/to/file_c.ext`, `path/to/test_c.ext` | Wave 2 |
| 2.2: [Task name] | 1.2 | `path/to/file_a.ext`, `path/to/test_d.ext` | Wave 2 |

### File Overlap Matrix

{{Show which tasks touch the same files. This identifies potential merge conflicts when tasks run in parallel.}}

| File | Task 1.1 | Task 1.2 | Task 2.1 | Task 2.2 |
|------|----------|----------|----------|----------|
| `path/to/file_a.ext` | W | - | - | W |
| `path/to/file_b.ext` | - | W | - | - |
| `path/to/test_a.ext` | W | - | - | - |

*W = Write, R = Read only, - = Not touched*

**Intra-Wave File Conflicts**:
- {{List any files written by multiple tasks in the SAME wave. These are conflicts that must be resolved by reordering tasks or merging them.}}
- {{If none, state "No intra-wave file conflicts detected."}}

---

## Parallelization Plan

### Wave Execution Schedule

| Wave | Tasks | Max Concurrency | Estimated Duration |
|------|-------|----------------|--------------------|
| 0 | 0.1: Test infrastructure | 1 | {{estimate}} |
| 1 | 1.1: [name], 1.2: [name] | 2 | {{estimate}} |
| 2 | 2.1: [name], 2.2: [name] | 2 | {{estimate}} |

### Agent Selection

| Task | Agent Type | Rationale |
|------|-----------|-----------|
| 0.1 | {{e.g., infrastructure agent}} | {{Why this agent type}} |
| 1.1 | {{e.g., backend agent}} | {{Why this agent type}} |
| 1.2 | {{e.g., backend agent}} | {{Why this agent type}} |

---

## Wave 0: Test Infrastructure

**Objective**: Establish the test foundation so that all subsequent waves can write and run tests from the first RED step.

### Test Framework Configuration

- **Framework**: {{e.g., JUnit 5, pytest, Jest, etc.}}
- **Runner**: {{e.g., Maven Surefire, pytest, npm test}}
- **Coverage tool**: {{e.g., JaCoCo, coverage.py, Istanbul}} *(optional)*

**Setup tasks**:
- [ ] {{Add test dependencies to build file if not present}}
- [ ] {{Configure test runner settings}}
- [ ] {{Set up test source directories}}

### Shared Fixtures and Test Utilities

{{List any shared test helpers, fixtures, factories, or mocks that multiple waves will need.}}

- **File**: `path/to/test_fixtures.ext`
  - {{Fixture 1 description}}
  - {{Fixture 2 description}}

- **File**: `path/to/test_utils.ext`
  - {{Utility 1 description}}
  - {{Utility 2 description}}

### Stub Test File

{{Create a minimal stub test to verify the test infrastructure works end-to-end.}}

**File**: `path/to/stub_test.ext`

```[language]
// Stub test to verify test infrastructure
// This test should pass immediately after Wave 0 setup
[stub test code]
```

### CI Verification

**Command**:
```bash
[command to run the stub test and verify infrastructure works]
```

### Wave 0 Success Criteria

*Automated*:
- [ ] Stub test passes
- [ ] Test runner produces output in expected format
- [ ] Shared fixtures importable from test files

*Manual*:
- [ ] Test command runs without configuration errors

---

## Phase 1: [Wave 1 Name]

{{Description of what this wave accomplishes and why these tasks are grouped together.}}

### Task 1.1: [Task Name]

**Wave**: 1

#### RED -- Write failing test

**Test file**: `path/to/test_file.ext`
**Behavior**: [What the test verifies — describe the expected behavior in plain language]

```[language]
// Test code here
// This test MUST fail before the GREEN step
```

**Expected failure**: `[Expected error message or assertion failure text]`
**Run**:
```bash
[test command targeting this specific test]
```

#### GREEN -- Make it pass

**File**: `path/to/implementation.ext`
**Changes**: [Describe the minimal changes needed to make the test pass — no more, no less]

```[language]
// Implementation code here
// Only enough to make the failing test pass
```

**Run**: `[test command]` -- should pass

#### REFACTOR -- Clean up

**Focus**: [What to improve — naming, DRY, extract method, performance, readability, etc.]
**Constraint**: All tests must remain green
**Run**:
```bash
[full test suite command]
```

---

### Task 1.2: [Task Name]

**Wave**: 1

#### RED -- Write failing test

**Test file**: `path/to/test_file_b.ext`
**Behavior**: [What the test verifies]

```[language]
// Test code here
```

**Expected failure**: `[Expected error/assertion message]`
**Run**:
```bash
[test command]
```

#### GREEN -- Make it pass

**File**: `path/to/implementation_b.ext`
**Changes**: [Minimal changes to make the test pass]

```[language]
// Implementation code here
```

**Run**: `[test command]` -- should pass

#### REFACTOR -- Clean up

**Focus**: [Improvement areas]
**Constraint**: All tests must remain green
**Run**:
```bash
[full test suite command]
```

---

### Phase 1 Success Criteria

*Automated*:
- [ ] All Wave 1 tests pass: `[test command for wave 1]`
- [ ] No regressions in Wave 0 tests
- [ ] {{Additional automated checks}}

*Manual*:
- [ ] {{Manual verification relevant to this phase}}

---

## Phase 2: [Wave 2 Name]

{{Description of what this wave accomplishes. This wave depends on Phase 1 being complete.}}

### Task 2.1: [Task Name]

**Wave**: 2

#### RED -- Write failing test

**Test file**: `path/to/test_file_c.ext`
**Behavior**: [What the test verifies]

```[language]
// Test code here
```

**Expected failure**: `[Expected error/assertion message]`
**Run**:
```bash
[test command]
```

#### GREEN -- Make it pass

**File**: `path/to/implementation_c.ext`
**Changes**: [Minimal changes]

```[language]
// Implementation code here
```

**Run**: `[test command]` -- should pass

#### REFACTOR -- Clean up

**Focus**: [Improvement areas]
**Constraint**: All tests must remain green
**Run**:
```bash
[full test suite command]
```

---

### Phase 2 Success Criteria

*Automated*:
- [ ] All Wave 2 tests pass: `[test command for wave 2]`
- [ ] No regressions in Wave 0 or Wave 1 tests
- [ ] Full suite green: `[full test suite command]`

*Manual*:
- [ ] {{Manual verification for this phase}}

---

*{{Repeat Phase N sections as needed for additional waves.}}*

---

## Testing Strategy

### Unit Tests
- **Scope**: {{What unit tests cover — individual functions, classes, methods}}
- **Location**: `path/to/unit/tests/`
- **Run**: `[unit test command]`

### Integration Tests
- **Scope**: {{What integration tests cover — cross-module interactions, API contracts, database access}}
- **Location**: `path/to/integration/tests/`
- **Run**: `[integration test command]`

### Manual Testing
- {{Manual test scenario 1}}
- {{Manual test scenario 2}}

---

## Performance Considerations

- {{Performance consideration 1 — e.g., "New query adds an index lookup; measure latency impact"}}
- {{Performance consideration 2 — e.g., "Batch size tuned to avoid memory pressure"}}
- {{If none, state "No significant performance implications identified."}}

---

## Migration Notes

- {{Migration step 1 — e.g., "Run database migration before deploying new code"}}
- {{Migration step 2 — e.g., "Feature flag `NEW_FEATURE` must be enabled after deploy"}}
- {{If none, state "No migration steps required."}}

---

## References

- [Ticket: TICKET-NNN](link) — {{Brief description}}
- [Research doc](link) — {{Brief description, if prior research exists}}
- [Similar implementation](link or `path/to/file.ext`) — {{What pattern it demonstrates}}
- [Relevant documentation](link) — {{What it covers}}
