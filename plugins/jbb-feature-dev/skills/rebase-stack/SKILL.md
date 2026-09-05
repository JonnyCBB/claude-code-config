---
name: rebase-stack
description: >
  Cascade-rebase all branches in a stacked PR chain after any branch is updated.
  Reads the Branch Chain table from a scoping document to determine branch order.
  Handles squash-merge scenarios with git rebase --onto, supports --update-refs
  (Git 2.38+), and uses stop-and-report for conflict handling.
  Use when a stacked PR branch has been updated and downstream branches need rebasing,
  or after a base PR is squash-merged. Trigger phrases (1) "rebase stack"
  (2) "cascade rebase" (3) "rebase stacked PRs" (4) "update stack branches"
  (5) "rebase-stack".
argument-hint: "--scoping-doc PATH [--non-interactive]"
---

# Rebase Stack

Cascade-rebase all branches in a stacked PR chain. Reads the Branch Chain table from
a scoping document, determines the rebase order, and rebases each branch onto its
updated parent — handling both normal updates and squash-merge scenarios.

## Arguments

| Flag                   | Default    | Effect when set                                        |
| ---------------------- | ---------- | ------------------------------------------------------ |
| `--scoping-doc <path>` | (required) | Path to scoping document containing Branch Chain table |
| `--non-interactive`    | off        | Skip confirmations, auto-decide all prompts            |

## Mode Detection

Parse `$ARGUMENTS` for flags:

- `--scoping-doc <path>`: extract path, validate file exists
- `--non-interactive`: enable autonomous mode
- If `--scoping-doc` is not provided: display usage instructions and exit

## Step 1: Parse Scoping Document

1. Read the scoping document at the provided path
2. Locate the `### Branch Chain` table (markdown table under PR Strategy)
3. Parse each row: Plan name, Branch Name, Base Branch, Estimated LOC
4. Validate the chain: ensure no cycles, all base branches resolve
5. Build the ordered branch list (bottom of stack first, top last)

**Expected format** (from map-feature-to-plans output):

| Plan   | Branch Name              | Base Branch              | Estimated LOC |
| ------ | ------------------------ | ------------------------ | ------------- |
| Plan A | feat/stacked-pr-pipeline | master                   | 305           |
| Plan B | feat/stacked-pr-rebase   | feat/stacked-pr-pipeline | 330           |

If the table is missing or malformed, report the error and exit.

## Step 2: Assess Rebase State

For each branch in the chain (bottom-up order):

1. Check if the branch exists locally: `git branch --list <branch>`
2. Check if a remote tracking branch exists: `git ls-remote --heads origin <branch>`
3. Read git config for stack metadata:
   - `git config branch.<branch>.gh-merge-base` — the declared parent branch
   - `git config branch.<branch>.stackBaseCommit` — the parent's SHA at branch creation time
4. Determine rebase mode per branch:
   - **Normal rebase**: parent branch exists and has new commits since `stackBaseCommit`
   - **Squash-merge rebase**: parent branch was deleted (squash-merged to its base) — use `git rebase --onto`
   - **No-op**: branch is already up to date with parent
   - **Missing**: branch doesn't exist locally or remotely — report and skip

## Step 3: Execute Cascade Rebase

Read `references/cascade-rebase.md` for the rebase algorithm.

Process branches in bottom-up order (first branch in chain first):

1. **Check for `--update-refs` optimization**: If ALL branches need normal rebase (no squash-merge cases), and Git version >= 2.38, use the single-command approach:

   ```bash
   git checkout <top-of-stack>
   git rebase <stack-base> --update-refs
   ```

   This rebases the entire stack in one operation. Skip to Step 4.

2. **Sequential rebase** (general case): For each branch in order:
   - Determine the rebase command per `references/cascade-rebase.md`
   - Execute the rebase
   - If conflict: read `references/conflict-handling.md`, follow stop-and-report pattern
   - If success: update git config for the next branch in chain
   - Track status: DONE, CONFLICT, SKIPPED

3. **Interactive confirmation** (unless `--non-interactive`):
   Before executing, display the rebase plan and ask for confirmation:

   ```
   Rebase plan:
   1. git rebase master feat/plan-1
   2. git rebase feat/plan-1 feat/plan-2
   3. git push --force-with-lease --force-if-includes origin feat/plan-1 feat/plan-2

   Proceed? [Y/n]
   ```

## Step 4: Force Push

After all branches are rebased (or after partial completion up to a conflict):

1. Collect all successfully rebased branches
2. Push with safety flags:
   ```bash
   git push --force-with-lease --force-if-includes origin <branch-1> <branch-2> ...
   ```
3. If pushing multiple branches, consider `--atomic` for all-or-nothing semantics
4. Report push results per branch

**Interactive mode**: Ask before force pushing.
**Non-interactive mode**: Push automatically.

## Step 5: Update Git Config

After successful rebase and push, update the stored stack metadata:

For each rebased branch:

```bash
git config branch.<branch>.stackBaseCommit $(git rev-parse <parent-branch>)
```

This ensures the next invocation of `/rebase-stack` has correct divergence points.

## Step 6: Report Results

Display a summary table:

| Branch      | Status           | Details                                         |
| ----------- | ---------------- | ----------------------------------------------- |
| feat/plan-1 | Rebased + Pushed | 3 commits replayed                              |
| feat/plan-2 | Conflict         | Conflict in src/foo.md — see instructions below |
| feat/plan-3 | Skipped          | Blocked by feat/plan-2 conflict                 |

If any conflicts occurred, display resolution instructions from `references/conflict-handling.md`.

## Error Handling

| Error                                    | Action                                                                                |
| ---------------------------------------- | ------------------------------------------------------------------------------------- |
| `--scoping-doc` not provided             | Display usage and exit                                                                |
| Scoping doc file not found               | Report path and exit                                                                  |
| Branch Chain table not found in doc      | Report expected format and exit                                                       |
| Branch doesn't exist locally or remotely | Report, skip branch, continue cascade                                                 |
| Rebase conflict                          | Stop cascade, report conflict details, provide resolution instructions                |
| Force push rejected (lease failed)       | Report that remote branch was updated by someone else, suggest `git fetch` and re-run |
| Git version < 2.38 (for --update-refs)   | Fall back to sequential rebase, log warning                                           |

## Guidelines

- **Scoping document is required** — never auto-detect branches or infer stack structure
- **Bottom-up order** — always rebase from the branch closest to main first
- **Stop on conflict** — never attempt to auto-resolve rebase conflicts
- **Safe force push** — always use `--force-with-lease --force-if-includes`, never bare `--force`
- **Preserve parallel execution** — this skill runs sequentially (rebase is inherently serial), but it must not interfere with other concurrent git operations
- **Update config after success** — always update `stackBaseCommit` after rebase so future invocations work correctly

## Reference Files

| File                              | When to Read            | Purpose                                                                |
| --------------------------------- | ----------------------- | ---------------------------------------------------------------------- |
| `references/cascade-rebase.md`    | Step 3 (execute rebase) | Sequential bottom-up algorithm, --update-refs, --onto for squash merge |
| `references/conflict-handling.md` | Step 3 (on conflict)    | Stop-and-report pattern, conflict detection, resumption, rollback      |
