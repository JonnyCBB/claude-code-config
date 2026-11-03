#!/usr/bin/env bash
# Bring the remote conductor, the agent-deck board and switchboard back up, and prove each one.
#
# WHY THIS IS A SCRIPT RATHER THAN A SKILL (the burden of proof, discharged):
# the situation it exists for is "the agent is dead". On 2026-09-11 the remote conductor and all six
# of its workers died at once. A skill needs a live agent to run it; this needs to be typeable as one
# command from any terminal, including a phone over Termius. Prose cannot do that. Every step below
# is also deterministic - two careful people given the same state would agree on each one - which is
# the other half of the test. The judgement calls are deliberately NOT here; see REFUSES, below.
#
# WHAT IT REFUSES TO DO, on purpose:
#   - grant switchboard's live-queue permit. That consent is Jonny's and is given by him, never here.
#   - restart the dead workers. Only the conductor knows what each was doing; restarting one with
#     lost context risks duplicating work.
#   - kill an existing session holder. The holder is the only thing keeping the user manager alive;
#     a new one must OVERLAP the old, never replace it.
#
# THE UNDERLYING FAULT, so nobody re-derives it at 2am:
# the VM has Linger=no, and agent-deck puts the tmux server and every pane inside the per-user
# systemd manager. When the last login session closes, that manager exits and takes everything with
# it. A dropped VPN on the Mac does exactly that. The permanent fix needs an administrator:
#     sudo loginctl enable-linger <username>
# It cannot be done by the user: polkit is not running on that host - not even installed - so logind
# refuses the self-service call whatever the policy file says.
# The no-root substitute, if an administrator will not run that: see setup-remote-conductor-vm,\
# references/systemd-scheduling.md ("When enable-linger is refused").

set -uo pipefail

VM=${CONDUCTOR_VM:-conductor-vm}          # override for a differently-named host
HOLD_SECONDS=${HOLD_SECONDS:-28800}          # 8 hours
HOLD_FLOOR=${HOLD_FLOOR:-1800}               # start a fresh holder if the oldest has under 30 min left
BOARD_REMOTE=8420 ; BOARD_LOCAL=8421
SWBD_REMOTE=8890  ; SWBD_LOCAL=8891
SSH="ssh -o BatchMode=yes -o ConnectTimeout=12"

ok(){ printf '  OK    %s\n' "$*"; }
no(){ printf '  FAIL  %s\n' "$*"; }
info(){ printf '  ..    %s\n' "$*"; }
step(){ printf '\n%s\n' "$*"; }

fail_count=0
note_fail(){ no "$1"; fail_count=$((fail_count+1)); }

step "1. Can this machine reach the VM at all?"
# A public control is what distinguishes a dropped VPN from the VM being down. Without it, both look
# identical and you will blame the wrong thing.
pub=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 https://example.com 2>/dev/null)
if [ "$pub" != "200" ]; then
  no "the public internet is unreachable ($pub) - this is your network, not the VM. Stopping."
  exit 1
fi
ok "public internet reachable"
if ! $SSH "$VM" true 2>/dev/null; then
  no "cannot reach $VM while the public internet is fine - that is the VPN. Reconnect GlobalProtect, then re-run."
  exit 1
fi
ok "$VM reachable over ssh"

# Match ONLY holder ssh clients. A bare sleep pattern also matches unrelated sleeps and both ends
# of our own ssh - measured on a real host it matched three processes where one holder existed, so
# this would either over-count and never top up, or start a holder on every run.
step "2. Is a login session held open? (without one, everything started below dies when this ssh ends)"
longest=$($SSH "$VM" 'ps -eo etimes,args 2>/dev/null | awk "/ssh .*localhost sleep [0-9]+\$/ {left=\$NF-\$1; if (left>m) m=left} END {print m+0}"' 2>/dev/null)
longest=${longest:-0}
if [ "$longest" -ge "$HOLD_FLOOR" ] 2>/dev/null; then
  ok "an existing holder has ${longest}s left - leaving it alone and adding nothing"
else
  info "no holder with more than ${HOLD_FLOOR}s left; starting one that OVERLAPS any existing holder"
  ssh -f -o BatchMode=yes "$VM" "sleep $HOLD_SECONDS" 2>/dev/null
  sleep 3
  n=$($SSH "$VM" 'loginctl list-sessions --no-legend 2>/dev/null | wc -l' 2>/dev/null)
  [ "${n:-0}" -ge 1 ] && ok "holder started; $n login session(s) now open" || note_fail "could not confirm a login session"
fi

step "3. The conductor"
if $SSH "$VM" 'tmux ls 2>/dev/null | grep -q conductor-hq'; then
  ok "conductor tmux session already present"
else
  info "starting it"
  $SSH "$VM" 'agent-deck session start conductor-hq' >/dev/null 2>&1
  sleep 12
  if $SSH "$VM" 'tmux ls 2>/dev/null | grep -q conductor-hq'; then
    ok "conductor tmux session is up"
  else
    note_fail "conductor did not come up - check: ssh $VM 'agent-deck session show --json conductor-hq'"
  fi
fi

step "4. The agent-deck board (needs a real terminal AND the outer-tmux override - it refuses both ways otherwise)"
if $SSH "$VM" "ss -lnt 2>/dev/null | grep -q ':$BOARD_REMOTE '"; then
  ok "already listening on $BOARD_REMOTE"
else
  info "starting it in its own tmux session on the conductor's server"
  $SSH "$VM" "tmux kill-session -t svc-agentdeck-web 2>/dev/null; tmux new-session -d -s svc-agentdeck-web -c \"\$HOME\" 'AGENT_DECK_ALLOW_OUTER_TMUX=1 \$HOME/.local/bin/agent-deck web'" >/dev/null 2>&1
  sleep 10
  $SSH "$VM" "ss -lnt 2>/dev/null | grep -q ':$BOARD_REMOTE '" \
    && ok "listening on $BOARD_REMOTE" \
    || note_fail "board did not bind - read it with: ssh $VM 'tmux capture-pane -p -t svc-agentdeck-web -S -20'"
fi

step "5. Switchboard (its launcher DETACHES and returns - an exited tmux session here is normal, not a failure)"
if $SSH "$VM" "ss -lnt 2>/dev/null | grep -q ':$SWBD_REMOTE '"; then
  ok "already listening on $SWBD_REMOTE"
else
  info "starting it through its own launcher"
  $SSH "$VM" 'L=$(ls -1 $HOME/.claude/plugins/cache/switchboard/switchboard/*/bin/switchboard 2>/dev/null | head -1); [ -n "$L" ] && tmux new-session -d -s svc-switchboard -c "${SWITCHBOARD_DIR:-$HOME/src/switchboard}" "$L --no-open 2>&1 | tee -a $HOME/svc-switchboard.log"' >/dev/null 2>&1
  sleep 18
  if $SSH "$VM" "ss -lnt 2>/dev/null | grep -q ':$SWBD_REMOTE '"; then
    ok "listening on $SWBD_REMOTE"
  else
    note_fail "switchboard did not bind - read: ssh $VM 'cat ~/svc-switchboard.log | tail -20'"
    info "if it refuses on the live queue, that permit is JONNY'S to grant. This script will not."
  fi
fi

step "6. Local tunnels"
for pair in "$BOARD_LOCAL:$BOARD_REMOTE" "$SWBD_LOCAL:$SWBD_REMOTE"; do
  l=${pair%%:*}
  if lsof -nP -iTCP:"$l" -sTCP:LISTEN >/dev/null 2>&1; then ok "port $l already forwarded"; fi
done
if ! lsof -nP -iTCP:"$BOARD_LOCAL" -sTCP:LISTEN >/dev/null 2>&1 || ! lsof -nP -iTCP:"$SWBD_LOCAL" -sTCP:LISTEN >/dev/null 2>&1; then
  info "opening tunnels"
  ssh -N -f -L "$BOARD_LOCAL:127.0.0.1:$BOARD_REMOTE" -L "$SWBD_LOCAL:127.0.0.1:$SWBD_REMOTE" "$VM" 2>/dev/null
  sleep 3
fi

step "7. Proof - HTTP through the tunnels, because a listening socket is not a working path"
# A dead tunnel still LISTENS locally. Only a real response proves the whole chain.
for pair in "board:$BOARD_LOCAL" "switchboard:$SWBD_LOCAL"; do
  name=${pair%%:*}; port=${pair##*:}
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 12 "http://127.0.0.1:$port" 2>/dev/null)
  if [ "$code" = "200" ]; then ok "$name answers 200 on http://127.0.0.1:$port"
  else note_fail "$name returned '$code' on 127.0.0.1:$port (000 = refused at the far end, i.e. the service is down)"; fi
done

step "Summary"
left=$($SSH "$VM" 'ps -eo etimes,args 2>/dev/null | awk "/ssh .*localhost sleep [0-9]+\$/ {left=\$NF-\$1; if (left>m) m=left} END {print m+0}"' 2>/dev/null)
if [ "${left:-0}" -gt 0 ] 2>/dev/null; then
  printf '  Protection lasts another %s minutes (the longest session holder).\n' "$(( left / 60 ))"
fi
lg=$($SSH "$VM" 'loginctl show-user "$(id -u)" -p Linger 2>/dev/null' 2>/dev/null)
if [ "$lg" = "Linger=yes" ]; then
  printf '  Linger is ENABLED - this machine now survives on its own and this script is a formality.\n'
else
  printf '  Linger is still OFF. Everything above dies when the last session closes.\n'
  printf '  Permanent fix, needs an administrator: sudo loginctl enable-linger <username>\n'
fi
if [ "$fail_count" -eq 0 ]; then
  printf '\nEverything is up and proved.\n'; exit 0
else
  printf '\n%s check(s) failed - read the lines marked FAIL above.\n' "$fail_count"; exit 1
fi
