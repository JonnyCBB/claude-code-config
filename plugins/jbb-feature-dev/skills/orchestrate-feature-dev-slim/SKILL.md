---
name: orchestrate-feature-dev-slim
description: >
  Use for a feature that is ONE PLAN WIDE, INSTEAD of /orchestrate-feature-dev:
  a slim six-stage pipeline that keeps the context isolation and drops the
  planning machinery. Runs /research-problem, a red-green TDD implementation
  under a real /goal loop, /simplify, /jbb-feature-dev:code-review with its
  recommendations applied by default, /jbb-feature-dev:verify-implementation,
  then /jbb-feature-dev:submit-pr. Each stage runs as its own isolated worker, so
  source code, research text and test logs never reach the orchestrator's
  context. No plan DAG, no wave executor, no validation contract, no Slack
  routing. Prefer the parent skill when the feature needs multi-plan scoping or
  a frozen live-testing contract. Takes a requirements file or a plain-English
  description. Trigger phrases: (1) "orchestrate feature slim" (2) "run the slim
  pipeline" (3) "slim feature pipeline" (4) "build this feature end-to-end,
  slim".
argument-hint: '[--prompt "<text>"] [--requirements <path>] [--branch <name>] [--no-worktree] [--restart]'
---

# /orchestrate-feature-dev-slim

Six stages, one invocation: research, red-green TDD implementation, cleanup,
review-and-apply, verification, pull request. Same destination as
`/orchestrate-feature-dev` and the same context-isolation discipline, with the
planning machinery taken out.

**Gone deliberately**: the plan DAG from `/map-feature-to-plans` and the wave
executor around it; the separate `/create-plan-tdd` and `/implement-plan-tdd`
stages, because stage 2 implements straight from the requirements; the
validation contract and validator agent; Slack routing; the escalation ladder;
the final report template. Reach for the parent skill when a feature is
genuinely several plans wide, or when acceptance has to be gated on a frozen
live-testing contract — those are the two things this pipeline cannot do.

**Kept**: per-stage context isolation, the isolated worktree, and a minimal
resumable run-state file (`references/run-state.md`). The state file is kept on
purpose rather than surviving by accident: stage 2 is measured in tens of
minutes to hours, and without state a stage-5 failure re-runs it.

## Orchestrator discipline

You are the orchestrator. You launch workers, read their short completion
reports, update run state, and launch the next one. Source code, research prose,
diffs and test output in **your** context defeat the entire point.

**Never in this context**: read source files of the target repo; `Grep`/`Glob`
the target repo; read the body of the research, review or verification
documents; poll `git diff`, `git status` or `ps aux` while a stage is running;
re-attempt a stage while a prior attempt may still be live; spawn ad hoc
subagents for research, exploration or fixes. The only workers are the six
stages below.

**Sanctioned reads**: `jq` against the run-state file; a stage's milestone log
during recovery; `git -C <worktree> log --oneline -1` to record a commit SHA;
`wc -l` or `test -f` against an artifact path to confirm it exists. Confirming
an artifact exists is not the same as reading it.

## Inputs

| Flag                    | Default | Effect                                             |
| ----------------------- | ------- | -------------------------------------------------- |
| `--prompt "<text>"`     | not set | Plain-English feature description; run from scratch |
| `--requirements <path>` | not set | Start from an existing requirements document        |
| `--branch <name>`       | auto    | Use this branch instead of deriving one             |
| `--no-worktree`         | off     | Work in the current checkout                        |
| `--restart`             | off     | Delete prior run state and logs first               |

`--prompt` and `--requirements` are mutually exclusive, and exactly one is
required. Unknown flags are a hard error, not a warning. Record every parsed
**configuration** flag into `cli_args` so a resume recovers the original wiring.
`--restart` is deliberately not persisted — it is a one-shot action, and a
resume that re-read it would delete the state it had just read.

**Prerequisite.** Stage 2 depends on `/goal`, which is a Claude Code built-in
(v2.1.139 and later, documented at `https://code.claude.com/docs/en/goal`) and
not something this plugin ships. Confirm it resolves before starting — the cheap
precondition in `references/stages.md § Stage 2` takes seconds, and skipping it
means finding out after the longest stage in the pipeline has already run.

**Where this skill assumes it is running.** The orchestrator should be a session
that can itself launch `claude -p` and write outside the worktree — an
interactive session, or a headless one with equivalent permissions. Stage 2 needs
to *create* a top-level session, and a restricted headless orchestrator cannot:
one was measured unable to invoke `claude` at all, which makes stage 2 impossible
from that position rather than merely awkward. Every worker also inherits this
session's permission mode, so this is the single setting that decides whether the
stages can write what they need.

## Workspace

Derive the run id and paths per `references/run-state.md`. By default create a
git worktree at `~/.claude/worktrees/<run-id>` and work there — **never** under
`/tmp` or `/private/tmp`, where macOS cleanup coinciding with a session restart
destroyed hours of uncommitted work in a real run (2026-07-10). With
`--no-worktree`, check the branch out in place.

**Base the branch on the remote default branch, not on whatever is checked out.**
`git worktree add -b <branch> <path> origin/<default>`, having fetched first. A
worktree created from the current HEAD inherits every unrelated commit on it, and
stage 6 then opens a pull request containing someone else's work alongside the
feature — which is invisible until a human reads the diff. Then run
`git branch --unset-upstream` immediately: `worktree add` from `origin/<default>`
sets that as the new branch's upstream, so a bare `git push` would target the
default branch directly. Always push with an explicit refspec.

In `--prompt` mode the run id is `_pending` until stage 1 produces a research
document; defer branch and worktree creation until it has been finalized.

## How a stage runs

Stages 1 and 3-6 are **named background Agent-tool workers**. The canonical
mechanics — wrapper invocation, prompt template, Output Location Override,
milestone log contract, final-message contract, checkout anchor, fallback
timers, the recovery ladder and the fallback artifact search — are inherited
unchanged from
`../orchestrate-feature-dev/references/stage-execution.md`. Read it before
launching the first stage. Per-stage arguments, modes, models and timers for
*these six* stages are in `references/stages.md`.

The rules that matter most, restated because breaking any one of them strands a
run. Rules 1, 5 and 6 are each here because they cost a real run something on
2026-08-23.

1. Spawn with `run_in_background: true`, an explicit `name`, and a model you
   chose and recorded with its reason. **Tell the worker to deliver its
   completion report by calling SendMessage to `"main"`.** A named teammate's
   plain final message is silently dropped, so a worker that follows the
   inherited final-message contract literally reports nothing — and you, applying
   rule 5, would score a successful stage as failed.
2. Pair each stage with one background-sleep fallback timer.
3. Wait for the completion notification or the timer. Do not poll.
4. Never re-attempt while a prior attempt may still be running.
5. On completion, **check the artifact is real, not merely present.** Existence
   is not the test: a run has produced a 12-byte file containing the word
   `placeholder` at the canonical path, which passes an existence check and fails
   the pipeline three stages later. Check a plausible size and that the structure
   you expect is there — for a document, its headings.
6. Expect the worker's runtime to be poorer than the stage skill assumes, and
   require it to *record* every substitution rather than absorb it. Measured in
   one stage: the stage skill was absent from the worker's Skill listing, a
   specialist `subagent_type` it mandates did not exist, and four tools it uses
   were missing. **If the Skill tool cannot resolve a stage skill, read that
   skill's `SKILL.md` from its plugin directory and execute it directly** — that
   is a recorded degradation instead of a dead stage.

**Paths must be absolute, expanded from `$HOME`.** A run read `~/.claude/` as
repo-relative and built its worktree *inside* the repository, which put a second
copy of the tree where the feature's own file scans could see it. The `/tmp`
prohibition below is worth nothing if the replacement path silently resolves
somewhere else.

**If you are a headless `claude -p` orchestrator, set
`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`.** The default kills background tasks at
600 seconds, and stage 1 is documented as taking hours. A run died at ten minutes
with its stage-1 worker healthy and its fallback timer correctly armed. That
default silently deletes the whole spawn-and-wait pattern this skill is built on.

**Stage 2 is the one exception, and it is forced rather than chosen.** `/goal`
is a session-scoped Stop hook that reaches only a genuine top-level session;
inside an Agent-tool subagent it is inert, so a `/goal` written into a worker's
prompt is decorative text that looks like a convergence loop and is not one.
Stage 2 therefore runs as a detached top-level `claude -p` session, which
isolates context *better* than a worker since its output goes to a log file
rather than into any conversation. `references/stages.md § Stage 2` has the
measurement behind this, the launch and wait pattern, and how to confirm the
loop actually engaged.

## The six stages

### 1. Research

`/jbb-feature-dev:research-problem`, read-only, in a worker. Pass the
requirements path — or, in `--prompt` mode, `$LOG/prompt-input.md`, which you
write the prompt text into first — as a **positional** argument. Append the
review-phase enforcement addendum from
`../orchestrate-feature-dev/references/review-phase-enforcement.md`, then run
that file's artifact check afterwards. Missing review evidence escalates; it
does not retry.

Inherit that file's addendum text and its evidence ladder only. Its
`## Failure Handling` section belongs to the parent: here a missed review sets
the stage to `failed`, writes the diagnostic and stops per `## Escalation`
below — there is no `failed_review_phase_check` status in this pipeline's enum,
and no Slack to route to.

Research legitimately runs for hours. Duration alone is never a stall signal —
follow the milestone log.

Then finalize the run-id slug if it is still `_pending`, and create the branch
and worktree.

### 2. Implement, red-green, under a real `/goal`

A detached top-level `claude -p "/goal <condition>"` session, because of the
measurement above. The condition states the outcome in terms the session's own
transcript can demonstrate — the evaluator only reads the transcript, it does
not run tools — and carries its own turn bound, which is how `/goal` is
documented to be bounded.

Red-green-refactor is the requirement, not a suggestion: a failing test first,
then the code that passes it. The pipeline has no plan document, so the
requirements and research documents are the specification.

The stage commits its own work. Everything downstream depends on that, and a
commit is also all that survives a lost worktree.

### 3. Simplify

`/simplify` once, in a worker, on the cumulative diff. Not `/polish-code`, and
not per-commit or in a loop: `/simplify` applies cleanups and does not hunt for
correctness bugs, so there is no gate to converge toward and nothing to
re-measure. Running it across the whole diff is also the only way it can see
duplication that accumulated between one part of the work and another.

Ordering is deliberate — cleaning before the review means the review spends its
attention on correctness instead of on mess that was about to be deleted.

**It must commit before stage 4 starts.** The review resolves its scope as a
committed range and only falls back to the working tree when that range is
empty, which stage 2 guarantees it is not. An uncommitted `/simplify` is
therefore invisible to the review, which then reports findings whose line
numbers no longer match the files on disk — the exact inversion of the ordering
rationale above.

**When a cleanup would reach outside the feature's own files, the checkout anchor
wins and the finding gets filed.** `/simplify` is told to look for reuse, and the
best reuse findings are frequently cross-file — a helper the repo already has, a
harness duplicated in four places. The anchor says touch nothing else. Measured
2026-08-23: a stage-3 worker found three such findings, applied none, and
recorded all three, which is the right outcome — but it reached it by its own
judgement, not because anything told it to. Say it, so the next worker does not
either sprawl or drop them silently.

Non-fatal: if it fails, record it and carry on with the current code.

### 4. Code review, then apply what it found

Two workers, because `/jbb-feature-dev:code-review` is explicitly read-only and
this context may not edit files — neither actor can do both halves.

**4a — review, once.** One pass, no loop, no severity gate, no confirmatory
re-run. Its first argument is a bare branch name, never a path and never a PR
URL. `--non-interactive` is mandatory. An Output Location Override is mandatory
too: the skill derives its default path from a PR number, and no PR exists yet.

**4b — apply, once.** A single worker that edits, commits, and reports counts.

> **The default is to apply.** Every recommendation gets applied unless there is
> a specific reason not to, and that includes Minor and Enhancement priority
> code-style findings. Declining is the exception and must carry a written
> reason naming the finding.

That direction matters. "Apply the sensible ones" without naming the default is
how minor findings get dropped in silence — they rank below whatever else is in
flight, so they are always what gets cut when a stage runs long. Anything not
applied is filed, never merely mentioned.

**A finding that contradicts a written acceptance criterion is evidence the
criterion is wrong, not evidence the finding is out of scope.** This is the
tempting decline, and it is usually the wrong one: the criterion is in writing and
the finding is not, so declining feels like discipline. Measured 2026-08-23: a
requirements doc said only backtick-quoted paths counted as references, and every
single one of the feature's real target cases turned out to be a markdown link. A
spec-faithful implementation would have passed all nine criteria and missed the
entire problem the feature existed to solve. The review caught it; applying it is
what made the feature work. Apply, and flag the conflict for a human rather than
resolving the requirements yourself.

**The accounting is the enforcement.** The stage returns four counts and must
satisfy two invariants:

```
applied + declined == reported    # every finding went one way or the other
filed == declined                 # and every declined one survives this run
```

`filed` is not a third bucket of findings — it is the check that a decline was
written down somewhere durable instead of merely mentioned. Getting this wrong
in the other direction (`applied + declined + filed == reported`) double-counts
every decline and so escalates the exact outcome this stage is designed to
produce.

A mismatch means findings were dropped, and with no second review pass nothing
downstream will ever surface them again — treat it as a failed stage and
escalate. Record all four counts in run state.

### 5. Verify

`/jbb-feature-dev:verify-implementation` in a worker, against the requirements
and the research document.

**Always pass an explicit positional document path.** This skill has no
`--non-interactive` flag, and its plan-location step falls through to "ask
user" — in a background worker, a stage that never returns, with no error and no
artifact. Passing the path explicitly is what keeps that rung unreachable; see
`references/stages.md § Argument notes, per stage` for the second hazard on the
same fall-through. Filed as `jbrooksbartlett-nv27y`.

A green unit-test suite is not verification evidence. Behaviour exercised
against the requirements is.

### 6. Submit the pull request

`/jbb-feature-dev:submit-pr` in a worker, with `--verification`,
`--requirements`, `--non-interactive`, and the target branch. Stages 2, 3 and 4
committed their own work, so this stage pushes and opens the PR rather than
sweeping up. Confirm the PR URL came back and record it.

## Escalation

Unrecoverable failure stops the run and surfaces to a human. There is no
ladder, no Slack routing and no auto-retry here: write what failed, the stage,
the last milestone line and the worktree path into the run-state file, say it
plainly, and stop. Leave the worktree in place for triage.

A review finding that was declined with a reason, or filed, is **not** a
failure — that is the design working. An honest failed run with a clear
diagnostic beats a PR carrying hollow evidence.

## References

- `references/stages.md` — per-stage arguments, modes, models, timers, artifacts, and the stage-2 launch/wait pattern
- `references/run-state.md` — run-state schema, paths, resume rules, atomic writes

Inherited unchanged from `../orchestrate-feature-dev/references/`:
`stage-execution.md` (worker mechanics, recovery ladder, fallback artifact
search) and `review-phase-enforcement.md` (addendum text and artifact check).
