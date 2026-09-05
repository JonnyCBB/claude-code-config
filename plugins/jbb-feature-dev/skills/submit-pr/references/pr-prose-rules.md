# PR Prose Rules

Content generation and prose quality rules for PR descriptions. Read this file
when Phase 2 instructs you to apply content generation rules.

## The Diff-Deducible Test (Hard Rule)

Before writing any bullet in the "What" section, ask: "Can a reviewer learn this
by reading the diff?" If yes, omit it.

Examples of diff-deducible content that MUST be omitted:

- Version bumps: "pom.xml: BOM 3002-20260714 -> 3002-20260715"
- File renames or moves
- Import changes
- Removed code: "removed the Caffeine AsyncLoadingCache"
- Config file edits: "monitoring-info.yaml: removed the dashboard row"
- Mechanical refactors where the diff is self-explanatory

Examples of content that is NOT diff-deducible and SHOULD be included:

- Why a dependency was bumped (if there's a reason beyond routine updates)
- Why code was removed (the motivation, not the fact of removal)
- Behavioral consequences of a config change that aren't obvious from the YAML
- Design tradeoffs the reviewer can't infer from the code alone

## Per-Section Length Constraints

| Section | Constraint                                       |
| ------- | ------------------------------------------------ |
| Why     | 1-3 sentences. State the problem or motivation.  |
| What    | 2-4 bullets. Behavior changes, not file changes. |
| Links   | Just the links. No prose.                        |
| Testing | Bullets only for non-CI verification activities. |

**Proportionality rule**: Description length scales with change complexity.
A BOM bump or dependency update needs 1-2 sentences total, not multiple sections.
A multi-service feature change warrants the full template. Use judgment.

## Prose Quality Rules

These rules prevent the PR description from reading as obviously AI-generated.
They are derived from the `sound-like-me` skill's most PR-relevant patterns.

When invoking that skill from here, pass `--register=ghe-pr-body`. It has one persona file per
destination surface, and applying the wrong one measured worse than applying none at all.

### Do not narrate the diff

Describe what the code does now, not the mechanics of the change.

Before: "This function was added to replace the previous approach of iterating
through all items, which caused O(n^2) performance."

After: "Uses a hash map for O(1) lookups instead of iterating the full list."

### Do not use inline-header bullet lists

Do not write bullets with bolded category headers.

Before:

- **Performance:** Reduced latency by switching to batch queries.
- **Security:** Added input validation on the endpoint.
- **Testing:** Added integration tests for the new path.

After:

- Switch to batch queries to reduce latency.
- Add input validation on the search endpoint.

### Do not use AI vocabulary

Ban these words in PR descriptions: leverage, robust, streamline, enhance,
ensure, foster, facilitate, utilize, comprehensive, seamless, cutting-edge,
harness, empower, bolster, augment, spearhead.

Use concrete, specific verbs instead. "Add" not "enhance." "Fix" not "address."
"Use" not "leverage." "Check" not "ensure."

### Do not inflate significance

Before: "This marks a significant step in modernizing our authentication
architecture, contributing to the broader initiative of platform reliability."

After: "Add token refresh to the auth service so sessions don't drop after 1 hour."

### Cut filler phrases

Remove on sight: "In order to," "It is important to note that," "It should be
noted that," "As part of this change," "This PR introduces," "This change
implements."

Just state what changed and why.

### Use active voice

Before: "Configuration changes are not required." / "The cache was removed."

After: "You don't need to change any config." / "This removes the cache."

### Do not force groups of three

Use as many bullets as the change warrants. If one bullet covers it, write one.
If five are needed, write five. Do not pad to three or trim to three.

### Do not add unrequested sections

Do not generate "Known Limitations," "Future Work," "Notes," or "Additional
Context" sections unless the change genuinely requires them. If nothing is
broken or limited, say nothing.

## Post-Generation Audit

After generating the PR description, run these checks before submitting:

1. **Diff-deducible scan**: Re-read each bullet in "What." For each, ask: "Would
   a reviewer already know this from the diff?" Remove if yes.
2. **AI-vocabulary scan**: Grep the body for: leverage, robust, streamline,
   enhance, ensure, foster, facilitate, utilize, comprehensive, seamless. Replace
   with concrete alternatives.
3. **Filler scan**: Grep for "In order to," "It is important," "It should be
   noted," "This PR introduces," "This change implements." Cut or rewrite.
4. **Length check**: Count visible lines (excluding collapsibles). If > 30 on a
   typical change, trim.
5. **Why check**: Does the "Why" section contain information not derivable from
   the code? If not, and interactive mode is on, prompt the user. If non-interactive,
   write a factual summary and add `<!-- why: not provided -->`.
6. **Narration check**: Does any bullet start with "Added," "Removed," "Updated,"
   "Modified," or "Changed" followed by a filename? Rewrite as a behavior change.
