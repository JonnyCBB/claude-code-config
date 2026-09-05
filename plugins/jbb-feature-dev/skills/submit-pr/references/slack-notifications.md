# Slack Notifications Reference

This document describes the Slack notification patterns used by the `/submit-pr` skill.

## When Slack Notifications Are Sent

Slack notifications are **only sent when the `--notify <channel>` flag is specified**.
If the flag is omitted, no Slack messages are sent at any point during the workflow.

Notifications are sent on the following events:

- **Build success** — all CI checks pass
- **Build failure** — an irrecoverable test or build failure is detected
- **Auto-fix applied** — lint/format issues were automatically fixed and pushed
- **Auto-fix skipped due to active review** — a lint failure was detected but auto-fix was skipped because a review is already in progress

## Message Templates

Use these exact message formats when constructing notifications:

| Event | Template |
|---|---|
| Build success | `PR #<N> checks passed: <URL>` |
| Build failure | `PR #<N> checks failed: <failed_check_names> — <URL>` |
| Auto-fix applied | `PR #<N> lint auto-fixed and pushed: <URL>` |
| Auto-fix skipped | `PR #<N> has a lint failure but auto-fix was skipped — active review in progress: <URL>` |

Where:
- `<N>` is the PR number
- `<URL>` is the pull request URL
- `<failed_check_names>` is a comma-separated list of the names of failed checks

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

If `slack_search_channels` returns no results, log a warning and continue without sending.

## Error Handling

All Slack operations are **non-blocking**. The monitoring loop continues even if a notification fails. Never abort or pause the workflow due to a Slack error.

Specific error cases:

| Error | Action |
|---|---|
| Slack MCP unavailable | Log a warning, continue |
| Channel not found | Log a warning, continue |
| Message send fails | Log a warning, continue |

The warning log should indicate what was attempted (e.g., `"Warning: could not send Slack notification to #channel-name — channel not found"`) so the user can diagnose the issue without the workflow being interrupted.
