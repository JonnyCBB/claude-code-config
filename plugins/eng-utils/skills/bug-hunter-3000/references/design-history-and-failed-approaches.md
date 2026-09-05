# Design History and Failed Approaches

Read this before changing the run loop's partition rule, its per-squad cap, its
candidate-grouping step, how many candidates a finder forwards, the optional bound on how many
are verified, or how the threat level is scored and banded -- or when one of those rules
looks arbitrary and you are tempted to "fix" it.
Each replaced something that was tried and measured. `SKILL.md` states the rules; this file
records what they cost to learn, so the same ground is not re-lost.

Nothing here is an instruction. It is the evidence behind eleven of them, and one amendment
that was proposed, tested and rejected.

## 1. Partition by file size, not by package

**Superseded:** one finder per component, then a package-shaped partition.

One finder per component means one search of the component's whole surface, and the most
locally-decidable candidate dominates it. The candidate-budget argument cannot compensate: it caps
candidates per run, not per component. (At the time this was measured a finder also returned only
one hypothesis, which compounded it -- see section 7, which supersedes that part.)

Package-shaped partitioning was the first replacement and still failed. On a 79-file component
the `pages/` mandate held 26 files including all 22 page classes, and the defect sat in the
component's single largest file (564 lines). The same finder found that defect immediately when
the file was its entire mandate. Competition _within_ a mandate is what hides path-sensitive
divergences, and file size is the best cheap proxy for where they hide. Components typically
have only a handful of files over 400 lines, so isolating them costs little.

## 2. The cap counts components investigated, not candidates found

**Superseded:** the cap's original trigger (first `READY_LOCAL_CANDIDATE`), then a candidate budget.

The rule as written tripped the cap on `READY_LOCAL_CANDIDATE`. That couples breadth to the
confirmation rate -- and the measured confirmation rate is near 100%: 26 of 26 candidates
confirmed across seven observed runs, with zero `DISCARDED` and zero `HOLD`. Any
success-triggered cap therefore fires on component one, and a squad-scoped run collapses to a
single component. A run that named three components investigated one.

Rationing on candidates was the second attempt, and it failed for an arithmetic reason worth
keeping: fan-out yields roughly one candidate per mandate, so a single 8-mandate component
exhausts a budget of 3 immediately and the cap trips exactly as early as before. Raising the
budget only moves the collapse point.

Counting attention rather than successes decouples the two, so breadth becomes a property of
the schedule instead of an artifact of how often the verifiers agree. **This is a deliberate
departure from that trigger.** The cap's purpose -- not over-investing in one squad -- is
preserved; only its trigger changed.

## 3. An enumerated component list replaces squad membership

The competing reading is that named components are merely investigated first, and the loop then
continues into the rest of the squad. That yields a different run entirely: three named plus
three unnamed before the cap fires, rather than three in total.

A probe surfaced this by noticing that the caller's phrasing -- the word "limited" -- was doing
the disambiguating work rather than the skill. Hence the rule is explicit, and must not be
inferred from how a caller happened to word the request.

## 4. Grouping happens before verification, and is not `DUPLICATE`

Fan-out created a duplicate class that one-finder-per-component could not produce: a defect
spanning a call boundary is discovered from both sides, by the two mandates owning the caller
and the callee. Measured -- one run spent six verification agents on a single metric-label
defect found once from `ServiceHandler` (the caller emitting untagged metrics) and once from
`CustomMetrics` (the methods building the `MetricId` without the label). The fingerprint hashes
free text, the two finders worded their summaries differently, so nothing collided.

Grouping is a mechanical same-run consolidation and the orchestrator's to perform. `DUPLICATE`
(row 8) is human-assigned and means "a prior decision already covers this". Do not collapse the
two concepts.

The asymmetry that sets the conservatism: a wrongly grouped pair loses a real defect, while a
wrongly separated pair only costs verification time.

**Superseded within this iteration:** the first grouping rule keyed on bare `file:line`
intersection between mechanism claims. Two probes, given three distinct defects that all cited
`BlenderModular.java:108-110` -- a delegation point every `StepsMutator` page routes through --
independently reported that the rule read literally told them to merge two different
page-class defects, and that they reached the right answer only by falling back on "when
unsure, do not group". One also found that a packet citing a whole method body (`:103-123`)
encloses every narrower citation in that method, making it a grouping magnet.

Both failures come from the same confusion, and mutual defect-site citation resolves both: the
qualifying evidence is that each packet's mechanism claim cites the _other's declared defect
site_, not that the two claims happen to share a line. A shared consumer several
independently-wrong callers all reach is part of each path, never a defect site. This is why
the finder is required to label its defect site explicitly rather than leaving it implicit in
a list of cited locations.

**Superseded a fourth time, in the magnet count itself:** excluding sites that share the
target's mandate. That wording was added to stop a phantom conflict and made the count inert by
construction -- a defect site always lies inside its own finder's mandate, and the partition rule
gives each file to one mandate, so every declared site in a file shares the target's mandate and was
always excluded. The count was permanently zero, so an enclosing citation always qualified, including
the whole-method-holding-three-defects case the clause exists to veto. The count now collapses
overlapping sites into distinct partners and never mentions mandates, which is what stops it going
inert: nested views of one place are one partner, three separate defects in a cited method are three.
Verified against the fixture two blind assessors and a mechanical replay had agreed on -- same one
group, same two near-misses.

**Superseded a third time:** excluding enclosing citations outright. The magnet observation
above was true but the clause drawn from it over-approximated, and the cost was total. On a
44-candidate run the rule formed **zero** groups and declined all 12 pairs that had a citation
in one direction, every one of them for the same reason: the callee-side packet declares a
single line, the caller-side packet cites the enclosing four-to-ten-line emitter method, and
"enclosure never qualifies" classified that as the magnet case. Two of the declined pairs were
the `ServiceHandler`/`CustomMetrics` metric-label pair this section exists to catch
(`M3-P1`'s `CustomMetrics.java:182-186` enclosing `M4-P2`'s declared `:184`, and `M3-P2`'s
`:109-118` enclosing `M4-P5`'s declared `:113`), and in both the finders had asked in writing
to be grouped. The rule could not group the pair it was written for.

What went wrong is that enclosure was used as a proxy for the property that actually matters,
which is how many declared defect sites a range contains. The original observation involved a
21-line whole-method citation; the short emitter methods here contain exactly one declared site
each and are not acting as magnets at all. The test is therefore a count: an enclosing citation
qualifies unless its range holds more than one of the run's declared defect sites. Note the
count is scoped to the current run, so it is computable at grouping time from the packets in
hand and needs no judgement about what a method "is".

One caution for whoever measures this next. A run summary's own near-miss table listed a third
instance of the motivating pair, citing `CustomMetrics.java:188-191`; that range does not appear
in the packet's citations on disk, which are `:182`, `:182-186` and a bare `:188`. Two instances
survive checking against the packets, not three. Read the packets, not the summary built from
them.

## 5. Why the sweep table's columns are fixed

Finders given the sweep's schema have substituted their own. Two of three kept a shape that
enumerated downstream decisions and found a real defect; the third replaced the columns with
`degraded path | reference | emission | parity`, which has nowhere to record what each
downstream decision receives, and walked past a defect three methods from where it was looking.
The schema is doing the work, not the diligence -- hence "add columns, never remove the three
load-bearing ones" (discriminator, downstream decision, effective configuration).

**Superseded a second time:** an adherence clause alone ("these columns are not yours to
redesign") did not bind. Finders substituted their own schema four times running, each time for
something that looked natural for the component in front of them, and each substituted schema
omitted any column for the configuration actually sent downstream. Across samples where the
schema is on record: 2 of 2 finders whose table carried such a column found the target
divergence; 0 of 4 without it did, despite each correctly enumerating seven or eight other
downstream decisions. The effective-configuration column is therefore mandatory, not an
optional addition. Telling a finder to follow a schema is weaker than telling it which
question the schema has to be able to answer.

## 6. Pre-flight matches capability, not tool name

All four agent definitions declare `mcp__plugin_eng-utils_*` tool names. A measured run found
those do not resolve in every runtime, while the same capabilities were present under a
different plugin's prefix. A pre-flight that stops on a prefix mismatch aborts runs that could
have proceeded correctly -- and a pre-flight that cries wolf gets routed around, which is its
own silent failure.

## 7. A finder forwards every unrefuted candidate, not just its favourite

**Superseded:** one falsifiable hypothesis per mandate.

The original contract had a finder return exactly one candidate. Measured against a single
564-line file: six finders produced roughly thirty-one candidate-grade observations between them
and forwarded six. The same real defects recurred and were relegated to prose by different finders
on different runs, and one defect that four finders noticed was forwarded by none of them. All six
also invented a "candidates considered and set aside" section that the output contract never asked
for, which is the clearest signal available that the limit was discarding work already done rather
than reducing work.

The distinction that matters is why a candidate is dropped. Refuting it is legitimate and the
refutation is worth recording. Dropping a live, unrefuted mechanism because another looked more
interesting is a comparative judgement the finder is not positioned to make, and it is invisible
downstream: no verifier can assess a candidate it never received.

Cost moves from mandates to candidates. Measured on the run that followed: 44 candidates from 8
mandates, mean 5.5, which is 8 finders plus 132 downstream agents. That overran the session's
agent limit mid-run. The intended lever is bounded verification (`SKILL.md` section 8) -- at the time a caller opt-in,
now applied automatically, see `bounded-verification.md`'s "Why this stopped being a caller opt-in"
-- which this change turns from near-inert into load-bearing. Quietly verifying a subset instead is the one
response that must not happen, since an unverified candidate absent from the portfolio cannot be
distinguished from one that was never found.

## 8. Ranking was named as the cost lever three times before it existed

**Superseded:** a candidate budget (section 2), then three dangling references to a procedure
with no definition.

Section 2 records why rationing on candidates failed. What replaced it in the prose -- "the
caller's opt-in candidate ranking" -- was then cited as the load-bearing lever in two places in
`SKILL.md` and once here, while no section anywhere defined its criteria, its opt-in syntax, or
what became of the candidates below the cut. Meanwhile the frontmatter's `argument-hint` still
advertised the superseded `[candidate-budget]`. So the declared interface offered a lever that
had been removed and omitted the one meant to replace it.

The consequence was not hypothetical. The 44-candidate run hit its session limit with no defined
way to bound itself, and its own summary recorded that "the caller declined ranking" -- when in
fact there was nothing to decline. A reference to a procedure is not a procedure, and an
orchestrator that reaches a cost wall holding only a pointer will either stop or improvise.

Two decisions inside the resulting section 8 are worth keeping deliberate:

Ranking scores on the **existing threat-level rubric** rather than a new one, so the skill has a
single severity vocabulary. The rubric was already there for post-verification scoring; reusing
it pre-verification costs nothing and keeps the thresholds in one canonical file.

Ranking lives in the **orchestrator**, and the metric query lives with it. The alternative --
giving finders metric tools so exposure resolves at the source -- is closer to the evidence but
wrong twice over: it multiplies query cost by the fan-out, and it hands a finder a comparative
input one paragraph after `agents/bug-hunt-finder.md` tells it that ranking is not its job. The
measurement that motivated this: 43 of 44 packets reported exposure `UNKNOWN`, but 20 of them had
already named a specific queryable metric and cited the line declaring it. The finders located
the instrumentation; only the lookup was missing, and the orchestrator already holds the
capability that STEP 0 verifies.

**The 2026-08-28 measurement, and it is the canonical one. Every other file points here rather than
restating these numbers.** Across four rendered reports on two components:

| What was measured | Figure |
| --- | --- |
| exposure column an absence, `search-influence` 08-12, checked findings | 26 of 26 |
| exposure column an absence, `home-config-reader`, checked findings | 24 of 26 |
| component denominator reaching the column, all four reports | 0 of 62 |
| checked findings naming a metric artifact in their own packet | 7 of 26 |
| ... of those, citing it with a file and line | 6 of 7 |
| ... resolved by the run | **0** |
| findings banded Act-Now with no impact figure behind them | 9 |

One of those 9 recorded its own gap verbatim: `Exposure: UNKNOWN absolute volume (metric exists,
never queried)`. Resolving it took a single query against `apollo_randomized_candidates_counter_total`
and returned **0.048% of Influence requests** -- which is within rounding of the hard-coded `0.0005f`
gate the finder itself cited, an independent corroboration that the denominator is the right one.

**That figure was wrong the first time it was written down here, and the correction is the whole
argument for the reconciler's refine clause.** It first read `0.0058% of component RPCs`, computed by
dividing the randomization counter by `apollo_rpc_total_counter_total` -- every RPC the component
takes *and makes*, across fifteen client dependencies -- rather than by the Influence server method
alone. Wrong denominator, roughly 8x too large a base, and the resulting figure was an order of
magnitude out while looking entirely plausible. Nothing in the pipeline would have caught it: it is
`MEASURED`, it carries two denominators, it validates. **Only an actor holding the harm's own evidence
trail can see that the base does not match the harm**, which is what
`agents/bug-hunt-reconciler.md` is now told to do. The error was made on the first real attempt at
this, by the person who then wrote the rule, and it was caught by an independent resolution pass
rather than by review.

## 9. Ranking and banding were one multiplied number, and it failed at the corners

**Superseded:** `composite = Impact x Likelihood x Consequence`, 1-27, cut into three bands.

The Consequence factor itself was sound and stays. What failed was multiplying all three into a
single score and cutting that score into bands, which asked one number to do two different jobs:
produce a total order for ranking, and produce coarse buckets for a human. Measured on one
20-candidate corpus scored twice by independent agents blind to each other:

Why the product was abandoned, all of it measured on one 20-candidate corpus scored twice, independently:

- **A Tier 3/4 component could never reach Act-Now.** Its ceiling was `1 x 3 x 3 = 9` against a floor of 18, so a confirmed thread-pinning loop on 100% of traffic banded "not urgent".
- **The Act-Now floor contradicted its own rationale.** The text said Act-Now required "a real failure or bypass" and cited `3 x 3 x 2` as the qualifying shape -- but Consequence 2 is not a failure. Both scorers found this, and both watched dead-dashboard candidates outrank an all-pages outage.
- **The product cannot separate the cases anyway.** `1 x 3 x 3` (Tier 4, always fires, catastrophic) and `3 x 3 x 1` (Tier 1, always fires, cosmetic) are both 9. No choice of boundary can split them, which is what makes this a limitation of multiplying rather than of the numbers picked.
- **With Impact constant, the reachable values were `{3, 6, 9, 12, 18, 27}` and the two commonest were 6 and 18** -- exactly the two band floors, so the most frequent scores sat precisely where the boundary decision mattered most.

The replacement separates the jobs: rank by Consequence, then Likelihood, then Impact; read the
band off a Consequence x Likelihood table. Impact breaks ranking ties but is not an input to the
band, so a component's tier cannot downgrade a total outage. Both scorers, independently, banded
the corpus's most severe defect correctly under the new scheme.

The transferable lesson, which cost two rewrites to learn: a product of small integers cannot
encode a priority that is lexicographic in intent. If the rule you actually want is "a real
failure outranks a cosmetic defect however often the cosmetic one fires", sort on the factors in
that order rather than hoping a multiplication preserves it.

## 10. Two numeric threat-level scales, and why there is now none

**Superseded:** `Impact x Likelihood x Consequence` cut into bands (section 9), then the same three
factors as a lexicographic sort key plus a 9-cell band table.

Section 9 records the first attempt. The second replaced the product with a sort order and a band
table, fixing every defect section 9 lists -- and produced eight new ones, measured the same way, by
two scorers working the same 20 candidates blind to each other:

- **The two scorers disagreed about which candidate ranked first.** That is the finding. One admitted
  an accumulation defect to the top row via "capability under any reachable input"; the other
  narrowed the same question using the shape list and ranked it far lower. Same rubric, same
  evidence, opposite answer.
- **The rubric reproduced the exact inversion it opened by describing.** A mis-tagged metric ranked
  first, above a non-terminating loop, an all-pages crash, and a client-triggerable failure -- because
  the emission fires on every request. Frequency of a harmless emission was standing in for
  frequency of the harm. Measured: the claimed unbounded cardinality was bounded at a few dozen
  values and its harmful subset was 0.041% of traffic.
- **"Judge one occurrence" and "capability under any reachable input" are opposite tests** for any
  accumulation defect, and both appeared in the same section.
- **The tie-break was inert exactly where it was needed.** Impact comes from tier, so a
  component-scoped run has it constant: 18 of 20 candidates sat in unbreakable ties and four of the
  top five were one tie, so a top-5 cut fell where it did by luck.
- **Likelihood was undefined for absence defects, and the literal reading inverted intent.** If the
  harm is that a path never runs, its execution rate is 0%, which bands it lowest -- while the row
  that exists to catch "an alert bound to a series never emitted" is the reason the axis was added.
- **`UNKNOWN` was a penalty box with no exit**, and would have shipped the most serious candidate in
  the corpus without a band.
- **The worked example was one of the candidates being scored**, teaching the answer.
- **Overlapping candidates were not deduped**, so one root cause landed in two different bands.

Two rewrites, twelve distinct defects, no overlap between the two sets. That pattern is the
argument: the trouble was not the numbers chosen but that an ordinal scale was being asked to encode
a judgement. What both scorers did _well_ was measurement -- 25-plus production queries between them,
refuting three finders' severity claims outright. So the third version keeps every measurement
requirement, drops the scale entirely, and asks for a weighed judgement with the cut-line pair
justified in writing.

If you are tempted to add a score back, note that it is genuinely the obvious move, and that both
previous attempts looked correct until two independent agents ran them over real candidates.

## 11. Bands reproduce, total orders do not

**Superseded:** the top-N cut, as the shape of the caller's cost lever.

Section 10 records dropping the numeric scale. The replacement -- measure, then weigh four
considerations -- was tested the same way, two assessors on the same 20 candidates, blind to each
other, this time emitting a fixed `RANK|CANDIDATE|BAND|...` block so agreement could be counted
mechanically rather than parsed out of prose.

It worked, and in a specific place:

- **Bands agreed 19 of 20**, and both assessors independently placed the same candidate first and the
  same candidate second. Under the previous scale they had disagreed about which candidate ranked
  first at all.
- **Both refuted the same two finder claims with matching numbers** -- an "unbounded cardinality" that
  measured 19 distinct `limit` values and 27 distinct `offset`, and an "SLO ratio can exceed 1.0"
  bounded at 0.089 percentage points. Removing the scale is what made querying feel obligatory.
- **The Low band agreed perfectly**, all five.

And it failed in one place, cleanly: **within-band ordering did not reproduce.** Twelve of the twenty
landed in Important, and nothing in the rubric orders candidates inside a band, so the two assessors
diverged by up to seven places there, each having invented its own criteria (silent versus loud
failure, blast radius per occurrence, constant blindness versus intermittent blemish). One assessor
named the diagnosis exactly: the scale was never the root cause, the demand for a total order was.

So the lever changed shape rather than gaining another clause. Bound on bands -- verify all Act-Now,
plus Importants nominated in writing -- because that is the part two independent readings agree on. A
top-N cut drawn through a twelve-candidate band is a boundary the evidence cannot support, and
presenting it as a severity judgement misrepresents what the instrument measured.

The transferable lesson: when a rubric disagrees with itself, measure _where_ it disagrees before
amending it. Three versions of this rubric were rewritten on the assumption that the ordering
mechanism was wrong. The reproducible part had been there since version two; what was wrong was
asking for output the evidence could not support.

## 12. Rejected: scoping the grouping eligibility bar to files instead of mandates

**Proposed, tested, rejected.** Recorded because the reasoning for it is genuinely persuasive and
will occur to whoever reads the grouping rule next.

The argument: grouping's eligibility bar excludes two packets from the same mandate, but a mandate
can cover many files, so two candidates in _different_ files on one call chain are blocked purely
for sharing a finder. And since the partition rule gives the largest files solo mandates and groups
"the remainder into the rest", multi-file mandates are the designed common case, not an edge one.
One real mandate held five packets across three files, all mutually ineligible.

Measured on that 17-packet fixture, against the same-mandate arm whose output two independent
assessors and a mechanical replay had already agreed on:

- **Identical output.** 8 of 136 pairs changed eligibility; the one cross-file citation among them
  matched nothing. Same single group, same two near-misses.
- **The unblocked candidates were five distinct defects**, sharing only the per-request config path
  -- which is exactly the "shared line neither packet calls its defect site" false positive the rule
  already excludes. Their failure modes were opposite in kind and their fixes unrelated.
- **The pairs with a plausible one-defect reading were same-file**, and stay blocked under either
  bar. The real duplicate signal in that mandate was intra-file, so the amendment points away from
  where the evidence is.
- **It silently deletes the magnet count.** That count only ever runs inside a same-file comparison,
  so translating its exclusion to files makes it identically zero and an enclosing citation always
  qualifies. The magnet was the measured compromise that replaced "exclude enclosure outright",
  which had formed zero groups. The amendment keeps only the permissive half, and the proposer did
  not notice.

The fixture also has low power in both directions, which is worth stating rather than hiding: it
contains no same-mandate cross-file pair qualifying bidirectionally, so no benefit was
demonstrable, and no cross-mandate same-file pair, so no harm was either. This is "no evidence for,
some structural evidence against", not "proven harmful". Revisit it with a fixture that contains the
missing shape -- and if you do adopt it, keep the magnet count keyed to mandates.

The wider point: this amendment was argued from structure and looked sound. Testing it cost one
agent and found a consequence its author had missed entirely. Every previous change to the grouping
rule that shipped on reasoning alone introduced a defect.

## 13. The three-step artifact write, and a gate that certified its own destruction

The write used to be three caller-side steps: mask to stdout, redirect into the destination, re-scan
the destination. It is now one call to `scripts/write_artifact.py`, which owns all three. The reason
is a single measured run in which every step failed together.

Partway through a four-hour run, the plugin tree was replaced underneath it. The host re-cloned the
marketplace as a shallow clone of `master`, discarding the branch under test, so from that moment the
run was executing an older revision of the skill than the one it had pinned. The older
`redact_scan.py` had no `--mask` mode. An unrecognised flag was silently ignored, the script fell
back to report mode, and report mode's stdout was status JSON -- so the caller's
`--mask > artifact.md` wrote this over ten artifacts, each becoming 35 identical bytes:

```
{"status": "CLEAN", "findings": []}
```

Then the third step ran. It re-scanned each file on disk, found no secret shapes in a JSON status
blob, and reported `CLEAN` for all ten. The run summary recorded "all 9 artifact files were written
through `redact_scan.py --mask` (exit 0 each) and then re-verified on disk (all CLEAN)" -- false in
every clause, and the gate is what made it look true.

That re-scan had been added one commit earlier, specifically to catch a formatter that rewrites bytes
after a write. It was the right instinct aimed at the wrong question. "Does this file contain
secrets?" and "is this file the artifact?" are different questions, and only the second one rejects a
status blob. An empty-input guard does not help: 35 bytes of JSON is not empty.

Four changes came out of it, and the ordering matters because only the first two are load-bearing:

1. **The destination is an argument, not a redirect.** No shell redirection means no stdout for a
   typo to turn into content. This removes the failure rather than detecting it.
2. **`--sentinel` is required.** The artifact's own fingerprint must appear in the bytes on disk.
   Required rather than optional, because an optional integrity check is the one that gets left off
   on the run where it would have mattered.
3. **Unknown flags are rejected, in both scripts.** The incident began with a flag being dropped on
   the floor.
4. **Report-mode JSON moved from stdout to stderr.** `redact_scan.py in.md > out.md` now yields an
   empty `out.md` instead of a plausible 35-byte one. Nobody mistakes an empty file for an artifact.

There is a fifth property worth naming because it was free: `write_artifact.py` does not exist in
older revisions of this skill, so a tree that reverts makes the write fail with
`No such file or directory` rather than succeeding against a script that quietly does something
else. A new required file is a version tripwire.

**What this says about the version gate.** The manifest gate ran once, at the start, and returned
`MATCH  14 files pinned`. It was true when it ran and stopped being true two thirds of the way
through. A start-of-run pin cannot cover a long run against a tree an external process can replace,
so re-verify it before the write-out phase and again at the end, and report all outcomes. A gate that
runs once measures the moment it ran, not the run.

## 14. The digest, the scope rework, and what they retired (2026-08-06)

This iteration added a human-readable HTML digest, replaced the org traversal with three scope
strategies, and renamed the skill to `verified-bug-hunt` -- the name it carried until it was renamed
again to `bug-hunter-3000` on 2026-08-23. What follows is what it **retired**, so the
next editor does not reintroduce any of it as an obvious improvement.

**The premise is second-order and worth stating.** The binding constraint on this work being useful
is organisational -- reviewer capacity against bet commitments -- not output quality. In July a
goalie bot independently confirmed 12 of 14 findings and the owning team still declined, citing bet
work. This iteration lowers the cost of saying yes. It was never expected to be the unlock on its
own, and it should not be judged as though it were.

### The per-squad rationing rule is retired

Not disabled, not defaulted off -- removed, along with the org traversal that supplied the squad
membership it counted against. Section 2 above already measured a success-triggered cap collapsing a
squad-scoped run to one component, and two of the three replacement strategies have no squad concept
at all, so a per-squad counter has nothing to count.

`SKILL.md` section 8's bounded verification is the real cost lever and is unaffected.

**The accepted risk**: nothing bounds finder fan-out any more. Section 7 above measured the run that
overran mid-run, and is canonical for its figures. Under the cap a run always completed. An overrun happens _mid-run_
and the digest is written at the _end_, so an overrun now produces **no readable artifact at all**,
which is worse than a bounded partial run. This was decided deliberately rather than overlooked.
Mitigation is guidance, not mechanism: for a large system, use a named component list and bound it
yourself. `references/scope-strategies.md` section 6 says so.

### The UNTIERED stratum rule is rehomed, not retired

It moved from the archived org-traversal reference into `references/scope-strategies.md` section 5,
and still binds. A missing `reliability_tier` is a cataloguing gap, never folded into Tier 4.

### Effort stays an estimate

A planned change would have made Effort _measured_ by capturing a diff from the mechanism-verifier.
**The premise was a misreading and the change was cut.** `agents/bug-hunt-mechanism-verifier.md`
compares **existing commits** -- reproduce on the candidate state, move to the pre-change state,
reproduce again, return -- and authors no fix, so there is no diff to capture. Making Effort measured
would require the verifier to author a fix for every confirmed candidate, a real scope increase for
an agent whose non-negotiable boundary is read-only-and-local.

The misreading originated upstream, in the research and requirements documents, and was corrected in
both.

### A fifth reader-facing verdict was rejected

`DUPLICATE`, `KNOWN_ACCEPTED_RISK` and `BACKLOGGED` all map to `Not a bug` and render in the
collapsed section with their state name shown. This is the one lossy point in the disposition-to-
verdict translation, and it is deliberate: all three are human-assigned post-hoc, none requires
action now, and a fresh run does not produce them. A fifth verdict would have been scope creep
against a case that may never occur.

### `DISPUTED` was considered and dropped

The disposition vocabulary is internal and never shown to a reader, so a new state would not surface
usefully. Reviewer disagreement folds into the false-positive table instead -- and only where the
evidence actually establishes intent. See `references/known-bug-false-positives.md`.

### The numbered acceptance-criteria references were removed entirely, 2026-08-28

This skill used to cite requirements as bare numbers -- `AC-1` through `AC-11` -- 61 times across
ten files, including four Python scripts. They are all gone, replaced by a plain statement of the
rule each one stood for. **Do not reintroduce the numbering.**

The numbers pointed at a static requirements document that exists only on one person's machine. To
everyone else, and to every agent reading this skill at runtime, `AC-9` was an opaque token: it
named a rule without stating it, so a reader who did not already know the rule could not look it up
and could not check whether the surrounding text still honoured it.

Consolidating them into one reference file was considered first and rejected, and the reasons it was
rejected are the reasons removal was the right answer instead. Two of them stood at the time:
`references/tool-restriction-and-outbound-safety.md` already claimed sole authority over the
zero-outbound rule, so reproducing it would have created two files each claiming to be canonical for
one fact; and the requirements document carried **eight** criteria while this codebase cited
**eleven**, so formalising the eleven would have enshrined an unreconciled list.

**The unreconciled list turned out to be worse than unreconciled. It was ambiguous.** On removal, at
least four numbers were found carrying two different meanings in different files:

| Number | One meaning | The other meaning |
| --- | --- | --- |
| `AC-1` | the digest opens in a browser by default | a run does not stop at the first confirmed candidate |
| `AC-2` | `no-open` prints the path and opens nothing | the per-squad cap is retired |
| `AC-3` | a run finding nothing still produces a digest | the UNTIERED stratum rule |
| `AC-6` | the prompt-injection boundary | the org traversal that supplied squad membership |

A reader resolving `AC-3` in `render_digest.py` against `AC-3` in `SKILL.md` would have got two
unrelated requirements. That is not a documentation blemish; it is a reference scheme that returns
the wrong answer, and it went undetected for as long as the numbers were never expanded.

**The rule this leaves behind:** state the requirement, not its index. If a rule is worth citing it
is worth saying, and a sentence that names what it requires cannot drift out of sync with itself the
way a number can.

### Known gap: the per-candidate audit requirement has no automated enforcement

The requirement is that the per-candidate audit files and both verification axes behave exactly as before. There is
**no CI in this repo** -- no `.github/workflows` locally or on the remote, confirmed by a real 404 --
and the unit tests that covered `scripts/` were removed from the shipped skill, so nothing enforces
that automatically. They were deleted deliberately: this skill ships inside a plugin that other
people install, and test files, fixtures and eval harnesses are not needed to run it. They remain in
this branch's git history if the suite is ever wanted back. The criterion is currently enforced only
by a human exercising the pipeline by hand.

### One deviation from the implementation plan, and why it stands

The plan for this iteration said, in as many words, to leave `SKILL.md`'s
`impact = tier-to-impact score (Tier 1->3, Tier 2->2, Tier 3/4/UNTIERED->1)` line
unchanged. The token refactor removed it, initially without anyone noticing.

An independent eval agent then found the line was wrong. Section 6 of
`behavior-dossier-and-verdict-schema.md` -- which `SKILL.md` itself names as
canonical two lines later -- says tier carries **deliberately no number**. Worse,
the mapping scored `UNTIERED` identically to Tier 4, which is precisely the fold
the UNTIERED stratum rule forbids, performed through arithmetic instead of through a label.

**The removal stands.** A numeric line contradicting the canonical rubric is the
same failure section 10 above records twice, in miniature: an ordinal scale asked
to encode a judgement. Threat level is now computed per section 6 with no scale
to multiply.

Recorded here rather than left as a silent diff, because the plan said one thing
and the tree does another, and the next reader deserves to know which won.

## 15. What each run-summary item is defending against

`SKILL.md` section 7 lists six items and no longer carries the reason for each. The
reasons are these, and each is a failure that was observed rather than imagined.

- **The absolute path, first line.** On a scheduled fire nobody is watching the
  session, so the path in the summary is the only way anyone finds the artifact at
  all. A relative path, or one buried mid-summary, is a run whose output is lost.
- **The dossier leak scan's own count.** Reporting that it ran even when it found
  nothing is the point: a clean sweep and a check that never executed produce
  identical-looking summaries otherwise. Same reason `NO_INPUT` is not a pass.
- **Agent count and wall-clock.** Two numbers, and the answer to the first question
  any reader of a recurring pilot asks, which is whether it is worth its cost.
- **Components outside the caller's scope.** When a caller narrows the scope and the
  summary does not say so, a fully-honoured override reads as a truncated run, and
  the next reader concludes the skill dropped components on its own.
