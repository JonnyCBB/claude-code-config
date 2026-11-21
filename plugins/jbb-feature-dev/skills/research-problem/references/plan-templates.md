# Plan Templates (Step 2)

Give every question and success criterion a stable ID (Q1, SC1) and keep it through the run.

## Research Questions

```
## Research Questions

To answer "[user's question]", I need to investigate:

1. Q1: [Question] -> Will use [jbb-feature-dev:agent-type]
2. Q2: [Question] -> Will use [jbb-feature-dev:agent-type]
```

## Assumptions

```
## Assumptions

**Explicit** (stated or strongly implied by the query):
1. [e.g. "Research is limited to this repository"]

**Implicit** (inferred from context):
1. [e.g. "Current code is the source of truth over old docs"]

**Constraints:**
1. [e.g. "All relevant code is in this repository"]
```

Step 5 marks each assumption CONFIRMED, INVALIDATED or UNCERTAIN.

## Success Criteria

```
## Success Criteria

- [ ] SC1: [Specific deliverable, e.g. "All authentication entry points identified with file paths"]
- [ ] SC2: [Level of detail or coverage]
```

## Scope

```
## Scope

**In scope:** [what will be investigated]
**Explicitly out of scope:** [what will not, and depth limits]
```

## Research Context

```
## Research Context

**Known starting points:** [files/components named in the question, or "none"]
**Prior knowledge assumed:** [what the user appears to know]
**Previous research:** [links in ~/.claude/thoughts/shared/research/, or "none found"]
```

## Research Execution Plan

```
## Research Execution Plan

| Question | Type | Depends On | Rationale |
|----------|------|------------|-----------|
| Q1 | Parallel | None | Independent starting point |
| Q2 | Sequential | Q1 | Q1's answer about [X] narrows Q2's search |
| Q3 | Direct | None | Single deterministic lookup |

Batch 1 (parallel): Q1
   | (wait, extract context)
Batch 2: Q2 (informed by Q1)

Context to pass after Batch 1: [what from Q1 informs Q2]
```

- **Parallel**: no information dependency. The default when unsure.
- **Sequential**: a prior answer narrows scope, supplies vocabulary, or changes the search.
- **Direct**: one grep, glob or file read answers it outright in the main context. Direct is a
  property of the question's shape (the answer is a name, version, path, field list or
  yes/no), never of what you have already read. A question about how something works, why it
  behaves as it does, what order things run in, or what happens in some case is never Direct.

  On a real run an executor classified all four questions Direct because Step 1 had "already
  answered them", spawned zero agents, and Step 4 then confirmed "0 agent types listed, 0
  spawned -> match". The research phase disappeared and every later check passed.

At least one question is Parallel or Sequential. Resolve Direct questions before Batch 1; if a
Direct lookup is ambiguous, send it to an agent in the next batch.

## Domain Expert Check

Cross-reference every question against the Domain Expert Table in
`references/agent-guide.md` here, in Step 2, because agent types are committed and approved
here.

```
## Domain Expert Check

| Research Question | Domain Keywords | Matching Expert | Researcher? | Verifier (Step 7)? | Justification |
|---|---|---|---|---|---|
| Q1: [question] | [keywords] | [expert or "None"] | Yes/No | Yes/No | [reason] |
```

If a matching expert is not used as the primary researcher, say why (for example "the question
is about locating files").

## Agent Type Verification

```
## Agent Type Verification

- jbb-feature-dev:codebase-explorer (Q1, Q3)
- jbb-feature-dev:web-search-researcher (Q2)

Domain expert verification in Step 7: [expert, or none]
```

## Complexity Classification

Use the highest level any signal implies:

| Signal              | Simple | Medium | Complex       |
| ------------------- | ------ | ------ | ------------- |
| Research questions  | 1-2    | 3-5    | 6+            |
| Domains/systems     | Single | 2-3    | Cross-cutting |
| Agent types spawned | 1-2    | 2-3    | 4+            |
| Execution batches   | 1      | 1-2    | 3+            |

## Plan file (NON_INTERACTIVE only)

In interactive mode the plan lives in the response, not on disk.

```yaml
---
date: YYYY-MM-DD
type: research-plan
topic: "[research topic]"
status: approved
related_research_doc: "~/.claude/thoughts/shared/research/YYYY-MM-DD-description.md"
---
```

Path: `~/.claude/thoughts/shared/research_plans/YYYY-MM-DD-description-plan.md`.

## Example: automerge decomposition

Question: "How do we handle automerge for dependency bot PRs?"

| Question | Agent | Type | Depends On |
| -------- | ----- | ---- | ---------- |
| Q1 Which dependency bots does this repo use? | codebase-explorer | Parallel | None |
| Q2 How does automerge work for those bots? | web-search-researcher | Parallel | None |
| Q3 What automerge config exists in this repo? | codebase-explorer | Sequential | Q1 |
| Q4 What patterns do similar repos use? | codebase-explorer | Sequential | Q1, Q3 |
| Q5 What do Renovate/Dependabot support? | web-search-researcher | Sequential | Q1 |

```
Batch 1: Q1, Q2      -> Q1 reveals "We use Renovate"
Batch 2: Q3, Q5      -> Q3 reveals ".github/renovate.json5 with automerge disabled"
Batch 3: Q4          -> search for repos with Renovate and automerge: true
```
