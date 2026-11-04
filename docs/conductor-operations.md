# Conductor operations: reference depth behind hq/CLAUDE.md

`hq/CLAUDE.md` loads every conductor turn and holds only always-do-X rules; this file is depth needed occasionally, each section keyed to a trigger. It lives here because `agent-deck conductor setup hq` rewrites `hq/CLAUDE.md` and both `POLICY.md` files and that directory is in no git repository.

Triage, dispatch, capacity, closing, merging, the effect gate, skill routing and conductor discipline are owned by `conductor-work-contract.md`; how the conductor writes to Jonny is owned by `conductor-communication-contract.md`. Where this file disagrees with a contract, the contract wins.

---

## 1. Before running `agent-deck conductor setup hq`

**Trigger: you are about to run it, for any reason.** It rewrites `hq/CLAUDE.md`, so every hand-edit there is at risk.

`-instructions-md` SYMLINKS rather than copying, so a path under `/tmp` vanishes on the next temp sweep. `diff <backup> CLAUDE.md` returns clean even then, because it compares the file to itself; check the file type instead:

```bash
BK=~/.local/share/agent-deck/conductor/hq-CLAUDE.md.backup   # durable, never /tmp
cp ~/.local/share/agent-deck/conductor/hq/CLAUDE.md "$BK"
agent-deck conductor setup hq -instructions-md "$BK" -heartbeat
ls -la ~/.local/share/agent-deck/conductor/hq/CLAUDE.md      # MUST be -rw-, not lrwx-
```

If it came back a symlink, convert it to a real file (you cannot write through it):

```bash
cd ~/.local/share/agent-deck/conductor/hq
cp "$BK" CLAUDE.md.realfile && rm CLAUDE.md && mv CLAUDE.md.realfile CLAUDE.md
```

`POLICY.md` and `heartbeat.sh` are regenerated too but are unmodified generated files; only `CLAUDE.md` carries hand-edits. `Bash(agent-deck conductor setup*)` stays in `permissions.ask` deliberately.

---

## 2. Forking a session

**Trigger: you are considering `agent-deck session fork` instead of `agent-deck launch`.**

Fork carries conversation history and uncommitted state into a new worktree, but works only on a Claude, OpenCode, Pi or Codex session. A `"tool": "shell"` session has no transcript, and "origin still alive" does not mean forkable.

```bash
agent-deck session show --json <origin> | grep -E '"(tool|can_fork|claude_session_id)"'
# Viable ONLY if tool is claude/opencode/pi/codex AND claude_session_id is present.
# can_fork is omitted entirely when false - absence is a NO.
```

When the origin fails the check, launch instead and make the bead self-contained.

---

## 3. Why claims are leases, and why the mismatch cannot be tuned away

**Trigger: you are wondering whether to wire up a `bd reclaim` timer, raise the claim TTL, or ask a worker to heartbeat.**

`bd update <id> --claim` takes a lease with a ~5 minute TTL; a P0 takes hours. `bd reclaim` expects a supervisor timer with a window of ~2x the TTL, and none is wired up, so a lapsed lease is inert: the bead sits `in_progress` and nothing reaps it. Adding a reclaim timer without fixing the worker side would yank long-running work back to `ready` and dispatch it twice.

The conductor heartbeat is every 15 minutes, so it cannot sustain a 5-minute lease at any window. If leases are ever made to matter, `bd config set claim.ttl <value>` must first raise the TTL well above the heartbeat cadence. Ask agent-deck (tmux session exists?) or the remote runtime (session running?) rather than inferring death from silence.

---

## 4. The bead-and-session join, and the gap it leaves

**Trigger: you are reconnecting dispatched work after a restart, or a bead and a session disagree.**

Beads and agent-deck are joined only by convention:

- **Bead to session:** the bead's notes carry session title, session id and worktree (the join-key block in `hq/CLAUDE.md` under Dispatching).
- **Session to conductor:** the child's `parent_session_id` is the conductor's id, which routes completion events home. If empty or wrong, the conductor is never told the child finished.
- **Reconnect after a restart:** `bd list --status in_progress`, read each bead's notes for its session id, then `agent-deck session show --json <id>`. Bead `in_progress` with the session missing or `error` is orphaned work. Confirm any `error` by advancement before acting.

A session started outside the conductor's view tells the queue nothing. `bd ready` is the truth about work, `agent-deck list` about sessions; reconcile by hand when they disagree.

---

## 5. Why the capture gate sits at triage rather than at capture

**Trigger: someone proposes gating bead creation.**

Follow-up work surfaces mid-implementation, so capture must work at any point without derailing work in flight; gating triage does not. Over-capture is cheap; under-capture is the failure mode.

Provenance is a convention: Beads records no useful creator field (`created_by` is always the OS user), so the `agent-proposed` label is the only provenance, which is why it survives promotion to `open` and why the skim query also filters `--status deferred`. `bd q` prints only an ID, so live capture costs one line; sharpen after confirmation.

The spec bar: a bead is ready for a worker only when its description alone lets a stranger start. "Re-phase the injectors" is not delegatable; the same line plus file path, gate name, template to copy and how to verify is.

---

## 6. Capacity: the hardware the thresholds were derived from

**Trigger: you are revising the capacity thresholds, not merely applying them.** Apply them from work contract section 4; this is only the measurement behind them.

Derived on an Apple M3 Pro, 12 cores, 18 GB RAM: memory, not cores, is the binding constraint. A worker's pane tree is 0.27-0.37 GB at rest but several times that mid-turn with 4-8 subagents fanned out, so budget ~1 GB per concurrent worker at peak.

```bash
ps -A -o rss=,command= | grep -c claude    # process-count sanity, alongside the section 4 checks
```

---

## 7. Bead IDs cannot be renamed, so the fix is presentational

**Trigger: you are tempted to make IDs self-describing at the source.**

`bd rename-prefix` changes `hq-` database-wide; nothing is per-issue, and the suffix is the primary key (renaming breaks `discovered-from:` edges, join keys in notes and cross-references). Write `id - title` on every mention, as `conductor-communication-contract.md` specifies.

## 8. At startup, sweep every launchd job's exit status, not just your own

**Trigger: conductor startup.**

```bash
launchctl list | awk 'NR>1 && $2 != 0 && $2 != "-"' | grep -v com.apple.
```

Column 2 is the last exit status. Apple's agents are almost all `-9` (normal), so filtering `com.apple.` leaves only real failures. `NR>1` is load-bearing: the `PID Status Label` header is neither `0` nor `-` and would otherwise print on a healthy machine.

This catches a job firing on its timer while its output path is dead. A scheduled monitor ticked every 15 minutes for an hour, failing to nudge a session that died with a fleet restart, each failure written to a `/tmp/*-tick.err` file and its own `tick.log`, which nobody opens.

- **Report what you find even when it is not yours.** The conductor's job is to notice.
- **Do not diagnose from the exit code alone.** Read the job's stdout and stderr paths from `launchctl print gui/$(id -u)/<label>`.
- **Do not trust an instrument that reports on a dead thing.** Over a dead tmux server, `agent-deck status`, `agent-deck list`, the monitor's tick mark and `agent-deck session show` (exit 0, full record for a gone session) all reported success (`hq-9j7h`). Confirming a delivery path needs a delivery, not a status read.
