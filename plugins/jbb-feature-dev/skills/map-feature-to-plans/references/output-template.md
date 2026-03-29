# Scoping Document Template

Use this template when writing the scoping document in Step 5 of the map-feature-to-plans skill.

---

```markdown
---
date: YYYY-MM-DD
type: scoping
source_research_doc: "[path to the research document]"
feature_name: "[name of the feature being scoped]"
status: draft
---

# Scoping: [Feature Name]

## Source Research Document

[Link or path to the research document that was scoped]

## Complexity Assessment

- **Estimated files changed**: N
- **Estimated LOC**: N
- **Domains crossed**: [list]
- **Risk level**: low / medium / high

## Splitting Decision

**Decision**: Single plan / Multiple plans
**Rationale**: [Why — which criteria triggered splitting, or why none triggered]

## Plan Outlines

### Plan 0: Test Infrastructure (Wave 0)

> Only include if multiple plans depend on shared test infrastructure.
> If only one plan needs test setup, keep it internal to that plan's Wave 0.

- **Scope**: [shared fixtures, test utilities, framework config]
- **Files**: [list]
- **Dependencies**: None

### Plan 1: [Feature Slice A]

- **Scope**: [what this plan covers — end-to-end behavior description]
- **Files**: [list of files to be touched]
- **Estimated LOC**: N
- **Dependencies**: Plan 0 (if exists)

### Plan 2: [Feature Slice B]

- **Scope**: [what this plan covers]
- **Files**: [list]
- **Estimated LOC**: N
- **Dependencies**: Plan 0 (if exists)

## Wave 0 Assessment

**Shared test infrastructure needed?**: Yes / No
**Rationale**: [Do multiple plans depend on common test fixtures/helpers?]

## Dependency Graph
```

Plan 0 (infra) ──→ Plan 1 (parallel with Plan 2)
Plan 0 (infra) ──→ Plan 2 (parallel with Plan 1)
Plan 1 ──→ Plan 3 (depends on Plan 1)

```

## Execution Wave Strategy

| Wave | Plans | Execution |
|------|-------|-----------|
| 0 | Plan 0 (test infrastructure) | Sequential |
| 1 | Plan 1, Plan 2 | Parallel |
| 2 | Plan 3 | Sequential (depends on Wave 1) |

## PR Strategy

**Estimated total diff**: N lines
**Strategy**: Single PR / Stacked PRs / Stacked PRs + re-scope
**Rationale**: [Based on adaptive thresholds from pr-strategy.md]

## Suggested Next Steps

For each plan:
- Plan 0: `/create-plan-tdd "Plan 0 outline"`
- Plan 1: `/create-plan-tdd "Plan 1 outline"` (after Plan 0)
- Plan 2: `/create-plan-tdd "Plan 2 outline"` (parallel with Plan 1, after Plan 0)
```
