# Reaching the VM: from the Mac, and from a phone

Phase 11 of `SKILL.md`. Everything here assumes the `conductor-vm` SSH alias from phase 1
already exists and points at the right FQDN.

## What is and is not open

Everything reaches the VM through **port 22, already open from the VPN**. Non-22 ports are closed
by default and opening one needs a Bento firewall PR reviewed by `#security`, with a human in the
loop and an unknown turnaround.

Switchboard and agent-deck web listen on **loopback only**. Nothing reaches them except through
an SSH tunnel, which is a feature: the loopback guard is satisfied because a tunnelled request
genuinely arrives on loopback.

## The three Mac aliases

```bash
# ~/.zshrc on the Mac

# attach to the running tmux session on the VM
alias conductor='ssh conductor-vm -t tmux attach -t conductor'

# both browser tunnels in the background - note the OFFSET ports
alias conductor-tunnels='ssh -f -N -L 8421:127.0.0.1:8420 -L 8891:127.0.0.1:8890 conductor-vm'
```

**The local ports are deliberately offset by one.** `8421` and `8891` avoid clashing with the
Mac's own agent-deck (`8420`) and switchboard (`8890`). Bind the same numbers on both ends and
you will read the Mac's board while believing you are reading the VM's — a silent wrong-answer
failure, not a connection error. So: `localhost:8421` is the remote agent-deck,
`localhost:8891` is the remote switchboard.

The tunnels die when the laptop sleeps; the VM keeps running. `conductor-tunnels` re-establishes
them in one command. Reattaching after a laptop close is 1–2 seconds.

**To check a tunnel is carrying the remote service and not a local one, shut the Mac's own copy
down first.** With the Mac's switchboard up on `8890`, a request to the tunnelled port can be
answered locally and the check cannot fail. With it down, the pair of facts you want is: the VM
shows a listener on its own port (via `ss -ltnp` there), *and* the tunnelled local port answers.

## Transport: SSH, mosh, or Eternal Terminal?

Two problems that sound like one, and only the second is open:

- **The session surviving a shut laptop is already solved by tmux.** It never stopped running.
- **The SSH connection dying and needing a manual reconnect** is the real question.

A VPN layer underneath does **not** save the SSH session. GlobalProtect reconnects the tunnel on
wake; the TCP session inside it is already dead. None of these is an organisation standard, so
choose on the merits below.

| | Auto-reconnect on wake? | Scrollback | Port forwarding | Server needs | Firewall |
| --- | --- | --- | --- | --- | --- |
| **SSH + tmux** (baseline) | No — type one command | Yes (tmux) | Yes | tmux only | Port 22 (open) |
| **mosh + tmux** | Yes — instant screen resync | No (needs tmux under it) | No | `mosh-server`, per session | UDP 60000–61000 (Bento review) |
| **Eternal Terminal** | Re-invoke `et` — reconnects into the same process | Yes (inherits shell) | Yes (`-t`) | `etserver` daemon | TCP 2022 (Bento review, one port) |
| **autossh + tmux** | Yes — respawns SSH automatically | Yes (tmux) | Yes | tmux only (client-side wrapper) | Port 22 (open) |

**Start with the plain alias, and say why.** There is no technical reason to prefer it — ET gives
scrollback, port forwarding and reconnection into the same running process, which are three
things the alias does not. The reason is scheduling: the alias needs nothing at all, so it gives
a working remote conductor **today**, while a firewall PR is in flight. If the review is known to
be fast, or is filed the same day the VM is created, go straight to ET.

The alias is the fallback for the gap between "VM is up" and "firewall rule approved", **not a
recommended permanent state.** Say that when reporting, so it does not silently become the
end state.

Mosh is the alternative only if the use case changes to lossy or roaming connections — a train, a
conference. For a clean long disconnection followed by a return to good network, ET and the alias
solve the same problem at different comfort levels.

## The phone gate

This is the one test that decides whether the VM is reachable from a phone at all. Run it, and
report the result either way.

**The route that has been verified:** an SSH client (Termius on managed Android, Blink on iOS)
over GlobalProtect VPN, connecting with an **ED25519** key.

**Use the internal IP, not the hostname.** The phone's DNS cannot resolve the private hostname —
GlobalProtect's split tunnel routes IP traffic but does not push internal DNS. This is why phase
1 asks for the IP alongside the FQDN. **If the VM is ever recreated with a new IP, the saved
phone connection has to be updated**, and it will fail in a way that looks like the VM being
down.

Steps:

1. Install the SSH client (check Self Service first; on managed Android both GlobalProtect and
   Termius come from the work-profile Play Store).
2. Connect GlobalProtect.
3. SSH to the **IP** with the ED25519 key. If that connects, the gate is passed.
4. Then try local port forwarding — `ssh -L 8890:127.0.0.1:8890 <ip>` — and open
   `localhost:8890` in the phone browser for the full board UI.

**Known limit, and state it rather than discovering it later:** the tunnel **dies on phone
lock**, because the OS suspends background network. The board is reachable while the phone is
awake and in the app, and not otherwise.

## What you will not have

State these plainly in the report. A setup that omits its limits reads as though it has none.

**No flowing mobile chat.** Every phone route is either a one-shot SSH command or a tunnel that
dies on lock. The always-connected native-app experience exists elsewhere and is deliberately not
being used for the conductor.

**No push notifications on the phone** without the TLS and firewall work, which is the heaviest
step and three separate projects: a non-22 port opened by a reviewed Bento PR, a TLS certificate
the VM does not have by default, and the phone trusting that certificate. Do it only when daily
friction justifies it. On the Mac, `agent-deck web --push` works today on loopback.

**No automatic retry of a turn killed mid-flight.** Moving hosts makes it much rarer. It does not
make it zero, and the completion ledger still cannot see it.
