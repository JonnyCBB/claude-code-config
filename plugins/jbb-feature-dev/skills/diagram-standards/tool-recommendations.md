# Diagram Tool Recommendations

## Primary Tools (recommend these first)

1. **Mermaid** - General purpose, ~23+ types incl. Radar, Treemap, Architecture, Kanban; v11.12.3 (Feb 2025). Easiest syntax
2. **PlantUML** - UML specialist, comprehensive, good for architecture; v1.2026.1 (Jan 2026), new Chart diagram type
3. **D2** - Modern syntax, great for architecture with code snippets. Still v0.x (v0.7.1, Aug 2024), release cadence slowed
4. **GraphViz** - Complex graphs, network topology, dependencies

## Specialized Tools (when appropriate)

- **C4-PlantUML/Structurizr** - Software architecture at multiple abstraction levels; C4-PlantUML v2.13.0 (Jan 2025), new themes and modernized wireframes. Structurizr has added Python support, vNext in development
- **BPMN** - Complex business processes (international standard)
- **Erd** - Simple database ER diagrams
- **Vega-Lite** - Data visualization charts
- **Eraser.io** - DiagramGPT for AI-powered diagram generation from natural language descriptions
- **Diagrams (mingrammer)** - Python cloud infrastructure diagrams (AWS, GCP, Azure, K8s); v0.25.1

## Selection Criteria

- For general diagrams: Prefer Mermaid (easiest, widely supported)
- For UML: Prefer PlantUML (industry standard)
- For architecture: Prefer C4 Model or Mermaid
- For graphs/networks: Prefer GraphViz or BlockDiag
- For databases: Prefer Mermaid erDiagram or Erd tool
- For cloud infrastructure: Consider Diagrams (Python) for programmatic generation
- For AI-assisted diagramming: Consider Eraser.io DiagramGPT

## Document Type Detection and Context-Aware Tool Selection

Detect document type from context and adjust tool recommendations accordingly:

### For TechDocs/Backstage Documentation

- **Strongly prefer Mermaid** (native MkDocs Material support, no export needed)
- Note: "Mermaid recommended - renders natively in TechDocs"
- Fallback to static PNG if Mermaid cannot express the diagram
- Avoid PlantUML unless UML-specific need

### For RFCs (Google Docs)

- **Prefer Mermaid, PlantUML, or D2** (all work well with google-docs skill)
- Note: "Diagram code will be included in the Google Doc"
- Mention compatibility with `${CLAUDE_PLUGIN_ROOT}/skills/google-docs/`

### For Tutorials/Blog Posts

- **Prefer simple, readable syntax** (Mermaid, D2)
- Avoid overly complex tools like full PlantUML syntax
- Note: "Simple syntax makes tutorial easier to follow and modify"

### For Architecture Documentation

- **Prefer C4 Model, PlantUML, or D2**
- Consider multi-level C4 diagrams for progressive disclosure
- Note: "C4 recommended for multi-level architecture views"

### For Print/PDF Documentation

- **Consider SVG vs PNG rendering**
- Note export format considerations
- Mention: "SVG recommended for scalability in print"

### Detection Method

1. Ask user to specify document type if not immediately clear from context
2. Look for clues in document:
   - mkdocs.yml present → TechDocs
   - "RFC:" in title → RFC
   - Tutorial keywords ("Getting Started", "How to") → Tutorial
   - Architecture keywords ("System Design", "Architecture") → Architecture doc
3. Adjust tool recommendations in each recommendation based on detected type
