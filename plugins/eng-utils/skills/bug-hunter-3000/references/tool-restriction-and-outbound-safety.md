# Tool restriction and outbound safety

This skill must never create a PR, ticket, Slack message, notification, or page. That guarantee has to come from the runtime not having those tools available, not from instructions telling it to avoid them. This document is the authoritative source for how that is enforced, in three layers, and what residual risk remains after all three are applied.

## 1. Why this needs more than one layer

A skill's `disallowed-tools` frontmatter is turn-scoped: it applies to the turn that invoked the skill and clears once the next message is sent. It does not persist across a whole multi-turn autonomous run.

This skill's workflow is exactly that kind of multi-turn run: it fans out to finder agents, then to two independent verifier agents (mechanism and intent), repeated on a recurring schedule. Every turn after the first would be unprotected by `disallowed-tools` alone. No single mechanism is sufficient; the three layers below cover different scopes and lifetimes and are only safe in combination.

## 2. Layer 1 - SKILL.md frontmatter (disallowed-tools)

Scope: the invoking turn only.

Current inventory of confirmed outbound-capable tools, from direct cross-reference of `.mcp.json`'s registered servers against their tool lists (not assumed from naming):

- `mcp__plugin_eng-utils_atlassian-mcp__create_ticket` - Jira write action
- `mcp__plugin_eng-utils_atlassian-mcp__create_ticket_advanced` - Jira write action
- `mcp__plugin_eng-utils_atlassian-mcp__edit_ticket` - Jira write action
- `mcp__plugin_eng-utils_atlassian-mcp__add_comment` - Jira write action
- `mcp__plugin_eng-utils_oliver__create_reported_incident` - incident/paging-adjacent
- `mcp__plugin_eng-utils_dataplatform__detective_set_anomaly_status` - a mutation, excluded here for parsimony though not squarely a "PR/ticket/Slack/page" action

Every other MCP server registered for this plugin exposes only `get_*` / `list_*` / `query_*` / `search_*`-shaped read tools. This was confirmed by direct tool-list inspection, not assumed from naming.

No Slack MCP server is registered in `eng-utils` today. `jbb-feature-dev`'s `slack-mcp` write/schedule/canvas tools (`slack_send_message`, `slack_send_message_draft`, `slack_schedule_message`, `slack_create_canvas`, `slack_update_canvas`) are listed defensively in this design in case of future co-installation in the same runtime, not because they are currently reachable from `eng-utils`.

**The `disallowed-tools` frontmatter carries BOTH the `jbb-feature-dev` and `eng-utils` prefixed names.** A dead name in a deny list fails open -- the guard protects nothing while reading as though it protects everything. Since MCP prefix resolution can shift between sessions (user-level `~/.claude.json` outranks plugin copies, and stale names can resolve under no prefix or either), denying only the currently-live prefix leaves a hole whenever resolution changes. Denying a name that does not exist costs nothing; failing to deny one that does costs everything. Take the union, not a substitution.

## 3. Layer 2 - custom subagent tool lists (the durable layer)

Scope: every spawn of the subagent, for the life of the run, regardless of turn boundaries.

Each of the four custom subagents this skill spawns declares its own fixed `tools:` list in frontmatter, and that list simply never includes an outbound-capable tool:

- `agents/bug-hunt-finder.md`
- `agents/bug-hunt-mechanism-verifier.md`
- `agents/bug-hunt-intent-verifier.md`
- `agents/bug-hunt-reconciler.md`

Unlike `disallowed-tools`, which resets at the next message boundary, a subagent's own `tools:` list applies every time that subagent is spawned via the Agent tool, for as long as the run continues. The actual investigation work happens inside these subagents, so this is the layer that should be trusted to hold for the whole run, not the skill's own turn-scoped frontmatter.

**This layer only exists if the children really are these four declared types.** Spawning them as `general-purpose` instead -- the usual workaround when registered agent types do not resolve in a given runtime -- inherits **every** tool the session holds, including ticket, Slack and incident creation. Layer 2 then contributes nothing and the zero-outbound guarantee degrades to instruction alone. Measured on seven consecutive runs.

The fallback is sometimes the only way to finish a run at all, so it is not forbidden outright. What must not happen is finishing such a run and describing it as structurally safe. Say prominently in the run summary that the declared types did not resolve and that the boundary was held by prose rather than by tool lists.

## 4. Layer 3 - operator/session-level guidance

Scope: not enforceable by the skill itself; this is guidance for whoever schedules or operates it.

1. Per the live-fetched Workflows docs: "the subagents the workflow spawns always run in `acceptEdits` mode and inherit your tool allowlist, regardless of your session's mode." This means the session's, or the Routine's/loop's, own tool allowlist is the true backstop, and that allowlist should itself deny the Layer 1 tool list as permission-settings deny rules, rather than relying on the skill alone.
2. Whichever scheduling substrate is eventually chosen (Honk, Routines, or `/loop` - explicitly not this plan's decision) should be configured with connectors/MCP servers that do not include write-capable Slack or Jira tools in the first place. A tool that is never registered cannot be called regardless of any allowlist.

## 5. Residual risk

Stated honestly, not as a solved problem: `Bash` access (needed by the finder and mechanism-verifier subagents for code search and live local reproduction) is not itself an outbound-capable named tool. But a sufficiently capable shell could in principle reach an external endpoint directly (for example, `curl` to a webhook URL) if one were reachable from the execution environment.

The layered restriction in sections 2 through 4 closes every named-MCP-tool path completely. It does not close a raw-network-egress path. That would require sandboxing or network policy outside this plan's scope. This is a known, disclosed limitation, consistent with the requirements doc's own framing of this skill as a pilot, not a hardened production control.

## 6. The digest, `open`, and why the zero-outbound guarantee is untouched by it

A run writes one HTML digest and, unless the caller passed `no-open`, opens it in a browser. Neither
step is an outbound action, and the distinction is worth writing down because "opens a browser" reads
like one.

**The write is local.** The digest goes through `scripts/write_artifact.py` to a local path, exactly
as every per-candidate portfolio file does, with the run id as its sentinel. Nothing about the digest
bypasses the gate in section 5 of `SKILL.md`.

**`open <file>` is a local process invocation, not a network write.** It hands a path to the
operating system's default handler. It creates nothing, comments on nothing, assigns nothing and
notifies nobody, which is the whole of what the zero-outbound rule prohibits.

**Publishing stays a human step, and that is a structural choice rather than an omission.** The
digest is deliberately a single self-contained file so a human can publish it by dropping one file
somewhere. Adding a publish tool to the orchestrator would move the guarantee out of the Layer 2 durable
tool-list guarantee and into the Layer 3 prose layer that section 4 already identifies as the weakest
of the three. **Do not add one.**

**One disclosed wrinkle, in the same spirit as the BuildBuddy exception.** The digest's stylesheet
links three webfonts from `fonts.googleapis.com`. Opening the file therefore makes a network request.
This does not breach the rule: the skill writes a local file and the _browser_ fetches the font when a
human opens it -- the browser is acting, not the skill. Two consequences are recorded rather than
left to be discovered: a digest opened offline or on a host without egress falls back to system
fonts, and opening one is not a zero-network event. A guarantee with an undisclosed hole is worse
than a narrower guarantee stated plainly.

## 7. Why `disable-model-invocation` is deliberately unset

Per the Claude Code Skills docs this field is exactly what is recommended for a
side-effecting workflow like this one -- but as of Claude Code v2.1.196 it **also
blocks a scheduled-task prompt from executing the skill at all** (such fires reach
Claude as plain text instead of executing). Since this skill's entire purpose is to
be recurring and schedulable, leaving it unset is the correct choice. **Do not add
it to `SKILL.md`'s frontmatter** -- its absence is deliberate, not an oversight, and
adding it silently disables every scheduled fire.

The resulting risk of an unwanted mid-conversation auto-trigger is mitigated by the
description's specificity and by this skill expecting explicit scope and budget
arguments a casual mention would not supply. **The new name must therefore not be
casually matchable** -- that specificity is the only trigger guard.

This reasoning lives here rather than in `SKILL.md`'s frontmatter because the
frontmatter is read by the platform, not just by humans, and should not carry
explanatory prose.

## Maintenance note

The Layer 1 list in section 2 is only correct as long as it matches `SKILL.md`'s `disallowed-tools` frontmatter exactly. Re-check both together whenever either changes, and whenever a new MCP server is added to `eng-utils/.mcp.json` or an existing server gains a new mutating tool.
