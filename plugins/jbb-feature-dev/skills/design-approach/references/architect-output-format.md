# Architect Output Format

This document defines the required output format for architect agents in the design-approach workflow. Each architect agent MUST produce all 7 sections below.

---

## Required Output Sections

### 1. Approach Name and Summary

Provide a short, memorable name for the approach and a 2-3 sentence summary of the design philosophy. The summary must convey the core architectural principle, the primary trade-off accepted, and why this approach fits the problem space.

### 2. Key Design Decisions

A bullet list of architectural choices specific enough that implementers can act on them without ambiguity. Each bullet must name the decision and the rationale. Avoid vague statements like "use a service layer" — instead state what the service layer does, what it owns, and what it delegates.

### 3. Component Structure

A table with the following columns:

| Component | File Path | Responsibility | Public Interface |
| --------- | --------- | -------------- | ---------------- |

- **Component**: the logical name of the module or class
- **File Path**: concrete path relative to the repo root (e.g. `src/services/foo/bar.py`) — not abstract layer names
- **Responsibility**: one sentence describing what this component owns
- **Public Interface**: the methods, endpoints, or events this component exposes to callers

### 4. Data/Control Flow

Describe the end-to-end flow from entry points through processing steps to outputs. Format as a numbered sequence:

1. Entry point (caller, event, or trigger)
2. Processing step
3. ...
4. Output or side effect

An optional Mermaid diagram may follow the numbered list if the flow is complex.

### 5. Requirements Compliance

> Section tag: `requirements compliance`

A table validating each acceptance criterion against this approach:

| Criterion | Met? | How / Why Not |
| --------- | ---- | ------------- |

- **Criterion**: quote or paraphrase the requirement
- **Met?**: Yes / Partial / No
- **How / Why Not**: concrete explanation of how the approach satisfies or violates the criterion

If no requirements doc was provided, state exactly:

> No requirements doc provided — compliance check skipped.

### 6. Trade-offs

Explicit pros and cons of this approach. Must include at least 2 pros and 2 cons.

**Pros:**

- ...

**Cons:**

- ...

### 7. Risk Assessment

At least 1 risk that could cause the approach to fail or require significant rework. For each risk, name it, describe the likelihood, and state the mitigation.

| Risk | Likelihood | Mitigation |
| ---- | ---------- | ---------- |

---

## Constraints

- Each architect agent must commit to ONE approach — no "it depends" answers or conditional recommendations
- Output must fit within 1-2 pages (approximately 400-800 words of prose, tables excluded)
- Component structure must reference concrete file paths, not abstract layer names
- If the architect's chosen approach violates a stated requirement, they must note this explicitly in the Requirements Compliance table and explain why the trade-off is acceptable

---

## Agent Prompt Template

Use this template when invoking an architect agent. Replace all `{{placeholder}}` values before sending.

```
You are an architect agent. Your job is to design ONE concrete technical approach for the problem below.

## Research Doc
{{research_doc_content}}

## Requirements Doc
{{requirements_doc_content_or_NONE_IF_NOT_PROVIDED}}

## Settled Decisions (DO NOT re-open these)

The research doc has already made the following decisions. Your approach MUST
respect every one of them regardless of your assigned perspective. Do not
propose alternatives to these — they are hard constraints, not design options.

{{settled_decisions_list}}

Your perspective should only influence how you resolve the OPEN TENSIONS
listed in the next section. If your perspective conflicts with a settled
decision, the settled decision wins.

## Open Tensions (your design space)

These are the unresolved questions where your perspective applies. Design
your approach by making concrete choices on each of these:

{{open_tensions_list}}

## Your Assigned Perspective
{{perspective_or_philosophy}}
Examples: "minimise operational complexity", "optimise for query latency", "prefer existing platform primitives"

## Instructions

1. Commit to ONE approach. Do not hedge with "it depends" or present multiple options.
2. Produce all 7 required sections from the architect output format.
3. Keep your total output to 1-2 pages. Tables do not count toward the page limit.
4. Component structure must use concrete file paths, not abstract layer names.
5. If your approach fails to meet a stated requirement, say so explicitly in the Requirements Compliance table.
6. Do not re-open settled decisions. If you find yourself proposing something that contradicts a settled decision, stop and redesign within the constraint.

## Output Format

Follow the architect output format defined in:
~/.claude/plugins/jbb-feature-dev/skills/design-approach/references/architect-output-format.md

Sections required:
1. Approach Name and Summary
2. Key Design Decisions
3. Component Structure (table with file paths)
4. Data/Control Flow
5. Requirements Compliance (table — if no requirements doc, state "No requirements doc provided — compliance check skipped.")
6. Trade-offs (at least 2 pros and 2 cons)
7. Risk Assessment (at least 1 risk)
```
