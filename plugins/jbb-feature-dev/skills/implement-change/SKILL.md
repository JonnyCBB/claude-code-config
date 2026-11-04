---
name: implement-change
description: >
  Implement a specified change in the current session, then independently simplify,
  review, and verify it. Submit only with permission and follow latest-head CI and
  clean review to completion. Use when asked to implement a feature, fix, or approved
  task, or to run /implement-change. Not for research-only work, read-only review,
  deployment, or merging.
argument-hint: "<task description or objective/criteria file>"
---

# Implement change

## Establish scope and authority

1. Read the task, supplied objective or acceptance criteria, and repository instructions.
   Inspect affected code, callers, existing helpers, types, tests, and local verification setup.
   State intended changes and exclusions. Ask only for decisions that block implementation or verification.
   A research report, formal plan, or validation contract is not required.
2. Confirm repository root, worktree, branch, intended target branch, fixed base commit, and current head.
   Work in the current session and checkout unless the user requests isolation. Preserve unrelated work.
   If creating a branch, verify its intended base; unset an inherited default-branch upstream before any push.
   Keep any requested worktree outside temporary directories, where cleanup can destroy uncommitted work.
3. Establish separate authority for edits, commits, pushes, and PR creation or updates.
   A local patch request does not authorize submission. Ask before an unauthorized action.
   Do not send Slack messages or change unrelated external records without authorization.
   Never merge or enable automatic merging, including through another skill.
4. Keep the objective, root, branch, target branch, fixed base, head, evidence paths, pass results, and next action
   in the repository's task record. For each pass, record the actual assessor, input state, instructions actually read,
   and evidence, not only the intended dispatch. Use Beads (`bd`) when configured; otherwise use a durable task note outside pushed source.
   On resume, inspect actual artifacts and revisions before reusing completed work. File existence,
   newest-file ordering, and an author's summary do not prove relevance or completion.
   Retain the checkout, unrelated changes, and evidence on success or failure. Deletion needs explicit approval
   for the exact paths and verified ownership; never force-remove a worktree or clean the caller's checkout.

## Implement minimally

- Use red-green-refactor for runtime behavior: run a small failing test, make the least change that passes,
  then refactor. Keep verbatim failing and passing output. Do not test documentation wording.
- Reuse existing operations. Implement only the objective; record unrelated findings separately.
  With Beads, label agent-proposed follow-ups `agent-proposed` and keep them `deferred` until triage.
  Make decisions clear through names and structure, not dense expressions or needless helpers.
- Default to no comments. Keep one only for a necessary fact that clearer code cannot express.
- Run relevant checks and inspect the actual diff. Attribute failures before fixing them.
  Establish an independent cause before declaring a failure unrelated; do not weaken checks to get green.

## Three independent quality passes

Run these passes sequentially on the cumulative change. Read each skill before invoking it.
Use its existing assessors, not an extra wrapper solely to invoke the skill.
If it defines no independent assessor, use a fresh agent. Never reuse an earlier pass's assessor.
The implementer may coordinate and apply findings, but never assess or grade its own change.
If a skill falls back to implementer self-assessment, obtain a fresh assessor or report the pass blocked.

| Order | Skill | Assessment and result |
| --- | --- | --- |
| 1 | Claude's built-in `/simplify` | Invoke directly with its internal review agents; inspect behavior-preserving edits and check output. Do not substitute `/polish-code` or a plugin package. |
| 2 | [code-review](../code-review/SKILL.md) | Invoke `/jbb-feature-dev:code-review` directly; it dispatches two fresh read-only assessors (general and bug) against one snapshot. Review the simplified diff and apply confirmed findings. |
| 3 | [verify-implementation](../verify-implementation/SKILL.md) | Use a fresh verification agent, not the implementer, fixer, or an earlier assessor. Produce objective-linked local scenarios and observed evidence. |

Give each pass and its internal agents the objective, acceptance criteria, repository/worktree path,
expected branch, target branch, fixed base, current head, skill path, and actual cumulative diff from that base.
Include staged, unstaged, and relevant untracked files with their contents; a committed range alone is insufficient.
Each assessor confirms its own root and branch and reports the reviewed revision/file set,
commands, output excerpts, changed files, and limits. Read its actual artifacts and inspect its edits before continuing.
Always supply this same scope to built-in `/simplify`; do not rely on its default diff selection or override its instructions.
An empty scope or missing independent pass is blocked, not clean. If built-in `/simplify` cannot run, report that blocker.

After simplification, run code-review on the simplified diff. Do not replace its two assessors with one reviewer.
For a local code review, supply the branch name, pinned base, and explicit output path in the brief;
use `--non-interactive` only when no user can answer scope questions. Never switch branches or stash work to review it.

Read every exact finding against current code. Apply every valid, safe, in-scope recommendation, including LOW,
documentation, Minor, and Enhancement findings, or retain it as a required blocker. Priority is not permission to skip.
Reject only with evidence that the premise is invalid or the recommendation does not apply to this change.
Keep unsafe fixes, scope expansion, and design or objective conflicts blocked for a decision; do not change criteria,
weaken tests or contracts, or apply a harmful fix to satisfy a reviewer. Record each candidate's outcome and reason
in the existing task/review record, including rejected, skipped, and blocked candidates and unresolved review concerns.
File unresolved work durably; filing is not resolution or readiness. Extra fixes cannot offset unaddressed findings.

Use the objective and acceptance criteria as the verification contract when no formal plan exists.
The verifier checks every recorded candidate outcome against the final diff and evidence, including rejections,
skips, blockers, and structural recommendations, not only admitted bugs or runtime fixes.
For a service, exercise the changed endpoint locally; for UI changes, use a browser against the local app.
For a library, run a focused executable example or behavioral test with actual inputs and outputs.
For documentation, inspect the instructions and relevant existing checks; do not start an unrelated service.
Keep dependencies local too. Never substitute production requests, copied secrets, or weakened authentication.
Record precise setup, inputs, action, expected output, observed output, and explicit unverified criteria.
Confirm a claimed environmental blocker from the actual error and configuration; ask for missing user action.
A fix for a failed live scenario needs the same setup and action rechecked locally, not only a passing unit test.
After later fixes, independently refresh affected review conclusions and verification scenarios, not the entire pass chain.
After the last edit, rerun relevant checks, including existing formatter/lint checks, and refresh affected evidence.

## Submit with evidence, only when authorized

Use [submit-pr](../submit-pr/SKILL.md) with the verified objective, actual review and verification artifacts,
explicit target branch, `--verification <path>`, and `--monitor`. Pass `--requirements <path>` only when supplied.
Use [commit](../commit/SKILL.md) only within commit authority; submission must not silently expand permissions.
Honor submit-pr's clear-prose rules and optional `jiffy-toolkit:sound-like-me --register=github-pr-body` support.
Without that skill or persona, follow its [PR prose fallback](../submit-pr/references/pr-prose-rules.md).
The PR body must stand alone: objective, precise scenario inputs, expected and actual outputs,
reproduction steps, verbatim evidence, and remaining limits, not author-only report pointers or test counts alone.
Run available branch CI before submission; local checks never replace remote CI.

Follow [submit-pr's build and review monitoring policy](../submit-pr/references/build-monitoring.md)
as the sole convergence procedure, including watcher startup, all-priority findings, focused fixes, evidence refresh,
and stop rules. Do not start a competing monitor. Completion requires green CI and an explicit clean
automated-review result for the unchanged latest remote head, with no outstanding findings.
PR creation, silence, stale approvals, resolved threads, or a timeout never establish completion.
A focused review correction does not restart the three passes unless it adds materially new scope.

## Handoff

Report the verified local patch or PR URL, verified head, check and review evidence, and verification limits.
If submission is not authorized, return the local patch and state that remote CI and PR review remain unverified.
If blocked, surface the exact failure immediately in this conversation and the task record, with the next action.
Preserve resumable progress; do not claim an unattended watcher exists unless its startup is confirmed.
