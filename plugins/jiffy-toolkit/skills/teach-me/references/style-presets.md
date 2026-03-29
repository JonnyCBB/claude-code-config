# Style Presets

> All presets use the same 11 CSS color variables and 3 font variables. The structural HTML never changes — only the `:root` values, alternate theme block, and font `<link>` tags swap per preset.

## Variable Contract

Every preset MUST define these exact variable names:

**Colors** (11): `--color-bg`, `--color-surface`, `--color-text`, `--color-text-secondary`, `--color-primary`, `--color-primary-light`, `--color-accent`, `--color-accent-light`, `--color-border`, `--color-success`, `--color-error`

**Fonts** (3): `--font-heading`, `--font-body`, `--font-mono`

**Shadows** (3, in alternate theme): `--shadow-sm`, `--shadow-md`, `--shadow-lg`

---

### 1. Warm Scholar

**Vibe**: Warm, literary, contemplative, gentle, inviting
**Best for**: General-purpose, gentle introductions, conceptual explanations, humanities
**Default theme**: light

**Typography**:

- Heading: Instrument Serif (400)
- Body: DM Sans (400, 600)
- Code: JetBrains Mono (400, 600)

**Font Loading**:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@100..1000&family=JetBrains+Mono:wght@400;600&display=swap"
  rel="stylesheet"
/>
```

**Colors (Primary Mode)**:

```css
:root {
  --color-bg: #faf9f5;
  --color-surface: #ffffff;
  --color-text: #1a1a18;
  --color-text-secondary: #6b6a68;
  --color-primary: #d97757;
  --color-primary-light: #f5e6df;
  --color-accent: #6a9bcc;
  --color-accent-light: #e0edf5;
  --color-border: #e8e6dc;
  --color-success: #788c5d;
  --color-error: #c45a4a;

  --font-heading: "Instrument Serif", Georgia, serif;
  --font-body: "DM Sans", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", "Fira Code", monospace;
}
```

**Colors (Alternate Mode)**:

```css
[data-theme="dark"] {
  --color-bg: #2b2a27;
  --color-surface: #353431;
  --color-text: #eeeeee;
  --color-text-secondary: #9a9893;
  --color-primary: #d97757;
  --color-primary-light: #4a3530;
  --color-accent: #6a9bcc;
  --color-accent-light: #2a3a4a;
  --color-border: #4a4945;
  --color-success: #98ac7d;
  --color-error: #e07060;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.5);
}
```

**Signature Elements**:

- Subtle grain texture overlay (SVG noise filter at 8% opacity)
- Warm-tinted shadows in light mode (`rgba(26,26,24,...)`)

---

### 2. Observatory

**Vibe**: Dark, contemplative, scientific, precise, luminous
**Best for**: Mathematics, physics, algorithms, neural networks, data visualization
**Default theme**: dark

**Typography**:

- Heading: Space Grotesk (400, 600, 700)
- Body: Source Serif 4 (400, 600, italic)
- Code: JetBrains Mono (400, 600)

**Font Loading**:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;600&display=swap"
  rel="stylesheet"
/>
```

**Colors (Primary Mode)**:

```css
:root {
  --color-bg: #0f1117;
  --color-surface: #1a1b26;
  --color-text: #e2e0dc;
  --color-text-secondary: #8a8880;
  --color-primary: #00d4ff;
  --color-primary-light: #0a2a33;
  --color-accent: #f5a623;
  --color-accent-light: #2a2010;
  --color-border: #2a2b36;
  --color-success: #4ade80;
  --color-error: #f87171;

  --font-heading: "Space Grotesk", system-ui, sans-serif;
  --font-body: "Source Serif 4", Georgia, serif;
  --font-mono: "JetBrains Mono", "Fira Code", monospace;
}
```

**Colors (Alternate Mode)**:

```css
[data-theme="light"] {
  --color-bg: #f8f9fc;
  --color-surface: #ffffff;
  --color-text: #1a1b26;
  --color-text-secondary: #6b6a68;
  --color-primary: #0098b8;
  --color-primary-light: #e0f4f8;
  --color-accent: #c47b1a;
  --color-accent-light: #fdf3e0;
  --color-border: #e2e4ea;
  --color-success: #22c55e;
  --color-error: #ef4444;
  --shadow-sm: 0 1px 2px rgba(26, 27, 38, 0.06);
  --shadow-md: 0 4px 6px rgba(26, 27, 38, 0.08);
  --shadow-lg: 0 10px 25px rgba(26, 27, 38, 0.12);
}
```

**Signature Elements**:

- Subtle star-field particle animation in background
- Glowing strokes on visualizations (`filter: drop-shadow(0 0 6px var(--color-primary))`)

---

### 3. Field Notes

**Vibe**: Warm, hand-crafted, organic, exploratory, journalistic
**Best for**: Biology, data science, qualitative reasoning, "thinking out loud" content
**Default theme**: light

**Typography**:

- Heading: Bitter (400, 700)
- Body: Source Sans 3 (400, 600)
- Code: Fira Code (400, 600)

**Font Loading**:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Bitter:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@400;600&family=Fira+Code:wght@400;600&display=swap"
  rel="stylesheet"
/>
```

**Colors (Primary Mode)**:

```css
:root {
  --color-bg: #f7f3eb;
  --color-surface: #fefcf7;
  --color-text: #2c3e50;
  --color-text-secondary: #7d7a72;
  --color-primary: #c1553b;
  --color-primary-light: #f5e0da;
  --color-accent: #4a7c59;
  --color-accent-light: #e2ede5;
  --color-border: #ddd5c7;
  --color-success: #4a7c59;
  --color-error: #c1553b;

  --font-heading: "Bitter", Georgia, serif;
  --font-body: "Source Sans 3", system-ui, sans-serif;
  --font-mono: "Fira Code", "JetBrains Mono", monospace;
}
```

**Colors (Alternate Mode)**:

```css
[data-theme="dark"] {
  --color-bg: #2a2520;
  --color-surface: #352f29;
  --color-text: #e8e2d8;
  --color-text-secondary: #9e978c;
  --color-primary: #d47a63;
  --color-primary-light: #3d2a23;
  --color-accent: #6da67a;
  --color-accent-light: #253028;
  --color-border: #4a4239;
  --color-success: #6da67a;
  --color-error: #d47a63;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.5);
}
```

**Signature Elements**:

- Rough.js hand-drawn borders on callout boxes
- Margin annotations styled as pencil-written sidenotes

---

### 4. Neon Terminal

**Vibe**: Hacker, cyberpunk, electric, immersive, dangerous
**Best for**: Programming, systems design, cybersecurity, DevOps, networking
**Default theme**: dark

**Typography**:

- Heading: Space Mono (400, 700)
- Body: IBM Plex Sans (400, 600)
- Code: Fira Code (400, 600)

**Font Loading**:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Sans:wght@400;600&family=Fira+Code:wght@400;600&display=swap"
  rel="stylesheet"
/>
```

**Colors (Primary Mode)**:

```css
:root {
  --color-bg: #0a0a0f;
  --color-surface: #141420;
  --color-text: #c0c0c0;
  --color-text-secondary: #707080;
  --color-primary: #39ff14;
  --color-primary-light: #0a2a08;
  --color-accent: #ff2d6f;
  --color-accent-light: #2a0a18;
  --color-border: #252535;
  --color-success: #39ff14;
  --color-error: #ff2d6f;

  --font-heading: "Space Mono", "Courier New", monospace;
  --font-body: "IBM Plex Sans", system-ui, sans-serif;
  --font-mono: "Fira Code", "JetBrains Mono", monospace;
}
```

**Colors (Alternate Mode)**:

```css
[data-theme="light"] {
  --color-bg: #f0f2f5;
  --color-surface: #ffffff;
  --color-text: #1a1a2e;
  --color-text-secondary: #5a5a70;
  --color-primary: #0d8a00;
  --color-primary-light: #d9f5d6;
  --color-accent: #c4205a;
  --color-accent-light: #fce0ea;
  --color-border: #d8dae0;
  --color-success: #0d8a00;
  --color-error: #c4205a;
  --shadow-sm: 0 1px 2px rgba(10, 10, 15, 0.06);
  --shadow-md: 0 4px 6px rgba(10, 10, 15, 0.08);
  --shadow-lg: 0 10px 25px rgba(10, 10, 15, 0.12);
}
```

**Signature Elements**:

- CRT scanline overlay effect (repeating-linear-gradient at 2px intervals)
- ASCII-art dividers between sections (`═══════════════`)

---

### 5. Distillery

**Vibe**: Academic, rigorous, beautiful, typographic, focused
**Best for**: Machine learning, statistics, research explainers, mathematical proofs
**Default theme**: light

**Typography**:

- Heading: Fraunces (400, 700)
- Body: Literata (400, 600, italic)
- Code: JetBrains Mono (400, 600)

**Font Loading**:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,700;1,400&family=Literata:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;600&display=swap"
  rel="stylesheet"
/>
```

**Colors (Primary Mode)**:

```css
:root {
  --color-bg: #fafafa;
  --color-surface: #ffffff;
  --color-text: #1a1a1a;
  --color-text-secondary: #6e6e6e;
  --color-primary: #007a7a;
  --color-primary-light: #e0f2f2;
  --color-accent: #5a4fcf;
  --color-accent-light: #eeedf8;
  --color-border: #e5e5e5;
  --color-success: #2e7d32;
  --color-error: #c62828;

  --font-heading: "Fraunces", Georgia, serif;
  --font-body: "Literata", "Georgia", serif;
  --font-mono: "JetBrains Mono", "Fira Code", monospace;
}
```

**Colors (Alternate Mode)**:

```css
[data-theme="dark"] {
  --color-bg: #1a1a1a;
  --color-surface: #262626;
  --color-text: #e8e8e8;
  --color-text-secondary: #9e9e9e;
  --color-primary: #26a6a6;
  --color-primary-light: #1a3333;
  --color-accent: #8a80e0;
  --color-accent-light: #2a2740;
  --color-border: #3a3a3a;
  --color-success: #66bb6a;
  --color-error: #ef5350;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.5);
}
```

**Signature Elements**:

- Tufte-style sidenotes in wide margins
- Full-width figures with generous whitespace and inline-expanding footnotes

---

### 6. Greenhouse

**Vibe**: Lush, organic, nurturing, verdant, approachable
**Best for**: Data science, ecology, growth/optimization concepts, gentle introductions
**Default theme**: light

**Typography**:

- Heading: Cormorant Garamond (400, 600)
- Body: DM Sans (400, 600)
- Code: Fira Code (400, 600)

**Font Loading**:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@400;600&family=Fira+Code:wght@400;600&display=swap"
  rel="stylesheet"
/>
```

**Colors (Primary Mode)**:

```css
:root {
  --color-bg: #e8ede4;
  --color-surface: #f5f7f2;
  --color-text: #1a2f1a;
  --color-text-secondary: #5a6e5a;
  --color-primary: #d4a055;
  --color-primary-light: #f5ead5;
  --color-accent: #c97b84;
  --color-accent-light: #f5e4e7;
  --color-border: #c8d4c0;
  --color-success: #3d5a3d;
  --color-error: #b54a4a;

  --font-heading: "Cormorant Garamond", "Garamond", serif;
  --font-body: "DM Sans", system-ui, sans-serif;
  --font-mono: "Fira Code", "JetBrains Mono", monospace;
}
```

**Colors (Alternate Mode)**:

```css
[data-theme="dark"] {
  --color-bg: #1a2518;
  --color-surface: #253022;
  --color-text: #e2e8de;
  --color-text-secondary: #8e9a88;
  --color-primary: #e0b46a;
  --color-primary-light: #2e2510;
  --color-accent: #d99aa2;
  --color-accent-light: #352025;
  --color-border: #3a4a35;
  --color-success: #6da67a;
  --color-error: #d47a6a;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.5);
}
```

**Signature Elements**:

- SVG botanical line-art at section breaks
- Vine-shaped progress indicator with organic growth animation

---

### 7. Blueprint

**Vibe**: Precise, engineered, confident, structured, technical
**Best for**: Engineering, system architecture, infrastructure, databases
**Default theme**: dark

**Typography**:

- Heading: Archivo (400, 600, 700)
- Body: Atkinson Hyperlegible (400, 700)
- Code: Source Code Pro (400, 600)

**Font Loading**:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700&family=Atkinson+Hyperlegible+Next:ital,wght@0,400;0,700;1,400&family=Source+Code+Pro:wght@400;600&display=swap"
  rel="stylesheet"
/>
```

**Colors (Primary Mode)**:

```css
:root {
  --color-bg: #1e2a3a;
  --color-surface: #263545;
  --color-text: #f0f4f8;
  --color-text-secondary: #9ab0c8;
  --color-primary: #ff6b35;
  --color-primary-light: #3a2a1e;
  --color-accent: #ffd166;
  --color-accent-light: #2a2810;
  --color-border: #34495e;
  --color-success: #2ecc71;
  --color-error: #e74c3c;

  --font-heading: "Archivo", system-ui, sans-serif;
  --font-body: "Atkinson Hyperlegible Next", system-ui, sans-serif;
  --font-mono: "Source Code Pro", "Fira Code", monospace;
}
```

**Colors (Alternate Mode)**:

```css
[data-theme="light"] {
  --color-bg: #f0f4f8;
  --color-surface: #ffffff;
  --color-text: #1e2a3a;
  --color-text-secondary: #546e88;
  --color-primary: #d45a2a;
  --color-primary-light: #fde8df;
  --color-accent: #c49b20;
  --color-accent-light: #fdf5dc;
  --color-border: #d0dae4;
  --color-success: #27ae60;
  --color-error: #c0392b;
  --shadow-sm: 0 1px 2px rgba(30, 42, 58, 0.06);
  --shadow-md: 0 4px 6px rgba(30, 42, 58, 0.08);
  --shadow-lg: 0 10px 25px rgba(30, 42, 58, 0.12);
}
```

**Signature Elements**:

- Background grid pattern (subtle repeating blueprint lines)
- Dashed-border callout boxes with corner registration markers

---

### 8. Corporate Brand

**Vibe**: Dark, confident, brand-aligned, modern, energetic
**Best for**: Corporate educational content, onboarding materials, tech talks
**Default theme**: dark

**Typography**:

- Heading: Satoshi (400, 700)
- Body: General Sans (400, 600)
- Code: JetBrains Mono (400, 600)

**Font Loading**:

```html
<link
  href="https://api.fontshare.com/v2/css?f[]=satoshi@400,700&display=swap"
  rel="stylesheet"
/>
<link
  href="https://api.fontshare.com/v2/css?f[]=general-sans@400,600&display=swap"
  rel="stylesheet"
/>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap"
  rel="stylesheet"
/>
```

**Colors (Primary Mode)**:

```css
:root {
  --color-bg: #191414;
  --color-surface: #282828;
  --color-text: #ffffff;
  --color-text-secondary: #b3b3b3;
  --color-primary: #1db954;
  --color-primary-light: #1a3a28;
  --color-accent: #5925ff;
  --color-accent-light: #2a1a4a;
  --color-border: #3a3a3a;
  --color-success: #19e68c;
  --color-error: #e07060;

  --font-heading: "Satoshi", system-ui, sans-serif;
  --font-body: "General Sans", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", "Fira Code", monospace;
}
```

**Colors (Alternate Mode)**:

```css
[data-theme="light"] {
  --color-bg: #f5f5f5;
  --color-surface: #ffffff;
  --color-text: #191414;
  --color-text-secondary: #6a6a6a;
  --color-primary: #1db954;
  --color-primary-light: #e8f5e9;
  --color-accent: #5925ff;
  --color-accent-light: #ede7f6;
  --color-border: #e0e0e0;
  --color-success: #15b870;
  --color-error: #c45050;
  --shadow-sm: 0 1px 2px rgba(25, 20, 20, 0.06);
  --shadow-md: 0 4px 6px rgba(25, 20, 20, 0.08);
  --shadow-lg: 0 10px 25px rgba(25, 20, 20, 0.12);
}
```

**Signature Elements**:

- Green accent bars on progress indicators and active states
- Brand-faithful color hierarchy: green for actions, purple for illustrations

---

### 9. Whiteboard Session

**Vibe**: Clean, bold, collaborative, sharp, structured
**Best for**: Programming tutorials, system design, step-by-step processes
**Default theme**: light

**Typography**:

- Heading: Syne (400, 600, 700)
- Body: Inter (400, 600)
- Code: JetBrains Mono (400, 600)

**Font Loading**:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap"
  rel="stylesheet"
/>
```

**Colors (Primary Mode)**:

```css
:root {
  --color-bg: #ffffff;
  --color-surface: #f8f9fa;
  --color-text: #1a2332;
  --color-text-secondary: #5a6577;
  --color-primary: #2563eb;
  --color-primary-light: #dbeafe;
  --color-accent: #f97066;
  --color-accent-light: #fee2e2;
  --color-border: #d1d5db;
  --color-success: #16a34a;
  --color-error: #dc2626;

  --font-heading: "Syne", system-ui, sans-serif;
  --font-body: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", "Fira Code", monospace;
}
```

**Colors (Alternate Mode)**:

```css
[data-theme="dark"] {
  --color-bg: #1a2332;
  --color-surface: #243044;
  --color-text: #f0f2f5;
  --color-text-secondary: #94a3b8;
  --color-primary: #60a5fa;
  --color-primary-light: #1e3a5f;
  --color-accent: #fb923c;
  --color-accent-light: #3a2510;
  --color-border: #334155;
  --color-success: #4ade80;
  --color-error: #f87171;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.5);
}
```

**Signature Elements**:

- Heavy black-bordered cards with 3px offset box-shadows
- Color-coded chapter markers with bold section numbering

---

### 10. Liquid Glass

**Vibe**: Premium, modern, spatial, luminous, immersive
**Best for**: Modern tech topics (AI/ML, cloud computing, APIs, web technologies), product engineering
**Default theme**: dark

**Typography**:

- Heading: Clash Display (400, 600, 700)
- Body: General Sans (400, 600)
- Code: JetBrains Mono (400, 600)

**Font Loading**:

```html
<link
  href="https://api.fontshare.com/v2/css?f[]=clash-display@400,600,700&display=swap"
  rel="stylesheet"
/>
<link
  href="https://api.fontshare.com/v2/css?f[]=general-sans@400,600&display=swap"
  rel="stylesheet"
/>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap"
  rel="stylesheet"
/>
```

**Colors (Primary Mode)**:

```css
:root {
  --color-bg: #0c0c1d;
  --color-surface: rgba(255, 255, 255, 0.06);
  --color-text: #e4e4e7;
  --color-text-secondary: #8888a0;
  --color-primary: #8b5cf6;
  --color-primary-light: #1e1540;
  --color-accent: #06b6d4;
  --color-accent-light: #0a2030;
  --color-border: rgba(255, 255, 255, 0.1);
  --color-success: #34d399;
  --color-error: #ec4899;

  --font-heading: "Clash Display", system-ui, sans-serif;
  --font-body: "General Sans", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", "Fira Code", monospace;
}
```

**Colors (Alternate Mode)**:

```css
[data-theme="light"] {
  --color-bg: #f5f5fa;
  --color-surface: rgba(255, 255, 255, 0.8);
  --color-text: #1a1a2e;
  --color-text-secondary: #6b6b80;
  --color-primary: #7c3aed;
  --color-primary-light: #ede9fe;
  --color-accent: #0891b2;
  --color-accent-light: #e0f7fa;
  --color-border: rgba(0, 0, 0, 0.08);
  --color-success: #059669;
  --color-error: #db2777;
  --shadow-sm: 0 1px 2px rgba(12, 12, 29, 0.06);
  --shadow-md: 0 4px 6px rgba(12, 12, 29, 0.08);
  --shadow-lg: 0 10px 25px rgba(12, 12, 29, 0.12);
}
```

**Signature Elements**:

- Frosted glass content cards (`backdrop-filter: blur(20px)` with translucent borders)
- Gradient mesh backgrounds with ambient animated gradient orbs
