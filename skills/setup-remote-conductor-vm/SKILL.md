---
name: setup-remote-conductor-vm
description: Sets up the conductor stack on a remote Linux VM that already exists, given only its address - tooling, git-host auth, the beads queue cloned from its git remote, the repos the queue targets, plugins, the conductor directory with its macOS paths rewritten by file role, switchboard, agent-deck web, a systemd user timer replacing launchd, and the Mac-side SSH alias and tunnels. Ends with a phone-access gate and one handover block of the commands needing a sudo password. Use when asked to "set up the remote VM", "set up the conductor on the VM", "provision the remote conductor", "set it up like the last one", or when handed a remote-development host on a private hostname to put the stack on - including when a VM has been rebuilt or re-IP'd and it all has to be redone. NOT for creating the VM (that is the organisation's own VM provisioning), NOT for setting up a Mac, and NOT for operating or debugging a conductor that is already running.
---

# Setting up the conductor stack on a remote Linux VM

The VM already exists. You have its address. Your job is everything from the first SSH into it to
a conductor taking work, reachable from the Mac and from a phone.

**You know how to run these commands.** What this skill carries is the order, the unguessable
literals, and the checks — because this stack's dominant failure mode is a step that reports
success while doing nothing. Seven or more separate recorded instances. So the governing rule:

> Before accepting any check, ask: **what would this print if the thing were broken?** If the
> answer is "the same thing", it is not a check. Replace it.

Two consequences. **Prove the operation you need, not the transport you assume it uses** — SSH to
the git host returns `Permission denied (publickey)` on these VMs while clones work fine, so probing
`ssh -T` wrongly concludes the git host is unreachable and stops. And **never conclude something is absent
because a search did not find it**; state what would have found it, and confirm the instrument
could have.

[`references/verification-doctrine.md`](references/verification-doctrine.md) holds the cross-phase
instrument traps (`read -t`, `status: error`, `bd show --json`'s array, MCP dual registration) and
the rule that `bd` flag facts go stale between release candidates. Read it before phase 9.

## Order, and why it is this order

**Platform facts → the human's root block → tooling → auth → queue → repos → plugins → conductor
directory → services → scheduling → access.**

Rewriting paths before the repos exist is wasted work, and scheduling a job before the config is
reconciled points a timer at files that will move.

## 1. Collect the inputs and establish the platform facts

**Derive the address; do not ask for it and do not trust a cached one.** A remote-dev instance
name carries a trailing number that changes when the VM is **recreated** (it survives a restart),
so a hostname someone hands you — or an existing SSH alias — may point at an instance that no
longer exists. The failure is `nodename nor servname provided`, which reads as a network problem
rather than a stale name.

```bash
gcloud compute instances list --project=<remote-dev project>   --filter="name~<your-handle> AND status=RUNNING"   --format="table(name,zone.basename(),status,networkInterfaces[0].networkIP)"
```

`status=RUNNING` is load-bearing: a stopped predecessor otherwise gives you two rows and no signal
about which is live. If you do not know the project, read it from an instance you can already
reach — its own metadata server (`metadata.google.internal/computeMetadata/v1/project/project-id`,
with header `Metadata-Flavor: Google`) reports project, zone, name and internal IP as facts rather
than as inferences from a naming convention. Record the project for next time.

You need three values: the **FQDN**, the **internal IP** (the phone needs the IP — its DNS cannot
resolve the private hostname), and the **Linux username**.

**Add a short SSH alias before anything else.** These hostnames run past 60 characters, longer
than a Unix socket path allows, which breaks SSH `ControlMaster` and makes `agent-deck remote
update` fail for a reason that looks nothing like hostname length:

```
Host conductor-vm
  HostName <FQDN>
  User <username>
  ForwardAgent yes
```

**Check for a stale alias first, and back the file up before touching it.** A `conductor-vm` entry
may already exist pointing at a previous VM; it will fail to resolve, or worse connect to the wrong
box, while every later step fails confusingly. Compare its `HostName` against the FQDN you just
derived, update in place, and do not add a second stanza. This one comparison is the whole check —
it costs one command and it is the difference between a five-second fix and an hour of chasing a
network problem that is not one.

Then confirm the box answers and note its shape (cores, RAM, disk). Use `conductor-vm` for every
remote command from here on.

**Five platform differences shape everything that follows.** State them to the user now, because
each silently breaks something that looks fine:

| macOS assumption | Reality on the VM | Consequence |
| --- | --- | --- |
| `launchd` schedules jobs | `~/Library/LaunchAgents` does not exist | Every scheduled job has no scheduler and **fails by never running**. Nothing errors. Phase 10. |
| `caffeinate`/`pmset` keep it awake | Neither exists; a VM does not sleep | The conductor's startup checklist step 1 is **inapplicable here**. Say so, or a conductor will try to start a `dont-sleep` session that cannot work. |
| Paths are `/Users/<user>` | `/home/<user>` | Absolute paths appear in permission rules, dispatch specs and evidence files, and need three different treatments. Phase 8. |
| `sudo` is passwordless-ish | `sudo` needs a password | No agent can do it. Collect those commands into one block. Phase 2. |
| Login sessions persist | with lingering off, the per-user manager exits when the LAST login session closes | agent-deck's tmux lives in that manager, so the **conductor and every worker** die, not only timers. Phase 2. |

## 2. Hand the human their root block, then carry on

Do not discover root-requiring commands one at a time over the next hour. Give them all at once
and continue while they run them. Today that is one line:

```
sudo loginctl enable-linger <username>
```

**This is not "the timer dies at logout".** With lingering off, the per-user systemd manager exits
when the last login session closes, and agent-deck runs its tmux server inside it — so the **conductor and every worker**
are torn down together in milliseconds. No error surfaces anywhere - the journal records an ordinary
manager stop, not a failure. Measured 2026-09-11: a dropped VPN ended the only login session and
nine panes stopped within 17ms, taking the conductor and every worker it was running.

**`KillUserProcesses=false` does not save you.** It governs system-manager session scopes, not the
per-user manager, and agent-deck's tmux is in the latter. It is the most plausible wrong conclusion
available here, because it looks exactly like the setting that would protect you.

**Still park-and-continue rather than a gate** — setup completes without it because you are logged
in throughout, which is precisely what makes it dangerous: the failure cannot appear until you leave.
Report whether it was run; `loginctl show-user <username>` prints `Linger=yes` or `Linger=no`, so
that check can fail.

**If it is refused, do not finish without a substitute.** Refusal is ordinary: the self-service call
can return `Access denied` even where the policy file grants it, because logind asks polkit and polkit
may not be running. Run `systemctl is-active polkit` before blaming the policy.
[`references/systemd-scheduling.md`](references/systemd-scheduling.md) carries a tested no-root
substitute — a cron job that keeps one login session open by connecting to the host from itself.

## 3. Install the tooling, and prove each one by running it

`~/.local/bin` is not on PATH by default, so export it in `~/.bashrc` first. Then install and
**verify each tool by running it**, never by checking that a file exists:

| Tool | Route | The check that can fail |
| --- | --- | --- |
| `claude` | standard installer | `claude --version` prints a version |
| `agent-deck` | GitHub release tarball into `~/.local/bin` | `agent-deck --version` prints a version |
| `bd` | Linux tarball, **version matched to the Mac** | `bd --version` string-identical to the Mac's |
| `node`/`npm` | distro packages | satisfies switchboard's `engines.node` range |
| `uv` | linuxbrew | `uv --version` prints a version; the google-docs skill and `uv run` MCP servers need it |
| `gh` | linuxbrew | phase 4 |
| `dolt` | release tarball into `~/.local/bin`, **no root** | `dolt version` prints a version |
| `git`, `tmux`, `jq`, `python3`, `rsync` | distro packages | usually already present |

**`agent-deck remote add`/`remote update` fails on these hosts** because of the socket-path length
in phase 1. Install from the release tarball by hand and do not read the failure as a symptom of
anything else.

**The bd version must match the Mac exactly, and you derive it rather than assuming it.** A
mismatch is not a warning but a schema wall — a Mac database at schema v65 is unreadable by a
binary that knows up to v53. Read the Mac's version with **`which -a bd`**, not `which`: there are
often two binaries (one from Homebrew, one in `~/.local/bin`) and PATH order decides which runs,
so the version you would otherwise have quoted may not be the one in play.

**Read switchboard's Node range from its own `package.json`** (`engines.node`) rather than trusting
a remembered number, and compare the VM's `node --version` against it. The range is narrow. The
Mac's ambient Node may sit well outside it, which is fine — it is the VM's that must satisfy it.

**Install `dolt` even though `bd` runs Dolt embedded, because the queue-recovery procedures need
it** — resolving a real divergence, and the recovery for destroyed bead notes, both drop to the
`dolt` CLI, and nobody discovers it is missing until they need it. It takes **no root**, so it is
not a phase 2 handover; the three commands, and what to do with it, are in
[`references/shared-queue-sync.md`](references/shared-queue-sync.md).

Codex is optional — see [`references/verification-doctrine.md`](references/verification-doctrine.md)
for the no-root install, the egress check whose good answer is a `401`, and why the browser
sign-in cannot complete here.

## 4. Fix auth, and do not test it the obvious way

`gh` must be authenticated for `github.com` **and** for any other git host the queue or the repos
live on.

**Test the git host with `git ls-remote` against a real repo — never `ssh -T`.** A ref line printing
means the host is reachable; nothing printing means it genuinely is not. `ssh -T` returning `Permission
denied (publickey)` here proves nothing, because a global `insteadOf` rewrite sends these URLs over
HTTPS. That same rewrite is why a Claude Code marketplace whose source is `git@<git-host>:...`
installs fine in phase 7 — and, as phase 5.3 covers, why `bd dolt` is a separate problem entirely.

## 5. Provision the queue by cloning its remote — never by copying `.beads`

**This is a gate. Do not continue past a failure here**, and read
[`references/shared-queue-sync.md`](references/shared-queue-sync.md) before you start. Two
conductors sharing this queue is the **highest-consequence failure mode in the setup** — on a real
run it broke within an hour, silently, with both machines dispatching the same bead.

Copying a `.beads` directory produces a database with the right contents and the wrong lineage: a
pull reports "Pull complete" and changes nothing, then push is rejected non-fast-forward. **If you
find an existing `~/beads-hq/.beads` that did not come from a clone, stop and report it.** Do not
work around it.

**5.1 — Clone `beads-hq`, then read two sections of its own `RUNBOOK.md`**: "Setting this queue up
on another machine" and "Never do these". The runbook travels with the queue and is canonical, so
follow it rather than a copy of it here. Clones land at `0755` and `bd` warns, so `chmod 700` the
`.beads` directory. The prohibition that matters most on a fresh box: **never `bd init` in
`$HOME`** — it also runs `git init` and turns the entire home directory into a git repository.

**5.2 — Set three environment facts before any `bd` call.** These are the unguessable part:

- **`BEADS_DIR=$HOME/beads-hq/.beads` must reach non-interactive shells**, because Claude Code
  hooks and agent sessions run in them. On Linux `~/.bashrc` alone does not cover that — put it in
  `~/.profile` as well.
- **`git config --global beads.role maintainer`** — global, not local. `bd` is invoked from
  everywhere and reads the *current* directory's git config, so a local setting still leaves two
  warning lines on every `bd` call.
- **Set the beads actor to match the handle your historical claims carry.** `bd close` refuses a
  claim whose assignee differs from the actor (`assignee is "jonny", actor is "Jonny
  Brooks-Bartlett"`), and the actor comes from `git config user.name`. Matching them now avoids
  needing `--force` on every inherited claim later.
- **Set a distinct `node_id` on this machine, and confirm the Mac has one too.** `bd reclaim` skips
  leases another replica granted — but **the guard is opt-in with no hostname fallback**, so an
  unnamed deployment keeps the old unguarded behaviour. That is the real root cause of the 93-bead
  divergence in phase 9, and arming it is strictly better than switching reclaim off. Use
  `bd config set node_id <name>` (per-machine `~/.config/bd/config.yaml`, **never committed**), one
  id per *store* rather than per host. `bd config get node_id` prints `(not set in ...)` when it is
  absent, so the check can fail. Details in
  [`references/shared-queue-sync.md`](references/shared-queue-sync.md).

**5.3 — Fix the Dolt remote's transport BEFORE trying to sync.** `bd dolt` does not resolve URLs
through git's config, so the `insteadOf` rewrite that makes plain `git` work does nothing for it.
This trap looks exactly like a lineage failure and is not one. Decide it by reading
`bd dolt remote list`: an `ssh://`, `git+ssh://` or `git@host:` URL **cannot be used from this
VM**. If it is any SSH form, add an HTTPS remote alongside it and pass `--remote <name>` to every
sync from then on, including the phase 9 dispatch gate. The details, and why `bd sync`'s automatic
remote adoption is a hazard here rather than a convenience, are in
[`references/shared-queue-sync.md`](references/shared-queue-sync.md).

**5.4 — `bd bootstrap` is the step that actually populates the database.** The git clone brings
**only the config files**; the issues live in `refs/dolt/data` and bootstrap is what pulls them.
Skipping it leaves a valid-looking empty queue. Use `bd bootstrap`, never `bd init --force` —
bootstrap never deletes existing issues, and it exits non-zero when it cannot set up a database.

**The positive check is a non-zero issue count** (`bd count`, `bd stats`). Zero, or a "creates a
fresh one" plan in the bootstrap output, means it fell through to the empty-database branch and the
queue is *not* provisioned — which otherwise reads as a healthy install of nothing.

**5.5 — Prove the lineage with a real round-trip.** A bootstrap that succeeds is not evidence the
queue can *sync*. Use `bd sync`, which pulls, checks for conflicts **positively from the conflict
tables** rather than from the pull's exit status, repairs the `is_blocked` flag, and pushes. Branch
on its exit code:

| Exit | Meaning | Action |
| --- | --- | --- |
| `0` | synced, or nothing to do | the only outcome that clears this gate |
| `1` | transport, auth or storage | suspect the remote URL (5.3), **not** the lineage |
| `2` | merge conflict, halted, nothing pushed | stop, report — needs a human |
| `3` | retries exhausted, transient | retry |
| `4` | dirty working set stuck, not busy | stop, report — needs an operator |

**Never `bd dolt push --force`** — it is the one action that can destroy the other conductor's
queue. And keep the two failure causes apart: `rc=1` on an SSH-form remote is 5.3's transport
problem, while a pull that integrates nothing followed by a non-fast-forward rejection is the
unrelated-histories lineage problem, which only re-cloning fixes.

**5.6 — Read the queue back against an unfiltered control.** `bd ready` and `bd list` both need
**`--limit 0`**; the silent default is 100, and that display cap was mistaken for the real figure
for half a day. Both counts go in the report as *numbers measured today*, and into no file that is
loaded every turn — counts decay silently and are then read as current by every future session.
Write the query, not the count.

## 6. Clone the repos the queue targets, and build them

Every ready and in-flight item names a repo path, so rewriting paths in phase 8 achieves nothing if
the repo is absent — the paths point at emptiness.

**Derive the list from the queue rather than assuming it**, by extracting checkout paths from the
ready set's descriptions, notes and titles. **Anchor the pattern on the checkout root — a home
prefix, then `src/`, then exactly one path segment (`~/src/<repo>`).** Anything looser matches every
`.../src/main/...` *source file* in every bead body: on real queue data a loose pattern returned
dozens of Java and proto files and not one repo. Count occurrences per checkout so you can see
which ones the queue actually leans on, and check the deduped list against the raw match count so a
silently-failing filter is visible.

Switchboard needs `npm ci && npm run build` or its launcher refuses.

**Decide where the canonical checkout lives, once, and say so.** Two checkouts (`~/switchboard` and
`~/src/switchboard`) are survivable while they match and a silent trap the
moment they do not. The launcher resolves by trying `SWITCHBOARD_REPO`, then walking up from the
current directory, then its default — so name the one the dispatch specs name.

**Expect exactly one test failure, and name it.** `liveBdContract` fails when `.bd-version` pins a
different version than the ambient `bd`. That is a designed alarm firing correctly, not
environmental noise. The consequence for every dispatch spec written on this host: *"npm test must
be green"* is unsatisfiable. Write instead — *expect exactly one failure, `liveBdContract`'s version
alarm, and treat any other failure as real.* Otherwise a worker either grinds on a failure that is
not its own or quietly decides it passed.

## 7. Install the plugins BEFORE starting any session

**A session fixes its skill set and its Bash PATH at startup.** A plugin installed at 11:22 into a
session that started at 11:02 is unresolvable in that session, with no error explaining why.

`~/.claude` is itself a clone of the setup repo, so the marketplace may already be declared in the
synced `settings.json`. Two consequences, both seen:

- `plugin marketplace add` can **fail** because the marketplace is already declared with a
  different source URL, while `plugin install` still **works**. A failing `add` is not a blocker.
- Switchboard's launcher and its `/switchboard` skill ship as a plugin from the switchboard repo.
  Install it (`/plugin marketplace add git@github.com:JonnyCBB/switchboard.git`, then
  `/plugin install switchboard@switchboard`) rather than writing launch commands into this skill.

The positive check is `/plugin` in a session started **after** the installs, showing every expected
plugin as enabled. Do not infer "installed" from a directory existing on disk.

Note `~/.claude/thoughts/` is gitignored, so nothing in it arrives via the clone. Any handoff or
research document you want on the VM has to be copied deliberately, and any reference to a
`thoughts/` path in a file you copy over will dangle.

## 8. Copy the conductor directory, rewrite paths by file role, and pre-trust

The conductor directory is not in a repo, so it comes over by `rsync`. Exclude `run-status/`.

### Rewrite by file role, never with one blanket rule

A single `sed` over the copied files is wrong three different ways. Sort every `/Users/...`
reference by what the file is for:

| File role | Treatment | Why |
| --- | --- | --- |
| **Live instruction files** — dispatch specs, preambles | Rewrite to `~/`, which resolves on both machines. Only standalone repo-location lines. | They are read and acted on. |
| **Permission rules** — `.claude/settings.json` | **Add Linux twins alongside the Mac paths**, never replace. Allow and deny lists are additive, so the file then works on both machines. | Rules need literal absolute paths. |
| **Historical evidence** — `task-log.md`, `evidence/*.log`, `run-status/`, stored tracebacks | **Leave untouched.** | These are records of what ran on the Mac. Rewriting them falsifies the evidence the work contract depends on. Most references legitimately remain. |

**The most serious trap here: Mac-only `deny` rules protect nothing on Linux.** The conductor's own
guardrails — deny writes to `*.sh`, `.claude/**`, `.envrc`, `.mcp.json` — are written with absolute
`/Users/...` paths. On arrival they match nothing, so the conductor can overwrite its own safety
rules and **no prompt fires**. "Does the config load" is not a check for this.

Three things to get right, all covered in
[`references/path-rewriting-and-trust.md`](references/path-rewriting-and-trust.md): the rules live
in the **conductor directory's** `.claude/settings.json`, not `~/.claude/settings.json` (which
holds none); a count of zero is ambiguous between "no Linux rules" and "no rules at all", so report
the total and the per-prefix counts together; and the rules use a **triple-slash** form
(`Edit(///Users/<user>/...)`) that a hand-written twin will drop, matching nothing while looking
right.

### Reconcile `~/.claude`, and commit local edits BEFORE anything else

If `~/.claude` on the VM came from a fresh clone it is current — say so and move on. If it was
copied from the Mac, it will be far behind `origin/master` with locally-modified files that were
also modified upstream, so a plain `git pull` conflicts. **That staleness is the root cause of a
whole class of confusing symptom:** instructions referencing documents the checkout predates, so
the references dangle. It looks like a broken instruction file; it is an old checkout.

Order matters, and this is the highest-value step in the phase:

1. **Commit the local edits to a branch first, before attempting any merge or pull.** A
   hand-written rule can exist in no commit on any branch, with the working tree its only copy — a
   careless checkout destroys it. Split commits by provenance so each is independently droppable:
   authored rules, then machine-local settings, then copied-in documents.
2. **Do not push.** `git branch --unset-upstream`, so a bare `git push` fails rather than doing
   something surprising.
3. **Stay on that branch.** Switching back to `master` reverts those files out of what Claude Code
   actually reads, while leaving the commits looking safe.
4. Only then decide whether to merge master. **Do not automate this** — it is a prose merge in the
   user's own words and belongs to them. Every other step here is mechanical.

### Create the output directories, and register MCP servers in the right file

A missing output directory fails at the moment of writing, hours later. Create the
`thoughts/shared/{handoffs,evidence,verification,requirements}` tree, `~/.claude/worktrees`, and
`~/evidence/{reclamation,rescued-worktree-files}`.

**`~/evidence/reclamation/` is the log directory for a weekly *worktree disk-cleanup* job — it has
nothing to do with bead-lease reclaim.** The two share an English word and nothing else. Do not
read the note about reclamation in phase 9 as being about this directory, and do not disable the
worktree cleanup on its account; it is harmless.

**MCP servers go in `~/.claude.json`, not `settings.json`**, which does not accept an `mcpServers`
key. Register them with `claude mcp add <name> -s user -- <command>`.

### Pre-trust every path a session will open — the biggest single killer

**Symptom:** a launched worker reports `status: error` within seconds and its tmux pane is gone. No
pane under any name, no process. Real death, not the status field lying.

**Cause:** Claude Code asks *"Quick safety check: Is this a project you created or one you trust?"*
on any path it has not seen, and **the pre-selected option is `No, exit`**. The launch then delivers
its initial message, and that Enter keystroke selects exit. The process quits, the pane dies, and
the brief is swallowed unread. Every dispatch creates a new worktree path, so every worker hits it
— it had silently destroyed five sessions before anyone understood why.

The fix is `hasTrustDialogAccepted: true` under the absolute path in `~/.claude.json`'s `projects`
map, for the conductor directory now and each worktree path at dispatch. Trusting the repo root is
**not** enough; `.worktrees/<branch>` is a different path. Preserve any other keys already on an
existing entry.

**And do not verify this with `claude -p`.** Print mode skips the dialog, so the probe passes while
the interactive launch keeps dying — reproduce through a tmux-launched interactive session instead.
A resumed session also comes back with an *empty* prompt, because the brief was consumed by the
dialog; re-send a short message pointing at a spec **file**, using `--message-file`.

## 9. Start the services and the conductor

Read [`references/verification-doctrine.md`](references/verification-doctrine.md) before this phase.
Every liveness judgement below depends on it.

Start switchboard through **its own launcher and its own skill** (`/switchboard`), not `npm start`.
`npm start` cannot tell whether a board is already running, which is how you get two servers
writing one queue; the launcher detects a live board and starts nothing.

Two settings that matter and one that must not be set:

- **Leave `SWITCHBOARD_ADAPTERS` unset.** The launcher's own default is correct. An explicit set
  that omits the command-centre adapter makes the front door **silently serve the committed test
  fixture** while `bd` and `agent-deck` are real — a board showing three-week-old data and looking
  entirely healthy.
- **Live-queue consent goes through `switchboard permit --grant`**, recorded once by a person at a
  terminal. Exporting the equivalent environment variable is precisely what stops the interlock
  ever firing. Never set it yourself.
- **Grep the shell rc files for aliases wrapping the tools you just corrected.** A one-line `sb`
  alias in `~/.bashrc` was the root cause of all three problems above and would have recreated them
  after any fix. Either there are no hits, or every hit is one you have read and approved.

Then agent-deck's web UI. Its TUI **refuses to run inside tmux by design**, so `--no-tui` with
`--listen 127.0.0.1:8420` is the right form here rather than a workaround. **Prove it bound and
answers** — a start command that returns is not evidence of a listener. Check for the listener with
`ss -ltnp` (never `pgrep`, which matches your own shell's command line) *and* for an HTTP status; no
listener line is the failure.

Then the conductor session: `agent-deck add <conductor-dir> -c claude --model 'claude-opus-5[1m]'
-t conductor-hq -g conductor`, then `agent-deck session start conductor-hq`. **Two prompts land on
first run** — trust the conductor directory (phase 8 pre-empts this) and bypass-permissions mode.
Both need a human at the terminal once.

Everything else about launching — the full model id rather than the `opus` alias, the branch that
gets renamed under you, the upstream that must be unset, `parent_id` — recurs at **every** dispatch,
so it lives as one checklist in
[`references/path-rewriting-and-trust.md`](references/path-rewriting-and-trust.md).

**Check the board is real rather than a fixture** by reading a bead id straight from `bd` and
confirming that same id appears on the board. A fixture cannot know an id you just read.

### Two conductors, one queue — build the dispatch gate now

The Mac conductor keeps running, so this queue is shared. **Do not leave coordination to a
convention both sides have to remember.** Two facts make an informal rule insufficient:

- **A blocked pull is indistinguishable from a queue where nothing changed.** A conductor that
  pulls, hits a merge conflict, and reads the ready set sees a normal-looking queue that simply
  lacks the other side's changes.
- **Claims do not save you.** They prevent duplicate dispatch only when both sides are current, and
  a blocked pull means one side never is.

So gate dispatch on a **successful `bd sync --remote <name>`** (phase 5.3's remote), treating `2`
and `4` as halt-and-escalate, and record each outcome where the next read can see it. The gate's
shape, and the limits of what it can catch, are in
[`references/shared-queue-sync.md`](references/shared-queue-sync.md).

**And settle bead-lease reclaim before either machine sweeps again.** This is what broke it on a
real run: a lease-expiry sweep flipped 93 beads from `in_progress` to `open` on one machine while
the other still held them as `in_progress`. It is structural rather than unlucky — leases expire in
about five minutes while real work takes hours, so **every dispatched bead carries a stale lease by
design**.

The fix is the `node_id` replica guard from phase 5.2, on **both** machines — with it armed, reclaim
skips foreign leases by construction and a scheduled sweep is safe. **Prefer that to disabling
reclaim**, which trades away dead-worker recovery: a genuinely crashed worker then leaves its claim
stuck `in_progress` until someone frees it by hand. Until the guard is armed on both sides, keep any
reclaim manual and sandwiched between two successful syncs.

Confirm the conductor's `CLAUDE.md` carries its "Two conductors, one queue" section rather than
assuming the rsync brought it.

**And flag, without editing, that its reclaim rule predates the guard.** That file's standing rule
is *"NEVER run a bare `bd reclaim`"*, justified on the grounds that the subcommand returned
`unknown command` — true of bd 1.2.2, false of the version now installed, where `bd reclaim` exists
and carries the `node_id` guard. The rule's *conclusion* is still sound while the guard is unarmed,
but its stated reason is stale. It is the user's own prose, so surface it for their decision rather
than rewriting it.

**One thing to flag in the report, not solve:** two conductors writing one `status.json` means
last-write-wins. Whether the Mac is still writing into a copy of the same conductor directory is
unknowable from the VM and needs the user to confirm.

### Re-authenticate the MCP servers, as a checklist

Expect **roughly twenty servers needing re-auth** after a fresh setup, each one an interactive
`/mcp` login. Make it an explicit checklist step rather than a surprise found later by a worker that
silently lacks a capability. **Count from `/mcp`, not from the startup warning line**, which
under-reports — see [`references/verification-doctrine.md`](references/verification-doctrine.md) for
the dual-registration trap that makes some "missing" capabilities merely differently named.

## 10. Replace the launchd jobs with a systemd user timer

The step with no macOS equivalent, and the one most likely to be forgotten because **nothing
complains**. Unit files, the environment probe and the enable sequence are in
[`references/systemd-scheduling.md`](references/systemd-scheduling.md).

**Port the heartbeat, but enumerate the rest before you finish.** "The launchd jobs" is plural and
the Mac carries several — measured on this machine, `ls ~/Library/LaunchAgents | grep -v com.apple`
returned the conductor heartbeat, a transition notifier, an hourly beads-triage job, and a weekly
worktree cleanup. Decide each one explicitly: port it to systemd, leave it
Mac-only, or — **for anything that writes the shared queue, as beads-triage
does** — confirm it will only ever run on one machine. A second automated queue-writer running hourly
on both sides is the same divergence phase 9 exists to prevent, arriving through a different door.
Note the triage job's code and its plist live *inside* `beads-hq`, which phase 5.1 clones onto the
VM, so it travels there whether or not you meant it to.

Four facts to carry into whatever you write:

- **Prefer a timer to `agent-deck conductor setup <name> -heartbeat`**, which regenerates the
  conductor's instruction files and symlinks rather than copies.
- **A user unit gets a minimal environment.** `Environment=` must declare PATH *and* every other
  variable the script needs. If `agent-deck` is not found the heartbeat's first gate fails and the
  script **exits 0** — success reported, nothing sent.
- **Scheduling and delivery are two separate legs**, and delivery is the one that has historically
  failed. Verify it by a new line in `heartbeat-received.log`, never by the timer's exit code, and
  arrange for the tick to land while the conductor is idle.
- **Lingering is in the phase 2 root block, and it protects far more than the timer.** If it was
  refused, the substitute in `references/systemd-scheduling.md` is not optional.

## 11. Mac-side access, and the phone gate

Follow [`references/mac-and-phone-access.md`](references/mac-and-phone-access.md): the `conductor`
attach alias, the two tunnel aliases and the port offsets that avoid clashing with the Mac's own
services, the phone route over VPN, and when the Eternal Terminal upgrade is worth the firewall
review.

The phone step is a **gate, not a task** — it is the one test that decides whether the VM is
reachable from a phone at all. Report the result either way.

## Closing report

Report in three parts, kept separate:

1. **Verified working** — each with the check that produced it and what that check prints when
   broken. No "it should work" lines.
2. **Needs the human** — the phase 2 root block if unrun **and whether the no-root session holder
   was installed in its place**, the `~/.claude` prose merge if it was copied rather than cloned,
   whether the Mac conductor still writes into a copy of the same conductor directory, and which
   switchboard checkout is canonical.
3. **Known-degraded, deliberately** — the expected `liveBdContract` failure and the MCP servers
   still needing auth, counted **from `/mcp`**.

File a follow-up bead for anything in part 2 or 3 you are not fixing on this pass, per the
follow-up capture rule, rather than leaving it in the report only.
