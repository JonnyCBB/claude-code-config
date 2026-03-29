# Tactical Splitting Criteria

Use these criteria in Step 2 of the map-feature-to-plans skill to determine whether a single feature
should be split into multiple implementation plans.

Apply criteria in order. If ANY criterion triggers, flag for splitting.
If NO criteria trigger, output "single plan" — the map-feature-to-plans step is a no-op pass-through.

---

## 1. Size-Based

| Signal         | Threshold                                        | Action             | Source                   |
| -------------- | ------------------------------------------------ | ------------------ | ------------------------ |
| Estimated LOC  | >600 lines                                       | Must split         | Google/Cisco PR research |
| Files touched  | >10 files                                        | Flag for splitting | GSD, Amazon Q            |
| Context window | >50% of available (~100K tokens for 200K window) | Must split         | GSD heuristic            |

## 2. Dependency-Based

| Signal                     | Rule                                     | Action                                       |
| -------------------------- | ---------------------------------------- | -------------------------------------------- |
| Shared files               | Two plan slices touching the same files  | Sequence them (same wave = conflict)         |
| API contracts              | Consumer plan needs provider plan's API  | Provider plan must complete first            |
| Data model                 | Schema changes needed before API changes | Schema plan → API plan → Frontend plan       |
| Shared test infrastructure | Multiple plans need common fixtures      | Extract to Plan 0 (only if >1 plan needs it) |

## 3. Verifiability-Based

| Signal                  | Rule                                                                     |
| ----------------------- | ------------------------------------------------------------------------ |
| Independent testability | Each plan MUST have concrete verification (tests, lint, build)           |
| Self-check capability   | Agent must be able to run verification within its session                |
| Evidence requirement    | Each plan produces evidence: passing tests, clean lint, successful build |

A plan that cannot be independently verified is not a valid plan — merge it with another
or split differently.

## 4. Risk-Based

| Signal               | Rule                                                                     |
| -------------------- | ------------------------------------------------------------------------ |
| High-risk components | Auth, payments, data migrations, cryptography → isolate in separate plan |
| Destructive changes  | DROP TABLE, schema migration → never in same plan as consumer changes    |
| Feature flags        | Medium-risk changes → plan should include flag setup                     |

## No-Op Heuristic

If NONE of the above criteria trigger:

- Estimated LOC <= 600
- Files touched <= 10
- Context budget is comfortable
- No dependency conflicts
- No high-risk components

Then output **"single plan"** with a brief rationale. The map-feature-to-plans step is a pass-through —
proceed directly to `/create-plan-tdd` with the full research document.
