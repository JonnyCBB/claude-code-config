# Severity and Safety Tiers

Reference for the document review pipeline's calibrator agent and edit logic. Defines the four severity levels and two edit safety tiers.

## Severity Rubric

### CRITICAL

Issues that fundamentally break the document's usefulness or create harm.

- Factual errors that mislead the reader
- Broken links that block comprehension (to critical resources)
- Accessibility violations that prevent access (missing alt text on essential diagrams, broken heading hierarchy preventing screen reader navigation)
- Security-sensitive information exposed (credentials, PII, internal URLs in public docs)

Examples: "Section claims the API uses OAuth 1.0 but the linked spec shows OAuth 2.0", "The only installation link returns 404", "Diagram conveys critical architecture but has no alt text"

### MAJOR

Issues that significantly impede reader comprehension or navigation.

- Structural issues impeding navigation (missing table of contents in 20+ page doc, sections in illogical order)
- Undefined acronyms in critical sections
- Misleading or ambiguous statements that could cause incorrect action
- Missing required sections for the document type (RFC without alternatives considered, README without installation)

Examples: "RBAC used 12 times but never defined", "The 'Getting Started' section assumes a step that's only mentioned in the appendix"

### MINOR

Issues that reduce quality but don't block comprehension.

- Grammar and spelling errors
- Inconsistent terminology (same concept called different names)
- Passive voice where active is clearer
- Suboptimal formatting (wall of text, inconsistent list styles)

Examples: "Uses both 'endpoint' and 'route' for the same concept", "'The configuration is loaded by the system' -> 'The system loads the configuration'"

### ENHANCEMENT

Opportunities to improve engagement, clarity, or polish.

- Diagram opportunities (complex explanation would benefit from a visual)
- Engagement improvements (collapsible sections, callout boxes)
- Optional restructuring (splitting long sections, adding summary)
- Style polish (more vivid examples, better headings)

Examples: "This 4-paragraph explanation of the caching layer would benefit from a sequence diagram", "Consider using a `<details>` block for the full error code table"

## Edit Safety Tiers

### Auto-Edit Safe

`auto_edit_safe: true` -- Changes that preserve meaning and don't remove or reorder content.

- Spelling and grammar fixes
- Acronym expansions (inserting the full form on first use)
- Formatting corrections (heading hierarchy, list style consistency)
- Adding alt text to images and diagrams
- Inserting diagram code at identified locations
- Fixing broken links (when correct URL is known)
- Whitespace and punctuation normalization

Classification rule: the edit corrects an objective error or adds information without altering existing content, emphasis, or author intent.

### Recommend Only

`auto_edit_safe: false` -- Changes that could alter meaning, emphasis, or author intent.

- Content removal (cutting paragraphs, sentences, or sections)
- Section reordering (moving content to different locations)
- Paragraph restructuring (splitting, combining, rewriting)
- Simplifying technical terms (could lose precision)
- Combining or splitting sections
- Tone changes (formal to informal or vice versa)
- Replacing examples or analogies

Classification rule: the edit changes, removes, or reorders existing content in a way that could shift meaning, emphasis, or the author's intended framing.
