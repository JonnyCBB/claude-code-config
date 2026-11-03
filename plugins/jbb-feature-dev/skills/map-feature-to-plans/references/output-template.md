# Scoping Document Template

For a single-plan result, keep the frontmatter, Splitting Decision and Autonomous
Decisions sections and omit the rest.

````markdown
---
date: YYYY-MM-DD
type: scoping
source_research_doc: "[path]"
feature_name: "[name]"
plan_count: N
status: draft
---

# Scoping: [Feature Name]

## Splitting Decision

**Decision**: Single plan / Multiple plans (N)
**Justifications checked**: context fit, risk / landing order, checkpoint, separate
delivery. [For each: holds or not, with the evidence.]

## Plan Outlines

### Plan 1: [Name]

- **Scope**: [end-to-end behaviour this plan delivers]
- **Files**: [list]
- **Dependencies**: None

### Plan 2: [Name]

- **Scope**: [...]
- **Files**: [list]
- **Justification**: [one of the four, with evidence]
- **Dependencies**: Plan 1 ([the concrete artifact it needs])

## Dependency Graph

```
Plan 1 ──→ Plan 2
Plan 1 ──→ Plan 3 (parallel with Plan 2)
```

## Execution Wave Strategy

| Wave | Plans          | Execution         |
| ---- | -------------- | ----------------- |
| 1    | Plan 1         | Sequential        |
| 2    | Plan 2, Plan 3 | Parallel planning |

## PR Strategy

**Strategy**: Single PR per repo / Stacked PRs
**Rationale**: [which justification requires separate merges, or the repo precedent]

### Branch Chain

Include only when the strategy is "Stacked PRs".

| Plan   | Branch Name             | Base Branch             | Estimated LOC |
| ------ | ----------------------- | ----------------------- | ------------- |
| Plan 1 | feat/<prefix>-<slice-1> | master                  | N             |
| Plan 2 | feat/<prefix>-<slice-2> | feat/<prefix>-<slice-1> | N             |

## Autonomous Decisions

Non-interactive runs only.

### Review Synthesis

[Each Must Address item and how it was resolved; Should Consider items as advisory notes.]
````

## Branch Chain rules

`implement-plan-tdd`, `submit-pr` and `rebase-stack` read the Branch Name and Base Branch
columns and process rows top to bottom, so:

- Row order is dependency order.
- A plan with no upstream dependency has the repo default branch as its Base Branch.
- A dependent plan's Base Branch is the Branch Name of the plan it depends on. A plan
  with several upstreams needs them chained one after another above it, so its Base
  Branch contains all of them.
- Independent plans each list the default branch; they form separate stacks, not one
  chain.
