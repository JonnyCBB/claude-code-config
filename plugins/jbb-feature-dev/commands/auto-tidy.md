---
argument-hint: [scope]
description: Non-interactive code tidy-up with autonomous decision-making and formatting
---

# Auto-Tidy Command

You are performing a non-interactive, autonomous code tidy-up workflow. Follow this workflow exactly. Every decision must be logged with rationale — no user prompts.

## Argument Parsing

Arguments provided: `$ARGUMENTS`

Parse the arguments to determine:

- **Scope**: What code to tidy up
  - If `--branch <branch>` or `-b <branch>`: Compare current branch against specified branch
  - If `--staged` or `-s`: Only staged changes
  - If file/directory paths provided: Specific files/directories
  - If no arguments: Default to change-level scope (current branch vs auto-detected base branch)
- **No interactive fallback** — if no scope can be determined, use current branch vs base branch

## Workflow Overview

Execute the following steps in order. Create a TODO list at the start to track progress.

```
Step 0: Pre-flight (safety commit, detect project, baseline tests)
   ↓
Step 1: Extract Change-Level Scope
   ↓
Step 2: Agent Verification Contract
   ↓
Step 3: Test Enhancement (autonomous)
   ↓
Step 4: Source Code Simplification (autonomous, liberal)
   ↓
Step 5: Test Code Simplification (autonomous, liberal)
   ↓
Step 6: Data Annotation Review (auto-apply)
   ↓
Step 7: Coding Guidelines Review (auto-apply)
   ↓
Step 8: Formatting
   ↓
Step 9: Test Suite & Build Verification + Summary Report
```

---

### Step 0: Pre-flight Checks

1. **Record starting commit**: `STARTING_COMMIT=$(git rev-parse HEAD)`
2. **Log scope** — output what scope will be used (no confirmation needed)
3. **Safety commit**: If there are uncommitted changes:
   - Stage only tracked files: `git add -u`
   - Create commit: `git commit -m "Safety commit before auto-tidy"`
   - If working tree is clean, skip
4. **Detect project type(s)**:
   - Look for `pom.xml` (Java/Maven), `build.sbt` (Scala/sbt), `package.json` (Node), `pyproject.toml`/`setup.py` (Python)
   - For mixed projects, prefer Scala/sbt
   - Store the detected type(s) for later steps
5. **Detect base branch**:
   - Try `git symbolic-ref refs/remotes/origin/HEAD` to get default branch
   - Fallback to `master` or `main`
   - Store as `BASE_BRANCH`
6. **Run baseline tests**:
   - Use the appropriate test command for the project type
   - **HARD STOP if tests fail** — report to user, cannot proceed
   - This establishes the baseline — all subsequent test runs must pass

### Step 1: Extract Change-Level Scope

**Only applies when scope is `--branch <branch>`, `--staged`, or default (no arguments).**

If scope is explicit file/directory paths, skip this step and use file-level scope for all subsequent steps.

1. **Get diff with line numbers**:

   ```bash
   # For branch comparison (default or explicit)
   git diff <BASE_BRANCH>...HEAD --unified=0 --no-color

   # For staged changes
   git diff --cached --unified=0 --no-color
   ```

2. **Parse diff into CHANGE_SCOPE**:
   Extract file paths and line ranges from the diff output. Create a structured scope:

   ```
   CHANGE_SCOPE:
   - file: src/main/java/com/example/UserService.java
     changes:
       - lines: 45-52 (added)
       - lines: 102-105 (modified)
   - file: src/main/java/com/example/OrderService.java
     changes:
       - lines: 23-30 (added)
   ```

3. **Store CHANGE_SCOPE** for use in Steps 3, 4, 5

4. **Log scope summary**:
   - Show count of files changed
   - Show total lines added/modified
   - No confirmation needed

### Step 2: Agent Verification Contract

Create an explicit agent contract based on project type:

**Language-based agents** (from `commands/shared/language-agent-registry.md`):

- Select test reviewer and code simplification reviewer for each detected language

Reference `commands/shared/agent-verification-pattern.md` for the full pattern.

```
## Agent Type Verification

Based on the project type detected, I will spawn:

**Language-based agents:**
- [test-reviewer for language]
- [code-simplification-reviewer for language]

Total unique agents: [N]

⚠️ This list is my CONTRACT for Steps 3, 4, and 5.
```

### Step 3: Test Enhancement (Autonomous)

1. **Run appropriate test reviewer sub-agent** with CHANGE_SCOPE (see `commands/shared/language-agent-registry.md`):
   - For Java files: Use `java-test-reviewer` sub-agent
   - For Python files: Use `python-test-reviewer` sub-agent
   - For TypeScript/JavaScript files: Use `typescript-test-reviewer` sub-agent
   - For unsupported languages: Use `general-code-reviewer`
   - **CRITICAL — Provide the sub-agent with CHANGE_SCOPE**:
     - The CHANGE_SCOPE from Step 1 (files AND specific line ranges)
     - Explicit instruction: "ONLY recommend tests for code that was ADDED or MODIFIED in the specified line ranges. Do NOT recommend tests for unchanged code in these files."
   - If scope was explicit file paths (not branch/staged), use file-level scope

2. **Autonomous Decision Framework:**

   ```
   CRITICAL priority: ALWAYS implement
   HIGH priority: ALWAYS implement
   MEDIUM priority: Implement if it covers a meaningful code path that was changed
   LOW priority: Implement only if trivially simple (< 10 lines) and adds clear value
   ```

3. **Log decisions with rationale (REQUIRED):**

   ```
   ## Test Enhancement Decisions

   Implementing:
   - ✅ [CRITICAL] testUserAuthenticationFailure — covers changed auth logic
   - ✅ [HIGH] testNullInputHandling — covers new validation code
   - ✅ [MEDIUM] testEdgeCaseEmptyList — changed code path, low effort

   Skipping:
   - ⏭️ [LOW] testToStringFormat — cosmetic, not testing changed behavior
   ```

4. **Validate scope of recommendations** (when using CHANGE_SCOPE):
   - For each test recommendation, verify the source code location is within CHANGE_SCOPE
   - Filter out any recommendations targeting code outside the specified line ranges
   - Log filtered recommendations for transparency

5. **Implement accepted recommendations** — DO NOT modify source files

6. **Run tests** — if fail, retry up to 3 times, then revert checkpoint and continue:

   ```
   If tests fail after 3 retries:
   - git reset --hard <pre-step-3-commit>
   - Log: "Test enhancement caused failures after 3 retries. Reverted. Continuing."
   ```

7. **Create commit** if changes kept: `git add -u && git commit -m "Add/improve tests (auto-tidy)"`

### Step 4: Source Code Simplification (Autonomous, Liberal)

1. **Create checkpoint commit**: `git add -u && git commit -m "Checkpoint before source simplification"` (skip if nothing to commit)

2. **Run appropriate simplification sub-agent** with CHANGE_SCOPE — source files only (see `commands/shared/language-agent-registry.md`):
   - For Java: Use `java-code-simplification-reviewer` sub-agent
   - For Python: Use `python-code-simplification-reviewer` sub-agent
   - For TypeScript/JavaScript: Use `typescript-code-simplification-reviewer` sub-agent
   - For unsupported languages: Use `general-code-reviewer`
   - **CRITICAL — Provide the sub-agent with CHANGE_SCOPE**:
     - Filtered to source files only
     - Explicit instruction: "ONLY recommend simplifications for code that was ADDED or MODIFIED in the specified line ranges. Do NOT recommend simplifications for unchanged code. Focus on source files only (not test files)."

**REQUIRED: Pre-Spawn Verification**

Before spawning simplification agents, output verification table matching contract from Step 2. If skipping any agent, provide reason.

Reference: See `commands/shared/agent-verification-pattern.md` for the full pattern.

3. **Autonomous Decision Framework (Liberal):**

   ```
   CRITICAL/HIGH: ALWAYS implement
   MEDIUM: Implement unless it risks changing behavior
   LOW: Implement if it improves readability at all — code simplification is generally preferred

   Only skip if:
   - The change risks altering runtime behavior
   - The simplification makes the code LESS clear (rare)
   ```

4. **Log decisions with rationale (REQUIRED)** — same format as Step 4

5. **Validate scope of recommendations** (when using CHANGE_SCOPE):
   - For each recommendation, verify the code location is within CHANGE_SCOPE
   - Filter out any recommendations targeting code outside the specified line ranges
   - Log filtered recommendations for transparency

6. **Implement accepted recommendations** — DO NOT modify test files

7. **Run tests** — retry up to 3 times on failure, then revert to checkpoint:

   ```
   git reset --hard <checkpoint-commit>
   ```

   Log: "Source simplification caused test failures. Reverted changes. Continuing."

8. **Create commit** if changes kept: `git add -u && git commit -m "Simplify source code (auto-tidy)"`

### Step 5: Test Code Simplification (Autonomous, Liberal)

1. **Create checkpoint commit**: `git add -u && git commit -m "Checkpoint before test simplification"` (skip if nothing to commit)

2. **Run appropriate simplification sub-agent** with CHANGE_SCOPE — test files only (see `commands/shared/language-agent-registry.md`):
   - Same language-agent mapping as Step 4
   - **CRITICAL — Provide the sub-agent with CHANGE_SCOPE**:
     - Filtered to test files only
     - Explicit instruction: "ONLY recommend simplifications for TEST code that was ADDED or MODIFIED in the specified line ranges. Focus on simplifications that improve clarity and readability."

3. **Autonomous Decision Framework:**

   ```
   Focus on deduplication and clarity
   Implement simplifications that reduce redundancy
   Implement simplifications that make test intent clearer

   Only skip if:
   - The simplification makes test intent LESS clear
   - The simplification removes important test setup that isn't truly duplicated
   ```

4. **Log decisions with rationale (REQUIRED)** — same format as Step 3

5. **Implement accepted recommendations** — DO NOT modify source files

6. **Run tests** — retry up to 3 times on failure, then revert to checkpoint:

   ```
   git reset --hard <checkpoint-commit>
   ```

   Log: "Test simplification caused test failures. Reverted changes. Continuing."

7. **Create commit** if changes kept: `git add -u && git commit -m "Simplify test code (auto-tidy)"`

### Step 6: Data Annotation Review (Auto-Apply)

1. **Detect schema files in scope**:
   - Scala files with `@BigQueryType`, `@description`, `saveAsTypedParquetFile`, or `ParquetType`
   - Avro schema files (\*.avsc)
   - Protobuf files (\*.proto) with metadata annotations
   - YAML/dbt files with policy annotations

2. **If schema files found**:
   - Run: `python ${CLAUDE_PLUGIN_ROOT}/skills/data-annotation/scripts/validate_annotations.py --recursive --format json <scope>`
   - Launch `data-annotation-reviewer` subagent

3. **Auto-apply fixes by severity:**

   ```
   Critical (missing GDPR annotations): Always fix
   Major (incorrect semantic types): Always fix
   Minor (style/consistency): Agent judgment, bias toward fixing
   ```

4. **Log what was changed and why**

5. **Create commit** if changes made: `git add -u && git commit -m "fix: update data annotations (auto-tidy)"`

6. **If no schema files found**: log "No schema files in scope, skipping data annotation review"

No test verification needed — annotation changes don't affect runtime behavior.

### Step 7: Coding Guidelines Review (Auto-Apply)

1. **Use Explore agent** (subagent_type: `Explore`) to find coding guidelines/standards:
   - Search for: CONTRIBUTING.md, .editorconfig, style guides, CLAUDE.md rules
   - Only search within the project scope
   - Also check available skills (both project-level and user-level) for domain-specific
     conventions or patterns. These may specify API client architecture patterns, naming
     conventions, or data processing idioms that should be respected during simplification.

2. **If guidelines found**:
   - Review changed files against guidelines
   - Auto-apply guideline fixes (guidelines always take precedence)
   - Log what was changed and why
   - Run tests after changes — retry once on failure, then revert guideline changes
   - Create commit: `git add -u && git commit -m "Apply coding guidelines (auto-tidy)"`

3. **If no guidelines found**: log "No coding guidelines found, skipping"

### Step 8: Formatting

1. **Run appropriate formatter(s)** based on detected project type:
   - **Java/Maven**: `mvn fmt:format`
   - **Scala/sbt**: `sbt scalafmtAll`
   - **Python**: `black .` or project-specific formatter
   - **TypeScript**: `npx prettier --write .` or project-specific
   - For mixed projects: Run all applicable formatters

2. **Handle formatter errors gracefully**:
   - If formatter fails or is not configured: log the error, continue
   - Do NOT stop the workflow

3. **Create commit**: `git add -u && git commit -m "Apply code formatting (auto-tidy)"`

### Step 9: Test Suite & Build Verification + Summary Report

1. **Run full test suite**

2. **Run build verification**:
   - Java: `mvn clean verify`
   - Scala: `sbt clean test`

3. **Generate summary report:**

   ```
   ## Auto-Tidy Summary

   ### Commits Created
   [git log --oneline <STARTING_COMMIT>..HEAD]

   ### Changes Summary
   - Tests added/modified: [count]
   - Source files simplified: [count]
   - Test files simplified: [count]
   - Data annotation fixes: [count]
   - Coding guideline fixes: [count]
   - Formatting changes: [count]

   ### Decision Log
   [Consolidated decisions from Steps 4-8]

   ### Final Status
   - Tests: PASS/FAIL
   - Build: PASS/FAIL

   ### Total Diff
   [git diff --stat <STARTING_COMMIT> HEAD]
   ```

---

## Important Guidelines

- **Selective staging only**: Use `git add -u` exclusively — no other staging commands are permitted
- **Continue on failures**: Only hard stop is baseline test failure (Step 0)
- **Checkpoint-and-revert**: Each major step creates a checkpoint commit; revert on test failure
- **Decision logging is mandatory**: Every autonomous decision must be logged with rationale
- **Stay within scope**: Only modify files in the initial scope
- **Retry limits**: 3 retries for Steps 3/4/5; 1 retry for Step 7
- **Change-level scope enforcement**: Sub-agents must only analyze/recommend for CHANGE_SCOPE
- **Scope validation logging**: Log CHANGE_SCOPE at start of each sub-agent invocation; log filtered recommendations
- **Guidelines > Simplifier**: Coding guidelines take precedence over simplifier suggestions
- **Clarity over cleverness**: Especially for test simplification
- **Use TodoWrite tool**: Create and track the workflow steps
- **No user prompts**: This command is fully autonomous — no confirmation, permission, or input prompts

## Error Handling Strategy

```
| Error                                    | Action                                               |
|------------------------------------------|------------------------------------------------------|
| Baseline tests fail (Step 0)             | HARD STOP — report to user, cannot proceed            |
| Tests fail after enhancement (Step 3)    | Retry up to 3 times → revert checkpoint → continue    |
| Tests fail after simplification (Step 4/5)| Retry up to 3 times → revert checkpoint → continue   |
| Data annotation validation fails (Step 6)| Log error → continue                                 |
| Tests fail after guidelines (Step 7)     | Retry once → revert changes → continue               |
| Formatter fails (Step 8)                | Log error → continue                                 |
| Build fails (Step 9)                    | Report in summary — user must investigate             |
```

## Sub-agent Usage

You will use these sub-agents via the Agent tool:

- Built-in `Explore` agent: For finding coding guidelines
- Language-specific test reviewers: For test enhancement (see `commands/shared/language-agent-registry.md`)
- Language-specific simplification reviewers: For code simplification (see `commands/shared/language-agent-registry.md`)

Always provide clear, specific prompts to sub-agents including:

- What files to process (with CHANGE_SCOPE)
- What the goal is
- Any special instructions

---

Begin by parsing arguments, creating a TODO list, and starting Step 0.
