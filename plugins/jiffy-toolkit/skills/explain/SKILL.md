---
name: explain
description: >
  Generates a self-contained, visually engaging HTML explainer for a reader who has not read the
  source material: a research document, or a pull request. Harvests context the source itself does
  not carry - the bead behind the work, linked documents, working notes, verification evidence and
  any instigating message - and declares what it looked for and could not find. PR mode adds a merge
  recommendation backed by a deterministic signal sheet. Use when asked to explain a research
  document or a pull request, to write an explainer, briefing or walkthrough, or to make a dense
  document readable before a decision.
when_to_use: >
  Use for "/explain", "explain this research", "explain this PR", "write an explainer", "briefing
  doc", "PR walkthrough", or before deciding whether to merge. NOT for teach-me (scrollytelling
  tutorials), NOT for frontend-slides (presentations), NOT for review-document (editorial review of
  an existing doc), and NOT for "explain this function" or "explain this file" - those are ordinary
  code questions, not artifact generation.
argument-hint: "[<doc-path>|<pr-url>|<owner/name#N>]"
---

# Explain

Produce a self-contained HTML explainer for the engineer who commissioned this work.

**The reader's profile:** fluent in engineering generally; no familiarity with this specific system,
its internals or its vocabulary. They have not read the source document. They *do* know why the work
happened - they commissioned it, or they saw the high-level ask - so do not re-explain the motivation
as if it were news. Explain what they do not have: the detail, the internals, and the terminology.

Write in accessible language. Define every acronym and project-specific term at first use, in the
`full name (ACRONYM)` form. Nothing a reader arriving cold would stop at should be left bare.

**Use the common word for anything that is not a term of art.** Two kinds of word get two different
treatments, and conflating them is how an explainer ends up either impenetrable or patronising:

- **A term of art** - a name for something real in this system, this codebase or this field:
  `assertion`, `mutation`, `glob`, `test double`, `namespace`, `idempotent`. **Keep it, and gloss it
  at first use.** Never swap a vague word in for a precise one. Removing it takes away the thing the
  reader can search for, and reads as talking down to them.
- **Your own vocabulary** - an uncommon English word where a common one means exactly the same thing:
  `provenance`, `salient`, `requisite`, `extant`, `elide`, `orthogonal` where you only mean unrelated,
  `surface` as a verb, `leverage` as a verb. **Just use the common word.** Nothing is lost, because
  there was never anything to search for.

**The test, applied per word:** would the reader ever meet this word again - in the code, the docs, a
ticket, or a conversation with the author? If yes it is a term of art: keep it and explain it. If no,
it is only your phrasing: `provenance` becomes **where it came from**, `salient` becomes **the part
that matters**, `we surfaced it` becomes **we found it**.

This came from a real explainer. "Provenance" appeared once, explained nothing, and had a four-word
plain equivalent sitting right there. The engineering was never the problem; the vocabulary around it
was.

Use visual elements liberally - diagrams, flowcharts, figures, graphs. **The rule: if a concept would
otherwise need a wall of text, and a diagram, figure or graph would convey it better, use the visual
instead of the text. Not both.** Every figure still needs enough prose around it to say what it shows
and what to take from it - a figure nobody introduces is not doing the work of the paragraph it
replaced.

Every claim resting on a file, table, dashboard, document or command carries a real reference the
reader can follow. The document may be forwarded to the person whose work it concerns.

Anything unverified is rendered as visibly as anything verified. A finished-looking document is not
evidence that the checks behind it happened.

Use `/frontend-design:frontend-design` to design it. The look is yours and should suit this subject -
palette, typography, layout and the one signature visual device are all open. Do not reach for a
template. This is a front-loaded briefing, not a scroll-driven narrative.

When it is finished, open it in the browser.

---

## Where everything else lives

**Read `craft.md`, then the file for the mode you are in. Neither read is optional.** An eval measured
what happens without them: baseline runs given this task with no skill produced documents far longer
than a briefing should be, missed the visual-density target most of the time, and pulled in external
font URLs so the output would not render offline. `craft.md` carries the measured figures and is the
only place they live.

| Read this | When |
| --- | --- |
| [`references/craft.md`](references/craft.md) | **First, and again before calling it finished.** How long, how many visuals and how much prose around them, self-containment, and the devices the explainers that landed well share. Measured as the highest-value file here. |
| [`references/research-mode.md`](references/research-mode.md) | The subject is a research document, or a `.md` path. The context harvest, what to cover, where the output goes. |
| [`references/pr-mode.md`](references/pr-mode.md) | The subject is a pull request - a URL or `owner/name#N`. The signal script, the seven-source harvest, the merge verdict, the determinism rules. A bare PR number is ambiguous and is rejected rather than guessed. |
| `scripts/pr_risk_signals.py` | Invoked by PR mode. Emits the signal sheet as JSON; run it with no arguments for usage. |

With no argument, infer the subject from the conversation - the document just written, or the pull
request just discussed - and say what was inferred before proceeding. If two candidates are equally
plausible, ask rather than picking one.
