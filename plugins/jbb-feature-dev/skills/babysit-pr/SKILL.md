---
name: babysit-pr
description: >
  Watches a pull request through to green: polls CI, reads the build log on failure, fixes the
  small mechanical things (formatting, a missing import, an assertion expecting the old value,
  a bot review comment), and escalates anything bigger with a diagnosis. Fixes by default;
  pass --no-fix for a read-only diagnosis. Never merges and never posts to Slack or Jira.
  Use when the user asks to "babysit a PR", "watch this PR", "watch CI", "get this PR green",
  "poll until the checks pass", "fix the lint failure on my PR", or says "/babysit-pr"; also
  when a pipeline needs a PR driven to green unattended. Prefer it over /submit-pr --monitor
  when the failure might be anything other than lint, because that path notifies and stops.
argument-hint: "[pr-number] [--repo OWNER/REPO] [--no-fix]"
---

# Babysit PR

Poll CI, get the build green, fix small things yourself, escalate the rest.

**A "wakeup" is one cycle.** Under an external loop driver such as `/loop`, if you have one, the
driver supplies them and you do one per invocation. Invoked once by hand, do the cycles
in-process, waiting four or five minutes between them, and say how many you ran.

**FIXING IS THE DEFAULT** — lint, build and test fixes alike, one tier, committed and pushed
without being asked. **`--no-fix` turns it off**, leaving you to diagnose and report while changing
nothing on the branch. `--fix` is still accepted and now means nothing, so an older invocation that
passes it keeps working. The push gate under "Pushing" is what actually governs a push, and
`--no-fix` is one conjunct of it. Neither flag gates the two writes that
leave the code untouched: replying to a review comment, and retriggering a build once after an
infrastructure failure. Never merge or enable auto-merge, and never post to Slack or transition
Jira (`/jbb-feature-dev:submit-pr` owns those). **Never invoke a review tool that blocks until a
human clicks through a browser** — `/jbb-feature-dev:crit-pr-review`, and `/crit` if the separate
`crit` plugin is installed. An unattended loop reaching one hangs until morning.

You know how to drive `gh` and `git`. What follows is only what you would get wrong by
guessing.

**One rule governs all of it, and it is the one this skill has broken most often.** Every check
here answers a question by reading something, and *every reading has a failure that looks like
an answer*. So whenever you conclude that something is absent, empty, clean, zero, done or
verified, say how you know the instrument worked — the exit status, a non-empty variable, a
value you can see. Every signal is therefore in one of three states, and this file uses these
three words in exactly this sense:

- **CLEAN** — you read the signal and found it satisfied.
- **ABSENT** — the instrument worked and reported nothing there. You may stop on an absent
  signal, but name it absent: "no CI in this repo" is not "the checks passed".
- **UNMEASURED** — you could not read the instrument at all. Never report this as absence.
  Escalate as ambiguous, saying which reading failed. Treating an unreadable instrument as a
  clean one is how this skill has reported success it never measured.

Each failure mode below is an instance of that rule, and each says how its own instrument
lies — loudly, by a non-zero exit, or silently, by an empty value at exit 0.

## Reading the state

Fetch these fields. Note `reviews` **and** `comments` — omitting the second is most of this
skill's history. `updatedAt` feeds the idle timeout under "Stopping and reporting", which needs
a second timestamp beside it; see that section for why one is not enough.

```
state isDraft mergeable mergeStateStatus headRefOid headRefName
reviewDecision statusCheckRollup reviews comments updatedAt isCrossRepository
```

- **Review feedback lives in THREE places; the field list reaches two.** `reviews` holds formal
  submissions only, so a PR whose only feedback is an issue comment — or an AI review bot post, which
  arrives via `gh pr comment` — reads `reviews: []`, `reviewDecision: ""`, invisible until
  `comments` is requested (measured on a live PR).
  **Line-anchored comments are in neither field**: fetch
  `gh api repos/$REPO/pulls/$PR/comments`. Measured on cli/cli PR 14390, `comments` returned `0`
  and a review had an empty body while that endpoint held the real line-anchored comment, so
  **an empty review body means the text is elsewhere, not absent** — and the push gate's "no
  active review" is unevaluable without it, since the anchors a new commit moves live only
  there.
- **An empty `statusCheckRollup` does not mean green** — see "Does this repo run CI at all".
- **The rollup mixes two node shapes with disjoint keys.** A `CheckRun` has `conclusion` and no
  `state`; a `StatusContext` has `state` and no `conclusion`. Both arrive at once — measured,
  an external CI's StatusContext beside `tests` as a CheckRun. Read both keys or you read half the
  checks as "no failure found".
- **`reviewDecision` is the empty string on any repo not requiring a reviewer** — measured on
  three open mergeable PRs. That is clean, not unrecognised. Only `REVIEW_REQUIRED` and
  `CHANGES_REQUESTED` block.
- **Green but blocked is a third state, not done.** `isDraft`, `REVIEW_REQUIRED`, or
  `mergeStateStatus` `BLOCKED`/`QUEUED` mean a person must act: stop and name the blocker.
  `DIRTY` is a merge conflict — the most common thing here a human has to resolve — so stop and
  say so. `UNKNOWN` usually means the PR is closed or merged (measured beside `state: MERGED`),
  where the merged stop wins; on an open PR it means not yet computed, so cycle. **Any other
  value of either field escalates**, `STALE` and `UNSTABLE` included.
- **Being behind base is invisible to `mergeStateStatus`** — it says `CLEAN` while the branch is
  behind, and green CI on a stale base can be red once updated. Use `behind_by` from
  `gh api repos/$REPO/compare/$BASE...$BRANCH`, qualifying a cross-fork head as
  `<owner>:$BRANCH` — `isCrossRepository` in the field list is how you know, and guessing wrong
  404s. Never measure it from local `HEAD` unless you have confirmed you are on the PR's branch:
  measured, `HEAD..origin/$BASE` gave `0` where the truth was `2`.

**`$REPO` is bare `owner/repo` and the host goes in `GH_HOST`.** `gh pr view --repo` accepts a
host-prefixed slug; `gh api repos/github.example.com/owner/repo/...` returns **404**,
indistinguishable from a repo that does not exist. Default the host to `github.com`, and
set `GH_HOST` to the Enterprise host for a GitHub Enterprise PR — forcing the wrong one 404s the same way.

**Arguments do not reach a shell block you run** — `$1` is always unset, measured. Substitute
the PR number literally. `PR=${1:-$(gh pr view --json number -q .number)}` silently targets the
working directory's branch instead, and then fails with the same "no pull requests found"
string that means *stop*, so a wrong-PR run can look like a clean stop.

## Does this repo run CI at all

The one probe worth spelling out:

```bash
export GH_HOST=${GH_HOST:-github.com}   # nothing persists between tool calls
PR=123   # substitute the real number - see below, an argument does not reach this block
ERR=$(mktemp)   # not a fixed path - two babysit runs would clobber each other
verdict() {     # a failure to resolve is usually permanent, but an outage is not - read $ERR
  if grep -qEi 'error connecting|connection refused|timed out|could not resolve host' "$ERR"
  then echo "TRANSIENT, so ambiguous - cycle, do not stop:"
  else echo "DEFINITE - stop, this does not fix itself:"; fi
}
REPO=${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>>"$ERR")}   # or pass it in
echo "targeting REPO=[$REPO] - CONFIRM this is the repo you were asked about"
BASE=$(gh pr view "$PR" --repo "$REPO" --json baseRefName -q .baseRefName 2>>"$ERR") || BASE=
if [ -z "$REPO" ] || [ -z "$BASE" ]; then
  echo "cannot resolve repo or base - $(verdict)"
  cat "$ERR"; [ -z "$REPO" ] && git remote -v   # only if the REPO lookup is what failed
  exit 1
fi
HEAD=$(gh pr view "$PR" --repo "$REPO" --json headRefOid -q .headRefOid 2>>"$ERR") || HEAD=
[ -n "$HEAD" ] || { echo "cannot resolve head SHA - $(verdict)"; cat "$ERR"; exit 1; }
for REF in "$HEAD" "$BASE"; do                 # BOTH refs, BOTH endpoints - see below
  cr=$(gh api "repos/$REPO/commits/$REF/check-runs" --jq '.total_count' 2>>"$ERR") || cr=
  st=$(gh api "repos/$REPO/commits/$REF/status"     --jq '.total_count' 2>>"$ERR") || st=
  printf 'ref=%s check-runs=[%s] statuses=[%s]\n' "$REF" "$cr" "$st"
done
echo '--- stderr ---'; cat "$ERR"    # in THIS call - see the note on the export above
```

Without the guard, no remote means `$REPO` and `$BASE` come back empty, the probe queries
`repos///commits//check-runs`, and the `404` it captures is a fact about a malformed URL rather
than about CI — measured. The two resolving calls print `no git remotes found` on *their own*
stderr, so capturing only the `gh api` calls shows the symptom and hides the cause. **Failing to
resolve a repo is usually definite and permanent; an empty count from a repo you did reach is
ambiguous and may be transient** — opposite handling, so separate them before routing. The one
exception is why the block calls `verdict` instead of hard-coding the word: a network outage also
lands on the resolve path, and measured, a hard-coded "DEFINITE" there stops a babysit run
permanently on a blip. Route on the stderr, not on which branch you took to reach it.

**All four zero** → decide by the PR's age, which `updatedAt` gives you on the very first
wakeup: touched minutes ago, cycle once more; `updatedAt` older than the idle timeout, the
zeroes are real — report CI **ABSENT** and stop rather than polling. **That is an age
comparison, not the idle-timeout stop condition** under "Stopping and reporting": the stop
condition needs a prior reading and cannot fire on a first wakeup, so requiring it here would
make "no CI here" unreachable and poll a repo that will never report. **Any non-zero** → this
repo runs checks, so yours are most likely still attaching: cycle. Then four ways this lies:

- **The base ref alone is the wrong instrument.** Checks that attach only to a pull request's
  head — Prow, or any workflow triggered on `pull_request` — never touch base. Measured on
  kubernetes/kubernetes PR 141969: head carried `statuses=2` with the rollup **pending**, while
  base `master` read `check-runs=0 statuses=0`. A base-only probe prints two zeroes and stops,
  abandoning a pull request with a live build. Probe `headRefOid` too.
- **The two endpoints are not two looks at one thing.** Measured the same hour:
  kubernetes/kubernetes served `0` check-runs and `2` statuses on that head, while cli/cli
  served `416` check-runs and `0` statuses on its base. Different vendors post to different
  places, so a zero from one says nothing about the other — and `/status` alone returned
  `pending` with zero statuses on a no-CI repo *and* a CI-backed one alike.
- **A zero can also be transient**, since checks attach asynchronously after a commit: observed
  once as `0` beside `2`, reading `5` minutes later. **Four zeroes therefore do not separate "no
  CI" from "nothing has attached yet"** — both look identical. Discriminate on `updatedAt`,
  which you already fetched: minutes old, cycle once more; well past the idle timeout, the
  zeroes are real. **Never substitute a commit's `committer.date`** — that is a property of the
  commit object, so a rebase, amend or cherry-pick reports weeks old on a head pushed seconds
  ago (measured), abandoning exactly the pull request this bullet protects.
- **A failed lookup is neither a zero nor a count.** `gh api` writes its error body
  (`{"message":"Not Found",…}`) to stdout on a `404`/`422` while exiting non-zero: measured both
  ways, a variant missing the `|| cr=` fallback read that body as a non-zero count and polled
  forever. With the fallback the variable blanks instead — and `check-runs= statuses=` then
  reads exactly like the two zeroes that mean stop, which is what the brackets are for. Read the
  stderr the block printed and treat the result as UNMEASURED.

## Classifying a failure

**Never classify from the check name** — many CI systems report one aggregate check covering
compilation, tests and lint at once.
`references/ci-logs.md` is how to get the log; read it on any CI failure.

**Classification keys on evidence, not on the log file.** No log and nothing else → UNMEASURED,
so the reader knows it is uncategorised rather than mysterious. But a local
reproduction of the failing check is *better* evidence than a log and is grounds to fix —
common where there is no CI service at all. Check its provenance as you would a log's: measured,
a stale `__pycache__` made a failure cite a file in another tree, which reads as "not this PR's
failure". Clear caches and re-run before trusting a path.

## Fixing, or escalating

Fix it yourself **only if all three hold**; if one fails, escalate saying which.

- **Attribution** — the failing check passes on base. Fetch base before checking it out, or you
  test a stale one: measured, `PASS` from local `master` where base said `FAIL`, which inverts
  this judgement. Return to where you started; ending detached empties
  `git log origin/$BASE..HEAD`, which is your only memory across wakeups.
- **Local verification** — you ran the check and it passes. "It compiles" is not enough for a
  test fix. Quote the command and its output.
- **Non-weakening** — the fix does not reduce what the tests assert.

**Seven ways to weaken a suite:** delete an assertion · widen one (`assertEqual(x, 42)` →
`assertIsNotNone(x)`) · wrap a call so the failure is swallowed · add `skip`/`xfail`/`@Ignore` ·
mock the failing dependency · **narrow the input or fixture so the failing path is no longer
exercised** · **move an expected value to match the new behaviour**.

The last two leave every assertion byte-identical and appear in no test diff, so a checklist
misses them. And the seventh is *also a legitimate fix*, so no checklist can decide it.
**Decide from evidence the PR did not touch:** the docstring above the changed function, the
commit message's own claim, an unmodified fixture. Measured case: the docstring still said
"add shipping once for the whole order" and the commit claimed "pure refactor", so the source
was wrong and the expected value was right. When that evidence is absent or contradictory,
escalate rather than pick.

**Commit your fix, then diff the whole PR against base** — an earlier commit's weakening still
ships in this PR. Check `git status --porcelain -uno` is empty **and that it exited 0**
first — outside a repository it exits 128 with empty output, so emptiness alone reads a git
failure as a clean tree. Commit first because a three-dot range compares committed history:
measured, an uncommitted weakening was invisible and the check returned its strongest result
while the edit sat unstaged. **`-uno` is required, not tidiness** — running the suite creates an
untracked `__pycache__`, so a bare `--porcelain` fails the gate on output your own verification
step produced. Untracked files cannot hide a weakening from a three-dot diff anyway; the gate
wants uncommitted *tracked* changes. Cover test files, fixtures, *and* added
files — a new `conftest.py` with `collect_ignore` silences a test with no test diff at all.

**Then get independent eyes on it, always.** `/jbb-feature-dev:code-review $PR
--non-interactive` — the flag is not optional, since that skill prompts for a scope it cannot
resolve. If it cannot resolve a target,
spawn a fresh reviewer and say you substituted; do not skip the pass. CRITICAL or HIGH **saying
your fix is defective** → revert and escalate. A CRITICAL or HIGH that is a *consequence of the
fix being right* — usually that the PR is now a no-op — is not grounds to revert: that would
restore the defect just to silence a severity. Escalate the PR instead.

## Pushing

`--no-fix` NOT given · PR open · no review still being written · non-weakening confirmed · head
SHA unmoved · under five pushes · not a second fix for the same failure.

**"Still being written" means pending, not answered.** A review in progress has comments anchored
to lines your commit would move, so pushing scrambles it. A *submitted* `CHANGES_REQUESTED` is
the opposite case: fixing it is the whole point, and it does not block the push. **A conjunct you
could not measure blocks the push.** In the report UNMEASURED is a state you record and stop on;
here it is a denial, because pushing acts on the world. Count pushes and prior fixes from
your own commits on the branch — **`git log origin/$BASE..HEAD`, with `$BASE`
checked non-empty AND the command checked for exit 0.** `$BASE` holds an API ref name like
`master`, which is a *different commit* locally: measured, local `master` was 22 commits behind
`origin/master`, so the two ranges disagreed by exactly that.

  Both failures are real, but not the ones you would guess. An empty `$BASE` makes this
  `origin/..HEAD`, which exits **128** — loud, measured. The silent one is a **detached HEAD at
  base**: `origin/$BASE..HEAD` then exits **0** with empty output (measured), reading as "no
  prior pushes, no prior fixes" and passing two conjuncts on a measurement that never happened.
  That is why returning to the branch you started on, above, is a gate and not housekeeping.

Push with `--force-with-lease` only, never `--force`, and always an explicit refspec:
`git push --force-with-lease origin "HEAD:refs/heads/$BRANCH"`.

**Take `$BRANCH` from `gh`, never by pasting the name.** `feature/foo$(id)` is a branch name git
accepts, and in a double-quoted assignment the substitution runs: measured, via `$(gh pr view
…)` the name stayed literal, while pasted the `$(id)` ran and spliced its entire output into the
branch name. One commit per finding, naming the failure.

## Review comments

Three buckets, all reported: **needs action** (verified defect or explicit request — fix only
if the three conditions under "Fixing, or escalating" hold and the change is mechanical, else
escalate), **discuss**, **skipped** with its verification. On
anything you think is wrong, say why and **do not resolve the thread** — that is the
review-shaped version of weakening a test. Human comments and design opinions are never
auto-applied.

**Verify a bot comment against the code first**; a review bot's false-positive rate makes that
mandatory, and it may post independently of CI, so the first green cycle with no comments is early
rather than clean — give it one more. **Post replies with
`gh pr comment "$PR" --body-file reply.md`**, never inline or in a heredoc: comment text is
written by other people, and backticks and `$(…)` in it execute.

## Stopping and reporting

Stop when CI, review and mergeability are all clean **at the same wakeup** — reaching them one
at a time is not the same thing, and green CI with `CHANGES_REQUESTED` is not done. **Take one
more wakeup after CI stops being the blocker** — green *or* absent, since on a no-CI repo it
never goes green and a guard keyed on that waits for an event that cannot happen. The review-bot
caveat above is why; a pull request already idle past the timeout has discharged that wait.
Also stop
on: merged or closed · two attempts at the same failure, counting one you verified locally but
the push gate blocked · someone
else pushed · the push cap above · the idle timeout below ·
the failure is not this PR's · no log **and** no local reproduction. Gather the review buckets
even on a stop; stopping ends polling, not reporting.

**The idle timeout needs the newest timestamp available, and a prior reading.** Count 45 minutes
from the newest of `updatedAt` and any `startedAt`/`completedAt` in the rollup — check
transitions do not bump `updatedAt` (measured: 10 of 24 open PRs had a newer check timestamp,
one by 99 minutes). The first wakeup has no prior reading, so the timeout **cannot fire there**:
a stale `updatedAt` on a PR with a queued build would otherwise stop the run before it polled.
This restriction is on *this* stop condition only — the four-zeroes verdict above compares
`updatedAt` against the same 45 minutes as a plain age check, and that works on any wakeup.

**Give every signal one of the three states defined at the top** — CLEAN, ABSENT or UNMEASURED —
and never let one stand in for another. The non-weakening check has its own wording: "clean, N
test files changed" is evidence, "clean, no test changes — diff empty" is the strongest result,
and if you could not get a diff say **"not run"**, never "clean".

**Say the report out loud** — this skill posts nowhere, so it reaches a person only if whatever
invoked it surfaces the final message. End with: the stop reason · each signal's state and any
blockers · what you fixed with the command and output that verified it · the non-weakening
result · the three buckets · and what you are escalating, with which condition failed and the
log excerpt a human starts from. An escalation without a diagnosis is a notification, and "CI
is red" is something the author could already see.
