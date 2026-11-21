# Conductor operations

Occasional procedures, each keyed to a trigger. Where this file disagrees with a contract, the contract wins.

## 1. Before running `agent-deck conductor setup hq`

**Trigger: you are about to run it.** It rewrites `hq/CLAUDE.md`, so every hand-edit there is at risk. `-instructions-md` SYMLINKS rather than copies, so a backup under `/tmp` vanishes on the next sweep, and `diff <backup> CLAUDE.md` returns clean because it compares the file to itself. Check the file type:

```bash
BK=~/.local/share/agent-deck/conductor/hq-CLAUDE.md.backup   # durable, never /tmp
cp ~/.local/share/agent-deck/conductor/hq/CLAUDE.md "$BK"
agent-deck conductor setup hq -instructions-md "$BK" -heartbeat
ls -la ~/.local/share/agent-deck/conductor/hq/CLAUDE.md      # MUST be -rw-, not lrwx-
```

If it came back a symlink, replace it with a real file: `cp "$BK" CLAUDE.md.realfile && rm CLAUDE.md && mv CLAUDE.md.realfile CLAUDE.md` in the hq directory.

## 2. Forking a session

**Trigger: you are considering `agent-deck session fork` instead of `agent-deck launch`.** Fork works only when `tool` is claude, opencode, pi or codex AND `claude_session_id` is present (`agent-deck session show --json <origin>`). `can_fork` is omitted entirely when false: absence is a no. Otherwise launch, and make the bead self-contained.

## 3. Claims and leases, and the heartbeat interval

**Trigger: you are thinking of wiring a `bd reclaim` timer, changing the claim TTL, or asking workers to heartbeat.** `bd update --claim` takes a ~5-minute lease and nothing renews or reaps it, so a lapsed lease is inert. A reclaim timer added without first raising `claim.ttl` well above the heartbeat interval would yank running work back to ready and dispatch it twice. Judge liveness from agent-deck or the remote runtime, never from a lease.

The real heartbeat interval is the launchd plist's `StartInterval` (or the systemd timer on Linux), never `meta.json`'s `heartbeat_interval`. `scripts/install-conductor-heartbeat.sh` prints it.

## 4. Reconnecting beads and sessions

**Trigger: after a restart, or when a bead and a session disagree.** They are joined only by convention: the bead's notes carry the session title, id and worktree; the child's `parent_session_id` must be the conductor's id, or completion events never arrive. Reconnect with `bd list --status in_progress`, read each bead's session id, then `agent-deck session show --json <id>`. `in_progress` with the session missing or `error` is orphaned work; confirm any `error` by advancement (work contract section 9) first.

**Suspected context loss after a resume:** one wrong answer proves nothing; check the transcript's `parentUuid` chain. `session show --json` re-derives `claude_session_id` when the stored value is missing, so it cannot prove the id survived; query the sqlite `tool_data` column.

Bead IDs cannot be renamed per issue (`bd rename-prefix` is database-wide and breaks edges and notes), so always write `id - title`.
