# Finding Schema

Canonical finding structure — the inter-agent contract between Phase 2 (review agents) and Phase 3 (post-review agents).

## Schema Definition

```
file_path: string     — relative path to the file
position: int         — diff marker number (line in hunk)
body: string          — markdown-formatted comment (using comment-format.md structure)
severity: enum        — ENHANCEMENT | LOW | MEDIUM | HIGH | CRITICAL
category: enum        — BUG | SECURITY | BEST_PRACTICE | STYLE
confidence: float     — 0.0 to 1.0
source_agent: string  — name of the agent that produced this finding
mode: enum|null       — test-review | code-style-review | null. The framing the agent was spawned under.
suggested_fix: string  — concrete fix suggestion (1-3 lines of code or mitigation steps). Optional.
cwe_id: string         — CWE identifier for security findings (e.g., "CWE-22"). Optional, used by security-reviewer.
```

## Field Descriptions

### file_path

Relative path from the repository root to the file containing the finding. Must match the path as it appears in the diff.

Example: `src/main/java/com/example/OrderService.java`

### position

The diff hunk position number where the comment should be anchored. See `position-anchoring.md` for calculation rules. Must reference a changed line (not a context line).

### body

Markdown-formatted review comment following the structure defined in `comment-format.md`. Should be self-contained.

### severity

One of five values:

- `ENHANCEMENT` — nice-to-have improvement, not tied to a specific problem
- `LOW` — optional improvement
- `MEDIUM` — author discretion
- `HIGH` — should fix before merge
- `CRITICAL` — must fix before merge

See `severity-rubric.md` for detailed criteria.

### category

One of four values:

- `BUG` — functional correctness issue (null pointer, off-by-one, logic error)
- `SECURITY` — security vulnerability (injection, auth bypass, data exposure)
- `BEST_PRACTICE` — deviation from established patterns or best practices
- `STYLE` — readability, naming, documentation

### confidence

Float between 0.0 and 1.0 representing how certain the reviewer is that the issue is real. Findings below 0.5 confidence MUST be filtered out before emission. See `severity-rubric.md` for confidence bands.

### source_agent

String identifier of the agent that produced this finding. Used for traceability and deduplication. Examples: `security-reviewer`, `bug-reviewer`, `best-practice-reviewer`.

### mode

The framing a `{language}-expert` agent was spawned under, set by the orchestrator at spawn time:
`test-review`, `code-style-review`, or `null` for every other agent.

**Why this is a field and not derivable.** The language experts (`python-expert`,
`typescript-expert`) are each spawned twice per review — once per
mode — and both invocations report the same `source_agent`. Without `mode`, a finding from the
style pass is indistinguishable from one from the test pass, and the severity filter in Phase 3
Step 2 cannot apply the ALL-severity exemption those two passes are entitled to.

**This was a real defect, not a hypothetical.** The filter previously identified those passes by
substring-matching the agent *name* (`code-style`, `test-reviewer`) — names that stopped existing
when the separate reviewers were consolidated into the four experts. Zero of the agents in
`agents/` carry either substring, so the exemptions matched nothing and LOW and ENHANCEMENT style
and test findings were discarded. Measured 2026-09-07 across two identical runs, the drop was
*intermittent*: one orchestrator read the rule literally and dropped them, another inferred the
intent and kept them. An intermittent silent drop is worse than a consistent one, because it reads
as reviewer variance.

**Compare `mode` by equality against the two values above. Never by substring containment.**
Containment is what produced the original defect twice over: `code-style-review` happens to contain
`code-style`, so a substring fix would appear to work, while `test-review` does not contain
`test-reviewer` (no trailing `er`) and would stay broken — restoring half the behaviour and hiding
the other half behind a working example.

### suggested_fix

Concrete fix suggestion — 1-3 lines of code or mitigation steps. Optional. Primarily used by `security-reviewer` to provide actionable remediation. Other agents may include this field when a specific code change is recommended.

Example: `"Add path validation: if not os.path.realpath(user_path).startswith(allowed_base): raise ValueError()"`

### cwe_id

CWE identifier for security findings (e.g., `"CWE-22"`, `"CWE-532"`). Optional. Used by `security-reviewer` for traceability. Non-security agents should omit this field.

## Contract

- All review agents (Phase 2) MUST emit findings in this format
- The orchestrator sets `mode` when it collects a `{language}-expert`'s findings — the agent does
  not set it, because the agent does not know which of its two invocations it is. Every other agent
  emits `mode: null`.
- All post-review agents (Phase 3: calibrator, deduplicator) MUST consume this format
- This is the contract that enables the pipeline — deviations will break downstream processing

## Example Finding

```json
{
  "file_path": "src/main/java/com/example/OrderService.java",
  "position": 14,
  "body": "`processOrder()` does not check whether `order.items` is null before iterating, but `OrderService.getOrder()` returns null items for cancelled orders.\n\n**Impact/Risk**: When a cancelled order is passed to this method during batch reprocessing, a NullPointerException will crash the processing loop, halting all subsequent orders.\n\n**Recommendation**: Add a null check: `if (order.items == null) { return Collections.emptyList(); }`",
  "severity": "HIGH",
  "category": "BUG",
  "confidence": 0.85,
  "source_agent": "bug-reviewer",
  "mode": null,
  "suggested_fix": "Add a null check: `if (order.items == null) { return Collections.emptyList(); }`",
  "cwe_id": null
}
```
