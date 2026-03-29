# jiffy-toolkit

Creative and standards tools for Claude Code.

## Skills

| Skill                        | Command                         | Description                                                                                                                              |
| ---------------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| teach-me                     | `/teach-me [concept]`           | Generate interactive scrollytelling HTML pages that progressively explain any concept using GSAP animations and optional Manim for math. |
| frontend-slides              | `/frontend-slides`              | Create animation-rich HTML presentations from scratch or by converting PowerPoint files.                                                 |
| context-and-skills-standards | `/context-and-skills-standards` | Evidence-based standards for writing CLAUDE.md, AGENTS.md, and skill files                                                               |
| editorial-standards          | `/editorial-standards`          | Editorial standards and technical writing best practices for document review                                                             |
| diagram-standards            | `/diagram-standards`            | Diagram standards including type selection, color palettes, WCAG 2.2 accessibility                                                       |

## Notable skills

### /teach-me

Generate interactive scrollytelling HTML pages that progressively explain any concept. Uses prerequisite reasoning to build understanding from foundational concepts, GSAP animations as the primary visualization engine, and Manim for mathematical content.

**How it works:** An 8-phase workflow that researches your concept, builds a prerequisite chain (DAG of concepts sorted from foundational to target), lets you pick a visual theme, then generates a self-contained HTML page with scroll-driven animations and interactive playback controls.

**Key features:**

- Prerequisite reasoning — automatically identifies what you need to know first and teaches concepts in dependency order
- GSAP animations with playback controls (play/pause, speed, step-through, scrub)
- 10 visual theme presets (Warm Scholar, Observatory, etc.)
- Optional Manim integration for mathematical content
- Agent team debate mode for visualization choices (when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)
- Visual QA with Playwright screenshots to catch rendering issues

**Output:** `~/.claude/teach-me/[slug]/index.html`

### /frontend-slides

Create zero-dependency, animation-rich HTML presentations that run entirely in the browser. Supports creating from scratch, converting PowerPoint files, or enhancing existing HTML presentations.

**How it works:** A multi-phase workflow that discovers your content needs, lets you explore 20 visual style presets through live previews ("show, don't tell"), then generates a production-quality slide deck with strict viewport fitting — every slide fits exactly on screen with no scrolling.

**Key features:**

- 20 style presets (Bold Signal, Dark Botanical, Terminal Green, Liquid Glass, etc.)
- Three modes: new presentation, PPT/PPTX conversion, existing presentation enhancement
- Multi-file output with `python3 serve.py` (or `--single-file` for portability)
- Strict viewport fitting — content density limits enforced per slide type
- Optional inline editing — edit text directly in the browser with auto-save
- Image pipeline — evaluates user-provided assets and co-designs slides around them
- Agent team debate mode for design decisions (when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)

**Output:** `~/.claude/presentations/[name]/` (multi-file) or single HTML file

## Agents (5)

| Agent                       | Purpose                                                  |
| --------------------------- | -------------------------------------------------------- |
| web-search-researcher       | External documentation and web research                  |
| codebase-explorer           | Find files and understand code across repos              |
| context-and-skills-reviewer | Review CLAUDE.md/AGENTS.md/skill files against standards |
| document-editor-reviewer    | Editorial review of technical documents                  |
| visual-aid-recommender      | Recommend diagrams and visualizations for documentation  |

## Prerequisites

### Optional

- Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `~/.claude/settings.json` under `env` for enhanced teach-me and frontend-slides agent team features (multi-agent debate for visualization choices)
- Python 3, Playwright (for teach-me visual QA)
- Manim (for teach-me mathematical content)
- python-pptx, decktape (for frontend-slides export)
