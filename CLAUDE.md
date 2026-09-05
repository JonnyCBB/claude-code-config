# Global instructions

This file is a table of contents. Detail lives in `~/.claude/docs/` and is loaded on demand. Apply the always-on rules below to every task; consult the linked docs when their triggers fire.

## Always-on rules

### Formatting

Use integer-only numbering for steps, phases, and sections (1, 2, 3 — never 5.5 or 2.1).

Never use non-ASCII characters (em-dashes, smart quotes, etc.) in YAML comments. Some infra validators reject them outright with no inline PR annotation, only a build failure. Use plain ASCII punctuation (hyphens, straight quotes) in any YAML file comment.

The `security-block` Write hook rejects any file path containing the substring `credentials`, including legitimate memory files (it blocked `credentials-absent-is-not-credentials-broken.md`). Rename around the substring. Relatedly, add a `MEMORY.md` pointer only _after_ confirming the paired file write succeeded — indexing first leaves a dangling pointer when the write is blocked.

### Debugging

Reproduce before theorizing. Write a concrete test or repro script first; verify hypotheses against real behavior rather than speculating.

### Verification

Run against local services, not deployed/production. Include verbatim log output or response snippets as proof — no "it should work" claims.

Never present an unverified claim as settled. Label a suggestion as a hypothesis, state what would falsify it, and cite only primary sources you actually opened. This applies to causal claims (root causes) and factual ones (APIs, ownership, docs) alike.

Never ground an absence claim in an index, cache, or capped listing. Search-index file listings truncate silently (observed: 200 of 635 files returned while the response still reported `"limited": false`) — use a count/existence query rather than eyeballing a listing, and corroborate every negative against the live source system.

### Unattended work: recorded is not delivered

A scheduled job, hook or background agent has no reader, so writing a failure to its own log, to
`/tmp`, or to launchd's `last exit code` is not failing loudly - it is failing silently into a file
nobody opens. Before shipping anything unattended, name two things: **where a failure surfaces, and
who opens that place.** If you cannot name the reader it is not reported, and the job has to escalate
somewhere that is - a bead, the conductor, or the report of a job someone already opens.

**Definite and ambiguous failures want opposite handling.** A definite one (the target does not
exist, the config will not parse) is proof something is wrong regardless of side effects: escalate on
the first occurrence. An ambiguous one (a send returned non-zero but may have arrived) must not
escalate at all, or the escalation becomes noise and stops being read. Bucketing them together is
what let an unattended on-call sweep retry into a dead target for an hour on 2026-08-21, under a note reading
"rejection does not prove non-delivery" - true of the ambiguous case, false of the one it was hitting.

Also read the whole status column of any registry you consult for your own entries, and report a
failure that is not yours. The launchd sweep, and why it belongs at conductor startup, is section 8
of [conductor operations](docs/conductor-operations.md).

### Prove it works

Verify against the real artifact, never a proxy. "It compiles", a green suite, an mtime, or a
subagent's own summary are not evidence — run it and exercise the actual path. When verification
fails, suspect the observation method before the system. For delegated work read the artifact (diff,
file, runtime behaviour), not the report: agents report what they intended, not what happened.
Prefer a script a reviewer can re-run over a one-time eyeball; keep it as the evidence.

### Decisions and questions

Put every open decision to the user through `AskUserQuestion`, with the options, their tradeoffs, and your explicit recommendation marked as one of the options. Never a prose list of ambiguities, never a bare "pending your call".

**Exception — unattended runs (conductor, scheduled job, overnight `/loop`).** With nobody at the
keyboard a question is not a decision deferred, it is the work stopping. The gate becomes **effect,
not difficulty**: reversible effect → proceed and present afterwards. Escalate only the
irreversible, real-traffic exposure, spend, messaging a person, or a genuine product call — and even
then park that one item and continue with the rest. Interactive sessions are unchanged. Conductor
version: [conductor heartbeat rules](docs/conductor-heartbeat-rules.md).

### Writing to a person who has to act on it: the objective goes first, in plain words

Open with what you want to be true afterwards, not the change you want the reader to make, then
name only what they need in order to act: if they would have to look it up and the sentence works
without it, cut it. Do not add asks, and never delete one they wrote. Never infer an objective they
did not state: leading with a goal they did not set is a fabrication. This does not ban saying what
you did not verify, bounding your own evidence, naming a scope limit, or the options in a decision
message.

**Position alone is not the fix.** Measured 2026-08-28: an identifier-dense Slack request drew _"can
you explain in human language what you need and what you're trying to achieve?"_ despite already
carrying a bolded "What we're trying to do" second paragraph. It named a mechanism where the
rewrite that worked named an outcome. Worked before/after: `/jiffy-toolkit:sound-like-me`.

**This applies to Jonny too, but only the opening does.** Everything after it is governed by
[the communication contract](docs/conductor-communication-contract.md), and that file wins: its
sections 1 and 6 say identifiers, narration and report items are never dropped for him.

### Follow-up capture (always, mid-work, without pausing)

The moment you notice something you will not fix on this branch — a bug, a stale doc, a missing
test, a decision someone must make — **file it immediately and carry on**. Do not wait for the end
of the session, do not ask permission first, do not hold it in your head. The failure mode this
prevents is real and measured: work that exists only in chat scrollback is lost when the session is.

```bash
TITLE=$(cat <<'BD_TITLE'
<what you noticed - verbatim, any characters>
BD_TITLE
)
ID=$(bd create "$TITLE" -p <0-4> -l agent-proposed \
  --deps discovered-from:<current-id> --silent)
[ -n "$ID" ] || { echo "bd create failed - follow-up NOT filed"; exit 1; }
bd update "$ID" -s deferred
```

**Run that as one shell invocation.** `$ID` does not survive between tool calls, and
`bd update "" -s deferred` prints an error and then **exits 0** — so splitting it looks like
success while leaving the bead `open`.

**The heredoc is not ceremony.** A title goes straight into a shell command, and it routinely
quotes someone else's words. Written inline it is interpolated, so backticks and `$(...)` in it
RUN: a title reading ``the `bd ready` query misses deferred beads`` executed `bd ready` and filed
the bead with its output spliced into the title, at exit 0. `<<'BD_TITLE'` (quoted delimiter)
turns off every expansion, and `"$TITLE"` is not re-expanded once assigned.

**`-l agent-proposed` and the `bd update -s deferred` that follows it are not optional.** Once
both have run, the item stays out of `bd ready` until Jonny confirms it, so nothing you propose
gets picked up or dispatched by accident. Anything **he** files carries no such flags and is live
immediately.

**Run the second command. Do not stop between them.** `bd create` has no status flag on bd 1.2.2,
so the bead is briefly `open` and dispatchable until `bd update -s deferred` lands — and if that
never runs, it stays that way. Closing that window for good is `jbrooksbartlett-l7qs`.

Three rules that are easy to get wrong:

1. **On a child item (`--parent`), pass `-l agent-proposed` and run the `bd update -s deferred`
   step EXPLICITLY.** Beads inherits labels parent-to-child but **not status**, so a child of a
   confirmed parent would otherwise default to `open` and land in `bd ready` having never been
   triaged.
2. **Confirmation is a status transition (`deferred` → `open`), never a `confirmed` label.** A
   label would be inherited by children nobody has looked at.
3. **Rescue ephemeral evidence before it dies.** If the proof lives in `/private/tmp`, a session
   scratchpad, or only in your context, copy it somewhere durable outside any git-pushed directory
   and record the absolute path on the bead. Durable evidence — git paths, PR numbers, merged
   commits — is referenced, never copied.

**The bar for the description:** a stranger opening it later must be able to understand and
reproduce the problem without asking Jonny anything. Include the fact you learned at cost, and any
trap that would mislead someone who has not done the digging. "Re-phase the injectors" is not
delegatable; the same line plus the file path, the gate name and how to verify is.

Over-capture is cheap. Under-capture is the failure mode.

### Agent orchestration

A spawned agent cannot spawn NAMED or BACKGROUND children — the team roster is flat. Omit `name` and use `run_in_background: false`; get parallelism by emitting several Agent calls in one message. Named teammates MUST call `SendMessage` to deliver results (a text-only final message is silently dropped); unnamed synchronous children often have no `SendMessage` tool and must put the report in their final message.

Relaying "the user authorized this" into a spawned agent NEVER unblocks a blocked action — the permission classifier scopes consent to the acting agent's own transcript, and retrying or rewording the relay never flips it. Route the action to the session holding the user's own grant, then have the agent resume from the resulting artifact.

An agent definition's tool list is a declaration, not a binding: spawned agents routinely hold fewer tools than their definition claims. Probe the tools in the runtime that will host the work, and never route OAuth-authenticated MCP work (Slack, etc.) to a spawned subagent.

`SendMessage`'s `to` takes a **bare teammate name**. The composite `name@session-id` form is rejected (`to must be a bare teammate name -- there is only one team per session`), and some skill docs still tell you to use it. Names keep working after an agent completes; use the raw `agentId` only for an unnamed agent or when a newer agent has taken the name.

Two `SendMessage` targets behave surprisingly. Messaging a teammate you already `TaskStop`'d does not no-op — it **resumes** it as a live in-process agent with its full prior history ("was not running; resumed it as an in-process teammate with N prior messages"), so retiring an agent and then messaging it un-retires it; stop it again afterwards. And `claude` is NOT a reachable target — a background subagent told to report to `claude` delivers nothing, while `main` works. Instruct subagents to report to `main`.

Agent types are plugin-namespaced at runtime even where skill docs name them bare. `subagent_type: "codebase-explorer"` fails outright with "Agent type not found"; use `jbb-feature-dev:codebase-explorer` (likewise `jbb-feature-dev:thoughts-explorer`, `:python-expert`, `:typescript-expert`, and the `eng-utils:`/`jiffy-toolkit:` variants). Translate skill-named types to the namespaced form before spawning — only some names have a bare alias, and a wrong one costs a mid-pipeline respawn.

### Git hosting

A `gh` CLI authenticated against the wrong host 404s indistinguishably from "this path does not exist". If a lookup you expect to succeed 404s, check `gh auth status` before concluding the path is missing, and force the host explicitly when in doubt: `gh api --hostname github.com ...` or `GH_HOST=github.com gh ...`.

`git worktree add -b <branch> <path> origin/master` and `git checkout -b <branch> origin/master` both set the new branch's upstream to `origin/master` — a bare `git push` then pushes feature commits straight to master. Run `git branch --unset-upstream` immediately after creating such a branch (a later bare push then fails safely with "no upstream configured"), and always push with an explicit refspec.

### TDD scope

Apply Red-Green-Refactor TDD only to code behavior files (source code, tests, configuration that affects runtime behavior). Do NOT write tests for documentation files (markdown, READMEs, workflow templates) unless the user explicitly requests it. This applies to `/create-plan-tdd`, `/orchestrate-feature-dev`, `/implement-plan-tdd`, and any workflow that uses TDD methodology.

**A markdown file that EXECUTES is not documentation. Narrowed 2026-08-19, on measurement.**
"Skill definitions" was previously exempt outright. Split it:

- A skill file that DESCRIBES behaviour - explains, instructs, gives context - stays exempt. Writing
  tests against instruction prose is the low-value pattern this rule exists to prevent.
- A skill file that **shells out, templates a string into a command, or defines a data format another
  step parses** is a program written in prose. It gets tested like code.

**Why, measured 2026-08-19 on an on-call triage skill:** an independent review found three
CRITICAL/HIGH defects and **all three were in `SKILL.md`, none in the 215 lines of tested Python** -
which five reviewers found correct. The three: a `bd` command using a flag that does not exist, so
every run would fail silently at the step that files the result; a queue-key prefix collision that
silently drops a real request; and a heredoc delimiter collision that **executes shell from a
colleague's pasted message text**. The implementer's own conclusion: _"I drew the tested/untested line
in the wrong place, and I drew it before the review rather than after."_

It happened three times the same day - the dedup check, the bead-filing command and the body
templating were each "just orchestration" until someone looked. **The dangerous code is reliably the
code nobody classified as code.**

**The operational test:** could a wrong character in this file cause a command to fail, run the wrong
thing, or run something an outsider supplied? If yes, it is code.

### Skill compliance

Follow a skill's mandatory steps even when prior context appears to subsume them. **Auto mode only suppresses tool-use permission prompts. It does NOT skip:**

- Mandatory steps (e.g., spawning sub-agents — that is action, not planning, and "input research seems thorough" is not a valid justification)
- Interactive gates that ask the user a question (e.g., `AskUserQuestion` checkpoints in skills like `create-plan-tdd` at the wave-structure and plan-outline gates) — auto mode does not authorize the model to make those design decisions on the user's behalf
- Multi-pass review loops where reviewer feedback is normally surfaced to the user

A skill behaves identically in auto mode and normal mode unless it has an explicit `--non-interactive` flag. If you skip any mandatory step or gate, state the justification to the user _before_ proceeding, not after.

## On-demand references

Read these when their trigger condition fires.

- [Persistent memory (infinite-memory)](docs/infinite-memory.md) — Use when semantic search across a large corpus of stored facts would add value beyond the auto-memory index.
- [The bd CLI contract](docs/bd-cli-contract.md) — Use after any `bd` upgrade, and before writing a `bd` command into an instruction file, skill, hook or doc. Covers `scripts/tests/test-bd-cli-contract.py`, and why bd 1.2.2 has a higher version and fewer features than 1.2.1.
- [Test writing guidelines](docs/test-writing.md) — Use when writing or reviewing tests; lists low-value patterns reviewers reject (static config, language internals, framework behavior).
- [Implementation pattern discovery](docs/implementation-patterns.md) — Use when planning or implementing a new feature; describes how to find existing abstractions (interfaces, ABCs, traits) before writing new code.
- [Jira integration](docs/jira-integration.md) — Use when commenting on or editing Jira tickets via the Atlassian MCP; covers markdown vs wiki markup and hyperlink handling.
- [Incident investigation heuristics](docs/incident-heuristics.md) — Use when triaging recurring pipeline errors (MISSING_DEPS, OOM, timeout); covers execution duration as an error signal.
- [Subagent fan-out](docs/subagent-fanout.md) — Use when splitting a large input across many subagents; covers the Read tool's two truncation ceilings, byte-based chunk sizing, the coverage-accountability requirement that prevents silent partial analysis, and file-based result delivery.
- [Conductor heartbeat rules / standing orders](docs/conductor-heartbeat-rules.md) — **Read at conductor startup.** Injected into every heartbeat by `scripts/conductor-heartbeat.sh`. Holds the dispatch imperative, the NEVER ASK table, the park-and-continue rule (moved here from the work contract 2026-08-29 so it is reinforced per-turn rather than read once) and the exit predicate. The live `HEARTBEAT_RULES.md` is a symlink to it.
- [The work contract (Jonny <-> conductor)](docs/conductor-work-contract.md) — **Read at conductor startup, and before any triage, dispatch, merge or close decision.** Agreed 2026-08-18. What runs without asking, when an agent-filed bead may be set ready, how capacity is counted, what `closed` means, and which merges the conductor makes itself. Amends `hq/CLAUDE.md` (its section 11 lists which rules) and outranks both `POLICY.md` files.
- [The communication contract (how the conductor writes to Jonny)](docs/conductor-communication-contract.md) — **Read at conductor startup, and before writing ANY message to Jonny.** Agreed 2026-08-18. The work contract governs what gets done; this governs how it is described to him. No identifier stands alone, every technical term is glossed, length stays net-neutral, and the four message types he sees most have fixed shapes. Extends the "NEVER write a bare ID" rule in `hq/CLAUDE.md`. Enforcement `jbrooksbartlett-5r44` is not built yet.
- [Conductor operations](docs/conductor-operations.md) — Use before running `agent-deck conductor setup` (it symlinks rather than copies, and `diff` cannot detect that), before forking a session, or when reconnecting beads to sessions after a restart. Also holds the lease arithmetic, the capacity measurements and why the capture gate sits at triage.
- [Conductor repo gates](docs/conductor-repo-gates.md) — Use before merging a `switchboard` PR (the cold-gate the standing grant does not remove), or before putting any PR on Jonny's list.
