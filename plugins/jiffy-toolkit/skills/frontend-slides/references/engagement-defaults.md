## Progressive Disclosure: Less Is More

**Core principle: Fragment sparingly and group logically. Every click should feel purposeful, not tedious.**

Excessive fragmentation disrupts presentation flow. The audience should never feel like they're waiting for content to appear — fragments exist to build narrative tension or reveal a punchline, not to animate every element onto the screen.

### Click Budget

**MAX 3-4 fragment steps per slide.** This is a hard ceiling, not a target. Many slides need 0 fragment steps. If a slide would require more than 4 clicks to fully reveal, either reduce the number of fragment groups or split into multiple slides.

### Logical Grouping Principle

**Related elements MUST appear together as a single fragment group, not individually.** Use `data-fragment-index` to assign the same index to elements that belong together.

Examples of logical groups:
- **Diagrams/DAGs**: All nodes AND their connecting edges within the same layer appear together
- **Title + subtitle**: These are one unit — show together or not at all
- **A bullet point + its sub-bullets**: Reveal as one group
- **A chart + its legend/annotation**: One group
- **An image + its caption**: One group

```html
<!-- GOOD: Nodes and edges in the same DAG layer share a fragment index -->
<g class="dag-node fragment" data-fragment-index="1">...</g>
<g class="dag-node fragment" data-fragment-index="1">...</g>
<line class="dag-edge fragment" data-fragment-index="1" ... />

<!-- BAD: Every element is its own click -->
<g class="dag-node fragment">...</g>
<line class="dag-edge fragment">...</line>
<g class="dag-node fragment">...</g>
```

### Fragment Strategy by Slide Type

| Slide Type | Fragment Strategy |
|------------|------------------|
| Title slide | **No fragments by default.** Title, subtitle, and tags appear immediately. Only fragment if the agent judges it adds narrative value (e.g., a dramatic reveal). |
| Section divider | No fragments (single visual element) |
| Content (bullets) | Group into 2-3 logical reveal steps, NOT one-per-bullet. E.g., 6 bullets = 2 groups of 3, or 3 groups of 2. |
| Two-column | Left column appears first, then right column (2 steps max) |
| Feature grid | Reveal row by row (2-3 steps), NOT card by card |
| Code slide | Code is always visible; line highlights are fragments (2-3 highlight groups) |
| Fact/stat | Number appears first (with counter animation), then label (2 steps) |
| Image-left/right | Show everything at once, or image first then text (1-2 steps max) |
| Quote | Show everything at once, or quote then attribution (1-2 steps max) |
| Diagram/DAG | Reveal by logical layer — all nodes AND edges in a layer appear together |
| Image-only | No fragments |

### Fragment Animation Defaults
- Standard fragments: `fade-up` (opacity + translateY), 0.4s duration
- Lists: stagger 0.1s between items within a group
- Emphasis: `fade-in-then-semi-out` for "highlight current" effect
- Code: highlight current line group, dim others to 30%

### When NOT to Fragment
- Title slides (default — agent may override with justification)
- Section divider slides
- Image-only slides
- Slides with 1-2 content elements (nothing to progressively disclose)
- Slides the user explicitly requests to show all at once
- When fragmentation would require more than 4 clicks

## Auto-Animate Between Related Slides

**Rule: Use auto-animate for 2-4 slide pairs per presentation maximum.**

Best candidates:
1. Code evolution — show code changing across 2-3 slides
2. Progressive building — architecture diagram that adds components
3. Before/After — layout that morphs to show transformation
4. Concept expansion — simple version expands to detailed version

Implementation:
- Mark paired slides with `data-auto-animate` attribute
- Match elements with `data-auto-animate-id="[unique-id]"`
- Duration: 0.8s with ease-out easing
- Uses FLIP animation (see navigation-and-interaction.md)

## Content Density: More Slides, Less Content

**Rule: Generate more slides with less content rather than fewer dense slides.**

- One core message per slide
- Max 30 words of text per slide
- If a bullet list exceeds 4 items, split across 2 slides
- Use `fade-in-then-semi-out` so previous items dim as new ones appear

### Enforcement Limits
- Content items > 6 on a single slide -> Split into multiple slides
- Bullet points > 4 -> Consider splitting or different layout (cards, timeline)
- Paragraphs > 1 -> Split into separate slides
- Code > 10 lines -> Use code highlighting with fragments

### Additional Engagement Patterns
1. Section dividers between topic changes (visual breathing room)
2. Fact slides for key metrics (`layout-fact` with animated counter)
3. Varied layouts (don't repeat same layout on consecutive slides)
4. Transitions with purpose (auto-animate for related content; standard for topic switches)
