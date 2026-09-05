---
name: orchestrate-feature-dev
description: >
  End-to-end pipeline orchestrator for jbb-feature-dev. Chains /research-problem,
  /operational-context, /design-approach, /validation-contract-generation,
  /map-feature-to-plans, /create-plan-tdd, /implement-plan-tdd, /simplify,
  /jbb-feature-dev:code-review, validator agent, /commit and /submit-pr via
  background Agent-tool stage subagents, all with context isolation. Honors the DAG produced by /map-feature-to-plans;
  runs validation contract and scoping in parallel after requirements
  reconciliation; runs validator agent + execution
  gates and embeds verification evidence into the PR body. Use to automate
  manual /clear-between-stages workflow. Trigger phrases (1) "orchestrate
  feature" (2) "run the full pipeline" (3) "build this feature end-to-end".
argument-hint: '[--prompt "<text>"] [--requirements <path>] [--skip-research] [--design <path>] [--slack-channel <id>] [--ticket <KEY>] [--restart] [--branch <name>] [--no-worktree]'
---

# /orchestrate-feature-dev

End-to-end pipeline orchestrator: one invocation drives research, planning,
implementation, review, verification, commit, and PR submission. Every stage
runs in its own background Agent-tool subagent (a "stage wrapper") for context
isolation. By default all work runs in an isolated git worktree so the
original checkout stays untouched.

## Parent-Context Discipline

You ARE the orchestrator. Your job is to spawn background stage wrapper
subagents (via the Agent tool) that do the work, then collect their
artifacts. Source code and research content in YOUR context defeats the
orchestrator's purpose.

**Stage wrapper delivery resilience**: a wrapper may go idle without
delivering, or die silently. Follow the recovery ladder in
`references/stage-execution.md § Waiting Discipline and Recovery Ladder` —
milestone log first (an idle notification during pending background work
means keep waiting), then one SendMessage nudge by name, then one respawn,
then halt and escalate. Never self-evaluate as a substitute for an
independent stage.

**Never in this context:**

- Read source files of the target repo (no `Read`, no `cat`, no glob walks)
- Use `Grep` / `Glob` to explore the target repo or any external repo
- Spawn ad hoc sub-agents for research, exploration, analysis, or fixes —
  the only sanctioned Agent calls are the stage wrappers defined in this
  pipeline and the subagents the `/goal` fix loops direct
- Read the body prose of requirements, research, scoping, or plan docs
- Poll `git diff`, `git status`, or `ps aux` while waiting for a stage
- Re-attempt a stage while a prior attempt is still running

**Sanctioned reads (narrow exceptions):**

- `grep -q '^## '` against a research doc to detect routing headings
- `awk`/`sed` against doc frontmatter for slug derivation
- `jq` against the state file for plan IDs, statuses, DAG structure
- Reading a stage's milestone log during the recovery ladder
- A single `Bash` for workspace prep (e.g., sparse-checkout for a monorepo)
- Committing what `/simplify` (step 8) hands back uncommitted, and writing the
  `code_review` state object from the counts step 9b returns — the only writes
  this context makes directly. It never reads the review document itself; the
  step 9b fix stage does that

## Inputs and Flags

Parse `$ARGUMENTS` for these flags. No positional arguments; unknown flags
are a hard error.

| Flag                    | Default | Effect                                                  |
| ----------------------- | ------- | ------------------------------------------------------- |
| `--prompt "<text>"`     | not set | Free-text problem statement; full pipeline from scratch |
| `--requirements <path>` | not set | Skip elicitation; start at research                     |
| `--skip-research`       | off     | Skip research step (user must explicitly request this)  |
| `--design <path>`       | not set | Skip design exploration; thread into planning           |
| `--slack-channel <id>`  | not set | Route notifications to this channel instead of DM       |
| `--ticket <KEY>`        | auto    | Force a Jira key; otherwise auto-detected from branch   |
| `--restart`             | off     | Delete prior state file and logs before running         |
| `--branch <name>`       | auto    | Use this branch instead of auto-creating one            |
| `--no-worktree`         | off     | Work directly in the current checkout                   |

**Mutual exclusion**: `--prompt` is exclusive with `--requirements`/`--design`.
`--design` requires `--requirements`.
At least one of `--prompt` or `--requirements` must be provided.

Record every parsed flag into the state file's `cli_args` verbatim so
resumed runs recover their original configuration.

## State Management

State file: `~/.claude/thoughts/shared/orchestrator-state/<run-id>.json`.
Log directory: `~/.claude/thoughts/shared/orchestrator-state/logs/<run-id>/`.

**Run ID derivation**: with `--requirements`, the basename without extension.
With `--prompt`, deferred — hold the placeholder `_pending` until research
produces a doc, then take the slug from its `title:` frontmatter or first H1.
The slug must be kebab-case, lowercase, at least 6 characters, and reflect the
understood objective rather than the surface prompt text. Never fall back to a
hash or timestamp.

**Artifact layout**: pipeline artifacts go under
`~/jbb-feature-dev/orchestrator-runs/<run-id>/`, each named
`<YYYY-MM-DD>-<type>.md`. Internal state stays under
`~/.claude/thoughts/shared/orchestrator-state/`.

See `references/state-file.md` for the JSON schema, resumability rules, and
the atomic write pattern (always `mktemp` + `mv`, never edit in place).

## Stage Execution Pattern

Every pipeline stage runs as a named background Agent-tool subagent that invokes
the stage's skill via the Skill tool (or executes a direct agent prompt) and
writes a milestone log. `references/stage-execution.md` has the canonical
wrapper call and prompt template, the Output Location Override, the mode table
and per-stage model selection, the milestone and final-message contracts,
fallback timers, the recovery ladder, and the parallel launch/wait pattern.

**Key rules:**

1. Spawn every stage with `run_in_background: true`, an explicit `name`,
   the mode from the mode table, and a model you chose and recorded.
2. Pair every stage with a background-sleep fallback timer sized per
   `references/stage-execution.md § Fallback Timers`.
3. Wait for the completion notification or the timer — do not poll.
4. Never re-attempt while a prior attempt is running.
5. After completion, check for the output artifact; if missing at the
   canonical path, search fallback locations before re-launching.

---

## Pipeline

### 1. Setup

Parse arguments and validate mutual exclusion. Create or resume the state
file. On resume (no `--restart`), read the existing state file and recover
`cli_args` — persisted args win over re-supplied flags. Reset any
`in_progress` plans to `pending` for crash recovery.

Compute a feature branch name (e.g., `feature/<ticket>-<run-id>` or
`feature/<run-id>`). In worktree mode (default), create a git worktree at
`~/.claude/worktrees/<run-id>` — never under `/tmp` or `/private/tmp`, where
macOS cleanup coinciding with a session restart destroyed hours of uncommitted
implementation work in a long-running run (verified 2026-07-10). In
`--no-worktree` mode, checkout the branch in the current repo. On resume,
reuse the existing worktree if it still exists; recreate from the
persisted branch if the worktree location was cleared — note this only
restores what was already _committed_, which is exactly why step 7b now
commits after every plan rather than deferring everything to step 14.

If `RUN_ID == "_pending"` (--prompt mode), defer branch and worktree
creation until after Slug Finalization (step 3).

Copy input files (requirements, research, design) to
`$RUNS_BASE/input/` for archival. Idempotent on resume.

### 2. Research

**Skip if**: `--skip-research` was explicitly supplied by the user.

Invoke `/research-problem` via a stage wrapper. If `--requirements` is set,
pass the requirements path as a **positional** argument — the skill does
not parse `--requirements` as a flag. If `--prompt` mode, persist `$PROMPT`
to `$LOG_DIR/prompt-input.md` first, then pass that path positionally.

Append the review-phase enforcement addendum from
`references/review-phase-enforcement.md`. Wrapper mode: `auto`.
Research legitimately runs for hours — size the fallback timer
accordingly and never classify the stage as stalled on duration alone;
follow the milestone log.

**Output**: `$RUNS_BASE/<date>-research.md`

**Post-check**: Run the review artifact check from
`references/review-phase-enforcement.md`. Absence of review evidence is
a hard escalation, not a retry.

### 3. Slug Finalization

**Only when** `RUN_ID == "_pending"` (--prompt mode).

Extract the project slug from the research doc's `title:` frontmatter or
first H1 heading. If extraction fails, escalate — never fall back to a
hash. Rename all placeholder paths (state file, log dir, artifact dir)
from `_pending` to the final slug. Re-derive all path variables. Then run
the deferred branch and worktree creation from step 1.

### 4. Conditional Operational Context and Design Approach

Scan the research doc for routing recommendation headings:

- `## Operational Context Recommendation` containing "Consider running"
  → launch `/operational-context`
- `## Design Exploration Recommendation` containing "Consider running"
  → launch `/design-approach`

When both are recommended, launch them **in parallel** as background stage
wrappers, then wait for both.

**Override**: skip `/design-approach` if `--design <path>` was supplied.

Both skills parse their arguments in forms that fail silently when you get them
wrong — read `references/stage-execution.md § Stage-Specific Argument Notes`
before invoking either. Extract `/operational-context`'s component names from
the research doc's own "Consider running" recommendation text.

Wrapper mode: `auto` for both. Pick each model per
`references/stage-execution.md § Choosing a model per stage`.

Record the routing decision in the state file's `decisions` array.

### 5. Requirements Reconciliation

Reconcile the requirements against findings from research, ops context and
design approach, so that stale assumptions, unrealistic NFRs and approach
mismatches are corrected before contract generation consumes them.

Invoke a reconciliation agent via a direct background Agent call using the
prompt from `references/agent-prompts.md § Reconciliation Agent`. Pass paths to
all available stage outputs as file references — the agent reads them itself, so
do not inline content. Mode `dontAsk`; instruct it to use only Read and Write.

It returns a status JSON (`objective_conflict`, `changes_made`) and optionally an
updated requirements doc with provenance markers. Escalate if the Objective is
contradicted. If changes were made, validate the updated doc (required sections
present, at least half the original length), then point `$REQUIREMENTS` at it.

Non-fatal: retry once on failure, then proceed with the original requirements.
Record the decision in the state file.

### 6. Contract Generation and Feature Scoping (parallel)

**Dependency**: runs after requirements reconciliation (which may update
`$REQUIREMENTS`). The two stages read disjoint inputs — the contract reads
the reconciled requirements, scoping reads the research doc — and both are
read-only, so launch them **in parallel** as background stage wrappers in
a single message (one shared fallback timer sized to the slower stage),
then wait for both.

**Contract**: invoke `/validation-contract-generation` via a stage wrapper
with `--requirements <path> --non-interactive`. Mode
`auto`. Output: `$RUNS_BASE/<date>-verification-contract.md`

**Scoping**: invoke `/map-feature-to-plans` via a stage wrapper with
`<research-doc-path> --non-interactive` (positional; see the argument notes).
Append the review-phase enforcement addendum. Mode `auto`. Output:
`$RUNS_BASE/<date>-scoping.md`

**Post-check**: run the review artifact check against the scoping output.

Parse the scoping document to extract the DAG of waves and plans. Mirror
this structure into the state file's `dag.waves` array so wave execution
and resumability work correctly.

### 7. Wave Execution

Iterate waves sequentially in the DAG's topological order. Each wave plans
and implements its plans before advancing to the next wave. Within a wave,
**planning runs in parallel** across plans (read-only, API-bound);
**implementation runs strictly sequentially**, one plan at a time. Code
review runs once after all waves complete (step 9).

**7a. Planning**: `/create-plan-tdd` is a single-feature planner with no
multi-plan concept, so each plan in the wave needs its own standalone input
document extracted from the scoping doc — see `references/stage-execution.md
§ Stage-Specific Argument Notes`. Launch every pending plan in the wave as a
parallel background stage wrapper passing `<plan-outline-path> --contract
<contract-path> --non-interactive`. Append the review-phase enforcement
addendum. Wrapper mode: `auto`.

**Output per plan**: `$RUNS_BASE/<date>-plan-<plan-id>.md`

Wait for all plans in the wave. Mark each plan's planning phase `complete`
or `failed` based on exit code. Run the review artifact check on each
completed plan. Then run a plan coverage check: grep each completed plan
doc for `VAL-*` assertion IDs from the contract and warn if any are
uncovered. Abort if any plan failed.

**7b. Implementation**: For each plan in the wave, in the scoping doc's
listed order, invoke
`/implement-plan-tdd <plan-path> --non-interactive --skip-final-review`
via a stage wrapper and **wait for it to complete before starting the next
plan**. Plans are never implemented in parallel — not even with disjoint
file sets. Concurrent implementations run concurrent test suites, which
caused CPU saturation and cross-plan test noise in the 2026-06-30 run.
`--skip-final-review` stays for the reason in the argument notes. Wrapper mode:
`dontAsk` (needed for writes to sensitive directories like `~/.claude/`).

Immediately after each plan's implementation stage reports complete —
before starting the next plan or advancing to the next wave — invoke
`/commit --non-interactive` via a stage wrapper (mode `auto`) to commit that
plan's changes. Do not batch multiple plans'
implementation work into one commit deferred to step 14: a run with
several waves and hours-long implementation stages can accumulate
substantial uncommitted work, and a committed change survives a lost or
recreated worktree while an uncommitted one does not, however durable the
worktree's location is (verified 2026-07-10, see step 1). Step 14's later
`/commit` invocation then only needs to capture whatever steps 10-12 (contract
amendment, validation fixes) added on top; steps 8 and 9b commit their own work.

### 8. Code Simplification

After all wave implementations complete — and **before** the code review —
invoke `/simplify` once on the cumulative diff via a stage wrapper. Wrapper
mode: `dontAsk`.

**Once, not per plan, and not a loop.** `/simplify` reviews for reuse,
simplification, efficiency and altitude and applies what it finds; it explicitly
does not hunt for correctness bugs, so there is no gate to converge toward and
nothing to re-measure. Running it on the cumulative diff lets it see duplication
*between* plans, which is where most of it accumulates and which a per-plan pass
cannot see at all.

Ordering matters: cleaning first means the review's attention goes to
correctness rather than to mess that was about to be removed anyway.

**Commit whatever it changed, before step 9 runs.** The review resolves its
scope as a committed range and only falls back to the working tree when that
range is empty — which step 7b guarantees it is not. So an uncommitted
`/simplify` is invisible to the review: it would read the pre-simplify tree and
report findings whose line numbers no longer match the file on disk, which is
the exact inversion of the ordering rationale above. Commit via
`/commit --non-interactive` in a wrapper, or directly.

Non-fatal: if it fails, proceed with the current code. Record the outcome.

### 9. Code Review

One review, one fix pass, no loop. The review and the fixing are **two separate
stage wrappers** because `/jbb-feature-dev:code-review` is explicitly a read-only
command ("DO NOT make any code changes") and this parent context may not read
source or edit files. Neither actor can do both halves.

**9a. Run the review, once.** Invoke `/jbb-feature-dev:code-review` via a stage
wrapper with `<branch-name> --non-interactive`, and append the Output Location
Override naming `$RUNS_BASE/code-review.md`. Wrapper mode: `dontAsk` — the skill
does `mkdir -p ~/.claude/thoughts/shared/reviews/` and writes there, and `auto`
does not permit writes under `~/.claude/`.

Three details are load-bearing:

- **The first argument is a branch name, never a path and never a PR URL.** The
  skill checks that argument out against an already-cloned repo. A worktree path
  in that slot is parsed as a branch and the checkout fails. The worktree reaches
  the stage through the wrapper's checkout anchor, not through this argument.
- **`--non-interactive` is not optional.** Without it an unresolvable scope stops
  the stage on a question nobody is present to answer, and the run stalls with no
  error.
- **The Output Location Override is what makes the artifact findable.** The
  skill's own default path is derived from a PR number, and no PR exists until
  step 14. Without the override the document lands somewhere this pipeline cannot
  predict, and `references/stage-execution.md § Fallback Artifact Search`
  explicitly does not cover review documents.

There is no fix loop, no severity gate and no confirmatory re-run — one pass, and
what it reports is the last diff-reading signal this pipeline produces.

**Why one pass, stated plainly because it is a trade and not a cleanup.** The
loop this replaces was measured over 12 rounds: its stop-or-continue decision
flipped on 25% of rounds when the identical review was re-run against the
identical commit, and 41% of the findings it blocked on sat in tests, comments or
scaffolding no user can reach. Real defects will ship that the loop would have
caught. The functional net that remains is step 12's verify-fix loop, which tests
behaviour against the contract instead of reading the diff, and which is never
waivable.

**Output**: `$RUNS_BASE/code-review.md`. If the wrapper's `ARTIFACT` line names a
different path, record that one instead — step 10 halts without a review
document.

**9b. Address the findings, in one fix stage.** Spawn a single stage wrapper
(mode `dontAsk`) using the prompt in `references/agent-prompts.md § Code Review
Fix Pass`. It runs **once**. Do not set a `/goal`, do not re-run the review to
check its work, and do not spawn a second pass — a second draw is precisely the
noisy signal that was measured and abandoned.

That prompt carries the standing default: **the fix stage addresses code-style
findings, including Minor and Enhancement ones**, and files everything it does
not fix. The reason is that they are cheap and usually right, and that in real
runs they are the findings most likely to be dropped — they rank below whatever
gate is in force, so they are always the work that gets cut when a stage runs
long. That is operator experience across real runs, not something the A/B eval
of this change demonstrated: on a small clean fixture the previous skill's own
style pass addressed all of them. The default exists for the long, loaded run,
which is the case the fixture cannot reproduce.

The stage commits its own work and returns three counts in its final message:
findings reported, findings addressed, findings filed.

**9c. Record what happened.** Write the `code_review` object to the state file
from those three counts per `references/state-file.md` note 9, and emit the
`STAGE_METRIC` line per `references/stage-execution.md § Loop metrics every run
must record`.

**`addressed + filed` must equal the number reported.** If it does not, the fix
stage dropped findings silently — and with no second review pass to re-report
them, nothing downstream will ever surface them again. Treat a mismatch as a
failed stage and escalate; it is the only check standing between "shipped with
known findings", which is the design, and "shipped with forgotten ones", which is
not.

### 10. Contract Amendment

Amend the validation contract to cover files changed during implementation
that were not anticipated by the original requirements.

Invoke `/validation-contract-generation --amend` via a stage wrapper (mode
`auto`) with `--contract <contract-path> --non-interactive`, plus one
`--review-doc`: the review document step 9 recorded. `--review-doc` is
repeatable and **at least one is mandatory in amend mode** — the skill halts
with an error when it is missing, so pass it explicitly rather than relying on
discovery. There is exactly one review document per run now, so if step 9's path
was not recorded this stage has nothing to pass and cannot run correctly.

Retry once on failure; on second failure, proceed with the unamended
contract (amendment is strictly additive — no regression). Record outcome.

### 11. Validation

**A background stage cannot perform real writes to shared services**, and
relaying the user's own authorization into one never unblocks it — the
permission classifier scopes consent to the acting agent's transcript. Handle
that in two places. An assertion whose stimulus is such a write is marked
`operator_executed` when the contract is written (step 10), so its status is a
design decision rather than a surprise here. If one reaches this step unmarked,
it becomes `needs_operator` and escalates — never `blocked`, and never deferred
into a post-merge follow-up. The hand-off procedure is in
`references/escalation.md § Operator-Executed Assertions`. Read-only
verification (SQL against a run-state database, transcripts, audit events) stays
available to a background stage throughout.

**11a. Validator agent**: invoke via a direct background Agent call using
the prompt from `references/agent-prompts.md § Validator Agent`. Mode
`dontAsk`; instruct the agent to use only Read, Bash, and
Write. The validator writes structured JSON to
`$RUNS_BASE/validation-state.json` conforming to
`scripts/validator-schema.json`.

After the validator completes, cross-reference its output against the
contract — any contract assertions (`VAL-*`) the validator omitted get
appended as `failed`.

**11b. Execution gates**: independently verify build and test exit codes.
Detect the build system from file presence (`pom.xml`, `build.sbt`,
`pyproject.toml`, `BUILD`/`BUILD.bazel`). Run build and test commands. If
the contract mentions a health endpoint URL, curl it. Append `GATE-BUILD`,
`GATE-TEST`, and optionally `GATE-HEALTH` assertions to
`validation-state.json`.

**11c. Aggregate**: run `scripts/aggregate_verify.py` against
`validation-state.json` and the contract to produce a verify summary.

### 12. Verify-Fix Loop

Set the `/goal` using the verbatim text from `references/agent-prompts.md
§ Verify-Fix Goal`, which carries the non-negotiable core: every contract
assertion passes, the validator agent reruns the full contract each cycle, and
an assertion that failed a _live_ validator pass is only confirmed by a targeted
live recheck of the same Setup/Stimulus/Assertion — never by a passing unit test,
which is not evidence for timing, state or event-ordering failures.

**Recheck merging**: after each targeted recheck produces its own result
file, merge it into the running `validation-state.json` with
`scripts/aggregate_verify.py merge <validation-state.json>
<validation-state.json> <recheck.json>` (the recheck's verdict supersedes
the assertion's prior entry; unrelated assertions are untouched). This is
the canonical merge path — do not hand-roll `jq`/`python3` merges for
recheck results.

After the goal resolves, record the verification outcome
(total/passed/failed/blocked counts) in the state file.

### 13. Final Report

Generate `final-report.md` — this is mandatory and feeds the PR description.

Invoke a report generator via a direct background Agent call using the
prompt from `references/agent-prompts.md § Report Generator`. Pass absolute
paths to the state file, log directory, runs base directory, and this
skill's `references/report-template.md`. Mode `dontAsk`; instruct the agent to
use only Read, Write, and Bash. This is a mechanical template fill — the one
stage where `haiku` is genuinely enough, because an error is cheap and obvious.

**Output**: `$RUNS_BASE/final-report.md`

Verify the report file exists after completion.

### 14. Commit and PR

Invoke `/commit --non-interactive` via a stage wrapper. Wrapper mode:
`auto`. Per-plan implementation work is already committed (step 7b), and so are
simplification (step 8) and the review fixes (step 9b) — this call captures
whatever remains: contract amendment (10) and validation/verify-fix changes
(11-12). It is not expected to be a no-op even when 7b ran cleanly.

Then invoke `/submit-pr` via a stage wrapper with:

- `--verification <verify-summary-path>`
- `--requirements <requirements-path>`
- `--scoping-doc <scoping-path>` (if the scoping doc exists)
- `--non-interactive`

Wrapper mode: `auto`. Auto-detect the Jira key from the branch name
(regex `[A-Z]+-[0-9]+`) and record it in the state file. Do not forward
`--ticket` to `/submit-pr`.

### 15. Build Verification Loop

Set the `/goal` using the verbatim text from `references/agent-prompts.md
§ Build Verification Goal`. Both halves are required: the PR build green via
`gh pr checks` with failures classified before fixing, and every Gosling Code
Review finding checked on every iteration — Gosling posts new findings after
each push — verified against the current code rather than applied blindly, then
fixed or rebutted, replied to, and its thread resolved.

### 16. Cleanup and Notification

On success: stage subagents leave untracked scratch behind — ad hoc scratch
directories, local databases used for live validation, `nohup.out`, pidfiles.
None of it is a deliverable, because every deliverable was committed in step 14
and the artifacts live under `$RUNS_BASE`. Run `git -C <worktree> clean -fdx`,
then `git worktree remove <worktree>`, falling back to `--force` if that fails;
the worktree is disposable once the branch is on the remote.

On escalation: leave the worktree intact for triage.

Send a Slack notification with the PR URL. Route to the invoking user's DM
by default, or to `--slack-channel` if set. See `references/slack-routing.md`
for resolution flows. Slack errors never fail the run.

---

## Escalation

Any unrecoverable failure escalates rather than retrying.
`references/escalation.md` has the trigger conditions, the diagnostic doc, the
failure report and the notification procedure. Never auto-retry an escalation: a
skipped review phase, a review that examined nothing, or a repeated verify
failure indicates a systemic problem that another automated attempt will not
address. A review finding the run does not fix is **not** one of these — it is
filed and the pipeline continues (`references/escalation.md`).

## References

- `references/state-file.md` — JSON schema, resumability rules, atomic write pattern
- `references/stage-execution.md` — stage wrapper invocation pattern, mode table, per-stage model selection (tier costs and what varies between stages), milestone log contract, fallback timers, recovery ladder, waiting discipline
- `references/agent-prompts.md` — Reconciliation, validator, and report generator prompts; Verify-Fix / Build Verification goal texts; TDD fix protocol; verify-fix recheck prompt; how to file what ships unfixed
- `references/report-template.md` — 6-section final report template
- `references/review-phase-enforcement.md` — Verbatim addendum text and post-stage artifact check patterns
- `references/slack-routing.md` — DM vs channel resolution, failure tolerance
- `references/escalation.md` — Diagnostic doc, failure report, and notification procedure
- `scripts/aggregate_verify.py` — Validation-state.json aggregator
- `scripts/validator-schema.json` — JSON schema for validator agent structured output
