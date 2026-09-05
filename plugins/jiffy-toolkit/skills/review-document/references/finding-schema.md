# Finding Schema

Inter-agent contract for the document review pipeline. All specialist review agents emit findings in this format; all post-processing agents (calibrator, deduplicator) consume it. This schema replaces the code-review finding schema with adaptations for document-level review: section-based location instead of file paths, document-appropriate severity levels, and category values aligned to the seven specialist review dimensions.

## Schema Definition

```
section_reference: string  — heading path or section identifier
location: string            — paragraph number, line range, or character range within the section
body: string                — markdown-formatted finding description
severity: enum              — CRITICAL | MAJOR | MINOR | ENHANCEMENT
category: enum              — STRUCTURE | PROSE | VISUAL | ACCESSIBILITY | AGENT_READABILITY | ENGAGEMENT | CONSISTENCY
confidence: float           — 0.0 to 1.0
source_agent: string        — name of the agent that produced this finding
suggested_edit: string      — concrete edit text (optional)
rationale: string           — why this is an issue, what standard it violates
auto_edit_safe: boolean     — whether this edit can be auto-applied without user confirmation
```

## Field Descriptions

### section_reference

Heading path or section identifier that locates the finding within the document. Uses the `>` delimiter to express nesting depth. Must match the heading text as it appears in the document.

Constraints:

- Must be non-empty
- Uses `>` to separate heading levels
- Heading text must match the document verbatim (case-sensitive)

Example values:

- `"## Architecture > ### Caching Layer"`
- `"## Introduction"`
- `"## API Design > ### Error Handling > #### Retry Semantics"`

### location

Paragraph number, line range, or character range within the section identified by `section_reference`. Provides sub-section precision for anchoring the finding.

Constraints:

- Must reference content within the identified section
- Use `p` prefix for paragraph numbers, `L` prefix for line ranges, `c` prefix for character ranges

Example values:

- `"p3"` — third paragraph in the section
- `"L12-L18"` — lines 12 through 18 within the section
- `"p1, c45-c72"` — characters 45 through 72 in the first paragraph
- `"table row 2"` — second row of a table in the section

### body

Markdown-formatted finding description. Should be self-contained and readable without requiring other fields for context. Describes what the issue is and its impact on the document.

Constraints:

- Must be non-empty
- Should be self-contained (understandable without other fields)
- Use markdown formatting for emphasis, code references, and structure

Example value:

- `"The acronym **CTP** is used here without prior definition. First occurrence should expand it — readers unfamiliar with the system will lose context."`

### severity

Severity level indicating the urgency and impact of the finding on document quality.

Values:

- `CRITICAL` — factual error, misleading claim, or structural flaw that could cause the reader to make a wrong decision. Must fix before publishing.
- `MAJOR` — significant gap, ambiguity, or inconsistency that materially reduces document effectiveness. Should fix before publishing.
- `MINOR` — quality issue that does not block understanding but degrades the reading experience. Fix when convenient.
- `ENHANCEMENT` — optional improvement that would elevate the document beyond its current quality level. Nice-to-have.

### category

The review dimension this finding belongs to, corresponding to the seven specialist review agents.

Values:

- `STRUCTURE` — document organization, section ordering, logical flow, heading hierarchy, missing sections
- `PROSE` — grammar, spelling, clarity, conciseness, word choice, sentence structure, tone
- `VISUAL` — diagrams, tables, figures, formatting, visual hierarchy, whitespace usage
- `ACCESSIBILITY` — alt text, color contrast, screen reader compatibility, heading levels for navigation, link text quality
- `AGENT_READABILITY` — whether the document is parseable and unambiguous for AI agents consuming it (structured data, explicit cross-references, deterministic instructions)
- `ENGAGEMENT` — reader interest, narrative flow, examples, analogies, callouts, actionability
- `CONSISTENCY` — terminology consistency, formatting uniformity, cross-reference accuracy, style guide adherence

### confidence

Float between 0.0 and 1.0 representing how certain the reviewer is that the finding is a genuine issue. Findings below 0.5 confidence MUST be filtered out before emission.

Constraints:

- Must be between 0.0 and 1.0 inclusive
- Findings below 0.5 must not be emitted

Example values:

- `0.95` — the finding is almost certainly correct (e.g., a misspelled word)
- `0.75` — likely correct but depends on author intent
- `0.55` — plausible issue, borderline

### source_agent

String identifier of the specialist review agent that produced this finding. Used for traceability, deduplication, and pipeline diagnostics.

Constraints:

- Must match the agent's registered name
- One finding, one source agent (no multi-attribution)

Example values:

- `"structure-reviewer"`
- `"prose-quality-reviewer"`
- `"accessibility-reviewer"`
- `"agent-readability-reviewer"`
- `"visual-aid-reviewer"`
- `"engagement-reviewer"`
- `"consistency-checker"`

### suggested_edit

Concrete replacement text or edit instruction that resolves the finding. Optional — omit when the finding is observational or when the fix requires author judgment.

Constraints:

- Must be directly applicable to the text at the identified location
- Should be minimal — change only what is necessary
- Omit rather than provide a vague suggestion

Example values:

- `"Replace \"CTP\" with \"Content Trust Platform (CTP)\""`
- `"Add alt text to the architecture diagram: \"System architecture showing the request flow from API gateway through cache layer to the database\""`

### rationale

Explanation of why this is an issue and what standard, convention, or principle it violates. Helps the author understand the reasoning, not just the symptom.

Constraints:

- Must be non-empty
- Should reference a concrete standard, convention, or principle when applicable
- Should explain impact on the reader, not just state a rule

Example values:

- `"Undefined acronyms violate the plain-language principle — readers must be able to understand the document without prior institutional knowledge."`
- `"Heading levels skipped from H2 to H4, breaking the document outline for screen readers and navigation tools (WCAG 2.1 §1.3.1)."`

### auto_edit_safe

Boolean indicating whether the suggested edit can be auto-applied without requiring user confirmation. Used by the edit-mode pipeline to classify findings into safety tiers.

Constraints:

- `true` only when the edit is mechanical, unambiguous, and cannot change meaning (e.g., fixing a typo, expanding a defined acronym, correcting a heading level)
- `false` when the edit involves subjective judgment, restructuring, or could alter the author's intended meaning
- Must be `false` if `suggested_edit` is omitted or empty

Example values:

- `true` — fixing a spelling error, normalizing whitespace
- `false` — rewriting a paragraph for clarity, restructuring a section

## Contract

- All specialist review agents MUST emit findings in this format
- All post-processing agents (calibrator, deduplicator) MUST consume this format
- This schema is the inter-agent contract that enables the pipeline — deviations will break downstream processing

## Example Finding

```json
{
  "section_reference": "## System Overview > ### Architecture",
  "location": "p2",
  "body": "The acronym **CTP** appears here for the first time without expansion. Readers outside the Content Trust team will not know what this refers to, breaking comprehension for the rest of the section.",
  "severity": "MAJOR",
  "category": "PROSE",
  "confidence": 0.92,
  "source_agent": "prose-quality-reviewer",
  "suggested_edit": "Replace \"CTP\" with \"Content Trust Platform (CTP)\"",
  "rationale": "Undefined acronyms violate the plain-language principle — readers must be able to understand the document without prior institutional knowledge. All acronyms must be expanded on first use.",
  "auto_edit_safe": true
}
```

## Differences from Code-Review Schema

| Code-Review Field                                             | Document-Review Field                                                                         | Change     | Reason                                                                                          |
| ------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------- |
| `file_path`                                                   | `section_reference`                                                                           | Replaced   | Documents have sections and headings, not file paths                                            |
| `position` (diff line number)                                 | `location` (paragraph/line within section)                                                    | Replaced   | Documents are navigated by paragraph and section, not diff hunks                                |
| `suggested_fix`                                               | `suggested_edit`                                                                              | Renamed    | "Edit" is more appropriate than "fix" for document improvements                                 |
| —                                                             | `rationale`                                                                                   | Added      | Document authors need to understand why something is an issue to accept the feedback            |
| —                                                             | `auto_edit_safe`                                                                              | Added      | Supports edit mode's safety tier classification for auto-applying mechanical corrections        |
| `cwe_id`                                                      | —                                                                                             | Removed    | Security-specific field not applicable to document review                                       |
| Severity: 5 levels (ENHANCEMENT, LOW, MEDIUM, HIGH, CRITICAL) | Severity: 4 levels (ENHANCEMENT, MINOR, MAJOR, CRITICAL)                                      | Simplified | LOW mapped to MINOR; MEDIUM/HIGH collapsed to MAJOR — documents need fewer gradations than code |
| Category: BUG, SECURITY, BEST_PRACTICE, STYLE                 | Category: STRUCTURE, PROSE, VISUAL, ACCESSIBILITY, AGENT_READABILITY, ENGAGEMENT, CONSISTENCY | Replaced   | Categories aligned to the seven specialist review dimensions                                    |
