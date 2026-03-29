# Phase 3: Codebase Exploration

This file contains the complete workflow for Phase 3 of system-architecture-doc.
Read this file when Phase 3 begins.

---

## Step 3a: Domain Detection

**MANDATORY OUTPUT**: Output the completed domain detection table to the user before proceeding to Step 3b.

Scan the Phase 2 `inventory.md` for domain patterns. For each domain, check whether any component in the inventory matches the detection signals:

| Domain           | Detection Signal                        | Expert Agent            | Detected? | Evidence              |
| ---------------- | --------------------------------------- | ----------------------- | --------- | --------------------- |
| ml-training      | ray, TorchTrainer, training config      | ml-training-expert      | ✓/✗       | [component or "none"] |
| experimentation  | experiment, A/B test, feature flag      | experimentation-expert  | ✓/✗       |                       |
| ml-serving       | model serving, feature store, inference | ml-serving-expert       | ✓/✗       |                       |
| event-processing | @produces, @consumes, event handler     | event-processing-expert | ✓/✗       |                       |

**GATE**: Do not proceed to Step 3b until this table has been output to the user.

---

## Step 3b: Agent Type Verification

**MANDATORY OUTPUT**: Output the agent contract to the user before proceeding to Step 3c.

Follow the agent contract pattern from `${CLAUDE_PLUGIN_ROOT}/commands/shared/agent-verification-pattern.md`.
Create the contract using the inventory from Phase 2 and the domain detection from Step 3a:

- **Codebase agents**: One per repo or group of 2-3 related repos
- **Domain specialist agents**: One per detected domain from Step 3a

**GATE**: Do not proceed to Step 3c until this contract has been output to the user.

---

## Step 3c: Pre-Spawn Verification Table

**MANDATORY OUTPUT**: Output the pre-spawn verification table before spawning any agents.

Follow the pre-spawn verification pattern from `${CLAUDE_PLUGIN_ROOT}/commands/shared/agent-verification-pattern.md`.
Every row must show "Yes" or have a concrete reason for skipping (only "repo not accessible"
or "agent type not available" are valid).

**GATE**: Do not proceed to Step 3d until this table has been output to the user.

---

## Step 3d: Spawn Parallel Agents

Launch all agents in **FOREGROUND (blocking) mode**. Do NOT use `run_in_background: true`.
Send all agent calls in a single message to run them in parallel. Wait for all agents to
return results before proceeding to Step 3e.

### Explore Agent Prompt Template

One per repo (or group of 2-3 related repos). Each investigates:

```
Explore the codebase at [repo-path] for architecture documentation.

Investigate and document:
1. Service identity: What is this service? (check README, config files)
2. Technology stack: What frameworks/languages/build tools? (check build files, imports)
3. API surface: What APIs does it expose? (check proto files, OpenAPI, route definitions)
4. Internal architecture: Key packages, main entry points, important classes
5. Storage: What databases, caches, queues does it use? (check config, client code)
6. Request flows: Identify 2-3 main request flows through the service

Return structured findings with file paths for each discovery.
Do NOT suggest improvements — only document what exists.
```

### Domain Specialist Prompt Template

Spawn one agent for each detected domain from Step 3a:

```
Provide [DOMAIN] expertise for architecture documentation:
- Identify [DOMAIN]-specific components and their roles in the system
- Document [DOMAIN] patterns and configurations found
- Highlight [DOMAIN]-specific dependencies and data flows
- Reference [DOMAIN] documentation and configuration files
```

Replace `[DOMAIN]` with the domain name and tailor the prompt to the specific expert agent
listed in the Step 3a detection table.

### Batching Rules

If there are more than 6 repos, batch Explore agents into groups of 2-3 related repos per
agent to avoid overwhelming the system. Group repos by functional similarity (e.g., batch
a service with its shared library, or batch two closely related microservices).

---

## Step 3e: Pre-Synthesis Verification

**MANDATORY OUTPUT**: After all agents complete, output this verification before proceeding to Phase 4.

Follow the pre-synthesis verification pattern from `${CLAUDE_PLUGIN_ROOT}/commands/shared/agent-verification-pattern.md`.

Verify that:

- Every contracted codebase agent returned results
- Every contracted domain specialist agent returned results
- No agent returned empty or error-only output

**GATE**: Do not proceed to Phase 4 until verification is complete and all contracted agents
are accounted for. If any agents failed, note the gap for the final summary.
