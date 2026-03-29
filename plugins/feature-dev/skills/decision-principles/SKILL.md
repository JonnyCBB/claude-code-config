---
name: decision-principles
description: >
  Decision-making principles for agent teams reviewing research, plans, and code.
  Use when resolving open questions, choosing between approaches, making design
  decisions, gathering requirements, or reviewing technical documents. Provides
  14 ranked principles with defaults, override conditions, and priority ordering
  for conflict resolution.
---

# Decision-Making Principles

## When to Apply

Use these principles when:

- Resolving open questions in research or plans
- Choosing between design approaches
- Reviewing RFCs, PRs, or implementation plans
- Making decisions during implementation where the plan leaves room for judgement
- Gathering requirements and deciding when to ask the human vs. proceed autonomously

Do NOT use for:

- Codebase-discoverable decisions (naming, import ordering)
- Tool-specific configuration (those belong in domain skills)

## Decision Workflow

When facing a choice, check these two non-negotiable guardrails first, then reason
contextually using the Quick Reference table and Priority Ordering below.

1. **Check safety** — Does any option involve bypassing safety mechanisms? If yes, default to
   the safe option (Principle 1). No other principle overrides this.

2. **Check request flow efficiency** — In request flows, does the option introduce unnecessary
   sequential operations? Default to concurrency unless there's a data dependency (Principle 11).

For all other considerations — evidence, simplicity, scope, precedent, consolidation — use your
contextual reasoning informed by the principles in the Quick Reference table. The Priority
Ordering resolves conflicts when principles tension against each other.

## Priority Ordering

When principles conflict:

1. **Safety First** (P1) — always wins
2. **Specification Completeness** (P12) — can't proceed without requirements
3. **Confidence-Based Escalation** (P13) — ask before assuming
4. **Evidence Over Opinion** (P5) — follow the data
5. **Request Flow Efficiency** (P11) — concurrency unless data dependency
6. **Domain-Adaptive Questioning** (P14) — right questions for the domain
7. **Simplicity** (P2 override) — simpler wins unless safety or evidence says otherwise
8. **Current Need Over Future Vision** (P3) — don't build for speculation
9. **Everything else** (P4, P6-P10) — use judgement

## Quick Reference

| #   | Principle                         | Default                                                | Override When                                           |
| --- | --------------------------------- | ------------------------------------------------------ | ------------------------------------------------------- |
| 1   | Safety First                      | Don't send unvetted results                            | Content source is pre-vetted                            |
| 2   | Follow Codebase Precedent         | Model after existing patterns                          | Alternative is significantly simpler                    |
| 3   | Scope to Current Need             | Build minimum for current use case                     | Future need is certain AND retrofitting is expensive    |
| 4   | "Too Complex for v1"              | Say no to scope-creeping questions                     | Feature is a safety requirement or trivially small      |
| 5   | Evidence Over Opinion             | Back decisions with data                               | Decision is low-stakes and aesthetic                    |
| 6   | Consolidate Over Proliferate      | Merge similar components                               | Components have different failure modes                 |
| 7   | Learn From Incidents              | Inform designs from production incidents               | (Always check — no clean override)                      |
| 8   | Check Internal Tools First        | Check internal tools before external                   | No internal tool exists or it's deprecated              |
| 9   | Delegate Aesthetic Decisions      | Let implementer decide low-stakes choices              | Choice creates structural dependencies                  |
| 10  | Document Rejected Approaches      | Always document alternatives with rationale            | (No override — always do this)                          |
| 11  | Optimize Request Flow Efficiency  | Run new operations concurrently                        | Operation depends on another's output                   |
| 12  | Verify Specification Completeness | Verify acceptance criteria and scope before proceeding | Well-specified bug fix or pure refactoring              |
| 13  | Confidence-Based Escalation       | Ask rather than assume when confidence is below high   | Non-interactive mode (document assumptions instead)     |
| 14  | Domain-Adaptive Questioning       | Adapt question depth and categories to domain          | Pure infrastructure/refactoring with no behavior change |

## Override Guidance

When overriding a principle, document which principle is being overridden and which
override condition applies. This is guidance, not a mandate — the goal is traceability
for future readers.

For full principle details with examples and evidence, read `references/principles-detail.md`.
