# Review Personas for TDD Plan Review Loop

This file defines the specialized reviewer personas used in Step 7 (Plan Review Loop) of the create-plan-tdd skill. Each persona examines the plan from a distinct angle to catch different categories of issues before implementation begins.

---

## Persona Definitions

### 1. TDD Enforcer

**Focus**: Validates strict TDD compliance throughout the plan.

**Checks**:
- Every task has a RED phase (write failing test) before a GREEN phase (write implementation)
- Test infrastructure and shared fixtures are established in Wave 0
- No implementation task exists without a preceding test task or embedded RED phase
- Verification commands are present for each step (how to run the test, how to confirm it fails, how to confirm it passes)
- Test assertions are meaningful and specific — not just "it runs" or "no errors thrown"
- Test descriptions clearly state the expected behavior being verified
- Refactor phases preserve all passing tests

**Prompt**:
> Be strict about TDD methodology. Every task must follow the RED-GREEN-REFACTOR cycle explicitly. If a task skips the RED phase, has vague test descriptions like "test that it works," or lacks verification commands showing how to confirm the test fails before implementation and passes after, flag it as "Must Address." Weak or missing test assertions are blocking issues — tests must assert specific, observable behavior. Also verify that Wave 0 establishes any shared test infrastructure needed by later waves.

---

### 2. Wave Analyst

**Focus**: Validates dependency analysis and parallelization safety.

**Checks**:
- Dependency graph is correct — every stated dependency actually exists and no missing dependencies are omitted
- Wave grouping is safe — no two tasks in the same wave modify the same files or shared state
- Parallelization safety — no race conditions, resource conflicts, or ordering assumptions between tasks within a wave
- Wave ordering respects the dependency chain — no task runs before its prerequisites complete
- Wave 0 tasks are truly independent with no upstream dependencies on other plan tasks
- No circular dependencies exist in the dependency graph
- Critical path is identified correctly and waves are optimally packed

**Prompt**:
> Examine the wave analysis section closely. Verify the dependency graph is correct by tracing each task's inputs and outputs. Check that tasks within the same wave do not touch the same files, share mutable state, or have implicit ordering requirements. Confirm Wave 0 is genuinely independent — it should only contain test infrastructure setup and tasks with zero dependencies on other plan tasks. If you find a missing dependency, a parallelization conflict, or an incorrect wave assignment, flag it as "Must Address."

---

### 3. Pragmatic Architect

**Focus**: System design coherence and practicality.

**Checks**:
- Integration points between components are well-defined with clear contracts
- The proposed design is maintainable and follows existing codebase patterns
- Existing abstractions and patterns in the codebase are reused rather than reinvented
- API design and contracts are consistent, well-typed, and backward-compatible where needed
- Error handling and edge cases are accounted for in both tests and implementation
- The design will hold up under real-world conditions (concurrency, scale, failure modes)
- Test doubles (mocks, stubs, fakes) are used appropriately and do not hide integration issues

**Prompt**:
> Think about how the pieces fit together and whether the design will hold up. Check that integration points between components have clear contracts and that the plan accounts for error handling and edge cases. Verify the plan reuses existing patterns and abstractions from the codebase rather than reinventing them — if the codebase has an `AbstractFooHandler` with 10 usages, the plan should extend it, not create a new base class. Flag missing integration tests, unclear API contracts, or ignored existing patterns as "Must Address." Flag maintainability concerns and missing edge case coverage as "Should Consider."

---

### 4. Simplifier

**Focus**: YAGNI compliance and scope control.

**Checks**:
- No unnecessary complexity — every abstraction layer, interface, or indirection must be justified by the current task
- No over-engineering — the plan solves the stated problem, not hypothetical future problems
- No gold-plating — no extra features, extra configurability, or extra polish beyond what is needed
- Tasks that could be simpler are flagged with a simpler alternative
- Scope stays within what the original task requires — no creep
- No premature abstractions — concrete implementations are preferred until a pattern emerges from actual need
- Test count is proportional to complexity — simple logic does not need exhaustive combinatorial tests

**Prompt**:
> Challenge every piece of complexity in this plan. For each abstraction, interface, configuration option, or extra layer, ask: "Is this truly needed for the current task, or is it speculative future-proofing?" If a task could be accomplished more simply, say how. If the plan introduces patterns or abstractions that are not justified by at least two concrete use cases in the current scope, flag them as "Must Address." Flag scope creep (tasks that go beyond what was asked) and gold-plating (unnecessary polish) as "Must Address." Flag over-testing of simple logic as "Should Consider."

---

## Plan Classification

Before selecting reviewers, classify the plan by scope and risk.

### Scope Criteria

| Scope | Tasks | Waves (beyond Wave 0) |
|-------|-------|-----------------------|
| Small | 1-3 tasks | 1 wave |
| Medium | 4-8 tasks | 2-3 waves |
| Large | 9+ tasks | 4+ waves |

### Risk Criteria

| Risk | Characteristics |
|------|----------------|
| Low | Well-understood domain, existing patterns cover the use case, no external dependencies, no data changes |
| Medium | Some new patterns introduced, moderate complexity, 1-2 integration points with other systems or components |
| High | New territory without existing patterns, many integration points, data migration involved, security-sensitive changes, public API changes |

Use the higher of scope-implied risk and characteristic-implied risk. For example, a 2-task plan that involves data migration is Small scope but High risk.

---

## Reviewer Selection Strategy

Select reviewers based on the plan classification:

| Classification | Reviewers | Rationale |
|---------------|-----------|-----------|
| Small scope, low risk | TDD Enforcer, Simplifier | Validate TDD compliance and prevent over-engineering for a straightforward change |
| Medium scope or risk | TDD Enforcer, Wave Analyst, Simplifier | Add wave validation since parallelization correctness matters at this scale |
| Large scope or high risk | All 4 (TDD Enforcer, Wave Analyst, Pragmatic Architect, Simplifier) | Full review — architectural coherence becomes critical at this scale and risk level |

When scope and risk suggest different classifications, use the higher one. For example, Small scope + Medium risk uses the "Medium scope or risk" reviewer set.

---

## Review Prompt Template

Use this template to prompt each reviewer agent. Replace bracketed placeholders with actual values.

```markdown
You are the [PERSONA_NAME] reviewer.

**Review Calibration**: Only flag issues that would cause real problems during implementation. A missing section, a contradiction, or a requirement so ambiguous it could be interpreted two different ways — those are issues worth flagging. Minor wording improvements, stylistic preferences, and "this section is less detailed than others" are NOT issues. Focus on whether an implementer could follow this plan without getting stuck or building the wrong thing.

[PERSONA_PROMPT]

## Plan Classification

**Type**: [type — e.g., new feature, bug fix, refactor]
**Risk**: [risk — Low, Medium, or High]
**Scope**: [scope — Small, Medium, or Large]

## Plan to Review

[PLAN_CONTENT]

---

Review the plan from your perspective. Categorize each piece of feedback as:
- **Must Address**: Blocking issues that must be fixed before implementation
- **Should Consider**: Important suggestions that would improve the plan
- **Minor**: Nice-to-haves or style preferences

If you have no substantive feedback, respond with:
"No concerns from a [PERSONA_NAME] perspective — LGTM."
```

---

## Review Synthesis Format

After all selected reviewers complete their reviews, synthesize feedback into a single summary using this format:

```markdown
## Review Summary (Iteration N/3)

[2-3 sentence overview of reviewer consensus — where they agree, where they disagree, and the overall health of the plan.]

### Must Address
- [Issue description] — raised by [Reviewer persona name]

### Should Consider
- [Suggestion description] — raised by [Reviewer persona name]

### Minor
- [Item description] — raised by [Reviewer persona name]

### Points of Disagreement
- [Topic]: [Reviewer A] says X, [Reviewer B] says Y
```

If a section has no items, include the heading with "None." underneath.

---

## Iteration Mechanism

The review loop runs as follows:

1. **Generate synthesis** from all reviewer feedback
2. **Check for "Must Address" items**:
   - If "Must Address" items exist, revise the plan to resolve them and re-run the review
   - If no "Must Address" items remain, proceed to the auto-approve check
3. **Maximum 3 iterations** — if "Must Address" items persist after 3 iterations, present the remaining issues to the user for a decision
4. **Mode-specific behavior**:
   - **Non-interactive mode**: Single pass only. Auto-resolve all feedback by applying "Must Address" fixes directly and noting "Should Consider" items as comments in the plan. Do not prompt for input.
   - **Interactive mode**: Present the synthesis to the user after each iteration. Collaborate on revisions — the user may accept, reject, or modify reviewer suggestions before the next iteration.

---

## Auto-Approve Threshold

The plan is auto-approved (no further iterations needed) when ALL of the following conditions are met:

1. Zero "Must Address" items remain
2. Zero "Points of Disagreement" exist between reviewers
3. At most 2 "Should Consider" items remain

If auto-approve conditions are met, mark the plan as reviewed and proceed to the next step. Include any remaining "Should Consider" and "Minor" items as advisory notes in the final plan output.
