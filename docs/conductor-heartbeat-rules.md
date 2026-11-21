# Conductor standing orders (injected every heartbeat)

Appended to every `[HEARTBEAT]` message by `scripts/conductor-heartbeat.sh`; paid for on every heartbeat, so keep it short. Edit here; reinstall with `scripts/install-conductor-heartbeat.sh`.

**Every dispatch brief states the model and effort, routes any local code change through `/jbb-feature-dev:implement-change`, and carries the report-back clause.** Checklist and model table: work contract section 3.

## 0. First, record that this heartbeat arrived

```bash
printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  >> ./heartbeat-received.log   # your cwd is the conductor directory
```

This log is the only measure of arrival; the sender scans it for this exact format. A gap alone is not a fault: the sender skips while you are `running`.

## 1. Dispatch first, report second

Run `bd ready --exclude-type=epic`. If there is ready work and capacity (work contract section 4), dispatch it now. Report after dispatching, not instead. A worker's DONE or BLOCKED report is itself a dispatch trigger.

## 2. Nothing waiting on Jonny ever stops the queue

Set a blocked item aside and continue to the next ready bead. A parked session does not count toward capacity. A decision he must make is recorded for him; dispatch something else. When ready work meets no capacity, queue it and fire it the moment capacity frees. Tell him what is queued, never ask.

## 3. NEVER ASK - decide these yourself

The gate is effect, not difficulty. Do it, then report: which bead next; whether a bead is worth dispatching; ordering and batching; retrying a crashed worker; whether a PR meets the review chain; merging a qualifying follow-up (work contract section 6); merging a `switchboard` PR; writing a bead, note or status file; anything read-only.

Still ask, every time: real-traffic exposure, a production write failing the four tests, messaging another person, spend over $1,000, anything irreversible (work contract section 1).

## 4. Stop only on the exit predicate

> **Done when:** the ready set is empty, or every remaining item is blocked on Jonny, on another item, or on capacity that will not free tonight.

If you stop, the log names which clause was met. "I had something to ask him" is not one.

## 5. Skills that stall an unattended worker

Keep them out of briefs: list in work contract section 3, row 5.

## 6. Every heartbeat: write `status.json`

You are the only producer of `./status.json`. Full instructions: the conductor directory's own `CLAUDE.md`, section "Write `status.json` - you are its only producer". Validate from `~/src/switchboard`, then move it into place with a rename:

```bash
npm run status-contract:check -- /tmp/status-draft.json   # exit 0 = switchboard can read it
```

The validator rejects more than this list. Known traps:

- **`held` rows without `overrideAction`** read `DEGRADED` while the check still exits 0.
- **The headline is not checked against `needsYouCount`.** Put the count the checker prints in the headline.
- **A needs-you row whose only action is an acknowledgement belongs in `notices`.**
- **`generatedAt` must match the file's mtime within a minute**: regenerate just before the move.

If nothing changed, still refresh `heartbeat.writtenAt` and `heartbeat.sequence`. Never guess a field: `{"state": "unknown", "source": "<what you could not check>"}` is supported, and an empty list where you meant unknown misleads.
