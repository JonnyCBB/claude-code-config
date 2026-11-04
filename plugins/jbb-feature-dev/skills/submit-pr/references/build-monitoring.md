# Build and Review Monitoring

Use this reference when `--monitor` requests post-submission monitoring.
This workflow never merges a PR or enables automatic merging, including in non-interactive mode.

## 1. Canonical Review Convergence Policy

This reference owns the completion policy for `/submit-pr --monitor` and orchestrator workers that link here.
CI means continuous integration, the automated checks attached to the PR.
Convergence means that CI and review meet every completion condition for the same latest head commit.
The automated reviewer is whatever review bot or check the repository uses; it may appear under more than one name.
Discover the actual reviewer account/check and completion signal from the PR or repository instructions.
Do not guess a bot login, trigger command, or universal clean-result phrase.

1. Record the remote PR head commit after submission or each authorized push.
   Read all pages of review comments, threads, review summaries, and CI results for this PR.
   Include human findings, file-level findings, and review-level findings, not only inline threads.
   Incomplete pagination or inaccessible results block readiness.
2. Wait for CI and the automated reviewer to complete for that exact head.
   Inspect the expected checks against repository requirements and the actual provider.
   Require observed green CI and an explicit clean review for that head.
   Absent, pending, failed, skipped, cancelled, stale, or unobservable checks and reviews do not satisfy this condition.
   Zero comments, resolved threads, a successful transport check, or an old approval alone do not prove a clean review.
3. Apply every valid, safe, in-scope review finding, including LOW, Minor, Enhancement, and documentation-only findings,
   or retain it as a required blocker. Priority is not permission to skip.
   Human findings remain visible and block readiness when unresolved.
   Read the exact finding and current code. Make the narrow correction, run relevant checks, and inspect the diff.
   A focused review fix does not restart the full implementation, simplification, and independent-review chain.
   If a fix adds materially new scope, apply the full chain to that added scope.
   Reject only with evidence of an invalid premise or inapplicability; record the outcome in the existing task/review record.
   Keep unsafe fixes, scope expansion, and design/objective conflicts blocked for a decision without weakening tests or contracts.
   Preserve material unresolved concerns and coverage limits separately from admitted findings.
   Do not silently ignore findings, dismiss them, or resolve threads merely to manufacture a clean state.
4. Commit and push verified corrections only within the established authorization and repository process.
   Stage changed files by name. This policy does not authorize rewriting remote history.
   Inspect and reconcile unexpected remote changes before pushing.
   Each push invalidates earlier clean verdicts and check results. Return to step 1 for the new head.
   Independently refresh affected candidate conclusions and verification scenarios, including structural outcomes and rejected/skipped decisions.
   Refresh affected evidence in the PR body. Read that body with the final reviewer-visible diff under submit-pr's post-generation audit,
   then wait for new CI and review results.
   Use only a documented, authorized review trigger if review does not start automatically.
5. Finish only when the remote head is unchanged, CI is green, and the automated reviewer explicitly reports no issues for that head.
   Require no outstanding human or bot findings, no conflicts, and compliance with repository base-update requirements.
   Re-read head, checks, and all review pages immediately before reporting success.

Example: review A finds an unreadable condition. Fixing it creates head B.
Review B finds a missing boundary case. Fixing it creates head C.
Green CI and clean review A do not finish C. Wait for green CI and an explicit clean review of C.

Drive this policy until every completion condition holds, not as one repair attempt.
There is no timeout that converts silence into success.
Report definite failures immediately in the conversation and task record.
If access, tooling, CI, stalled review, repeated non-progressing fixes, or session limits prevent completion, report **blocked**.
Preserve the latest head, check and review state, evidence links, and exact next action.
A notification means work resumes; it does not replace handling the result.

## 2. Claude `/loop` Setup

After PR creation, invoke `/loop` through the Skill tool.
Do not use CronCreate directly or replace Claude's supported scheduler with shell polling.
Read the installed `/loop` instructions and confirm its interface before invocation.
Do not run blocking watch commands or shell sleep/poll loops.

Pass this prompt to `/loop`, substituting the real PR, repository, reference path, and optional notification channel:

```text
/loop 5m Monitor PR #<N> on <GH_HOST>/<ORG>/<REPO>.
Read <CLAUDE_PLUGIN_ROOT>/skills/submit-pr/references/build-monitoring.md.
Follow Section 1 for latest-head CI and explicit automated-review convergence.
Read all pages of human and bot findings. Address every priority, including LOW and documentation findings.
Follow Section 3 for CI-provider discovery and actual failure logs.
Make focused authorized fixes, run relevant checks, and refresh affected evidence after each push.
Each push invalidates old verdicts. Recheck the new head before reporting success.
Report definite failures and blockers immediately in the conversation and task record.
If --notify is set, use <channel> with Section 5 and references/slack-notifications.md.
Do not send Slack messages otherwise. Never merge or enable automatic merging.
If another actor merges or closes the PR, report that external state and follow Section 4.
Continue while results are pending; stop as blocked if progress requires unavailable access, authorization, or tools.
Stop successfully only when Section 1's full completion condition holds.
```

Resolve `<CLAUDE_PLUGIN_ROOT>` to this installed plugin's actual root before starting the watcher.
Replace `<N>` and `<GH_HOST>/<ORG>/<REPO>` with the captured PR number and full repository slug.
Pass the literal `--notify <channel>` value when present. Remove that placeholder when no channel is supplied.

Retain the scheduler's returned identifier and confirm that the watcher actually starts.
Record the PR URL, repository, branch, current head SHA, identifier, next check, and runtime lifetime limits.
Name where failures surface and who reads them: the conversation/task record for the user or supervising worker, plus authorized Slack notifications.
A background log alone does not deliver a failure report.

If `/loop` is unavailable or startup fails, perform one bounded status check and report ongoing monitoring as blocked.
Do not promise a watcher without a confirmed start. A single check does not establish ongoing monitoring.

## 3. Discover the Actual CI Provider

Inspect the PR's live status checks, their target URLs, and repository configuration.
Use the installed `gh pr view` interface to inspect `headRefOid`, `statusCheckRollup`, and PR state.
Confirm supported fields with local CLI help before composing commands.
Do not infer the provider from a generic check name or assume GitHub Actions, Buildkite, or any other provider.

When the provider has an installed skill or CLI, use its documented commands for build status and logs.
If the skill or CLI is unavailable, report that blocker and retain the actual check URL.
Otherwise use the provider's verified local tool or documented interface.
Do not guess artifact buckets, URL formats, or build identifiers.

Read actual logs before classifying a failure or changing code.
Attribute the failure to the submitted change, pre-existing code, or the environment using evidence.
Check-name guesses do not justify automated fixes or a success claim.
Include the actual error excerpt, build URL, and classification in a failure report.
Report inaccessible logs explicitly instead of inventing an error.

## 4. Fixes and External Closure

Fix task-related failures only within the active authorization, then run relevant local checks.
A pending review or `CHANGES_REQUESTED` status alone does not forbid a corrective commit.
Follow Section 1 after each push, regardless of finding priority or file type.
Do not limit the loop to lint fixes or stop at the first green build.

If another actor merges or closes the PR, stop monitoring and report that external state.
A closed or merged state does not prove review convergence.
Keep the existing Jira transition behavior for an externally merged PR, using `references/jira-integration.md`.
Never merge or enable automatic merging from this monitor.

## 5. Slack Channel Passing

Pass the literal `--notify <channel>` value from SKILL.md Phase 3 to the `/loop` prompt.
Use `references/slack-notifications.md` for channel resolution and notification templates.

If `--notify` is absent, send no Slack messages.
Report failures and blockers through the conversation and task record instead.
If `--notify` is present, include the actual error excerpt, build URL, and failure classification when available.
Report unavailable logs explicitly rather than inventing an error.
Send a success notification only after Section 1 completes, not when CI alone becomes green.
Report notification failures in the conversation and task record without abandoning monitoring.
