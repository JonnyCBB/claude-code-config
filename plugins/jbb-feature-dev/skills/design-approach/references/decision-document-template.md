# Design Decision Document Template

## File Location

Write the completed document to:

```
~/.claude/thoughts/shared/feature_designs/YYYY-MM-DD-description.md
```

Create the directory `~/.claude/thoughts/shared/feature_designs/` if it does not exist.

---

## Document Template

```markdown
---
date: YYYY-MM-DD
author: Claude jbb-feature-dev design-approach
research_doc: ~/.claude/thoughts/shared/YYYY-MM-DD-research-description.md
requirements_doc: ~/.claude/thoughts/shared/YYYY-MM-DD-requirements-description.md  # or "N/A"
design_method: consensus  # consensus | discussion | user-alternative
status: approved
---

## Design Summary

2-3 sentences describing the chosen approach and the primary reasons it was
selected over the alternatives. Include the core trade-off that made this the
winning option.

---

## Key Decisions

| Decision | Chosen Option | Rationale | Rejected Alternatives |
|----------|--------------|-----------|----------------------|
| Example decision 1 | Option A | Meets performance SLA, lower ops burden | Option B, Option C |
| Example decision 2 | Option X | Aligns with existing platform patterns | Option Y |

---

## Chosen Approach Detail

Paste the selected architect's full output here, or the user's alternative
design if design_method is user-alternative. Preserve all detail so downstream
planning agents have complete context.

---

## Constraints for Downstream Planning

Explicit hard constraints that /create-plan-tdd must respect:

- Constraint 1: e.g., must use existing authentication service, no new auth layer
- Constraint 2: e.g., zero-downtime migration required
- Constraint 3: e.g., backward-compatible API changes only
- Constraint 4: add additional constraints as needed

---

## Rejected Approaches

### Approach A — [Name]

2-3 sentence summary of this approach and why it was rejected. Include the
specific trade-off or risk that made it unsuitable for this context.

### Approach B — [Name]

2-3 sentence summary of this approach and why it was rejected. Note any
scenarios where this approach might be preferred in a different context.

---

## Requirements Deviations

List any deviations from the requirements document, along with the user's
explicit acknowledgment for each:

- Deviation 1: [description] — Acknowledged by user on YYYY-MM-DD
- None (if no deviations)

---

## Next Steps

Run the following command to generate an implementation plan:

\`\`\`
/create-plan-tdd <path-to-this-design-doc> <path-to-research-doc>
\`\`\`
```
