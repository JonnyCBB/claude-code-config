---
name: code-review
description: Comprehensive code review with internalized bug detection (bug-catcher), OWASP security analysis (security-reviewer), code simplification (language reviewers), test quality (test reviewers), holistic review (general-code-reviewer), domain expertise (domain agents), and a post-review pipeline (review-calibrator, review-deduplicator). Replaces /pr-review.
argument-hint: "[pr-number-or-branch] [--all-severities] [--strict-severity] [--severity LEVELS]"
---

# Code Review

Conduct a comprehensive code review using specialized agents and a post-review calibration/dedup pipeline.

**IMPORTANT**: This is a review command. DO NOT make any code changes. Only provide constructive, actionable recommendations.

## Arguments

- First argument: PR number or branch name (optional -- prompts if missing)
- `--all-severities`: Show all findings including LOW/MEDIUM for all agents
- `--strict-severity`: Keep only HIGH+CRITICAL for ALL agents including code simplification and test reviewers (overrides the default MEDIUM+ and ALL-severity exemptions)
- `--severity LEVELS`: Comma-separated severity levels to include (e.g., `--severity MEDIUM,HIGH,CRITICAL`)

**Default severity behavior**: MEDIUM+HIGH+CRITICAL for most agents, **except** code simplification and test reviewers which keep ALL severities (test reviewers skip LOW findings they consider unhelpful). Use `--strict-severity` to enforce HIGH+CRITICAL across every dimension.

## Phase 1: Context Gathering (parallel)

1. **Determine what to review**: If user provided PR number or branch, use that. Otherwise check current branch and ask.
2. **Get the diff**: `gh pr diff {{PR_NUMBER}}` for PRs, or `git diff origin/master...HEAD` for branches
3. **Identify languages**: Analyze diff for file extensions. Look up in `${CLAUDE_PLUGIN_ROOT}/commands/shared/language-agent-registry.md`
4. **Spawn context agents in parallel**:
   - `codebase-explorer` (subagent_type: Explore): Find patterns, conventions, CLAUDE.md in the target repo. **Critically**: identify sibling implementations — other classes/methods in the same package or system that implement the same interface, extend the same base class, or follow the same architectural pattern as the code under review (e.g., other handlers in the same service, other endpoints in the same API). Read their key methods to understand what patterns they follow (error handling, graceful degradation, field usage, logging practices).
5. **Read shared reference files**: Load these into context for injection into Phase 2 prompts:
   - `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/false-positive-guidance.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/position-anchoring.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/severity-rubric.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/comment-format.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/finding-schema.md`
6. Wait for all context agents to complete

## Phase 2: Review Agents (parallel, informed by Phase 1)

**Agent Type Verification**: Before spawning, create an explicit agent contract per `${CLAUDE_PLUGIN_ROOT}/commands/shared/agent-verification-pattern.md`.

Construct prompts for each agent, injecting:

- The diff
- Context findings from Phase 1 (patterns, conventions, ops context)
- Sibling implementation context from Phase 1 (if found) — include file paths and key patterns (error handling, field usage, graceful degradation) so agents can flag inconsistencies between the new code and established sibling patterns
- Shared reference content (false-positive guidance, position anchoring, severity rubric, comment format, finding schema)

Spawn review agents in parallel:

- **bug-catcher** (always) -- Bug detection specialist
- **security-reviewer** (always) -- OWASP security analysis
- **Language-specific code simplification reviewer** (from language-agent-registry)
- **Language-specific test reviewer** (from language-agent-registry)
- **general-code-reviewer** (always) -- Holistic review with ops context. Additionally check: (1) Did any existing file grow by more than 200 new lines? (2) Are any new files already over 500 lines? (3) Does each changed file maintain a single clear responsibility? If a plan was provided in the PR description, verify the changes follow the planned file structure.

All agents MUST emit findings using the schema defined in `finding-schema.md`:

```
file_path, position, body, severity, category, confidence, source_agent
```

Wait for all review agents to complete. Collect all findings into a consolidated list.

## Phase 3: Post-Review Pipeline (sequential)

### Step 1: Calibration

Spawn **review-calibrator** with ALL findings from Phase 2.

The calibrator performs adversarial verification (reads actual code to validate each finding) and calibration (categorizes, filters false positives, normalizes severity, assigns confidence).

Timeout: 2 minutes. If timeout: skip calibration, proceed with raw findings.

### Step 2: Severity Filter

Apply severity filter based on `source_agent` and flags:

**Default behavior** (no flags):

- For findings from **code simplification reviewers** (agents whose name contains `simplification`): keep ALL severities including ENHANCEMENT
- For findings from **test reviewers** (agents whose name contains `test-reviewer`): keep ALL severities including ENHANCEMENT, but skip LOW findings the reviewer considers unhelpful (e.g., testing static mappings, framework behavior, or language implementation details)
- For all other agents: keep MEDIUM, HIGH, and CRITICAL findings

**Flag overrides**:

- `--strict-severity`: Keep only HIGH and CRITICAL for ALL agents, including code simplification and test reviewers
- `--all-severities`: Keep all findings from all agents regardless of severity
- `--severity LEVELS`: Keep only the specified severity levels from all agents (e.g., `--severity MEDIUM,HIGH,CRITICAL`)

The test and simplification exemptions exist because test coverage gaps and code quality improvements are valuable even at ENHANCEMENT/LOW/MEDIUM severity — they compound over time and are frequently raised by human reviewers. ENHANCEMENT findings represent aspirational improvements (modernization, better patterns, reusable helpers) that aren't tied to a specific problem but improve code quality over time. The MEDIUM default for other agents ensures findings like PII-in-logs, pattern inconsistencies, and missing error handling are surfaced rather than silently filtered. Use `--strict-severity` when you only care about correctness and security.

### Step 3: Deduplication

Spawn **review-deduplicator** with calibrated, filtered findings.

The deduplicator handles same-file, cross-file, adjacent-line consolidation and removes findings already covered by human reviewers.

Timeout: 2 minutes. If timeout: skip dedup, proceed with calibrated findings.

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

| Source                    | Status            | Findings        |
| ------------------------- | ----------------- | --------------- |
| bug-catcher               | Completed         | N findings      |
| security-reviewer         | Completed         | N findings      |
| [language]-simplification | Completed         | N findings      |
| [language]-test-reviewer  | Completed         | N findings      |
| general-code-reviewer     | Completed         | N findings      |
| review-calibrator         | Completed/Skipped | Filtered M of N |
| review-deduplicator       | Completed/Skipped | Deduped to K    |

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

## Notes

- This is a READ-ONLY review. Never modify code files.
- Read all context documents fully (no limit/offset parameters)
- Phase 1 MUST complete before Phase 2 (context informs review)
- Phase 2 agents run in parallel; Phase 3 agents run sequentially
- All review agent prompts MUST include Phase 1 findings and shared reference content
- Finding schema is the contract between Phase 2 and Phase 3
- Severity filter is applied between calibration and deduplication
- File path and line number references enable automated PR comment submission via `/crit-pr-review`
- For sub-agent model selection guidance, see `${CLAUDE_PLUGIN_ROOT}/commands/shared/model-selection-guide.md`
