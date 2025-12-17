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
   - If there are uncommitted changes, create a safety commit: `git add -A && git commit -m "Safety commit before tidy-up"`
3. **Detect project type(s)**:
   - Look for `pyproject.toml` (Python)
   - Store the detected type(s) for later steps
4. **Run baseline tests**:
   - Use the appropriate test command for the project type
   - If tests fail, STOP and report to user
   - This establishes the baseline - all subsequent test runs must pass

### Step 1: Test Enhancement

1. **Identify changed source files** (based on scope)
2. **Run appropriate test Reviewer sub-agent**:
   - For Python files: Use `python-test-reviewer` sub-agent
   - Provide the sub-agent with:
     - The scope of files to test
     - Instruction: "Ensure tests follow naming conventions and provide comprehensive coverage"
3. **Get permission from the user before implementing recommendations**
   - Present the user with the test recommendations:
     - Display the names of the tests (the names should be self explanatory)
     - Group the tests by the module/method that they are testing
     - For each test give a priority category (LOW, MEDIUM, HIGH) and a brief explanation as to why
   - Before making any changes ask the user whether they would like to implement the recommendations
   - NEVER make changes to files without user permission
4. **Implement recommendations**
   - Spin up a new subtask agent to implement the changes that have been approved by the user.
   - DO NOT make changes to source files.
5. **Run tests** after they've been written:
   - Run only affected tests if tooling supports it, otherwise run all tests
   - If tests fail, report to user and ask how to proceed
6. **Run coverage tools** if available:
   - Show coverage results to user
7. **Show diff of test changes**:
   - Show the user the names of all of the tests that were newly added or modified and group them by module name. This is so the user can see precisely what functionality is covered by the tests. It should be clear which tests are new and which are modified
   - Use `git diff` to show what changed
   - Ask user: "Do you want to keep these test changes?"
   - If no: `git restore <test-files>` to revert
8. **Create commit** if changes accepted:
   - `git add <test-files> && git commit -m "Add/improve tests for tidy-up"`

### Step 2: Source Code Simplification

1. **Create checkpoint commit**:
   - `git add -A && git commit -m "Checkpoint before source simplification"`
2. **Identify source files** (exclude test files):
   - Filter scope to only source files (e.g., `src/**`, exclude `tests/**`)
3. **Run appropriate simplification reviewer sub-agent on SOURCE files only**:
   - For Python: Use `python-code-simplification-reviewer` sub-agent
   - Provide explicit instruction: "Provide simplification review on ONLY source files (not test files)"
4. **Get permission from the user before implementing recommendations**
   - Present the user with the simplification recommendations:
     - Group recommendations by priority category (LOW, MEDIUM, HIGH) and a brief explanation as to why they have been given that category.
   - Before making any changes ask the user whether they would like to implement the recommendations
   - NEVER make changes to files without user permission.
5. **Implement recommendations**
   - Spin up a new subtask agent to implement the changes that have been approved by the user.
   - DO NOT make changes to test files.
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

### Step 3: Test Code Simplification

1. **Create checkpoint commit**:
   - `git add -A && git commit -m "Checkpoint before test simplification"`
2. **Identify test files** only:
   - Filter scope to only test files (e.g., `tests/**`, files beginning in `test_*.py` etc.)
3. **Run appropriate simplification-reviewer sub-agent on TEST files only**:
   - For Python: Use `python-code-simplification-reviewer` sub-agent
   - **Critical instruction to sub-agent**: "Review ONLY test files. Focus on simplications that improve clarity and readability. Tests should remain explicit and easy to understand. Do not over-optimize."
4. **Get permission from the user before implementing recommendations**
   - Present the user with the simplification recommendations:
     - Group recommendations by priority category (LOW, MEDIUM, HIGH) and a brief explanation as to why they have been given that category.
   - Before making any changes ask the user whether they would like to implement the recommendations
   - NEVER make changes to files without user permission.
5. **Implement recommendations**
   - Spin up a new subtask agent to implement the changes that have been approved by the user.
   - DO NOT make changes to source files.
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

### Step 4: Formatting

1. **Run appropriate formatter(s)** based on detected project type:
   - **Python**: `uv run ruff format`
2. **Handle formatter errors gracefully**:
   - If formatter fails or is not configured:
     - Log the error
     - Report to user: "Formatter failed: <error>. Continuing with remaining steps."
     - Do NOT stop the workflow
3. **Create separate commit for formatting**:
   - `git add -A && git commit -m "Apply code formatting"`

### Step 5: Post-flight Validation

1. **Final test run**:
   - Run full test suite
   - Report results
   - If tests fail: Report to user with details
2. **Build verification**:
   - Run appropriate build command if it exists
   - Report results
3. **Generate summary report**:
   - List all commits created during tidy-up
   - Show `git log --oneline -<n>` where n is the number of commits made
   - Summarize:
     - Files changed
     - Tests added/modified
     - Source files simplified
     - Test files simplified
     - Formatting applied
     - Final test/build status
   - Show total diff stat: `git diff --stat <starting-commit> HEAD`

## Important Guidelines

- **Always show diffs** at each major step and get user approval before proceeding
- **Create commits** at each major step for easy rollback
- **Continue on failures** - Don't stop the workflow, report issues and continue
- **Run affected tests only** when tooling supports it (otherwise run all tests)
- **Stay within scope** - Only modify files in the initial scope
- **Retry limit** - Maximum 2 attempts when simplification breaks tests
- **Use TodoWrite tool** to create and track the workflow steps
- **Clarity over cleverness** - Especially for test simplification

## Error Handling Strategy

- **Tests fail during pre-flight**: STOP, cannot establish baseline
- **Tests fail after test writing**: Report, ask user how to proceed
- **Tests fail after simplification**: Retry once, then revert, ask user to continue
- **Formatter fails**: Log, report, continue
- **Build fails**: Report to user, this is final validation

## Sub-agent Usage

You will use these sub-agents via the Task tool:
- `python-test-reviewer`: For test enhancement review
- `python-code-simplification-reviewer`: For code simplification review

Always provide clear, specific prompts to sub-agents including:
- What files to process
- What the goal is
- Any special instructions (e.g., "only if it improves clarity" for tests)

---

Begin by parsing arguments, creating a TODO list, and starting Step 0.
