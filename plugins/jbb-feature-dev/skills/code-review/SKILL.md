---
name: code-review
description: Single-pass personal code review of a branch, working tree or PR against its objective, covering correctness, scope, tests, reuse, performance, minimal code, readability, naming and comments. Fixes findings on Jonny's own work; on a colleague's PR it stays read-only, recommends approve or request changes, and drafts comments. Leaves security and repo conventions to a dedicated review bot or reviewer. Use when asked to review code, review a PR, or for /code-review.
---

# Code review

## 1. Mode

- An explicit read-only request overrides author-based mode selection. Never edit or commit in read-only mode.
- PR number given: compare `gh pr view <N> --json author --jq .author.login` with `gh api user --jq .login`.
  Different author is **colleague mode**; same author is **fix mode**. No PR number is fix mode.
- Colleague mode is read-only: never edit files, switch branches, commit, or post to GitHub.

## 2. Scope

- Colleague PR: `gh pr diff <N>` and `gh pr view <N> --json title,body,baseRefName,baseRefOid,headRefName,headRefOid,comments,reviews`, plus
  `gh api repos/{owner}/{repo}/pulls/<N>/comments` for inline comments. Do not check out.
- Fix mode on Jonny's PR: if the current branch is not the PR's `headRefName`, or the tree has unrelated
  uncommitted changes, `git worktree add <repo>/.worktrees/review-<N> <headRefName>` and work there.
  Keep worktrees outside `/tmp` and `/private/tmp`; cleanup can destroy uncommitted work. Never touch the current checkout.
- Fix mode: use the supplied base commit. Otherwise resolve the task's actual target branch and record its
  merge base with HEAD. Ask when the target is unclear; do not guess a default branch or replace a supplied base.
  Inspect the diff from that recorded commit through the working tree, including staged and unstaged changes.
  List relevant untracked files with `git ls-files --others --exclude-standard` and read them separately.
  Limit fixes to the supplied task scope; record unrelated changes without editing them.
- Nothing changed: say so and stop. Never report a clean review of an empty diff.
- Over ~1,500 changed lines or 40 files: review hunks only, skip generated, vendored and lock files, and say so.

## 3. Objective

State in 1-3 lines what the change is meant to do, from the PR body, bead, Jira, plan file or this conversation.
Colleague mode: follow links in the PR body (issue tracker, chat threads, docs) once each with tools already
connected; skip any that need setup, and list the sources used. If no objective exists, ask; if nobody can
answer, write "objective unknown" and skip the alignment verdict.

## 4. Review

Dispatch two fresh `general-purpose` agents with the Agent tool, in one message so they run concurrently, against the same snapshot, even if this session made no edits.
Do not use a named or specialist agent type. Invoke them directly, without a wrapper or third reviewer.
Both assessors are read-only, including in parent fix mode: no source edits, commits, posting, or child delegation.

Give both the mode, objective, acceptance criteria, repository root, worktree, branch, fixed base and head,
full tracked working-tree diff, relevant untracked contents, scope exclusions, and the full section 5 output format.
For a colleague PR, supply its base/head, diff, file contents, and existing comments instead of the local checkout's state.
Include resolved skill/checklist paths, the shared read-only, file-reading and reporting rules, and the role-specific instructions below.
Do not pass dispatch/wait/apply instructions or section 7 to the children; this prevents recursive dispatch.
Each assessor confirms its root and branch and reports the assessed state, instructions actually read, evidence, and coverage limits.
Read full changed files unless section 2's large-diff limit applies; retain that limit and report reduced coverage.

- **General assessor:** Read every non-Correctness section of `checklist.md` in this skill's directory, including Do not report.
  Own objective/scope, tests, reuse/performance, minimal code, readability, naming, and comments/contracts.
  For java, python and typescript in the diff, read `<lang>.md` here and report idioms only where it states a rule.
  Other languages: checklist only, and say so. Use source inspection only, not test or probe execution.
  Treat readability as an implementation concern, not a final cleanup pass. Expose decisions through meaningful
  names and focused helpers; do not use line counts as a substitute for judging clarity. Search existing code
  and the new diff for reusable logic. Incidental correctness findings are allowed, but do not replace the bug assessment.
- **Bug assessor:** Read [bug-review](../bug-review/SKILL.md) and the Correctness and Do not report sections of `checklist.md`.
  Own correctness analysis. Safe, isolated local probes are allowed; do not run shared baseline checks.
  Return not applicable only when the diff changes neither executable behavior nor a behavioral contract.
  State the evidence and reason; not applicable is not a clean bug review.

Wait for both results before validating findings or applying fixes. A missing independent pass blocks completion; do not substitute inline review.
Compare the current head, tracked diff, and relevant untracked contents with the shared snapshot before using results.
If the input changes, refresh affected independent assessments against that state or report the review incomplete.
Deduplicate by root cause, retaining evidence from both assessors. Validate each finding's evidence, applicability, and task scope.
Reject only with evidence that disproves its premise or applicability. Return disputed conclusions to the responsible assessor.
Keep required unresolved uncertainty blocked, outside admitted findings, with the evidence needed, owner, and next action.
In fix mode, the parent runs shared baseline checks under section 7 after both assessors return, not concurrently with their inspection.

Colleague mode: drop findings an existing comment (including a review bot's) already raises.
Note in one line any existing comment that looks wrong or unresolved and matters for approval.

## 5. Output

1. **Objective:** aligned / partially / not aligned, one sentence why.
2. **Findings**, ordered: correctness, objective and scope, tests, reuse and performance, minimal code,
   readability, naming and comments. Each: `file:line`, rule, consequence, quoted line, suggested fix.
   Report what matters; do not pad.
3. **Looks good:** only if worth saying.
4. Security and repo conventions belong to a dedicated review bot or reviewer.
   If none has reviewed, say that this review does not cover those checks. Use only a bot invocation verified
   in current repo instructions or PR evidence; otherwise ask for it rather than guessing.

## 6. Colleague mode: verdict and comments

- Tag each finding **must fix before merge** (correctness, objective misalignment, low-value tests,
  tests that pass while broken, or a severe consequence) or **nice to have**.
- Verdict: Approve / Approve with comments / Request changes, with a one-line reason.
- Ask which findings to send back. For the chosen ones, draft ready-to-paste `file:line` comments and rewrite
  them with the `sound-like-me` skill's GitHub-comment voice. Post nothing.

## 7. Fix mode: apply

1. After both assessors return, find test and lint commands: the repo's AGENTS.md or CLAUDE.md first,
   then package.json scripts, pom, sbt, pyproject or Makefile. Run them for a baseline.
2. Apply every validated, safe, in-scope finding except those needing a design decision. Low priority or minor impact is not an exemption.
   List design decisions and any remaining required work that cannot be applied safely as **needs you**, with an owner and next action.
   Write clear code first. Add comments only when clearer code cannot express necessary context or contracts.
3. Re-run. A previously passing test now failing: one repair attempt, else revert that fix and list it under
   **needs you**. Baseline failures are reported, not fixed.
4. Return the verified edits. Commit only when the user or parent explicitly authorizes a commit.
   If authorized and checks pass, create one new commit with the required co-author trailer. Never amend or push.
   If no test or lint command exists, say verification was unavailable and do not commit.
5. Report: what was fixed, needs you, test results, any authorized commit SHA, and the worktree path if used.
   Do not repeat the findings list.
