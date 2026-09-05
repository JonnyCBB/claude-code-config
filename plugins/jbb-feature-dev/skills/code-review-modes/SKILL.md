---
name: code-review-modes
description: Defines plan/implement/test-review/code-style-review/deep-analysis modes for the {language}-expert agents. Carries CHANGE_SCOPE rules and per-language verbatim block schemas. Use when authoring or modifying any {language}-expert agent.
allowed-tools: Read
---

# Code Review Modes

This skill defines the five framing modes under which a `{language}-expert`
agent (`python-expert`, `typescript-expert`) can
be invoked. The mode selects the output schema, skill emphasis, and degree of
behavioral detail.

Mode is **inferred from natural caller phrasing**, not a strict flag. Verb cues
(below) drive selection; precedence rules disambiguate when multiple cues
match.

## Plan Mode

Use when the caller wants per-language **design advice** before writing code,
typically spawned by `/create-plan-tdd` during the planning phase.

In plan mode, the language expert:

- Reviews the requirement / proposed feature and identifies the language-idiomatic
  decomposition (file boundaries, type/class shape, public API, dependency wiring).
- Surfaces deep-language pitfalls relevant to the design (e.g., shuffle hotspots
  for the detected language, async/blocking-call mismatches for Python, hooks-rule
  violations for TypeScript/React, service wiring sequence).
- **Does not** emit `TEST NEEDED` / `ISSUE` blocks. Output is a structured
  design note (plan body field) consumed by the planner.
- May load the language-specific code style skill plus any
  language-specific domain skill (e.g., `ml-model-patterns`)
  to ground recommendations.

## Implement Mode

Use when the caller wants the expert to **write idiomatic code** for a task,
typically spawned by `/implement-plan-tdd` as the per-wave implementation agent
for a single-language wave.

In implement mode, the language expert:

- Edits / writes source files using `Edit`, `Write`, `MultiEdit` tools.
- Writes idiomatic code in the target language. Honors repository conventions
  (assertion library, type declarations, import style).
- Makes failing tests pass (TDD GREEN phase) or scaffolds new code per the
  task spec.
- **Does not** emit review blocks. Output is the diff and a brief implementation
  note.

## Test-Review Mode

Use when the caller wants **test coverage analysis** for a diff. This is today's
test-reviewer pipeline. Output schema is preserved verbatim so
`review-deduplicator` and `review-calibrator` parse without changes.

In test-review mode, the language expert:

- Identifies missing test coverage for changed code paths.
- Identifies redundant / low-value tests (anti-patterns from
  `code-style-common/test-anti-patterns.md`).
- Identifies test-quality issues (naming, assertion alignment, weak assertions,
  missing-feature assertions, mocking, fixtures).
- Emits **`TEST NEEDED`**, **`REDUNDANT TEST`**, **`QUALITY ISSUE`** blocks per
  the per-language schema in `schemas/{lang}.md#test-review-schema`.

## Code-Style-Review Mode

Use when the caller wants **code-quality style analysis** for a diff.
This is today's code style reviewer pipeline.

In code-style-review mode, the language expert:

- Identifies DRY / SOLID / complexity / naming issues.
- Identifies opportunities for modern language features and idiomatic refactors
  (Java records / streams, Scala FP / for-comprehensions, Python comprehensions
  / async, TypeScript discriminated unions / type-narrowing).
- Identifies repository-convention violations (FQN imports, var/val,
  type declarations).
- Emits **`ISSUE`** blocks per the per-language schema in
  `schemas/{lang}.md#code-style-review-schema`.

## Deep-Analysis Mode

Use when the caller wants **language-specific deep-dive analysis** that doesn't
fit the test or code style framings — e.g., data-pipeline shuffle / join / windowing
optimization, serving wiring sequence and gRPC / batch-feature reader
integration, performance critical-path review.

In deep-analysis mode, the language expert:

- Loads the relevant deep-language skill (e.g., `ml-model-patterns`,
  `ml-model-patterns`).
- Produces a long-form analytical narrative with concrete recommendations
  citing specific lines, alongside any of the structured `ISSUE` blocks where
  applicable.
- Is **caller-explicit-only** — see Mode Precedence below. Never auto-inferred
  from diff content.

## Verb-Cue Inference

Caller phrasing maps to modes per the table below. Inference robustness is a
non-functional requirement (Reqs NFR line 141). When multiple cues match, see
Mode Precedence.

| Caller phrasing                                                                           | Inferred mode     |
| ----------------------------------------------------------------------------------------- | ----------------- |
| "advise on design", "plan the {feature}", "design advice", "per-language design"          | plan              |
| "implement {task}", "write idiomatic {lang}", "make tests pass", "TDD GREEN"              | implement         |
| "review test coverage", "evaluate test adequacy", "are tests sufficient", "test gap"      | test-review       |
| "review code quality", "identify style issues", "code review", "review for FP"            | code-style-review |
| "deep analysis", "deep dive on X", "pipeline optimization analysis", "serving wiring deep dive" | deep-analysis     |

## Mode Precedence

When caller phrasing matches more than one verb-cue, apply Precedence rules in
this order:

1. **deep-analysis is caller-explicit-only.** It activates only when caller
   phrasing explicitly says "deep analysis", "deep dive on X", "pipeline
   optimization analysis", "serving wiring deep dive", or an equivalent phrase.
   It is NEVER auto-inferred from diff content. A diff containing shuffle code
   does not imply deep-analysis. A diff touching `BatchFeatureReader` does not
   imply deep-analysis. The caller must say so.

2. **Plan and implement dominate review modes** when caller phrasing signals
   planning or implementation framing. If "plan", "design", or "implement",
   "write code" cues are present alongside review cues, prefer plan or
   implement.

3. **Within review modes, test-review dominates code-style-review** when
   test-related cues match. If the caller mentions tests, test coverage,
   assertions, or test adequacy, use test-review even if "code quality" or
   "review" appears in the same prompt.

4. **Default mode when no cues match: code-style-review.** That is, the
   default mode is code-style-review. This preserves today's pipeline
   behavior — `/code-review` spawns the language expert in code style
   framing by default.

## CHANGE_SCOPE

When the caller provides a CHANGE_SCOPE (specific line ranges), the language
expert MUST honor it across all review modes (test-review,
code-style-review, deep-analysis). These rules are universal across the
four old test reviewers (Java, Scala, Python, TypeScript) and lifted verbatim
from those agents per research §2.2.

When provided with a CHANGE_SCOPE (specific line ranges), you MUST:

1. **Only analyze changed code**: Focus exclusively on the lines specified in the scope
2. **Ignore coverage gaps in unchanged code**: Even if a method in the same file has zero tests, do NOT recommend tests for it if it wasn't changed
3. **Test the changes, not the file**: Your goal is ensuring the NEW/MODIFIED code is tested, not achieving comprehensive file coverage

### Scope Interpretation Examples

**Given scope:**

```
CHANGE_SCOPE:
- file: src/main/java/com/example/UserService.java
  changes:
    - lines: 45-52 (added method: validateEmail)
```

**CORRECT behavior:**

- Recommend tests for `validateEmail()` method (lines 45-52)
- Analyze what edge cases the NEW validateEmail code should handle

**INCORRECT behavior:**

- Recommend tests for `findUserById()` method (lines 10-30) - NOT IN SCOPE
- Recommend tests for `updateUser()` method (lines 80-120) - NOT IN SCOPE
- Recommend comprehensive coverage for the entire UserService class - NOT IN SCOPE

### Output Filtering

Before finalizing recommendations, verify each one:

- [ ] Is the source code being tested within the specified line ranges?
- [ ] Was this code added or modified in the current changes?

If NO to either question, REMOVE the recommendation from your output.

**If no CHANGE_SCOPE is provided**, assume file-level scope and provide comprehensive coverage analysis.

### Canonical Rule (semantic DRY anchor)

ONLY recommend tests for code that was ADDED or MODIFIED. The CHANGE_SCOPE
contract above is the single source for this rule across the
language-expert agents and their loaded skills.

## Schema Reference Table

Per-mode block schemas live in `schemas/{language}.md` files alongside this
SKILL.md. Each schema file is the verbatim lift of the corresponding old-agent
output template, preserving on-disk space-form block names (`TEST NEEDED`,
`REDUNDANT TEST`, `QUALITY ISSUE`, `ISSUE`) so downstream parsers don't change.

| Language   | Mode              | Schema file                                      |
| ---------- | ----------------- | ------------------------------------------------ |
| java       | test-review       | `schemas/java.md#test-review-schema`             |
| java       | code-style-review | `schemas/java.md#code-style-review-schema`       |
| scala      | test-review       | `schemas/scala.md#test-review-schema`            |
| scala      | code-style-review | `schemas/scala.md#code-style-review-schema`      |
| python     | test-review       | `schemas/python.md#test-review-schema`           |
| python     | code-style-review | `schemas/python.md#code-style-review-schema`     |
| typescript | test-review       | `schemas/typescript.md#test-review-schema`       |
| typescript | code-style-review | `schemas/typescript.md#code-style-review-schema` |

## Output Contract

Per-mode block schemas populate the `body` field of each finding emitted by
the language expert. If `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/finding-schema.md`
exists, it defines the wrapping envelope (severity, file, line, body). Where
that finding-schema reference is absent, treat the per-language schema files
as the complete output contract — the schema text IS the body field, in the
verbatim space-form block layout that downstream agents
(`review-deduplicator`, `review-calibrator`) parse today.

## Plugin Caveats

Two known Claude Code plugin issues affect skill-driven invocation:

- **GitHub issue #25834** — silent skill-injection failure: under some
  conditions a skill listed in agent frontmatter does not actually load,
  with no visible error. Mitigation: language experts should reference
  this skill's content via short, self-contained quotes where the rule must
  hold even if the skill failed to load (the canonical CHANGE_SCOPE
  sentence above is anchored here so a single grep verifies presence).
- **GitHub issue #7406** — parallel-spawn flakiness: `/code-review` and
  `/polish-code` spawn the language expert twice in parallel (test-review +
  code-style-review). Under flake conditions, one of the two parallel
  spawns may not register its output. Combined-invocation fallback is
  documented in `code-review/SKILL.md` — a single sequential invocation
  emitting both schemas in one response. Use it when parallel spawn drops
  findings.
