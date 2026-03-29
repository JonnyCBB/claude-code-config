# Navigation & Interaction Reference

JavaScript features for the SlidePresentation class, fragments, auto-animate, overview mode, routing, and keyboard shortcuts.

## Required JavaScript Features

Every presentation should include:

1. **SlidePresentation Class** — Main controller
   - Keyboard navigation (arrows, space)
   - Touch/swipe support
   - Mouse wheel navigation
   - Progress bar updates
   - Navigation dots

2. **Intersection Observer** — For scroll-triggered animations
   - Add `.visible` class when slides enter viewport
   - Trigger CSS animations efficiently

3. **Optional Enhancements** (based on style):
   - Custom cursor with trail
   - Particle system background (canvas)
   - Parallax effects
   - 3D tilt on hover
   - Magnetic buttons
   - Counter animations
   - **Inline editing** (only if user opted in during content discovery):
     - Edit toggle button (hidden by default, revealed via hover hotzone or `E` key)
     - Auto-save to localStorage
     - Export/save file functionality
     - See [references/edit-mode.md](edit-mode.md) for required code patterns

## Fragments System (Step-by-Step Content Reveal)

Fragments integrate with the existing scroll-snap model. When a slide has fragments, keypress/scroll first advances through all fragments, then moves to the next slide. Scrolling backward reverses fragments before going to the previous slide.

Use fragments for 2-4 slides per presentation maximum — typically for building an argument, step-by-step processes, or revealing a punchline. Never fragment every slide. MAX 3-4 fragment steps per slide — if more would be needed, split into multiple slides instead. Group related elements (e.g., a DAG node and its edges, a title and subtitle) into a single fragment step using shared `data-fragment-index` values.

**HTML pattern:**
```html
<section class="slide">
    <h2 class="reveal">Building Our Platform</h2>
    <ul>
        <li class="reveal fragment">First, we built the foundation</li>
        <li class="reveal fragment">Then, we added the API layer</li>
        <li class="reveal fragment fade-in-then-semi-out">Next, the UI components</li>
        <li class="reveal fragment">Finally, the monitoring</li>
    </ul>
</section>
```

**CSS additions:**
```css
/* ===========================================
   FRAGMENTS: Step-by-step content reveal
   Elements with .fragment are hidden until their turn.
   Press arrow-right/space to reveal one at a time.
   =========================================== */
.fragment {
    opacity: 0;
    transform: translateY(10px);
    transition: opacity 0.4s var(--ease-out-expo),
                transform 0.4s var(--ease-out-expo);
    pointer-events: none;
}
.fragment.visible {
    opacity: 1;
    transform: none;
    pointer-events: auto;
}
/* fade-in-then-semi-out: dims after the next fragment appears */
.fragment.visible.semi-out {
    opacity: 0.35;
}
/* highlight-current: only the active fragment is fully opaque */
.fragment.visible.highlight-dimmed {
    opacity: 0.3;
}
```

**JS additions to SlidePresentation class:**
```javascript
// In constructor:
this.fragmentIndex = {}; // { slideIndex: currentFragmentIndex }

// New method:
getFragments(slide) {
    return slide.querySelectorAll('.fragment');
}

// Modified navigation logic:
navigateNext() {
    const currentSlide = this.slides[this.currentSlide];
    const fragments = this.getFragments(currentSlide);
    const fi = this.fragmentIndex[this.currentSlide] || 0;

    if (fi < fragments.length) {
        // Reveal next fragment
        const frag = fragments[fi];
        frag.classList.add('visible');

        // Handle fade-in-then-semi-out: dim previous fragments
        if (fi > 0) {
            const prev = fragments[fi - 1];
            if (prev.classList.contains('fade-in-then-semi-out')) {
                prev.classList.add('semi-out');
            }
        }

        // Handle highlight-current: dim all previous
        fragments.forEach((f, i) => {
            if (i < fi && f.classList.contains('highlight-current')) {
                f.classList.add('highlight-dimmed');
            }
        });

        this.fragmentIndex[this.currentSlide] = fi + 1;
        return; // Don't advance slide
    }

    // All fragments shown — advance to next slide
    this.goToSlide(this.currentSlide + 1);
}

navigatePrev() {
    const currentSlide = this.slides[this.currentSlide];
    const fi = this.fragmentIndex[this.currentSlide] || 0;

    if (fi > 0) {
        // Hide last revealed fragment
        const fragments = this.getFragments(currentSlide);
        const frag = fragments[fi - 1];
        frag.classList.remove('visible', 'semi-out', 'highlight-dimmed');

        // Un-dim the now-last fragment
        if (fi > 1) {
            fragments[fi - 2].classList.remove('semi-out', 'highlight-dimmed');
        }

        this.fragmentIndex[this.currentSlide] = fi - 1;
        return; // Don't go to previous slide
    }

    // No fragments to hide — go to previous slide
    this.goToSlide(this.currentSlide - 1);
}
```

## Code Line Highlighting with Fragments

Integrates with the fragment system to walk through code step by step.

```css
/* ===========================================
   CODE HIGHLIGHTING: Walk through code step by step
   Integrates with fragment system.
   =========================================== */
pre code .line { transition: opacity 0.3s; }
pre code.highlighting .line { opacity: 0.3; }
pre code.highlighting .line.highlighted { opacity: 1; }
```

```html
<!-- Each fragment step highlights different lines -->
<pre><code class="highlighting">
<span class="line fragment" data-highlight="1-3">import { useState } from 'react';</span>
<span class="line fragment" data-highlight="4-6">function Counter() {</span>
<span class="line fragment" data-highlight="7-9">  return <button>{count}</button>;</span>
</code></pre>
```

Wrap each code line in a `<span class='line'>`. Use the fragment system to highlight groups of lines on each keypress — dim unhighlighted lines to 30% opacity.

## Auto-Animate (FLIP)

FLIP (First, Last, Invert, Play) captures element positions before and after a transition, then animates the difference. Elements are matched between consecutive slides by a shared `data-auto-animate-id` attribute.

Use auto-animate for 2-3 slide transitions per presentation maximum — typically for showing code evolution, layout changes, or concept building. Don't auto-animate every transition.

```html
<!-- Slide 1: Elements with data-auto-animate-id are tracked -->
<section class="slide" data-auto-animate>
    <h2 class="reveal" data-auto-animate-id="title">Our Architecture</h2>
    <div class="reveal" data-auto-animate-id="box1"
         style="width: 200px; height: 100px; background: var(--accent);">
        API Layer
    </div>
</section>

<!-- Slide 2: Same IDs in different positions — FLIP animates the transition -->
<section class="slide" data-auto-animate>
    <h2 class="reveal" data-auto-animate-id="title">Our Architecture (Expanded)</h2>
    <div class="reveal" data-auto-animate-id="box1"
         style="width: 300px; height: 150px; background: var(--accent); margin-left: 200px;">
        API Layer
    </div>
</section>
```

```javascript
/* ===========================================
   AUTO-ANIMATE (FLIP)
   Automatically morphs matching elements between
   consecutive slides. Uses data-auto-animate-id to
   match elements. Zero dependencies.

   FLIP = First, Last, Invert, Play
   - First: capture element position before transition
   - Last: let the browser render the new position
   - Invert: apply a transform to make it look like the old position
   - Play: remove the transform with a transition, animating to new position
   =========================================== */

// In SlidePresentation class:

capturePositions(slide) {
    const positions = new Map();
    slide.querySelectorAll('[data-auto-animate-id]').forEach(el => {
        const rect = el.getBoundingClientRect();
        const styles = getComputedStyle(el);
        positions.set(el.dataset.autoAnimateId, {
            x: rect.left,
            y: rect.top,
            width: rect.width,
            height: rect.height,
            opacity: parseFloat(styles.opacity),
            borderRadius: styles.borderRadius,
            backgroundColor: styles.backgroundColor,
        });
    });
    return positions;
}

flipAnimate(fromSlide, toSlide) {
    // Only animate between consecutive slides with data-auto-animate
    if (!fromSlide.hasAttribute('data-auto-animate') ||
        !toSlide.hasAttribute('data-auto-animate')) return;

    // FIRST: capture positions in the old slide
    const firstPositions = this.capturePositions(fromSlide);

    // LAST: positions in the new slide are already rendered
    // (use requestAnimationFrame to ensure layout)
    requestAnimationFrame(() => {
        toSlide.querySelectorAll('[data-auto-animate-id]').forEach(el => {
            const id = el.dataset.autoAnimateId;
            const first = firstPositions.get(id);
            if (!first) return; // New element, no FLIP needed

            const last = el.getBoundingClientRect();

            // INVERT: calculate the delta
            const dx = first.x - last.left;
            const dy = first.y - last.top;
            const sw = first.width / last.width;
            const sh = first.height / last.height;

            // Apply inverse transform (element appears in old position)
            el.style.transform = `translate(${dx}px, ${dy}px) scale(${sw}, ${sh})`;
            el.style.transformOrigin = 'top left';
            el.style.transition = 'none';

            // PLAY: remove transform with transition
            requestAnimationFrame(() => {
                el.style.transition = 'transform 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                el.style.transform = 'none';

                // Clean up after animation
                el.addEventListener('transitionend', () => {
                    el.style.transform = '';
                    el.style.transition = '';
                    el.style.transformOrigin = '';
                }, { once: true });
            });
        });
    });
}

// In goToSlide() — call flipAnimate before transitioning:
// const fromSlide = this.slides[this.currentSlide];
// const toSlide = this.slides[targetIndex];
// this.flipAnimate(fromSlide, toSlide);
```

**Anti-slop note**: FLIP only animates `transform` and `opacity` (GPU-composited properties). Don't try to FLIP `color`, `font-size`, or `padding` — those require layout recalculation and will jank. If you need to animate text size changes, scale the container instead. The `data-auto-animate` attribute on the `<section>` acts as an opt-in — slides without it won't trigger FLIP.

## Overview / Grid Mode

Press ESC or O to toggle overview mode, showing a thumbnail grid of all slides. Click any slide to jump to it.

```css
/* ===========================================
   OVERVIEW MODE: Thumbnail grid of all slides
   Press ESC or O to toggle. Click any slide to jump to it.
   =========================================== */
body.overview-mode {
    overflow: auto;
    scroll-snap-type: none;
}
body.overview-mode .slide {
    height: auto;
    aspect-ratio: 16 / 9;
    scroll-snap-align: none;
    transform: scale(0.25);
    transform-origin: top left;
    cursor: pointer;
    border: 2px solid transparent;
    transition: border-color 0.2s;
}
body.overview-mode .slide:hover {
    border-color: var(--accent, #4361ee);
}
.overview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
    padding: 2rem;
}
```

```javascript
toggleOverview() {
    const isOverview = document.body.classList.toggle('overview-mode');
    if (isOverview) {
        // Wrap slides in grid container
        const grid = document.createElement('div');
        grid.className = 'overview-grid';
        this.slides.forEach(slide => grid.appendChild(slide));
        document.body.appendChild(grid);
        // Add click handlers
        this.slides.forEach((slide, i) => {
            slide.addEventListener('click', () => {
                this.exitOverview(i);
            });
        });
    } else {
        this.exitOverview(this.currentSlide);
    }
}

exitOverview(targetSlide) {
    document.body.classList.remove('overview-mode');
    // Unwrap from grid
    const grid = document.querySelector('.overview-grid');
    if (grid) {
        this.slides.forEach(slide => document.body.insertBefore(slide, grid));
        grid.remove();
    }
    this.goToSlide(targetSlide);
}

// In keyboard handler:
case 'Escape':
case 'o':
case 'O':
    this.toggleOverview();
    break;
```

### Container Query Adaptations for Overview

When slides are thumbnailed in overview mode, container queries adapt content for the smaller size — hiding body text, enlarging headings, etc.

```css
/* ===========================================
   OVERVIEW MODE: Container Query Adaptations
   When slides shrink to thumbnails, adapt content
   for readability at small sizes.
   =========================================== */

/* Slides already have container-type: inline-size on .slide-content */
body.overview-mode .slide .slide-content {
    container-type: inline-size;
}

@container (max-width: 400px) {
    /* In thumbnail view, simplify content */
    .bullet-list li,
    .feature-list li { display: none; }
    .bullet-list li:first-child,
    .feature-list li:first-child { display: list-item; }
    .bullet-list li:first-child::after,
    .feature-list li:first-child::after {
        content: ' ...';
        color: var(--text-secondary);
    }

    /* Hide secondary elements */
    .slide-image { max-height: 30%; }
    .playback-controls { display: none; }
    .nav-dots { display: none; }
    pre code { font-size: 0.6rem; max-height: 40%; overflow: hidden; }
}

@container (max-width: 250px) {
    /* Very small thumbnails — show heading only */
    p, ul, ol, pre, .video-container, .mermaid-container,
    .animation-container, .chart-container { display: none; }
}
```

**Anti-slop note**: These container query rules are purely additive — they only apply inside `body.overview-mode` where slides are thumbnailed.

## URL Hash Routing / Deep Linking

Each slide gets a URL fragment (`#slide-1`, or a custom `data-hash` attribute like `#problem`, `#solution`). Enables sharing links to specific slides and browser back/forward navigation.

```html
<!-- Slides can have optional custom hash names -->
<section class="slide" data-hash="problem">
    <h2 class="reveal">The Problem</h2>
</section>
<section class="slide" data-hash="solution">
    <h2 class="reveal">Our Solution</h2>
</section>
```

```javascript
/* ===========================================
   URL HASH ROUTING
   Each slide gets a URL fragment for deep linking.
   Uses data-hash attribute if present, falls back to slide index.
   =========================================== */

// In SlidePresentation class:

updateHash() {
    const slide = this.slides[this.currentSlide];
    const hash = slide.dataset.hash || `slide-${this.currentSlide + 1}`;
    history.replaceState(null, '', `#${hash}`);
}

goToHashSlide() {
    const hash = location.hash.slice(1);
    if (!hash) return;

    // Try data-hash first, then slide-N format
    const byHash = this.slides.findIndex(s => s.dataset.hash === hash);
    if (byHash >= 0) {
        this.goToSlide(byHash);
        return;
    }

    const match = hash.match(/^slide-(\d+)$/);
    if (match) {
        const idx = parseInt(match[1]) - 1;
        if (idx >= 0 && idx < this.slides.length) {
            this.goToSlide(idx);
        }
    }
}

// In constructor:
this.goToHashSlide();
window.addEventListener('hashchange', () => this.goToHashSlide());

// In goToSlide():
this.updateHash();
```

**Anti-slop note**: Use `history.replaceState` (not `pushState`) to avoid polluting browser history with every slide navigation. The user can still use browser back/forward because `hashchange` events are listened for.

## Fullscreen Mode (F Key)

```javascript
/* ===========================================
   FULLSCREEN MODE
   Press F to toggle browser fullscreen.
   Uses the Fullscreen API (97%+ support).
   =========================================== */

// In keyboard handler:
case 'f':
case 'F':
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
    break;
```

**Anti-slop note**: No CSS needed — the browser handles fullscreen rendering. Don't add a fullscreen button to the UI; keyboard shortcut is sufficient for presentations.

## Home/End Keyboard Shortcuts

```javascript
// In keyboard handler:
case 'Home':
    e.preventDefault();
    this.goToSlide(0);
    break;
case 'End':
    e.preventDefault();
    this.goToSlide(this.slides.length - 1);
    break;
```

## Keyboard Shortcut Reference

| Key | Action |
|-----|--------|
| Right / Space / Down | Next slide / fragment |
| Left / Up | Previous slide / fragment |
| ESC / O | Toggle overview mode |
| S | Open speaker view |
| B | Toggle blackout |
| W | Toggle whiteout |
| E | Toggle edit mode (if enabled) |
| F | Toggle fullscreen |
| T | Cycle theme variant (light/dark) |
| P | Toggle presenter mode (cross-tab sync) |
| Home | Jump to first slide |
| End | Jump to last slide |
