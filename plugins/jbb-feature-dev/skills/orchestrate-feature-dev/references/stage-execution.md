# Stage Execution

How the orchestrator invokes pipeline stages. Every stage runs as a named
**background Agent-tool subagent** (a "stage wrapper") that invokes the
stage's skill via the Skill tool — or executes a direct agent prompt from
`references/agent-prompts.md` — and writes a milestone log.

Why Agent-tool wrappers and not `claude -p`: harness-tracked background
`claude -p` subprocesses were killed at ~30 minutes (verified in the
2026-06-30 run: 4 dead research attempts, 2 dead ops-context attempts,
2 dead reconciliation attempts), and the detached workaround has no
completion notification, forcing wasteful fixed-interval polling. Background
Agent subagents were empirically verified on 2026-07-02 to survive 55+
minutes, resolve skills via the Skill tool, and spawn the skill's own
nested subagents (all delivered first-try). See the appendix for the
detached `claude -p` escape hatch.

## Canonical Wrapper Invocation

Spawn one wrapper per stage with the Agent tool:

- `subagent_type`: `general-purpose` (must be a type whose tool list
  includes `Agent` and `Skill` — restricted types like `Explore` cannot
  spawn the skill's sub-agents)
- `name`: `<stage>-<short-run-id>` (e.g., `research-seal-recovery`) —
  required; this is the SendMessage address for recovery
- `mode`: from § Mode Table below
- `model`: your choice per § Choosing a model per stage below, recorded with its
  reason
- `run_in_background`: `true`

## Wrapper Prompt Template

Every wrapper prompt is assembled from these parts, in order:

1. **Skill invocation**: "Invoke the Skill tool with skill
   `<plugin:skill-name>` and args `<exact args>`, then execute its
   instructions faithfully in non-interactive mode, including spawning
   every sub-agent the skill mandates." (Direct-prompt agents —
   reconciliation, validator, report generator, verify-fix recheck — use
   their prompt from `references/agent-prompts.md` instead.)
2. **Output Location Override** (see below).
3. **Review-phase enforcement addendum**, only for the three gated stages
   (see `references/review-phase-enforcement.md`).
4. **Milestone log contract** (see below).
5. **Final-message contract**: "Your final message must be a short
   structured completion report: STATUS (complete/failed), ARTIFACT
   (absolute path), SUBAGENT_ANOMALIES (idle-without-content events and
   recovery used, or 'none'), NOTES (one line). Do NOT include artifact
   content in the final message."
6. **Checkout anchor**: "You are operating in the git worktree at
   `<absolute worktree path>`. Confirm `git rev-parse --show-toplevel`
   matches that path before doing any work. Every sub-agent you spawn must
   be given this absolute path in its prompt and must confirm its own
   toplevel matches before reporting any finding."

**Why part 6 is mandatory.** The wrapper's own `cd "$WORKTREE"` does not
propagate to the sub-agents it spawns, so a reviewer or verification agent
can silently resolve to the main clone on `master` and then report
correct-looking findings about the wrong tree — the failure is invisible
because the findings are internally consistent. One contract-amendment
stage's Coverage Auditor raised 5 "fabrication" Must Address items for
exactly this reason; re-spawning with the path anchored cleared all 5, at
the cost of a full extra Sonnet+Opus review cycle. Verification agents
running greps against the wrong checkout produce the same class of error.

Agent prompts are tool parameters, not shell arguments — markdown
formatting (`**bold**`, backticks, heredoc-hostile characters) is safe.
There is no stdin workaround and no shell-quoting concern.

## Output Location Override

Append this instruction to every stage prompt so each skill writes its
artifact to the orchestrator's canonical path instead of its default
`~/.claude/thoughts/shared/<topic>/` location:

```
IMPORTANT — Output Location Override:
Use the Write tool to save your canonical output document to the absolute
path below. Do NOT write to your skill's default location; the orchestrator
reads this artifact at the exact path and ignores the default location.

Output path: <absolute-path>
```

## Milestone Log Contract

Each wrapper appends timestamped lines to `$LOG_DIR/<stage-name>.log`:

```
<ISO-8601 local> <epoch> <MILESTONE> <optional detail>
```

Required milestones: `START`, `SKILL_START`, one line per notable
sub-event (sub-agent delivery, review iteration, escalation), and
`DONE artifact=<path>` (or `FAILED reason=<...>`). The log is the
orchestrator's ground truth when a wrapper's final delivery is dropped —
it is read during the recovery ladder, never polled while the stage is
healthy.

### Loop and stage metrics every run must record

`STAGE_METRIC` and `LOOP_METRIC` are part of the required milestone output
above, not optional extras: each is written by the orchestrator after the stage
or loop it describes returns, from the counts that stage handed back.

Two loop counters and one single-pass counter go in the logs in a greppable
form, because they are how a future change to any of these gets judged:

```
<ts> <epoch> STAGE_METRIC stage=code-review    findings=7 addressed=5 filed=2 scope=cumulative
<ts> <epoch> LOOP_METRIC  loop=verify-fix        iterations=1 passed=16 failed=0
<ts> <epoch> LOOP_METRIC  loop=build-verification iterations=2 gosling_findings=3 unresolved=0
```

The labels are deliberately named for what the loop *does*, not for where it
sits. This file is read by both pipelines, and they number the same work
differently — steps 9, 12 and 15 here, gates G5, G6 and G7 in the Fable sibling.
A label naming either scheme sends the other pipeline's reader grepping for a
string their own run never emits.

`code-review` is a single pass, not a loop, so it records what it found and what
it did with it rather than an iteration count. `addressed + filed` must equal
`findings`: a finding that is neither fixed nor filed has been dropped silently,
and with no second pass to re-report it, nothing downstream will surface it
again.

A cycle that never produced a gate takes `result=failed-to-run` **instead of**
any counts, naming the cause — `scope=cumulative result=failed-to-run
cause=empty-scope`. Do not fall back to `iterations=0 critical=0 major=0`: this
is the line a future reader greps to judge the loop, and zero counts there are
indistinguishable from a clean gate, which is the same confusion the adapter's
exit codes exist to prevent.

The G6 and Gosling counters matter more than they look. The review that feeds
G5 reports a capped number of findings, so the way a lighter review shows up as
a regression is not a worse review document — it is more work landing
downstream: extra G6 iterations, or more Gosling findings on the PR. Neither
was recorded before, which meant the pipeline had no way to notice that
trade being made. Absolute values are enough to act on; a rise in either is
the signal to look.

## Mode Table

Mode is prescribed; model is yours (next section). Mode is a permission
constraint, not a quality judgement — `dontAsk` is required for any stage that
writes to a directory including sensitive paths like `~/.claude/`, and
`acceptEdits` is **not** a substitute (it still blocks those writes). Direct-prompt
agents also get a prompt-level tool restriction ("use only Read, Bash, Write"),
because the Agent tool has no allowed-tools parameter.

| Stage                             | Mode      | Why                                    |
| --------------------------------- | --------- | -------------------------------------- |
| `/research-problem`               | `auto`    | Read-only                              |
| `/operational-context`            | `auto`    | Read-only                              |
| `/design-approach`                | `auto`    | Read-only                              |
| Reconciliation agent              | `dontAsk` | Writes status + updated requirements   |
| `/validation-contract-generation` | `auto`    | Read-only                              |
| `/map-feature-to-plans`           | `auto`    | Read-only                              |
| `/create-plan-tdd`                | `auto`    | Read-only                              |
| `/implement-plan-tdd`             | `dontAsk` | Writes to files including `~/.claude/` |
| `/simplify`                       | `dontAsk` | Applies fixes                          |
| `/jbb-feature-dev:code-review`     | `dontAsk` | Writes its doc under `~/.claude/`      |
| Code-review fix pass (step 9b)    | `dontAsk` | Edits source and commits               |
| Validator agent                   | `dontAsk` | Writes validation-state.json           |
| Verify-fix recheck agent          | `dontAsk` | Writes recheck JSON                    |
| Report generator                  | `dontAsk` | Writes final-report.md                 |
| `/commit`                         | `auto`    | Git operations                         |
| `/submit-pr`                      | `auto`    | Git + GitHub operations                |

## Choosing a model per stage

**There is no default model. You choose one per stage and record why.**

You are better placed than this document to make that call, because you can see
what the stage actually is: how novel the problem is, how tightly the stage skill
scripts the work, how much a mistake there costs, and how much of the run's
budget is already spent. Both `opus` and `sonnet` are live options — the `opus`
alias resolves to `claude-opus-5` in the CLI (`--model opus`) and the Agent tool
(`model: opus`), verified 2026-08-04.

### What a tier costs

Per million tokens, input / output:

| Alias    | Resolves to      | $/MTok in   | $/MTok out    |
| -------- | ---------------- | ----------- | ------------- |
| `haiku`  | Claude Haiku 4.5 | 1           | 5             |
| `sonnet` | Claude Sonnet 5  | 3 (2 intro) | 15 (10 intro) |
| `opus`   | Claude Opus 5    | 5           | 25            |
| `fable`  | Claude Fable 5   | 10          | 50            |

Sonnet 5's introductory rate runs through 2026-08-31, so the `opus`/`sonnet`
output ratio is 2.5x until then and 1.67x after. Re-check pricing rather than
trusting these figures indefinitely — invoke the `claude-api` skill, which reads
from a dated table and can fetch live rates.

Output tokens dominate: a stage that writes a plan or a diff is priced mostly on
what it produces, so the ratio that matters is the output column.

### What actually varies between stages

The signal worth weighing is **how much of the thinking the stage skill has
already done**, not whether a stage sounds important:

- Stages whose skill is a detailed procedure — `/implement-plan-tdd`'s red-green
  script, the validator executing contract assertions, `/simplify`'s cleanup
  angles, `/commit` — hand the model a decision-poor path to walk. A cheaper tier
  executing a good procedure competes well here, and these are also the longest
  stages, so tier choice moves the bill most.
- Stages that are open judgment with no script — `/design-approach` choosing
  between architectures, reconciliation deciding whether a finding contradicts a
  requirement, `/map-feature-to-plans` deciding where to cut a feature — spend
  most of their tokens deciding rather than producing. They are short, so a
  stronger tier costs little in absolute terms, and a wrong decision propagates
  into every downstream stage.
- Mechanical fills — the report generator populating a template — are the case
  where `haiku` is genuinely enough and an error is cheap and obvious.

Two facts constrain the choice rather than informing it:

- **Unpinned children inherit the wrapper's model** (verified 2026-07-04), so a
  stage's tier applies to every sub-agent it spawns. A stage that fans out to
  many sub-agents multiplies whatever you picked.
- **Goal-loop fix subagents deliberately carry no `model:` override** and inherit
  the orchestrator session's model (decision 2026-07-05). That is not yours to
  vary per stage.

### Recording the choice

Append one line to the state file's `decisions` array per stage: the stage, the
tier, and the reason in a clause. A run that cost more or less than expected is
only diagnosable if the tier choices are recoverable — and without the reasons,
two runs of the same feature that picked differently look like noise instead of
two defensible judgements.

## Stage-Specific Argument Notes

Every stage skill here parses arguments its own way, and three of them fail
silently rather than erroring on the wrong form. Check this list before
invoking any of them.

- `/research-problem` takes its requirements path as a **positional**
  argument. Passing `--requirements <path>` causes the skill to treat the
  flag literally as a search term and produce empty output.
- `/operational-context` takes no `--requirements` flag either — one or more
  positional `<component-name>` arguments instead, plus `--non-interactive`.
- `/design-approach` requires the equals form `--requirements=<path>` (the space
  form is not parsed correctly) **and** a positional research-doc path:
  `<research-doc-path> --requirements=<path> --non-interactive`. Always pass the
  orchestrator's own canonical research-doc path, never one the research doc
  suggests in its own text — that suggestion targets the skill's default output
  location, which will not exist once the Output Location Override has
  redirected the real artifact elsewhere.
- `/map-feature-to-plans` takes no `--requirements` flag — the research-doc path
  is a required positional argument, and the only file it reads.
- `/jbb-feature-dev:code-review` takes a bare **PR number or branch name** as its
  first positional argument — never a path, never a PR URL. It checks that
  argument out against an already-cloned repo, so a worktree path there is
  parsed as a branch and the checkout fails; the worktree travels via the
  wrapper's checkout anchor instead. **Always pass `--non-interactive`**: without
  it, an unresolvable scope stops the stage on a prompt nobody is present to
  answer and the run stalls with no error.
- `/create-plan-tdd` is a single-feature planner: a positional input-file path,
  `--contract <path>`, `--non-interactive`. It has no `--plan-id` and no
  multi-plan concept at all, so scoping it to one plan of a multi-plan wave
  means extracting that plan's outline into its own standalone single-plan input
  document first (title, scope, files, dependencies, coverage, plus pointers to
  the full context docs — the convention the scoping doc's own "Suggested Next
  Steps" section already uses).
- `/implement-plan-tdd` gets `--skip-final-review` from the orchestrator — its
  Steps 6-7 are quality and guideline-compliance passes, which step 9's single
  `/jbb-feature-dev:code-review` covers once for the whole change, and cleanup is
  covered by `/simplify` in step 8.

## Review-Phase Enforcement

Three stages require the review-phase addendum appended to their wrapper
prompt: `/research-problem`, `/map-feature-to-plans`, `/create-plan-tdd`.
See `references/review-phase-enforcement.md` for the exact addendum text
and the post-stage artifact check.

## Fallback Timers

Pair every stage with one background-sleep watchdog
(`sleep <seconds>` with `run_in_background: true`) launched right after
the wrapper. If the wrapper's completion notification arrives first, the
timer's later expiry is ignored. If the timer fires first, enter the
recovery ladder.

Size timers at roughly 2× the stage's historical duration (2026-06-30 run),
with a 30-minute floor:

- research: hours by design — 4h minimum, and duration alone is NEVER a
  stall signal (follow the milestone log)
- ops-context / design / contract / scoping / simplify / report / commit /
  submit-pr: 45-60 min
- code review (step 9): 60 min. It fans out to roughly ten agents in parallel
  and then runs a sequential calibrate/dedup pipeline, so it is materially
  slower than the single-pass inline review this pipeline used to call — size
  the timer from that, not from the 236 s the old transport measured.
- planning per plan: 2h (plan 1 took 49 min)
- implementation per plan: 3h (plan 1 took 75 min)
- reconciliation / validator / recheck: 60 min

## Waiting Discipline and Recovery Ladder

1. After launching, WAIT for the wrapper's completion notification or the
   fallback timer. Do not poll, run diagnostics, check output files, or
   run `git status`.
2. NEVER re-attempt a stage while a prior attempt may still be running.
3. An `idle_notification` without content from a wrapper is NOT completion
   and NOT failure. Check the milestone log (sanctioned read): if it shows
   an in-progress phase with pending background work, keep waiting — a
   wrapper waiting on background tasks reports as "available" (observed
   2026-07-02).
4. If the fallback timer fires, or the log shows the stage should already
   have delivered: SendMessage the wrapper **by name** once, asking it to
   finish and deliver its completion report. Known harness gap (2026-07-02,
   broadened 2026-07-05): a wrapper idle-waiting on its own background work
   is not reliably woken by that work's completion — and this applies to
   ALL wait shapes, not just child sub-agents: a wrapper Monitor-waiting on
   a plain background Bash task stalled silently for ~7 hours on a
   90-second `tox` run before a SendMessage nudge woke it. The nudge is
   standard recovery. Wrappers should therefore avoid fire-and-forget
   background waits, stay synchronous wherever possible, and ACTIVELY poll
   their own spawned subagents/tasks (TaskOutput/output-file reads) rather
   than idle-waiting for wake events. Include this instruction verbatim in
   wrapper prompts: "Prefer actively checking any subagents or background
   tasks you spawn over idle-waiting; wake events are unreliable."
   Watchdog-timer caveat (2026-07-05): background sleep timers can be
   stopped externally (user or harness) without expiring — a killed timer
   notification is not a stage signal; check the milestone log and re-arm
   or switch to nudge-based liveness checks instead of assuming anything
   about the stage.
5. If the nudge produces nothing within ~5 minutes, check the artifact and
   milestone log, then respawn the stage once.
6. If the respawn also fails, halt and escalate. Only conclude failure
   from evidence: log stalled AND artifact missing AND no response.
7. Record each wrapper's `name` and returned agent id in the state file so
   recovery is possible after context compaction.

## Parallel Execution Pattern

Three points in the pipeline run wrappers in parallel: the
ops-context/design pair (step 4), the contract/scoping pair (step 6), and
per-plan planning within a wave (7a). Implementation (7b) is strictly
sequential.

1. For each pending plan in the wave, mark `in_progress` in the state
   file, then spawn all wrappers **in a single message** (one Agent call
   per plan) plus one shared fallback timer sized to the slowest stage.
2. Wait for all completion notifications.
3. Mark each plan `complete` or `failed` from its wrapper's completion
   report and artifact check, using the atomic write pattern.
4. If any plan failed, abort the run — downstream waves never start with
   broken inputs.

## Fallback Artifact Search

Skills sometimes ignore the Output Location Override and write to their
default path. When the canonical artifact is missing after a stage completes:

1. Check these fallback directories (files modified within the last 60 minutes):
   - Research: `~/.claude/thoughts/shared/research/`
   - Scoping: `~/.claude/thoughts/shared/scoping/`
   - Plans: `~/.claude/thoughts/shared/plans/` or `~/.claude/thoughts/shared/research_plans/`
   - Contract: `~/.claude/thoughts/shared/` (files matching `*contract*.md`)
   - Review: `~/.claude/thoughts/shared/reviews/`
2. **Always pick the most recently modified file** when multiple candidates
   match. Skills that write repeatedly to the same base name append a counter
   suffix (`_2`, `_3`, ...), so `find ... | sort` by name picks the oldest; use
   `ls -t` or `find -printf '%T@ %p\n' | sort -rn` to get the newest. Picking a
   stale file causes a stage to re-evaluate already-addressed material.

   Review documents are exempt, but only because step 9a passes an Output
   Location Override naming `$RUNS_BASE/code-review.md`, so the document is
   addressed directly rather than discovered. If that override is ever dropped,
   this exemption becomes a hole: the skill's own default path is built from a
   PR number that does not exist yet at step 9, so there would be nothing
   predictable to fall back to.

3. If found at a fallback location, copy it to the canonical path.
4. If not found anywhere, treat as a stage failure.

## Appendix: Detached `claude -p` Fallback

Escape hatch if Agent-tool wrappers prove unreliable in practice. Launch
the stage as a detached subprocess and wait on the artifact with the
Monitor tool (until-loop on artifact existence) — never fixed sleeps:

```bash
cat > "$LOG_DIR/<stage>-prompt.txt" << 'PROMPTEOF'
<slash-command + args + addenda — markdown is safe inside a heredoc>
PROMPTEOF

cd "$WORKTREE" && nohup bash -c 'cat "$LOG_DIR/<stage>-prompt.txt" \
  | claude -p --permission-mode <mode> --model <tier> \
  > "$LOG_DIR/<stage>.log" 2>&1' &
```

Notes preserved from the claude -p era: prompts containing `**` sequences
must be piped via stdin (CLI argument parsing misreads them as
`--allowedTools` wildcards); never pass `--bare`, `--continue`, or
`--resume`; harness-tracked (non-detached) background `claude -p` is killed
at ~30 minutes and must not be used for any stage.
