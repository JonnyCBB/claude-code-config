# PR Description Template

Reference for default PR template structure, template discovery logic, and content generation rules.

---

## Template Discovery

Use the `codebase-explorer` agent to search for pull request template files before using the default format.

**Search paths in order:**

1. `.github/pull_request_template.md`
2. `.github/PULL_REQUEST_TEMPLATE.md`
3. `.github/PULL_REQUEST_TEMPLATE/` (directory — use any `.md` file inside)
4. `docs/pull_request_template.md`
5. `PULL_REQUEST_TEMPLATE.md`

**Agent prompt:**

> "Find pull request template files in this repository. Look for files like pull_request_template.md, PULL_REQUEST_TEMPLATE.md, or similar PR template files in .github/, docs/, or root directory."

**If a template is found:**

- Read the template file(s)
- Use the template structure exactly — fill in sections based on analyzed changes
- Maintain the template's formatting, sections, and style
- If diagrams were generated, insert an "Architecture Overview" section after "Summary"/"Context" and before "Testing"/"Checklist", using judgment for placement

**If no template is found:**

- Use the default format defined in this document

---

## Default PR Description Format

Aim for ≤ 30 visible lines on a typical change. Conditional sections (Stack, Architecture Overview) and the verification details collapsible expand the body only when their triggers fire.

### Title

- Concise, outcome-focused (under 72 characters)
- Imperative mood: "Add X", "Fix Y", "Refactor Z"
- Include measurable impact when known

### Why

1-3 sentences stating the problem solved or the user/system motivation. Source
from a requirements doc or user input (see Phase 1 step 7) when present;
otherwise derive from the diff and commit messages. Never fabricate motivation —
if the real reason is unknown, describe what the change does factually. Do not
write "improved maintainability," "performance optimization," or similar unless
commit messages or requirements explicitly say so.

### What

2-4 bullets describing behavior changes — not file changes, not the diff
restated. Each bullet should pass the Diff-Deducible Test from
`references/pr-prose-rules.md`: if a reviewer would already know it from
reading the diff, omit it. Focus on what would surprise a reviewer or what
they need to understand before reading the code.

When triggered by Phase 1 auto-detection in `SKILL.md`, conditional callouts
(Breaking change / Feature flag / Migration / Screenshots prompt) emit as a
single inline line at the top of What.

### Links

- Jira ticket(s) extracted from the branch
- Related PRs, design docs, or RFCs (reviewer-accessible URLs only — see SKILL.md "Reviewer-Visible Content Only")

### Stack

[Include only when `--scoping-doc` is in stacked-PR mode — omit otherwise.]

> This PR is part of a stacked PR chain. Each PR builds on the previous one and should be reviewed in order.

| #   | PR                                  | Base                 | Status |
| --- | ----------------------------------- | -------------------- | ------ |
| 1   | #NNN — [Plan 1 title]               | `master`             | open   |
| 2   | **#NNN — [Plan 2 title] (this PR)** | `feat/plan-1-branch` | open   |
| 3   | #NNN — [Plan 3 title]               | `feat/plan-2-branch` | draft  |

### Architecture Overview

[Include only if diagrams were generated per `references/diagram-generation.md` and `--no-diagram` was not set — omit otherwise.]

```mermaid
[Diagram code from visual-aid-recommender]
```

[1-2 sentence caption explaining what the diagram shows.]

### Testing & Verification

Short visible bullets — one per non-CI verification activity (live testing,
integration against external services, manual repro, screenshots). Do NOT list
unit tests — CI reports those directly on the PR (see SKILL.md "Do Not Restate
CI-Covered Signals"). When a verification report is present at
`~/.claude/thoughts/shared/verification/`, append the Level-1 collapsible
documented in "Verification Results Embedding" below, omitting the `Unit` row
from the per-category counts table; otherwise omit it.

---

### Skeletal example: minimal default body

(No requirements doc, no verification report, no diagram. ~30 visible lines.)

```markdown
### Title

Add cache eviction metrics to PlaylistService

### Why

Recent latency investigations have been blocked by lack of cache eviction visibility.

### What

- Emit `cache.evictions.count` and `cache.evictions.bytes` from the eviction path.
- Tag metrics with cache name and reason (size / ttl / explicit).
- Add a smoke test that asserts metric emission on synthetic eviction.

### Links

- Jira: [PROJ-1234](https://your-org.atlassian.net/browse/PROJ-1234)

### Testing & Verification

- Local smoke run validated metric tags
```

### Skeletal example: with requirements doc, verification report, and UI screenshot prompt

(Demonstrates the Level-1 verification collapsible with summary, reproduction overview, and AC mapping; Level-2 nested per-scenario transcripts. UI files in the diff trigger the screenshot HTML comment.)

````markdown
### Title

Add experiment exposure filter for paid-only cohorts

### Why

A/B exposures previously emitted on every request, polluting analytics for free-tier users that the experiment never targeted. The filter restricts exposure to the cohort defined in the requirements doc.

### What

**Feature flag**: `paid_only_exposure_filter` default `false`.

- Add request-time check against the entitlement service.
- Emit exposures only when the cohort matches.
- Skip the filter when the flag is off (matches current behavior).

### Links

- Jira: [PROJ-5678](https://your-org.atlassian.net/browse/PROJ-5678)

### Testing & Verification

- Integration tests against a stubbed entitlement service
- Live testing performed against staging

<details>
<summary><strong>Verification details: PASS</strong></summary>

**Verdict**: PASS

| Category    | Total | Pass | Fail | Skip |
| ----------- | ----- | ---- | ---- | ---- |
| Integration | 4     | 4    | 0    | 0    |
| Live        | 3     | 3    | 0    | 0    |

**Reproduction overview:**

1. Prereqs: `gcloud auth login`, `JAVA_HOME` set.
2. Start: `mvn spring-boot:run` (port 8080).
3. Health: `curl localhost:8080/healthz`.

**Acceptance Criteria Verification:**

| Criterion                              | Result    |
| -------------------------------------- | --------- |
| Filter blocks free-tier exposures      | PASS (S1) |
| Filter passes paid-tier exposures      | PASS (S2) |
| Flag-off path matches current behavior | PASS (S3) |

<details>
<summary><strong>S1: free-tier blocked — "user_id=free_user_42"</strong></summary>

**Request:**

```bash
curl -X POST localhost:8080/exposures -d '{"user_id":"free_user_42"}'
```

**Response:**

```json
{ "emitted": false, "reason": "cohort_mismatch" }
```

</details>

<details>
<summary><strong>S2: paid-tier passed — "user_id=paid_user_7"</strong></summary>

**Request:**

```bash
curl -X POST localhost:8080/exposures -d '{"user_id":"paid_user_7"}'
```

**Response:**

```json
{ "emitted": true, "exposure_id": "exp_abc123" }
```

</details>

<details>
<summary><strong>S3: flag-off no-op — "user_id=any"</strong></summary>

**Request:**

```bash
curl -X POST localhost:8080/exposures \
  -H "X-Flag-Override: paid_only_exposure_filter=false" \
  -d '{"user_id":"any"}'
```

**Response:**

```json
{ "emitted": true, "exposure_id": "exp_xyz789" }
```

</details>

</details>

<!-- screenshot recommended -->
````

### Conditional Callouts

Emitted as a single inline line at the top of What when Phase 1 auto-detection fires. Trigger conditions are sourced from `SKILL.md` (do not duplicate them here).

- `**Breaking change**: <one-sentence description>` — see Phase 1 auto-detection in `SKILL.md`
- `**Feature flag**: <name> default <value>` — see Phase 1 auto-detection in `SKILL.md`
- `**Migration**: <one-sentence description>` — see Phase 1 auto-detection in `SKILL.md`
- Screenshots prompt — when no screenshot is provided, emit `<!-- screenshot recommended -->` as an HTML comment in What. See Phase 1 auto-detection in `SKILL.md`.

### Insertion rules for discovered templates

When a repository template is discovered (per Template Discovery above), use the discovered structure as authoritative and map content like this:

- Why → discovered "Summary" / "Context" / "Description" equivalent
- What → discovered "What changed" / "Changes" equivalent
- Links → discovered "Related" / "References" equivalent
- Architecture Overview → insert before discovered "Testing" / "Checklist"
- Verification details collapsible → append after discovered "Testing" or "How have you verified?"
- Stack section → insert after discovered "Summary"/"Context" equivalent
- Conditional callouts → inline at the top of the discovered "Description" / "What" equivalent

### Implementation Notes

- Default body, no enhancements: aim ≤ 30 visible lines. Warn (do not error) if it grows past that.
- Verification details collapsible, when present, may exceed the visible-line budget — that is intentional.
- Cap nested per-scenario collapsibles at 10. Beyond 10, summarize remaining scenarios in the AC mapping table only.
- Auto-tick checklist items only when the diff confirms them.
- **Never reference local files or local-only context** — see SKILL.md "Reviewer-Visible Content Only". Local paths (`~/.claude/thoughts/...`, `/Users/...`, `/tmp/...`) and pointers to author-only artifacts are forbidden.
- Stacked PR descriptions: bold the current PR's row in the Stack table; use real PR numbers (captured during creation), not placeholders; status values are `draft`, `open`, `merged`. The Stack section goes after Why/What in the default body, or after the closest "Summary"/"Context" equivalent in a discovered template.

---

## Conventional Commit Parsing

Parse commit messages for conventional commit prefixes. Each prefix **informs the LLM-authored** Why/What prose — it does not drive subsystem buckets.

| Prefix      | Hint for prose authoring               |
| ----------- | -------------------------------------- |
| `feat:`     | Lead Why with the user-visible benefit |
| `fix:`      | Lead Why with the bug or regression    |
| `chore:`    | Keep What concise; rarely user-facing  |
| `refactor:` | Note behavior preservation in What     |
| `docs:`     | What focuses on doc updates            |
| `test:`     | What focuses on coverage gains         |

**How to apply:**

- Run `git log --oneline --no-merges origin/{{TARGET_BRANCH:-master}}..HEAD`
- For each commit, detect the prefix; let it shape Why/What prose, not section structure.
- Do not reintroduce subsystem-bucket headers in What.

---

## Verification Results Embedding

**Detect a verification report:**

If `--verification <path>` was provided, use that path directly — skip auto-detection.
Otherwise, auto-detect:

```bash
ls -t ~/.claude/thoughts/shared/verification/2*.md 2>/dev/null | head -1
```

If no report exists from either source, omit the collapsible entirely. Visible Testing & Verification bullets remain.

If a report exists, render a single Level-1 `<details>` collapsible at the bottom of Testing & Verification. Use the `<details>` / `<summary>` syntax from `references/collapsible-format.md`. The summary text is `Verification details: <VERDICT>` (PASS / FAIL / PARTIAL). Inside the Level-1 collapsible:

- `**Verdict**: <PASS | FAIL | PARTIAL>` — one-liner restating the verdict
- Per-category counts table from the report's `## Summary` — **omit the `Unit` row**;
  CI reports unit-test results directly on the PR
- Reproduction overview: 3-5 numbered steps (prerequisites, service startup, health check)
- "Acceptance Criteria Verification" table mapping each acceptance criterion to a result and a scenario reference

When live testing was performed, append Level-2 nested `<details>` collapsibles inside the Level-1 collapsible — one per scenario:

- Scenario header: literal `S1: <name> — "<key input>"`, `S2: …`, etc.
- Verbatim Request command (copy-pasteable bash) and Response payload (full, untruncated JSON)

Cap nested scenarios at 10. Beyond 10, summarize remaining scenarios in the AC mapping table only.

**Insertion point:**

- Default template: appended to the bottom of "Testing & Verification".
- Discovered template: append to the closest "Testing" or "How have you verified?" equivalent section.
