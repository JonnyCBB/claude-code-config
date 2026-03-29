# Animation Libraries

## Table of Contents
- CDN Links
- GSAP Initialization + Timeline API
- GSAP ScrollTrigger Integration
- Playback Control Pattern
- D3.js Data Visualization Pattern
- p5.js Algorithm Visualization Pattern
- Three.js 3D Concept Pattern
- Rough.js Hand-Drawn Style
- Decision Matrix

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

## GSAP Initialization + Timeline API

Basic GSAP timeline for sequential animations:

```javascript
// Register plugins
gsap.registerPlugin(ScrollTrigger);

// Create a timeline for a concept
function createConceptTimeline(stepIndex, containerId) {
  const tl = gsap.timeline({ paused: true });
  const container = document.getElementById(containerId);

  // Fade in elements sequentially
  tl.from(container.querySelectorAll(".anim-element"), {
    opacity: 0,
    y: 30,
    stagger: 0.3,
    duration: 0.6,
    ease: "power2.out"
  });

  // Animate specific properties
  tl.to(container.querySelector(".highlight"), {
    scale: 1.2,
    fill: "var(--color-primary)",
    duration: 0.4
  });

  return tl;
}
```

## GSAP ScrollTrigger Integration

Bind animations to scroll position:

```javascript
// Play timeline when step enters viewport
function bindTimelineToStep(stepElement, timeline) {
  ScrollTrigger.create({
    trigger: stepElement,
    start: "top center",
    end: "bottom center",
    onEnter: () => timeline.play(),
    onLeave: () => timeline.pause(),
    onEnterBack: () => timeline.play(),
    onLeaveBack: () => timeline.reverse()
  });
}

// Scrub-linked animation (animation progress = scroll progress)
ScrollTrigger.create({
  trigger: "#scrolly",
  start: "top top",
  end: "bottom bottom",
  scrub: 1,
  animation: mainTimeline
});
```

## Playback Control Pattern (ALWAYS include for GSAP animations)

Every GSAP timeline animation MUST include playback controls for user interactivity.
Read `templates/playback-controls.html` for the full implementation.

Guiding principle: **The user should be in control of their learning.**

### What the controls provide:
- Play/Pause — toggle animation playback
- Step Forward/Back — advance frame-by-frame when paused
- Speed selector — 0.5x, 1x, 2x via `timeline.timeScale()`
- Progress scrubber — jump to any point via `timeline.progress()`
- Replay — restart from beginning

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

## D3.js Data Visualization Pattern

For data-driven charts and tree diagrams:

```javascript
function createD3Visual(containerId, data) {
  const width = 400, height = 300;
  const svg = d3.select(`#${containerId}`)
    .append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`);

  // Bar chart example
  const x = d3.scaleBand().domain(data.map(d => d.label)).range([40, width - 20]).padding(0.2);
  const y = d3.scaleLinear().domain([0, d3.max(data, d => d.value)]).range([height - 30, 20]);

  svg.selectAll("rect")
    .data(data)
    .join("rect")
    .attr("x", d => x(d.label))
    .attr("y", height - 30)  // Start at bottom
    .attr("width", x.bandwidth())
    .attr("height", 0)       // Start collapsed
    .attr("fill", "var(--color-primary)")
    .transition()
    .duration(800)
    .delay((d, i) => i * 150)
    .attr("y", d => y(d.value))
    .attr("height", d => height - 30 - y(d.value));
}
```

## p5.js Algorithm Visualization Pattern

For interactive algorithm simulations:

```javascript
function createP5Sketch(containerId) {
  new p5((p) => {
    let array = [];
    let comparing = -1;

    p.setup = () => {
      const canvas = p.createCanvas(400, 300);
      canvas.parent(containerId);
      array = Array.from({ length: 20 }, () => p.random(10, 280));
    };

    p.draw = () => {
      p.background(getComputedStyle(document.documentElement)
        .getPropertyValue("--color-bg").trim());

      array.forEach((val, i) => {
        p.fill(i === comparing ? "var(--color-accent)" : "var(--color-primary)");
        p.noStroke();
        p.rect(i * 20, 300 - val, 16, val);
      });
    };

    // Expose control functions
    p.stepForward = () => { /* advance algorithm one step */ };
    p.reset = () => { /* reset to initial state */ };
  }, containerId);
}
```

## Three.js 3D Concept Pattern

For 3D spatial concepts:

```javascript
function create3DScene(containerId) {
  const container = document.getElementById(containerId);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  // Add orbit controls for interactivity
  // const controls = new OrbitControls(camera, renderer.domElement);

  camera.position.z = 5;

  function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
  }
  animate();
}
```

## Rough.js Hand-Drawn Style

For whiteboard/sketch aesthetic:

```javascript
function createRoughDiagram(containerId) {
  const container = document.getElementById(containerId);
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 400 300");
  container.appendChild(svg);

  const rc = rough.svg(svg);

  // Hand-drawn rectangle
  svg.appendChild(rc.rectangle(50, 50, 120, 80, {
    roughness: 1.5,
    fill: "var(--color-primary-light)",
    fillStyle: "hachure"
  }));

  // Hand-drawn arrow
  svg.appendChild(rc.line(170, 90, 230, 90, { roughness: 1.2 }));

  // Hand-drawn circle
  svg.appendChild(rc.circle(280, 90, 60, {
    roughness: 1.5,
    fill: "var(--color-accent-light)",
    fillStyle: "cross-hatch"
  }));
}
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
