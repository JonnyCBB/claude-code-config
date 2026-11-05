# Conductor standing orders (injected every heartbeat)

Appended to every `[HEARTBEAT]` message by `scripts/conductor-heartbeat.sh`. Keep it short: it is paid for on every heartbeat. Edit here; reinstall via `scripts/install-conductor-heartbeat.sh`.

---

## 0. First, record that this heartbeat arrived

```bash
printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  >> ./heartbeat-received.log   # your cwd is the conductor directory
```

The sender sends with `-q` and logs only failures, so this log is the only measure of arrival. Read the real interval from the plist, never from `meta.json` (its `heartbeat_interval: 0` is wrong):

```bash
awk '/StartInterval/{getline; gsub(/[^0-9]/,""); print $0" seconds"; exit}' \
  ~/Library/LaunchAgents/com.agentdeck.conductor-heartbeat.$(basename "$PWD").plist
```

Materially fewer receipts than the interval predicts means delivery is dropping (`hq-8ytz2`). A gap alone is not a fault: the sender skips while you are `running`.

## 1. Dispatch first, report second

```bash
bd ready --exclude-type=epic
```

If there is ready work and capacity, dispatch it now. Do not suggest it or defer it. Report after dispatching, not instead.

## 2. Nothing waiting on Jonny ever stops the queue

A blocked item is set aside; the run continues to the next ready bead until the ready set is empty or every remaining item is genuinely blocked. This covers:

- A **session parked** on a PR awaiting review or merge: it does not count toward capacity.
- A **decision** he has to make: record it for the morning and dispatch something else.
- An **escalation** already sent: it stays `deferred`; keep going.

When ready work meets no capacity, queue it and fire the instant capacity frees. He is told what is queued and why, never asked.

## 3. NEVER ASK - decide these yourself

The gate is effect, not difficulty. A hard decision with a reversible effect is still yours.

| Do not escalate | Do it, then report |
| --- | --- |
| Which ready bead to dispatch next | Dispatch it |
| Whether a bead is worth dispatching | Decide; if unclear, park it and take the next |
| Ordering, sequencing, batching | Choose an order |
| Retrying a failed or crashed worker | Retry it |
| Whether a PR meets the review chain | Apply the chain; send it back if not |
| Merging a qualifying follow-up | Merge it (work contract section 6) |
| Merging a `switchboard` PR | Merge it (standing grant) |
| Writing a bead, note, or status file | Write it |
| Anything read-only | Do it |

Still ask, every time: real-traffic exposure (experiments, ramps, variants), production writes, messaging another person, spend over $1,000, anything irreversible. Full gate: work contract section 1.

## 4. Stop only on the exit predicate

> **Done when:** the ready set is empty, or every remaining item is blocked on Jonny, on another item, or on capacity that will not free tonight.

A hard question or a plateau is not the predicate. If you stop, the log must show which clause was met; "I had something to ask him" is not one.

## 5. Five skills stall an unattended worker. None has a flag.

Keep them out of dispatch specs; a worker that reaches one waits until morning:

| Skill | Why it stalls |
| --- | --- |
| `/crit-pr-review`, `/crit` | Block until a human clicks "Finish Review" in a browser |
| `/frontend-slides` | Three unconditional `AskUserQuestion` calls |
| `/teach-me` | Asks the user to pick a theme |

Use the built-in `/code-review` at a named effort level instead of the crit pair. Do not dispatch work routed through the other two. One conditional gate: always pass a register to `/sound-like-me` (e.g. `--register=github-pr-body`), or it asks which surface and stops.

## 6. Every heartbeat: write `status.json`

You are the only producer of `./status.json` (in the conductor directory); switchboard shows "I cannot see into the conductor" while it is absent. Full instructions: the conductor directory's own `CLAUDE.md` (not this repo's), section "Write `status.json` - you are its only producer". Validate from `~/src/switchboard`:

```bash
npm run status-contract:check -- /tmp/status-draft.json   # exit 0 = switchboard can read it
```

Then move it into place with a rename, never by writing over the live path. The validator rejects things the prose does not spell out; run it, do not treat this list as complete:

- **`held` rows require `overrideAction`.** Without it the section reads `DEGRADED` while the file still exits 0.
- **Session entries require `livenessSignals` and `stopReasonSentence`.**
- **`stopReason.value` is a closed enum**: `asked-a-question`, `hit-a-permission-prompt`, `finished-the-turn`, `errored`, `still-working`.
- **A needs-you row whose only action is an acknowledgement belongs in `notices`.**
- **`generatedAt` must match the file's mtime within a minute**, so regenerate immediately before the atomic move.
- **The headline is free text and not checked against `needsYouCount`.** Put the count the checker prints in the headline.

If nothing changed, still refresh `heartbeat.writtenAt` and `heartbeat.sequence`; switchboard uses them to detect staleness. Never guess a field to avoid leaving it unknown: `{"state": "unknown", "source": "<what you could not check>"}` is a supported answer. An empty list where you meant unknown tells Jonny nothing is waiting on evidence nobody has.
