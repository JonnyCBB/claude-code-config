# Dynamic Team Composition Rules

## How to Use This File

Read this file during Phase 2 (Classify & Compose) of the review workflow.
Use the classification tables to determine the base team, then scan for content
signals to add extended roles.

## Contents

- **Layer 1**: Document Type Classification, Complexity, Base Team by Type
- **Layer 2**: Content Signal Detection, Max Extended Roles, Signal Detection Table
- **Pre-Allocation**: Agent Teams vs Sub-Agent Fallback guidance
- **Output Format**: Classification and composition display template

---

## Layer 1: Document Type Classification

### Document Type

Classify based on document location and content:

| Signal | Type |
|--------|------|
| Located in `research/` directory | research_document |
| Located in `plans/` directory | implementation_plan |
| Contains "Research Question", "Findings", "Evidence" headers | research_document |
| Contains "Phase N:", "Success Criteria", "Changes Required" headers | implementation_plan |
| User specifies type | User's classification takes priority |

If signals conflict (e.g., a plan in a research/ directory), prefer content-based
signals over location. If still ambiguous, ask the user.

### Complexity

| Complexity | Word Count | Sections | Cross-references |
|-----------|-----------|---------|-----------------|
| Simple | <=1500 | <=3 | None |
| Moderate | 1500-3000 | 4-6 | Some |
| Complex | >3000 | >6 | Cross-system deps, multiple open questions |

Count top-level sections (## headers) for the section count. "Cross-references"
means the document references other documents, systems, or codebases that affect
its conclusions.

### Base Team by Type

| Document Type | Core Role 1 | Core Role 2 | Core Role 3 | Core Role 4 |
|--------------|-------------|-------------|-------------|-------------|
| research_document | Synthesis Lead | Critical Analyst | Domain Expert (3a) | Clarity Reviewer (4a) |
| implementation_plan | Synthesis Lead | Critical Analyst | Feasibility Reviewer (3b) | Risk Checker (4b) |

---

## Layer 2: Content Signal Detection

After classifying type and complexity, scan the document for content signals.
Add extended roles up to the maximum allowed by complexity.

### Max Extended Roles by Complexity

| Type + Complexity | Base | Max Extended | Total Max |
|-------------------|------|-------------|-----------|
| Research + Simple | 4 | 1 | 5 |
| Research + Moderate | 4 | 3 | 7 |
| Research + Complex | 4 | 5 | 9 |
| Plan + Simple | 4 | 1 | 5 |
| Plan + Moderate | 4 | 2 | 6 |
| Plan + Complex | 4 | 4 | 8 |

### Signal Detection Table

Scan the document for these signals. Add extended roles in priority order (if
the max is reached, prefer earlier rows):

| Priority | Signal Category | Keywords / Thresholds | Detection Threshold | Role Triggered |
|----------|----------------|----------------------|-------------------|---------------|
| 1 | Security/auth | auth, token, encryption, RBAC, OAuth, credentials, vulnerability, breaking change, irreversible, production | >=2 keyword matches | Risk Assessor (#6) |
| 2 | Large scope | File change count, section count, word count | >10 files OR >8 sections OR >3000 words | Scope Guardian (#7) |
| 3 | User-facing | UI, UX, user experience, API endpoint, public interface, customer-facing | >=1 keyword match | User/Audience Advocate (#8) |
| 4 | Novel approach | new approach, first time, prototype, no precedent | Any match + appears genuinely novel (not incidental use) | Historical Context Specialist (#9) |
| 5 | Strategic | roadmap, long-term, architecture decision, tech debt, migration, strategic | >=2 keyword matches | Visionary / Strategic (#10) |
| 6 | Implementation in research | implementation, build, deploy, phase, timeline (research docs only) | >=3 keyword matches | Feasibility Reviewer (#5) |

**Notes on signal detection:**
- Keyword matching is case-insensitive
- Match whole words only (e.g., "auth" matches "authentication" but not "author")
- For Priority 4 (Novel approach), use judgement — the phrase "new approach" in a
  summary of existing literature doesn't trigger the role; it needs to describe
  the document's own proposal as novel
- Priority 6 only applies to research documents (implementation plans already have
  Feasibility Reviewer as a core role)

---

## Pre-Allocation for Agent Teams vs Sub-Agent Fallback

### Agent Team Path

When creating agent teams, **pre-allocate ALL triggered roles** at creation time.
This is necessary because agent teams cannot spawn new teammates mid-session.

Pre-allocated roles whose concerns don't arise during review should:
1. Read the document
2. Confirm their concern area is not relevant
3. Declare their stand-down message (e.g., "No security/compliance risks identified")
4. Stand down from further deliberation

### Sub-Agent Fallback Path

For the sub-agent fallback, **only spawn triggered roles** (no pre-allocation needed).
Sub-agents are spawned on demand, so roles can be added in later phases if initial
review findings flag uncovered concerns.

---

## Output Format

After classification and composition, present to the user:

```
## Document Classification

- **Type**: {research_document | implementation_plan}
- **Complexity**: {simple | moderate | complex}
- **Word count**: {N words}
- **Sections**: {N top-level sections}

## Team Composition

**Core team** (4 roles):
1. Synthesis Lead — always present (coordinator)
2. Critical Analyst — always present (adversarial)
3. {Domain Expert | Feasibility Reviewer} — {reason for selection}
4. {Clarity Reviewer | Risk Checker} — {reason for selection}

**Extended roles** ({N} of {max} slots used):
5. {Role name} — triggered by: {specific signals found}
6. {Role name} — triggered by: {specific signals found}

**Total team size**: {N}
```
