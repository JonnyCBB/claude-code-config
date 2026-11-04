# conductor-signals: the three work-contract success signals

`scripts/conductor-signals.sh` prints the three signals in [the work contract](conductor-work-contract.md) section 10 as three numbers. Run it at heartbeat time. It reads; it never writes the queue, dispatches, or closes anything.

```bash
~/.claude/scripts/conductor-signals.sh            # adds a 20s swapouts sample
~/.claude/scripts/conductor-signals.sh --fast     # skips it
~/.claude/scripts/conductor-signals.sh escalate 6 "asked to merge a follow-up PR"
```

Needs bash 4+ (the shebang finds Homebrew's), plus `bd`, `gh`, `jq` and `agent-deck` on PATH. `--fast` takes ~35s wall, mostly waiting on the git host; treat any single timing as noise (`hq-6i7q`). It is not a dashboard: driving the system beats watching it.

**Stale against the work contract.** The script still gates on a cap of 3 and the swap-free veto, which contract section 4 has replaced (no numeric cap; swap-free dropped). Signal 2 is computed against those old limits until the script is updated.

## A zero always says whether it was measured

| Renders as | Means |
| --- | --- |
| `5` | a real measurement |
| `>=5` | measured, but blind somewhere: a floor |
| `?` | could not be measured at all |

All three signals target 0, so a `0` that means "I did not look" is worse than no signal. Every read is checked; any failure prints a `NOT A CLEAN READ` banner above all three numbers naming what failed.

| Read that failed | Effect |
| --- | --- |
| `bd list` | signal 1 `?` |
| a repo path missing, or its PR list unreadable | signal 1 `>=` |
| `agent-deck list` | signal 2 `?`, signal 1 `>=` (live worker repos undiscovered) |
| one worker session whose branch will not resolve | signal 2 `>=` (counted active) |
| `bd list --label signal1-ack` | signal 1 keeps a number, banner says dismissed hits may reappear (inflates rather than zeroes) |
| `bd ready` | signal 2 `?` |
| the capacity read | signal 2 `?` |
| the escalation log unreadable or unparseable | signal 3 `?` |

"The git host was unreachable" must never render as "no complete-but-open beads".

## Signal 1: complete but open

Target 0. "Complete" is not a bd status, so it is inferred: **a merged PR, plus one side saying in words that the PR closes the bead.**

| Rule | Fires when |
| --- | --- |
| `pr-declares` | the merged PR's title, branch or body closes the bead in words ("Closes `hq-lzih`") |
| `bead-declares` | a closure verb sits within 40 characters *before* a PR reference in the bead's own prose ("RESOLVED BY switchboard PR #27") |

Shared verbs: `close/closes/closed/closing`, `fixes/fixed`, `resolve/resolves/resolved`. Bare `fix` is excluded (it opens every conventional-commit subject). Both drop a match whose clause carries a negator ("It does not close hq-av0"). Details of the guard, each forced by a live case:

1. **Per clause, not per document**, or an incidental "cannot resolve which" elsewhere silences a genuine hit.
2. **A dot followed by a digit is not a clause break** (bead ids carry dots: `-w45.20`).
3. **`cannot` and `unable` are separate words**; the letter before `not` in `cannot` defeats the word boundary.
4. **"until" survives the guard**: "Do not close it until PR 142 merges" records a pending closure the merge has now met.

`bead-declares` additionally requires the verb *before* the reference.

**When a hit is right but the bead should stay open:** `bd label add <id> signal1-ack`. Without it a bead left open after a partial merge is permanent noise and the number stops being read.

**Known blind spot**, printed in the script's output: beads that complete without a PR (research, operator actions, work split across PRs where none declares closure) (`hq-uixd`). False positives are low but not zero; each hit is a fifteen-second worklist entry, not a verdict.

**Detections tried and rejected** (all "checks that cannot stop firing"): `in_progress` with no agent-deck session (precision ~25%; absence means abandoned, remedy `bd reclaim`); `in_progress` with an expired lease (fired on 11 of 12; nothing calls `bd heartbeat`, so the lease is always `started_at + 5min`); a bead and merged PR citing each other (~2 of 12 correct; mutual citation is the signature of a follow-up).

## Signal 2: ready work idle while capacity is free

Target 0. The number is how many dispatches should happen right now:

```
signal 2 = resources_ok && free > 0  ?  min(ready, free)  :  0
free     = cap(3) - active
```

`ready` is `bd ready --exclude-type=epic`. `active` and `parked` follow contract section 4: a worker whose branch has an open PR is parked and does not count.

An unreadable capacity read is a **veto**, not a pass. An unreadable **session list** counts as fully occupied, not zero sessions, so signal 2 never urges dispatch past real workers.

**The capacity read reports two answers on purpose.** The script's veto is memory >= 25% free, swap >= 2000M free, 1-min load < 9. Swap free is a high-water mark (macOS grows the swap file and never shrinks it), so it can veto a machine that is not paging. `hq-cjxs` proposes replacing it with the swapouts delta and is deferred pending Jonny. The script reports both, the agreed threshold governs the veto, and when they disagree it says so. `--fast` skips the sample and says so in the line where the check would be, since silence would read as agreement.

Wiring: nothing runs this yet; `heartbeat.sh` does not call it (`hq-3798`).

## Signal 3: escalations that the contract already answered

Target: trending down. Only the conductor knows it escalated something it had authority to decide, so it increments a counter itself:

```bash
conductor-signals.sh escalate 6 "asked whether to merge a follow-up PR passing all four tests"
```

Appended to `${XDG_STATE_HOME:-~/.local/state}/conductor-signals/escalations.jsonl`, outside any git-pushed directory and not in `state.json` (`agent-deck conductor setup hq` rewrites that directory, and a counter a re-run can erase cannot measure a trend). The write reports failure rather than printing "recorded" regardless. The report shows today's count, the contract sections that should have applied, and the prior seven days' average.

## Configuration

| Variable | Default | |
| --- | --- | --- |
| `CONDUCTOR_SIGNALS_REPOS` | `~/.claude`, `~/src/switchboard`, `~/src/beads-hq` | Colon-separated. Live worker repos are added automatically; defaults never drop out, because a repo whose sessions are all retired is where a merged-but-open bead hides |
| `CONDUCTOR_SIGNALS_CAP` | `3` | Active-session cap |
| `CONDUCTOR_SIGNALS_SWAP_VETO_MB` | `2000` | The contested threshold |
| `CONDUCTOR_SIGNALS_MEM_FREE_MIN_PCT` | `25` | |
| `CONDUCTOR_SIGNALS_LOAD_MAX` | `9` | |
| `CONDUCTOR_SIGNALS_PR_DAYS` | `14` | How far back to read merged PRs |
| `CONDUCTOR_SIGNALS_PR_LIMIT` | `40` | Merged PRs fetched per repo |
| `CONDUCTOR_SIGNALS_SAMPLE_SECONDS` | `20` | Swapouts sample window, also `--sample-seconds` |
| `CONDUCTOR_SIGNALS_STATE_DIR` | `$XDG_STATE_HOME/conductor-signals` | Escalation log location |

`--resources-from <file>` replaces the live capacity read with a captured one, to exercise the veto and disagreement paths.
