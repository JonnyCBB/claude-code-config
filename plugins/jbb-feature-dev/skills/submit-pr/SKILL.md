---
name: submit-pr
description: >
  Submit work for review with comprehensive PR descriptions, Jira integration,
  build monitoring, and Slack notifications. Creates or updates GitHub PRs,
  transitions Jira tickets, and optionally monitors build status with auto-fix.
  Use when the user asks to submit a PR, create a PR, or says "/submit-pr".
argument-hint: "[target-branch] [--draft] [--no-diagram] [--no-jira] [--monitor] [--notify CHANNEL] [--auto-merge] [--scoping-doc PATH] [--verification PATH] [--requirements PATH] [--non-interactive]"
---

# Submit PR

Submit work for review. Creates or updates GitHub PRs with comprehensive descriptions,
optionally integrating with Jira, monitoring builds, and sending Slack notifications.

## Arguments

| Flag                    | Default                | Effect when set                                                                                                                                                     |
| ----------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[target-branch]`       | `master`               | Branch to compare against                                                                                                                                           |
| `--draft`               | off                    | Create as draft PR                                                                                                                                                  |
| `--no-diagram`          | off (diagrams enabled) | Skip diagram generation                                                                                                                                             |
| `--no-jira`             | off (Jira enabled)     | Skip Jira ticket integration                                                                                                                                        |
| `--monitor`             | off                    | Start build monitoring loop via `/loop`                                                                                                                             |
| `--notify <channel>`    | not set                | Slack channel for build notifications                                                                                                                               |
| `--auto-merge`          | off                    | Enable `gh pr merge --auto --squash --delete-branch`                                                                                                                |
| `--non-interactive`     | off                    | Auto-push, auto-decide all prompts                                                                                                                                  |
| `--scoping-doc <path>`  | not set                | Read Branch Chain from scoping doc, create stacked PRs                                                                                                              |
| `--verification <path>` | not set                | Explicit path to a verification report or summary to embed in the PR description; takes precedence over auto-detection at `~/.claude/thoughts/shared/verification/` |
| `--requirements <path>` | not set                | Path to the requirements document; used to enrich the PR description's Why/What sections with feature context beyond what `git log` provides                        |

## Mode Detection

Parse `$ARGUMENTS` for all flags before starting:

- If `--non-interactive` is set: auto-push without asking, auto-decide all prompts
- Otherwise: interactive mode — ask before pushing, confirm key decisions
- Extract `[target-branch]` as first positional arg if present (default: `master`)
- Record all flags for use in later phases
- If `--scoping-doc <path>` is set: read the scoping document, parse the Branch Chain table. If the PR Strategy is "Stacked PRs" and a Branch Chain table exists, enter stacked PR mode. Otherwise, fall through to single-PR mode.

## Phase 1: Pre-Submit (Analyze and Gather Context)

Read references/pr-description-template.md for template sections.
Read references/diagram-generation.md for complexity analysis.

1. **Fetch and analyze changes** against target branch:
   - Run `git diff`, `git log`, `git diff --name-only` to gather context
   - Summarize commits, changed files, and scope of changes

2. **Extract Jira ticket** from branch name using regex from references/jira-integration.md
   (skip if `--no-jira` is set)

3. **Auto-detect key information**:
   - Breaking changes (API changes, removed fields, migration requirements)
   - Feature flags referenced in the diff
   - Test coverage (new or modified tests)
   - Documentation changes

4. **Analyze PR complexity** for diagram generation using thresholds from references/diagram-generation.md
   - If thresholds met and `--no-diagram` not set: spawn visual-aid-recommender to generate architecture diagram

5. **Discover PR template** in repository by searching paths from references/pr-description-template.md
   (e.g., `.github/PULL_REQUEST_TEMPLATE.md`, `PULL_REQUEST_TEMPLATE.md`)

6. **Locate verification report** — if `--verification <path>` was provided, use that
   path directly. Otherwise, auto-detect at `~/.claude/thoughts/shared/verification/`.
   If a report exists (from either source) and includes live testing results, the PR
   description MUST include:
   1. **Reproduction instructions** from the report's "Reproduction Instructions" section
      (prerequisites, service startup command, health check, all test request commands, cleanup)
   2. **Verbatim request/response transcripts** for each live test scenario, each in a
      collapsible `<details>` section (per `references/collapsible-format.md`)
   3. **Summary verdict table** from the report's "Summary" section
      Do NOT omit the verbatim transcripts or reproduction instructions — they are the strongest
      evidence that the implementation works and allow reviewers to verify without re-running.
      If no live testing was performed, include only the summary verdict table and key assertions.
      When the report is a structured verification summary (assertion table with Status/Expected/
      Actual/Detail columns — as produced by the orchestrator's validator), embed the full table
      inside a collapsible `<details>` section with summary text
      `Verification details: <VERDICT>` (PASS when all passed, FAIL otherwise). The visible
      Testing & Verification section should still contain a short human-readable summary
      (e.g., "22/22 assertions passed") above the collapsible.

7. **Elicit the "why"** (interactive mode only, skip if `--non-interactive` or
   `--requirements` provides context):
   - If commit messages and available context don't clearly explain the motivation,
     ask the user ONE question via AskUserQuestion:
     "Would you like to add context about why this change was made? This helps
     reviewers but is optional — I can derive what I can from the commits."
   - Options: "Yes, let me explain" / "No, use what you have"
   - If yes: ask "What's the motivation for this change?"
   - If no: derive the "why" from commits, ticket, and diff without inventing reasons
   - **Never fabricate motivation.** If the real reason is unknown, write a factual
     description of what the change does. Never insert plausible-sounding reasons
     like "performance optimization" or "improved maintainability" unless the commit
     messages or requirements doc explicitly say so.

## Phase 2: Submit (Create or Update PR)

Read references/collapsible-format.md for formatting guidelines.
Read references/jira-integration.md for ticket transitions.

1. **Generate PR description** using discovered repository template or default format from
   references/pr-description-template.md — apply collapsible formatting per references/collapsible-format.md.
   Apply the content generation and prose quality rules from `references/pr-prose-rules.md` during generation.
   **Then audit the body per the "Reviewer-Visible Content Only" rule below** — strip any local file paths or
   references to material that exists only on the author's machine before submitting. The audit MUST also
   strip any unit-test mentions, counts, or `Unit` table rows per the "Do Not Restate CI-Covered Signals" rule,
   and run the post-generation audit from `references/pr-prose-rules.md`.

2. **Push branch** if needed:
   - Interactive mode: ask user before pushing
   - Non-interactive mode: auto-push without prompting

3. **Create or update PR** via `gh pr create` / `gh pr edit`:
   - Add `--draft` flag if `--draft` was specified
   - Capture PR URL from output

### Stacked PR Creation (when `--scoping-doc` is provided)

**Skip this section if `--scoping-doc` was not provided or no Branch Chain table found.**

When in stacked PR mode, Phase 2 replaces the single-PR creation with a loop:

1. **Parse Branch Chain table** from the scoping document:
   - Extract each row's Plan, Branch Name, and Base Branch
   - Process plans in table order (top to bottom = dependency order)

2. **For each plan in the Branch Chain**:
   a. Check out the plan's branch: `git checkout <branch-name>`
   b. Push the branch: `git push -u origin <branch-name>`
   c. Create PR with correct base:

   ```bash
   gh pr create --base <base-branch> --title "<plan-title>" --body "<description>"
   ```

   Add `--draft` flag if `--draft` was specified.
   d. Capture the PR URL and number from the output
   e. If `--auto-merge` is set: `gh pr merge --auto --squash --delete-branch`

3. **Add Stack section to all PRs**: After all PRs are created (so we have all PR numbers), update each PR's description to include the Stack section:

   ```bash
   gh pr edit <pr-number> --body "<updated-description-with-stack-section>"
   ```

   The Stack section template is defined in `references/pr-description-template.md`.

4. **Jira integration**: Link the first PR (or all PRs) to the Jira ticket. Each PR gets a comment with its URL.

**Backwards compatibility**: If `--scoping-doc` is not provided, Phase 2 behaves exactly as today — single PR on the current branch, no stacking, no `--base` flag.

4. **Jira integration** (skip if `--no-jira` or no ticket found):
   - `add_comment(ticket, "PR: <URL>")` — link PR to ticket
   - `get_available_transitions` — fetch available status transitions
   - Fuzzy match to find appropriate "In Review" or equivalent transition
   - `edit_ticket(transition_to=<match>)` — move ticket to review state
   - All Jira operations are non-blocking — never fail the PR creation

## Phase 3: Post-Submit (Integrate and Monitor)

1. **Auto-merge** (if `--auto-merge` is set):
   - Run `gh pr merge --auto --squash --delete-branch`

2. **Slack notification** (if `--notify <channel>` is set):
   - Read references/slack-notifications.md for notification templates
   - Send PR URL and summary to specified Slack channel

3. **Build monitoring** (if `--monitor` is set):
   - Read references/build-monitoring.md for monitoring prompt template
   - Invoke `/loop` via the Skill tool with the monitoring prompt template from that file
   - Do NOT use CronCreate directly — always compose with `/loop`

## Completion

Display a summary including:

- PR URL (created or updated)
- Jira ticket linked (if applicable)
- Build monitoring started (if `--monitor` was set)
- Slack notification sent (if `--notify` was set)

## Important Note about ~/.claude/thoughts directory

**Important Note about `~/.claude/thoughts` directory**:

- You MAY use information from the `~/.claude/thoughts` directory to provide additional context for the PR description
- You MUST NOT commit or push any changes from the `~/.claude/thoughts` directory unless:
  - The changes are already in a committed state, OR
  - The user explicitly requests to include them
- When analyzing git changes, filter out or ignore uncommitted `~/.claude/thoughts/` changes in your PR description

## Reviewer-Visible Content Only (Hard Rule)

Reviewers see only the GitHub PR — they cannot access anything on the author's local machine. Anything the PR description refers to must be reachable from the PR itself.

**Never include in the PR description:**

- Local file paths (e.g., `~/.claude/thoughts/...`, `/Users/...`, `/tmp/...`, project-relative paths to files outside the diff)
- References to research docs, plans, scoping docs, verification reports, or notes that exist only on the author's machine
- Numbered "options" (e.g., "Option 2", "Approach B"), tradeoff comparisons, or decision rationale that was enumerated in a local doc — without first inlining that option's content into the PR description itself
- Phrases like "see the plan", "per the research doc", "as discussed in the scoping doc", "from my notes" — unless the referenced material is fully inlined or linked to a reviewer-accessible URL (Jira, Google Doc, GitHub issue, internal wiki)

**Allowed references:**

- Files in the PR's diff (reviewers can see them in GitHub)
- Files elsewhere in the same repo at a stable path (reviewers can navigate to them on GitHub)
- URLs reviewers can open: Jira tickets, Google Docs, internal wiki pages, other PRs, GitHub issues
- Verbatim, inlined content from local docs (the content itself is in the PR body, not a pointer)

**Before finalizing the PR body, audit it:**

1. Grep the body for `~/`, `/Users/`, `/tmp/`, `.claude/`, `thoughts/`, `verification/`, `scoping/`, `research/`, `plans/` — remove or replace any matches.
2. For every reference to "Option N", "Approach X", "the plan", "the doc", "the report" — confirm the referenced material is either fully inlined in the PR body or linked to a reviewer-accessible URL. If neither, either inline it or remove the reference.
3. If a local doc was the source of context but the context itself matters for review, paraphrase the relevant reasoning into the PR body directly rather than pointing at the doc.

## Do Not Restate CI-Covered Signals (Hard Rule)

CI build checks run unit tests and report results directly on the PR. Restating
that information in the PR body is noise — it duplicates the check, can go stale,
and pads the description.

**Never include in the PR description:**

- "Unit tests added", "unit tests pass", "all tests green", or any equivalent claim
- Unit-test counts, pass/fail tallies, or coverage percentages
- A `Unit` row in the verification per-category counts table
- Any framing that asserts unit-test success ("tested with X assertions")

**Still include (CI cannot run these):**

- Live testing transcripts (verbatim request/response from a running service)
- Integration tests that require external services CI does not provision
- Manual verification steps, screenshots, reproduction instructions

**Audit step before finalizing:** grep the PR body for `unit test`, `unit tests`,
`/Unit/` (table row), and `tests pass`. Remove every match unless it documents a
non-CI verification activity reviewers cannot otherwise see.

## Reference Files

| File                                    | When to Read                               | Phase   |
| --------------------------------------- | ------------------------------------------ | ------- |
| `references/pr-description-template.md` | PR template discovery and default format   | Phase 1 |
| `references/diagram-generation.md`      | Complexity analysis and diagram generation | Phase 1 |
| `references/pr-prose-rules.md`          | Content generation and prose quality       | Phase 2 |
| `references/collapsible-format.md`      | Formatting detailed examples               | Phase 2 |
| `references/jira-integration.md`        | Ticket extraction and transitions          | Phase 2 |
| `references/build-monitoring.md`        | Build monitoring via /loop                 | Phase 3 |
| `references/slack-notifications.md`     | Slack notification templates               | Phase 3 |
