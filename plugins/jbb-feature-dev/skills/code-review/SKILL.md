---
name: code-review
description: >
  Comprehensive code review with internalized bug detection (bug-catcher), OWASP security
  analysis (security-reviewer), repo-declared rules (repo-rules-reviewer), code
  style (language reviewers), test quality (test reviewers), holistic review
  (general-code-reviewer), domain expertise (domain agents), and a post-review pipeline
  (review-calibrator, review-deduplicator). Use when the user asks to "review my code",
  "review this PR", "code review", or says "/code-review".
argument-hint: "[pr-number-or-branch] [--all-severities] [--strict-severity] [--severity LEVELS] [--incremental] [--non-interactive]"
---

# Code Review

Conduct a comprehensive code review using specialized agents and a post-review calibration/dedup pipeline.

**IMPORTANT**: This is a read-only review command, including for the caller's own work. Reviewers report findings; the caller applies accepted findings only within its edit authorization. Reviewing a colleague's PR never authorizes edits, commits, branch switches, or posting comments.

Use this skill's existing specialist agents and post-review agents for independent assessment. Do not add an outer wrapper solely to invoke the skill. A session that implements or simplifies the change may coordinate and apply findings, but must not assess or grade its own work. If an independent assessment agent is unavailable, record that pass as blocked rather than replacing it with implementer self-review.

## Arguments

- First argument: a bare PR number or branch name (optional -- prompts if missing, unless `--non-interactive`). Never a PR URL. The skill operates on an already-checked-out repo; it does not clone.
- `--all-severities`: Show all findings including LOW/MEDIUM for all agents
- `--strict-severity`: Keep only HIGH+CRITICAL for ALL agents including code simplification and test reviewers (overrides the default MEDIUM+ and ALL-severity exemptions)
- `--severity LEVELS`: Comma-separated severity levels to include (e.g., `--severity MEDIUM,HIGH,CRITICAL`)
- `--incremental`: Review changes since the prior recorded snapshot, including relevant local work for a local scope. Outputs "New findings" separately from "Previously identified".
- `--non-interactive`: Never prompt. Resolve the review scope automatically (see Phase 1 step 1) and record the resolved scope in the review document. Unattended callers pass this when no user can answer a prompt; unresolved scope must report blocked rather than stall on an unseen question.

**Default severity behavior**: MEDIUM+HIGH+CRITICAL for most agents, **except** code style and test reviewers which keep ALL severities (test reviewers skip LOW findings they consider unhelpful). Use `--strict-severity` to enforce HIGH+CRITICAL across every dimension.

## Review effort policy

This section is canonical for callers selecting code-review effort. Select it after implementation and any simplification, from the actual diff and consequences, not an intake risk label. Reassess after material changes.

| Actual change and risk | Requested effort |
| --- | --- |
| A few locally verifiable, low-risk lines | low |
| Ordinary module work | medium |
| Production writes or weakened checks | high |
| Security boundaries or behavior that cannot be verified locally | xhigh, only if supported |

Use the highest applicable risk. Use `max` only when explicitly requested. Effort controls reasoning depth; model selection chooses the model. Preserve the specialist roster and dual language modes at every effort level. Follow `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/model-selection-guide.md` for model selection rather than replacing specialists with one stronger reviewer.

Check the installed Claude Code controls with `claude --help` before applying effort. When it advertises `--effort`, a caller starting a review session can set that session's effort with this flag. Use only levels supported by that installation and selected model; use `high` and record the limitation when `xhigh` is unavailable. Do not invent an `effort` parameter on the Agent tool, confuse its `model` parameter with effort, or treat prompt wording as a runtime setting. For an existing session or child agent, verify the documented control or inheritance before claiming effort is applied. If no supported control exists, retain the configured setting and report the requested effort as unapplied.

Record the diff-based reason, requested effort, effective setting or limitation, and model separately in the review document and agent brief.

## Phase 1: Context Gathering (parallel)

1. **Establish objective and boundaries**: Confirm repository root, branch, worktree, PR or supplied base, and ownership. State the objective and acceptance criteria from the conversation, PR body, linked task, or approved plan. Follow objective links once with available tools; list sources and unavailable context. Do not select an unrelated plan because it is newest. Investigate affected code, callers, consumers, tests, and existing helpers before judging alignment.

   Resolve missing scope from the current branch and task's actual target branch, not a guessed `master` or `main`. Honor a supplied base. In interactive mode, ask if the objective or target remains unclear. With `--non-interactive`, record unresolved scope as blocked; if only the objective is unavailable, mark it unknown and omit the alignment verdict. Record out-of-scope dirty work without editing it.

2. **Capture the actual review input without changing the checkout**:
   - **PR review**: Read PR metadata, base/head SHAs, and `gh pr diff {{PR_NUMBER}}`. Verify on-disk files match that head and have no local changes in scope before giving them to agents. If they do not match, read source at the recorded PR head through repository tools, or have the caller supply an isolated matching checkout. Never switch branches, pull, stash, or overwrite dirty work to perform a review. A colleague's PR stays read-only. Local changes are not part of a remote PR unless explicitly requested as a separate local scope.
   - **Local branch or working-tree review**: Use the supplied base SHA, or record the merge base with the verified target branch once. Inspect the cumulative diff from that base through the current working tree, including staged and unstaged changes even when committed changes also exist. List untracked files separately and read relevant ones in full. Do not substitute the implementer's summary for these inputs.

     After substituting the recorded base SHA, capture the candidate file lists in one block. Shell state does not persist across tool calls:

     ```bash
     BASE=$(git rev-parse --verify '{{RECORDED_BASE_SHA}}^{commit}') || exit 1
     FILES=$(git diff --name-only "$BASE" --) || exit 1
     UNTRACKED=$(git ls-files --others --exclude-standard) || exit 1
     MODE="local diff"
     if [ -z "$FILES" ] && [ -z "$UNTRACKED" ]; then
       MODE="none"
     fi
     printf 'MODE=%s\nBASE=%s\nFILES:\n%s\nUNTRACKED:\n%s\n' "$MODE" "$BASE" "$FILES" "$UNTRACKED"
     git diff --binary "$BASE" --
     ```

     Filter these candidates to the objective and explicit scope, and log exclusions. If only irrelevant untracked files remain, there is nothing in scope to review. **An empty scope is a stop, not a pass**: never emit a clean severity count for an unreviewed change.

   - **Record a shared snapshot**: Save root, branch, target branch, mode, objective, acceptance criteria, base/head SHAs, resolved file list, exact diff, and relevant untracked file contents or content hashes in the review artifact. For untracked files, construct added-file hunks for anchoring findings. All agents use this same snapshot, not a live revision expression. Record the effort decision from the policy above after inspecting these inputs.

   **2b. Check for file exclusion config** (Gap 2): Look for `.code-review.yaml` in the repo root. If found, read `exclude_files` glob patterns and filter the diff to remove matching files before any review agents see them. Log which files were excluded.

   **2c. Check for large PR** (Gap 3): Estimate token count of the diff. If the diff exceeds ~50K tokens:
   - Warn the user: "This is a large PR (~N tokens). Review quality may be reduced."
   - Suggest splitting: Analyze the diff for independent modules/directories and suggest logical split points
   - Do not create a quality finding from size alone. Explain concrete responsibility or review-coverage problems if the diff demonstrates them.
   - Continue with the review (do not abort)

   **2d. Check for incremental mode** (Gap 7): If `--incremental` flag is set:
   - Search `~/.claude/thoughts/shared/reviews/` for a previous review document matching this PR number
   - If found: identify the prior reviewed snapshot and compute changes since it. Include relevant staged, unstaged, and untracked work for a local scope, even when no new commit exists. If the prior local snapshot is unavailable, review the full current scope and state that limit.
   - Store the FULL PR diff separately (for repo-rules-reviewer)
   - Replace the default diff with the incremental diff for most Phase 2 agents
   - Pre-compute `changed_locations_since_prior`: a map of files and line ranges modified since the last review commit. Pass this to the deduplicator in Phase 3.
   - Store the prior review findings for the deduplicator
   - If no previous review found: warn and proceed normally

   **2e. Discover repo-specific coding guidelines** (Gap 1): Search the repository for AGENTS.md, CLAUDE.md and other coding guideline sources:
   - Check for AGENTS.md and CLAUDE.md at repo root and subdirectories
   - Search for: CONTRIBUTING.md, style guides, .editorconfig, lint configs, README sections about coding standards
   - Store discovered guidelines for: (a) the repo-rules-reviewer agent, (b) all other review agents as informational context

   **2f. Fetch human PR review comments** (Gap 5): If reviewing a PR:
   - Fetch existing human review comments via `gh api repos/{owner}/{repo}/pulls/{number}/comments` (add `--hostname <host>` for a GitHub Enterprise repo)
   - Also fetch review-level comments via `gh api repos/{owner}/{repo}/pulls/{number}/reviews` (same host rule)
   - Store for the deduplicator in Phase 3

3. **Identify languages**: Analyze diff for file extensions. Look up in `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md`
4. **Detect domains**: Follow the detection procedure in `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` — check changed file names/paths against file triggers first (deterministic), then check diff content for strong and corroborating signals
5. **Spawn context agents in parallel**:
   - `codebase-explorer` (subagent_type: `Explore`): Find patterns, conventions, CLAUDE.md, and reusable helpers, types, constants, and components in the target repo. Compare repeated decision rules within the new diff as well as existing code. **Critically**: identify sibling implementations — other classes/methods in the same package or system that implement the same interface, extend the same base class, or follow the same architectural pattern as the code under review (e.g., other handlers in the same service, other endpoints in the same API). Read their key methods to understand what patterns they follow (error handling, graceful degradation, field usage, logging practices).
   - `jbb-feature-dev:web-search-researcher` (if a third-party framework or library is central to the change): Research its current documented best practices
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

- The recorded root, branch, target branch, base/head SHAs, objective, acceptance criteria, and scope boundaries
- The actual diff, including relevant uncommitted and untracked work for a local scope
- The effort decision and effective runtime setting or limitation, separate from model selection
- Context findings from Phase 1 (patterns, conventions, ops context)
- Sibling implementation context from Phase 1 (if found) — include file paths and key patterns (error handling, field usage, graceful degradation) so agents can flag inconsistencies between the new code and established sibling patterns
- Shared reference content (false-positive guidance, position anchoring, severity rubric, comment format, finding schema)

Each agent confirms its root and branch, reads full changed files plus relevant callers and siblings, and reports evidence against the shared snapshot. Record the actual assessor, input state, instructions actually read, and evidence in the existing review document. A finding quotes the changed line, names the violated rule or contract, states the concrete consequence, and suggests a fix. Zero findings is valid; do not pad. Separate missing evidence from a clean result.

Parallel work is source inspection. Only bug-catcher may run safe isolated local probes under
[bug-review](../bug-review/SKILL.md); include that contract in its brief, without spawning another bug worker.
Other reviewers return proposed build/test commands instead of running them against shared outputs.
After assessments, the coordinator runs needed shared checks once, sequentially and without changing reviewed source,
or arranges explicit safe serialization. Keep existing calibrator source checks; they do not build or run tests.

### Code-quality assessment contract

Assign these checks to the existing reviewers below, without adding a separate assessment wrapper:

- **bug-catcher**: Trace accepted boundary inputs through coupled calculations, thresholds, classifications, callers, and consumers. Check malformed present data and unknown values do not silently become normal absence or weaker checks. Compare changed behavior with error messages, comments, schema/proto contracts, and actual input formats. A passing test does not disprove a demonstrated bug.
- **general-code-reviewer**: Check objective alignment and scope, including missing behavior and unrequested features or refactors. Check hidden assumptions about units, ordering, uniqueness, and absent values. Identify unused abstractions, impossible-state fallbacks, symptom fixes, and duplicated framework guarantees. Report performance only with a concrete consequence at realistic scale.
- **language experts, test-review**: Check whether subtly broken behavior still passes, assertions weaken, mocks replace the unit under test, or fixtures add dead setup. Prefer assertions on existing scenarios where sufficient. Flag tests of static mappings, configuration, language internals, or framework behavior rather than conditional business behavior.
- **language experts, code-style-review**: Search existing code and the new diff for reusable helpers, types, constants, and matching decision rules. Name both duplicate locations; share the operation only when semantics match. Check collection mutability against contracts and callers. Make decisions visible through meaningful names, types, and focused structure, not dense expressions, shortest code, line counts, or helpers that merely rename syntax. Judge comments with surrounding logic; use the mode's naming/comment boundaries and preserve tool directives and necessary contracts.

Spawn review agents in parallel:

- **`jbb-feature-dev:bug-catcher`** (always) -- Bug detection specialist
- **`jbb-feature-dev:security-reviewer`** (always) -- OWASP security analysis
- **Language expert agent** (per detected language, from language-agent-registry: `jbb-feature-dev:python-expert`, `jbb-feature-dev:typescript-expert`) -- spawned TWICE in parallel per language: once with test-review mode framing, once with code-style-review mode framing. See "Dual parallel spawn pattern" below.
- **`jbb-feature-dev:general-code-reviewer`** (always) -- Holistic review with ops context and the objective/scope checks above. Check clear responsibilities and comprehension, not file length as a proxy for quality. If an approved plan supplies file boundaries, verify those boundaries against the actual change.
- **Domain experts** (if detected from domain-agent-registry; spawned in parallel ALONGSIDE language experts when both apply — overlapping language + workflow domain coverage spawns BOTH the language expert AND the matching workflow domain expert concurrently)
- **`jbb-feature-dev:repo-rules-reviewer`** (always, but returns empty if no guidelines found) -- Enforces repo-specific coding rules from AGENTS.md, CLAUDE.md and other discovered guidelines. Pass the discovered guidelines from Phase 1 step 2e as the agent's primary input. Pass guidelines as informational context to ALL other review agents as well. **Incremental mode note**: repo-rules-reviewer always receives the FULL PR diff (not the incremental diff), because repo rules apply to all changed code regardless of when commits were made.

### Dual parallel spawn pattern

For each language detected in scope, spawn the corresponding `{language}-expert` agent TWICE in parallel:

1. **test-review framing** — invoke the agent with mode = `test-review`. Output schema: `TEST NEEDED`, `REDUNDANT TEST`, `QUALITY ISSUE` blocks (per `code-review-modes/SKILL.md`).
2. **code-style-review framing** — invoke the agent with mode = `code-style-review`. Output schema: `ISSUE` blocks (per `code-review-modes/SKILL.md`).

Both invocations MUST run concurrently (single message containing both Agent tool calls). Each emits its own per-mode block schema. Downstream `review-deduplicator` (Phase 3 Step 3) consolidates overlapping findings between the two passes and merges adjacent-line duplicates.

**Set the `mode` field on every finding as you collect it** — `test-review` or `code-style-review`, per `finding-schema.md`. You set it, not the agent: both invocations report the same `source_agent` (e.g. `python-expert`), so the agent cannot know which one it is. Every other agent's findings carry `mode: null`. A finding collected without `mode` loses its ALL-severity exemption at Step 2; see `finding-schema.md` `### mode` for the defect this caused.

**Skill-injection canary** (issue #25834): the silent skill-injection failure mode in plugin issue #25834 means a spawned agent may receive an empty skill body without any error surfaced. Each mode-framed prompt MUST include a canary token (e.g., `MODE_CANARY=test-review-v1`) that the agent is instructed to echo verbatim in its first output line. The orchestrator verifies the echo before accepting findings; absence of the canary indicates the skill content did not reach the agent and the invocation is retried with explicit inline content rather than skill reference.

When both a language expert and a workflow domain expert apply to the same diff (e.g., Python + ML model training code), spawn BOTH in parallel — they cover orthogonal axes (general language quality vs. workflow-specific best practices) and their findings are merged by the deduplicator.

All agents MUST emit findings using the schema defined in `finding-schema.md`:

```
file_path, position, body, severity, category, confidence, source_agent, mode
```

Wait for all review agents to complete. Collect findings, material unresolved concerns, and coverage separately.
Keep every candidate's outcome and evidence in the existing review document through calibration, filtering,
deduplication, and quality checking, including reasons for removal and links to surviving duplicates.
A severity filter controls presentation, not validity or resolution. Return these outcomes to the caller;
code-review remains read-only and does not apply recommendations.
Report an incomplete review, not an unqualified clean verdict, while material concerns or required coverage remain unresolved.

## Phase 3: Post-Review Pipeline (sequential)

### Step 0: Re-verify the review scope

Before calibration, compare the current input with the Phase 1 snapshot. Read recorded values from the artifact, not shell variables from earlier calls.

For local scope, repeat Phase 1's capture with the same recorded base SHA. Compare HEAD, exact diff contents, relevant untracked contents or hashes, and file list. A same-file edit matters even when names and HEAD stay unchanged. Do not recompute a moving target branch's merge base as a replacement for the pinned base.

For a PR, re-read its base/head SHAs and diff through the same repository tools. If the reviewed input changes, repeat affected assessments against a fresh shared snapshot before a current-scope verdict. If that is unavailable, mark the review incomplete. Drop findings outside the reviewed scope, but never treat dropping stale findings as proof the new content is reviewed.

### Step 1: Calibration

Spawn **`jbb-feature-dev:review-calibrator`** with ALL findings from Phase 2, the objective, scope, and shared snapshot. Supply the same assessment brief to the deduplicator and quality checker; the implementer never substitutes its own grade for these agents.

Also supply unresolved concerns, coverage limits, and probe evidence as context, not admitted findings.
Preserve the calibrator's false-positive and confidence checks. Require evidence for an invalid premise or
inapplicability when rejecting a candidate. Missing context or execution is a limit, not disproof.
Retain consequential NEEDS-CONTEXT or insufficient-evidence candidates as material unresolved concerns, not admitted findings.
Carry those concerns separately through later filters; their absence from findings cannot establish clean coverage.

The calibrator performs adversarial verification (reads actual code to validate each finding) and calibration (categorizes, filters false positives, normalizes severity, assigns confidence).

Timeout: 2 minutes. If timeout: skip calibration, proceed with raw findings.

### Step 2: Severity Filter

Apply severity filter based on `source_agent` and flags:

**Default behavior** (no flags):

- `mode == "code-style-review"`: keep ALL severities including ENHANCEMENT
- `mode == "test-review"`: keep ALL severities including ENHANCEMENT, but skip LOW findings recommending tests
  that only restate static mappings, static configuration, language internals, or framework/library behavior
  (e.g., `case X -> "Y"` returns `"Y"`). Keep findings recommending removal or replacement of those tests.
  Tests of conditional business behavior that could realistically have bugs are valuable.
- `mode == null` (every other agent): keep MEDIUM, HIGH, and CRITICAL findings

**Compare `mode` by equality against those two literal values.** Never match a substring, and never key off the agent name — `finding-schema.md` `### mode` records why both fail, and that a substring fix silently works for one mode and not the other.

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

## Objective, scope, and review effort

[Objective and acceptance criteria, sources, root/branch/worktree, target branch, ownership, mode, pinned base/head SHAs, reviewed files, exclusions, and snapshot location]

[Diff-based risk reason, requested effort, effective runtime setting or limitation, and model]

## Do the code changes align with the PR objective?

[Aligned / partially aligned / not aligned, with evidence; unknown if the objective is unavailable]

## Highlights

- [Positive patterns and well-executed implementations]

## Review Sources

| Source                                | Status            | Findings        |
| ------------------------------------- | ----------------- | --------------- |
| bug-catcher                           | Completed         | N findings      |
| security-reviewer                     | Completed         | N findings      |
| [language]-expert (code-style-review) | Completed         | N findings      |
| [language]-expert (test-review)       | Completed         | N findings      |
| general-code-reviewer                 | Completed         | N findings      |
| repo-rules-reviewer                   | Completed         | N findings      |
| review-calibrator                     | Completed/Skipped | Filtered M of N |
| review-deduplicator                   | Completed/Skipped | Deduped to K    |
| quality-checker                       | Completed/Skipped | Removed M of N  |

## Candidate outcomes and coverage limits

[Every recorded candidate's outcome and reason, including rejected, filtered, duplicate, skipped, and blocked candidates.
Keep material unresolved concerns and missing execution/context separate from admitted findings.
For each Review Source above, record the actual assessor, input state, instructions actually read, and evidence.]

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

Each finding includes: `- Recommendation [i] - \`file_path:line\``, the quoted line, rule or contract, consequence, and suggested fix. List blocked assessments and verification limits before any clean verdict. Return findings to the caller; do not apply them. For a colleague's PR, provide an approval recommendation with reasons and draft comments only, never post them.

## Combined-invocation fallback

When parallel-spawn flakiness blocks the dual-invocation pattern (issue #7406), fall back to a single sequential combined invocation.

```pseudo
spawn {language}-expert ONCE with prompt = test-review framing + "---END-PASS-1---" + code-style-review framing
receive single response containing both pass outputs
split response on "---END-PASS-1---"
route pass-1 half to review-deduplicator with source_agent={language}-expert, mode="test-review"
route pass-2 half to review-deduplicator with source_agent={language}-expert, mode="code-style-review"
```

Wall-clock cost: ~2× single-pass duration (sequential rather than concurrent). Activated only by explicit operator decision (e.g., `/code-review --combined-invocation`); never automatic. Reference: parallel-spawn flakiness tracked in issue #7406; verify the skill-injection canary from issue #25834 still echoes correctly in the combined prompt.

## Notes

- This is a READ-ONLY review. Never modify code files.
- Read all context documents fully (no limit/offset parameters)
- Phase 1 MUST complete before Phase 2 (context informs review)
- Phase 2 agents run in parallel; Phase 3 agents run sequentially
- All review agent prompts MUST include Phase 1 findings and shared reference content
- Finding schema is the contract between Phase 2 and Phase 3; `mode` is set by the orchestrator on collection, not by the agent
- Severity filter is applied between calibration and deduplication
- File path and line number references enable automated PR comment submission via `/crit-pr-review`
- For sub-agent model selection guidance, see `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/model-selection-guide.md`
- Repo-rules-reviewer findings bypass the severity filter (always included)
- Quality checker runs as a single-pass gate after deduplication
- `--incremental` uses the prior recorded snapshot; missing snapshot evidence requires a full current-scope review
- File exclusions from .code-review.yaml are applied before Phase 2
