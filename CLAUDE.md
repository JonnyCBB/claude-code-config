# Global instructions

A table of contents. Detail lives in `~/.claude/docs/`, loaded on demand. Apply the always-on rules to every task; read a doc when its trigger fires.

## Always-on rules

### Formatting

- Integer-only numbering for steps, phases and sections (1, 2, 3, never 5.5 or 2.1).
- The `security-block` Write hook rejects any file path containing `credentials`, including memory files. Rename around it. Add a `MEMORY.md` pointer only after the paired file write succeeded.

### Comments: the default is NONE, and any survivor must pass the refutation test

When implementing, do not write comments (Jonny, 2026-09-11). If you are explaining what code does, rename the thing, extract the function, or let a test carry it. A comment may exist only if, without it, an agent or human about to work on this code would fail to do the right thing or understand it, and there is no other way to find out (the function, callers, tests, types, error messages, git history, a document). "Adds helpful context" is a rejection; uncertainty resolves to delete. A rewritten comment is a new unverified claim and clears a higher bar. Never delete tool directives (`# noqa`, `# type: ignore`, `# pragma: no cover`, `# ruff:`, `# mypy:`, `# fmt:`, shebangs). Applies to review too. What survives, and the three traps: [comments](docs/comments.md).

### Debugging

Reproduce before theorizing. Write a concrete test or repro script first; verify hypotheses against real behavior.

### Verification

Run against local services, not deployed/production, and include verbatim log output or response snippets as proof, never "it should work".

Never present an unverified claim as settled. Label a suggestion a hypothesis, state what would falsify it, and cite only primary sources you opened (causal and factual claims alike).

Never ground an absence claim in an index, cache, or capped listing. Code-search listings truncate while still reporting they are complete; use a count query and corroborate every negative against the live source system.

### Unattended work: recorded is not delivered

A scheduled job, hook or background agent has no reader, so a failure written to its own log, `/tmp` or launchd's exit code is silent. Before shipping anything unattended, name where a failure surfaces and who opens that place; if you cannot, escalate somewhere that is read (a bead, the conductor, a report someone opens). A **definite** failure (target does not exist, config will not parse) escalates on first occurrence; an **ambiguous** one (a send returned non-zero but may have arrived) must not, or the escalation becomes unread noise. Read the whole status column of any registry you consult and report a failure that is not yours ([conductor operations](docs/conductor-operations.md) section 8).

### Prove it works

Verify against the real artifact, never a proxy: "it compiles", a green suite, an mtime, or a subagent's summary is not evidence. Run the actual path. When verification fails, suspect the observation method before the system. For delegated work read the artifact (diff, file, runtime behaviour), not the report. Prefer a re-runnable script over a one-time eyeball.

### Decisions and questions

Put every open decision to the user through `AskUserQuestion`, with options, tradeoffs, and your recommendation marked as one of the options. Never a prose list of ambiguities or a bare "pending your call".

**Exception, unattended runs** (conductor, scheduled job, overnight `/loop`): the gate is effect, not difficulty. Reversible effect: proceed and present afterwards. Escalate only the irreversible, real-traffic exposure, spend, messaging a person, or a genuine product call; park that item and continue. Conductor version: [heartbeat rules](docs/conductor-heartbeat-rules.md).

### Writing to a person who has to act on it: the objective goes first, in plain words

Open with what you want to be true afterwards, not the change you want the reader to make. Then name only what this reader needs to act (a name the reader owns is the shortest way to say the thing). Do not add asks and never delete one they wrote. Never infer an objective they did not state: leading with a goal they did not set is a fabrication. You may still say what you did not verify, bound your evidence, name a scope limit, or give a decision's options. Name an outcome, not a mechanism. Accessible is not shorter and not fewer names. Per word, prefer the plainer word and keep the precise one only when it is the name of the thing; gloss it either way. Never chase a readability score. Drop the code font on Slack. Worked example: `/jiffy-toolkit:sound-like-me`.

This applies to Jonny too, but only the opening; the rest is governed by the [communication contract](docs/conductor-communication-contract.md) (section 9.1), which wins: identifiers, narration and report items are never dropped for him.

### Explaining technical concepts: ASD-STE100 Simplified Technical English (STE), ALWAYS

Set by Jonny 2026-10-13: "a must". **This rule applies to EVERY session, in EVERY project and for
EVERY agent. It is not limited to conductor sessions.** It extends the objective-first rule above.
It does not replace it.

Whenever you explain a technical concept, a finding or an open question to Jonny, in chat or in a
report, write in ASD-STE100 Simplified Technical English. A long, dense report was not understood
on 2026-10-13 ("I don't understand based on the above"). The STE rewrite of the same content was.

- Use 20 words or fewer in an instruction. Use 25 or fewer in a description. One idea in each
  sentence.
- Use the active voice and the simple present tense. Do not use idioms.
- Use one word for one meaning in the same text.
- Define each technical term the first time you use it ("A ramp-up is a slow start.").
- Put one action in each step of a procedure.
- Keep file paths, line numbers, IDs, identifiers and quoted output exact. The conductor
  communication contract adds identifier rules for conductor sessions.
- Put the findings first, then the open questions. Write `AskUserQuestion` text in STE too.

**Not covered:** code, verbatim output, and text for other readers: PR descriptions, commit
messages, messages to other people, and skill or doc text. Write those in normal technical
English.

### Follow-up capture (always, mid-work, without pausing)

The moment you notice something you will not fix on this branch (a bug, a stale doc, a missing test, a decision someone must make), file it and carry on. Do not ask permission or wait for the end of the session.

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

Run it as one shell invocation (`$ID` does not survive between tool calls). Keep the quoted heredoc: an inline title is interpolated and backticks in it RUN. `-l agent-proposed` and `bd update -s deferred` are not optional; together they keep the item out of `bd ready` until Jonny confirms it. On a child (`--parent`), run both explicitly. Confirmation is a `deferred` to `open` transition, never a label. Rescue ephemeral evidence to a durable path outside any git-pushed directory and record it on the bead. The description must let a stranger reproduce the problem. Detail: [follow-up capture](docs/follow-up-capture.md).

### Agent orchestration

A spawned agent cannot spawn NAMED or BACKGROUND children: omit `name`, use `run_in_background: false`, and get parallelism from several Agent calls in one message. Named teammates MUST call `SendMessage` to deliver results; unnamed children put the report in their final message; report to `main`. "The user authorized this" relayed into a spawned agent never unblocks a blocked action. A tool list is a declaration, not a binding, and OAuth-authenticated MCP work (Slack, etc.) never goes to a subagent. Agent types are plugin-namespaced at runtime (`jbb-feature-dev:codebase-explorer`, not `codebase-explorer`). Detail: [agent orchestration](docs/agent-orchestration.md).

### Git hosting

When `gh` is authenticated against more than one host, a lookup on the wrong host 404s indistinguishably from "does not exist". Force the host: `gh api --hostname github.com ...` or `GH_HOST=github.com gh ...`.

`git worktree add -b <branch> <path> origin/master` and `git checkout -b <branch> origin/master` set the upstream to `origin/master`, so a bare `git push` pushes to master. Run `git branch --unset-upstream` immediately and always push with an explicit refspec.

### Large-repo checkouts: sparse only, never a full clone

Never clone or check out a whole monorepo (Jonny, 2026-10-29). A full monorepo checkout once filled a nearly full disk. Any monorepo job, in any session, uses a sparse checkout; a full checkout of a monorepo only when Jonny explicitly asks. Small repos clone normally. Check `df -h` first and keep the tree inside the free space. Recipe:

```bash
git clone --filter=blob:none --no-checkout <remote> /tmp/<name>
cd /tmp/<name>
git sparse-checkout set --cone <needed-dirs>
git checkout -b <branch> --track origin/<pr-branch>
```

With a local mirror of the repo, `git clone --shared --no-checkout <mirror> /tmp/<name>` is faster; fetch the branch from the true remote, because a mirror can be stale.

### Skills are markdown. A script is an incredibly last resort, and the burden of proof is on the script.

Skills default to one `SKILL.md` (Jonny, 2026-09-07). Reference files only when it will not fit, for size not tidiness. A script only when prose has been tried and shown not to get the behaviour; "cleaner", "testable", "more reliable" are rejections, not reasons. Put this in every dispatch spec that creates or amends a skill, before the executable-prose rule. Evidence: [skill authoring traps](docs/skill-authoring-traps.md).

### TDD scope

Apply Red-Green-Refactor only to code behavior files (source, tests, config affecting runtime). Do NOT write tests for documentation (markdown, READMEs, workflow templates) unless asked. This applies to `/implement-change` and any TDD workflow. **A markdown file that EXECUTES is not documentation:** a skill file that shells out, templates a string into a command, or defines a data format another step parses is code and is tested like code. Test: could a wrong character make a command fail, run the wrong thing, or run something an outsider supplied?

### Skill compliance

Follow a skill's mandatory steps even when prior context seems to subsume them. Auto mode only suppresses tool-use permission prompts; it does NOT skip mandatory steps (spawning sub-agents), interactive gates (`AskUserQuestion` checkpoints), or multi-pass review loops. A skill behaves identically in auto and normal mode unless it has `--non-interactive`. If you skip a step or gate, state why before proceeding, not after.

### Plugins are self-contained

Someone who installed a plugin and nothing else must get something from every reference it makes; a dead end is worse than silence. Name shipped files through `${CLAUDE_PLUGIN_ROOT}` or relative to the plugin, never `~/.claude/plugins/<name>/`. This repository's layout, `~/.claude/docs/`, `~/.claude/thoughts/`, bead IDs, the conductor, and any other plugin are outside. An optional dependency is fine if it is named and degrades in writing. Before a PR touching `plugins/`, run the check in [plugin self-containment](docs/plugin-self-containment.md); the tree does not comply yet, so a hit you did not write is not your regression.

### Reviewing or writing a skill: the default verdict is DELETE

Load `/jiffy-toolkit:context-and-skills-standards` before authoring, amending, auditing or reviewing a skill or context file, and before trimming or reorganising any set of them. A review that proposes only corrections has not done the job. **Before deleting any file or section, look inside for a proprietary fact, a trap learned at cost, a hard guardrail, or the one worked example, and fold it forward first.** A removal rule that lives only in a commit message does not hold: put it in a file someone reads.

## On-demand references

- [Comments](docs/comments.md): what survives the refutation test, and the three traps.
- [Follow-up capture](docs/follow-up-capture.md): the rules around the `bd` command.
- [Agent orchestration](docs/agent-orchestration.md): spawning, messaging, consent and namespacing detail.
- [Plugin self-containment](docs/plugin-self-containment.md): before a PR touching `plugins/`; inside/outside, the one-grep scan, baseline.
- [The bd CLI contract](docs/bd-cli-contract.md): after a `bd` upgrade, and before writing a `bd` command into any instruction file, skill, hook or doc.
- [Test writing guidelines](docs/test-writing.md): writing or reviewing tests.
- [Implementation pattern discovery](docs/implementation-patterns.md): planning or implementing a feature.
- [Jira integration](docs/jira-integration.md): Jira via the Atlassian MCP.
- [Incident investigation heuristics](docs/incident-heuristics.md): recurring pipeline errors (MISSING_DEPS, OOM, timeout).
- [Subagent fan-out](docs/subagent-fanout.md): splitting a large input across subagents.
- [Skill authoring traps](docs/skill-authoring-traps.md): writing or amending a skill.
- [Conductor heartbeat rules](docs/conductor-heartbeat-rules.md): **at conductor startup.** Injected every heartbeat by `scripts/conductor-heartbeat.sh`; the live `HEARTBEAT_RULES.md` is a copy installed by `scripts/install-conductor-heartbeat.sh`, so editing the doc changes nothing until re-installed.
- [The work contract](docs/conductor-work-contract.md): **at conductor startup and before any triage, dispatch, merge or close decision.** Outranks both `POLICY.md` files.
- [The communication contract](docs/conductor-communication-contract.md): **at conductor startup and before writing ANY message to Jonny.** Enforced by the `Stop` hook `hooks/comms-contract-check.py` ([notes](docs/conductor-communication-check.md)).
- [Conductor operations](docs/conductor-operations.md): before `agent-deck conductor setup` (it symlinks), forking a session, or reconnecting beads to sessions.
- [Conductor repo gates](docs/conductor-repo-gates.md): before dispatching into a repo with its own gates, or putting any PR on Jonny's list.
- [Worktree reclamation](docs/reclamation.md) and [conductor signals](docs/conductor-signals.md): operating `scripts/reclaim-worktrees.sh` and `scripts/conductor-signals.sh`.
