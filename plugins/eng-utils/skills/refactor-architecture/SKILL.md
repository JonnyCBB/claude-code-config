---
name: refactor-architecture
description: >
  Explore a codebase for architectural friction (scattered concepts, shallow modules,
  tight coupling), quantify issues with coupling metrics, design multiple interface
  alternatives via parallel agents, and produce a proposal document with old/new
  architecture diagrams and honest pros/cons. Proposal-only — never makes code changes.
  Use when asked to "refactor architecture", "improve codebase structure", "deepen modules",
  "reduce coupling", "make code more navigable", or when /code-review repeatedly surfaces
  structural issues. Invocable as /refactor-architecture [scope-path].
argument-hint: "[scope-path]"
---

# Refactor Architecture

Identify structural problems at the module/component level and produce an architectural
refactoring proposal. This skill operates between code-level simplification (/tidy) and
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

2. **Present numbered list**. For each candidate show:
   - **Cluster**: which modules/concepts are involved
   - **Why they're coupled**: shared types, call patterns, co-ownership of a concept
   - **Dependency category**: classify using `references/dependency-categories.md`
     (In-process / Local-substitutable / Remote-owned / External)
   - **Coupling metrics**: Ce, Ca, files-per-concept counts
   - **Test impact**: what existing tests would be replaced by boundary tests
   - **Readability improvement**: estimated files-per-concept after refactoring

3. **Do NOT propose interfaces yet.** Ask: "Which of these would you like to explore?"

4. **Wait for user selection** — one or multiple candidates.

## Phase 3: Design (parallel agents)

For the selected candidate(s), design multiple radically different interfaces.

1. **Frame the problem space** (show to user):
   - Constraints any new interface must satisfy
   - Dependencies it must rely on
   - A rough illustrative code sketch to ground the constraints (not a proposal)

2. **Agent verification**: create an explicit agent contract per
   `${CLAUDE_PLUGIN_ROOT}/commands/shared/agent-verification-pattern.md`.

3. **Spawn parallel `general-purpose` agents**, each with a different interface constraint.
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

4. **Present designs sequentially**, then **compare in prose**. Evaluate on:
   - Interface simplicity (fewer methods, simpler params)
   - Depth (small interface hiding significant complexity = good)
   - Ease of correct use vs ease of misuse
   - Testing implications

5. **Give an opinionated recommendation**: which design is strongest and why. If elements
   from different designs combine well, propose a hybrid.

## Phase 4: Document (proposal output)

Generate the architectural proposal document. This skill never makes code changes.

1. **User picks interface** or accepts recommendation.

2. **Generate proposal** using `references/proposal-template.md`:
   - Problem Summary with friction pattern classifications and coupling metrics
   - Architecture Comparison with PlantUML C4 diagrams (current vs proposed)
   - Proposed Solution with module responsibilities, interface design, dependency strategy,
     and testing strategy
   - Honest Assessment with pros, cons/limitations, and risks/unknowns

3. **Create output directory**: `mkdir -p ~/.claude/thoughts/shared/refactor-proposals/`

4. **Write proposal** to `~/.claude/thoughts/shared/refactor-proposals/YYYY-MM-DD-description.md`

5. **Present summary** to user with the file path and key findings.

6. **Next step**: "To implement this proposal, run `/create-plan-tdd` with the proposal
   document path."

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

- **[`references/proposal-template.md`](references/proposal-template.md)** — Read in
  Phase 4 when generating the output document. Contains the full proposal template with
  YAML frontmatter, section structure, PlantUML C4 syntax guide, and navigability
  metrics guide.
