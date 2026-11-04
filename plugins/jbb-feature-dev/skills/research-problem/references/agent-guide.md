# Agent Selection Guide for Step 3: Spawn Sub-Agents

Rules for selecting, verifying, and spawning research sub-agents.
Read this file when Step 3 instructs you to `Read references/agent-guide.md`.

## Pre-Spawn Verification Table

Before making ANY Task tool calls, output a verification table that cross-checks your planned agent types against what you're about to spawn. This prevents agent type substitution errors (e.g., accidentally using the built-in `Explore` when you planned the custom `codebase-explorer`).

**IMPORTANT**: The "Planned Agent" column MUST be copied from the **Research Questions** section (where agents were first named next to each question), NOT from the Agent Type Verification summary. The Research Questions are the source of truth.

```
## Pre-Spawn Verification (Batch N)

| Question | Agent in Research Questions | Agent I Will Spawn | Match? |
|----------|---------------------------|-------------------|--------|
| Q1       | jbb-feature-dev:web-search-researcher | jbb-feature-dev:web-search-researcher | Y |
| Q2       | jbb-feature-dev:codebase-explorer | jbb-feature-dev:codebase-explorer | Y |
| ...      | ...                        | ...               | ... |

All rows show Y? Proceed with spawning.
Any row shows N? STOP. Reconcile — update the Research Questions (with explanation) or fix the agent.
```

**CRITICAL**: When writing the `subagent_type` parameter, COPY the exact agent type string from your Research Questions in Step 2. Do NOT type it from memory or from a downstream summary.

### Agent types are plugin-qualified, and the bare name fails

Every agent named anywhere in this skill is reached as **`jbb-feature-dev:<name>`**. The bare
name is not an alias — it is rejected outright:

```
Agent type 'codebase-explorer' not found. Available agents: ... eng-utils:codebase-explorer,
jiffy-toolkit:codebase-explorer, jbb-feature-dev:codebase-explorer ...
```

Measured against the running binary. Three plugins ship an agent called
`codebase-explorer`, so there is no unambiguous bare form for the runtime to resolve. Write
`jbb-feature-dev:codebase-explorer`, `jbb-feature-dev:web-search-researcher`,
`jbb-feature-dev:thoughts-explorer`, and so on for every agent in this file, including each row of
the Domain Expert Table. A wrong name costs a mid-research respawn, and an executor whose
spawn errors is one nudge away from doing the research itself — which is the failure this
step exists to prevent.

## Batch Execution Rules

- Execute batches in sequence, with parallel spawning within each batch
- For each batch:
  1. Spawn all agents in that batch in parallel
  2. Wait for all agents in the batch to complete
  3. Extract relevant findings to pass as context to the next batch
  4. Call `TaskUpdate` to mark completed agent tasks; call `TaskList` to verify batch status
  5. Proceed to next batch with enriched context

When spawning agents in Batch N+1, include a structured "Batch Summary" in their prompts:

```
## Prior Findings (Batch N Summary)

### Key Findings
- [Concrete finding 1 with file path/URL]
- [Concrete finding 2 with evidence reference]

### Terminology Discovered
- [Term]: [Definition/usage as discovered in this codebase or domain]

### Scope Narrowing
- [What was originally broad is now specific because of finding X]

### Dead Ends
- [Search query that returned nothing useful — do not repeat this search]

Use this context to focus your research more precisely.
```

## Question Combining Rules

You MAY combine multiple related questions into a single subagent IF:

- The questions are closely related and can be answered by the same source/agent type
- It's more efficient than spawning separate agents
- **Tell the user which questions you're combining and why**
  Example: "Combining questions 1 & 2 into codebase-explorer since both involve the same API's request validation"

## Direct Question Handling

Questions classified as "Direct" in the Research Execution Plan are resolved in the main
context using grep, glob, or file read — without spawning a sub-agent. See
`references/plan-templates.md` for the full Direct question definition, examples, and rules.

Direct questions do not appear in the Pre-Spawn Verification Table since they don't use agents.

## Model Selection for Sub-Agents

For guidance on choosing sub-agent models (when to use Sonnet vs. the user's default), see
`${CLAUDE_PLUGIN_ROOT}/skills/shared-references/model-selection-guide.md`.

## Default Agent Choice

**Default subagent choice: codebase-explorer** for questions the code can answer; **web-search-researcher** when the answer lives outside the repo on the public web.

**Before defaulting, check the question against these routing rules** — historical analysis of 69 research plans showed live-system questions were routinely misrouted to doc-searchers and left unanswered:

| Question needs...                                                                            | Route to                                                                                     |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Production behavior: metrics, latency/error baselines, SLOs, alerts, incidents, logs, traces | Main context, using whatever observability tool or MCP server the user has connected; otherwise an Open Question naming the system to query |
| Deployment state, service topology, ownership, dataset contents                              | Main context with the user's connected tools; otherwise an Open Question                     |
| GitHub PR/issue/CI state                                                                     | jbb-feature-dev:codebase-explorer (gh CLI via Bash), or a Direct `gh` call                   |
| Code structure, configuration, schemas checked into a repo                                   | jbb-feature-dev:codebase-explorer                                                            |
| Public docs, library behavior, release notes, prior art                                      | jbb-feature-dev:web-search-researcher                                                        |
| Earlier research, plans, decisions in `~/.claude/thoughts/`                                  | jbb-feature-dev:thoughts-explorer                                                            |

Do not route a live-system question to a doc-searcher and accept "not found" as the answer. If no connected tool can query the system, say so in the document.

## Codebase Research Agents

- Use **codebase-explorer** (subagent_type: `"jbb-feature-dev:codebase-explorer"`) to find files AND understand how code works in a single pass
- **IMPORTANT**: This is NOT the built-in `Explore` agent type, and the bare `"codebase-explorer"` does not resolve. Use `"jbb-feature-dev:codebase-explorer"`.
- Prompt patterns:
  - For locating files: "where is X?" or "find files for X"
  - For understanding implementation: "how does X work?"
  - For finding patterns: "show me examples of X"
  - For both location and analysis: specify both in the same prompt (the agent adapts its depth)
- This replaces the previous two-phase locator->analyzer pattern -- codebase-explorer handles both in one invocation
- Spawn codebase-explorer agents in parallel with other research agents (no sequential dependency required)

## Thoughts Directory Agents

- Use the **thoughts-explorer** agent to find relevant documents AND extract key insights in a single pass
- If the thoughts directory doesn't exist at `~/.claude/thoughts`, create it

## Documentarian Principle

Document by default; permit evidence-backed evaluation when explicitly requested within scope.

**Empirical Testing Principle**: Resolve material questions through authorized, available
reads within budget. Inspect mixed-action tools and commands before executing; do not mutate
records, send messages, connect servers, or change settings. Report exact action, source,
response, available call ID, and limits. Tool registration or help is not end-to-end proof.

## Confidence Signaling

All research agents MUST include a Confidence Assessment section in their output:

```
## Confidence Assessment
- Overall: High/Medium/Low
- Areas of high confidence: [list with evidence references]
- Areas of low confidence: [list with what's missing or uncertain]
- Inconclusive searches: [queries that returned no useful results]
```

This enables the synthesis step to weight findings appropriately and the review phase to
focus on low-confidence areas.

### Close What You Can Before You Report It

Instruct every research agent: before reporting low confidence or inconclusive searches,
check whether authorized, available evidence can close the material gap within budget.
Several safe reads may form one attempt. Report attempts, classified failures, and verified
access, safety, scope, or budget limits. Unfinished material evidence remains incomplete.

This matters because a gap listed here flows into the synthesis and, if nobody notices it was
cheap to close, into the finished document's Open Questions. Observed failure: an agent ran
`git log --follow` on a deleted file, reported "last commit was X", and stopped — one more
flag (`--diff-filter=D`) would have named the deletion commit and answered the question
outright. Surfacing a fact _adjacent to_ the answer is not the same as answering.

Two specific habits to avoid:

- Writing "this could be confirmed by [instrument]" instead of using that instrument. If you
  can name what would settle it, you are one step from settling it.
- Grounding an absence claim in an index, cache, or capped listing. Verify source/query
  coverage through authorized live reads; record the query, scope, result, and missing checks.
  Empty results establish absence only within that coverage.

## External Research Agents

**web-search-researcher** -- use for:

- External documentation and resources
- Recommended tools and libraries, and how others solved the same problem
- Release notes, API references, and anything that may have changed after the training cutoff

For live-system questions (production behavior, deployment state, service topology, datasets),
see the routing table in `## Default Agent Choice`: use the user's connected tools from the main
context, or record the question as open. Do not ask web-search-researcher to answer them.

**LINKS requirement**: Instruct these agents to return links with their findings, and include those links in the final report.

## Domain Expert Table

**IMPORTANT**: Domain experts serve two distinct roles — **primary researcher** (Step 3) and
**technical verifier** (Step 7). Both should be considered when a domain pattern matches.
The Domain Expert Check in Step 2 (`references/plan-templates.md`) determines which role(s)
to use. This section governs spawning behavior.

| Domain Pattern                         | Expert Agent                          | When to Use                                          |
| -------------------------------------- | ------------------------------------- | ---------------------------------------------------- |
| ML training, model code, PyTorch       | jbb-feature-dev:ml-pipeline-reviewer  | ML pipeline, training, and model-code questions      |

Use `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` as the source of truth
for domain detection; this table only summarizes it.

### Domain Expert as Primary Researcher (Step 3)

Use a domain expert instead of codebase-explorer when the question requires domain-specific
knowledge, not just file discovery. For example:

- "Why does validation loss diverge after epoch 3?" → `ml-pipeline-reviewer` (knows training-loop
  pitfalls, data-loader leakage, optimizer settings — will check things a generalist wouldn't think of)
- "Where is the training loop code?" → `codebase-explorer` (pure file discovery)

**When to spawn as primary researcher:**

- The research question explicitly mentions a technology a domain expert covers
- The question asks HOW something works in a domain, not just WHERE code lives
- Domain-specific knowledge would narrow the search or produce richer findings

### Domain Expert as Verifier (Step 7)

When a domain expert matches the research topic, it MUST be spawned in Step 7 as a
**Domain Expert Verifier** alongside the generic reviewer personas (for Medium and
Complex research). See `references/review-personas.md` for the verifier persona definition
and prompt template.

**When to spawn as verifier:**

- Medium or Complex complexity AND a domain expert matches the research topic
- The domain expert was NOT used as primary researcher (verification is especially valuable
  when generalist agents produced the findings)
- The domain expert WAS used as primary researcher but findings from OTHER agents touch
  the domain (cross-check between agents)

**When the verifier is not added** (the generic reviewer personas still run — this governs
only whether the domain expert joins them):

- Simple complexity, unless the user asks for it
- No domain expert matches the research topic

