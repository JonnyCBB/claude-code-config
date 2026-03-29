# Requirements Document Template

Write the requirements document using this structure. Sections marked (required) must always
be present. Sections marked (if applicable) should be included when relevant information was
gathered during the interview.

## Compatibility Note

Sections marked with * are compatible with the claude-agent-orchestrator interview.py output
format (Objective, Context, Constraints, References, Success Criteria). Additional sections
extend beyond interview.py's 5 categories.

---

## Template

```markdown
---
date: YYYY-MM-DD
author: [interviewer]
topic: "[feature/task description]"
status: draft
scope_mode: [mvp | complete | ambitious]
related_ticket: "[ticket ID or N/A]"
related_research: "[path to research doc or N/A]"
---

# Requirements: [Feature/Task Name]

## Objective *
[1-3 sentences: What are we building and why? What problem does it solve?]

## Context *
[Current state: what exists today, what's changing, which systems are involved.
Include repo paths and component names.]

## Scope

| Feature / Sub-task | Priority | Rationale |
|--------------------|----------|-----------|
| [Feature 1] | Essential | [Why it's needed for v1] |
| [Feature 2] | Nice-to-have | [Why it can wait] |
| [Feature 3] | Not needed | [Why it's out of scope] |

## Acceptance Criteria

GIVEN [precondition]
WHEN [action]
THEN [expected outcome]

GIVEN [precondition]
WHEN [action]
THEN [expected outcome]

## Success Criteria *
[How will we know this succeeded? Metrics, user behavior changes, or operational improvements.]

## Constraints *
[Technical constraints, deadlines, dependencies, organizational constraints.
Include any merge freezes, release cuts, or stakeholder approval requirements.]

## Non-Functional Requirements (if applicable)
[Latency budgets, throughput targets, availability requirements, security considerations.]

## Domain-Specific Requirements (if applicable)
[Requirements specific to the detected domain — API contracts, SLOs, model metrics, etc.]

## Historical Context (if applicable)
[Prior attempts, known pitfalls, temporal considerations for implementation.]

## References *
[Links to tickets, research docs, Slack threads, design docs, related PRs.]

## Assumptions (non-interactive mode only)
[For each assumption made without human confirmation:]

ASSUMPTION: [what was assumed]
CONFIDENCE: [high | medium | low]
IF WRONG: [what would need to change]
```
