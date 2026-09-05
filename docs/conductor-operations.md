# Conductor operations: the reference depth behind hq/CLAUDE.md

Migrated out of `~/.local/share/agent-deck/conductor/hq/CLAUDE.md` on 2026-08-18
(`jbrooksbartlett-0vju`). That file loads on every conductor turn, so it now holds only always-do-X
rules; everything here is depth needed occasionally, and each section names the trigger that should
send you to it.

**Two reasons this lives here rather than in the conductor directory.** `agent-deck conductor setup
hq` rewrites `hq/CLAUDE.md` and both `POLICY.md` files, and that directory is in no git repository -
no history, no diff, no revert. This repo has all three plus a remote.

**What is NOT here:** anything the two contracts say canonically.
`~/.claude/docs/conductor-work-contract.md` owns triage, dispatch, capacity, closing, merging, the
effect gate, skill routing and conductor discipline;
`~/.claude/docs/conductor-communication-contract.md` owns how the conductor writes to Jonny. Where
this file and a contract disagree, the contract wins.

---

## 1. Before running `agent-deck conductor setup hq`

**Trigger: you are about to run `agent-deck conductor setup hq`, for any reason.**

Setup's own help says it "creates its directory, instructions file, meta.json, and session
registration". The instructions file is `hq/CLAUDE.md`. Every hand-edit in it is at risk on any
re-run, and it has already lost content this way once - the generated version named
`~/.agent-deck/conductor/hq/`, a directory that does not exist (corrected 2026-08-14).

**`-instructions-md` SYMLINKS, it does not copy.** Learned on 2026-08-14: passing
`-instructions-md /tmp/...` replaced `CLAUDE.md` with a symlink into a session-scoped
`/private/tmp` scratchpad, so the conductor's instructions would have vanished on the next temp
sweep.

**The trap that hid it:** the obvious check, `diff <backup> CLAUDE.md`, returned **clean** - it was
comparing the file to itself. A clean diff does not prove a copy happened. Check the file **type**.

```bash
BK=~/.local/share/agent-deck/conductor/hq-CLAUDE.md.backup   # durable, outside the regenerated dir
cp ~/.local/share/agent-deck/conductor/hq/CLAUDE.md "$BK"
agent-deck conductor setup hq -instructions-md "$BK" -heartbeat
ls -la ~/.local/share/agent-deck/conductor/hq/CLAUDE.md      # MUST be -rw-, not lrwx-
```

The backup you pass to `-instructions-md` must live somewhere durable, **never `/tmp`**. If it came
back a symlink, convert it to a real file - you cannot write through it:

```bash
cd ~/.local/share/agent-deck/conductor/hq
cp "$BK" CLAUDE.md.realfile && rm CLAUDE.md && mv CLAUDE.md.realfile CLAUDE.md
```

`POLICY.md` and `heartbeat.sh` are regenerated too, but they are unmodified generated files. Only
`CLAUDE.md` carries hand-edits worth protecting.

`Bash(agent-deck conductor setup*)` remains in `permissions.ask` deliberately - it is one of nine
rules still gated after the 2026-08-18 permission change, and it is the most destructive of them.

---

## 2. Forking a session

**Trigger: you are considering `agent-deck session fork` instead of `agent-deck launch`.**

Fork carries full conversation history **and** uncommitted working state into a new worktree, which
is what makes it the right choice when a bead needs context a fresh session would have to be
re-taught. But **most sessions here cannot be forked**, and the failure surfaces at dispatch time,
after you have already planned around it.

Fork works only on a **Claude, OpenCode, Pi or Codex** session. A session with `"tool": "shell"` has
no transcript to carry, and "the origin session is still alive" does not mean forkable - every SEAL
session is alive as a bare bash prompt.

```bash
agent-deck session show --json <origin> | grep -E '"(tool|can_fork|claude_session_id)"'
# Viable ONLY if tool is claude/opencode/pi/codex AND claude_session_id is present.
# can_fork is omitted entirely when false - absence is a NO, not a maybe.
```

On 2026-08-14 a fork was planned for `mqv` on exactly this bad assumption and had to be abandoned at
dispatch time. When the origin fails the check, launch instead and make the bead self-contained -
that is what the spec bar exists for.

---

## 3. Why claims are leases, and why the mismatch cannot be tuned away

**Trigger: you are wondering whether to wire up a `bd reclaim` timer, raise the claim TTL, or ask a
worker to heartbeat.**

The four operating rules are in `hq/CLAUDE.md` and they are what you follow. This section is the
arithmetic behind them, which matters only if someone proposes changing the setup.

`bd update <id> --claim` takes a lease with a **~5 minute TTL**. `bd show` displays it:
`Lease: expires in 4 mins (heartbeat just now)`.

**The mismatch:** a P0 takes hours; the lease lasts minutes. `bd reclaim`'s own help says to run it
*"from a supervisor on a timer with a window of roughly 2x the claim TTL."* That supervisor is the
conductor, and **there is no such timer wired up**. So today a lapsed lease is inert: the bead sits
`in_progress` with a stale lease and nothing reaps it.

**That makes this a latent trap, not a live fire.** It becomes real the moment anyone adds a reclaim
timer without also fixing the worker side, because long-running dispatched work then gets yanked
back to `ready` mid-flight and dispatched a second time.

**The arithmetic that forbids the obvious fix:** the guidance window is ~2x the TTL; the default TTL
is ~5 minutes; the conductor's heartbeat is every 15. **A 15-minute cadence cannot sustain a 5-minute
lease at any window** - that is structural, not tuning. If leases are ever made to matter,
`bd config set claim.ttl <value>` must raise the TTL well above the heartbeat cadence first.

**Why "ask, don't guess" is the right resolution rather than a workaround:** a lease exists to infer
death from silence, which is only necessary when you have no way to check. Here you do - agent-deck
knows whether a tmux session exists, Honk knows whether a pod runs. Querying a system that knows
beats inferring from silence, always. Decided by Jonny 2026-08-14 after the `mqv` dispatch
demonstrated the problem live: its lease expired about 16 minutes in while it was working perfectly.

---

## 4. The bead-and-session join, and the gap it leaves

**Trigger: you are reconnecting dispatched work after a restart, or you have found a bead and a
session that disagree.**

Beads and agent-deck do not talk to each other. The two are joined by **convention**, established on
the first real dispatch (`mqv`) on 2026-08-14:

- **Bead to session:** the bead's notes carry the session title, session id and worktree (the
  join-key block in `hq/CLAUDE.md` under Dispatching).
- **Session to conductor:** the child's `parent_session_id` is the conductor's id, which is what
  makes completion events route home. If it is empty or points elsewhere, the conductor is never
  told the child finished.
- **Reconnect after a restart:** `bd list --status in_progress`, read each bead's notes for its
  session id, then `agent-deck session show --json <id>`. Bead `in_progress` plus session missing or
  `error` means orphaned work, and this is the only reliable way to detect it. Confirm any `error`
  by advancement before acting on it.

**The gap that remains:** a session started outside the conductor's view still tells the queue
nothing. The join only covers work the conductor dispatched. So `bd ready` is the truth about
*work*, `agent-deck list` is the truth about *sessions*, and the conductor reconciles them by hand
when they disagree.

---

## 5. Why the capture gate sits at triage rather than at capture

**Trigger: someone proposes gating bead creation, or asks why agent-filed beads are not simply
reviewed as they arrive.**

Follow-up work is not only announced at the end of a session. It surfaces mid-implementation, often
at the moment it is best understood, so capture has to work at any point without derailing what is
in flight. Gating capture would interrupt work in flight, which is exactly what Jonny asked to
avoid. Gating triage does not.

**Over-capture is cheap; under-capture is the actual failure mode.** Work that exists only in chat
scrollback is lost when the session is.

**Provenance is a convention, not a feature.** Beads records no useful creator field - a bead's JSON
carries only id, title, status, priority, type and timestamps, and `created_by` is always the OS
user. The `agent-proposed` label is the only provenance the system has, which is why it survives
promotion to `open` and why the skim query has to filter on `--status deferred` as well.

`bd q` is documented as "designed for scripting and AI agent integration" - it prints an ID and
nothing else, so live capture costs one line mid-turn. Do not stop to write a full spec at that
point; sharpening happens after confirmation.

**The spec bar, and why it is worth the second pass:** a bead is ready to hand to a worker only when
its description alone is enough for a stranger to start. "Re-phase the injectors" is not
delegatable; the same line plus the file path, the gate name, the template to copy and how to verify
is. A confirmed bead without a dispatchable description is not yet startable.

---

## 6. Capacity: the hardware the thresholds were derived from

**Trigger: you are revising the concurrency cap or the memory thresholds, not merely applying them.**

The cap, the three session states, the thresholds and the reclamation order are **work contract
section 4**. Apply them from there. This is only the measurement behind them.

**The machine: Apple M3 Pro, 12 cores, 18 GB RAM, 14 GB swap.** 18 GB is the binding constraint,
not the cores - which is why the load-average threshold (9 on 12 cores) almost never fires first and
swap almost always does.

**Measured 2026-08-16 with three workers running:** a worker's whole pane tree is only **0.27-0.37
GB at rest**, but that is *between* turns. A worker mid-turn with 4-8 subagents fanned out costs
multiples of that, and the fan-outs are what spike. Budget **~1 GB per concurrent worker at peak**,
never the resting figure.

```bash
ps -A -o rss=,command= | grep -c claude    # process-count sanity, alongside the section 4 checks
```

**Why 3 and not a number derived from memory alone:** three is also the limit at which the conductor
can still answer each worker's design questions properly. The resource ceiling and the attention
ceiling happen to coincide. Raise it only from a measurement, never from optimism.

---

## 7. Bead IDs cannot be renamed, so the fix is presentational

**Trigger: you are tempted to make the IDs self-describing at the source instead of writing
`id - title` every time.**

`bd` has `rename-prefix`, which changes `jbrooksbartlett-` across the whole database, but nothing
per-issue. **The suffix is the primary key.** Changing it would break `discovered-from:` dependency
edges, the bead-to-session join keys written into notes, and every cross-reference.

So there is no source-level fix. The correction is presentational and it is the conductor's to apply
on every single mention - which is what
`~/.claude/docs/conductor-communication-contract.md` specifies, and what
`jbrooksbartlett-5r44` will eventually enforce automatically.

## 8. At startup, sweep every launchd job's exit status, not just your own

**Trigger: conductor startup. This is the one moment a conductor reliably reads this file, which is
the only reason the check belongs here rather than in a job that would have to remember to run it.**

```bash
launchctl list | awk 'NR>1 && $2 != 0 && $2 != "-"' | grep -v com.apple.
```

Column 2 is the last exit status. Apple's own agents are almost all `-9`, because launchd SIGKILLs
on-demand agents when it is done with them and that is normal, so **filtering `com.apple.` leaves a
signal where every remaining line is real.** Verified 2026-08-21 on this machine: the sweep returned
exactly one line.

**`NR>1` is load-bearing, not tidiness.** `launchctl list` prints a `PID Status Label` header, and
`Status` is neither `0` nor `-`, so without it the header passes the filter on every run. The check
would then print a line on a perfectly healthy machine, "no output means nothing is failing" would
stop being true, and the sweep would join the instruments in the last paragraph of this section. That
was a real defect in the first version of this line, caught twenty minutes after writing it.

**THE SHAPE THIS CATCHES, and it is not "a job crashed":** a job can be firing perfectly on its
timer, every fifteen minutes, for as long as you like, while its OUTPUT PATH is dead. The timer is
healthy. The work is not happening. Nothing in the job's own view is wrong enough to stop it.

That was the on-call goalie on 2026-08-21. Its tick fired on schedule and tried to nudge an
agent-deck session that had died with a session-fleet restart. Four consecutive failures, once every
fifteen minutes, each one written to `/tmp/oncall-goalie-tick.err` and to its own `tick.log`. The
skill documented that the tick "fails loudly rather than guessing" and it did exactly that - into two
files nobody opens. It was found because an unrelated session read the exit-status column of
`launchctl list` while looking for its own stray jobs, which is luck, not a process. This section is
the process.

**Report what you find even when it is not yours.** The conductor is the thing whose job is to
notice; a failing job in another skill's territory is still a failing job, and the owner is not
watching the column either.

**Do not diagnose from the exit code alone.** A non-zero status tells you the job's last run failed,
not why, and for a job whose output path is a live session the interesting failure is invisible from
launchd's side. Read the job's own stdout and stderr paths, which `launchctl print
gui/$(id -u)/<label>` gives you, before concluding anything.

**And do not trust an instrument that reports on a dead thing.** In that same incident four separate
instruments reported success over a dead tmux server: `agent-deck status` ("0 waiting, 0 running, 0
idle"), `agent-deck list`, the goalie's own stdout tick mark, and `agent-deck session show`, which
exits 0 and prints a full record for a session that is gone. Tracked as `jbrooksbartlett-9j7h`.
Confirming a delivery path works needs a delivery, not a status read.
