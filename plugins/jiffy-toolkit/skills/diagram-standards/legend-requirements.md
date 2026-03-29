# Legend Requirements

**Every diagram with 2+ colors/shapes MUST include a legend** explaining what each color and shape represents. This is critical for accessibility and clarity.

## Legend Placement Options

### 1. Mermaid Subgraph Legend (preferred for flowcharts)
```mermaid
subgraph Legend
    direction LR
    L1[Input/Data Source]:::inputClass
    L2[Processing]:::processClass
    L3[Output/Result]:::outputClass
    L4[(Database)]:::storageClass
end
```

### 2. Mermaid Note-based Legend (for sequence diagrams)
```mermaid
Note over Legend: Color Key
Note over Legend: Blue = Input/Request
Note over Legend: Orange = Processing
Note over Legend: Green = Output/Response
```

### 3. Separate Legend Section (when inline legend clutters the diagram)
Include a markdown table immediately after the diagram code:

```markdown
**Legend:**
| Color | Shape | Meaning |
|-------|-------|---------|
| Blue (#E3F2FD) | Rectangle | Input / Data Source |
| Orange (#FFF3E0) | Rectangle | Processing / Transform |
| Green (#E8F5E9) | Rectangle | Output / Result |
| Purple (#EDE7F6) | Cylinder | Database / Storage |
```

## Legend Content Requirements
- List ALL colors used in the diagram with their semantic meaning
- List ALL shapes used if different shapes have different meanings
- Use the same color codes as the diagram for consistency
- Keep legend entries concise (2-4 words per meaning)
- Position legend so it doesn't interfere with the main diagram flow

## Example Complete Diagram with Legend
```mermaid
%%{init: {'theme':'base'}}%%
flowchart TB
    %% Color class definitions
    classDef inputClass fill:#E3F2FD,stroke:#0D47A1,color:#01579B,stroke-width:2px
    classDef processClass fill:#FFF3E0,stroke:#E65100,color:#BF360C,stroke-width:2px
    classDef outputClass fill:#E8F5E9,stroke:#1B5E20,color:#1B5E20,stroke-width:2px
    classDef storageClass fill:#EDE7F6,stroke:#311B92,color:#4A148C,stroke-width:2px

    %% Main diagram
    A[User Request]:::inputClass --> B[Process Data]:::processClass
    B --> C[(Database)]:::storageClass
    C --> D[Response]:::outputClass

    %% Legend
    subgraph Legend
        direction LR
        L1[Input]:::inputClass
        L2[Processing]:::processClass
        L3[Storage]:::storageClass
        L4[Output]:::outputClass
    end
```
