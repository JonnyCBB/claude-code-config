# False Positive Guidance

Categories of false positives that review agents MUST filter before emitting findings.

## Categories

### PRE_EXISTING

Issue not introduced by this change. Check git blame — if the code existed before this PR, do not flag it.

- Apply the "did this PR introduce it?" test to every finding
- If a line appears only as a context line (no `+` or `-` prefix), it is pre-existing
- If the pattern existed in the file before the PR and the PR did not modify it, do not flag

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

### EXTERNAL_KNOWLEDGE

Claims requiring knowledge the model cannot verify from the diff alone. Only flag if confidence >= 0.9 AND the claim is anchored to a specific diff line with verifiable evidence.

Examples of external knowledge claims to be skeptical of:
- "This API is deprecated"
- "This method has a known bug"
- "This library version has a CVE"
- "This pattern is discouraged by the team"

Unless the evidence is directly visible in the diff or surrounding context, do not assert it.

### LOW_VALUE

Nitpicks, naming preferences, theoretical scenarios with no concrete exploit/failure path. Filter.

- Subjective naming preferences ("I would call this X instead of Y")
- Theoretical performance concerns with no measurable impact
- "Consider using X instead of Y" without a concrete benefit
- Scenarios that require multiple unlikely conditions to manifest

## Anti-Hallucination Rules

1. **Never claim an API/method exists or is deprecated** without reading the actual source
2. **Never claim a state machine can reach a particular state** without tracing all transitions
3. **Apply the "did this PR introduce it?" test** to every finding
4. **Read PR author inline comments before flagging** — authors often explain non-obvious choices in PR descriptions or inline comments
5. **Do not invent failure scenarios** — every claimed failure must have a concrete, traceable path from the code in the diff
