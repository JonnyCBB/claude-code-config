---
argument-hint: [scope]
description: Comprehensive code tidy-up with tests, simplification, and formatting
---

# Code Tidy-Up Command

You are performing a comprehensive code tidy-up workflow. Follow this workflow exactly and methodically.

## Argument Parsing

Arguments provided: `$ARGUMENTS`

Parse the arguments to determine:

- **Scope**: What code to tidy up
  - If `--branch <branch>` or `-b <branch>`: Compare current branch against specified branch
  - If `--staged` or `-s`: Only staged changes
  - If file/directory paths provided: Specific files/directories
  - If no scope specified: Ask user interactively

## Workflow Overview

Execute the following steps in order. Create a TODO list at the start to track progress.

### Step 0: Pre-flight Checks

1. **Confirm scope with user** - Show what files/changes will be tidied up, ask for confirmation
2. **Check for uncommitted changes**:
   - Run `git status`
   - If there are uncommitted changes, create a safety commit using selective staging:
     - Stage only tracked files: `git add -u`
     - Exclude `~/.claude/thoughts/` directory and local config files (e.g., `.env`, `*.local`, etc.)
     - Create commit: `git commit -m "Safety commit before tidy-up"`
3. **Detect project type(s)**:
   - Look for `pom.xml` (Java/Maven), `build.sbt` (Scala/sbt)
   - For mixed projects, prefer Scala/sbt
   - Store the detected type(s) for later steps
4. **Run baseline tests**:
   - Use the appropriate test command for the project type
   - If tests fail, STOP and report to user
   - This establishes the baseline - all subsequent test runs must pass

### Step 1: Extract Change-Level Scope

**Only applies when scope is `--branch <branch>` or `--staged`.**

If scope is explicit file/directory paths, skip this step and use file-level scope for all subsequent steps.

1. **Get diff with line numbers**:

   ```bash
   # For branch comparison
   git diff <branch>...HEAD --unified=0 --no-color

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

3. **Store CHANGE_SCOPE** for use in Steps 2, 3, and 5 (test enhancement, source simplification, test simplification)

4. **Display scope summary to user**:
   - Show count of files changed
   - Show total lines added/modified
   - Confirm this matches their expectations

### Step 2: Test Enhancement

1. **Identify changed source files** (based on scope)
2. **Run appropriate test reviewer sub-agent** (see `commands/shared/language-agent-registry.md` for full details):
   - For Java files: Use `java-test-reviewer` sub-agent
   - For Python files: Use `python-test-reviewer` sub-agent
   - For TypeScript/JavaScript files: Use `typescript-test-reviewer` sub-agent
   - For unsupported languages: Skip test review or use `general-code-reviewer`
   - **CRITICAL - Provide the sub-agent with CHANGE_SCOPE**:
     - The CHANGE_SCOPE from Step 1 (files AND specific line ranges)
     - Explicit instruction: "ONLY recommend tests for code that was ADDED or MODIFIED in the specified line ranges. Do NOT recommend tests for unchanged code in these files, even if that code lacks test coverage. The goal is to ensure the NEW/CHANGED code is tested, not to achieve comprehensive coverage of the entire file."
   - If scope was explicit file paths (not branch/staged), use file-level scope and instruct: "Provide comprehensive test coverage review for these files."
3. **Get permission from the user before implementing recommendations**
   - **Validate scope of recommendations** (when using CHANGE_SCOPE):
     - For each test recommendation, verify the source code location is within CHANGE_SCOPE
     - Filter out any recommendations targeting code outside the specified line ranges
     - Log filtered recommendations for transparency
   - Present the user with the test recommendations:
     - Display the names of the tests (The names should be self explanatory)
     - Group the tests by the module/method that they are testing
     - For each test give a priority category (LOW, MEDIUM, HIGH) and a brief explanation as to why
   - Before making any changes ask the user whether they would like to implement the recommendations
   - NEVER make changes to files without user permission
4. **Implement recommendations**
   - Spin up a new subtask agent to implement the changes that have been approved by the user
   - DO NOT make any changes to source files
5. **Run tests** after test writer completes:
   - Run only affected tests if tooling supports it, otherwise run all tests
   - If tests fail, report to user and ask how to proceed
6. **Run coverage tools** if available:
   - Java: Try `mvn jacoco:report` or similar
   - Scala: Try `sbt coverage test coverageReport` or similar
   - Show coverage results to user
7. **Show diff of test changes**:
   - Show the user the names of all of the tests that were newly added or modified and group them by module name. This is so the user can see precisely what functionality is covered by the tests. It should be clear which tests are new and which are modified
   - Use `git diff` to show what changed
   - Ask user: "Do you want to keep these test changes?"
   - If no: `git restore <test-files>` to revert
8. **Create commit** if changes accepted:
   - `git add <test-files> && git commit -m "Add/improve tests for tidy-up"`

### Step 3: Source Code Simplification

1. **Create checkpoint commit**:
   - Stage only tracked files: `git add -u`
   - Create commit: `git commit -m "Checkpoint before source simplification"`
2. **Identify source files** (exclude test files):
   - Filter scope to only source files (e.g., `src/main/**`, exclude `src/test/**`)

**REQUIRED: Pre-Spawn Verification**

Before spawning simplification agents, output verification table matching contract from Step 0. If skipping any agent, provide reason and inform user.

Reference: See `commands/shared/agent-verification-pattern.md` for the full pattern.

3. **Run appropriate simplification sub-agent on SOURCE files only** (see `commands/shared/language-agent-registry.md` for full details):
   - For Java: Use `java-code-simplification-reviewer` sub-agent
   - For Python: Use `python-code-simplification-reviewer` sub-agent
   - For TypeScript/JavaScript: Use `typescript-code-simplification-reviewer` sub-agent
   - For unsupported languages: Use `general-code-reviewer`
   - **CRITICAL - Provide the sub-agent with CHANGE_SCOPE**:
     - The CHANGE_SCOPE from Step 1 (files AND specific line ranges), filtered to source files only
     - Explicit instruction: "ONLY recommend simplifications for code that was ADDED or MODIFIED in the specified line ranges. Do NOT recommend simplifications for unchanged code in these files. If unchanged code has issues, ignore them - they are out of scope. Focus on source files only (not test files)."
   - If scope was explicit file paths (not branch/staged), use file-level scope and instruct: "Provide comprehensive simplification review for these source files."
4. **Get permission from the user before implementing recommendations**
   - **Validate scope of recommendations** (when using CHANGE_SCOPE):
     - For each simplification recommendation, verify the code location is within CHANGE_SCOPE
     - Filter out any recommendations targeting code outside the specified line ranges
     - Log filtered recommendations for transparency
   - Present the user with simplification recommendations:
     - Group the recommendations by priority category (LOW, MEDIUM, HIGH) and a brief explanation as to why they have been given that category.
   - Before making any changes ask the user whether they would like to implement the recommendations
   - NEVER make changes to files without user permission
5. **Implement recommendations**
   - Spin up a new subtask agent to implement the changes that have been approved by the user
   - DO NOT make any changes to test files
6. **Run tests** after simplification:
   - Run only affected tests if possible
   - **If tests fail**:
     - Attempt 1: Ask sub-agent to fix
     - Attempt 2: If still failing, `git reset --hard HEAD` to revert to checkpoint
     - Report to user: "Source simplification caused test failures. Reverted changes. Continue with remaining steps?"
     - Maximum 2 retry attempts
7. **Show diff of source changes**:
   - `git diff HEAD~1` to show changes since checkpoint
   - Ask user: "Do you want to keep these source simplifications?"
   - If no: `git reset --hard HEAD~1` to revert
8. **Keep commit** if changes accepted (already committed by checkpoint)

### Step 4: Data Annotation Review

1. **Detect schema files** in scope:
   - Scala files with `@BigQueryType`, `@description`, `saveAsTypedParquetFile`, or `ParquetType`
   - Avro schema files (\*.avsc)
   - Protobuf files (\*.proto) with metadata annotations
   - YAML/dbt files with policy annotations in descriptions

2. **If schema files found**:
   - Run validation script: `python ${CLAUDE_PLUGIN_ROOT}/skills/data-annotation/scripts/validate_annotations.py --recursive --format json <scope>`
   - Launch `data-annotation-reviewer` subagent with validation output and file list
   - Wait for analysis to complete

3. **Present findings**:
   - Summary of issues by severity (Critical, Major, Minor)
   - List of required fixes

4. **Get user permission** before suggesting any annotation changes

5. **If approved**, suggest specific fixes with code examples

6. **Create checkpoint commit** if changes made: `git commit -m "fix: update data annotations for GDPR compliance"`

**Note**: This step does not require test verification since annotation changes don't affect runtime behavior.

### Step 5: Test Code Simplification

1. **Create checkpoint commit**:
   - Stage only tracked files: `git add -u`
   - Create commit: `git commit -m "Checkpoint before test simplification"`
2. **Identify test files** only:
   - Filter scope to only test files (e.g., `src/test/**`, files ending in `Test.java`, `Spec.scala`, etc.)
3. **Run appropriate simplification sub-agent on TEST files only** (see `commands/shared/language-agent-registry.md` for full details):
   - For Java: Use `java-code-simplification-reviewer` sub-agent
   - For Python: Use `python-code-simplification-reviewer` sub-agent
   - For TypeScript/JavaScript: Use `typescript-code-simplification-reviewer` sub-agent
   - For unsupported languages: Use `general-code-reviewer`
   - **CRITICAL - Provide the sub-agent with CHANGE_SCOPE**:
     - The CHANGE_SCOPE from Step 1 (files AND specific line ranges), filtered to test files only
     - Explicit instruction: "ONLY recommend simplifications for TEST code that was ADDED or MODIFIED in the specified line ranges. Do NOT recommend simplifications for unchanged test code. Focus on simplifications that improve clarity and readability. Tests should remain explicit and easy to understand."
   - If scope was explicit file paths (not branch/staged), use file-level scope and instruct: "Provide comprehensive simplification review for these test files, focusing on clarity."
4. **Get permission from the user before implementing recommendations**
   - **Validate scope of recommendations** (when using CHANGE_SCOPE):
     - For each simplification recommendation, verify the code location is within CHANGE_SCOPE
     - Filter out any recommendations targeting code outside the specified line ranges
     - Log filtered recommendations for transparency
   - Present the user with simplification recommendations:
     - Group the recommendations by priority category (LOW, MEDIUM, HIGH) and a brief explanation as to why they have been given that category.
   - Before making any changes ask the user whether they would like to implement the recommendations
   - NEVER make changes to files without user permission
5. **Implement recommendations**
   - Spin up a new subtask agent to implement the changes that have been approved by the user
   - DO NOT make any changes to source files
6. **Run tests** after simplification:
   - **If tests fail**:
     - Attempt 1: Ask sub-agent to fix
     - Attempt 2: If still failing, `git reset --hard HEAD` to revert to checkpoint
     - Report to user: "Test simplification caused failures. Reverted changes. Continue with remaining steps?"
     - Maximum 2 retry attempts
7. **Show diff of test changes**:
   - `git diff HEAD~1`
   - Ask user: "Do you want to keep these test simplifications?"
   - If no: `git reset --hard HEAD~1`

### Step 6: Coding Guidelines Review

1. **Use the built-in Explore agent** (subagent_type: `Explore`) to find coding guidelines:
   - Search for: "coding guidelines", "style guide", "contributing guide", "CONTRIBUTING.md", ".editorconfig", etc.
   - Only search within the project scope
   - Also check available skills (both project-level and user-level) for domain-specific
     conventions or patterns. These may specify API client architecture patterns, naming
     conventions, or data processing idioms that should be respected during simplification.
2. **If guidelines found**:
   - Show guidelines summary to user
   - Review changed files against guidelines
   - **Suggest changes** (do NOT auto-apply):
     - List specific guideline violations
     - Propose fixes
     - Ask user: "Would you like me to apply these guideline fixes?"
   - If user approves:
     - Make changes
     - Stay within initial scope only
     - **Important**: Guidelines take precedence over simplifier suggestions
     - Run tests after changes
     - Show diff
     - Stage only tracked files: `git add -u`
     - Create commit: `git commit -m "Apply coding guidelines"`
3. **If no guidelines found**:
   - Report to user: "No coding guidelines found in codebase"

### Step 7: Formatting

1. **Run appropriate formatter(s)** based on detected project type:
   - **Java/Maven**: `mvn fmt:format`
   - **Scala/sbt**: `sbt scalafmtAll`
   - For mixed projects: Run both
2. **Handle formatter errors gracefully**:
   - If formatter fails or is not configured:
     - Log the error
     - Report to user: "Formatter failed: <error>. Continuing with remaining steps."
     - Do NOT stop the workflow
3. **Show formatting diff**:
   - `git diff`
   - Usually formatting changes are numerous, summarize instead of showing all
4. **Create separate commit for formatting**:
   - Stage only tracked files: `git add -u`
   - Create commit: `git commit -m "Apply code formatting"`

### Step 8: Post-flight Validation

1. **Final test run**:
   - Run full test suite
   - Report results
   - If tests fail: Report to user with details
2. **Build verification**:
   - Run appropriate build command:
     - Java: `mvn clean verify`
     - Scala: `sbt clean test`
   - Report results
3. **Generate summary report**:
   - List all commits created during tidy-up
   - Show `git log --oneline -<n>` where n is the number of commits made
   - Summarize:
     - Files changed
     - Tests added/modified
     - Source files simplified
     - Test files simplified
     - Guidelines applied
     - Formatting applied
     - Final test/build status
   - Show total diff stat: `git diff --stat <starting-commit> HEAD`

## Important Guidelines

- **Always show diffs** at each major step and get user approval before proceeding
- **Create commits** at each major step for easy rollback
- **Selective staging only** - Use `git add -u` to stage only tracked files; NEVER use `git add -A` or `git add .` to avoid committing local config files and the `~/.claude/thoughts/` directory
- **Continue on failures** - Don't stop the workflow, report issues and continue
- **Run affected tests only** when tooling supports it (otherwise run all tests)
- **Stay within scope** - Only modify files in the initial scope
- **Retry limit** - Maximum 2 attempts when simplification breaks tests
- **Use TodoWrite tool** to create and track the workflow steps
- **Guidelines > Simplifier** - Coding guidelines take precedence over simplifier suggestions
- **Clarity over cleverness** - Especially for test simplification
- **CRITICAL: Change-level scope enforcement** - When scope is branch-based or staged:
  - Sub-agents must ONLY analyze and recommend changes for the specific line ranges in CHANGE_SCOPE
  - Recommendations for unchanged code (even in files that were touched) are OUT OF SCOPE
  - Before presenting recommendations to user, verify each one targets code within CHANGE_SCOPE
  - If a recommendation targets code outside CHANGE_SCOPE, FILTER IT OUT and log: "Filtered out-of-scope recommendation: [test/simplification name] for [file:lines]"
- **Scope validation logging** - For debugging scope issues:
  - At the start of each sub-agent invocation, log the CHANGE_SCOPE being passed
  - After receiving recommendations, log how many were filtered as out-of-scope
  - If >50% of recommendations are filtered, warn user: "Many recommendations were filtered as out-of-scope. Consider running /tidy with explicit file paths for comprehensive review."

## Error Handling Strategy

- **Tests fail during pre-flight**: STOP, cannot establish baseline
- **Tests fail after test writing**: Report, ask user how to proceed
- **Tests fail after simplification**: Retry once, then revert, ask user to continue
- **Formatter fails**: Log, report, continue
- **Build fails**: Report to user, this is final validation

## Sub-agent Usage

You will use these sub-agents via the Task tool:

- Built-in `Explore` agent: For finding coding guidelines
- Language-specific test reviewers: For test enhancement review (see `commands/shared/language-agent-registry.md`)
- Language-specific simplification reviewers: For code simplification review (see `commands/shared/language-agent-registry.md`)

Always provide clear, specific prompts to sub-agents including:

- What files to process
- What the goal is
- Any special instructions (e.g., "only if it improves clarity" for tests)

---

Begin by parsing arguments, creating a TODO list, and starting Step 0.
