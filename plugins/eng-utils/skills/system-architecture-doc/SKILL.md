---
name: system-architecture-doc
description: >
  Create architecture documentation for a system with C4 diagrams and enriched
  Structurizr DSL models. Use when asked to document a system's architecture, produce C4
  diagrams from system names or repos, or create a comprehensive architecture README with
  diagrams and request flow walkthroughs. Trigger phrases include "create architecture
  documentation", "document this system", "generate C4 diagram", "system architecture doc".
  Outputs to ~/.claude/thoughts/shared/architecture/.
---

# System Architecture Documentation

You are an architecture documentation specialist. Your mission: take user input about a system (free text, repo links, screenshots) and produce two primary artifacts — an **enriched Structurizr DSL model** (`workspace.dsl`) and a **human-readable markdown document** (`README.md`) with C4 diagrams, sequence diagrams, and prose walkthroughs.

## Phase Execution Rules

**MANDATORY — read before starting any phase.**

1. **All phases are mandatory.** Do not skip any phase, even if you believe you already have the information it would produce. Each phase exists because it discovers things the previous phases cannot.
2. **Each phase produces a specific artifact.** Do not proceed to the next phase until that artifact has been created and (where specified) presented to the user. The artifact chain is:

   | Phase    | Produces                                             | Required By |
   | -------- | ---------------------------------------------------- | ----------- |
   | Phase 1  | Scope definition (user-confirmed)                    | Phase 2     |
   | Phase 2  | `inventory.md` written to output directory           | Phase 3a    |
   | Phase 3a | Domain detection table (output to user)              | Phase 3b    |
   | Phase 3b | Agent contract table (output to user)                | Phase 3c    |
   | Phase 3c | Pre-spawn verification table (output to user)        | Phase 3d    |
   | Phase 3d | Agent results (all agents completed)                 | Phase 3e    |
   | Phase 3e | Pre-synthesis verification (output to user)          | Phase 4     |
   | Phase 4  | `workspace.dsl` + validation summary + rendered SVGs | Phase 5     |
   | Phase 5  | `README.md`                                          | Phase 6     |

3. **Launch all subagents in FOREGROUND (blocking) mode.** Do NOT use `run_in_background: true`. The next phase always depends on agent results, so blocking is the correct pattern. Attempting to poll or resume running background agents wastes turns and produces errors.
4. **Verification tables must be output to the user.** They are user-visible checkpoints, not internal checklists you can skip. Output them as markdown in your response.
5. **When a phase says "GATE", you must STOP and produce the required artifact before proceeding.** Do not batch multiple phases together or skip ahead.

---

## Initial Setup

When this command is invoked:

**If arguments provided** (e.g., `/system-architecture-doc payment-service`):

- Parse arguments for: system names, GitHub repo links (`github.com/org/...`), local repo paths (`~/projects/...`), file paths (screenshots, docs)
- If a screenshot or file path is given, read it for context
- Proceed to Phase 1 with extracted context

**If no arguments provided**:

- Display:

  ```
  I'll help you create architecture documentation for a system.

  You can provide:
  - A system or service name (e.g., "payment-service", "the order system")
  - A GitHub repository link
  - A local repo path
  - Screenshots of existing diagrams or architecture docs
  - Any combination of the above

  What system would you like to document?
  ```

- Wait for user input before proceeding

---

## Phase 1 — Intent Resolution (Interactive)

**ASSESS**: From the user's input, determine what's already known:

- Which system(s) are being documented?
- Is the scope clear (single service vs full system vs cross-system)?
- Are data pipelines relevant?
- What's the emphasis (architecture overview, request flows, data model)?

**ASK**: Resolve only what the user's input doesn't already answer. Pose 2-4 targeted questions:

```
To create the right architecture documentation, I need to clarify:

1. **Scope boundary**: Are we documenting [single service / the full system / cross-system interactions]?
   → Default: [inferred from input]

2. **Data pipelines**: Should I include data pipelines and data stores, or focus on backend services only?
   → Default: Include if discovered

3. **Emphasis**: What's most important — architecture overview / request flows / data model / all?
   → Default: Architecture overview + key request flows
```

**Output**: A scope definition summarizing:

- System name(s)
- Known repositories
- Scope depth (service / system / cross-system)
- Data pipeline inclusion (yes / no)
- Emphasis areas

**Present the scope definition to the user and ask for confirmation. Do NOT proceed until the user explicitly approves.**

---

## Phase 2 — Scope Discovery (Subagent)

**DO NOT skip this phase even if the user has already provided repository and component information.** The user's list is a starting point, not a complete inventory. The scope-discovery agent explores dependencies and data lineage to discover components and relationships that are NOT visible from the user's initial input — hidden dependencies, shared infrastructure, data pipelines, and services the user may not know about.

Spawn the `scope-discovery` agent in **foreground (blocking) mode** to produce a structured inventory.

**For single-system scope:**

```
Spawn one scope-discovery agent with:
- System name / repo / Backstage URL from Phase 1
- Scope depth from Phase 1
- Whether to include data pipelines
- Any repositories/components the user already provided (as starting points, not a complete list)
```

**For cross-system scope:**

```
Spawn one scope-discovery agent PER system in foreground mode.
Each agent receives its system name and the same scope directives.
Launch all scope-discovery agents in a single parallel batch (multiple Task tool calls in one message), but do NOT use run_in_background.
```

**After all scope-discovery agents complete:**

1. Write the combined inventory to the output directory as `inventory.md`
2. Present the system inventory to the user
3. Ask: "Does this look complete? Any services or dependencies missing?"
4. Wait for user response
5. Incorporate any corrections into `inventory.md` before proceeding

**GATE**: Do not proceed to Phase 3 until `inventory.md` has been written and the user has confirmed the inventory.

**Output**: `inventory.md` written to `~/.claude/thoughts/shared/architecture/<system-name>/inventory.md`.

---

## Phase 3 — Codebase Exploration (Parallel Agents)

Read `references/agent-orchestration.md` for the complete Phase 3 workflow including domain
detection, agent contracts, prompt templates, and orchestration details.

Follow `${CLAUDE_PLUGIN_ROOT}/commands/shared/agent-verification-pattern.md` for the agent contract and
verification table pattern.

**GATE**: Do not proceed to Phase 4 until all agents have completed and the pre-synthesis
verification has been output to the user.

---

## Phase 4 — Architecture Modeling

Read `references/c4-modeling.md` for the complete Phase 4 workflow including enrichment,
validation, PlantUML rendering, and sequence diagram generation.

Read `${CLAUDE_PLUGIN_ROOT}/skills/c4-architecture/SKILL.md` and its references for format decisions,
DSL syntax, and element mapping patterns:

- `${CLAUDE_PLUGIN_ROOT}/skills/c4-architecture/references/c4-formats.md` — Structurizr DSL syntax, PlantUML C4 elements

**GATE**: Present the validation summary to the user before proceeding to Phase 5.

---

## Phase 5 — Human Documentation Generation

Read `references/doc-template.md` for the complete Phase 5 specification including mandatory
sections, conditional sections, and design constraints.

---

## Phase 6 — Output Storage and Presentation

Read `references/output-storage.md` for the complete Phase 6 workflow including directory
structure, file list, and summary presentation template.

---

## Incremental Update Support

When the output directory already exists (`~/.claude/thoughts/shared/architecture/<system-name>/`),
read `references/incremental-updates.md` for the merge strategy and change summary workflow.

---

## Error Handling

Sub-agent-level errors (catalog misses, dependency lookup failures, data lineage failures) are handled internally by the `scope-discovery` agent and `Explore` agents. The command only handles orchestration-level errors:

**Structurizr validation fails:**

1. Show the validation errors to the user
2. Attempt to fix the DSL syntax issues
3. Re-validate once
4. If still failing, present the errors and ask the user how to proceed

**Agent returns empty or failed:**

1. Note in the Pre-Synthesis Verification which agents failed
2. Continue with available data
3. In the final summary, inform the user of gaps:
   ```
   Gaps in documentation due to agent failures:
   - [agent-name] for [repo/domain]: [error/empty result]
   - Impact: [what's missing from the documentation]
   ```

**Repository not accessible (Phase 3 can't explore):**

1. Flag to the user immediately
2. Ask if they can provide an alternative path or if they want to skip this repo
3. Document what's missing in the output README.md:
   ```
   > **Note**: [repo-name] was not accessible during documentation generation.
   > The architecture model may be incomplete for this component.
   ```

---

## Reference Files

- **`references/agent-orchestration.md`** — Read in Phase 3. Domain detection table, agent
  contracts, prompt templates, batching rules.
- **`references/c4-modeling.md`** — Read in Phase 4. Enrichment templates, validation
  procedure, PlantUML rendering pipeline, sequence diagram generation.
- **`references/doc-template.md`** — Read in Phase 5. README section structure, conditional
  sections, design constraints.
- **`references/output-storage.md`** — Read in Phase 6. Output directory structure, file
  list, summary presentation template.
- **`references/incremental-updates.md`** — Read when updating existing architecture docs.
  Merge strategy, change summary template, user confirmation gate.
