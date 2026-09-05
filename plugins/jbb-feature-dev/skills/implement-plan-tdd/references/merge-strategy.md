# Branch Targeting and Stacked PR Support

This document defines how `implement-plan-tdd` targets git branches,
including the stacked-PR flow driven by `--scoping-doc`. It is consumed by
SKILL.md Step 2.

**Historical note**: prior versions of this file defined "Strategy C" — a
per-task worktree isolation and merge procedure for parallel RED/GREEN
agents. Per-task worktrees were removed in 0.9.0 (they repeatedly misfired
in orchestrated runs, creating worktrees against the wrong repo, and became
unnecessary once same-file tasks were barred from running concurrently).
All work now happens in the main working directory on a single target
branch; the File Overlap Matrix is the sole parallelism gate (see
`wave-execution-guide.md` Section 4).

---

## 1. Target Branch

All task work is committed on a single `target_branch`, set explicitly by
the orchestrator in SKILL.md Step 2 — never inferred from
`git branch --show-current`:

```bash
# target_branch is set by the orchestrator:
#   - If --scoping-doc with "Stacked PRs" strategy: the plan's branch name
#     from the Branch Chain table
#   - Otherwise: "main" (default behavior)
git checkout "$target_branch"
```

Implementer agents do NOT commit. The orchestrator owns git state: it may
create a checkpoint commit after each wave's integration check passes
(rollback granularity), and the final commit happens via the user or the
calling pipeline's `/commit` stage.

## 2. Git Config Recording

After creating a plan's branch (SKILL.md Step 2), the orchestrator records
metadata for downstream skills:

```bash
# gh CLI reads this for automatic --base detection
git config branch."$target_branch".gh-merge-base "$base_branch"

# rebase-stack reads this for --onto after squash merge
git config branch."$target_branch".stackBaseCommit "$(git rev-parse "$base_branch")"
```

These config values:

- Survive `git rebase` operations
- Survive parent branch deletion
- Are local to the repository (not pushed to remote)
- Follow the `gh` CLI convention for branch base tracking

## 3. Rollback

If a wave fails its integration check and a rollback is required, the
rollback target is the previous checkpoint commit (or the pre-wave commit
if no checkpoints were made).

- **Interactive mode**: present the failing wave, the failing tests, and
  the rollback target hash. NEVER auto-rollback — `git reset --hard`
  discards all of the wave's work; the user must decide.
- **Non-interactive mode**: do NOT auto-rollback. Log the failure with the
  rollback target hash and halt with a non-zero status so the calling
  process knows intervention is required.
