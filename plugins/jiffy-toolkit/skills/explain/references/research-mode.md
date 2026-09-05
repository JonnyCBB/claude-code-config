# Research mode

The subject is a markdown research document. Everything in `SKILL.md` applies; this file adds the
procedure.

## Step 1: Harvest before writing

**This comes first and is not optional.** The source document is rarely the only context available,
and the difference between a thin explainer and a complete one is usually a lookup nobody ran. Collect
all of the following, then record the result of each in the provenance block from Step 3 — including
the ones that found nothing.

| # | Source | How to reach it | What it carries |
| --- | --- | --- | --- |
| 1 | The bead named in frontmatter | `bd show <id> --json` | The original ask, in the asker's own words, and the reasoning behind the dispatch |
| 2 | The bead's edges | the `dependencies` array on that bead | A parent often holds requirements; siblings hold known follow-ups |
| 3 | Sibling working notes | `<doc-dir>/.drafts/` | Per-question notes, discarded lines of enquiry, measurements that did not make the document |
| 4 | Sibling assets | `<doc-slug>-assets/` | Existing figures, and any earlier explainer for the same document |
| 5 | Instigating messages and linked documents | Slack, Google Doc and ticket URLs cited in the body | Research often exists *because* someone wrote something somewhere; that message is real context |

**The bead is usually the highest-value source and the easiest to skip.** Measured on a real run: it
supplied the original complaint verbatim and all six questions as they were actually asked, none of
which the source document foregrounded.

**What this list buys is coverage, not capability - and that correction came from an eval.** Two
baseline runs with no skill at all performed this harvest unprompted, and one went further than
anything here asks by checking whether the document's recommendations had actually been taken. So the
value of writing the sources down is not that a model cannot find them; it is that the list is
*exhaustive and the same every time*. The with-skill run produced a table of all five sources each
with a result, including "not applicable - no bead, so no edges"; the baselines declared the absences
they happened to notice. Systematic beats opportunistic when a reader has to trust that a missing
section means missing context.

Which sets the honest expectation for this section: on a rich, well-connected subject a capable model
will likely do most of it anyway, and the list is insurance. On a thin subject, or with a weaker
model, it is the difference between an explainer and a summary. Do not re-litigate whether it earns
its place without re-running the eval - and note that both fixtures in iteration 1 happened to have
no bead, so a successful bead harvest is the one path that suite never tested.

**Read the bead as a pointer, not as the record.** `bd update --notes` replaces the whole field rather
than appending, and notes changes are not written to the audit log at all, so a bead's notes may have
been overwritten with no trace. Follow the paths and identifiers a bead names and read those
documents; do not treat the notes text as the durable account of the work.

**When a lookup fails, keep going.** A thinner explainer that says it is thinner is useful. One that
omits the section silently is not.

## Step 2: What to cover

The original ask and why, in the asker's framing. What was already known or done beforehand. What was
found, ordered by what matters most to someone who knows nothing — lead with consequences, not method.
What is proposed. What was considered and rejected, and why. What is still open or unverified, and who
needs to decide it. The recommendation.

## Step 3: Output and provenance

Write to `<doc-slug>-assets/index.html`, beside the source document, and open it in the browser.

The document ends with two things:

1. **A sourced footer** — the path to the full source document, the source repository's current commit
   SHA, and the generation timestamp. Staleness has to be visible on inspection. The timestamp belongs
   here rather than in any machine-readable output, where it would make repeat runs differ for no
   reason.
2. **A provenance block** — every source from Step 1, each marked with what was looked for and what
   came back. "No bead named in frontmatter" and "bead found, no parent" are both results worth
   printing. A reader must be able to tell the difference between context that did not exist and
   context that existed and was missed.
