# Decomposition Document Template

Use this template when writing the decomposition document in Step 5 of the break-down-initiative skill.

---

```markdown
---
date: YYYY-MM-DD
type: decomposition
source_document: "[path or URL to the PRD/RFC/epic]"
status: draft
---

# Decomposition: [Initiative Name]

## Source Document

[Link or path to the PRD/RFC/epic that was decomposed]

## Complexity Assessment

- **Total features identified**: N
- **Domains crossed**: [list of domains/bounded contexts]
- **Risk level**: low / medium / high
- **HITL features**: N (requiring human decisions before implementation)
- **AFK features**: N (fully automatable)

## Features

### Feature 1: [Title]

**Description**: [2-3 sentences describing end-to-end behavior, not layer-by-layer]
**Type**: HITL / AFK
**Estimated complexity**: trivial / small / standard
**Blocked by**: None / Feature N
**User stories covered**: [list from source document]

**Acceptance criteria**:

- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

### Feature 2: [Title]

[Same structure as Feature 1]

## Dependency Graph
```

Feature 1 (AFK) ──→ Feature 3 (AFK)
Feature 2 (HITL) ──→ Feature 4 (AFK)
Feature 5 (AFK) (independent)

```

## Execution Order

Recommended order for running features through the pipeline:

1. **Parallel**: Feature 1, Feature 2, Feature 5 (no dependencies)
2. **After Feature 1**: Feature 3
3. **After Feature 2**: Feature 4

Note: HITL features block their dependents until the human decision is made.

## Suggested Next Steps

For each feature:
- Feature 1 [AFK]: `/research-problem "Feature 1 description"`
- Feature 2 [HITL]: Needs human decision on [X] before research
- Feature 3 [AFK]: `/research-problem "Feature 3 description"` (after Feature 1)
```
