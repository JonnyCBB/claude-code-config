# Visual QA Multi-Agent Review Process

## 1. Overview

This document defines the multi-agent review process for visual output produced by
teach-me (Phase 7) and frontend-slides (Phase 5). It is read by the orchestrating
context after QA artifacts have been collected and before the final output is
delivered to the user.

The review is designed to catch layout defects, interaction failures, and
accessibility violations through independent, specialized agents that each
examine a distinct slice of the QA output. No single agent sees everything;
findings are synthesized and deduplicated in the main context.

---

## 2. Review Agent Personas

### Visual Layout Reviewer

- **model: "opus"**
- **Data source:** screenshots captured by the QA script (PNG files read via the Read tool)
- **Responsibility:** layout integrity, spacing consistency, overflow/clipping,
  text truncation, z-index stacking issues, responsive breakpoint correctness,
  color contrast at a glance, and any visible rendering artifacts.

### Interaction and Functionality Reviewer

- **model: "sonnet"**
- **Data source:** `qa_report.json` (console errors, click/scroll/input test results)
- **Responsibility:** console errors and warnings, JavaScript exceptions, broken
  interactive controls (buttons, toggles, sliders, nav), animation failures,
  scroll-triggered events that never fire, and dead links or missing assets.

### Accessibility and Polish Reviewer

- **model: "sonnet"**
- **Data source:** `a11y.json` (axe-core or similar audit) and `aria.yaml` (ARIA snapshot)
- **Responsibility:** WCAG 2.2 AA violations, ARIA role/attribute correctness,
  heading hierarchy (h1-h6 order), focus order, color contrast ratios, alt text
  presence, landmark regions, and semantic HTML usage.

---

## 3. Adaptive Spawning Rules

Spawning is adaptive to avoid wasting tokens on empty data.

| Agent                              | Spawn condition                                                                 |
|------------------------------------|---------------------------------------------------------------------------------|
| Visual Layout Reviewer             | **Always** -- screenshots are available via fallback capture even if QA script partially fails |
| Interaction and Functionality Reviewer | **Skip** if `qa_report.json` field `interactive_elements_tested` equals zero   |
| Accessibility and Polish Reviewer  | **Skip** if the accessibility audit file is unavailable AND the ARIA snapshot is empty |

When an agent is skipped, the synthesis step records the reason so the user
understands the scope of review.

---

## 4. Review Is Blind

Each review agent receives only QA output artifacts. Agents do **not** see:

- The generation plan or narrative outline that produced the HTML
- The prompt or user request
- Findings from other review agents

This prevents anchoring bias. Agents evaluate what was produced, not what was
intended. The main context is the only participant that holds the full picture.

---

## 5. Agent Prompt Templates

### Visual Layout Reviewer prompt

```
You are a Visual Layout Reviewer (model: "opus").

INPUT: screenshots at {screenshot_paths}
Read each screenshot with the Read tool.

Check for:
- Overflow or clipping of text/images beyond viewport
- Inconsistent spacing or alignment between sections
- Z-index stacking errors (elements hidden behind others)
- Text truncation or unreadable font sizes
- Responsive layout breaks

For each issue, report:
  file: <screenshot filename>
  region: <top-left quadrant | center | etc.>
  severity: Must Fix | Should Fix | Minor | Advisory
  description: <what is wrong and where>

Severity guide:
  Must Fix    — content is unreadable, invisible, or broken
  Should Fix  — visible defect that degrades quality
  Minor       — cosmetic imperfection most users would not notice
  Advisory    — suggestion for improvement, not a defect
```

### Interaction and Functionality Reviewer prompt

```
You are an Interaction and Functionality Reviewer (model: "sonnet").

INPUT: qa_report.json at {qa_report_path}

Check for:
- Console errors or unhandled exceptions
- Interactive controls that failed click/input tests
- Animations that did not trigger or completed with errors
- Scroll-triggered events that never fired
- Missing assets (404s, broken images/fonts)

For each issue, report:
  source: <JSON path in qa_report.json>
  severity: Must Fix | Should Fix | Minor | Advisory
  description: <what failed and its user impact>

Severity guide:
  Must Fix    — functionality is broken (JS exception, dead control)
  Should Fix  — degraded experience (animation skip, slow load)
  Minor       — non-blocking warning in console
  Advisory    — optimization opportunity
```

### Accessibility and Polish Reviewer prompt

```
You are an Accessibility and Polish Reviewer (model: "sonnet").

INPUT:
  a11y.json at {a11y_path}
  aria.yaml at {aria_path}

Check for:
- WCAG 2.2 AA violations (contrast, target size, reflow)
- Incorrect or missing ARIA roles and attributes
- Heading hierarchy gaps (e.g., h1 -> h3 with no h2)
- Missing alt text on informational images
- Focus order that does not match visual order
- Missing landmark regions (main, nav, banner)

For each issue, report:
  source: <a11y.json rule ID or aria.yaml path>
  severity: Must Fix | Should Fix | Minor | Advisory
  description: <what violates which criterion>

Severity guide:
  Must Fix    — WCAG AA failure (contrast < 4.5:1, missing alt, broken focus)
  Should Fix  — best practice violation (landmark missing, heading skip)
  Minor       — AAA-level suggestion
  Advisory    — polish opportunity
```

---

## 6. Synthesis Process

After all spawned agents return, the main context synthesizes findings.

1. **Collect** -- gather finding lists from each agent into a single table.
2. **Categorize** -- verify each finding carries a severity: Must Fix, Should Fix,
   Minor, or Advisory.
3. **Deduplicate** -- when two or more agents flag the same root cause (e.g., a
   missing CSS rule causes both a layout overflow and an a11y reflow failure),
   merge into a single finding and note all affected areas.
4. **Sanity thresholds** -- confirm baseline data quality:
   - `meta.screenshots_captured > 0`
   - `meta.pages_visited > 0`
   - If any threshold fails, flag the QA run itself as suspect and note it in
     the output.
5. **Produce the review summary** -- ordered by severity, deduplicated, with
   agent attribution removed (findings stand on their own).

---

## 7. Iteration Loop

The iteration loop runs mechanical fixes and re-reviews until quality gates pass
or the ceiling is reached.

```
iteration = 0
max_iterations = 3

while iteration < max_iterations:
    run QA script against current HTML
    spawn review agents on QA output
    synthesize findings

    if zero Must Fix items AND sanity thresholds met:
        auto-approve output
        break

    spawn fix agent (general-purpose, default model) with:
        - current HTML file
        - Must Fix + Should Fix findings only
    fix agent makes mechanical CSS/JS corrections only
        (no structural changes, no content rewrites)

    iteration += 1

if iteration == max_iterations AND Must Fix items remain:
    deliver best-so-far output
    append "Known Issues" section listing unresolved Must Fix items
```

### Fix agent constraints

- The fix agent receives the HTML source and the filtered finding list.
- It applies targeted CSS and JS patches -- no DOM restructuring.
- It does not see the original prompt or generation plan.
- After fixes, the QA script is re-run and review agents are re-spawned on
  the new output to confirm fixes landed and no regressions appeared.

---

## 8. Transparency

After the iteration loop completes, a brief summary is shown to the user:

> Review found N issues (X fixed, Y advisory).

If the output was auto-approved on the first pass, the message is:

> Review passed -- no issues found.

If the ceiling was reached with remaining Must Fix items:

> Review found N issues. X were fixed across M iterations. Y unresolved
> issues are listed in the Known Issues section at the end of the output.

The full finding table is not shown unless the user requests it. The goal is
to communicate confidence level without overwhelming the reader.
