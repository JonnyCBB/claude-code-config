---
name: submit-pr
description: >
  Submit work for review with comprehensive PR descriptions, Jira integration,
  build monitoring, and Slack notifications. Creates or updates GitHub PRs,
  transitions Jira tickets, and optionally monitors build status with auto-fix.
  Use when the user asks to submit a PR, create a PR, or says "/submit-pr".
argument-hint: "[target-branch] [--draft] [--no-diagram] [--no-jira] [--monitor] [--notify CHANNEL] [--scoping-doc PATH] [--verification PATH] [--requirements PATH] [--non-interactive]"
---

# Submit PR

Submit work for review. Creates or updates GitHub PRs with comprehensive descriptions,
optionally integrating with Jira, monitoring builds, and sending Slack notifications.

## Arguments

| Flag                    | Default                | Effect when set                                                                                                                                                     |
| ----------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[target-branch]`       | recorded task target, otherwise resolve | Branch to compare against and explicit PR base                                                                                                                                           |
| `--draft`               | off                    | Create as draft PR                                                                                                                                                  |
| `--no-diagram`          | off (diagrams enabled) | Skip diagram generation                                                                                                                                             |
| `--no-jira`             | off (Jira enabled)     | Skip Jira ticket integration                                                                                                                                        |
| `--monitor`             | off                    | Monitor latest-head CI and review convergence via `/loop` |
| `--notify <channel>`    | not set                | Slack channel for build notifications                                                                                                                               |
| `--auto-merge`          | rejected               | Unsupported. This workflow never merges or enables automatic merging. |
| `--non-interactive`     | off                    | Auto-push and decide routine submission prompts; never authorize merging |
| `--scoping-doc <path>`  | not set                | Read Branch Chain from scoping doc, create stacked PRs                                                                                                              |
| `--verification <path>` | not set                | Use a verification artifact after checking its repository, branch, objective, and tested change |
| `--requirements <path>` | not set                | Path to the requirements document; used to enrich the PR description's Why/What sections with feature context beyond what `git log` provides                        |

## Mode Detection

Parse `$ARGUMENTS` for all flags before starting:

- Reject `--auto-merge` before any side effect. Explain that this workflow never merges or enables automatic merging.
- If `--non-interactive` is set: auto-push without asking and decide routine submission prompts only
- Otherwise: interactive mode — ask before pushing, confirm key decisions
- Extract `[target-branch]` as first positional arg if present; otherwise use the recorded task target.
- Without either, resolve the intended target from repository/PR context; never assume `master` or `main`.
  If ambiguous or inconsistent with the reviewed scope, ask or report blocked in non-interactive mode.
- Record the resolved target branch separately from the pinned comparison commit. Reuse the supplied pinned base;
  a changed target requires renewed scope/evidence checks before submission.
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

6. **Gather objective-based verification evidence** for every PR, including libraries and documentation.
   - Use `--verification <path>`, a task-linked artifact, or a report that matches this repository, branch, objective, and current change.
   - Never select an arbitrary newest report from `~/.claude/thoughts/shared/verification/`.
   - Check the tested commit and relevant working-tree changes against the submitted head.
   - Treat missing provenance or older commits as unverified for the latest head. Re-run relevant verification or state the limit.
   - Without an artifact, gather direct evidence or mark unsupported scenarios unverified. Never omit the verification section.
   - Follow `references/pr-description-template.md`, "Verification Results Embedding", for scenario mapping and complete reproduction details.
   - Preserve real outputs and verbatim transcripts. Never invent commands, results, motivation, or success claims.

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
   Apply STE clear prose and, when available, `jiffy-toolkit:sound-like-me --register=github-pr-body`, with the fallback in `references/pr-prose-rules.md`.
   Audit reviewer access and evidence provenance before submitting. Preserve exact identifiers and verbatim transcripts.
   Remove routine CI noise, not behavioral unit-test evidence needed to explain the objective.
   Run the post-generation audit from `references/pr-prose-rules.md` while reading the final reviewer-visible diff
   and PR description together against the resolved target. Check that examples and evidence cover this final state,
   and that relevant existing formatter/lint results remain current. Refresh affected checks and independent conclusions
   after later fixes; do not present stale examples or a prior diff's results as current evidence.

2. **Push branch** if needed:
   - Interactive mode: ask user before pushing
   - Non-interactive mode: auto-push without prompting

3. **Create or update PR** via `gh pr create` / `gh pr edit`:
   - For a single PR, pass the resolved target explicitly with `--base` on creation; do not rely on CLI defaults.
   - Before updating an existing PR, read its current base with `gh pr view <pr-number> --json baseRefName`.
     If it differs from the resolved target, obtain explicit confirmation before retargeting and recheck scope/evidence.
     Without confirmation, report blocked in non-interactive mode rather than prompting or changing the base.
     Otherwise update its body and metadata without silently changing its base.
   - Add `--draft` flag on creation if `--draft` was specified
   - Capture PR URL and number from output
   - Confirm the actual base and head with `gh pr view <pr-number> --json baseRefName,headRefName`.
     Compare them with the recorded target and intended head branch. A mismatch blocks submission completion;
     reconcile within authorization and recheck scope/evidence before proceeding.

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
   e. Leave the PR open for review. Never merge or enable automatic merging.

3. **Add Stack section to all PRs**: After all PRs are created (so we have all PR numbers), update each PR's description to include the Stack section:

   ```bash
   gh pr edit <pr-number> --body "<updated-description-with-stack-section>"
   ```

   The Stack section template is defined in `references/pr-description-template.md`.

4. **Jira integration**: Link the first PR (or all PRs) to the Jira ticket. Each PR gets a comment with its URL.

Without stacked-PR mode, create one PR on the current branch with the explicitly resolved `--base`, or update its existing PR after checking the base.
For stacked PRs, confirm each actual base/head against its Branch Chain row using the same metadata check above.

4. **Jira integration** (skip if `--no-jira` or no ticket found):
   - `add_comment(ticket, "PR: <URL>")` — link PR to ticket
   - `get_available_transitions` — fetch available status transitions
   - Fuzzy match to find appropriate "In Review" or equivalent transition
   - `edit_ticket(transition_to=<match>)` — move ticket to review state
   - All Jira operations are non-blocking — never fail the PR creation

## Phase 3: Post-Submit (Integrate and Monitor)

1. **Leave the PR open**. This workflow never merges or enables automatic merging, including in non-interactive mode.
   Handle any later merge request separately, under the applicable per-PR confirmation policy.

2. **Slack notification** (if `--notify <channel>` is set):
   - Read references/slack-notifications.md for notification templates
   - Send PR URL and summary to specified Slack channel

3. **Build monitoring** (if `--monitor` is set):
   - Read `references/build-monitoring.md` for the canonical latest-head CI and review convergence policy and monitoring prompt.
   - Invoke `/loop` via the Skill tool. Do not use CronCreate directly.
   - Confirm the watcher starts and retain its identifier. Report setup failures as blocked, not as active monitoring.
   - Follow that reference after each push until CI and the explicit automated review are clean for the latest head.

## Completion

Display a summary including:

- PR URL (created or updated)
- Jira ticket linked (if applicable)
- Monitoring identifier and verified startup, current head, and next check, or the exact blocker
- Latest-head CI and automated-review evidence; report incomplete convergence as blocked
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

- Author-only file pointers (e.g., `~/.claude/thoughts/...` or absolute home-directory paths used instead of inlined evidence)
- References to research docs, plans, scoping docs, verification reports, or notes that exist only on the author's machine
- Numbered "options" (e.g., "Option 2", "Approach B"), tradeoff comparisons, or decision rationale that was enumerated in a local doc — without first inlining that option's content into the PR description itself
- Phrases like "see the plan", "per the research doc", "as discussed in the scoping doc", "from my notes" — unless the referenced material is fully inlined or linked to a reviewer-accessible URL (Jira, Google Doc, GitHub issue, internal wiki)

**Allowed references:**

- Files in the PR's diff (reviewers can see them in GitHub)
- Files elsewhere in the same repo at a stable path (reviewers can navigate to them on GitHub)
- URLs reviewers can open: Jira tickets, Google Docs, internal wiki pages, other PRs, GitHub issues
- Verbatim, inlined content from local docs (the content itself is in the PR body, not a pointer)

**Before finalizing the PR body, audit it:**

1. Check matches for `~/`, `/Users/`, `/tmp/`, `.claude/`, `thoughts/`, `verification/`, `scoping/`, `research/`, and `plans/`.
   Remove author-only pointers, not valid repository paths, reproducible commands, exact identifiers, or verbatim evidence.
   If a transcript contains author-only paths, preserve it and provide portable reproduction setup separately.
2. For every reference to "Option N", "Approach X", "the plan", "the doc", "the report" — confirm the referenced material is either fully inlined in the PR body or linked to a reviewer-accessible URL. If neither, either inline it or remove the reference.
3. If a local doc was the source of context but the context itself matters for review, paraphrase the relevant reasoning into the PR body directly rather than pointing at the doc.

## Behavioral Evidence, Not Routine CI Noise

Always explain how verification demonstrates the objective before reviewers read code.
Include behavioral unit-test evidence when needed, especially for pure libraries without a running service.
Show exact inputs, expected and observed outputs, a reproducible command, and a real output excerpt.
A test count or a green check alone does not explain behavior.

Omit routine pass totals, coverage percentages, and generic claims such as "all tests green".
Keep relevant live transcripts, integration evidence, manual steps, and screenshots, even when CI also checks the behavior.
State unverified behavior and environment limits explicitly.

## Reference Files

| File                                    | When to Read                               | Phase   |
| --------------------------------------- | ------------------------------------------ | ------- |
| `references/pr-description-template.md` | PR template discovery and default format   | Phase 1 |
| `references/diagram-generation.md`      | Complexity analysis and diagram generation | Phase 1 |
| `references/pr-prose-rules.md`          | Content generation and prose quality       | Phase 2 |
| `references/collapsible-format.md`      | Formatting detailed examples               | Phase 2 |
| `references/jira-integration.md`        | Ticket extraction and transitions          | Phase 2 |
| `references/build-monitoring.md`        | Canonical convergence policy and /loop setup | Phase 3 |
| `references/slack-notifications.md`     | Slack notification templates               | Phase 3 |
