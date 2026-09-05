# Craft notes

Read before writing, and again before calling it finished. These are measured from the explainer
corpus, not preferences. They apply to both modes.

Everything here is about *how much* and *what shape*. Nothing here specifies a look — palette,
typography and layout belong entirely to `/frontend-design`.

## How long

**Target 20-33% of the source document's word count.** Measure it; do not estimate.

```bash
wc -w <source>.md
python3 -c "import re,sys,pathlib; t=pathlib.Path(sys.argv[1]).read_text(); \
  t=re.sub(r'<(style|script|svg).*?</\1>','',t,flags=re.S); \
  print(len(re.sub(r'<[^>]+>',' ',t).split()))" <output>.html
```

The band comes from the corpus: briefings written for a single decision-maker landed at 22-33% of
their source, while peer-facing reviews ran 71-79%. A briefing is the lower band.

**This is the rule the eval showed carries the most weight, so here is the evidence rather than an
assertion.** Across three baseline runs given the same task with no skill, **none landed in the band**
- the two that produced research-doc explainers came in at **52% and 67% of source**. A document at
two-thirds the length of its source is not a briefing; it is the source with the citations removed.
The same runs missed the density target 2 times in 3, once with a single visual in 3,000 words, and
**both pulled in external font URLs** - one while describing itself as "a single self-contained file",
which is the worst kind of failure because the artifact looks finished and silently will not render
offline.

**Coming in under the band is the likelier failure, and it does not look like one.** A terse document
reads as confident and well-edited while having quietly dropped whole findings. A first run of this
skill produced 9% against a hand-written baseline of 23.8% for the same source, having shed seven of
the source's sections. If the count is below the band, the question is not "is this tight enough" but
"which findings are missing".

## How many visuals — and how much prose around them

**Roughly one visual element per 100-200 words**, counted as `<svg>` + `<figure>` + `<table>`:

```bash
python3 -c "import re,sys,pathlib; t=pathlib.Path(sys.argv[1]).read_text(); \
  b=re.sub(r'<style.*?</style>','',t,flags=re.S); \
  w=len(re.sub(r'<[^>]+>',' ',re.sub(r'<svg.*?</svg>','',b,flags=re.S)).split()); \
  v=b.count('<svg')+b.count('<figure')+b.count('<table') \
    - sum(1 for m in re.finditer(r'<figure[^>]*>(.*?)</figure>',b,flags=re.S) if '<svg' in m.group(1)); \
  print(f'{w} words / {v} visuals = ' + (f'{w//v} words per visual' if v else 'NO VISUALS AT ALL'))" <output>.html
```

**The subtraction is not optional.** A figure that wraps an SVG - which is the normal shape for a
numbered plate - was counted twice by the earlier version, halving the apparent words-per-visual. On a
real artifact it reported 105 when the true figure was 172. Worse, an agent following the skill found
the two bands **jointly unsatisfiable** because of it: hitting the density target as measured drove the
word count to 42% of source, outside the compression band. Do not work around this by avoiding
`<figure>`; count each visual once.

**That last clause is not defensive padding.** An earlier version divided by `max(v,1)`, so a document
with zero visuals reported "3 words / 0 visuals = 3 words per visual" - reading as outstanding density
when nothing had been drawn at all. A check whose worst input produces its best-looking output is worse
than no check. Found by running the block against an empty fixture, not by reading it.

Use one definition and stay with it. Counting theme class names like `.plate` or `.chart` as well
gives a different number for the same file, and a rule whose figure and whose check disagree is worse
than no rule.

**Three ways this goes wrong, all observed:**

1. **Too sparse.** A first run came in at 282 words per visual — a wall of text with occasional
   pictures — while passing every other check. This failure is independent of the word count.
2. **Traded against the word count.** A second run reached 68 words per visual and fell to 11.8%
   compression, because it converted prose into figure labels rather than adding figures to prose.
   **Check both numbers together and treat a pass on one with a fail on the other as a fail.**
3. **Figures without context.** The same run put figures next to each other with too little prose
   between them to say what each showed. **A figure needs a sentence introducing what it is and a
   sentence saying what to take from it.** The rule in `SKILL.md` — use the visual instead of the
   paragraph, not both — means replace the *explanation*, not the *framing*. An unintroduced figure
   is not doing the work of the paragraph it replaced; it is just sitting there.

A visual counts when it carries information the prose does not then repeat. A decorative rule or an
icon does not count.

## Devices the explainers that landed well share

Derived from two artifacts singled out as good. **The palette is not among them** — one is near-black,
the other a cool light grey, and both work. What they share is structure and scale, which is why these
are recorded and the look is not.

1. **The `h1` is the reader's own question, or the verdict, in plain words** — at a size that
   dominates the first screen. A neutral title is a wasted slot.
2. **A persistent verdict chip.** A small boxed line in a corner, so the answer is legible before
   anything is read and stays legible while scrolling.
3. **A full-width short-answer band.** A rule across the page, a small label, and the answer in large
   type. This is the highest-value block in the document.
4. **The hero pairs prose with a bespoke data figure, side by side.** Not a stat grid. **Invent the
   figure for this dataset** — one square per file, 178 of them, 21 marked — rather than reaching for
   a generic chart type. A borrowed chart shape says nothing specific.
5. **Figures are numbered plates, not loose diagrams.** A bordered panel with a titled eyebrow, a
   corner label for state, real numbers embedded, and one accent-coloured annotation carrying the
   insight the plate exists to deliver. Number them only because they are cross-referenced — that is
   a real function. Do not number sections, which is decoration.
6. **Address the reader directly.** "You asked whether X earns its cost", "your instinct about Y was
   right and about Z was not". The rule against definite pronouns is about not naming or gendering a
   person; it is not a reason to write coldly.

**Where the data is a trend, draw a plot** — axes, gridlines, an expected line against the actual one.
Labelled rectangles are for structure and flow and are not a substitute.

## Self-containment

One file. Inline `<style>` and inline `<script>`. No `<img>` tags — diagrams are inline `<svg>` with
`<title>` and `<desc>`, or CSS-drawn. No external stylesheet or script, and no network requests of any
kind, so the file works from `file://` indefinitely. Every custom font falls back to a system stack.

## Before calling it finished

Look at the rendered page, at a narrow viewport and a wide one. Two real defects in one artifact were
caught only that way and by nothing else: a horizontal overflow at 390px, and two verdict labels
rendered in colours that meant the opposite of what they said. The `explain` profile in
`${CLAUDE_PLUGIN_ROOT}/skills/shared/scripts/visual_qa.py` captures the screenshots and console
errors; read its report as diagnostic only, since its interaction stages report passes that mean
nothing on a static briefing.
