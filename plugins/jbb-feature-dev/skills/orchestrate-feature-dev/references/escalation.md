# Escalation

When the orchestrator encounters an unrecoverable failure, it escalates to
a human rather than retrying blindly.

## Trigger Conditions

- Wave failure: any plan in a wave exits non-zero
- Goal loop exhausted its iteration cap or wall-clock budget, or oscillation
  was detected (see `references/agent-prompts.md` § Loop Termination
  Contract). Include the loop's preserved state in the diagnostic doc:
  resolved items, remaining items with IDs, what was attempted for each,
  and which bound was hit — the usual resolution is to raise one bound and
  resume, which requires that state
- Assertion marked `needs_operator`: a contract assertion requires a real
  write to a shared service, which a background stage cannot perform (see
  § Operator-Executed Assertions below). Include the prepared command block
  verbatim and the evidence-verification protocol, so the operator can run it
  and the run can resume. This is not a failure of the environment and must not
  be recorded as `blocked`
- Review-phase skip detected: artifact check finds no review evidence
- Review examined nothing: step 9's review resolved an empty scope, or exited
  non-zero for any other reason. Record it as a failed stage, not as
  `failed_review_phase_check` — the review phase was not skipped, it had nothing
  to run against. A branch 0 commits ahead with a clean tree is the usual cause,
  and since step 7b commits after every plan, it means no implementation work
  was ever committed; say so in the diagnostic doc rather than just reporting
  the empty scope.

  **Findings step 9 leaves unfixed are NOT an escalation.** The single-pass
  review is designed to hand back findings the run will not fix; they are filed
  as deferred beads (`agent-prompts.md § Filing What Ships Unfixed`) and the
  pipeline continues. Only a review that failed to *run* escalates
- Objective contradiction: requirements reconciliation finds the Objective
  is contradicted by findings
- Slug extraction failure: cannot derive a project slug from the research doc
- Unhandled exception or unexpected state

## Operator-Executed Assertions

A background stage is denied any real write to a shared service, and relaying
the user's verbatim authorization from the orchestrator does not help: the
classifier treats a quoted approval arriving in a teammate message as another
agent's output rather than a direct user instruction, so re-relaying or
rewording never flips it. The pipeline runs headless, so there is no
user-present session to hand the work to mid-run either.

When SKILL.md step 11 reaches such an assertion:

1. **Prepare** the exact command block the assertion needs, plus an
   evidence-verification protocol stating what output would prove it.
2. **Write that block to a durable artifact** under the run directory and
   record the path in `validation-state.json`.
3. **Mark the assertion `needs_operator`** — distinct from both `passed` and
   `blocked`, because nothing about the environment is broken; only this
   agent's authority is missing.
4. **Escalate** per the procedure below, with the command block verbatim in the
   diagnostic doc. The operator runs it and the run resumes per the
   resumability rules in `state-file.md`.

Escalation is the channel that already exists for "a human is required". On one
run the validator stage could not execute a single one of its own contract
commands, and with no prescribed alternative it nearly shipped two assertions as
post-merge follow-ups while the user was available to run them in seconds. The
failure was routing a permission limit into `blocked`.

## Escalation Procedure

1. **Write a diagnostic doc** to
   `~/.claude/thoughts/shared/escalations/<YYYY-MM-DD>-<run-id>.md`
   containing:
   - The `run_id`, failed stage, artifact path
   - Current branch and worktree path
   - The `project_dir` being used
   - The last 200 lines of relevant log files

2. **Generate a failure report** at `$RUNS_BASE/final-report.md` with
   pipeline status `FAILED`. Populate what data is available from the
   state file: executive summary naming the failure stage and reason,
   stage timeline (stages after failure marked "not reached"), key
   decisions recorded so far, code review findings if any, verification
   outcome if reached, and artifact listing.

3. **Leave the worktree intact.** Do NOT run `git reset`, `git checkout`,
   `git stash`, or `git worktree remove`. The human operator inspects the
   working tree as part of triage.

4. **Mark the failure in the state file**: set `status` to `"failed"` and
   add an `escalation` object with `stage` and `reason` fields. For
   review-phase skips, use status `"failed_review_phase_check"` so a
   restart-less re-invocation resumes from the right place.

5. **Send a Slack alert** via the same routing as success notifications
   (DM by default, `--slack-channel` override). The alert should name the
   failed stage and link to the diagnostic doc.

6. **Exit non-zero** so the parent shell or harness sees the failure.

## Rules

- Never auto-retry an escalation. A skipped review phase, a goal loop that
  exhausted its bounds (see `agent-prompts.md § Loop Termination Contract`),
  or a repeated verify failure all indicate the
  model is not respecting the contract; blind retries burn tokens without
  addressing the cause. Raising a bound and resuming is an operator
  decision, not an automatic one.

- Before escalating, verify the background process has actually terminated.
  A missing output file while a background stage is still running is NOT a
  failure — it means the stage has not finished yet. Only escalate after
  receiving the completion notification and confirming the process exited.

- If the orchestrator is already escalating because of a pipeline failure,
  a Slack delivery error must not mask the original failure — log the Slack
  error separately and proceed to surface the underlying escalation reason.
