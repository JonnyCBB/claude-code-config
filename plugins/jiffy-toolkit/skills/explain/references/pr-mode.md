# PR mode

Produce an HTML walkthrough of a pull request for a reader who has not looked at the code, ending in
a merge recommendation they can act on.

Everything in `SKILL.md` still applies, and `references/craft.md` carries the length band, the visual
density target and the self-containment rules for both modes - it is the single place those numbers
live, so do not restate them here. This file adds only what is specific to a pull request.

## Step 1: Run the signals script first

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/explain/scripts/pr_risk_signals.py <pr-url-or-owner/name#N>
```

**A bare PR number is rejected on purpose.** It would resolve against the current directory's git
remote, so the same reference in two worktrees describes two different pull requests - and the output
would be internally consistent in each, so nothing downstream could catch it. Pass a full URL or
`owner/name#N`.

**Read the JSON it prints. Do not work from a schema written down here.** There is deliberately no
field table in this file: a prose copy of the script's keys is a second source of truth whose only
function is to drift, and nothing enforces agreement between them. The output is self-describing.

Exit codes, monotonic by severity:

| code | meaning | what to do |
| --- | --- | --- |
| `0` | complete computed tier | proceed |
| `1` | partial - something could not be collected | proceed, and render the affected fields as `unverifiable` with the attempted lookup shown |
| `2` | unresolvable reference, or no PR found | **stop.** Report why, quoting the `errors` entry. Do not write a walkthrough |

## Step 2: Harvest, and read the `relation` field

The script resolves four sources itself and reports each as
`{source, lookup_attempted, resolved_path, relation}`. That makes "declares what it looked for and
could not find" a mechanical fact rather than something the author has to remember. Render every row,
including the ones that found nothing.

Three sources it does **not** resolve, which are yours to follow once a bead is known: the bead's
dependency edges (a parent often holds requirements, siblings hold known follow-ups), any documents
the bead or PR body links, and the PR's own commit messages and comments - where reasoning the PR
body dropped often sits.

**`relation` is the field that matters most, and ignoring it is the easiest way to mislead.**

- `resolved` - the lookup key uniquely identifies that artifact.
- `unverified-mention` - free text merely referenced the PR. **This does not establish that the
  artifact is the PR's own.** Measured while building the script: searching for PR #98 returned a
  research bead that quotes #98 as a worked example and also names the repository, so neither the
  number nor a repository corroboration separates a mention from ownership.

So render a bead with `relation: unverified-mention` as *"a bead that references this PR"*, never as
*"the bead behind this work"*. If it turns out to be the wrong bead, a walkthrough built on it will
be confidently wrong about the entire motivation.

**Why the join is weak, in one line:** 199 of 874 beads reference a PR at all, across three fields in
two syntaxes, and `external_ref` is populated on 0 of 874. Until something writes a structured
pointer at PR-creation time, this is best-effort by construction.

> **Note for a future grounding audit.** `external_ref` has zero hits anywhere outside this skill,
> which is the signature of a fabricated API. It is not one: `bd create --help` and `bd update --help`
> both carry `--external-ref string  External reference (e.g., 'gh-9', 'jira-ABC', Linear URL)`, and
> the field is absent from real beads because **nothing writes it** — which is the very fact cited
> above. Verified 2026-08-20. Do not delete the claim on a zero-trace result.

## Step 3: What to cover

The verdict, up front. The problem this solves. What the code does - before and after of the same
flow. What this lets the system do that it could not before. Where it could go wrong, and what
protects against that. The evidence, including **which checks did not run**. The merge
recommendation. What is still unproven, adjacent to the recommendation.

## Step 4: The verdict

Three labels: `MERGE`, `MERGE AFTER <specific action>`, `DO NOT MERGE`. Each is followed by the one
condition that would flip it, and sits next to what is still unproven - because that section is the
qualifier on the verdict, not a footnote to it.

**No automated check state means no unconditional `MERGE`.** If `check_state.total` is `0`, there is
no CI in that repository and the strongest available verdict is `MERGE AFTER`. Measured: this
repository has no CI at all - zero check runs, zero statuses, no tags, no releases - so expect the
conditional form to be the normal case here, not the exception.

**Which means the clause is the output, not the label.** A label that never varies carries no
information, so the whole signal lives in what follows `AFTER`. It must name a concrete, checkable
action derived from *this* PR's actual gaps.

| | |
| --- | --- |
| Acceptable | `MERGE AFTER running the 4 publish-to-snow script tests locally and confirming the two bash snippets in SKILL.md execute` |
| **A failure to correct, not an acceptable output** | `MERGE AFTER manual checks` |

**`branch_currency` has three values and only one of them is good news.** `current` means the branch
is up to date. `stale` means it is not. **`unverifiable` is not a pass** - it is what a merged PR
returns (measured: `mergeStateStatus` is `UNKNOWN` on PR #98), and a "not BEHIND" test would read it
as current. Render it as unverifiable.

## Step 5: Four rules that make the evidence section trustworthy

1. **Verbatim only.** Every value in the evidence table is copied unchanged from the script's JSON -
   no paraphrasing, rounding, reformatting or reordering. If a field is not in the JSON, it is not in
   the table.
2. **Judgment renders outside the table**, attributed, naming the files it rests on. Which lines are
   load-bearing, whether tests exercise the changed path, whether this sets a precedent - these are
   judgments and cannot be derived from paths. They must be visibly distinguishable from computed
   numbers.
3. **Surface the run token** - `pr_ref` plus `head_commit_sha` - so a stale table is detectable. The
   generation timestamp goes in the footer, sourced from the render step; it is deliberately absent
   from the JSON, where it would make repeat runs differ for no reason.
4. **A missing tier renders as `unverifiable` with the attempted lookup shown.** Never blank, never
   absent, never a green tick. `tiers_omitted` always contains `judgment`, because the script renders
   no verdict by design - so seeing two of three tiers is normal and does **not** mean the profile is
   complete.

## Step 6: When computed and found disagree

If a computed signal contradicts a harvested finding - the diff touches no interface file, but a
review flagged a breaking contract change - **render both, mark it a conflict, and cap the verdict at
`MERGE AFTER <resolve the conflict>`.**

Do not silently prefer either. A disagreement is information: it usually means the path-based buckets
are too coarse to see what a reader saw, which is a known limitation rather than a bug. Preferring
the computed value hides a real finding; preferring the finding quietly makes the byte-stable table
overridable by prose.

## Step 7: Fail loudly on a shape you do not recognise

Reading another skill's output by glob is the dependency that silently degraded the review store to
roughly 49% recall - no error, no test, in a repository with no CI. When a harvested document does not
have the shape expected, **say so visibly in the provenance block**. Do not report it as an absence:
"looked and found nothing" and "found something I could not parse" are different facts, and
collapsing them is how the earlier failure stayed invisible.
