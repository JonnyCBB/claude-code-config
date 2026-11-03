# Naming and comments in code-style-review mode

Two report/do-not-report boundaries for `code-style-review` mode, kept out of `SKILL.md` because
they apply to one of its five modes and `SKILL.md` loads for all of them.

Both categories were previously unreportable in practice — filtered as low-value nitpicks — and both
were re-enabled against measured evidence. The decision tests below are what stops that re-enabling
from turning a review into a nitpick list. Read this file when invoked in code-style-review mode.

## Contents

- [Vague and generic names](#vague-and-generic-names)
- [Unnecessary comments](#unnecessary-comments)

## Vague and generic names

The `LOW_VALUE` filter's naming bullet now carves out rule-citing findings — see
`${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/false-positive-guidance.md` for why.
This section draws the boundary of that carve-out, so it does not become
noise. The line is:

**Can you name the rule the identifier breaks, and quote it?**

If yes, report it. If the answer is "I would have called it something else", it is taste — filter it.

Report:

1. **A generic verb where the rule names one.** `process()`, `data()`, `handle()`,
   `handleRequest()`, `manage()`, `doWork()` — `${CLAUDE_PLUGIN_ROOT}/skills/code-style-common/naming-conventions.md`
   names these as too vague to say what the method does. Recommend the verb-noun form.
2. **Wrong casing for the language.** `snake_case` in Java, `camelCase` in Python, a lowercase
   class. The language skill states the convention.
3. **A name that contradicts what the code does.** `getUser()` that also writes, `isValid()` that
   returns a count. Worse than vague, because a reader trusts it — raise at **MEDIUM**.
4. **Single-letter or placeholder names outside a tight scope.** `d`, `tmp`, `x` as a parameter or
   a field. A loop index or a comprehension variable is fine.

Do NOT report:

- A name you would have chosen differently, with no rule behind it. `userCount` vs `numUsers`,
  `fetch` vs `get`, `cfg` vs `config`.
- A name that matches the surrounding file's established convention, even if the convention is not
  your preference. Consistency within a file beats an outside rule.
- Domain vocabulary you do not recognise. An unfamiliar term is not a vague one.
- Names on lines this PR did not touch (CHANGE_SCOPE).
- A case you cannot place on either side of the test. Confidence below 0.6 means the finding is
  ambiguous between taste and rule violation — leave it, same floor as the comments check below.

**Emit as**: `category: STYLE`, `severity: LOW` (or `MEDIUM` for case 3, a name that lies), citing
the rule in the body so the author can check it. Group a file's naming findings into one `ISSUE`.

## Unnecessary comments

The default for added code is **no prose comment**. Prefer meaningful names, types, and structure
before adding explanation. A comment earns its place only when clearer code cannot express a
necessary fact or contract, such as a hidden constraint, subtle invariant, or workaround.

Review comments on ADDED or MODIFIED lines with the surrounding logic:

**Does the comment mislead or obscure intent? Can clearer code replace its explanation?**

State the concrete effect, not just that a comment exists. Use these report boundaries:

1. **Restates the code.** `// increment the counter` above `count++`; `# return the user` above
   `return user`. The identifier already says it.
2. **Labels structure.** `// arrange` / `// act` / `// assert`, `// helpers`,
   `// --- validation ---`. Section markers substitute for extraction; if a block needs a label it
   usually wants to be a named method.
3. **Narrates the change or its callers.** "added for the X flow", "used by Y", "handles the case
   from issue #123", "new in this PR". Belongs in the PR description; in the code it rots on the
   next change.
4. **Explains code that should have been clearer.** A comment doing the job a name or an extracted
   method should do. Recommend the extraction or rename, not a better comment — the fix removes the
   need for the comment rather than improving it.
5. **Justifies its own explicitness.** "spelled out here rather than left implicit", "stated for
   clarity". Meta-commentary about the comment.
6. **Is wrong or stale.** Contradicts the code it sits above, or describes behaviour that has since
   changed. Raise this one at **MEDIUM** — an inaccurate comment is worse than no comment, because
   a reader trusts it. Detection cues in
   `${CLAUDE_PLUGIN_ROOT}/skills/code-style-common/comment-quality.md` under "Inaccurate Comments"
   and "Outdated Comments".

Do NOT flag:

- Tool directives such as `# noqa`, formatter controls, type-checker suppressions, or generated-file markers. They are not prose comments; never remove them through comment pruning.
- Comments carrying necessary context that clearer code cannot express: a hidden constraint, subtle
  invariant, workaround, or surprising behavior. These are the warranted cases; leave them. For what a
  warranted comment looks like written well, see
  `${CLAUDE_PLUGIN_ROOT}/skills/code-style-common/comment-quality.md`.
- API/interface documentation on a public contract (Javadoc, docstrings, `.proto` field comments)
  that documents the contract rather than the implementation.
- Comments on lines this PR did not touch. Per CHANGE_SCOPE, pre-existing comments are out of scope
  even when they are bad.
- A comment whose removal is a judgement call. Confidence below 0.6 means leave it — the point is
  reducing noise, and a wrong comment finding is itself noise.

**Emit as**: `category: STYLE`, `severity: LOW` (or `MEDIUM` for case 6, wrong or stale),
`confidence` per the rubric. Group adjacent unnecessary comments in one file into a single `ISSUE`
rather than one per line — a review with fourteen separate comment findings is the noise this rule
exists to reduce.

**This check applies to test code, protos and config exactly as to source.** Test files are
routinely the worse offender: in six pull requests measured on 2026-09-07, 54% of the comment lines
a human removed were in test files, and the second-largest single file was a `.proto`.

**Comments are one dimension of this mode, not a separate pass.** Assess clarity and reuse with
names, structure, and comments together. Measured 2026-09-07: a reviewer running the comment check
found every unnecessary comment but only **2 of 4** planted structural defects, against **3 of 4**
for a reviewer without it. Structural issues take priority.
