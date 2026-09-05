# Jira Integration Reference

This document covers Jira ticket extraction, fuzzy transition matching, and MCP tool usage
patterns for the submit-pr skill. All Jira operations are non-blocking: any failure at any
step produces a warning and allows the PR creation flow to continue uninterrupted.

---

## 1. Ticket ID Extraction

Ticket IDs follow the pattern `[A-Z]+-\d+` (e.g. `ENG-1234`, `PLAT-567`).

**Step 1 — Search the branch name first:**

```bash
git branch --show-current | grep -oE '[A-Z]+-[0-9]+'
```

Common branch naming patterns that contain a ticket ID:

| Branch pattern          | Example              |
|-------------------------|----------------------|
| `feature/<ID>-desc`     | `feature/ENG-1234-desc` |
| `<ID>/desc`             | `ENG-1234/desc`      |
| `<user>/<ID>-fix`       | `jbb/ENG-1234-fix`   |

**Step 2 — Fall back to recent commit messages:**

If no ticket ID is found in the branch name, search the last 10 commits:

```bash
git log --oneline HEAD~10..HEAD | grep -oE '[A-Z]+-[0-9]+' | head -1
```

**Step 3 — No ticket found:**

If neither the branch name nor the commit messages contain a ticket ID, emit a warning and
continue. This is non-blocking: PR creation proceeds without any Jira operations.

```
WARN: No Jira ticket ID found in branch name or recent commits. Skipping Jira updates.
```

---

## 2. Fuzzy Transition Matching Algorithm

When a ticket ID has been found, use fuzzy matching to locate the correct "In Review"
transition rather than hard-coding a transition name. Follow these steps exactly:

**Step 1 — Discover available transitions:**

Call `get_available_transitions(ticket_key)` to retrieve the list of valid transition names
for the ticket's current workflow state.

**Step 2 — Normalise names:**

Apply the same normalisation to both the available transition names and each candidate:
- Convert to lowercase
- Strip punctuation (remove characters that are not alphanumeric or whitespace)
- Trim leading and trailing whitespace

**Step 3 — Candidate list for "In Review" transitions:**

```
["in review", "code review", "ready for review", "waiting for approval"]
```

**Step 4 — Score each available transition:**

For every available transition (after normalisation), compute a substring overlap score
against the candidate list. The score is the length of the longest candidate string that
is a substring of the normalised transition name, divided by the length of that candidate.
Use the highest score across all candidates as the transition's final score.

**Step 5 — Select the best match:**

Choose the available transition with the highest score. If that score is >= 0.6, use it.

**Step 6 — Handle no match:**

If no available transition scores >= 0.6, emit a warning that includes the full list of
available transitions (to aid debugging), and skip the transition entirely:

```
WARN: No Jira transition matched for "In Review" (confidence floor 0.6).
      Available transitions: [<list>]. Skipping transition.
```

**Step 7 — Log the selected transition:**

When a match is found, always log the selected transition name and its score for
auditability:

```
INFO: Jira transition selected: "<name>" (score=0.87). Transitioning ENG-1234.
```

---

## 3. MCP Tool Usage Patterns

All Jira operations use the `atlassian-mcp` MCP server tools. Treat every call as
non-blocking (wrap in try/catch or equivalent; on failure warn and continue).

### Discover valid transitions

```
get_available_transitions(issue_key="ENG-1234")
```

Returns an array of transition objects. Use the `name` field for fuzzy matching.

### Transition the ticket

```
edit_ticket(issue_key="ENG-1234", transition_to=<matched_name>)
```

Pass the exact transition name returned by `get_available_transitions`, not the normalised
form.

### Add a PR link comment

```
add_comment(
  issue_key="ENG-1234",
  comment_text="PR created: <PR_URL>\n\n<PR_summary>"
)
```

The comment body should include the full PR URL on the first line followed by a blank line
and a brief summary of the changes (one or two sentences).

---

## 4. Error Handling

All Jira operations are non-blocking (design doc Constraint #9). The table below lists
every failure scenario and the required behaviour.

| Failure scenario                              | Action                                              |
|-----------------------------------------------|-----------------------------------------------------|
| No ticket ID in branch name or commits        | Warn, skip all Jira operations, continue            |
| `get_available_transitions` call fails        | Warn, skip transition and comment, continue         |
| No transition matches with score >= 0.6       | Warn (log available transitions), skip, continue    |
| `edit_ticket` call fails                      | Warn, skip, continue                                |
| `add_comment` call fails                      | Warn, skip, continue                                |
| Atlassian MCP server unavailable              | Warn, skip all Jira operations, continue            |

The PR must be created regardless of the outcome of any Jira step. Never propagate a Jira
error as a fatal error in the submit-pr flow.

---

## 5. Post-Merge Transition Candidates

After the PR is merged, the ticket should be transitioned to a "Done" state. This
transition is triggered by `build-monitoring.md` when it detects that the PR has been
merged. That file references this same fuzzy matching algorithm.

**Candidate list for "Done" transitions:**

```
["done", "closed", "resolved", "complete"]
```

Apply exactly the same normalisation and 0.6 confidence floor described in Section 2. If
no available transition scores >= 0.6 against these candidates, log a warning with the
full list of available transitions and skip the post-merge transition.
