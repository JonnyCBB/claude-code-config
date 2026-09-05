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
1. [Assumption about domain, e.g., "The system uses standard shared infrastructure"]
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

## TaskCreate Tracking Pattern

Use `TaskCreate` (not the deprecated TodoWrite) to track research progress. Tasks are
visible in the Claude Code UI and the system periodically nudges the model to check them.

**Task creation timing:**

- Post-research step tasks (Steps 4-9, Pre-Document Gate, Steps 10-13): create ALL
  immediately after Step 3 agents are spawned (see SKILL.md "Post-Research Step Tracking")
- Per-iteration tasks (new agents, new synthesis, new validation): create when the
  evaluator returns ITERATE in Step 6

**Task lifecycle:** `pending` → `in_progress` (via TaskUpdate when starting) →
`completed` (via TaskUpdate when done)

**Before each step:** Call `TaskList` to verify the previous step is `completed`. If not,
STOP and complete it first.

Do NOT begin synthesis until all current-phase agent tasks are `completed` (Step 4); create
a fresh synthesis + validation task pair per iteration via `TaskCreate`.

## Research Plan File Specification (NON_INTERACTIVE mode only)

In NON_INTERACTIVE mode only, save the plan to disk so pipeline consumers can read it.
In **interactive mode, do NOT write the plan to a file** -- render it in full in the
Claude Code UI instead (see "Interactive Confirmation Gate" below).

- Directory: `~/.claude/thoughts/shared/research_plans/` (create if needed)
- Filename: `YYYY-MM-DD-description-plan.md`
- YAML frontmatter:
  ```yaml
  ---
  date: YYYY-MM-DD
  type: research-plan
  topic: "[research topic]"
  status: approved # non-interactive only; interactive mode does not write this file
  related_research_doc: "~/.claude/thoughts/shared/research/YYYY-MM-DD-description.md"
  ---
  ```
- Plan captures intent (WHAT and WHY); research doc captures findings (WHAT we found).

## Interactive Confirmation Gate

In interactive mode, the plan lives in the Claude Code UI, not on disk. After printing
the full plan to the UI, call the **`AskUserQuestion`** tool to gate Step 3. Example:

```
AskUserQuestion(
  question: "Proceed with this research plan?",
  options: [
    "Proceed with this plan as-is",
    "Request changes (I'll tell you what to adjust)",
    "Cancel the research",
  ]
)
```

- Do **NOT** emit the plain-text "Do these look correct?" prompt -- always use the
  AskUserQuestion tool so the user gets a structured choice in the UI.
- Wait for the user's selection before proceeding to Step 3. If they pick "Request
  changes", revise the plan (again rendered fully in the UI) and ask via
  AskUserQuestion again.
- Skip this gate entirely in NON_INTERACTIVE mode.

## Domain Expert Check

**MANDATORY**: Before finalizing agent assignments, cross-reference every research question
against the Domain Expert Table in `references/agent-guide.md`. This must happen in Step 2
(not Step 3) because agent types are committed here and approved by the user.

```
## Domain Expert Check

Cross-referencing research questions against the Domain Expert Table:

| Research Question | Domain Keywords | Matching Expert | Use as Researcher? | Use as Verifier (Step 7)? | Justification |
|---|---|---|---|---|---|
| Q1: [question] | [keywords found] | [expert or "None"] | Yes/No | Yes/No | [reason] |
| Q2: [question] | [keywords found] | [expert or "None"] | Yes/No | Yes/No | [reason] |

Domain expert matches found: [N]
```

**Decision rules:**

- If a question's core topic matches a domain pattern → use the domain expert as
  **primary researcher** for that question (prefer over codebase-explorer for domain questions)
- If the domain expert matches the overall research topic but not a specific question →
  flag it for **verification in Step 7**
- If you choose NOT to use a matching domain expert as primary researcher, you MUST explain
  why (e.g., "question is about locating files, not domain-specific knowledge")
- A domain expert can serve as both primary researcher (Step 3) AND verifier (Step 7) —
  these roles are complementary, not redundant

## Agent Type Verification

At the end of Step 2, create an accountability list:

```
## Agent Type Verification

Based on the questions above, I will spawn the following agent types:
- codebase-explorer (questions 1, 3)
- web-search-researcher (question 2)
- codebase-explorer (question 4)

Total unique agent types: 2

Domain expert verification in Step 7: [expert-name] (if applicable)
```

This list is your contract: all listed agent types must be spawned before synthesis.

## Example: Automerge Decomposition

User question: "How do we handle automerge for dependency bot PRs?"

**Questions:**

1. What dependency bots are available? -> **web-search-researcher**
2. How does automerge work? -> **web-search-researcher**
3. What automerge configurations exist in this repository? -> **codebase-explorer**
4. What automerge patterns do similar repos use? -> **codebase-explorer**
5. What external tools (Renovate, Dependabot) support automerge? -> **web-search-researcher**

**Dependency Analysis:**

| Question | Type       | Depends On | Rationale                                                              |
| -------- | ---------- | ---------- | ---------------------------------------------------------------------- |
| Q1       | Parallel   | None       | Need to know what bots exist before understanding their configs        |
| Q2       | Parallel   | None       | General platform context, independent                                   |
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
