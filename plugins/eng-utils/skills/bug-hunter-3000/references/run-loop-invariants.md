# Run Loop Invariants

`SKILL.md` section 4 holds the loop itself. This file holds the twenty-two things
that must stay true about it, each of which replaced something that was tried and
measured.

**Read this before changing the loop.** The pseudocode in `SKILL.md` is short
enough to look obvious, and most of what makes it correct is not visible in it.

**Nothing here is a rule you can derive from the code.** Every bullet is either a
measured failure or a distinction two readers got wrong. Where a bullet cites
`design-history-and-failed-approaches.md`, that file has the figures.

Then assemble the run record and produce the digest -- section 9.

The partition rule and the grouping step each replaced an approach that was tried and measured. `references/design-history-and-failed-approaches.md` records what each cost to learn -- read it before changing either, so a superseded approach is not reintroduced as an obvious improvement.

**The per-squad rationing rule is retired, and its deletion here is deliberate rather than an oversight.** The loop above used to be nested by squad, with a counter that skipped a squad's remaining components once it had been given three. That is gone entirely: two of the three scope strategies have no squad concept at all, and removing the org traversal removed the mechanism that supplied squad membership to the outer loop. `references/scope-strategies.md` section 6 holds the reasoning and the accepted risk. **Do not reintroduce a cap here** -- section 8's bounded verification is the cost lever.

This loop depends on a few things holding:

- This run investigates multiple components within its resolved scope and does not stop at the first confirmed candidate. **That requirement is reworded rather than preserved**: it used to assert breadth over several squads at once, which a single-squad run contradicts by definition. That clause is gone; the "does not stop at the first confirmed candidate" half is the part that was always load-bearing.
- No disposition of any kind stops the loop -- not `READY_LOCAL_CANDIDATE`, not mechanism confirmation, not `READY_CROSS_SYSTEM_DOSSIER` or `PRODUCT_EXPERIENCE_DOSSIER`. Every component in scope is investigated regardless of what earlier components yielded.
- Each component is searched by several finders in parallel, one per disjoint mandate, rather than by a single finder that owns the whole component. One finder per component means one search of the component's entire surface, and the most locally-decidable candidate dominates it.
- A finder returns zero or more packets, forwarding every candidate its own static check failed to kill and discarding only what it refuted. An earlier one-per-mandate rule was measured to discard live, unrefuted work that finders had already done, so expect several packets per mandate rather than one, and expect grouping and the automatic bounded verification (section 8) to carry real load rather than being near-inert. `references/design-history-and-failed-approaches.md` section 7 holds the yields.
- Mandates are partitioned by file size, not by package, and to a **target size rather than to a fixed count**. `references/mandate-partitioning.md` is canonical for the target itself and is the only place it is stated -- this file deliberately does not repeat the number, because it was repeated once and went stale the day the target was revised. The largest files get mandates of their own. Competition within a mandate is what hides path-sensitive divergences, and file size is the best cheap proxy for where they hide -- which is exactly why a fixed count fails: it forces whatever is left over into bins of unbounded size. Measured at `max=8` on an 11,181-line component: four solo mandates yielded 5.73 packets per 1,000 lines and four bins of ~2,490 lines yielded 0.50. `references/mandate-partitioning.md` holds the figures, the confound analysis, and the floor below which smaller mandates stop helping.
- Mandate count now routinely exceeds what can run concurrently, so finders dispatch in **batches of `parallelism`** (default in `references/mandate-partitioning.md`, which is canonical for it). Within a batch every Agent call goes in one message; across batches the loop waits. A batched run is not a bounded run -- every mandate is still dispatched, and batching does not change whether the automatic ceiling in `bounded-verification.md` applies.
- A second **lens pass** runs after the file pass: whole-component finders, one bug class each, dispatched to the same `agents/bug-hunt-finder.md` type. It exists because a defect whose halves live in different mandates belongs to no file-slice finder -- measured, two DI-scoping defects spanning three modules were found only because their provider file happened to be a solo mandate. `references/finder-lenses.md` is canonical.
- **Lens finders are blind to what the file pass returned.** Telling them would let a lens search a "covered" region less, and recall is the only reason the pass exists. Deduplication happens afterwards, where it costs arithmetic rather than a defect.
- **Merging lens and file packets by fingerprint is NOT the grouping rule.** Grouping consolidates two views of one defect via mutual defect-site citation and forbids declaration-against-declaration matching; fingerprint merging is exact equality on packets describing the same site. Two finders reaching one defect independently is corroboration and both are recorded against the single candidate. Conflating the two re-breaks the most-rewritten rule in this skill.
- **Same-site merge runs AFTER grouping and fingerprint merge.** Two candidates that declare an identical `defect_site` string but carry different fingerprints are collapsed into one candidate with both finders recorded. This catches the file-pass/lens-pass rediscovery shape that bidirectional-citation grouping cannot reach: the lens pass is blind to the file pass, so neither side cites the other, and different mechanism descriptions produce different fingerprints. The lens pass stays blind -- the merge happens after both passes complete. The FIRST fingerprint in sort order becomes the group's primary for downstream consumers (packet re-read, portfolio naming, resolver keying); all constituent fingerprints and mandates are recorded in a `merged_from` list on the surviving candidate. On a real 132-candidate run, 26 sat on 12 repeated defect_site strings; all 12 were cross-pass pairs (file-mandate + lens-mandate describing the same mechanism at the same line).
- The loop **reports projected verification cost** (3 agents per candidate) before spending it. That report is information only, and never a licence to improvise a bound from runtime cost pressure. Bounding is governed by the automatic ceiling in `references/bounded-verification.md` rather than by ad-hoc runtime judgement, because a run that invented its own subset would produce a portfolio that looks complete and is not.
- A component is never left half-searched: every mandate for a component is reconciled before the loop moves on.
- **Wall clock is not a stopping condition.** As long as context window remains, the run continues through every stage for every selected candidate. Claude Code sessions routinely run for hours; individual agents in this pipeline take 2-20 minutes each. The only legitimate resource constraint is context exhaustion after compaction. If that happens, produce the digest with the candidates that completed the full pipeline (finders through reconciler) -- never skip pipeline stages for candidates still in progress. A finding with verification but no reconciler is not a finding; it is an incomplete investigation.
- **An enumerated component list replaces discovered membership; it does not reorder it.** A run naming three components investigates exactly those three. Do not infer a different reading from whether the caller happened to say "limited to" -- a bare list is still a replacement, and a caller wanting named components _plus_ continued discovery has to say so. `references/scope-strategies.md` section 1 is canonical on this and records why it is spelled out.
- **Nothing bounds finder fan-out.** This is an accepted risk, not an oversight, and it is the one thing to understand before running strategy 3 over a large system: an overrun happens mid-run while the digest is written at the end, so an overrun produces no readable artifact at all. `references/scope-strategies.md` section 6 holds the measured figures and the mitigation.
- `impact_exposure` is reported `UNKNOWN` only after a metric query was actually attempted and either failed or found no instrumentation for the path. It is never the value that simply arrives from upstream: an unattempted `UNKNOWN` omits the band, and an omitted band reads as "low severity" to whoever reads the portfolio.
- A finder may legitimately return nothing for its mandate -- zero findings is a complete, acceptable result. Move on rather than forcing a hypothesis, and rely on the finder's Coverage record to show the mandate was genuinely searched.
- Verification cost scales with candidates, not with mandates: three downstream agents per candidate, on top of one finder per mandate. Treat a single component-scoped run as costing well over a hundred agents unless the run stays under the ceiling in section 8, which applies automatically and is never waiting on anyone's consent -- a measured run without that ceiling exhausted its session before reconciling anything (`references/design-history-and-failed-approaches.md` section 7). Never respond to the cost by quietly verifying a subset: an unverified candidate that never reaches the portfolio is indistinguishable from one that was never found.
- Grouping is not the `DUPLICATE` disposition. `DUPLICATE` (row 8) is human-assigned and means "a prior decision already covers this". Grouping is a mechanical same-run consolidation of packets describing one mechanism, and it is the orchestrator's to do.
- A grouped candidate keeps every constituent packet's fingerprint, one-sentence summary, and originating mandate, recorded against the single verdict. Collapsing them into one record would corrupt coverage accounting -- two mandates did real work and both must remain visible -- and would break cross-run deduplication for whichever fingerprint was discarded.
- Grouping never crosses components, and it is not the `DUPLICATE` disposition. The qualifying-evidence test, the containment count, the multi-partner resolution and the parse-failure guard all live in `references/grouping-rule.md`; that file is canonical and this loop must not restate any of it.
- Mechanism and intent verification are dispatched together, and neither waits on or sees the other's result or progress: intent verification always runs, unconditionally, even for a candidate whose mechanism later comes back `REFUTED`.
- The intent-verifier separately checks its own known-false-positive table, `references/known-bug-false-positives.md`, as part of its evidence search -- this loop does not need to read that file itself.
- Exposure is resolved before banding by `agents/bug-hunt-impact-resolver.md`, once per component, and **its per-candidate entry is part of the reconciler's dispatch payload.** A reconciler dispatched without it cannot carry out its own `impact_exposure` instruction and will fall back to the packet's `UNKNOWN` without saying so.
- The disposition is produced by `agents/bug-hunt-reconciler.md`, which reads both verifiers' full evidence trails and the disposition table in `references/behavior-dossier-and-verdict-schema.md` section 5. The reconciler weighs evidence quality (not just verdict labels) and produces all six verdict-schema fields.

**Optional acceleration, not a dependency.** If a human explicitly invokes this skill interactively and separately asks for a workflow, the same per-component loop above may be expressed as a Workflow script for parallel throughput across components and squads. This is a performance optimization available only in that specific, explicitly-opted-into context. The scheduled/recurring path this skill exists for must never depend on it firing, and nothing in this skill's own instructions is itself an opt-in on a scheduled run's behalf.

## Where the rest lives

- The partition rule's reasoning: `design-history-and-failed-approaches.md` section 1.
- The grouping rule in full: `grouping-rule.md`. It is canonical and `SKILL.md`
  must not restate any of it.
- The disposition table: `behavior-dossier-and-verdict-schema.md` section 5.
- Bounded verification, which is the only lever that changes this loop's cost:
  `bounded-verification.md`.

## Rationale removed from the pseudocode's comments

`SKILL.md` section 4's comments were compressed to the operative instruction plus a
pointer, so the orchestrator stays inside its retention budget. No reasoning was
lost; it moved. Most of it is below, unchanged. The rest went to the file that owns
the subject: the finder-count threshold that triggers a degradation warning and the
cost of carrying packets forward are in `mandate-partitioning.md`; the threat-level
inputs (tier as context, effort reported separately, deliberately no numeric scale)
are in `behavior-dossier-and-verdict-schema.md` section 6; and the re-dispatch rule
has its own section at the end of this file.

**Why the partition is greedy bin-packing by size.** It is specified rather than
left to judgement only so two runs on one component produce the same partition --
a run left to balance by eye cannot be compared with the next one. Package-shaped
partitions were measured and failed; see section 1 of
`design-history-and-failed-approaches.md`.

**Why finders must be spawned from one message.** Several Agent calls in a single
message run in parallel; one call per message runs them in series. No finder sees
another's mandate, progress, or result.

**Why a finder returns zero or more packets.** It forwards every candidate its own
static check failed to kill, so flatten rather than assuming one packet per mandate.

**The grouping rule, in brief -- and it is only a summary.** Two packets group when
each one's evidence cites the OTHER's declared defect site; only across mandates;
and when unsure, do not group, because a wrongly grouped pair loses a real defect
while a wrongly separated pair only costs verification time. `grouping-rule.md` is
the whole rule.

**Why bounding is not a top-N cut.** Bands reproduce across assessors; within-band
order does not.

**Why a LEAKED dossier blocks dispatch.** A verifier cannot un-see a conclusion, so
there is no recovering the independence afterwards. Regenerating a dossier launders
nothing, because the dossier is derived rather than authored. `NO_INPUT` means the
check did not run and must never be recorded as withholding held.

**Why the scan's own numbers are the ones reported.** The verifiers also self-report
leaks, and those reports undercount: on one run they caught five of seven leaks that
the scan caught in seven of seven. `SKILL.md` section 7 reports the scan's count, and
a verifier self-report never substitutes for it.

**What the intent-verifier must never receive**, and the trap in stripping it: never
the packet's hypothesis, confidence, or proposed fix, and never the `Defect site:`
field -- fold its lines into neutral Code locations and drop the label, because the
field NAME asserts a defect was found and where. Remove each withheld field's LABEL
AND ITS VALUE together: deleting labels alone orphans the values, so
`Confidence: high` becomes a bare `high`. Then verify by searching the dossier for
the VALUES, not the labels -- a label-keyed grep returned zero on every file of a
run whose dossiers still carried the orphaned text, and certified the strip as clean.

## A finder that dies is re-dispatched once, never escalated to the caller

A finder can error, be interrupted, or return nothing parseable. When that happens, **re-dispatch
that one mandate once, without asking anyone.** If the retry also fails, record the mandate as an
unsearched gap in the digest's coverage and carry on with the run.

Two reasons it is never a question. The answer is always the same -- coverage is the whole point of
the fan-out, and a single extra finder is the cheapest agent in this pipeline -- so asking spends a
round trip to be told what the skill already knows. And the caller is usually someone who has never
run this skill and cannot weigh "re-run one search" against "accept a hole", which is the same
reason section 8's bound stopped being an opt-in.

**What must never happen is silence.** A finder that vanished and a slice that was searched and came
back clean are indistinguishable in the output unless the gap is recorded, which is the failure the empty-run rule
exists to prevent: a clean component and an unsearched one must not look alike. Measured: one lens
finder was interrupted mid-run, and nothing in the pipeline noticed -- the loss was visible only
because a human happened to see the interruption.
