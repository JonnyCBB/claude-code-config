# Strategy C: Hybrid Merge Procedure

This document defines the merge procedure used in Step 4 of the implement-plan-tdd skill. Strategy C combines worktree isolation with the no-file-overlap guarantee from wave analysis to produce safe, predictable merges.

---

## 1. Strategy C Overview

Strategy C is a hybrid approach that layers two independent safety mechanisms:

1. **No-file-overlap guarantee (primary)**: The wave analysis performed by `create-plan-tdd` ensures that no two tasks within the same wave write to the same file. This means merges within a wave should always be clean. See `wave-analysis-guide.md` Section 4 (File Overlap Detection) for the file overlap matrix and Section 5 (Parallelization Safety Checklist) for the full set of intra-wave safety conditions.

2. **Worktree isolation (defense-in-depth)**: Each agent works in its own git worktree with its own branch. This provides filesystem-level isolation so that even if the wave analysis contains a bug, agents cannot silently overwrite each other's work.

**Why both?** The no-overlap guarantee is what makes merges clean. Worktree isolation is the safety net that catches wave-analysis bugs before they corrupt the main branch. If the wave analysis is correct (and it should be), worktree isolation is redundant. If the wave analysis has a bug, worktree isolation turns a silent data-loss scenario into a loud merge conflict.

---

## 2. Pre-Merge Checklist

Before merging any worktree branch, verify ALL of the following:

- [ ] Agent completed successfully (check agent return status or exit code)
- [ ] Agent committed its changes (run `git log` in the worktree to confirm)
- [ ] Test verification passed for the relevant phase:
  - RED phase: new tests fail as expected, existing tests still pass
  - GREEN phase: all tests pass including the new ones
- [ ] No unexpected files modified (compare `git diff --name-only main` in the worktree against the plan's "Files Touched" for that task)

### Verification Commands

Check that the agent committed changes in a worktree:

```bash
# From the main working directory
git -C "/path/to/worktree-1-1-red" log --oneline -3
```

Check which files the agent modified:

```bash
# Compare worktree branch against main
git diff --name-only main..worktree-1-1-red
```

---

## 3. Merge Procedure (Per-Wave)

After all agents in a wave pass (either all RED agents or all GREEN agents) complete, perform the following merge procedure from the **main working directory**.

### Merge Loop

```bash
# Ensure you are on the main branch in the main working directory
git checkout main

# Define the branches to merge (example: Wave 1 RED pass)
branches=("worktree-1-1-red" "worktree-1-2-red")

# Merge each branch
for branch in "${branches[@]}"; do
  echo "Merging $branch..."
  git merge "$branch" --no-edit
  if [ $? -ne 0 ]; then
    echo "ERROR: Merge conflict on $branch — possible wave-analysis bug"
    # In interactive mode: STOP here and present conflict to user
    # In non-interactive mode: attempt auto-resolution (see Section 5)
    exit 1
  fi
  echo "Successfully merged $branch"
done

# Run full test suite after all branches in this pass are merged
echo "Running test suite..."
# Replace with the project's actual test command
./run-tests.sh
```

### Cleanup After Successful Merge

```bash
# Remove worktrees and delete branches for completed tasks
for branch in "${branches[@]}"; do
  worktree_path=".worktrees/$branch"
  echo "Cleaning up $branch..."
  git worktree remove "$worktree_path"
  git branch -d "$branch"
done
```

### Post-Merge Verification

After merging all branches in a pass and cleaning up:

- [ ] All expected branches are merged (check `git log --oneline`)
- [ ] Test suite passes with expected results for the current phase
- [ ] No orphaned worktrees remain (check `git worktree list`)

---

## 4. Merge Sequencing Within a Wave

Each wave has two passes, and they must be merged in this exact order:

### Pass 1: RED Merge

1. Merge all RED worktree branches (e.g., `worktree-1-1-red`, `worktree-1-2-red`)
2. Run the full test suite
3. **Expected result**: All NEW tests from this wave FAIL. All previously-existing tests PASS.

```bash
# Merge all RED branches for Wave 1
for branch in worktree-1-1-red worktree-1-2-red; do
  git merge "$branch" --no-edit
done

# Run tests — new tests should fail, existing tests should pass
./run-tests.sh
```

### Pass 2: GREEN Merge

1. Merge all GREEN worktree branches (e.g., `worktree-1-1-green`, `worktree-1-2-green`)
2. Run the full test suite
3. **Expected result**: ALL tests PASS, including the new tests from this wave.

```bash
# Merge all GREEN branches for Wave 1
for branch in worktree-1-1-green worktree-1-2-green; do
  git merge "$branch" --no-edit
done

# Run tests — all tests should pass
./run-tests.sh
```

### Why This Sequencing Matters

This RED-then-GREEN order enforces the TDD discipline at the integration level:

1. **RED merge proves the tests are meaningful.** If the new tests pass before the implementation is merged, something is wrong — either the tests are trivially passing or the implementation leaked into the RED phase.
2. **GREEN merge proves the implementation satisfies the tests.** The implementation is only accepted if it makes the previously-failing tests pass.
3. **Separation prevents false greens.** If RED and GREEN were merged together, you could not distinguish between "tests pass because the implementation is correct" and "tests pass because they were written to match a pre-existing state."

---

## 5. Conflict Handling

### Expected Outcome

No conflicts. The wave analysis in `create-plan-tdd` guarantees that no two tasks within the same wave write to the same file (see `wave-analysis-guide.md` Section 4: File Overlap Detection). If the wave analysis is correct, every merge is a fast-forward or a clean merge of non-overlapping files.

### If a Conflict Occurs

A merge conflict within a wave indicates a **bug in the wave analysis**. Two tasks were placed in the same wave despite writing to the same file.

#### Interactive Mode

1. Log the conflict details:
   ```bash
   echo "WAVE ANALYSIS BUG: Merge conflict during merge of $branch"
   echo "Conflicting files:"
   git diff --name-only --diff-filter=U
   echo "Wave: $wave_number, Tasks involved: $task_ids"
   ```
2. **STOP.** Present the conflict to the user with full context (which files, which tasks, which wave).
3. Ask the user how to proceed. Do NOT auto-resolve.

#### Non-Interactive Mode

1. Log the conflict details (same as above).
2. Abort the failed merge:
   ```bash
   git merge --abort
   ```
3. Re-run the conflicting tasks sequentially instead of in parallel:
   ```bash
   echo "Re-running conflicting tasks sequentially to avoid overlap"
   # Run the first task, merge it, then run the second task
   ```
4. Log the mismatch between the wave analysis and actual file modifications for post-mortem review.

---

## 6. Rollback Procedure

If a wave fails integration testing after all its branches have been merged (i.e., the test suite produces unexpected failures), a rollback may be necessary.

### Identify the Pre-Wave Commit

```bash
# Find the commit just before this wave's merges began
git log --oneline -10
# Look for the last commit that was NOT a merge from this wave
# Example output:
#   a1b2c3d Merge branch 'worktree-1-2-green'
#   e4f5g6h Merge branch 'worktree-1-1-green'
#   i7j8k9l Merge branch 'worktree-1-2-red'
#   m0n1o2p Merge branch 'worktree-1-1-red'
#   q3r4s5t <-- this is the pre-wave commit
```

### Interactive Mode

1. Present the situation to the user:
   - Which wave failed
   - Which tests are failing unexpectedly
   - The pre-wave commit hash that would be the rollback target
2. Ask the user whether to rollback or debug.
3. **NEVER auto-rollback.** Rolling back is destructive — it discards all work from the wave's agents. The user must make this decision.

If the user chooses to rollback:

```bash
git reset --hard q3r4s5t
```

### Non-Interactive Mode

1. Do **NOT** auto-rollback. This is too destructive to perform without human oversight.
2. Log the failure with full details:
   ```bash
   echo "WAVE INTEGRATION FAILURE: Wave $wave_number failed post-merge testing"
   echo "Pre-wave commit: $pre_wave_commit"
   echo "Failing tests:"
   # Include test output
   ```
3. **STOP.** Exit with a non-zero status code so the calling process knows intervention is required.

---

## 7. Worktree Naming Convention

### Pattern

```
worktree-{wave}-{task}-{phase}
```

Where:
- `{wave}` is the wave number (1, 2, 3, ...)
- `{task}` is the task number within the wave (1, 2, 3, ...)
- `{phase}` is either `red` or `green`

### Examples

| Worktree / Branch Name | Meaning |
|------------------------|---------|
| `worktree-1-1-red`    | Wave 1, Task 1, RED phase |
| `worktree-1-1-green`  | Wave 1, Task 1, GREEN phase |
| `worktree-1-2-red`    | Wave 1, Task 2, RED phase |
| `worktree-2-3-red`    | Wave 2, Task 3, RED phase |
| `worktree-2-3-green`  | Wave 2, Task 3, GREEN phase |

### Branch Names

Branch names follow the same pattern as worktree names. When creating a worktree:

```bash
# Create worktree for Wave 1, Task 1, RED phase
git worktree add ".worktrees/worktree-1-1-red" -b worktree-1-1-red
```

---

## 8. Known Limitations

1. **Cannot merge from within a worktree (Superpowers issue #167).** All merge operations MUST be performed from the main working directory, never from inside a worktree. Attempting to merge from a worktree will fail or produce unexpected results.

2. **No-change worktrees are auto-cleaned.** If an agent with `isolation: "worktree"` makes no changes (no commits), the worktree is automatically cleaned up. There will be no branch to merge, and no merge step is needed for that task.

3. **Disk space requirements.** Each worktree creates a full copy of the working directory (though git history is shared via the `.git` directory). For large repositories, ensure sufficient disk space before creating multiple worktrees in parallel.

4. **Independent working directories, shared history.** Each worktree has its own independent working directory and index, but all worktrees share the same git object store and history. This means:
   - Commits made in one worktree are visible to others via branch references
   - Concurrent writes to the same branch from different worktrees will corrupt state
   - Each worktree must work on its own dedicated branch (enforced by the naming convention above)
