# Skill File Guidelines (SKILL.md + Resources)

Detailed guidance for creating and reviewing skills. See SKILL.md for the core principles.

---

## When to Write a Skill (Domain Coverage Assessment)

Skills are not always beneficial. Before writing one, assess the domain:

| Domain type                                        | Expected gain | Examples                                  |
| -------------------------------------------------- | ------------- | ----------------------------------------- |
| Proprietary systems (absent from training data)    | +42–52pp      | Internal tools, custom frameworks         |
| Healthcare / manufacturing (low training coverage) | +42–52pp      | Medical workflows, factory processes      |
| New frameworks not in training data                | +47pp         | Next.js 16 new API (Vercel finding)       |
| Standard software engineering patterns             | +4–6pp        | REST APIs, SQL queries, unit tests        |
| Math / algorithms                                  | ~+6pp         | Sorting algorithms, math proofs           |
| Topics already documented in the repo              | −2 to −3%     | Anything in existing docs the model reads |

**Practical rule:** If you're writing a skill for a proprietary internal system that the model
has no pretraining coverage for — write the skill. If you're writing a skill to teach general
coding patterns, be skeptical: the gains are small and the risk of conflicting procedures is real.

**Three pre-writing questions:**

1. Does the model already handle this correctly? → Run it without the skill first.
2. Is this covered by existing documentation the model can read? → Link to it instead.
3. Could adding procedures conflict with how the model currently succeeds at this? → Test.

---

## Optimal Skill Structure

Research-backed structure for maximum impact:

**Module count:** 2–3 focused modules (+18.6pp) is optimal. 4+ shows diminishing returns
(+5.9pp). A module is a SKILL.md body section or a reference file.

**Length:** Moderate is best. Detailed (+18.8pp) and compact (+17.1pp) both work. Comprehensive
hurts (−2.9pp). There is no optimal line count — optimize signal-to-noise ratio.

**Format:** Procedural workflows > declarative descriptions. The model needs to know _what to
do_, not just _what things are_.

**Examples:** Include at least one working code example per non-trivial workflow. One real
code snippet showing your pattern beats three paragraphs describing it (GitHub finding).

**Structure pattern:**

```
skill-name/
├── SKILL.md                # Core workflow + selection guidance (moderate length)
└── references/
    ├── [variant-a].md      # Details for variant A (loaded only when needed)
    └── [variant-b].md      # Details for variant B (loaded only when needed)
```

Keep SKILL.md to the core workflow. Move variant-specific details, schemas, and reference
material to `references/` files — they're only loaded when Claude determines they're needed.

---

## What Makes a Good Skill

A skill earns its cost when it:

**Provides procedural workflows** — Step sequences with concrete actions, not abstract
principles. "Run `sbt clean compile` first, then `sbt test`" > "Make sure to compile before
testing."

**Covers a class of tasks, not a single instance** — The skill should apply to multiple
future tasks, not just the one you're working on now.

**Includes at least one working example** — Show the pattern with real code, not pseudocode.
The example should be copy-paste usable or close to it.

**Targets genuine knowledge gaps** — The model doesn't know this from training data and can't
easily discover it from the repository.

**Explicitly matches agent constraints** — If the skill produces output in a specific format,
remind the agent of that format. Models sometimes revert to generic behavior without reminders.

**Example of good skill content:**

```markdown
## Creating a Scheduled Workflow

Run the generator:
\`\`\`bash
./scripts/generate-workflow.py --component my-service --schedule "PT1H"
\`\`\`
This creates `workflows/workflow.yaml`. Edit the component ID field to match
your component (find it in your project config).
```

---

## What Makes a Bad Skill

Avoid these patterns — research shows they actively harm performance:

**Comprehensive documentation** (−2.9pp) — A skill that documents everything about a
domain. The model can't prioritize; everything gets equal attention. Prefer focused, targeted
guidance over complete coverage.

**Generic principles without specific API patterns** — "Use pandas for data processing" is
not actionable. "Use `pd.read_parquet(path, columns=['col1','col2'])` to avoid loading all
columns" is. The SkillsBench failure mode: models identify that domain knowledge is needed
but generate imprecise procedures.

**Content the model already knows from training** — Instructions about standard Python, Java,
or Scala patterns that any competent model handles correctly. This adds cost without benefit.

**Task-specific solutions rather than general procedures** — A skill that solves one specific
ticket is not reusable. Abstract the pattern from the specific instance.

**Overlapping skills with conflicting procedures** — Two skills that give different advice for
the same situation create model confusion. 4+ skills on related topics is a warning sign.

---

## Testing Guidance

Because skills can hurt performance (P8 — 19% of tasks degrade), test before deploying:

1. **Baseline first** — Attempt the task WITHOUT the skill active. Record the outcome.
2. **Test with skill** — Attempt the same task with the skill. Compare.
3. **Test on tasks the model already handles** — Specifically look for regression on tasks
   that worked before. If the model is worse at something it previously handled correctly,
   the skill is conflicting with its optimal approach.
4. **Iterate from real usage** — The best skill improvements come from watching actual
   failures, not from speculating about what might help.
5. **Remove or narrow if degrading** — If a skill hurts a class of tasks, narrow its scope
   (more specific description) or remove the conflicting section.

---

## The Self-Generation Trap

**Never ship a skill generated entirely by an LLM without human curation.**

SkillsBench finding: self-generated skills show −1.3pp performance on average (worse than
no skill). Two failure modes:

1. **Incomplete procedure generation** — The model identifies that domain knowledge is needed
   but generates imprecise procedures ("use the appropriate API") without specific patterns.

2. **Domain knowledge gaps** — The model fails to recognize the need for specialized knowledge
   at all and attempts the task with general-purpose approaches.

**What works:** LLM-assisted drafting with human-in-the-loop refinement and real-task
evaluation. Arize found +5.19% improvement using iterative, eval-driven optimization with
human review at each cycle.

The model can help you draft the skill structure and prose, but a human must:

- Verify each procedure against the actual system behavior
- Add the working code examples that make procedures concrete
- Remove generic content that the model already knows
- Test the skill on real tasks and iterate based on failures
