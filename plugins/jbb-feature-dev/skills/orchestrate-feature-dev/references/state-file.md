# Orchestrator State File

The orchestrator persists run state to a single JSON file on the local filesystem so a re-invocation can resume mid-pipeline without re-running completed plans. There is no external service; the file is the source of truth.

## Canonical Paths

1. State file: `~/.claude/thoughts/shared/orchestrator-state/<run-id>.json`
2. Log directory: `~/.claude/thoughts/shared/orchestrator-state/logs/<run-id>/`

`<run-id>` is the kebab-slug derived from the requirements doc filename (basename without extension, lowercased, non-alphanumerics collapsed to `-`). Both paths are absolute (relative to `$HOME`), never relative to the invoking shell's CWD.

## JSON Schema

The canonical shape. All keys are required unless noted.

```json
{
  "run_id": "add-user-quota-limits",
  "status": "in_progress",
  "cli_args": {
    "requirements": "~/.claude/thoughts/shared/requirements/add-user-quota-limits.md",
    "prompt": "",
    "ticket": "PROJ-1234",
    "slack_channel": "C01XYZ789",
    "research": "",
    "design": ""
  },
  "branch": "feat/add-user-quota-limits",
  "ticket": "PROJ-1234",
  "decisions": [
    {
      "stage": "design-approach-selection",
      "summary": "ops=1, design=1"
    },
    {
      "stage": "requirements-reconciliation",
      "summary": "conflict=false, changes=true"
    }
  ],
  "verification_outcome": {
    "total": 5,
    "passed": 5,
    "failed": 0,
    "blocked": 0
  },
  "dag": {
    "waves": [
      {
        "wave_id": 1,
        "plans": [
          {
            "plan_id": "plan-a",
            "path": "~/.claude/thoughts/shared/plans/add-user-quota-limits-plan-a.md",
            "status": "complete",

            "artifacts": {
              "research": "~/.claude/thoughts/shared/research/add-user-quota-limits.md",
              "plan": "~/.claude/thoughts/shared/plans/add-user-quota-limits-plan-a.md",
              "verify_summary": "logs/add-user-quota-limits/plan-a/verify-summary.md"
            }
          },
          {
            "plan_id": "plan-b",
            "path": "~/.claude/thoughts/shared/plans/add-user-quota-limits-plan-b.md",
            "status": "in_progress",
            "artifacts": {}
          }
        ]
      }
    ]
  }
}
```

Field notes:

1. `status` (top-level) and per-plan `status` share the enum `pending | in_progress | complete | failed`.
2. `cli_args` mirrors the original `/orchestrate-feature-dev` invocation so a resume produces the same wiring.
3. `branch` is the working branch for the run; created once, reused across resumes.
4. `dag.waves[].plans[].artifacts` is an open map; downstream stages add keys (e.g. `research`, `plan`, `code_review`, `verify_summary`) as they produce outputs.
5. `cli_args.slack_channel` is persisted as the resolved canonical channel ID (e.g. `C01XYZ789`); `#name` inputs are resolved via `slack_search_channels` at start-of-run and the canonical ID is persisted, so a renamed channel does not break resume.
6. `cli_args.prompt` and `cli_args.requirements` are mutually exclusive on input (per requirements doc lines 122-138): exactly one is non-empty for any given run. Both keys are always serialized (the empty one is `""`) so resume read-back is uniform.
7. `cli_args.skip_research` stores the boolean flag for `--skip-research`. `cli_args.design` stores the path supplied via `--design`. Both are always serialized (false/empty string if not supplied) so resume recovery can restore the configuration.
8. `decisions` is a top-level array of `{stage, summary}` objects. Each entry records a key pipeline decision (design approach selection, requirements reconciliation outcome, code review result, contract amendment). Appended via `jq` after each decision point.
9. `code_review` is a top-level object recording step 9's single review pass. **Step 9c writes it**, from the three counts the step 9b fix stage returns on its final `COUNTS` line — this parent context never reads the review document itself. It is absent until step 9 has run; an absent object means "not reached", which a pass that failed to run must not overwrite with zeroes.

   ```json
   "code_review": {
     "doc": "~/.claude/thoughts/shared/reviews/<slug>-review.md",
     "scope": "committed range",
     "base": "<sha>",
     "files": 28,
     "total_findings": 11,
     "addressed": 9,
     "filed": 2,
     "style_findings": { "in_scope": 6, "addressed": 6, "skipped": [] }
   }
   ```

   **`addressed + filed` must equal `total_findings`.** A finding that is neither fixed nor filed as a deferred bead has been dropped silently, and with no second review pass to re-report it nothing downstream will ever surface it again — see `agent-prompts.md § Filing What Ships Unfixed`. There are no `iterations` and no `loop_count`: step 9 runs once, so an attempt history would be a shape with one element forever.

   `style_findings` is broken out from the totals because step 9 addresses code-style findings by default whatever their severity. A run where `style_findings.addressed` sits well below `in_scope` is the signal that the default was quietly abandoned, which is invisible in the roll-up counts.

10. `dag.waves[].plans[]` has no `review` object. Plans are planned, implemented and committed (step 7); cleanup happens once on the cumulative diff at step 8 and review once at step 9, so nothing review-shaped is recorded per plan.

11. `verification_outcome` is a top-level object with `{total, passed, failed, blocked}` counts from the validator's `validation-state.json`. Populated after the verify-fix loop completes.
12. Stage and per-plan entries MAY record `agent` — an object `{"name": "<wrapper-name>", "id": "<agent-id>"}` for the stage wrapper subagent currently (or last) running that stage. This is what makes SendMessage recovery possible after context compaction. Optional and additive: state files without it remain valid and resumable.

## Resumability Rules

1. On any re-invocation without `--restart`:
   1. Read the state file at the canonical path. If absent, treat as a fresh run.
   2. Per plan: `complete` is skipped, `pending` is executed, `failed` halts the run for human review.
2. Startup transition (mid-wave crash recovery): before the first wave executor begins, scan every plan and **reset** any plan whose `status` is `in_progress` to `pending`. The orchestrator may have died after persisting `in_progress` but before the wave finished; reverting forces a clean re-run of that plan rather than abandoning it as half-done. Persist the reset atomically (see below) before launching wave executors.
3. `--restart` deletes both canonical paths before anything else runs:
   1. `rm -f ~/.claude/thoughts/shared/orchestrator-state/<run-id>.json`
   2. `rm -rf ~/.claude/thoughts/shared/orchestrator-state/logs/<run-id>/`
      Both deletions use absolute paths; never use a path relative to CWD, since the orchestrator may be invoked from any directory.
4. CLI args from the persisted `cli_args` win over re-supplied flags on resume, except `--restart` (which short-circuits the read entirely). This keeps a resumed run identical to the original invocation.
5. For `--prompt` mode, `<run-id>` is content-derived from the prompt hash. Resuming a `--prompt` run requires re-supplying the byte-identical prompt text; a paraphrased prompt produces a different `<run-id>` and starts a fresh run. The `cli_args` read-back guarantee is therefore informational for `--prompt` mode (the resume already succeeded by the time it fires) and substantive only for `--requirements` mode (where `<run-id>` is derived from the path, and a re-invocation can recover `cli_args.requirements` from the persisted state).

## Atomic Write Pattern

Every state mutation writes to a sibling temp file and renames in place. `mv` within the same directory is atomic on POSIX, so a crash mid-write leaves either the old file or the new file — never a partial JSON document.

```bash
tmp="$(mktemp "${STATE_FILE}.XXXXXX")"
jq '.dag.waves[0].plans[0].status = "complete"' "$STATE_FILE" > "$tmp"
mv "$tmp" "$STATE_FILE"
```

Rules:

1. Always `mktemp` in the same directory as `$STATE_FILE` (the `${STATE_FILE}.XXXXXX` template guarantees this) so `mv` stays on the same filesystem.
2. Never edit the state file in place with `sed -i` or shell redirection (`>`); a SIGKILL mid-write truncates it.
3. One mutation per `jq` invocation keeps the diff auditable in the run log.
4. Read-modify-write sequences are not concurrency-safe across processes. The orchestrator is single-writer by design — wave executors emit completion markers via separate log files, and only the parent orchestrator process writes to `$STATE_FILE`.
