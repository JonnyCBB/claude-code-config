# Context File Guidelines (CLAUDE.md / AGENTS.md)

Detailed guidance for writing and reviewing context files. See SKILL.md for the core
principles that underpin these guidelines.

---

## What Context Files Are For

Context files correct model behavior where it makes **specific, observable mistakes** on
real tasks. They are NOT:

- Codebase tours or architecture overviews
- Onboarding documentation for humans
- A place to document every file and directory
- A comprehensive manual for your project

The correct mental model: a context file is a collection of corrections. Each entry exists
because you saw the model make a specific mistake and you want to prevent it from recurring.

---

## The Instruction Economy

Every line in a context file has a non-zero token cost. The model will:

1. Read every instruction, consuming context budget
2. Faithfully follow every instruction, consuming reasoning steps
3. Apply bad instructions just as diligently as good ones

This means a context file with 10 well-chosen instructions outperforms one with 50 mixed-quality
instructions. The cost of an unnecessary instruction is not zero — it's a small performance
penalty that compounds across every task.

**The key insight from "Evaluating AGENTS.md" (2602.11988):** When existing documentation was
removed from repos, LLM-generated context files improved performance by 2.7% — proving their
only harm in the baseline condition was redundancy with docs the model already reads.

---

## Iterative Refinement: Add Reactively, Not Proactively

**Good process:**

1. Run the agent without any instruction on this topic
2. Observe the mistake
3. See the same mistake a second time (confirm it's a pattern, not a fluke)
4. Add a minimal, targeted instruction to prevent it

**Bad process:**

- Pre-emptively documenting everything you think the model might need
- Generating a comprehensive context file with an LLM
- Adding instructions "just in case"

Builder.io: "Iterate and add a rule the second time you see the same mistake."
Anthropic: "If Claude already does something correctly without the instruction, delete it."

---

## Recommended Structure

Effective context files share these characteristics:

**Short, named sections** — Not a wall of text. Group related instructions under clear headings.

**Specific tooling commands** — Exact commands with flags, not descriptions of what to run.

```
# Good: specific and runnable
Run tests with: `sbt test -Dtest.include=*Spec`

# Bad: vague
Run the tests before committing.
```

**Before/after examples for mistake patterns** — Show the wrong pattern and the right one.

```
# Good: shows the mistake and the fix
When writing Avro schemas, use `"type": ["null", "string"]` for optional fields,
NOT `"type": "string"` with a default — the latter breaks schema evolution.
```

**Tooling-specific, non-obvious information** — Things the model can't infer from general
knowledge.

```
# Good: non-obvious, specific to this repo
Use the Grep tool for code search, NOT the Bash tool with `grep` — the Grep tool
has better permissions handling and output formatting.
```

---

## Anti-Patterns (With Evidence)

**Comprehensive overviews** — Summarizing what the project does, listing all directories,
explaining the architecture. Research finding: no meaningful reduction in steps to locate
files. The model uses codebase exploration tools, not prose descriptions.

**Auto-generated content** — Running `/init` or asking an LLM to "generate a CLAUDE.md."
"Evaluating AGENTS.md": −2 to −3% performance, +20–23% cost. LLMs identify that documentation
is needed but generate generic, noisy content that consumes budget without helping.

**Standard language conventions** — Instructions like "write clean code," "use descriptive
variable names," or "follow PEP 8." The model already does these without being told. Including
them is pure cost with no benefit.

**File-by-file directory listings** — "The `src/main/` directory contains the main source
files, `src/test/` contains tests..." Research finding: agents don't use these descriptions.
They explore the filesystem directly.

**Formatting instructions for well-known patterns** — "Use 4-space indentation," "put imports
at the top." The model knows these. Only include formatting instructions that are non-standard
for your repo (e.g., "this project uses tabs, not spaces").

---

## Length Guidance

There is no optimal line count — the right length is determined by signal-to-noise ratio.

**Practical references:**

- HumanLayer recommends under 60 lines
- Anthropic: "keep it concise" — important rules get lost in noise if the file is too long
- Martin Fowler (Feb 2026): models have become powerful enough that extensive context
  previously necessary may no longer be required

**The test to apply to every line:**
_"Would removing this line cause the model to make a specific, observable mistake on a real task?"_

If no → delete it. Apply this test ruthlessly. The value of a context file comes from
precision, not completeness.
