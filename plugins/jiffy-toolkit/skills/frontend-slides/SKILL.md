---
name: frontend-slides
description: Create stunning, animation-rich HTML presentations from scratch or by converting PowerPoint files. Use when the user wants to build a presentation, convert a PPT/PPTX to web, or create slides for a talk/pitch. Helps non-designers discover their aesthetic through visual exploration rather than abstract choices.
---

# Frontend Slides Skill

Create zero-dependency, animation-rich HTML presentations that run entirely in the browser. This skill helps non-designers discover their preferred aesthetic through visual exploration ("show, don't tell"), then generates production-quality slide decks.

## Core Philosophy

1. **Zero Dependencies** — No npm, no build tools. Multi-file output served via `python3 serve.py`. Single-file option available with `--single-file` for portability.
2. **Show, Don't Tell** — People don't know what they want until they see it. Generate visual previews, not abstract choices.
3. **Distinctive Design** — Avoid generic "AI slop" aesthetics. Every presentation should feel custom-crafted.
4. **Production Quality** — Code should be well-commented, accessible, and performant.
5. **Viewport Fitting (CRITICAL)** — Every slide MUST fit exactly within the viewport. No scrolling within slides, ever. This is non-negotiable.

---

## CRITICAL: Viewport Fitting Requirements

**This section is mandatory for ALL presentations. Every slide must be fully visible without scrolling on any screen size.**

### The Golden Rule

```
Each slide = exactly one viewport height (100vh/100dvh)
Content overflows? -> Split into multiple slides or reduce content
Never scroll within a slide.
```

### Content Density Limits

To guarantee viewport fitting, enforce these limits per slide:

| Slide Type       | Maximum Content                                           |
| ---------------- | --------------------------------------------------------- |
| Title slide      | 1 heading + 1 subtitle + optional tagline                 |
| Content slide    | 1 heading + 4-6 bullet points OR 1 heading + 2 paragraphs |
| Feature grid     | 1 heading + 6 cards maximum (2x3 or 3x2 grid)             |
| Code slide       | 1 heading + 8-10 lines of code maximum                    |
| Quote slide      | 1 quote (max 3 lines) + attribution                       |
| Image slide      | 1 heading + 1 image (max 60vh height)                     |
| Two-column       | 1 heading + 2 columns of 3-4 bullets each                 |
| Fact/stat        | 1 large number + 1 subtitle + optional context line       |
| Section divider  | 1 heading + optional subtitle                             |
| Image-left/right | 1 image + 1 heading + 3-4 bullets                         |
| Video slide      | 1 heading + 1 video (max 60vh height)                     |

**If content exceeds these limits -> Split into multiple slides**

For the full mandatory CSS architecture, responsive breakpoints, and troubleshooting, see [references/viewport-fitting.md](references/viewport-fitting.md).

---

## Phase 0: Detect Mode

First, determine what the user wants:

**Mode A: New Presentation**

- User wants to create slides from scratch
- Proceed to Phase 1 (Content Discovery)

**Mode B: PPT Conversion**

- User has a PowerPoint file (.ppt, .pptx) to convert
- Proceed to Phase 4 (PPT Extraction)

**Mode C: Existing Presentation Enhancement**

- User has an HTML presentation and wants to improve it
- Read the existing file, understand the structure, then enhance
- **CRITICAL: When modifying existing slides, ALWAYS ensure viewport fitting is maintained**

**Mode D: Multi-File Output (Default for New Presentations)**

- When creating a new presentation (Mode A) or converting PPT (Mode B), output defaults to multi-file format
- Output directory: `~/.claude/presentations/[presentation-name]/`
- Structure: index.html + style.css + script.js + slides/\*.html + serve.py
- See [references/multi-file-architecture.md](references/multi-file-architecture.md) for full architecture
- **Single-file option**: If user requests `--single-file` or mentions wanting a portable single file, post-process the multi-file output into one HTML file (see multi-file-architecture.md)
- Mode C (enhancing existing single-file presentations) is unaffected

### Mode C: Critical Modification Rules

When enhancing existing presentations, follow these mandatory rules:

**1. Before Adding Any Content:**

- Read the current slide structure and count existing elements
- Check against content density limits (see table above)
- Calculate if the new content will fit within viewport constraints

**2. When Adding Images (MOST COMMON ISSUE):**

- Images must have `max-height: min(50vh, 400px)` or similar viewport constraint
- Check if current slide already has maximum content (1 heading + 1 image)
- If adding an image to a slide with existing content -> **Split into two slides**
- Example: If slide has heading + 4 bullets, and user wants to add an image:
  - **DON'T:** Cram image onto same slide
  - **DO:** Create new slide with heading + image, keep bullets on original slide
  - **OR:** Reduce bullets to 2-3 and add image with proper constraints

**3. When Adding Text Content:**

- Max 4-6 bullet points per slide
- Max 2 paragraphs per slide
- If adding content exceeds limits -> **Split into multiple slides or create a continuation slide**

**4. Required Checks After ANY Modification:**

```
Does the slide have `overflow: hidden` on `.slide` class?
Are all new elements using `clamp()` for font sizes?
Do new images have viewport-relative max-height?
Does total content respect density limits?
Will this fit on a 1280x720 screen? On mobile portrait?
```

**5. Proactive Reorganization (NOT Optional):**
When you detect that modifications will cause overflow:

- **Automatically split content across slides** — Don't wait for user to ask
- Inform user: "I've reorganized the content across 2 slides to ensure proper viewport fitting"
- Use "continued" pattern for split content (e.g., "Key Features" -> "Key Features (Continued)")

**6. Testing After Modifications:**
Mentally verify the modified slide at these viewport sizes:

- Desktop: 1280x720 (smallest common)
- Tablet portrait: 768x1024
- Mobile: 375x667

**If in doubt -> Split the content. Never allow scrolling within a slide.**

---

## Phase 1: Content Discovery (New Presentations)

Before designing, understand the content. Ask via AskUserQuestion:

### Step 1.1: Presentation Context + Images (Single Form)

**IMPORTANT:** Ask ALL 4 questions in a single AskUserQuestion call so the user can fill everything out at once before submitting.

**Question 1: Purpose**

- Header: "Purpose"
- Question: "What is this presentation for?"
- Options:
  - "Pitch deck" — Selling an idea, product, or company to investors/clients
  - "Teaching/Tutorial" — Explaining concepts, how-to guides, educational content
  - "Conference talk" — Speaking at an event, tech talk, keynote
  - "Internal presentation" — Team updates, strategy meetings, company updates

**Question 2: Slide Count**

- Header: "Length"
- Question: "Approximately how many slides?"
- Options:
  - "Short (5-10)" — Quick pitch, lightning talk
  - "Medium (10-20)" — Standard presentation
  - "Long (20+)" — Deep dive, comprehensive talk

**Question 3: Content**

- Header: "Content"
- Question: "Do you have the content ready, or do you need help structuring it?"
- Options:
  - "I have all content ready" — Just need to design the presentation
  - "I have rough notes" — Need help organizing into slides
  - "I have a topic only" — Need help creating the full outline

**Question 4: Images**

- Header: "Images"
- Question: "Do you have images to include? Select 'No images' or select Other and type/paste your image folder path."
- Options:
  - "No images" — Text-only presentation (use CSS-generated visuals instead)
  - "./assets" — Use the `assets/` folder in the current project

The user can select **"Other"** to type or paste any custom folder path (e.g. `~/Desktop/screenshots`). This way the image folder path is collected in the same form — no extra round-trip.

**Question 5: Inline Editing**

- Header: "Editing"
- Question: "Do you need to edit text directly in the browser after generation?"
- Options:
  - "Yes (Recommended)" — Can edit text in-browser, auto-save to localStorage, export file
  - "No" — Presentation only, keeps file smaller

**Remember the user's choice — it determines whether edit-related HTML/CSS/JS is included in Phase 3.**

If user has content, ask them to share it (text, bullet points, images, etc.).

### Step 1.2: Image Evaluation

**User-provided assets are important visual anchors** — but not every asset is necessarily usable. The first step is always to evaluate. After evaluation, the curated assets become additional context that shapes how the presentation is built. This is a **co-design process**: text content + curated visuals together inform the slide structure from the start, not a post-hoc "fit images in after the fact."

**If user selected "No images"** -> Skip the entire image pipeline. Proceed directly to Phase 2 (Style Discovery) and Phase 3 (Generate Presentation) using text content only. The presentation will use CSS-generated visuals (gradients, shapes, patterns, typography) for visual interest — this is the original behavior and produces fully polished results without any images.

**If user provides an image folder:**

1. **Scan the folder** — Use `ls` to list all image files (`.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`)
2. **View each image** — Use the Read tool to see what each image contains (Claude is multimodal)
3. **Evaluate each image** — For each image, assess:
   - Filename and dimensions
   - What it shows (screenshot, logo, chart, diagram, photo)
   - **Usability:** Is the image clear, relevant to the presentation topic, and high enough quality? Mark as `USABLE` or `NOT USABLE` (with reason: blurry, irrelevant, broken, etc.)
   - **Content signal:** What feature or concept does this image represent? (e.g., "chat_ui.png" -> "conversational interface feature")
   - Shape: square, landscape, portrait, circular
   - Dominant colors (important for style compatibility later)
4. **Present the evaluation and proposed slide outline to the user** — Show which images are usable and which are not, with reasons. Then show the proposed slide outline with image assignments.

**Co-design: curated assets inform the outline**

After evaluation, the **usable** images become context for planning the slide structure alongside text content. This is not "plan slides then add images" — it's designing the presentation around both text and visuals from the start:

- 3 usable product screenshots -> plan 3 feature slides, each anchored by one screenshot
- 1 usable logo -> title slide and/or closing slide
- 1 usable architecture diagram -> dedicated "How It Works" slide
- 1 blurry/irrelevant image -> excluded, with explanation to user

This means curated images are factored in **before** style selection (Phase 2) and **before** HTML generation (Phase 3). They are co-equal context in the design process.

5. **Confirm outline via AskUserQuestion** — Do NOT break the flow by asking the user to type free text. Use AskUserQuestion to confirm:

**Question: Outline Confirmation**

- Header: "Outline"
- Question: "Does this slide outline and image selection look right?"
- Options:
  - "Looks good, proceed" — Move on to style selection
  - "Adjust images" — I want to change which images go where
  - "Adjust outline" — I want to change the slide structure

This keeps the entire flow in the AskUserQuestion format without dropping to free-text chat.

For image processing code (Pillow operations), see [references/media-and-widgets.md](references/media-and-widgets.md).

---

## Phase 2: Style Discovery (Visual Exploration)

**CRITICAL: This is the "show, don't tell" phase.**

Most people can't articulate design preferences in words. Instead of asking "do you want minimalist or bold?", we generate mini-previews and let them react.

### How Users Choose Presets

Users can select a style in **three ways**:

**Option A: Guided Discovery ("Show me options")**

- User answers a mood question
- Skill generates a theme explorer with recommended presets highlighted
- User browses and picks their favorite
- Best for users who don't have a specific style in mind

**Option B: Direct Selection ("I know what I want")**

- User picks from a shortlist of popular presets
- Skip to Phase 3 immediately

**Option C: Full Browse ("Let me browse all")**

- User browses all 20 presets in the theme explorer with no filtering
- Best for users who want to see everything before deciding

**Available Presets:**
| Preset | Vibe | Best For |
|--------|------|----------|
| Bold Signal | Confident, high-impact | Pitch decks, keynotes |
| Electric Studio | Clean, professional | Agency presentations |
| Creative Voltage | Energetic, retro-modern | Creative pitches |
| Dark Botanical | Elegant, sophisticated | Premium brands |
| Notebook Tabs | Editorial, organized | Reports, reviews |
| Pastel Geometry | Friendly, approachable | Product overviews |
| Vintage Editorial | Witty, personality-driven | Personal brands |
| Neon Cyber | Futuristic, techy | Tech startups |
| Terminal Green | Developer-focused | Dev tools, APIs |
| Swiss Modern | Minimal, precise | Corporate, data |
| Paper & Ink | Literary, thoughtful | Storytelling |
| Liquid Glass | Modern, premium, depth | Product launches |
| Director's Cut | Cinematic, moody | Keynotes, stories |
| Micrographic | Precise, technical | Engineering reviews |
| Jewel Mono | Focused, brandable | Corporate, fintech |
| Whiteboard | Informal, sketch-like | Brainstorming, workshops |
| Bento Box | Premium, modular | Product launches, QBRs |
| Aurora Glow | Atmospheric, cinematic | Vision decks, keynotes |
| Scrapbook | Curated chaos, collage | Retrospectives, culture |
| Retro Futura | Space-age, retrofuturist | Roadmaps, innovation |

For full preset details (colors, fonts, signature elements), see [references/style-presets.md](references/style-presets.md).

### Step 2.0: Style Path Selection

First, ask how the user wants to choose their style:

**Question: Style Selection Method**

- Header: "Style"
- Question: "How would you like to choose your presentation style?"
- Options:
  - "Show me options" — Answer a quick mood question, then browse recommended styles (best for undecided users)
  - "I know what I want" — Pick from popular presets directly
  - "Let me browse all" — Open the full theme explorer with all 20 styles

**If "Show me options"** -> Continue to Step 2.1 (Mood Selection)

**If "I know what I want"** -> Show preset picker:

**Question: Pick a Preset**

- Header: "Preset"
- Question: "Which style would you like to use?"
- Options:
  - "Bold Signal" — Vibrant card on dark, confident and high-impact
  - "Dark Botanical" — Elegant dark with soft abstract shapes
  - "Liquid Glass" — Modern glassmorphism with depth
  - "Bento Box" — Premium modular tile grid, Apple-style
  - "Notebook Tabs" — Editorial paper look with colorful section tabs
  - "Scrapbook" — Curated collage with washi tape and polaroids

(If user picks one, skip to Phase 3. If they want to see more options, proceed to "Let me browse all" flow.)

**If "Let me browse all"** -> Skip to Step 2.2, generating the theme explorer with ALL 20 presets visible (no mood filtering, no highlighted recommendations).

### Step 2.1: Mood Selection (Guided Discovery -- "Show me options" path only)

This step only runs when the user chose "Show me options" in Step 2.0.

**Question 1: Feeling**

- Header: "Vibe"
- Question: "What feeling should the audience have when viewing your slides?"
- Options:
  - "Impressed/Confident" — Professional, trustworthy, this team knows what they're doing
  - "Excited/Energized" — Innovative, bold, this is the future
  - "Calm/Focused" — Clear, thoughtful, easy to follow
  - "Inspired/Moved" — Emotional, storytelling, memorable
- multiSelect: true (can choose up to 2)

### Step 2.2: Generate Theme Explorer

Based on the user's path, generate a **single self-contained HTML file** as the theme explorer:

**Output**: `~/.claude/presentations/.theme-explorer/index.html`

This file replaces the old 3-file preview system. It contains all candidate presets as switchable views in a single page.

#### Theme Explorer Specification

**Structure**:

- Single HTML file, fully self-contained (inline CSS + JS, no external dependencies except Google Fonts)
- Each preset is rendered as a mini title-slide preview in its own CSS scope
- CSS scoping: each preset preview lives in a `<section>` with inline CSS variables in a `<style>` block, preventing cross-contamination

**Layout**:

- **Gallery view** (default): Grid of preset cards. Each card shows the preset name, a mini title-slide preview rendered in that preset's style (typography, colors, signature elements)
- If coming from "Show me options" path: 3 recommended presets highlighted at top with "Recommended for you" label, remaining presets in "All styles" grid below
- If coming from "Let me browse all" path: all 20 presets in a single grid, no recommendations section

**Interaction**:

- Click a card -> full-width preview of a representative slide (title heading + subtitle + 2-3 content elements) rendered in that preset's full style
- Keyboard navigation: arrow keys to cycle between presets in full-width view, Enter to select, Escape to return to gallery
- Each full-width preview includes a "Select [Preset Name]" button and a "Back to gallery" link

**Mood-to-Preset Mapping** (for "Show me options" path -- determines which 3 presets are highlighted):

| Mood                | Recommended Presets                                                                        |
| ------------------- | ------------------------------------------------------------------------------------------ |
| Impressed/Confident | Bold Signal, Electric Studio, Dark Botanical, Liquid Glass, Bento Box                      |
| Excited/Energized   | Creative Voltage, Neon Cyber, Retro Futura                                                 |
| Calm/Focused        | Notebook Tabs, Paper & Ink, Swiss Modern, Micrographic, Jewel Mono                         |
| Inspired/Moved      | Dark Botanical, Vintage Editorial, Pastel Geometry, Director's Cut, Aurora Glow, Scrapbook |

Pick 3 presets from the matching mood(s). If the user selected 2 moods, pick 2 from the first mood and 1 from the second.

**Logo in explorer**: If the user provided images in Phase 1 and a logo was identified as `USABLE`, embed it (base64) into each preset's preview card. This creates a "wow moment" -- the user sees their own brand identity styled twenty different ways.

### Step 2.3: Present Theme Explorer

Open the theme explorer in the browser:

```
I've created a theme explorer for you to browse all available styles:

~/.claude/presentations/.theme-explorer/index.html

Open it in your browser to see each style in action. Click any card for a full-size preview, use arrow keys to cycle, and press Escape to return to the gallery.
```

Then use AskUserQuestion:

**Question: Pick Your Style**

- Header: "Style"
- Question: "Which style do you prefer?"
- Options:
  - "[Recommended 1]" — [Brief description] _(only if "Show me options" path)_
  - "[Recommended 2]" — [Brief description] _(only if "Show me options" path)_
  - "[Recommended 3]" — [Brief description] _(only if "Show me options" path)_
  - "Other" — I found a different style I like in the explorer
  - "Mix elements" — Combine aspects from different styles

If "Other", ask which preset name.
If "Mix elements", ask for specifics.

---

## Phase 3: Generate Presentation

Now generate the full presentation using the multi-file architecture.
Output directory: `~/.claude/presentations/[presentation-name]/`

For agent persona prompts, see [references/agent-team-prompts.md](references/agent-team-prompts.md).
For engagement defaults, see [references/engagement-defaults.md](references/engagement-defaults.md).
For multi-file architecture, see [references/multi-file-architecture.md](references/multi-file-architecture.md).

### Step 3.0: Detect Agent Team Availability

Check for the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` environment variable:

```bash
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
```

Branch to Step 3A (agent team) or Step 3B (sub-agent fallback).

### Step 3A: Agent Team Path (PREFERRED when enabled)

> Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
>
> **This path uses agent teams for DEBATE and PLANNING only, then switches to
> parallel sub-agents for HTML generation. Agent teams excel at inter-agent
> discussion; sub-agents excel at independent parallel generation.**

#### 3A.1: Determine team size

Based on the narrative outline slide count:

- Up to 15 slides: 1 Engagement Strategist (2 agents total)
- 16+ slides: 1 Engagement Strategist + 1 Visual Critic (3 agents total)

#### 3A.2: Story Architect creates narrative outline + style.css

Before spawning teammates, the team lead (you) must:

1. Create the narrative outline with per-slide specifications:
   - Slide number, filename, type, content assignment
   - Fragment strategy, auto-animate markers
   - Layout class and special features
   - Batch assignments for later sub-agent generation

2. Generate style.css:
   - Apply chosen preset's CSS variables and signature elements
   - Include all global layout classes, fragment CSS, auto-animate CSS,
     responsive breakpoints, viewport fitting rules, and accessibility rules

#### 3A.3: Create team and debate engagement strategy

Use the `TeamCreate` tool to create the team. You (the main session) are the
Story Architect and team lead.

```
TeamCreate(team_name="slides-[presentation-name]", description="Planning engagement for [presentation-name]")
```

Spawn teammate(s) using the `Agent` tool with `team_name` and `name` parameters:

```
# Always spawn:
Agent(
  team_name="slides-[presentation-name]",
  name="engagement-strategist",
  subagent_type="general-purpose",
  prompt="[Full Engagement Strategist persona from references/agent-team-prompts.md + narrative outline + engagement rules + style preset]"
)

# Only spawn if 16+ slides:
Agent(
  team_name="slides-[presentation-name]",
  name="visual-critic",
  subagent_type="general-purpose",
  prompt="[Full Visual Critic persona from references/agent-team-prompts.md + narrative outline]"
)
```

**Debate phase:**

- Engagement Strategist reviews the narrative outline and proposes engagement enhancements:
  fragment strategies, auto-animate opportunities, animation timing, interactive features
- Visual Critic (if present) challenges safe choices and pushes for more distinctive visuals
- Story Architect moderates via SendMessage (max 2 rounds)

#### 3A.4: Plan lock

After debate concludes, the Story Architect synthesizes all feedback into an
**enhanced narrative outline** — the locked plan. This is the same outline from
3A.2 but enriched with engagement and visual decisions from the debate:

- Per-slide fragment strategy (confirmed/enhanced)
- Auto-animate pairs (confirmed/enhanced)
- Animation timing specifications
- Interactive feature assignments
- Visual distinctiveness notes

Write the enhanced outline to a file the sub-agents will read:
`~/.claude/presentations/[presentation-name]/plan.md`

#### 3A.5: Team shutdown

Shut down teammates via `SendMessage(type="shutdown_request")` and clean up team resources.

#### 3A.6: Parallel sub-agent generation

> **IMPORTANT: Use standalone background sub-agents here, NOT agent team members.**
> The debate team was shut down in Step 3A.5. Generation sub-agents must be spawned
> as independent background agents using `Agent(run_in_background: true)` — do NOT
> pass `team_name` or `name` parameters. Agent teams are for debate (Steps 3A.1-3A.5);
> sub-agents are for parallel generation (this step). Mixing these patterns causes
> coordination overhead and delivery problems.

Spawn 2-3 parallel sub-agents using a single message with multiple Agent tool calls,
each with `run_in_background: true` and `subagent_type: "general-purpose"`.
Determine count based on slide count (same logic as Step 3B):

- Up to 15 slides: 2 sub-agents
- 16+ slides: 3 sub-agents

Each sub-agent receives in their prompt:

- The enhanced narrative outline (plan.md) for their assigned slide batch
- The CSS class catalog from references/agent-team-prompts.md
- The engagement rules from references/engagement-defaults.md
- The style preset details
- The output directory path (`~/.claude/presentations/[name]/slides/`)

Each sub-agent writes their batch of slides/\*.html files and returns:
list of files written, any auto-animate pairs created.

**CRITICAL: Wait for ALL sub-agents to complete before proceeding.**
Do NOT generate slides yourself while sub-agents are running — even if they appear
slow. Sub-agents with detailed prompts produce specialized, high-quality output
that ad-hoc generation cannot match. Generating HTML yourself while sub-agents run
wastes their output, creates integration problems, and produces an inferior result.
If a sub-agent crashes or fails (not just "takes a while"), only then should you
generate its assigned slides yourself.

#### 3A.7: Story Architect assembles and reviews

After all sub-agents complete:

- Writes index.html (shell with CDN dependencies)
- Writes script.js with the SLIDES manifest array
- Does coherence review (narrative, visual, engagement, technical)
- Reads all generated slides and applies any missing engagement defaults:
  - Add missing fragments
  - Validate auto-animate pairs
  - Check content density limits
- Copies serve.py to presentation directory
- Fixes any issues found

### Step 3B: Sub-Agent Fallback Path

> Used when agent teams are not enabled

Display notice:

```
Agent teams not enabled. Using sub-agent fallback.
To enable agent teams, set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

**3B.1: Main session creates narrative outline** (acts as Story Architect)

**3B.2: Main session generates style.css**

**3B.3: Spawn 2-3 parallel sub-agents for slide generation**

Spawn sub-agents (Agent tool, subagent_type: general-purpose, model: sonnet):

- Each receives: their assigned slide specs, CSS class catalog, engagement rules,
  the style preset, and the output directory path
- Each writes their batch of slides/\*.html files
- Each returns: list of files written, any auto-animate pairs created

**3B.4: Main session reviews engagement** (acts as Engagement Reviewer)

Read all generated slides and apply engagement defaults:

- Add missing fragments
- Validate auto-animate pairs
- Check content density limits

**3B.5: Main session assembles**

- Write index.html + script.js
- Copy serve.py
- Do coherence review

### Step 3C: Single-File Post-Processing (if requested)

If the user requested --single-file or mentioned wanting a portable file:

1. Read all generated files
2. Inline style.css into <style> in index.html <head>
3. Concatenate all slides/\*.html in order into <body>
4. Inline script.js into <script> in <body>, removing fetch-based assembly
5. Write combined file to ~/.claude/presentations/[name]/[name].html

---

## Feature Reference

Features are organized by reference file. Load the relevant file when the presentation needs that feature.

### Navigation & Interaction -> [references/navigation-and-interaction.md](references/navigation-and-interaction.md)

Load when generating the SlidePresentation class JavaScript.

- **Fragments**: Step-by-step content reveal (use for 2-4 slides max per presentation, max 3-4 steps per slide, group related elements)
- **Code line highlighting**: Walk through code step by step (use on code slides)
- **Auto-animate (FLIP)**: Morph elements between slides (use for 2-3 transitions max)
- **Overview mode**: ESC/O thumbnail grid of all slides
- **URL hash routing**: Deep linking to specific slides
- **Fullscreen**: F key toggle
- **Keyboard shortcuts**: Complete reference table

### Media & Widgets -> [references/media-and-widgets.md](references/media-and-widgets.md)

Load when the presentation includes images, video, diagrams, or animated widgets.

- **Image pipeline**: Pillow processing, placement patterns, CSS framing
- **Video slides**: Embedded video with play/pause, auto-pause on nav
- **Mermaid diagrams**: CDN-rendered diagrams with theme integration
- **Animated counters**: CSS @property + JS fallback for hero metrics
- **CSS charts**: Bar and pie charts (3-5 data points max)
- **GSAP playback controls**: Timeline scrubbing for animated slides
- **SVG widget library**: 5 widget patterns (process flow, comparison, build-up, data transform, math function)
- **Optional CDN dependencies**: GSAP, Mermaid, Rough.js — include only when needed

### Presenter Features -> [references/presenter-features.md](references/presenter-features.md)

Load when the presentation needs presenter/audience tools.

- **Speaker view**: S key opens notes + timer window (BroadcastChannel)
- **Cross-tab sync**: P key for audience follow-along
- **Blackout/whiteout**: B/W keys to pause presentation
- **Theme toggle**: T key cycles light/dark variants
- **Print stylesheet**: One slide per page, hidden UI
- **Scroll-driven animations**: Progressive enhancement for CSS-only entrance animations
- **Code copy button**: Hover-to-show copy button on code blocks

### Edit Mode -> [references/edit-mode.md](references/edit-mode.md)

Load ONLY when user opted in to inline editing in Phase 1.

- Edit button with hotzone hover pattern (must use JS, not CSS ~ selector)

### Accessibility & Quality -> [references/accessibility-and-quality.md](references/accessibility-and-quality.md)

Load when finalizing any presentation.

- Code comment standards, semantic HTML, ARIA, inert slides, reduced motion, high contrast

### Style Presets -> [references/style-presets.md](references/style-presets.md)

Load when generating style previews or applying a preset in Phase 2/3.

- 20 curated presets with colors, fonts, and signature elements
- Font pairing quick reference
- Viewport fitting base CSS (also in viewport-fitting.md)

### Multi-File Architecture -> [references/multi-file-architecture.md](references/multi-file-architecture.md)

Load when generating any new presentation (Phase 3).

- File structure conventions, index.html/script.js/serve.py templates
- Slide fragment file format, assembly via fetch
- Single-file post-processing instructions

### Engagement Defaults -> [references/engagement-defaults.md](references/engagement-defaults.md)

Load when generating slides (Phase 3) — both agent team and sub-agent paths.

- Progressive disclosure rules per slide type
- Auto-animate rules and candidates
- Content density enforcement limits
- Fragment animation defaults

### Agent Team Prompts -> [references/agent-team-prompts.md](references/agent-team-prompts.md)

Load when executing Phase 3 (Generate Presentation).

- Story Architect persona (team lead, Opus)
- Engagement Strategist persona (Sonnet) for debate
- Visual Critic persona (Sonnet, 16+ slides) for debate
- CSS Class Catalog for sub-agent generation

---

## Anti-Slop Patterns

### DO NOT USE (Generic AI Patterns)

**Fonts:** Inter, Roboto, Arial, system fonts as display

**Colors:** `#6366f1` (generic indigo), purple gradients on white

**Layouts:** Everything centered, generic hero sections, identical card grids

**Decorations:** Realistic illustrations, gratuitous glassmorphism, drop shadows without purpose

### CSS Gotchas

**CSS Function Negation:**

- Never negate CSS functions directly — `-clamp()`, `-min()`, `-max()` are silently ignored by browsers with no console error
- Always use `calc(-1 * clamp(...))` instead

```css
/* WRONG — silently ignored by browsers: */
right: -clamp(28px, 3.5vw, 44px); /* Invalid! */

/* CORRECT — wrap in calc(): */
right: calc(-1 * clamp(28px, 3.5vw, 44px)); /* Works */
```

**Responsive & Viewport Fitting (CRITICAL):**

- Every `.slide` must have `height: 100vh; height: 100dvh; overflow: hidden;`
- All typography and spacing must use `clamp()`
- Respect content density limits (max 4-6 bullets, max 6 cards, etc.)
- Include breakpoints for heights: 700px, 600px, 500px
- When content doesn't fit -> split into multiple slides, never scroll

---

For animation patterns (entrance animations, staggered text, backgrounds, grain textures, interactive effects) and style-effect mapping, see [references/html-architecture.md](references/html-architecture.md).

---

## Phase 4: PPT Conversion

When converting PowerPoint files:

### Step 4.1: Extract Content

Use Python with `python-pptx` to extract all content. For each slide, collect:

- **Title** from `slide.shapes.title`
- **Text** from all `shape.has_text_frame` shapes
- **Images** from `shape.shape_type == 13` (Picture) — save `shape.image.blob` to `assets/` directory
- **Notes** from `slide.notes_slide.notes_text_frame` if present

### Step 4.2: Confirm Content Structure

Present the extracted content to the user and confirm before proceeding to style selection.

### Step 4.3: Style Selection

Proceed to Phase 2 (Style Discovery) with the extracted content in mind.

### Step 4.4: Generate HTML

Convert the extracted content into the chosen style, preserving:

- All text content
- All images (referenced from assets folder)
- Slide order
- Any speaker notes (as HTML comments or separate file)

---

## Phase 5: Delivery

### Final Output

When the presentation is complete:

1. **Clean up temporary files** — Delete `~/.claude/presentations/.theme-explorer/` if it exists
2. **Start the server and open** — Launch serve.py and open in browser:
   ```bash
   cd ~/.claude/presentations/[presentation-name] && python3 serve.py &
   open http://localhost:8000
   ```
3. **Provide summary**

```
Your presentation is ready!

Folder: ~/.claude/presentations/[presentation-name]/
Slides: [count]
Style: [Style Name]

**To view:**
cd ~/.claude/presentations/[presentation-name]
python3 serve.py
# Then open http://localhost:8000

**Navigation:**
- Arrow keys or Space to navigate
- Scroll/swipe also works
- Click the dots on the right to jump to a slide

**To customize:**
- Colors: Edit style.css (look for :root CSS variables)
- Individual slides: Edit files in slides/ directory
- Fonts: Change the font link in index.html

**To edit a specific slide:**
- Open slides/[NN]-[name].html in your editor
- Changes take effect on browser refresh

Would you like me to make any adjustments?
```

If user opted in to inline editing, add:

```
**Editing:**
- Hover over top-left corner or press E to enter edit mode
- Click any text to edit directly
- Ctrl+S or click "Save file" to save changes
```

If single-file was generated, add:

```
**Portable version:**
A single-file version is also available at:
~/.claude/presentations/[name]/[name].html
This file can be opened directly in any browser without a server.
```

---

## Phase 6: Export (Optional)

After delivering the presentation, offer to export it to Google Slides or PDF.

### When to Offer

Always mention export availability at the end of Phase 5 delivery. Add this to the summary:

```
**To export:**
- Google Slides: Just ask "export to Google Slides"
- PDF: Just ask "export to PDF"
```

### Prerequisites

The following must be installed (one-time setup):

```bash
npm install -g decktape
pip install google-api-python-client google-auth google-auth-httplib2 beautifulsoup4
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/drive.file,https://www.googleapis.com/auth/presentations,https://www.googleapis.com/auth/cloud-platform
```

If the user asks to export and prerequisites are missing, guide them through setup first.

### Export to Google Slides

When the user asks to export to Google Slides:

1. **Run the export script**:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/frontend-slides/scripts/export-to-gslides.py \
     ~/.claude/presentations/[presentation-name]/ \
     --title "[Presentation Title]" \
     --format gslides
   ```

2. **Report results**:

   ```
   Exported to Google Slides!

   Google Slides: [URL]
   PDF: ~/.claude/presentations/[name]/[name].pdf

   The presentation is shared via Google Slides (view-only).

   Note: Animations and transitions are not preserved in Google Slides —
   each fragment step becomes a separate slide. For the full animated
   experience, use the original HTML version.
   ```

### Export to PDF Only

When the user asks for PDF only:

1. **Run the export script**:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/frontend-slides/scripts/export-to-gslides.py \
     ~/.claude/presentations/[presentation-name]/ \
     --format pdf
   ```

2. **Report results**:

   ```
   PDF exported!

   PDF: ~/.claude/presentations/[name]/[name].pdf

   Each fragment step is a separate page. The PDF preserves the visual
   appearance of each slide exactly as rendered.
   ```

### Troubleshooting Export

- **Decktape not found**: Run `npm install -g decktape`
- **Google auth error**: Run the `gcloud auth application-default login` command above
- **Decktape captures too few/many slides**: Adjust `--pause` (default 2000ms). Increase for complex animations, decrease for simple slides.
- **Images not loading in Google Slides**: Ensure `gcloud auth` includes the `drive.file` scope

---

## Troubleshooting

For viewport troubleshooting (content overflow, text scaling, short screens), see [references/viewport-fitting.md](references/viewport-fitting.md).

**Fonts not loading:** Check Fontshare/Google Fonts URL and font names in CSS.
**Animations not triggering:** Verify Intersection Observer is running and `.visible` class is being added.
**Scroll snap not working:** Ensure `scroll-snap-type` on html/body and `scroll-snap-align: start` on each slide.
**Performance issues:** Use `will-change` sparingly; prefer `transform` and `opacity` animations.

---

## Related Skills

- **learn** — Generate FORZARA.md documentation for the presentation
- **frontend-design** — For more complex interactive pages beyond slides
- **design-and-refine:design-lab** — For iterating on component designs

---

## Example Session Flows

**New presentation:** User asks for pitch deck -> Phase 1 (purpose, content, images) -> Evaluate images -> Confirm outline -> Phase 2 (style path selection -> theme explorer -> pick style) -> Phase 3 (agent team generates multi-file presentation to ~/.claude/presentations/) -> Phase 5 (serve and open) -> Tweaks -> Done.

**Single-file presentation:** Same as above, but user requests --single-file -> Phase 3 generates multi-file first, then post-processes into one HTML file -> Open directly in browser -> Done.

**PPT conversion:** User provides .pptx -> Extract content/images -> Confirm structure -> Phase 2 (style selection) -> Generate HTML with preserved assets -> Done.

**Export to Google Slides:** User asks to export -> Check prerequisites -> Run export-to-gslides.py with --format gslides -> Report Google Slides URL and PDF path -> Done.
