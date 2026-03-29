# Severity Rubric

Five severity levels for review findings, plus confidence scoring.

## Severity Levels

### ENHANCEMENT

Nice-to-have improvements that aren't tied to a specific problem. Suggestions for better patterns, modernization, or code quality improvements that go beyond fixing an issue. **Aspirational — no expectation to address.**

Examples:
- Adopting a newer API or language feature that would improve readability
- Extracting a reusable helper from inline code that works fine as-is
- Adding type hints or documentation where none existed before
- Suggesting a more idiomatic pattern when the current one is correct
- Recommending a library utility that replaces working hand-rolled code

### CRITICAL

Production failures, data corruption, credential leakage, authentication bypass. **Must fix before merge.**

Examples:
- Hardcoded credentials or secrets in source code
- SQL injection or command injection vulnerabilities
- Authentication/authorization bypass
- Data corruption (writing to wrong table, overwriting user data)
- Unbounded resource consumption that will crash production (OOM, infinite loops)

### HIGH

Likely failures under realistic conditions, security vulnerabilities with exploit path, race conditions with data impact. **Should fix before merge.**

Examples:
- Race conditions that can corrupt shared state
- Missing null checks on values that are realistically null
- Security vulnerabilities with a concrete but non-trivial exploit path
- Resource leaks (connections, file handles) in long-running services
- Missing error handling that silently drops failures

### MEDIUM

Edge case failures, moderate performance impact, missing validation on non-critical paths. **Author discretion.**

Examples:
- Edge case handling that fails under uncommon but possible inputs
- Performance issues with moderate impact (e.g., N+1 queries on small datasets)
- Missing input validation on internal APIs
- Error messages that leak implementation details
- Missing logging for diagnosability

#### File Growth and Single Responsibility

Large file growth and single-responsibility violations often indicate design problems that compound over time.

Examples:
- Existing file grew by more than 200 new lines in a single PR
- New file already exceeds 500 lines
- Single file handles multiple unrelated responsibilities (e.g., HTTP routing + business logic + data access)
- File has no clear single responsibility — would require a compound name to describe its purpose

### LOW

Minor improvements, style suggestions, documentation gaps. **Optional.**

Examples:
- Suggestions for improved readability
- Documentation improvements
- Minor code simplifications
- Test coverage suggestions
- Non-critical naming improvements (only when genuinely confusing)

## Confidence Scoring

Confidence represents how certain the reviewer is that the issue is real and correctly characterized.

| Range     | Label      | Meaning                                                    |
|-----------|------------|------------------------------------------------------------|
| 0.9 - 1.0 | Definite   | Issue is provably present from the diff                    |
| 0.7 - 0.9 | Very likely | Strong evidence from diff, minor ambiguity                |
| 0.5 - 0.7 | Probable   | Evidence suggests issue but verification needed            |
| Below 0.5 | Filter     | Insufficient evidence — do not include in findings         |

### Confidence Rules

- Findings with confidence below 0.5 MUST be filtered out — do not emit them
- CRITICAL findings require confidence >= 0.7 to be emitted
- When in doubt, lower the confidence rather than inflating the severity
- Confidence reflects evidence quality, not severity — a LOW severity finding can have 1.0 confidence
