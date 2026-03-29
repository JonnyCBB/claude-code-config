# Scrollytelling Patterns

## Table of Contents
- Sticky Graphic Pattern
- Scrollama Setup
- Chapter/Step HTML Structure
- CSS Scroll Progress Bar
- Responsive Breakpoints
- Accessibility
- Nutshell.js Expandable Definitions

## Sticky Graphic Pattern

The core scrollytelling layout uses a sticky figure panel that stays fixed while text scrolls past:

```html
<section id="scrolly">
  <figure class="sticky-figure">
    <div id="graphic"><!-- animation renders here --></div>
  </figure>
  <article class="steps">
    <div class="step" data-step="1">
      <h3>Concept Name</h3>
      <p>Explanation text...</p>
    </div>
    <div class="step" data-step="2">
      <h3>Next Concept</h3>
      <p>Next explanation...</p>
    </div>
  </article>
</section>
```

CSS for sticky positioning:

```css
#scrolly {
  position: relative;
  display: flex;
}

.sticky-figure {
  position: sticky;
  top: 2rem;
  width: 50%;
  height: calc(100vh - 4rem);
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: flex-start;
}

#graphic {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.steps {
  width: 50%;
  padding: 0 2rem;
}

.step {
  min-height: 75vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  opacity: 0.3;
  transition: opacity 0.3s ease;
}

.step.is-active {
  opacity: 1;
}
```

## Scrollama Setup

Initialize Scrollama to detect which step is currently in view:

```javascript
const scroller = scrollama();

scroller
  .setup({
    step: ".step",
    offset: 0.5,
    progress: true
  })
  .onStepEnter(({ element, index, direction }) => {
    // Activate step styling
    document.querySelectorAll(".step").forEach(s => s.classList.remove("is-active"));
    element.classList.add("is-active");

    // Trigger animation for this step
    updateAnimation(index);

    // Update sidebar TOC
    updateTOC(index);
  })
  .onStepProgress(({ element, index, progress }) => {
    // Optional: use progress (0-1) for fine-grained animation control
  });

// Handle window resize
window.addEventListener("resize", scroller.resize);
```

## Chapter/Step HTML Structure

Each chapter follows this consistent structure:

```html
<div class="step" data-step="3" id="concept-gradient">
  <!-- Step counter -->
  <span class="step-counter">3</span>

  <!-- Analogy callout -->
  <div class="analogy-callout">
    <p>"Feeling which way is downhill while blindfolded"</p>
  </div>

  <!-- Concept heading -->
  <h3>Gradient</h3>

  <!-- Main explanation -->
  <p>A gradient points in the direction of steepest increase...</p>

  <!-- Bridge to next concept -->
  <p class="bridge">Now that we know which direction to go, we need a strategy for walking...</p>

  <!-- Animation target (populated by JS) -->
  <div class="animation-target" data-animation="build-up" data-concept="gradient"></div>
</div>
```

## CSS Scroll Progress Bar

Pure CSS progress bar using scroll-driven animations (no JS needed):

```css
.progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: var(--color-primary);
  transform-origin: left;
  transform: scaleX(0);
  animation: progress-grow linear;
  animation-timeline: scroll();
  z-index: 1000;
}

@keyframes progress-grow {
  to { transform: scaleX(1); }
}
```

Fallback for browsers without `animation-timeline` support:

```javascript
if (!CSS.supports("animation-timeline", "scroll()")) {
  const bar = document.querySelector(".progress-bar");
  window.addEventListener("scroll", () => {
    const pct = window.scrollY / (document.body.scrollHeight - window.innerHeight);
    bar.style.transform = `scaleX(${pct})`;
  });
}
```

## Responsive Breakpoints

Switch from side-by-side to stacked layout on narrow screens:

```css
@media (max-width: 768px) {
  #scrolly {
    flex-direction: column;
  }

  .sticky-figure {
    position: relative;
    width: 100%;
    height: 50vh;
    top: 0;
  }

  .steps {
    width: 100%;
    padding: 0 1rem;
  }

  .sidebar-toc {
    display: none;
  }
}
```

## Accessibility

Always include reduced-motion support:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

This ensures scrollytelling content is accessible to users with vestibular disorders or motion sensitivity. The content remains fully readable — only animations and transitions are disabled.

## Nutshell.js Expandable Definitions

Use Nutshell for inline expandable definitions of technical terms:

```html
<!-- Load Nutshell -->
<script src="https://cdn.jsdelivr.net/gh/ncase/nutshell/nutshell.min.js"></script>

<!-- Usage: wrap term in a link with # prefix -->
<p>The <a href="#gradient">gradient</a> tells us which direction to go.</p>

<!-- Define the expansion (hidden heading) -->
<h4 id="gradient" hidden>Gradient</h4>
<p>A vector pointing in the direction of greatest increase of a function.</p>
```

When the reader clicks "gradient", the definition expands inline without navigating away.
