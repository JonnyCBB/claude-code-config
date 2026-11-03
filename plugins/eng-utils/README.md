# eng-utils

Engineering utilities for architecture documentation, proactive bug hunting, and code pruning.

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

### Proactive Bug Hunting (2 skills)

| Skill                | Command                 | Description                                                                                                                                                                                                                                |
| -------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| bug-hunter-3000      | `/bug-hunter-3000`      | Bug investigation over a named component list, a team's repos, or a system, verified via independent mechanism and intent checks, written to a local portfolio plus an HTML digest                                                       |
| bug-hunter-crossfire | `/bug-hunter-crossfire` | Bugs between two services rather than inside one: reads how every caller of a shared callee handles the failure path and names the one that handles it unlike its peers, written to a local HTML digest with a generated topology diagram |

## Agents (8)

| Agent                       | Purpose                                                                                                   |
| --------------------------- | --------------------------------------------------------------------------------------------------------- |
| codebase-explorer           | Find files and understand code across repos                                                               |
| bug-hunt-finder             | Investigate one slice of one component and propose a falsifiable bug hypothesis                           |
| bug-hunt-mechanism-verifier | Independently verify a candidate bug via safe local reproduction                                          |
| bug-hunt-intent-verifier    | Independently assess whether observed behavior is a bug or intended design                                |
| bug-hunt-impact-resolver    | Turn the impact evidence a finder cited into figures where a local source exists, and account for the rest |
| bug-hunt-reconciler         | Reconcile mechanism and intent evidence trails into a final disposition for a candidate                   |
| bug-hunt-cohort-screener    | Screen the callers of one shared callee to decide which need reading properly; routes, never concludes    |
| bug-hunt-cohort-reader      | Read how every caller of one shared callee handles a degraded path, and state what the population implies |

## Prerequisites

This plugin declares no MCP servers. Every agent works from local checkouts with `Read`, `Grep`,
`Glob` and `Bash` (`git`, and `gh` for GitHub repositories you can read).

### CLI Tool Dependencies

| Tool      | Install                       | Used By                                                   |
| --------- | ----------------------------- | --------------------------------------------------------- |
| `git`     | Built-in on macOS             | all bug-hunt skills, prune-code                           |
| `gh`      | `brew install gh`             | codebase-explorer and bug hunts on repos not cloned locally |
| `python3` | Built-in on macOS             | bug-hunter-3000 and bug-hunter-crossfire scripts          |
