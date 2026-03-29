# Diagram Type Selection

## Visual Aid Decision Criteria

### Quantitative Heuristics
- >2 paragraphs needed to explain concept
- ≥3 entities/systems interact
- ≥3-5 items to compare side-by-side
- >7 sequential steps in a process
- Working memory limit (~7 chunks) exceeded

### Concept Complexity Indicators
- Relationships between multiple entities
- Sequential flows with decision points
- Hierarchical/nested structures
- Spatial relationships (layout matters)
- State changes or transformations
- System architecture or component structure

### When NOT to Recommend Visuals
- When restating text without adding clarity
- When too detailed to be readable (recommend splitting)
- When 3-row table or sentence would suffice
- For purely decorative purposes

## Diagram Type Selection Framework

Use this mapping to select appropriate diagram types:

| Situation | Recommended Visual | Tool |
|-----------|-------------------|------|
| User/system journey | Flowchart or journey map | Mermaid |
| Service interactions over time | Sequence diagram | Mermaid, PlantUML |
| System structure/components | Component diagram | Mermaid, PlantUML, C4 |
| State-dependent behavior | State machine | Mermaid, PlantUML |
| Data model | ER diagram | Mermaid (erDiagram), Erd |
| Eventing/data movement | Event flow, Sankey | Mermaid |
| Deployment/runtime | Deployment diagram | PlantUML, C4 |
| Trade-off comparison | Decision matrix (table) | Markdown table |
| Business process | Flowchart, BPMN | Mermaid, BPMN |
| Object-oriented design | Class diagram | Mermaid, PlantUML |
| Algorithm/logic flow | Flowchart | Mermaid |
| Architecture (multi-level) | C4 Model | C4-PlantUML, Structurizr |
| Network topology | Network diagram | BlockDiag (NwDiag), GraphViz |
| Project timeline | Gantt chart | Mermaid |
| Hierarchical ideas | Mindmap | Mermaid |
