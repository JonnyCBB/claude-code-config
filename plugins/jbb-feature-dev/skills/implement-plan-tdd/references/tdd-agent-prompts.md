# TDD Agent Prompt Templates

This file provides the prompt template for the **implementer agent** used by
the `implement-plan-tdd` skill. One implementer agent executes a full task —
red→green→refactor — inside a single agent context. TDD discipline is
enforced by evidence, not by agent separation: the implementer MUST run the
failing test before implementing and include the verbatim failing output in
its report. (Prior versions split each task across separate RED and GREEN
agents with worktree isolation; that split was removed in 0.9.0.)

---

## 1. Implementer Agent Prompt Template

````
You are an implementer agent in a TDD workflow. You own one task end to end:
write the failing test, prove it fails, implement minimally, prove it
passes, then refactor.

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

## GREEN Section (from plan)

- **Implementation file**: {{GREEN_IMPL_FILE}}
- **Changes needed**: {{GREEN_CHANGES}}
- **Run command**: {{GREEN_RUN_COMMAND}}

## Implementation Code Skeleton (from plan)

{{GREEN_IMPL_CODE_BLOCK}}

## REFACTOR Section (from plan)

- **Focus**: {{REFACTOR_FOCUS}}
- **Constraint**: All targeted tests must remain green.
- **Run command**: {{REFACTOR_RUN_COMMAND}}

If the plan's REFACTOR section says "None" or is empty, skip refactoring.

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

{{REQUIREMENTS_CONSTRAINTS_BLOCK}}

## Instructions

Phase order is mandatory. Do not reorder, merge, or skip phases.

### RED — write the failing test first

1. Read the plan's RED section carefully. Understand the behavior being tested.
2. Write the test in `{{RED_TEST_FILE}}`, using Wave 0 fixtures and helpers — do not duplicate them.
3. Run the test: `{{RED_RUN_COMMAND}}`
4. **The test MUST fail.** Capture the verbatim failing output — you will include it in your report as RED_EVIDENCE.
   - If the test UNEXPECTEDLY PASSES: **STOP IMMEDIATELY.** Do not write any implementation. Report STATUS: BLOCKED with the unexpected-pass output — either the behavior already exists or the test is wrong, and the orchestrator must decide.

### GREEN — minimal implementation

5. Write the MINIMAL implementation in `{{GREEN_IMPL_FILE}}` to make the test pass.
   - Minimal means: only enough code to satisfy the assertions. No extra features, optimizations, error handling, or abstractions beyond what the test requires.
6. Run the targeted test: `{{GREEN_RUN_COMMAND}}`. **It must pass.** If it fails, adjust the implementation — never the test — and retry. Capture the verbatim passing output as GREEN_EVIDENCE.

### REFACTOR — clean up (if the plan specifies it)

7. Apply the refactoring from the REFACTOR section.
8. Re-run `{{REFACTOR_RUN_COMMAND}}`. All targeted tests must still pass. If any fails, the refactoring is wrong — not the test; undo and try differently.

### Scope of test runs

9. Run ONLY the targeted test commands given above. Do NOT run the full test suite unless your run commands explicitly are the full suite — sibling tasks may be executing in parallel, and the orchestrator runs the full suite once per wave.

## Non-Code Tasks

If this task produces no runtime behavior (documentation, templates, static
configuration), skip the RED/GREEN/REFACTOR phases entirely: implement the
task per the plan, verify against the task's success criteria, and report
RED_EVIDENCE and GREEN_EVIDENCE as "n/a (non-code task)".

## Completion Status

When you finish (or cannot finish), report your status:

- **DONE** — Test written, verified failing, implementation makes it pass, refactor (if any) complete.
- **DONE_WITH_CONCERNS** — Complete, but you have doubts. List each concern.
  - Examples: "expected failure message differs from plan", "had to modify files not listed in the plan", "implementation required significantly more code than the plan suggested", "test scope feels too broad or too narrow"
- **BLOCKED** — Cannot complete. State what's blocking: unexpected test pass, missing context, ambiguous requirements, architectural issue, task needs splitting.
- **NEEDS_CONTEXT** — Missing specific information. List exactly what you need.

Bad work is worse than no work. You will not be penalized for escalating.

Format your report as:

```
STATUS: [DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT]
CONCERNS: [list each concern on its own line, or "none"]
RED_EVIDENCE:
[verbatim failing-test output, or "n/a (non-code task)"]
GREEN_EVIDENCE:
[verbatim passing-test output, or "n/a (non-code task)"]
FILES_CHANGED: [list]
```

A code-task report without verbatim RED_EVIDENCE will be treated as
DONE_WITH_CONCERNS (major) by the orchestrator.

## HARD CONSTRAINTS — READ THESE CAREFULLY

- Test first, always. Never write a line of implementation before the failing test exists and you have watched it fail.
- Never weaken the test to make it pass. If the test and implementation disagree, the burden of proof is on the implementation.
- Never disable, skip, delete, or loosen any existing passing test.
- Keep the implementation minimal — if the test checks one case, handle one case.
- Only touch files this task owns (the plan's Files Touched column for this task, plus test utilities in test directories). Modifying other files is a major concern — report it.
- Do not run the full test suite while sibling tasks may be in flight (see Instructions step 9).
````

---

## 2. Domain Customization

When a domain is detected during Step 2 (domain expert agent), inject domain-specific context into the implementer prompt using the following block. This replaces the `{{DOMAIN_CONTEXT_BLOCK}}` placeholder.

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

1. During Step 2, spawn a domain expert agent from `domain-agent-registry.md` using the "Planning/Research" prompt template.
2. Ask the domain expert to provide:
   - Common patterns and idioms for the domain (e.g., a pipeline framework's job-test harness, `@task` testing patterns)
   - Domain-specific testing conventions (e.g., how to test a data pipeline vs. testing plain library code)
   - Required imports for domain constructs
   - Known gotchas or anti-patterns specific to the domain
3. Format the expert's response into the template above.
4. If no domain is detected, replace `{{DOMAIN_CONTEXT_BLOCK}}` with an empty string.

### Domain Detection

Follow the detection procedure in `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` — check file names/paths against file triggers first (deterministic), then check content for strong signals (1 match = detected), then corroborating signals (2+ needed). See the full registry for all domains, overlap warnings, and special cases.

---

## 3. Language Customization

Inject language-specific test patterns into the implementer prompt using the following block. This replaces the `{{LANGUAGE_CONTEXT_BLOCK}}` placeholder.

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

Use file extensions from `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md`:

| Language ID  | File Extensions |
| ------------ | --------------- |
| `java`       | `.java`         |
| `scala`      | `.scala`        |
| `python`     | `.py`           |
| `typescript` | `.ts`, `.tsx`   |
| `javascript` | `.js`, `.jsx`   |

If the language is not in this table, omit the language context block (replace `{{LANGUAGE_CONTEXT_BLOCK}}` with an empty string) and rely on the plan's code blocks for guidance.

---

## 4. Guidelines Customization

When the plan includes a "Coding Guidelines" section, inject it into the implementer prompt using the following block. This replaces the `{{GUIDELINES_CONTEXT_BLOCK}}` placeholder.

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

## 5. Requirements Constraints Customization

When a requirements document is loaded in Step 1, inject its non-negotiable constraints into the implementer prompt and all review agent prompts using this block. This replaces the `{{REQUIREMENTS_CONSTRAINTS_BLOCK}}` placeholder.

**Important**: These constraints take precedence over code style preferences and simplification suggestions. A code quality reviewer that proposes a change violating a requirements constraint must not have that change applied.

### Requirements Constraints Injection Template

```

## Requirements Constraints (Non-Negotiable)

These constraints come from the approved requirements document and MUST NOT
be violated by any code change, including refactoring and code simplification.
If a proposed change would violate any of these constraints, do NOT make
that change — even if it would improve readability or reduce complexity.
These constraints take precedence over code style preferences.

{{REQUIREMENTS_CONSTRAINTS_LIST}}

```

### How to Populate

1. In Step 1, the orchestrator reads the requirements doc linked from the plan's `## References` section.
2. Extract items from these sections of the requirements doc:
   - `## Constraints` — all MUST/MUST NOT items (e.g., "Language classification MUST run in parallel with the LLM call, not sequentially")
   - `## Acceptance Criteria` — items with behavioral invariants, especially those involving execution patterns, timing, or architectural boundaries (e.g., "both run in parallel — language classification does NOT add sequential latency to the happy path")
   - `## Scope` — items marked "Not needed" become negative constraints (e.g., "Feature flag / gradual rollout: Not needed" → "Do NOT add feature flags or gradual rollout mechanisms")
   - `## Non-Functional Requirements` — latency budgets, execution patterns (e.g., "sub-millisecond if local library, must not exceed main call duration if LLM")
3. Format each constraint as a single bullet point with its source section for traceability:

```

- [Constraints] Language classification MUST run in parallel, not sequentially. Zero added latency on the critical path.
- [Acceptance Criteria] Classification and entity decoration run in parallel — classification does NOT add sequential latency to the happy path.
- [Scope: Not needed] Do NOT add feature flags or gradual rollout mechanisms.

```

4. If no requirements doc is referenced in the plan, replace `{{REQUIREMENTS_CONSTRAINTS_BLOCK}}` with an empty string.

---

## 6. Prompt Composition Flow

The orchestrator assembles each implementer's final prompt by combining the template with context:

```

Final implementer prompt = Implementer Agent Prompt Template (Section 1)

- Task context fields filled from plan's task section
  - {{TASK_ID}}, {{TASK_NAME}}, {{WAVE_NUMBER}}, {{TASK_DESCRIPTION}}
  - {{RED_TEST_FILE}}, {{RED_BEHAVIOR}}, {{RED_EXPECTED_FAILURE}}, {{RED_RUN_COMMAND}}, {{RED_TEST_CODE_BLOCK}}
  - {{GREEN_IMPL_FILE}}, {{GREEN_CHANGES}}, {{GREEN_RUN_COMMAND}}, {{GREEN_IMPL_CODE_BLOCK}}
  - {{REFACTOR_FOCUS}}, {{REFACTOR_RUN_COMMAND}} (may be empty)
- Wave 0 test infrastructure fields filled from plan's Wave 0 section
  - {{TEST_FRAMEWORK}}, {{TEST_RUNNER_COMMAND}}
  - {{WAVE0_FIXTURES}}, {{WAVE0_TEST_UTILS}}, {{WAVE0_BASE_CLASSES}}
- Domain context (if detected, from Section 2; empty string if not)
- Language context (if detected, from Section 3; empty string if not)
- Guidelines context (if present in plan, from Section 4; empty string if not)
- Requirements constraints (if requirements doc loaded in Step 1, from Section 5; empty string if not)

```

### Composition Steps

1. **Parse the plan**: Extract task fields, Wave 0 infrastructure, per-task RED/GREEN/REFACTOR sections, and the "Coding Guidelines" section (if present).
2. **Detect domain**: Follow the detection procedure in `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` (file triggers first, then strong signals, then corroborating signals) for files referenced in the plan. If a domain is detected, spawn the domain expert and populate the domain context block.
3. **Detect language**: Check file extensions of the test and implementation files. Look up the language in the language-agent-registry. Populate the language context block.
4. **Extract guidelines**: Read the plan's "Coding Guidelines" section. If it contains key constraints, populate the guidelines context block per Section 4. If absent or empty, use an empty string.
5. **Extract requirements constraints**: If a requirements doc was loaded in Step 1, populate the requirements constraints block per Section 5. If no requirements doc, use an empty string.
6. **Assemble and spawn**: Fill the implementer template and spawn one agent per task, respecting the File Overlap Matrix parallelism rules (SKILL.md Step 5).
7. **Collect reports**: Read each implementer's STATUS report, verify RED_EVIDENCE for code tasks, and act on the status protocol (Section 7).
8. **Advance**: After the wave's integration check passes, move to the next wave.

---

## 7. Status Protocol

Every implementer agent reports a structured completion status. The orchestrator uses this status to decide whether to proceed, pause, or re-dispatch.

### Status Definitions

| Status             | Meaning                                                  | Orchestrator Action                             |
| ------------------ | -------------------------------------------------------- | ----------------------------------------------- |
| DONE               | Task completed successfully, no concerns                 | Verify RED_EVIDENCE (code tasks), then proceed  |
| DONE_WITH_CONCERNS | Task completed but agent has doubts                      | Classify concerns as minor or major (see below) |
| BLOCKED            | Cannot complete the task (includes unexpected test pass) | Stop wave execution, present to user            |
| NEEDS_CONTEXT      | Missing information needed to proceed                    | Provide requested context, re-dispatch agent    |

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
- Missing verbatim RED_EVIDENCE on a code task
- Implementation required significantly more or less code than the plan suggested
- Agent is unsure the implementation is correct
- Created abstractions or patterns the plan did not call for
- Test may not be testing the right behavior

→ In interactive mode: STOP execution and present concerns to user with options (proceed, fix, or abort).
→ In non-interactive mode: log to mismatch file, apply decision-principles for resolution.

### Key Principle

**Bad work is worse than no work.** Agents are never penalized for reporting DONE_WITH_CONCERNS, BLOCKED, or NEEDS_CONTEXT. Silent completion of incorrect work is far more expensive to fix than an honest escalation.
