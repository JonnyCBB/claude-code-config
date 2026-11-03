# The run record

The JSON contract between the orchestrator and `scripts/digest_model.py`, which is the executable
form of it. **Assemble, run the validator, fix what it names, re-run.** It reports *every* problem
with its field path (`findings[2].fingerprint`) rather than the first, and rejects an unknown key by
name — so the field-level mechanics below are a checklist, not the specification. What this file
carries that the validator cannot is section 2: the judgement a script cannot check.

## 1. The fields

**Top level.** `run_id` (also the write gate's sentinel), `scope_strategy`, `scope_label`,
`components` (each a name, or an object carrying a non-empty `name`),
`findings` (**may be empty**), `coverage` (file PATHS, not a count), `degraded_paths`,
`dead_surface`, `cost` {`agents`, `wall_clock_minutes`}, `shortfall` ({`reason`, `cause`:
`CEILING`|`ENDED_EXTERNALLY`, plus `selected` with the latter}, or null — **required whenever any
finding is `DEFERRED_UNVERIFIED`, refused when none is unless `findings` is empty**; `CEILING` claims
you verified at least the ceiling, `ENDED_EXTERNALLY` that the run was ENDED — context gone, killed,
restarted — never that it judged itself short of time. `selected` is how many went to verification,
controls included, and must exceed what you verified unless both are `0`; `reason` is reader's prose),
`gate` {`dossiers_scanned`, `leaks_found`, `redaction_hits`}, `repo` {`host`, `full_name`,
`ref`} or null, `permalink_resolution`, `provenance_resolution`, `exposure_resolution`,
`reresolution` (null **only** when nothing was rejected).

The three `*_resolution` blocks are `{attempted, resolved|linked, unresolved|unlinked}` and all
carry the arithmetic guard: **`{attempted: 76, resolved: 0, unresolved: []}` is rejected** as the
shape a stage takes when it silently did nothing. **Only `permalink_resolution` and
`exposure_resolution` also cross-check `attempted` against the findings count** —
`provenance_resolution` does not. `exposure_resolution` additionally requires
`resolved_fingerprints` and `resolver_agent_id`.

**Per finding**, every key required: `fingerprint` (`^[0-9a-f]{16}$`, **lowercase** — it is both the
within-band sort key and the cross-run dedup key, so two spellings sort apart and dedup as two
defects), `state`, `band` (`Read closely` | `Worth a look` | `Skim` | `Not triaged`; null **only**
for a discarded finding; `Not triaged` **iff** `state` is `DEFERRED_UNVERIFIED`, both directions
validated), `band_reason`, `title`,
`consequence`, `harm_statement`, `observed_symptom`, `observed_full`, `defect_site`, `component`,
`tier`, `exposure`, `effort`, `mechanism` {`verdict`,`trail`}, `intent` {`verdict`,`trail`},
`fix_prompt`, `permalink`, `verification`, `provenance`, `method`.

`tier` is a closed set — `1`|`2`|`3`|`4`|`UNTIERED` — as a **bare value**, not `Tier 2`. `UNTIERED`
is the absence of a tier, never folded into Tier 4, and writing "Tier UNTIERED" would perform in
presentation the fold the rule forbids in data.

**`run_id` is load-bearing in a way that is easy to miss.** `write_artifact.py` checks
`if sentinel not in source` **before writing at all** and exits 2 on a miss. The digest is a
run-level artifact with no fingerprint, so its sentinel is the run id — `render_digest.py` must emit
it as visible text or every real run fails before a byte lands.

**Never hand-write `permalink`, `provenance`, `figure_kind`, `share.harm_hash` or
`resolved_fingerprints`.** `resolve_permalinks.py`, `resolve_provenance.py` and `exposure_block.py`
derive them. Each replaced a hand-assembly that failed silently.

## 2. What the validator cannot check

### No word this skill invented reaches the reader

The digest is opened by someone who has not read `SKILL.md`, and who meeting "141 candidates
deferred by the verification bound" cannot tell whether that is bad and will assume it is fine.

Banned in every reader-facing string — `title`, `consequence`, `observed_symptom`, `exposure.note`,
`shortfall.reason`, `band_reason`, and any prose in `fix_prompt`:

| Do not write | Write instead |
| --- | --- |
| mandate | the part of the code that was searched |
| Finder Packet | the write-up in the report folder |
| finder / verifier | name the action: "reproduced locally", "checked separately" |
| band | group, or name it: "read closely", "not triaged" |
| disposition / state | the plain outcome: "a bug", "not a bug", "not checked" |
| defect site | the file and line |
| fingerprint | omit it; it is an internal key |
| axis / two axes | say what was actually done, in words |
| deferred | not checked |
| candidate | possible problem |
| coverage record | what was searched |
| degraded-path sweep | what happens when things go wrong |

**The rule binds hardest where text is COPIED, not written.** `mechanism.trail` and `intent.trail`
are reader-facing and the obvious way to fill them is to paste the verifier's report — but verifiers
write for the orchestrator, in this skill's vocabulary. Measured: after every renderer string was
fixed, `candidate` still appeared 76 times in one digest, 23 of them in titles taken straight from
finder output. **Summarise the trail in your own plain words** and keep the verbatim version in the
report folder. One run's digest carried `Finder Packet` 143 times and `axis`/`axes` 298 times,
almost all from prose the orchestrator wrote rather than from the renderer.

The test before writing any string: **would this sentence make sense to the on-call engineer who
owns this component and has never run this skill?**

### Reader-facing prose is a finished thought

`title`, `band_reason`, `consequence`, `fix_prompt`, `mechanism.trail`, `intent.trail` and
`exposure.note` each render as their own block and must end in punctuation. **`title` and
`band_reason` are in that set and are the two most often missed** -- `digest_model._PROSE_FIELDS`
is canonical, and a title written as a headline with no full stop fails the whole record. Measured, on one record: **129 fields stopped
mid-sentence** — 44 consequences, 25 reproduction trails, 24 exposure notes, 20 of 21 fix prompts —
every one from an orchestrator assembling a field as `f"...{other_field[:300]}"`.

**Do not satisfy the rule by appending a full stop to a slice.** That produces a field that passes
and still says nothing, which is worse than the error. One reader copied a fix prompt that stopped
at `has no arti`.

**A fix prompt is a standalone instruction**, written to be copied and run without the rest of the
report: what to change, where, and what to add as a regression test. Not a summary of the evidence
and not a place to restate the verdict.

Three fields are excluded and the exclusions matter as much as the rule: `observed_symptom` and
`observed_full` are **captured output** — a stack trace ends where the runtime ended it, and
demanding punctuation would push an author into editing real evidence. Every `reason` field is a
**sentence fragment** by design.

### `observed_symptom` is one line; `observed_full` is everything else

The bound (no line breaks, ≤120 chars) is the *consequence* of the rule, not the rule. The field is
**the single most diagnostic line of real output — the exception and its message, or the assertion
that failed.** It is **not the opening fragment of a stack trace**, and an author who reads only
"make it shorter" will slice a trace to fit and reproduce the exact defect this rejects. Measured:
an orchestrator filled it with 200-400 character multi-line traces on a 64-finding run; the row
clipped every one mid-token, and 56 of 64 were over the bound.

Write the summary line yourself and put the raw capture in `observed_full`, which renders for
**every** finding in every band. Before it existed, this required, validated field reached the
reader nowhere at all for 55 of 64 findings.

### A two-arm reproduction needs every arm read before anything is written

**When the mechanism trail carries a control, a counterfactual, or a before/after, read every arm
before writing any reader-facing string.** There is no single most diagnostic line, because **the
diagnosis is the difference**. `observed_symptom` carries the contrast; `title` stays a claim and
must not assert something another arm refutes — but do not pack arm-by-arm figures into it either.

Wrong, written from the arm the orchestrator happened to store:

    observed_symptom: isTrialAccount=false -> price[TRIAL_ONLY]=[discount:01]
    title:            The trial discount is applied to paid accounts, not to trial accounts

Right, written from the trail:

    observed_symptom: paid: [annual plan] discounted to 0.0; trial: [monthly, annual, add-on] all discounted
    title:            A trial-account discount rule also discounts annual plans for paid accounts.

This reached a reader. Every stage below the orchestrator was right — the finder said "paid users
silently get the annual discount", the reconciler wrote "trial side byte-identical" — and the inversion came
from the one agent that had stopped reading trails to fit the run into a session. **The disk
indexing that makes a large run survivable is what hides the second arm, so the moment you are most
efficient is the moment you are most likely to invert something.**

### The exposure block

`basis` is `MEASURED`, `ESTIMATED` or `UNKNOWN` — provenance, not magnitude.

**`share` is a four-key object or null**, and the renderer **divides it and never parses your
prose**. Across 16 findings carrying a `basis`, a renderer taking the leading figure from each prose
denominator would have been right on 6, wrong on 7 where the two sides count different things
(21,427 metric *series* over 25 grpc *pairs*; a rate over *5 regions*), and fabricated on 3.

    "share": {"numerator": 2.92, "denominator": 63000, "unit": "req/s",
              "of": "reaching this component", "harm_hash": "9f2c1b7ad4e60381"}

`unit` ≤24 chars and `of` ≤52; validation **rejects rather than truncates**, so an over-long `of`
fails the whole record. **One `unit` covers both sides on purpose** — a shared unit is the only proof
the two figures are commensurable, and it makes `21,427 series of 25 pairs` impossible to write.
**`of` completes `<numerator> of <denominator> <unit> ___`**; the renderer cannot supply that noun,
because 63,000 counts searches in one service and items in the next.

Two measured failures this shape exists to make unrepresentable: one finding shipped
`path_denominator: "~63,000 req/s"` beside an identical `component_denominator` — divided, **100%**,
the largest figure the column can show, on a finding nobody had checked, where the numerator was
never measured but the population copied into its slot. And one row's denominator named two
populations, 6,465,151/s and 3,752,452/s, for one numerator: 0.083% and 0.143%, **1.72x apart, from
one cell**.

**`share_absent` names which of three absences it is**, because they are not interchangeable for
someone setting priority:

| Value | Means |
| --- | --- |
| `NOT_QUERIED` | Nobody looked. The common case. |
| `NO_INSTRUMENT` | No instrument for this harm exists. |
| `NOT_REQUEST_SCOPED` | An instrument exists but cannot attribute the harm to requests. |

**The line between the last two is whether an instrument exists at all**, not whether the harm feels
request-shaped. The first wording read "a request denominator does not apply", which describes the
harm rather than the instrument — so a resolver handed the case the value was written FOR, a
timer-driven gauge, reasoned a wrong deadline conceptually *is* a per-request event and reached for
`NO_INSTRUMENT`. A gauge reading `0` on a timer is `NOT_REQUEST_SCOPED`: the instrument exists, so
`NO_INSTRUMENT` overstates the gap, but its `0` is not a measured zero and a `share` of `0` would be
a fabricated measurement.

**`component_denominator` holds the component's traffic and an absolute rate is the normal form** —
0 of 82 values on the measured run were a share, and that is not drift: you cannot write `Y% of
component traffic` without knowing Y. **`path_denominator` must say what its figure is a share of**;
validation rejects a bare figure, and a reader met a bare `0.072%` beside an urgent finding and
named that column as the part of the report they could not understand. **A value with no figure is
normal and needs no apology** — and `basis` is deliberately dropped there, because printing
`ESTIMATED` under an absent figure claims an estimate exists. One run shipped `n/a` above
`ESTIMATED` or `MEASURED` on all 76 rows. Write the placeholder or your own wording, never a bare
figure: the renderer drops a bare absence token and its own placeholder alike.

**`harm_statement` is the question any figure is a share OF, and it is required on every finding.**
Optional would defeat it: a producer omitting it makes the hash comparison pass by leaving nothing to
compare. It is not rendered. **The resolver echoes the statement it measured against verbatim in
`harm_measured`; the orchestrator hashes that echo.** Hashing the finding's *current* statement
would satisfy the check while defeating it, and nothing inside one record can tell the two apart.

The defect all this exists to make unrepresentable: on one run, candidates that never reached a
verifier kept **52 of 52** resolver figures and candidates that did kept **4 of 31** — reaching a
verifier is what deleted the figure, because the assembler nulled the share unless the fingerprint
appeared in a hand-typed four-item frozenset, and fingerprints are run-scoped so the next run matches
nothing. Of the 15 findings a reader could act on, 2 showed a figure, 12 had one resolved and then
deleted, and **0 were genuinely unmeasurable**.

**`figure_disposition` is compared by equality against its four values, never by containment.** Both
things it replaced were containment tests — a fingerprint in a run-scoped frozenset, and
`"downgrad" in note.lower()` — and each decided the whole column without leaving a trace.
`NO_FIGURE` exists because the other three would force a false claim where there was no figure to
judge; it is not a rejection, so it does not trigger re-resolution.

**`resolver_agent_id` must name a real agent**, and is required even when `resolved` is 0 — making
it conditional would let a bypassing run report zero to dodge the check, and zero is exactly what the
run that prompted this reported. `digest_model.py` rejects `orchestrator`, `self`, `main`, `n/a`,
`none`, `null`, `-`, `unknown`. **This does not make the bypass impossible and is not meant to**: it
converts a silent shortcut into a deliberate false statement and makes the omission script-detectable.
What the block certifies is that an **independent** stage did the lookup — on the run that prompted
it, the orchestrator queried the metric source itself rather than dispatch the resolver, reasoning that a named
subagent might drop its output. That reasoning is locally correct and globally wrong, and the run
would have scored its headline criterion PASS for a stage that never executed.

**Write every count from the list, never from a counter** — a counter can be incremented zero times
by a loop that never ran, which is precisely how this failure has spelled itself as success here
before.

### Three more that cost a reader

- **No author and no owning team, anywhere.** `git blame` hands back a name for free and the report
  never records it: a shared artifact printing a person beside the word "bug" reads as an accusation
  whatever the wording, and the pull request reaches them in one click. Team fails the same test and
  adds a second problem — ownership moves, so a team resolved today is a claim about today attached
  to a commit from years ago.
- **Nothing in this record writes the heading, and there is no summary field. Adding one back is the
  change to argue against.** A `thesis` field produced *"Twenty-eight parallel readings of this
  service turned up seventy-six things worth a look..."* and two readers rejected it independently
  within a day. The one that matters: **a summary at the top of a machine-generated report has to be
  persuasive to justify its space, and persuasive prose over machine findings reads as something to
  discount** — it spends exactly the credibility the two verification passes earned. It also could
  not be kept honest: one finding was rebanded after publication and the prose still read "all ten in
  the most urgent group" while the header rendered `9`.
- **`method` must be honest about absence, and that is the whole design.** A block rendered only
  where the method looks thorough is an advertisement. `before_after: null` renders as "the code was
  not re-run at an earlier commit for comparison" and an empty `history_read` as "that second check
  settled the question without reading the history", both in as many words. `history_read` is a flat
  list of what was opened, never a summary of what was concluded. **`method: null` renders nothing**,
  so an unrecorded method says nothing rather than claiming nobody checked the finding.

**`shortfall.reason` completes a sentence** — it renders as "These were never looked at, because
**<reason>**. Not because anyone decided they were unimportant." So write a lowercase clause with no
trailing stop, in the reader's language. Good: `the run's checking limit was reached, and only after
every finding in the most urgent group had been checked`. Bad: `group, not budget` — that is the
internal distinction, not a sentence, and it reaches the reader verbatim.
