# Build Monitoring Reference

This document describes how the `/submit-pr` skill monitors PR builds after creation,
including the `/loop` composition pattern, CI log retrieval, auto-fix safety
protocol, decision framework, exit conditions, and Slack channel passing.

---

## 1. `/loop` Composition

After PR creation (Phase 3 of SKILL.md), the skill invokes `/loop` via the Skill tool.
Do NOT use CronCreate or any direct scheduling mechanism — always compose via `/loop`.

The monitoring prompt template passed to `/loop`:

```
/loop 5m Check PR #<N> build status on <GH_HOST>/<ORG>/<REPO>.
Run 'gh pr checks <N> --repo <GH_HOST>/<ORG>/<REPO> --json name,state,bucket'.
If all checks pass, send a Slack message to <channel> (if --notify was specified)
and stop this loop. If any check failed, investigate the failure using the
CI log retrieval steps in references/build-monitoring.md Section 1.1
before deciding on action. If a lint/format check failed, follow the auto-fix
safety protocol below. If a test or build failure occurred, include the actual
error from the build log in the Slack notification to the developer, then stop
this loop. If checks are still pending, describe current status and continue.
If the PR has been merged, transition the Jira ticket to "Done" using the fuzzy
match algorithm from references/jira-integration.md (candidates: "done", "closed",
"resolved", "complete") and stop this loop. If the PR has been closed without
merging, stop this loop.
```

Replace `<N>` with the PR number, `<GH_HOST>/<ORG>/<REPO>` with the full repo slug
(e.g., `github.com/search-platform/search-wasp`), and `<channel>` with the literal
Slack channel string from the `--notify` flag (see Section 5).

---

## 1.1 CI Log Retrieval

CI may be GitHub Actions, BuildKite, or another provider. The `gh run view`
and `gh run view --log-failed` commands do NOT work. Use the approach below to get
actual build logs when a check fails.

### Identify the CI System

```bash
gh pr view <PR_NUMBER> --repo <REPO_SLUG> --json statusCheckRollup
```

| Check name / context                        | CI System |
| ------------------------------------------- | --------- |
| `ci` or `continuous-integration/ci`         | Generic   |
| `CI-PR`                                     | BuildKite |
| `ci/tests` or `ci/coverage`                 | Generic   |
| `tests` (alongside `CI-PR`)                 | BuildKite |

# Extract the build id from the CI status check targetUrl
BUILD_URL=$(gh pr view <PR_NUMBER> --repo <REPO_SLUG> --json statusCheckRollup \
  --jq '.statusCheckRollup[] | select(.targetUrl != null and (.targetUrl | contains("/build/"))) | .targetUrl' | head -1)

BUILD_ID=$(echo "$BUILD_URL" | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | tail -1)

# Download last 300 lines of console log
gsutil cat "gs://<your-ci-log-bucket>/<ORG>/<REPO>/$BUILD_ID/console.log" 2>/dev/null | tail -300
```

### BuildKite Logs

Direct BuildKite API access is restricted. Extract the build URL from the
`CI-PR` status check `targetUrl` and include it in notifications for the developer.

### Using Logs for Classification

With actual log text, you can reliably classify the failure:

| Log pattern                                                                   | Classification                      |
| ----------------------------------------------------------------------------- | ----------------------------------- |
| `spotless`, `checkstyle`, `eslint`, `prettier`, `black`, `scalafmt`, `ktlint` | Lint/format — eligible for auto-fix |
| `Test.*FAILED`, `assertion.*error`, `expected.*but was`                       | Test failure — notify developer     |
| `BUILD FAILED`, `COMPILATION ERROR`, `javac.*error`, `scalac.*error`          | Build failure — notify developer    |
| `timed out`, `deadline exceeded`, `resource exhausted`                        | Infra issue — note in notification  |

**Without logs** (GCS download failed), fall back to check-name heuristics:

- `Static Code Analysis` or `ci/lint` → likely lint
- `ci/tests` → likely test failure
- `ci` (generic) → unknown, include the build URL in notification

---

## 2. Auto-Fix Safety Protocol

Before pushing any automated fix for a lint/format failure, the skill MUST perform a
safety check to avoid overwriting changes under active review.

Steps:

1. Run `gh pr reviews <PR> --json state` to retrieve all reviews on the PR.
2. If any review has state `PENDING` or `CHANGES_REQUESTED`:
   - Skip the auto-fix entirely.
   - Send a Slack notification to `<channel>` (if `--notify` was specified):
     > "Lint failure detected but skipping auto-fix — active review on PR"
   - Stop — do not push any changes.
3. If no review is in `PENDING` or `CHANGES_REQUESTED` state:
   - Run the appropriate formatter (e.g., `./gradlew spotlessApply`, `black .`, `prettier --write .`).
   - Stage only the changed files: `git add <changed-files>`.
   - Commit with message: `git commit -m "Auto-fix lint/format"`.
   - Push: `git push --force-with-lease`.

**Critical**: Always use `--force-with-lease`, never `--force`. This prevents overwriting
concurrent pushes that may have occurred since the last fetch.

---

## 3. Auto-Fix Decision Framework

Only lint/format failures are eligible for automated fixing. All other failure types
require developer notification. **Always attempt to download and read build logs
(Section 1.1) before classifying** — check names alone are unreliable because CI providers
often reports a single `ci` check covering compilation, tests, and lint.

| Check Type             | How to Identify (from logs)                                 | Action                                     |
| ---------------------- | ----------------------------------------------------------- | ------------------------------------------ |
| Lint/format failure    | Log contains `spotless`, `checkstyle`, `eslint`, `scalafmt` | Auto-fix (after safety check in Section 2) |
| Test failure           | Log contains `Test.*FAILED`, assertion errors               | Notify developer via Slack, stop loop      |
| Build/compilation fail | Log contains `BUILD FAILED`, `COMPILATION ERROR`            | Notify developer via Slack, stop loop      |
| Infra/timeout          | Log contains `timed out`, `resource exhausted`              | Notify developer via Slack, stop loop      |
| Any other failure      | Log not retrievable or no pattern match                     | Notify developer via Slack, stop loop      |

**Why tests and builds are never auto-fixed**: Automatically modifying test or build
failures risks masking real bugs. These failures require human investigation and judgment.

**Slack failure notifications MUST include**:

- The specific error from the build log (first 5-10 lines of the relevant error)
- The CI build URL (from `statusCheckRollup` targetUrl) so the developer can
  click through to the full log
- The classification (lint, test, build, infra) so the developer knows what to expect

---

## 4. Exit Conditions

The `/loop` monitoring prompt instructs the loop to stop under the following conditions:

| Condition                 | Action before stopping                                               |
| ------------------------- | -------------------------------------------------------------------- |
| All checks pass           | Send Slack success notification (if `--notify` was specified)        |
| Test or build failure     | Send Slack failure notification to developer                         |
| PR merged                 | Transition Jira ticket to "Done" using fuzzy match (see below), stop |
| PR closed without merging | Stop immediately, no notification required                           |

**Jira transition on merge**: When the PR is merged, use the fuzzy match algorithm from
`references/jira-integration.md` to find and apply the appropriate transition. Candidate
transition names to match against: `"done"`, `"closed"`, `"resolved"`, `"complete"`.

The loop continues (without stopping) when checks are still in a pending state — it
should describe current pending check status and await the next interval.

---

## 5. Slack Channel Passing

The `--notify <channel>` argument is passed from SKILL.md Phase 3 into the `/loop`
prompt template as a literal string substitution. For example, if the user invokes:

```
/submit-pr --notify "#my-team-alerts"
```

Then the loop prompt replaces `<channel>` with `#my-team-alerts`:

```
...send a Slack message to #my-team-alerts (if --notify was specified)...
```

**Interface contract**:

- SKILL.md Phase 3 reads the `--notify` value and substitutes it into the loop prompt.
- build-monitoring.md (this file) defines where `<channel>` appears in the prompt.
- `references/slack-notifications.md` provides the message templates used when
  `slack_send_message` is called with that channel.

If `--notify` was not specified, skip all Slack notifications — the loop still monitors
and auto-fixes lint failures, but sends no messages on success or failure.
