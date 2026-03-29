# Interview Question Dimensions

This file provides guidance dimensions and example question patterns for the interview skill.
These are NOT fixed questions — the agent generates contextually appropriate questions based on
the specific feature being discussed. Use these dimensions to ensure important topics are covered,
and adapt the wording to the situation.

## Recommended Asking Order

1. Premise challenge (is this the right problem?)
2. Scope mode (MVP / Complete / Ambitious)
3. Core clarifying questions (motivation, acceptance criteria, success metrics, scope)
4. Situational questions (as relevant)
5. Domain-specific questions (based on detected domain)

## Domain Detection

Detect domain from the task description and referenced files:

| Domain         | Signals                                                                  |
| -------------- | ------------------------------------------------------------------------ |
| Backend/APIs   | gRPC, REST, endpoint, service, client, timeout, latency, Apollo, handler |
| Data Pipelines | BigQuery, pipeline, endpoint, SLO, partition                             |
| ML Models      | model, training, inference, features, evaluation, metrics                |

When multiple domains apply, ask questions from all relevant domains.

---

## Core Dimensions (most interviews should cover these)

### 1. Premise Challenge

**Why research can't answer**: Research finds what exists; only the human knows if building something new is the right move.
**Example**: "Before we dive in — what happens if we do nothing? Is this solving a real pain point, or a hypothetical one?"
**Options pattern**: A) Real pain point — [describe impact] B) Preventive — avoids future problem C) Opportunistic — nice to have but not urgent
**Skip if**: The task is a bug fix with clear reproduction steps, or a well-defined ticket with stakeholder sign-off already documented.

### 2. Scope Mode

**Why research can't answer**: Scope posture is a human judgment call about ambition vs. speed.
**Example**: "What's your scope posture for this work?"
**Options pattern**: A) MVP — minimum that ships value, cut everything else B) Complete — full scope as described, make it bulletproof C) Ambitious — go beyond the ask if it creates a better outcome
**Skip if**: The ticket explicitly states scope (e.g., "quick fix", "full feature", "spike").

### 3. Motivation & Business Context

**Why research can't answer**: Business drivers live in stakeholder heads, not in code.
**Example**: "What problem does this solve, and why now? What business outcome does it drive?"
**Skip if**: A ticket or research doc already contains a clear problem statement with business context.

### 4. Acceptance Criteria

**Why research can't answer**: Code shows current behavior, not desired future behavior.
**Example**: "What does 'done' look like? Can you describe 1-2 key scenarios in GIVEN/WHEN/THEN format?"
**Options pattern**: Offer to draft acceptance criteria from the description for the user to confirm/edit.
**Skip if**: The input already contains 2+ explicit acceptance criteria or GIVEN/WHEN/THEN scenarios.

### 5. Success Metrics

**Why research can't answer**: Not in code unless previously instrumented.
**Example**: "How will you know this succeeded? What metric moves, or what user behavior changes?"
**Skip if**: The input already specifies measurable success criteria.

### 6. Scope Classification

**Why research can't answer**: Prioritization requires human judgment on what matters most.
**Example**: Present discovered features/sub-tasks and ask: "For each, is this Essential, Nice-to-have, or Not needed for v1?"
**Options pattern**: Table format — Feature | Essential / Nice-to-have / Not needed
**Skip if**: The input already classifies scope or has a single, atomic task with no sub-features.

---

## Situational Dimensions (ask when relevant)

### 7. Edge Cases & Error Handling

**Why research can't answer**: Research finds tested cases; humans know which untested cases matter.
**Example**: "Which edge cases matter most for v1? Any failure scenarios you're particularly worried about?"
**Skip if**: Task is a pure refactoring with no behavior change, or acceptance criteria already cover edge cases.

### 8. Non-Functional Requirements

**Why research can't answer**: /operational-context gets current metrics; humans know the TARGET for new features.
**Example**: "Any specific latency budget, throughput target, or availability requirement for this feature?"
**Skip if**: Task is internal tooling with no SLO, or operational context doc already specifies targets.

### 9. Deployment & Rollout

**Why research can't answer**: Rollout strategy is often undocumented team convention.
**Example**: "How should this roll out? Feature flag? Staged rollout? Big bang?"
**Options pattern**: A) Feature flag with gradual ramp B) Staged rollout (canary → percentage → full) C) Direct deploy (low risk, easily reversible) D) Other
**Skip if**: Task is a config change or documentation update with no deployment implications.

### 10. Historical Context & Temporal

**Why research can't answer**: Past failed attempts and future implementation pitfalls live in human memory.
**Example**: "Has this been tried before, or are there known pitfalls? What will surprise the implementer during integration?"
**Skip if**: Task is greenfield with no prior art, or the research doc already covers historical context.

---

## Domain-Specific Dimensions (worked examples — extend for any domain)

The domains below are worked examples showing HOW to generate domain-specific questions.
They are not a closed list. For any domain not listed here, identify the domain from the
task description and generate domain-appropriate questions using the same pattern.

### Generating questions for unlisted domains

For a domain not covered below, ask yourself:

- What are the domain's **unique quality attributes**? (e.g., for CLIs: ergonomics, shell completion, exit codes; for SDKs: API surface, version support)
- What are the domain's **unique failure modes**? (e.g., for infrastructure: blast radius, rollback; for event systems: ordering, deduplication, backpressure)
- What are the domain's **unique compatibility concerns**? (e.g., for SDKs: backwards compat, deprecation policy; for migrations: data format versioning)
- What are the domain's **unique operational concerns**? (e.g., for monitoring: alert fatigue, dashboard design; for batch jobs: retry strategy, idempotency)

Generate 2-4 questions from the most relevant dimensions above, adapting wording to the specific feature.

### Backend/APIs (ask when backend signals detected)

**11. API Contract & Compatibility**
"Should this be backwards-compatible with existing clients? Any API versioning concerns?"
**Skip if**: Internal-only endpoint with no external consumers.

**12. Timeout & Latency Budget**
"What's the latency budget for this new codepath? How does it fit within the upstream timeout?"
**Skip if**: /operational-context already specifies latency constraints.

**13. Error Response Design**
"How should errors surface to callers? Specific error codes, retry guidance, or degraded responses?"
**Skip if**: Existing error handling patterns in the service cover this case.

### Data Pipelines (ask when data signals detected)

**14. Data Freshness & SLO**
"What's the acceptable data freshness for this output? What SLO should it have?"
**Skip if**: Endpoint already has documented SLO, or this is a one-off backfill.

**15. Schema Evolution & Backwards Compatibility**
"Will this change the output schema? How should downstream consumers handle the transition?"
**Skip if**: No schema change, or schema is append-only (new fields only).

**16. Data Quality & Validation**
"What data quality checks should fail the pipeline? Any known data quality issues in upstream sources?"
**Skip if**: Pure infrastructure/config change with no data transformation.

### ML Models (ask when ML signals detected)

**17. Evaluation Metrics & Thresholds**
"What evaluation metric matters most? What's the minimum acceptable threshold before deployment?"
**Skip if**: Metrics are already defined in an experiment spec or model card.

**18. Training Data & Freshness**
"Where does training data come from? How fresh does it need to be? Any known biases or gaps?"
**Skip if**: Training pipeline is already established and data source is unchanged.

**19. Serving & Latency Requirements**
"What's the serving latency requirement? Online vs batch inference? Model versioning strategy?"
**Skip if**: Serving infrastructure is already established.
