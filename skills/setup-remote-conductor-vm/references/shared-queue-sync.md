# Two conductors, one queue: keeping the sync honest

Phases 5 and 9 of `SKILL.md`, which state why this is the setup's highest-consequence failure mode.

## Why it is silent, which is the whole problem

Phase 9 states the two structural facts: a blocked pull is indistinguishable from a queue where
nothing changed, and claims only prevent duplicate dispatch while both sides are current. The
error, for recognition — reproduced on bd 1.3.0-rc.1 against a manufactured conflict:

```
Error: merge rigremote/main: merge conflicts in issues require operator resolution;
merge aborted and working set restored
```

Note "working set restored": the machine is left clean and healthy-looking. And note the exit
code, because it is a trap — **`bd dolt pull` exits `1` on a merge conflict**, the same code it
uses for transport and auth failures. Only `bd sync` separates the two (`2` for a conflict). That
is the reason the gate is built on `bd sync` and never on a raw pull.

## Use `bd sync`, not a hand-rolled pull-then-push

`bd sync` pulls, checks for conflicts **positively** from Dolt's conflict tables, recomputes the
denormalized `is_blocked` flag so dependency edges merged in from another replica do not leave
`bd ready` stale, and pushes with a bounded retry when the other replica wins the push race.
Phase 5.5 of `SKILL.md` tabulates its exit codes.

Its help states the authority for the rule above: conflicts are *"never inferred from the pull's
exit status, which is not a trustworthy conflict signal in either direction"*.

## The Dolt remote's transport, which is not git's

**`bd dolt` does not resolve URLs through git's config.** The global `insteadOf` rewrite that
makes plain `git` reach the git host over HTTPS does nothing for it. This was tried on a real VM: an
`insteadOf` rule was added for the `git+ssh://` form, `git ls-remote` then resolved fine, and
**`bd dolt` still failed identically**. URL rewriting and credentials are separate questions here —
it ignores the former and does use the latter, as below — so fix the transport by naming a second
remote, never by adding a rewrite rule.

On these VMs SSH to the git host is denied while HTTPS works, and the Dolt remote inherited from the repo is
an SSH URL — measured on the Mac, `bd dolt remote list` returns a single `origin` on
`git+ssh://git@<git-host>/...`, which is exactly the unusable form.

Add an HTTPS remote alongside it — `bd dolt remote add <name> <https-url>` — and from then on pass
it as **`--remote <name>`**. The positive check is that **both** remotes then list.

**The remote is a flag. The positional form is accepted and silently ignored.** `bd dolt pull
<name>` does not complain and pulls from the **default** remote anyway — which here is the SSH
`origin`, so it fails `Permission denied (publickey)`, an error that blames your SSH keys for what
is really a dropped argument. Measured in a throwaway database holding two non-resolving remotes,
so the error names the one actually contacted:

```
bd dolt pull originhttps          -> Error: fetch from origin/main: ... ssh: ...
bd dolt pull --remote originhttps -> Error: fetch from originhttps/main: ... https ...
```

`bd dolt pull --help` states it: *"Use --remote to pull from a specific named remote instead of the
default."* Same for `bd dolt push` and `bd sync`. Passing `--remote` also **never adopts** a remote,
which closes the adoption hazard above with the same flag; `--no-adopt` does it explicitly.

**`bd dolt` over the HTTPS remote needs no auth of its own — it reuses git's credential helper.**
Measured on this VM: the store's own history carries successful `Merge branch 'originhttps/main'`
commits, and the only credential in play is the host-scoped helper `gh auth git-credential` that
`gh auth setup-git` installs. So **queue sync depends on `gh` staying authenticated**: when HTTPS
sync starts failing on auth, check `gh auth status` before suspecting the remote or the lineage.
Note the helper is configured per host (`credential.https://<git-host>.helper`), so a bare
`git config --get credential.helper` prints nothing and is not evidence there is none.

**Do not collapse these failures into the lineage failure.** They need opposite responses:

| Symptom | Cause | Fix |
| --- | --- | --- |
| `rc=1`, `Permission denied (publickey)` | SSH-form remote, this section | Add the HTTPS remote |
| `rc=1`, an auth/401 error on the HTTPS remote | `gh`'s credential, not transport | Re-auth `gh`; do not re-clone |
| Pull integrates nothing, then push rejected non-fast-forward | Unrelated histories (a copied `.beads`) | Re-clone; nothing else works |

## The gate to build on the exit codes

The five exit codes and the action each one implies are tabulated once, in phase 5.5 of `SKILL.md`.
Do not restate them here or in any file you write — read them there.

### Make a failed sync refuse to dispatch

This is the whole difference between a silent divergence and a visible stop. What the gate has to do:

1. Run `bd sync --remote <name>` and capture **its exit code**, not its output.
2. Append the UTC timestamp and that code to a stamp file the next read will check — somewhere
   durable in the conductor directory, not `/tmp`.
3. Permit dispatch **only** on `0`. Treat `3` as "retry next tick, do not dispatch". Treat `2` and
   `4` as halt-and-escalate: say plainly that an operator must resolve the divergence.
4. Exit with the same code, so a caller can branch on it too.

**Do not branch on output text.** The exit codes exist precisely so a timer can branch without
parsing prose, and the halt message's wording varies with the pull route — it reports whether the
merge was aborted or left live in the working set.

Then, before any dispatch, require that the newest stamp line is `rc=0` **and** recent.

### What this gate still cannot catch — state these limits, do not oversell it

**It bounds staleness; it does not eliminate it.** `rc=0` means "current as of the sync", not
"current now" — the other conductor can push a second later, so a recent `rc=0` still permits
dispatching a bead the other side has just claimed. **No threshold closes that, so do not hunt for
a tighter one:** `bd` runs Dolt embedded, in process, on each machine, so "both sides current" is
still two independent local replicas with no cross-machine lock, and a claim made on one is
invisible to the other until the first pushes and the second pulls. The race is structural to that
topology, not a defect in the gate.

**The gate must sit at the dispatch decision, not only in a timer.** A guard's characteristic
failure is *vanishing* rather than deciding wrongly: a gate living only inside the sync timer goes
away with it when that timer's environment is wrong, leaving dispatch unguarded and silent. So put
the stamp check in the dispatch path, **require `rc=0` AND recency, and treat a missing stamp as a
failure** — a gate that finds no file must refuse, or the first run and every run after the file
moves sails through unchecked.

**`rc=0` also covers "nothing to do", and says nothing about what integrated.** To know whether
work actually moved, count issues before and after.

## Reclaim on a shared queue: what the replica guard does not do

Phase 9 carries the incident and the fix — arm `node_id` on both machines rather than disabling
reclaim — and phase 5.2 carries how to set and check it. Four things neither states:

- The guard's own justification, from `bd reclaim --help`: *"A lease is only meaningful on the
  replica that granted it"*. It records the granting replica on each lease, skips a lease another
  replica granted, and summarises what it declined on stderr — **one line per run**, which `bd -v`
  expands to the first 20 leases individually. Do not expect a line per lease.
- `BEADS_NODE_ID` in the environment is equivalent to `bd config set node_id`.
- **`--any-replica` defeats the guard.** Bare `--any-replica` reverts **every** foreign stale lease,
  live peers included. Use it only when a replica is permanently gone, and prefer the narrow
  `--any-replica --id <id>`. Freeing one genuinely stuck claim by hand is `bd update --force`, not a
  reclaim flag — `bd reclaim` has none.
- **Two invariants the guard cannot enforce**, quoted: *"grace window > sync interval, and lease
  TTL > sync interval"*. Raise the TTL or grace above the sync cadence, never the reverse. And the
  guard does not make a bulk status flip legitimate: treat a large uniform-timestamp status change
  as a red flag when reading history, not as tidying.

## A same-cell divergence never becomes a conflict — it is settled last-write-wins

Measured: two replicas each set a different `description` on the same bead, then pulled. Exit `0`,
"Pull complete.", and the losing side's text was simply gone. The only trace is one stdout line:

```
Notice: auto-merged issue A-zd4; description, updated_at settled last-write-wins
        (the older side's edit was superseded)
```

So **`rc=0` does not mean both sides' content survived** — it means nothing halted. The classes that
auto-settle are machine-local metadata, audit-only dependency rows and last-write-wins on issue
cells; anything beyond them halts. Read the `Notice:` lines as part of the sync outcome, and never
cite a clean sync as evidence that no content was overwritten.

## Resolving a halt: what each tool can actually see

`bd sync` exiting `2` is the divergence becoming *visible*, and it does not mean re-cloning. Measured
on bd 1.3.0-rc.1, embedded storage, against a manufactured delete-vs-edit conflict. **`bd sync` has
no `--strategy`** (only `--attempts`, `--no-adopt`, `--remote`, `--yes`) so do not hunt for one, and
do not reach for `bd federation sync` — a different command for peer towns, which would resolve by
fiat on a queue holding real claims.

**1. `bd conflicts list` will say "No merge conflicts." — and that is not an answer.** The pull
underneath aborts the merge and restores the working set, so nothing is live for it to see. bd's own
halt message says so: *"'bd conflicts list' will show nothing right now — this pull route restores
the working set instead of leaving conflicts live for it."*

**2. To make the conflict inspectable, re-run the merge so it is left live**, with `dolt merge
<remote>/main` in the real repository directory (see below). `bd vc merge` will not do it — it rolls
the transaction back on conflict, and `--dolt-auto-commit off` does not change that.

**3. Once the merge is live, `bd conflicts` works and is the readable route.** `bd conflicts show`
prints base/ours/theirs per field under a header naming the shape (`[we modified / they deleted]`).
Prefer it to `dolt conflicts cat issues`, which prints every column of the row three times over —
the issues table's 56 columns become 170 — and is unreadable. To query the raw table, name fields:

```
dolt sql -q "select our_description, their_description, our_diff_type, their_diff_type
             from dolt_conflicts_issues"
```

**4. `--ours`/`--theirs` can only pick a side — they cannot union.** A genuinely diverged record
holds real content on both sides, and picking either discards the other. Two measured limits:
`bd conflicts resolve <id> --ours` refuses unless the row exists on both sides (*"not a modify/modify
conflict … resolve it with a whole-table strategy or edit the row directly"*), and the merge commits
only once no conflicts remain, so a partial pass leaves it open for the next one. For a union, the
procedure that worked: **union both sides with a marked boundary between them, check the result for
lost fragments, and leave a field where the two sides genuinely disagree flagged rather than decided
by fiat.**

`bd dolt pull --remote <name> --strategy ours|theirs` resolves instead of aborting (embedded storage
only) — the blunt instrument, settling every conflict the same way. Use it only once you have
established that one side should win wholesale.

The prohibition on `bd dolt push --force` is stated once, in phase 5.5 of `SKILL.md`. It still
applies: `bd sync` never forces internally, it halts — so the warning targets exactly the person
tempted to force past a halt.

## Where the database actually is, and why `dolt init` is the wrong answer

**`dolt` installs without root.** Three commands, no `sudo`, verified on this VM as an unprivileged
user — so this does **not** belong in the phase 2 root block, and "the Dolt-level recovery is
unavailable here" is not a real limit. `~/.local/bin` is already on the login-shell PATH:

```bash
curl -fsSL https://github.com/dolthub/dolt/releases/latest/download/dolt-linux-amd64.tar.gz -o dolt.tar.gz
tar -xzf dolt.tar.gz
install -m 755 dolt-linux-amd64/bin/dolt ~/.local/bin/dolt
```

**`bd dolt status` reports the parent of the repository, not the repository.** It prints
`Data: …/.beads/embeddeddolt`, and `dolt` run there answers *"The current directory is not a valid
dolt repository. run: `dolt init` before trying to run this command"* — which reads as "your queue is
gone". The repository is **one level deeper**, in a directory named after the database
(`…/embeddeddolt/<db>/`, the one holding `.dolt`). From there `dolt status`, `dolt log`, `dolt merge`
and `dolt config --local --list` all work. This is structural to embedded storage rather than one
VM's quirk: a freshly `bd init`-ed database nests the same way.

**Do not take the suggestion.** Measured in a throwaway of the same shape: `dolt init` there
**succeeds**, and `dolt status` then reports `On branch main` / `nothing to commit, working tree
clean` — an empty database, described confidently, one level above the real one. The nested database
and its rows survive, so this is recoverable rather than fatal; what it costs you is the ability to
notice the instrument was pointing at the wrong place. That is the governing rule with its sign
flipped: a check that cannot fail, because you made it answer about something else.

**Identity for a manual merge.** A hand-run `dolt merge`/`dolt commit` needs an author and may have
none — there is no global dolt identity on these VMs and a bd-created store need not carry a local
one, so it stops with *"Could not determine name and/or email"*. Set it **local to that repository**
and to the identity bd's own writes use, not your own name; the author column already carries both
`beads <beads@local>` and `root <root@%>` from bd itself, so it is not the record of your hand pass —
the backup and your notes are.

```bash
dolt config --local --add user.name beads
dolt config --local --add user.email beads@local
```

**Back up first — `cp -a embeddeddolt embeddeddolt.bak` — and measure it rather than assuming it is
small.** Size is not a constant to quote: this store measured 4.1 GB, of which 3.8 GB was a
re-fetchable `git-remote-cache`, while the backup taken the day before was 7.4 MB. `du -sh` answers
it in the moment; a number written here is wrong within a day.
