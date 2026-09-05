---
name: context-and-skills-standards
description: >
  Evidence-based standards for writing context files (CLAUDE.md, AGENTS.md) and skills
  (SKILL.md). Use when: (1) writing or reviewing a CLAUDE.md or AGENTS.md, (2) creating
  or reviewing a skill file, (3) deciding whether a new skill or instruction is warranted,
  (4) evaluating if an existing instruction is earning its token cost. Based on
  "Evaluating AGENTS.md" (arxiv 2602.11988), "SkillsBench" (arxiv 2602.12670), and
  55+ corroborating sources. Compatible with skill-creator (this skill provides principles;
  skill-creator provides the creation workflow).
---

# Context and Skills Standards

Evidence-based guidelines for what to put in context files and skills. The research consensus:
**what you put in matters far more than having them at all.** Single-pass LLM-generated
content averages −1.3pp (SkillsBench) because models generate imprecise procedures. Curated,
procedural skills with eval-driven iteration improve performance by +16.2pp on average.

## Core Principles

**P1 — Every instruction has an additive cost** _(Very High evidence)_
Models faithfully follow all instructions, consuming tokens and reasoning steps. Unnecessary
instructions actively harm performance — instruction-following degrades as total instruction
count grows (context rot, prompt underspecification). Litmus test: "Would removing this
cause the model to make mistakes?"

**P2 — Provide only what the model doesn't know** _(Very High evidence)_
Proprietary/new frameworks absent from training data: up to +51.9pp gain. Standard SE
patterns: only +4.5pp, with most SE skills showing zero improvement (SWE-Skills-Bench).
Redundant with existing docs: −2 to −3%. Focus skill effort
on proprietary systems where the model has no training coverage. Before writing, ask: "Does
the model already know this from training or from files it can read?"

**P3 — Procedural beats declarative** _(High evidence)_
Describe HOW to do things (step sequences, workflows), not WHAT things are (overviews,
architecture docs). Procedural workflows show +25% correctness improvement over declarative
descriptions (Augment Code AuggieBench — directional, vendor benchmark). One working code
example is worth more than three paragraphs of explanation.

**P4 — Moderate length is optimal; comprehensive hurts** _(Very High evidence)_
Detailed/compact instructions: +17–19pp. Comprehensive documentation: −2.9pp. Anthropic
targets: CLAUDE.md under 200 lines, SKILL.md under 500 lines. Auto-compaction retains the
first 5,000 tokens per skill (25,000 total budget). These are empirical targets, not hard
limits — optimize signal-to-noise ratio, but respect the targets as practical ceilings.

**P5 — 2–3 focused modules is optimal** _(High evidence)_
1 module: +17.8pp. 2–3 modules: +18.6pp (best). 4+ modules: +5.9pp. Excessive skill count
creates cognitive overhead and conflicting guidance.

**P6 — External feedback is essential; single-pass self-generation fails** _(Very High evidence)_
Curated skills: +16.2pp. Single-pass self-generated skills: −1.3pp (SkillsBench). The key
differentiator is external feedback — Trace2Skill achieves +57.65pp with multi-agent
generation using external feedback, while self-feedback alone induces recursive drift
(SkillLearnBench). The recommended pattern: eval-driven iteration with human review, as
skill-creator implements. LLMs can draft skills effectively when paired with evaluation loops
and human oversight; the risk is single-pass generation without external validation.

**P7 — Always-present vs lazy-loaded depends on usage frequency** _(Medium evidence)_
Frequently needed, broadly applicable knowledge → CLAUDE.md (always-present). Specialized,
occasional knowledge → skills (lazy-loaded). Note: 56% of skills were never invoked in one
study — lazy-loading can cause knowledge to be missed for frequently-needed content. See P9
for description budget constraints that affect skill visibility.

**P8 — Skills can hurt; test for regression** _(Very High evidence)_
19% of tasks showed performance degradation with skills (SkillsBench). In SE specifically,
39/49 skills showed zero improvement and average gain was only +1.2% (SWE-Skills-Bench).
Gains further degrade as evaluation settings become more realistic (How Well Do Skills Work
in the Wild). Skills hurt most when the model already handles the task well or when
procedures conflict with optimal paths. Test before deploying — baseline first, then with
skill.

**P9 — Descriptions are the activation mechanism** _(High evidence)_
Skill descriptions determine whether a skill triggers. Without descriptions, routing accuracy
drops 31–44pp (SkillRouter). Write descriptions in third person with action verbs and concrete
use cases. Use the `when_to_use` field for activation conditions. Combined description +
when_to_use budget: 1,536 characters (hard limit). Test triggering — description quality
directly determines whether users can find and activate the skill.

**P10 — Match instruction specificity to fragility** _(Medium evidence)_
Use the degrees-of-freedom model: high freedom for creative tasks (text guidance, multiple
valid approaches), low freedom for fragile operations (specific scripts, exact commands).
Explain the WHY behind instructions — prescriptions without rationale invite blind following
or wholesale ignoring (Anthropic best practices, Block Engineering). Think "narrow bridge with
cliffs" (low freedom, exact steps) vs "open field" (high freedom, directional guidance).

---

## Decision Framework: Should I Write This?

Before writing any instruction or skill, answer four questions:

1. **Domain coverage**: Does the model already know this well? Standard coding patterns,
   math, general SE → skip or be minimal. Proprietary systems, new frameworks, company-specific
   processes → high value. (e.g. a bespoke internal platform, scheduler or datastore is high-value domains.)

2. **Redundancy check**: Is this already documented elsewhere the model can read? If yes,
   link or reference it rather than duplicating. Redundant instructions are actively harmful
   (−2 to −3% from redundancy alone).

3. **Regression risk**: Could this instruction hurt tasks the model currently handles correctly?
   If the model already does this well, adding instructions may introduce conflicting procedures.

4. **Activation**: Will this skill trigger when needed? Is the description specific enough to
   route correctly? (Descriptions determine activation — 31–44pp routing drop without them.)

Only write the instruction if you can answer: _"Without this, the model will make a specific,
observable mistake on a real task."_

---

## Instruction Evaluation Checklist

Apply to every instruction before including it:

- [ ] **Necessity**: Would removing this cause the model to make mistakes? (If no → delete)
- [ ] **Novelty**: Does the model already know this from training data? (If yes → delete)
- [ ] **Procedural**: Does it describe HOW, not just WHAT? (If no → rewrite)
- [ ] **Example**: Does it include at least one concrete example or code snippet? (For non-trivial steps)
- [ ] **Non-redundant**: Is this documented elsewhere the model can read? (If yes → link, don't duplicate)
- [ ] **Regression-safe**: Could this conflict with tasks the model handles well? (If yes → test first)
- [ ] **Well-described**: For skills — is the description specific enough to trigger correctly? (Test activation)
- [ ] **Grounded**: Does every proprietary API, schema key, flag, or method named here have at least one hit _outside_ this skill's own files? (Check with code search. If the only hits are the skill's own SKILL.md and references, treat it as fabricated, not stale.)

### Fabricated vs drifted claims

These look identical in a diff and need opposite responses, so separate them before editing.

- **Drifted**: the API existed and has since changed. Fix the specific claim against current ground truth.
- **Fabricated**: the API never existed. Do not patch the flagged line — a skill that invented one API has usually invented others around it, so audit the whole skill against ground truth.

A useful threshold: if 3 of 3 spot-checked technical claims are unfindable outside the skill, stop spot-checking and audit everything.

**Why this check earns its place:** four independent skill audits on a single day each found documented APIs with zero production hits anywhere — `.withDefaultBackendExposureDisabled()` and `.withOnlineResolution()` matched only the experimentation skill's own reference files; `mlplatform.mlflow.init_mlflow` existed nowhere in the codebase; a feature-store `FeatureSpec`/`LabelSpec` surface had no version, past or present; and an indexing skill's entire `index.yaml` schema (`module:`, `team:`, `entity:`, `index:`, `loaders:`) had never existed. An agent following those skills writes code against APIs that cannot work, and the failure surfaces far from the skill that caused it.

**Rule out false "zero trace" before concluding fabrication:** the symbol may be used from a client in another language, live in an archived or unindexed repo, or be generated at build time by codegen or protobuf rather than appearing in source.

### Executable content: run it, don't just read it

Any command or code block a skill embeds is an instruction an agent will follow literally, so review it by running it.

- **Execute every embedded shell block against a real fixture, in every input state it can meet** — empty result, populated result, and the degenerate state (no input at all). Reading catches syntax; execution catches semantics. On one change, an independent expert review of the same text found four defects and still missed two that surfaced immediately on execution: a second block referencing an unassigned variable, and a degenerate input state that reported as a normal one.
- **Each block must be self-contained.** Shell state does not persist between an agent's tool calls, so a variable assigned in one block is gone by the next. If a later step needs a value, have the earlier step record it somewhere durable and read it back — don't assume the variable survives.
- **Check the degenerate case explicitly.** A block that yields "nothing found" must be distinguishable from one that yields "nothing to look at". Collapsing those two is how a check reports success without having checked anything.

### Never restate a number in two places

A limit, cap, threshold or count stated in more than one file will drift. Name one canonical location and make every other mention a pointer to it.

Three stale restatements surfaced in a single change — including one inside a file that same change had already edited, and one that went stale hours later when the value was revised. Orphaned reference files are where this accumulates fastest, so verify every reference file is still reachable from its `SKILL.md`; the unreachable ones are both unread and unmaintained.

### Never cite ephemeral or machine-local artifacts in a distributed skill

A skill that ships in a plugin is read by people who have never seen the author's machine. A
citation they cannot check — a session name, a local run directory, a path under `~/evidence/` — looks
like evidence and functions as decoration. It borrows the credibility of verifiable citations without
earning it, and a reader who tries to follow it learns only that the reference was never meant for
them.

What to cut: session names (`bh3k-charpro-0.21.0`), run IDs with timestamps
(`bh3-component-20260903-201106`), absolute paths to local directories (`~/evidence/...`), and
anything whose only copy lives on one person's filesystem.

What to keep: dates used as change-history markers (`Added 2026-08-28`, `Changed in 0.21.0`) are
fine — they're version history, not artifact citations, and don't require access to anything.
Measured figures are fine when stated as facts (`on a real 132-candidate run, 55 were
NOT_REQUEST_SCOPED`) rather than as pointers to a specific artifact nobody else can open.

The test: could a stranger reading this skill verify the citation? If the answer is "only if they
have access to my machine," remove the citation and keep the fact.

### Comparing two versions of a skill

When testing whether an amendment works, run the old and new instructions against the same fixture rather than asking an agent to judge the text. Four traps, all of which produce a confident wrong answer:

- **Do not ask both arms to produce the artifact that is the intervention.** If the change is "require a coverage report", asking both arms for a coverage report makes both pass and proves nothing.
- **A null result can mean the comparison is shaped wrong, not that the change is unnecessary.** Failure modes that only appear under parallel fan-out, or under a competing instruction, will not reproduce in a single clean run.
- **Read the baseline arm's commentary, not just its score.** A capable baseline often notices the problem anyway; when it independently proposes the change you are testing, that is stronger evidence than the score delta.
- **Attribute results per file.** Multi-file `grep` ordering does not reliably map to the arms, and getting it backwards inverts the conclusion.

---

## Quick Reference: Include vs Exclude

| Include                                 | Exclude                                         |
| --------------------------------------- | ----------------------------------------------- |
| Repository-specific tooling commands    | Standard language conventions the model knows   |
| Proprietary API patterns with examples  | Codebase overviews and directory listings       |
| Non-obvious step sequences              | Architecture descriptions                       |
| Common mistakes you've seen in practice | Things the model currently does correctly       |
| Company-specific processes and naming   | Single-pass LLM-generated content without eval  |
| Known failure modes with fixes          | Generic best practices covered in training data |

---

## Reference Files

Read these files for detailed guidance when:

- **[`references/context-file-guidelines.md`](references/context-file-guidelines.md)** — Writing or
  reviewing a CLAUDE.md or AGENTS.md. Covers instruction economy, anti-patterns, iterative
  refinement process, length targets, and CLAUDE.md vs Skills decision rule.

- **[`references/skill-file-guidelines.md`](references/skill-file-guidelines.md)** — Creating or
  reviewing a SKILL.md or skill package. Covers domain coverage assessment, description
  optimization, skill categories, degrees of freedom, and eval-driven development.

- **[`references/evidence-base.md`](references/evidence-base.md)** — Assessing source quality or
  explaining recommendations to others. Full citation list with confidence levels for all 10
  principles.
