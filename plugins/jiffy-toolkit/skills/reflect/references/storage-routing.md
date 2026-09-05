# Storage Routing

## Decision Tree

Walk top-to-bottom for each learning. A learning can match multiple branches — route
to all matching destinations.

Auto-memory (`~/.claude/projects/<hash>/memory/`) is the canonical persistence layer —
harness-native, always loaded, no MCP round-trip. Infinite Memory is a supplementary
semantic-search store: reserve it for learnings that genuinely apply beyond the current
project (Claude Code/harness behavior, cross-repo tool quirks), where its `scope: "global"`
covers ground auto-memory's per-project file index cannot. Default to auto-memory for
anything project-specific, even for types (bugfix, decision, pattern) that used to route
to Infinite Memory unconditionally.

```
Learning
│
├─ About a PERSON, TEAM, SYSTEM, or their RELATIONSHIP?
│  → Knowledge Graph (add_node + add_edge)
│
├─ USER CORRECTION or PREFERENCE about how to work?
│  → Auto-memory (feedback type). Infinite Memory (correction, scope: global)
│    too, but only if the correction applies beyond this project.
│
├─ BUG FIX or WORKAROUND?
│  → Auto-memory (bugfix type) — the common case, this project only.
│    Infinite Memory (bugfix type, scope: global) only if it's a
│    cross-project Claude Code/tool quirk, not a repo-specific bug.
│
├─ DECISION with rationale (WHY X over Y)?
│  → Auto-memory (decision type) for a project-specific decision.
│  + Knowledge Graph if it's about a system or project
│
├─ TOOL or COMMAND the model gets wrong repeatedly?
│  → CLAUDE.md (global if cross-project, project-level if repo-specific)
│  This goes in CLAUDE.md because it needs to load every session
│
├─ PROJECT TIMELINE, DEADLINE, or OWNERSHIP CONTEXT?
│  → Auto-memory (project type)
│
├─ EXTERNAL REFERENCE (URL, dashboard, Slack channel)?
│  → Auto-memory (reference type)
│
├─ PATTERN or PROCEDURE for internal systems?
│  → Auto-memory (pattern or procedure type) for a project-specific pattern.
│    Infinite Memory (scope: global) only if it applies beyond this project.
│
└─ Everything else → SKIP
```

## Dedup Thresholds

| Store                               | Duplicate (skip)        | Related (flag for user) | Unique   |
| ----------------------------------- | ----------------------- | ----------------------- | -------- |
| Infinite Memory (recall similarity) | >0.85                   | 0.6-0.85                | <0.6     |
| Knowledge Graph (search match)      | Same node, same info    | Same node, new info     | No match |
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

### Knowledge Graph

```
mcp__knowledge-graph__add_node(name, type, properties)
mcp__knowledge-graph__add_edge(source, target, relation)
mcp__knowledge-graph__update_node(name, properties)
```

Common types: `person`, `team`, `system`, `service`, `project`, `decision`, `tool`
Common relations: `owns`, `depends_on`, `member_of`, `decided`, `uses`

### Infinite Memory

Supplementary only — use for `scope: "global"` cross-project learnings (Claude Code
behavior, harness/tool quirks). For a project-specific bugfix/decision/pattern, use
Auto-memory instead; do not default here just because a `type` value matches.

```
mcp__infinite-memory__remember(
  title: "Short descriptive title (max 200 chars)",
  content: "Full learning detail with context",
  type: "bugfix|decision|pattern|procedure|correction|fact|reference|constraint|learning",
  tags: ["relevant", "classification", "tags"],
  scope: "project",
  confidence: 0.85,
  project_path: "/absolute/path/to/project"
)
```

Use `scope: "global"` for learnings that apply across projects (e.g., Claude Code
behavior, global tool usage). Use `scope: "project"` for repo-specific learnings.
