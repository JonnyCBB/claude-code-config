# eng-utils

Engineering utilities for architecture documentation and code pruning.

## Installation

```bash
claude plugins add github.com/JonnyCBB/claude-code-config/plugins/eng-utils
```

## Skills

### Architecture and Maintenance (4 primary)

| Skill                         | Command                          | Description                                                                              |
| ----------------------------- | -------------------------------- | ---------------------------------------------------------------------------------------- |
| improve-codebase-architecture | `/improve-codebase-architecture` | Explore codebase for architectural friction, quantify issues, design alternatives        |
| system-architecture-doc       | `/system-architecture-doc`       | Create C4 architecture documentation with Structurizr DSL models                         |
| c4-architecture               | (loaded by other skills)         | C4 model architecture diagrams for systems                                               |
| prune-code                    | `/prune-code`                    | Delete dead code, redundant tests and stale comments in a commit range or repo, verified |

## Agents (1)

| Agent                       | Purpose                                                                                                   |
| --------------------------- | --------------------------------------------------------------------------------------------------------- |
| codebase-explorer           | Find files and understand code across repos                                                               |

## Prerequisites

This plugin declares no MCP servers. Every agent works from local checkouts with `Read`, `Grep`,
`Glob` and `Bash` (`git`, and `gh` for GitHub repositories you can read).

### CLI Tool Dependencies

| Tool      | Install                       | Used By                                                   |
| --------- | ----------------------------- | --------------------------------------------------------- |
| `git`     | Built-in on macOS             | prune-code                                                |
| `gh`      | `brew install gh`             | codebase-explorer on repos not cloned locally               |
