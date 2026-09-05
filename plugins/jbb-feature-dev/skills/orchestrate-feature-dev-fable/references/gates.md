# Gates

A gate is an outcome that must be true, backed by evidence recorded in the
run state, before dependent work starts. Gates are the fixed part of this
pipeline; the route between them is yours. Each section states the outcome,
the default way to produce it, the evidence check, and what (if anything) is
waivable.

Two gates exist because of the user's acceptance bar and are **never
waivable**: G2 (a frozen, live-testing-enforced validation contract before
implementation) and G6 (live verification evidence for every assertion).
Without live evidence the user does not have enough to accept an
implementation — a green unit-test suite is not acceptance evidence.

The two convergence loops — G6's verify-fix and G7's build/Gosling loop — run
as `/goal`s, not scripts: set a `/goal` stating the outcome and the legitimate
stop conditions, then let the goal mechanism hold direction across the loop
(this is the sibling pipeline's proven pattern for the same two loops, and
matches the Fable guidance to put the full goal up front rather than steering
turn-by-turn). **G5 is not among them — it is a single pass, by design.** Word stop conditions as evidence,
never effort: "every in-scope finding resolved or classified unfixable with
a reason", not "best effort".

**Both loops also carry explicit bounds.** Evidence-worded
stop conditions define _done_ correctly but delegate all iteration control to
model judgement, which is how the sibling pipeline produced a 12-hour
non-converging loop. Bounds are not a quality ceiling — they mark the point
where continuing has stopped being the cheapest way to make progress and you
should look at it yourself.

The per-loop numbers and the reasoning behind each are stated once, in
`../../orchestrate-feature-dev/references/agent-prompts.md § Loop Termination
Contract` — G6 verify-fix maps to its "Step 12 — Verify-Fix" row and G7
build/Gosling to "Step 15 — Build Verification". Read the bounds from there rather than from a copy here; a
duplicated number is a number that drifts, and this pipeline is meant to stay
in lockstep with its sibling.

**Per-attempt scope budget**: an attempt may touch only the files named by the
findings it targets, plus their direct test files. Scope creep mid-loop is how
a bounded fix becomes unbounded, and it makes the oscillation signal
unreadable.

**Oscillation detection** — stop and escalate when any holds: the same finding
ID fails twice consecutively with the same error signature; the count of
_pre-existing_ findings fails to fall across two consecutive iterations
(track newly-arrived findings separately — G7's Gosling posts new findings
each iteration, so a flat total can hide real progress plus a stall); or an
attempt re-touches the same lines as the previous one without reducing the
count.

**On stopping, hand back state rather than discarding it**: what is resolved,
what remains with IDs, what was attempted for each, and which bound was hit.
Raising one bound and resuming is the usual next move, and it needs that
state. `eng-utils:merge-bot-prs` is the in-toolkit precedent worth copying —
it keeps an unbounded per-repo fix loop safe with explicit termination
conditions, an oscillation detector, CI as external verifier, and a scope
budget.

---

## G0 — Grounded run

**Outcome**: state file + run journal exist, inputs archived, branch and
worktree ready.

State file format, run-id derivation, artifact layout, resumability rules,
and the atomic write pattern are shared with the sibling skill — follow
`../../orchestrate-feature-dev/references/state-file.md` and
`../../orchestrate-feature-dev/SKILL.md § State Management` verbatim (same
paths, same schema; add fields additively). Two additions for this pipeline:

- Record `pipeline: fable` and every routing decision, gate verdict, and
  question-escalation answer in the state file's `decisions` array — a
  resumed run must be able to reconstruct WHY the route looks the way it
  does, not just where it stopped.
- On resume, reset `in_progress` plans to `pending`, honor persisted
  `cli_args` over re-supplied flags, and re-verify the most recent gate's
  evidence before continuing past it.

**Evidence**: state file + run journal exist at the canonical paths with
`cli_args` and `pipeline: fable` populated; branch and worktree confirmed;
inputs copied under the run's `input/` directory.

**Waivable**: nothing, but `--no-worktree` changes where, not whether.

## G1 — Shared understanding

**Outcome**: the problem is understood well enough that the contract and
plans will be built on facts: research evidence exists, operational and
design inputs exist where they matter, and the requirements document does not
contradict the findings.

**Default route**: `/research-problem` (sonnet, auto, review-phase addendum);
then, guided by the research doc's own recommendation headings,
`/operational-context` and/or design exploration in parallel. For design:
prefer parallel Sonnet architect workers producing competing approaches, with
you deciding (see `delegation.md § Model and effort policy`); `/design-approach`
remains available when you want its full machinery. Reconcile requirements
against findings yourself — you are qualified to detect factual conflicts
from the docs' key sections — or delegate the sibling's Reconciliation Agent
prompt (`../../orchestrate-feature-dev/references/agent-prompts.md
§ Reconciliation Agent`) when the documents are large. Protected sections (Objective, Success
Criteria, Scope priorities) are human intent: never auto-edit them; an
Objective contradiction is an escalation.

**Evidence**: research artifact at canonical path + review-phase artifact
check passed (`../../orchestrate-feature-dev/references/review-phase-enforcement.md`);
routing decisions recorded; reconciliation outcome recorded
(`conflict=/changes=`).

**Your judgment**: depth and breadth. A small, well-understood change needs
less than a novel system. Skipping research entirely requires the user's
explicit request (`--skip-research` or equivalent words) — cite them.

## G2 — Frozen validation contract (never waivable)

**Outcome**: a validation contract exists, derived from the requirements'
acceptance criteria, with `status: frozen`, reviewed by the multi-persona
review including the **Live Testing Enforcer**, BEFORE any implementation
begins. Freezing before implementation is what makes verification
falsifiable — a contract written after the code describes what was built,
not what was required.

**Default route**: `/validation-contract-generation --requirements <path>
--non-interactive` (sonnet, auto). The skill internally mandates the
Coverage Auditor + Live Testing Enforcer review loop and halts without
writing when Must-Address items persist — treat that halt as a gate failure
to escalate, not to work around.

**Evidence**: contract at canonical path with frontmatter `status: frozen`;
`live_testing: true` with `live_assertion_count ≥ 1` per endpoint/RPC under
test — or `live_testing: false` with a skip reason that survives the
enforcer's own standard (pure library, no runnable service; "complex setup"
and "external dependencies" are not valid reasons).

**Your judgment**: none on the gate itself. You may add assertions you
believe are missing (via the worker), never remove or weaken them.

## G3 — Reviewed plans covering the contract

**Outcome**: implementation plan(s) exist, each reviewed (review-phase
evidence), collectively covering the contract's assertions, with an execution
order that respects dependencies.

**Default route**: `/map-feature-to-plans <research-doc> --non-interactive`
when the feature may warrant splitting ("single plan" is a valid outcome);
mirror the resulting DAG into the state file. Then `/create-plan-tdd` per
plan — parallel across a wave — each with `--contract <path>` and the
review-phase addendum. Single-plan features may skip scoping; record the
decision.

**Evidence**: plan artifact(s) + review-phase artifact check per plan;
coverage check: every `VAL-*` assertion ID in the contract appears in some
plan (grep); uncovered assertions are a gate failure — re-plan or escalate,
don't proceed and hope.

**Your judgment**: decomposition, wave structure, plan sizing.

## G4 — Red-green TDD implementation (never waivable methodology)

**Outcome**: every plan implemented via red-green-refactor with verbatim
failing-test evidence per task, full test suite green at each plan boundary.

**Default route**: `/implement-plan-tdd <plan-path> --non-interactive
--skip-final-review` (sonnet, dontAsk), strictly sequential across plans
(`field-notes.md § Execution constraints`). The skill enforces per-task RED
evidence; your job is to not undermine it — no "quick fixes" outside the TDD
loop, including your own.

**Evidence**: implementer completion reports with failing-test evidence
noted; suite-green confirmation per plan; state file plan statuses updated
atomically.

**Your judgment**: ordering within dependency constraints, retry-vs-respawn
on worker failure, and (with recorded justification + true isolation)
parallel implementation — the bar is high; see
`field-notes.md § Execution constraints`.

## G5 — Simplified, reviewed once, findings triaged

**Outcome**: `/simplify` has run once over the cumulative diff; one pass of
`/jbb-feature-dev:code-review` has run after it; every finding the review reports
is either addressed or filed as a deferred bead; the contract is amended to
cover files the original requirements did not anticipate.

**One review pass. This gate is not a loop.** It stopped being one on
2026-08-21, deliberately and with the price known — the measured flip-rate and
unreachable-finding figures that motivated it are stated once, in
`../../orchestrate-feature-dev/SKILL.md § 9. Code Review`. Read them there; a
figure restated here is a figure that drifts. Real defects now reach G6 and the
user. G6 is never waivable precisely because it, and not this gate, is the net
that has to hold.

**Nothing here blocks the pipeline.** There is no severity gate, no adapter and
no clean-review condition to satisfy. G5 passes when every finding has been given
a destination — fixed or filed. It fails only if the review did not run, or ran
against nothing.

**Order is load-bearing**: simplify first, review second. Cleaning first means
the review's attention goes to correctness rather than to mess that was about to
be removed anyway. `/simplify` runs on the cumulative diff, not per plan, so it
can see duplication *between* plans — which is where most of it accumulates.

**Address by judgement, with one standing default**: fix what genuinely improves
the change, and **address the code-style findings even when they are Minor or
Enhancement**. They rank below every severity gate, which makes them the first
work cut whenever a stage runs long. Deciding not to fix one is legitimate -
file it. Leaving it unread is not.

**File everything left unfixed before moving on** — the sibling's
`agent-prompts.md § Filing What Ships Unfixed` carries the exact command and the
two traps inside it. Shipping with known findings is the decision; shipping with
forgotten ones is not, and with no second pass to re-report them, filing is the
only thing separating the two.

**Default route**: mirror the sibling's steps 8-10
(`../../orchestrate-feature-dev/SKILL.md`) — `/simplify` once on the cumulative
diff and **commit it** (non-fatal if it fails), then the single
`/jbb-feature-dev:code-review` pass, then a single fix worker, then
`/validation-contract-generation --amend --contract <path> --review-doc <path>`
(additive only; retry once, then proceed unamended).

**Review and fix are two different workers, and that is not stylistic.**
`/jbb-feature-dev:code-review` is explicitly read-only ("DO NOT make any code
changes"), and you conduct rather than edit — so neither you nor the reviewer can
close a finding. The sibling's step 9b prompt is the fix worker; read its
argument and counting contract there rather than improvising one.

The cleanup step is `/simplify`, a Claude Code built-in. It is not
`/polish-code`, which is a different skill doing a different job.

Two parts are not yours to vary:

- **Do not add a rule pass, quality pass or style pass after the review.**
  `/jbb-feature-dev:code-review` already spawns the security, repo-rules,
  repo-rules, holistic, per-language style and per-language test reviewers, and
  already keeps every severity for the style and test reviewers rather than
  filtering to Major and above. A follow-up pass re-reviews ground this call has
  already covered.
- **Do not reinstate the fix loop** by re-running the review to check your own
  fixes. One pass is the design, and a second draw is precisely the noisy signal
  that was measured and then abandoned.

**Before ending a turn in this gate, check your last paragraph.** If it is a plan
or a promise — "I'll file the remaining findings", "next I'll address the style
findings" — do that work now with tool calls instead. This gate's filing step is
the exposed one: leaving a finding unfixed is only legitimate because it was
filed, so a turn that ends by intending to file converts a deliberate trade into
an undocumented one.

**Evidence**: the review document; the count of findings addressed and the count
filed, which together must account for every finding reported; style findings
addressed and any skipped with reasons; `/simplify` outcome; amendment outcome.

**Your judgment**: you arbitrate every finding — a reviewer can be wrong, and you
may overrule one with recorded reasoning. You may not skip the review, or
substitute your own reading of the diff for it.

## G6 — Live verification (never waivable)

**Outcome**: every contract assertion — originals and amendments — has been
executed by an independent validator against the real implementation, live
assertions against a genuinely running service, with raw evidence captured;
failures are fixed via TDD and re-verified LIVE; anything unfixable is
classified with a defensible reason.

**Default route**:

1. **Validator worker** (sonnet, dontAsk; Read/Bash/Write only): prompt from
   `../../orchestrate-feature-dev/references/agent-prompts.md § Validator
Agent`, schema `../../orchestrate-feature-dev/scripts/validator-schema.json`,
   output `validation-state.json`. Cross-reference afterwards: any `VAL-*`
   assertion the validator omitted is appended as `failed`.
2. **Execution gates**: independently run build + test (detect the build
   system from file presence) and curl any contract health endpoint; append
   `GATE-BUILD` / `GATE-TEST` / `GATE-HEALTH`.
3. **Aggregate**: `../../orchestrate-feature-dev/scripts/aggregate_verify.py`
   → verify summary.
4. **Verify-fix loop** until all assertions pass or are defensibly
   unfixable: group failures by root cause; TDD fix workers; and for any
   assertion that failed a LIVE pass, a fixing worker's unit-test claim is
   NOT confirmation — run the Verify-Fix Recheck (same Setup/Stimulus/
   Assertion, live) and merge with `aggregate_verify.py merge`
   (`field-notes.md § Verification facts`).

**Evidence**: `validation-state.json` conforming to the schema; verify
summary with total/passed/failed/blocked; per-unfixable-assertion
classification (environment-blocked with root cause traced, or Nice-to-have
not implemented by design). "Blocked" requires root-cause proof —
`field-notes.md § Verification facts`.

**Your judgment**: fix strategy and loop budget (escalate when a failure
survives ~3 fix-recheck rounds — repeated failure is a systemic signal, and
grinding past it burns tokens without addressing the cause). The validator's
independence is not yours to waive: the implementer never validates its own
work, and you never mark an assertion passed from a fixing worker's claim.

## G7 — Shipped with evidence

**Outcome**: final report generated; work committed; PR open with
verification evidence embedded; CI green; every Gosling bot finding replied
to and resolved; workspace cleaned; user notified.

**Default route**: report generator (haiku, dontAsk; template + prompt in
the sibling's references) → `/commit --non-interactive` → `/submit-pr
--verification <summary> --requirements <path> [--scoping-doc <path>]
--non-interactive` → build/Gosling loop: check `gh pr checks`; classify
failures (format → fix+push; small test/build → TDD fix worker; large or
unclear, e.g. mid-run merge conflict → escalate with analysis, never resolve
solo). Gosling findings are claims to verify, not instructions: fix real
ones via TDD workers, reply with the commit; rebut false positives with
reasons; resolve every thread either way (GraphQL `resolveReviewThread`,
thread id from `reviewThreads`, not the REST comment id). Cleanup: `git
clean -fdx` scratch artifacts, remove the worktree (deliverables are already
committed and pushed); on escalation leave the worktree intact for triage.
Slack notification per `../../orchestrate-feature-dev/references/slack-routing.md`
— Slack errors never fail the run.

**Evidence**: `final-report.md` exists; PR URL + Jira key in the state file;
checks green; zero unreplied/unresolved Gosling threads.

---

## Escalation

Unrecoverable failure at any gate follows
`../../orchestrate-feature-dev/references/escalation.md` verbatim:
diagnostic doc, failure report, worktree left intact, state marked, Slack
alert, non-zero exit. Never auto-retry an escalation. Signals that mean
"stop, surface to a human": a skipped review phase, an Objective
contradiction, a review that examined nothing, a verify failure that survives
repeated fix-recheck rounds, a gate whose evidence you would have to
manufacture.

A Critical or Major finding you decide not to fix is **not** on that list. G5
files it and the run continues — that is the trade, and escalating instead
would quietly reinstate the blocking gate G5 no longer has.
