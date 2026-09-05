# Requirements Document Template (friendly variant)

Write the requirements document using this structure. Sections marked (required) must always
be present. Sections marked (if applicable) should be included when relevant information was
gathered during requirements elicitation.

The friendly variant inherits the schema of `elicit-requirements/references/output-template.md`
verbatim and adds one new section — `## Technical Assumptions` — to surface silent decisions
the agent made during the interview. The downstream contract with `/research-problem` and
`/create-plan-tdd` is unchanged: every section those tools rely on is preserved.

## Compatibility Note

Sections marked with \* are compatible with the claude-agent-orchestrator interview.py output
format (Objective, Context, Constraints, References, Success Criteria). Additional sections
extend beyond interview.py's 5 categories. The friendly variant adds `## Technical Assumptions`
on top of the existing schema; otherwise the structure matches the standard `elicit-requirements`
template exactly so downstream consumers do not need to branch on which skill produced the doc.

---

## Template

```markdown
---
date: YYYY-MM-DD
author: [agent]
topic: "[feature/task description]"
status: draft
scope_mode: [mvp | complete | ambitious]
related_ticket: "[ticket ID or N/A]"
related_research: "[path to research doc or N/A]"
---

# Requirements: [Feature/Task Name]

## Objective \*

[1-3 sentences: What are we building and why? What problem does it solve?]

## Context \*

[Current state: what exists today, what's changing, which systems are involved.
Include repo paths and component names.]

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

GIVEN [precondition]
WHEN [action]
THEN [expected outcome]

GIVEN [precondition]
WHEN [action]
THEN [expected outcome]

## Success Criteria \*

[How will we know this succeeded? Metrics, user behavior changes, or operational improvements.]

## Constraints \*

[Technical constraints, deadlines, dependencies, organizational constraints.
Include any merge freezes, release cuts, or stakeholder approval requirements.]

## Technical Assumptions

Silent decisions the agent made during Steps 1-4 that the user did not need to weigh in on.
Each entry uses the decisions-log shape (see `references/escalation-and-authority.md`):
Decision, Why, Reversibility. The user reviews this section during Step 5 (mutual
confirmation) and may reject any entry; rejections move the decision back into the interview.

### [Short label for the decision]

- Decision: [what was decided silently]
- Why: [grounding evidence — code path, ticket, prior convention, research doc]
- Reversibility: [easy | medium | hard] — [one-line note on what flipping the decision would cost]

### [Another decision]

- Decision: [...]
- Why: [...]
- Reversibility: [...] — [...]

## Non-Functional Requirements (if applicable)

[Latency budgets, throughput targets, availability requirements, security considerations.
For the friendly variant, the agent collects these via NFR Probes from
`references/question-bank.md` in user-language and writes them in their proper
non-functional category here.]

## Domain-Specific Requirements (if applicable)

[Requirements specific to the detected domain — API contracts, SLOs, model metrics, etc.]

## Historical Context (if applicable)

[Prior attempts, known pitfalls, temporal considerations for implementation.]

## References \*

[Links to tickets, research docs, Slack threads, design docs, related PRs.]

## Assumptions (non-interactive mode only)

[For each assumption made without human confirmation:]

ASSUMPTION: [what was assumed]
CONFIDENCE: [high | medium | low]
IF WRONG: [what would need to change]
```
