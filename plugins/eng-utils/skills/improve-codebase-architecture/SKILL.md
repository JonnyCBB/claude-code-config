---
name: improve-codebase-architecture
description: >
  Explore a codebase for architectural friction (scattered concepts, shallow modules,
  tight coupling), quantify issues with coupling metrics, design multiple interface
  alternatives via parallel agents, and produce a proposal document with old/new
  architecture diagrams and honest pros/cons. Proposal-only — never makes code changes.
  Use when asked to "improve codebase architecture", "refactor architecture",
  "improve codebase structure", "deepen modules", "reduce coupling", "make code more
  navigable", or when /code-review repeatedly surfaces structural issues. Invocable as
  /improve-codebase-architecture [scope-path].
argument-hint: "[scope-path]"
---

# Improve Codebase Architecture

Identify structural problems at the module/component level and produce an architectural
refactoring proposal. This skill operates between code-level simplification (/simplify) and
system-level documentation (/c4-architecture). It never makes code changes — all output
is a proposal document that feeds into `/create-plan-tdd`.

## Argument Parsing

Parse `$ARGUMENTS` for:

- **Scope path**: directory or file to focus exploration on (e.g., `src/services/`)
- **Default**: current working directory

## Phase 1: Understand (read-only exploration)

Explore the codebase organically, noting where understanding breaks down. The friction
you encounter IS the signal.

1. **Spawn `codebase-explorer`** to navigate the scoped directory. Instruct it to:
   - Note where understanding one concept requires bouncing between many files
   - Note where modules are so shallow that the interface is nearly as complex as the implementation
   - Note where tightly-coupled modules create integration risk
   - Note which parts are untested or hard to test
   - Report back with file paths, line counts, and import relationships

2. **Read architectural context** if available:
   - Check `~/.claude/thoughts/shared/architecture/` for a C4 workspace.dsl
   - If found, read it for structural context (service boundaries, component relationships)
   - If not found, skip — the exploration provides sufficient context

3. **Classify friction points**: Read `references/friction-patterns.md` and classify each
   discovered issue by pattern (Scattered Concept, Shallow Module, God Class, Tight
   Coupling, Feature Envy, Missing Abstraction, Leaky Abstraction, Untested Integration Seam).

4. **Compute quantitative signals** (see Quantitative Signals section in
   `references/friction-patterns.md`):
   - Files-per-concept: `grep -rl "ConceptName" <scope> | wc -l`
   - Module depth: count public methods vs implementation lines
   - Import/dependency count per module: `grep -c "^import" <file>`
   - Reverse references: `grep -rl "ModuleName" <scope> | wc -l` (estimates Ca)

## Phase 2: Propose (interactive)

Present refactoring candidates to the user for selection.

1. **Rank candidates** by composite score:
   - Friction severity (qualitative — how confusing/scattered?)
   - Coupling risk (Ce/Ca — high Ce + low Ca = safe to change; high Ca = high impact)
   - AI navigability impact (files-per-concept reduction potential)

2. **Build candidate details**. For each candidate gather:
   - **Cluster**: which modules/concepts are involved
   - **Why they're coupled**: shared types, call patterns, co-ownership of a concept
   - **Dependency category**: classify using `references/dependency-categories.md`
     (In-process / Local-substitutable / Remote-owned / External)
   - **Coupling metrics**: Ce, Ca, files-per-concept counts
   - **Test impact**: what existing tests would be replaced by boundary tests
   - **Readability improvement**: estimated files-per-concept after refactoring

3. **Present candidates via HTML+crit or fallback to AskUserQuestion.** Follow the
   presentation procedure in the "Presenting Candidates and Designs" section below.

   For the HTML report, structure each candidate as a card with the details from step 2.
   Rank-order them with the recommended candidate first. Each card must include a
   **Mermaid flowchart diagram** (5-8 nodes) showing the friction cluster's module
   topology and coupling arrows:
   - Nodes = modules involved (include line counts or key metrics in the label)
   - Arrows = coupling relationships, labeled with the type (e.g., "30 accesses",
     "duplicate assembly", "shared type")
   - Color-code with `classDef`: red (`fill:#fee2e2,stroke:#dc2626`) for god modules /
     primary friction sources, orange (`fill:#ffedd5,stroke:#ea580c`) for affected
     modules, gray (`fill:#f3f4f6,stroke:#6b7280`) for external / unchanged dependencies
   - Use `subgraph` to group modules by package or layer

   For the AskUserQuestion fallback, use:
   - `question`: "Which refactoring candidate(s) should we explore further?"
   - `header`: "Candidates" (max 12 chars)
   - `multiSelect: true`
   - `options`:
     - label: "Candidate 1 (Recommended)" — description: "[Cluster name] — [friction pattern], spans N files; [dependency category]"
     - label: "Candidate 2" — description: "[Cluster name] — [friction pattern], spans N files; [dependency category]"
     - label: "Candidate 3" — description: "[Cluster name] — [friction pattern], spans N files; [dependency category]"
     - label: "Skip refactor" — description: "None worth pursuing right now; exit without proposal"

   **More than 4 candidates**: the AUQ tool caps options at 4. If you have 5+ candidates
   and are using the AUQ fallback, render the full numbered list to the UI first, then use
   a free-form prompt: "Which numbers (e.g., 1, 3, 5)?" Do not drop candidates to fit the tool.

   **Auto-"Other"**: the AUQ tool surfaces an "Other" option automatically — do not add one manually. The user can use it to describe a custom selection in free text.

4. **Proceed to Phase 3** with the selected candidate(s). If the user selected "Skip refactor", exit the skill without generating a proposal.

## Phase 3: Design (parallel agents)

For the selected candidate(s), design multiple radically different interfaces.

1. **Frame the problem space and render it to the user _before_ spawning agents.** This gives the user something to read while the parallel agents work. Output:
   - **Constraints** any new interface must satisfy (input/output types, callers, performance budgets, error semantics)
   - **Dependencies** the interface must rely on, with their dependency category (in-process / local-substitutable / remote-owned / external — see `references/dependency-categories.md`)
   - **A rough illustrative code sketch** to ground the constraints. This is _not_ a proposal — it shows the shape of the problem so the agents (and the user) have a shared starting point.

   Render this frame to the conversation UI immediately. Then proceed to step 2.

2. **Agent verification**: create an explicit agent contract per
   `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md`.

3. **Spawn parallel `general-purpose` agents**, each with a different interface constraint.

   **Agent delivery resilience**: Subagents may go idle without delivering results (known Claude Code issue). If an agent sends an `idle_notification` without content: (1) prompt it via SendMessage using its agent ID (not name), (2) if still no delivery, respawn once, (3) if respawn fails, gather data directly or document the gap. Never self-evaluate as a substitute for an independent agent.
   Choose the number and constraints appropriate to the problem. Example constraints:
   - "Minimize the interface — aim for 1-3 entry points max"
   - "Maximize flexibility — support many use cases and extension"
   - "Optimize for the most common caller — make the default case trivial"
   - "Design around the ports & adapters pattern" (when cross-boundary deps exist)

   Each agent receives a technical brief with: file paths, coupling details, dependency
   category, what complexity is being hidden. Each outputs:
   - Interface signature (types, methods, params)
   - Usage example showing how callers use it
   - What complexity it hides internally
   - Dependency strategy (from `references/dependency-categories.md`)
   - Trade-offs

4. **Present designs via HTML+crit or fallback to AskUserQuestion.** Follow the
   presentation procedure in the "Presenting Candidates and Designs" section below.

   For the HTML report, present each design as a section with its interface signature,
   usage example, trade-offs, and a **side-by-side "Current → Proposed" Mermaid diagram
   pair** in a CSS flexbox row (`display: flex; gap: 2rem`):
   - **Current** (left): the friction cluster as-is — reuse the topology from Phase 2,
     possibly slightly expanded to show callers
   - **Proposed** (right): the new module structure with the interface boundary visible
     as a `subgraph` and callers outside it
   - Same color scheme as Phase 2, plus green (`fill:#dcfce7,stroke:#16a34a`) for new
     clean boundaries / interfaces
   - Keep each side to 8-12 nodes — this is a sketch, not the full C4 from Phase 4

   Also include a prose comparison evaluating:
   - Interface simplicity (fewer methods, simpler params)
   - Depth (small interface hiding significant complexity = good)
   - Ease of correct use vs ease of misuse
   - Testing implications

   Include an opinionated recommendation naming which design is strongest and why. If
   elements from different designs combine well, propose a hybrid.

   For the AskUserQuestion fallback, first render the designs and comparison in prose,
   then use:
   - `question`: "Which interface design fits best, or should we combine?"
   - `header`: "Design" (max 12 chars)
   - `options`:
     - label: "Design A (Recommended)" — description: "[1-sentence tradeoff summary]"
     - label: "Design B" — description: "[1-sentence tradeoff summary]"
     - label: "Hybrid" — description: "Combine elements; I'll describe which parts in 'Other'"

   **Convergence shortcut**: if all parallel design agents converge on a single design,
   skip the presentation entirely and proceed to Phase 4 with that design as the chosen
   one. State the convergence in prose so the user can override if desired.

## Phase 4: Document (proposal output)

Generate the architectural proposal document. This skill never makes code changes.

1. **Confirm the proposal direction** via `AskUserQuestion`:
   - `question`: "Ready to write the proposal document with this interface?"
   - `header`: "Proposal" (max 12 chars)
   - `options`:
     - label: "Proceed (Recommended)" — description: "Generate the proposal at ~/.claude/thoughts/shared/improve-codebase-architecture-proposals/"
     - label: "Adjust interface" — description: "Revise method signatures or dependency strategy first"
     - label: "Adjust diagrams" — description: "Tweak the current-vs-proposed C4 sketches before writing"

   If the user picks an "Adjust" option (or "Other" with their own ask), revise per their feedback and re-ask via `AskUserQuestion` until they choose "Proceed". Then continue with step 2 below.

2. **Generate proposal** using `references/proposal-template.md`:
   - Problem Summary with friction pattern classifications and coupling metrics
   - Architecture Comparison with PlantUML C4 diagrams (current vs proposed)
   - Proposed Solution with module responsibilities, interface design, dependency strategy,
     and testing strategy
   - Honest Assessment with pros, cons/limitations, and risks/unknowns

3. **Create output directory**: `mkdir -p ~/.claude/thoughts/shared/improve-codebase-architecture-proposals/`

4. **Write proposal** to `~/.claude/thoughts/shared/improve-codebase-architecture-proposals/YYYY-MM-DD-description.md`

5. **Present summary** to user with the file path and key findings.

6. **Next step**: "To implement this proposal, run `/create-plan-tdd` with the proposal
   document path."

## Presenting Candidates and Designs

Phase 2 and Phase 3 both present structured content for the user to review and choose from.
The preferred presentation is an HTML report reviewed via `crit`; the fallback is the
chat-rendered prose + `AskUserQuestion` flow described inline in each phase.

### HTML+crit presentation (preferred)

1. **Generate a self-contained HTML file** with **Mermaid.js flowchart diagrams** — see
   [`references/mermaid-guide.md`](references/mermaid-guide.md) for CDN setup, syntax
   rules, color palette, and the side-by-side layout pattern. The HTML must be fully
   self-contained (inline styles, CDN script tags only — no build step).

2. **Write the HTML** to a temp file:
   - Phase 2: `/tmp/improve-arch-candidates-YYYY-MM-DD.html`
   - Phase 3: `/tmp/improve-arch-designs-YYYY-MM-DD.html`

3. **Check crit availability**: run `which crit` via Bash. If crit is not found, or if
   the invocation context is non-interactive (e.g., called from `/orchestrate-feature-dev`
   with `--non-interactive`), skip to step 7 (fallback).

4. **Open the report for review**: run `crit preview <html-file>`. This opens the HTML
   in the user's browser with crit's commenting overlay.

5. **Tell the user** to review the report and leave comments indicating their selection.
   Comments are free-form — there is no fixed marker syntax. Examples of valid comments:
   - "This one" or "Yes" on a candidate card
   - "Not this" or "Too risky" on a candidate to reject
   - "Combine A's interface with B's dependency strategy"
   - A general comment at the top like "Go with candidate 2 and 4"

6. **Read the user's selection**: run `crit comments --json <html-file>` after the user
   returns. Interpret the comments to determine which candidate(s) or design the user
   chose. If the comments are ambiguous, ask a clarifying question in chat. Clean up the
   temp HTML file after reading.

7. **Fallback (AskUserQuestion)**: if crit is unavailable or the context is non-interactive,
   render the content as numbered prose in the conversation UI, then use the
   `AskUserQuestion` call described in the relevant phase above.

## Reference Files

Read these files when the workflow reaches their relevant phase:

- **[`references/friction-patterns.md`](references/friction-patterns.md)** — Read in
  Phase 1 when classifying friction points and computing quantitative signals. Contains
  8 friction patterns with detection heuristics and severity thresholds, plus 3
  navigability metrics (files-per-concept, context budget, module depth).

- **[`references/dependency-categories.md`](references/dependency-categories.md)** — Read
  in Phase 2 when classifying dependency types for each candidate. Contains 4 categories
  (in-process, local-substitutable, remote-owned, external) with testing strategies and
  before/after examples.

- **[`references/mermaid-guide.md`](references/mermaid-guide.md)** — Read in Phase 2 and
  Phase 3 when generating HTML presentations. Contains Mermaid.js CDN setup, flowchart
  syntax rules (including the critical double-quoting rule), the color palette for
  friction categories, and the side-by-side layout pattern for design comparisons.

- **[`references/proposal-template.md`](references/proposal-template.md)** — Read in
  Phase 4 when generating the output document. Contains the full proposal template with
  YAML frontmatter, section structure, PlantUML C4 syntax guide, and navigability
  metrics guide.
