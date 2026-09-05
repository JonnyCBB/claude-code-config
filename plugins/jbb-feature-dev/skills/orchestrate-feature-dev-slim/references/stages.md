# Stages

Per-stage arguments, modes, timers and artifacts for the six stages. Worker
mechanics themselves — prompt template, Output Location Override, milestone log,
final-message contract, checkout anchor, recovery ladder, fallback artifact
search — are inherited from
`../../orchestrate-feature-dev/references/stage-execution.md` and are not
repeated here.

`$RUNS` is `~/jbb-feature-dev/slim-runs/<run-id>/`. `$LOG` is
`~/.claude/thoughts/shared/orchestrator-slim/logs/<run-id>/`.

**The inherited files use the parent's names for these, so substitute as you
read.** Its `$LOG_DIR` is this pipeline's `$LOG`, its `$RUNS_BASE` is `$RUNS`,
and its steps 9 and 9a are stages 4 and 4a here. This matters in two specific
places rather than as a general caution: `stage-execution.md` sends milestone
lines to `$LOG_DIR/<stage-name>.log`, and `review-phase-enforcement.md` greps
`"$LOG_DIR/${STAGE}.log"` as the last rung of its evidence ladder before a hard
escalation. Neither name is defined anywhere in this skill, so taken literally
both resolve against an unset variable and test a path at the filesystem root.

## The table

| # | Stage    | Invocation                                                                                       | Mode      | Timer | Artifact                        |
| - | -------- | ------------------------------------------------------------------------------------------------ | --------- | ----- | ------------------------------- |
| 1 | Research | `jbb-feature-dev:research-problem` — `<doc-path> --non-interactive`                                | `auto`    | 4h    | `$RUNS/<date>-research.md`      |
| 2 | Implement | detached `claude -p "/goal ..."` (see below)                                                     | `dontAsk` | 4h    | `$LOG/implement-done.md` + commit |
| 3 | Simplify | `simplify`                                                                                        | `dontAsk` | 60m   | commit                          |
| 4a | Review  | `jbb-feature-dev:code-review` — `<branch> --non-interactive`                                       | `dontAsk` | 60m   | `$RUNS/code-review.md`          |
| 4b | Apply   | direct prompt (see below)                                                                         | `dontAsk` | 90m   | commit + the counts             |
| 5 | Verify   | `jbb-feature-dev:verify-implementation` — `<requirements-path> --requirements <requirements-path>`  | `dontAsk` | 90m   | `$RUNS/<date>-verification.md`  |
| 6 | Submit   | `jbb-feature-dev:submit-pr` — `master --verification <path> --requirements <path> --non-interactive` | `auto`    | 60m   | PR URL                          |

**The Mode column is not something you set. It is a requirement on YOU.** The
Agent tool's `mode` parameter is deprecated and ignored — its own schema says
"Subagents inherit the parent session's permission mode". Measured 2026-08-23:
the same stage, with the same table entry, had a write denied under a restricted
headless orchestrator and permitted under an interactive one. The table entry had
no effect either way.

So read the column as **what each stage must be able to write**, and satisfy the
strictest entry with the orchestrator's own permission mode before starting. Every
stage here needs to write under `~/.claude/` — the milestone log at minimum, and
stage 1 also writes `research-problem`'s internal research plan there — so the
orchestrator needs a mode that permits those writes. `acceptEdits` does not.

Keeping the column matters even though it is not settable: it is what makes the
orchestrator's own requirement checkable, and it tells you which stage to suspect
when a write is refused.

Timers are starting points at 2x expected duration — re-size them from your own
runs, and never treat duration alone as a stall signal for stage 1 or 2.

## Choosing a model

There is no default. Choose per stage and record the reason in `decisions`.
The full reasoning — tier costs, and what actually varies between stages — is in
`../../orchestrate-feature-dev/references/stage-execution.md § Choosing a model
per stage`. The short version for these six: stages 2 and 3 walk a detailed
procedure and are the longest, so tier choice moves the bill most there; stage
4b is judgement about whether a finding is right, which is where a weak tier
costs you most; stage 6 is close to mechanical.

Unpinned subagents inherit their parent's model, so a stage that fans out
multiplies whatever you picked.

## Argument notes, per stage

Each of these fails quietly rather than erroring, so check the form before
invoking.

**1 — research-problem** takes its document path **positionally**. Passing
`--requirements <path>` makes the skill treat the flag as a literal search term
and produce empty output. Append the review-phase enforcement addendum, and run
the artifact check afterwards.

**3 — simplify** is `/simplify`. Not `/polish-code`, which is a different skill
with a different job. Do not re-derive this from a filesystem search: a command
can be registered without a file at any path you would guess, so a search that
finds nothing proves nothing. `/simplify` is the step.

**4a — code-review** takes a bare **branch name** first — never a path, never a
PR URL. It checks that argument out against an already-cloned repo, so a
worktree path there is parsed as a branch and the checkout fails; the worktree
reaches the stage through the wrapper's checkout anchor instead.
`--non-interactive` is mandatory or an unresolvable scope stalls the stage on a
question nobody will answer. The Output Location Override is mandatory because
the skill's own default path is built from a PR number that does not exist yet,
and the inherited fallback artifact search explicitly does not cover review
documents.

**5 — verify-implementation** has **no `--non-interactive` flag** and its Step 1
"Locate Plan" is a four-rung fall-through ending in "ask user". Two rungs are
hazards for this pipeline, which writes no plan document at all:

- The last rung asks the user. In a background worker there is no user, so the
  stage hangs with no error, no exit code and no artifact.
- An earlier rung globs the most recent file in
  `~/.claude/thoughts/shared/plans/` matching the branch topic, which can match
  a stale plan from an unrelated run and yield confident evidence for the wrong
  feature.

Passing an explicit positional path keeps both unreachable. Pass the
requirements document, and pass it again via `--requirements` so the skill also
runs its requirements-alignment steps. Tracked as `jbrooksbartlett-nv27y`.

**6 — submit-pr** takes the target branch positionally, then `--verification`,
`--requirements` and `--non-interactive`. Do not pass `--auto-merge`.

## Stage 2: the detached `/goal` session

`/goal` is a session-scoped Stop hook and reaches only a genuine top-level
session. Measured 2026-08-23 on v2.1.241: inside an Agent-tool subagent it is
inert (no interception, no evaluator, no slash-command tool in that runtime);
as `claude -p "/goal ..."` it ran 6 turns and billed a second
`claude-haiku-4-5` model alongside the worker, which is the evaluator firing.

**Check the precondition first — it costs seconds.** Confirm `/goal` resolves in
a top-level session before committing hours to the stage:

```
claude -p '/goal Reply with the single word READY and stop after 1 turn.' \
  --output-format json 2>/dev/null | python3 -c 'import json,sys; \
  print(list(json.load(sys.stdin).get("modelUsage",{}).keys()))'
```

Two models listed means the Stop hook is live. One model, or an error, means
stage 2 cannot work as designed — stop here rather than discovering it later.

**Launch detached.** A harness-tracked background `claude -p` is killed at
around 30 minutes, which is well inside this stage's normal duration, so it must
be detached with `nohup`. Write the goal text to a file and pipe it in rather
than passing it as an argument: a prompt containing `**` is misread by CLI
argument parsing as an `--allowedTools` wildcard. Never pass `--bare`,
`--continue` or `--resume`.

**Run this as ONE invocation, with both paths exported.** Shell state does not
survive between an agent's tool calls, and the child `bash -c` inherits only
*exported* variables — `$LOG` appears inside single quotes, so the outer shell
never expands it and the child must resolve it from the environment. Get this
wrong and the failure is silent in the worst way: `cat ""` fails, the redirect
lands at the filesystem root and is denied, `nohup` still reports success
because it is backgrounded, `implement-done.md` is never written, and the wait
below blocks forever on a file that will never appear.

```
export WORKTREE=<absolute worktree path>
export LOG=<absolute log directory>

cat > "$LOG/implement-goal.txt" << 'GOALEOF'
/goal <your condition text>
GOALEOF

cd "$WORKTREE" && nohup bash -c 'cat "$LOG/implement-goal.txt" \
  | claude -p --permission-mode dontAsk --model <tier> \
      --output-format json > "$LOG/implement.json" 2> "$LOG/implement.err"' &
```

**Write the condition so the transcript can prove it.** The evaluator reads the
conversation and nothing else — it runs no tools and reads no files. So
"the tests pass" only works because the test command and its output land in the
transcript; "the code is clean" never works. State the outcome, the red-green
obligation, the artifact you want written, and a turn bound, all in the
condition text — a turn or time clause inside the condition is how `/goal`
documents bounding, and there is no separate parameter for it.

The condition must require the session to commit its work and to write a short
completion report to `$LOG/implement-done.md`: status, commit SHA, the test
command it ran and its result, and anything it could not do. That file is both
the artifact and the thing you wait on.

**Wait with a Monitor until-loop on `$LOG/implement-done.md`.** A detached
process sends no completion notification, so this is the one stage you do wait
on by condition — never a fixed sleep, and never by reading `implement.json`,
which is the full transcript and will flood your context.

**Two signals will lie to you about this stage being dead.** `implement.json` is
empty for the whole run, because `--output-format json` writes once at exit — an
empty file means "still going", not "died". And a name-pattern process check can
miss the session entirely: `pgrep -fc 'claude -p'` returned 0 against a session
that was running with 547MB resident. Check `pgrep -P <wrapper-pid>` for the real
child instead. Taken together those two false negatives read exactly like a silent
death, and acting on them means relaunching a live stage — two sessions writing one
worktree and one commit. Conclude failure only from the conjunction the inherited
recovery ladder names: log stalled AND artifact missing AND no response.

**Then confirm the goal loop actually engaged**, before trusting the stage. In
`implement.json`, `modelUsage` should list two models: the worker tier you chose
and a Haiku evaluator. One model means the Stop hook never fired and you got a
single-pass implementation wearing a convergence loop's clothes — treat that as
a failed stage, because the red-green discipline was never enforced by anything.
`num_turns` greater than one is corroborating but weaker; a one-turn success is
possible on a trivial feature.

**Then check every condition yourself. Session exit is not success.** Measured
2026-08-23: a stage-2 session exited cleanly, with the evaluator genuinely
engaged and the code genuinely working and tested, having met three of the five
conditions its own goal text stated — it never committed, and never wrote its
completion report. Both omissions break the next two stages, which resolve their
scope as a committed range, so neither is cosmetic.

Walk the conditions: is there a new commit (`git log <base>..HEAD`), is the tree
clean (`git status --porcelain`), does the completion report exist, and does the
test command it claims to have run actually pass when *you* run it. A condition
the evaluator waved through is still unmet.

Related, and worth not relying on: **the turn clause is advisory.** A condition
reading "stop after 40 turns regardless" ran to 53. `/goal`'s own documentation
presents that clause as the bounding mechanism, but it is not a hard cap — size
the fallback timer as though the bound were absent.

## Stage 4b: the apply-the-findings worker

One worker, once. No `/goal`, no second review pass to check its work — a second
draw on the same review is the noisy signal this single-pass design exists to
avoid.

Give it: the review document path, the worktree path, and this direction.

> Apply every recommendation in the review document unless there is a specific
> reason not to. **This includes Minor and Enhancement priority code-style
> findings — the default is to apply them.** Declining is the exception: for any
> finding you do not apply, write down which finding and why, in one sentence,
> and file it so it survives this run. Every declined finding gets filed — those
> are the same findings counted twice under two names, not two separate groups.
> Then commit your work.
>
> Your final message reports exactly these counts and nothing else: reported,
> applied_from_report, applied_extra, declined, filed — plus one line per declined
> finding giving its identifier and your reason. Do not include diffs, code or
> finding bodies. Define any count you report precisely enough that the
> orchestrator can re-derive it: in a real run "18" (findings) and "20" (lines of
> output) were both correct and were mistaken for a discrepancy, because nobody
> had said which was being counted. That is why the invariants above are stated
> over the review document, which is countable, rather than over a free-text
> metric, which is not.

Two invariants, not one, and both are about **the reported set**:

```
applied_from_report + declined == reported   # every reported finding went one way
filed == declined                            # and every declined one survives
```

`applied_extra` is counted separately and constrained by neither. A stage that
does more than it was asked is behaving well, and the arithmetic must not punish
it: measured 2026-08-23, a fix stage applied 18 things — the 16 reported plus 2
the review's own severity gate had excluded — and reported `applied=16`. Had it
counted honestly against a single `applied` bucket, `applied + declined ==
reported` would have failed on a stage that had over-delivered. Splitting the
counts is what lets the invariant mean "nothing reported was dropped" instead of
"nothing beyond the report was done".

`filed` counts the same findings as `declined`, not different ones — it is the
check that each decline was written down durably rather than merely mentioned.
Adding it as a third bucket (`applied + declined + filed == reported`)
double-counts every decline, so it fails the run precisely when the stage did
what it was told.

If either invariant breaks, the stage dropped findings; with no second review
pass, nothing downstream will surface them again. Treat it as a failed stage and
escalate.

Record all four counts and every decline reason in run state. The counts are
also how a future change to this stage gets judged, so write a greppable
milestone line:

```
<ts> <epoch> STAGE_METRIC stage=review reported=7 applied_from_report=6 applied_extra=2 declined=1 filed=1
```
