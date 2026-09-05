# Cascade Rebase Algorithm

Reference document for the `/rebase-stack` skill. Defines the sequential bottom-up
rebase algorithm, the `--update-refs` optimization, and the `--onto` form for
squash-merge scenarios.

## 1. Sequential Bottom-Up Algorithm

Process branches in dependency order (branch closest to main first, top of stack last).

### Normal Rebase (Parent Branch Updated)

When the parent branch has new commits but still exists:

```bash
git checkout <branch>
git rebase <parent-branch>
```

Example for chain `master -> feat/plan-1 -> feat/plan-2 -> feat/plan-3`:

```bash
git checkout feat/plan-1
git rebase master

git checkout feat/plan-2
git rebase feat/plan-1

git checkout feat/plan-3
git rebase feat/plan-2
```

### Squash-Merge Rebase (--onto form)

When a parent branch has been squash-merged into its base and deleted, use `rebase --onto`
to skip the orphaned commits:

```bash
# Read the stored divergence point
old_tip=$(git config branch.<branch>.stackBaseCommit)

# Rebase onto the new base, skipping commits from the deleted parent
git rebase --onto <new-base> $old_tip <branch>
```

Example: After `feat/plan-1` is squash-merged into `master`:

```bash
old_tip=$(git config branch.feat/plan-2.stackBaseCommit)
git rebase --onto master $old_tip feat/plan-2

# Update config for the new state
git config branch.feat/plan-2.gh-merge-base master
git config branch.feat/plan-2.stackBaseCommit $(git rev-parse master)
```

### Detecting Squash-Merge

A parent branch was squash-merged if:

1. The parent branch no longer exists locally or remotely, AND
2. The parent's base branch (grandparent) contains a commit with the squash-merge message

Check:

```bash
# Does the parent branch exist?
git rev-parse --verify <parent-branch> 2>/dev/null
# Exit code 128 = branch doesn't exist = likely squash-merged
```

## 2. The --update-refs Optimization (Git 2.38+)

When ALL branches in the stack need a normal rebase (no squash-merge scenarios),
the entire stack can be rebased in a single command:

```bash
git checkout <top-of-stack>
git rebase <stack-base> --update-refs
```

This rebases the top branch and automatically updates all intermediate branch pointers
to their new positions in the rewritten history.

### When to Use --update-refs

| Condition                               | Use --update-refs?                    |
| --------------------------------------- | ------------------------------------- |
| All branches need normal rebase         | Yes                                   |
| Any branch needs --onto (squash-merge)  | No -- fall back to sequential         |
| Git version < 2.38                      | No -- not available                   |
| Branches checked out in other worktrees | No -- those branches won't be updated |

### Git Version Check

```bash
git_version=$(git --version | grep -oE '[0-9]+\.[0-9]+')
if awk "BEGIN{exit !($git_version >= 2.38)}"; then
  echo "update-refs available"
fi
```

### Combining --update-refs with --onto

`--update-refs` IS compatible with `--onto`. However, in the squash-merge scenario,
the `<upstream>` argument to `--onto` only covers a subset of the stack, so intermediate
branches outside that range won't be updated. For mixed scenarios (some branches need
`--onto`, others don't), use sequential rebase.

## 3. Git Config for Stack Metadata

The skill reads and writes per-branch git config values to track stack relationships.

### Config Keys

| Key                             | Purpose                            | Set By                      | Read By                      |
| ------------------------------- | ---------------------------------- | --------------------------- | ---------------------------- |
| `branch.<name>.gh-merge-base`   | Declared parent branch name        | implement-plan-tdd (Plan A) | rebase-stack, `gh pr create` |
| `branch.<name>.stackBaseCommit` | Parent branch SHA at creation time | implement-plan-tdd (Plan A) | rebase-stack (for --onto)    |

### Reading Config

```bash
parent=$(git config branch.feat/plan-2.gh-merge-base)
old_tip=$(git config branch.feat/plan-2.stackBaseCommit)
```

### Updating Config After Rebase

After a successful rebase, update the stored SHA to reflect the new parent state:

```bash
git config branch.<branch>.stackBaseCommit $(git rev-parse <new-parent>)
```

If a squash-merge changed the parent, also update the parent name:

```bash
git config branch.<branch>.gh-merge-base <new-parent-name>
```

### Config Durability

- Git config keys survive `git rebase` (stored by branch name, not SHA)
- Git config keys survive parent branch deletion
- Git config keys are removed when `git branch -d <branch>` deletes the branch itself
- Git config keys are moved when `git branch -m <old> <new>` renames the branch

## 4. Force Push

After rebasing, all affected branches have rewritten history and must be force-pushed.

### Safe Force Push

```bash
# Single branch
git push --force-with-lease --force-if-includes origin <branch>

# Multiple branches (atomic -- all succeed or all fail)
git push --atomic --force-with-lease --force-if-includes origin \
  <branch-1> <branch-2> <branch-3>
```

### Flag Semantics

| Flag                  | Protection                                                                |
| --------------------- | ------------------------------------------------------------------------- |
| `--force-with-lease`  | Refuses if remote ref updated since last fetch                            |
| `--force-if-includes` | Strengthens lease: checks reflog for actual local awareness of remote tip |
| `--atomic`            | All-or-nothing: if any branch push fails, none are pushed                 |

### When Force Push Fails

If `--force-with-lease` rejects the push:

1. Someone else pushed to the branch since your last fetch
2. Run `git fetch origin` to update remote-tracking refs
3. Re-assess whether a rebase is still needed
4. Re-run `/rebase-stack` if needed

## 5. Per-Branch Status Tracking

Track the status of each branch during the cascade:

| Status      | Meaning                                                       |
| ----------- | ------------------------------------------------------------- |
| PENDING     | Not yet processed                                             |
| REBASING    | Currently being rebased                                       |
| DONE        | Successfully rebased                                          |
| CONFLICT    | Rebase stopped due to conflict -- see conflict-handling.md    |
| SKIPPED     | Skipped (blocked by upstream conflict, or already up to date) |
| PUSH_FAILED | Rebase succeeded but push was rejected                        |

On conflict, all downstream branches transition to SKIPPED.
See `conflict-handling.md` for the stop-and-report protocol.
