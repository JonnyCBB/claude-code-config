# reclaim-worktrees: the weekly reclamation, as a job

`scripts/reclaim-worktrees.sh` applies the SCHEDULED RECLAMATION rules in
[the work contract](conductor-work-contract.md) section 4: it removes worktrees whose pull request
is finished, rescues the ones holding uncommitted work, never touches a path a live session is in,
and clears the build caches with their own commands.

```bash
~/.claude/scripts/reclaim-worktrees.sh --dry-run           # classify everything, change nothing
~/.claude/scripts/reclaim-worktrees.sh                     # the weekly run
~/.claude/scripts/reclaim-worktrees.sh --if-due            # ...but only if one is overdue
~/.claude/scripts/reclaim-worktrees.sh --install-schedule  # register the launchd job
```

Needs bash 4+ (macOS `/bin/bash` is 3.2; the shebang finds Homebrew's), plus `git`, `jq`,
`agent-deck` and `gh` on PATH.

Measured on the real machine 2026-08-19, 71 repositories and 99 worktrees: **38 seconds** for a
`--dry-run`, **42 seconds** for the destructive run that removed 6 worktrees. Most of it is `find`
over `$HOME`. Both figures are in `~/evidence/jbrooksbartlett-e1ak/measurements-2026-08-19.md`.

## Why it is a job and not a checklist

On 2026-08-19 the disk reached **136 MB free on a 460 GB volume** and every session's writes began
failing. A manual sweep that morning cleaned two repositories, reported the job done, and never
examined a third holding **45 GB** - because it had been scoped by repository from memory. Disk
free went 49 GB -> 114 GB on the second pass.

That is the whole argument. A human sweeping from memory misses whole repositories; discovery here
is mechanical, and anything it could not examine is named in the report.

Of the 35 worktrees cleared that day, 34 needed no rescue at all: 25 belonged to merged pull
requests, 7 were stale auto-created copies, 2 were live sessions. **Exactly one held uncommitted
work.** The steady-state cost is structural - one worktree per bead means one full dependency tree
per bead, and nothing was reclaiming them.

## The safety argument, which is the whole design

**Removing a worktree does not delete its branch or its commits.** Those live in the repository's
object store and survive - verified across all 35 removals on 2026-08-19, and asserted in the
suite. Only **uncommitted files** are ever at risk.

So the job is safe if and only if it

1. never touches a path held by a live agent-deck session, and
2. rescues uncommitted work before it considers removing anything.

Two things follow that reviewers ask about:

**Unpushed commits are not checked, and do not need to be.** A branch ahead of master keeps its
commits after its worktree is gone. Commit counts would also be the wrong test for the wrong
question: a squash-merged branch still reads as ahead of master, which is why **pull request state
decides removal, never a commit count**. That distinction is what made the 2026-08-19 audit
trustworthy.

**`git worktree remove` is called without `--force`.** Measured on git 2.54.0: a worktree holding
only gitignored paths - a 200 MB `node_modules` - removes cleanly, while one holding an untracked
or modified file is refused with `contains modified or untracked files`. The gigabytes are all in
the first case, so declining to force costs no disk. It only protects the dirty worktrees, where
git's own refusal is a second opinion behind the script's own dirty check.

## What happens to each worktree

Checked in this order. The first rule that matches wins, so the live-session check runs before
anything else and the dirty check runs before any removal decision.

| Verdict | When | What happens |
| --- | --- | --- |
| `kept-live` | a live session is in it | nothing, ever |
| `kept-uncommitted` | tracked changes or untracked files | rescued to `~/evidence/rescued-worktree-files/<date>-<repo>-<name>/`, **left in place** |
| `rescue-failed` | it is dirty but the rescue could not be proved | left in place, reported for a human |
| `kept-locked` | locked, and the holder is alive or unidentifiable | nothing |
| `removed-after-unlock` | locked, and `ps -p` says the holder is gone | unlocked, then removed |
| `kept-pr-open` | its pull request is open | nothing |
| `removed` | its pull request is MERGED or CLOSED | removed |
| `removed` | no pull request, and nothing has touched it for 14 days | removed |
| `kept-no-pr` | no pull request, but something touched it more recently than that | nothing |
| `kept-undetermined` | detached HEAD, `gh` unreachable, or git could not report | nothing |

`--dry-run` reports `would-remove`, `would-remove-after-unlock` and `would-rescue` and writes
nothing but the report itself.

The order is load-bearing, and two tests exist solely to pin it: an ancient no-PR worktree that is
dirty is still rescued and left in place, and an ancient no-PR worktree a session is sitting in is
still untouched. If either fails, the age rule has been moved ahead of a guard.

### The no-pull-request class is reclaimed on age

A worktree whose branch has no pull request at all is reclaimed once **nothing has touched it for
14 days** (`RECLAIM_NO_PR_MIN_AGE_DAYS`), a rule Jonny set on 2026-08-19 (`jbrooksbartlett-e6ne`).
The argument is that **pull request state is not a safety signal in the first place**. A removed
worktree keeps its branch and its commits either way, so what pull request state actually tells you
is whether someone is still *using* the working copy - and for that, age
is a better answer than the absence of a pull request. The safety comes from the live-session and
uncommitted checks, which run first and apply to this class identically.

It mattered: this class was 7 of the 35 worktrees cleared on 2026-08-19, **20% of the reclaim**, and
nothing else reaches it - those 7 were not locked either, so the dead-lock rule missed them too.

Age is the **newest** of two signals, so any sign of life keeps the worktree:

- the worktree directory's own mtime
- `logs/HEAD` in the worktree's private git admin directory, which git touches on every checkout,
  commit, reset or rebase performed *in that worktree*

The HEAD commit's date is deliberately **not** one of them. It answers a different question and
gets it wrong in both directions: a worktree created today from an ancient release commit would
read as long-dead, and a branch whose last commit was pushed from another machine would read as
alive while this copy sat untouched for a month. A worktree whose age cannot be read at all is
kept, not guessed at.

### A dirty worktree is rescued and LEFT IN PLACE

Removing a dirty tree would mean passing `--force`, which discards the one safety property the
contract itself praises. A rescue copy makes the work recoverable; leaving the tree makes it not
need recovering, which is the better outcome for a job running unattended at 03:00.

This superseded an earlier rule that rescued and then removed (`jbrooksbartlett-trts`).

## Reading the report

Printed to stdout and written to `~/evidence/reclamation/reclaim-<timestamp>.md`.

The gap list comes **first**, because it caps what every number below is allowed to mean. On a
clean run there is no gap list at all:

```
WORKTREE RECLAMATION  2026-08-20T14:39:44Z
work contract section 4, SCHEDULED RECLAMATION

repositories swept ......... 71
worktrees examined ......... 103  (71 of them a repository main tree, never removable)
unreadable directories ..... 121 known
not git repositories ....... 1 (a .git that is not a repository, so it cannot hold a worktree)
live sessions consulted .... 21
```

### A permanent entry in the gap list is a defect, not noise

The gap list is the only channel that can ever say a sweep was incomplete, and it is printed above
the numbers so it cannot be skipped. That makes a permanently-recurring entry worse than useless: a
reader who learns the list is always the same stops reading it, and the next entry, the one that
mattered, is lost. Three separate cases of this turned up on 2026-08-20 and all three are now
handled the same way, by moving the constant out of the gap list and leaving only the news in it.

**A `.git` that is not a repository is counted, not gapped.** `~/.cache/uv/sdists-v9` is a build
artifact whose `.git` is a zero-byte file, and it appeared in the gap list of the first real run.
The test is structural rather than a reading of git's verdict, because git reports both cases as
failures and cannot separate them for us:

```
~/.cache/uv/sdists-v9      .git is a zero-byte FILE   fatal: invalid gitfile format
a repo with a broken HEAD  .git is a DIRECTORY        fatal: not a git repository
```

A valid `.git` file contains `gitdir: <path>`; a malformed one cannot hold a worktree, so nothing
can hide there and its unexaminability is not a blindness. A `.git` **directory** could hold one and
we cannot tell, so it stays a gap. There are 32 such `.git` entries under `~/.cache` alone.

**Only NEWLY-unreadable directories are gapped.** The set is 196 paths and byte-identical across
consecutive runs, mostly macOS TCC-protected `Library` subtrees. The known set lives in
`~/evidence/reclamation/unreadable-baseline.txt`, the count is stated as a plain fact every run, and
only paths not seen before raise a gap, so a newly-unreadable directory is reported exactly once.
The report lists only the new ones for the same reason: printing all 123 buried the two that
mattered.

**A uv cache lock held by a live process is SKIPPED, not FAILED.** See below.

Then the counts, the cache results, and **`KEPT, AND WHY` - every worktree that was not removed,
with its reason**. That section is the point: a cleanup reporting success having examined half the
machine is the defect class this codebase produces most often, and if a worktree is not in the
report it was not seen. The unreadable directories are listed in full at the end of the file, so
the summary stays short and the detail stays actionable.

Exit codes: **0** a clean sweep, **1** swept but something could not be examined, **2** refused
before touching anything.

### The one refusal

If `agent-deck list --json` cannot be read, the run **refuses and does nothing**. An unreadable
registry is not an empty registry, and treating it as empty is the one mistake that deletes a live
session's worktree. Nothing is lost by retrying.

## Caches

Tool-native commands only - `npm cache clean --force`, `yarn cache clean`, `pip cache purge`. A
recursive force-delete is rejected by the `security-block` hook, correctly, and a tool that knows
its own cache layout is the safer instrument anyway.

**Bazel is reported, not cleared, and that is deliberate.** `bazel clean` needs a workspace to run
in, so it cannot reach an output base whose workspace has been deleted - which is exactly the stale
case worth reclaiming. Guessing at the layout with a recursive delete is the one thing the contract
forbids. No bazel output base exists on this machine, so a bazel branch here could not be tested
and would be a check that cannot fail.

### The caches only work if the tools can be found, and launchd makes that hard

**Measured on the first real run of the installed job, 2026-08-20.** It reclaimed nothing from any
cache and said so like this:

```
npm    not present   npm is not on PATH
yarn   not present   yarn is not on PATH
pip    not present   pip is not on PATH
```

All three were installed. launchd hands the job the `PATH` written into its plist and nothing else:
no shell, no profile, no nvm shim. On this machine `npm` and `yarn` live under
`~/.nvm/versions/node/<version>/bin`, which no fixed `PATH` can name because the version moves, and
there is a `pip3` but no `pip` at all. So the job cleared **0 of 11 GB** of cache while reclaiming
46 MB of worktrees, exited 0, and read as clean. Interactively it had always worked, because an
interactive shell has the nvm path.

Two fixes, and the second matters more than the first. `resolve_tool()` now looks on `PATH` and
then in the places launchd cannot reach, and `pip` resolves through `pip3` first. And a tool that
still cannot be found is a **gap**: it reports `NOT FOUND ... this cache was NOT cleared` and the
run exits 1. "Not present" reading as "nothing to do" is exactly the failure this job's whole
report design exists to prevent, and it had it.

`RECLAIM_TOOL_DIRS` overrides that fallback list. That exists because the fallback let the script
walk straight past the test suite's stubs and purge a real 7.3 GB pip cache during a test run: a
subject that can step outside its harness is not under test.

**The uv cache will usually NOT be reclaimed, and the job reports it as SKIPPED rather than
failed.** Measured
2026-08-20 under a faithful launchd environment, with npm, yarn and pip all cleaning successfully:

```
uv  FAILED  uv cache prune -> Cache is currently in-use, waiting for other uv processes to finish
            error: Timeout (30s) when waiting for lock on ~/.cache/uv/.lock
```

Three long-running MCP servers on this machine are `uv run` processes (`trellis`,
`knowledge-graph`, `mcpdoc`) and they hold that lock for as long as they are up, which is
essentially always. So the largest single cache, 3.7 GB, is the one the job can least often touch.
That is expected rather than broken, so it is reported `SKIPPED` and does **not** set exit 1. The
distinction is narrow and both halves are checked, because giving up a true signal for a quiet false
green would be the worse trade: `lsof` must name at least one process holding `<cache>/.lock`,
`ps -p` must confirm it is alive, **and** uv's own output must say it was a lock. Any other failure
stays a `FAILED` row with a gap and exit 1, and if `lsof` is unavailable the check cannot be made so
the failure stands. Two tests pin each half independently.

`--force` would override the lock and is deliberately not used: pruning a cache another process is
reading is a worse trade than leaving it. `RECLAIM_UV_LOCK_TIMEOUT` bounds the wait, defaulting to
30 seconds because the uv default is 300 and an unattended job spent all of it.

**How much is actually at stake, measured rather than estimated:** `uv cache prune` would reclaim
**1.93 GB of 3.69 GB** (72,399 files). Measured on an APFS copy-on-write clone of the cache with
`UV_CACHE_DIR` pointed at it, so the live cache was never touched. That is more than npm, pip and
yarn combined, so the honest way to reclaim it is to stop the uv processes briefly and prune by
hand; it is not something this job should force at 03:00.

`uv` is in the cache list (`jbrooksbartlett-di8u`) because its cache measured **3.7 GB**, roughly
ten times the three caches named before it, combined. The
rule is `uv cache prune` rather than `uv cache clean`: `clean` reclaims all 3.7 GB and then charges
most of it back on the next resolve, so the real saving is smaller than the number looks, while
`prune` keeps what is still in use.

## The two traps, and why the code looks the way it does

Both were paid for on 2026-08-19. Both have tests that fail if the fix is removed.

### The live-session check is directional, not a substring match

The obvious implementation asks whether a worktree path *matches* any live session path. As a
substring or regex match that **fails silently and totally**: one live session's path is the
repository root, a prefix of every worktree beneath it. Measured - substring match **37 LIVE / 0
stale**, correct match **2 LIVE / 35 stale**. The report would have read "nothing to clean", which
is indistinguishable from a clean machine. On this machine it is worse: one session's path is
`$HOME`, a prefix of every path that exists.

**A pure exact match is also wrong, in the other direction**, and nothing in the bead says so. A
session that has `cd`'d into a subdirectory of its own worktree matches nothing exactly, so its
worktree reads as stale and is removed underneath it. That is the failure that loses live work
rather than merely disk.

So the test is: a worktree is held if some session path **is** it, or lies **beneath** it. Never
the other direction.

### Rescuing uncommitted work must handle untracked directories

A rescue loop that copies each untracked path with plain `cp` **silently skips a directory**:

```
$ git status --porcelain
?? .claude/
$ cp wt/.claude dest/
cp: wt/.claude is a directory (not copied).
```

That is not hypothetical. `~/.claude/.claude/worktrees/review-home-experiment` still reports its
uncommitted state as exactly one line naming a directory, and the 2026-08-19 rescue of that class
produced an empty patch and no files - and reported success.

Two defences, because one is not enough:

1. Enumerate with `git ls-files --others --exclude-standard`, which lists **files** and never
   directories, rather than `git status --porcelain`, which collapses an untracked directory to a
   single entry. The trap cannot arise from an input that is never a directory. `cp -R` is still
   used, for a symlink-to-directory and for any future git that answers differently.
2. **Prove the copy landed.** If the dirty check said there was something and the rescue ends with
   an empty patch and no files copied, that is the trap recurring and it is reported as
   `rescue-failed`. A rescue that cannot fail is not a rescue.

Verified live on that worktree: 19 files rescued with their directory structure intact.

### Two smaller ones, from the first live run

**Pull request state is asked per branch, not per repository.** Batching one `gh pr list` per
repository looked cheaper and was wrong twice: 18 of 71 repositories returned a full page of 400,
so a branch whose pull request sat further back read as having none; and it was not even cheaper,
because most repositories have nothing but their main working tree, so it bought 71 calls to answer
about 20 questions. Per-branch is exact, uncappable, and took the run from 1m43s to 38s.

**Records are separated by `0x1f`, not by a tab.** Tab is an IFS *whitespace* character, so bash
collapses a run of them and a record with an empty field reads back with every later field shifted
one place left. Measured while writing this: a detached worktree (empty branch) parsed as a
**locked** worktree whose lock reason was `0`.

## The schedule

`--install-schedule` writes `~/Library/LaunchAgents/com.jonnybrooks.reclaim-worktrees.plist`,
loads it, and then **verifies that `launchctl` lists the label** - failing loudly if not. An
install that wrote a plist nobody loaded is a schedule that never fires, and on disk it looks
exactly like one that will; only a positive marker can tell them apart.

Sundays 03:00, **plus at load, guarded by `--if-due`.**

**Asleep at 03:00 is fine.** launchd starts the job at the next wake - in practice Monday morning,
which is when a week of dispatches starts and disk pressure matters most. The job is safe whenever
it runs, so the drift costs nothing.

**Powered off at 03:00 was not fine, and that is what `RunAtLoad` fixes.** The occurrence was
skipped outright and the next run was the *following* Sunday: no error, no log line, nothing to
notice, and a week of reclamation that silently did not happen. `man launchd.plist` documents only
the sleep case; `launchctl print` shows why off differs - the schedule is a
`com.apple.launchd.calendarinterval` event stream monitored by `UserEventAgent`, which exists only
for the boot session it is in, so an occurrence with no session to fire into is simply gone.

### The `--if-due` guard, and why it is not optional

Logins are frequent and this job **deletes directories**, so an unguarded `RunAtLoad` would sweep
several times a day. `--if-due` makes the run conditional on the last **completed** run being
**6 days or more** old.

| parameter | value | why |
| --- | --- | --- |
| window | 6 days or more (`RECLAIM_DUE_AFTER_DAYS`, manual runs only - see below) | Not 7. A weekly job's own runs are 7 days apart, so a 7-day window plus an hour of clock drift or a DST transition reads its own week as "recent" and skips it. 6 days leaves 24 hours of slack and still suppresses a login the day after a run. |
| record | `~/evidence/reclamation/last-run`, epoch seconds | Survives a reboot, so not `$TMPDIR` - a missed week must not be re-missed. Outside every git repository, because **this job sweeps `~/.claude` itself**, and state kept in the repo is state the job can delete out from under its own guard. Moves with `--evidence-dir`, so the suite fences it in. It sits beside the reports and `unreadable-baseline.txt`, which are durable for the same reasons. |
| written when | at **completion**, not at start | Both directions have a cost. At start, a run that crashes in its first minute suppresses itself for a week - which *reproduces* the bug being fixed. At completion, a run that **hangs** never records, so the next login runs it again. Completion wins because the hang is already bounded and the crash is not: the sweep holds a lock, so a second run while the first is going refuses with exit 2 and removes nothing. |
| what counts as a run | exit 0 or exit 1 | Exit 1 is "swept, with gaps" - it swept. Exit 2 is "refused before doing anything", and every exit-2 path sits *above* the record write, so "a run that started and failed is not a run" is true by construction rather than by a flag. `--dry-run` records nothing. |

`RECLAIM_DUE_AFTER_DAYS` **only affects manual invocations.** The generated plist's
`EnvironmentVariables` dict carries `PATH` and `HOME` and nothing else, so the scheduled job always
uses the code default of 6 days. That is true of every `RECLAIM_*` variable in the script, not just
this one - exporting one before `--install-schedule` does not change the installed job. To change
the window the job actually uses, change the default in the script and reinstall.

**The guard errs toward running, always.** No record, an empty record, a record full of prose, a
number too long to be a timestamp, a timestamp in the future: none of them is evidence that a sweep
completed, and only evidence of a run may suppress one. The two failure modes are not symmetric -
always saying "ran recently" gives a weekly job that never runs again, silently, which is strictly
worse than losing one week.

launchd has **one `ProgramArguments` per job** and no way to tell a job which trigger started it, so
the flag applies to the Sunday occurrence too. That is deliberate and it self-corrects: 7 days
between Sundays always exceeds the 6-day window, and if a login catch-up ran on the Saturday then
the Sunday occurrence one day later is correctly skipped - that week has already been swept.

`--if-due` is passed **only** by the launchd job. A run started by hand is never suppressed.

### Two things that will surprise you

**`--install-schedule` now starts a run.** `RunAtLoad` means `launchctl bootstrap` launches the job
immediately, and with no record yet it reads as due - so installing begins a real sweep. Measured
2026-08-21: a probe install registered the label and launchd started the script the same second.
The install output says so when there is no record.

**Never run `--install-schedule` outside the suite to inspect the plist.** It calls the real
`launchctl`, and with `RunAtLoad` the job starts. Use the suite, which stubs `launchctl`, or read
the template in `write_plist`.

### Why not XPC Activity

It is the mechanism that expresses "every N seconds, catching up" directly -
`LaunchEvents > com.apple.xpc.activity > {Interval, Repeating, Priority}`, used by
`com.apple.applessdstatistics` and other system daemons on this machine. It was rejected on a hard
requirement, not on taste: `man launchd.plist` states that with `LaunchEvents` "the job promises to
use the `xpc_set_event_stream_handler(3)` API to consume events", and a bash script cannot call it
or mark an activity done. It also trades a fixed 03:00 for an opaque tolerance window at the
system's discretion, and `launchctl` has no verb that fires an activity - so it could not be
verified the way every change to this job has been, by installing a temporary copy and firing it.

(`pmset repeat wakeorpoweron` is the other real option. It powers the machine on at 02:55 - a
change to the laptop rather than to this job, and out of scope.)

`--uninstall-schedule` reverses the install.

## Tests

```bash
bash scripts/tests/test-reclaim-worktrees.sh                        # prints N passed, 0 failed
EXPECT_BOOTSTRAP_RED=1 bash scripts/tests/test-reclaim-worktrees.sh # must fail, exactly once
```

The repositories in the suite are **real git repositories with real worktrees**, so classification
runs against real `git worktree list --porcelain`, real `git status`, real `git ls-files` and a real
`git worktree remove`. Only `agent-deck`, `gh`, `ps`, the cache tools and `launchctl` are stubbed -
the last so the suite can never register a real weekly job, and the cache tools so it can assert
that `bazel` is never invoked. Both traps live in how git's own output is interpreted, so stubbing
git would test nothing.

This repo has no CI (`jbrooksbartlett-sqmi`), so that suite is the only gate, which is why it
carries a bootstrap-RED sentinel: a harness that recorded zero assertions would otherwise print
"0 passed, 0 failed" and exit green.
