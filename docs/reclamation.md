# reclaim-worktrees: the weekly reclamation, as a job

`scripts/reclaim-worktrees.sh` applies the SCHEDULED RECLAMATION rules in [the work contract](conductor-work-contract.md) section 4: it removes worktrees whose pull request is finished, rescues ones holding uncommitted work, never touches a path a live session is in, and clears build caches with their own commands.

```bash
~/.claude/scripts/reclaim-worktrees.sh --dry-run           # classify everything, change nothing
~/.claude/scripts/reclaim-worktrees.sh                     # the weekly run
~/.claude/scripts/reclaim-worktrees.sh --if-due            # ...but only if one is overdue
~/.claude/scripts/reclaim-worktrees.sh --install-schedule  # register the launchd job
~/.claude/scripts/reclaim-worktrees.sh --uninstall-schedule
```

Needs bash 4+ (macOS `/bin/bash` is 3.2; the shebang finds Homebrew's), plus `git`, `jq`, `agent-deck` and `gh` on PATH. A run takes under a minute.

## Why it is a job and not a checklist

A manual sweep scoped by repository from memory missed a repository holding 45 GB while the disk sat at 136 MB free. Discovery here is mechanical, and anything it could not examine is named in the report. The steady-state cost is structural: one worktree per bead means one dependency tree per bead.

## The safety argument

**Removing a worktree does not delete its branch or commits**; only uncommitted files are at risk. So the job is safe if and only if it (1) never touches a path held by a live agent-deck session and (2) rescues uncommitted work before considering removal.

- **Unpushed commits are not checked.** A branch ahead of master keeps its commits after its worktree is gone, and a squash-merged branch still reads as ahead. **Pull request state decides removal, never a commit count.**
- **`git worktree remove` is called without `--force`.** A worktree holding only gitignored paths (a 200 MB `node_modules`) removes cleanly; one with an untracked or modified file is refused. The gigabytes are all in the first case, so declining to force costs no disk and git's refusal is a second opinion behind the script's dirty check.

## What happens to each worktree

Checked in this order; the first match wins.

| Verdict | When | What happens |
| --- | --- | --- |
| `kept-live` | a live session is in it | nothing, ever |
| `kept-uncommitted` | tracked changes or untracked files | rescued to `~/evidence/rescued-worktree-files/<date>-<repo>-<name>/`, **left in place** |
| `rescue-failed` | dirty, but the rescue could not be proved | left in place, reported for a human |
| `kept-locked` | locked, holder alive or unidentifiable | nothing |
| `removed-after-unlock` | locked, and `ps -p` says the holder is gone | unlocked, then removed |
| `kept-pr-open` | its pull request is open | nothing |
| `removed` | its pull request is MERGED or CLOSED | removed |
| `removed` | no pull request, and nothing has touched it for 14 days | removed |
| `kept-no-pr` | no pull request, touched more recently | nothing |
| `kept-undetermined` | detached HEAD, `gh` unreachable, or git could not report | nothing |

`--dry-run` reports `would-remove`, `would-remove-after-unlock` and `would-rescue` and writes nothing but the report. The order is load-bearing: an ancient no-PR worktree that is dirty is still rescued and left in place, and one a session sits in is still untouched.

**No-PR worktrees are reclaimed on age** (`RECLAIM_NO_PR_MIN_AGE_DAYS`, 14). PR state is not a safety signal, since the branch survives either way; it only says whether someone is still using the copy, and age answers that better. Age is the **newest** of the worktree directory's mtime and `logs/HEAD` in its private git admin directory (touched by every checkout, commit, reset or rebase in that worktree). The HEAD commit's date is deliberately excluded: a worktree created today from an ancient commit would read as dead, and a branch last pushed from another machine would read as alive. Age that cannot be read keeps the worktree.

**A dirty worktree is rescued and LEFT IN PLACE.** Removing it needs `--force`, which discards the safety property above; the rescue copy makes the work recoverable and leaving the tree makes it not need recovering.

## Reading the report

Printed to stdout and written to `~/evidence/reclamation/reclaim-<timestamp>.md`. The gap list comes first, because it caps what every number below means; on a clean run there is none. Then the counts, the cache results, and `KEPT, AND WHY` (every worktree not removed, with its reason; a worktree not in the report was not seen). Unreadable directories are listed in full at the end.

Exit codes: **0** clean sweep, **1** swept but something could not be examined, **2** refused before touching anything.

**A permanent entry in the gap list is a defect:** a reader who learns the list never changes stops reading it, and the entry that mattered is lost. So constants are counted, not gapped:

- **A `.git` that is not a repository is counted.** A zero-byte `.git` FILE (`fatal: invalid gitfile format`, e.g. under `~/.cache/uv`) cannot hold a worktree; a `.git` DIRECTORY with `fatal: not a git repository` could, so it stays a gap. The test is structural because git reports both as failures.
- **Only newly-unreadable directories are gapped.** The known set (mostly TCC-protected `Library` subtrees) lives in `~/evidence/reclamation/unreadable-baseline.txt`; its count is stated every run and only paths not seen before raise a gap.
- **A uv cache lock held by a live process is SKIPPED, not FAILED** (below).

**The one refusal:** if `agent-deck list --json` cannot be read, the run refuses and does nothing. An unreadable registry is not an empty registry, and treating it as empty deletes a live session's worktree.

## Caches

Tool-native commands only: `npm cache clean --force`, `yarn cache clean`, `pip cache purge`, `uv cache prune`. A recursive force-delete is rejected by the `security-block` hook, correctly.

**Bazel is reported, not cleared.** `bazel clean` needs a workspace, so it cannot reach an output base whose workspace is gone, which is the stale case worth reclaiming; guessing at the layout with a recursive delete is forbidden. No bazel output base exists on this machine, so a bazel branch could not be tested.

**launchd hands the job only its plist `PATH`.** No shell, profile or nvm shim, so `npm` and `yarn` (under `~/.nvm/versions/node/<version>/bin`, a moving path) and `pip` (only `pip3` exists) were "not present" and the first installed run cleared 0 of 11 GB, exited 0, and read as clean. So `resolve_tool()` searches `PATH` and then the places launchd cannot reach (`pip` via `pip3` first), and a tool still not found is a **gap**: `NOT FOUND ... this cache was NOT cleared`, exit 1. `RECLAIM_TOOL_DIRS` overrides the fallback list; it exists because the fallback once walked past the test stubs and purged a real 7.3 GB pip cache.

**The uv cache usually is not reclaimed, and that is SKIPPED, not failed.** Long-running `uv run` MCP servers (`trellis`, `mcpdoc`) hold `~/.cache/uv/.lock`, so `uv cache prune` times out ("Cache is currently in-use"). It is `SKIPPED` and does not set exit 1 only if all three hold: `lsof` names a process holding `<cache>/.lock`, `ps -p` confirms it is alive, and uv's own output says it was a lock. Any other failure stays `FAILED` with a gap and exit 1, as does a missing `lsof`. `--force` is deliberately not used (pruning a cache another process is reading). `RECLAIM_UV_LOCK_TIMEOUT` bounds the wait at 30 seconds (uv's default of 300 was all spent unattended). Reclaiming the roughly 1.9 GB of a 3.7 GB cache means stopping the uv processes and pruning by hand, not forcing it at 03:00. `prune`, not `clean`, because `clean` charges most of what it frees back on the next resolve.

## The traps, and why the code looks the way it does

**The live-session check is directional.** A worktree is held if some session path **is** it or lies **beneath** it, never the reverse. A substring or regex match fails silently and totally: one live session's path is the repository root (here `$HOME`), a prefix of every worktree, so everything reads LIVE and the report says "nothing to clean". An exact match is wrong the other way: a session that `cd`'d into a subdirectory of its worktree matches nothing and its worktree is removed underneath it.

**Rescuing uncommitted work must handle untracked directories.** `git status --porcelain` collapses an untracked directory to one entry, and plain `cp` silently skips a directory, producing an empty patch reported as success. Two defences: enumerate with `git ls-files --others --exclude-standard` (files only; `cp -R` stays for symlink-to-directory), and **prove the copy landed**: a dirty check that found something followed by an empty patch and no files is `rescue-failed`.

**PR state is asked per branch, not per repository.** One `gh pr list` per repository returns a capped page (18 of 71 repos returned the full 400), so a branch with a PR further back read as having none.

**Records are separated by `0x1f`, not a tab.** Tab is IFS whitespace, so bash collapses empty fields and shifts every later field left (a detached worktree parsed as a locked one).

## The schedule

`--install-schedule` writes `~/Library/LaunchAgents/com.jonny.reclaim-worktrees.plist`, loads it, and **verifies `launchctl` lists the label**, failing loudly if not. Sundays 03:00, **plus at load, guarded by `--if-due`.**

Asleep at 03:00 is fine: launchd runs it at the next wake. **Powered off at 03:00 skips the occurrence outright** (the calendar interval is an event stream that exists only for the boot session), a silent lost week, which `RunAtLoad` fixes.

### The `--if-due` guard

Logins are frequent and the job deletes directories, so `--if-due` runs only if the last **completed** run is **6 or more days** old. `--if-due` is passed only by the launchd job; a run by hand is never suppressed.

| parameter | value | why |
| --- | --- | --- |
| window | 6 days (`RECLAIM_DUE_AFTER_DAYS`) | Not 7: a weekly job's runs are 7 days apart, so 7 plus an hour of drift or a DST shift reads its own week as recent. |
| record | `~/evidence/reclamation/last-run`, epoch seconds | Survives reboot (not `$TMPDIR`), and sits outside every git repository because the job sweeps `~/.claude` itself and could delete its own guard. Moves with `--evidence-dir`. |
| written when | at **completion** | At start, a first-minute crash suppresses the job for a week. At completion, a hang never records and the next login reruns it; the sweep holds a lock so a second run refuses with exit 2. |
| what counts | exit 0 or 1 | Exit 2 paths all sit above the record write. `--dry-run` records nothing. |

`RECLAIM_DUE_AFTER_DAYS`, like every `RECLAIM_*` variable, affects manual runs only: the plist's `EnvironmentVariables` carries `PATH` and `HOME` and nothing else. To change what the job uses, change the script default and reinstall.

**The guard errs toward running.** No record, an empty or prose record, an over-long number, a future timestamp: none is evidence a sweep completed, and only evidence of a run may suppress one. launchd has one `ProgramArguments` per job, so the flag applies to the Sunday occurrence too; that self-corrects (7 days between Sundays exceeds the window; a Saturday catch-up correctly skips Sunday).

**`--install-schedule` starts a run.** `RunAtLoad` launches the job at `launchctl bootstrap`, and with no record it reads as due. **Never run it to inspect the plist**; read `write_plist` instead.

XPC Activity was rejected on a hard requirement: it needs `xpc_set_event_stream_handler(3)`, which a bash script cannot call, and `launchctl` cannot fire an activity to verify it. `pmset repeat wakeorpoweron` changes the laptop, not this job, and is out of scope.
