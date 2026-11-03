# The run loop

Everything `SKILL.md` section 4 does between a component and a run record. Read this before
changing the loop: most of what makes it correct is not visible in the pseudocode.

## 1. Mandates: partition by file SIZE, never by package; to a TARGET, never to a fixed count

**~500 lines per mandate.** The count falls out of the component: a 1,500-line component yields 3
mandates, an 11,000-line one yields ~22.

The algorithm, deterministic so two runs on one component partition identically:

1. Rank files by line count, descending.
2. **Never split a file across mandates.** A file is the smallest unit.
3. Any file at or above the target becomes its own mandate.
4. Greedy bin-pack the remainder: each file joins whichever open mandate holds the fewest lines.

Step 3 means a 426-line file gets a mandate to itself rather than being padded. Overshoot on a
single large file is fine; the target governs the *bins*, which is where dilution happened.

**Do not reintroduce a fixed count**, and not in disguise as "cap the count, then bin-pack the
remainder". Measured at `max=8` on an 11,181-line component: four solo mandates yielded **5.73
packets per 1,000 lines**, four bin-packed mandates of ~2,490 lines yielded **0.50** — an 11x gap,
same component, same finder, same prompt.

**Do not target much below ~250 lines either.** Per-finder context re-reading is roughly fixed and
dominates below that, and more defects fall *across* mandate boundaries, where the grouping rule
breaks ties toward not grouping.

**Batching.** Dispatch in batches of `parallelism`, **default 10**, capped by the runtime's 20. Within a
batch every Agent call goes in **one message** — that is the only thing that makes them parallel.
A batched run is not a bounded run: every mandate is still dispatched.

**The binding constraint is the orchestrator's context, not the agent count.** The finder holds no
`Write` tool, so packets would return through the orchestrator's context — at 42 finders, ~2.8MB
before a single verifier runs. Measured outcome: an orchestrator reached verification with too
little context left to use it, and verified 5 of 22 selected candidates for a reason that had
nothing to do with their band. This is why the finder writes its own packet to disk
(`index_packets.py`) and why the finder count is a context budget, not just an agent budget.

## 2. The lens pass

A second finder pass, after the file pass, dispatched to the same `agents/bug-hunt-finder.md`
type. A **lens mandate** is a bug *class* over the whole component where a file mandate is a set of
files; same agent, same packet contract.

It exists because **a defect whose two halves live in different mandates belongs to no file-slice
finder.** Measured: two DI-scoping defects spanned three modules and were found only because the
provider file happened to be a solo mandate. That is luck, not method.

| Lens | What it hunts | Measured instance |
| --- | --- | --- |
| **Resource lifecycle & scoping** | Providers, factories, pools, clients whose scope or shutdown does not match how they are consumed | Two `@Provides` missing `@Singleton`, creating ~14 and 4 redundant thread pools |
| **API-shape consistency** | Every call site of one API against the others; the outlier is the finding | `Collectors.toMap` with no merge function where four siblings had one; an SLF4J call with one placeholder and two arguments |
| **Asymmetric siblings** | Parallel implementations that should behave alike and diverge | `convertTrack` omitting a field `convertEpisode` sets |
| **Contract drift across boundaries** | Two sides of a boundary reading or writing different fields, defaults, or units | A gate reading `semSensitivityLabel` while the path it gates reads `isSemSensitiveContent` |
| **Dead / inert declarations** | Configuration, guards, retries, metrics that cannot take effect as written | A Resilience4j retry that can never fire, because the wrapped call converts every failure into a success |

**API-shape consistency is grep-shaped rather than read-shaped**, so it scales to a whole
component for a fraction of a reading finder's budget. Do not drop it as trivial.

**Lenses run blind to the file pass.** A lens told a region is covered searches it less, and recall
is the only reason the pass exists. Blindness costs one duplicate packet; anchoring costs a defect.

**This is not the degraded-path sweep**, which every finder runs *within* its own mandate. A lens
is whole-component, run once. Neither replaces the other.

## 3. Grouping

Consolidates packets describing **one** defect found from two sides, so the pipeline spends one set
of verifiers on it. Fan-out creates that duplicate class: a defect spanning a call boundary is
discovered by the mandate owning the caller and the mandate owning the callee, and neither finder
knows the other exists.

**This rule has been rewritten four times, and every version that shipped on reasoning alone
introduced a defect.** Treat a clause that looks arbitrary as load-bearing.

### The test

**Two packets group when each one's evidence cites the other's declared defect site.**

**1. Only across mandates.** Two packets from the same finder are never eligible — that is one
finder forwarding two views of its own mandate, and those were written to be verified
independently. *Scoping this bar to the same file instead was tested and rejected:* on a 17-packet
fixture it changed 8 of 136 pairs and produced byte-identical output, and it silently deletes the
magnet count below, which only ever runs inside a same-file comparison. If you revisit it, bring a
fixture containing a same-mandate different-file pair that qualifies bidirectionally — none has
been observed.

**2. Citations come from everywhere in the packet EXCEPT the Coverage record and the sweep table.**
State it as an exclusion, not a list: an earlier four-field list read as exhaustive and left five
citation-bearing fields undefined, and a qualifying citation turned up in one of them. The two
exclusions are measured — the Coverage record logs what a finder merely *read*, and one shared
preamble citing `ServiceHandler.java:175-180` would have minted six spurious pairs from a single
context read. Finders may carry Coverage and sweep content **by reference** in a shared preamble
file; excluded content stays excluded wherever it physically lives.

**Parsing citations is the step most likely to fail silently.** A resolver that mishandles a form
produces a clean-looking "zero groups" rather than an error.

- **Bare continuations inherit the filename** from earlier in the same list:
  `` `CustomMetrics.java:36-45`, `:62-72`, `:266-312` `` is three citations of one file. Resolve
  against the most recent full path **within the same list or sentence**, never across paragraphs.
  This exact form was mis-parsed three times while the rule was being written, and the citation it
  hid was the one that formed the run's only group.
- **Match paths by suffix at a `/` boundary, and treat an ambiguous suffix as unresolvable.**
  Finders write `metrics/CustomMetrics.java` and bare `ServiceHandler.java:174-186` despite the
  contract asking for repo-root paths, so strict full-path equality compares almost nothing — a
  mechanical implementation of an earlier draft matched zero pairs for exactly this reason. Where a
  suffix matches two distinct files (two different `ConfigUtils.java` files exist in one measured
  service tree), report it unresolvable; do not pick one.
- **A form you cannot resolve mechanically is reported**, never silently treated as absent.

**3. A citation is compared against the other packet's *declared defect site*** — the line the
other finder labelled as where a fix lands. Never declaration against declaration. Two packets
declaring nearby lines in one file are two defects in that file, not one seen twice.

### Containment resolves by count, not by direction

Compare a citation to a declared site **only when both name the same file.** Omitting that word
once made the count file-blind and produced zero groups.

Within the same file, a citation **inside** the declared site qualifies; **identical** qualifies;
**enclosing** qualifies **unless** the enclosing range holds more than one **distinct partner**.
Count partners, not sites: declared sites that overlap each other are one partner, because they are
one place described twice.

"Enclosing" is **numeric containment and nothing else**: for a citation `start-end` and a site at
line `n`, it holds only when `start <= n <= end`. Do the arithmetic and write the interval down. It
is not topical proximity. A measured run applied the test correctly during the run, then reversed
itself at write-up by asserting `:230-356` enclosed a site at `:192`. It does not; 192 is below 230.
Nothing downstream re-checks a grouping claim, so an unchecked reversal at write-up is the last word.

| Situation | Sites in range | Partners | Outcome |
| --- | --- | --- | --- |
| One finder's two nested views of one place (`:174-180`, `:176-179`) | 2 | **1** — they overlap | qualifies |
| A caller citing a whole method holding three distinct defects (`:10`, `:20`, `:30`) | 3 | **3** | magnet, vetoed |
| A packet declaring two sites because the fix lands in two places | 2 | 1 or 2 by overlap | judged on the same test |

Excluding enclosure outright was tried and formed **zero** groups on a 44-candidate run, declining
all 12 pairs that had a citation in one direction — including the pair the rule exists to catch,
where both finders had asked in writing to be grouped.

### Two partners, parse failures, and the default

**When a packet qualifies with two partners** — and this runs only after bidirectional
qualification — resolve by asking which declared site each partner matched. *Different* sites means
two separate groups; one caller legitimately spans two callee defects. *The same* site, where the
two partners are from different mandates from each other and do not qualify with each other, is
genuinely unsure: do not group, report a near-miss. Check that second condition only against
**eligible** partner pairs — same-mandate partners were never eligible, so their failing to qualify
is vacuous.

**Parse failures are not absences.** Every packet declares at least one defect site by contract, so
the invariant is **per packet, not aggregate**: if any packet yields zero parsed sites, that is a
formatting variant you did not handle — name the packet and reread it. Do not assert
`sites == packets`; a multi-site packet makes that inequality normal. Anchor the parse at
start-of-line, or prose mentioning the words "defect site" reads as a declaration. Measured: one
mandate emitted all nine of its sites as markdown bullets, a strict parser returned zero, and that
read as "this mandate found nothing" — silently dropping the run's highest-yield mandate.

**When unsure, do not group.** A wrongly grouped pair loses a real defect permanently; a wrongly
separated pair only costs verification time. Those are not comparable.

**Never the test:** similar-sounding summaries; a shared line neither packet calls its defect site;
shared context reads; anything in the Coverage record or sweep table.

### Worked, both from one measured run

**Correctly NOT grouped.** A `ServiceHandler` mandate declared `:174-180`, `:176-179`, `:409`,
`:411`, `:418` and cited `CustomMetrics.java:182-191`. `CustomMetrics` declared `:138`, `:199-200`,
`:282-290` and cited `ServiceHandler.java` at `:143-145`, `:270-275`, `:283-291`, `:292-295`.
Neither side's citations touch any of the other's declared sites, in either direction. They agree
something is wrong at the boundary and disagree about which line a fix lands on: two defects.

**Correctly grouped.** A `CustomMetrics` packet cited `RankedHybridFeedPage.java:285-292`,
identical to a `pages` packet's declared site. The `pages` packet cited back
`` `CustomMetrics.java:36-45`, `:62-72`, `:266-312` `` — that third bare continuation encloses the
`CustomMetrics` declared `:282-290`, with no other eligible site in range, so the magnet count
passes. Mutual, cross-mandate, one defect seen from both ends.

### Fingerprint merge and same-site merge are NOT grouping

Both run **after** grouping and are exact-equality operations, where grouping is mutual citation.
Conflating them re-breaks the most-rewritten rule in this skill.

- **Fingerprint merge.** A lens packet and a file packet describing one defect carry the same
  root-cause fingerprint. Merge into one candidate and **record both finders on it** — two
  independent finders reaching one defect is real evidence about its strength. Disclosed limit: the
  fingerprint is exact-match hashing of free text, so two phrasings of one defect will not merge.
- **Same-site merge.** Collapse candidates declaring an **identical `defect_site` string** with
  different fingerprints. This catches the file-pass/lens-pass shape mutual citation cannot reach,
  because the lens pass is blind to the file pass so neither cites the other. The **first**
  fingerprint in sort order becomes the primary; all constituent fingerprints and mandates go in a
  `merged_from` list so packet re-read, portfolio naming and resolver keying can reach every
  constituent. On a real 132-candidate run, 26 sat on 12 repeated site strings, all 12 cross-pass.

## 4. Bounded verification

**Applied automatically above the ceiling, and never put to the caller.** `SKILL.md` section 8
states the bound itself and is the only place that number lives.

An unbounded component-scoped run costs well over a hundred agents and has been measured overrunning
a session limit mid-run. **An overrun is not a partial result:** the digest is written at the end, so
an overrun produces no readable artifact at all, which is why the ceiling is enforced up front
rather than discovered.

**It is not a top-N cut.** Bands reproduce and within-band order does not, so bound on bands —
`verdicts-and-bands.md` section 4 is canonical for the measurement behind that.

**The ceiling is about the reader, not only the budget** — a digest carrying a hundred candidates
is one nobody reads to the end. So if a future change makes verification cheap, it still stands.

### Fill order within a band

1. **User-facing first**, by `share_absent`: `null` (has a resolved share) → `NOT_QUERIED` →
   `NO_INSTRUMENT` → `NOT_REQUEST_SCOPED`. On a real 132-candidate run 55 were
   `NOT_REQUEST_SCOPED`, and under the old fingerprint-only rule 8 of 22 selected candidates were,
   consuming slots that could have gone to user-facing candidates from the next band down.
2. **Fingerprint-ascending within each tier.** Fingerprint order is right precisely because it is
   *meaningless*: uncorrelated with severity, so it cannot smuggle back within-band ranking, and
   deterministic, so two runs select the same candidates.

This does not change the banding rubric. Say in the run summary that the fill order prefers
user-facing candidates — a reader who sees 3 of 41 verified will otherwise assume the 3 were worst.

### Batches, controls, and the shortfall

**Dispatch verification in batches of 8 candidates (16 agents: 8 x 2 axes), and every batch runs.**
The runtime allows **20 concurrent subagents** — measured, with finders repeatedly losing the race to
it — so 8 leaves headroom where 10 sits exactly on the cap and anything higher exceeds it: the second
axis makes every candidate cost two agents. `SKILL.md`'s loop sketch carries this number too —
**move both or neither**.
A batch boundary is NOT the run boundary. Observed, when batches were 5: an orchestrator stopped
after batch 1 (5 of 22) because the skill discussed "the agent budget" without defining it, and
invented one equal to the batch size — with substantial context remaining.

**Always verify one or two control candidates from outside the bound, sampled without regard to
band.** Sort every unverified candidate by fingerprint ascending and take positions `0` and
`len(pool) // 2` — zero-indexed, so a pool of four gives 0 and 2. The formula is spelled out because
"the middle" is ambiguous for an even-length pool, and a control whose selection rule shifts between
runs cannot be compared across them.

Their purpose is measurement, not coverage. Bounding verifies the candidates most likely to be real,
so the confirmation rate stops being evidence: one bounded run returned 7 of 7 `CONFIRMED` with zero
discards, which says more about selection than about the verifiers. **Do not select the
lowest-banded candidates as controls** — that was tried and cannot do the job, because low band means
low *urgency*, not likely-*false*, so it handed the axes two straightforward true positives. Report
controls separately and read them as a diagnostic: if they keep coming back confirmed, either the
finders are unusually accurate or an axis is rubber-stamping.

**When the top band alone exceeds the ceiling, the ceiling wins and the shortfall is named.** Verify
as many as the ceiling allows, mark the remainder `DEFERRED_UNVERIFIED`, and record `cause: CEILING`
with a reason saying **the ceiling rather than severity stopped the run** — **not "cost"**, a word a
run borrowed to write "cost (wall clock)" and stop on the clock. Never silently drop the excess.

**What that forbids is a LOWER band, not `Not triaged`.** Writing `Not triaged` on the excess is
required — see below — and it is not the rebrand this warns against, because it says nobody checked
rather than claiming somebody checked and found it minor. But it does cost something, and the cost
is why `shortfall.reason` is not optional here: `Not triaged` renders last and collapses once it
passes five, so a deferred top-band candidate now sits inside a fold with nothing on its own row
saying it was urgent. **The urgency lives only in `shortfall.reason`, which renders in the
always-visible header.** Say there that the ceiling stopped the run, and name them.

**Bounding never discards.** Every unverified candidate keeps its full packet in the portfolio,
marked `DEFERRED_UNVERIFIED` with `band: "Not triaged"`, and appears in the digest by name. That is
what makes bounding legitimate and quiet subsetting not.

**The band the fill order used does not survive into the record.** It was computed from finder
evidence to decide who got verified; once the bound has closed, nobody has checked the remainder and
there is no scrutiny to assign, so they are written `Not triaged` — which is the absence of a band,
not a demotion to a lower one. `digest_model.py` rejects a record that pairs `DEFERRED_UNVERIFIED`
with anything else, or `Not triaged` with a state somebody did check. Measured 2026-09-11: 46
unverified candidates carried `Read closely`, `Worth a look` and `Skim` into the record, and the
digest rendered the whole unchecked tail as expanded rows reading "Not checked" instead of the
one-click list.

**A scope override is not a bounding instruction, and never was.** Nor is bounding a caller opt-in:
asking was measured on a 63-candidate run to produce no new information, because the person running
this skill has usually never run it. What survives is the *disclosure*, not the question.

## 5. Invariants the pseudocode does not show

Each replaced something tried and measured.

- **A finder returns zero or more packets** — it forwards every candidate its own static check
  failed to kill, so flatten. Measured against a single 564-line file: six finders produced ~31
  candidate-grade observations and forwarded six under the old one-per-mandate rule; one defect four
  finders noticed was forwarded by none. Zero findings for a mandate is also a complete result.
- **Both axes dispatch together, and intent always runs** — unconditionally, even for a candidate
  whose mechanism later comes back `REFUTED`. Neither verifier sees the other's result or progress.
- **A finder that dies is re-dispatched once, without asking anyone.** If the retry also fails,
  record the mandate as an unsearched gap in the digest's coverage and carry on. It is never a
  question: the answer is always the same, and the caller cannot weigh "re-run one search" against
  "accept a hole". **What must never happen is silence** — a finder that vanished and a slice that
  came back clean are indistinguishable otherwise. Measured: one lens finder was interrupted mid-run
  and nothing in the pipeline noticed; the loss was visible only because a human saw it happen.
- **No disposition stops the loop**, and there is no cap on components. A run does not stop at the
  first confirmed candidate. **Do not reintroduce a per-team cap** — `scope-and-safety.md`
  section 3 holds why it is retired.
- **When the run is ENDED rather than choosing to stop — context gone, killed, restarted, and
  `SKILL.md` section 8 is canonical on why — produce the digest with the candidates that completed
  the *full* pipeline, and write every candidate that did not, whether never started or started and
  unfinished, into `findings` as `DEFERRED_UNVERIFIED` with `band: "Not triaged"`, with a
  `shortfall`.** A record carrying only the ones that finished renders as a complete run.
- **`impact_exposure` is `UNKNOWN` only after a query was actually attempted** and either failed or
  found no instrumentation. It is never the value that simply arrives from upstream.
- **Report projected verification cost (3 agents per candidate) before spending it.** Information
  only: the ceiling is the bound, and `digest_model.py` refuses a `CEILING` claim below it but
  cannot catch an improvised bound under any other cause — that one rests on this rule.
- **Optional acceleration, not a dependency.** A human who explicitly asks may get the loop as a
  Workflow script. The scheduled path must never depend on it firing, and nothing in this skill is
  itself an opt-in on a scheduled run's behalf.
