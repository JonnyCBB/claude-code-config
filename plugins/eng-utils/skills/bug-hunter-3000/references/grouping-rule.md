# The grouping rule

Read this before the grouping step in `SKILL.md` section 4, and before changing it.

Grouping consolidates packets that describe **one** defect found from two sides, so the pipeline
spends one set of verifiers on it instead of two. Fan-out creates that duplicate class: a defect
spanning a call boundary is discovered independently by the mandate owning the caller and the
mandate owning the callee, and neither finder knows the other exists.

This rule has been rewritten four times. `design-history-and-failed-approaches.md` section 4
records what each version cost; read it before you decide any clause here is arbitrary.

## The test

Two packets group when **each one's evidence cites the other's declared defect site.**

Three parts, all load-bearing:

**1. Only across mandates.** Two packets from the same finder are never eligible.

_Tested and rejected: scoping this bar to the same **file** instead._ The motivation is real --
a mandate covering several files blocks pairs that are in different files, and the partition rule
deliberately groups leftover files into shared mandates. But measured on a 17-packet fixture the
amendment changed 8 of 136 pairs and produced byte-identical output, because the one cross-file
citation among those pairs matched nothing, and on the merits the unblocked candidates were five
distinct defects sharing only a request path. The two pairs there with a plausible one-defect
reading were _same-file_ and would stay blocked either way -- the real signal was intra-file, so
the amendment points away from it. It also silently deletes the magnet count: that count only ever
runs inside a same-file comparison, so keying its exclusion to files makes it identically zero and
an enclosing citation always qualifies. `design-history-and-failed-approaches.md` section 12 has
the detail. If you revisit this, bring a fixture containing a same-mandate, different-file pair
that qualifies bidirectionally -- none has been observed yet. That is a
different situation -- one finder forwarding two views of its own mandate -- and those packets were
already written to be verified independently. This also keeps same-mandate pairs out of the
multi-partner test below, where they used to create phantom conflicts.

**2. Citations come from everywhere in the packet EXCEPT the Coverage record and the sweep
table.** State it as an exclusion, not a list -- an earlier four-field list read as exhaustive and
left five citation-bearing fields undefined, and a qualifying citation turned up in one of them
(`Observed behavior`). Everything a finder asserts about its own candidate counts: the mechanism
claim, Observed behavior, Conditions, Code locations, Boundary and call-graph info, Evidence links,
the reproduction plan, Impact and exposure evidence.

The two exclusions are load-bearing and measured. The Coverage record and sweep table log what a
finder merely _read_, so counting them fuses unrelated defects: one shared preamble cited
`ServiceHandler.java:175-180` -- inside one declared site, enclosing another -- and because three
packets shared that preamble by reference, counting it would have minted six spurious pairs from a
single context read. Another Coverage record cited a range enclosing all three of a mandate's
declared sites.

Note that finders may carry Component, Coverage and sweep content **by reference** in a shared
preamble file rather than inline. Excluded content stays excluded wherever it physically lives;
resolve the reference before deciding what is in scope, and do not treat a preamble as packet
evidence.

Restricting the test to the mechanism claim alone was tried and made the rule blind, because the
finder's output contract routes `file:line` into the NEUTRAL location fields. The rule must read
where the contract writes.

**Parsing citations is the step most likely to fail silently.** Finders use several shorthand
forms, and a resolver that mishandles one produces a clean-looking "zero groups" rather than an
error. Concretely, from one measured run:

- **Bare continuations** inherit the filename from earlier in the same list:
  `` `CustomMetrics.java:36-45`, `:62-72`, `:266-312` `` is three citations of one file. Resolve them
  against the most recent full path **within the same list or sentence**, never across paragraphs.
  This exact form was mis-parsed three times while this rule was being written, and the citation it
  hid was the one that formed the run's only group.
- **Match paths by suffix, and treat an ambiguous suffix as unresolvable.** Do not assume declared
  sites arrive fully qualified. The finder contract asks for a repo-root path, and finders have
  written `metrics/CustomMetrics.java` and bare `ServiceHandler.java:174-186` anyway; citations are
  partial more often than not. Strict full-path equality therefore
  compares almost nothing -- a mechanical implementation of an earlier draft silently matched zero
  pairs for exactly this reason. So treat a citation and a declared site as the same file when one
  path is a suffix of the other at a `/` boundary. Where that suffix matches two distinct files in
  the component -- and it can, two different `ConfigUtils.java` files exist in this repo's
  `home-page-serving` tree -- the citation is unresolvable: report it, do not pick one.
- **A form you cannot resolve mechanically** -- a detached class name with no path, for instance --
  is reported as an unresolvable citation, never silently treated as absent.

**3. A citation is compared against the other packet's _declared defect site_** -- the line the
other finder labelled as where a fix lands. Never declaration against declaration. Two packets
that merely declare nearby lines in one file are two defects in that file, not one defect seen
twice.

## Containment resolves by count, not by direction

Compare a citation to a declared site **only when both name the same file.** A citation
`CustomMetrics.java:266-312` says nothing whatever about a declared site in
`ReasonedHybridFeedPage.java:285-292`, even though 285-292 falls numerically inside 266-312.
Omitting that word once made the count file-blind, which turned both directions of the only genuine
pair in a run into magnets and produced zero groups.

Within the same file:

- A citation **inside** the declared site qualifies. A caller naming the specific call lines within
  a callee's declared range is the ordinary shape of this evidence.
- A citation **identical** to the declared site qualifies. It is the strongest evidence available,
  and it is both inside and enclosing, so say so rather than leaving the case to be argued.
- A citation **enclosing** the declared site qualifies **unless** the enclosing range holds more than
  one **distinct partner**. Count partners, not sites: declared sites that overlap each other are one
  partner, because they are one place described twice. Two or more distinct partners is the magnet
  case; the intended target alone is not.

"Enclosing" is **numeric containment and nothing else**: for a citation `start-end` and a declared
site at line `n`, it holds only when `start <= n <= end`. Do the arithmetic and write the interval
down. It is not topical proximity -- citing the method that a defect sits near, or the region a
defect "belongs to", is not enclosure, and neither is citing a range in the same file. A measured run
applied the numeric test correctly during the run, then reversed itself while writing the summary by
asserting that a citation of `:230-356` enclosed a declared site at `:192`. It does not; 192 is below 230. Nothing downstream re-checks a grouping claim, so an unchecked reversal at write-up time is the
last word.

Counting partners rather than sites is the whole of it, and it replaced two separate exclusions that
between them broke the clause. The earlier version ignored sites sharing the target's mandate, which
sounds narrow and is not: a defect site always lies inside its own finder's mandate, and the
partition rule gives each file to one mandate, so **every** declared site in a file shares the
target's mandate. The count was therefore always zero and an enclosing citation always qualified --
including the case this clause exists to stop, where a caller cites a whole method holding three
separate callee defects and would group with all three.

The overlap test gets both cases right without referring to mandates at all, which is why it cannot
go inert the same way:

| Situation                                                                           | Sites in the enclosing range | Partners              | Outcome                 |
| ----------------------------------------------------------------------------------- | ---------------------------- | --------------------- | ----------------------- |
| One finder's two nested views of one place (`:174-180`, `:176-179`)                 | 2                            | **1** -- they overlap | qualifies               |
| A caller citing a whole method holding three distinct defects (`:10`, `:20`, `:30`) | 3                            | **3**                 | magnet, vetoed          |
| A packet declaring two sites because the fix lands in two places                    | 2                            | 1 or 2 by overlap     | judged on the same test |

The first row is measured: two independent assessors and a mechanical replay all treated that pair's
enclosing citation as qualifying, and an earlier wording that vetoed it destroyed the pair this rule
exists to catch.

Scope the count to the current run and the current component, since grouping never crosses
components.

Excluding enclosure outright was tried and formed zero groups on a real run, declining even the pair
this rule exists to catch, where both finders had asked in writing to be grouped.
`design-history-and-failed-approaches.md` section 4 holds the counts.

## When a packet qualifies with two partners

**This section runs only after bidirectional qualification.** A packet has a "partner" when the pair
already qualifies both ways. One-directional pairs are near-misses and never reach here -- asking
which declared site each partner matched has no answer when the partner matched none of them.

Not automatically unsure. Resolve by asking which of its declared defect sites each partner
matched:

- **Different declared sites** -> two separate groups. One caller legitimately spans two callee
  defects. The caller is verified once per group, which costs one extra verification and never
  fuses two defects.
- **The same declared site**, and the two partners are from different mandates from each other and
  do not qualify with each other -> genuinely unsure. Do not group; report a near-miss.

That second condition must be checked only against **eligible** partner pairs. Same-mandate
partners were never eligible to qualify with each other, so their failing to qualify is vacuous
and is not evidence of a conflict. An earlier wording omitted "from different mandates from each
other" and therefore fired "do not group" unconditionally on every same-mandate partner pair,
which is the fourth-iteration recurrence of the failure this rule keeps hitting.

## When unsure, do not group

A wrongly grouped pair loses a real defect permanently: it never gets verified and never reaches
the portfolio. A wrongly separated pair only costs verification time. Those are not comparable, so
break ties toward separating.

## Parse failures are not absences

Every packet declares at least one defect site by contract, and some legitimately declare two when
a fix lands in two places. So the invariant is **per packet, not aggregate**: if any packet yields
zero parsed defect sites, that is a formatting variant you did not handle. Name the packet and
reread it.

Do not assert `sites == packets`. A multi-site packet makes that inequality normal and the check
raises a false alarm. Anchor the parse at start-of-line: prose elsewhere in a packet can mention
the words "defect site" and a substring match will read it as a declaration.

Measured: one mandate emitted all nine of its defect sites as markdown bullets, a strict parser
returned zero, and that read as "this mandate found nothing" -- silently dropping the run's
highest-yield mandate out of grouping entirely.

## What is never the test

- Similar-sounding summaries.
- A shared line that neither packet calls its defect site. Several caller-side mandates
  legitimately reach the same shared callee; a common downstream line is the predictable false
  positive.
- Shared context reads.
- Anything in the Coverage record or sweep table.

## Worked examples, both from one measured run

**Correctly not grouped.** A `ServiceHandler` mandate and a `CustomMetrics` mandate both reported a
metric-labelling problem at the boundary between them. They did not group, and should not have.
`ServiceHandler` declared sites at `:174-180`, `:176-179`, `:409`, `:411`, `:418`, and cited
`CustomMetrics.java:182-191`. `CustomMetrics` declared `:138`, `:199-200`, `:282-290`, and cited
`ServiceHandler.java` at `:143-145`, `:270-275`, `:283-291` and `:292-295`. Neither side's citations
touch any of the other's declared sites, in either direction. They agree something is wrong at the
boundary and disagree entirely about which line a fix lands on, which is two defects, not one.

**Correctly grouped, and the citation that nearly hid it.** A `CustomMetrics` packet cited
`ReasonedHybridFeedPage.java:285-292`, identical to a `pages` packet's declared site. The `pages`
packet cited back `` `CustomMetrics.java:36-45`, `:62-72`, `:266-312` `` -- and that third, bare
continuation encloses the `CustomMetrics` packet's declared `:282-290`, with no other eligible
declared site in range, so the magnet count passes. Mutual, cross-mandate, one defect at the
page/metrics boundary seen from both ends. Two independent agents applying this rule formed exactly
this group and no other.

It is worth knowing how nearly it was missed. The `:266-312` continuation was mis-read as absent
three separate times while this rule was being drafted, each time producing a confident "one
direction only, do not group". Two of one agent's three parser iterations dropped it too. A rule
this dependent on citation parsing needs the parsing spelled out, which is why it now is.

**A near-miss worth reporting.** A `pages` packet cited `ServiceHandler.java:174-186`, which
encloses two declared sites from the `ServiceHandler` mandate. Under the magnet rule as corrected
above those two are same-mandate and do not count, so the citation qualifies -- but the pair still
fails, because neither `ServiceHandler` packet cites `ReasonedHybridFeedPage.java` at any line. One
direction only.

**A near-miss that was decided correctly and then written up wrongly.** A `pages` packet declared
`ReasonedHybridFeedPage.java:192` and cited `CustomMetrics.java:319-321`. A `metrics` packet declared
`CustomMetrics.java:319` and cited `ReasonedHybridFeedPage.java:285-291` and `:230-356`. The first
direction qualifies: `319-321` encloses `:319`. The second does not, because `192` is below both
`285` and `230`. One direction only, so the pair does not group -- which is what the run concluded
while it was running.

Writing the summary, it reversed itself: it claimed `:230-356` "encloses" `:192`, declared the pair
should have been grouped, and recorded a self-criticism for having missed the containment rule. The
original decision was right and the correction was wrong. Had it acted on the reversal it would have
merged two distinct defects into one verification group and lost one of them, which is exactly the
outcome "when unsure, do not group" exists to prevent. The conservative default held even though the
reasoning about it did not.

Two things to take from it. Re-examining a grouping decision is only worth anything if the interval
arithmetic is redone -- a reversal argued from memory of what a packet "was about" is not a check.
And a near-miss reported under section 7 must **show the intervals and the site line**, so that
`192 not in 230-356` is on the page. A near-miss recorded as prose reasoning can assert an enclosure
that no reader can test.

Report pairs like this in section 7. The near-misses are where a real defect would be lost, and a
reader cannot otherwise tell a conservative pass from one that never ran.
