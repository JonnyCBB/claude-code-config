# CSS Base System (Structural)

> This file contains structural CSS shared by all presets. Visual CSS (colors, fonts) is defined per-preset in `style-presets.md`.

## Table of Contents
- CSS Custom Properties
- Typography Scale
- Card Depth Hierarchy
- Staggered Animations
- Grain Texture Overlay
- Accessibility
- Sidebar TOC Styling

## CSS Custom Properties

```css
:root {
  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 2rem;
  --space-xl: 4rem;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.08);
  --shadow-lg: 0 10px 25px rgba(0,0,0,0.12);

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 300ms ease;
}
```

## Typography Scale

```css
h1 {
  font-family: var(--font-heading);
  font-weight: 400;  /* Instrument Serif looks best at regular weight */
  font-size: clamp(2rem, 4vw + 1rem, 3.5rem);
  line-height: 1.2;
  color: var(--color-text);
  text-wrap: balance;
}
h2 {
  font-family: var(--font-heading);
  font-weight: 400;
  font-size: clamp(1.5rem, 3vw + 0.75rem, 2.5rem);
  line-height: 1.3;
  color: var(--color-text);
  text-wrap: balance;
}
h3 {
  font-family: var(--font-heading);
  font-weight: 400;
  font-size: clamp(1.25rem, 2vw + 0.5rem, 1.75rem);
  line-height: 1.4;
  color: var(--color-text);
  text-wrap: balance;
}
h4 {
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 1.25rem;
  line-height: 1.4;
  color: var(--color-text-secondary);
}

body {
  font: 400 1.125rem/1.7 var(--font-body);
  color: var(--color-text);
  background: var(--color-bg);
  text-wrap: pretty;
}

code, pre {
  font-family: var(--font-mono);
  font-size: 0.9em;
  font-feature-settings: "tnum" 1;
}

code {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 0.1em 0.3em;
}

pre {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: var(--space-md);
  overflow-x: auto;
}

pre code {
  background: none;
  border: none;
  padding: 0;
}
```

## Card Depth Hierarchy

Use shadow depth to indicate semantic importance:

```css
/* Level 0: Flat content */
.content-block {
  background: var(--color-surface);
  border-radius: 8px;
}

/* Level 1: Slight elevation — analogy callouts */
.analogy-callout {
  background: var(--color-primary-light);
  border-left: 4px solid var(--color-primary);
  border-radius: 0 8px 8px 0;
  padding: var(--space-md) var(--space-lg);
  margin: var(--space-md) 0;
  font-style: italic;
}

/* Level 2: Medium elevation — animation containers */
.animation-container {
  border-radius: 12px;
  padding: var(--space-lg);
}

/* Level 3: High elevation — key insight/summary */
.key-insight {
  background: var(--color-accent-light);
  border: 2px solid var(--color-accent);
  border-radius: 12px;
  padding: var(--space-lg);
  box-shadow: var(--shadow-md);
}
```

## Staggered Animations

Use CSS custom property `--i` for staggered entrance animations:

```css
.stagger-item {
  opacity: 0;
  transform: translateY(20px);
  animation: stagger-in 0.5s ease forwards;
  animation-delay: calc(var(--i) * 0.1s);
}

@keyframes stagger-in {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

Usage in HTML:

```html
<div class="stagger-item" style="--i: 0">First item</div>
<div class="stagger-item" style="--i: 1">Second item</div>
<div class="stagger-item" style="--i: 2">Third item</div>
```

## Grain Texture Overlay

```css
/* Subtle noise texture — the single most effective anti-AI-slop differentiator */
body::after {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 9999;
  opacity: 0.08;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 256px 256px;
}
```

## Accessibility

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

## Sidebar TOC Styling

```css
.sidebar-toc {
  position: fixed;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 200px;
  padding: var(--space-md);
  z-index: 100;
}

.toc-item {
  display: block;
  padding: var(--space-xs) var(--space-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 0.85rem;
  border-left: 2px solid var(--color-border);
  transition: all var(--transition-fast);
}

.toc-item:hover {
  color: var(--color-primary);
  border-left-color: var(--color-primary);
}

.toc-item.is-active {
  color: var(--color-primary);
  border-left-color: var(--color-primary);
  font-weight: 600;
}
```

JavaScript to update active TOC item:

```javascript
function updateTOC(activeIndex) {
  document.querySelectorAll(".toc-item").forEach((item, i) => {
    item.classList.toggle("is-active", i === activeIndex);
  });
}
```
