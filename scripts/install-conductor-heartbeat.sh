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
if [ -z "${CONDUCTOR_HQ_DIR:-}" ]; then
    for d in "$HOME/.local/share/agent-deck/conductor/hq" "$HOME/.local/share/agent-deck/conductor/conductor-hq"; do
        [ -d "$d" ] && CONDUCTOR_HQ_DIR="$d" && break
    done
fi
HQ_DIR="${CONDUCTOR_HQ_DIR:-$HOME/.local/share/agent-deck/conductor/hq}"
HQ_NAME="$(basename "$HQ_DIR")"

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

# Report the real interval, from whichever scheduler this host actually uses.
# meta.json records heartbeat_interval: 0, which matches neither and must not be
# trusted; if agent-deck ever regenerates the job definition from meta.json the
# cadence could silently change, so surface the live figure here.
#
# Looking only at launchd printed "launchd plist not found at
# ~/Library/LaunchAgents/..." on the Linux VM -- a false alarm where nothing was
# wrong, and no interval at all on the host this is most often run from.
INTERVAL=""
SCHEDULER=""
PLIST="$HOME/Library/LaunchAgents/com.agentdeck.conductor-heartbeat.$HQ_NAME.plist"
TIMER="$HOME/.config/systemd/user/conductor-heartbeat-$HQ_NAME.timer"
if [ -f "$PLIST" ]; then
    SCHEDULER="the launchd plist"
    INTERVAL=$(awk '/StartInterval/{getline; gsub(/[^0-9]/,""); print; exit}' "$PLIST")
elif [ -f "$TIMER" ]; then
    SCHEDULER="the systemd timer"
    # OnUnitActiveSec takes a systemd time span: bare seconds, or a unit suffix.
    INTERVAL=$(awk -F= '/^ *OnUnitActiveSec *=/{v=$2; gsub(/[[:space:]]/,"",v);
        if (v ~ /^[0-9]+h$/)      {gsub(/h/,"",v); print v*3600}
        else if (v ~ /^[0-9]+m(in)?$/) {gsub(/m(in)?/,"",v); print v*60}
        else if (v ~ /^[0-9]+s?$/)     {gsub(/s/,"",v); print v}
        exit}' "$TIMER")
fi
if [ -n "$INTERVAL" ] && [ "$INTERVAL" -gt 0 ] 2>/dev/null; then
    printf 'note  interval %ss (%s min) per %s -- expect ~%s receipts overnight\n' \
        "$INTERVAL" "$((INTERVAL / 60))" "$SCHEDULER" "$((8 * 3600 / INTERVAL))"
elif [ -n "$SCHEDULER" ]; then
    printf 'note  found %s but could not read an interval from it\n' "$SCHEDULER"
else
    printf 'note  no scheduler found -- looked for %s and %s\n' "$PLIST" "$TIMER"
fi

# Same default and same override as conductor-heartbeat.sh, so the count
# reported here is taken from the file the runner actually interrogates. With
# only one of the two overrides honoured, setting it made this print the receipt
# count of a different file with no error on either side -- a check that passes
# while reading the wrong thing.
RECEIPTS="${HEARTBEAT_RECEIPT_LOG:-$HQ_DIR/heartbeat-received.log}"
if [ -f "$RECEIPTS" ]; then
    printf 'note  %s receipts recorded so far\n' "$(wc -l < "$RECEIPTS" | tr -d ' ')"
else
    printf 'note  no receipts yet (%s) -- expected until the next heartbeat lands\n' "$RECEIPTS"
fi

exit "$EXIT"
