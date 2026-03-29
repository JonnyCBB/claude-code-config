# Style Presets Reference

Curated visual styles for Frontend Slides. Each preset is inspired by real design references—no generic "AI slop" aesthetics. **Abstract shapes only—no illustrations.**

---

## ⚠️ CRITICAL: Viewport Fitting (Non-Negotiable)

**Every slide MUST fit exactly in the viewport. No scrolling within slides, ever.**

### Content Density Limits Per Slide

| Slide Type | Maximum Content |
|------------|-----------------|
| Title slide | 1 heading + 1 subtitle |
| Content slide | 1 heading + 4-6 bullets (max 2 lines each) |
| Feature grid | 1 heading + 6 cards (2x3 or 3x2) |
| Code slide | 1 heading + 8-10 lines of code |
| Quote slide | 1 quote (max 3 lines) + attribution |
| Two-column | 1 heading + 2 columns of 3-4 bullets each |
| Fact/stat | 1 large number + 1 subtitle + optional context line |
| Section divider | 1 heading + optional subtitle |
| Image-left/right | 1 image + 1 heading + 3-4 bullets |
| Video slide | 1 heading + 1 video (max 60vh height) |

**Too much content? → Split into multiple slides. Never scroll.**

### Required Base CSS (Include in ALL Presentations)

```css
/* ===========================================
   VIEWPORT FITTING: MANDATORY
   Copy this entire block into every presentation
   =========================================== */

/* 1. Lock document to viewport */
html, body {
    height: 100%;
    overflow-x: hidden;
}

html {
    scroll-snap-type: y mandatory;
    scroll-behavior: smooth;
}

/* Typography refinement — prevents orphan lines
   Progressive enhancement (87%+ support) — unsupported browsers render normal wrapping. No fallback needed. */
h1, h2, h3 { text-wrap: balance; }
p, li { text-wrap: pretty; }

/* 2. Each slide = exact viewport height */
.slide {
    width: 100vw;
    height: 100vh;
    height: 100dvh; /* Dynamic viewport for mobile */
    overflow: hidden; /* CRITICAL: No overflow ever */
    scroll-snap-align: start;
    display: flex;
    flex-direction: column;
    position: relative;
}

/* 3. Content wrapper */
.slide-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    max-height: 100%;
    overflow: hidden;
    padding: var(--slide-padding);
}

/* 4. ALL sizes use clamp() - scales with viewport */
:root {
    /* Typography */
    --title-size: clamp(1.5rem, 5vw, 4rem);
    --h2-size: clamp(1.25rem, 3.5vw, 2.5rem);
    --body-size: clamp(0.75rem, 1.5vw, 1.125rem);
    --small-size: clamp(0.65rem, 1vw, 0.875rem);

    /* Spacing */
    --slide-padding: clamp(1rem, 4vw, 4rem);
    --content-gap: clamp(0.5rem, 2vw, 2rem);
}

/* 5. Cards/containers use viewport-relative max sizes */
.card, .container {
    max-width: min(90vw, 1000px);
    max-height: min(80vh, 700px);
}

/* 6. Images constrained */
img {
    max-width: 100%;
    max-height: min(50vh, 400px);
    object-fit: contain;
}

/* 7. Grids adapt to space */
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));
    gap: clamp(0.5rem, 1.5vw, 1rem);
}

/* ===========================================
   RESPONSIVE BREAKPOINTS - Height-based
   =========================================== */

/* Short screens (< 700px height) */
@media (max-height: 700px) {
    :root {
        --slide-padding: clamp(0.75rem, 3vw, 2rem);
        --content-gap: clamp(0.4rem, 1.5vw, 1rem);
        --title-size: clamp(1.25rem, 4.5vw, 2.5rem);
    }
}

/* Very short (< 600px height) */
@media (max-height: 600px) {
    :root {
        --slide-padding: clamp(0.5rem, 2.5vw, 1.5rem);
        --title-size: clamp(1.1rem, 4vw, 2rem);
        --body-size: clamp(0.7rem, 1.2vw, 0.95rem);
    }

    .nav-dots, .keyboard-hint, .decorative {
        display: none;
    }
}

/* Extremely short - landscape phones (< 500px) */
@media (max-height: 500px) {
    :root {
        --slide-padding: clamp(0.4rem, 2vw, 1rem);
        --title-size: clamp(1rem, 3.5vw, 1.5rem);
        --body-size: clamp(0.65rem, 1vw, 0.85rem);
    }
}

/* Narrow screens */
@media (max-width: 600px) {
    .grid {
        grid-template-columns: 1fr;
    }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.2s !important;
    }
}

/* ===========================================
   HIGH CONTRAST
   Respect user OS "Increase Contrast" setting.
   Adds stronger borders and ensures text contrast.
   On dark presets, override --text-primary to #fff
   and --text-secondary to #ccc instead.
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
        opacity: 0;
    }
    .fragment.visible {
        opacity: 1;
    }
    .fragment.visible.semi-out {
        opacity: 0.5;
    }
}
```

### Viewport Fitting Checklist

Before finalizing any presentation, verify:

- [ ] Every `.slide` has `height: 100vh; height: 100dvh; overflow: hidden;`
- [ ] All font sizes use `clamp(min, preferred, max)`
- [ ] All spacing uses `clamp()` or viewport units
- [ ] Breakpoints exist for heights: 700px, 600px, 500px
- [ ] Content respects density limits (max 6 bullets, max 6 cards)
- [ ] No fixed pixel heights on content elements
- [ ] Images have `max-height` constraints
- [ ] No negated CSS functions (use `calc(-1 * clamp(...))` not `-clamp(...)`)

---

## Dark Themes

### 1. Bold Signal

**Vibe:** Confident, bold, modern, high-impact

**Layout:** Colored card on dark gradient. Number top-left, navigation top-right, title bottom-left.

**Typography:**
- Display: `Archivo Black` (900)
- Body: `Space Grotesk` (400/500)

**Colors:**
```css
:root {
    --bg-primary: #1a1a1a;
    --bg-surface: #FF5722;
    --bg-gradient: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --accent-primary: #FF5722;
    --accent-secondary: #FF8A65;
}
```

**Signature Elements:**
- Bold colored card as focal point (`background: var(--bg-surface)`) — orange, coral, or vibrant accent
- Text on card uses dark contrast (`color: #1a1a1a` on the `--bg-surface` card)
- Large section numbers (01, 02, etc.)
- Navigation breadcrumbs with active/inactive opacity states
- Grid-based layout for precise alignment

---

### 2. Electric Studio

**Vibe:** Bold, clean, professional, high contrast

**Layout:** Split panel—white top, blue bottom. Brand marks in corners.

**Typography:**
- Display: `Manrope` (800)
- Body: `Manrope` (400/500)

**Colors:**
```css
:root {
    --bg-primary: #0a0a0a;
    --bg-surface: #ffffff;
    --text-primary: #0a0a0a;
    --text-secondary: #555555;
    --accent-primary: #4361ee;
    --accent-secondary: #6b83f2;
}
```

**Signature Elements:**
- Two-panel vertical split
- Accent bar on panel edge
- Quote typography as hero element
- Minimal, confident spacing

---

### 3. Creative Voltage

**Vibe:** Bold, creative, energetic, retro-modern

**Layout:** Split panels—electric blue left, dark right. Script accents.

**Typography:**
- Display: `Syne` (700/800)
- Mono: `Space Mono` (400/700)

**Colors:**
```css
:root {
    --bg-primary: #0066ff;
    --bg-surface: #1a1a2e;
    --text-primary: #ffffff;
    --text-secondary: #b0b8d0;
    --accent-primary: #d4ff00;
    --accent-secondary: #0066ff;
}
```

**Signature Elements:**
- Electric blue + neon yellow contrast
- Halftone texture patterns
- Neon badges/callouts
- Script typography for creative flair

---

### 4. Dark Botanical

**Vibe:** Elegant, sophisticated, artistic, premium

**Layout:** Centered content on dark. Abstract soft shapes in corner.

**Typography:**
- Display: `Cormorant` (400/600) — elegant serif
- Body: `IBM Plex Sans` (300/400)

**Colors:**
```css
:root {
    --bg-primary: #0f0f0f;
    --bg-surface: #1a1a1a;
    --text-primary: #e8e4df;
    --text-secondary: #9a9590;
    --accent-primary: #d4a574;
    --accent-secondary: #e8b4b8;
    --accent-gold: #c9b896;
}
```

**Signature Elements:**
- Abstract soft gradient circles (blurred, overlapping)
- Warm color accents (pink, gold, terracotta)
- Thin vertical accent lines
- Italic signature typography
- **No illustrations—only abstract CSS shapes**

---

## Light Themes

### 5. Notebook Tabs

**Vibe:** Editorial, organized, elegant, tactile

**Layout:** Cream paper card on dark background. Colorful tabs on right edge.

**Typography:**
- Display: `Bodoni Moda` (400/700) — classic editorial
- Body: `DM Sans` (400/500)

**Colors:**
```css
:root {
    --bg-primary: #2d2d2d;
    --bg-surface: #f8f6f1;
    --text-primary: #1a1a1a;
    --text-secondary: #555555;
    --accent-primary: #98d4bb;
    --accent-secondary: #c7b8ea;
    --tab-1: #98d4bb; /* Mint */
    --tab-2: #c7b8ea; /* Lavender */
    --tab-3: #f4b8c5; /* Pink */
    --tab-4: #a8d8ea; /* Sky */
    --tab-5: #ffe6a7; /* Cream */
}
```

**Signature Elements:**
- Paper container with subtle shadow
- Colorful section tabs on right edge (vertical text)
- Binder hole decorations on left
- Tab text must scale with viewport: `font-size: clamp(0.5rem, 1vh, 0.7rem)`

---

### 6. Pastel Geometry

**Vibe:** Friendly, organized, modern, approachable

**Layout:** White card on pastel background. Vertical pills on right edge.

**Typography:**
- Display: `Plus Jakarta Sans` (700/800)
- Body: `Plus Jakarta Sans` (400/500)

**Colors:**
```css
:root {
    --bg-primary: #c8d9e6;
    --bg-surface: #faf9f7;
    --text-primary: #1a1a1a;
    --text-secondary: #555555;
    --accent-primary: #f0b4d4;
    --accent-secondary: #9b8dc4;
    --pill-pink: #f0b4d4;
    --pill-mint: #a8d4c4;
    --pill-sage: #5a7c6a;
    --pill-lavender: #9b8dc4;
    --pill-violet: #7c6aad;
}
```

**Signature Elements:**
- Rounded card with soft shadow
- **Vertical pills on right edge** with varying heights (like tabs)
- Consistent pill width, heights: short → medium → tall → medium → short
- Download/action icon in corner

---

### 7. Vintage Editorial

**Vibe:** Witty, confident, editorial, personality-driven
**Best for:** Personal brand decks, creative pitches, agency portfolios

**Layout:** Centered content on cream. Abstract geometric shapes as accent.

**Typography:**
- Display: `Fraunces` (700/900) — distinctive serif
- Body: `Work Sans` (400/500)

**Colors:**
```css
:root {
    --bg-primary: #f5f3ee;
    --bg-surface: #ffffff;
    --text-primary: #1a1a1a;
    --text-secondary: #555555;
    --accent-primary: #e8d4c0;
    --accent-secondary: #d4a574;
}
```

**Signature Elements:**
- Abstract geometric shapes (circle outline + line + dot)
- Bold bordered CTA boxes
- Witty, conversational copy style
- **No illustrations—only geometric CSS shapes**

**Why distinct:** Only preset that leans into personality and wit. Dark Botanical is elegant and restrained; Vintage Editorial is confident and playful with geometric shapes on warm cream.

---

## Specialty Themes

### 8. Neon Cyber

**Vibe:** Futuristic, techy, confident
**Best for:** Tech startups, cybersecurity talks, futuristic product demos

**Layout:** Dark canvas with neon-outlined cards and grid texture. Content floats on dark.

**Typography:**
- Display: `Clash Display` (600/700, Fontshare)
- Body: `Satoshi` (400/500, Fontshare)

**Colors:**
```css
:root {
    --bg-primary: #0a0f1c;
    --bg-surface: #111827;
    --text-primary: #e0e7ff;
    --text-secondary: #94a3b8;
    --accent-primary: #00ffcc;
    --accent-secondary: #ff00aa;
}
```

**Signature Elements:**
- Particle background effect:
  ```css
  .particle-bg {
      background-image: radial-gradient(circle, var(--accent-primary) 1px, transparent 1px);
      background-size: 30px 30px;
      animation: drift 20s linear infinite;
  }
  @keyframes drift {
      from { background-position: 0 0; }
      to { background-position: 30px 30px; }
  }
  ```
- Neon glow on key elements:
  ```css
  .neon-glow {
      box-shadow: 0 0 10px var(--accent-primary), 0 0 40px rgba(0, 255, 204, 0.15);
      text-shadow: 0 0 8px var(--accent-primary);
  }
  ```
- Grid pattern overlay on slides: `background-image: linear-gradient(rgba(0,255,204,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,204,0.03) 1px, transparent 1px); background-size: 50px 50px;`
- Scan line effect: `background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.1) 2px, rgba(0,0,0,0.1) 4px);`

**Why distinct:** Only preset with cyberpunk/neon aesthetic. Creative Voltage is retro-modern energy; Neon Cyber is dark, futuristic, dystopian.

---

### 9. Terminal Green

**Vibe:** Developer-focused, hacker aesthetic
**Best for:** Developer tools, API launches, CLI product demos

**Layout:** Full-dark background mimicking a terminal. Monospace everything. Content in "terminal windows."

**Typography:**
- Display: `JetBrains Mono` (700)
- Body: `JetBrains Mono` (400)

**Colors:**
```css
:root {
    --bg-primary: #0d1117;
    --bg-surface: #161b22;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --accent-primary: #39d353;
    --accent-secondary: #d29922;
}
```

**Signature Elements:**
- Scan lines overlay:
  ```css
  .terminal-scanlines {
      background: repeating-linear-gradient(
          0deg,
          transparent,
          transparent 2px,
          rgba(0, 0, 0, 0.15) 2px,
          rgba(0, 0, 0, 0.15) 4px
      );
      pointer-events: none;
  }
  ```
- Blinking cursor animation:
  ```css
  .cursor::after {
      content: '|';
      color: var(--accent-primary);
      animation: blink 1s step-end infinite;
  }
  @keyframes blink {
      50% { opacity: 0; }
  }
  ```
- Terminal prompt styling: prefix content blocks with `$ ` in `var(--accent-primary)` color
- Code syntax highlighting using `--accent-primary` for keywords, `--accent-secondary` for strings, `--text-secondary` for comments

**Why distinct:** Only preset that is fully monospace and mimics a terminal. Neon Cyber is flashy cyberpunk; Terminal Green is authentic developer aesthetic.

---

### 10. Swiss Modern

**Vibe:** Clean, precise, Bauhaus-inspired
**Best for:** Corporate presentations, data-driven decks, annual reports

**Layout:** Visible grid structure. Asymmetric layouts with mathematical precision. White space as a design element.

**Typography:**
- Display: `Archivo` (800, Google)
- Body: `Nunito` (400, Google)

**Colors:**
```css
:root {
    --bg-primary: #ffffff;
    --bg-surface: #f5f5f5;
    --text-primary: #111111;
    --text-secondary: #555555;
    --accent-primary: #ff3300;
    --accent-secondary: #000000;
}
```

**Signature Elements:**
- Visible grid background:
  ```css
  .grid-bg {
      background-image:
          linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px);
      background-size: 60px 60px;
  }
  ```
- Asymmetric column layouts: use CSS Grid with unequal column widths (`grid-template-columns: 2fr 1fr` or `1fr 3fr`)
- Geometric decoration shapes: circles and rectangles in `--accent-primary` with hard edges, no border-radius blur
- Oversized section numbers in `--accent-primary`: `font-size: clamp(4rem, 12vw, 10rem); font-weight: 800; opacity: 0.15;`

**Why distinct:** Only preset inspired by Swiss/Bauhaus design tradition. Micrographic is technical precision with annotation style; Swiss Modern is typographic boldness with red accent.

---

### 11. Paper & Ink

**Vibe:** Editorial, literary, thoughtful
**Best for:** Storytelling, thought leadership, literary presentations, book launches

**Layout:** Centered text-heavy layout on warm cream. Editorial conventions: drop caps, pull quotes, horizontal rules.

**Typography:**
- Display: `Cormorant Garamond` (600/700, Google)
- Body: `Source Serif 4` (400, Google)

**Colors:**
```css
:root {
    --bg-primary: #faf9f7;
    --bg-surface: #ffffff;
    --text-primary: #1a1a1a;
    --text-secondary: #666666;
    --accent-primary: #c41e3a;
    --accent-secondary: #9a8c7a;
}
```

**Signature Elements:**
- Drop caps on opening paragraphs:
  ```css
  .drop-cap::first-letter {
      font-family: 'Cormorant Garamond', serif;
      font-size: clamp(3rem, 6vw, 5rem);
      float: left;
      line-height: 0.8;
      margin-right: 0.1em;
      color: var(--accent-primary);
  }
  ```
- Pull quotes styled as large italic serif:
  ```css
  .pull-quote {
      font-family: 'Cormorant Garamond', serif;
      font-size: clamp(1.5rem, 3vw, 2.5rem);
      font-style: italic;
      border-left: 3px solid var(--accent-primary);
      padding-left: 1.5em;
      color: var(--text-secondary);
  }
  ```
- Elegant horizontal rules: thin line with centered diamond `hr::after { content: '\u25C6'; }`
- Footnote-style annotations: small text aligned to bottom margin with superscript reference numbers

**Why distinct:** Only preset with literary/editorial styling. Vintage Editorial is witty and personality-driven with geometric shapes; Paper & Ink is classic, restrained, text-first.

---

## Modern Themes

### 12. Liquid Glass

**Vibe:** Modern, premium, spatial depth
**Best for:** Product launches, design-forward companies, Apple-style keynotes

**Layout:** Content on frosted glass panels over gradient mesh background. Large rounded corners.

**Typography:**
- Display: `General Sans` (600/700) — or `Switzer` (Fontshare)
- Body: `General Sans` (400)

**Colors:**
```css
:root {
    --bg-primary: #4a3f8a;
    --bg-surface: rgba(255, 255, 255, 0.12);
    --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --bg-mesh: radial-gradient(at 20% 80%, #667eea 0%, transparent 50%),
               radial-gradient(at 80% 20%, #764ba2 0%, transparent 50%),
               radial-gradient(at 50% 50%, #5b8def 0%, transparent 60%);
    --glass-bg: rgba(255, 255, 255, 0.12);
    --glass-border: rgba(255, 255, 255, 0.2);
    --glass-shadow: rgba(0, 0, 0, 0.1);
    --text-primary: #ffffff;
    --text-secondary: rgba(255, 255, 255, 0.7);
    --accent-primary: #667eea;
    --accent-secondary: #764ba2;
}
```

**Signature Elements:**
- Frosted glass panels: `backdrop-filter: blur(16px); background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 16px;`
- Gradient mesh background (multiple layered `radial-gradient`)
- Soft box-shadow using `var(--glass-shadow)`
- Large rounded corners (16-24px)
- No hard edges — everything feels floaty and translucent

**Why distinct:** Only preset using `backdrop-filter`. Creates genuine perceived depth. Degrades gracefully to solid semi-transparent panels in unsupported browsers (support: 96%+).

---

### 13. Director's Cut

**Vibe:** Cinematic, moody, narrative, restrained
**Best for:** Keynotes, brand stories, case studies, narrative storytelling

**Layout:** Centered content with letterbox bars (top/bottom). Vignette darkening at edges.

**Typography:**
- Display: `Cinzel` (700/900, Google) — ALL-CAPS, letter-spacing: 0.2-0.4em
- Body: `Crimson Pro` (300/400, Google)

**Colors:**
```css
:root {
    --bg-primary: #0d1520;
    --bg-surface: #1a2332;
    --text-primary: #e8e0d4;
    --text-secondary: #8a7e72;
    --accent-primary: #d4a050;
    --accent-secondary: #c47830;
    --letterbox: #000000;
}
```

**Signature Elements:**
- Letterbox bars: `position: fixed; height: clamp(30px, 5vh, 60px); background: var(--letterbox);` at top and bottom
- Film grain texture overlay (from grain texture pattern)
- Extreme letter-spacing on headings (0.2-0.4em)
- Thin horizontal rules between sections
- Chapter/act numbering ("ACT I", "ACT II")
- Vignette effect: `box-shadow: inset 0 0 150px rgba(0,0,0,0.5);` on each slide
- Amber accent for highlights and emphasis

**Why distinct:** No current preset has cinematic framing. The letterbox bars alone create an immediately recognizable visual language. Paper & Ink is literary (book, not film). Neon Cyber is electric/loud. This is moody and restrained.

---

### 14. Micrographic

**Vibe:** Precise, technical, credible, restrained
**Best for:** Engineering reviews, research presentations, data-heavy decks, technical proposals

**Layout:** Content on light background with visible grid texture. Annotation-style labels in margins.

**Typography:**
- Display: `Space Grotesk` (500/700, Google)
- Body: `IBM Plex Sans` (400, Google)
- Mono: `IBM Plex Mono` (400, Google) — for labels and annotations

**Colors:**
```css
:root {
    --bg-primary: #f8f9fa;
    --bg-surface: #ffffff;
    --text-primary: #3a4a5c;
    --text-secondary: #5a6a7c;
    --accent-primary: #2a6ab0;
    --accent-secondary: #5a8ac0;
    --grid-line: rgba(58, 74, 92, 0.08);
    --annotation: #8a9ab0;
}
```

**Signature Elements:**
- Visible grid lines as design texture: `background-image: linear-gradient(var(--grid-line) 1px, transparent 1px), linear-gradient(90deg, var(--grid-line) 1px, transparent 1px); background-size: 40px 40px;`
- Small annotation text in margins: `font-family: var(--font-mono); font-size: 0.65rem; color: var(--annotation); text-transform: uppercase; letter-spacing: 0.1em;` — e.g., "FIG 01", "REF: 2026-Q1"
- Thin crosshair marks at grid intersections (via CSS `::before`/`::after` on decorative elements)
- Technical diagram-style dividers (thin lines with small circles at endpoints)
- Coordinate/index numbering on slides

**Why distinct:** Swiss Modern is Bauhaus-bold with red accents and chunky type — it shouts. Micrographic whispers. Terminal Green is hacker aesthetic. This is for engineers and scientists who want credibility through precision.

---

### 15. Jewel Mono

**Vibe:** Focused, sophisticated, brandable
**Best for:** Corporate presentations, brand-aligned decks, fintech, luxury

**Layout:** Tonal depth through single-hue shading. Color-block sections (dark/mid/light zones).

**Typography:**
- Display: `Epilogue` (700/800, Google)
- Body: `Epilogue` (400)

**Colors** (example: sapphire — swappable to any hue by changing `--hue`):
```css
:root {
    /* Change this one value to rebrand the entire deck */
    --hue: 220;

    /* Standard role mapping (oklch equivalents):
       --bg-primary   → --hue-darkest  oklch(0.15 0.05 var(--hue))
       --bg-surface   → --hue-surface  oklch(0.96 0.01 var(--hue))
       --text-primary → --text-on-light oklch(0.20 0.05 var(--hue))
       --text-secondary → --hue-mid    oklch(0.45 0.12 var(--hue))
       --accent-primary → --hue-mid    oklch(0.45 0.12 var(--hue))
       --accent-secondary → --hue-light oklch(0.65 0.08 var(--hue))
    */

    --hue-darkest: oklch(0.15 0.05 var(--hue));
    --hue-dark: oklch(0.25 0.08 var(--hue));
    --hue-mid: oklch(0.45 0.12 var(--hue));
    --hue-light: oklch(0.65 0.08 var(--hue));
    --hue-lightest: oklch(0.90 0.03 var(--hue));
    --hue-surface: oklch(0.96 0.01 var(--hue));
    --text-on-dark: oklch(0.95 0.01 var(--hue));
    --text-on-light: oklch(0.20 0.05 var(--hue));
}
```

**Signature Elements:**
- **Single-hue palette**: All colors derived from one hue value (no second color)
- Color-block sections: slides alternate between dark, mid, and light zones
- Tonal borders: slightly lighter/darker than background (never gray/black)
- Shadows using darker values of same hue (not `rgba(0,0,0,...)`)
- The constraint IS the aesthetic — restriction creates sophistication
- Most **brandable** preset: change `--hue` and every slide matches any corporate color

**Why distinct:** No existing preset is monochromatic. Every one uses 3+ colors. The single-hue restriction creates immediate sophistication. Change one CSS variable to match any brand.

**CSS technique note:** Uses `oklch()` with a shared `--hue` variable. This is more maintainable than `color-mix()` for monochrome — each tonal step has independent lightness and chroma control. Browser support: 93%+. Fallback: hardcode hex values.

#### Color Drench Variant

The Color Drench mode transforms Jewel Mono from sophisticated tonal restraint to full saturation immersion. Same `--hue` variable, higher chroma values:

**Default Jewel Mono** (restrained):
```css
--hue-dark: oklch(0.25 0.08 var(--hue));
--hue-mid: oklch(0.45 0.12 var(--hue));
--hue-light: oklch(0.65 0.08 var(--hue));
```

**Color Drench** (full saturation):
```css
--hue-dark: oklch(0.25 0.18 var(--hue));
--hue-mid: oklch(0.50 0.22 var(--hue));
--hue-light: oklch(0.70 0.16 var(--hue));
```

When a user requests "Color Drench" or "fully saturated Jewel Mono," use the higher chroma values. Also:
- Full-bleed saturated backgrounds (no white-space zones)
- Duotone photo treatment: `filter: grayscale(1) contrast(1.2); mix-blend-mode: multiply;` on images over a saturated background
- Bolder text shadows using the saturated hue: `text-shadow: 0 2px 20px oklch(0.3 0.2 var(--hue));`

---

### 16. Whiteboard

**Vibe:** Informal, sketch-like, brainstorming, approachable
**Best for:** Brainstorming sessions, early-stage pitches, workshop presentations, design thinking

**Layout:** Content on off-white background with hand-drawn borders and underlines. Elements look sketched, not polished.

**Typography:**
- Display: `Caveat` (700, Google) — handwriting-style
- Body: `Nunito` (400, Google) — friendly rounded sans-serif
- Mono: `Fira Code` (400, Google) — for code blocks

**Colors:**
```css
:root {
    --bg-primary: #fdf6e3;
    --bg-surface: #ffffff;
    --text-primary: #2c2c2c;
    --text-secondary: #5a5a5a;
    --accent-primary: #2d7dd2;
    --accent-secondary: #e74c3c;
    --accent-green: #27ae60;
    --sketch-stroke: #2c2c2c;
    --sketch-fill: rgba(45, 125, 210, 0.1);
}
```

**Signature Elements:**
- Hand-drawn borders on cards/containers using Rough.js: `const rc = rough.svg(svg); rc.rectangle(10, 10, 200, 100, { roughness: 1.5, stroke: 'var(--sketch-stroke)' });`
- SVG underlines under headings drawn with Rough.js `line()` — wobbly, not straight
- Sticky-note style cards: slight rotation (`transform: rotate(-1deg)` to `rotate(2deg)` randomly), yellow/pink/blue/green tints
- Doodle-style decorations: arrows, stars, circles drawn as SVG paths with rough.js
- No sharp shadows — use sketch-style cross-hatching fills instead
- Optional: grid-paper background using thin dotted lines

**CDN Requirement:**
```html
<script src="https://cdn.jsdelivr.net/npm/roughjs@4.6.6/bundled/rough.cjs.min.js"></script>
```

**Rough.js initialization pattern:**
```javascript
/* ===========================================
   ROUGH.JS WHITEBOARD ELEMENTS
   Draw hand-drawn borders and underlines on load.
   =========================================== */
document.querySelectorAll('.sketch-border').forEach(el => {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.style.position = 'absolute';
    svg.style.inset = '0';
    svg.style.width = '100%';
    svg.style.height = '100%';
    svg.style.pointerEvents = 'none';
    el.style.position = 'relative';
    el.appendChild(svg);

    const rc = rough.svg(svg);
    const rect = el.getBoundingClientRect();
    svg.setAttribute('viewBox', `0 0 ${rect.width} ${rect.height}`);
    svg.appendChild(rc.rectangle(4, 4, rect.width - 8, rect.height - 8, {
        roughness: 1.5,
        stroke: getComputedStyle(el).getPropertyValue('--sketch-stroke').trim() || '#2c2c2c',
        strokeWidth: 2,
        bowing: 2,
    }));
});

document.querySelectorAll('.sketch-underline').forEach(el => {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.style.position = 'absolute';
    svg.style.bottom = '-4px';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = '8px';
    svg.style.pointerEvents = 'none';
    el.style.position = 'relative';
    el.appendChild(svg);

    const rc = rough.svg(svg);
    const w = el.offsetWidth;
    svg.setAttribute('viewBox', `0 0 ${w} 8`);
    svg.appendChild(rc.line(0, 4, w, 4, {
        roughness: 1.2,
        stroke: getComputedStyle(el).getPropertyValue('--accent-primary').trim() || '#2d7dd2',
        strokeWidth: 2.5,
    }));
});
```

**Why distinct:** No existing preset uses hand-drawn aesthetics. Every other preset aims for polish — this intentionally looks unpolished, which is perfect for workshops and brainstorming where "finished" slides would feel too formal.

---

## 2026 Themes

### 17. Bento Box

**Vibe:** Premium, modular, information-dense, Apple-keynote-grade
**Best for:** Product launches, feature overviews, quarterly business reviews

**Layout:** Content organized in 6-9 asymmetrical rectangular tiles per slide. Varied tile sizes create visual hierarchy. Generous gutters between tiles. Large rounded corners.

**Typography:**
- Display: `Space Grotesk` (600/700, Google) — geometric, technical feel
- Body: `Space Grotesk` (400, Google) — same family for consistency with the grid

**Font Loading:**
```html
<!-- Source: Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
```

**Colors:**
```css
:root {
    --bg-primary: #0A0A0A;
    --bg-surface: #1C1C1E;
    --text-primary: #ffffff;
    --text-secondary: #98989D;
    --accent-primary: #0A84FF;
    --accent-secondary: #30D158;
}
```

**Signature Elements:**
- Asymmetric tile grid using CSS Grid: `grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr);` with varied `grid-column`/`grid-row` spans
- Generous gutters: `gap: clamp(0.5rem, 1.5vw, 1.5rem);`
- Rounded corners on all tiles: `border-radius: clamp(8px, 1vw, 16px);`
- One brand-tint accent color per slide (change `--accent-primary` per-slide section)
- Tiles use `--bg-surface` background with subtle border: `border: 1px solid rgba(255,255,255,0.06);`

**Why distinct:** Only preset using bento grid layout. Information hierarchy through tile size rather than text formatting. Inspired by Apple WWDC presentation style.

---

### 18. Aurora Glow

**Vibe:** Atmospheric, ambient, cinematic warmth
**Best for:** Brand storytelling, vision decks, keynotes, "inspire the room" moments

**Layout:** Full-bleed gradient mesh backgrounds with frosted card overlays for text. Content floats on atmospheric color.

**Typography:**
- Display: `Outfit` (300/400, Google) — light weight for ethereal feel
- Body: `Plus Jakarta Sans` (400/500, Google)

**Font Loading:**
```html
<!-- Source: Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap" rel="stylesheet">
```

**Colors:**
```css
:root {
    --bg-primary: #1a0533;
    --bg-surface: rgba(255, 255, 255, 0.08);
    --text-primary: #ffffff;
    --text-secondary: rgba(255, 255, 255, 0.65);
    --accent-primary: #14B8A6;
    --accent-secondary: #8B5CF6;
    --bg-gradient: radial-gradient(at 20% 80%, #6B21A8 0%, transparent 50%),
                   radial-gradient(at 80% 20%, #14B8A6 0%, transparent 50%),
                   radial-gradient(at 50% 100%, #1a0533 0%, transparent 70%);
}
```

**Signature Elements:**
- Full-bleed mesh gradient: `background: var(--bg-primary); background-image: var(--bg-gradient);`
- Frosted card overlays: `backdrop-filter: blur(20px); background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px;`
- Subtle glow on accent elements: `box-shadow: 0 0 30px rgba(20, 184, 166, 0.15);`
- Grain texture overlay: `background-image: url("data:image/svg+xml,...");` (same pattern as other presets using `.has-grain`)
- Ambient feel — all transitions use `ease-out` with 0.6s duration

**Why distinct:** Only preset with warm atmospheric gradients as the primary visual. Liquid Glass is cool/structural with glass UI card panels; Aurora Glow is warm and enveloping with gradient mesh backgrounds that create mood.

**Distinct from Liquid Glass:** Liquid Glass uses `backdrop-filter` on content cards against a cool gradient. Aurora Glow uses full-bleed warm gradients as the background itself, with frosted overlays being secondary to the atmospheric effect.

---

### 19. Scrapbook

**Vibe:** Curated chaos, collage-style layering, deliberately imperfect but tasteful
**Best for:** Team retrospectives, brainstorming recaps, personal storytelling, culture decks

**Layout:** Elements layered with deliberate imperfection. Slight rotations, overlapping frames, stacked on warm paper-like background.

**Typography:**
- Display: `Kalam` (700, Google) — handwritten, warm
- Body: `DM Sans` (400/500, Google) — clean contrast to handwritten headings

**Font Loading:**
```html
<!-- Source: Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
```

**Colors:**
```css
:root {
    --bg-primary: #F5F0E8;
    --bg-surface: #ffffff;
    --text-primary: #1a1a1a;
    --text-secondary: #5a5a5a;
    --accent-primary: #F2B5C8;
    --accent-secondary: #A8D8EA;
    --tape-yellow: #FDE68A;
    --tape-mint: #A7F3D0;
}
```

**Signature Elements:**
- Washi tape strips: CSS linear-gradient strips with slight rotation (`transform: rotate(-2deg)`) placed at top of content cards
- Torn-edge effect on images: `clip-path: polygon(...)` with irregular vertices
- Polaroid frames: White border (`padding: 8px; background: white; box-shadow: 2px 4px 12px rgba(0,0,0,0.15);`) with slight rotation (`transform: rotate(var(--rotation, -2deg));`)
- Paper texture background: `background-color: var(--bg-primary); background-image: url("data:image/svg+xml,...");` with subtle noise
- Sticker accents: small colored circles/shapes with `border-radius: 50%` positioned semi-randomly
- Elements have varied rotations: `-3deg` to `3deg` using CSS custom properties

**Why distinct:** Only preset with collage/physical-materials aesthetic. Whiteboard uses Rough.js for hand-drawn sketch borders; Scrapbook layers physical-world objects (tape, photos, stickers). Uses Kalam (not Caveat) to differentiate from Whiteboard.

---

### 20. Retro Futura

**Vibe:** 1960s-80s space-age retrofuturism, nostalgic but forward-looking
**Best for:** Vision decks, product roadmaps, conference keynotes, innovation narratives

**Layout:** Centered content with analog-style frames, starburst decorations, and rounded "screen" viewports.

**Typography:**
- Display: `Bebas Neue` (400, Google) — ALL CAPS, condensed, bold presence
- Body: `Figtree` (400/500, Google) — warm, modern sans
- Mono: `Space Mono` (400, Google) — for data/stats

**Font Loading:**
```html
<!-- Source: Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Figtree:wght@400;500;600&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
```

**Colors:**
```css
:root {
    --bg-primary: #0B1120;
    --bg-surface: #162035;
    --text-primary: #F0E7D8;
    --text-secondary: #8A9AB0;
    --accent-primary: #E86C3A;
    --accent-secondary: #D4A843;
    --teal: #5B9A8B;
}
```

**Signature Elements:**
- Starbursts: CSS `::before`/`::after` pseudo-elements with `clip-path: polygon(...)` creating pointed-star shapes
- Orbit lines: Thin dashed circles using `border: 1px dashed var(--accent-secondary); border-radius: 50%;`
- Halftone dot patterns: CSS `radial-gradient` with small dots as background texture
- Rounded "screen" viewports: Content areas with heavy border-radius (`border-radius: 20px`) and inset shadow simulating CRT/retro monitors
- Mid-century dividers: Horizontal rules with diamond/dot centerpiece
- ALL CAPS headings with generous `letter-spacing: 0.15em`

**Why distinct:** Only preset with retrofuturist aesthetic. Creative Voltage is retro-modern energy (electric blue + neon yellow); Retro Futura is specifically space-age optimism (navy + burnt orange + analog amber).

---

## Font Pairing Quick Reference

| # | Preset | Display Font | Body Font | Source |
|---|--------|--------------|-----------|--------|
| 1 | Bold Signal | Archivo Black | Space Grotesk | Google |
| 2 | Electric Studio | Manrope | Manrope | Google |
| 3 | Creative Voltage | Syne | Space Mono | Google |
| 4 | Dark Botanical | Cormorant | IBM Plex Sans | Google |
| 5 | Notebook Tabs | Bodoni Moda | DM Sans | Google |
| 6 | Pastel Geometry | Plus Jakarta Sans | Plus Jakarta Sans | Google |
| 7 | Vintage Editorial | Fraunces | Work Sans | Google |
| 8 | Neon Cyber | Clash Display | Satoshi | Fontshare |
| 9 | Terminal Green | JetBrains Mono | JetBrains Mono | JetBrains |
| 10 | Swiss Modern | Archivo | Nunito | Google |
| 11 | Paper & Ink | Cormorant Garamond | Source Serif 4 | Google |
| 12 | Liquid Glass | General Sans | General Sans | Fontshare |
| 13 | Director's Cut | Cinzel | Crimson Pro | Google |
| 14 | Micrographic | Space Grotesk | IBM Plex Sans | Google |
| 15 | Jewel Mono | Epilogue | Epilogue | Google |
| 16 | Whiteboard | Caveat | Nunito | Google |
| 17 | Bento Box | Space Grotesk | Space Grotesk | Google |
| 18 | Aurora Glow | Outfit | Plus Jakarta Sans | Google |
| 19 | Scrapbook | Kalam | DM Sans | Google |
| 20 | Retro Futura | Bebas Neue | Figtree | Google |

---

## DO NOT USE (Generic AI Patterns)

**Fonts:** Inter, Roboto, Arial, system fonts as display

**Colors:** `#6366f1` (generic indigo), purple gradients on white

**Layouts:** Everything centered, generic hero sections, identical card grids

**Decorations:** Realistic illustrations, gratuitous glassmorphism, drop shadows without purpose

---

## CSS Gotchas (Common Mistakes)

### Negating CSS Functions

**WRONG — silently ignored by browsers:**
```css
right: -clamp(28px, 3.5vw, 44px);   /* ❌ Invalid! Browser ignores this */
margin-left: -min(10vw, 100px);      /* ❌ Invalid! */
top: -max(2rem, 4vh);                /* ❌ Invalid! */
```

**CORRECT — wrap in `calc()`:**
```css
right: calc(-1 * clamp(28px, 3.5vw, 44px));  /* ✅ */
margin-left: calc(-1 * min(10vw, 100px));     /* ✅ */
top: calc(-1 * max(2rem, 4vh));               /* ✅ */
```

CSS does not allow a leading `-` before function names like `clamp()`, `min()`, `max()`. The browser silently discards the entire declaration, causing the property to fall back to its initial/inherited value. This is especially dangerous because there is no console error — the element simply appears in the wrong position.

**Rule: Always use `calc(-1 * ...)` to negate CSS function values.**

---

## Troubleshooting Viewport Issues

### Content Overflows the Slide

**Symptoms:** Scrollbar appears, content cut off, elements outside viewport

**Solutions:**
1. Check slide has `overflow: hidden` (not `overflow: auto` or `visible`)
2. Reduce content — split into multiple slides
3. Ensure all fonts use `clamp()` not fixed `px` or `rem`
4. Add/fix height breakpoints for smaller screens
5. Check images have `max-height: min(50vh, 400px)`

### Text Too Small on Mobile / Too Large on Desktop

**Symptoms:** Unreadable text on phones, oversized text on big screens

**Solutions:**
```css
/* Use clamp with viewport-relative middle value */
font-size: clamp(1rem, 3vw, 2.5rem);
/*              ↑       ↑      ↑
            minimum  scales  maximum */
```

### Content Doesn't Fill Short Screens

**Symptoms:** Excessive whitespace on landscape phones or short browser windows

**Solutions:**
1. Add `@media (max-height: 600px)` and `(max-height: 500px)` breakpoints
2. Reduce padding at smaller heights
3. Hide decorative elements (`display: none`)
4. Consider hiding nav dots and hints on short screens

### Testing Recommendations

Test at these viewport sizes:
- **Desktop:** 1920×1080, 1440×900, 1280×720
- **Tablet:** 1024×768 (landscape), 768×1024 (portrait)
- **Mobile:** 375×667 (iPhone SE), 414×896 (iPhone 11)
- **Landscape phone:** 667×375, 896×414

Use browser DevTools responsive mode to quickly test multiple sizes.
