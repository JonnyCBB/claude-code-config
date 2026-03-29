---
name: context-and-skills-standards
description: >
  Evidence-based standards for writing context files (CLAUDE.md, AGENTS.md) and skills
  (SKILL.md). Use when: (1) writing or reviewing a CLAUDE.md or AGENTS.md, (2) creating
  or reviewing a skill file, (3) deciding whether a new skill or instruction is warranted,
  (4) evaluating if an existing instruction is earning its token cost. Based on
  "Evaluating AGENTS.md" (arxiv 2602.11988), "SkillsBench" (arxiv 2602.12670), and
  45+ corroborating sources.
---

# Context and Skills Standards

Evidence-based guidelines for what to put in context files and skills. The research consensus:
**what you put in matters far more than having them at all.** LLM-generated content harms
performance; human-curated, procedural skills improve it by +16.2pp on average.

## Core Principles

**P1 — Every instruction has an additive cost** _(Very High evidence)_
Models faithfully follow all instructions, consuming tokens and reasoning steps. Unnecessary
instructions actively harm performance. Litmus test: "Would removing this cause the model
to make mistakes?"

**P2 — Provide only what the model doesn't know** _(Very High evidence)_
Proprietary/new frameworks absent from training data: up to +51.9pp gain. Standard SE
patterns: only +4.5pp. Redundant with existing docs: −2 to −3%. Before writing anything,
ask: "Does the model already know this from training or from files it can read?"

**P3 — Procedural beats declarative** _(High evidence)_
Describe HOW to do things (step sequences, workflows), not WHAT things are (overviews,
architecture docs). One working code example is worth more than three paragraphs of
explanation.

**P4 — Moderate length is optimal; comprehensive hurts** _(Very High evidence)_
Detailed/compact instructions: +17–19pp. Comprehensive documentation: −2.9pp. There is
no optimal line count — optimize signal-to-noise ratio, not length. Err toward concise.

**P5 — 2–3 focused modules is optimal** _(High evidence)_
1 module: +17.8pp. 2–3 modules: +18.6pp (best). 4+ modules: +5.9pp. Excessive skill count
creates cognitive overhead and conflicting guidance.

**P6 — Human curation is essential; self-generation fails** _(Very High evidence)_
Curated skills: +16.2pp. Self-generated skills: −1.3pp. LLM-generated context files: −2 to
−3%. Models cannot reliably author the procedural knowledge they benefit from consuming.

**P7 — Always-present vs lazy-loaded depends on usage frequency** _(Medium evidence)_
Frequently needed, broadly applicable knowledge → CLAUDE.md (always-present). Specialized,
occasional knowledge → skills (lazy-loaded). Note: 56% of skills were never invoked in one
study — lazy-loading can cause knowledge to be missed for frequently-needed content.

**P8 — Skills can hurt; test for regression** _(High evidence)_
19% of tasks showed performance degradation with skills. Skills hurt most when the model
already handles the task well (ceiling effect) or when procedures conflict with optimal paths.

---

## Decision Framework: Should I Write This?

Before writing any instruction or skill, answer three questions:

1. **Domain coverage**: Does the model already know this well? Standard coding patterns,
   math, general SE → skip or be minimal. Proprietary systems, new frameworks, company-specific
   processes → high value.

2. **Redundancy check**: Is this already documented elsewhere the model can read? If yes,
   link or reference it rather than duplicating. Redundant instructions are actively harmful.

3. **Regression risk**: Could this instruction hurt tasks the model currently handles correctly?
   If the model already does this well, adding instructions may introduce conflicting procedures.

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

---

## Quick Reference: Include vs Exclude

| Include                                 | Exclude                                         |
| --------------------------------------- | ----------------------------------------------- |
| Repository-specific tooling commands    | Standard language conventions the model knows   |
| Proprietary API patterns with examples  | Codebase overviews and directory listings       |
| Non-obvious step sequences              | Architecture descriptions                       |
| Common mistakes you've seen in practice | Things the model currently does correctly       |
| Company-specific processes and naming   | Auto-generated content without human review     |
| Known failure modes with fixes          | Generic best practices covered in training data |

---

## Reference Files

Read these files for detailed guidance when:

- **[`references/context-file-guidelines.md`](references/context-file-guidelines.md)** — Writing or
  reviewing a CLAUDE.md or AGENTS.md. Covers instruction economy, anti-patterns, iterative
  refinement process, and length guidance.

- **[`references/skill-file-guidelines.md`](references/skill-file-guidelines.md)** — Creating or
  reviewing a SKILL.md or skill package. Covers domain coverage assessment, what makes a
  good vs bad skill, and testing for regression.

- **[`references/evidence-base.md`](references/evidence-base.md)** — Assessing source quality or
  explaining recommendations to others. Full citation list with confidence levels.
