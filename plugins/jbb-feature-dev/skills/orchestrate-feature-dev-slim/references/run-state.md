# Run State

One JSON file per run, so a crash or a restart resumes instead of starting over.

This is a deliberately smaller thing than the parent pipeline's state file
(`../../orchestrate-feature-dev/references/state-file.md`). That one carries a DAG
of waves and per-plan status because it has plans to track. This pipeline has
six fixed stages in a fixed order, so the whole of its state is "which stages
are done, and where did each one put its artifact".

**Why it exists at all.** Stage 2 is the expensive one — a red-green TDD
implementation, measured in tens of minutes to hours. Without a state file, a
failure in stage 5 throws that away and re-runs it. The file is about fifteen
lines of prose to maintain and it buys back the single most expensive stage in
the pipeline. That is the trade, made deliberately rather than by omission.

## Paths

- State file: `~/.claude/thoughts/shared/orchestrator-slim/<run-id>.json`
- Log directory: `~/.claude/thoughts/shared/orchestrator-slim/logs/<run-id>/`
- Artifacts: `~/jbb-feature-dev/slim-runs/<run-id>/`

`<run-id>` is a kebab-case slug, at least six characters. With
`--requirements`, it is the basename without extension. With `--prompt`, it is
deferred: hold `_pending` until stage 1 produces a research document, then take
the slug from that document's `title:` frontmatter or first H1 and rename the
three paths above. Never fall back to a hash or a timestamp — a run whose
directory is named `run-1755938400` is one nobody will ever find again.

## Shape

```json
{
  "run_id": "add-user-quota-limits",
  "status": "in_progress",
  "cli_args": {
    "requirements": "~/.claude/thoughts/shared/requirements/add-user-quota-limits.md",
    "prompt": "",
    "branch": "",
    "no_worktree": false
  },
  "branch": "feature/add-user-quota-limits",
  "worktree": "~/.claude/worktrees/add-user-quota-limits",
  "stages": {
    "research": { "status": "complete", "artifact": "~/jbb-feature-dev/slim-runs/add-user-quota-limits/2026-08-23-research.md" },
    "implement": { "status": "complete", "artifact": "commit:4f2ab9c" },
    "simplify": { "status": "complete", "artifact": "commit:9de1f03" },
    "review": { "status": "in_progress", "artifact": "" },
    "verify": { "status": "pending", "artifact": "" },
    "submit": { "status": "pending", "artifact": "" }
  },
  "review_accounting": { "reported": 7, "applied": 6, "declined": 1, "filed": 1 },
  "decisions": [
    { "stage": "implement", "summary": "model=sonnet; procedure-heavy red-green loop, longest stage, tier moves the bill most" },
    { "stage": "review", "summary": "declined 1 finding: proposed helper duplicates an abstraction the repo deletes in PR #480" }
  ]
}
```

Every key is required. `stages.*.status` takes `pending | in_progress |
complete | failed` — that is the whole enum, so a status inherited from the
parent's references (`failed_review_phase_check`) is not admissible here.
`artifact` is an absolute path, or `commit:<short-sha>` for the two stages whose
output is a commit rather than a document.

`cli_args` holds configuration only, which is why `--restart` is absent from it.
Persisting `--restart` would mean a resumed run re-reads an instruction to
delete the state file it has just loaded.

## Resume rules

On invocation without `--restart`, read the state file if it exists.

1. In `--prompt` mode, look for `<slug>.json` first and fall back to
   `_pending.json`. A run that died during stage 1 never reached the rename, so
   `_pending.json` is all there is — and stage 1 is the hours-long research
   stage, which makes it the likeliest window to have died in.
2. `cli_args` from the file wins over re-supplied flags. A resumed run that
   silently changes its own configuration is worse than one that refuses to
   resume, because the difference does not show up until the artifacts disagree.
3. Reuse the recorded branch and worktree. If the worktree is gone, recreate it
   from the branch — which restores only what was **committed**, and is the
   whole reason stages 2, 3 and 4 each commit their own work rather than
   deferring to the end.
4. Reset any stage sitting at `in_progress` to `pending` and re-run it. A stage
   that was interrupted mid-flight cannot be trusted to have finished its
   writes, and every stage here is safe to repeat.
5. Skip stages already `complete`, but confirm the recorded artifact still
   exists at its path first. A `complete` status with a missing artifact means
   `pending`, not complete — trusting the status over the filesystem is how a
   resumed run feeds a downstream stage a path to nothing.
6. A stage marked `failed` stops the resume. Escalate rather than retrying
   automatically: it already had its retry.

## Writing it

Write atomically, always — `mktemp` in the same directory, write the full
document, then `mv` over the target. Never edit in place. A state file
truncated by a crash mid-write is not a degraded state file, it is an
unparseable one, and it takes the resume capability down with it at exactly
the moment that capability was needed.

Update the file after each stage returns, before launching the next one.
