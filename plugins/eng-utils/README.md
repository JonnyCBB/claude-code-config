# eng-utils

Engineering utilities for incident investigation, architecture documentation, and service diagnostics.

## Installation

```bash
claude plugins add github.com/JonnyCBB/claude-code-config/plugins/eng-utils
```

## Skills

### Incident & Architecture (7 primary)

| Skill                         | Command                          | Description                                                                             |
| ----------------------------- | -------------------------------- | --------------------------------------------------------------------------------------- |
| assess-incident               | `/assess-incident`               | Quick severity classification (S0-S3) with user/business impact analysis                |
| incident-investigation        | `/incident-investigation`        | Root cause investigation across backend, data pipeline, and indexing domains            |
| monitor-incidents             | `/monitor-incidents`             | Autonomous PagerDuty channel monitoring loop with per-incident investigation            |
| improve-codebase-architecture | `/improve-codebase-architecture` | Explore codebase for architectural friction, quantify issues, design alternatives       |
| system-architecture-doc       | `/system-architecture-doc`       | Create C4 architecture documentation with Structurizr DSL models                        |
| c4-architecture               | (loaded by other skills)         | C4 model architecture diagrams for systems                                      |
| merge-bot-prs                 | `/merge-bot-prs`                 | Merge bot dependency PRs (Renovate, scala-steward, Dependabot) across repos in parallel |

### Service Diagnostics (9 skills)

| Skill                       | Command                        | Description                                             |
| --------------------------- | ------------------------------ | ------------------------------------------------------- |
| diagnose-service-error-logs | `/diagnose-service-error-logs` | Search GKE logs for stack traces and error patterns     |
| diagnose-service-pods       | `/diagnose-service-pods`       | Diagnose pod health (CrashLoopBackOff, OOMKilled, etc.) |
| find-component-changes      | `/find-component-changes`      | Find PRs and commits that impacted a component          |
| diagnose-edge-config        | `/diagnose-edge-config`        | Diagnose edge proxy configuration issues                |
| request-logviewer-access    | `/request-logviewer-access`    | Request temporary PAM access to view service logs       |
| mma-tune-alerts             | `/mma-tune-alerts`             | Review and tune alerts in monitoring-info.yaml          |
| query-service-callgraph     | `/query-service-callgraph`     | Query gRPC service dependencies (callers/callees)       |
| manage-podlinks             | `/manage-podlinks`             | Configure cross-region routing and podlinks             |
| d15a-query-resources        | `/d15a-query-resources`        | Query resource status, lifecycle, and health            |

### Data Pipeline Skills (3, loaded by incident-investigator agent)

| Skill                   | Description                                                          |
| ----------------------- | -------------------------------------------------------------------- |
| data-endpoints          | Schema, data viewing, status, lineage, and PII validation            |

### Proactive Bug Hunting (1 skill)

| Skill                       | Command                        | Description                                                                                                          |
| --------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| bug-hunter-3000 | `/bug-hunter-3000` | Bug investigation over a named component list, a squad, or a system, verified via independent mechanism and intent checks, written to a local portfolio plus an HTML digest |

## Agents (7)

| Agent                       | Purpose                                                                                 |
| --------------------------- | --------------------------------------------------------------------------------------- |
| incident-investigator       | Routes incident investigation across backend, data, and indexing domains                |
| codebase-explorer           | Find files and understand code across repos                                             |
| codebase-explorer             | Discover all components, dependencies, and data pipelines for a system                  |
| bug-hunt-finder             | Investigate one Surfaces component and propose a falsifiable bug hypothesis             |
| bug-hunt-mechanism-verifier | Independently verify a candidate bug via safe local reproduction                        |
| bug-hunt-intent-verifier    | Independently assess whether observed behavior is a bug or intended design              |
| bug-hunt-impact-resolver    | Query the metric a finder cited and return a two-denominator impact figure              |
| bug-hunt-reconciler         | Reconcile mechanism and intent evidence trails into a final disposition for a candidate |

## Prerequisites

### MCP Servers (bundled)



**This plugin is self-sufficient and must stay that way.** It declares every MCP server its
agents use in its own `.claude-plugin/../.mcp.json`, and its agents reference only
`mcp__plugin_eng-utils_*` names. Never repoint them at another plugin's prefix, even when
that other prefix is the one that currently resolves.

**A known runtime caveat, which is a harness issue and not a plugin dependency.** Ten of the
servers this plugin declares are declared at the same URL by `jbb-feature-dev`, and Claude Code
deduplicates MCP servers by URL, registering only whichever plugin loaded first. On a machine
where both are installed and `jbb-feature-dev` loads first, this plugin's `mcp__plugin_eng-utils_*`
names resolve to nothing and its agents fall back to `Read`, `Grep`, `Glob` and `Bash`.
That is a defect in how the two are registered, not a reason to make this plugin depend on the
other. Repointing the names was tried and reverted deliberately: it fixed the co-installed case
by breaking the standalone one, which is the case that matters for anyone else installing this
plugin on its own.

### Org-Managed Connectors (enable in claude.ai settings)

- GDrive MCP

### CLI Tool Dependencies

Some diagnostic skills require CLI tools:

| Tool      | Install                | Used By                                      |
| --------- | ---------------------- | -------------------------------------------- |
| `grpcurl` | `brew install grpcurl` | find-component-changes, diagnose-edge-config |
| `jq`      | `brew install jq`      | diagnose-edge-config                         |
| `gcloud`  | Google Cloud SDK       | request-logviewer-access                     |
| `spt`     | internal CLI   | request-logviewer-access                     |
| `dig`     | Built-in on macOS      | find-component-changes                       |
| `curl`    | Built-in on macOS      | diagnose-edge-config                         |
