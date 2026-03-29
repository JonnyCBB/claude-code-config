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

Generate interactive scrollytelling HTML pages that progressively explain any concept using prerequisite reasoning, GSAP animations, and optional Manim renders.

## Guiding Principles

1. **The user is in control of their learning.** Dynamic visuals should be interactive
   by default. All GSAP animations include playback controls (play/pause, speed, step-through,
   scrub). The user sets the pace, not the animation.
2. **Research is transparent.** Before researching a concept, display what questions are being
   investigated and what assumptions are being made about the user's knowledge. This is
   informational, not blocking — the user can interrupt if the direction is wrong.

## Workflow

Follow these 8 phases in order. Read referenced files only when you reach the phase that needs them.

### Phase 1 — Understand Query

Parse the user's request to extract:

- **Target concept** (e.g., "ADAM optimizer", "binary search", "gradient descent")
- **Audience context** (e.g., "for a product manager", "for someone who knows basic programming")
- **Scope hints** (e.g., Mathematical? Algorithmic? Domain-specific?)
- **Theme preference** (e.g., "in the observatory style", "use the corporate brand theme") — optional

If audience is ambiguous, ask the user to clarify what background they have.

### Phase 2 — Research Concept

Before researching, display your research plan to the user:

#### Step 1: Identify research questions

List the specific questions that need answering to explain this concept accurately.
Display these to the user:

```
## Research Questions

To explain "[target concept]" to [audience], I need to answer:

1. [Question about the core mechanism/definition]
2. [Question about common misconceptions]
3. [Question about good analogies for this audience]
4. [Question about prerequisites the audience may not have]
...
```

#### Step 2: State assumptions about user knowledge

```
## Assumptions About Your Background

Based on "[audience context]", I'm assuming you:
- Know: [concept 1], [concept 2], ...
- Don't know: [concept 3], [concept 4], ...

If any of these are wrong, let me know and I'll adjust.
```

**Important**: These steps are informational — do NOT wait for user approval.
Display them and immediately proceed to spawning agents.
The user can interrupt if something looks wrong.

#### Step 3: Plan research agents (dynamic planning)

For each question from Step 1, determine:

- What type of information is needed (general knowledge, codebase, mathematical)
- Which agent type is best suited (see decision tree below)
- Dependencies on other questions' answers

**Agent selection decision tree:**

| Question Type                                     | Default Agent                                    | Override Conditions                                            |
| ------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------- |
| General explanations, analogies, misconceptions   | `web-search-researcher`                          | Default for most concepts                                      |
| Codebase implementation details                   | `codebase-explorer`                              | Only when concept maps to actual code in the working directory |
| Mathematical foundations, proofs, formal notation | `web-search-researcher` with math-focused prompt | When concept involves equations, proofs, or formal definitions |
| Domain-specific (ML, data, search, etc.)          | Domain expert agent from detected domain         | When concept maps to a known domain                            |

Display the research plan:

```
## Research Plan

To research "[concept]", I will:

1. [Question] -> [agent-type] (reason)
2. [Question] -> [agent-type] (reason)
3. [Question] -> [agent-type] (reason)
...

**Dependency Analysis:**

| Question | Depends On | Rationale |
|----------|------------|-----------|
| Q1 | None | Independent starting point |
| Q2 | Q1 | Q1's terminology will focus Q2's search |
| Q3 | None | Independent |

**Execution Batches:**

Batch 1 (parallel): Q1, Q3
   -> (wait, extract key context)
Batch 2 (parallel): Q2 (informed by Q1 findings)

**Agent Type Verification:**

Based on the questions above, I will spawn:
- [agent-type-1] (questions 1, 3)
- [agent-type-2] (question 2)

Total agents to spawn: [N]

This list is my CONTRACT.
```

**Important**: This plan is informational — do NOT wait for user approval.
Display and proceed immediately. The user can interrupt if the direction is wrong.

#### Step 4: Spawn research agents

Execute batches per the plan:

1. Spawn all Batch 1 agents in parallel (use a single message with multiple Agent tool calls)
2. Wait for Batch 1 to complete
3. Extract key context from Batch 1 results (terminology, scope, key findings)
4. Spawn Batch 2 agents, passing relevant Batch 1 context in their prompts
5. Continue until all batches are complete

**Default to parallelism when uncertain**: If the dependency between questions is weak
or speculative, put them in the same batch. Over-parallelizing is acceptable; missing
dependencies will surface during Phase 3 (Prerequisite Chain).

Collect enough material to write accurate explanations and design meaningful animations.
Do not proceed to Phase 3 until all agents have returned results.

### Phase 3 — Build Prerequisite Chain

Read `references/prerequisite-reasoning.md` for the full prompt template and algorithm.

Steps:

1. Generate a prerequisite DAG using the prompt template
2. Assess audience knowledge state based on their stated role/background
3. Cut the DAG at the known/unknown boundary
4. Topological sort (Kahn's algorithm) the unknown subgraph
5. For each concept in order, generate scaffolded content (analogy, explanation, bridge, animation spec)

Output a linearized list of concepts from most foundational to target concept.

### Phase 4 — Theme Selection

Select the visual theme for the generated page. Read `references/style-presets.md` for the 10 available presets.

#### Quick path

If the user specified a theme in their request (detected in Phase 1), confirm it:

```
Using the **[Theme Name]** theme. Proceeding to design.
```

Skip to Phase 5.

#### Default path

If no theme was specified:

1. Generate a single-file theme explorer at `~/.claude/teach-me/.theme-explorer/index.html`:
   - One card per preset, each rendered in that preset's CSS
   - Each card shows: preset name, a heading, a short paragraph, and a code block
   - Cards use scoped CSS (each in its own `<section>` with preset variables)

2. Open in browser:

   ```bash
   open ~/.claude/teach-me/.theme-explorer/index.html
   ```

3. Ask the user:

   ```
   AskUserQuestion: "Which theme would you like? (type a name or number, or 'default' for Warm Scholar)"
   ```

4. Map response to a preset from `style-presets.md`. Default to Warm Scholar if unclear.

### Phase 5 — Design & Generate Visual Experience

This phase uses a creative agent team to debate visualization choices and generate the HTML.
The team has deep knowledge of all available animation libraries (GSAP, D3, p5, Three.js,
Rough.js, Manim) and creative freedom to go beyond the existing widget templates.

#### Step 1: Determine coordination mechanism

Check if agent teams are available:

```bash
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
```

If set to `1` or `true`, use the **Agent Team Path** (Step 2A).
Otherwise, use the **Sub-Agent Fallback Path** (Step 2B).

#### Step 2A: Agent Team Path (PREFERRED when enabled)

> Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
>
> **This path uses agent teams for DEBATE and PLANNING only, then switches to
> parallel sub-agents for HTML generation. Agent teams excel at inter-agent
> creative debate; sub-agents excel at independent parallel generation.**

**Read these references first:**

- `references/agent-team-prompts.md` — role personas, team lifecycle
- `references/animation-libraries.md` — capabilities, CDN links, library patterns
- `references/scrollytelling-patterns.md` — structural patterns
- `references/css-base-system.md` — structural CSS
- `references/style-presets.md` — the selected preset
- All files in `templates/` — HTML templates

**Step 2A.1: Create the team using TeamCreate**

Use the `TeamCreate` tool to create the team. You (the main session) are the
Creative Director and team lead.

```
TeamCreate(team_name="teach-me-[concept-slug]", description="Planning visual explanation for [concept]")
```

**Step 2A.2: Spawn teammates for debate**

Spawn each teammate using the `Agent` tool with `team_name` and `name` parameters.
These are real agent team teammates for the debate phase only:

```
Agent(
  team_name="teach-me-[concept-slug]",
  name="animation-specialist",
  subagent_type="general-purpose",
  prompt="[Full Animation Specialist persona from references/agent-team-prompts.md].
  You have the prerequisite chain: [chain]. Audience: [audience].
  Reference files: [list]. Templates: [list].
  Your role is to DEBATE and PROPOSE — you will NOT generate HTML.
  Communicate with teammates via SendMessage to debate choices."
)

Agent(
  team_name="teach-me-[concept-slug]",
  name="pedagogy-advocate",
  subagent_type="general-purpose",
  prompt="[Full Pedagogy Advocate persona from references/agent-team-prompts.md].
  [Same context as above].
  Your role is to DEBATE and EVALUATE — you will NOT generate HTML.
  Communicate with teammates via SendMessage."
)

Agent(
  team_name="teach-me-[concept-slug]",
  name="ux-designer",
  subagent_type="general-purpose",
  prompt="[Full UX/Interaction Designer persona from references/agent-team-prompts.md].
  [Same context as above].
  Your role is to DEBATE and PROPOSE — you will NOT generate HTML.
  Communicate with teammates via SendMessage."
)

Agent(
  team_name="teach-me-[concept-slug]",
  name="visual-critic",
  subagent_type="general-purpose",
  prompt="[Full Visual Critic persona from references/agent-team-prompts.md].
  [Same context as above].
  Your role is to CHALLENGE choices — you will NOT generate HTML.
  Communicate with teammates via SendMessage."
)
```

**Provide all teammates with:**

- The prerequisite chain from Phase 3 (concepts, analogies, explanations, animation specs)
- The audience context from Phase 1
- Their full role persona prompt from `references/agent-team-prompts.md`
- Instruction: "Your role is debate and planning ONLY. You will NOT generate HTML."
- All reference files and templates listed above
- Instruction to use `SendMessage` to communicate with other teammates by name

**Step 2A.3: Debate phase (divergent)**

Teammates propose and debate via SendMessage. Creative Director moderates.
Max 3 debate rounds per concept.

- Animation Specialist proposes visualization for each concept
- Pedagogy Advocate evaluates each for teaching effectiveness
- UX/Interaction Designer proposes scroll pacing and interactive elements
- Visual Critic challenges safe/boring choices

**Step 2A.4: Plan lock (convergent)**

Creative Director synthesizes debate into a **visual experience plan**:

For each concept in the prerequisite chain:

- Visualization type and animation description
- Library choice (GSAP, D3, p5, Three.js, Rough.js, or Manim)
- Interactive elements (sliders, toggleable layers, hover states)
- Scroll pacing (number of scroll steps)
- Transition strategy to next concept
- Teaching effectiveness notes from Pedagogy Advocate
- Accessibility considerations from UX Designer

Also includes:

- Overall aesthetic direction
- Visual rhythm across chapters
- CDN dependencies needed

Write the plan to: `~/.claude/teach-me/[slug]/plan.md`

Share plan with all teammates for final confirmation via SendMessage.
All teammates confirm or raise final objections (max 1 round).

**Step 2A.5: Team shutdown**

Shut down teammates via `SendMessage(type="shutdown_request")` and clean up
team resources.

If ANY concept needs Manim, flag it for Phase 6 (Install Dependencies).

**Step 2A.6: Parallel sub-agent generation**

> **IMPORTANT: Use standalone background sub-agents here, NOT agent team members.**
> The debate team was shut down in Step 2A.5. Generation sub-agents must be spawned
> as independent background agents using `Agent(run_in_background: true)` — do NOT
> pass `team_name` or `name` parameters. Agent teams are for debate (Steps 2A.1-2A.5);
> sub-agents are for parallel generation (this step). Mixing these patterns causes
> coordination overhead and delivery problems.

Read templates for generation:

- `templates/scrollytelling-base.html` — full HTML skeleton (copy and customize)
- `templates/chapter-module.html` — chapter snippet (repeat for each concept)
- `templates/interactive-widgets.html` — reusable GSAP animation patterns
- `templates/playback-controls.html` — playback control bar (always include for GSAP)

Determine sub-agent count based on concept count:

- Up to 4 concepts: 2 sub-agents
- 5-8 concepts: 3 sub-agents
- 9+ concepts: 4 sub-agents

Spawn parallel sub-agents using a single message with multiple Agent tool calls,
each with `run_in_background: true` and `subagent_type: "general-purpose"`.
Instruct each sub-agent to write its output to a file (e.g., `/tmp/teach-me-chapters-N.html`)
so the output is reliably retrievable after completion.

Each sub-agent receives:

- The visual experience plan (plan.md) for their assigned concepts
- The chapter-module template
- The interactive-widgets template
- The CSS base system from references/css-base-system.md
- The selected theme preset details (from `references/style-presets.md`)
- Animation library reference from references/animation-libraries.md
- The output directory path
- Instruction: "Generate a complete HTML chapter section for each assigned concept.
  Follow the plan exactly. Include all GSAP timeline labels and wire to
  PlaybackController. Return the HTML for each chapter."

Each sub-agent returns: the HTML content for their assigned chapters.

**CRITICAL: Wait for ALL sub-agents to complete before proceeding.**
Do NOT generate HTML yourself while sub-agents are running — even if they appear
slow. Sub-agents with detailed prompts produce specialized, high-quality output
(procedural animations, interactive sliders, physics simulations) that ad-hoc
generation cannot match. Generating HTML yourself while sub-agents run wastes
their output, creates integration problems, and produces an inferior result.
If a sub-agent crashes or fails (not just "takes a while"), only then should you
generate its assigned chapters yourself.

**Step 2A.7: Creative Director assembles**

1. Copy the scrollytelling-base template as starting point
2. Replace `<!-- TOC_ITEMS -->` with sidebar links for each concept
3. Insert all chapter HTML from sub-agents into `<!-- CHAPTERS -->`
4. Insert all animation scripts into `<!-- ANIMATIONS -->`
5. Add playback controls from the playback-controls template
6. Update page title and metadata
7. Insert selected preset's CSS variables into the `:root` PRESET template slot
8. Insert selected preset's font `<link>` tags into the PRESET font loading slot
9. Set `data-theme` attribute on `<html>` to the preset's default theme value
10. Do coherence review:

- Teaching flow builds logically
- Consistent aesthetic across chapters
- All GSAP animations have playback controls
- All CDN dependencies included
- Scroll pacing is appropriate

11. Fix any issues found
12. Write final HTML to `~/.claude/teach-me/[slug]/index.html`

Proceed to Phase 6 (if Manim needed) or Phase 7 (Quality Check).

#### Step 2B: Sub-Agent Fallback Path

> Used when agent teams are not enabled (current default)

Display notice:

```
Agent teams not enabled. Using sub-agent fallback — agents will not debate
directly. To enable agent teams, set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

**Read these references first:**

- `references/animation-libraries.md` — capabilities, CDN links, library patterns
- `references/scrollytelling-patterns.md` — structural patterns
- `references/css-base-system.md` — structural CSS
- `references/style-presets.md` — the selected preset
- All files in `templates/` — HTML templates

**Spawn 3 parallel sub-agents** (Agent tool, subagent_type: `general-purpose`, model: `sonnet`):

1. **Animation Specialist**: "Given this prerequisite chain and audience, propose the most
   engaging visualization for each concept. You have access to GSAP, D3, p5, Three.js,
   Rough.js, and Manim. Go beyond the standard decision matrix. Be creative.
   Include: animation type, library choice, interactive elements, and a brief description
   of what the animation shows."

2. **Pedagogy Advocate**: "Given this prerequisite chain and audience, evaluate which
   concepts need the most visual support and what types of visualizations would best
   serve understanding. Flag any concepts where a simple text explanation is better
   than an animation. Identify where the teaching flow needs visual reinforcement."

3. **UX/Interaction Designer**: "Given this prerequisite chain, propose scroll pacing,
   interactive elements, and accessibility considerations. Include: how many scroll
   steps per concept, where to place interactive controls, transition strategies
   between concepts, and motion-preference media queries."

**After all sub-agents return:**

The main session acts as Creative Director + Visual Critic:

1. Synthesize the three perspectives into a visual experience plan
2. Challenge safe/bland choices (self-critique) — would a Visual Critic push for
   something more creative here?
3. Resolve conflicts between engagement and pedagogy
4. Generate the full HTML using the synthesized plan and templates

**Read templates for generation:**

- `templates/scrollytelling-base.html` — full HTML skeleton (copy and customize)
- `templates/chapter-module.html` — chapter snippet (repeat for each concept)
- `templates/interactive-widgets.html` — reusable GSAP animation patterns
- `templates/playback-controls.html` — playback control bar (always include for GSAP)

**Generation steps:**

1. Copy the base template as starting point
2. Replace `<!-- TOC_ITEMS -->` with sidebar links for each concept
3. For each concept, generate a chapter using the chapter-module template
4. For each chapter, generate the animation decided by the visual plan
5. For each GSAP animation, add timeline labels at meaningful checkpoints
   and wire the timeline to the shared PlaybackController
6. If Manim scenes are needed, flag for Phase 6
7. Insert all chapters into `<!-- CHAPTERS -->`
8. Insert all animation scripts into `<!-- ANIMATIONS -->`
9. Update page title and metadata

If ANY concept needs Manim, flag it for Phase 6 (Install Dependencies).

### Phase 6 — Install Dependencies (conditional)

**Skip this phase entirely if no Manim is needed.**

Run the dependency installer:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/teach-me/scripts/install_deps.sh --check-only
```

If Manim is not installed, inform the user that Manim installation is needed (~2-5 min), then run:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/teach-me/scripts/install_deps.sh
```

### Phase 7 — Quality Check

#### Step 1: Structural checks

The creative team (or main session in fallback mode) already reviewed the HTML for
teaching effectiveness and interaction quality. This step is a sanity check for:

- No broken script/style references (all CDN links load)
- Dark/light theme toggle works
- Sidebar TOC has correct anchor links
- Playback controls function on all GSAP animations
- Manim media files are present if referenced

Fix any issues found before proceeding to Step 2.

#### Step 2: Visual rendering QA

After structural checks pass, render the page and review it visually:

1. Run the visual QA script to capture screenshots:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/teach-me/scripts/visual_qa.py ~/.claude/teach-me/<slug>/index.html
   ```

2. Review screenshots using the Read tool (which supports image files).
   Read at minimum:
   - `/tmp/teach-me-qa/full-page.png` — check overall layout and spacing
   - Each `/tmp/teach-me-qa/visual-*.png` — check individual visualizations

3. For each screenshot, check for these defect categories:
   - **Text overflow**: Text extending beyond its container (SVG circles, boxes, cards)
   - **Overlapping elements**: Nodes, labels, or arrows colliding with each other
   - **Empty visualizations**: SVG/canvas areas that should have content but are blank
   - **Broken layout**: Elements misaligned, incorrectly stacked, or cut off
   - **Unreadable text**: Too small, clipped, or low contrast against background
   - **Bad initial state**: GSAP animations starting in a visually broken position

4. If defects are found:
   - Identify the root cause in the HTML/JS (e.g., font-size too large for container,
     circle radius too small for label text)
   - Fix the HTML source
   - Re-run the visual QA script to verify the fix
   - Maximum 2 fix-and-verify iterations

5. Common fixes reference:
   - **SVG text overflow**: Reduce `font-size`, increase circle `r`, split into `<tspan>` lines, or abbreviate label
   - **Overlapping nodes**: Adjust x/y coordinates to increase spacing
   - **Empty visualization**: Check that animation initial state has `opacity: 1` on at least the base elements

### Phase 8 — Deliver

1. Create output directory:

   ```bash
   mkdir -p ~/.claude/teach-me/<slug>
   ```

   Where `<slug>` is the concept name in kebab-case (e.g., "adam-optimizer", "binary-search")

2. Write the HTML to `~/.claude/teach-me/<slug>/index.html`

3. If Manim media exists, ensure `media/` directory is alongside `index.html`

4. Optionally run the media embedder for small files:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/teach-me/scripts/embed_media.py ~/.claude/teach-me/<slug>/index.html --max-size 500000
   ```

5. Open in browser:

   ```bash
   open ~/.claude/teach-me/<slug>/index.html
   ```

6. Report the output path to the user.

## Reference Files

| File                                    | When to Read                                                                |
| --------------------------------------- | --------------------------------------------------------------------------- |
| `references/prerequisite-reasoning.md`  | Phase 3 (Build Prerequisite Chain)                                          |
| `references/agent-team-prompts.md`      | Phase 5 (Design & Generate Visual Experience)                               |
| `references/animation-libraries.md`     | Phase 5 (Design & Generate Visual Experience)                               |
| `references/scrollytelling-patterns.md` | Phase 5 (Design & Generate Visual Experience)                               |
| `references/css-base-system.md`         | Phase 5 (Design & Generate — structural CSS)                                |
| `references/style-presets.md`           | Phase 4 (Theme Selection) and Phase 5 (Design & Generate — selected preset) |
| `references/manim-patterns.md`          | Phase 6 (only when Manim is needed)                                         |

## Templates

| File                                 | Purpose                                        |
| ------------------------------------ | ---------------------------------------------- |
| `templates/scrollytelling-base.html` | Full HTML skeleton — copy and customize        |
| `templates/chapter-module.html`      | Single chapter snippet — repeat per concept    |
| `templates/interactive-widgets.html` | Reusable GSAP animation patterns               |
| `templates/playback-controls.html`   | Playback control bar — always include for GSAP |

## Scripts

| File                      | Usage                                                                            |
| ------------------------- | -------------------------------------------------------------------------------- |
| `scripts/install_deps.sh` | `bash scripts/install_deps.sh [--check-only]`                                    |
| `scripts/render_manim.py` | `python3 scripts/render_manim.py <file> <class> --format gif --output-dir <dir>` |
| `scripts/embed_media.py`  | `python3 scripts/embed_media.py <html_file> --max-size 500000`                   |
| `scripts/visual_qa.py`    | `python3 scripts/visual_qa.py <html_file> [--output-dir DIR] [--width WIDTH]`    |
