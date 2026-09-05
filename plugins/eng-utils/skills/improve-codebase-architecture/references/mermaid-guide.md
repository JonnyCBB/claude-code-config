# Mermaid.js Flowchart Guide for Architecture Diagrams

Lightweight diagram syntax for HTML candidate and design presentations. Use Mermaid
flowcharts (not C4) — they are simpler, more reliably generated, and auto-layout handles
arrow routing.

## CDN Setup

Include in the HTML `<head>`:

```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({ startOnLoad: true, theme: "default" });
</script>
```

Place diagrams in `<pre class="mermaid">` blocks within the HTML body.

## Syntax Rules

- Use `graph LR` (left-to-right) or `graph TD` (top-down) — pick whichever suits the
  topology better
- **Always double-quote label text** to avoid parser crashes on special characters:
  `A["agent.py (1,552 lines)"]` — never `A[agent.py (1,552 lines)]`
- Use `subgraph` with a quoted title for grouping: `subgraph "agents/"`
- Use `classDef` for color-coding — define classes at the end of the diagram and apply
  with `:::className` suffix on nodes
- Arrow labels: `A -->|"label"| B` — quote the label text too
- Keep diagrams to 5-12 nodes — these are sketches, not comprehensive C4 diagrams

## Node Shapes

- `A["text"]` — rectangle (default, for modules/services)
- `A[("text")]` — cylinder (database/persistence)
- `A(["text"])` — stadium (entry point)

## Color Palette

Use `classDef` to define these semantic classes:

| Class       | Meaning                                          | Fill      | Stroke    |
| ----------- | ------------------------------------------------ | --------- | --------- |
| `problem`   | God modules / primary friction sources           | `#fee2e2` | `#dc2626` |
| `affected`  | Modules affected by the friction                 | `#ffedd5` | `#ea580c` |
| `unchanged` | External / unchanged dependencies                | `#f3f4f6` | `#6b7280` |
| `improved`  | New clean boundaries / interfaces (Phase 3 only) | `#dcfce7` | `#16a34a` |

Example:

```
classDef problem fill:#fee2e2,stroke:#dc2626
classDef affected fill:#ffedd5,stroke:#ea580c
classDef unchanged fill:#f3f4f6,stroke:#6b7280
classDef improved fill:#dcfce7,stroke:#16a34a
```

## Side-by-Side Layout (Phase 3)

For "Current → Proposed" comparisons, use a CSS flexbox wrapper around two separate
Mermaid diagrams:

```html
<div style="display: flex; gap: 2rem;">
  <div style="flex: 1;">
    <h4>Current</h4>
    <pre class="mermaid">
graph TD
      subgraph "agents/"
        A["agent.py (1,552 lines)"]:::problem
        B["runtime_nodes.py"]:::affected
      end
      A -->|"30 accesses"| C[("ctx.state")]:::affected
      classDef problem fill:#fee2e2,stroke:#dc2626
      classDef affected fill:#ffedd5,stroke:#ea580c
    </pre>
  </div>
  <div style="flex: 1;">
    <h4>Proposed</h4>
    <pre class="mermaid">
graph TD
      subgraph "domain/"
        D["GateBoundary"]:::improved
        E["SessionState"]:::improved
      end
      F["ADK Adapter"]:::unchanged --> D
      classDef improved fill:#dcfce7,stroke:#16a34a
      classDef unchanged fill:#f3f4f6,stroke:#6b7280
    </pre>
  </div>
</div>
```
