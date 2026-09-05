# Mandate Partitioning

How a component's source surface becomes finder mandates. `SKILL.md` section 4
points here and does not restate any of it.

**The rule: partition by file SIZE and never by package, to a TARGET SIZE and
never to a fixed count.** ~500 lines per mandate. The mandate count falls out of
the component rather than being imposed on it -- a 1,500-line component yields 3
mandates, an 11,000-line one yields ~22.

Both halves are measured, and the package half is the older of the two: package-
shaped partitions were tried and failed, because packages vary in size by an order
of magnitude and on the measured component the defect sat in the single largest
file. `design-history-and-failed-approaches.md` section 1 records it. Size is the
best cheap proxy for where path-sensitive divergences hide.

## Why a fixed count was wrong, measured

A `max=8` cap stood in `SKILL.md` section 4 and produced this on an 11,181-line,
178-file component:

| Mandate type   | Lines | Files | Packets | Yield per 1k lines |
| -------------- | ----- | ----- | ------- | ------------------ |
| Solo (4)       | 1,222 | 4     | 7       | **5.73**           |
| Bin-packed (4) | 9,959 | 174   | 5       | **0.50**           |

An **11x gap in yield density**, from one run, same component, same finder agent,
same prompt shape. Four finders read ~306 lines each; four read ~2,490 each.

**The confound, stated honestly.** Solo mandates got the component's _largest_
files, and large files may genuinely carry more defects, so the 11x is not purely
attention dilution. But it does not explain a gap that size. The bin finders'
Coverage records are full of `reviewed, no candidate` against files of 150-230
lines -- the same size band that yielded 7 packets when a finder had one file and
its context to think about. One bin finder read a 225-line file and returned 1
packet while also reading 42 other files; a solo finder read a 243-line file and
returned 2.

The cap is retired. Do not reintroduce it, and do not reintroduce it in disguise
as "cap the count, then bin-pack the remainder" -- that is the same failure with
a different arithmetic.

## The floor, and why one exists

**Do not target much below ~250 lines.** Smaller is not monotonically better:

- Per-finder context re-reading (interfaces, callers, config, tests) is roughly
  fixed. Below ~250 lines of target code it dominates the finder's budget.
- More defects fall _across_ mandate boundaries. A finder's contract requires the
  candidate to live inside its mandate, and `grouping-rule.md` breaks ties toward
  **not** grouping, so a defect split across two mandates is more likely lost than
  reassembled.

~500 sits well above that floor. It is NOT the measured optimum: the 5.73
packets/1k figure was measured at ~306 lines, and 500 is an extrapolation from it
rather than a second measurement. It was raised from 300 after a run on an
11,181-line component returned **146 candidates from 42 finders** -- far past what
a reader or a verification budget can absorb, and past the point where more recall
is the binding problem. What would falsify the choice: a run at 500 whose yield
density falls near the 0.50 packets/1k the old 2,490-line bins produced, which
would mean 500 has crossed into the dilution band and the floor is higher than 250. Measure it before raising further.

## The algorithm

Deterministic, so two runs on one component partition identically and can be
compared:

1. Rank files by line count, descending.
2. **Never split a file across mandates.** A file is the smallest unit.
3. Any file at or above the target becomes its own mandate.
4. Greedy bin-pack the remainder: each file joins whichever open mandate currently
   holds the fewest lines.

Step 3 means a 426-line file gets a mandate to itself rather than being padded to
exactly 300. Overshoot on a single large file is fine; the target governs the
_bins_, which is where dilution actually happened.

## Batching

Mandate count now routinely exceeds what can run at once. Dispatch in batches of
`parallelism`, **default 10**, caller-overridable.

Within a batch, all Agent calls go in **one message** -- that is the only thing
that makes them parallel; one call per message runs them in series. Across
batches, wait for the batch to complete before dispatching the next.

A batched run is not a bounded run. Every mandate is dispatched; batching changes
only how many are in flight. Nothing here caps coverage, and nothing here changes
whether the automatic ceiling in `bounded-verification.md` applies.

## Project the cost before dispatching, and say it out loud

Once the partition exists the finder count is known, so the run can price itself
**before** spending anything. Run the script; do not re-derive the arithmetic here:

    python3 scripts/project_cost.py --finders <len(mandates) + len(LENSES)> \
        [--candidates-per-finder <density>]

Report its output in the run summary before the first batch. When it says the run
will degrade, **say so plainly** and name the options -- bound it, split the
component, or accept a partial run -- rather than discovering it at the verification
stage.

**Supply `--candidates-per-finder` when you have a comparable prior run on the same
component**, because it is the dominant input. Without it the script uses a prior
range and widens the band, which is the honest representation of not knowing.

### Why this is a script and why the old one-line formula was wrong

The projection used to read `packet_mb = finders * 0.055`. That is a single term
keyed on finder count, and it is wrong in a way that does not announce itself:
**roughly 90% of returned packet volume scales with candidates FOUND, not with the
number of finders looking.** Two components with identical file counts and identical
partitions return very different volumes if one is buggier, and the old formula
projected them identically. It also reported 55KB per finder where the run it was
calibrated on measured 68.7KB -- understating by about a quarter on its own source.

`scripts/project_cost.py` models both terms, reports a range rather than a point, and
keys the degradation warning to **projected volume rather than finder count** -- a
dozen finders on a very dense component can exceed the budget while a warning keyed
to "roughly 30 finders" stays silent.

It is a script rather than prose for the same reason: a formula a run acts on must be
executable and assertable. The section immediately below still names `index_to_disk`,
which was left as pseudocode and consequently **shipped defined nowhere** -- a run
following that prose accumulated packets in context exactly as if the instruction had
been absent. `scripts/test_project_cost.py` exists so this one cannot go the same way.

**The coefficients come from ONE run and cannot currently be re-derived.** The finder
holds no `Write` tool, so packets returned through the orchestrator's context and were
never persisted; that context is gone, and four separate sources were checked on
2026-08-28 before concluding it. Improving them requires a run performed *with* the
disk index, not further analysis of the existing one. The script records this in its
`CALIBRATION` block and reports its basis as `ESTIMATED`; treat the expected value as
the middle of a wide band, not a number to plan against.

This exists because the failure is silent. The measured run dispatched 42 finders,
completed every one successfully, and only then ran out of room; nothing in the
output said "this is about to go wrong", so a reader would have concluded the
component simply had 141 unchecked candidates. A projection that is occasionally
pessimistic is worth far more than a run that degrades without saying so.

## The cost this moves rather than removes

Finders are the cheap half **in agents, and this is the sentence that misleads.**
Verification is 3 agents per candidate, so higher finder recall raises verification
cost proportionally -- a component going from 12 to 30 candidates goes from ~36 to
~90 verification agents.

**But the binding constraint is the orchestrator's context, not the agent count,
and nothing else in this skill prices it.** A Finder Packet carries a full Coverage
record and sweep table. Their measured mean and observed maximum are the `FIXED_KB_PER_FINDER`/`KB_PER_CANDIDATE`/`OBSERVED_MAX_KB_PER_FINDER` constants in `scripts/project_cost.py`, which is canonical; do not restate them here. The finder has
no `Write` tool -- so **every packet returns through the orchestrator's context.**
(That absence was once justified as what makes the zero-outbound guarantee structural.
It is not: the finder also holds `Bash`, which can write anywhere `Write` can. What
actually keeps the guarantee is the absence of outbound MCP tools.) At 42
finders that is ~2.8MB before a single verifier runs (recompute with
`scripts/project_cost.py` rather than from a figure written here -- this sentence
carried ~2.3MB until 2026-08-28, computed with the superseded 55KB-per-finder
coefficient, and went stale the moment that constant was corrected), and the measured
outcome was
an orchestrator that reached the verification stage with too little context left to
use it: 5 of 22 selected candidates verified, the rest deferred for a reason that
had nothing to do with their band.

Two consequences, both binding:

- **Index each batch to disk as it lands, and do not carry packets forward.**
  Extract the machine-read fields (fingerprint, defect site, one-line description)
  into a file, and re-read the full packet from the run records only when building
  a dossier or a portfolio entry. Doing this after the finder stage is too late;
  the context is already spent.
- **Treat the finder count as a context budget, not just an agent budget.** This is
  the real reason the target moved from 300 to 500: ~22 finders is survivable in one
  session and ~42 is not. If a component is large enough that even a 500-line target
  yields more finders than the session can hold, say so before dispatching rather
  than discovering it at the verification stage.

`SKILL.md` section 4 therefore reports the projected verification cost before
spending it. That report is **informational and decides nothing**. Bounding is
governed by the automatic ceiling in `bounded-verification.md` rather than by
ad-hoc runtime judgement, so a run never improvises a bound from cost pressure:
a subset chosen on the fly produces a portfolio that looks complete and is not,
whereas the automatic ceiling names every deferred candidate in the digest.
