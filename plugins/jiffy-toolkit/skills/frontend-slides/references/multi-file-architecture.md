# Multi-File Architecture

## Output Directory Convention

All new presentations are generated to:
```
~/.claude/presentations/[presentation-name]/
```

Where `[presentation-name]` is a kebab-case slug derived from the presentation title (e.g., "Q4 Revenue Review" -> `q4-revenue-review`).

## File Structure

```
~/.claude/presentations/[presentation-name]/
├── index.html          # Shell: loader, nav UI, empty #slides-container, CDN links
├── style.css           # Global styles: preset variables, layouts, animations, fragments
├── script.js           # SLIDES manifest, fetch assembly, navigation engine
├── serve.py            # HTTP server with Range request support (for video seeking)
├── assets/             # Images, videos, and other media
│   ├── hero.webp
│   └── diagram.svg
└── slides/             # Individual slide fragments
    ├── 01-title.html
    ├── 02-agenda.html
    ├── 03-problem.html
    ├── 04-solution.html
    └── ...
```

## index.html Shell Template

The index.html file is a minimal shell that loads dependencies, shows a loading state, and provides navigation UI. The `#slides-container` starts empty — slides are fetched and injected by script.js.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Presentation Title]</title>
  <link rel="stylesheet" href="style.css">
  <!-- CDN Dependencies -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <!-- [Preset-specific Google Font link] -->
</head>
<body>
  <!-- Loading indicator -->
  <div id="loader" class="loader">
    <div class="progress-bar"><div class="progress-fill"></div></div>
    <p>Loading presentation...</p>
  </div>

  <!-- Slide container (populated by script.js) -->
  <div id="slides-container"></div>

  <!-- Navigation UI -->
  <nav class="slide-nav" aria-label="Slide navigation">
    <div class="nav-dots" id="nav-dots"></div>
  </nav>
  <div class="slide-counter" id="slide-counter"></div>

  <!-- CDN Scripts -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <!-- [Optional: Mermaid, GSAP, etc. based on slide content] -->
  <script src="script.js"></script>
</body>
</html>
```

## script.js Template

The script.js file contains the SLIDES manifest array and the fetch-based assembly logic. After all slides are fetched and injected into the DOM, it initializes the SlidePresentation navigation engine.

```javascript
const SLIDES = [
  // Generated after all slide files exist
  // e.g., 'slides/01-title.html', 'slides/02-problem.html'
];

const SLIDE_NAME_TO_INDEX = {};
SLIDES.forEach((path, i) => {
  const name = path.replace('slides/', '').replace('.html', '');
  SLIDE_NAME_TO_INDEX[name] = i;
});

// Assembly: fetch all slide fragments and inject into container
const container = document.getElementById('slides-container');
Promise.all(SLIDES.map(path => fetch(path).then(r => r.text())))
  .then(htmls => {
    htmls.forEach(html => container.insertAdjacentHTML('beforeend', html));
    // After injection: initialize SlidePresentation, run syntax highlighting, etc.
    initPresentation();
  });
```

The `initPresentation()` function initializes the SlidePresentation class (navigation engine adapted from the single-file architecture), sets up keyboard/touch/scroll navigation, creates nav dots, runs `hljs.highlightAll()`, initializes Mermaid diagrams, starts animated counters, and hides the loader.

## serve.py Template

A minimal HTTP server with Range request support for video seeking:

```python
#!/usr/bin/env python3
"""HTTP server with Range request support for video seeking."""
import http.server
import os

class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if 'Range' not in self.headers:
            return super().do_GET()
        # Parse Range header and serve partial content
        range_header = self.headers['Range']
        byte_range = range_header.replace('bytes=', '').split('-')
        start = int(byte_range[0])
        path = self.translate_path(self.path)
        file_size = os.path.getsize(path)
        end = int(byte_range[1]) if byte_range[1] else file_size - 1
        length = end - start + 1
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
        self.send_header('Content-Length', str(length))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        with open(path, 'rb') as f:
            f.seek(start)
            self.wfile.write(f.read(length))

if __name__ == '__main__':
    http.server.HTTPServer(('', 8000), RangeRequestHandler).serve_forever()
```

Usage:
```bash
cd ~/.claude/presentations/[presentation-name]
python3 serve.py
# Open http://localhost:8000
```

## Slide Fragment File Conventions

### Filename Format
```
[NN]-[kebab-case-name].html
```
Examples: `01-title.html`, `02-agenda.html`, `03-problem-statement.html`

### File Structure

Each slide fragment file contains a single `<section>` element with optional scoped styles:

```html
<style>
  /* Scoped styles for this slide only */
  #slide-problem-statement .custom-element {
    /* Always scope by #slide-[name] to avoid conflicts */
  }
</style>

<section class="slide [layout-class]" id="slide-[name]" data-hash="[name]">
  <!-- Slide content using global CSS classes from style.css -->
  <h2 class="slide-title">Problem Statement</h2>
  <div class="content">
    <p class="fragment">First point revealed on click</p>
    <p class="fragment">Second point revealed on click</p>
  </div>
</section>
```

### Rules

- **One section per file** — each file contains exactly one `<section class="slide ...">` element
- **Scoped styles** — inline `<style>` at the top, all selectors scoped by `#slide-[name]`
- **Global classes** — use layout and animation classes from style.css (see CSS Class Catalog in agent-team-prompts.md)
- **Fragments** — any slide with 2+ content elements uses `class="fragment"` for progressive disclosure
- **Auto-animate** — paired slides include `data-auto-animate` on the `<section>` and `data-auto-animate-id` on matched elements
- **Viewport fitting** — all content must fit in 100vh; use `clamp()` for font sizes and spacing

## Dependency Graph

The files must be generated in this order to respect dependencies:

```
1. style.css          (no dependencies — generated first)
    ↓
2. slides/*.html      (depend on style.css classes — generated in parallel)
    ↓
3. script.js          (depends on slide filenames for SLIDES manifest)
    ↓
4. index.html         (depends on knowing CDN dependencies from slide content)
    ↓
5. serve.py           (no dependencies — can be copied at any time)
```

- **style.css** is generated first because Slide Authors need to know available CSS classes
- **Slide fragments** can be generated in parallel (2-3 authors working simultaneously)
- **script.js** is generated after all slides exist (needs the SLIDES manifest array)
- **index.html** is generated last (needs to know which CDN scripts to include based on slide content)
- **serve.py** is a static file copied as-is

## Single-File Post-Processing (--single-file flag)

When the user requests a single-file output (for portability without an HTTP server):

1. Read all generated files:
   - style.css -> inline into `<style>` in `<head>`
   - All slides/*.html -> concatenate in order into the `<body>`
   - script.js -> inline into `<script>` in `<body>` (remove the SLIDES fetch logic,
     slides are already in the DOM)

2. Replace the fetch-based assembly in script.js with direct DOM initialization:
   - Remove the SLIDES array and Promise.all fetch logic
   - Initialize SlidePresentation directly since slides are already in the DOM

3. Write the combined file to:
   `~/.claude/presentations/[presentation-name]/[presentation-name].html`

4. Images remain as relative paths (assets/ folder still needed)
   - If the user needs a truly portable single file with no external dependencies,
     convert images to base64 data URIs

The multi-file structure is still generated first — single-file is a post-processing step.
