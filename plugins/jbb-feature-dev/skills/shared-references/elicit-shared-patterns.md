# Elicit-Requirements Shared Patterns

Shared patterns used by both `elicit-requirements` and `elicit-requirements-friendly` skills. Edit here, not in either skill.

## Agent Dispatch

Both elicit variants spawn context-gathering agents during their Step 2 ("Context Sprint" / "Autonomous Context Sprint"). The dispatch table maps detected artifacts in the user's input to the appropriate agent.

| Artifact Detected                                                   | Agent to Spawn                                       | Query Focus                                                 |
| ------------------------------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------- |
| Repository name, file path, class/method name                       | codebase-explorer                                    | Architecture, existing patterns, related code               |
| Library / tool / framework name                                     | web-search-researcher + web-search-researcher | What it is, how it's used, docs                  |
| Component / service name                                            | web-search-researcher (lightweight)             | What it does, current health, dependencies, callers/callees |
| Dataset / BigQuery table / pipeline name                            | web-search-researcher (lightweight)             | Schema, contents, ownership, lineage, freshness             |
| Team / squad / person name                                          | web-search-researcher (Band Manager)          | Ownership, membership, whether still active                 |
| GHE PR / issue link                                                 | web-search-researcher (gh CLI)                | PR state, reviews, CI checks, linked discussion             |
| Domain keywords (from `shared-references/domain-agent-registry.md`) | matching domain expert agent                         | Domain-specific context and patterns                        |
| Existing research doc path                                          | thoughts-explorer                                    | Prior research findings                                     |

### Spawning rules

1. Spawn agents in PARALLEL.
2. Each agent gets a focused, narrow query — not open-ended exploration.
3. Wait for all spawned agents to complete before proceeding; correctness, detail, and accuracy take priority over speed.
4. Standard variant: only spawn when artifacts are detected AND relevant to the user's question (the step is OPTIONAL).
   Friendly variant: spawn aggressively — the friendly variant compensates for users who cannot fill technical gaps themselves.

### What NOT to do

- Do NOT replace human questions with agent findings — the point of the skill is to ask things only humans can answer.
- Do NOT dump raw agent output on the user — summarize concisely.
- Do NOT spawn agents for vague/generic input — only when concrete, relevant artifacts exist.

## Mid-Interview Research Triggers

The Context Sprint (Step 2) runs once before the interview. But during the interview, new uncertainty surfaces: the user says "I don't know," a recommendation has no grounding, or an answer opens a new branch ("it depends on whether X supports Y"). When this happens, default to spawning a research agent rather than recording an assumption — research findings frequently reveal additional human-only questions that are vital at the requirements stage.

### When to fire

Spawn mid-interview research when ANY of the following holds:

1. The user explicitly signals uncertainty on a research-answerable question ("I don't know," "not sure," "I'd have to look," "check the code," "I think it's X but verify").
2. The Recommended-answer principle hits empty grounding for a question where research could plausibly produce grounding (i.e., not a human-only dimension).
3. A user answer introduces a new branch in the design tree that an agent could resolve (a conditional, an unknown upstream behavior, a referenced component the agent has no context on).

### What to do

1. Narrate one line before spawning: "I'll spawn `<agent>` to answer `<focused question>` — back in a moment."
2. Spawn the appropriate agent from the dispatch table in `## Agent Dispatch` above. Use a narrow, focused query — not open-ended exploration.
3. Wait for the result. Fold findings into the next Category Preamble using the Context-Sharing Protocol.
4. Generate any follow-up questions the findings reveal before moving on. Do not end the wave until newly-surfaced branches are explored.

Default behavior is announce-and-spawn — do NOT ask the user for permission. The skill's premise is that research-revealed branches matter enough to be worth a few tool calls.

### Guardrails

- **Never spawn for human-only dimensions** — premise challenge, scope mode, motivation, business context, success metrics, acceptance criteria, historical context. These by definition have no research answer.
- **Require a concrete artifact target** — a file path, component name, tool name, codebase region, or domain keyword. Do not spawn on vague signals ("the system feels slow").
- **Cap at ~2 research dispatches per question branch.** If still unresolved after two passes, record as `UNKNOWN_TERM` (or ASSUMPTION in non-interactive mode) and proceed.
- **Non-interactive mode**: this section does not apply (the interview does not run; Context Sprint handles upfront research).

## Suggest Next Step

State the file path and recommend the next command:

```
Requirements saved to: [full path]

Next steps:
- Run `/research-problem [path]` to research the codebase and external context
- Run `/create-plan-tdd [path]` to create an implementation plan directly
- Run `/operational-context [component]` if you need production metrics first
```

The downstream chain (`/research-problem` → `/create-plan-tdd`) is unchanged across both variants — both produce a fully compatible requirements document.
