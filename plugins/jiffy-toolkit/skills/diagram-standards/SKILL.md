---
name: diagram-standards
description: Diagram standards for technical documentation including type selection, tool recommendations, color palettes (Material Design), WCAG 2.2 accessibility, legend requirements, and colorblind-safe alternatives. Use alongside visual-aid-recommender agent or when creating diagrams for any technical document.
allowed-tools:
  - Read
---

# Diagram Standards

Reference material for creating accessible, consistent, professional diagrams in technical documentation.

## Pattern Categories

- **[Diagram Type Selection](diagram-type-selection.md)**: Concept-to-diagram-type mapping (flowcharts, sequence, ER, C4, etc.)
- **[Tool Recommendations](tool-recommendations.md)**: Tool details with versions, selection criteria, and document-type context
- **[Color Palette](color-palette.md)**: Enhanced Material Design palette, semantic color mapping, Mermaid classDef templates
- **[Accessibility](accessibility.md)**: WCAG 2.2 requirements for captions, alt text, long descriptions, and contrast ratios
- **[Legend Requirements](legend-requirements.md)**: Legend patterns for Mermaid (subgraph, note-based) and markdown tables
- **[Colorblind Palettes](colorblind-palettes.md)**: Okabe-Ito, IBM Design Language, Paul Tol, and monochromatic alternatives

## Quick Reference

### Tool Selection by Document Type

| Document Type | Primary Tool | Reason |
|--------------|-------------|--------|
| TechDocs/Backstage | Mermaid | Native MkDocs Material rendering |
| RFC (Google Docs) | Mermaid, PlantUML, D2 | All work with google-docs skill |
| Tutorial/Blog | Mermaid, D2 | Simple readable syntax |
| Architecture Doc | C4-PlantUML, Structurizr, D2 | Multi-level abstraction |
| Print/PDF | Any (SVG export) | SVG recommended for scalability |

### Semantic Color Quick Lookup

| Component Type | Fill | Stroke | Text |
|---------------|------|--------|------|
| Input/Data Source | #E3F2FD | #0D47A1 | #01579B |
| Processing/Transform | #FFF3E0 | #E65100 | #BF360C |
| Output/Result | #E8F5E9 | #1B5E20 | #1B5E20 |
| Storage/Database | #EDE7F6 | #311B92 | #4A148C |
| External/Infrastructure | #FAFAFA | #212121 | #212121 |
| Security/Critical | #FFEBEE | #B71C1C | #B71C1C |

### WCAG 2.2 Contrast Minimums
- Text on backgrounds: 4.5:1 (7:1 ideal for AAA)
- Graphical objects / UI components: 3:1
- Never rely on color alone - always add text labels, shapes, or patterns

For complete patterns with detailed examples, see the category files above.
