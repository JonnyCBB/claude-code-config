# Path rewriting, the deny-rule twins, and pre-trusting paths

Detail for phase 8 of `SKILL.md`. The rules and the role table are there; this holds the parts
where the specific literal or the specific distinction is what matters.

## The deny-rule twins

**Check the right file.** The conductor's guardrails live in the **conductor directory's**
`.claude/settings.json`, not `~/.claude/settings.json`. Measured on the Mac at the time of writing,
the conductor directory held N deny rules with **all N carrying `/Users/` paths**, while
`~/.claude/settings.json` held none at all. Pointing the check at `~/.claude` prints a
clean-looking zero for a file that was never the subject, and leaves the real one unexamined.

**Report three numbers together, not one.** A single count of Linux-path rules is ambiguous — `0`
means both "rules exist but none apply here" and "there are no rules at all", which need opposite
responses. Read the total, the count matching `/home/`, and the count matching `/Users/`, and
distinguish four outcomes:

| State | Meaning |
| --- | --- |
| No settings file at all | Nothing is denied. The rsync did not bring `.claude/`. |
| `total=0` | File exists and declares no guardrails at all. |
| `total=N, linux=0, mac=N` | **The trap.** Guardrails exist and every one is inert on Linux. |
| `total=2N, linux=N, mac=N` | Twins added. This is the target state. |

**Add the twins by duplicating, never substituting** — allow and deny lists are additive, so the
file then works on both machines. Two things to get right:

- **Preserve the rule syntax exactly.** These are written `Edit(///Users/<user>/...)` with a
  *triple* slash. A twin that drops it matches nothing while looking right.
- **Derive the username on the VM** (`id -un`) rather than filling in a placeholder, so there is no
  hand-edit to get wrong.

Back the file up next to itself before rewriting, not to `/tmp`. Then re-read the three counts and
confirm they reached the target row, and that the printed twins still carry the triple slash.

## Pre-trusting paths

The key is `hasTrustDialogAccepted: true`, set under the **absolute path** as a key in the
`projects` map of `~/.claude.json`. Set it for the conductor directory before starting it, and for
each worktree path before launching into it — trusting the repo root is not enough, because
`.worktrees/<branch>` is a different path and every dispatch creates a new one.

Two things worth care when editing that file: **preserve any other keys already on an existing
project entry** rather than replacing the entry, and **print back what is now trusted** so a path
that failed to register is visible rather than assumed.

## At every dispatch, not just at setup

Everything above is per-worktree, so it recurs. The full checklist for launching a worker:

1. **Pre-trust the absolute worktree path** (above). Without it the worker dies on the dialog.
2. **Read the real branch and path back from the launch JSON.** `--worktree <name> -b` renames your
   branch: asking for `probe-x` produces `feature/probe-x` in `.worktrees/feature-probe-x`. Record
   `worktree_branch` and `worktree_path` as returned, never what you asked for.
3. **Unset the upstream** on the new worktree's branch. Every one comes up tracking `origin/master`,
   so a bare `git push` pushes feature commits straight to master.
4. **Pass the full model id, never the `opus` alias** — e.g. `--model 'claude-opus-5[1m]'`. Verify
   it in the launch JSON afterwards.
5. **Check `parent_id` in the launch JSON.** If it is not the conductor's session id, completion
   events never route home.
6. **Use `--message-file`** rather than piping a long spec through a shell.
