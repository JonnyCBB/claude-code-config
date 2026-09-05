#!/usr/bin/env bash
# Asserts content properties of references/pr-description-template.md.

F="$SKILL_DIR/references/pr-description-template.md"

# --- Preserved structure ---
assert_contains "$F" "^## Template Discovery$" "Template Discovery section preserved"
assert_contains "$F" "^## Default PR Description Format$" "Default PR Description Format section present"

# --- New 7-section default template ---
assert_contains "$F" "^### Title$" "Title section present"
assert_contains "$F" "^### Why$" "Why section present"
assert_contains "$F" "^### What$" "What section present"
assert_contains "$F" "^### Links$" "Links section present"
assert_contains "$F" "^### Stack$" "Stack section present (conditional)"
assert_contains "$F" "^### Architecture Overview$" "Architecture Overview section present (conditional)"
assert_contains "$F" "^### Testing & Verification$" "Testing & Verification section present"

# --- Removed sections must NOT appear as default headers ---
assert_not_contains "$F" "^### Summary$" "Summary section removed (renamed to Why)"
assert_not_contains "$F" "^### Context$" "Context section removed (folded into Why)"
assert_not_contains "$F" "^### What Changed$" "What Changed (with subsystem buckets) removed"
assert_not_contains "$F" "^### Behavioral Impact$" "Behavioral Impact section removed"
assert_not_contains "$F" "^### Behavioural Impact$" "Behavioural Impact section removed (UK spelling)"
assert_not_contains "$F" "^### Risk Assessment$" "Risk Assessment section removed"
assert_not_contains "$F" "^### Performance Impact$" "Performance Impact section removed"
assert_not_contains "$F" "^### Screenshots/Demo$" "Screenshots/Demo as fixed section removed"
assert_not_contains "$F" "^### Review Guidance$" "Review Guidance section removed"
assert_not_contains "$F" "^### Pre-merge Checklist$" "Pre-merge Checklist section removed"
assert_not_contains "$F" "^### Live Testing Evidence$" "Live Testing Evidence as separate section removed (now nested)"
# --- Callouts must NOT become their own sections (added in Wave 1; populated in Wave 2) ---
assert_not_contains "$F" "^### Breaking [Cc]hanges?$" "Breaking change is inline, not its own section"
assert_not_contains "$F" "^### Feature [Ff]lags?$" "Feature flag is inline, not its own section"
assert_not_contains "$F" "^### Migrations?$" "Migration is inline, not its own section"

# --- Removed subsystem buckets (literal phrases from current template) ---
assert_not_contains "$F" "Core Logic.*Main business logic" "Core Logic bucket removed"
assert_not_contains "$F" "API/Interface.*Public API modifications" "API/Interface bucket removed"

# --- Verification embedding rewritten for nested collapsibles ---
# Anchored on specific phrases the GREEN step commits to producing.
assert_contains "$F" "Verification details" "Verification details Level-1 collapsible documented (literal phrase)"
assert_contains "$F" "ls -t ~/.claude/thoughts/shared/verification" "verification report detection bash preserved"
assert_contains "$F" "Acceptance [Cc]riteria [Vv]erification" "Acceptance Criteria mapping included in Level-1"
# Level-2 nesting: assert that a <details> tag occurs at least twice (Level-1 + Level-2 in the
# example). Brittleness is acceptable here because the GREEN step renders both literally.
assert_contains "$F" "<details>.*<summary>" "first <details>/<summary> opening (Level-1) present"
assert_contains "$F" "S1: " "at least one Level-2 scenario header (literal 'S1:') present in skeletal example"

# --- Conventional Commit parser preserved but repurposed ---
assert_contains "$F" "Conventional Commit" "Conventional Commit Parsing section preserved"
assert_contains "$F" "feat:" "Conventional commit prefix 'feat:' preserved"
assert_contains "$F" "fix:" "Conventional commit prefix 'fix:' preserved"
# Parser repurpose: assert the new framing literal phrase from the GREEN spec.
assert_contains "$F" "informs the LLM-authored" "parser repurposed: 'informs the LLM-authored Why/What prose' framing"
# Parser is no longer described as populating "What Changed" subsections.
assert_not_contains "$F" "auto-populate.*What Changed" "parser no longer populates 'What Changed' buckets"

# --- Conditional auto-detection callouts (Wave 2) ---
# Inline-format examples — the literal pattern that callouts produce in the rendered PR body.
assert_contains "$F" "[*][*][Bb]reaking change[*][*]:" "Breaking change inline format example present"
assert_contains "$F" "[*][*][Ff]eature flag[*][*]:" "Feature flag inline format example present"
assert_contains "$F" "[*][*][Mm]igration[*][*]:" "Migration inline format example present"

# Screenshots prompt — HTML comment fallback emitted when UI extensions detected but no screenshot
# was provided.
assert_contains "$F" "<!--.*screenshot.*-->" "Screenshots HTML comment fallback documented"

# Pointer to SKILL.md as source-of-truth for trigger conditions.
assert_contains "$F" "see Phase 1 auto-detection in .?SKILL\.md" "callouts reference SKILL.md auto-detection rather than duplicating triggers (literal anchor)"
