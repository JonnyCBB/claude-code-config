---
name: teach-me
description: >
  Generate interactive scrollytelling HTML pages that progressively explain any concept.
  Uses prerequisite reasoning to build understanding from foundational concepts, GSAP
  animations as the primary visualization engine, and Manim for mathematical content.
  Use when the user says "/teach-me [concept]", "teach me about [concept]", "explain
  [concept] visually", "create an interactive explanation of [concept]", or asks for
  a visual/animated walkthrough of any topic. Outputs self-contained HTML to
  ~/.claude/teach-me/[slug]/index.html and opens it in the browser.
---

# Teach Me

Build an interactive scrollytelling page that teaches a concept in prerequisite order. `<slug>` is the concept in kebab-case (`adam-optimizer`); everything is written under `~/.claude/teach-me/<slug>/`. Read each reference only when you reach the phase that needs it.

## Phase 1 — Understand the request

Extract the target concept, the audience's background, scope hints (internal to a codebase? mathematical? algorithmic?) and any named theme. If the audience is unclear, ask what background they have.

## Phase 2 — Research

Show the user, then proceed without waiting for approval (they can interrupt):

- the research questions (mechanism, misconceptions, analogies for this audience, missing prerequisites);
- what you assume they already know and do not know;
- which agent answers each question, and which questions wait on another's answer.

| Question type | Agent | When |
| --- | --- | --- |
| General explanations, analogies, misconceptions | `web-search-researcher` | Skip if the concept is purely internal |
| Implementation details | `codebase-explorer` | Only when the concept maps to code in the working directory |
| Equations, proofs, formal notation | `web-search-researcher` with a math-focused prompt | When the concept is mathematical |
| ML, data, search, etc. | The domain expert agent for that domain | When the concept maps to a known domain |

Spawn independent questions in parallel (one message, several Agent calls); pass earlier findings into dependent ones. When the dependency is weak, parallelize. With 5 or more agents, spawn in sub-batches of 3-5.

Subagents can go idle without delivering (a known Claude Code issue). On an `idle_notification` with no content: prompt it via SendMessage using its agent ID (not name), then respawn once, then gather the data yourself or state the gap.

Do not start Phase 3 until every agent has returned.

## Phase 3 — Prerequisite chain

Follow `references/prerequisite-reasoning.md`: build the prerequisite graph, cut it at what the audience already knows, order the rest foundations-first, and write scaffolded content for each concept. Output an ordered list from most foundational to the target.

## Phase 4 — Theme

Presets are in `references/style-presets.md`. If the user named one, confirm it (`Using the **[Theme Name]** theme.`) and move on.

Otherwise write a theme explorer to `~/.claude/teach-me/.theme-explorer/index.html`: one card per preset, each in its own `<section>` scoped to that preset's variables, showing the name, a heading, a paragraph and a code block. `open` it, then ask with AskUserQuestion: "Which theme would you like? (type a name or number, or 'default' for Warm Scholar)". If the answer is unclear, use Warm Scholar.

## Phase 5 — Design and generate

Plan the visuals with four role personas from `references/agent-team-prompts.md` (Animation Specialist, Pedagogy Advocate, UX/Interaction Designer, Visual Critic), then generate. Libraries: GSAP, D3, p5, Three.js, Rough.js, Manim; the roles may go beyond the widget templates. Every GSAP animation gets the playback controls in `templates/playback-controls.html`, with timeline labels wired to the shared `PlaybackController`, so the learner sets the pace.

Inputs for planning and generation: the prerequisite chain, the audience, the role persona, `references/animation-libraries.md`, `references/css-base-system.md`, the selected preset, and every file in `templates/`.

### Plan and generate

1. Spawn Animation Specialist, Pedagogy Advocate and UX/Interaction Designer in parallel (`subagent_type: "general-purpose"`, `model: "sonnet"`), each with its full persona and the inputs above. Wait for all three.
2. Act as Creative Director and Visual Critic: push back on safe or bland choices, resolve conflicts between engagement and teaching, and lock one plan in `~/.claude/teach-me/<slug>/plan.md`. Per concept: visualization and what it shows, library, interactive elements, scroll steps, transition to the next concept, pedagogy and accessibility notes. Overall: aesthetic direction, visual rhythm, CDN dependencies, which concepts need Manim.
3. Generate every chapter yourself from `templates/chapter-module.html`, following the plan.

### Assemble

1. Start from `templates/scrollytelling-base.html`.
2. Fill `<!-- TOC_ITEMS -->`, `<!-- CHAPTERS -->` and `<!-- ANIMATIONS -->`, and add the playback controls.
3. Fill the PRESET slots: the preset's `:root` variables, its alternate theme block, its font `<link>` tags, and `data-theme` on `<html>`.
4. Set the page title and metadata.
5. Review the whole page in order and fix what fails: understanding builds from foundation to target, the aesthetic is consistent, every GSAP animation has controls, every CDN dependency is present, scroll pacing fits.
6. Write `~/.claude/teach-me/<slug>/index.html`.

## Phase 6 — Manim (only if the plan needs it)

Check with `bash ${CLAUDE_PLUGIN_ROOT}/skills/teach-me/scripts/install_deps.sh --check-only` (prints `installed` or `not-installed`). If missing, tell the user setup takes ~2-5 min, then run it without `--check-only`.

Write each scene following `references/manim-patterns.md` and render it into the page's media directory:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/teach-me/scripts/render_manim.py <scene.py> <SceneClass> --format gif --output-dir ~/.claude/teach-me/<slug>/media
```

## Phase 7 — Visual QA

Read [`${CLAUDE_PLUGIN_ROOT}/skills/shared/references/visual-qa-review.md`](${CLAUDE_PLUGIN_ROOT}/skills/shared/references/visual-qa-review.md) and follow it:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/shared/scripts/visual_qa.py ~/.claude/teach-me/<slug>/index.html --skill teach-me --output-dir /tmp/teach-me-qa
```

Spawn the review agents (skip the Interaction Reviewer when there are no interactive elements), sort findings into Must Fix / Should Fix / Minor / Advisory, and fix Must Fix items with a fix agent, re-running QA, for at most 3 iterations. Give the user a brief summary. Deliver only after the review approves or the iteration ceiling is reached.

## Phase 8 — Deliver

1. If Manim media exists, keep `media/` beside `index.html`. Optionally inline small files:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/teach-me/scripts/embed_media.py ~/.claude/teach-me/<slug>/index.html --max-size 500000
   ```

2. `open ~/.claude/teach-me/<slug>/index.html`
3. Report the path.
