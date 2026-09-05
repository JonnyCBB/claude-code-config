# Bounded Verification

`SKILL.md` section 8 states the trigger and defers here for everything else.

**Applied automatically above the ceiling, and never put to the caller.** Verification cost scales
with candidates -- three downstream agents each -- so an unbounded component-scoped run costs well
over a hundred agents and has been measured overrunning a session limit mid-run
(`references/design-history-and-failed-approaches.md` section 7). Below the ceiling the bound is a
no-op and every group is verified.

An overrun is not a partial result, either. The digest is written at the end of the run, so a run
that exhausts its session limit mid-verification produces no readable artifact at all -- which is
why the ceiling is enforced up front rather than discovered.

**`SKILL.md` section 8 states the bound itself -- the Act-Now floor and the numeric ceiling for
everything else -- and is the only place that number lives.** This file does not repeat it, because a
restated number goes stale on the day the other one is revised.

What belongs here is why the ceiling is a _fixed_ number rather than a function of the agent budget.
Filling is deterministic by band -- do not ask the caller to nominate individual Important
candidates, and do not rank within a band to choose (within-band order is not a severity judgement,
which is the same reason this is not a top-N cut).

**When a band is only partly consumed, prefer user-facing candidates, then use fingerprint order as
the final tie-break.** The fill order within a band has two stages:

1. **User-facing first.** Sort by `share_absent` in this priority:
   - `null` (has a resolved share) -- measured user-facing impact. Verify first.
   - `NOT_QUERIED` -- a user-facing request denominator exists but the numerator was not queried.
     These are the candidates most likely to produce an informative percentage once verified.
   - `NO_INSTRUMENT` -- no instrument can measure this path. Worth verifying but yields no number.
   - `NOT_REQUEST_SCOPED` -- no request denominator applies (timer-driven gauges, background
     processes, cron jobs). Verify last within the band.
   On a real 132-candidate run, 55 were `NOT_REQUEST_SCOPED`. Under the old fingerprint-only
   rule, 8 of 22 selected candidates were `NOT_REQUEST_SCOPED`, consuming slots that could
   have gone to user-facing candidates from the next band down.

2. **Fingerprint-ascending within each `share_absent` tier.** A band almost always holds more
   candidates than the remaining slots -- 3 slots against 41 Important, on the run this rule was
   written for -- so even after the user-facing preference a tie-break is needed. Fingerprint order
   is the right one precisely because it is _meaningless_: it is uncorrelated with severity, so it
   cannot smuggle back the within-band ranking the paragraph above forbids, and it is already the
   ordering this skill uses for within-band display and for control selection. It is also
   deterministic, so two runs over one component select the same candidates and stay comparable.

**This does not change the banding rubric.** Bands decide what priority something gets;
`share_absent` decides what gets verified first within a band. A `NOT_REQUEST_SCOPED` candidate that
gets verified still gets whatever band the evidence supports -- it is just verified after
user-facing candidates when the ceiling forces a choice.

Say in the run summary that the fill order prefers user-facing candidates within each band. A reader
who sees 3 of 41 verified will otherwise assume the 3 were the worst.

### Verification dispatches in batches, and every batch runs

**Dispatch verification in batches of 5 candidates (10 agents: 5 x 2 axes).** A batch boundary is
NOT the run boundary -- continue dispatching batches until every selected candidate has been
verified. The verification budget is the ceiling stated in `SKILL.md` section 8 plus controls, not
the batch size.

This was observed: an orchestrator stopped after batch 1 (5 of 22 candidates) because the skill
discussed "the agent budget" without defining it, and the orchestrator invented one equal to the
batch size. The session had substantial context remaining. Five more batches would have cost ~25
minutes against a 90-minute run.

### Why this stopped being a caller opt-in

Bounding used to require the caller to ask for it, and this file used to say the skill "must never
infer" it. That rule protected one specific failure: an unattended run that quietly verified a
subset would produce a portfolio that looks complete and is not.

**That failure is no longer representable.** `SKILL.md` section 9 now requires every unverified
candidate in the digest's `findings` array as `DEFERRED_UNVERIFIED` with `band: "Not checked"`, and
`digest_model.py` validates it. A subsetted run cannot look complete any more, because the digest
lists by name every candidate nobody looked at.

So the prohibition guarded a hole that is now closed, and its only remaining effect was to stop a
run mid-flight and ask a question. **Measured, on a 63-candidate run:** the caller was asked whether
to bound, and the exchange produced no new information -- the person running this skill has usually
never run it before, has no basis for choosing between 66 agents and 189, and takes the
recommendation. The cost was a stalled run; the benefit was zero.

What survives unchanged is the _disclosure_, which is what actually protected the reader: say in the
run summary that the bound was applied, how many were checked, and that the fill order is arbitrary.

A scope override is still not a bounding instruction, and it never was one.

**The ceiling is about the reader, not only the budget**, and that is why it is a fixed number rather
than a function of the agent cap. A digest carrying a hundred candidates is not a more thorough
artifact than one carrying the bound; it is one nobody reads to the end. Decided on a measured run that
produced 146 candidates from 42 finders, where the caller's judgement was that a reader would simply
stop. Cost and readability happen to point the same way here, but they are different constraints, and
if a future change makes verification cheap the ceiling still stands.

**This deliberately is not a top-N cut, and that is a measured decision.** Two independent assessors
banded one corpus near-identically and agreed on its top candidates, then diverged widely _inside_ the
band that held most of them, each inventing its own ordering criteria to place a cut.
`references/design-history-and-failed-approaches.md` section 11 holds the figures. Bands reproduce, so
bound on bands; nominate the rest explicitly so a reader can see and challenge the choice rather than
inheriting an arbitrary cut line.

**A scheduled run bounds itself on the same rule, which is the case that needed it most.** Under the
old opt-in there was nobody awake to opt in, so a component-scoped scheduled run predictably
exhausted its session before reconciling anything -- and because the digest is written at the end,
produced no artifact at all.

**When the Act-Now count alone exceeds the ceiling, the ceiling wins and the shortfall is named.** Three agents per candidate means a large Act-Now set can outrun the ceiling: one run banded 7 Act-Now, which with nominations and controls projected 41 agents against a cap of 34. Verify as many Act-Now candidates as the ceiling allows, then mark the remainder `DEFERRED_UNVERIFIED`, record **that cost rather than severity is what stopped the run** in `shortfall.reason`, and list them individually by name. Write that reason as a sentence the component's owner can read (`run-record-schema.md` is canonical for the wording; it renders verbatim into the digest). The shorthand "budget, not band" states the distinction for you, not for them. That distinction is the whole point: a candidate deferred for cost is a scheduling fact about this run, while a candidate deferred for band is a severity judgement, and a reader who cannot tell them apart will read an Act-Now candidate as unimportant. Never silently drop the excess, and never quietly rebrand it as a lower band to make the arithmetic work.

**Always verify one or two control candidates from outside the bound, sampled without regard to
band.** Sort every unverified candidate by root-cause fingerprint, ascending, and take positions
`0` and `len(pool) // 2` -- zero-indexed, so a pool of four gives positions 0 and 2. The formula is
spelled out because "the middle" is ambiguous for an even-length pool, and a control whose selection
rule shifts between runs cannot be compared across them. With a pool of one, position 0 is the only
control. That rule is deterministic and reproducible, and crucially it is **uncorrelated with band,
evidence strength and urgency**, which is what makes the resulting discard rate an estimate rather
than an artifact.

Do not select the lowest-banded candidates. That was tried and cannot do this job: low band means low
_urgency_, not likely-_false_, so it handed the axes two straightforwardly true positives and
measured nothing. A control that selects for weakness on the wrong dimension is worse than none,
because it produces a number that looks like a discard rate and is not.

Their purpose is measurement, not coverage. Bounding verifies the candidates most likely to be real,
so the confirmation rate stops being evidence of anything: one bounded run returned 7 of 7 mechanisms
`CONFIRMED` with zero discards, which says more about selection than about the verifiers. Two of the
most valuable results this method has produced were a `DISCARDED_INTENDED` and a refuted mechanism,
and bounded verification would have reached neither. Controls keep the discard rate observable at a
cost of three agents each.

Report controls as controls, separately from the findings, and read them as a diagnostic: if controls
keep coming back confirmed, either the finders are unusually accurate or an axis is rubber-stamping,
and the run summary should say which it looks like rather than folding them in.

**Bounding never discards.** Every candidate not verified keeps its full Finder Packet in the
portfolio (section 6), marked `DEFERRED_UNVERIFIED` with its band and the reason it was not
nominated, and appears in the run summary by name. It has no disposition, because none can be
assigned without both axes. That is what makes bounding a legitimate lever and quiet subsetting not:
the reader can see exactly what was found and not pursued.

### Scoring before verification

Band candidates with **the same considerations `references/behavior-dossier-and-verdict-schema.md`
section 6 defines** for post-verification reporting, so the skill carries one severity vocabulary
rather than two. Only the timing differs: the inputs are finder evidence rather than verifier
evidence, so every figure is a pre-verification estimate and carries section 6's
`ESTIMATED`/`MEASURED` label.

### Measure exposure rather than inheriting UNKNOWN

Finders hold no metric tools, so exposure arrives `UNKNOWN` far more often than the evidence
warrants. Measured, almost every packet reports `UNKNOWN` while a large minority have **already named
the exact metric that would resolve it** and could only cite its declaration.
`references/design-history-and-failed-approaches.md` section 8 holds those counts.

So before banding, each packet's `Impact and exposure evidence` field is read for a named metric and
that metric is queried read-only, using the capability STEP 0 already confirmed. The finder has
usually done the hard part by locating the instrumentation; turning its citation into a number is a
lookup, not an investigation.

**That lookup is now a stage, not an inline step: `agents/bug-hunt-impact-resolver.md`, spawned once
per component before banding.** It was an instruction to this orchestrator and it was executed on
**none** of the checked candidates on one measured run, most of which had already named the metric
that would resolve them (figures canonical in `design-history-and-failed-approaches.md` section 8,
deliberately not restated here). The instruction was not the problem; the actor was. This
orchestrator is the one measured to exhaust its working memory before reaching the checking stage, so
a required lookup placed here competes with the work it already loses. One batched agent holding the
metric tool costs one agent against a run that spends 27, and `exposure_resolution` in
`run-record-schema.md` now makes a skipped lookup fail validation rather than render a clean page.

Two things to hold onto. Banding stays in this orchestrator and never moves into the finder: a finder
told to band would be making the comparative judgement `agents/bug-hunt-finder.md` explicitly forbids,
and it would need metric tools that would multiply per-finder cost by the fan-out. And measurement is
what earns its keep here -- across two scored corpora, four finders' headline severity claims were
refuted outright by a single query each, including an "unbounded cardinality" that was bounded at a
few dozen values and a claimed hot path that was dormant.

## Why this file exists separately

Bounded verification is the skill's only cost lever, and every paragraph above is
a measured result rather than a preference -- which is exactly the material that
belongs in a reference rather than in an orchestrator a model reads on every run.
