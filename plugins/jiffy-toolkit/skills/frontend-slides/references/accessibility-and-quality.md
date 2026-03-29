# Accessibility & Quality Reference

Code quality requirements, accessibility standards, inert slides, and high contrast support.

## Accessibility Requirements

- Semantic HTML (`<section>`, `<nav>`, `<main>`)
- Keyboard navigation works
- ARIA labels where needed
- Reduced motion support
- `inert` attribute on non-visible slides
- ARIA slide semantics with live region announcements
- `prefers-contrast: more` media query

### Inert Slides

```javascript
/* ===========================================
   INERT SLIDES
   Non-visible slides are marked inert so they are
   removed from tab order and screen reader tree.
   =========================================== */

// In goToSlide():
this.slides.forEach((slide, i) => {
    slide.inert = (i !== this.currentSlide);
});
```

**Anti-slop note**: The `inert` attribute (97%+ support) is a single attribute that replaces the need for `aria-hidden="true"` + `tabindex="-1"` on every focusable child. Don't use both — `inert` alone is sufficient.

### ARIA Slide Semantics

```html
<!-- Each slide section gets ARIA attributes -->
<section class="slide"
         role="region"
         aria-roledescription="slide"
         aria-label="Slide 1 of 12">
    <h2 class="reveal">Slide Title</h2>
</section>
```

```javascript
/* ===========================================
   ARIA SLIDE SEMANTICS
   Announces slide changes to screen readers.
   =========================================== */

// In constructor — set up aria attributes:
this.slides.forEach((slide, i) => {
    slide.setAttribute('role', 'region');
    slide.setAttribute('aria-roledescription', 'slide');
    slide.setAttribute('aria-label', `Slide ${i + 1} of ${this.slides.length}`);
});

// Add live region for announcements:
const liveRegion = document.createElement('div');
liveRegion.setAttribute('aria-live', 'polite');
liveRegion.setAttribute('aria-atomic', 'true');
liveRegion.className = 'sr-only';
document.body.appendChild(liveRegion);
this.liveRegion = liveRegion;

// In goToSlide() — announce current slide:
this.liveRegion.textContent = `Slide ${index + 1} of ${this.slides.length}`;
```

### Screen Reader Only Utility

```css
/* Screen-reader only utility */
.sr-only {
    position: absolute;
    width: 1px; height: 1px;
    padding: 0; margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}
```

### High Contrast Support

```css
/* ===========================================
   HIGH CONTRAST
   Respect user OS "Increase Contrast" setting.
   Adds stronger borders and ensures text contrast.
   =========================================== */
@media (prefers-contrast: more) {
    :root {
        --text-primary: #000;
        --text-secondary: #333;
    }

    .slide {
        border-bottom: 2px solid currentColor;
    }

    .card, .content-box, .glass-panel {
        border: 2px solid currentColor;
    }

    .fragment {
        opacity: 0; /* Keep fragments hidden but ensure visible ones are fully opaque */
    }
    .fragment.visible {
        opacity: 1;
    }
    .fragment.visible.semi-out {
        opacity: 0.5; /* Higher than default 0.35 for contrast */
    }
}
```

**Anti-slop note**: On dark presets, override `--text-primary` to `#fff` and `--text-secondary` to `#ccc` instead. Presets should consider their own contrast overrides.

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
    .reveal {
        transition: opacity 0.3s ease;
        transform: none;
    }
}
```
