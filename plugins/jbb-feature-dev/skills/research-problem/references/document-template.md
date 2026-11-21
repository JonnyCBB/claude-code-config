# Research Document (Steps 10-15)

## Step 10: Metadata

Collect: date and time with timezone, and, inside a git work tree, the repository name, branch
(`git branch --show-current`) and commit (`git rev-parse HEAD`). Create
`~/.claude/thoughts/shared/research/` if it does not exist.

File name: `YYYY-MM-DD-ENG-XXXX-description.md`, with the ticket omitted when there is none
(`2025-01-08-authentication-flow.md`).

## Step 11: Template

**Emit every section, including empty ones**: keep the heading and write `None.` under it. A
reader cannot tell a section checked and found empty from one nobody looked at. The `None.`
lines sit outside the bracketed placeholders on purpose: on a real run, deleting a placeholder
that held the instruction deleted the `Competing Findings` heading with it.

```markdown
---
date: [ISO date and time with timezone]
researcher: [name]
git_commit: [hash]
branch: [branch]
repository: [repository]
topic: "[question/topic]"
tags: [research, relevant-component-names]
status: complete
last_updated: [YYYY-MM-DD]
last_updated_by: [name]
review_phase_status: completed
complexity: [Simple | Medium | Complex]
---

# Research: [question/topic]

**Date**: [date] | **Git Commit**: [hash] | **Branch**: [branch] | **Repository**: [repository]

## Step Ledger

Fill every row. `completed` means the step's work happened. A step that could not run, or ran
differently from the skill (a check not re-run after a revision, a roster changed), says so in
plain words and names what is missing as a result.

| Step | Status | Evidence |
| ---- | ------ | -------- |
| 1 Read mentioned files | completed | [files read, or "none mentioned"] |
| 2 Decompose | completed | [question count; plan path in non-interactive mode] |
| 3 Spawn researchers | completed | [agent types spawned, for which questions] |
| 4 Validate completion | completed | [assignments delivered vs planned] |
| 5 Synthesize | completed | [absolute path of the synthesis file] |
| 6 Completeness review | completed | [evaluator name; verdict per round; tool-use count] |
| 7 Review phase | completed | [personas by name; Must Address count; rounds] |
| 8 Grounding pass | completed | [grounding and verification agent names; decisions; iterations] |
| 9 Synthesis revision | completed | [claims revised; items annotated unresolved; re-checks run] |
| Pre-Document Gate | completed | [all artifacts confirmed present] |
| 10-13 Document | completed | [this document] |

## Research Question

[Original query]

## Summary

[What was found, answering the question by describing what exists]

## Detailed Findings

### [Component/Area]

- What exists ([file.ext:line](link)), how it connects to other components

## Code References

- `path/to/file.py:123` - what is there

## Architecture Documentation

[Patterns, conventions and design found in the code]

## Historical Context (from ~/.claude/thoughts/)

[Relevant earlier decisions, with paths]

## Related Research

[Links to other documents in ~/.claude/thoughts/shared/research/]

## Competing Findings

[Conflicting agent findings where neither is better sourced: both positions, with evidence]

None.

## Review Methodology

[Step 7 personas by name, any that did not deliver after the recovery ladder, and the user's
words if they asked for less review]

## Advisory Notes

[Unapplied Should Consider and Minor items, each with the persona that raised it]

None.

## Open Questions

[Only items Step 8 classified UNRESOLVABLE or SKIP, each as: the question - why research cannot
close it (a reason from `## What Legitimately Stays Open` in references/grounding-pass.md) -
what would close it]

None.

## Reproduction

[Step 13: the internal search queries and sources, code search queries and repositories, web pages, and
commands behind the findings]

## Design Exploration Recommendation

[If 2+ design tensions or competing approaches were found: list them and suggest
`/design-approach [path-to-this-doc]` (add `--requirements=[requirements-doc]` if one exists)
before `/implement-change`. Otherwise: "No significant design tensions; proceed to
`/implement-change`."]
```

## Step 12: Permalinks

If on main/master or the commit is pushed, get the owner and name with
`gh repo view --json owner,name` and replace local references with
`https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`.

## Step 15: Follow-up format

Update `last_updated`, `last_updated_by`, and add
`last_updated_note: "Added follow-up research for [description]"`, then append
`## Follow-up Research [timestamp]`.
