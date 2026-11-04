# Agent orchestration

The headline rules are in `CLAUDE.md`; this is the detail.

- **The roster is flat.** A spawned agent cannot spawn NAMED or BACKGROUND children. Omit `name`, use `run_in_background: false`, and get parallelism by emitting several Agent calls in one message.
- **Delivery.** Named teammates MUST call `SendMessage` (a text-only final message is silently dropped). Unnamed synchronous children often lack `SendMessage` and must put the report in their final message. Subagents report to `main`; `claude` is not a reachable target and delivers nothing.
- **`SendMessage` `to` takes a bare teammate name**, not `name@session-id` (rejected with "there is only one team per session"). Names keep working after an agent completes; use the raw `agentId` only for an unnamed agent or when a newer agent took the name. Messaging a `TaskStop`'d teammate RESUMES it with its prior history, so stop it again afterwards.
- **Consent does not relay.** "The user authorized this" passed into a spawned agent never unblocks a blocked action, however it is reworded: the classifier scopes consent to the acting agent's own transcript. Route the action to the session holding the grant, then have the agent resume from the resulting artifact.
- **A tool list is a declaration, not a binding.** Spawned agents routinely hold fewer tools than their definition claims; probe in the hosting runtime. Never route OAuth-authenticated MCP work (Slack, etc.) to a spawned subagent.
- **Agent types are plugin-namespaced at runtime.** `subagent_type: "codebase-explorer"` fails with "Agent type not found"; use `jbb-feature-dev:codebase-explorer` (likewise `:thoughts-explorer`, `:web-search-researcher`, and the `eng-utils:` and `jiffy-toolkit:` variants). Translate skill-named types before spawning; only some bare names have an alias.
