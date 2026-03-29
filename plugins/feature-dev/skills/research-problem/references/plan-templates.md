# Plan Templates for Step 2: Analyze and Decompose

These templates are used when decomposing a research question in Step 2 of the research-problem skill.
Read this file when Step 2 instructs you to `Read references/plan-templates.md`.

## Research Questions

```
## Research Questions

To answer "[user's question]", I need to investigate:

1. [Question 1] → Will use [subagent-type]
2. [Question 2] → Will use [subagent-type]
3. [Question 3] → Will use [subagent-type]
...
```

For each question, determine: what type of information is needed, which subagent type is most appropriate, and what specific areas to investigate.

## Assumptions

```
## Assumptions

In approaching "[user's question]", I am making the following assumptions:

**Explicit assumptions** (directly stated or strongly implied by the query):
1. [Assumption about scope, e.g., "Research is limited to this repository"]
2. [Assumption about intent, e.g., "You want documentation, not recommendations"]

**Implicit assumptions** (inferred from context):
1. [Assumption about domain, e.g., "The system uses standard infrastructure patterns"]
2. [Assumption about methodology, e.g., "Current codebase is source of truth over old docs"]

**Constraints assumed:**
1. [Time/scope constraints, e.g., "Research should complete in one session"]
2. [Access constraints, e.g., "All relevant code is in this repository"]
```

Evaluate each assumption: Was it explicitly stated? Inferred? Could it be wrong, and would that change the approach?

## Success Criteria

```
## Success Criteria

This research will be considered complete when:
- [ ] [Specific deliverable, e.g., "All authentication entry points are identified with file paths"]
- [ ] [Level of detail required, e.g., "Each component's role in the flow is documented"]
- [ ] [Scope of coverage, e.g., "Both happy path and error handling are covered"]
```

## Scope

```
## Scope

**In scope:**
- [What will be investigated]
- [Systems/components to cover]

**Explicitly out of scope:**
- [What will NOT be investigated, e.g., "Historical implementations before 2023"]
- [Systems to exclude, e.g., "Shared libraries outside this repository"]
- [Depth limits, e.g., "Will not deep-dive into database schemas"]
```

## Complexity Classification

After defining scope, classify the research complexity to determine the review phase scope
in Step 7. See `references/review-personas.md` for the authoritative complexity signal table
and reviewer selection criteria.

Based on the research plan, this research is classified as: **[Simple/Medium/Complex]**

**Review phase**: [Skip (Simple) / Lightweight — 3 personas (Medium) / Full — 5 personas (Complex)]

## Research Context

```
## Research Context

**Known starting points** (extracted from your question):
- [File/component mentioned, e.g., "`AuthService.java` - mentioned in question"]
- [Or: "None explicitly mentioned - will discover through research"]

**Prior knowledge assumed** (what you appear to already understand):
- [Inferred knowledge, e.g., "Familiar with OAuth flow based on question framing"]

**Previous research** (if any):
- [Link to existing research docs if found in ~/.claude/thoughts/shared/research/]
- [Or: "No prior research found on this topic"]
```

## Research Execution Plan

**Dependency types to consider:** scope narrowing, vocabulary/terminology, architecture understanding, existence validation.

```
## Research Execution Plan

**Dependency Analysis:**

| Question | Type | Depends On | Rationale |
|----------|------|------------|-----------|
| Q1 | Parallel | None | Independent starting point |
| Q2 | Sequential | Q1 | Q1's answer about [X] will narrow the scope of Q2's search |
| Q3 | Parallel | None | Independent - different system/domain |
| Q4 | Sequential | Q2, Q3 | Needs synthesis of both findings to form focused query |
| Q5 | Direct | None | Simple lookup, single agent sufficient |

**Question types:**
- **Parallel**: Truly independent — no information dependency on other questions
- **Sequential**: Answer from a prior question narrows scope, provides vocabulary, or changes the search strategy
- **Direct**: Simple enough to answer with a grep, glob, or single file read in the main context — no sub-agent needed. Use Direct when the question has a deterministic answer that doesn't require LLM reasoning. Handle Direct questions immediately in the main context before spawning any agents. Only escalate to a sub-agent if the direct lookup fails to produce a clear answer.

**Direct question examples and resolution**:

| Question | Tool | Command |
|----------|------|---------|
| "Does `AuthService.java` exist?" | Glob | `**/*AuthService.java` |
| "What interface does `NotificationHandler` implement?" | Grep | `class NotificationHandler.*(implements\|extends)` |
| "What version of guava is in the build file?" | Grep | `guava` in `**/pom.xml` or `**/build.gradle` |
| "Is there a `conftest.py` in the test directory?" | Glob | `**/conftest.py` |
| "What fields does the `UserEvent` proto have?" | Read | Read the `.proto` file directly |

**Direct question rules**:
- Resolve Direct questions BEFORE spawning Batch 1 agents
- If a Direct lookup is inconclusive (e.g., multiple matches, ambiguous result), escalate to a sub-agent in the next batch
- Direct questions do not appear in the Pre-Spawn Verification Table (they don't use agents)
- Document Direct question answers in the synthesis alongside agent findings

**Execution Batches:**

Batch 1 (parallel): Q1, Q3
   ↓ (wait for completion, extract key context)
Batch 2 (parallel): Q2 (informed by Q1 findings)
   ↓ (wait for completion)
Batch 3: Q4 (informed by Q2 + Q3 findings)

**Context to pass between batches:**
- After Batch 1: [What specific information from Q1/Q3 will inform later questions]
- After Batch 2: [What specific information from Q2 will inform later questions]
```

**Decomposition default rule:** Classify each question as Parallel, Sequential, or Direct. Default to Parallel when the dependency is unclear. Only classify as Sequential when there's a clear benefit to waiting (scope narrowing, vocabulary discovery). Use Direct for simple lookups that don't benefit from decomposition.

## TodoWrite Tracking Pattern

```
Phase 1 Research Tasks:
- Research question 1 with agent X (pending → in_progress → completed)
- Research question 2 with agent Y (pending → in_progress → completed)
- Spawn codebase-explorer for question 3 (pending → in_progress → completed)
[After ALL agents complete in step 4]
- Synthesis attempt 1 (pending → in_progress → completed)
- Validation iteration 1 (pending → in_progress → completed)
[If gaps found in step 6]
Phase 2 Research Tasks:
- Additional research for gap 1 (pending → in_progress → completed)
[After new agents complete]
- Synthesis attempt 2 (pending → in_progress → completed)
- Validation iteration 2 (pending → in_progress → completed)
```

Do NOT add synthesis tasks to the TODO list until all initial agents complete (Step 4).

## Research Plan File Specification

- Directory: `~/.claude/thoughts/shared/research_plans/` (create if needed)
- Filename: `YYYY-MM-DD-description-plan.md`
- YAML frontmatter:
  ```yaml
  ---
  date: YYYY-MM-DD
  type: research-plan
  topic: "[research topic]"
  status: approved # 'approved' in non-interactive, 'pending-approval' in interactive
  related_research_doc: "~/.claude/thoughts/shared/research/YYYY-MM-DD-description.md"
  ---
  ```
- Plan captures intent (WHAT and WHY); research doc captures findings (WHAT we found).

## Interactive Confirmation Gate

```
Do these look correct?
- Questions to investigate
- Research execution plan (dependencies and batching)
- Assumptions (explicit, implicit, constraints)
- Success criteria
- Scope (in/out)
- Research context (starting points, prior knowledge)

Should I adjust the questions, sequencing, or any other aspect before proceeding?
```

Wait for user confirmation before proceeding to Step 3. After approval, update plan file status to `approved`. Skip in NON_INTERACTIVE mode.

## Agent Type Verification

At the end of Step 2, create an accountability list:

```
## Agent Type Verification

Based on the questions above, I will spawn the following agent types:
- codebase-explorer (questions 1, 3)
- web-search-researcher (question 2)
- codebase-explorer (question 4)

Total unique agent types: 2
```

This list is your contract: all listed agent types must be spawned before synthesis.

## Example: Automerge Decomposition

User question: "How do we handle automerge for dependency bot PRs?"

**Questions:**

1. What dependency bots are available in this organization? -> **codebase-explorer**
2. How does automerge work in this codebase? -> **codebase-explorer**
3. What automerge configurations exist in this repository? -> **codebase-explorer**
4. What automerge patterns do similar repos use? -> **codebase-explorer**
5. What external tools (Renovate, Dependabot) support automerge? -> **web-search-researcher**

**Dependency Analysis:**

| Question | Type       | Depends On | Rationale                                                              |
| -------- | ---------- | ---------- | ---------------------------------------------------------------------- |
| Q1       | Parallel   | None       | Need to know what bots exist before understanding their configs        |
| Q2       | Parallel   | None       | General context, independent                                           |
| Q3       | Sequential | Q1         | Knowing which bots exist (Q1) tells us what config files to look for   |
| Q4       | Sequential | Q1, Q3     | Need to know our bot (Q1) and our config (Q3) to find similar patterns |
| Q5       | Sequential | Q1         | Knowing which bot we use (Q1) focuses external research                |

**Execution Batches:**

```
Batch 1 (parallel): Q1, Q2
   ↓ Q1 reveals: "We use Renovate"
Batch 2 (parallel): Q3 (search for renovate.json), Q5 (research Renovate automerge)
   ↓ Q3 reveals: "Config at .github/renovate.json5 with automerge disabled"
Batch 3: Q4 (find repos using Renovate with automerge enabled)
```

**Context passed:**

- Batch 1 -> Batch 2: "We use Renovate bot, search for renovate config files"
- Batch 2 -> Batch 3: "Our config is at .github/renovate.json5, look for similar repos with automerge: true"
