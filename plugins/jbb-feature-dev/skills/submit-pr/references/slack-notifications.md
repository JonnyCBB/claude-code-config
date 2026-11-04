# Slack Notifications Reference

This document describes the Slack notification patterns used by the `/submit-pr` skill.

## When Slack Notifications Are Sent

Slack notifications are **only sent when the `--notify <channel>` flag is specified**.
If the flag is omitted, no Slack messages are sent at any point during the workflow.

Notifications are sent on the following events:

- **Review-ready success**, only after `build-monitoring.md`, Section 1, confirms full latest-head convergence
- **Failure or blocker**, a check or review fails, or access, authorization, or tools prevent progress
- **Fix applied**, an authorized correction passes relevant local checks and is pushed; convergence still remains pending

A pending review or `CHANGES_REQUESTED` status alone does not forbid a corrective fix.
Use `build-monitoring.md` as the canonical policy instead of stopping at the first green CI result.

## Message Templates

Use these exact message formats when constructing notifications:

| Event | Template |
|---|---|
| Review-ready success | `PR #<N> CI and automated review are clean at <head_sha>: <URL>` |
| Failure or blocker | `PR #<N> blocked at <head_sha>: <finding_or_failed_check>. <classification>. <actual_error_or_unavailable_log_limit>. <build_or_review_URL>. <next_action>. <URL>` |
| Fix applied | `PR #<N> fix pushed at <head_sha>; latest-head CI and review pending: <URL>` |

Where:
- `<N>` is the PR number
- `<URL>` is the pull request URL
- `<head_sha>` is the exact remote PR head commit
- Failure fields contain the actual finding or failed check, error excerpt, accessible evidence URL, and next action
- If logs or review results are unavailable, state that limit instead of inventing an error

## Slack MCP Usage

### Sending a Message

Use the `slack_send_message` tool to post notifications:

```
slack_send_message(channel=<channel_id>, text=<message>)
```

The `channel` parameter must be a **channel ID**, not a channel name.

### Channel Resolution

If the user provides a channel name (e.g., `#my-team-alerts`), resolve it to a channel ID first using `slack_search_channels` before calling `slack_send_message`:

1. Call `slack_search_channels` with the channel name (strip the leading `#`)
2. Extract the channel ID from the result
3. Pass the channel ID to `slack_send_message`

If `slack_search_channels` returns no results, report the delivery blocker in the conversation and task record. Continue without sending.

## Error Handling

All Slack operations are **non-blocking**. The monitoring loop continues even if a notification fails.
Report delivery failures in the conversation and task record so the user or supervising worker sees them.
Reconcile an uncertain send before retrying it. Do not claim delivery without confirmation.

Specific error cases:

| Error | Action |
|---|---|
| Slack MCP unavailable | Report the delivery blocker, continue monitoring |
| Channel not found | Report the delivery blocker, continue monitoring |
| Message send fails | Report the delivery failure, continue monitoring |

The warning log should indicate what was attempted (e.g., `"Warning: could not send Slack notification to #channel-name — channel not found"`) so the user can diagnose the issue without the workflow being interrupted.
