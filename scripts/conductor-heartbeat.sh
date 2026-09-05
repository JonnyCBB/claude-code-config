#!/bin/bash
# Heartbeat runner for conductor: hq (profile: default)
# Sends a check-in message to the conductor session (non-blocking).
#
# THIS SUPERSEDES agent-deck's generated heartbeat.sh. It is installed as
#   ~/.local/share/agent-deck/conductor/hq/heartbeat-runner.sh
# and the launchd plist is pointed at it by scripts/install-conductor-heartbeat.sh.
#
# ### DO NOT INSTALL THIS AS `heartbeat.sh`. MEASURED 2026-08-29.
#
# `agent-deck conductor status --json` REGENERATES heartbeat.sh from a template,
# within a second, with no warning. It is not a write command and nothing in its
# name suggests it mutates anything -- but it does.
#
# That makes installing over heartbeat.sh self-defeating in the worst way: this
# script's FIRST action is an `agent-deck conductor status` call, so it would
# overwrite itself on its own first run and silently revert to the uninstrumented
# template. Verified by installing (6915 bytes, log() present), issuing one
# status call, and re-reading the file (1558 bytes, log() gone).
#
# Two neighbouring files were checked and DO survive regeneration, because
# agent-deck only owns heartbeat.sh by name: HEARTBEAT_RULES.md and this runner.
# The launchd plist also survives, which is what makes this approach work.
#
# WHAT THIS ADDS over the generated version (2026-08-29, bead jbrooksbartlett-8ytz2):
#
#  1. A log line on EVERY invocation. The generated script used
#     `agent-deck session send ... -q`, and -q prints nothing on success, so a
#     successful heartbeat left no trace. heartbeat.log therefore contained
#     nothing but failures and the delivery RATE was unmeasurable. Worse, when
#     the conductor's status was anything other than idle/waiting the script
#     took its silent `fi` branch and logged nothing at all -- so "the heartbeat
#     never fired" and "the heartbeat fired and was skipped" were the same
#     observation.
#
#  2. Escalation to the bead queue after repeated failure. Per the standing rule
#     in ~/.claude/CLAUDE.md ("Unattended work: recorded is not delivered"), a
#     failure written only to a log nobody opens is not reported. Jonny opens the
#     queue; he does not open heartbeat.log.
#
#     A single delivery failure is an AMBIGUOUS failure -- agent-deck cannot
#     always tell a dropped send from an unconfirmed one -- so it must NOT
#     escalate, or the escalation becomes noise. Consecutive failures across a
#     threshold ARE definite evidence, so that is where the bead is filed.

set -uo pipefail

SESSION="conductor-hq"
CONDUCTOR_ROOT="$HOME/.local/share/agent-deck/conductor"
HQ_DIR="$CONDUCTOR_ROOT/hq"
STATE_FILE="${HEARTBEAT_STATE_FILE:-$HQ_DIR/.heartbeat-state}"

# Consecutive failures before filing a bead. Ambiguous-failure discipline: one
# failure proves nothing, three across ~90 minutes is a standing outage.
FAIL_THRESHOLD="${HEARTBEAT_FAIL_THRESHOLD:-3}"

log() {
    # Structured, greppable, one line per invocation. Shares heartbeat.log with
    # agent-deck's own error text on purpose: the prose explaining WHY a send
    # failed is worthless in a different file from the record THAT it failed.
    printf '[HB] %s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

read_consecutive_failures() {
    [ -f "$STATE_FILE" ] || { echo 0; return; }
    local n
    n=$(cat "$STATE_FILE" 2>/dev/null)
    case "$n" in
        ''|*[!0-9]*) echo 0 ;;
        *) echo "$n" ;;
    esac
}

write_consecutive_failures() {
    printf '%s' "$1" >"$STATE_FILE" 2>/dev/null || true
}

# Escalate to the queue. Deduplicates on the marker so a long outage files one
# bead, not one per interval.
escalate() {
    local failures="$1"
    command -v bd >/dev/null 2>&1 || { log "escalate=skipped reason=bd-not-on-path"; return; }

    local marker="HEARTBEAT-DELIVERY-OUTAGE"
    if bd list --status open 2>/dev/null | grep -q "$marker"; then
        log "escalate=skipped reason=already-filed"
        return
    fi

    local title
    title="$marker: conductor heartbeat has failed to deliver ${failures}x consecutively"
    local id
    id=$(bd create "$title" -p 0 --silent 2>/dev/null)
    if [ -n "$id" ]; then
        bd update "$id" -d "Filed automatically by conductor-heartbeat.sh after ${failures} consecutive
delivery failures. The conductor is very likely NOT being nudged, which means
overnight dispatch has stopped.

Check, in order:
  1. tail -30 $HQ_DIR/heartbeat.log      # the [HB] lines carry status= and rc=
  2. agent-deck session show $SESSION --json | grep status
  3. tmux capture-pane -p -t \$(agent-deck session show $SESSION --json \\
       | awk -F'\"' '/tmux_session/{print \$4}') -S -40

Known agent-deck bugs behind this: #876 (send dropped silently), #1413 (typed
but Enter not accepted), #1793 (reached pane, submission unconfirmed).

Clear the counter after fixing: rm $STATE_FILE" >/dev/null 2>&1
        log "escalate=filed bead=$id failures=$failures"
    else
        # bd itself failed. Nothing else to fall back to, so make it loud in the
        # log rather than pretending the escalation happened.
        log "escalate=FAILED reason=bd-create-returned-empty failures=$failures"
    fi
}

# --- conductor enabled? --------------------------------------------------------
if ! agent-deck conductor status --json 2>/dev/null | grep -q '"enabled".*true'; then
    log "status=- action=skipped reason=conductor-disabled"
    exit 0
fi

STATUS=$(agent-deck session show "$SESSION" --json 2>/dev/null | awk -F'"' '/"status"/{print $4; exit}')
[ -n "$STATUS" ] || STATUS="unknown"

# --- assemble the message ------------------------------------------------------
# HEARTBEAT_RULES.md is the per-turn injection point for the conductor's standing
# orders. Lookup order mirrors conductor/bridge.py since PR #218. `[ -f ]` and
# `cat` both follow symlinks, so the live file may be a symlink into the
# version-controlled copy under ~/.claude/docs/ -- which is how it is set up.
RULES_FILE=""
for candidate in \
    "$HQ_DIR/HEARTBEAT_RULES.md" \
    "$CONDUCTOR_ROOT/default/HEARTBEAT_RULES.md" \
    "$CONDUCTOR_ROOT/HEARTBEAT_RULES.md" \
    "$HOME/.agent-deck/conductor/hq/HEARTBEAT_RULES.md" \
    "$HOME/.agent-deck/conductor/default/HEARTBEAT_RULES.md" \
    "$HOME/.agent-deck/conductor/HEARTBEAT_RULES.md"; do
    if [ -f "$candidate" ]; then
        RULES_FILE="$candidate"
        break
    fi
done

MSG="[HEARTBEAT] Check sessions in your group (hq). List any that are waiting, auto-respond where safe, and report what needs my attention."
RULES_STATE="absent"
if [ -n "$RULES_FILE" ]; then
    RULES=$(cat "$RULES_FILE" 2>/dev/null)
    if [ -n "$RULES" ]; then
        MSG="$MSG

$RULES"
        RULES_STATE="loaded"
    else
        RULES_STATE="empty"
    fi
fi

# --- send, but only when the conductor can actually receive ---------------------
# `running` means mid-turn; injecting then would interrupt it. That skip is
# CORRECT, but it must be visible: a conductor that stays `running` for hours
# receives no nudge, and before this log line that was indistinguishable from a
# heartbeat that never fired.
if [ "$STATUS" != "idle" ] && [ "$STATUS" != "waiting" ]; then
    log "status=$STATUS action=skipped reason=not-receptive rules=$RULES_STATE"
    exit 0
fi

agent-deck session send "$SESSION" "$MSG" --no-wait -q
RC=$?

if [ "$RC" -eq 0 ]; then
    log "status=$STATUS action=sent rc=0 rules=$RULES_STATE"
    write_consecutive_failures 0
else
    FAILURES=$(( $(read_consecutive_failures) + 1 ))
    write_consecutive_failures "$FAILURES"
    log "status=$STATUS action=send-failed rc=$RC consecutive=$FAILURES rules=$RULES_STATE"
    if [ "$FAILURES" -ge "$FAIL_THRESHOLD" ]; then
        escalate "$FAILURES"
    fi
fi

exit 0
