#!/bin/bash
# Install the conductor's standing orders into the live agent-deck conductor dir.
#
#   bash scripts/install-conductor-heartbeat.sh [--check]
#
# --check verifies the live file matches this repo and exits non-zero on drift.
#
# ### THIS DELIBERATELY DOES NOT TOUCH heartbeat.sh. MEASURED 2026-08-29.
#
# `agent-deck conductor status --json` REGENERATES
# ~/.local/share/agent-deck/conductor/hq/heartbeat.sh from a template, within a
# second, silently. It reads like a status query and is not one.
#
# Installing an instrumented script over heartbeat.sh is therefore self-defeating:
# such a script's first action is an `agent-deck conductor status` call, so it
# overwrites itself on its own first run and reverts to the uninstrumented
# template. Verified by installing (6915 bytes, log() present), issuing one status
# call, and re-reading (1558 bytes, log() gone).
#
# HEARTBEAT_RULES.md, by contrast, SURVIVES regeneration -- agent-deck owns
# heartbeat.sh by name only. Verified the same way. So the standing orders are
# safe to install here, and delivery is measured from the RECEIVING end instead
# (section 0 of the rules), which proves arrival rather than send-success.
#
# scripts/conductor-heartbeat.sh in this repo is the sender-side instrumented
# runner. It is tested but NOT installed by this script, because deploying it
# means repointing a launchd plist. See docs/conductor-heartbeat-rules.md.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HQ_DIR="${CONDUCTOR_HQ_DIR:-$HOME/.local/share/agent-deck/conductor/hq}"

SRC_RULES="$REPO_ROOT/docs/conductor-heartbeat-rules.md"
DST_RULES="$HQ_DIR/HEARTBEAT_RULES.md"

EXIT=0
fail() { printf 'FAIL  %s\n' "$1"; EXIT=1; }
ok()   { printf 'ok    %s\n' "$1"; }

[ -f "$SRC_RULES" ] || { printf 'FAIL  missing source: %s\n' "$SRC_RULES"; exit 1; }
[ -d "$HQ_DIR" ]    || { printf 'FAIL  conductor dir not found: %s\n' "$HQ_DIR"; exit 1; }

if [ "${1:-}" = "--check" ]; then
    cmp -s "$SRC_RULES" "$DST_RULES" && ok "HEARTBEAT_RULES.md matches repo" \
        || fail "HEARTBEAT_RULES.md differs from repo copy (re-run without --check)"
    exit "$EXIT"
fi

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
[ -f "$DST_RULES" ] && cp "$DST_RULES" "$DST_RULES.bak-$STAMP" \
    && printf 'backed up %s\n' "$DST_RULES.bak-$STAMP"

cp "$SRC_RULES" "$DST_RULES" && ok "installed HEARTBEAT_RULES.md" \
    || fail "could not install HEARTBEAT_RULES.md"

# Report the real interval. meta.json records heartbeat_interval: 0, which does
# NOT match the plist and must not be trusted; if agent-deck ever regenerates the
# plist from meta.json the cadence could silently change, so surface it here.
PLIST="$HOME/Library/LaunchAgents/com.agentdeck.conductor-heartbeat.hq.plist"
if [ -f "$PLIST" ]; then
    INTERVAL=$(awk '/StartInterval/{getline; gsub(/[^0-9]/,""); print; exit}' "$PLIST")
    if [ -n "$INTERVAL" ]; then
        printf 'note  interval %ss (%s min) per the plist -- expect ~%s receipts overnight\n' \
            "$INTERVAL" "$((INTERVAL / 60))" "$((8 * 3600 / INTERVAL))"
    fi
else
    printf 'note  launchd plist not found at %s\n' "$PLIST"
fi

RECEIPTS="$HQ_DIR/heartbeat-received.log"
if [ -f "$RECEIPTS" ]; then
    printf 'note  %s receipts recorded so far\n' "$(wc -l < "$RECEIPTS" | tr -d ' ')"
else
    printf 'note  no receipts yet (%s) -- expected until the next heartbeat lands\n' "$RECEIPTS"
fi

exit "$EXIT"
