# Animation Libraries

## CDN Links

```html
<!-- GSAP Core + ScrollTrigger (ALWAYS include) -->
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12/dist/ScrollTrigger.min.js"></script>

<!-- Scrollama (ALWAYS include) -->
<script src="https://unpkg.com/scrollama"></script>

<!-- D3.js (include when data visualization needed) -->
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>

<!-- p5.js (include when algorithm simulation needed) -->
<script src="https://cdn.jsdelivr.net/npm/p5@1.11/lib/p5.min.js"></script>

<!-- Three.js (include when 3D concepts needed) -->
<script src="https://cdn.jsdelivr.net/npm/three@0.160/build/three.module.js" type="module"></script>

<!-- Rough.js (include for hand-drawn aesthetic) -->
<script src="https://cdn.jsdelivr.net/npm/roughjs@4.6.6/bundled/rough.cjs.min.js"></script>

<!-- Nutshell (ALWAYS include for expandable definitions) -->
<script src="https://cdn.jsdelivr.net/gh/ncase/nutshell/nutshell.min.js"></script>
```

## Playback Control Pattern

Every GSAP timeline gets playback controls so the learner sets the pace. The implementation is `templates/playback-controls.html`.

### Timeline labels (required):
Every timeline must include GSAP labels at meaningful checkpoints:

```javascript
var tl = gsap.timeline({ paused: true });
tl.addLabel("show-array", 0);
tl.to(...);
tl.addLabel("check-middle", ">");
tl.to(...);
tl.addLabel("found", ">");
```

The playback controller uses these labels to show checkpoint names
on the progress scrubber and in the status text.

### Exception: Manim renders
Manim GIF/WebM output cannot be controlled via GSAP timelines.
For Manim content, use native `<video>` controls (play/pause/scrub)
or convert to frame sequences with manual stepping.

## Expandable Definitions (Nutshell)

Wrap a term in a link to a hidden heading; clicking it expands the definition inline:

```html
<p>The <a href="#gradient">gradient</a> tells us which direction to go.</p>
<h4 id="gradient" hidden>Gradient</h4>
<p>A vector pointing in the direction of greatest increase of a function.</p>
```

## Decision Matrix

| Concept Type | Primary Library | When to Choose | Alternatives |
|---|---|---|---|
| Process flow / step-by-step | GSAP | Default for most concepts | — |
| Side-by-side comparison | GSAP | Two things contrasted | — |
| Layered build-up | GSAP | Components assembling into whole | — |
| Data transformation | GSAP | Input → process → output | D3 if data-heavy |
| Math notation / equations | Manim | LaTeX needed, 3Blue1Brown style | GSAP with SVG text |
| Neural network diagrams | Manim (ManimML) | NN architecture visualization | GSAP SVG |
| Bar/line/scatter charts | D3.js | Data-driven with transitions | GSAP SVG |
| Tree/graph structures | D3.js | Hierarchical data | GSAP SVG |
| Sorting/searching algorithms | p5.js | Interactive simulation | GSAP |
| Particle systems | p5.js | Many moving elements | — |
| 3D geometry/molecules | Three.js | Spatial understanding needed | — |
| Informal/sketch aesthetic | Rough.js + GSAP | Approachable, non-intimidating | — |
| Simple text explanation | None | Concept is straightforward | Styled callout only |
