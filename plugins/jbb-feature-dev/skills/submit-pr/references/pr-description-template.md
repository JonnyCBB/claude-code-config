# PR Description Template

Use this reference for template discovery, body structure, and objective-based verification evidence.
Apply `pr-prose-rules.md` to authored prose, not verbatim evidence.

## Template Discovery

Use the `codebase-explorer` agent to find repository pull request templates.
Search these paths in order:

1. `.github/pull_request_template.md`
2. `.github/PULL_REQUEST_TEMPLATE.md`
3. `.github/PULL_REQUEST_TEMPLATE/` (read the available Markdown templates and select the relevant one)
4. `docs/pull_request_template.md`
5. `PULL_REQUEST_TEMPLATE.md`

Read the selected template in full. Keep its headings, formatting, and required sections.
Map Why to Summary or Context, What to Changes, and Links to References.
Insert architecture diagrams before Testing or Checklist when diagram generation applies.
Insert Stack after the closest Summary or Context section when stacked-PR mode applies.
Always include Testing & Verification content in the closest matching section, or add one if none exists.

Use the default structure below when no repository template exists.

## Default PR Description Format

Aim for at most 30 visible lines on a typical change, excluding collapsible details.
Move long evidence into collapsibles. Never remove required evidence to meet the visible-body budget.

### Title

Use a concise, outcome-focused title under 72 characters.
Use imperative wording, such as "Fix empty-input handling".
Include measured impact only when evidence supports it.

### Why

Use 1-3 sentences to state the objective and problem.
Use requirements, user input, tickets, or commit context as sources.
Never invent motivation. If the reason is unknown, state the factual behavior and the missing context.

### What

Use brief bullets to explain behavior that reviewers need before reading code.
Keep summaries that connect the objective to verification, even when the diff also shows that behavior.
Omit mechanical file inventories and duplicate implementation detail.

Add conditional callouts at the top of What when Phase 1 auto-detection applies (see Phase 1 auto-detection in `SKILL.md`):

- `**Breaking change**: <effect>`
- `**Feature flag**: <exact identifier> default <value>`
- `**Migration**: <required action>`
- `<!-- screenshot recommended -->` when UI changes lack a screenshot

### Links

Include relevant Jira tickets, related PRs, and reviewer-accessible design documents.
Never point reviewers to author-only files or notes.

### Stack

Include this section only in stacked-PR mode.
Explain that reviewers review the PRs in dependency order.
Use real PR numbers captured during creation. Bold the current PR's row.

| Order | PR | Base | Status |
| ----- | -- | ---- | ------ |
| <order> | <PR link and title> | <base branch> | <draft, open, or merged> |

### Architecture Overview

Include this section only when diagram generation applies and `--no-diagram` is absent.
Insert the generated diagram and a short caption explaining the relevant flow.

### Testing & Verification

Always include this section, even without a verification report or running service.
Lead with a short behavioral result and state important unverified limits.
Then include the evidence format below.

Behavioral unit-test evidence is valid when it explains the objective, especially for pure libraries.
Do not substitute routine test counts, coverage totals, or generic CI success for behavioral evidence.
A local behavioral result does not replace latest-head remote CI or review.

## Verification Results Embedding

### Select and validate evidence

Use `--verification <path>`, an artifact explicitly linked by the task, or direct verification from this task.
When searching `~/.claude/thoughts/shared/verification/`, select only a report that matches the repository, branch, objective, and current change.
Never select a report because it is the newest file in a shared directory.
An explicit path does not bypass these checks. If multiple matching reports conflict, report the conflict instead of guessing.

Check the repository, branch, objective, tested commit, and relevant working-tree changes against the submitted head.
Record the tested commit and environment in the PR body without author-only pointers.
If provenance is missing or the tested commit differs, the artifact does not prove the latest head.
Re-run relevant verification or label the affected scenarios unverified.
After each push, refresh affected evidence under `build-monitoring.md`, Section 1.
Do not relabel old results as a new run.

Without an artifact, gather direct evidence using the same format.
If verification cannot run, retain the objective mapping and state what blocks it.
Never fabricate outputs, commands, screenshots, transcripts, or a success verdict.

### Map the objective to scenarios

Use stable scenario IDs such as `S1` and `S2`.
A scenario is one concrete behavior check with defined inputs and expected results.
Include an Acceptance Criteria Verification table, or map a factual objective when no formal criteria exist:

| Objective or acceptance criterion | Scenario | Expected behavior | Observed behavior | Result |
| -------------------------------- | -------- | ----------------- | ----------------- | ------ |
| <exact requirement or factual objective> | <ID> | <precise expected output> | <actual output or not run> | <PASS, FAIL, or UNVERIFIED> |

Cover relevant successful behavior, boundary inputs, errors, and behavior that must remain unchanged.
State why a category does not apply instead of inventing an irrelevant scenario.
For documentation changes, check the documented procedure or example against its actual source or runtime where possible.
Mark runtime behavior unverified when only the document text has been checked.
For a structured validator summary, retain each assertion's Status, Expected, Actual, and Detail fields inside the verification details.
Map those assertions to scenarios. A summary table alone does not replace reproduction details or actual output.

### Include reproducible details

Put detailed evidence in a top-level `<details>` block with summary `Verification details: <PASS | FAIL | PARTIAL | UNVERIFIED>`.
Use PASS only when current-head evidence supports every required scenario.
Use FAIL for observed failures, PARTIAL for mixed verified and unverified coverage, and UNVERIFIED when no required behavior has evidence.

Include shared prerequisites once, then provide these fields for every scenario:

1. Objective or acceptance criterion and scenario ID.
2. Exact inputs, fixtures, configuration, dependency versions, and environment needed for reproduction.
3. Setup commands, service startup and health checks when relevant, and cleanup.
4. Exact action or runnable command, with all required arguments and request payloads.
5. Expected outputs or externally visible effects.
6. Observed outputs, real excerpts, and a result supported by those excerpts.
7. Limits, omitted environments, and unverified claims.

For live checks, preserve the actual request commands and request/response transcripts verbatim.
For library checks, show concrete function inputs, expected and observed values, the focused test command, and real output excerpts.
For manual or UI checks, show exact actions and resulting states, with reviewer-accessible screenshots when relevant.

Keep every scenario's reproduction instructions and evidence.
Do not cap scenarios or replace later scenarios with table rows alone.
Group related scenarios inside collapsibles when needed, without deleting inputs, expected results, observed outputs, or transcripts.

### Evidence skeleton

The placeholders below define structure, not execution evidence. Replace them only with facts from actual verification.
Apply `collapsible-format.md` to summaries and spacing.

```markdown
### Testing & Verification

- <Observed behavior and objective, or explicit unverified limit.>

<details><summary><strong>Verification details: <verdict></strong></summary>

Tested commit: <exact SHA>
Environment: <runtime, versions, and relevant configuration>

<Objective-to-scenario table>

<details>
<summary><strong>S1: <behavior and key input></strong></summary>

Objective: <criterion>
Inputs and setup: <exact fixture and prerequisites>
Action: <copy-pasteable command or precise manual steps>
Expected: <exact output or effect>
Observed: <actual output or effect>
Result: <PASS, FAIL, or UNVERIFIED>

<Verbatim command and output blocks from the real run>

Cleanup: <commands or actions, if needed>
Limits: <unverified behavior, if any>

</details>

<Repeat complete scenario details for every remaining scenario.>

</details>
```

### Reviewer access and final audit

Inline useful evidence from local reports or link to reviewer-accessible artifacts.
Do not replace reproducible repository-relative commands with pointers to author-only files.
Preserve exact identifiers and verbatim transcripts; audit surrounding prose separately.
If a transcript includes author-only paths, preserve it and add portable reproduction setup separately.
Auto-tick checklist items only when actual evidence confirms them.

## Conventional Commit Parsing

Each conventional commit prefix informs the LLM-authored Why/What prose, not section headings.
Read the actual commit messages against the selected target branch.

| Prefix | Prose focus |
| ------ | ----------- |
| `feat:` | User-visible objective |
| `fix:` | Bug or regression |
| `chore:` | Factual purpose without invented user impact |
| `refactor:` | Behavior that must remain unchanged |
| `docs:` | Documented behavior or procedure |
| `test:` | Behavior the verification demonstrates |
