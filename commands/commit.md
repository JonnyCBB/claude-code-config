---
argument-hint: [--non-interactive]
---

# Commit Changes

You are tasked with creating git commits for the changes made during this session.

## Mode Detection

Parse `$ARGUMENTS` for flags:
- If `$ARGUMENTS` contains `--non-interactive`: Set NON_INTERACTIVE mode
  - Skip Step 3 confirmation — proceed directly to committing
  - Use the same commit planning logic (grouping, messages) but execute without asking
- If `$ARGUMENTS` does not contain `--non-interactive`: Behave exactly as before (interactive mode)

## Process:

1. **Think about what changed:**
   - Review the conversation history and understand what was accomplished
   - Run `git status` to see current changes
   - Run `git diff` to understand the modifications
   - Consider whether changes should be one commit or multiple logical commits

2. **Plan your commit(s):**
   - Identify which files belong together
   - Draft clear, descriptive commit messages
   - Use imperative mood in commit messages
   - Focus on why the changes were made, not just what

3. **Present your plan and execute:**

   **If in NON_INTERACTIVE mode:**
   - Log the planned commits (files and messages) to stdout for traceability
   - Proceed directly to Step 4 (execution) without asking for confirmation

   **If in interactive mode (default):**
   - List the files you plan to add for each commit
   - Show the commit message(s) you'll use
   - Ask: "I plan to create [N] commit(s) with these changes. Shall I proceed?"

4. **Execute upon confirmation:**
   - Use `git add` with specific files (never use `-A` or `.`)
   - Create commits with your planned messages
   - Show the result with `git log --oneline -n [number]`

## Important:
- **Ensure that we attribute AI (e.g. Claude) with the commit**
- Write commit messages as if the user wrote them

## Remember:
- You have the full context of what was done in this session
- Group related changes together
- Keep commits focused and atomic when possible
- The user trusts your judgment - they asked you to commit
