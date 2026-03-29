# Incremental Update Support

This file contains the workflow for updating existing architecture documentation.
Read this file when the output directory already exists.

## When to Use

When the output directory already exists (`~/.claude/thoughts/shared/architecture/<system-name>/`):

## Merge Workflow

1. **Read existing model**: Read the existing `workspace.dsl`
2. **Compare**: Diff discovered elements against the existing model
3. **Merge strategy**:
   - **Add** new elements and relationships not in existing model
   - **Update** changed properties (owner, tier, regions, etc.)
   - **Preserve** user-added annotations: perspectives, ADR links, custom properties, comments
   - **Flag removals**: If an element exists in the model but was NOT discovered this run, flag it for user confirmation — do NOT auto-delete
4. **Present changes**: Show a summary of what will be added/updated/flagged before writing
5. **Wait for user confirmation** before overwriting files

## Change Summary Template

```
## Incremental Update Summary

### New elements to add:
- [element-name] ([type])
- ...

### Properties to update:
- [element-name]: [property] changed from [old] to [new]
- ...

### Elements no longer discovered (flagged for review):
- [element-name] — not found in this run's discovery. Remove? [Will NOT remove without your confirmation]
- ...

### Preserved annotations:
- [N] perspectives preserved
- [N] custom properties preserved
- [N] comments preserved

Proceed with update?
```
