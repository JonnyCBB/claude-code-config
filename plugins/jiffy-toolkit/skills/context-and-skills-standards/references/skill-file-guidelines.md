# Skill File Guidelines (SKILL.md + Resources)

Detailed guidance for creating and reviewing skills. See SKILL.md for the core principles.

---

## When to Write a Skill (Domain Coverage Assessment)

Skills are not always beneficial. Before writing one, assess the domain:

| Domain type                                        | Expected gain | Examples                                  |
| -------------------------------------------------- | ------------- | ----------------------------------------- |
| Proprietary systems (absent from training data)    | +42–52pp      | Bespoke internal platforms and datastores |
| Healthcare / manufacturing (low training coverage) | +42–52pp      | Medical workflows, factory processes      |
| New frameworks not in training data                | +47pp         | Next.js 16 new API (Vercel finding)       |
| Standard software engineering patterns             | +4–6pp        | REST APIs, SQL queries, unit tests        |
| Math / algorithms                                  | ~+6pp         | Sorting algorithms, math proofs           |
| Topics already documented in the repo              | −2 to −3%     | Anything in existing docs the model reads |

**Practical rule:** If you're writing a skill for a proprietary internal system (a bespoke
datastore, scheduler or serving layer), the model has no pretraining coverage — write the skill.
If you're writing a skill to teach general coding patterns, be skeptical: in real-world SE,
39/49 skills showed zero improvement (SWE-Skills-Bench). The gains are small and the risk
of conflicting procedures is real.

**Three pre-writing questions:**

1. Does the model already handle this correctly? → Run it without the skill first.
2. Is this covered by existing documentation the model can read? → Link to it instead.
3. Could adding procedures conflict with how the model currently succeeds at this? → Test.

---

## Description Optimization

Descriptions determine whether a skill triggers. Without adequate descriptions, routing
accuracy drops 31–44pp (SkillRouter) — a well-written skill that never activates provides
zero value.

**Platform constraints:**

- Combined `description` + `when_to_use` text is truncated at 1,536 characters (hard limit)
- Skill descriptions consume ~1% of context window
- Least-used skills' descriptions are dropped first when budget is exceeded

**Writing guidance:**

- Write in third person ("Migrates JUnit 4 tests to JUnit 5" not "Use this to migrate tests")
- Include action verbs and concrete use cases
- Define boundaries — what the skill does AND does not cover
- Front-load the most important information (truncation cuts from the end)

**Frontmatter fields:**

- `description`: Always present in skill listing. Primary activation signal.
- `when_to_use`: Appended to description in the listing. Use for trigger conditions, file
  patterns, or context clues ("Use when you see imports from org.junit").
- `paths`: Glob patterns that limit auto-activation to matching files. Use to scope skills
  to specific parts of the codebase.

For rigorous description testing and optimization, use skill-creator's eval workflow — it
includes baseline comparison and description A/B testing.

---

## Skill Categories

Not all skills age the same way. Understanding the category helps you evaluate and maintain
skills appropriately.

**Capability uplift skills** encode techniques beyond the base model's current ability.
These have _expiring_ value — as models improve, the skill becomes redundant. Examples:
complex multi-step debugging workflows, specific algorithm implementations the model can't
yet handle. Re-evaluate these periodically; delete when the model handles the task natively.

**Encoded preference skills** sequence capabilities per organizational workflows. These have
_appreciating_ value — they encode institutional knowledge that models can't learn from public
training data. Examples: company-specific deployment processes, internal code review standards,
proprietary API patterns. These are your highest-value skills.

---

## Degrees of Freedom

Match instruction specificity to the fragility of the operation (Anthropic best practices).

| Freedom Level | When to Use                                  | Instruction Style                     |
| ------------- | -------------------------------------------- | ------------------------------------- |
| **High**      | Creative tasks, multiple valid approaches    | Text guidance, directional principles |
| **Medium**    | Preferred patterns with acceptable variation | Pseudocode or scripts with parameters |
| **Low**       | Fragile operations, exact steps required     | Specific scripts, exact commands      |

Think "narrow bridge with cliffs" (low freedom — exact steps prevent disaster) vs "open field"
(high freedom — directional guidance, many valid paths).

Explain the WHY behind each instruction. Prescriptions without rationale create two failure
modes: blind following when the context doesn't fit, or wholesale ignoring because the
instruction feels arbitrary (Block Engineering, skill-creator).

---

## Optimal Skill Structure

Research-backed structure for maximum impact:

**Module count:** 2–3 focused modules (+18.6pp) is optimal. 4+ shows diminishing returns
(+5.9pp). A module is a SKILL.md body section or a reference file.

**Length:** Anthropic recommends SKILL.md under 500 lines (empirical target). Auto-compaction
retains the first 5,000 tokens per skill (25,000 total budget across all skills). Moderate
detail (+18.8pp) and compact (+17.1pp) both work; comprehensive hurts (−2.9pp). Optimize
signal-to-noise ratio within the line target.

**Format:** Procedural workflows > declarative descriptions. The model needs to know _what to
do_, not just _what things are_.

**Examples:** Include at least one working code example per non-trivial workflow. One real
code snippet showing your pattern beats three paragraphs describing it (GitHub finding).

**Structure pattern:**

```
skill-name/
├── SKILL.md                # Core workflow + selection guidance (under 500 lines)
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
This creates `kubernetes/scheduled-workflow.yaml`. Edit the `catalogId` field to match
your component's catalog ID (find it in `catalog-info.yaml`).
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

## Testing and Evaluation

Because skills can hurt performance (P8), adopt an evaluation-first approach.

**Evaluation-first development** (Anthropic best practices): Create evaluations BEFORE writing
extensive documentation. The workflow: identify gaps → create evaluations → establish baseline
→ write minimal instructions → iterate. This prevents investing effort in content that doesn't
help or actively harms.

**Testing steps:**

1. **Baseline first** — Attempt the task WITHOUT the skill active. Record the outcome.
2. **Test with skill** — Attempt the same task with the skill. Compare.
3. **Test on tasks the model already handles** — Specifically look for regression on tasks
   that worked before. If the model is worse at something it previously handled correctly,
   the skill is conflicting with its optimal approach.
4. **Iterate from real usage** — The best skill improvements come from watching actual
   failures, not from speculating about what might help.
5. **Remove or narrow if degrading** — If a skill hurts a class of tasks, narrow its scope
   (more specific description) or remove the conflicting section.

For rigorous evaluation infrastructure (baseline comparison, blind grading, benchmark
aggregation, description optimization), use skill-creator's eval workflow rather than
building your own.

---

## LLM-Assisted Skill Creation

Single-pass LLM-generated skills average −1.3pp performance (SkillsBench) — worse than no
skill at all. Two failure modes explain why:

1. **Incomplete procedure generation** — The model identifies that domain knowledge is needed
   but generates imprecise procedures ("use the appropriate API") without specific patterns.

2. **Domain knowledge gaps** — The model fails to recognize the need for specialized knowledge
   at all and attempts the task with general-purpose approaches.

Self-feedback doesn't fix this — it induces recursive drift, compounding rather than
correcting errors (SkillLearnBench). External feedback is what drives improvement: Trace2Skill
achieves +57.65pp using multi-agent generation with external feedback loops.

**The recommended pattern** (what skill-creator implements):
LLM draft → human review → eval-driven testing → iterate. Each cycle uses external validation
(human judgment, automated evals, real-task results) rather than the model grading its own
output. Arize found +5.19% improvement per iteration cycle with this approach.

The model can help you draft the skill structure and prose, but external validation must:

- Verify each procedure against the actual system behavior
- Add the working code examples that make procedures concrete
- Remove generic content that the model already knows
- Test the skill on real tasks and iterate based on failures
