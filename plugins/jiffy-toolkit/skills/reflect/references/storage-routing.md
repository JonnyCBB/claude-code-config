# Storage Routing

## Decision Tree

Walk top-to-bottom for each learning. A learning can match multiple branches — route
to all matching destinations.

Auto-memory (`~/.claude/projects/<encoded-cwd>/memory/`) is the canonical persistence layer:
harness-native, always loaded, no MCP round-trip. It is per-project. A learning that applies
beyond the current project (Claude Code/harness behavior, cross-repo tool quirks) belongs in
the global `~/.claude/CLAUDE.md` instead, because no per-project memory index loads elsewhere.

```
Learning
|
+- About a PERSON, TEAM, SYSTEM, or their RELATIONSHIP?
|  -> Auto-memory (project type for ownership/system facts, user type for the user)
|
+- USER CORRECTION or PREFERENCE about how to work?
|  -> Auto-memory (feedback type). Global CLAUDE.md too, but only if the
|    correction applies beyond this project.
|
+- BUG FIX or WORKAROUND?
|  -> Auto-memory (feedback or project type) - the common case, this project only.
|    Global CLAUDE.md only if it is a cross-project Claude Code/tool quirk,
|    not a repo-specific bug.
|
+- DECISION with rationale (WHY X over Y)?
|  -> Auto-memory (project type)
|
+- TOOL or COMMAND the model gets wrong repeatedly?
|  -> CLAUDE.md (global if cross-project, project-level if repo-specific)
|  This goes in CLAUDE.md because it needs to load every session
|
+- PROJECT TIMELINE, DEADLINE, or OWNERSHIP CONTEXT?
|  -> Auto-memory (project type)
|
+- EXTERNAL REFERENCE (URL, dashboard, Slack channel)?
|  -> Auto-memory (reference type)
|
+- PATTERN or PROCEDURE for internal systems?
|  -> Auto-memory (project type) for a project-specific pattern.
|    Global CLAUDE.md only if it applies beyond this project.
|
+- Everything else -> SKIP
```

## Dedup Thresholds

| Store                               | Duplicate (skip)        | Related (flag for user) | Unique   |
| ----------------------------------- | ----------------------- | ----------------------- | -------- |
| Auto-memory (MEMORY.md grep)        | Description matches     | Similar topic           | No match |
| CLAUDE.md (content grep)            | Overlapping instruction | Related instruction     | No match |

## Storage API Patterns

### Auto-memory

Write a file to `~/.claude/projects/<encoded-cwd>/memory/<slug>.md`:

```markdown
---
name: <kebab-case-slug>
description: <one-line summary — used for relevance matching in future sessions>
metadata:
  type: <user|feedback|project|reference>
---

<content>
```

For `feedback` type, structure the content as:

- Lead with the rule itself
- **Why:** line explaining the reason
- **How to apply:** line explaining when this guidance kicks in

Then add a one-line entry to that project's `MEMORY.md`:
`- [Title](slug.md) — one-line hook`

### CLAUDE.md

Edit `~/.claude/CLAUDE.md` (global) or `.claude/CLAUDE.md` (project-level) to append.
Place the instruction in the most relevant existing section. Format as a concise
instruction (1-3 lines). Include the WHY if non-obvious.
