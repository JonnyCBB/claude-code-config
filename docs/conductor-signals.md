# conductor-signals: the three work-contract success signals

`scripts/conductor-signals.sh` prints the three signals in
[the work contract](conductor-work-contract.md) section 10 as three numbers. Run it at heartbeat
time. It reads; it never writes the queue, dispatches, or closes anything.

```bash
~/.claude/scripts/conductor-signals.sh            # adds a 20s swapouts sample
~/.claude/scripts/conductor-signals.sh --fast     # skips it
~/.claude/scripts/conductor-signals.sh escalate 6 "asked to merge a follow-up PR"
```

Needs bash 4+ (macOS `/bin/bash` is 3.2; the shebang finds Homebrew's), plus `bd`, `gh`, `jq` and
`agent-deck` on PATH.

Measured `--fast` on the real queue: ~9.5s CPU, ~35s wall - of which about 22s is waiting on
github.com, and that latency is wildly variable (the same three `gh pr list` calls measured
4.9s and 15.4s minutes apart on an otherwise unchanged machine). Treat any single timing here as
noise. `jbrooksbartlett-6i7q` records what it would take to make it faster and why that was not
done.

It is not a dashboard. `jbrooksbartlett-bzc5` measured that driving the system beats watching it,
so a second thing to watch would be a regression. Three numbers, each with the evidence behind it,
and every one of them actionable in the same minute you read it.

## A zero always says whether it was measured

Every number renders in one of three forms, and the difference is visible without reading further:

| Renders as | Means |
| --- | --- |
| `5` | a real measurement |
| `>=5` | measured, but blind somewhere - a floor, so the true number may be higher |
| `?` | could not be measured at all |

This is the point of the whole script. All three signals target 0, so a `0` printed beside
"target 0" reads as reassurance - and a `0` that actually means "I did not look" is worse than no
signal, because it is reassurance that nothing is wrong. Every read is checked, any failure prints
a `NOT A CLEAN READ` banner above all three numbers naming exactly what could not be read, and the
affected numbers carry `>=` or `?`.

What degrades what:

| Read that failed | Effect |
| --- | --- |
| `bd list` (the bead set) | signal 1 `?` - with no beads there is nothing to match PRs against |
| a repo path missing, or its PR list unreadable | signal 1 `>=` - some PRs were searched, not all |
| `agent-deck list` (the session list) | signal 2 `?`, and signal 1 `>=` because live worker repos go undiscovered |
| one worker session whose branch will not resolve | signal 2 `>=` - it is counted active, which under-estimates free capacity |
| `bd list --label signal1-ack` | signal 1 keeps a plain number but the banner says dismissed hits may reappear: this read failing INFLATES the count rather than zeroing it, which neither `>=` nor `?` describes |
| `bd ready` | signal 2 `?` |
| the capacity read | signal 2 `?` |
| the escalation log unreadable or unparseable | signal 3 `?` |

## Signal 1: complete but open

Target 0. This is the failure Jonny named as the worst thing we can do.

"Complete" is not a bd status, so it has to be inferred. The rule is: **a merged PR, plus one side
or the other saying in words that the PR closes the bead.**

| Rule | Fires when | Example from the real queue |
| --- | --- | --- |
| `pr-declares` | the merged PR's title, branch or body closes the bead in words | PR #151: "Closes `jbrooksbartlett-lzih` (P0)." |
| `bead-declares` | a closure verb sits within 40 characters *before* a PR reference in the bead's own prose | `whd0`: "RESOLVED BY switchboard PR #27." |

Both rules share a verb list - `close/closes/closed/closing`, `fixes/fixed`,
`resolve/resolves/resolved`. Bare `fix` is excluded: it opens every conventional-commit subject and
carries no completion claim.

Both also drop a match whose clause carries a negator. That is not defensive programming - SEAL PR
#146 reads "This is a PARTIAL fix. **It does not close jbrooksbartlett-av0.**", and bead `quiet7`'s
real-world shape is "This is NOT resolved by PR #99." Without the guard the signal reports the one
bead whose author went out of their way to say it stays open.

Four details of that guard, each forced by a case in the live queue:

1. **The guard is per clause, not per document.** Bead `whd0` says "RESOLVED BY switchboard PR #27"
   and, in an unrelated sentence far away, "...cannot resolve which. WHY PR #27...". A
   whole-document guard silenced a genuine hit on an incidental phrase.
2. **A dot followed by a digit is not a clause break**, because bead ids carry dots (`-w45.20`) and
   splitting there would let `-w45` match inside one.
3. **`cannot` and `unable` are separate words**, not reachable through `not`, because the
   letter before `not` in `cannot` defeats the boundary. switchboard PR #30 pastes a UI error into
   its body - "cannot close jbrooksbartlett-0s2: 7 open child issue(s); close children first" - and
   that bead has seven open children. Only the live run caught it.
4. **"until" survives the guard.** "Do not close it until PR 142 merges" is how this queue records a
   *pending* closure - a conditional whose condition the merge has now met. That is bead `mqv`,
   three days stale with six dependents blocked, and a naive negation guard loses it.

`bead-declares` additionally requires the verb *before* the reference: `vgzl` reads "THE 2mdh JUnit
FIX (PR #27) DOES NOT RESOLVE THIS BEAD. Leave it standing."

### When a hit is right but you want it to stay open

```bash
bd label add <id> signal1-ack
```

Without this the one action the report recommends cannot silence the report, and a bead legitimately
left open after a partial merge becomes permanent noise at every heartbeat - which is how a number
stops being read.

### When it cannot see

**Every** read distinguishes "could not read" from "read a clean zero", and any failure prints
`NOT A CLEAN READ` above all three numbers, names the read that failed, and marks the affected
signals `>=` or `?` (see "A zero always says whether it was measured"). "GHE was
unreachable" must never render as "no complete-but-open beads" - GHE was down for about 16 hours on
2026-08-15/16 - and neither must a locked bd or a crashed agent-deck.

That guard started out covering only the merged-PR read. Review found `bd list`, `bd ready` and
`agent-deck list` all still reporting a confident zero on failure, and one live run had already
done it: 0 complete-but-open beads when the true answer was 5, because bd returned a short array
and nothing noticed. A configured repo path that does not exist is reported too, rather than
skipped.

### Measured rates

Run against the live queue on 2026-08-18 - 425 non-closed beads, ~120 merged PRs across three
repos:

- **5 hits, 5 of them genuine.** `lzih` (4 dependents blocked), `mqv` (6 dependents, merged three
  days earlier), `5nc`, `whd0`, `yloo`. Each was verified by hand against its PR.
- **False positives expected: low but not zero.** The rules trust an author's words. A PR that says
  "Closes X" and then only half-closes X will be reported. That is the right way round: each hit is
  a worklist entry costing about fifteen seconds to judge, not a verdict.
- **False negatives: one whole class, structurally.** Beads that complete without a PR - research
  ending in a document, operator actions, work split across several PRs where none declares
  closure. The script prints this blind spot in its own output. Tracked as `jbrooksbartlett-uixd`.

### Three detections that were tried and rejected, with the measurements

Recorded so nobody rebuilds them. All three are the "check that cannot fail" shape, arrived at from
the opposite direction - checks that cannot *stop* firing.

1. **A bead `in_progress` whose agent-deck session no longer exists.** Fired on 8 of 12
   `in_progress` beads; 2 were genuinely complete. Precision ~25%. Session absence means *abandoned*
   far more often than *complete*, and the remedy for abandoned is `bd reclaim`, not `bd close`.
2. **A bead `in_progress` whose lease has expired.** Fired on 11 of 12. bd leases run 5 minutes and
   nothing in this rig ever calls `bd heartbeat`, so `lease_expires_at` is only ever
   `started_at + 5min`. It measures nothing about the worker.
3. **A bead and a merged PR that cite each other.** Fired on 12 beads, ~2 correct. Mutual citation
   is the signature of a *follow-up*: the follow-up bead records the PR it was discovered from, and
   the PR records the follow-ups it filed. This is the rule the script shipped with for one
   iteration, and the live run is what killed it.

## Signal 2: ready work idle while capacity is free

Target 0. The number is how many dispatches should happen right now:

```
signal 2 = resources_ok && free > 0  ?  min(ready, free)  :  0
free     = cap(3) - active
```

`ready` is `bd ready --exclude-type=epic` - epics are never startable. `active` and `parked` follow
contract section 4: a worker session lives in a git worktree, and one whose branch has an **open
PR** is parked, so it does not count against the cap.

An unreadable capacity read is treated as a **veto**, not a pass. Before that guard a changed
`memory_pressure` wording parsed to empty, defaulted to 0, and became a permanent silent veto
indistinguishable from real exhaustion - or, with the thresholds skipped, let signal 2 fire having
checked nothing.

An unreadable **session list** is likewise not zero sessions. `agent-deck` failing used to mean
`active 0`, so the whole cap read as free and signal 2 would urge dispatch while real workers were
running - the one direction that can actually break the cap of 3. It now counts as fully occupied
and says so.

### The capacity read reports two answers on purpose

The contract's veto is memory >= 25% free, swap >= 2000M free, 1-min load < 9, and the swap
threshold is the one that bites. It is also a **high-water mark**: macOS grows the swap file and
never shrinks it, so one bad afternoon leaves the machine reading vetoed indefinitely. Measured
2026-08-18 13:30 - swap free 1113M (a hard veto) while memory was 50% free, load 2.87, and the
`vm_stat` Swapouts delta over 20 seconds was **zero**. Nothing was paging.

`jbrooksbartlett-cjxs` proposes replacing the swap read with the swapouts delta and is **deferred
pending Jonny**, because changing a threshold he agreed is his call. So the script reports both,
the agreed threshold still governs the veto, and when the two disagree it says so and names the
bead. It does not quietly drop the rule.

`--fast` skips the sample, so the disagreement check cannot run. The script says that in the line
where the check would have gone, rather than omitting it - an absent note would read as "the two
readings agree", which is the false-veto the machinery exists to defuse.

### Wiring

Nothing runs this yet. Contract section 10 still says "not instrumented yet", `heartbeat.sh` does
not call it, and `HEARTBEAT_RULES.md` does not exist. That gap is `jbrooksbartlett-3798`; it needs
an edit to the contract, which was being edited by hand while this landed.

## Signal 3: escalations that the contract already answered

Target: trending down. This one cannot be automated - only the conductor knows it escalated
something it had the authority to decide. So it is a counter the conductor increments itself:

```bash
conductor-signals.sh escalate 6 "asked whether to merge a follow-up PR passing all four tests"
```

Appended to `${XDG_STATE_HOME:-~/.local/state}/conductor-signals/escalations.jsonl`, outside any
git-pushed directory.

**Not `state.json`, which is what the bead asked for.** That file lives in
`~/.local/share/agent-deck/conductor/hq/`, which `agent-deck conductor setup hq` rewrites - the same
reasoning the work contract gives for why the contract itself does not live there. A counter that
can be erased by a setup re-run cannot measure a trend. The write also reports failure rather than
printing "recorded" regardless: this is the only signal a human supplies and a dropped escalation
is unrecoverable. The report shows today's count, the contract sections that should have been
applied, and the prior seven days' daily average to make the trend visible.

## Configuration

| Variable | Default | |
| --- | --- | --- |
| `CONDUCTOR_SIGNALS_REPOS` | `~/.claude`, switchboard, beads-hq | Colon-separated. Live worker repos are added automatically; the defaults never drop out, because a repo whose sessions have all been retired is exactly where a merged-but-open bead hides |
| `CONDUCTOR_SIGNALS_CAP` | `3` | Active-session cap |
| `CONDUCTOR_SIGNALS_SWAP_VETO_MB` | `2000` | The contested threshold. Named so a decision on `jbrooksbartlett-cjxs` changes one thing |
| `CONDUCTOR_SIGNALS_MEM_FREE_MIN_PCT` | `25` | |
| `CONDUCTOR_SIGNALS_LOAD_MAX` | `9` | |
| `CONDUCTOR_SIGNALS_PR_DAYS` | `14` | How far back to read merged PRs |
| `CONDUCTOR_SIGNALS_PR_LIMIT` | `40` | Merged PRs fetched per repo |
| `CONDUCTOR_SIGNALS_SAMPLE_SECONDS` | `20` | Swapouts sample window, also `--sample-seconds` |
| `CONDUCTOR_SIGNALS_STATE_DIR` | `$XDG_STATE_HOME/conductor-signals` | Where the escalation log lives |

`--resources-from <file>` replaces the live capacity read with a captured one, which is how the
tests exercise the veto and disagreement paths.

## Tests

```bash
bash scripts/tests/test-conductor-signals.sh                       # 67 assertions
EXPECT_BOOTSTRAP_RED=1 bash scripts/tests/test-conductor-signals.sh # must exit 1
```

Every signal has both a case that must fire and a case that must stay silent, and each silent case
is built from the real text that produced it.

Two things in the harness are there because they caught something:

- **The bootstrap-RED sentinel.** This repo runs no CI (`jbrooksbartlett-sqmi`), so this suite is
  the only gate, and a harness that recorded zero assertions would print `0 passed, 0 failed` and
  exit 0. The sentinel forces a deliberate failure to prove the harness can report one.
- **Fixture JSON validation before every run.** A trailing comma in `gh-merged.json` once made the
  script report zero signal-1 hits, which reads exactly like a clean queue. The same shape as the
  defect the script itself now guards against with `NOT A CLEAN READ`.

`bd`, `gh` and `agent-deck` are stubbed on PATH; the worker worktrees are real git repos, so branch
resolution under test is the real `git rev-parse`.
