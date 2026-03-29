# Decision Record Template

## How to Use This File

Read this file during Phase 6 (Produce Decision Record) of the review workflow.
Copy the template below and fill in all sections. The template combines MADR 4.0
structure, DACI role assignment, Fuchsia-style dissent handling, and an
append-only change audit trail.

Save the completed record to:
`~/.claude/thoughts/shared/decision_records/YYYY-MM-DD-{doc-name}.md`

## Template Sections

- Frontmatter (metadata), Decision, Executive Summary, Team Composition Rationale,
  Key Discussion Points, Dissenting Opinions, Changes Made to Document,
  Decision-Making Principles Applied, Confidence Assessment, Conditions for
  Re-Review, Review Metadata

---

## Template

```markdown
---
document_reviewed: {path to the document}
review_date: {YYYY-MM-DD HH:MM:SS TZ}
team_lead: Synthesis Lead
team_composition:
  core: [Critical Analyst, {Detail Investigator | Feasibility Reviewer}, {Clarity Reviewer | Risk Checker}]
  extended: [{list of extended roles, if any}]
document_type: {research_document | implementation_plan}
complexity: {simple | moderate | complex}
decision: {approved | approved_with_revisions | rejected}
---

# Decision Record: {Document Title}

## Decision

**Verdict**: {Approved | Approved with Revisions | Rejected}
**Date**: {YYYY-MM-DD HH:MM:SS TZ}
**Review Team**: {List of all roles that participated}
**Consensus Method**: {Unanimous | Unanimous minus N | Majority (X of Y)}

## Executive Summary

{2-4 sentences summarising the deliberation outcome, key findings, and rationale
for the decision. Written by Synthesis Lead after discussion concludes.}

## Team Composition Rationale

| Role | Included Because |
|------|-----------------|
| Synthesis Lead | Always present (coordinator) |
| Critical Analyst | Always present (adversarial) |
| {Role N} | {Why this role was triggered — e.g., "Security keywords detected: auth, token, OAuth"} |

## Key Discussion Points

| Topic | Raised By | Positions | Conclusion |
|-------|-----------|-----------|------------|
| {Discussion point 1} | {Role} | {Summary of positions taken by different reviewers} | {How it was resolved} |
| {Discussion point 2} | {Role} | {Positions} | {Resolution} |

## Dissenting Opinions

{If any reviewer disagreed with the final decision, record their position
neutrally here. Per Open Group Handbook and Fuchsia RFC process: record the
specific objection and explain why the decision proceeds despite it.}

- **{Role}**: {Specific objection, recorded neutrally}
  - **Resolution**: {Why the decision proceeds despite this objection}

{If no dissent: "All reviewers reached consensus on the final decision."}

## Changes Made to Document

{ALL changes made to the original document during review, with full audit trail.
This section is mandatory regardless of decision outcome.}

| Change # | Section Modified | Original Text (Summary) | New Text (Summary) | Proposed By | Consensus | Rationale |
|----------|-----------------|------------------------|--------------------|-----------  |-----------|-----------|
| 1 | {Section name} | {What was there before} | {What it was changed to} | {Role} | {Unanimous / Majority / etc.} | {Why the change was made} |

{If no changes were made: "No changes were made to the original document."}

## Decision-Making Principles Applied

{Which principles from the decision-principles skill were invoked during the
review and how they influenced the outcome.}

| Principle | Applied To | How It Influenced the Decision |
|-----------|-----------|-------------------------------|
| {Principle N: Name} | {Which discussion point} | {How it was applied} |

## Confidence Assessment

- **Overall Confidence**: {High | Medium | Low}
- **Basis**: {Consensus strength, evidence quality, reviewer expertise alignment}
- **Caveats**: {Any conditions under which this decision should be revisited}

## Conditions for Re-Review

{Under what circumstances should this document be reviewed again? E.g., "If the
upstream API changes, the feasibility assessment should be revisited."}

{If none: "No conditions for re-review identified."}

## Review Metadata

- **Coordination mechanism**: {Agent team | Sub-agent fallback}
- **Iterations**: {Number of deliberation rounds before consensus}
- **Duration**: {Approximate wall-clock time}
- **Decision-principles skill version**: {Reference to decision-making principles document}
- **Escalations**: {If any points were escalated to the human, document them here. Otherwise: "None."}
```
