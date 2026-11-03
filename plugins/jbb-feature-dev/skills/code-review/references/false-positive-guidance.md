# False Positive Guidance

Categories of false positives that review agents MUST filter before emitting findings.

## Categories

### PRE_EXISTING

Issue not introduced by this change. Check git blame — if the code existed before this PR, do not flag it.

- Apply the "did this change introduce it or make it wrong?" test to every finding
- Read unchanged callers and siblings for context, but anchor the finding to the scoped change that causes the failure
- If the pattern existed before and the change does not make it wrong or carry it into a new path, do not flag

### COMPILER_CATCHABLE

Type errors, missing imports, syntax errors that CI/compiler catches. Never flag.

- Missing imports will fail compilation
- Type mismatches will fail compilation
- Syntax errors will fail parsing
- These waste reviewer time because CI will catch them deterministically

### STRUCTURAL

Formatting, whitespace, import ordering — formatter/linter handles these. Never flag.

- Indentation issues
- Trailing whitespace
- Import ordering or grouping
- Line length violations
- Brace placement style
- These are enforced by automated tooling (formatters, linters) and should never appear in a code review

**Not structural: comment content.** No formatter or linter decides whether a comment earns its
place — that judgement needs a reader who understands the code. Unnecessary comments are a
legitimate STYLE finding, not a formatting nitpick. See
`${CLAUDE_PLUGIN_ROOT}/skills/code-review-modes/references/naming-and-comments.md` section "Unnecessary comments".

### EXTERNAL_KNOWLEDGE

Claims requiring knowledge the model cannot verify from the diff alone. Only flag if confidence >= 0.9 AND the claim is anchored to a specific diff line with verifiable evidence.

Examples of external knowledge claims to be skeptical of:
- "This API is deprecated"
- "This method has a known bug"
- "This library version has a CVE"
- "This pattern is discouraged by the team"

Unless the evidence is directly visible in the diff or surrounding context, do not assert it.

**A citation of a rule file you can read is not external knowledge.** This category is about claims
the model cannot check — the state of the outside world, or a team norm it is guessing at. A
convention written down in `code-style-common/`, a language skill, `AGENTS.md`, `CLAUDE.md` or `CONTRIBUTING.md`
is none of those: the file is on disk, it was injected into your prompt or you can open it, and the
claim "this name breaks that rule" is verifiable against it. Judge such a finding on whether the rule
says what the finding claims, not against the 0.9 confidence gate.

This matters because the two rules otherwise form a trap. `LOW_VALUE` keeps a naming finding only if
it **cites the rule it breaks** — and citing a rule is what makes it look like external knowledge, so
the finding gets removed for doing the very thing that was supposed to save it. Measured 2026-09-07:
a reviewer classified a naming finding citing `naming-conventions.md` as EXTERNAL_KNOWLEDGE, noted
its confidence was 0.8 against the 0.9 gate, and removed it. Note that "This pattern is discouraged
by the team" above reads almost identically to a legitimate rule citation; the difference is whether
you can point at the file.

### LOW_VALUE

Nitpicks, naming preferences, theoretical scenarios with no concrete exploit/failure path. Filter.

- Subjective naming preferences — a swap you simply prefer, with no rule behind it ("I would call this X instead of Y", `userCount` vs `numUsers`, `fetch` vs `get`)
- Theoretical performance concerns with no measurable impact
- "Consider using X instead of Y" without a concrete benefit
- Scenarios that require multiple unlikely conditions to manifest

**Exception — a naming finding that cites a rule is not a subjective preference.** The bullet above
covers taste. It does not cover a name that violates a convention someone wrote down:
`${CLAUDE_PLUGIN_ROOT}/skills/code-style-common/naming-conventions.md` names `process()`, `data()`,
`handleRequest()` and `handle()` as too vague to describe what they do, and the language skills carry
per-language casing rules. If you can point at the rule and the name breaks it, report it; that is a
convention violation with a concrete cost, not a preference.

This carve-out exists because the unqualified version silently deleted the whole naming dimension.
Measured 2026-09-07: given a diff containing a method named `handle(self, d)` with locals `raw`,
`tmp`, `r`, two independent reviewers both discarded it citing this bullet — one of them noting it
filtered the finding "despite naming being nominally in-scope". Meanwhile code-review-modes lists
naming as in scope for code-style-review and `naming-conventions.md` spends 167 lines on it.

**Exception — unnecessary comments are not low-value.** A comment that restates the code, labels
structure, narrates the change, or has gone stale is a real defect: it is a second copy of a claim
that drifts out of sync with the first, and a reader trusts it. Flag these per
`${CLAUDE_PLUGIN_ROOT}/skills/code-review-modes/references/naming-and-comments.md` section "Unnecessary comments", which
carries the decision test and the confidence floor. Do still group adjacent ones into a single
finding — fourteen separate comment findings in one review IS low-value, even when each is
individually correct.

## Anti-Hallucination Rules

1. **Never claim an API/method exists or is deprecated** without reading the actual source
2. **Never claim a state machine can reach a particular state** without tracing all transitions
3. **Apply the "did this PR introduce it?" test** to every finding
4. **Read PR author inline comments before flagging** — authors often explain non-obvious choices in PR descriptions or inline comments
5. **Do not invent failure scenarios** — every claimed failure must have a concrete, traceable path from the code in the diff
