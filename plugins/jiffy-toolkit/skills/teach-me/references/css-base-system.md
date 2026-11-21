# CSS Base System (Structural)

Component classes for chapter content. The rest of the structural CSS (spacing, typography, grain, reduced motion, sidebar TOC) is already in the FIXED block of `templates/scrollytelling-base.html`; colors and fonts come from the selected preset in `style-presets.md`.

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

