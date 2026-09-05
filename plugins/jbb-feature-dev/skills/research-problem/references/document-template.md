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

Use the metadata from Step 10 and structure the document with YAML frontmatter:

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
review_phase_status: [completed | skipped_simple_complexity]
complexity: [Simple | Medium | Complex]
---

# Research: [User's Question/Topic]

**Date**: [Current date and time with timezone from Step 10]
**Researcher**: [Researcher name]
**Git Commit**: [Current commit hash from Step 10]
**Branch**: [Current branch name from Step 10]
**Repository**: [Repository name]

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

## Open Questions

[Only questions the Step 8 grounding pass classified UNRESOLVABLE or SKIP, each stating the
qualifying reason it was classified under. `references/grounding-pass.md`
`## What Legitimately Stays Open` is the canonical list of which reasons qualify and which
phrasings disqualify a question from appearing here — do not restate it, apply it.

Open questions here are expected and healthy; there is no target of zero. What must not
appear is a question that more research alone could answer.

Format each as: the question — why research cannot close it — what would close it.]

## Operational Context Recommendation

{{If this research identified specific services, include:}}

The following services were identified in this research:

- [service-name-1]
- [service-name-2]

Consider running `/operational-context [service-names]` before creating an
implementation plan. This will gather production metrics, SLOs, dependency
health, and deployment status to inform planning decisions.

{{If no specific services were identified, include:}}

No specific services were identified in this research. Operational context
gathering is not recommended at this time.

## Design Exploration Recommendation

{{If this research identified 2+ design tensions, ambiguities, or competing approaches, include:}}

Multiple viable design approaches were identified in this research:

- [tension/ambiguity 1]
- [tension/ambiguity 2]

Consider running `/design-approach [path-to-this-doc]` to explore and compare
approaches before creating an implementation plan with `/create-plan-tdd`.

{{If requirements were gathered, add:}}
Include the requirements doc: `/design-approach [research-doc] --requirements=[requirements-doc]`

{{If this research is straightforward with one clear approach, include:}}

No significant design tensions were identified. Proceeding directly to
`/create-plan-tdd` is recommended.
```

## Step 12: GitHub Permalink Generation

- Check if on main branch or if commit is pushed: `git branch --show-current` and `git status`
- If on main/master or pushed, generate GitHub permalinks:
  - Get repo info: `gh repo view --json owner,name`
  - Create permalinks: `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`
- Replace local file references with permalinks in the document

## Step 13: MCP Call Documentation

Include information from the web-search-researcher output so findings can be reproduced:

- **aika mcp search**: query, source, and description
- **codesearch mcp search**: query, repository name, and description
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
