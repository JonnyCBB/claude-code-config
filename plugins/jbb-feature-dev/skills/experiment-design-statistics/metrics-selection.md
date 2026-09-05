# Metrics Selection

Choosing the right metrics for experiments.

## Metric Categories

The current EP taxonomy has two "decision metric" types (they determine the ship/hold call) plus one non-decision type — this replaced an older "Primary/Secondary/Guardrail" framing that's no longer accurate:

### Success Metrics

Single metric (or small set) that defines the experiment's ship/hold decision.

**Characteristics:**

- Directly measures business value
- Has clear expected direction
- Sensitive enough to detect change

**Examples:**

| Domain     | Success Metric      |
| ---------- | -------------------- |
| Search     | Query success rate   |
| Playback   | Stream starts        |
| Conversion | Premium signups      |

### Guardrail Metrics

Decision-driving safety checks that should NOT degrade.

**Guardrails are surface/team-specific, not a universal fixed list.** Concretely, as a worked example of documented per-surface requirements: a wearables surface might require WAU/DAU/session-length/active-users/crash-event guardrails; Home requires Active Days + consumption metrics plus Podcast/Audiobook engagement; User Protection requires D1 DAU, login success rate, signup success rate, and D0 crash rate. Error rate, latency, and crash rate do show up as guardrails on some surfaces, and as system-level auto-pause thresholds for some services — but don't present them as a blanket "must-have" set for every experiment; check what your surface/team actually requires.

### Exploratory Metrics

Everything else — added for context and mechanism understanding, but not part of the ship/hold decision.

**Purpose:**

- Understand mechanism of change
- Detect unintended effects
- Provide additional context

## Metrics Hub Integration

Metrics are defined in Metrics Hub (a legacy "Metrics Catalog" still coexists during an ongoing migration — Metrics Hub is the current direction of travel):

- Search for existing metrics first
- Create new metrics if needed
- Ensure proper exposure alignment

## Metric Selection Checklist

| Question                                        | Answer |
| ------------------------------------------------ | ------ |
| Is the success metric tied to a business goal?    |        |
| Can we detect the expected effect size?           |        |
| Do we have the guardrails our surface/team requires? |     |
| Are metrics available in Metrics Hub?             |        |

## Common Mistakes

| Mistake                    | Problem              | Fix                                                   |
| --------------------------- | --------------------- | ------------------------------------------------------ |
| Too many success metrics    | Unclear decision      | Pick one (or a small, explicitly-prioritized set)      |
| No guardrails               | Miss regressions      | Check your surface/team's required guardrails, don't assume a generic list |
| Vanity metrics               | No business value     | Tie to outcomes                                        |
