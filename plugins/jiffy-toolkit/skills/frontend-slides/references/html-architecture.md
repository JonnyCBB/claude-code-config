# HTML Architecture Reference

File structure patterns and the full HTML template for presentations.

## File Structure

For single presentations:
```
presentation.html    # Self-contained presentation
assets/              # Images, if any
```

For projects with multiple presentations:
```
[presentation-name].html
[presentation-name]-assets/
```

## HTML Template

Follow this structure for all presentations:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Presentation Title</title>

    <!-- Fonts (use Fontshare or Google Fonts) -->
    <link rel="stylesheet" href="https://api.fontshare.com/v2/css?f[]=...">

    <style>
        /* ===========================================
           CSS CUSTOM PROPERTIES (THEME)
           Easy to modify: change these to change the whole look
           =========================================== */
        :root {
            /* Colors */
            --bg-primary: #0a0f1c;
            --bg-secondary: #111827;
            --text-primary: #ffffff;
            --text-secondary: #9ca3af;
            --accent: #00ffcc;
            --accent-glow: rgba(0, 255, 204, 0.3);

            /* Typography - MUST use clamp() for responsive scaling */
            --font-display: 'Clash Display', sans-serif;
            --font-body: 'Satoshi', sans-serif;
            --title-size: clamp(2rem, 6vw, 5rem);
            --subtitle-size: clamp(0.875rem, 2vw, 1.25rem);
            --body-size: clamp(0.75rem, 1.2vw, 1rem);

            /* Spacing - MUST use clamp() for responsive scaling */
            --slide-padding: clamp(1.5rem, 4vw, 4rem);
            --content-gap: clamp(1rem, 2vw, 2rem);

            /* Animation */
            --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
            --duration-normal: 0.6s;
        }

        /* ===========================================
           COLOR-MIX() THEME GENERATION
           Derive palette variants from 2-3 base colors.
           Use oklch color space (not srgb) for perceptually uniform mixing.
           Browser support: 92%+. Fallback: hardcode hex values as custom property defaults.
           =========================================== */
        /* Example pattern — adapt base colors per preset:
        :root {
            --brand: #2563eb;
            --brand-light: color-mix(in oklch, var(--brand), white 40%);
            --brand-dark: color-mix(in oklch, var(--brand), black 30%);
            --brand-subtle: color-mix(in oklch, var(--brand), transparent 85%);
            --surface: color-mix(in oklch, var(--brand), white 95%);
        }
        */

        /* Typography refinement — prevents orphan lines
           Progressive enhancement (87%+ support) — unsupported browsers render normal wrapping. No fallback needed. */
        h1, h2, h3 { text-wrap: balance; }
        p, li { text-wrap: pretty; }

        /* ===========================================
           BASE STYLES
           =========================================== */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html {
            scroll-behavior: smooth;
            scroll-snap-type: y mandatory;
            height: 100%;
        }

        body {
            font-family: var(--font-body);
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow-x: hidden;
            height: 100%;
        }

        /* ===========================================
           SLIDE CONTAINER
           CRITICAL: Each slide MUST fit exactly in viewport
           - Use height: 100vh (NOT min-height)
           - Use overflow: hidden to prevent scroll
           - Content must scale with clamp() values
           =========================================== */
        .slide {
            width: 100vw;
            height: 100vh; /* EXACT viewport height - no scrolling */
            height: 100dvh; /* Dynamic viewport height for mobile */
            padding: var(--slide-padding);
            scroll-snap-align: start;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
            overflow: hidden; /* Prevent any content overflow */
        }

        /* Content wrapper that prevents overflow */
        .slide-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            max-height: 100%;
            overflow: hidden;
            container-type: inline-size;
        }

        /* Adapt layout based on available content width */
        @container (max-width: 700px) {
            .grid { grid-template-columns: repeat(2, 1fr); }
            .columns { grid-template-columns: 1fr; }
        }
        @container (max-width: 400px) {
            .grid { grid-template-columns: 1fr; }
        }

        /* ===========================================
           RESPONSIVE BREAKPOINTS
           Adjust content for different screen sizes
           =========================================== */
        @media (max-height: 600px) {
            :root {
                --slide-padding: clamp(1rem, 3vw, 2rem);
                --content-gap: clamp(0.5rem, 1.5vw, 1rem);
            }
        }

        @media (max-width: 768px) {
            :root {
                --title-size: clamp(1.5rem, 8vw, 3rem);
            }
        }

        @media (max-height: 500px) and (orientation: landscape) {
            /* Extra compact for landscape phones */
            :root {
                --title-size: clamp(1.25rem, 5vw, 2rem);
                --slide-padding: clamp(0.75rem, 2vw, 1.5rem);
            }
        }

        /* ===========================================
           ANIMATIONS
           Trigger via .visible class (added by JS on scroll)
           =========================================== */
        .reveal {
            opacity: 0;
            transform: translateY(30px);
            transition: opacity var(--duration-normal) var(--ease-out-expo),
                        transform var(--duration-normal) var(--ease-out-expo);
        }

        .slide.visible .reveal {
            opacity: 1;
            transform: translateY(0);
        }

        /* Stagger children */
        .reveal:nth-child(1) { transition-delay: 0.1s; }
        .reveal:nth-child(2) { transition-delay: 0.2s; }
        .reveal:nth-child(3) { transition-delay: 0.3s; }
        .reveal:nth-child(4) { transition-delay: 0.4s; }

        /* ... more styles ... */
    </style>
</head>
<body>
    <!-- Progress bar (optional) -->
    <div class="progress-bar"></div>

    <!-- Navigation dots (optional) -->
    <nav class="nav-dots">
        <!-- Generated by JS -->
    </nav>

    <!-- Slides -->
    <section class="slide title-slide">
        <h1 class="reveal">Presentation Title</h1>
        <p class="reveal">Subtitle or author</p>
    </section>

    <section class="slide">
        <h2 class="reveal">Slide Title</h2>
        <p class="reveal">Content...</p>
    </section>

    <!-- More slides... -->

    <script>
        /* ===========================================
           SLIDE PRESENTATION CONTROLLER
           Handles navigation, animations, and interactions
           =========================================== */

        class SlidePresentation {
            constructor() {
                // ... initialization
            }

            // ... methods
        }

        // Initialize
        new SlidePresentation();
    </script>
</body>
</html>
```

## Code Quality Requirements

**Comments:**
Every section should have clear comments explaining:
- What it does
- Why it exists
- How to modify it

```javascript
/* ===========================================
   CUSTOM CURSOR
   Creates a stylized cursor that follows mouse with a trail effect.
   - Uses lerp (linear interpolation) for smooth movement
   - Grows larger when hovering over interactive elements
   =========================================== */
class CustomCursor {
    constructor() {
        // ...
    }
}
```

**CSS Native Nesting (96%+ support):**
Generated CSS should use native nesting for readability. Note: `&` is required in native CSS (unlike Sass).

```css
/* PREFERRED: Native CSS nesting */
.slide {
    & h2 { text-wrap: balance; font-family: var(--font-display); }
    & .content { container-type: inline-size; }
    & .reveal { opacity: 0; }
    &.visible .reveal { opacity: 1; }
}
```

## Style Reference: Effect -> Feeling Mapping

Use this guide to match animations to intended feelings:

### Dramatic / Cinematic
- Slow fade-ins (1-1.5s), large scale transitions (0.9 -> 1)
- Dark backgrounds with spotlight effects, parallax, full-bleed images

### Techy / Futuristic
- Neon glow effects, particle systems, grid patterns
- Monospace accents, glitch/scramble text, cyan/magenta/electric blue

### Playful / Friendly
- Bouncy easing (spring physics), large rounded corners
- Pastel/bright colors, floating/bobbing animations, hand-drawn elements

### Professional / Corporate
- Subtle, fast animations (200-300ms), clean sans-serif
- Navy/slate/charcoal, precise spacing, data visualization focus

### Calm / Minimal
- Very slow, subtle motion, high whitespace
- Muted palette, serif typography, generous padding, content-focused

### Editorial / Magazine
- Strong typography hierarchy, pull quotes and callouts
- Image-text interplay, grid-breaking layouts, serif headlines + sans-serif body

## Animation Patterns Reference

### Entrance Animations

```css
/* Fade + Slide Up (most common) */
.reveal {
    opacity: 0;
    transform: translateY(30px);
    transition: opacity 0.6s var(--ease-out-expo),
                transform 0.6s var(--ease-out-expo);
}
.visible .reveal {
    opacity: 1;
    transform: translateY(0);
}

/* Scale In */
.reveal-scale {
    opacity: 0;
    transform: scale(0.9);
    transition: opacity 0.6s, transform 0.6s var(--ease-out-expo);
}

/* Slide from Left */
.reveal-left {
    opacity: 0;
    transform: translateX(-50px);
    transition: opacity 0.6s, transform 0.6s var(--ease-out-expo);
}

/* Blur In */
.reveal-blur {
    opacity: 0;
    filter: blur(10px);
    transition: opacity 0.8s, filter 0.8s var(--ease-out-expo);
}
```

### Staggered Text Reveal

Staggered text reveal creates a cinematic title-sequence feel. Use on 1-2 headlines per presentation — typically the title slide and one key section header. Using it everywhere destroys the effect.

```css
/* ===========================================
   STAGGERED TEXT REVEAL
   Characters/words slide up from behind a clipping boundary.
   Use ONLY on headlines (1-2 per presentation). Never on body text.
   =========================================== */
.reveal-text span {
    display: inline-block;
    clip-path: inset(0 0 100% 0);
    animation: text-up 0.6s cubic-bezier(0.77, 0, 0.175, 1) forwards;
    animation-delay: calc(var(--i) * 0.04s);
}
@keyframes text-up { to { clip-path: inset(0 0 0 0); } }
```

```javascript
/* Split headline text into individually animated spans */
function splitTextForReveal(element) {
    const words = element.textContent.split(' ');
    element.innerHTML = words.map((word, i) =>
        `<span style="--i:${i}">${word}&nbsp;</span>`
    ).join('');
}
// Apply to elements with .reveal-text class when they become visible
```

### Background Effects

```css
/* Gradient Mesh */
.gradient-bg {
    background:
        radial-gradient(ellipse at 20% 80%, rgba(120, 0, 255, 0.3) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(0, 255, 200, 0.2) 0%, transparent 50%),
        var(--bg-primary);
}

/* Grid Pattern */
.grid-bg {
    background-image:
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 50px 50px;
}
```

### Texture Overlay

Use grain on 1-3 slides per presentation maximum (typically title slide and section dividers). Never on every slide. Keep opacity between 0.08-0.15. This is the single most effective way to make CSS gradients look designer-crafted instead of AI-generated.

Uses pre-rendered canvas PNG data URI (not live SVG `feTurbulence`). SVG filters re-render on every paint causing jank; the canvas approach generates once on page load and costs zero runtime computation.

```javascript
/* Grain texture — pre-rendered noise tile for performance */
(function generateGrain() {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 200;
    const ctx = canvas.getContext('2d');
    const imageData = ctx.createImageData(200, 200);
    for (let i = 0; i < imageData.data.length; i += 4) {
        const v = Math.random() * 255;
        imageData.data[i] = imageData.data[i + 1] = imageData.data[i + 2] = v;
        imageData.data[i + 3] = 255;
    }
    ctx.putImageData(imageData, 0, 0);
    document.documentElement.style.setProperty('--grain-url', `url(${canvas.toDataURL()})`);
})();
```

```css
/* Apply grain as a pseudo-element overlay — use sparingly */
.slide.has-grain::after {
    content: '';
    position: absolute;
    inset: 0;
    background: var(--grain-url) repeat;
    mix-blend-mode: multiply;
    opacity: 0.12;
    pointer-events: none;
}
```

### Interactive Effects

```javascript
/* 3D Tilt on Hover */
class TiltEffect {
    constructor(element) {
        this.element = element;
        this.element.style.transformStyle = 'preserve-3d';
        this.element.style.perspective = '1000px';
        this.bindEvents();
    }

    bindEvents() {
        this.element.addEventListener('mousemove', (e) => {
            const rect = this.element.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;

            this.element.style.transform = `
                rotateY(${x * 10}deg)
                rotateX(${-y * 10}deg)
            `;
        });

        this.element.addEventListener('mouseleave', () => {
            this.element.style.transform = 'rotateY(0) rotateX(0)';
        });
    }
}
```
