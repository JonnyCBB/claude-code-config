# conductor-signals: the three work-contract success signals

`scripts/conductor-signals.sh` prints the three signals in [the work contract](conductor-work-contract.md) section 10. It only reads; it never writes the queue, dispatches or closes.

```bash
~/.claude/scripts/conductor-signals.sh            # adds a 20s swapouts sample
~/.claude/scripts/conductor-signals.sh --fast     # skips it (~35s, mostly the git host)
~/.claude/scripts/conductor-signals.sh escalate 6 "asked to merge a follow-up PR"
```

Needs bash 4.3+ (the shebang finds Homebrew's), plus `bd`, `gh`, `jq` and `agent-deck` on PATH. Nothing runs it automatically yet.

**Signal 2 is stale against the work contract.** The script still computes free capacity as a cap of 3 minus active sessions, and vetoes on memory >= 25% free, swap >= 2000M free and load < 9. Contract section 4 has no numeric cap and does not veto on swap. Read signal 2 as a hint, not a measurement, until the script changes.

## Reading the numbers

| Renders as | Means |
| --- | --- |
| `5` | a real measurement |
| `>=5` | measured, but blind somewhere: a floor |
| `?` | could not be measured |

Any failed read prints a `NOT A CLEAN READ` banner naming what failed. A `0` under that banner is not a zero.

**Signal 1 (complete but open)** fires on a merged PR plus words on either side saying the PR closes the bead. Each hit is a worklist entry, not a verdict. If a hit is right but the bead should stay open, run `bd label add <id> signal1-ack`, or it reappears every run. Blind spot: beads that complete without a PR.

**Signal 3 (escalations the contract already answered)** is counted only by the conductor itself: run `escalate <section> "<what>"` each time it asked Jonny something the contract let it decide. The log is `${XDG_STATE_HOME:-~/.local/state}/conductor-signals/escalations.jsonl`, outside `state.json` so a setup re-run cannot erase it.

## Configuration

`CONDUCTOR_SIGNALS_REPOS` (colon-separated; default `~/.claude`, `~/src/switchboard`, `~/src/beads-hq`; live worker repos are added automatically), `CONDUCTOR_SIGNALS_CAP` (3), `CONDUCTOR_SIGNALS_SWAP_VETO_MB` (2000), `CONDUCTOR_SIGNALS_MEM_FREE_MIN_PCT` (25), `CONDUCTOR_SIGNALS_LOAD_MAX` (9), `CONDUCTOR_SIGNALS_PR_DAYS` (14), `CONDUCTOR_SIGNALS_PR_LIMIT` (40), `CONDUCTOR_SIGNALS_SAMPLE_SECONDS` (20), `CONDUCTOR_SIGNALS_STATE_DIR`. `--resources-from <file>` replaces the live capacity read with a captured one.
