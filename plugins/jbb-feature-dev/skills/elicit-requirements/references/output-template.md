# Requirements Document Template

Write outcomes and observable evidence, not a proposed implementation or guessed test
commands. A named technique belongs in Constraints only when its source establishes a
compatibility, policy, or product need; otherwise it can be noted as a possible approach
in Context. Keep owner-confirmed decisions, independently verified facts, reversible agent
choices, and unconfirmed assumptions distinguishable.

## Compatibility Note

Sections marked with \* are compatible with the claude-agent-orchestrator interview.py output
format (Objective, Context, Constraints, References, Success Criteria). Additional sections
extend beyond interview.py's 5 categories.

---

## Template

```markdown
---
date: YYYY-MM-DD
author: [agent]
topic: "[feature/task description]"
status: draft
scope_mode: [mvp | complete | ambitious]
scope_mode_confirmed: [true | false]
related_ticket: "[ticket ID or N/A]"
related_research: "[path to research doc or N/A]"
---

# Requirements: [Feature/Task Name]

## Objective \*

[1-3 sentences: What are we building and why? What problem does it solve?]

## Context \*

[Current state and relevant systems. Attribute researched facts to their sources;
separate possible implementation approaches from required outcomes.]

## Terminology (if applicable)

| Term                 | Canonical referent                        |
| -------------------- | ----------------------------------------- |
| [term the user used] | [what it means in this feature's context] |

Include only when a semantic fork was resolved during the interview.

## Scope

| Feature / Sub-task | Priority     | Rationale                |
| ------------------ | ------------ | ------------------------ |
| [Feature 1]        | Essential    | [Why it's needed for v1] |
| [Feature 2]        | Nice-to-have | [Why it can wait]        |
| [Feature 3]        | Not needed   | [Why it's out of scope]  |

## Acceptance Criteria

GIVEN [meaningful starting condition]
WHEN [event or action]
THEN [what someone can observe or do, not a restatement of the precondition]

[Include meaningful exclusions and failure behavior. For a time window, leave its
reference event and boundary unresolved when not supplied. Do not invent the
interaction shape, output contents, or clock start.
Repeat for each distinct scenario. Do not add AC-N labels by default.]

## Success Criteria \*

[Observable result or type of evidence that would demonstrate success. Leave the
choice of local verification command to the implementer unless an external constraint
requires one; cite that constraint.]

## Constraints \*

[Owner-stated or sourced compatibility, policy, product, timing, or dependency limits.
Do not add general permissions to commit, deploy, spend, or message people.]

## Decisions (if applicable)

[Consequential choices the owner explicitly confirmed, with the answer's source.
Do not infer approval from a document the owner has not reviewed.]

## Technical Assumptions (if applicable)

[Only low-impact reversible implementation choices needed to interpret the document:
Decision: [choice]; Why: [basis]; Reversibility: [what changing it entails].
These are agent choices, not owner-approved requirements.]

## Non-Functional Requirements (if applicable)

[Latency budgets, throughput targets, availability requirements, security considerations.]

## Domain-Specific Requirements (if applicable)

[Requirements specific to the detected domain — API contracts, SLOs, model metrics, etc.]

## Historical Context (if applicable)

[Prior attempts, known pitfalls, temporal considerations for implementation.]

## References \*

[Links to tickets, research docs, Slack threads, design docs, related PRs.]

## Unknown Terms (if applicable)

Jargon encountered during the interview that the agent did not pause to clarify (not a
semantic fork — just unfamiliar). `/research-problem` should resolve these downstream.

- UNKNOWN_TERM: [term 1]
- UNKNOWN_TERM: [term 2]

## Assumptions (non-interactive mode only)

[For each unresolved consequential choice, never presented as owner approval. If
scope mode was not chosen, set scope_mode: mvp as a drafting default with
scope_mode_confirmed: false and record that provisional choice here:]

ASSUMPTION: [unconfirmed choice]
BASIS: [evidence, or state none]
CONFIDENCE: [high | medium | low]
OWNER: [decision owner if known, or unknown]
IF WRONG: [what would need to change]

In non-interactive mode, mirror each `UNKNOWN_TERM` marker here with CONFIDENCE=low and
IF-WRONG pointing at the downstream `/research-problem` step.
```
