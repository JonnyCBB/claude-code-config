---
name: code-review
description: >
  Comprehensive code review with internalized bug detection (bug-catcher), OWASP security
  analysis (security-reviewer), repo-declared rules (repo-rules-reviewer), code
  style (language reviewers), test quality (test reviewers), holistic review
  (general-code-reviewer), domain expertise (domain agents), and a post-review pipeline
  (review-calibrator, review-deduplicator). Use when the user asks to "review my code",
  "review this PR", "code review", or says "/code-review". Replaces /pr-review.
argument-hint: "[pr-number-or-branch] [--all-severities] [--strict-severity] [--severity LEVELS] [--incremental] [--non-interactive]"
---

# Code Review

Conduct a comprehensive code review using specialized agents and a post-review calibration/dedup pipeline.

**IMPORTANT**: This is a review command. DO NOT make any code changes. Only provide constructive, actionable recommendations.

## Arguments

- First argument: a bare PR number or branch name (optional -- prompts if missing, unless `--non-interactive`). Never a PR URL. The skill operates on an already-checked-out repo; it does not clone.
- `--all-severities`: Show all findings including LOW/MEDIUM for all agents
- `--strict-severity`: Keep only HIGH+CRITICAL for ALL agents including code simplification and test reviewers (overrides the default MEDIUM+ and ALL-severity exemptions)
- `--severity LEVELS`: Comma-separated severity levels to include (e.g., `--severity MEDIUM,HIGH,CRITICAL`)
- `--incremental`: Review only new commits since the last /code-review run on this PR. Outputs "New findings" separately from "Previously identified".
- `--non-interactive`: Never prompt. Resolve the review scope automatically (see Phase 1 step 1) and record the resolved scope in the review document. Pipeline callers such as `/orchestrate-feature-dev` pass this because there is no user present to answer a prompt — without it, an unresolvable scope would stall the whole pipeline on a question nobody sees.

**Default severity behavior**: MEDIUM+HIGH+CRITICAL for most agents, **except** code style and test reviewers which keep ALL severities (test reviewers skip LOW findings they consider unhelpful). Use `--strict-severity` to enforce HIGH+CRITICAL across every dimension.

## Phase 1: Context Gathering (parallel)

1. **Determine what to review**: If the user provided a PR number or branch, use that. Otherwise resolve the scope from the current branch.

   If `--non-interactive` is set, never ask — resolve automatically (current branch, else the working-tree diff per step 2) and record the resolved scope in the review document. Only in interactive mode, with no resolvable scope, may you ask the user.

2. **Sync to the PR's latest code**: Before capturing ANY diff, ensure local files match the PR head. This is critical — review agents read on-disk files, and a stale working tree produces false findings.
   - For PRs: `git fetch origin pull/{{PR_NUMBER}}/head:pr-{{PR_NUMBER}}-review && git checkout pr-{{PR_NUMBER}}-review` (or `gh pr checkout {{PR_NUMBER}}` if on GitHub.com). Verify with `git log --oneline -1` that the HEAD matches the PR's latest commit.
   - For branches: `git fetch origin && git checkout {{BRANCH}} && git pull`
   - **Only then** capture the diff. For PRs: `gh pr diff {{PR_NUMBER}}`. For branches, resolve the scope explicitly rather than handing agents a live revision expression:

     Resolve the base and the file list in **one** command block, then record the resolved values — a shell variable does not survive into a later Bash call, so anything that needs `BASE` again must read it back from the review document rather than expecting the variable to still exist:

     ```bash
     BASE=$(git merge-base origin/master HEAD)          # pin once
     FILES=$(git diff --name-only "$BASE"..HEAD)        # committed range
     MODE="committed range"
     if [ -z "$FILES" ]; then
       FILES=$(git diff HEAD --name-only)              # fall back: uncommitted, staged + unstaged
       MODE="working tree"
     fi
     if [ -z "$FILES" ]; then
       MODE="none"                                     # nothing committed AND nothing uncommitted
     fi
     printf 'MODE=%s\nBASE=%s\nFILES:\n%s\n' "$MODE" "$BASE" "$FILES"
     ```

     **`MODE=none` is a stop, not a pass.** It means there is genuinely nothing to review — no commits ahead and a clean tree. Report it as such and do not run Phase 2. Never emit a 0 Critical / 0 Major result for this case: a caller's severity gate cannot tell that apart from a real clean review, which is precisely how an unreviewed change advances a pipeline. Distinguishing the three modes is the whole point of resolving scope explicitly.

     Two further things this buys, both of which were real failures:

     - **One pinned range for every agent.** A live `origin/master...HEAD` expression is re-evaluated by each agent, so if master advances mid-review they disagree about what they are reviewing. Observed twice: master moved while 7 agents ran 10-17 minutes each, and findings were raised against files that were never in the branch.
     - **An empty committed range is not an empty change.** A branch 0 commits ahead of `origin/master` is the normal state inside an orchestrator worktree, where review runs before the work is committed — the diff is in the working tree. This mirrors `/simplify`'s Phase 0 fallback. Skipping it is worse than failing loudly: the review examines nothing, reports 0 Critical / 0 Major, and a caller's severity gate reads that as a pass and advances.

   - **State the resolved scope in the review document**: which mode was used (PR / committed range / working tree), the base SHA (or the PR head SHA for the PR path), and the resolved file list. A reader cannot otherwise tell a clean review from an empty one, and Phase 3 Step 0 reads these values back to detect a moving tree.
   - If checkout would lose uncommitted work, stash first and restore after the review

   **2b. Check for file exclusion config** (Gap 2): Look for `.gosling.yaml` or `.code-review.yaml` in the repo root. If found, read `exclude_files` glob patterns and filter the diff to remove matching files before any review agents see them. Log which files were excluded.

   **2c. Check for large PR** (Gap 3): Estimate token count of the diff. If the diff exceeds ~50K tokens:
   - Warn the user: "This is a large PR (~N tokens). Review quality may be reduced."
   - Suggest splitting: Analyze the diff for independent modules/directories and suggest logical split points
   - Create a finding: file_path="(PR-level)", severity=MEDIUM, category=BEST_PRACTICE, body="Large PR: this PR changes N files across M directories. Consider splitting into smaller, focused PRs for more effective review."
   - Continue with the review (do not abort)

   **2d. Check for incremental mode** (Gap 7): If `--incremental` flag is set:
   - Search `~/.claude/thoughts/shared/reviews/` for a previous review document matching this PR number
   - If found: identify the git commit range reviewed last time, compute the diff of only NEW commits since that point
   - Store the FULL PR diff separately (for repo-rules-reviewer)
   - Replace the default diff with the incremental diff for most Phase 2 agents
   - Pre-compute `changed_locations_since_prior`: a map of files and line ranges modified since the last review commit. Pass this to the deduplicator in Phase 3.
   - Store the prior review findings for the deduplicator
   - If no previous review found: warn and proceed normally

   **2e. Discover repo-specific coding guidelines** (Gap 1): Search the repository for GOSLING.md and other coding guideline sources:
   - Check for GOSLING.md at repo root and subdirectories
   - Search for: CONTRIBUTING.md, style guides, .editorconfig, lint configs, README sections about coding standards
   - Store discovered guidelines for: (a) the repo-rules-reviewer agent, (b) all other review agents as informational context

   **2f. Fetch human PR review comments** (Gap 5): If reviewing a PR:
   - Fetch existing human review comments via `gh api repos/{owner}/{repo}/pulls/{number}/comments --hostname github.com`
   - Also fetch review-level comments via `gh api repos/{owner}/{repo}/pulls/{number}/reviews --hostname github.com`
   - Store for the deduplicator in Phase 3

3. **Identify languages**: Analyze diff for file extensions. Look up in `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md`
4. **Detect domains**: Follow the detection procedure in `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` — check changed file names/paths against file triggers first (deterministic), then check diff content for strong and corroborating signals
5. **Spawn context agents in parallel**:
   - `codebase-explorer` (subagent_type: `Explore`): Find patterns, conventions, CLAUDE.md in the target repo. **Critically**: identify sibling implementations — other classes/methods in the same package or system that implement the same interface, extend the same base class, or follow the same architectural pattern as the code under review (e.g., other handlers in the same service, other endpoints in the same API). Read their key methods to understand what patterns they follow (error handling, graceful degradation, field usage, logging practices).
   - `jbb-feature-dev:web-search-researcher` (if unfamiliar internal tooling detected): Research organisation-specific best practices
   - `jbb-feature-dev:web-search-researcher` (if a service is identified): Gather operational context (SLOs, deployment health)
6. **Read shared reference files**: Load these into context for injection into Phase 2 prompts:
   - `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/false-positive-guidance.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/position-anchoring.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/severity-rubric.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/comment-format.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/finding-schema.md`
7. Wait for all context agents to complete

## Phase 2: Review Agents (parallel, informed by Phase 1)

**Agent Type Verification**: Before spawning, create an explicit agent contract per `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/agent-verification-pattern.md`.

**Agent delivery resilience**: This phase spawns 5-10+ agents in parallel. Subagents may go idle without delivering results (known Claude Code issue). If an agent sends an `idle_notification` without content: (1) prompt it via SendMessage using its agent ID (not name), (2) if still no delivery, respawn once, (3) if respawn fails, document the gap and proceed with available findings. Consider spawning in sequential sub-batches (e.g., specialist agents first, then language experts) to reduce cascade-failure risk.

Construct prompts for each agent, injecting:

- The diff
- Context findings from Phase 1 (patterns, conventions, ops context)
- Sibling implementation context from Phase 1 (if found) — include file paths and key patterns (error handling, field usage, graceful degradation) so agents can flag inconsistencies between the new code and established sibling patterns
- Shared reference content (false-positive guidance, position anchoring, severity rubric, comment format, finding schema)

Spawn review agents in parallel:

- **`jbb-feature-dev:bug-catcher`** (always) -- Bug detection specialist
- **`jbb-feature-dev:security-reviewer`** (always) -- OWASP security analysis
- **`jbb-feature-dev:repo-rules-reviewer`** (always) -- repo-declared rules from guideline files (graceful degradation to aika-codex if unavailable)
- **Language expert agent** (per detected language, from language-agent-registry: `jbb-feature-dev:python-expert`, `jbb-feature-dev:typescript-expert`) -- spawned TWICE in parallel per language: once with test-review mode framing, once with code-style-review mode framing. See "Dual parallel spawn pattern" below.
- **`jbb-feature-dev:general-code-reviewer`** (always) -- Holistic review with ops context. Additionally check: (1) Did any existing file grow by more than 200 new lines? (2) Are any new files already over 500 lines? (3) Does each changed file maintain a single clear responsibility? If a plan was provided in the PR description, verify the changes follow the planned file structure.
- **Domain experts** (if detected from domain-agent-registry; spawned in parallel ALONGSIDE language experts when both apply — overlapping language + workflow domain coverage spawns BOTH the language expert AND the matching workflow domain expert concurrently)
- **`jbb-feature-dev:repo-rules-reviewer`** (always, but returns empty if no guidelines found) -- Enforces repo-specific coding rules from GOSLING.md and other discovered guidelines. Pass the discovered guidelines from Phase 1 step 2e as the agent's primary input. Pass guidelines as informational context to ALL other review agents as well. **Incremental mode note**: repo-rules-reviewer always receives the FULL PR diff (not the incremental diff), because repo rules apply to all changed code regardless of when commits were made.

### Dual parallel spawn pattern

For each language detected in scope, spawn the corresponding `{language}-expert` agent TWICE in parallel:

1. **test-review framing** — invoke the agent with mode = `test-review`. Output schema: `TEST NEEDED`, `REDUNDANT TEST`, `QUALITY ISSUE` blocks (per `code-review-modes/SKILL.md`).
2. **code-style-review framing** — invoke the agent with mode = `code-style-review`. Output schema: `ISSUE` blocks (per `code-review-modes/SKILL.md`).

Both invocations MUST run concurrently (single message containing both Agent tool calls). Each emits its own per-mode block schema. Downstream `review-deduplicator` (Phase 3 Step 3) consolidates overlapping findings between the two passes and merges adjacent-line duplicates.

**Skill-injection canary** (issue #25834): the silent skill-injection failure mode in plugin issue #25834 means a spawned agent may receive an empty skill body without any error surfaced. Each mode-framed prompt MUST include a canary token (e.g., `MODE_CANARY=test-review-v1`) that the agent is instructed to echo verbatim in its first output line. The orchestrator verifies the echo before accepting findings; absence of the canary indicates the skill content did not reach the agent and the invocation is retried with explicit inline content rather than skill reference.

When both a language expert and a workflow domain expert apply to the same diff (e.g., Java + the serving layer ML serving), spawn BOTH in parallel — they cover orthogonal axes (general language quality vs. workflow-specific best practices) and their findings are merged by the deduplicator.

All agents MUST emit findings using the schema defined in `finding-schema.md`:

```
file_path, position, body, severity, category, confidence, source_agent
```

Wait for all review agents to complete. Collect all findings into a consolidated list.

## Phase 3: Post-Review Pipeline (sequential)

### Step 0: Re-verify the review scope

Phase 2 agents run for 10-17 minutes each, so the tree can move underneath them. Before calibrating, confirm the findings describe the code that was actually reviewed.

Read the base SHA and file list back from the review document — Phase 1 recorded them there for exactly this purpose. Do not expect a `BASE` shell variable to still exist: Phase 1 ran in a different Bash invocation, minutes earlier, and shell state does not persist across tool calls.

**If Phase 1 resolved a committed range or working tree** (the branch path):

```bash
git merge-base origin/master HEAD        # compare to the SHA recorded in the review doc
git diff --name-only <recorded-SHA>..HEAD   # compare to the recorded file list
```

**If Phase 1 resolved a PR**, there is no merge-base to re-check — the scope came from `gh pr diff`. Re-verify by re-listing the PR's files instead, and confirm the PR head has not advanced:

```bash
gh pr view <PR_NUMBER> --json headRefOid --jq .headRefOid   # compare to the head recorded in Phase 1
gh pr diff <PR_NUMBER> --name-only
```

If the base or PR head moved, or files appeared that agents were never given, drop findings whose files are outside the reviewed scope and note the drop in the review document. Findings against files that were never in the branch are worse than noise — they read as real defects and cost a reviewer's trust. In one observed case two findings rested entirely on such phantom content and survived only because two reviewers' diffs were cross-checked by hand during consolidation.

### Step 1: Calibration

Spawn **`jbb-feature-dev:review-calibrator`** with ALL findings from Phase 2.

The calibrator performs adversarial verification (reads actual code to validate each finding) and calibration (categorizes, filters false positives, normalizes severity, assigns confidence).

Timeout: 2 minutes. If timeout: skip calibration, proceed with raw findings.

### Step 2: Severity Filter

Apply severity filter based on `source_agent` and flags:

**Default behavior** (no flags):

- For findings from **code style reviewers** (agents whose name contains `code-style`): keep ALL severities including ENHANCEMENT
- For findings from **test reviewers** (agents whose name contains `test-reviewer`): keep ALL severities including ENHANCEMENT, but skip LOW findings the reviewer considers unhelpful (e.g., testing static mappings, framework behavior, or language implementation details)
- For all other agents: keep MEDIUM, HIGH, and CRITICAL findings

**Flag overrides**:

- `--strict-severity`: Keep only HIGH and CRITICAL for ALL agents, including code style and test reviewers
- `--all-severities`: Keep all findings from all agents regardless of severity
- `--severity LEVELS`: Keep only the specified severity levels from all agents (e.g., `--severity MEDIUM,HIGH,CRITICAL`)

The test and code style exemptions exist because test coverage gaps and code quality improvements are valuable even at ENHANCEMENT/LOW/MEDIUM severity — they compound over time and are frequently raised by human reviewers. ENHANCEMENT findings represent aspirational improvements (modernization, better patterns, reusable helpers) that aren't tied to a specific problem but improve code quality over time. The MEDIUM default for other agents ensures findings like PII-in-logs, pattern inconsistencies, and missing error handling are surfaced rather than silently filtered. Use `--strict-severity` when you only care about correctness and security.

**Severity bypass**: Findings from `repo-rules-reviewer` (identified by `source_agent` field) bypass the severity filter entirely — they are always included in the output regardless of the active severity mode.

### Step 3: Deduplication

Spawn **`jbb-feature-dev:review-deduplicator`** with calibrated, filtered findings.

The deduplicator handles same-file, cross-file, adjacent-line consolidation and removes findings already covered by human reviewers.

When spawning the deduplicator, also pass:

- Prior review findings from `~/.claude/thoughts/shared/reviews/` if a previous review exists (from Phase 1 step 2d), for Step 6
- The `changed_locations_since_prior` map pre-computed in Phase 1 step 2d, for Step 6
- Human PR review comments fetched in Phase 1 step 2f, for Steps 4 and 7

Timeout: 2 minutes. If timeout: skip dedup, proceed with calibrated findings.

### Step 4: Quality Check

Spawn **`jbb-feature-dev:quality-checker`** with the deduplicated findings and the original diff embedded in its prompt.

The quality checker evaluates the review on 6 dimensions (see `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/quality-check-dimensions.md`). This is a single-pass evaluation — no iterative loop.

If the quality checker flags findings for removal, it outputs a structured "Findings to remove" list where each entry is identified by the tuple `(source_agent, file_path, position)`. The orchestrator matches these tuples against the deduplicated findings list and removes matches before proceeding to Phase 4.

Timeout: 1 minute. If timeout: skip quality check, proceed with deduplicated findings.

## Phase 4: Generate Review Document

### Write review document

Ensure output directory exists: `mkdir -p ~/.claude/thoughts/shared/reviews/`

Write to `~/.claude/thoughts/shared/reviews/review_{{PR_NUMBER}}_{{DATE}}.md`:

```markdown
# [PR #{{PR_NUMBER}}: {{PR_TITLE}}] Review

## High level summary

[2-3 sentences summarizing findings]

## Do the code changes align with the PR objective?

["Yes" or "No" with explanation]

## Highlights

- [Positive patterns and well-executed implementations]

## Review Sources

| Source                                | Status            | Findings        |
| ------------------------------------- | ----------------- | --------------- |
| bug-catcher                           | Completed         | N findings      |
| security-reviewer                     | Completed         | N findings      |
| repo-rules-reviewer                | Completed/Skipped | N findings      |
| [language]-expert (code-style-review) | Completed         | N findings      |
| [language]-expert (test-review)       | Completed         | N findings      |
| general-code-reviewer                 | Completed         | N findings      |
| repo-rules-reviewer                   | Completed         | N findings      |
| review-calibrator                     | Completed/Skipped | Filtered M of N |
| review-deduplicator                   | Completed/Skipped | Deduped to K    |
| quality-checker                       | Completed/Skipped | Removed M of N  |

## Incremental Review Status

[Only included if --incremental was used]

- Prior review: `review_{{PR_NUMBER}}_{{PRIOR_DATE}}.md`
- Commits reviewed previously: [range]
- New commits since prior review: [range]
- New findings (not in prior review): [count]
- Previously identified (still open): [count]
- Resolved since prior review: [count]

## Existing PR Comments Assessment

[Only included if human PR review comments exist]

[agree/disagree reasoning from review-deduplicator Step 7 for each human reviewer comment]

## Prioritized Issues

### Critical

[Findings]

### Major

[Findings]

### Minor

[Findings]

### Enhancement

[Findings]
```

Each finding includes: `- Recommendation [i] - \`file_path:line\``

## Combined-invocation fallback

When parallel-spawn flakiness blocks the dual-invocation pattern (issue #7406), fall back to a single sequential combined invocation.

```pseudo
spawn {language}-expert ONCE with prompt = test-review framing + "---END-PASS-1---" + code-style-review framing
receive single response containing both pass outputs
split response on "---END-PASS-1---"
route pass-1 half to review-deduplicator tagged source_agent={language}-expert mode=test-review
route pass-2 half to review-deduplicator tagged source_agent={language}-expert mode=code-style-review
```

Wall-clock cost: ~2× single-pass duration (sequential rather than concurrent). Activated only by explicit operator decision (e.g., `/code-review --combined-invocation`); never automatic. Reference: parallel-spawn flakiness tracked in issue #7406; verify the skill-injection canary from issue #25834 still echoes correctly in the combined prompt.

## Notes

- This is a READ-ONLY review. Never modify code files.
- Read all context documents fully (no limit/offset parameters)
- Phase 1 MUST complete before Phase 2 (context informs review)
- Phase 2 agents run in parallel; Phase 3 agents run sequentially
- All review agent prompts MUST include Phase 1 findings and shared reference content
- Finding schema is the contract between Phase 2 and Phase 3
- Severity filter is applied between calibration and deduplication
- File path and line number references enable automated PR comment submission via `/crit-pr-review`
- For sub-agent model selection guidance, see `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/model-selection-guide.md`
- Repo-rules-reviewer findings bypass the severity filter (always included)
- Quality checker runs as a single-pass gate after deduplication
- `--incremental` reviews only new commits since the last review for this PR
- File exclusions from .gosling.yaml/.code-review.yaml are applied before Phase 2
