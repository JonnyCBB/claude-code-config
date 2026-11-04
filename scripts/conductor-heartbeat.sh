#!/bin/bash
# Heartbeat runner for conductor: hq (profile: default)
# Sends a check-in message to the conductor session (non-blocking).
#
# THIS SUPERSEDES agent-deck's generated heartbeat.sh. It is installed as
#   ~/.local/share/agent-deck/conductor/hq/heartbeat-runner.sh
# and the scheduler is pointed at it by scripts/install-conductor-heartbeat.sh.
#
# The scheduler differs by host, and its interval is not a constant worth
# quoting here:
#   macOS  launchd job     ~/Library/LaunchAgents/com.agentdeck.conductor-heartbeat.hq.plist
#          read it with:   launchctl print "gui/$(id -u)/com.agentdeck.conductor-heartbeat.hq"
#   Linux  systemd timer   ~/.config/systemd/user/conductor-heartbeat-hq.timer
#          read it with:   systemctl --user list-timers conductor-heartbeat-hq.timer
# The same conductor has run under both, at different intervals, so a number
# written here would be wrong on one of them.
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
# The scheduler's own job definition lives outside the conductor directory
# altogether and also survives, which is what makes this approach work.
#
# WHAT THIS ADDS over the generated version (2026-08-29, bead hq-8ytz2):
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
#
#  3. THE SENDER'S EXIT CODE IS NOT ALLOWED TO DECIDE, ON ITS OWN, THAT A
#     HEARTBEAT WAS LOST. Added 2026-09-11, and it is what makes item 2 safe to
#     deploy at all.
#
#     `agent-deck session send` reports a message as NOT delivered when it
#     cannot observe the recipient accepting it -- and "cannot observe" is not
#     "did not happen". Reproduced on this host on 2026-09-11 against a
#     throwaway Claude target, in BOTH send paths, including the `--no-wait -q`
#     path this script uses:
#
#       exit 1, "message reached the pane but submission was never confirmed
#       after 30 checks (issue #1793) ... Treat this as NOT delivered"
#
#     and the target answered the message a few minutes later. Upstream tracks
#     this as asheshgoplani/agent-deck#1978 (open, accepted, p1). The verdict
#     has also been seen wrong in the other direction -- exit 0 for a message
#     that never submitted -- so neither exit code is evidence by itself.
#
#     Left unguarded, that alone breaks item 2: three ordinary busy-conductor
#     heartbeats would trip FAIL_THRESHOLD and file a P0 bead about a channel
#     that is working. So the counter is cleared by a RECEIPT, from the
#     receiving end:
#
#       the conductor appends a UTC timestamp to heartbeat-received.log as the
#       first action of every heartbeat it processes (section 0 of
#       HEARTBEAT_RULES.md). A receipt dated at or after our last send proves
#       that send arrived, whatever the sender concluded.
#
#     The receipt is checked on the NEXT invocation, not inline: a heartbeat
#     that lands while the conductor is mid-turn is queued and consumed at the
#     end of that turn, which can be minutes later. Waiting for it here would
#     block the scheduler for a message that is already delivered.
#
#     So the counter does not count exit codes at all. It counts CONSECUTIVE
#     SENDS THAT HAVE NOT BEEN SHOWN TO ARRIVE, and `rc` survives only as a
#     log field. That is both stricter and simpler than counting failures:
#
#       - a send the tool called delivered, that never arrived, now counts --
#         under the old rule `rc=0` reset the counter, so the false-POSITIVE
#         direction could run forever without ever escalating;
#       - a send the tool called undelivered, that did arrive, now does not.
#
#     What escalation can therefore prove, and all it claims, is that the
#     conductor has not PROCESSED a check-in across FAIL_THRESHOLD consecutive
#     sends. That is the fact worth waking someone for -- the conductor has
#     stopped taking stock -- and it is true whichever way the sender was wrong.
#
#     A tick that correctly declines to send counts nothing. A conductor busy
#     for hours is working, not broken.
#
#  4. A SECOND COUNTER, for the hole the first one structurally cannot cover.
#     No send is attempted unless the conductor's status reads idle or waiting,
#     so if `agent-deck session show` cannot report a status at all -- a dead or
#     unregistered session -- the arrival counter never advances and nothing is
#     ever filed. Found in review against a dead session: three ticks, nothing
#     attempted, nothing escalated, and it would have stayed that way
#     indefinitely while every tick wrote a log line nobody opens.
#
#     "the target cannot be interrogated" is the DEFINITE kind of failure, so it
#     escalates on its own counter and its own bead. "the conductor is busy" is
#     the ambiguous kind -- it is what a working conductor looks like -- and is
#     deliberately never escalated here.

set -uo pipefail

SESSION="conductor-hq"
CONDUCTOR_ROOT="$HOME/.local/share/agent-deck/conductor"
# CONDUCTOR_HQ_DIR is honoured because install-conductor-heartbeat.sh honours it.
# With only one side honouring it, pointing the installer at a test directory made
# it report the receipt count of a file this script never reads -- a check that
# passes while reading the wrong thing.
HQ_DIR="${CONDUCTOR_HQ_DIR:-$CONDUCTOR_ROOT/hq}"
STATE_FILE="${HEARTBEAT_STATE_FILE:-$HQ_DIR/.heartbeat-state}"

# The conductor's own arrival record. Written by the conductor, read here: this
# is the only instrument on the box that reports what ARRIVED rather than what
# was attempted. See item 3 in the header.
RECEIPT_LOG="${HEARTBEAT_RECEIPT_LOG:-$HQ_DIR/heartbeat-received.log}"

# Consecutive unarrived sends before filing a bead. Ambiguous-failure
# discipline: one proves nothing, three in a row is a conductor that has
# stopped taking stock.
FAIL_THRESHOLD="${HEARTBEAT_FAIL_THRESHOLD:-3}"

# One spelling of the timestamp format, because three things have to agree on
# it: what we stamp a send with, what the conductor writes into the receipt log
# (section 0 of HEARTBEAT_RULES.md), and the shape receipt_since will accept.
# When they disagree the comparison stops matching and the failure direction is
# "no receipt", which is the input to escalation.
now_utc() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}

log() {
    # Structured, greppable, one line per invocation. Shares heartbeat.log with
    # agent-deck's own error text on purpose: the prose explaining WHY a send
    # failed is worthless in a different file from the record THAT it failed.
    printf '[HB] %s %s\n' "$(now_utc)" "$*"
}

# State is one line, two space-separated fields: "<unarrived> <last_send_ts>".
# Sets UNARRIVED and LAST_SEND directly rather than returning them to be
# re-split.
#
# A ONE-FIELD FILE IS DISCARDED, NOT CARRIED FORWARD, and that is the whole
# reason this needs a comment. An earlier version of this script wrote a bare
# integer counting SEND FAILURES -- the rule this one repudiates. Carrying that
# number into an arrival-based counter would mean the first run after an upgrade
# files a P0 whose title claims nothing has been PROCESSED, built entirely from
# exit codes, with `prev_send=none-on-record` on the same log line contradicting
# it. On any host where the old version ran that count is expected to be at or
# above the threshold already, so this is the normal case rather than a corner.
# A count with no arrival provenance is not evidence, so it starts at zero.
read_state() {
    UNARRIVED=0
    LAST_SEND=""
    [ -f "$STATE_FILE" ] && read -r UNARRIVED LAST_SEND <"$STATE_FILE"
    case "$UNARRIVED" in ''|*[!0-9]*) UNARRIVED=0 ;; esac
    if [ -z "$LAST_SEND" ]; then
        LAST_SEND="-"
        UNARRIVED=0
    fi
}

write_state() {
    printf '%s %s' "$1" "$2" >"$STATE_FILE" 2>/dev/null || true
}

# Did a heartbeat ARRIVE at or after $1? Answered from the receiving end, so it
# is independent of the sender's verdict -- which is the whole point (header
# item 3). ISO-8601 UTC sorts lexicographically, so a string compare is a time
# compare, and the regex means a hand-annotated or truncated line cannot be
# mistaken for a timestamp.
#
# Reads only the TAIL. The log is append-only and ascending, so the answer
# depends on the newest lines alone, and it grows by about one line per tick
# forever -- scanning from line 1 is the only unbounded work this script did.
# Ten lines is margin against a burst: duplicate deliveries have been observed
# arriving in pairs.
#
# KNOWN LIMIT, AND IT IS DELIBERATE. A receipt carries a timestamp and no
# correlation id, so a receipt written when the conductor finally consumes a
# heartbeat that was queued several ticks ago will also clear the count for a
# LATER send that was genuinely dropped. Distinguishing them needs a nonce in
# the message echoed back into the receipt, which is a change to the conductor's
# standing orders rather than to this script. Two reasons it is left as is: the
# error runs toward NOT escalating, which is the safe direction for an ambiguous
# signal; and measured on this host on 2026-09-11, across every conductor
# transcript there was exactly one heartbeat ever queued and it was absorbed
# five seconds later, so a heartbeat pending across ticks is not an observed
# state.
receipt_since() {
    local since="$1"
    [ "$since" = "-" ] && return 1
    [ -f "$RECEIPT_LOG" ] || return 1
    tail -n 10 "$RECEIPT_LOG" 2>/dev/null | awk -v since="$since" '
        /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z$/ \
            && $0 >= since { found = 1 }
        END { exit(found ? 0 : 1) }
    '
}

# Escalate to the queue. Deduplicates on the marker so a long outage files one
# bead, not one per interval.
escalate() {
    local unarrived="$1"
    command -v bd >/dev/null 2>&1 || { log "escalate=skipped reason=bd-not-on-path"; return; }

    local marker="HEARTBEAT-NOT-PROCESSED"
    if bd list --status open 2>/dev/null | grep -q "$marker"; then
        log "escalate=skipped reason=already-filed"
        return
    fi

    local title
    title="$marker: the conductor has not processed a heartbeat across ${unarrived} consecutive sends"
    local id
    id=$(bd create "$title" -p 0 --silent 2>/dev/null)
    if [ -n "$id" ]; then
        bd update "$id" -d "Filed automatically by conductor-heartbeat.sh after ${unarrived} consecutive
sends produced no receipt in
$RECEIPT_LOG. The conductor has stopped taking stock, which means
overnight dispatch has stopped.

THE CLAIM IS ABOUT ARRIVAL, NOT ABOUT THE SENDER'S EXIT CODE, and the exit code
is deliberately not part of it. agent-deck reports a delivered message as NOT
delivered when it cannot observe the recipient accepting it (upstream
asheshgoplani/agent-deck#1978, open; reproduced locally 2026-09-11 in both send
paths), and has also been seen reporting success for a message that never
submitted. Neither direction is evidence. A missing receipt is, because the
conductor writes one for every heartbeat it processes.

So do not start by asking whether the sends failed. Start by asking why nothing
the conductor received got as far as a receipt.

Check, in order:
  1. tail -30 $HQ_DIR/heartbeat.log      # the [HB] lines carry status=, rc= and prev_send=
  2. tail -5 $RECEIPT_LOG                # last time a heartbeat actually ARRIVED
  3. agent-deck session show $SESSION --json | grep status
  4. tmux capture-pane -p -t \$(agent-deck session show $SESSION --json \\
       | awk -F'\"' '/tmux_session/{print \$4}') -S -40

Read the pane BEFORE concluding the message is absent: a body sitting under
'Press up to edit queued messages' has arrived and will be consumed at the end
of the current turn.

Known agent-deck bugs behind a non-zero exit, if you see one in the log: #876
(send dropped silently -- the body is NOT in the pane, which is the genuine
case), #1413 (typed but Enter not accepted), #1793 (reached pane, submission
unconfirmed -- usually a FALSE negative).

Clear the counter after fixing: rm $STATE_FILE" >/dev/null 2>&1
        log "escalate=filed bead=$id unarrived=$unarrived"
    else
        # bd itself failed. Nothing else to fall back to, so make it loud in the
        # log rather than pretending the escalation happened.
        log "escalate=FAILED reason=bd-create-returned-empty unarrived=$unarrived"
    fi
}

# The other way the conductor stops being nudged, and it is a DIFFERENT
# diagnosis: the session cannot be interrogated at all, so no send is attempted
# and the arrival counter can never advance. Filed separately from
# HEARTBEAT-NOT-PROCESSED because the first thing to check is different -- there,
# whether the conductor is processing; here, whether the session still exists.
escalate_unaskable() {
    local ticks="$1"
    command -v bd >/dev/null 2>&1 || { log "escalate=skipped reason=bd-not-on-path"; return; }

    local marker="HEARTBEAT-SESSION-UNREACHABLE"
    if bd list --status open 2>/dev/null | grep -q "$marker"; then
        log "escalate=skipped reason=already-filed"
        return
    fi

    local id
    id=$(bd create "$marker: agent-deck cannot report the conductor session's status, ${ticks} ticks running" \
         -p 0 --silent 2>/dev/null)
    if [ -n "$id" ]; then
        bd update "$id" -d "Filed automatically by conductor-heartbeat.sh after ${ticks} consecutive ticks
where 'agent-deck session show $SESSION --json' returned no status field.

NO HEARTBEAT HAS BEEN ATTEMPTED ON THOSE TICKS, deliberately: sending blind
could interrupt a working conductor. So the arrival counter cannot advance
either, and without this bead the state is invisible except in the log -- every
tick writing 'status=unavailable action=skipped' and nothing else, indefinitely.

This is the DEFINITE kind of failure rather than the ambiguous kind: a conductor
reported as busy is what a working conductor looks like, but a conductor whose
status cannot be read at all is not a state anything healthy produces.

Check, in order:
  1. agent-deck session show $SESSION --json        # does it resolve at all?
  2. agent-deck list | grep $SESSION                # is the session still registered?
  3. tmux list-sessions | grep conductor            # is the pane still alive?
  4. tail -30 $HQ_DIR/heartbeat.log                 # the [HB] lines carry unaskable=

If the session is gone, restarting it is what clears this. Do NOT assume the
session is dead because one status read failed -- confirm it across two reads,
per the liveness rule in the conductor's own instructions.

Clear the counter after fixing: rm $UNASKABLE_FILE" >/dev/null 2>&1
        log "escalate=filed bead=$id unaskable=$ticks"
    else
        log "escalate=FAILED reason=bd-create-returned-empty unaskable=$ticks"
    fi
}

# --- settle the PREVIOUS send before doing anything new ------------------------
read_state
if [ "$LAST_SEND" = "-" ]; then
    PREV_SEND="none-on-record"
elif receipt_since "$LAST_SEND"; then
    PREV_SEND="arrived"
    UNARRIVED=0
else
    PREV_SEND="no-receipt-since-$LAST_SEND"
fi
# Persisted HERE, before any branch runs, so a confirmation resolved above
# cannot be lost to an early `exit 0`. A path added below is then safe by
# construction rather than by remembering to repeat the write.
write_state "$UNARRIVED" "$LAST_SEND"

# skip() is the only way out that is not a send: log why, and go. The state is
# already written, so nothing here has to remember to persist it.
skip() {
    log "$*"
    exit 0
}

# UNASKABLE is a separate counter from UNARRIVED and has to be, because the two
# are different kinds of evidence.
#
# UNARRIVED counts sends that were not shown to arrive. UNASKABLE counts ticks
# where `agent-deck session show` could not tell us the conductor's status at
# all -- so no send is even attempted, and the arrival counter can never
# advance. Without this the alarm cannot fire for the state its own bead text
# describes: a session that has died leaves every tick logging
# "status=unavailable action=skipped", attempting nothing, escalating nothing,
# forever, while receipts also stop because nothing is being delivered.
#
# Per the standing rule on definite versus ambiguous failure, "the target cannot
# be interrogated" is the DEFINITE kind -- unlike "the conductor is busy", which
# is what a working conductor looks like and is deliberately never escalated
# here. It still waits for FAIL_THRESHOLD consecutive ticks rather than firing on
# the first, because one failed CLI call is a hiccup and this must not become
# noise.
UNASKABLE_FILE="${HEARTBEAT_UNASKABLE_FILE:-$STATE_FILE.unaskable}"
read_unaskable() {
    UNASKABLE=0
    [ -f "$UNASKABLE_FILE" ] && read -r UNASKABLE <"$UNASKABLE_FILE"
    case "$UNASKABLE" in ''|*[!0-9]*) UNASKABLE=0 ;; esac
}
write_unaskable() {
    printf '%s' "$1" >"$UNASKABLE_FILE" 2>/dev/null || true
}

# --- conductor enabled? --------------------------------------------------------
if ! agent-deck conductor status --json 2>/dev/null | grep -q '"enabled".*true'; then
    skip "status=- action=skipped reason=conductor-disabled prev_send=$PREV_SEND"
fi

STATUS=$(agent-deck session show "$SESSION" --json 2>/dev/null | awk -F'"' '/"status"/{print $4; exit}')
# An unreadable status is NOT the same thing as a conductor that is busy, and
# the original silent `fi` branch reported them identically. Both still skip --
# sending blind could interrupt a working conductor -- but they are now
# distinguishable in the log, which is what a diagnosis needs.
#
# "unavailable" rather than "unknown" deliberately: agent-deck's own status
# vocabulary already contains `unknown` as the value it prints for a status it
# cannot classify, so reusing that word would have made "agent-deck does not
# know" and "we could not ask agent-deck" the same log line -- the collision
# this branch exists to remove.
read_unaskable
if [ -n "$STATUS" ]; then
    write_unaskable 0
else
    STATUS="unavailable"
    UNASKABLE=$((UNASKABLE + 1))
    write_unaskable "$UNASKABLE"
fi

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
    REASON=not-receptive
    if [ "$STATUS" = "unavailable" ]; then
        REASON=status-unavailable
        log "status=$STATUS action=skipped reason=$REASON unaskable=$UNASKABLE rules=$RULES_STATE prev_send=$PREV_SEND"
        [ "$UNASKABLE" -ge "$FAIL_THRESHOLD" ] && escalate_unaskable "$UNASKABLE"
        exit 0
    fi
    skip "status=$STATUS action=skipped reason=$REASON rules=$RULES_STATE prev_send=$PREV_SEND"
fi

# Both the increment and the timestamp are persisted BEFORE the send, not after.
# `session send` is the command that spends up to 50 verification checks, and
# these hosts sleep, reload timers and reboot; killed in flight, a send recorded
# only afterwards would have happened while leaving no trace, and the next tick
# would compare receipts against a stale timestamp or report none-on-record. The
# stamp being pre-send is also what makes a receipt written during the send's own
# verification count as at-or-after it.
SEND_TS=$(now_utc)
# Every send counts as unarrived until a receipt says otherwise, whatever RC
# says. RC is logged and nothing more -- header item 3. The next invocation
# clears the count if the receipt shows up, which on a healthy channel is every
# time, so this never climbs above 1.
UNARRIVED=$((UNARRIVED + 1))
write_state "$UNARRIVED" "$SEND_TS"

agent-deck session send "$SESSION" "$MSG" --no-wait -q
RC=$?

log "status=$STATUS action=sent rc=$RC unarrived=$UNARRIVED rules=$RULES_STATE prev_send=$PREV_SEND"
if [ "$UNARRIVED" -ge "$FAIL_THRESHOLD" ]; then
    escalate "$UNARRIVED"
fi

exit 0
