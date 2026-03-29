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
| Q1       | web-search-researcher      | web-search-researcher   | Y |
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
  4. Update TODO list to reflect batch completion
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
  Example: "Combining questions 1 & 2 into codebase-explorer since both involve the same service's request handling"

## Direct Question Handling

Questions classified as "Direct" in the Research Execution Plan are resolved in the main
context using grep, glob, or file read — without spawning a sub-agent. See
`references/plan-templates.md` for the full Direct question definition, examples, and rules.

Direct questions do not appear in the Pre-Spawn Verification Table since they don't use agents.

## Model Selection for Sub-Agents

For guidance on choosing sub-agent models (when to use Sonnet vs. the user's default), see
`${CLAUDE_PLUGIN_ROOT}/commands/shared/model-selection-guide.md`.

## Default Agent Choice

**Default subagent choice: codebase-explorer** (most questions involve understanding the local codebase).

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

## External Research Agents

**web-search-researcher** -- use for:

- External documentation and resources
- When no existing internal solution exists

**LINKS requirement**: Instruct agents to return links with their findings, and include those links in the final report.

## Domain Expert Table

If the research question involves specific technical domains, consider spawning domain experts:

| Domain Pattern             | Expert Agent           | When to Use                        |
| -------------------------- | ---------------------- | ---------------------------------- |
| Experiments, feature flags | experimentation-expert | Experimentation platform questions |

Spawn domain experts when:

- The research question explicitly mentions domain technologies
- Initial codebase research reveals domain-specific patterns
- You need best practices specific to a domain

## Agent Usage Tips

- Start with locator agents to find what exists, then use analyzer agents on promising findings
- Run multiple agents in parallel when they're searching for different things
- Each agent knows its job -- just tell it what you're looking for, don't over-specify HOW to search
- Remind agents they are documenting, not evaluating or improving
