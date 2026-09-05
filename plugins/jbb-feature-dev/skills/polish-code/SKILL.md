---
name: polish-code
argument-hint: "[scope] [--non-interactive]"
description: >
  Final quality gate before /submit-pr — runs six passes (test enhancement, source
  simplification, test simplification, data annotation, coding guidelines, formatting)
  with checkpoint commits for safe rollback. Use when the user asks to "polish code",
  "polish changes", "clean up before PR", "simplify and format the diff", or says
  "/polish-code". Pass --non-interactive for autonomous mode that logs decisions
  instead of prompting.
---

# Polish Code Command

`/polish-code` is the final quality gate before `/submit-pr`. It runs six passes:
test enhancement, source simplification, test simplification, data annotation, coding
guidelines, and formatting. Use `--non-interactive` for autonomous mode (decisions
logged to a summary report); otherwise the skill asks for approval at each pass.

## Mode Detection

Parse `$ARGUMENTS` for the `--non-interactive` flag and the scope arguments.

- **Non-interactive** (`--non-interactive`): no user prompts. Apply the autonomous decision frameworks below (liberal for simplification, MEDIUM-and-up for test enhancement). Log every decision and rationale; produce a summary report at the end. Resolve ambiguities using `${CLAUDE_PLUGIN_ROOT}/skills/decision-principles/SKILL.md`. Continue without stopping (only baseline test failure is a hard stop).
- **Interactive** (default): show diffs and recommendations at each pass and ask the user to confirm before applying. Never modify files without permission.
- **Scope arguments**:
  - `--branch <branch>` or `-b <branch>`: compare current branch against specified branch
  - `--staged` or `-s`: only staged changes
  - File/directory paths: explicit file-level scope
  - No scope provided: interactive mode prompts; non-interactive mode defaults to current branch vs auto-detected base branch.

## Workflow Overview

Execute the following steps in order. Create a TODO list at the start to track progress.

```
Step 0: Pre-flight (safety commit, detect project, detect domains, baseline tests)
   ↓
Step 1: Extract Change-Level Scope
   ↓
Step 2: Test Enhancement
   ↓
Step 3: Source Code Simplification
   ↓
Step 4: Test Code Simplification
   ↓
Step 5: Data Annotation Review
   ↓
Step 6: Coding Guidelines Review
   ↓
Step 7: Formatting
   ↓
Step 8: Verification + Summary Report
```

### Step 0: Pre-flight Checks

1. **Record starting commit**: `STARTING_COMMIT=$(git rev-parse HEAD)`
2. **Confirm or log scope**:
   - Interactive: show what files/changes will be processed and ask for confirmation.
   - Non-interactive: log the resolved scope, no confirmation.
3. **Safety commit** if there are uncommitted changes:
   - Stage only tracked files: `git add -u`
   - Exclude `~/.claude/thoughts/` and local config (`.env`, `*.local`).
   - Commit: `git commit -m "Safety commit before polish-code"`
4. **Detect project type(s)**: `package.json` (Node/TS), `pyproject.toml`/`setup.py` (Python). For mixed projects, handle each detected type. Store the detected type(s) for later steps.
5. **Detect domains in scope** — follow the procedure in `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` (file triggers first, then strong signals, then corroborating signals). Output:

   ```
   ## Domains Detected in Scope
   - ✓ [Domain]: Found [pattern] in [file]
   - ✗ [Domain]: Not detected
   ```

   Store detected domains for use in subsequent steps.

6. **Detect base branch**: try `git symbolic-ref refs/remotes/origin/HEAD`; fallback to `master` or `main`. Store as `BASE_BRANCH`.
7. **Required: Agent Type Verification** — create an explicit agent contract:

   ```
   ## Agent Type Verification

   Based on the project type and domains detected, I will spawn:

   **Language-based agents** (from `shared-references/language-agent-registry.md`):
   - {language}-expert in test-review mode
   - {language}-expert in code-style-review mode

   **Domain-based agents** (from `shared-references/domain-agent-registry.md`):
   - For each domain with "✓": [Domain] → [agent-name]

   Total unique agents: [N]

   ⚠️ This list is my CONTRACT for Steps 2, 3, and 4.
   ```

   Reference: `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md`.

8. **Run baseline tests** with the appropriate command for the project type. **HARD STOP if baseline tests fail** — cannot establish baseline. This applies in both modes.

### Step 1: Extract Change-Level Scope

**Only applies when scope is `--branch <branch>`, `--staged`, or default (no arguments).** If scope is explicit file/directory paths, skip this step and use file-level scope for all subsequent steps.

1. **Get diff with line numbers**:

   ```bash
   # Branch comparison (default or explicit)
   git diff <BASE_BRANCH>...HEAD --unified=0 --no-color

   # Staged changes
   git diff --cached --unified=0 --no-color
   ```

2. **Parse diff into CHANGE_SCOPE**:

   ```
   CHANGE_SCOPE:
   - file: src/services/user_service.py
     changes:
       - lines: 45-52 (added)
       - lines: 102-105 (modified)
   - file: src/services/order_service.py
     changes:
       - lines: 23-30 (added)
   ```

3. **Store CHANGE_SCOPE** for use in Steps 2, 3, 4.
4. **Display / log scope summary**: file count, lines added/modified. Interactive: confirm with user.

### Step 2: Test Enhancement

1. **Run the language expert in test-review mode** with CHANGE_SCOPE:
   - Use `{language}-expert` (read `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md` Expert Agent column to map detected language → expert agent name) in test-review mode.
   - For unsupported languages: skip test review or use `general-code-reviewer`.
   - **CRITICAL — provide CHANGE_SCOPE** (files AND specific line ranges). See `${CLAUDE_PLUGIN_ROOT}/skills/code-review-modes/SKILL.md` §CHANGE_SCOPE for scope rules — the canonical "added or modified" instruction lives there; do not inline it.
   - If scope is explicit file paths, instruct: "Provide comprehensive test coverage review for these files."
2. **Validate scope of recommendations** (when using CHANGE_SCOPE):
   - Verify each recommendation's source location is within CHANGE_SCOPE.
   - Filter out recommendations targeting code outside the line ranges; log for transparency.
3. **Decide which recommendations to apply**:
   - **Interactive**: present recommendations grouped by priority (LOW/MEDIUM/HIGH) with explanations. Ask the user before applying any. NEVER modify files without permission.
   - **Non-interactive Decision Framework**:

     ```
     CRITICAL priority: ALWAYS implement
     HIGH priority: ALWAYS implement
     MEDIUM priority: Implement if it covers a meaningful changed code path
     LOW priority: Implement only if trivially simple (< 10 lines) and adds clear value
     ```

   - Log every decision (implemented + skipped) with rationale.

4. **Implement accepted recommendations** — spawn a sub-agent. DO NOT modify source files. **Agent delivery resilience**: if the sub-agent sends an `idle_notification` without content, prompt it via SendMessage using its agent ID (not name); if still no delivery, respawn once; if respawn fails, apply recommendations directly or document the gap.
5. **Run tests**:
   - Run only affected tests if tooling supports it; otherwise run all tests.
   - On failure: retry up to 2 times via the sub-agent. If still failing, revert to the pre-step checkpoint and continue (non-interactive) or ask the user how to proceed (interactive).
6. **Show diff** of test changes (interactive: ask whether to keep). Commit if kept: `git add <test-files> && git commit -m "Add/improve tests"`.

### Step 3: Source Code Simplification

1. **Create checkpoint commit**: `git add -u && git commit -m "Checkpoint before source simplification"` (skip if nothing to commit).
2. **Pre-Spawn Verification**: output the verification table matching the contract from Step 0. If skipping any agent, log the reason.
3. **Run the language expert in code-style-review mode on SOURCE files only**:
   - Use `{language}-expert` (read `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md` Expert Agent column) in code-style-review mode.
   - For unsupported languages: use `general-code-reviewer`.
   - **Add domain experts if detected in Step 0**:
     - ML training / model code → `ml-pipeline-reviewer`.
     - Any other domain match → the Expert Agent named in `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md`.
   - Provide CHANGE_SCOPE filtered to source files only. Tell the agent: focus on source files (not tests).
4. **Validate scope of recommendations** (filter to CHANGE_SCOPE; log filtered).
5. **Decide which recommendations to apply**:
   - **Interactive**: present grouped by priority; ask before applying.
   - **Non-interactive Decision Framework (Liberal)**:

     ```
     CRITICAL/HIGH: ALWAYS implement
     MEDIUM: Implement unless it risks changing behavior
     LOW: Implement if it improves readability — code simplification is generally preferred

     Skip only if:
     - The change risks altering runtime behavior
     - The simplification makes the code LESS clear (rare)
     ```

   - Log every decision with rationale.

6. **Implement accepted recommendations** — DO NOT modify test files.
7. **Run tests** after simplification:
   - On failure: retry once via sub-agent. If still failing after retry, `git reset --hard <checkpoint-commit>` and continue. **Maximum 2 retry attempts** total.
8. **Show diff** of source changes (interactive: ask whether to keep). Commit if kept (already committed by checkpoint).

### Step 4: Test Code Simplification

1. **Create checkpoint commit**: `git add -u && git commit -m "Checkpoint before test simplification"` (skip if nothing to commit).
2. **Run the language expert in code-style-review mode on TEST files only**:
   - Use `{language}-expert` (same registry mapping) in code-style-review mode.
   - For unsupported languages: use `general-code-reviewer`.
   - Provide CHANGE_SCOPE filtered to test files only. Tell the agent: focus on simplifications that improve clarity and readability — tests should remain explicit and easy to understand.
3. **Validate scope of recommendations** (filter to CHANGE_SCOPE; log filtered).
4. **Decide which recommendations to apply**:
   - **Interactive**: present grouped by priority; ask before applying.
   - **Non-interactive**: focus on deduplication and clarity. Implement simplifications that reduce redundancy or make test intent clearer. Skip only if the simplification makes intent LESS clear or removes important non-duplicated setup.
   - Log every decision with rationale.
5. **Implement accepted recommendations** — DO NOT modify source files.
6. **Run tests**:
   - On failure: retry once. If still failing after retry, `git reset --hard <checkpoint-commit>` and continue. **Maximum 2 retry attempts** total.
7. **Show diff** of test changes (interactive: ask whether to keep).

### Step 5: Coding Guidelines Review

1. **Use the built-in Explore agent** (`subagent_type: Explore`) to find coding guidelines:
   - Search for: CONTRIBUTING.md, .editorconfig, style guides, CLAUDE.md rules.
   - Only search within the project scope.
2. **If guidelines found**:
   - Show guidelines summary.
   - Review changed files against guidelines.
   - **Decide which fixes to apply**:
     - **Interactive**: list specific violations with proposed fixes; ask before applying.
     - **Non-interactive**: auto-apply guideline fixes (guidelines always take precedence over simplifier suggestions). Log what was changed and why.
   - Stay within initial scope.
   - Run tests after changes — retry once on failure, then revert guideline changes and continue.
   - Commit: `git add -u && git commit -m "Apply coding guidelines"`.
3. **If no guidelines found**: log "No coding guidelines found in codebase".

### Step 6: Formatting

1. **Run the appropriate formatter(s)** based on detected project type:
   - **Python**: `ruff format .` / `black .`, or project-specific formatter
   - **TypeScript**: `npx prettier --write .` or project-specific
   - For mixed projects: run all applicable formatters.
2. **Handle formatter errors gracefully**: if formatter fails or is not configured, log the error and continue. Do NOT stop the workflow.
3. **Show formatting diff** (`git diff`). Formatting changes are usually numerous — summarize instead of showing all.
4. **Commit** in a separate commit: `git add -u && git commit -m "Apply code formatting"`.

### Step 7: Verification + Summary Report

1. **Final test run**: full test suite. Report results.
2. **Build verification**:
   - Python: project-specific build/test command (e.g. `uv run pytest`)
   - TypeScript: `npm run typecheck && npm test`
3. **Generate summary report**:

   ```
   ## Polish-Code Summary

   ### Commits Created
   [git log --oneline <STARTING_COMMIT>..HEAD]

   ### Changes Summary
   - Tests added/modified: [count]
   - Source files simplified: [count]
   - Test files simplified: [count]
   - Data annotation fixes: [count]
   - Coding guideline fixes: [count]
   - Formatting changes: [count]

   ### Decision Log (non-interactive only)
   [Consolidated decisions from Steps 2-6]

   ### Final Status
   - Tests: PASS/FAIL
   - Build: PASS/FAIL

   ### Total Diff
   [git diff --stat <STARTING_COMMIT> HEAD]
   ```

   The Decision Log section is included only in non-interactive mode.

## Important Guidelines

- **Always show diffs** at each major step; interactive mode requires user approval before proceeding.
- **Create commits** at each major step for easy rollback.
- **Selective staging only**: use `git add -u` exclusively — never `git add -A` or `git add .` (avoids committing local config and `~/.claude/thoughts/`).
- **Continue on failures**: don't stop the workflow except on baseline test failure (Step 0).
- **Run affected tests only** when tooling supports it; otherwise run all tests.
- **Stay within scope**: only modify files in the initial scope.
- **Retry limit**: maximum 2 attempts when simplification breaks tests; revert checkpoint after exhaustion.
- **Use TodoWrite tool** to create and track the workflow steps.
- **Guidelines > Simplifier**: coding guidelines take precedence over simplifier suggestions.
- **Clarity over cleverness**: especially for test simplification.
- **CRITICAL: Change-level scope enforcement** — when scope is branch-based or staged:
  - Sub-agents must ONLY analyze and recommend changes within the CHANGE_SCOPE line ranges.
  - Recommendations for unchanged code (even in touched files) are OUT OF SCOPE.
  - Filter and log out-of-scope recommendations: "Filtered out-of-scope recommendation: [name] for [file:lines]".
  - If >50% of recommendations are filtered, warn (or log in non-interactive mode): "Many recommendations filtered as out-of-scope. Consider running /polish-code with explicit file paths."
- **Decision logging is mandatory in non-interactive mode**: every autonomous decision (implement / skip / revert) must be logged with rationale.

## Error Handling Strategy

| Error                                      | Action                                             |
| ------------------------------------------ | -------------------------------------------------- |
| Baseline tests fail (Step 0)               | HARD STOP — report and exit                        |
| Tests fail after enhancement (Step 2)      | Retry up to 2 times → revert checkpoint → continue |
| Tests fail after simplification (Step 3/4) | Retry up to 2 times → revert checkpoint → continue |
| Data annotation validation fails (Step 5)  | Log error → continue                               |
| Tests fail after guidelines (Step 6)       | Retry once → revert changes → continue             |
| Formatter fails (Step 7)                   | Log error → continue                               |
| Build fails (Step 8)                       | Report in summary — user must investigate          |

## Sub-agent Usage

Use these sub-agents via the Agent tool:

- Built-in `Explore` agent — finding coding guidelines.
- `{language}-expert` in test-review mode — test enhancement (resolve via `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md`).
- `{language}-expert` in code-style-review mode — code style review (same registry).
- Domain experts (e.g., `ml-pipeline-reviewer` for ML training code) — see `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md`.

Always provide clear, specific prompts including:

- What files to process (with CHANGE_SCOPE)
- What the goal is
- Any special instructions (e.g., "only if it improves clarity" for tests)

---

Begin by parsing arguments, creating a TODO list, and starting Step 0.
