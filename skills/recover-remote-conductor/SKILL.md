---
name: recover-remote-conductor
description: Brings the remote conductor stack back up after the VM's tmux server has died - the conductor session, the agent-deck web board, switchboard, and the Mac-side SSH tunnels - and proves each one by an HTTP response rather than an exit code. Runs one bundled script that is safe to re-run when things are already healthy. Use when the remote conductor is unreachable, when "agent-deck list" on the VM shows every session as error, when the board or switchboard stop answering in the browser, or after the Mac's VPN has dropped. NOT for first-time provisioning (that is setup-remote-conductor-vm) and NOT for restarting individual dead workers, which is the conductor's own decision to make.
---

# Recovering the remote conductor stack

```bash
bash "$(dirname "$0")/recover.sh"     # or: bash ~/.claude/skills/recover-remote-conductor/recover.sh
```

One command, safe to re-run. It checks before it acts, so running it on a healthy stack changes
nothing except topping up a session holder that is close to expiring.

**Why a script rather than steps in this file.** The situation it exists for is *the agent is dead*
— on 2026-09-11 a conductor and all six of its workers died together. A skill needs a live agent to
run it; this has to be typeable in one line from any terminal, including a phone. That is the case
prose cannot cover, which is why the burden of proof for a script is met here.

## What it does, in order

Reachability (with a public-internet control, so a dropped VPN is not mistaken for a dead VM) →
session holder → conductor → agent-deck board → switchboard → tunnels → proof.

**Read the last section of its output, not the exit code.** It proves the board and switchboard by
fetching them through the tunnels, because a dead tunnel still LISTENS locally and a listening
socket is not a working path. A `000` there means the far end refused — the service is down, not the
tunnel.

## What it deliberately will not do

- **Grant switchboard's live-queue permit.** That consent is the operator's, given deliberately.
- **Restart dead workers.** Only the conductor knows what each was doing; restarting one with lost
  context risks duplicating work. Hand it the facts and let it decide.
- **Kill an existing session holder.** Holders must overlap — the per-user systemd manager exits the
  instant the session count reaches zero, so replacing rather than overlapping is how you cause the
  outage you are recovering from.

## Two failure modes worth knowing before you debug it

**The board refuses to start twice over.** `agent-deck web` runs a terminal interface alongside the
server, so it needs a real terminal and cannot run as a background service; it also refuses to run
inside tmux at all without `AGENT_DECK_ALLOW_OUTER_TMUX=1`. The script sets both conditions. If you
start it by hand and it exits silently, that is why.

**Switchboard's launcher detaches and returns.** The tmux session created for it exits immediately
and that is normal, not a failure. Check the port, never the session.

## The underlying fault

The stack dies this way because the VM has lingering disabled and agent-deck runs its tmux server
inside the per-user systemd manager, which exits when the last login session closes — so a dropped
VPN on the operator's laptop takes the whole stack with it. Recovery is the second-best fix.

The first is `sudo loginctl enable-linger <username>`, which needs an administrator. Failing that,
`setup-remote-conductor-vm`'s `references/systemd-scheduling.md` carries a no-root substitute that
makes the VM hold its own session open. **If you are running this script more than once, fix the
cause instead.**
