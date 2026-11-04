# Replacing the launchd jobs with a systemd user timer

Phase 10 of `SKILL.md`. This is the step with no macOS equivalent, and the one most likely to be
forgotten because **nothing complains**. On arrival expect: crontab empty, no timer,
`agent-deck conductor status` reporting both daemons `STOPPED`, and `heartbeat.sh` present and
correct with nothing to run it.

## Prefer a timer to `agent-deck conductor setup`

`agent-deck conductor setup <name> -heartbeat` regenerates `CLAUDE.md`, `POLICY.md` and
`heartbeat.sh` in the conductor directory, and its `-instructions-md` flag **symlinks rather than
copies** — which once replaced hand-edited instructions with a link into a temp directory, and
the obvious `diff` check came back clean because it was comparing the file to itself. A timer
touches none of that.

Take a durable backup before any regenerating command, and not to `/tmp`.

## The unit files

`~/.config/systemd/user/conductor-heartbeat-hq.service`:

```ini
[Service]
Type=oneshot
Environment=PATH=/home/<user>/.local/bin:/home/linuxbrew/.linuxbrew/bin:/usr/local/bin:/usr/bin:/bin
Environment=BEADS_DIR=/home/<user>/beads-hq/.beads
WorkingDirectory=/home/<user>/.local/share/agent-deck/conductor/hq
ExecStart=/usr/bin/bash -c 'printf "%%s fired\\n" "$(date -u +%%Y-%%m-%%dT%%H:%%M:%%SZ)"; exec /usr/bin/bash heartbeat.sh'
StandardOutput=append:/home/<user>/.local/share/agent-deck/conductor/hq/heartbeat-timer.log
StandardError=append:/home/<user>/.local/share/agent-deck/conductor/hq/heartbeat-timer.log
```

**Spell the home directory out.** systemd's `Environment=` does no shell expansion, so a literal
`$HOME` in a unit file stays literal and the PATH silently becomes garbage. The `%%` in
`ExecStart` is systemd's own escaping for a literal `%`, not a typo.

`~/.config/systemd/user/conductor-heartbeat-hq.timer`:

```ini
[Timer]
OnActiveSec=2min          # a fresh install proves itself instead of waiting an hour
OnBootSec=5min
OnUnitActiveSec=1h        # match the interval the conductor's own docs record
AccuracySec=30s
Unit=conductor-heartbeat-hq.service
[Install]
WantedBy=timers.target
```

## Four traps, all met in practice

**A user unit gets a minimal environment, and `heartbeat.sh` calls `agent-deck` as a bare
command.** Declaring `Environment=` is mandatory — and every variable the script needs, not just
PATH, which is why `BEADS_DIR` is there too. **The failure is silent**: the script's first action
gates on `agent-deck conductor status --json`, so if `agent-deck` is not found the gate fails and
the script **exits 0**, reporting success while sending nothing.

**Prove the environment inside a real unit, not by reasoning about it.** `systemd-run --user
--wait --pipe` with the same `-p Environment=...` values, running a command that resolves
`agent-deck` and `bd` and echoes `BEADS_DIR`, is the check. Both paths and a non-empty `BEADS_DIR`
must print; **nothing printing is the actual failure mode**, so treat empty output as a failure
rather than as no news.

Note the asymmetry that makes this work: in a `systemd-run` command line the shell expands `$HOME`
before systemd sees it, which is why that form succeeds where a literal `$HOME` inside a unit file
silently does not.

**`OnBootSec` in the past fires immediately** on timer start, so the first firing happens at
install time rather than on the schedule. Do not read that as the schedule working.

**`heartbeat.sh` only sends when the conductor's status is `idle` or `waiting`.** A test run
while the conductor is mid-turn correctly sends nothing — which proves the timer works and proves
nothing about delivery. Arrange for a tick to land while the target is idle.

**Delivery is a separate leg from scheduling, and it is the leg that has historically failed.**
Recorded sender logs are wall-to-wall errors of the form *"send dropped silently"* and *"message
typed but not submitted"*. Verify delivery by a **new line in `heartbeat-received.log`**, never by
the timer's exit code.

## Enable, and verify both legs separately

`systemctl --user enable --now <timer>`, then check the two legs independently, because passing one
says nothing about the other:

- **Scheduling** — `systemctl --user list-timers <timer>` shows a future firing in its `NEXT`/`LEFT`
  columns.
- **Delivery** — `heartbeat-received.log` gains a line timestamped after the timer was enabled,
  taken while the conductor was idle. An empty tail here alongside a healthy timer is the
  historical failure, and it is the one that matters.

## When `enable-linger` is refused: hold a session from the VM itself

Reach for this only after the phase 2 root block has been refused and phase 2's `Linger` and polkit
checks have been run.

**Confirm the claim this rests on, on your own host** — a different agent-deck version may not place
its tmux the same way. Read `/proc/<tmux pid>/cgroup`: agent-deck's server sits under
`user@<uid>.service/…/agentdeck-tmux-*.scope`, inside the per-user manager, while a plain `tmux`
lands in a system-manager `session-*.scope` and survives logout. That asymmetry is the whole fault.

**Why a substitute exists at all.** The login session does not have to come from the operator's
laptop. `cron` is driven by the *system* manager, so it keeps running while that laptop is asleep or
off the network, and an SSH connection from the host to itself registers a real logind session. So
the VM can hold its own door open. Verify both before relying on either — a crontab nothing executes
is useless, and if the self-connection does not register a session it holds nothing:

```bash
systemctl is-active cron                                   # or crond, depending on the distro
before=$(loginctl list-sessions --no-legend | wc -l)
ssh -o BatchMode=yes -f localhost "sleep 45"
sleep 3
echo "sessions $before -> $(loginctl list-sessions --no-legend | wc -l)"   # must increase
```

**The script, and the two properties that matter.** Holders must **overlap**: the manager exits the
instant the session count reaches zero, so a replacement started after the last one ended is too
late. And it must never terminate an existing holder.

```bash
#!/usr/bin/env bash
# ~/.local/bin/session-holder.sh   — install with: chmod +x, then
#   (crontab -l 2>/dev/null; echo "*/5 * * * * $HOME/.local/bin/session-holder.sh >/dev/null 2>&1") | crontab -
STATE="$HOME/.local/state"; mkdir -p "$STATE"     # without this the marker below silently never appears

# Match ONLY our own holders. A bare /sleep [0-9]+$/ matches any long sleep on the box and both ends
# of our own ssh: measured on a real host it matched three processes where one holder existed, so an
# unrelated `sleep 86400` would read as "covered" and nothing would start.
longest=$(ps -eo etimes,args | awk '/ssh .*localhost sleep [0-9]+$/ { l = $NF - $1; if (l > m) m = l } END { print m+0 }')

if [ "${longest:-0}" -ge 900 ]; then
  echo "$(date -u +%FT%TZ) covered longest=${longest}s action=none" > "$STATE/session-holder.lastrun"; exit 0
fi
ssh -o BatchMode=yes -o ConnectTimeout=10 -f localhost "sleep 3600"
echo "$(date -u +%FT%TZ) topped-up longest=${longest}s action=started-3600s" > "$STATE/session-holder.lastrun"
```

**Record the DECISION, not merely that it ran.** A marker saying only "ran" hides every way this can
be wrong: a pattern matching nothing reads `longest=0` forever while sessions drain, a pattern
matching everything reads a huge number and never tops up, and an inverted comparison looks identical
to both. Writing `longest` and the action taken makes all three visible on the first tick — and a
missing marker still means "cron never ran", which is the ambiguity it exists to remove.

**Exercise four input states before trusting it**, not just the happy one: no holder at all, a holder
with plenty left, a holder nearly expired, and — the one you will not meet by accident — an unrelated
long `sleep` running with no holder. That last is where the loose pattern fails silently.

**Verify the schedule fires, not just that the script works.** Record the marker's value, wait past
one interval, and check it moved on its own. Running the script by hand proves only the script.

**Two instrument traps, both met while testing this.** `systemctl --user is-active` returns **empty
under cron** — there is no session bus — whether the manager is alive or dead, so it reports a
healthy system as gone; ask the system manager instead, with `systemctl is-active user@$(id -u).service`.
And an observer polling the host over SSH during a test **manufactures the very sessions the test is
removing**; a clean check needs a window with no connections from outside.

**What this does not do.** It keeps the manager alive; it does not restart anything already dead, and
it stops helping if cron stops. It is a substitute for lingering, not an equal: keep asking for
`enable-linger`.
