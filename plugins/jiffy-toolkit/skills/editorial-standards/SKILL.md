---
name: editorial-standards
description: Editorial standards and technical writing best practices for document review. Covers editorial dimensions (content, style, mechanics, consistency, accessibility), document type-specific standards (RFC, README, Tutorial, API), decision frameworks for when to edit vs. preserve, and authoritative style guide references. Use alongside document-editor-reviewer agent or when reviewing any technical document.
allowed-tools:
  - Read
---

# Editorial Standards

Reference material for technical document editorial review, based on professional editing standards and authoritative style guides.

## Pattern Categories

- **[Editorial Dimensions](editorial-dimensions.md)**: 10 dimensions for evaluating documents (content, style, mechanics, consistency, technical writing, accessibility, document type, formatting, accuracy, clarity)
- **[Document Type Standards](document-type-standards.md)**: Type-specific requirements for RFCs, READMEs, tutorials, and API documentation
- **[Decision Framework](decision-framework.md)**: When to flag issues vs. preserve author intent (Always Flag / Flag with Caution / Preserve)
- **[Special Considerations](special-considerations.md)**: Multi-cultural audiences, technical accuracy, regulatory/compliance
- **[References and Resources](references-and-resources.md)**: Authoritative style guides, technical writing courses, readability research

## Quick Reference

### Style Guide Priority Order

When recommendations conflict, prioritize in this order:
1. **Project-specific style guide** (if mentioned in document or CLAUDE.md)
2. **Document type conventions** (RFC standards, README conventions, etc.)
3. **Accessibility requirements** (Plain Language Act, WCAG 2.2 standards)
4. **Major tech company guides**: Google Developer Docs Style Guide, Microsoft Writing Style Guide, GitLab Documentation Style Guide
5. **Academic standards**: Purdue OWL, UNC Writing Center
6. **Expert judgment** based on clarity and usability

### Reading Pattern Awareness

Technical writers should optimize for these scanning patterns:
| Pattern | Behavior | Optimization |
|---------|----------|--------------|
| F-pattern | Users read first 2 lines fully, then scan left side | Front-load keywords in headings and first sentences |
| Spotted | Users scan for specific keywords/links | Use bold for key terms, descriptive link text |
| Layer-cake | Users read headings only, skip body text | Make headings self-explanatory and information-rich |
| Commitment | Users read everything (rare, high-stakes docs) | Optimize for F-pattern anyway; commitment readers will read regardless |

### Plain Language Quick Rules
- One idea per sentence
- Aim for 8th-12th grade reading level (unless expert audience)
- Active voice unless passive is intentionally formal
- "In order to" -> "to"; "utilize" -> "use"; "prior to" -> "before"
- Front-load the main point (inverted pyramid)

For complete patterns with detailed examples, see the category files above.
