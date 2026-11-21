# Interview Question Dimensions

This file provides guidance dimensions and example question patterns for the elicit-requirements
skill. These are not fixed questions — the agent generates contextually appropriate questions
based on the specific feature being discussed. Use these dimensions to ensure important topics
are considered, and adapt the wording to the situation. Considering a dimension does not
mean producing a requirement for it: most interviews leave several dimensions with none.

## Domain Detection

Detect domain from the task description and referenced files:

| Domain         | Signals                                                                   |
| -------------- | ------------------------------------------------------------------------- |
| Backend/APIs   | gRPC, REST, endpoint, service, client, timeout, latency, Apollo, handler  |
| Data Pipelines | BigQuery, pipeline, endpoint, SLO, partition, scheduler, DAG |
| ML Models      | model, training, inference, serving, features, evaluation, metrics |

When multiple domains apply, ask questions from all relevant domains.

---

## Core Dimensions (most interviews should cover these)

### 1. Premise Challenge

**Wave**: 1
**Why research can't answer**: Research finds what exists; only the human knows if building something new is the right move.
**Example**: "Before we dive in — what happens if we do nothing? Is this solving a real pain point, or a hypothetical one?"
**Options pattern**: A) Real pain point — [describe impact] B) Preventive — avoids future problem C) Opportunistic — nice to have but not urgent
**Skip if**: The task is a bug fix with clear reproduction steps, or a well-defined ticket with stakeholder sign-off already documented.

### 2. Motivation & Business Context

**Wave**: 1
**Why research can't answer**: Business drivers live in stakeholder heads, not in code.
**Example**: "What problem does this solve, and why now? What business outcome does it drive?"
**Skip if**: A ticket or research doc already contains a clear problem statement with business context.

### 3. Acceptance Criteria

**Wave**: 1
**Why research can't answer**: Code shows current behavior, not desired future behavior.
**Example**: "What does 'done' look like? Can you describe 1-2 key scenarios in GIVEN/WHEN/THEN format?"
**Options pattern**: Offer to draft acceptance criteria from the description for the user to confirm/edit.
**Skip if**: The input already contains 2+ explicit acceptance criteria or GIVEN/WHEN/THEN scenarios.

### 4. Success Metrics

**Wave**: 1
**Why research can't answer**: Not in code unless previously instrumented.
**Example**: "How will you know this succeeded? What metric moves, or what user behavior changes?"
**Skip if**: The input already specifies measurable success criteria.

### 5. Scope Classification

**Wave**: 1
**Why research can't answer**: Prioritization requires human judgment on what matters most.
**Example**: Present discovered features/sub-tasks and ask: "For each, is this Essential, Nice-to-have, or Not needed for v1?"
**Options pattern**: Table format — Feature | Essential / Nice-to-have / Not needed
**Skip if**: The input already classifies scope or has a single, atomic task with no sub-features.

---

## Situational Dimensions (ask when relevant)

### 6. Edge Cases & Error Handling

**Wave**: 2
**Why research can't answer**: Research finds tested cases; humans know which untested cases matter.
**Example**: "Which edge cases matter most for v1? Any failure scenarios you're particularly worried about?"
**Stress-test scenarios** (apply when the user's answer is vague): invent concrete
stress-test scenarios and ask the user to adjudicate. Seed from Context Sprint findings when possible.
Each scenario carries a recommended resolution per the Recommended-answer principle.
Invent only enough to resolve the vagueness. A scenario whose answer does not change whether the objective is met produces no requirement.
Examples:

- "When the upstream service returns a 503 during a paginated fetch — do we retry only the
  failed page, restart the whole fetch, or surface a partial result? (I'd suggest retry-
  failed-page for bounded blast radius.)"
- "When the user cancels mid-request after partial state has been written — do we roll
  back, mark-incomplete, or leave as-is? (I'd suggest mark-incomplete with a visible
  status.)"
  **Skip if**: Task is a pure refactoring with no behavior change, or acceptance criteria already cover edge cases.

### 7. Non-Functional Requirements

**Wave**: 2
**Why research can't answer**: research can read current metrics; humans know the TARGET for new features.
**Example**: "Any specific latency budget, throughput target, or availability requirement for this feature?"
**Skip if**: Task is internal tooling with no SLO, or operational context doc already specifies targets.

### 8. Deployment & Rollout

**Wave**: 2
**Why research can't answer**: Rollout strategy is often undocumented team convention.
**Example**: "How should this roll out? Feature flag? Staged rollout? Big bang?"
**Options pattern**: A) Feature flag with gradual ramp B) Staged rollout (canary → percentage → full) C) Direct deploy (low risk, easily reversible) D) Other
**Skip if**: Task is a config change or documentation update with no deployment implications.

### 9. Historical Context & Temporal

**Wave**: 2
**Why research can't answer**: Past failed attempts and future implementation pitfalls live in human memory.
**Example**: "Has this been tried before, or are there known pitfalls? What will surprise the implementer during integration?"
**Skip if**: Task is greenfield with no prior art, or the research doc already covers historical context.

---

## Domain-Specific Dimensions (Wave 3)

For each detected domain, generate 2-4 questions from what is unique to it:

- What are the domain's **unique quality attributes**? (e.g., for CLIs: ergonomics, shell completion, exit codes; for SDKs: API surface, version support)
- What are the domain's **unique failure modes**? (e.g., for infrastructure: blast radius, rollback; for event systems: ordering, deduplication, backpressure)
- What are the domain's **unique compatibility concerns**? (e.g., for SDKs: backwards compat, deprecation policy; for migrations: data format versioning)
- What are the domain's **unique operational concerns**? (e.g., for monitoring: alert fatigue, dashboard design; for batch jobs: retry strategy, idempotency)
