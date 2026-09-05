# Run Record Schema

The JSON contract between the orchestrator and `scripts/digest_model.py`. The
orchestrator assembles this record at the end of a run and pipes it in.

**This file and `scripts/digest_model.py` must not drift.** The script's
`_RECORD_CHECKS` and `_FINDING_CHECKS` dispatch tables are the executable form of
what is below, and they reject an unknown key by name rather than ignoring it --
so a field added here and not there fails loudly on the next run rather than
being silently dropped from the digest.

Validation reports **every** problem, not the first, each naming its field path
(`findings[2].fingerprint`). The caller repairing this record is an agent, and it
will fix exactly what it is told about and re-run.

**Contents.** Read the section for the field you are filling; you do not need the
whole file.

- [Top level](#top-level) and [Per finding](#per-finding) -- the two field tables
- [Every string in this record is read by someone who has never seen this skill](#every-string-in-this-record-is-read-by-someone-who-has-never-seen-this-skill) -- the banned-vocabulary table
- [Nothing in this record writes the heading](#nothing-in-this-record-writes-the-heading)
- [`shortfall.reason` completes a sentence](#shortfallreason-completes-a-sentence)
- [Reader-facing prose is a finished thought](#reader-facing-prose-is-a-finished-thought-and-the-validator-enforces-it) -- **canonical for the measured truncation counts**
- [`observed_symptom` / `observed_full`](#observed_symptom-is-one-line-observed_full-is-everything-else)
- [A two-arm reproduction needs every arm read](#a-two-arm-reproduction-needs-every-arm-read-before-anything-is-written)
- [`exposure`](#exposure), [`tier`](#tier-is-a-closed-set-and-it-reaches-the-reader), [`effort`](#effort-is-an-estimate-and-stays-one)
- [`share`](#share-because-a-percentage-cannot-be-recovered-from-the-prose) -- **canonical for the share-derivation figures**
- [`share_absent`](#share_absent-because-three-different-absences-were-rendering-alike)
- [`permalink`](#permalink-and-why-a-branch-link-is-rejected) and [`permalink_resolution`](#permalink_resolution-because-null-cannot-say-whether-anyone-looked)
- [`provenance` and `provenance_resolution`](#provenance-and-provenance_resolution-the-change-that-wrote-the-line) -- **canonical for the no-author rule**
- [`exposure_resolution`](#exposure_resolution-proof-that-somebody-queried) -- **canonical for why an UNKNOWN exposure is only meaningful once somebody looked**
- [`method`](#method-what-was-done-including-what-was-not)
- [`verification`](#verification)

## Top level

| Field                   | Type             | Notes                                                                                          |
| ----------------------- | ---------------- | ---------------------------------------------------------------------------------------------- |
| `run_id`                | non-empty string | **Also the write gate's sentinel.** See the warning below.                                     |
| `scope_strategy`        | non-empty string | Which of the three strategies ran. See `scope-strategies.md`.                                  |
| `scope_label`           | non-empty string | Human-readable scope. Used for `<title>`, and for the heading on a multi-component run.        |
| `components`            | non-empty list   | Every component in scope. A single-component run's heading is this name.                       |
| `findings`              | list             | **May be empty.** A run that found nothing is valid: a clean component and an unsearched one must not look alike.                               |
| `coverage`              | list of objects  | What was searched. `files` is the list of file PATHS, not a count -- see below.                |
| `degraded_paths`        | list of objects  | The sweep table: one row per discriminator x downstream decision.                              |
| `dead_surface`          | list of objects  | Surfaces carrying no live traffic. Coverage information, not severity information.             |
| `cost`                  | object           | Requires `agents` and `wall_clock_minutes`.                                                    |
| `shortfall`             | object or null   | Requires `reason` when present, and nothing else. See below.                                   |
| `gate`                  | object           | Requires `dossiers_scanned`, `leaks_found`, `redaction_hits`.                                  |
| `repo`                  | object or null   | Requires `host`, `full_name`, `ref` when present. Provenance for line numbers.                 |
| `permalink_resolution`  | object           | Proof that linking was **attempted**. Requires `attempted`, `linked`, `unlinked` -- see below. |
| `provenance_resolution` | object           | Proof that commit tracing was **attempted**. Requires `attempted`, `resolved`, `unresolved`.   |
| `exposure_resolution`   | object           | Proof that the impact lookup was **attempted by an independent stage**. Requires `attempted`, `resolved`, `unresolved`, `resolver_agent_id` (string or list of strings for chunked dispatch). |

**`run_id` is load-bearing in a way that is easy to miss.** `write_artifact.py`
checks `if sentinel not in source` **before writing at all** and exits 2 on a
miss. Since the digest is a run-level artifact with no candidate fingerprint, its
sentinel is the run id -- so `render_digest.py` must emit the run id as visible
text or every real run fails before a byte lands.

## Every string in this record is read by someone who has never seen this skill

The digest is the artifact a stranger opens. They have not read `SKILL.md`, they do
not know what a mandate is, and **no word invented by this skill may appear in text
they see**. This is not a style preference: a reader who meets "141 candidates
deferred by the verification bound" cannot tell whether that is bad, and will
usually assume it is fine.

Banned in every reader-facing string -- `title`, `consequence`, `observed_symptom`,
`exposure.note`, `shortfall.reason`, and any prose in `fix_prompt`:

| Do not write        | Write instead                                               |
| ------------------- | ----------------------------------------------------------- |
| mandate             | the part of the code that was searched                      |
| Finder Packet       | the write-up in the report folder                           |
| finder / verifier   | name the action: "reproduced locally", "checked separately" |
| band                | group, or name it: "act now", "not checked"                 |
| disposition / state | the plain outcome: "a bug", "not a bug", "not checked"      |
| defect site         | the file and line                                           |
| fingerprint         | omit it; it is an internal key                              |
| axis / two axes     | say what was actually done, in words                        |
| deferred            | not checked                                                 |
| candidate           | possible problem                                            |
| coverage record     | what was searched                                           |
| degraded-path sweep | what happens when things go wrong                           |

Measured: one run's digest carried `Finder Packet` 143 times, `axis`/`axes` 298
times and `mandate` 5 times, almost all of it from prose the orchestrator wrote
into this record rather than from the renderer. Fixing the renderer alone does not
fix the digest.

**The rule binds hardest where text is COPIED, not written.** `mechanism.trail` and
`intent.trail` are reader-facing, and the obvious way to fill them is to paste the
verifier's report. Verifiers write for the orchestrator, in the skill's own
vocabulary -- "the candidate", "this packet", "the intent axis" -- so pasting is how
the vocabulary gets in even after the renderer is clean. Measured: after every
renderer string was fixed, `candidate` still appeared 76 times in one digest, 23 of
them in finding titles taken straight from finder output. **Summarise the trail in
your own plain words and keep the verbatim version in the report folder**, where a
reader who wants that level of detail has already opted in.

The test to apply before writing any string here: **would this sentence make sense
to the on-call engineer who owns this component and has never run this skill?** If
it needs a glossary, rewrite it.

## Nothing in this record writes the heading

The heading is `Bug report: <component>`, built by the renderer from `components`
(or from `scope_label` when a run covers more than one). **There is no field for a
summary sentence, and adding one back is the change to argue against.**

There used to be. A `thesis` field asked for "one plain-English sentence for the
hero", and it produced this: _"Twenty-eight parallel readings of this service turned
up seventy-six things worth a look; twenty-six were investigated two independent
ways, and eighteen of those are real..."_ Two readers rejected it independently
within a day of each other. One said it was "a lot of text in the title (like 5
lines)". The other said it read "like an article title for The Verge".

The second objection is the one that matters, and it is not about taste. **A summary
at the top of a machine-generated report has to be persuasive to justify its space,
and persuasive prose over machine findings reads as something to discount.** It
spends exactly the credibility the two independent verification passes earned. The
field was not misused; asking a model for a compelling one-sentence summary and
getting a compelling one-sentence summary is the field working.

It also could not be kept honest. A hand-authored sentence duplicates numbers the
renderer computes from `findings`, so the two drift the moment anything changes.
Measured: one finding was reblanded after publication and the surrounding prose still
read "all ten in the most urgent group" while the band header rendered `9`.

Everything that sentence carried is already on the page and computed rather than
asserted: the counts are the band headers, what was searched is the coverage section,
how far each finding got is its verdict column.

## `shortfall.reason` completes a sentence

When present, `reason` is rendered directly into the Not-checked band as:

> These were never looked at, because **&lt;reason&gt;**. Not because anyone decided
> they were unimportant.

So write a lowercase clause that finishes that sentence, in the reader's language,
with no trailing full stop. Good: `the run's checking limit was reached, and only
after every finding in the most urgent group had been checked`. Bad: `group, not
budget` -- that is the internal distinction, not a sentence, and it reaches the
reader verbatim.

**The distinction it encodes is load-bearing** and is the reason this field survived
when `unverified_count` and `statement` did not: a finding skipped for cost is a
scheduling fact about this run, while one skipped because its group was never reached
is a severity judgement. A reader who cannot tell them apart reads an unchecked
urgent finding as unimportant. `bounded-verification.md` is canonical for which case
applies.

The count is not in this record. The Not-checked band header already renders it from
`findings`, and stating it twice is how the last one went stale.

## Reader-facing prose is a finished thought, and the validator enforces it

`consequence`, `fix_prompt`, `mechanism.trail`, `intent.trail` and
`exposure.note` each render as their own block, so each must end in punctuation.
`digest_model.py` rejects one that does not.

**This file is the only place the measured counts live.** `digest_model.py` and
`SKILL.md` point here rather than restating them, because the first draft of this
change put one count in three files, revised it twice while testing, and shipped
two files disagreeing with each other about the same number.

**Measured, on the run that prompted this rule: 129 fields stopped mid-sentence
in a single record** -- 44 consequences, 25 reproduction trails, 24 exposure
notes, 20 of 21 fix prompts, and 16 contract-check trails. Every one came from
the same habit, an orchestrator assembling a field as
`f"...{other_field[:300]}"` because nothing said not to. The fix prompt is where
it hurt most, because that field is the artifact the report exists to hand over
and one reader copied a prompt that stopped at `has no arti`.

**Do not satisfy the rule by appending a full stop to a slice.** That produces a
field that passes and still says nothing, which is worse than the error. Write
each field as its own sentence. If you want the reconciled reasoning in the
report, it is already in the two trails -- pasting a truncated copy of it onto
the end of a fix prompt puts a second, shorter, worse version in front of the
reader.

**A fix prompt is a standalone instruction**, written to be copied and run
without the rest of the report for context: what to change, where, and what to
add as a regression test. It is not a summary of the evidence and not a place to
restate the verdict.

Three fields are excluded, and the exclusions matter as much as the rule.
`observed_symptom` and `observed_full` are **captured output** -- a stack trace
ends where the runtime ended it, and demanding punctuation there would push an
author into editing real evidence. Every `reason` field is a **sentence
fragment** by design, as the section above spells out for `shortfall.reason`.

## Per finding

Every key below is required. An unknown key is an error, reported by name.

| Field              | Type              | Notes                                                                                      |
| ------------------ | ----------------- | ------------------------------------------------------------------------------------------ |
| `fingerprint`      | string            | Must match `^[0-9a-f]{16}$`. Lowercase only -- see below.                                  |
| `state`            | enum name         | One of the eleven `FindingState` members. Ten dispositions plus `DEFERRED_UNVERIFIED`.     |
| `band`             | string or null    | `Act Now`, `Important`, `Low`, `Not checked`. Null **only** for a discarded finding.       |
| `title`            | non-empty string  | The finding, in a line.                                                                    |
| `consequence`      | non-empty string  | One line of plain English: what goes wrong for a user.                                     |
| `observed_symptom` | non-empty string  | The ONE most diagnostic line of real output. No line breaks, max 120 chars -- see below.   |
| `observed_full`    | string or null    | The complete verbatim capture, may be multi-line. Null when there is no more -- see below. |
| `defect_site`      | non-empty string  | `File.java:118`.                                                                           |
| `component`        | non-empty string  |                                                                                            |
| `tier`             | closed set        | `1`\|`2`\|`3`\|`4`\|`UNTIERED`. Bare value, not `Tier 2` -- the renderer formats it.       |
| `exposure`         | object            | Requires `basis`, `path_denominator`, `component_denominator`, `note`.                     |
| `effort`           | `S` \| `M` \| `L` | An **estimate**, from the finder's proposed fix complexity. Never measured -- see below.   |
| `mechanism`        | object            | Requires `verdict`, `trail`. The live-reproduction axis.                                   |
| `intent`           | object            | Requires `verdict`, `trail`. The blind-contract axis.                                      |
| `fix_prompt`       | string or null    | Required on every `Bug`; conditional form on `Your call`; null otherwise.                  |
| `permalink`        | string or null    | Verified source link, or null. Must be pinned to a 40-char SHA -- see below.               |
| `verification`     | object or null    | Requires the five keys below when present.                                                 |
| `provenance`       | object or null    | Written by `resolve_provenance.py`, never by hand. Key must be present -- see below.       |
| `method`           | object or null    | Requires `before_after` and `history_read`. Key must be present -- see below.              |

**Fingerprints are lowercase hex, and the validator rejects uppercase.** They are
both the within-band sort key and the cross-run deduplication key, so two
spellings of one fingerprint would sort apart and deduplicate as two distinct
defects.

**`band` is required for anything not discarded.** A non-discarded finding with a
null band has nowhere to render, so validation rejects it rather than letting it
vanish. Discards carry a null band because `SKILL.md` section 6 assigns a threat
level only to non-discarded dispositions.

### `observed_symptom` is one line; `observed_full` is everything else

`observed_symptom` renders in the **always-visible row** for Act Now findings, so
it is bounded: non-empty, **no line breaks**, and **at most 120 characters**, which
is what that row shows in full at the sheet's mono size. `digest_model.py` rejects
anything else by name.

**The bound is not the rule; it is the consequence of the rule.** The field is the
single most diagnostic line of real output -- **the exception and its message, or
the assertion that failed**. It is not the opening fragment of a stack trace, and
an author who reads only "make it shorter" will slice a trace to fit and reproduce
the exact defect this rejects.

Measured: an orchestrator filled this field with 200-400 character multi-line stack
traces on a 64-finding run. The row clipped every one of them mid-token, so a
reader saw a broken fragment on every single row where the evidence was meant to
be. 56 of the 64 were over the bound.

**Write the summary line yourself and put the raw capture in `observed_full`.** The
complete verbatim capture goes there, multi-line and unabridged; it is `null` only
when the one-line summary genuinely is the whole capture. The renderer shows the
first two lines of `observed_full` (falling back to `observed_symptom` when it is
null) under **What was observed**, and the remaining lines one click down as
"Show N more frames". Nothing is truncated -- the shortening is editorial, done by
you, and the original survives intact one field over.

That block renders for **every** finding in every group. Before it existed, the
symptom appeared only on Act Now rows, so on the measured run this required,
validated field reached the reader nowhere at all for the other 55 findings.

### A two-arm reproduction needs every arm read before anything is written

**When the mechanism trail carries a control, a counterfactual, or a before/after,
read every arm before writing any reader-facing string.** For a two-arm reproduction
there is no single most diagnostic line, because **the diagnosis is the difference**.

The two fields then do different jobs with it, and conflating them makes the title
worse:

- **`observed_symptom` carries the contrast.** It fits inside the bound above.
- **`title` stays a claim, not a data dump.** It must not assert something another
  arm refutes -- but do not pack arm-by-arm figures into it. Measured on a fixture:
  an author told to write the title "from both arms" produced a 152-character title
  reciting three arms' hit rates, where the plain claim was shorter, equally true,
  and the one a reader could actually scan.

Wrong -- written from the arm the orchestrator happened to store:

    observed_symptom: isChildAccount=false -> served[CHILD_SENSITIVE]=[audiobook:01]
    title:            Child-safety downranking is applied to adults, not to children

Right -- written from the trail:

    observed_symptom: adult: [audiobook] downranked to 0.0; child: [track, album, audiobook] all downranked
    title:            A child-account audiobook rule also downranks audiobooks for adults

Measured, and it reached a reader. The trail printed both accounts side by side: the
adult arm one content type, the child arm all three, which is the rule working. Every
stage below the orchestrator was right -- the finder's severity note said "adult users
silently lose audiobooks", and the reconciler wrote "child side byte-identical", which
says outright that children's behaviour does not change. The inversion came from the
one agent that had stopped reading trails in order to fit the run into a session, and
the owning engineer caught it after publication.

Two habits follow. **Re-read the trail before writing any reader-facing string** -- the
disk indexing that makes a large run survivable is what hides the second arm, so the
moment you are most efficient is the moment you are most likely to invert something.
And **an over-applied restriction is not a defeated one**: the corrected finding also
left Act Now, because firing a guard too widely meets none of
`behavior-dossier-and-verdict-schema.md` section 6's consideration-1 tests, while the
wrong headline had made it the most urgent item in the run.

### `exposure`

| Key                     | Notes                                                                       |
| ----------------------- | --------------------------------------------------------------------------- |
| `basis`                 | `MEASURED`, `ESTIMATED` or `UNKNOWN`. Provenance, not magnitude.            |
| `share`                 | The percentage, as data. Object or `null` -- see below.                     |
| `share_absent`          | Why there is no percentage. One of three names, or `null`.                  |
| `share_absent_detail`   | The finding-specific sentence, when there is one. Max 72 chars, or `null`.  |
| `path_denominator`      | `X% of <the page or path this defect lives on>`, max 80 chars -- see below. |
| `component_denominator` | The component's traffic. An absolute rate is normal -- see below.          |
| `note`                  | How it was measured, or why it could not be. Positive controls belong here. |

Both denominators are required because they differ by orders of magnitude and the
choice silently decides priority. `behavior-dossier-and-verdict-schema.md` section
6 is canonical on what to measure; nothing here restates a threshold from it.

**`component_denominator` holds the component's traffic, and an absolute rate is
the normal form.** This field was specified as `Y% of component traffic` and
measured otherwise: **0 of 82** values on the character-pro run were a share, and
all 82 were an absolute rate. That is not drift. You cannot write `Y% of component
traffic` without knowing Y, and on most of those findings nobody did (see
`share_absent` below), so the population is the only honest thing available. A
share is welcome where the harm rate is genuinely known, and requiring one would
invite the fabricated numerator `share` exists to refuse.

**`path_denominator` renders in the always-visible row, and the `of <what>` half is
the load-bearing one.** Validation rejects a value that leads with a figure and
never says what the figure is a share of, because **the renderer cannot supply that
noun**: `0.072%` is a share of searches in one service and of something else
entirely in the next, so any unit hardcoded in the renderer would be wrong
everywhere except where it was written.

Measured: the field held a bare `0.072%`, the renderer showed the figure and dropped
the rest, and a first-time reader met that number beside an **Act Now** finding and
named this column as the part of the report they could not understand. A figure that
small next to that group does not merely fail to inform -- it argues against the
group, and the phrase that would have resolved it was one click away.

**A value with no figure at all is normal and needs no apology.** "not measured --
the share of the path this sits on was not queried" is a complete answer, and the
row shows `not measured` with **no provenance word attached**. `basis` is deliberately
dropped in that case: it qualifies a figure, and printing `ESTIMATED` under an absent
one claims an estimate exists directly above the absence of one. Measured: one run
shipped `n/a` above `ESTIMATED` or `MEASURED` on all 76 rows, which reads as having
measured nothing.

**`basis` may be `UNKNOWN`, and the table above said otherwise until now.** The
closed set in `digest_model.py` has held three values since the resolver needed a
third; the table listed two. A producer reading only the table had no legal way
to say "attempted and not resolved", which is the majority case on a real
component.

### `share`, because a percentage cannot be recovered from the prose

A reader setting priority wants a percentage. 1% of requests and 25% of requests
are different problems, and neither prose denominator yields one.

    "share": {
      "numerator":   2.92,
      "denominator": 63000,
      "unit":        "req/s",
      "of":          "reaching this component"
    }

| Key           | Bound                                                              |
| ------------- | ------------------------------------------------------------------ |
| `numerator`   | A number, `>= 0`, and never greater than `denominator`.            |
| `denominator` | A number, `> 0`. Zero is the absence of a denominator, not a share. |
| `unit`        | Max 24 characters. `req/s` and `items/s` are the shape.            |
| `of`          | Max 52 characters. Completes `<n> of <d> <unit> ___`.              |

Validation **rejects** rather than truncates, on all four, so an over-long `of`
fails the whole record. The bounds are what the column fits without pushing the
finding text out of its own column; the rest goes in `note`.

**The renderer divides these. It never parses the prose fields**, and the reason
is measured. The figures below are canonical here and are not restated in
`agents/bug-hunt-impact-resolver.md` or `digest_model.py`, which point at this
section, because a count in two files is a count that will drift. Across the 16 findings on the character-pro run that carried a
`basis`, a renderer that took the leading figure from each prose denominator and
divided would have been right on 6, wrong on 7 where the two sides count
different things -- 21,427 metric _series_ over 25 grpc _pairs_, a rate over _5
regions_, a rate over _a Grafana panel name_ -- and fabricated on 3.

**Resolver non-conformance, measured on a 0.24.0 character-pro run.** 5 resolver agents returned
results for 52 candidates and produced zero structured share objects: 20 were prose strings, 15
were bare floats, 17 were null. Every one of the 35 non-null results carried real information
that never reached the reader because the renderer cannot use it. The orchestrator now validates
`share` on receipt and reclassifies non-conforming results as unresolved; the resolver brief
points here for the figures.

Two of those three are what this shape exists to make unrepresentable:

- One finding shipped `path_denominator: "~63,000 req/s"` beside a
  `component_denominator` of the same `~63,000 req/s`. Divided, that is **100%**:
  the largest figure the column can show, in its largest type, beside a **Low**
  band, on a finding nobody had checked. The numerator was never measured -- it is
  the population copied into the numerator's slot.
- One row's denominator names two populations, `items-before = 6,465,151/s` and
  `items-after = 3,752,452/s`, for a numerator of `5,362.7/s`. Those divide to
  **0.083%** and **0.143%**, 1.72x apart, from one cell. Only the stage that ran
  the query knows which population the defect sits under, and a renderer taking
  the first figure it finds picks the wrong one here.

**`unit` is one field covering both sides, on purpose.** A shared unit is the
only proof the two figures are commensurable, and it makes `21,427 series of 25
pairs` impossible to write rather than merely discouraged. The impact resolver's
brief used to ask for units inside `note`, in the form `numerator (per X) /
denominator (per Y)`, and stated outright that there was no separate unit key, so
a unit stated anywhere else was dropped silently. This is that key; the brief now
points here instead of describing the workaround.

**`of` completes the phrase `<numerator> of <denominator> <unit> ___`.** The
renderer cannot supply it, for the same reason `path_denominator` carries its own
noun: 63,000 counts searches in one service and items in the next.

Validation refuses a share that cannot be true: a numerator above its
denominator, a zero denominator, an empty `unit` or `of`, and -- the one that
catches the fabricated 100% above -- **any share at all sitting on `basis:
UNKNOWN`**, because `UNKNOWN` means no numerator was established, so there is
nothing to divide.

### `share_absent`, because three different absences were rendering alike

`share` is `null` on most findings and that is permanent, not a gap to be
closed: 66 of 82 findings on the measured run had no numerator. What was missing
is *why*, and the three reasons are not interchangeable for somebody setting
priority.

| Value                | Means                                                          |
| -------------------- | -------------------------------------------------------------- |
| `NOT_QUERIED`        | Nobody looked. The common case.                                |
| `NO_INSTRUMENT`      | No instrument for this harm exists.                            |
| `NOT_REQUEST_SCOPED` | An instrument exists but cannot attribute the harm to requests. |

`NO_INSTRUMENT` is the one that earns the distinction. It says the harm is also
**undetectable in production**, which is a priority input in its own right rather
than a gap in the run -- and it is the same fact the flagged finding's
`band_reason` already cites as "harm undetectable".

**The line between the last two is whether an instrument exists at all**, and the
first wording of this table got it wrong in a way worth recording. It read "a
request denominator does not apply at all", which describes the harm rather than
the instrument -- so a resolver handed the case the value was written FOR, a
timer-driven gauge, reasoned that a wrong deadline conceptually *is* a per-request
event, concluded a request denominator therefore did apply, and reached for
`NO_INSTRUMENT` instead. The set was right and the definition was not.

Worked, on three real findings from one run:

| Finding                                                    | Value                | Why                                                                                          |
| ---------------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------- |
| `CharacterProApolloModule.java:216-218`                    | `NO_INSTRUMENT`      | Nothing separates an empty registry from an absent one. No instrument exists to be scoped.  |
| `apollo_default_slot_mismatch_gauge`, read 0               | `NOT_REQUEST_SCOPED` | The gauge exists and reads 0, but it samples on a timer, so it can never tie harm to a request. |
| The other 74 findings on that run                          | `NOT_QUERIED`        | A metric may well exist; the impact pass did not reach them.                                 |

The middle row is the one to check yourself against: a reading of `0` from a
wrongly-scoped instrument is not a measured zero. `NO_INSTRUMENT` would overstate
the gap, and a `share` of `0` would be a fabricated measurement.

`share` and `share_absent` are mutually exclusive, and a record carrying neither
is read as `NOT_QUERIED` so that a run written before this field still renders.

**A `path_denominator` that is nothing but an absence token is dropped from the
column.** Found by re-rendering the real record rather than by reading the code:
65 rows produced a bare `UNKNOWN` and 1 a bare `not measured` directly beneath
the headline that already said so with a reason attached -- 66 of 82 rows stating
the absence twice, the second time without the reason. The match is against the
whole value and never a prefix, because "not established -- the share of requests
was not queried" is the shape this section documents as correct and it carries
the reason.

### `tier` is a closed set, and it reaches the reader

Two changes here, both because the field was previously validated as free text and
then never rendered.

**Closed set, so the rule below is enforceable.** `scope-strategies.md` section 5 forbids
folding `UNTIERED` into Tier 4, because Tier 4 is an assigned tier while `UNTIERED`
is the absence of one and merging them hides a cataloguing gap. Under free-text
validation nothing stopped a run doing exactly that and the schema could not tell.
`4` and `UNTIERED` are now distinct legal values and anything else is rejected by
name.

**Bare value, not `Tier 2`.** The value is data; `Tier 2` is presentation.
`UNTIERED` has no natural "Tier N" spelling, so accepting the prefixed form would
make the set inconsistent with its own absence case -- and writing "Tier UNTIERED"
would perform in presentation the fold the rule forbids in data. Measured need:
the canonical fixture emitted `Tier 1` while a real run emitted `2`, so two
producers had already diverged.

**It renders in two places.** The component and formatted tier appear in the
expansion, satisfying the threat rubric's fourth consideration ("report the tier
itself"). `UNTIERED` additionally gets a marker on the always-visible row, because
The rule asks for a _visible stratum_ and a marker inside a collapsed expansion is not
one. A real tier gets no row marker: it is context, and on the common
single-component run every candidate shares it, so a column would be constant
noise.

Measured gap this closed: `render_digest.py` previously contained zero occurrences
of `tier`. The field was required, validated, carried into the render model, and
dropped -- so an `UNTIERED` component's findings rendered identically to a Tier 1
component's.

### `permalink`, and why a branch link is rejected

The reader's only route from a finding to the code is this link, so it has one
job: land on the line the finding is actually about.

`digest_model.py` enforces the shape `https://<host>/<owner>/<repo>/blob/<40-hex
SHA>/<path>#L<line>`. The pinned SHA is mandatory **by pattern**, which means a
branch-name link cannot be represented at all. That is deliberate: a branch moves,
and when it does the link keeps resolving while silently pointing somewhere else.

**Measured, on the run that added this field.** The examined checkout was a local
review branch where the defect sat at `InfluenceModule.java:164`. The same
`@Provides` was at `:168` on the pushed ref, and `:164` there held an unrelated
`.build();`. A `master` link would have sent every reader of two findings to the
wrong code, with nothing on the page admitting it.

**Emit a permalink only after proving the file matches.** Compare the defect
site's file at the pinned ref against the checkout the finder read; they must be
byte-identical. If they differ -- unpushed branch, local edit, dirty tree -- emit
`null`. The digest then renders the path as plain text and says why, which is a
worse reader experience and an honest one.

`null` is therefore a normal value, not a failure. Nine of eleven findings on the
measured run linked cleanly; two did not, and saying so cost less than one wrong
link would have.

### `permalink_resolution`, because `null` cannot say whether anyone looked

| Key         | Type            | Notes                                                                           |
| ----------- | --------------- | ------------------------------------------------------------------------------- |
| `attempted` | integer         | **Must equal the number of findings.** Validation cross-checks it.              |
| `linked`    | integer         | How many got a link.                                                            |
| `unlinked`  | list of objects | One entry per finding without a link. Each requires `fingerprint` and `reason`. |

A `null` permalink is legitimate -- the section above is emphatic that it is the
honest answer for a file that does not match a pushed ref. But **"we attempted the
check and the file differed" and "nobody ran the check" are both spelled `null` on
the finding**, and until this field existed the schema could not tell them apart.

Measured, on the run that added it: the orchestrator emitted `null` for all 64
findings without attempting the check once. Validation passed, because
`_permalink` accepts `null` unconditionally and has to. The digest then told the
reader, 64 times, that the examined checkout did not match a pushed commit --
a cause nobody had established, and a false one: every one of the 49 distinct
defect files was byte-identical to `origin/master` and all 64 could have linked.
**A report that volunteers an untested cause is worse than one that links nothing,
because the false cause is the part the reader remembers.**

So `attempted` is cross-checked against `len(findings)`: a record cannot report a
clean resolution pass over findings it never looked at. Write it from the findings
list rather than from a counter -- a counter can be incremented zero times by a
loop that never ran, which is precisely how the failure above spelled itself as
success.

**Each `reason` is reader-facing text.** The renderer prints it verbatim in place
of the sentence it used to hardcode, so it must name the ref and the failure --
"file differs from `origin/master` at the examined checkout", never "could not
verify". A reason that names both is auditable; a generic one is the same silence
that produced the failure above. Where a finding has no link and no recorded
reason, the digest says exactly that and asserts nothing.

`scripts/resolve_permalinks.py` produces this block, and running it is the
supported way to fill `permalink` at all.

### `provenance` and `provenance_resolution`: the change that wrote the line

`scripts/resolve_provenance.py` fills both, between `resolve_permalinks.py` and
`digest_model.py`. **Never write either by hand.** The introducing commit is a
mechanical fact about the checkout, and the argument that keeps `permalink` out
of an agent's hands applies here without modification.

| Key            | Notes                                                                       |
| -------------- | --------------------------------------------------------------------------- |
| `commit`       | Full 40-char SHA. Short SHAs are rejected; abbreviations collide over time. |
| `commit_short` | The 8 chars the digest displays.                                            |
| `commit_url`   | Built from `repo.host` and `repo.full_name`.                                |
| `date`         | Human date, or null.                                                        |
| `pull_request` | `{number, url}`, or **null when the commit subject names none**.            |

A null `pull_request` is a fact about that commit, not a failure: commits
predating the merge tooling that writes `(#12345)` carry no reference, and on the
run this was built against 17 of 76 findings landed on one. The digest says "no
pull request on this commit" rather than leaving a gap, because a reader cannot
otherwise tell a missing link from a withheld one.

`provenance_resolution` is `{attempted, resolved, unresolved}` and carries the
same arithmetic guard as `permalink_resolution`: every attempt ends in a commit
or a named reason, and `{attempted: 76, resolved: 0, unresolved: []}` is rejected
as the shape a stage takes when it silently did nothing.

**No author, and no owning squad.** Blame hands back a name for free and the
report never records it. A shared artifact that prints a person beside the word
"bug" reads as an accusation whatever the surrounding wording says, and the pull
request already reaches that person in one click for anyone who needs them. The
squad variant fails the same test and adds a second problem: ownership moves, so
a squad resolved today is a claim about today attached to a commit from years
ago.

### `band_reason`: the sentence the rubric always required

One sentence naming which consideration decided the band. **Required on every
finding carrying a band other than `Not checked`**, null only where there is no
band decision to justify, and validated as prose so it cannot ship truncated
mid-word. Rendered in the **always-visible row**, not the expansion.

The rubric has demanded this sentence since bands existed
(`behavior-dossier-and-verdict-schema.md` section 6) and there was no field for
it, so what reached a reader was per-band boilerplate identical for every finding
in the group -- *"Ordered only where the order can be justified in writing."* on
every Act-Now row alike.

**It stopped being cosmetic on 2026-08-28.** The band rule now demotes a finding
whose harm measures dormant, whatever its capability. That is a deliberate
reversal of an earlier carve-out, and the risk it accepts is that a
client-reachable unbounded loop reads as `Low` while remaining a real defect. The
demotion is only safe if the capability is disclosed beside it, and a bare band
cannot carry that. So the field is required, and it is rendered where a reader
cannot miss it -- reasoning one click away is precisely how the exposure column
came to discard real impact statements while the page looked complete.

### `exposure_resolution`: proof that somebody queried

**`resolver_agent_id` is required, and it must name a real agent (or agents).** Added 2026-08-28
(`jbrooksbartlett-tstqk`). Accepts a single string or a list of strings -- the list form supports
chunked resolver dispatch where multiple resolver agents each handle ~30 candidates.

STEP 0's pre-flight leaves the orchestrator holding metric tools, and on the run that
prompted this it used them: rather than dispatch the resolver, it queried Oliver
itself, reasoning that a named subagent might drop its output. That reasoning is
locally correct -- named agents do drop output unless they call `SendMessage` -- and
globally wrong, because what this block certifies is that an **independent** stage did
the lookup. Figures the orchestrator gathered prove only that its own session can
reach the metric tools, which STEP 0 had already established. The run would have
scored its headline criterion PASS for a stage that never executed, on a document that
was internally consistent and cited live production metrics. A human reading the
terminal is what caught it.

Where to get the value: it is the agent id the harness assigns to the spawned
resolver, which arrives in that agent's task notification (`<task-id>`) and appears in
its transcript filename. Record it verbatim.

`digest_model.py` rejects a record whose `resolver_agent_id` is missing, empty, or
drawn from `_NOT_A_RESOLVER` -- `orchestrator`, `self`, `main`, `n/a`, `none`, `null`,
`-`, `unknown`. **This does not make the bypass impossible**, and it is not meant to:
an orchestrator can invent an id. What it does is convert a silent shortcut into a
deliberate false statement, and make the omission detectable by a script rather than
by whoever happens to be watching the pane.

The field is required even when `resolved` is 0. Making it conditional on `resolved > 0`
would let a bypassing run report zero to dodge the check -- and zero is exactly what
the preceding run reported.

Written by the impact-resolution stage (`agents/bug-hunt-impact-resolver.md`),
spawned once per component before banding. `{attempted, resolved, unresolved}`,
carrying the same arithmetic guard as its two siblings: every attempt ends in a
figure or a named reason, and `{attempted: 26, resolved: 0, unresolved: []}` is
rejected as the shape a stage takes when it silently did nothing.

**Why it is required rather than optional.**
`behavior-dossier-and-verdict-schema.md` has always said an `UNKNOWN` exposure
"is legitimate only after a query was actually attempted and either failed or
found no instrumentation". Nothing stood behind that sentence, so "queried, and
there is no instrumentation" and "nobody queried" produced the same empty cell
and the same clean-looking page.

**Measured, on two runs across two components:** the exposure column was almost
entirely an absence, while a substantial minority of those findings had named a
metric artifact in their own packet and cited it with a file and line, and the
run resolved none of them. The figures are canonical in
`references/design-history-and-failed-approaches.md` section 8 and are not
restated here, because a count in two files is a count that will drift.

`attempted` is cross-checked against the findings count, so a record cannot claim
a clean impact pass over findings nobody looked at. **Write it from the candidate
list, never from a counter** -- a counter can be incremented zero times by a loop
that never ran, which is precisely how this failure has spelled itself as success
in this pipeline before.

**An unresolved candidate is a result, not a gap.** "No series exists for this
path, confirmed against production" is useful output and passes validation. What
does not pass is silence, and what must never be substituted is a plausible
figure: a confidently wrong number is worse than a blank, because the false
figure is the part the reader remembers.

### `method`: what was done, including what was not

Two keys, both required when the object is present, and the key itself must
appear on every finding even when its value is null. Null means nobody recorded
how this finding was checked -- which the digest renders as that, rather than as
silence.

| Key            | Notes                                                                           |
| -------------- | ------------------------------------------------------------------------------- |
| `before_after` | One sentence from the mechanism-verifier, or **null when no before/after ran**. |
| `history_read` | `[{label, url}]` from the intent-verifier. **Empty list when none was read.**   |

This block exists because someone watching a run's report presented asked
whether the checking had included re-running the code at the commit before the
change. It sometimes had; the answer varied per finding and the report was
discarding it.

**Both fields must be honest about absence, and that is the whole design.** A
block rendered only where the method looks thorough is an advertisement, and a
reader shown evidence only when it flatters the finding cannot calibrate on it.
So `before_after: null` renders as "the code was not re-run at an earlier commit
for comparison" and an empty `history_read` renders as "that second check settled
the question without reading the history", both in as many words.

`history_read` is a flat list of what was opened, never a summary of what was
concluded. The reasoning belongs in `intent.trail`, and duplicating it here would
give a reader two versions of one argument to reconcile.

### `verification`

| Key                 | Notes                                                                     |
| ------------------- | ------------------------------------------------------------------------- |
| `metric_query`      | The query itself.                                                         |
| `reads_today`       | What it returns now.                                                      |
| `expected_after`    | What it should return after the fix.                                      |
| `expectation_basis` | **Why.** An expectation with its reasoning, never a fact.                 |
| `artifact_form`     | PromQL panel query, MMA alert-rule YAML, or a `servicelevels:` SLO block. |

A confidently wrong prediction is worse than none. Where the agent cannot reason
confidently about what the fix changes, `expected_after` says so rather than
guessing -- the same `MEASURED`/`ESTIMATED` discipline the exposure fields apply.

### Effort is an estimate and stays one

`effort` is the finder's S/M/L judgement of fix complexity. It is **not** derived
from a validated diff.

This is worth stating because the opposite was briefly planned. The premise was
that `agents/bug-hunt-mechanism-verifier.md` already applies a candidate fix, so a
diff exists to size. It does not: that agent compares **existing commits** --
reproduce on the candidate state, move to the pre-change state, reproduce again,
return -- and authors no fix at all. Making effort measured would require the
verifier to author one, which is a real scope increase for an agent whose
non-negotiable boundary is read-only-and-local.

Effort is reported alongside the band and is never an input to it. Standard own
vulnerability SLAs do not discount urgency for cheap fixes.
