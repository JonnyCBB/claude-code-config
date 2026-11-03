---
name: bug-hunter-3000
description: Runs a recurring, multi-candidate bug-hunt pilot over a named component list, a single team, or a single system/repo, using two independent verification axes (a live-reproduced mechanism plus a blind intent investigation) to avoid the false-positive pattern that caused a prior incident, and writes findings to a local-only markdown portfolio plus one HTML digest, with zero outbound actions. Use when explicitly asked to run, schedule, or pilot the bug hunter 3000 on named components. Do not use for general code review, ad hoc bug hunting, or any task that expects a PR, ticket, or notification as output.
disallowed-tools: mcp__claude_ai_Slack_MCP__slack_send_message mcp__claude_ai_Slack_MCP__slack_schedule_message mcp__claude_ai_Slack_MCP__slack_send_message_draft mcp__claude_ai_Google_Workspace_MCP__gmail_send_message
argument-hint: "[component-list | team | system-or-repo] [metrics <path>...] [open-digest | no-open]"
---

# Bug Hunter 3000

A thin orchestrator over two independent verification axes per candidate, reconciled into a
disposition before anything is called a real candidate. Outputs are local only: portfolio
(section 6), digest (section 9), session summary (section 7), nothing outbound (section 2).

**Read the reference file linked from a section before touching its step.** Several record measured
failures; a rule that looks arbitrary usually replaced something that was tried.

- `references/run-loop.md` — partitioning, lenses, grouping, bounded verification, loop invariants
- `references/verdicts-and-bands.md` — dossier withholding, dispositions, banding, reader verdicts
- `references/run-record.md` — the record contract, and the judgement its validator cannot check
- `references/scope-and-safety.md` — the three scope strategies and the zero-outbound design
- `references/local-reproduction.md` — how the mechanism-verifier builds and drives a service

## 1. STEP 0 — Pre-flight

Confirm access to, in this order:

- The **Agent tool**, needed to spawn every subagent below.
- **A local checkout of every component in scope**, or `gh` authenticated for github.com so the
  missing ones can be shallow-cloned read-only into the run directory.
- **All five subagents**: `agents/bug-hunt-{finder,mechanism-verifier,intent-verifier,impact-resolver,reconciler}.md`.

**If any is missing, stop and name it.** A run missing the intent-verifier silently drops one of the
two axes this methodology exists to keep independent; it is not a smaller valid run.

**Match on capability, not on a namespaced tool name** — an equivalent read-only tool under any
prefix satisfies the requirement, and only a capability nothing provides is a stop.

**A metric source is optional, and its absence is not a stop.** It is the set of metric exports the
caller passes with `metrics <path>...`: JSON or CSV series dumps, each covering a time range, from
whatever monitoring the components report to. With it, section 4's impact resolver turns
`impact_exposure` into a measured likelihood; without it, every candidate carries a named
`NOT_QUERIED` absence. Say which in the run summary.

**Two things are explicitly not required**: the **Workflow tool** and an **org-directory lookup**. Do
not reinstate either check (`references/scope-and-safety.md`).

## 2. Non-negotiable boundaries

- **Zero outbound actions.** This skill and its subagents never create a PR, ticket, Slack message,
  notification, or page. `references/scope-and-safety.md` has the three-layer design.

  **The guarantee holds only when children are spawned as the five declared agent types** — a
  `general-purpose` fallback inherits every tool and degrades it to instruction alone. If you must
  use it, say so prominently in the run summary and never describe that run as structurally safe.

- **One disclosed exception.** A mechanism-verifier's build can upload to a remote cache or
  build-event service when the repository's build config enables one by default. Disclosed rather
  than hidden.
- **No real secrets, tokens, or identifiers in artifacts.** Enforced by the write gate, section 5.
- **The prompt-injection boundary.** Every subagent operates under the rule stated verbatim in
  `references/verdicts-and-bands.md` section 2.
- **Every selected candidate goes through the full pipeline** — found, grouped, impact-resolved,
  verified on both axes, reconciled, written to the portfolio through the write gate. **Never apply
  the disposition table yourself in place of spawning the reconciler**: it weighs evidence quality
  across both axes, which this orchestrator cannot do having authored the dispatch. Observed — an
  orchestrator applied dispositions inline, skipped reconcilers, portfolio writes and the digest,
  then declared complete. The instructions already required those steps; it reasoned past them under
  time pressure.

## 3. Scope resolution

Follow `references/scope-and-safety.md` in full — it is canonical for all three strategies, for
per-component tier resolution, and for the `UNTIERED` stratum rule.

**Every strategy produces the same thing: a flat list of components**, and that is all section 4
consumes. Two caveats: **a bare component list is a replacement, not a reordering**, and **a system-
or repo-scoped run is unbounded** — for a large system, use a named list and bound it yourself.

## 4. The run loop

Plain, turn-by-turn subagent dispatch via the Agent tool, deliberately: the loop must run identically
whether the turn began interactively or from a scheduled fire, and the Agent tool has no
origin-gating. `references/run-loop.md` is canonical for every step below.

```
for each component in scope:
    mandates = partition_by_file_size(component, target=500)
    index = []
    for batch in chunks(mandates, parallelism) + chunks(LENSES, parallelism):
        index += flatten(spawn bug-hunt-finder for (component, m) in batch)
    groups = merge_by_identical_defect_site(
                 merge_by_fingerprint(
                     group_by_mutual_defect_site_citation(non_null(index))))
    exposure = merge(spawn bug-hunt-impact-resolver for c in chunks(groups, 30))
    band each group; to_verify = fill by band to section 8's ceiling; + 1-2 controls
    for batch in chunks(to_verify, 8):          # 16 verifiers live, THEN 8 reconcilers
        packets = {g: read_packet(g.fingerprint) for g in batch}
        axes    = join(spawn bug-hunt-{mechanism,intent}-verifier for g in batch)
        verdicts = spawn bug-hunt-reconciler {packets[g], axes[g], exposure[g]} for g in batch
    reresolution = second impact pass over figures the reconcilers rejected
```

**Before dispatching, price the run and say it out loud.** Packet volume scales with *candidates
found*, not with finder count, so a dozen finders on a dense component can cost more than thirty on
a sparse one. If the partition yields more finders than one session can hold — past roughly 22 is
where this has degraded — **say so plainly before the first batch** and name the options: bound it,
split the component, or accept a partial run. Do not discover it at the verification stage.

**Every finder prompt MUST carry three things, as absolute paths and ids.** Without them the finder
cannot run its write command at all, and one that invents a path scatters packets where `--collect`
and `--read` will not find them, which reads downstream as "searched nothing".

- **mandate id**, unique within the run (`m01`). Two finders sharing one id **overwrite each other's
  packets**.
- **run directory**, absolute. Create it before the first batch.
- **skill directory**, absolute, so the finder can invoke `<skill-dir>/scripts/index_packets.py`.

**The finder writes its own packet to disk and returns only the index**, by piping its packet through
`index_packets.py`. **Do not ask a finder to return its packet inline, and do not read packet files
here** — 32 finders once returned ~2.2MB through one orchestrator's context, which then reached
verification with too little room to use it. Re-reading is surgical and happens only where marked.
Merge the per-mandate indexes with `python3 scripts/index_packets.py --run-dir <run-dir> --collect`.

A failed or unusable finder is **re-dispatched once without asking**; a second failure is an
unsearched gap recorded in the digest's coverage.

**Impact resolution runs before banding**, because section 4's top-band clause requires a figure or a
recorded failed attempt. Chunk candidates into batches of ~30 — a single resolver given a whole
component's candidates resolves too few. Pass each group's **root-cause fingerprint**, its verbatim
`Impact and exposure evidence`, defect site, observed symptom, **the harm statement its figure
must be a share of**, and the run's metric source (the absolute export paths, or "none supplied").
Pass **no** verdict, band or conclusion. Spawn the resolver even when no metric source was supplied:
its per-candidate `NOT_QUERIED` accounting is what the digest shows, and an orchestrator writing that
accounting itself is the bypass described below.

- **Record all resolver agent ids** in `exposure_resolution.resolver_agent_id`; `digest_model.py`
  rejects a missing or empty one.
- **Validate each candidate's `share` on receipt.** Non-null means a dict with
  `{numerator, denominator, unit, of}`. A string or bare number means real data in a form the
  renderer cannot use: reclassify as unresolved with "resolver returned non-conforming share" and
  decrement `resolved`. Do not parse prose or infer denominators.
- **Check `harm_measured` against what you dispatched.** It is the resolver's verbatim echo, so a
  difference means the figure answers something else. One string comparison here; two stages later it
  presents as "the figure answers a superseded question".
- **`attempted` must equal the total number of groups**, written from the groups list, never a counter.
- **If a chunk dies or delivers nothing**, re-dispatch once. If the second
  attempt also delivers nothing, record `resolved: 0` for that chunk with every candidate in
  `unresolved` giving "impact resolver did not deliver", and say so in the run summary.
- **You must not read the metric exports yourself**, here or anywhere in this loop, even though
  you hold the paths and doing it directly looks cheaper. What `exposure_resolution` certifies is
  that an **independent** stage did the lookup. Measured 2026-08-28: an orchestrator reasoned exactly
  this way, obtained real production figures, and was about to score the run's headline criterion PASS
  for a stage that never ran.

Every agent in this loop is spawned **unnamed** and returns in its final message.

**Inside the verification loop**, re-read the packet per group rather than per batch — a batch re-read
reassembles the 2.2MB this design exists to avoid, one iteration later:
`python3 scripts/index_packets.py --run-dir <run-dir> --read <fingerprint>`.

**Build the dossier with the script. Do not hand-roll the withholding:**

```bash
python3 scripts/build_dossier.py --packet <run-dir>/packets/finder-<m>.md \
    --fingerprint <fp> --out <run-dir>/dossiers/<fp>.md
python3 scripts/dossier_leak_scan.py <run-dir>/dossiers/<fp>.md
```

The builder emits only the closed five-item list, drops everything at and below `--- APPENDIX ---`,
re-checks itself with the scanner's own patterns, and refuses to write if anything survives. Then run
the scanner itself, **because the builder is not the gate**: `0` CLEAN, `1` LEAKED (blocks dispatch),
`2` NO_INPUT (the check did not run). Measured 2026-08-29: a run that hand-rolled this had 7 of 8
dossiers rejected and verified none of its 103 candidates — eleven of the eighteen leaks were the word
"refuted" from the Coverage record, appendix content the marker exists to separate mechanically.

**The reconciler's payload must include this group's resolved exposure entry.** Without it, its own
contract — adopt the figure, downgrade one that measures the wrong thing — refers to data it was never
handed, and the band silently falls back to the packet's `UNKNOWN`.

**Threat level is the orchestrator's, not the reconciler's.** For any disposition that is not
discarded, band per `references/verdicts-and-bands.md` section 4 plus a `band_reason`: one sentence
naming what decided it, **including the retained capability on a demotion**.

**Re-resolve the figures the reconcilers rejected**, against the corrected harm statement — only this
pass can produce a harm share, because a harm share needs a confirmed harm to be a share of. Select by
**equality** against `{DOWNGRADED, REPLACED}`, never containment; `ADOPTED` and `NO_FIGURE` are not
rejections. Share-validated exactly as above.

**Build the exposure blocks with the script, never by hand** — prose was tried and deleted 27 of 31
real figures:

```bash
python3 scripts/exposure_block.py --resolver <merged first pass> \
    [--reresolve <second pass>] --verdicts <run-dir>/verdicts \
    --states <fingerprint-to-state map> --out <run-dir>/exposure.json
```

Splice its blocks onto the findings and write none of those fields yourself. It also returns both
`resolved_fingerprints` lists and the re-resolve attempt count, which the resolver's own output does
not carry. Exit 1 means it refused and named a contradiction; fix the input rather than working around it.

**Record assembly gate: every reconciler for every selected candidate must have returned before you
assemble the run record or run the digest pipeline.** A digest built from incomplete results ships
findings with no band, which `digest_model.py` accepts for discarded findings but a reader cannot
distinguish from a pipeline failure. Observed: a digest produced while a reconciler was still running,
with 11 findings carrying no band.

## 5. The write gate

Write every portfolio and deferred file with **`scripts/write_artifact.py --sentinel <fingerprint>
<dest>`**, passing the drafted markdown on stdin. One call redacts, writes, re-reads, and proves that
what landed is that artifact. **Read the exit code, not the status string:**

- `0` / `OK` — written and verified. If the JSON's `redacted` field is true, a secret shape was masked:
  record it as a gate hit in the run summary.
- `1` / `VERIFY_FAILED` — bytes landed and they are not this artifact. Report `problems` verbatim and
  do not record the candidate as written.
- `2` / `NO_INPUT` or usage — nothing written and nothing scanned. **This is not a pass and not a
  redaction finding**; the invocation is wrong. Fix it and rerun.

Three rules, each of which cost a measured incident:

- **Do not mask it yourself** — a caller-side `replace` on `masked_preview` matches nothing.
- **Do not redraft and rescan.** The only sanctioned retry is byte-identical and automatic; a
  redraft-and-rescan loop was measured laundering a real identifier through the gate in reworded form.
- **Do not treat `NO_INPUT` as a pass.**

## 6. Portfolio format

One markdown file per candidate, named `{fingerprint}-{run_id}.md`, with a numeric disambiguator if
two candidates in one run collide.

Each file carries **in full**: every constituent Finder Packet with its Coverage record and mandate;
both verifiers' complete evidence trails, not just verdict labels; the reconciler's full verdict block
with reasoning; and for non-discarded dispositions the threat-level block.

A candidate deferred by bounded verification gets a file too: its packet, `Not triaged` where a band
would sit, and `DEFERRED_UNVERIFIED` in place of a disposition, with no verifier trails and no threat
level. It must never read as though a verdict were pending. **Omitting these files is the one option
not available.**

## 7. Run-level summary

**A short text signal, not the report.** Findings, coverage, the sweep table, dead surface and cost
live in the digest. This exists for the case where nobody opens a browser. Six items; do not restate
the digest in prose.

- **The digest's absolute path**, first line. On a scheduled fire nobody is watching the session, so
  this is the only way anyone finds the artifact.
- **The write gate's result** per file, plus any redaction gate hits. A hit never halts the run but is
  always reported.
- **The dossier leak scan**: how many scanned, and every leak found and fixed. Report it ran even when
  it found nothing — a clean sweep and a check that never executed look identical otherwise. Never
  substitute the verifiers' self-reports: on one run they caught five of seven leaks where the scan
  caught seven of seven.
- **Agent count and wall-clock** — the answer to the first question any reader of a recurring pilot asks.
- **Any early exits**: a STEP 0 stop, or a redaction gate failure.
- **Components outside the caller's scope**, if the caller narrowed it. Otherwise a fully-honoured
  override reads as a truncated run.

Grouping decisions, including near-misses, stay in the portfolio files where a reader can check them
against the packets. A near-miss must **show the intervals and the site line**, so `192 not in 230-356`
is on the page rather than asserted.

## 8. Bounded verification, applied automatically

**Automatic above the ceiling, and never a question for the caller.** The bound: **every
Read-closely candidate, then fill to 20 total from the bands below; exceed 20 only if all are Read
closely.** Below 20 candidates the bound does nothing and every group is verified.
`_VERIFICATION_CEILING` in `digest_model.py` checks a `CEILING` claim against this number — **move
both or neither**, because raising it here alone is the drift with no signal. Do not raise it — the
extra slots come off the BOTTOM of the fill order.

**THE CEILING IS THE ONLY BOUND YOU MAY CHOOSE, and being stopped is not deciding to stop.** The
clock and the agent count are not stopping conditions; `shortfall.cause` has no value for either.
A run that merely feels short of time must keep going. A run that was ENDED — context gone, killed,
restarted — writes `ENDED_EXTERNALLY` and every candidate that did not complete the pipeline.

**Apply it silently and say so in the run summary. Never ask the caller.** Two things are
load-bearing and routinely lost: **bounding never discards, and neither does self-truncation** —
every candidate that did not complete the pipeline keeps its packet, is written
`DEFERRED_UNVERIFIED` with `band: "Not triaged"`, and appears in the digest by name — and **always
verify one or two control candidates from outside the bound**, or the confirmation rate measures
selection rather than accuracy. `references/run-loop.md` section 4.

## 9. The digest

One HTML file per run, written locally and opened in a browser unless the caller said not to. It is
the thing a human actually reads; the portfolio files remain the evidence of record behind it.

**The digest is the deliverable, and the run is not complete until it exists.** A run that verifies
candidates but produces no digest has spent its entire budget and delivered nothing a component owner
can act on. `write_artifact.py` exiting 0 on the digest is what marks the run done — not the last
verifier returning, not the last reconciler completing, and not a summary posted to the session.

### What goes in it

`references/run-record.md` is canonical. Five properties erode easily:

- **Bands in fixed order** — Read closely, Worth a look, Skim, Not triaged — verdict as the first
  column inside each. Within-band order is fingerprint-ascending and is **not** a severity judgement;
  the digest says so on the page.
- **No word this skill invented reaches the reader**, and **no internal disposition name**. The
  substitution table and the eleven-state translation are in the reference files.
- **Evidence splits across two fields because it has two jobs.** `observed_symptom` is the
  scannable line and `observed_full` the complete capture; `references/run-record.md` owns the
  bound, the "not the opening fragment of a stack trace" rule, and the measured incident.
- **An exposure figure says which question it answers**, and every word above it links to a
  definition. A reader cannot otherwise recover whether a percentage is the share HARMED or the share
  that merely REACHES the code, nor what `MEASURED` promises against `ESTIMATED`. The definitions are
  static in `render_digest.py` because they describe how this pipeline reaches a number. **Do not put
  them in the record** — a per-run copy drifts from the code that sets the labels.
- **Every finding names the change that wrote its line.** The commit and its pull request are visible
  in the expansion; a collapsed block carries the method where the record holds one. The provenance
  **never names an author or a team**, and that block **states what did not happen** as plainly as
  what did, or a reader calibrates on evidence they only see when it flatters the finding.
- **A run that finds nothing still produces a digest**, proving what was searched. A clean component
  and an unsearched one must not look alike, so coverage records file NAMES, not a count.
- **No convergence mark.** A two-track glyph for the two axes was designed and dropped; with the
  verdict spelled out as a word it became decoration. Do not reintroduce it.

### Producing it

Assemble a run record matching `references/run-record.md`, then run the pipe:

```bash
set -o pipefail
python3 scripts/resolve_permalinks.py --repo "$CHECKOUT" < run.json > run.linked.json
python3 scripts/resolve_provenance.py --repo "$CHECKOUT" < run.linked.json > run.traced.json
python3 scripts/digest_model.py < run.traced.json \
  | python3 scripts/render_digest.py \
  | python3 scripts/write_artifact.py --sentinel "$RUN_ID" "$DEST"
```

**`set -o pipefail` is not optional.** A bash pipeline reports only the last command's status, so
without it an upstream failure is masked by a successful write of whatever reached the gate.

**`resolve_provenance.py` is a separate stage because it is slow, not because it is optional.** It runs
`git blame` once per distinct file, measured at ~4 seconds per call and **3.5 minutes for a 76-finding
run spanning 51 files**. Keeping it out of the pipe means re-rendering after a validation failure costs
nothing, which matters because the prose gate rejects a whole record at once. `digest_model.py` requires
the `provenance_resolution` block it writes, so skipping it fails validation rather than quietly
shipping a report with no history.

**Never hand-write `permalink`, and never leave it null without running the resolver.** `null` is
legitimate for a file that differs from every pushed commit, which is precisely why "never checked" and
"checked and failed" are indistinguishable to a reader and to validation alike. Measured: 64 findings
shipped null with no check attempted, and all 64 were in fact linkable.

**The sentinel is the run id, not a fingerprint** — a run-level artifact has none. `write_artifact.py`
checks it *before writing at all* and exits 2 if absent, so `render_digest.py` emits the run id as
visible text.

**Do not hand-write the HTML.** The two scripts own the structure so it cannot drift between runs;
agents given latitude substituted their own schema four times running.

**On `VERIFY_FAILED`: retry once, with identical bytes**, then fail loudly and report `problems`
verbatim. **Never regenerate content to retry** — a byte-identical retry is not a redraft, and that
distinction is the point. The retry helps against a transient clobber and does nothing for a
deterministic failure.

### Opening it

`open-digest` (default) opens it in a browser. `no-open` prints the absolute path and opens nothing.

**It is a caller argument because there is no runtime signal to branch on.** A scheduled prompt writes
`no-open` into its own text — a caller's instruction authored earlier. **The skill never infers its own
origin.** `open <file>` is a local process invocation, not a network write, so the zero-outbound
guarantee is unaffected. **Publishing stays a human step** — print the command if you like, never
perform it.
