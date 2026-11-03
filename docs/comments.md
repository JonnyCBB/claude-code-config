# Comments: the refutation test in full

The default is NONE (Jonny, 2026-09-11, after a sweep removed 22,546 comments from one repo and left 22 lines of prose). The rule and the test are in `CLAUDE.md`; this is the detail.

**What survives** (the only two kinds that did, measured over ~22,500 comments, plus two qualifiers). Violating each fails at runtime, so no test can carry the knowledge:

- A workaround for a named external defect, where the code looks wrong without it.
- An ordering or concurrency constraint invisible locally and fatal if reordered.
- A wire or protocol requirement imposed from outside.
- A deliberate choice that looks like a bug and would be "fixed" by the next reader.

One or two lines even then. Where to look for the fact before keeping a comment: the function, its callers, its tests, a type, an error message, git history, a bead, a document.

**Never delete these; they are not comments:** `# noqa`, `# type: ignore`, `# pragma: no cover`, `# ruff:`, `# mypy:`, `# fmt:`, shebangs, coding declarations. They instruct tools.

**Three traps:**

1. **A rewritten comment is a new claim nobody verified.** A sweep that condensed rather than deleted added 991 lines of fresh prose. Rewrites clear a higher bar than originals.
2. **Deleting a comment can break code.** A test scanned raw source and a comment was the only qualifying reference to a constant. Run the suite; a syntax-tree check cannot see this.
3. **Docstrings cite comments.** After removing comments, check what still refers to them (19 docstrings in one change pointed at nothing).

**Review too:** a PR that adds comments is asked to justify each against the test; the usual honest answer is to remove it.
