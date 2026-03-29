# Phase 6: Output Storage and Presentation

This file contains the complete workflow for Phase 6 of system-architecture-doc.
Read this file when Phase 6 begins.

## Step 6a: Create Output Directory

```bash
mkdir -p ~/.claude/thoughts/shared/architecture/<system-name>/
```

## Step 6b: Write Output Files

Write output files:
1. `workspace.dsl` — enriched Structurizr DSL model from Phase 4
2. `README.md` — human-readable documentation from Phase 5
3. `inventory.md` — system inventory from Phase 2 (the scope-discovery agent's output)
4. `diagrams/*.puml` — PlantUML C4 source files from Step 4d
5. `diagrams/*.svg` — rendered SVG images from Step 4d

## Step 6c: Present Summary

```
## Architecture Documentation Complete

### Output Files
- `~/.claude/thoughts/shared/architecture/<system-name>/workspace.dsl` — Enriched C4 model
- `~/.claude/thoughts/shared/architecture/<system-name>/README.md` — Human-readable documentation
- `~/.claude/thoughts/shared/architecture/<system-name>/inventory.md` — System inventory

### What Was Discovered
- [N] components documented
- [N] external dependencies mapped
- [N] data stores/pipelines included
- [N] request flows documented

### Validation Summary
- Structurizr CLI: [PASS/FAIL]
- Confirmed elements: [N] / Unverified: [N]
- Confirmed relationships: [N] / Potentially missing: [N]

### Human Follow-Up Tasks
These sections require operational knowledge and should be added manually:
- [ ] **Cross-Cutting Concerns**: auth patterns, observability strategy, error handling
- [ ] **Architecture Decisions**: key ADRs with context, decision, and consequences

Would you like me to drill deeper into any component, add more sequence diagrams, or adjust the scope?
```
