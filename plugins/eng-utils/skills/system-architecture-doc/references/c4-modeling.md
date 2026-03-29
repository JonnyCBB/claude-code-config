# Phase 4: Architecture Modeling

This file contains the complete workflow for Phase 4 of system-architecture-doc.
Read this file when Phase 4 begins.

## Step 4a: Read the C4 Architecture Skill

Read these files for format decisions and syntax reference:

- `${CLAUDE_PLUGIN_ROOT}/skills/c4-architecture/SKILL.md` — format decisions, level selection, file conventions
- `${CLAUDE_PLUGIN_ROOT}/skills/c4-architecture/references/c4-formats.md` — Structurizr DSL syntax, PlantUML C4 elements, sequence patterns

## Step 4b: Generate the Enriched C4 Model

Use the DSL syntax from `c4-formats.md` to build the Structurizr DSL model. Do NOT duplicate
those references here — read them directly.

**Enrichment** — add properties discovered in Phase 2 and Phase 3:

For each element:

```
properties {
    "owner" "<team-name>"
    "repo" "<repository-url>"
    "tier" "<reliability-tier>"
    "regions" "<deployment-regions>"
}
```

For each relationship (where discovered):

```
container1 -> container2 "description" "protocol" {
    properties {
        "timeout" "<value>"
        "retry_policy" "<value>"
    }
}
```

Add perspectives where relevant:

```
perspectives {
    "Security" "<security notes>"
    "Technical Debt" "<debt notes>"
}
```

**Views to generate**:

- System Context view: `autoLayout lr`
- Container view: `autoLayout tb`
- Component views: max 2, only for containers with complex internals discovered in Phase 3

## Step 4c: Validate the Model

**Do not skip this step.** Validation catches errors before they reach the final documentation.

1. **Structurizr CLI validation**: Run `structurizr-cli validate workspace.dsl` to check DSL syntax. If `structurizr-cli` is not installed, note "Structurizr CLI: NOT AVAILABLE (not installed)" in the summary and proceed with the remaining checks. Do not silently skip the entire validation step.
2. **Dependency cross-check**: Compare model relationships against dependency data from the Phase 2 inventory. If dependency data was not collected in Phase 2, note this gap.
3. **Inventory cross-check**: Compare model elements against `inventory.md` from Phase 2. Every component in the inventory should appear in the model.

```
## Validation Summary

Structurizr CLI: [PASS/FAIL/NOT AVAILABLE]
- [errors if any]

Inventory cross-check:
- Components in inventory: [N]
- Components in model: [N]
- Missing from model: [list, or "none"]

Relationship cross-check against dependency data:
- Confirmed relationships: [N]
- In model but not in dependency data (may be async/infrequent): [list]
- In dependency data but not in model (potentially missing): [list]

Unverified elements (from catalog only, no tracing confirmation): [list]
```

**GATE**: Present the validation summary to the user before proceeding to Step 4d.

## Step 4d: Export and Render PlantUML C4 Diagrams

Export the Structurizr DSL model to PlantUML C4 and render to SVG for embedding in the README.

**1. Export DSL to C4-PlantUML**

```bash
structurizr-cli export -f plantuml/c4plantuml -w workspace.dsl -o diagrams/
```

This produces `.puml` files for each view defined in the workspace.

**2. Render PlantUML to SVG**

```bash
plantuml -tsvg diagrams/*.puml
```

**3. Verify rendering**

```bash
ls diagrams/*.svg
```

If `plantuml` is not installed, note "PlantUML: NOT AVAILABLE (not installed — run `brew install plantuml`)" in the summary and include the `.puml` source files without rendered SVGs.

**4. Optional: Add layout hints**

If the auto-generated layout has issues, edit the `.puml` files to add directional positioning
(`Rel_D()`, `Rel_R()`) or invisible layout hints (`Lay_D()`, `Lay_R()`).
See `c4-formats.md` Section 3 for the full reference. Then re-render: `plantuml -tsvg diagrams/*.puml`

## Step 4e: Generate Companion Sequence Diagrams

For 2-3 key request flows discovered in Phase 3, create Mermaid `sequenceDiagram` blocks:

- Each diagram shows a request flowing across containers from the C4 model
- Use the participant aliases from the C4 model for consistency
- Follow the pattern from `c4-formats.md` Section 4
