# Tension Analysis Guide

This guide defines the 5-category signal taxonomy for detecting design tensions
in research documents. Tensions indicate where multiple valid implementation
approaches exist and where architect perspectives are needed.

## What Is a Design Tension?

A design tension is a point in a research document where the author has
identified that two or more approaches are plausible but has not made a final
commitment. Tensions are not flaws—they are honest signals that design work
remains to be done.

---

## Category A: Explicit Structural Markers

These are sections or elements that the author intentionally placed to surface
unresolved choices.

- **Open Questions sections** — A dedicated heading named "Open Questions",
  "Outstanding Questions", or "Questions for Review" containing items not yet
  resolved.
- **Advisory Notes** — Callouts labeled "Note:", "Caution:", "Warning:", or
  similar that flag caveats requiring a decision.
- **Ranked options tables** — Tables that list two or more implementation
  options with pros/cons columns but no selected winner row.
- **Comparison matrices** — Side-by-side feature grids comparing approaches
  without a final recommendation.
- **Priority matrices with "Requires Design Work"** — Any matrix cell or row
  that explicitly states design work is pending.

---

## Category B: Linguistic Signals

Specific phrases that signal the author is weighing alternatives.

- **"X vs Y"** — Direct comparison phrasing in headings or body text.
- **"could be done via X or Y"** — Explicit enumeration of alternative
  implementation paths.
- **"tradeoff between A and B"** — Explicit acknowledgment of competing
  concerns without resolution.
- **"open question" inline** — The phrase appearing outside a dedicated section,
  embedded in paragraphs.
- **"Partial fix"** — Signals a known limitation with no complete solution yet
  identified.
- **Numbered alternatives** — Lists such as "Option 1 / Option 2 / Option 3"
  without a concluded recommendation.
- **"fundamentally different" context qualifiers** — Phrases like "this is a
  fundamentally different approach" that signal a fork point in design thinking.

---

## Category C: Structural Ambiguity Patterns

Patterns visible in the document's overall shape and argument structure.

- **Competing Findings** — Two findings sections that contradict each other or
  that support different conclusions.
- **Conditional recommendations** — "If X do A; if Y do B" structures where the
  condition is unresolved.
- **Scope boundary debates** — Sections that argue about whether a problem is
  in-scope or out-of-scope without settling it.
- **Untested territory flags** — Statements like "we have not validated this"
  or "this is an assumption" attached to a key design claim.
- **Multi-layer root causes** — Problem analyses that identify more than one
  independent root cause, implying different fixes may be needed.

---

## Category D: Absent-Signal Indicators

Tensions revealed by what is missing rather than what is present.

- **No decisions despite complete research** — A document that has full
  findings but no Decisions or Recommendations section.
- **Open Questions without Resolved counterparts** — An Open Questions section
  exists, but no corresponding Resolved Questions or Decisions section follows.
- **Comparison tables without a recommendation row** — A table compares
  options but the final row ("Recommended" or "Winner") is absent or blank.
- **Gap items without proposed solutions** — A Gaps or Limitations section
  lists problems but provides no path forward for any of them.

---

## Category E: Quantitative Thresholds

Even when individual signals seem minor, their count indicates significant
unresolved tension.

| Threshold                                    | Signal                                        |
| -------------------------------------------- | --------------------------------------------- |
| >= 2 approach-level open questions           | Multiple independent design choices remain    |
| >= 1 comparison table without a clear winner | At least one unresolved structured tradeoff   |
| >= 2 "X vs Y" phrases                        | Repeated either/or framing throughout the doc |
| >= 3 "Partial fix" or gap items              | Substantial known-incomplete coverage         |
| >= 3 Advisory Notes                          | High caution density signaling uncertainty    |

When any single row in this table is satisfied, treat the document as having
meaningful design tension warranting architect perspectives.

---

## Settlement Detection

Before finalizing the tension list, scan for decisions the research has already
made. These are NOT tensions — they are constraints that all architect agents
must respect.

### Category S1: Explicit Exclusions

Statements where the research doc rules something out:

- **"No skill action needed"** or **"not in scope"** or **"out of scope"**
- **"Skip entirely"** or **"delegate to X"**
- **"Automatic"** or **"No action needed"** in a Skill's Relationship or
  Integration column of a table
- **"Not widely used anymore"** or **"legacy"** attached to a feature the
  skill would otherwise implement

### Category S2: Single-Option Conclusions

Sections that evaluate options and land on one answer without leaving it open:

- A recommendation that is NOT listed in Open Questions or Design Exploration
  Recommendation sections
- **"Should use X"**, **"must use X"**, **"recommended: X"** with no
  unresolved caveats or contradicting open question
- Table rows where the Skill's Relationship column gives a definitive
  instruction (e.g., "Monitor via X", "No skill action needed")

### Category S3: Absent From Scope

Features that were never proposed as part of the new skill:

- Items not appearing in any "proposed structure", "proposed actions", or
  "recommended features" section
- Features that appear only in the ecosystem context section as something
  another tool handles, never as something the skill should do

---

## Cross-Reference Rule

For each detected tension, check if ANY settlement signal contradicts it:

- If a tension signal (e.g., an "X vs Y" phrase) is contradicted by a
  settlement signal elsewhere in the same document (e.g., a table row saying
  "No skill action needed" for X), **classify it as a settled decision, not
  a tension**.
- The settlement takes precedence over the tension signal.
- When the same topic appears as both a tension and a settlement in different
  sections, the more specific and concrete statement wins. A table with
  explicit "No action needed" is more specific than a passing "X vs Y"
  mention in a summary list.

**Output format after cross-referencing:**

```
## Settled Decisions (constraints for all architects)
- [Decision]: [What was settled] — Source: [section/line reference]

## Open Tensions (where architects may diverge)
1. [Tension]: [What is unresolved] — Signals: [categories that triggered it]
```

Only the Open Tensions feed into the Perspective Derivation Algorithm below.
The Settled Decisions are passed to architect agents as hard constraints.

---

## Perspective Derivation Algorithm

Use the following procedure to convert detected tensions into named architect
perspectives.

**Step 1: Identify the primary tension axis.**
From the signals found (Categories A–E), determine what the core disagreement
is about. Common axes:

- Scope (narrow fix vs. broad refactor)
- Coupling (tight integration vs. loose abstraction)
- Speed (fast delivery vs. long-term correctness)
- Ownership (centralized vs. distributed)
- Risk (conservative vs. aggressive change)

**Step 2: Polarize the axis.**
Name the two ends of the tension as distinct stances. For example, on a
Scope axis: "Minimal Intervention" vs. "Full Rewrite".

**Step 3: Derive a middle perspective.**
Identify a pragmatic synthesis that takes partial elements from both poles.
Name it to reflect the synthesis: "Incremental Refactor", "Phased Migration",
"Targeted Extension".

**Step 4: Assign each perspective a one-sentence driving principle.**
The principle captures the core value the perspective optimizes for.

**Step 5: Check coverage.**
Ensure the three perspectives together span the full range of plausible
responses to the research document's tensions. If a significant option is
unrepresented, add a fourth perspective.

---

## Fallback Perspectives

When the tension signals are present but the axis is unclear, use these three
default perspectives as starting points and adjust their content to fit the
specific document.

1. **Minimal Changes** — Preserve the existing system shape; fix only what is
   explicitly broken. Optimizes for low disruption and fast delivery.

2. **Clean Architecture** — Take the tension as evidence the current design
   needs structural correction. Optimizes for long-term maintainability and
   correctness.

3. **Pragmatic Balance** — Combine targeted structural improvements with
   short-term fixes. Optimizes for delivering value while reducing future
   debt.

---

## Worked Example

**Document excerpt:**

> We identified two possible indexing strategies: batch re-index on write
> (Option 1) or event-driven incremental updates (Option 2). Both have been
> prototyped. The tradeoff between A and B involves consistency guarantees vs.
> operational complexity. We have not validated latency at production scale.
> Open question: which strategy is acceptable given our SLO targets?

**Signal detection:**

- Category B: "tradeoff between A and B", "Open question" inline, numbered
  alternatives ("Option 1", "Option 2")
- Category C: Untested territory flag ("We have not validated latency at
  production scale")
- Category D: Open question present with no resolution in the excerpt

**Primary tension axis:** Consistency vs. Operational Complexity

**Derived perspectives:**

1. **Consistency-First** — Choose batch re-index (Option 1); accept higher
   operational cost to guarantee read consistency. Driving principle: data
   correctness is non-negotiable.

2. **Operational-First** — Choose event-driven updates (Option 2); accept
   eventual consistency to keep operational complexity low. Driving principle:
   reliability of the pipeline matters more than perfect read consistency.

3. **Hybrid Indexing** — Use event-driven updates for hot paths and scheduled
   batch reconciliation for correctness guarantees. Driving principle: meet
   the SLO without committing to a single strategy prematurely.
