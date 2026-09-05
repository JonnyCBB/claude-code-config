# Sample Size

Power analysis and experiment sizing.

## Key Inputs

| Input | Description | Typical Value |
|-------|-------------|---------------|
| Baseline Rate | Current metric value | From historical data |
| MDE | Minimum Detectable Effect | Business requirement |
| Power | Probability of detecting effect | 80% |
| Significance | False positive rate | 5% |

## Reducing Required Sample Size: Sequential Testing and CUPED

Before sizing an experiment from the rough table below, know that two techniques can reduce the sample size/duration needed for a given MDE:

- **Sequential testing** is a current, mainstream, first-class capability — EP's own Golden Path glossary lists "Sequential testing" as a selectable "Horizon Strategy" (vs. "Fixed horizon testing"), letting you observe results at any time rather than waiting for a fixed sample. Available in mainstream confidence-interval libraries via an always-valid / sequential correction method.
- **CUPED** (variance reduction) is real and available in the same class of library, but treat it as less mature than sequential testing: current best-practices documentation frames it as still being evaluated internally ("the field is still at the stage of comparing how effective variance reduction techniques have been... arguing for their adoption"), even though it's marketed as a fully mainstream feature externally. Try it, but don't assume it's uniformly deployed for every metric yet.

The rough table below doesn't account for either technique — a team using sequential testing or CUPED may need meaningfully less sample/duration than it suggests.

## Quick Sizing Guide (rough starting point only)

### By Effect Size

| Expected Effect | Sample per Variant | Total Duration |
|-----------------|-------------------|----------------|
| Large (>10%) | 5K-10K | Days |
| Medium (3-10%) | 20K-100K | 1-2 weeks |
| Small (1-3%) | 100K-500K | 2-4 weeks |
| Very Small (<1%) | 500K+ | 4+ weeks |

### By Metric Type

| Metric Type | Typical Sensitivity |
|-------------|-------------------|
| Conversion (rare) | Needs large N |
| Engagement (common) | Medium N |
| Revenue (high variance) | Needs large N |

## EP/C4S Sample Size Calculator

Use the built-in calculator in the EP or C4S UI (both platforms have one):

1. Enter baseline metric value
2. Enter minimum detectable effect
3. Get required sample size

**Not universal**: some teams can't use the built-in calculator. User Protection's own documentation states it doesn't account for their aggressive post-hoc exposure filtering, and they size manually via a stats library instead. If your experiment applies unusual exposure filtering, check whether the built-in calculator's assumptions still hold before trusting its output.

## Diagnosing Delayed or Ramping Effects: DSE Curves vs. Exploratory Analysis

Two distinct (don't conflate them) newer capabilities help diagnose how an effect evolves over the course of an experiment, useful when a metric looks flat early but you suspect it's still ramping:

- **DSE (days-since-exposure) Curves**: a Surfaces-DS-team-built Streamlit app for visualizing how experiment effects evolve, stabilize, or decay over time by days-since-exposure.
- **Exploratory Analysis**: a built-in C4S platform feature (a feature-flagged, org-wide-enabled section on the experiment results page) for ad-hoc metric calculation beyond your predefined success/guardrail/exploratory metrics.

These are two different tools built by different teams — don't assume one replaced the other.

## Running Underpowered

**Risks:**
- False negatives (miss real effects)
- Inconclusive results
- Wasted engineering effort

**When Acceptable:**
- Exploratory experiments
- Large expected effects
- Time-sensitive decisions

## Duration Estimation

```
Duration = Required Sample / Daily Users in Target
```

Example:
- Need 100K users
- 10K users/day in target
- Duration = 10 days

Add buffer for:
- Weekend/weekday variation
- Holiday effects
- Ramp-up time
