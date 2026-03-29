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

## Contract

- All review agents (Phase 2) MUST emit findings in this format
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
  "source_agent": "bug-reviewer"
}
```
