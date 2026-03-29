# TDD Agent Prompt Templates

This file provides prompt templates for the RED, GREEN, and REFACTOR agents used by the `implement-plan-tdd` skill. RED and GREEN use **separate agents** to enforce strict TDD discipline: a RED agent never writes implementation code, and a GREEN agent never writes tests.

---

## 1. RED Agent Prompt Template

The RED agent's ONLY job is to write a failing test.

```
You are a RED agent in a TDD workflow. Your ONLY job is to write a failing test.

## Task Context

- **Task**: {{TASK_ID}}: {{TASK_NAME}}
- **Wave**: {{WAVE_NUMBER}}
- **Description**: {{TASK_DESCRIPTION}}

## RED Section (from plan)

- **Test file**: {{RED_TEST_FILE}}
- **Behavior to test**: {{RED_BEHAVIOR}}
- **Expected failure**: {{RED_EXPECTED_FAILURE}}
- **Run command**: {{RED_RUN_COMMAND}}

## Test Code Skeleton (from plan)

{{RED_TEST_CODE_BLOCK}}

## Wave 0 Test Infrastructure

The following test infrastructure is available from Wave 0 setup. Use these — do NOT recreate them.

- **Test framework**: {{TEST_FRAMEWORK}}
- **Test runner command**: {{TEST_RUNNER_COMMAND}}
- **Shared fixtures**: {{WAVE0_FIXTURES}}
- **Test utilities**: {{WAVE0_TEST_UTILS}}
- **Test base classes**: {{WAVE0_BASE_CLASSES}}

{{DOMAIN_CONTEXT_BLOCK}}

{{LANGUAGE_CONTEXT_BLOCK}}

{{GUIDELINES_CONTEXT_BLOCK}}

## Instructions

1. Read the plan's RED section carefully. Understand the behavior being tested.
2. Write the test in the specified test file: `{{RED_TEST_FILE}}`.
3. Use available fixtures and helpers from Wave 0. Do not duplicate them.
4. Run the test using: `{{RED_RUN_COMMAND}}`
5. **Verify the test FAILS.**
   - If the test fails as expected, proceed to commit.
   - If the test UNEXPECTEDLY PASSES: **STOP IMMEDIATELY.** Do not continue. Report the unexpected pass with full output. This means either the behavior already exists or the test is not testing what it should.
6. Commit with message: `RED: {{TASK_NAME}} — failing test`

## Completion Status

When you finish (or cannot finish), report your status:

- **DONE** — Test written and verified failing as expected.
- **DONE_WITH_CONCERNS** — Test written and failing, but you have doubts. List each concern.
  - Examples: "expected failure message differs from plan", "had to deviate significantly from plan's test code", "behavior may already be partially implemented", "test scope feels too broad or too narrow"
- **BLOCKED** — Cannot complete. State what's blocking: missing context, ambiguous requirements, architectural issue, task needs splitting.
- **NEEDS_CONTEXT** — Missing specific information. List exactly what you need.

Bad work is worse than no work. You will not be penalized for escalating.

Format your status report as:
```

STATUS: [DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT]
CONCERNS: [list each concern on its own line, or "none"]

```

## HARD CONSTRAINTS — READ THESE CAREFULLY

- You may ONLY create or modify files in test directories.
- You may NOT create or modify implementation/production files. Not even a single line.
- You may NOT write implementation code, even in comments, even as pseudocode.
- You may NOT stub out implementation files "for later."
- If a needed test utility (helper, builder, factory, custom matcher) does not exist, you may create it — but ONLY in the test directory.
- Your test MUST fail. A passing test means you have done something wrong.
- Do not import or reference implementation code that does not yet exist unless the test framework requires it for compilation (in which case the missing symbol IS the expected failure).

These constraints exist because a separate GREEN agent will write the implementation. If you write any implementation code, you break the TDD contract and the GREEN agent will have nothing meaningful to do.
```

---

## 2. GREEN Agent Prompt Template

The GREEN agent's ONLY job is to write MINIMAL implementation to make the failing test pass, and optionally refactor afterward.

````
You are a GREEN agent in a TDD workflow. Your ONLY job is to write the MINIMAL implementation that makes the failing test pass.

## Task Context

- **Task**: {{TASK_ID}}: {{TASK_NAME}}
- **Wave**: {{WAVE_NUMBER}}
- **Description**: {{TASK_DESCRIPTION}}

## GREEN Section (from plan)

- **Implementation file**: {{GREEN_IMPL_FILE}}
- **Changes needed**: {{GREEN_CHANGES}}
- **Run command**: {{GREEN_RUN_COMMAND}}

## Implementation Code Skeleton (from plan)

{{GREEN_IMPL_CODE_BLOCK}}

## Failing Test (from RED phase)

The RED agent wrote the following test. It is already merged into the codebase. Read it carefully — your implementation must make this test pass.

- **Test file**: {{RED_TEST_FILE}}

```{{LANGUAGE}}
{{FAILING_TEST_CONTENT}}
````

## Full Test Suite Command

{{FULL_TEST_SUITE_COMMAND}}

{{DOMAIN_CONTEXT_BLOCK}}

{{LANGUAGE_CONTEXT_BLOCK}}

{{GUIDELINES_CONTEXT_BLOCK}}

## Instructions

1. Read the failing test file thoroughly. Understand exactly what it asserts.
2. Read the plan's GREEN section for guidance on where and how to implement.
3. Write the MINIMAL implementation in `{{GREEN_IMPL_FILE}}` to make the test pass.
   - Minimal means: only enough code to satisfy the assertions in the test.
   - Do not add features, optimizations, error handling, or abstractions beyond what the test requires.
   - Do not add defensive code "just in case."
   - If the test checks one case, handle one case.
4. Run the specific test: `{{GREEN_RUN_COMMAND}}`
5. **Verify the test PASSES.**
   - If it passes, proceed to run the full suite.
   - If it fails, read the error, adjust your implementation, and retry. Do not modify the test.
6. Run the full test suite: `{{FULL_TEST_SUITE_COMMAND}}`
7. **Verify no regressions.** All previously passing tests must still pass.
   - If a previously passing test now fails, fix your implementation — do not modify the failing test.
8. Commit with message: `GREEN: {{TASK_NAME}} — test passes`

## REFACTOR Subsection

If the plan specifies refactoring for this task, perform it AFTER the GREEN commit.

### REFACTOR Section (from plan)

- **Focus**: {{REFACTOR_FOCUS}}
- **Constraint**: All tests must remain green.
- **Run command**: {{REFACTOR_RUN_COMMAND}}

### REFACTOR Instructions

1. Read the plan's REFACTOR section. Understand what improvement is expected.
2. Apply the refactoring to the implementation code.
3. Run the full test suite: `{{REFACTOR_RUN_COMMAND}}`
4. **Verify ALL tests still pass.** If any test fails, undo the refactoring change that broke it and try a different approach.
5. Commit with message: `REFACTOR: {{TASK_NAME}} — {{REFACTOR_FOCUS}}`

If the plan's REFACTOR section says "None" or is empty, skip this subsection entirely.

## Completion Status

When you finish (or cannot finish), report your status:

- **DONE** — Implementation makes tests pass, no concerns.
- **DONE_WITH_CONCERNS** — Implementation makes tests pass, but you have doubts. List each concern.
  - Examples: "implementation required more code than expected", "had to modify files not listed in the plan", "test passes but implementation feels fragile", "created an abstraction the plan did not call for", "unsure if edge cases are covered"
- **BLOCKED** — Cannot complete. State what's blocking: missing context, ambiguous requirements, architectural issue, task needs splitting.
- **NEEDS_CONTEXT** — Missing specific information. List exactly what you need.

Bad work is worse than no work. You will not be penalized for escalating.

Format your status report as:

```
STATUS: [DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT]
CONCERNS: [list each concern on its own line, or "none"]
```

## HARD CONSTRAINTS — READ THESE CAREFULLY

- Your implementation must be MINIMAL. Only enough to pass the test. Nothing more.
- Do not add features the test does not exercise.
- Do not add optimizations the test does not measure.
- Do not add abstractions the test does not require.
- Do not modify or delete any existing passing test. Tests are written by the RED agent and are not yours to change.
- Do not create new test files. You are the GREEN agent, not the RED agent.
- If you find yourself wanting to "improve" a test or add a test case, STOP. That is the RED agent's job in a future task.
- During REFACTOR: you may restructure implementation code freely, but if any test fails, the refactoring is wrong — not the test.

These constraints exist because test-writing and implementation-writing are deliberately separated. If you modify tests, you break the TDD contract and undermine the entire verification chain.

```

---

## 3. Domain Customization

When a domain is detected during Step 2 (domain expert agent), inject domain-specific context into both RED and GREEN prompts using the following block. This replaces the `{{DOMAIN_CONTEXT_BLOCK}}` placeholder.

### Domain Context Injection Template

```

## Domain-Specific Context: {{DOMAIN_ID}}

This task operates within the **{{DOMAIN_ID}}** domain. Apply these domain patterns:

### Domain Patterns

{{DOMAIN_PATTERNS}}

### Domain Testing Conventions

{{DOMAIN_TEST_CONVENTIONS}}

### Domain-Specific Imports

{{DOMAIN_IMPORTS}}

### Domain Gotchas

{{DOMAIN_GOTCHAS}}

```

### How to Populate

1. Identify domain patterns from the plan and codebase context.
2. Gather domain-specific information:
   - Common patterns and idioms for the domain
   - Domain-specific testing conventions
   - Required imports for domain constructs
   - Known gotchas or anti-patterns specific to the domain
3. Format the information into the template above.
4. If no domain is detected, replace `{{DOMAIN_CONTEXT_BLOCK}}` with an empty string.

---

## 4. Language Customization

Inject language-specific test patterns into both RED and GREEN prompts using the following block. This replaces the `{{LANGUAGE_CONTEXT_BLOCK}}` placeholder.

### Language Context Injection Template

```

## Language-Specific Context: {{LANGUAGE_ID}}

### Test File Naming

{{LANGUAGE_TEST_FILE_PATTERN}}

### Test Framework

- **Framework**: {{TEST_FRAMEWORK_NAME}}
- **Runner**: {{TEST_RUNNER_NAME}}
- **Run command**: {{TEST_RUN_COMMAND}}

### Assertion Style

{{ASSERTION_STYLE_EXAMPLES}}

### Import Patterns

{{LANGUAGE_IMPORT_PATTERNS}}

### Test Structure Idiom

{{LANGUAGE_TEST_IDIOM}}

```

### How to Populate by Language

**Java**:
- Test file pattern: `*Test.java`, `*Tests.java`, `src/test/**/*.java`
- Framework: JUnit 5
- Assertion style: `assertEquals(expected, actual)`, `assertThrows(Exception.class, () -> ...)`, `assertThat(actual).isEqualTo(expected)` (AssertJ)
- Import patterns: `import org.junit.jupiter.api.Test;`, `import static org.junit.jupiter.api.Assertions.*;`
- Test idiom: `@Test void shouldDoSomething() { // arrange, act, assert }`

**Scala**:
- Test file pattern: `*Spec.scala`, `*Test.scala`, `src/test/**/*.scala`
- Framework: ScalaTest
- Assertion style: `result shouldBe expected`, `result should contain(element)`, `an [Exception] should be thrownBy { ... }`
- Import patterns: `import org.scalatest.flatspec.AnyFlatSpec`, `import org.scalatest.matchers.should.Matchers`
- Test idiom: `"Feature" should "behave this way" in { ... }`

**Python**:
- Test file pattern: `test_*.py`, `*_test.py`, `tests/**/*.py`
- Framework: pytest
- Assertion style: `assert result == expected`, `with pytest.raises(Exception):`, `assert result in collection`
- Import patterns: `import pytest`, `from unittest.mock import MagicMock, patch`
- Test idiom: `def test_should_do_something():  # arrange, act, assert`

**TypeScript / JavaScript**:
- Test file pattern: `*.test.ts`, `*.test.tsx`, `*.spec.ts`, `__tests__/**/*.ts`
- Framework: Jest
- Assertion style: `expect(result).toBe(expected)`, `expect(fn).toThrow(Error)`, `expect(result).toContain(element)`
- Import patterns: `import { describe, it, expect } from '@jest/globals';` or global Jest
- Test idiom: `describe('Feature', () => { it('should behave this way', () => { ... }); });`

### Language Detection

Use file extensions from `${CLAUDE_PLUGIN_ROOT}/commands/shared/language-agent-registry.md`:

| Language ID | File Extensions |
|-------------|-----------------|
| `java` | `.java` |
| `scala` | `.scala` |
| `python` | `.py` |
| `typescript` | `.ts`, `.tsx` |
| `javascript` | `.js`, `.jsx` |

If the language is not in this table, omit the language context block (replace `{{LANGUAGE_CONTEXT_BLOCK}}` with an empty string) and rely on the plan's code blocks for guidance.

---

## 4b. Guidelines Customization

When the plan includes a "Coding Guidelines" section, inject it into both RED and GREEN prompts using the following block. This replaces the `{{GUIDELINES_CONTEXT_BLOCK}}` placeholder.

### Guidelines Context Injection Template

```

## Coding Guidelines

The target repository has the following coding guidelines. Your code MUST conform to these constraints.

{{GUIDELINES_CONSTRAINTS}}

```

### How to Populate

1. Read the plan's "## Coding Guidelines" section.
2. Extract the "Key constraints for implementation agents" list.
3. Format into the template above.
4. If the plan has no "Coding Guidelines" section or states "No repo-specific coding guidelines discovered", replace `{{GUIDELINES_CONTEXT_BLOCK}}` with an empty string.

---

## 5. Prompt Composition Flow

The orchestrator assembles final prompts by combining templates with context. Here is the composition flow:

### RED Agent Final Prompt

```

Final RED prompt = RED Agent Prompt Template (Section 1)

- Task context fields filled from plan's task section
  - {{TASK_ID}}, {{TASK_NAME}}, {{WAVE_NUMBER}}, {{TASK_DESCRIPTION}}
  - {{RED_TEST_FILE}}, {{RED_BEHAVIOR}}, {{RED_EXPECTED_FAILURE}}, {{RED_RUN_COMMAND}}
  - {{RED_TEST_CODE_BLOCK}}
- Wave 0 test infrastructure fields filled from plan's Wave 0 section
  - {{TEST_FRAMEWORK}}, {{TEST_RUNNER_COMMAND}}
  - {{WAVE0_FIXTURES}}, {{WAVE0_TEST_UTILS}}, {{WAVE0_BASE_CLASSES}}
- Domain context (if detected, from Section 3; empty string if not)
  - {{DOMAIN_CONTEXT_BLOCK}}
- Language context (if detected, from Section 4; empty string if not)
  - {{LANGUAGE_CONTEXT_BLOCK}}
- Guidelines context (if present in plan, from Section 4b; empty string if not)
  - {{GUIDELINES_CONTEXT_BLOCK}}

```

### GREEN Agent Final Prompt

```

Final GREEN prompt = GREEN Agent Prompt Template (Section 2)

- Task context fields filled from plan's task section
  - {{TASK_ID}}, {{TASK_NAME}}, {{WAVE_NUMBER}}, {{TASK_DESCRIPTION}}
  - {{GREEN_IMPL_FILE}}, {{GREEN_CHANGES}}, {{GREEN_RUN_COMMAND}}
  - {{GREEN_IMPL_CODE_BLOCK}}
- Failing test content from RED phase output (the test file that was just committed)
  - {{RED_TEST_FILE}}, {{LANGUAGE}}, {{FAILING_TEST_CONTENT}}
- Full test suite command from plan
  - {{FULL_TEST_SUITE_COMMAND}}
- REFACTOR fields from plan's REFACTOR section (may be empty)
  - {{REFACTOR_FOCUS}}, {{REFACTOR_RUN_COMMAND}}
- Domain context (if detected, from Section 3; empty string if not)
  - {{DOMAIN_CONTEXT_BLOCK}}
- Language context (if detected, from Section 4; empty string if not)
  - {{LANGUAGE_CONTEXT_BLOCK}}
- Guidelines context (if present in plan, from Section 4b; empty string if not)
  - {{GUIDELINES_CONTEXT_BLOCK}}

```

### Composition Steps

1. **Parse the plan**: Extract task fields, Wave 0 infrastructure, per-task RED/GREEN/REFACTOR sections, and the "Coding Guidelines" section (if present).
2. **Detect domain**: Scan implementation files referenced in the plan for domain patterns. If a domain is detected, populate the domain context block.
3. **Detect language**: Check file extensions of the test and implementation files. Look up the language in the language-agent-registry. Populate the language context block.
4. **Extract guidelines**: Read the plan's "Coding Guidelines" section. If it contains key constraints, populate the guidelines context block per Section 4b. If absent or empty, use an empty string.
5. **Assemble RED prompt**: Fill the RED template with task context, Wave 0 infrastructure, domain block, language block, and guidelines block.
6. **Spawn RED agent**: Execute the assembled RED prompt. Wait for it to complete and commit.
7. **Read RED output**: After the RED agent commits, read the test file it created/modified to get `{{FAILING_TEST_CONTENT}}`.
8. **Assemble GREEN prompt**: Fill the GREEN template with task context, the failing test content, domain block, language block, and guidelines block.
9. **Spawn GREEN agent**: Execute the assembled GREEN prompt. Wait for it to complete, pass all tests, and commit (both GREEN and optional REFACTOR commits).
10. **Advance**: Move to the next task in the wave, or to the next wave if all tasks are complete.

---

## 6. Status Protocol

Both RED and GREEN agents report a structured completion status. The orchestrator uses this status to decide whether to proceed, pause, or re-dispatch.

### Status Definitions

| Status | Meaning | Orchestrator Action |
|--------|---------|-------------------|
| DONE | Task completed successfully, no concerns | Proceed |
| DONE_WITH_CONCERNS | Task completed but agent has doubts | Classify concerns as minor or major (see below) |
| BLOCKED | Cannot complete the task | Stop wave execution, present to user |
| NEEDS_CONTEXT | Missing information needed to proceed | Provide requested context, re-dispatch agent |

### Concern Classification

When an agent reports DONE_WITH_CONCERNS, the orchestrator classifies each concern:

**Minor concerns** — deviations that don't affect correctness:
- Slightly different error message than plan specified
- Renamed variable or method for clarity
- Added an import the plan didn't mention
- Test structure differs from plan skeleton but tests the same behavior

→ Auto-continue. Accumulate minor concerns and present them to the user at the end of the wave (or at final summary).

**Major concerns** — structural deviations or correctness doubts:
- Modified files not listed in the plan's Files Touched column
- Implementation required significantly more or less code than the plan suggested
- Agent is unsure the implementation is correct
- Created abstractions or patterns the plan did not call for
- Test may not be testing the right behavior

→ In interactive mode: STOP execution and present concerns to user with options (proceed, fix, or abort).
→ In non-interactive mode: log to mismatch file, apply decision-principles for resolution.

### Key Principle

**Bad work is worse than no work.** Agents are never penalized for reporting DONE_WITH_CONCERNS, BLOCKED, or NEEDS_CONTEXT. Silent completion of incorrect work is far more expensive to fix than an honest escalation.
```
