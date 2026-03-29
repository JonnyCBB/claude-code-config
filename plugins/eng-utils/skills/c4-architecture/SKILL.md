---
name: c4-architecture
description:
  C4 model architecture diagrams for systems. Use when asked to create
  architecture documentation, model a system for agent reasoning, generate C4 diagrams from
  code/config, or plan multi-system refactorings that need architectural context.
allowed-tools:
  - Read
  - Glob
  - Grep
---

# C4 Architecture Skill

Guides agents in creating C4 model architecture diagrams that serve two audiences:
humans reading TechDocs/GitHub and agents reasoning about multi-system changes.

## When to Use This Skill

Invoke when:

- Asked to "create architecture documentation" or "document this system"
- Asked to "generate a C4 diagram" (any level)
- Working on a cross-service refactoring and needing architectural context
- Scanning a codebase to produce a system overview
- Asked "what does this system's architecture look like?"

Do NOT use for:

- Flowcharts, ER diagrams, sequence diagrams standalone (use `diagram-standards/`)
- Code-level class diagrams
- Enterprise/business architecture (ArchiMate territory)

## Format Decision

Two output formats serve different purposes:

| Format              | When to use                                              | Key property                                                        |
| ------------------- | -------------------------------------------------------- | ------------------------------------------------------------------- |
| **Structurizr DSL** | Creating a persistent `workspace.dsl` architecture model | One file captures full model; agents read directly as text          |
| **PlantUML C4**     | TechDocs, architecture docs, RFC sections                | Renders natively in TechDocs; pre-render to SVG for GitHub/markdown |

**Default**: Always create a Structurizr DSL `workspace.dsl` as the primary model — it
defines all levels in one file and provides maximum flexibility. Additionally generate
PlantUML C4 diagrams (rendered to SVG) for any levels the user has clearly indicated, or for
the most relevant level (Container) if not specified. The rendering pipeline is:
`structurizr-cli export -f plantuml/c4plantuml` → `plantuml -tsvg`.
Mermaid is used only for `sequenceDiagram` blocks (request flow diagrams).

## C4 Level Selection

| Task type                                              | Right C4 level     | Diagram type      |
| ------------------------------------------------------ | ------------------ | ----------------- |
| Cross-service refactoring, multi-system API change     | Level 2: Container | `C4Container`     |
| Understanding system boundaries, external dependencies | Level 1: Context   | `C4Context`       |
| Within-service component change                        | Level 3: Component | `C4Component`     |
| Request flow / change propagation across services      | Supplementary      | `sequenceDiagram` |
| Deployment topology (K8s nodes, regions)               | Supplementary      | `C4Deployment`    |

**Avoid Level 4 (Code/C4Code)** — too granular, equivalent to reading source files.

## File Conventions

Architecture docs are stored centrally in:

```
~/.claude/thoughts/shared/architecture/
├── <system-name>/
│   ├── workspace.dsl              # Structurizr DSL model (primary, agent-readable)
│   ├── diagrams/
│   │   ├── structurizr-SystemContext.puml  # C4Context (PlantUML source)
│   │   ├── structurizr-SystemContext.svg   # C4Context (rendered SVG)
│   │   ├── structurizr-Containers.puml    # C4Container (PlantUML source)
│   │   └── structurizr-Containers.svg     # C4Container (rendered SVG)
```

Pass these files as context when starting agent tasks involving multiple services.

## Related Skills

- `diagram-standards/` — Visual quality: colors, WCAG accessibility, legends
- PlantUML C4 uses its own styling via C4-PlantUML stdlib; no custom classDef needed

## Reference Files

- `references/c4-formats.md` — Structurizr DSL syntax + PlantUML C4 element vocabulary + sequence patterns
