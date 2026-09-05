# Tactical Splitting Criteria

Use these criteria in Step 2 of the map-feature-to-plans skill to determine whether a single feature
should be split into multiple implementation plans.

**Single plan is the default outcome.** Splitting is a cost: every additional plan adds a full
planning pass (~49 min observed), a strictly-sequential implementation pass (~75 min observed),
and per-plan research overhead in `/create-plan-tdd`. Split only when the evidence below demands it.

Two classes of criteria:

- **Hard triggers** — any one forces a split: context-window overflow, dependency conflicts,
  risk isolation.
- **Soft flags** — size signals (LOC, file count). A soft flag alone never forces a split;
  it requires a corroborating signal — a domain-boundary crossing, a verifiability
  failure, or a risk trigger — before splitting.

If nothing triggers, output "single plan" — the map-feature-to-plans step is a no-op pass-through.

---

## 1. Size-Based (soft flags)

| Signal        | Threshold   | Action                                        | Source                                                 |
| ------------- | ----------- | --------------------------------------------- | ------------------------------------------------------ |
| Estimated LOC | >2000 lines | Flag — split only with a corroborating signal | Sonnet 5 planner/implementer calibration (v2, 2026-07) |
| Files touched | >25 files   | Flag — split only with a corroborating signal | Sonnet 5 planner/implementer calibration (v2, 2026-07) |

A corroborating signal is one of: changes cross >2 domain boundaries, a verifiability
failure (section 4), or a risk trigger (section 5). Test files and BUILD/build-config files
count toward the file total but rarely justify a split on their own — a service change plus
its tests and BUILD edits is normal single-plan work.

## 2. Context-Window (hard trigger)

| Signal         | Threshold                                                 | Action     |
| -------------- | --------------------------------------------------------- | ---------- |
| Context window | Plan material >75% of the planning model's context window | Must split |

This is a physical constraint, not a calibration choice. Count tokens with the CURRENT
model's tokenizer: Sonnet 5's tokenizer produces ~30% more tokens than Sonnet 4.x for the
same text, so token estimates carried over from older calibrations undercount. When in
doubt, estimate from the actual research-doc + file-content volume, not from remembered
per-file averages.

## 3. Dependency-Based (hard triggers)

| Signal                     | Rule                                     | Action                                       |
| -------------------------- | ---------------------------------------- | -------------------------------------------- |
| Shared files               | Two plan slices touching the same files  | Sequence them (same wave = conflict)         |
| API contracts              | Consumer plan needs provider plan's API  | Provider plan must complete first            |
| Data model                 | Schema changes needed before API changes | Schema plan → API plan → Frontend plan       |
| Shared test infrastructure | Multiple plans need common fixtures      | Extract to Plan 0 (only if >1 plan needs it) |

Dependency rules govern how plans are sequenced once a split exists; a dependency between
two halves of a feature is only a reason to split if the halves must land in separate PRs.

## 4. Verifiability-Based

| Signal                  | Rule                                                                     |
| ----------------------- | ------------------------------------------------------------------------ |
| Independent testability | Each plan MUST have concrete verification (tests, lint, build)           |
| Self-check capability   | Agent must be able to run verification within its session                |
| Evidence requirement    | Each plan produces evidence: passing tests, clean lint, successful build |

A plan that cannot be independently verified is not a valid plan — merge it with another
or split differently.

## 5. Risk-Based (hard triggers)

| Signal               | Rule                                                                     |
| -------------------- | ------------------------------------------------------------------------ |
| High-risk components | Auth, payments, data migrations, cryptography → isolate in separate plan |
| Destructive changes  | DROP TABLE, schema migration → never in same plan as consumer changes    |
| Feature flags        | Medium-risk changes → plan should include flag setup                     |

Risk isolation overrides size: a risk-class artifact forces its own plan regardless of how
small the combined work would be.

## No-Op Heuristic

If no hard trigger fires and no corroborated soft flag stands:

- Estimated LOC <= 2000 (or larger with no corroborating signal)
- Files touched <= 25 (or more with no corroborating signal)
- Plan material fits comfortably under 75% of the planning model's context window
- No dependency conflicts
- No high-risk components

Then output **"single plan"** with a brief rationale. The map-feature-to-plans step is a pass-through —
proceed directly to `/create-plan-tdd` with the full research document.
