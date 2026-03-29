# Preset Creation Guide

## Purpose

This guide applies to anyone creating new visual presets for the `/teach-me` or `/frontend-slides` skills. It establishes the design bar, variable contracts, and quality checks every preset must meet before being added to the skill.

---

## Design Principles

**Bold aesthetic direction** — Every preset needs a clear conceptual direction. Timid compromises produce forgettable output. Name the vibe, commit to it, and let the code reflect it fully.

**Distinctive typography** — Never use Inter, Roboto, Arial, or system fonts as the primary display font. Pair a distinctive display font (from Google Fonts, Adobe Fonts, or a variable font stack) with a refined, legible body font. Typography is the fastest signal of quality.

**Cohesive color with dominance** — One dominant color anchored by a sharp accent outperforms an evenly-distributed six-color palette every time. Pick a dominant, pick an accent, and let everything else support them.

**Motion for delight** — One well-orchestrated page load animation beats scattered micro-interactions across every element. If the preset includes motion, make it intentional and singular.

**Atmospheric backgrounds** — Flat colors are table stakes. Reach for gradient meshes, subtle noise textures, geometric patterns, or layered transparencies to create depth without clutter.

**Match complexity to vision** — Maximalist designs earn elaborate CSS and markup. Minimalist designs earn restraint. Never add complexity to a simple preset or strip character from a rich one to save lines.

---

## anti-slop Checklist

Run through these before submitting a new preset:

- [ ] Does it have a clear, distinct vibe that no other preset already covers?
- [ ] Could you describe it in 3 adjectives that don't apply to any existing preset?
- [ ] Is the display font distinctive — not Inter, Roboto, Arial, or system fonts?
- [ ] Does the color palette have a dominant color, not an even spread?
- [ ] Would a user recognize this preset from a thumbnail at 200px wide?

If any box is unchecked, revise before adding.

---

## Variable Contract (teach-me)

All teach-me presets must populate these 14 CSS custom properties. Both light and dark mode variants must define all 14.

### Colors

| Variable | Role |
|---|---|
| `--color-bg` | Page / slide background |
| `--color-surface` | Card, panel, elevated surface |
| `--color-text` | Primary body text |
| `--color-text-secondary` | Captions, metadata, muted text |
| `--color-primary` | Primary interactive / brand color |
| `--color-primary-light` | Tinted background for primary elements |
| `--color-accent` | Sharp accent for highlights and calls to action |
| `--color-accent-light` | Tinted background for accent elements |
| `--color-border` | Dividers, input borders, outlines |
| `--color-success` | Success states and positive feedback |
| `--color-error` | Error states and destructive actions |

### Fonts

| Variable | Role |
|---|---|
| `--font-heading` | Display font for titles and headings |
| `--font-body` | Body and UI text |
| `--font-mono` | Code blocks and monospaced content |

---

## Accessibility Requirements

- **WCAG 2.2 AA minimum**: 4.5:1 contrast ratio for body text; 3:1 for large text (18px+ bold or 24px+ regular) and UI components such as buttons and inputs.
- **Both modes independently**: Light and dark mode variants must each meet contrast requirements on their own — passing in one mode does not excuse failures in the other.
- **Reduced motion**: Include a `prefers-reduced-motion` media query that disables or substantially reduces any animations and transitions defined by the preset.

Suggested verification tools: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/), browser DevTools accessibility panel, or the `axe` CLI.
