# Document Template for Steps 10-13: Research Document Generation

Metadata gathering, file naming, document structure, permalinks, and follow-up format.
Read this file when Steps 10-13 instruct you to `Read references/document-template.md`.

## Step 10: Metadata Gathering

Run this script to collect metadata:

```bash
#!/usr/bin/env bash
set -euo pipefail

DATETIME_TZ=$(date '+%Y-%m-%d %H:%M:%S %Z')
FILENAME_TS=$(date '+%Y-%m-%d_%H-%M-%S')

if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$REPO_ROOT")
GIT_BRANCH=$(git branch --show-current 2>/dev/null || git rev-parse --abbrev-ref HEAD)
GIT_COMMIT=$(git rev-parse HEAD)
else
REPO_ROOT=""
REPO_NAME=""
GIT_BRANCH=""
GIT_COMMIT=""
fi

echo "Current Date/Time (TZ): $DATETIME_TZ"
[ -n "$GIT_COMMIT" ] && echo "Current Git Commit Hash: $GIT_COMMIT"
[ -n "$GIT_BRANCH" ] && echo "Current Branch Name: $GIT_BRANCH"
[ -n "$REPO_NAME" ] && echo "Repository Name: $REPO_NAME"
echo "Timestamp For Filename: $FILENAME_TS"
```

Create `~/.claude/thoughts/shared/research/` if it doesn't exist.

### File Naming Conventions

- Format: `YYYY-MM-DD-ENG-XXXX-description.md`
  - YYYY-MM-DD is today's date
  - ENG-XXXX is the ticket number (omit if no ticket)
  - description is a brief kebab-case description of the research topic
- Examples:
  - With ticket: `2025-01-08-ENG-1478-parent-child-tracking.md`
  - Without ticket: `2025-01-08-authentication-flow.md`

## Step 11: Research Document Template

Use the metadata from Step 10 and structure the document with YAML frontmatter.

**Emit every section, including the ones that come out empty.** A section with no content
gets the heading and the single word `None.` underneath. Do not delete the heading.

This is the same principle as the Step Ledger, applied to findings rather than steps: a
reader cannot tell a section that was checked and came back empty from one nobody looked at,
and the whole point of both is that absence is stated rather than implied. Measured
2026-09-10 on a real run: the `Competing Findings` heading was dropped entirely rather than
written as `None.`, because the instruction to write `None.` was inside the bracketed
placeholder that the author is meant to replace - so removing the placeholder removed the
instruction with it.

```markdown
---
date: [Current date and time with timezone in ISO format]
researcher: [Researcher name]
git_commit: [Current commit hash]
branch: [Current branch name]
repository: [Repository name]
topic: "[User's Question/Topic]"
tags: [research, codebase, tools, libraries, relevant-component-names]
status: complete
last_updated: [Current date in YYYY-MM-DD format]
last_updated_by: [Researcher name]
review_phase_status: completed # the review phase runs at every complexity
complexity: [Simple | Medium | Complex]
---

# Research: [User's Question/Topic]

**Date**: [Current date and time with timezone from Step 10]
**Researcher**: [Researcher name]
**Git Commit**: [Current commit hash from Step 10]
**Branch**: [Current branch name from Step 10]
**Repository**: [Repository name]

## Step Ledger

Every step of the skill, what it produced, and the evidence. Fill every row. `completed`
means the step's work happened; a step that could not run says so in plain words and names
what is consequently missing. Never record a skipped step as `completed`.

| Step | Status | Evidence |
| ---- | ------ | -------- |
| 1 Read mentioned files | completed | [files read, or "none mentioned"] |
| 2 Decompose | completed | [question count; plan path in non-interactive mode] |
| 3 Spawn researchers | completed | [agent types spawned, and for which questions] |
| 4 Validate completion | completed | [agents committed vs spawned] |
| 5 Synthesize | completed | [absolute path of the synthesis file] |
| 6 Completeness review | completed | [evaluator agent name; verdict; iterations run] |
| 7 Review phase | completed | [reviewer personas spawned by name; Must Address count] |
| 8 Grounding pass | completed | [grounding + verification agent names; final decision; iterations] |
| 9 Synthesis revision | completed | [count of claims revised; count annotated unresolved] |
| Pre-Document Gate | completed | [all artifacts confirmed present] |
| 10-13 Document | completed | [this document] |

A reader checking this research should be able to tell from this table alone which
verification actually happened. That is its whole purpose — the previous version of this
template recorded only the review phase, via a single frontmatter field the orchestrator
also wrote itself, so nine other steps had no audit surface at all.

## Research Question

[Original user query]

## Summary

[High-level documentation of what was found, answering the user's question by describing what exists]

## Detailed Findings

### [Component/Area 1]

- Description of what exists ([file.ext:line](link))
- How it connects to other components
- Current implementation details (without evaluation)

### [Component/Area 2]

...

## Code References

- `path/to/file.py:123` - Description of what's there
- `another/file.ts:45-67` - Description of the code block

## Architecture Documentation

[Current patterns, conventions, and design implementations found in the codebase]

## Historical Context (from ~/.claude/thoughts/)

[Relevant insights from ~/.claude/thoughts/ directory with references]

- `~/.claude/thoughts/shared/something.md` - Historical decision about X
- `~/.claude/thoughts/local/notes.md` - Past exploration of Y

## Related Research

[Links to other research documents in ~/.claude/thoughts/shared/research/]

## Competing Findings

[Where two agents returned conflicting information and neither is better sourced, both
positions with their evidence and source tiers. Step 5 requires contradictions to stay
visible rather than being silently resolved, and this is where they go.]

None.

## Review Methodology

[Which reviewer personas ran in Step 7, any that did not deliver after the recovery ladder
was exhausted, and — if the user asked for less review — their words. Write the reviewer
names, not a count: "the review ran" is exactly the unfalsifiable claim the Step Ledger
exists to replace.]

## Advisory Notes

["Should Consider" and "Minor" items from Step 7 that were not applied, each attributed to
the persona that raised it.]

None.

## Open Questions

[Only questions the Step 8 grounding pass classified UNRESOLVABLE or SKIP, each stating the
qualifying reason it was classified under. `references/grounding-pass.md`
`## What Legitimately Stays Open` is the canonical list of which reasons qualify and which
phrasings disqualify a question from appearing here — do not restate it, apply it.

Open questions here are expected and healthy; there is no target of zero. What must not
appear is a question that more research alone could answer.

Format each as: the question — why research cannot close it — what would close it.]

## Design Exploration Recommendation

{{If this research identified 2+ design tensions, ambiguities, or competing approaches, include:}}

Multiple viable design approaches were identified in this research:

- [tension/ambiguity 1]
- [tension/ambiguity 2]

Consider running `/design-approach [path-to-this-doc]` to explore and compare
approaches before implementing with `/implement-change`.

{{If requirements were gathered, add:}}
Include the requirements doc: `/design-approach [research-doc] --requirements=[requirements-doc]`

{{If this research is straightforward with one clear approach, include:}}

No significant design tensions were identified. Proceeding directly to
`/implement-change` is recommended.
```

## Step 12: GitHub Permalink Generation

- Check if on main branch or if commit is pushed: `git branch --show-current` and `git status`
- If on main/master or pushed, generate GitHub permalinks:
  - Get repo info: `gh repo view --json owner,name`
  - Create permalinks: `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`
- Replace local file references with permalinks in the document

## Step 13: MCP Call Documentation

Include information from the research agents' output so findings can be reproduced:

- **MCP or internal search calls**: tool, query, source, and description
- **code searches**: query, repository name, and description
- **relevant webpages**: links and descriptions

## Follow-up Research Format (Step 15)

When handling follow-up questions, update the existing research document:

1. Update frontmatter fields:
   - `last_updated`: current date in YYYY-MM-DD format
   - `last_updated_by`: researcher name
   - Add: `last_updated_note: "Added follow-up research for [brief description]"`

2. Add a new section to the document:

   ```markdown
   ## Follow-up Research [timestamp]
   ```

3. Spawn new sub-agents as needed for additional investigation
4. Continue updating the document and syncing
