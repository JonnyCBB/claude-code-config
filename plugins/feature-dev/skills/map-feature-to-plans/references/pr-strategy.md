# Adaptive PR Strategy

Use this in Step 3 of the map-feature-to-plans skill to determine the PR strategy for multi-plan work.

---

## Decision Table

| Estimated Total Diff | Strategy                                   | Rationale                              |
| -------------------- | ------------------------------------------ | -------------------------------------- |
| < 500 lines          | Single PR per repo                         | Stacking overhead not worth it         |
| 500-1500 lines       | Stacked PRs per repo (one per plan)        | Keeps each PR reviewable               |
| > 1500 lines         | Stacked PRs per repo + consider re-scoping | Total diff too large even when stacked |

## Defect Detection by PR Size

| Lines Changed | Defect Detection Rate |
| ------------- | --------------------- |
| 1-100         | 87%                   |
| 101-300       | 78%                   |
| 301-600       | 65%                   |
| 601-1,000     | 42%                   |
| 1,000+        | 28%                   |

Source: Google, Cisco/SmartBear, Graphite research

## Stacked PR Mechanics

**Branch naming**: Each plan creates a branch based on the previous plan's branch:

```
feat/ftp-infra      → PR 1 (base: master)
feat/ftp-slice-a    → PR 2 (base: feat/ftp-infra)
feat/ftp-slice-b    → PR 3 (base: feat/ftp-slice-a)
```

**Each PR shows only its own diff.** Reviewers see small, focused changes.

**Creation order**: Dependency order (blockers first) so real issue/PR numbers can
be referenced.

## Multi-Repo Handling

Each repository gets its own independent PR chain. Stacking is within a single repo
only. For features spanning multiple repos, each repo has its own scoping document
and PR strategy.

## When to Re-Scope

If estimated total exceeds 1500 lines, suggest re-running `/map-feature-to-plans` with tighter
splitting criteria before proceeding to planning.
