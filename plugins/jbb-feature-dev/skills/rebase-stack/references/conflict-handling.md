# Conflict Handling

Reference document for the `/rebase-stack` skill. Defines the stop-and-report pattern
for handling rebase conflicts during cascade rebase, including conflict detection,
interactive/non-interactive resolution, resumption from partial completion, and rollback.

## 1. Stop-and-Report Pattern

When a rebase conflict occurs during the cascade, the skill STOPS immediately and
reports the conflict. It does not attempt auto-resolution.

### Why Stop?

Rebase conflicts require human judgment — the correct resolution depends on intent
that cannot be inferred from file content alone. Auto-resolution risks silently
discarding changes or creating semantically broken code that passes syntax checks
but fails at runtime.

### Conflict Detection

After running `git rebase`, check the exit code and git state:

```bash
if ! git rebase <args> 2>&1; then
  # Check if it's a conflict (vs. a fatal error)
  if git rev-parse --verify REBASE_HEAD &>/dev/null; then
    # REBASE_HEAD exists = conflict on a specific commit
    conflicting_commit=$(git rev-parse REBASE_HEAD)
    conflicting_files=$(git diff --name-only --diff-filter=U)
    echo "Conflict on commit: $conflicting_commit"
    echo "Conflicted files: $conflicting_files"
  else
    # No REBASE_HEAD = fatal error (not a conflict)
    echo "Fatal rebase error"
  fi
fi
```

### What to Report

When a conflict is detected, report ALL of the following:

1. **Which branch** was being rebased
2. **Which commit** caused the conflict (from `REBASE_HEAD`)
3. **Which files** are conflicted (`git diff --name-only --diff-filter=U`)
4. **The conflict markers** in each file (show relevant sections)
5. **The cascade state** — which branches completed, which are blocked

## 2. Interactive Resolution

In interactive mode (default), present the conflict to the user:

```
Rebase conflict detected on feat/plan-2.

Conflicting commit: a1b2c3d "Add new endpoint handler"
Conflicted files:
  - src/handler.py (both modified)
  - src/config.yaml (both modified)

Options:
  1. Resolve manually: edit the files, then run `git rebase --continue`
  2. Abort this branch: `git rebase --abort` (restores pre-rebase state)
  3. Skip this commit: `git rebase --skip` (drops the conflicting commit)

After resolution, re-run `/rebase-stack --scoping-doc <path>` to continue
with remaining branches.
```

Wait for the user to resolve before proceeding.

## 3. Non-Interactive Resolution

In non-interactive mode (`--non-interactive`), the skill cannot wait for manual input:

1. Abort the failed rebase: `git rebase --abort`
2. Log the conflict details (branch, commit, files)
3. Mark the branch as CONFLICT in the status table
4. Mark all downstream branches as SKIPPED
5. Continue with the force push of any successfully-rebased upstream branches
6. Report the full status table at the end

The user must manually resolve and re-invoke the skill for remaining branches.

## 4. Blast Radius

When branch N in the chain conflicts:

| Branch Position   | Status   | Explanation                                     |
| ----------------- | -------- | ----------------------------------------------- |
| Branches 1..N-1   | DONE     | Already rebased and pushed before the conflict  |
| Branch N          | CONFLICT | Rebase stopped, needs manual resolution         |
| Branches N+1..end | SKIPPED  | Cannot rebase until N is resolved (depend on N) |

**Key property**: Branches earlier in the chain are NOT affected by a downstream
conflict. Their rebase and push are complete and safe.

### Example

Chain: `master -> feat/plan-1 -> feat/plan-2 -> feat/plan-3`

If `feat/plan-2` conflicts:

- `feat/plan-1`: DONE — already rebased onto master and pushed
- `feat/plan-2`: CONFLICT — stopped, `git rebase --abort` applied (in non-interactive)
- `feat/plan-3`: SKIPPED — depends on feat/plan-2, cannot proceed

## 5. Partial Completion and Resumption

The skill supports resumption after a conflict is resolved:

### How Resumption Works

1. User resolves the conflict in branch N manually:
   - Edit conflicted files
   - `git add <resolved-files>`
   - `git rebase --continue`
   - `git push --force-with-lease --force-if-includes origin <branch-N>`
2. User re-runs `/rebase-stack --scoping-doc <path>`
3. The skill re-assesses all branches:
   - Branches 1..N: detected as up-to-date (no-op)
   - Branches N+1..end: detected as needing rebase
4. Only branches that still need rebasing are processed

### Why This Works

The skill is **stateless** — it reads the current git state on each invocation rather
than maintaining a progress file. By checking each branch's relationship to its parent
(is it already rebased? does it need `--onto`?), it naturally skips completed work
and resumes from the first branch that still needs attention.

## 6. Rollback

### Per-Branch Rollback

If a rebase produces unexpected results on a specific branch:

```bash
# Abort an in-progress rebase (restores pre-rebase state)
git rebase --abort

# If the rebase already completed but results are wrong:
# Find the pre-rebase HEAD from reflog
git reflog show <branch>
git reset --hard <pre-rebase-sha>
```

### Full Stack Rollback

There is no single command to roll back the entire stack. Each branch must be
individually restored from reflog. The force-push step is the point of no return
for remote state — after push, the remote has the new history. Other collaborators
who have fetched the pushed branches will need to `git pull --rebase` or
`git reset --hard origin/<branch>`.

**Recommendation**: In interactive mode, review the rebase plan before confirming.
