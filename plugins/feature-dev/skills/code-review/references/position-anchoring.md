# Position Anchoring

Rules for anchoring review comments to diff positions.

## Core Rules

1. **Only comment on changed lines** — lines starting with `+` or `-` in the diff are valid anchor targets
2. **Context lines are for understanding ONLY** — lines starting with ` ` (space) in the diff are context lines. NEVER anchor a comment to a context line
3. **Set position to the diff marker number** — the line count within the hunk, starting at 1 after the `@@` header
4. **Multi-line issues**: If an issue spans multiple lines, anchor to the most relevant changed line
5. **Deleted code**: If the issue is about deleted code, anchor to the `-` line
6. **File-wide patterns**: If the issue is about a pattern across the file but the file has changes, anchor to the first relevant changed line
7. **No relevant changed lines?** If none of the file's changed lines relate to the finding, the finding may be PRE_EXISTING — reconsider whether to include it

## Position Calculation

The position value is the line number within the diff hunk:
- Line 1 is the first line after the `@@` hunk header
- Count every line in the hunk (context, additions, deletions) sequentially
- The position refers to where the comment will appear in the diff view

## Examples

Given this hunk:
```diff
@@ -10,6 +10,8 @@ public class Example {
     private final Logger log;        // position 1 (context — do NOT anchor here)
     private final Client client;     // position 2 (context — do NOT anchor here)

+    private String unsanitized;      // position 4 (addition — valid anchor)
+    private int count = -1;          // position 5 (addition — valid anchor)
+
     public void process() {          // position 7 (context — do NOT anchor here)
```

- Valid anchor targets: positions 4, 5 (changed lines)
- Invalid anchor targets: positions 1, 2, 3, 6, 7 (context lines)

## Common Mistakes to Avoid

- Do not anchor to a context line just because it is "related" to the issue
- Do not anchor to a line outside the diff hunks
- Do not use file line numbers — use hunk-relative position numbers
- Do not create a finding if the only relevant code is in context lines (it is likely PRE_EXISTING)
