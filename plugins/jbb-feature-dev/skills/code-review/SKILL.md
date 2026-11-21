---
name: code-review
description: >
  Read-only code review of a branch, working tree or PR against its objective, by three fresh
  assessors (general, bug, contract) plus a concern verifier that probes every concrete concern.
  Covers correctness, claims and keys, scope, tests, reuse, performance, minimal code, readability,
  naming and comments. Leaves security and repo conventions to a dedicated review bot or reviewer. Use
  when the user asks to "review my code", "review this PR", "code review", or says "/code-review".
argument-hint: "[pr-number-or-branch] [--non-interactive]"
---

# Code review

Read-only on the reviewed repository, including for the caller's own work: never edit, commit, switch branches, or post to GitHub.
Return findings; the caller applies accepted ones within its own edit authorization. A session that wrote
or simplified the change may coordinate the review but must not assess or grade its own work.

## 1. Scope

- First argument: a bare PR number or branch name. Never a PR URL; this skill does not clone.
  Missing: ask, or with `--non-interactive` resolve from the current branch and record how.
- PR: `gh pr diff <N>` and `gh pr view <N> --json title,body,baseRefName,baseRefOid,headRefName,headRefOid,comments,reviews`,
  plus `gh api repos/{owner}/{repo}/pulls/<N>/comments` for inline comments. If on-disk files do not match
  the PR head, read source at the head through repository tools. Never check out, pull or stash.
- Local: use the supplied base commit, or record the merge base with the task's actual target branch.
  Never guess `master` or `main`. Diff from that commit through the working tree, including staged and
  unstaged changes. List relevant untracked files with `git ls-files --others --exclude-standard` and read them.
- Drop files matching `exclude_files` in `.code-review.yaml`, and say which.
- Nothing in scope: say so and stop. Never report a clean review of an empty diff.
- Over ~1,500 changed lines or 40 files: review hunks only, skip generated, vendored and lock files, and say so.

Record root, branch, base and head SHAs, file list and diff as the shared snapshot every assessor uses.

## 2. Objective

State in 1-3 lines what the change is meant to do, from the PR body, bead, issue tracker, plan file or this
conversation. Follow links once each with tools already connected; list the sources used. If no objective
exists, ask; with `--non-interactive`, write "objective unknown" and skip the alignment verdict.

## 3. Review

Dispatch three fresh `general-purpose` subagents concurrently in one message. Do not use named review agents.
Pass each the Agent tool's `effort`, chosen from the actual diff, not an intake label: `low` for a few locally
verifiable lines, `medium` for ordinary module work, `high` for production writes, weakened checks, or behaviour
that cannot be verified locally. Use the same effort for the concern verifier.
Give each the objective, acceptance criteria, scope exclusions, the shared snapshot, existing PR comments,
the section 4 output format, the severities below, and its role with the resolved paths of the files it must read.

Severities: **critical** production failure or data corruption; **high** likely failure under realistic input or
state; **medium** failure on an uncommon accepted input, or a name or comment that misleads; **low** anything else
worth reporting.

Each is read-only, dispatches nothing, confirms root and head first, reads full changed files plus callers
and siblings, and reports instructions actually read, evidence, coverage limits, and unresolved concerns
separately from findings.

- **General assessor:** Read every non-Correctness section of `checklist.md` in this skill's directory,
  including Do not report. Own objective/scope, tests, reuse/performance, minimal code, readability, naming,
  and comments/contracts. For each language in the diff, read `${CLAUDE_PLUGIN_ROOT}/skills/<lang>-code-style/SKILL.md`
  if it exists and report idioms only where it states a rule. Source inspection only. Search existing code
  and the new diff for reusable logic. Incidental correctness findings are allowed.
- **Bug assessor:** Read [bug-review](../bug-review/SKILL.md) and the Correctness and Do not report
  sections of `checklist.md`. Own correctness. Safe, isolated local probes are allowed; no shared builds.
  Run bug-review's probe for each medium or higher candidate when the repository has a runnable test harness.
  Return not applicable only when the diff changes neither executable behaviour nor a behavioural contract.
- **Contract assessor:** Read the Correctness section of `checklist.md`. Own only the two tables below; leave
  other bugs to the bug assessor. Fill every row before writing anything else, and probe each row with the
  repository's test harness when it has one. Return both tables even when they are empty:
  - **Claims:** one row per acceptance criterion and per "every", "only" or "never" statement in the PR body, commit
    messages, changed comments and changed docs (README, help text), and one row per code location or set member it
    covers. Mark each row holds or broken under the checklist's universal-claims item.
  - **Keys and shared state:** one row per map key, merge key, identity or flag the diff builds for stored, compared
    or shared state, with the result of the checklist's two-entry and per-item cases.
  A broken row is a finding. A row whose own analysis describes a wrong observable behaviour is broken, however
  small. "Harmless", "low impact", "acceptable" and "same as the old system" set the severity, not the verdict.
  For the checklist's unbounded-wait item, a timeout counts only if you find it in code or configuration; a library
  default you did not confirm is not a timeout.

Wait for all three. Then collect every unresolved concern that names a concrete input or state and dispatch
one more fresh `general-purpose` **concern verifier** with only those concerns, the snapshot and bug-review's
probe rules. It probes each one and returns confirmed (a finding, with output), refuted (with output), or
blocked (with the reason). Refute only when the stated mechanism does not happen; a mechanism that happens but
looks harmless or unreachable is confirmed at low severity. A concern never stays parked because an assessor did not run it.

Also give the verifier every medium or high finding that claims wrong runtime behaviour, to verify live: run
the changed code through a real entry point (a local service, CLI or the repository's integration harness) with
the finding's input, and show the wrong observable result. If nothing runs live, use a test through the public
entry point a real caller uses, with that caller's input; fake only what is outside the repository. A unit probe shows the mechanism, not that a caller
reaches it. A finding the run does not reach is confirmed at low severity, as above. One that neither can run
goes under Unresolved with the command that would settle it, not into Findings. Each finding states its evidence
(live or public entry point) and any unverified precondition on real traffic.

Wait for the verifier too; write section 4 only after every subagent has returned. A missing assessor blocks completion; do not substitute your own review. Re-read the head and diff; if they
changed, re-run affected assessors or report the review incomplete. Deduplicate by root cause, keeping every
assessor's evidence. Reject a finding only with evidence that disproves its premise; missing context is a
limit, not disproof. Drop findings an existing PR comment (including a review bot's) already raises.

## 4. Output

Write `~/.claude/thoughts/shared/reviews/review_<PR-or-branch>_<DATE>.md` and return it:

1. **Scope:** snapshot, sources, exclusions, effort passed and model, and which assessors ran.
2. **Objective:** aligned / partially / not aligned, one sentence why.
3. **Findings**, ordered: correctness, objective and scope, tests, reuse and performance, minimal code,
   readability, naming and comments. Each: `file:line`, severity, rule, consequence, quoted line, suggested fix.
4. **Unresolved:** blocked concerns and coverage limits, with what would settle each. List these before any
   clean verdict.
5. **Contract tables** from the contract assessor.
6. **Looks good:** only if worth saying.
7. Security and repo conventions belong to a dedicated review bot or reviewer. If none has reviewed, say this
   review does not cover them.

For a colleague's PR, tag each finding **must fix before merge** or **nice to have**, give Approve / Approve
with comments / Request changes with a one-line reason, and draft `file:line` comments without posting them.
`/crit-pr-review` can post them.
