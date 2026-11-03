#!/bin/bash
# Tests for scripts/conductor-heartbeat.sh
#
# That script runs unattended on the scheduler's interval -- read it from the
# host rather than assuming, the two hosts differ -- and decides whether the
# conductor gets nudged at all. A wrong character here stops overnight dispatch
# silently, which is exactly the failure class it was written to detect, so it
# is tested like the program it is.
#
# Run: bash scripts/tests/test-conductor-heartbeat.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$SCRIPT_DIR/conductor-heartbeat.sh"

PASS=0
FAIL=0

# Bootstrap-RED sentinel, matching scripts/tests/test-conductor-signals.sh and
# test-reclaim-worktrees.sh. Without it a harness that recorded zero assertions
# would print "0 passed, 0 failed" and exit 0 -- green. This repo has no CI, so
# this suite is the only gate and it has to prove it can report a failure.
#   EXPECT_BOOTSTRAP_RED=1 bash scripts/tests/test-conductor-heartbeat.sh
# must exit non-zero and show exactly one FAIL.
BOOTSTRAP_RED=${EXPECT_BOOTSTRAP_RED:-0}

pass() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n     %s\n' "$1" "${2:-}"; }

# expect_log collapses the assertion this suite makes most: "the run logged
# this". The label is written once, so the pass and fail messages cannot drift.
expect_log() {
    if grep -q "$2" <<<"$OUT"; then pass "$1"; else fail "$1" "got: $OUT"; fi
}

# Reaps the PREVIOUS sandbox, never the current one: the assertions after each
# case still read $SANDBOX and $STATE, so reaping the current one would delete
# the evidence before it is checked. Called at the top of every case and once
# more on exit, which is what takes the litter to zero -- unreaped, this suite
# left 16 directories in /tmp per run.
reap_sandbox() {
    [ -n "${SANDBOX:-}" ] && [ -d "$SANDBOX" ] && rm -r -- "$SANDBOX"
    return 0
}
trap reap_sandbox EXIT

# Each case runs the real script against fake `agent-deck` and `bd` binaries on a
# shim PATH, so nothing touches the live conductor or the real bead queue.
run_case() {
    local name="$1" ad_status="$2" ad_send_rc="$3" enabled="$4"
    # $5 is the raw state-file contents, so a case can seed either the historical
    # bare integer ("2") or the current two-field form ("2 2026-09-11T10:00:00Z").
    local initial_state="${5:-}" bd_list_out="${6:-}" receipts="${7:-}"

    reap_sandbox

    SANDBOX=$(mktemp -d)
    BIN="$SANDBOX/bin"; mkdir -p "$BIN"

    cat >"$BIN/agent-deck" <<EOF
#!/bin/bash
case "\$*" in
  *"conductor status"*) echo '{"enabled": $enabled}' ;;
  *"session show"*)     echo '{"status": "$ad_status"}' ;;
  *"session send"*)     echo "\$*" >>"$SANDBOX/sent.txt"; exit $ad_send_rc ;;
esac
EOF

    cat >"$BIN/bd" <<EOF
#!/bin/bash
case "\$1" in
  list)   printf '%s\n' "$bd_list_out" ;;
  create) echo "\$*" >>"$SANDBOX/bd-create.txt"; echo "fake-bead-id" ;;
  update) echo "\$*" >>"$SANDBOX/bd-update.txt" ;;
esac
EOF
    chmod +x "$BIN/agent-deck" "$BIN/bd"

    STATE="$SANDBOX/state"
    [ -n "$initial_state" ] && printf '%s' "$initial_state" >"$STATE"

    # The receipt log is the conductor's own arrival record. An empty string
    # means the file does not exist at all, which is a state the script must
    # survive -- not the same as an existing file with no matching line.
    RECEIPTS="$SANDBOX/heartbeat-received.log"
    [ -n "$receipts" ] && printf '%s\n' "$receipts" >"$RECEIPTS"

    OUT=$(PATH="$BIN:$PATH" HOME="$SANDBOX" \
          HEARTBEAT_STATE_FILE="$STATE" \
          HEARTBEAT_RECEIPT_LOG="$RECEIPTS" \
          bash "$TARGET" 2>&1)
    RC=$?
}

echo "== conductor-heartbeat.sh =="

# 0. The harness has to be able to report a failure. See the sentinel above.
if [ "$BOOTSTRAP_RED" = "1" ]; then
    fail "bootstrap-RED sentinel: deliberate FAIL (proves this suite can go red)"
else
    pass "harness sanity"
fi

# 1. Every invocation logs. This is the whole point: before it, a successful
#    heartbeat wrote nothing and the delivery rate could not be measured.
run_case "sent" idle 0 true
expect_log "logs a line on every send" '^\[HB\] .* action=sent rc=0'

# 2. The silent-skip hole. A conductor stuck 'running' got no nudge AND no log,
#    making "never fired" and "fired but skipped" indistinguishable.
run_case "running" running 0 true
expect_log "logs the skip when the conductor is not receptive" 'action=skipped reason=not-receptive'
if [ ! -f "$SANDBOX/sent.txt" ]; then
    pass "does not inject into a mid-turn conductor"
else
    fail "does not inject into a mid-turn conductor" "a send happened"
fi

# 3. THE COUNTER COUNTS ARRIVAL, NOT EXIT CODES. A send is unarrived until a
#    receipt says otherwise, so rc is logged and nothing more. Reproduced on the
#    VM 2026-09-11: the sender exits 1 with "(issue #1793) ... Treat this as NOT
#    delivered" for a message the target then answers (upstream
#    asheshgoplani/agent-deck#1978, open).
run_case "unconfirmed" idle 1 true
expect_log "a non-zero exit is logged as a send, with rc as a field" 'action=sent rc=1 unarrived=1'

# 4. Ambiguous-failure discipline: ONE unarrived send must not escalate.
if [ ! -f "$SANDBOX/bd-create.txt" ]; then
    pass "does not escalate on a single unarrived send"
else
    fail "does not escalate on a single unarrived send" "filed a bead too early"
fi

# 5. THE FALSE-POSITIVE DIRECTION MUST ESCALATE TOO. The sender has also been
#    seen reporting success for a message that never submitted, and the old rule
#    reset the counter on rc=0 -- so that direction could run forever without
#    ever filing anything. rc=0 here, nothing arriving, and it still escalates.
run_case "rc0-nothing-arrives" idle 0 true "2 2026-09-11T10:00:00Z"
expect_log "counts a successful-looking send that did not arrive" 'action=sent rc=0 unarrived=3'
if [ -f "$SANDBOX/bd-create.txt" ] && grep -q 'HEARTBEAT-NOT-PROCESSED' "$SANDBOX/bd-create.txt"; then
    pass "escalates on rc=0 when nothing has arrived across the threshold"
else
    fail "escalates on rc=0 when nothing has arrived across the threshold" "no bead; log: $OUT"
fi

# 6. And the non-zero direction still escalates at the threshold.
run_case "threshold" idle 1 true "2 2026-09-11T10:00:00Z"
if [ -f "$SANDBOX/bd-create.txt" ] && grep -q 'HEARTBEAT-NOT-PROCESSED' "$SANDBOX/bd-create.txt"; then
    pass "escalates at the threshold when the sender also reports failure"
else
    fail "escalates at the threshold when the sender also reports failure" "no bead; log: $OUT"
fi
# The bead has to name arrival rather than the exit code, or it sends the reader
# to diagnose the wrong thing -- which is what the old wording did.
if grep -q 'not processed a heartbeat' "$SANDBOX/bd-create.txt" 2>/dev/null; then
    pass "the bead claims what the evidence supports: nothing was processed"
else
    fail "the bead claims what the evidence supports" "title: $(cat "$SANDBOX/bd-create.txt" 2>/dev/null)"
fi

# 7. Dedup: a long outage files one bead, not one per interval.
run_case "dedup" idle 1 true "5 2026-09-11T10:00:00Z" "open  HEARTBEAT-NOT-PROCESSED: something"
expect_log "does not file a duplicate bead while one is open" 'escalate=skipped reason=already-filed'

# 8. A RECEIPT is what clears the counter. Nothing else does.
run_case "receipt-clears" idle 1 true "2 2026-09-11T10:00:00Z" "" "2026-09-11T10:00:30Z"
expect_log "reports the previous send as arrived when a later receipt exists" 'prev_send=arrived'
expect_log "a receipt clears the carried count before the new send is counted" 'unarrived=1'
if [ ! -f "$SANDBOX/bd-create.txt" ]; then
    pass "does not escalate when the channel is proven to be delivering"
else
    fail "does not escalate when the channel is proven to be delivering" "filed a bead"
fi
# The send timestamp must be recorded, or the next invocation has nothing to
# compare a receipt against and the whole confirmation path is dead code.
if grep -qE '^1 [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$' "$STATE" 2>/dev/null; then
    pass "records the send timestamp alongside the counter"
else
    fail "records the send timestamp alongside the counter" "state=$(cat "$STATE" 2>/dev/null)"
fi

# 9. A receipt from BEFORE the last send is not evidence about that send.
run_case "stale-receipt" idle 1 true "2 2026-09-11T10:00:00Z" "" "2026-09-11T09:59:59Z"
expect_log "a receipt older than the last send does not confirm it" 'prev_send=no-receipt-since-2026-09-11T10:00:00Z'

# 10. A missing receipt log must not crash the run or read as a confirmation.
#     This is the state of a fresh install.
run_case "no-receipt-log" idle 1 true "1 2026-09-11T10:00:00Z"
expect_log "an absent receipt log is not a confirmation" 'prev_send=no-receipt-since-'
expect_log "an absent receipt log leaves the count intact" 'unarrived=2'

# 11. Only the TAIL of the receipt log is read -- it grows by about one line per
#     tick forever, and scanning from line 1 was the only unbounded work here.
#
#     BOTH DIRECTIONS, and getting direction (a) to discriminate took two
#     attempts -- worth recording, because the first two fixtures could not fail.
#     Seeding only lines newer than `since` passes on the newest line alone, so
#     it stays green even at `tail -n 1`. For an ASCENDING log that is not a test
#     artefact, it is a fact: if any line matches, the newest one does too, and
#     one line would genuinely be enough.
#
#     The margin therefore only earns its place for a log that is NOT strictly
#     ascending, which is the case it was written for -- duplicate deliveries
#     have been observed arriving in pairs. So (a) seeds the match followed by
#     OLDER lines, which is what an out-of-order burst looks like, and fails at
#     `tail -n 1`. (b) puts the only match beyond the window and fails if there
#     is no window at all.
TAIL_OUT_OF_ORDER=$(printf '2026-09-11T10:00:30Z\n2026-09-11T09:59:00Z\n2026-09-11T09:59:10Z\n')
run_case "receipt-inside-window" idle 1 true "2 2026-09-11T10:00:00Z" "" "$TAIL_OUT_OF_ORDER"
expect_log "finds a matching receipt that is not the newest line" 'prev_send=arrived'

# The only matching receipt is 20 lines back, beyond the 10-line window, and
# every newer line is older than `since`. Found => there is no window.
TAIL_BEYOND=$(printf '2026-09-11T10:00:30Z\n'; for i in $(seq 1 20); do printf '2026-09-10T09:%02d:00Z\n' "$i"; done)
run_case "receipt-beyond-window" idle 1 true "2 2026-09-11T10:00:00Z" "" "$TAIL_BEYOND"
expect_log "does not read past the tail window" 'prev_send=no-receipt-since-2026-09-11T10:00:00Z'

# 12. A state file written by the earlier version holds a bare integer, and that
#     integer counted SEND FAILURES under the rule this script repudiates.
#     Carrying it forward would file a P0 on the first run after an upgrade,
#     titled "has not processed a heartbeat", built entirely from exit codes --
#     and on any host where the old version ran the count is expected to be at
#     or above the threshold already. A count with no arrival provenance is not
#     evidence, so it must be discarded.
run_case "legacy-state" idle 1 true "3"
expect_log "discards a legacy failure count rather than carrying it" 'unarrived=1'
expect_log "a legacy state file has no send to settle" 'prev_send=none-on-record'
if [ ! -f "$SANDBOX/bd-create.txt" ]; then
    pass "a legacy state file does not file a P0 on the first run"
else
    fail "a legacy state file does not file a P0 on the first run" \
         "filed: $(cat "$SANDBOX/bd-create.txt" 2>/dev/null)"
fi

# 13. A confirmation resolved on a tick that then SKIPS must be persisted. If the
#     skip path dropped it, a busy conductor would keep a stale count forever and
#     eventually escalate on evidence that had already been overturned.
run_case "skip-persists" running 0 true "2 2026-09-11T10:00:00Z" "" "2026-09-11T10:00:30Z"
expect_log "the skip path still settles the previous send" 'action=skipped'
expect_log "the skip path reports the settled result" 'prev_send=arrived'
if [ "$(cut -d' ' -f1 "$STATE" 2>/dev/null)" = "0" ]; then
    pass "the skip path persists the cleared counter"
else
    fail "the skip path persists the cleared counter" "state=$(cat "$STATE" 2>/dev/null)"
fi

# 14. Disabled conductor is a legitimate quiet state, but still leaves a trace.
run_case "disabled" idle 0 false
expect_log "logs when the conductor is disabled" 'action=skipped reason=conductor-disabled'

# 15. A missing or failed `session show` must not read as receptive, and must be
#     distinguishable from a conductor that is busy. agent-deck's own vocabulary
#     already uses `unknown` for a status it cannot classify, so this must not
#     reuse that word or the two diagnoses collapse into one log line.
run_case "status-unavailable" "" 0 true
expect_log "treats an unreadable status as not-receptive" 'action=skipped'
expect_log "distinguishes an unreadable status from a busy conductor" 'status=unavailable action=skipped reason=status-unavailable'
if [ ! -f "$SANDBOX/bd-create.txt" ]; then
    pass "one unreadable status does not escalate"
else
    fail "one unreadable status does not escalate" "filed a bead on the first tick"
fi

# 16. A CONDUCTOR THAT CANNOT BE INTERROGATED MUST EVENTUALLY ESCALATE, and this
#     is the hole the arrival counter cannot cover: no send is attempted on those
#     ticks, so `unarrived` never advances, and the state would otherwise be
#     invisible forever except in the log. Verified during review against a dead
#     session: three ticks, nothing attempted, nothing filed.
#
#     "cannot be interrogated" is the DEFINITE kind of failure; "busy" is the
#     ambiguous kind and is deliberately never escalated. So this needs its own
#     counter and its own bead, not a share of the arrival one.
run_case "unaskable-threshold" "" 0 true
printf '2' >"$SANDBOX/state.unaskable"
OUT=$(PATH="$BIN:$PATH" HOME="$SANDBOX" HEARTBEAT_STATE_FILE="$STATE" \
      HEARTBEAT_RECEIPT_LOG="$RECEIPTS" \
      HEARTBEAT_UNASKABLE_FILE="$SANDBOX/state.unaskable" bash "$TARGET" 2>&1)
expect_log "counts consecutive ticks where the status could not be read" 'unaskable=3'
if [ -f "$SANDBOX/bd-create.txt" ] && grep -q 'HEARTBEAT-SESSION-UNREACHABLE' "$SANDBOX/bd-create.txt"; then
    pass "escalates a conductor whose status cannot be read at all"
else
    fail "escalates a conductor whose status cannot be read at all" "no bead; log: $OUT"
fi
# It must be a DIFFERENT bead from the arrival one: the first thing to check is
# whether the session still exists, not whether the conductor is processing.
if ! grep -q 'HEARTBEAT-NOT-PROCESSED' "$SANDBOX/bd-create.txt" 2>/dev/null; then
    pass "files the unreachable-session bead, not the not-processed one"
else
    fail "files the unreachable-session bead, not the not-processed one" \
         "filed: $(cat "$SANDBOX/bd-create.txt" 2>/dev/null)"
fi

# 17. And a status that CAN be read clears that counter, so an old outage cannot
#     produce a late bead once the session is back.
run_case "unaskable-clears" idle 0 true
printf '9' >"$SANDBOX/state.unaskable"
PATH="$BIN:$PATH" HOME="$SANDBOX" HEARTBEAT_STATE_FILE="$STATE" \
    HEARTBEAT_RECEIPT_LOG="$RECEIPTS" \
    HEARTBEAT_UNASKABLE_FILE="$SANDBOX/state.unaskable" bash "$TARGET" >/dev/null 2>&1
if [ "$(cat "$SANDBOX/state.unaskable" 2>/dev/null)" = "0" ]; then
    pass "a readable status clears the unreachable counter"
else
    fail "a readable status clears the unreachable counter" \
         "counter=$(cat "$SANDBOX/state.unaskable" 2>/dev/null)"
fi

# 10. The standing orders must actually reach the message. If HEARTBEAT_RULES.md
#     stops being picked up, the conductor silently loses its dispatch rules --
#     the failure Priority 1 exists to prevent, reintroduced by a path typo.
reap_sandbox; SANDBOX=$(mktemp -d); BIN="$SANDBOX/bin"; mkdir -p "$BIN"
mkdir -p "$SANDBOX/.local/share/agent-deck/conductor/hq"
echo "PARK-AND-CONTINUE-SENTINEL" >"$SANDBOX/.local/share/agent-deck/conductor/hq/HEARTBEAT_RULES.md"
cat >"$BIN/agent-deck" <<EOF
#!/bin/bash
case "\$*" in
  *"conductor status"*) echo '{"enabled": true}' ;;
  *"session show"*)     echo '{"status": "idle"}' ;;
  *"session send"*)     echo "\$*" >>"$SANDBOX/sent.txt" ;;
esac
EOF
chmod +x "$BIN/agent-deck"
OUT=$(PATH="$BIN:$PATH" HOME="$SANDBOX" HEARTBEAT_STATE_FILE="$SANDBOX/state" bash "$TARGET" 2>&1)
if grep -q 'PARK-AND-CONTINUE-SENTINEL' "$SANDBOX/sent.txt" 2>/dev/null; then
    pass "injects HEARTBEAT_RULES.md contents into the message"
else
    fail "injects HEARTBEAT_RULES.md contents into the message" "sent: $(cat "$SANDBOX/sent.txt" 2>/dev/null)"
fi
if grep -q 'rules=loaded' <<<"$OUT"; then
    pass "records that the rules file was loaded"
else
    fail "records that the rules file was loaded" "got: $OUT"
fi

# 11. A symlinked rules file must resolve -- the live file points into the
#     version-controlled copy under ~/.claude/docs/, so if symlinks did not
#     work the rules would silently vanish.
reap_sandbox; SANDBOX=$(mktemp -d); BIN="$SANDBOX/bin"; mkdir -p "$BIN"
mkdir -p "$SANDBOX/.local/share/agent-deck/conductor/hq" "$SANDBOX/real"
echo "SYMLINK-SENTINEL" >"$SANDBOX/real/rules.md"
ln -s "$SANDBOX/real/rules.md" "$SANDBOX/.local/share/agent-deck/conductor/hq/HEARTBEAT_RULES.md"
cat >"$BIN/agent-deck" <<EOF
#!/bin/bash
case "\$*" in
  *"conductor status"*) echo '{"enabled": true}' ;;
  *"session show"*)     echo '{"status": "idle"}' ;;
  *"session send"*)     echo "\$*" >>"$SANDBOX/sent.txt" ;;
esac
EOF
chmod +x "$BIN/agent-deck"
PATH="$BIN:$PATH" HOME="$SANDBOX" HEARTBEAT_STATE_FILE="$SANDBOX/state" bash "$TARGET" >/dev/null 2>&1
if grep -q 'SYMLINK-SENTINEL' "$SANDBOX/sent.txt" 2>/dev/null; then
    pass "resolves a symlinked HEARTBEAT_RULES.md"
else
    fail "resolves a symlinked HEARTBEAT_RULES.md" "sent: $(cat "$SANDBOX/sent.txt" 2>/dev/null)"
fi

echo
echo "passed: $PASS   failed: $FAIL"
[ "$FAIL" -eq 0 ]
