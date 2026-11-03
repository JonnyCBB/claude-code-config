# Craft notes

Read before writing, and again before calling it finished. They apply to both modes. No number here
is a target: length and visuals are judged by whether the reader can follow every step.

Everything here is about *how much* and *what shape*. Nothing here specifies a look — palette,
typography and layout belong entirely to `/frontend-design`.

## How long

**As long as the reader needs to understand everything, and no longer.** Never cut a sentence to reach
a word count. Run these three checks on every section:

1. **Inference.** Read it as the reader, who does not know this system. Every place where they must
   work out a state, a next step or a reason for themselves is a missing sentence: add it. A real
   section about a size rule never said whether the section was locked, or whether it was removed,
   and the reader had to ask.
2. **Coverage.** Every finding in the source appears. A terse document reads as confident while having
   dropped whole findings: a first run of this skill shed seven of the source's sections.
3. **Cut.** Remove only what the reader loses nothing without: restatement, an account of how the
   investigation went, citation trails the footer carries, a motivation the reader already knows.
   Never remove a definition, a step in a causal chain, a worked example or a stated result. Explainers
   written without this skill failed by keeping the investigation's method and citations, not by
   being long.

Measure and report the ratio to the source, as a description only:

```bash
wc -w <source>.md
python3 -c "import re,sys,pathlib; t=pathlib.Path(sys.argv[1]).read_text(); \
  t=re.sub(r'<(style|script|svg).*?</\1>','',t,flags=re.S); \
  print(len(re.sub(r'<[^>]+>',' ',t).split()))" <output>.html
```

## How many visuals — and how much prose around them

**Draw a visual wherever it makes a mechanism, flow, state change or trend easier to follow.** There
is no target ratio. Report words per visual, counted as `<svg>` + `<figure>` + `<table>`, as a
description only:

```bash
python3 -c "import re,sys,pathlib; t=pathlib.Path(sys.argv[1]).read_text(); \
  b=re.sub(r'<style.*?</style>','',t,flags=re.S); \
  w=len(re.sub(r'<[^>]+>',' ',re.sub(r'<svg.*?</svg>','',b,flags=re.S)).split()); \
  v=b.count('<svg')+b.count('<figure')+b.count('<table') \
    - sum(1 for m in re.finditer(r'<figure[^>]*>(.*?)</figure>',b,flags=re.S) if '<svg' in m.group(1)); \
  print(f'{w} words / {v} visuals = ' + (f'{w//v} words per visual' if v else 'NO VISUALS AT ALL'))" <output>.html
```

**The subtraction is not optional.** A figure that wraps an SVG is one visual; counting it twice
halves the figure. "NO VISUALS AT ALL" is always a defect. Any other result is never a reason to cut
words.

Use one definition and stay with it. Do not replace the script's count with a hand count, and do not
count theme class names like `.plate` or `.chart` as well.

**Three ways this goes wrong, all observed:**

1. **A wall of text.** A mechanism explained only in paragraphs when a figure of its states would let
   the reader see it. Add the figure; keep the prose that explains it.
2. **Prose turned into figure labels.** A run that chased a density number converted its explanation
   into labels and table cells. A cell saying "Match, but position 3 already won" leaves the reader to
   work out why. The sentence that says why belongs in the prose.
3. **Figures without context.** The same run put figures next to each other with too little prose
   between them to say what each showed. **A figure needs a sentence introducing what it is, a
   sentence on how to read it when that is not obvious, and a sentence saying what to take from it.**
   The rule in `SKILL.md` — use the visual instead of the paragraph — means replace the *description*,
   never the *explanation* or the *framing*. An unintroduced figure is not doing the work of the
   paragraph it replaced; it is just sitting there.

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
