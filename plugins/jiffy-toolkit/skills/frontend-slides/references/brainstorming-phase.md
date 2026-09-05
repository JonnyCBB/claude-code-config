# Phase 2: Collaborative Brainstorming

The brainstorming phase captures narrative arc, per-slide messaging, animation key moments, and visual direction — including style preset selection — before slide generation. It replaces the former Phase 2 (Style Discovery) by absorbing style selection into Wave 3.

The phase uses a 3-wave interview structure adapted from `/elicit-requirements`, enriched with presentation design expertise. At each wave boundary, the agent generates lightweight HTML mockups and opens them for visual feedback — creating an agent→generate→review→iterate loop.

---

## When This Phase Runs

**Standard order** (user has content — "I have rough notes" or "I have all content ready"):
Phase 1 (Content Discovery) → **Phase 2 (Collaborative Brainstorming)** → Phase 3 (Generation)

**Content-routing order** (user has "topic only"):
Phase 1 Step 1.1 (context questions only) → **Phase 2 (Collaborative Brainstorming)** → Phase 1 (remaining steps, smart dedup) → Phase 3 (Generation)

The routing signal comes from Phase 1 Step 1.1 Question 3 (content readiness). When the user selects "I have a topic only", Phase 2 runs immediately after the initial context questions, before the full content discovery flow.

---

## Skip Prompt

At phase entry, offer the user a choice via AskUserQuestion:

**Question: Brainstorming**

- Header: "Brainstorm"
- Question: "I have a brainstorming phase to help align narrative, visuals, and animations. Want to brainstorm, or proceed directly to generation?"
- Options:
  - "Let's brainstorm (Recommended)" — Align on narrative, slide design, and visual direction before generating
  - "Skip to generation" — Proceed directly with the content and style I have in mind

If the user skips, no `brainstorm-notes.md` is created. The pipeline proceeds directly to Phase 3 (Generation).

---

## Session Resume Detection

Before the skip prompt, check for an existing `brainstorm-notes.md` at `~/.claude/presentations/[name]/.brainstorm/brainstorm-notes.md`.

If found, read the `status` field from frontmatter:

- `wave-1-complete`: Wave 1 is done, Wave 2 pending
- `wave-2-complete`: Waves 1-2 done, Wave 3 pending
- `complete`: All waves done (unlikely to see this — it means brainstorming finished but generation didn't run)

Offer three options via AskUserQuestion:

**Question: Resume Brainstorming**

- Header: "Resume"
- Question: "I found a partial brainstorming session (completed through [wave name]). How would you like to proceed?"
- Options:
  - "Resume from [next wave] (Recommended)" — Continue where we left off
  - "Use what we have" — Proceed to generation with partial brainstorm decisions
  - "Start fresh" — Skip brainstorming entirely (full creative control)

---

## Context-Sharing Protocol

Adapted from `/elicit-requirements`. Apply throughout all three waves.

### Before each wave (Wave Preamble)

```
**My understanding so far:** [2-4 sentences summarizing what's been decided]

**What I'd like to explore next — [Wave Name]:** [1-2 sentences on why this matters for the presentation]
```

### After each wave (Wave Wrap-Up)

```
**What I gathered from [Wave Name]:**
- [Key decision 1]
- [Key decision 2]

**Updated understanding:** [2-4 sentences — revised mental model]
```

### Recommended-Answer Principle

Every interview question carries the agent's best guess grounded in evidence already gathered (content from Phase 1, presentation purpose, audience). Users confirm or correct — they don't draft from scratch.

Phrasing template: "Based on your [purpose/audience/content], I'd suggest [X] — does this resonate?"

With AskUserQuestion: the recommended option gets "(Recommended)" appended.

---

## Wave 1: Narrative Foundation

### Interview Questions

Ask via AskUserQuestion (batch up to 4 questions per call):

**Question 1: Audience**

- Header: "Audience"
- Question: "Who is your audience, and what do they already know about this topic?"
- Options:
  - "Executives / decision-makers" — Limited time, care about outcomes and business impact
  - "Technical peers" — Deep domain knowledge, care about implementation details
  - "Mixed / general audience" — Varying backgrounds, need accessible framing
  - "External / clients" — Need to build trust and credibility

**Question 2: Core Message**

- Header: "Message"
- Question: "If the audience remembers one thing from this presentation, what should it be?"
- Options:
  - Agent provides 2-3 recommended options based on the content gathered so far, each as a concise sentence
  - The user can select "Other" to type their own

**Question 3: Narrative Arc**

The agent recommends a narrative structure based on the presentation purpose (gathered in Phase 1 or inferred from context). The agent uses presentation design framework knowledge internally but NEVER names frameworks to the user.

- Header: "Structure"
- Question: "How should the presentation flow?"
- Options (agent selects 3-4 relevant options and recommends one):
  - "Lead with the conclusion" — State the key point upfront, then support with evidence (best for executive/decision-maker audiences)
  - "Build to a climax" — Start with context, build tension, deliver the payoff (best for conference talks, storytelling)
  - "Problem → Solution" — Present the challenge, then show how to solve it (best for pitch decks, proposals)
  - "Teach step by step" — Progressive learning, each section builds on the last (best for tutorials, workshops)

Internal mapping (not shown to user):

- "Lead with the conclusion" → Minto Pyramid
- "Build to a climax" → Duarte Sparkline / Hero's Journey
- "Problem → Solution" → SCR (Situation-Complication-Resolution)
- "Teach step by step" → Three-Act Structure with progressive disclosure

**Question 4: Emotional Journey**

- Header: "Journey"
- Question: "What emotional arc should the audience experience?"
- Options:
  - "Confident → Excited" — Start with credibility, build to an energizing vision
  - "Curious → Convinced" — Hook with a question or mystery, resolve with evidence
  - "Concerned → Relieved" — Present a problem the audience feels, then resolve it
  - "Calm → Inspired" — Steady introduction, build to an emotional or aspirational close

### Visual Checkpoint: Storyboard Overview

After Wave 1 interview questions are answered, generate a self-contained HTML storyboard:

**Output**: `~/.claude/presentations/[name]/.brainstorm/storyboard.html`

**Specification**:

```html
<!-- Storyboard Overview -->
<!-- Self-contained HTML, inline CSS, no external dependencies except Google Fonts -->
<style>
  @import url("https://fonts.googleapis.com/css2?family=Balsamiq+Sans&display=swap");
  :root {
    --card-bg: #f5f5f5;
    --card-border: #ddd;
    --annotation-color: #888;
    --highlight: #4a90d9;
  }
  body {
    font-family: "Balsamiq Sans", cursive;
    background: #fff;
    padding: 2rem;
  }
  .storyboard {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
  }
  .slide-card {
    aspect-ratio: 16/9;
    background: var(--card-bg);
    border: 2px solid var(--card-border);
    border-radius: 8px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
  }
  .slide-number {
    font-size: 0.75rem;
    color: var(--annotation-color);
  }
  .slide-title {
    font-size: 1rem;
    font-weight: bold;
  }
  .slide-annotation {
    font-size: 0.7rem;
    color: var(--highlight);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .flow-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--annotation-color);
    font-size: 1.5rem;
  }
</style>
```

- CSS Grid of mini-slides showing narrative arc
- Each card: 16:9 aspect ratio, slide number, title, narrative annotation (e.g., "HOOK", "TENSION", "EVIDENCE", "RESOLUTION", "CALL TO ACTION")
- Gray boxes with Balsamiq Sans font for wireframe aesthetic
- Flow annotations between cards showing the narrative arc

### Dual-Channel Visual Feedback

Open the storyboard for review using the dual-channel feedback flow (see [Dual-Channel Feedback](#dual-channel-visual-feedback-flow) section below).

AskUserQuestion guided prompts for Wave 1:

**Question: Storyboard Review**

- Header: "Storyboard"
- Question: "How does this narrative flow feel? Focus on: Does the opening hook the audience? Does the pacing feel right? Is the ending strong enough?"
- Options:
  - "Looks good, move on" — Narrative structure works
  - "Adjust pacing" — Some sections need more or fewer slides
  - "Change structure" — The overall narrative arc needs rethinking
  - "Adjust content" — Some slides need different content focus

### Update brainstorm-notes.md

After feedback is incorporated, write or update `~/.claude/presentations/[name]/.brainstorm/brainstorm-notes.md`:

```markdown
---
presentation: [name]
status: wave-1-complete
last_updated: [ISO timestamp]
speaker_notes: false
---

## Narrative (Wave 1)

- audience: [description from Q1]
- core_message: [from Q2]
- framework: [internal framework name — NOT shown to user]
- arc: [emotional journey from Q4]
- slide_count: [estimated from storyboard]
- storyboard_html: ~/.claude/presentations/[name]/.brainstorm/storyboard.html
```

---

## Wave 2: Slide-Level Design

### Interview Questions

**Wave Preamble**: Present Context-Sharing Protocol summary of Wave 1 decisions before asking.

For each slide identified in the storyboard, the agent proposes content assignment and layout. Present the full slide plan, then ask:

**Question 1: Slide Plan**

- Header: "Slides"
- Question: "Here's the proposed content for each slide. Does this distribution work?"
- Options:
  - "Looks good (Recommended)" — Content assignments match my intent
  - "Redistribute content" — Some slides have too much or too little
  - "Add/remove slides" — The slide count needs adjusting

**Question 2: Engagement Moments**

The agent identifies 3-5 slides where auto-animate, complex fragments, or interactive elements would have maximum narrative impact.

- Header: "Animation"
- Question: "I've identified [N] key moments where animation would enhance the story: [list]. Should I plan animations for these?"
- Options:
  - "Yes, those moments (Recommended)" — Animate the identified key moments
  - "Fewer animations" — Only animate the most impactful 1-2 moments
  - "More animations" — Add engagement elements to additional slides
  - "No animations" — Keep it simple, no progressive disclosure or auto-animate

**Question 3: Data Visualization** (only if content includes data)

- Header: "Data"
- Question: "How should data be presented?"
- Options:
  - "Clean charts (Recommended)" — CSS charts for key metrics, keep it visual
  - "Numbers only" — Large stat numbers with context, no charts
  - "Detailed charts" — Include more data points and labels

### Visual Checkpoint: Slide Wireframes

Generate HTML wireframes showing per-slide content placement:

**Output**: `~/.claude/presentations/[name]/.brainstorm/wireframes.html`

**Specification**:

- Individual slide previews at viewport scale using `aspect-ratio: 16/9`
- Eric Meyer wireframe CSS technique: `data-wf` attributes with diagonal gradient X-boxes for placeholder regions
- SVG data URI placeholders for images: `data:image/svg+xml;charset=UTF-8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='300'><rect fill='%23ddd' width='400' height='300'/><text fill='%23999' font-family='sans-serif' font-size='14' x='50%25' y='50%25' text-anchor='middle' dy='.3em'>[Image]</text></svg>`
- Content placement shown with gray boxes and labels
- Animation key moments marked with a highlight border and "ANIMATION" badge
- Each wireframe card includes: slide number, title, layout type label, content zones

### Dual-Channel Visual Feedback

Open wireframes for review. AskUserQuestion guided prompts:

**Question: Wireframe Review**

- Header: "Wireframes"
- Question: "How do these slide layouts look? Focus on: Is content well-distributed? Are the right elements prominent? Do the animation moments make sense?"
- Options:
  - "Looks good, move on" — Layout and content placement works
  - "Adjust layouts" — Some slides need different arrangements
  - "Change content focus" — Different elements should be prominent
  - "Adjust animations" — Different slides should be animation key moments

### Update brainstorm-notes.md

Update the file, adding Wave 2 section:

```markdown
## Slide Plan (Wave 2)

| Slide | Title   | Content Summary | Layout        | Animation Key Moment |
| ----- | ------- | --------------- | ------------- | -------------------- |
| 1     | [title] | [brief content] | [layout type] | No                   |
| 2     | [title] | [brief content] | [layout type] | Yes — [rationale]    |
| ...   | ...     | ...             | ...           | ...                  |

- animation_key_moments:
  - Slide [N]: [rationale — e.g., "Product demo reveal — builds anticipation"]
  - Slide [N]: [rationale]
  - Slide [N]: [rationale]
- data_visualization: [strategy chosen]
- wireframe_html: ~/.claude/presentations/[name]/.brainstorm/wireframes.html
```

Update frontmatter: `status: wave-2-complete`

---

## Wave 3: Visual Direction + Style Preset Selection

### Interview Questions

**Wave Preamble**: Present Context-Sharing Protocol summary of Waves 1-2 decisions.

**Question 1: Mood**

- Header: "Mood"
- Question: "What feeling should the audience have when viewing your slides?"
- Options:
  - "Impressed/Confident" — Professional, trustworthy, this team knows what they're doing
  - "Excited/Energized" — Innovative, bold, this is the future
  - "Calm/Focused" — Clear, thoughtful, easy to follow
  - "Inspired/Moved" — Emotional, storytelling, memorable
- multiSelect: true (can choose up to 2)

**Question 2: Color Direction**

- Header: "Colors"
- Question: "What color direction feels right?"
- Options (agent recommends based on mood selection):
  - "Dark background" — Bold, immersive, modern
  - "Light background" — Clean, open, professional
  - "Warm palette" — Approachable, energetic, inviting
  - "Cool palette" — Calm, sophisticated, trustworthy

**Question 3: Typography Feel**

- Header: "Typography"
- Question: "What typographic personality fits?"
- Options:
  - "Modern/Clean" — Sans-serif, geometric, contemporary
  - "Classic/Elegant" — Serif accents, refined, authoritative
  - "Playful/Creative" — Expressive, personality-driven
  - "Technical/Precise" — Monospace accents, developer-friendly

**Question 4: Imagery Style**

- Header: "Imagery"
- Question: "What visual style for non-text elements?"
- Options:
  - "Abstract shapes" — CSS-generated gradients, geometric patterns
  - "Photography" — Real photos (user provides or agent suggests stock approach)
  - "Illustrations" — Hand-drawn or vector illustration style
  - "Minimal/None" — Typography and whitespace carry the design

### Agent-Curated Style Preset Recommendations

Based on the user's mood, color, typography, and imagery answers, the agent curates a selection of style presets from [references/style-presets.md](style-presets.md). There is no hard cap on the number of recommendations — the agent presents however many are genuinely good matches.

**Mood-to-Preset Mapping** (starting point — agent uses judgment to adjust):

| Mood                | Strong Matches                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------ |
| Impressed/Confident | Bold Signal, Electric Studio, Dark Botanical, Liquid Glass, Bento Box                      |
| Excited/Energized   | Creative Voltage, Neon Cyber, Retro Futura                                                 |
| Calm/Focused        | Notebook Tabs, Paper & Ink, Swiss Modern, Micrographic, Jewel Mono                         |
| Inspired/Moved      | Dark Botanical, Vintage Editorial, Pastel Geometry, Director's Cut, Aurora Glow, Scrapbook |

If the user selected 2 moods, blend recommendations from both sets.

### Visual Checkpoint: Mood Board + Style Preset Preview

Generate an HTML mood board with style preset previews:

**Output**: `~/.claude/presentations/[name]/.brainstorm/moodboard.html`

**Specification**:

- Color palette section: CSS Grid of swatches using CSS custom properties from the recommended presets
- Typography specimens: heading/body font pairings at multiple sizes, loaded via Google Fonts / Fontshare CDN
- Mini-slide previews: 2-3 recommended presets rendered as mini title-slide cards in their full style (colors, fonts, signature elements)
- Each preset card: preset name, brief description, a sample title slide in that style
- If the user provided images in Phase 1 and a logo was identified, embed it (base64) into each preset preview

### Dual-Channel Visual Feedback

Open mood board for review. AskUserQuestion guided prompts:

**Question: Style Selection**

- Header: "Style"
- Question: "Which style direction resonates? Browse the mood board to see each option in action."
- Options:
  - "[Recommended Preset 1] (Recommended)" — [Brief description]
  - "[Recommended Preset 2]" — [Brief description]
  - "[Recommended Preset 3]" — [Brief description]
  - "Mix elements" — Combine aspects from different presets

If "Mix elements", ask for specifics.

### Opt-In Speaker Notes

After style selection, ask:

**Question: Speaker Notes**

- Header: "Notes"
- Question: "Would you like speaker notes generated for each slide? These provide talking points you can reference during the presentation."
- Options:
  - "Yes, generate notes (Recommended)" — Each slide gets concise talking points based on the narrative
  - "No notes" — Slides only, no speaker notes

### Update brainstorm-notes.md

Update the file, adding Wave 3 section:

```markdown
## Visual Direction (Wave 3)

- style_preset: [selected preset name]
- mood: [mood selection(s)]
- color_direction: [dark/light/warm/cool]
- typography_feel: [modern/classic/playful/technical]
- imagery_style: [abstract/photography/illustrations/minimal]
- mood_board_html: ~/.claude/presentations/[name]/.brainstorm/moodboard.html
```

Update frontmatter: `status: complete`, `speaker_notes: true|false`

---

## Soft Nudge After 2 Feedback Rounds

After 2 rounds of feedback on any visual checkpoint (crit reviews or AskUserQuestion iterations), the agent suggests proceeding:

**Question: Continue?**

- Header: "Progress"
- Question: "We can refine further during generation — ready to move on?"
- Options:
  - "Move on (Recommended)" — Proceed to the next wave or generation
  - "One more round" — I want to iterate again on this checkpoint

This is a soft nudge, not a hard cap. The user can always choose to continue iterating.

---

## Exit Synthesis

After all three waves complete (or after the user chooses to proceed with a partial brainstorm), present a final synthesis:

```
**Presentation plan summary:**
- Narrative: [framework description, not name] with [N] slides
- Key animation moments: [list of 3-5 slides]
- Visual direction: [preset name] — [1-sentence aesthetic summary]
- Speaker notes: [Yes/No]
- Ready to proceed to Phase 3 (Generation)?
```

**Question: Proceed**

- Header: "Next"
- Question: "Ready to generate the presentation?"
- Options:
  - "Generate presentation (Recommended)" — Proceed to Phase 3 with these decisions
  - "Revisit narrative" — Go back to Wave 1 decisions
  - "Revisit visual direction" — Go back to Wave 3 decisions

---

## Dual-Channel Visual Feedback Flow

This flow applies at every visual checkpoint (storyboard, wireframes, mood board).

### Step 1: Detect crit availability

```bash
command -v crit >/dev/null 2>&1
```

### Step 2a: Crit path (crit installed)

1. Generate HTML mockup → write to `~/.claude/presentations/[name]/.brainstorm/[mockup].html`
2. Open in crit preview:
   ```bash
   crit preview ~/.claude/presentations/[name]/.brainstorm/[mockup].html
   ```
3. Ask guided questions via AskUserQuestion (see wave-specific prompts above)
4. Read crit review JSON to incorporate pin-comment feedback:
   ```bash
   # Review key = sha256(cwd + "\0preview\0" + absolute_path)[:12]
   # Review file at ~/.crit/reviews/<key>/review.json
   ```
5. If pin comments exist, address each one:
   - Read `dom_anchor.css_selector` and `dom_anchor.accessible_name` to identify the element
   - Read `dom_anchor.outer_html` for context on what the user is commenting on
   - Make the requested change to the HTML mockup
   - Reply via CLI: `crit comment --reply-to <comment_id> --author 'Claude Code' '<description of change>'`
6. Update HTML mockup on disk
7. Re-open in crit preview (triggers SSE update for the user)
8. Repeat from step 3 until the user is satisfied (soft nudge after 2 rounds)

### Step 2b: Browser fallback (crit NOT installed)

1. Generate HTML mockup → write to disk
2. Open in default browser:
   ```bash
   open ~/.claude/presentations/[name]/.brainstorm/[mockup].html
   ```
3. Ask guided questions via AskUserQuestion (same wave-specific prompts)
4. Iterate based on AskUserQuestion responses (no pin-comment granularity)

---

## brainstorm-notes.md Contract

The file serves three consumers:

1. **Phase 1 (Content Discovery) — Smart Dedup**: When Phase 2 runs before Phase 1 (content-routing case), Phase 1 reads `brainstorm-notes.md` and skips questions already answered. Specifically:
   - If `audience` is set → skip Phase 1 audience questions
   - If `core_message` is set → skip Phase 1 messaging questions
   - If `slide_count` is set → skip Phase 1 slide count question
   - If the Slide Plan table exists → skip Phase 1 outline confirmation

2. **Phase 3 (Generation) — Creative Brief**: The agent reads `brainstorm-notes.md` and:
   - Uses `framework` + `arc` to structure the narrative outline
   - Uses the Slide Plan table for per-slide content assignment
   - Uses `animation_key_moments` to plan fragments and auto-animate
   - Uses `style_preset` to select CSS variables and signature elements
   - Uses `speaker_notes` flag to decide whether to generate notes
   - Has creative latitude over: animations, transitions, visual flourishes, layout details, and aesthetic enhancements NOT specified in the brainstorm notes

3. **Session Resume — Human-Readable State**: The `status` field in frontmatter indicates completion progress. The file is plain markdown readable by both agents and humans.

### Full Schema

```markdown
---
presentation: [name]
status: wave-1-complete | wave-2-complete | complete
last_updated: [ISO 8601 timestamp]
speaker_notes: true | false
---

## Narrative (Wave 1)

- audience: [audience description]
- audience_knowledge: [what they already know]
- core_message: [single sentence]
- framework: [internal framework name — NEVER shown to user]
- arc: [emotional journey description]
- slide_count: [number]
- storyboard_html: [absolute path to storyboard HTML]

## Slide Plan (Wave 2)

| Slide | Title   | Content Summary | Layout | Animation Key Moment |
| ----- | ------- | --------------- | ------ | -------------------- |
| 1     | [title] | [brief]         | [type] | No                   |
| 2     | [title] | [brief]         | [type] | Yes — [rationale]    |

- animation_key_moments:
  - Slide [N]: [rationale]
  - Slide [N]: [rationale]
  - Slide [N]: [rationale]
- data_visualization: [strategy]
- wireframe_html: [absolute path to wireframes HTML]

## Visual Direction (Wave 3)

- style_preset: [preset name from style-presets.md]
- mood: [mood selection(s)]
- color_direction: [dark/light/warm/cool]
- typography_feel: [modern/classic/playful/technical]
- imagery_style: [abstract/photography/illustrations/minimal]
- mood_board_html: [absolute path to mood board HTML]
```

---

## Content-Based Routing Logic

### How It Works

Phase 1 Step 1.1 runs first and asks 5 context questions (purpose, length, content readiness, images, editing). The answer to Question 3 (content readiness) determines routing:

- **"I have a topic only"** → Phase 2 (Brainstorming) runs NEXT, before Phase 1 continues with remaining steps (Step 1.2 image evaluation, outline confirmation). Brainstorming handles both narrative strategy and initial content structuring.
- **"I have rough notes"** or **"I have all content ready"** → Phase 1 completes fully (including Step 1.2), then Phase 2 runs.

### Smart Dedup (Phase 1 reading brainstorm-notes.md)

When Phase 2 runs before Phase 1 (content-routing case), Phase 1 Step 1.1 has already been answered (the 5 context questions ran before Phase 2). When Phase 1 resumes after brainstorming:

1. Read `brainstorm-notes.md` at `~/.claude/presentations/[name]/.brainstorm/brainstorm-notes.md`
2. For each Phase 1 question, check if the brainstorm notes already contain the answer
3. Skip questions that are already answered; only ask questions that add new information
4. Present a summary of carried-forward decisions: "From brainstorming, I'm carrying forward: [audience], [core message], [N slides]. I still need to confirm: [remaining questions]."

---

## Presentation Design Knowledge

The agent internalizes these frameworks and principles to guide brainstorming. CRITICAL: Never name frameworks to the user. Use plain-language descriptions.

### Narrative Structure Frameworks (Internal)

| Framework           | When to Recommend                                     | User-Facing Description                                                 |
| ------------------- | ----------------------------------------------------- | ----------------------------------------------------------------------- |
| Minto Pyramid       | Executive presentations, consulting, internal updates | "Lead with the conclusion, then support with evidence"                  |
| Duarte Sparkline    | Keynotes, inspiring talks                             | "Build to a climax — oscillate between current state and future vision" |
| SCR                 | Problem-solution presentations, pitch decks           | "Present the challenge, then show how to solve it"                      |
| Hero's Journey      | Pitch decks, transformation stories                   | "Take the audience on a journey of change"                              |
| Three-Act Structure | Tutorials, teaching, general purpose                  | "Teach step by step, building on each section"                          |

### Purpose-to-Framework Mapping

| Presentation Purpose      | Primary Recommendation | Alternative            |
| ------------------------- | ---------------------- | ---------------------- |
| Pitch deck                | Minto Pyramid          | SCR                    |
| Conference talk / keynote | Duarte Sparkline       | Hero's Journey         |
| Teaching / tutorial       | Three-Act Structure    | Progressive disclosure |
| Internal presentation     | Minto Pyramid          | SCR                    |

### Visual Storytelling Principles (Internal)

Apply these when recommending slide design and content placement:

- **Tufte's Data-Ink Ratio**: Maximize ink used for actual data; eliminate chartjunk
- **Picture Superiority Effect**: Visuals are remembered better than text — favor images and diagrams over walls of text
- **Gestalt Principles**: Proximity (group related elements), similarity (consistent styling), figure-ground (clear foreground/background)
- **Duarte's Glance Test**: If the audience can't understand the slide's point in ~3 seconds, simplify it

### Anti-Patterns to Steer Away From

During brainstorming, gently guide away from these without lecturing:

1. Text overload / wall of text → suggest splitting across slides or using visuals
2. Cluttered design without clear focal points → suggest visual hierarchy
3. Overcomplicated charts → suggest simplifying to key data points
4. Inconsistent visual language → suggest committing to one style
5. Gratuitous animations → suggest purposeful animation at key moments only
