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
| Q1       | web-search-researcher | web-search-researcher | Y |
| Q2       | codebase-explorer          | codebase-explorer | Y |
| ...      | ...                        | ...               | ... |

All rows show Y? Proceed with spawning.
Any row shows N? STOP. Reconcile — update the Research Questions (with explanation) or fix the agent.
```

**CRITICAL**: When writing the `subagent_type` parameter in Task tool calls, COPY the exact agent type string from your Research Questions in Step 2. Do NOT type it from memory or from a downstream summary.

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
  Example: "Combining questions 1 & 2 into codebase-explorer since both involve search-api video detection"

## Direct Question Handling

Questions classified as "Direct" in the Research Execution Plan are resolved in the main
context using grep, glob, or file read — without spawning a sub-agent. See
`references/plan-templates.md` for the full Direct question definition, examples, and rules.

Direct questions do not appear in the Pre-Spawn Verification Table since they don't use agents.

## Model Selection for Sub-Agents

For guidance on choosing sub-agent models (when to use Sonnet vs. the user's default), see
`${CLAUDE_PLUGIN_ROOT}/skills/shared-references/model-selection-guide.md`.

## Default Agent Choice

**Default subagent choice: codebase-explorer** for questions the code can answer; **web-search-researcher** when the answer lives outside the repo.

**Before defaulting, check the question against these routing rules** — historical analysis of 69 research plans showed live-system questions were routinely misrouted to doc-searchers and left unanswered:

| Question needs...                                                                            | Route to                                             |
| -------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Production behavior: metrics, latency/error baselines, SLOs, alerts, incidents, logs, traces | web-search-researcher                     |
| Deployment state: pods, canaries, rollout status                                             | web-search-researcher                     |
| Service topology: who calls whom, service catalog, component ownership                       | web-search-researcher                     |
| Data: warehouse datasets, dataset contents/schemas, lineage, scheduled workflows             | web-search-researcher                     |
| Experiment state: experiment results and exposures                                           | web-search-researcher                     |
| Live Slack thread/channel content                                                            | web-search-researcher (live Slack tools)  |
| GitHub PR/issue/CI state                                                                     | web-search-researcher (gh CLI via Bash)   |
| Docs, indexed Slack search, Drive/RFCs, issue tracker, people/teams                          | web-search-researcher                     |

## Codebase Research Agents

- Use **codebase-explorer** (subagent_type: `"codebase-explorer"`) to find files AND understand how code works in a single pass
- **IMPORTANT**: This is NOT the built-in `Explore` agent type. Always use subagent_type `"codebase-explorer"`, not `"Explore"`.
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

**IMPORTANT**: All agents are documentarians, not critics. They will describe what exists without suggesting improvements.

**Empirical Testing Principle**: When you discover a tool, API, or configuration that is relevant to the research question, attempt to verify it works by calling it with a minimal test input. Report both the existence AND the empirical result. This does not violate the documentarian principle — you are documenting empirical behavior, not evaluating or suggesting improvements.

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

Instruct every research agent: **before listing anything under "areas of low confidence" or
"inconclusive searches", check whether one more tool call, file read, or command would close
it — and if so, run it.** Report the gap only if you attempted it and it failed, or if closing
it needs access you do not have; say which of the two it was.

This matters because a gap listed here flows into the synthesis and, if nobody notices it was
cheap to close, into the finished document's Open Questions. Observed failure: an agent ran
`git log --follow` on a deleted file, reported "last commit was X", and stopped — one more
flag (`--diff-filter=D`) would have named the deletion commit and answered the question
outright. Surfacing a fact _adjacent to_ the answer is not the same as answering.

Two specific habits to avoid:

- Writing "this could be confirmed by [instrument]" instead of using that instrument. If you
  can name what would settle it, you are one step from settling it.
- Grounding an absence claim in an index, cache, or capped listing. Prefer a count or an
  existence check against the live source, and say which you used.

## External Research Agents

**web-search-researcher** -- use for:

- Recommended/approved tools and libraries, and how others solved the same problem
- Relevant Slack discussions -- both the historical index AND live thread/channel reads (prefer live reads when the exact thread matters or the index looks stale)
- Google Docs/Slides/Sheets
- Relevant email threads (Gmail) about decisions or announcements
- Meeting/calendar context
- People/team/ownership facts
- GitHub PR/issue/CI state (gh CLI via Bash)
- Production behavior of named services: metrics, SLOs, alerts, incidents, logs, traces
- Deployment state: pods, canaries, rollout status
- Service topology: production callgraph, service catalog, component ownership
- Data questions: warehouse queries, dataset schemas/contents, lineage, scheduled workflows
- Anything where the honest answer requires querying a live system rather than reading about it
- Discovering whether an MCP server exists that could answer an otherwise-unanswerable question (report-only -- name candidate servers in the findings; do not invoke them)

**When to spawn as primary researcher:**

- The research question explicitly mentions a technology a domain expert covers
- The question asks HOW something works in a domain, not just WHERE code lives
- Domain-specific knowledge would narrow the search or produce richer findings

### Domain Expert as Verifier (Step 7)

When a domain expert matches the research topic, it MUST be spawned in Step 7 as a
**Technical Accuracy Verifier** alongside the generic reviewer personas (for Medium and
Complex research). See `references/review-personas.md` for the verifier persona definition
and prompt template.

**When to spawn as verifier:**

- Medium or Complex complexity AND a domain expert matches the research topic
- The domain expert was NOT used as primary researcher (verification is especially valuable
  when generalist agents produced the findings)
- The domain expert WAS used as primary researcher but findings from OTHER agents touch
  the domain (cross-check between agents)

**When to skip verification:**

- Simple complexity (unless user requests it)
- No domain expert matches the research topic

## Agent Usage Tips

- Start with locator agents to find what exists, then use analyzer agents on promising findings
- Run multiple agents in parallel when they're searching for different things
- Each agent knows its job -- just tell it what you're looking for, don't over-specify HOW to search
- Remind agents they are documenting, not evaluating or improving
