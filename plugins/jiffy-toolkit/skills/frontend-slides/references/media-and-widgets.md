# Media & Widgets Reference

Image pipeline, video slides, mermaid diagrams, animated counters, CSS charts, GSAP playback, and SVG widgets.

## Image Pipeline (skip if no images)

If the user chose "No images" in Step 1.2, **skip this entire section** and go straight to generating HTML. The presentation will be text-only with CSS-generated visuals — this is a fully supported, first-class path.

If the user provided images, execute these steps **before** generating HTML.

**Key principle: Co-design, not post-hoc.** The curated images from Step 1.2 (those marked `USABLE`) are already part of the slide outline. The pipeline's job here is to process images for the chosen style and place them in the HTML.

### Image Processing (Pillow)

For each curated image, determine what processing it needs based on the chosen style (e.g., circular crop for logos, resize for large files) and what CSS framing will bridge any color gaps between the image and the style's palette. Then process accordingly.

**Rules:**
- **Never repeat** the same image on multiple slides (except logos which may bookend title + closing)
- **Always add CSS framing** (border, glow, shadow) for images whose colors clash with the style's palette

**Dependency:** Python `Pillow` library (the standard image processing library for Python).

```bash
# Install if not available (portable across macOS/Linux/Windows)
pip install Pillow
```

**Common processing operations:**

```python
from PIL import Image, ImageDraw

# --- Circular Crop (for logos on modern/clean styles) ---
def crop_circle(input_path, output_path):
    """Crop a square image to a circle with transparent background."""
    img = Image.open(input_path).convert('RGBA')
    w, h = img.size
    # Make square if not already
    size = min(w, h)
    left = (w - size) // 2
    top = (h - size) // 2
    img = img.crop((left, top, left + size, top + size))
    # Create circular mask
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, size, size], fill=255)
    img.putalpha(mask)
    img.save(output_path, 'PNG')

# --- Resize (for oversized images that inflate the HTML) ---
def resize_max(input_path, output_path, max_dim=1200):
    """Resize image so largest dimension <= max_dim. Preserves aspect ratio."""
    img = Image.open(input_path)
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    img.save(output_path, quality=85)

# --- Add Padding / Background (for images that need breathing room) ---
def add_padding(input_path, output_path, padding=40, bg_color=(0, 0, 0, 0)):
    """Add transparent padding around an image."""
    img = Image.open(input_path).convert('RGBA')
    w, h = img.size
    new = Image.new('RGBA', (w + 2*padding, h + 2*padding), bg_color)
    new.paste(img, (padding, padding), img)
    new.save(output_path, 'PNG')
```

**When to apply each operation:**

| Situation | Operation |
|-----------|-----------|
| Square logo on a style with rounded aesthetics | `crop_circle()` |
| Image > 1MB (slow to load) | `resize_max(max_dim=1200)` |
| Screenshot needs breathing room in layout | `add_padding()` |
| Image has wrong aspect ratio for its slide slot | Manual crop with `img.crop((left, top, right, bottom))` |

**Save processed images** alongside originals with a `_processed` suffix (e.g., `logo_round.png`). Never overwrite the user's original files.

### Place Images

**Use direct file paths** — do NOT convert images to base64 data URIs. Since presentations are viewed locally, reference images with relative paths from the HTML file:

```html
<img src="assets/logo_round.png" alt="Logo" class="slide-image logo">
<img src="assets/screenshot.png" alt="Screenshot" class="slide-image screenshot">
```

This keeps the HTML file small and images easy to swap. Only use base64 encoding if the user explicitly requests a fully self-contained single-file presentation.

**Image CSS classes (adapt border/glow colors to match the chosen style):**
```css
/* Base image constraint — CRITICAL for viewport fitting */
.slide-image {
    max-width: 100%;
    max-height: min(50vh, 400px);
    object-fit: contain;
    border-radius: 8px;
}

/* Screenshots: add framing to bridge color gaps with the style */
.slide-image.screenshot {
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* Logos: smaller, no frame */
.slide-image.logo {
    max-height: min(30vh, 200px);
}
```

**IMPORTANT:** Adapt the `.screenshot` border and shadow colors to match the chosen style's accent color. For example:
- Dark Botanical (gold accent): `border: 1px solid rgba(197, 160, 89, 0.2); box-shadow: 0 0 20px rgba(197, 160, 89, 0.08);`
- Creative Voltage (neon yellow): `border: 2px solid rgba(212, 255, 0, 0.25); box-shadow: 0 0 20px rgba(212, 255, 0, 0.08);`

**Placement patterns:**
- **Title slide:** Logo centered above or beside the title
- **Feature slides:** Screenshot on one side, text on the other (two-column layout)
- **Full-bleed:** Image as slide background with text overlay (use with caution)
- **Inline:** Image within content flow, centered, with caption below

**Note:** Processed images (e.g. `logo_round.png`) are saved alongside originals in the assets folder. Reference them with relative paths in the HTML.

## Video Slide Type

```html
<!-- ===========================================
     LAYOUT: Video Slide
     Embedded video with play/pause on Space, auto-pause on nav.
     =========================================== -->
<section class="slide layout-video" data-has-video>
    <h2 class="reveal">Demo Video</h2>
    <div class="video-container">
        <video class="slide-video" preload="metadata" playsinline>
            <source src="assets/demo.mp4" type="video/mp4">
        </video>
        <button class="video-play-btn" aria-label="Play video">&#9654;</button>
    </div>
</section>
```

```css
/* ===========================================
   LAYOUT: Video
   Embedded video with overlay play button.
   =========================================== */
.slide.layout-video .video-container {
    position: relative;
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    max-height: min(65vh, 500px);
}

.slide-video {
    width: 100%;
    max-height: min(60vh, 480px);
    object-fit: contain;
    border-radius: 8px;
}

.video-play-btn {
    position: absolute;
    width: 64px; height: 64px;
    border-radius: 50%;
    border: none;
    background: color-mix(in oklch, var(--bg-primary), transparent 30%);
    color: var(--text-primary);
    font-size: 1.5rem;
    cursor: pointer;
    transition: transform 0.2s, opacity 0.2s;
}
.video-play-btn:hover { transform: scale(1.1); }
.video-play-btn.hidden { opacity: 0; pointer-events: none; }
```

```javascript
/* ===========================================
   VIDEO SLIDE CONTROLLER
   Space toggles play/pause on current slide's video.
   Auto-pauses when navigating away.
   =========================================== */

// In SlidePresentation class:

initVideoSlides() {
    this.slides.forEach(slide => {
        const video = slide.querySelector('.slide-video');
        if (!video) return;

        const playBtn = slide.querySelector('.video-play-btn');

        const toggleVideo = () => {
            if (video.paused) {
                video.play();
                playBtn.classList.add('hidden');
            } else {
                video.pause();
                playBtn.classList.remove('hidden');
            }
        };

        playBtn.addEventListener('click', toggleVideo);

        video.addEventListener('ended', () => {
            playBtn.classList.remove('hidden');
        });

        // Store reference for auto-pause
        slide._video = video;
        slide._videoPlayBtn = playBtn;
    });
}

// In goToSlide() — auto-pause videos on previous slide:
const prevSlide = this.slides[prevIndex];
if (prevSlide._video && !prevSlide._video.paused) {
    prevSlide._video.pause();
    prevSlide._videoPlayBtn.classList.remove('hidden');
}

// Modify keyboard handler — Space on video slide toggles video:
case ' ':
    e.preventDefault();
    const currentVideo = this.slides[this.currentSlide].querySelector('.slide-video');
    if (currentVideo) {
        // Toggle video play/pause instead of advancing slide
        if (currentVideo.paused) {
            currentVideo.play();
            this.slides[this.currentSlide]._videoPlayBtn.classList.add('hidden');
        } else {
            currentVideo.pause();
            this.slides[this.currentSlide]._videoPlayBtn.classList.remove('hidden');
        }
    } else {
        this.navigateNext();
    }
    break;
```

**Anti-slop note**: Space key behavior changes on video slides — it toggles video play/pause instead of advancing. Arrow keys still navigate. Use `preload="metadata"` (not `preload="auto"`) to avoid loading large video files until the user presses play. Add `playsinline` for iOS.

## Mermaid Diagram Support

```html
<!-- Include Mermaid CDN at end of body (only if presentation uses diagrams) -->
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({ startOnLoad: true, theme: 'dark' });</script>

<!-- Mermaid diagram slide -->
<section class="slide">
    <h2 class="reveal">System Architecture</h2>
    <div class="mermaid-container reveal">
        <pre class="mermaid">
graph LR
    A[Client] --> B[API Gateway]
    B --> C[Auth Service]
    B --> D[Data Service]
    D --> E[(Database)]
        </pre>
    </div>
</section>
```

```css
/* ===========================================
   MERMAID DIAGRAMS
   Rendered by Mermaid CDN. Container constrains
   to viewport. Use theme matching the preset.
   =========================================== */
.mermaid-container {
    display: flex;
    justify-content: center;
    align-items: center;
    max-height: min(60vh, 500px);
    overflow: hidden;
}

.mermaid-container .mermaid {
    max-width: 90%;
}

.mermaid-container svg {
    max-height: min(55vh, 450px);
    width: auto;
}
```

```javascript
/* ===========================================
   MERMAID THEME INTEGRATION
   Set Mermaid theme to match the presentation's
   color scheme. Detect dark/light from background.
   =========================================== */

// Before mermaid.initialize():
const bgColor = getComputedStyle(document.documentElement)
    .getPropertyValue('--bg-primary').trim();
const isDark = isDarkColor(bgColor);

mermaid.initialize({
    startOnLoad: true,
    theme: isDark ? 'dark' : 'default',
    themeVariables: {
        primaryColor: getComputedStyle(document.documentElement)
            .getPropertyValue('--accent').trim() || '#4a9eff',
    }
});

function isDarkColor(color) {
    // Simple luminance check — works for hex and rgb
    const div = document.createElement('div');
    div.style.color = color;
    document.body.appendChild(div);
    const rgb = getComputedStyle(div).color.match(/\d+/g).map(Number);
    document.body.removeChild(div);
    const luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255;
    return luminance < 0.5;
}
```

**Anti-slop note**: Only include the Mermaid CDN script if the presentation actually contains `<pre class="mermaid">` blocks. The CDN is ~150KB gzipped — don't load it for presentations without diagrams. Mermaid renders on page load; no manual render call needed with `startOnLoad: true`.

## Animated Number Counters

Use with `layout-fact` slides for hero metrics. Browser support: Chrome, Edge, Safari 16.4+, Firefox 128+.

```css
/* ===========================================
   ANIMATED COUNTER: Numbers count up from 0
   Use with layout-fact slides for hero metrics.
   =========================================== */
@property --num {
    syntax: "<integer>";
    initial-value: 0;
    inherits: false;
}
.counter {
    animation: count-up 2s ease-out forwards;
    animation-play-state: paused; /* Triggered when slide becomes visible */
    counter-reset: num var(--num);
    font-variant-numeric: tabular-nums;
}
.counter::after {
    content: counter(num);
}
.slide.visible .counter {
    animation-play-state: running;
}
```

```html
<!-- Usage: set target via custom property in style attribute -->
<div class="big-number counter" style="--target: 4200000">
    <!-- CSS counter displays the animating number -->
</div>
```

```css
@keyframes count-up { to { --num: var(--target); } }
```

**JS fallback** for broader support (recommended):
```javascript
// JS-driven counter for broader browser support
function animateCounter(el, target, duration = 2000) {
    const start = performance.now();
    function step(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        el.textContent = Math.floor(eased * target).toLocaleString();
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}
```

## CSS-Only Animated Charts

CSS charts are for simple data storytelling (3-5 bars, 2-4 pie segments). For anything more complex, embed a screenshot of a real chart tool. These are presentation aids, not data visualization tools.

```css
/* ===========================================
   ANIMATED BAR CHART
   Bars grow from zero when slide enters viewport.
   Suitable for 3-5 bars. Not for complex datasets.
   =========================================== */
.bar-chart {
    display: flex;
    align-items: flex-end;
    gap: clamp(0.5rem, 2vw, 1.5rem);
    height: clamp(150px, 30vh, 300px);
    padding-top: 2rem;
}
.bar {
    flex: 1;
    border-radius: 4px 4px 0 0;
    transform-origin: bottom;
    transform: scaleY(0);
    transition: transform 0.8s var(--ease-out-expo);
}
.slide.visible .bar {
    transform: scaleY(1);
}
.bar:nth-child(1) { transition-delay: 0.1s; }
.bar:nth-child(2) { transition-delay: 0.2s; }
.bar:nth-child(3) { transition-delay: 0.3s; }
.bar:nth-child(4) { transition-delay: 0.4s; }
.bar:nth-child(5) { transition-delay: 0.5s; }
.bar-label {
    text-align: center;
    font-size: var(--small-size);
    margin-top: 0.5rem;
}
```

```css
/* ===========================================
   ANIMATED PIE CHART (conic-gradient)
   Uses @property for smooth animation.
   Suitable for 2-4 segments.
   =========================================== */
@property --p1 { syntax: "<percentage>"; initial-value: 0%; inherits: false; }
@property --p2 { syntax: "<percentage>"; initial-value: 0%; inherits: false; }
.pie-chart {
    width: clamp(120px, 20vw, 250px);
    height: clamp(120px, 20vw, 250px);
    border-radius: 50%;
    background: conic-gradient(
        var(--chart-color-1, #4f46e5) var(--p1),
        var(--chart-color-2, #e5e7eb) var(--p1)
    );
}
.slide.visible .pie-chart {
    animation: fill-pie 1.5s ease-out forwards;
}
@keyframes fill-pie { to { --p1: 72%; } }
```

## Optional CDN Dependencies

The skill is zero-dependency by default. These CDN includes are added only when specific features are used. Always include them at the end of `<body>`, before the `SlidePresentation` script.

| Feature | CDN | When to Include |
|---------|-----|-----------------|
| GSAP animations | `<script src="https://cdn.jsdelivr.net/npm/gsap@3.12/dist/gsap.min.js"></script>` | Slide has `data-animation` attribute |
| GSAP MotionPath | `<script src="https://cdn.jsdelivr.net/npm/gsap@3.12/dist/MotionPathPlugin.min.js"></script>` | Using the math-function widget |
| Mermaid diagrams | `<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>` | Slide contains `<pre class="mermaid">` |
| Rough.js | `<script src="https://cdn.jsdelivr.net/npm/roughjs@4.6.6/bundled/rough.cjs.min.js"></script>` | Using the Whiteboard preset |

## GSAP Playback Controls

When a slide has `data-animation`, it gets a playback control bar at the bottom. Adapted from the teach-me skill's `PlaybackController`.

```html
<!-- GSAP-animated slide with playback controls -->
<section class="slide" data-animation="process-flow">
    <h2 class="reveal">How Our Pipeline Works</h2>
    <div class="animation-container" id="anim-process-flow">
        <!-- SVG content from widget (see SVG Widget Library below) -->
    </div>
    <div class="playback-controls">
        <div class="playback-row">
            <button class="pb-btn" data-action="play" aria-label="Play">&#9654;</button>
            <button class="pb-btn" data-action="step-back" aria-label="Step back" disabled>&#9664;&#9664;</button>
            <button class="pb-btn" data-action="step-fwd" aria-label="Step forward" disabled>&#9654;&#9654;</button>
            <button class="pb-btn" data-action="replay" aria-label="Replay">&#8634;</button>
            <div class="pb-speed">
                <button class="pb-speed-btn" data-speed="0.5">0.5x</button>
                <button class="pb-speed-btn is-active" data-speed="1">1x</button>
                <button class="pb-speed-btn" data-speed="2">2x</button>
            </div>
        </div>
        <div class="playback-row">
            <input type="range" class="pb-scrubber" min="0" max="1" step="0.001" value="0">
            <span class="pb-status"></span>
        </div>
    </div>
</section>
```

```css
/* ===========================================
   GSAP PLAYBACK CONTROLS
   Appears at bottom of slides with data-animation.
   Controls play/pause, step, speed, and scrubbing.
   =========================================== */
.playback-controls {
    position: absolute;
    bottom: var(--slide-padding);
    left: 50%;
    transform: translateX(-50%);
    width: min(520px, calc(100% - 2 * var(--slide-padding)));
    padding: 0.5rem 1rem;
    background: color-mix(in oklch, var(--bg-primary), transparent 20%);
    border: 1px solid color-mix(in oklch, var(--text-primary), transparent 80%);
    border-radius: 8px;
    z-index: 10;
}

.playback-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
}
.playback-row + .playback-row { margin-top: 0.25rem; }

.pb-btn {
    width: 32px; height: 32px;
    border-radius: 50%;
    border: 1px solid color-mix(in oklch, var(--text-primary), transparent 70%);
    background: transparent;
    color: var(--text-primary);
    font-size: 0.85rem;
    display: flex; align-items: center; justify-content: center;
    padding: 0; cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
}
.pb-btn:hover:not(:disabled) {
    border-color: var(--accent, var(--text-primary));
    background: color-mix(in oklch, var(--accent, var(--text-primary)), transparent 85%);
}
.pb-btn:disabled { opacity: 0.3; cursor: default; }

.pb-speed { display: flex; gap: 2px; margin-left: auto; }
.pb-speed-btn {
    padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;
    border: 1px solid color-mix(in oklch, var(--text-primary), transparent 70%);
    background: transparent;
    color: var(--text-primary);
    font-family: var(--font-mono, monospace);
    cursor: pointer;
}
.pb-speed-btn.is-active {
    background: var(--accent, var(--text-primary));
    color: var(--bg-primary, #000);
    border-color: var(--accent, var(--text-primary));
}

.pb-scrubber {
    flex: 1; height: 4px;
    accent-color: var(--accent, var(--text-primary));
    cursor: pointer;
}

.pb-status {
    font-family: var(--font-mono, monospace);
    font-size: 0.75rem;
    color: color-mix(in oklch, var(--text-primary), transparent 40%);
    white-space: nowrap;
    min-width: 80px;
    text-align: right;
}

@media (prefers-reduced-motion: reduce) {
    .playback-controls { display: none; }
}
```

```javascript
/* ===========================================
   PLAYBACK CONTROLLER
   Connects the playback UI to a GSAP timeline.
   Each animated slide creates its own timeline;
   the controller wires it to the UI.

   Usage:
     const pc = new PlaybackController(slideElement);
     pc.setTimeline(tl, ["Step 1", "Step 2", "Done"]);
   =========================================== */

class PlaybackController {
    constructor(slideEl) {
        this.slideEl = slideEl;
        this.tl = null;
        this.isPlaying = false;
        this.labels = [];
        this.rafId = null;

        // Bind to controls within this slide only
        const q = (sel) => slideEl.querySelector(sel);
        const qa = (sel) => slideEl.querySelectorAll(sel);

        this.playBtn = q('[data-action="play"]');
        this.stepBack = q('[data-action="step-back"]');
        this.stepFwd = q('[data-action="step-fwd"]');
        this.replayBtn = q('[data-action="replay"]');
        this.scrubber = q('.pb-scrubber');
        this.statusEl = q('.pb-status');
        this.speedBtns = qa('.pb-speed-btn');

        this.playBtn.addEventListener('click', () => this.togglePlay());
        this.stepBack.addEventListener('click', () => this.step(-0.02));
        this.stepFwd.addEventListener('click', () => this.step(0.02));
        this.replayBtn.addEventListener('click', () => this.replay());
        this.scrubber.addEventListener('input', () => this.scrub(this.scrubber.value));
        this.speedBtns.forEach(btn => {
            btn.addEventListener('click', () => this.setSpeed(parseFloat(btn.dataset.speed)));
        });
    }

    setTimeline(tl, labels) {
        if (this.rafId) cancelAnimationFrame(this.rafId);
        if (this.tl) this.tl.pause();
        this.tl = tl;
        this.labels = labels || [];
        this.isPlaying = false;
        this.scrubber.value = 0;
        this.updateUI();
    }

    togglePlay() { this.isPlaying ? this.pause() : this.play(); }

    play() {
        if (!this.tl) return;
        if (this.tl.progress() >= 1) this.tl.restart();
        else this.tl.play();
        this.isPlaying = true;
        this.updateUI();
        this.startSync();
    }

    pause() {
        if (!this.tl) return;
        this.tl.pause();
        this.isPlaying = false;
        this.updateUI();
        if (this.rafId) { cancelAnimationFrame(this.rafId); this.rafId = null; }
    }

    step(delta) {
        if (!this.tl) return;
        this.tl.pause();
        this.isPlaying = false;
        this.tl.progress(Math.max(0, Math.min(1, this.tl.progress() + delta)));
        this.updateUI();
        this.scrubber.value = this.tl.progress();
    }

    setSpeed(speed) {
        if (this.tl) this.tl.timeScale(speed);
        this.speedBtns.forEach(btn => {
            btn.classList.toggle('is-active', parseFloat(btn.dataset.speed) === speed);
        });
    }

    scrub(progress) {
        if (!this.tl) return;
        this.tl.pause();
        this.isPlaying = false;
        this.tl.progress(parseFloat(progress));
        this.updateUI();
    }

    replay() {
        if (!this.tl) return;
        this.tl.restart();
        this.isPlaying = true;
        this.updateUI();
        this.startSync();
    }

    updateUI() {
        this.playBtn.innerHTML = this.isPlaying ? '&#9646;&#9646;' : '&#9654;';
        this.playBtn.setAttribute('aria-label', this.isPlaying ? 'Pause' : 'Play');
        this.stepBack.disabled = this.isPlaying;
        this.stepFwd.disabled = this.isPlaying;
        if (this.tl && this.labels.length) {
            const i = Math.min(
                Math.floor(this.tl.progress() * this.labels.length),
                this.labels.length - 1
            );
            this.statusEl.textContent = this.labels[i] || '';
        }
    }

    startSync() {
        const tick = () => {
            this.scrubber.value = this.tl.progress();
            this.updateUI();
            if (this.tl.progress() >= 1) { this.isPlaying = false; this.updateUI(); return; }
            if (this.isPlaying) this.rafId = requestAnimationFrame(tick);
        };
        this.rafId = requestAnimationFrame(tick);
    }
}
```

**Anti-slop note**: Each slide gets its own `PlaybackController` instance scoped to that slide's DOM. Don't use global IDs — use `slideEl.querySelector()` so multiple animated slides can coexist. Pause the timeline when navigating away from the slide (hook into `goToSlide()`).

## SVG Widget Library (GSAP)

Use these 5 widget patterns for animated diagram slides. Each creates a GSAP timeline. Pick the widget that matches your content type.

| Widget | Pattern | Best For |
|--------|---------|----------|
| Process Flow | Step-by-step boxes with arrows | Architecture, workflows, pipelines |
| Comparison | Side-by-side with highlight | Before/after, option analysis |
| Build-Up | Layered stacking diagram | "How it works", layer explanations |
| Data Transform | Input -> Process -> Output | Data pipelines, API flows |
| Math Function | Animated graph with moving point | Data/ML talks, metrics |

**Usage**: Mark a slide with `data-animation="process-flow"` (or any widget name). Include the corresponding SVG in the slide. The `SlidePresentation` class initializes the matching widget timeline and wires it to the playback controls when the slide becomes visible.

Don't include all 5 widget SVGs in every presentation. Only include the SVG for widgets actually used. The widget factory pattern means unused widgets add zero code. If a presentation uses no GSAP animations, the entire GSAP CDN include and PlaybackController should be omitted.

Use `var(--accent)` and `var(--text-primary)` instead of `var(--color-primary)` and `var(--color-text)` to match the slides skill's CSS variable naming. Scope all CSS class selectors to the slide context. Add viewport-relative sizing (`max-width: min(500px, 80vw)`).

```javascript
/* ===========================================
   WIDGET INITIALIZATION
   In SlidePresentation constructor, find all
   data-animation slides and initialize their widgets.
   =========================================== */

// Widget factory — maps data-animation values to timeline creators
const widgetFactory = {
    'process-flow': createProcessFlowTimeline,
    'comparison': createComparisonTimeline,
    'build-up': createBuildUpTimeline,
    'data-transform': createDataTransformTimeline,
    'math-function': createMathFunctionTimeline,
};

// In constructor:
this.animatedSlides = new Map();
this.slides.forEach((slide, i) => {
    const type = slide.dataset.animation;
    if (type && widgetFactory[type]) {
        const { timeline, labels } = widgetFactory[type](slide);
        const pc = new PlaybackController(slide);
        pc.setTimeline(timeline, labels);
        this.animatedSlides.set(i, pc);
    }
});

// In goToSlide() — pause previous, optionally auto-play new:
if (this.animatedSlides.has(prevIndex)) {
    this.animatedSlides.get(prevIndex).pause();
}
```
