# Slack Routing

The orchestrator emits Slack notifications via direct Slack MCP tool calls — never by forwarding through `/submit-pr --notify`. The same target is used for both success notifications and escalation alerts: a single resolved channel ID per run, derived once and reused.

Default routing is a DM to the invoking user. The `--slack-channel <id>` flag overrides the default and routes everything to that channel instead.

The available Slack MCP surface (per the orchestrator runtime) is `slack_search_users`, `slack_send_message`, `slack_read_user_profile`, and `slack_search_channels`. There is no `slack_open_dm` tool — DM delivery is achieved by passing a user ID directly as the `channel` parameter to `slack_send_message`, which causes Slack to auto-create or reuse the IM channel between the bot and the user.

## DM Routing

When `--slack-channel` is not provided, the orchestrator routes to the invoking user's DM. Resolution path:

1. Resolve the invoking user's email (or username) to a Slack user ID via `slack_search_users`. Pick the first match; if zero matches, log a warning and skip Slack notification entirely.
2. Pass the resolved `user_id` (e.g. `U01ABC123`) directly as the `channel` argument to `slack_send_message`. Slack will open or reuse the IM channel implicitly.
3. Fallback path (only if step 2 fails at runtime): call `slack_read_user_profile <user_id>` to fetch the user's IM channel ID from the profile payload, then send via `slack_send_message --channel <im-channel-id>`. Document the rejected path in run logs so future runs prefer the working one.

Pseudo-code (these are MCP tool calls, not literal CLI invocations — adapt to the runtime helper):

```bash
set +e  # Slack delivery is auxiliary; never escalate or fail the run on a Slack error.

USER_ID=$(call_mcp slack_search_users --query "$INVOKING_USER_EMAIL" \
  | jq -r '.users[0].id')

if [ -z "$USER_ID" ] || [ "$USER_ID" = "null" ]; then
  echo "WARN: could not resolve Slack user for $INVOKING_USER_EMAIL; skipping notification" >&2
else
  call_mcp slack_send_message --channel "$USER_ID" --text "$MESSAGE" \
    || echo "WARN: slack_send_message failed for user $USER_ID" >&2
fi

set -e
```

Cache the resolved `user_id` in the run state so subsequent notifications (success, escalation) reuse it without re-running `slack_search_users`.

## Channel Routing

When `--slack-channel <id>` is provided, skip DM resolution entirely. The flag value is treated as a literal Slack channel ID (e.g. `C01XYZ789`) and passed straight to `slack_send_message`.

If the user supplies a channel name instead of an ID (leading `#` or no `C…` prefix), optionally resolve the name to a `channel_id` via `slack_search_channels` before sending. Otherwise reject names and require the canonical ID — the orchestrator's CLI doc should make this explicit.

```bash
set +e

CHANNEL_ID="$SLACK_CHANNEL_FLAG"
case "$CHANNEL_ID" in
  C*|G*|D*) ;;  # already a channel ID
  *)
    CHANNEL_ID=$(call_mcp slack_search_channels --query "${CHANNEL_ID#\#}" \
      | jq -r '.channels[0].id')
    ;;
esac

if [ -z "$CHANNEL_ID" ] || [ "$CHANNEL_ID" = "null" ]; then
  echo "WARN: could not resolve Slack channel '$SLACK_CHANNEL_FLAG'; skipping notification" >&2
else
  call_mcp slack_send_message --channel "$CHANNEL_ID" --text "$MESSAGE" \
    || echo "WARN: slack_send_message failed for channel $CHANNEL_ID" >&2
fi

set -e
```

## Failure Tolerance

Slack notification is auxiliary. Wrap every Slack MCP call in `set +e` (or an equivalent error trap) so a transient MCP error, missing scope, or unresolved user does not escalate or fail the orchestrator run. On failure, log a warning to stderr and continue.

The same rule applies to escalation alerts: if the orchestrator is already escalating because of a pipeline failure, a Slack delivery error must not mask or supersede the original failure — log the Slack error separately and proceed to surface the underlying escalation reason via the run's exit status and state file.
