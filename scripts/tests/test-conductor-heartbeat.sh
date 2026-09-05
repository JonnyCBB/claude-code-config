#!/bin/bash
# Tests for scripts/conductor-heartbeat.sh
#
# This script runs unattended every 30 minutes and decides whether the conductor
# gets nudged at all. A wrong character here stops overnight dispatch silently,
# which is exactly the failure class it was written to detect -- so it is tested
# like the program it is.
#
# Run: bash scripts/tests/test-conductor-heartbeat.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$SCRIPT_DIR/conductor-heartbeat.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n     %s\n' "$1" "${2:-}"; }

# Each case runs the real script against fake `agent-deck` and `bd` binaries on a
# shim PATH, so nothing touches the live conductor or the real bead queue.
run_case() {
    local name="$1" ad_status="$2" ad_send_rc="$3" enabled="$4"
    local initial_failures="${5:-}" bd_list_out="${6:-}"

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
    [ -n "$initial_failures" ] && printf '%s' "$initial_failures" >"$STATE"

    OUT=$(PATH="$BIN:$PATH" HOME="$SANDBOX" \
          HEARTBEAT_STATE_FILE="$STATE" \
          bash "$TARGET" 2>&1)
    RC=$?
}

echo "== conductor-heartbeat.sh =="

# 1. Every invocation logs. This is the whole point: before it, a successful
#    heartbeat wrote nothing and the delivery rate could not be measured.
run_case "sent" idle 0 true
if grep -q '^\[HB\] .* action=sent rc=0' <<<"$OUT"; then
    pass "logs a line on successful send"
else
    fail "logs a line on successful send" "got: $OUT"
fi

# 2. The silent-skip hole. A conductor stuck 'running' got no nudge AND no log,
#    making "never fired" and "fired but skipped" indistinguishable.
run_case "running" running 0 true
if grep -q 'action=skipped reason=not-receptive' <<<"$OUT"; then
    pass "logs the skip when the conductor is not receptive"
else
    fail "logs the skip when the conductor is not receptive" "got: $OUT"
fi
if [ ! -f "$SANDBOX/sent.txt" ]; then
    pass "does not inject into a mid-turn conductor"
else
    fail "does not inject into a mid-turn conductor" "a send happened"
fi

# 3. A failed send must be recorded as failed, and must count.
run_case "failed" idle 1 true
if grep -q 'action=send-failed rc=1 consecutive=1' <<<"$OUT"; then
    pass "counts the first failure"
else
    fail "counts the first failure" "got: $OUT"
fi

# 4. Ambiguous-failure discipline: ONE failure must not escalate.
if [ ! -f "$SANDBOX/bd-create.txt" ]; then
    pass "does not escalate on a single failure"
else
    fail "does not escalate on a single failure" "filed a bead too early"
fi

# 5. Consecutive failures across the threshold ARE definite -- escalate.
run_case "threshold" idle 1 true 2
if [ -f "$SANDBOX/bd-create.txt" ] && grep -q 'HEARTBEAT-DELIVERY-OUTAGE' "$SANDBOX/bd-create.txt"; then
    pass "escalates to the queue at the failure threshold"
else
    fail "escalates to the queue at the failure threshold" "no bead filed; log: $OUT"
fi

# 6. Dedup: a long outage files one bead, not one per interval.
run_case "dedup" idle 1 true 5 "open  HEARTBEAT-DELIVERY-OUTAGE: something"
if grep -q 'escalate=skipped reason=already-filed' <<<"$OUT"; then
    pass "does not file a duplicate bead while one is open"
else
    fail "does not file a duplicate bead while one is open" "got: $OUT"
fi

# 7. A success resets the counter, so an old outage cannot trigger a late bead.
run_case "reset" idle 0 true 2
if [ "$(cat "$STATE" 2>/dev/null)" = "0" ]; then
    pass "resets the failure counter on success"
else
    fail "resets the failure counter on success" "counter=$(cat "$STATE" 2>/dev/null)"
fi

# 8. Disabled conductor is a legitimate quiet state, but still leaves a trace.
run_case "disabled" idle 0 false
if grep -q 'action=skipped reason=conductor-disabled' <<<"$OUT"; then
    pass "logs when the conductor is disabled"
else
    fail "logs when the conductor is disabled" "got: $OUT"
fi

# 9. A missing/failed `session show` must not read as receptive.
run_case "unknown" "" 0 true
if grep -q 'status=unknown action=skipped' <<<"$OUT"; then
    pass "treats an unreadable status as not-receptive"
else
    fail "treats an unreadable status as not-receptive" "got: $OUT"
fi

# 10. The standing orders must actually reach the message. If HEARTBEAT_RULES.md
#     stops being picked up, the conductor silently loses its dispatch rules --
#     the failure Priority 1 exists to prevent, reintroduced by a path typo.
SANDBOX=$(mktemp -d); BIN="$SANDBOX/bin"; mkdir -p "$BIN"
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
SANDBOX=$(mktemp -d); BIN="$SANDBOX/bin"; mkdir -p "$BIN"
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
