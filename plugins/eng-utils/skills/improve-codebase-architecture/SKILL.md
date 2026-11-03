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

Produce a refactoring proposal, not code changes. This sits between `/simplify`
and `/c4-architecture`.
Use the `$ARGUMENTS` scope path, or the current directory if none is supplied.
Resolve relative resource paths from the directory containing this loaded `SKILL.md`.

## 1. Understand

If no scope is supplied, use recurring areas in recent commit history to focus exploration.
Read relevant `GLOSSARY.md`, `docs/adr/`, and any existing C4 `workspace.dsl` under
`~/.claude/thoughts/shared/architecture/`. Use domain names from the glossary.
Flag proposals that contradict an ADR, with evidence for reopening the decision.

Spawn `codebase-explorer` for the scope. Ask it to report source paths, line counts,
import relationships, and where understanding requires file-hopping, interfaces expose
implementation complexity, coupled modules resist independent change, or tests miss integration.
Include cases where isolated helper tests miss faults in how callers assemble the behavior.
Classify findings as Scattered Concept, Shallow Module, God Class, Tight Coupling,
Feature Envy, Missing Abstraction, Leaky Abstraction, or Untested Integration Seam.

Measure outgoing dependencies (Ce), incoming dependents (Ca), public methods versus
implementation lines, and files needed to understand a concept. Inspect the relationships;
keyword matches are not dependency counts. Record the scope of each count.
Use task-relevant source bytes when context load matters. Distinguish measurements from
estimates; line-count ratios alone do not establish depth.

Before proposing removal, apply the deletion test: does complexity disappear, or reappear
in callers? For example, a one-line rounding policy shared by two callers can earn its
module; inlining it duplicates policy rather than removing complexity.

## 2. Propose

Rank candidates by observed friction, coupling/change impact, and likely reduction in
files-per-concept. For each, give the cluster and source evidence, why it is coupled,
Ce/Ca and navigation metrics, proposed improvement, dependency category, test impact,
and estimated files-per-concept after refactoring.

Classify dependencies with this matrix:

| Category | Testing and deepening strategy |
| --- | --- |
| In-process | Consolidate related logic and test through the public interface. |
| Local-substitutable | Own storage/query logic; use a local implementation with compatible semantics. |
| Remote-owned | Hide transport behind an interface for the module's needs. |
| External | Mock only required behaviors behind an injected interface; verify the real contract separately. |

Do not invent adapters for hypothetical uses. A production adapter plus a needed in-memory
test adapter can justify an interface. Propose boundary tests that replace redundant tests
of now-internal pieces without losing coverage. Distinguish public-contract tests from
focused internal tests; internal seams need not become public interfaces.

Present candidates using section 5, recommended first. Each card includes a Mermaid
flowchart of the current module cluster, measured labels, and coupling arrows.
Ask which candidates to explore, allow multiple selections and **Skip refactor**.
Exit without a proposal if skipped. Do not drop candidates to fit a choice tool;
show the full numbered list and accept typed selections when necessary.

## 3. Design

Before spawning designers, show constraints (types, callers, performance, errors),
dependencies with categories, and an illustrative code sketch, not a chosen design.

Create an explicit agent contract per
`${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md`.

Spawn parallel general-purpose agents with different interface constraints, such as
minimal surface, extensibility, common-caller simplicity, or ports and adapters.
Choose the number and constraints for the problem. Give each source paths, coupling
evidence, dependency categories, constraints, and complexity to hide.
Require interface signatures, caller examples, hidden complexity, dependency strategy,
and trade-offs from each agent.
If an agent delivers no result, follow up, then retry once. If still missing, report the
gap; do not substitute self-evaluation for an independent design.

Compare designs on interface simplicity, depth, correct use versus misuse, and testing.
Recommend one or a justified hybrid. Present each using section 5, with its interface,
example, trade-offs, and side-by-side Current/Proposed Mermaid flowcharts.
Reuse the current topology; show proposed interface boundaries with callers outside.
Ask the user to choose a design or hybrid. If all agents converge, state the convergence
and proceed to confirmation, allowing the user to override it.

## 4. Document

Ask whether to **Proceed**, **Adjust interface**, or **Adjust diagrams**.
Revise and ask again until the user confirms. Write the proposal to
`~/.claude/thoughts/shared/improve-codebase-architecture-proposals/YYYY-MM-DD-description.md`,
creating the directory if needed. Use this structure:

- Frontmatter: `date: YYYY-MM-DD`, `type: refactor-proposal`, `repository: <name>`, `status: draft`.
- **Executive Summary**: problem, recommendation, expected improvement.
- **Problem Summary**: friction classifications, coupling metrics, navigation impact.
- **Architecture Comparison**: current and proposed PlantUML C4 Component diagrams,
  then what moves, merges, or extracts, and why.
- **Proposed Solution**: each module's responsibilities, hidden complexity, public
  interface and rationale, dependency strategy, replacement boundary tests and test removals.
- **Honest Assessment**: pros, cons/limitations, risks/unknowns, and complexity moved rather than removed.
- **Operational Boundaries**: module-specific **Always do**, **Ask first**, and **Never touch** rules.
- **Next Steps**: implementation planning using the proposal.

For C4 syntax, read `../c4-architecture/references/c4-formats.md` when writing the diagrams.
Optionally include recommended CLAUDE.md updates and before/after navigation metrics
when the proposal changes them. Present the file path, key findings, and planning handoff.

## 5. Presenting Candidates and Designs

Prefer HTML reviewed through Crit. Use inline styles and Mermaid from a CDN, without a
build step. Write candidate and design reports respectively to
`/tmp/improve-arch-candidates-YYYY-MM-DD.html` and `/tmp/improve-arch-designs-YYYY-MM-DD.html`.
Use compact flowcharts, grouping modules by package or layer. Mark friction sources red,
affected modules orange, unchanged dependencies gray, and proposed boundaries green.
Quote labels to avoid Mermaid parser errors. A minimal setup:

```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad: true, theme: "default"});</script>
<pre class="mermaid">
flowchart LR
  A["Order caller"] -->|"calls"| B["Pricing policy (1 entry point)"]
</pre>
```

Check whether `crit` is available. If crit is not found, or if the invocation context
cannot open an interactive browser, use the fallback below.
Otherwise run `crit preview <html-file>`. Find its session ID with `crit status --json`,
matching the report path. Ask the user to comment with selections, rejections, or combinations. After they return,
read `crit comments --session <id> --json`; interpret selections and clarify ambiguity
with `AskUserQuestion`. Remove temporary reports after reading the feedback.

Fallback: render numbered candidates or designs in chat, then use `AskUserQuestion`.
For candidates, use multiple selection and include **Skip refactor**; for designs,
include the recommendation, alternatives, and **Hybrid**. Accept custom input.
