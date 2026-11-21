# Agent Selection Guide (Steps 2-3)

## Agent types are plugin-qualified; the bare name fails

Every agent in this skill is reached as `jbb-feature-dev:<name>`. The bare name is rejected:

```
Agent type 'codebase-explorer' not found. Available agents: ... eng-utils:codebase-explorer,
jiffy-toolkit:codebase-explorer, jbb-feature-dev:codebase-explorer ...
```

Three plugins ship a `codebase-explorer`, so no bare form resolves. `jbb-feature-dev:codebase-explorer`
is also not the built-in `Explore` agent. A failed spawn costs a respawn, and an executor whose
spawn errors is one nudge away from doing the research itself.

## Pre-Spawn Verification Table

Before any spawn, copy each question's agent type from **Research Questions** (the source of
truth, not the Agent Type Verification summary) and compare it with what you will spawn:

```
## Pre-Spawn Verification (Batch N)

| Question | Agent in Research Questions | Agent I Will Spawn | Match? |
|----------|-----------------------------|--------------------|--------|
| Q1       | jbb-feature-dev:web-search-researcher | jbb-feature-dev:web-search-researcher | Y |
| Q2       | jbb-feature-dev:codebase-explorer | jbb-feature-dev:codebase-explorer | Y |
```

Any N: stop and reconcile, either by updating Research Questions with the reason or by fixing
the spawn. Direct questions do not appear here.

## Prior Findings between batches

```
## Prior Findings (Batch N Summary)

### Key Findings
- [Concrete finding with file path/URL]

### Terminology Discovered
- [Term]: [usage in this codebase or domain]

### Scope Narrowing
- [What is now specific because of finding X]

### Dead Ends
- [Search that returned nothing useful - do not repeat it]
```

## Routing

Default: `jbb-feature-dev:codebase-explorer` for questions the code can answer, and
`jbb-feature-dev:web-search-researcher` when the answer is on the public web. Check the question
against this table first. Live-system questions used to be routed to doc-searchers and left unanswered.

| Question needs...                                                                            | Route to |
| -------------------------------------------------------------------------------------------- | -------- |
| Production behaviour: metrics, latency/error baselines, SLOs, alerts, incidents, logs, traces | Main context, with whatever observability tool or MCP server the user has connected; otherwise an Open Question naming the system to query |
| Deployment state, service topology, ownership, dataset contents                              | Main context with the user's connected tools; otherwise an Open Question |
| GitHub PR/issue/CI state                                                                     | jbb-feature-dev:codebase-explorer (gh CLI), or a Direct `gh` call |
| Code: where it lives, how it works, examples                                                 | jbb-feature-dev:codebase-explorer |
| Past decisions in `~/.claude/thoughts/`                                                       | jbb-feature-dev:thoughts-explorer |
| Public docs, library behaviour, release notes, prior art                                     | jbb-feature-dev:web-search-researcher |

Do not route a live-system question to a doc-searcher and accept "not found" as the answer. If no
connected tool can query the system, say so in the document.

## What every research prompt asks for

- Document what exists; evaluate only when the user asked.
- Links with every finding (web researchers).
- A Confidence Assessment: overall High/Medium/Low, high- and low-confidence areas with
  evidence, and inconclusive searches with their queries.
- **Close what you can before reporting it as a gap.** Two habits to avoid:
  - Writing "this could be confirmed by [instrument]" instead of using it. An agent ran
    `git log --follow` on a deleted file, reported the last commit, and stopped; one more flag
    (`--diff-filter=D`) would have named the deletion commit and answered the question.
  - Grounding an absence claim in an index, cache or capped listing. An empty result proves
    absence only within the query's coverage; state the query and scope.

## Domain Expert Table

A domain expert can be the primary researcher (Step 3), the verifier (Step 7), or both.

| Domain Pattern                         | Expert Agent |
| -------------------------------------- | ------------ |
| ML training, model code, PyTorch       | jbb-feature-dev:ml-pipeline-reviewer |

**Primary researcher**: use the expert instead of codebase-explorer when the question asks how
something works in the domain, not only where code lives. "Why does validation loss diverge
after epoch 3?" goes to `ml-pipeline-reviewer`; "Where is the training loop?" goes to
`codebase-explorer`.

**Verifier**: add the Domain Expert Verifier at Medium or Complex complexity when an expert
matches the topic, especially when generalist agents produced the domain findings. Do not add
it at Simple (unless the user asks) or when nothing matches.
