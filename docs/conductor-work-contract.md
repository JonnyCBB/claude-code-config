# The work contract: how Jonny and the conductor handle beads

Agreed 2026-08-18 in an interview with Jonny. Reasoning, the evidence each rule was decided against, and the options he rejected: `~/.claude/thoughts/shared/requirements/2026-08-18-conductor-work-contract-requirements.md`. Read it when a rule looks arbitrary.

**Why this file lives here:** `agent-deck conductor setup hq` rewrites `hq/CLAUDE.md` and `hq/POLICY.md`, so anything in the hq directory can be destroyed without warning. This file and `~/.claude/CLAUDE.md` (which points at it) are outside that command's reach.

**This is an AMENDMENT.** It changes the rules named in section 11 and leaves the rest of `hq/CLAUDE.md` and `../CLAUDE.md` in force. Superseded text has been edited in place so a restarted conductor cannot act on it.

**PRECEDENCE: this contract outranks BOTH `POLICY.md` files**, because neither is durable: `agent-deck conductor setup` writes `hq/POLICY.md` (`-policy-md`) and `../POLICY.md` (`-shared-policy-md`). `hq/CLAUDE.md` prefers `./POLICY.md` when it exists and today it does not, so `../POLICY.md` is in force; a setup re-run that creates `hq/POLICY.md` would shadow the shared file entirely and reinstate superseded rules. **If a POLICY.md contradicts this contract, the contract wins; the POLICY.md has probably just been regenerated. Check it against `../POLICY.md.pre-contract-2026-08-18`.**

**The bias:** dispatch as soon as possible with the least friction; ask forgiveness, not permission; the conductor has far more context than Jonny, so its queue judgement is usually better.

**The failure he cares most about:** "The worst thing we can do is to not close a bead when it is completed and therefore block another bead from being dispatched."

---

## 1. The effect gate: what the conductor does without asking

The line is EFFECT: what exists afterwards that did not before, and can the conductor alone undo it, quickly, with nobody outside this rig having seen it.

### Autonomous - do it, report after

| Action | Notes |
| --- | --- |
| Any read | Code, docs, logs, dashboards, metrics, live and production systems |
| Any queue write | Triage, priority, dependency edges, ready, dispatch, close, dedup |
| A live or production write passing ALL FOUR tests below | |
| Spending up to **$1,000 on a single decision** | No aggregate cap. Log the amount and what it bought |

**The four tests for an autonomous live write. All four must hold.**

1. The conductor can revert it **within minutes**.
2. The revert path is **proven, not believed**: exercised before, or dry-run immediately before the write.
3. The revert needs **nobody else** (no other team, on-call, or second review).
4. It does **not expose real traffic**: no experiments, ramps, or variants reaching real users.

### Ask, every time, never on inherited authority

| Action | Why |
| --- | --- |
| A live write failing any of the four tests | Forgiveness is unavailable for what you cannot undo alone |
| Real-traffic exposure: experiments, ramps, variants | Stopping it does not un-expose anyone and the data stays contaminated |
| Messaging another person, posting outwardly, filing to another team | At any cost, under any authority. You cannot unsend |
| Over $1,000 on a single decision | |

Example: a live production Home config write is revertible by writing the old config back, but an all-users change is real-traffic exposure and fails test 4, so it is an **ask**.

**The $1,000 covers** money leaving the owner's accounts or drawing on a nameable budget (cloud spend, GPU reservations, paid API calls, licences). It does NOT cover Claude token spend on this machine, which the capacity rules in section 4 govern.

---

## 2. Triage

A scheduled agent runs **every 3 hours** and pre-triages the queue (not built yet: `hq-a5ss`). It closes duplicates as duplicates, corrects wrong priorities, adds visible dependency edges, sets to `open` anything passing the auto-ready test, and leaves a skim list of what it could not decide. **It writes the queue. It does NOT dispatch**: the conductor alone owns the capacity budget, or two dispatchers put five workers against a ceiling of three.

**Dedup means `bd close` with the `superseded` label, NEVER `bd delete --force`.** Force-delete orphans dependents: their `dependency_count` drops to zero and they read as UNBLOCKED (`hq-f1kv`).

### What earns a bead at all. Set by Jonny 2026-09-11; it outranks the auto-ready test.

File a bead only if something will break or not work as intended because of something not done. Keep: beads Jonny files himself, agent-filed beads that would otherwise leave a service non-functional or broken, and incredibly important user-valuable features.

**Do not file it, and delete it on sight if already filed:** "would be nice", a doc to tidy, a test or lint rule to strengthen, a lesson worth recording, prior art, a defect nobody will hit, someone else's tool we will not fix. All FAIL at every priority, P0 included.

**A bead recording Jonny asking for something is HIS.** `agent-proposed` records who typed the command, not whose decision it was: strip the label and leave the bead live.

**Deleting in bulk: write the rows down first.** One JSON line per bead (id, title, priority, status, labels, description, notes) to a durable path outside any git tree, line count checked against the delete set before the first delete. Dolt history is not a recovery plan. Check dependents too: `--force` is required to delete and orphans them in the same breath.

### The auto-ready test

An agent-filed bead goes from `deferred` to `open` without asking Jonny when **all four** hold:

1. It names a **concrete defect** with a reproducible failure, or a specific `file:line`.
2. The fix is **confined to the repo it was found in**.
3. It ends in a **reviewable PR**.
4. It was **discovered during real work**, not by a speculative hunt (six beads from speculative hunts passed tests 1 to 3 and were closed not-wanted).

Anything failing stays `deferred` with the `agent-proposed` label, invisible to `bd ready`, until Jonny confirms it. **The `agent-proposed` label survives promotion**: Beads records no useful creator field (`created_by` is always the OS user), so it is the only provenance. The skim query filters status as well, so a kept label costs nothing:

```bash
bd list --label agent-proposed --status deferred   # BOTH filters required
```

**Jonny's own beads carry no special flags and are live immediately.**

---

## 3. Dispatch

**Ready means dispatch. No approval, no announcement-and-wait.** A bead triaged to `open` that meets the spec bar is dispatched. Holding work back is the more expensive error: one dispatched bead whose job was to EXERCISE the system found 19 issues including a P0 alpha-blocker while the conductor held it against a concurrency ceiling.

**Every dispatch gives Jonny a way to watch the worker, in the announcing message**: session id plus `agent-deck session output <id> -q` plus the tmux name for local workers; the session's web link, if the runtime gives one, for remote workers. Several in one turn means a table, not a sentence each.

**Never write a bare ID to Jonny, bead or session. Always `id - title`.**

**Never put speed pressure in a dispatch spec.** "Other plans are blocked on you" is a reason to get it right, not to hurry. Correctness over speed is a standing preference.

---

## 4. Capacity and the three session states

**THERE IS NO NUMERIC CONCURRENCY CAP. THE CAP IS MACHINE RESOURCE CAPACITY, MEASURED** (Jonny, 2026-09-10). Dispatch while the machine has room, established by measuring, not by counting sessions. The earlier caps of 3 and 8 were derived on an 18 GB Mac and do not transfer between the machines sharing this queue; a number that does not transfer reads as a rule and behaves as a guess (a conductor under-dispatched all evening on a 64 GB machine with 51% memory free while quoting the stale figure).

| State | Definition | Counts toward capacity? |
| --- | --- | --- |
| **Active** | Working a bead | **Yes** |
| **Parked** | PR open, awaiting review or merge | **No.** Stays alive, excluded from the budget |
| **Finished** | Bead closed or merged | Removed immediately, after the section 5 checks |

**Parked sessions do not block dispatch.** The operative rule (a blocked item is set aside and the run continues to the next ready bead; nothing waiting on Jonny ever stops the queue; queue it, auto-fire when capacity frees, tell him, never ask) lives only in `conductor-heartbeat-rules.md` section 2, which is injected into every heartbeat. This file keeps the reasoning and the capacity table.

### Reclamation order under memory pressure

1. Retire **finished** sessions (cheapest, usually sufficient).
2. Stop **parked** sessions, **oldest first**. Stop, not remove: the worktree and PR stay intact. Record on the bead that the PR is merge-ready and what a relaunch would need.
3. Only then consider holding a dispatch.

**Stopping a parked session PRESERVES its conversation** (verified on all three stop paths: idle, `session restart`, mid-turn). `agent-deck session start` on a stopped Claude session runs `claude --resume <claude_session_id>`; the id and transcript `.jsonl` are unchanged.

1. **`start` and `restart` are the same resume path**; plain `start` already is the resume.
2. **A resumed session comes back IDLE** and does not continue on its own; send it a message.
3. **Do not diagnose context loss from one answer.** A fully-resumed session once answered "I DO NOT KNOW" to its planted token, then quoted it two questions later. Check the transcript's `parentUuid` chain. `session show --json`'s `claude_session_id` is re-derived from `~/.claude/projects/` when the registry value is missing, so it cannot confirm the stored id survived; query the sqlite `tool_data` column.

`agent-deck session remove` is registry-only by default: it preserves the transcript and does not touch the worktree; `--prune-worktree` is the destructive flag. Stop is still preferred because it keeps the session addressable.

### The thresholds

Dispatch while ALL FOUR hold, **re-measuring after each dispatch** (a reading more than a few minutes old is worthless; load moved from 1.3 to 16.3 within single 15-minute windows):

| Signal | Keep dispatching while | Why this number |
| --- | --- | --- |
| memory free | **>= 35%** | pageouts stayed zero down to 36% free |
| 1-minute load | **< 8** on 12 cores | ~0.67 per core; 16+ was simultaneous fan-outs |
| pageout rate | **~0** over a 15-second sample | the live signal; not yet calibrated against a genuine three-worker fan-out, so treat a sustained nonzero rate as the signal and load as the veto |
| **disk free** | **>= 20 GB** | covers a worktree plus dependency install (~200 MB for switchboard), build output, and fan-out room; a gate at 2 GB trips too late |

```bash
memory_pressure | tail -2         # free % >= 35
memory_pressure | grep Pageouts   # sample TWICE ~15s apart; the RATE must be near zero
uptime                            # 1-min load < 8 on 12 cores
df -g /System/Volumes/Data | awk 'NR==2 {print $4" GB free"}'   # want >= 20
```

**Free swap is NOT a veto.** macOS allocates swap one 1 GiB file at a time on demand (files live in `/System/Volumes/VM/`), which holds free swap near 1 GB in every machine state, so a `free >= 2000M` veto fires always and carries no information. Measure the paging itself (the `Pageouts` delta). 94% swap *used* is normal here.

**Memory vs disk are different failures:** memory pressure makes the machine SLOW; a full disk makes writes FAIL, unrecoverably mid-task, and can leave truncated files that look like syntax errors. Budget **~1 GB per active worker at peak** (0.57 GB measured at rest; fan-outs of 4-8 subagents spike it). **The failure mode of over-dispatching is slowness, not loss** (zero memory-kill or jetsam events across 24 hours including a load-25 peak); under-dispatching costs work that never happened. Those are not symmetric. Concurrent fan-outs can still exhaust memory and lose work, so **DISPATCH ONE AT A TIME AND RE-MEASURE.**

### SCHEDULED RECLAMATION - do not wait for the gate to trip

One worktree per bead means one dependency tree per bead; the disk hit 136 MB free when 28 switchboard worktrees (5.7 GB) and stale auto-created copies sat on work merged weeks earlier. The disk check stops a dispatch into a full disk but not the disk filling, so reclamation is **WEEKLY**, by `scripts/reclaim-worktrees.sh` via launchd (operator guide: [reclamation.md](reclamation.md)). Removing a worktree does **NOT** delete its branch or commits; only uncommitted files are at risk.

| What | Rule |
| --- | --- |
| Worktrees held by a **live session** | never touch; check `agent-deck list --json` paths, not titles. DIRECTIONAL: held if a session path IS it or lies BENEATH it |
| Worktrees with **uncommitted** changes | rescue the diff and untracked files to `~/evidence/rescued-worktree-files/<date>-<repo>-<name>/`, then **LEAVE THE WORKTREE IN PLACE** (removal needs `git worktree remove --force`, which discards git's refusal, the safety property) |
| Worktrees **locked** by a dead process | `ps -p <pid>` first. A lock whose process is gone is STALE and safe |
| Worktrees whose pull request is **MERGED or CLOSED** | remove |
| Worktrees with **no pull request** | remove once nothing has touched them for **14 days**. Age is the NEWEST of the directory's mtime and `logs/HEAD` in its private git admin directory (never the HEAD commit's date); unreadable age keeps it. PR state is not a safety signal, so age is the better test |
| Build caches (Bazel, npm, yarn, pip, **uv**) | tool-native commands (`npm cache clean`, `yarn cache clean`, `pip cache purge`, `uv cache prune`). A tool that cannot be FOUND is a gap, not a no-op (launchd gives only its plist PATH; npm, yarn and pip once read "not present" while 11 GB sat there). Bazel is REPORTED, not cleared |

**THE ROWS ARE EVALUATED IN ORDER, TOP TO BOTTOM, AND THE ORDER IS THE SAFETY.** Live session, then uncommitted work, then locks, then PR state or age. Read as an unordered set the table licenses removing a dirty worktree because its PR merged, which is backwards. The job reports every worktree it KEPT and why, and every repository it could not read.

**Do not run `rm -rf` to do any of this.** The `security-block` hook rejects it, rightly: `git worktree remove` refuses on a dirty tree and a recursive delete does not.

### FREE CAPACITY IS A DEFECT. FILL IT WITHOUT BEING ASKED.

Getting the backlog done is the conductor's core job; a conductor that reports accurately while the machine sits idle has failed at it. **ON EVERY HEARTBEAT AND AFTER EVERY SESSION CLOSES:**

1. Count ACTIVE sessions (parked ones awaiting Jonny do not count).
2. If the four capacity targets hold, **DISPATCH SOMETHING.** Do not wait for a prompt, report the free slot as an observation, or ask which item he prefers.
3. **Check the remote option separately and always**: remote sessions cost this machine nothing, so no capacity condition justifies skipping it.

**HOW TO CHOOSE, in order:**

- **Highest priority first**, weighted by LEVERAGE where close (`hq-fy9y`, moving plugins to an org repo, unblocks a class of remote work).
- **Jonny-originated beads outrank agent-proposed ones**; a bead carrying his own timing words outranks both.
- **Avoid collision:** no two sessions in the same repo area or onto work another in-flight session will touch. Check `agent-deck list --json` paths.
- **Route by shape:** needs a skill, credentials, a live system or local documents -> LOCAL. Everything it needs is in the repository and the output is a written conclusion or small diff -> REMOTE.

**IF NOTHING QUALIFIES, SAY SO AND WHY** ("Looked, three P1s left, all collide with the switchboard work in flight"); silence is indistinguishable from not having looked. **A bead too thin to dispatch gets SHARPENED, not skipped** (section 2's job; it takes minutes). "Nothing was dispatchable" is true only after trying to make something dispatchable.

### THE 3-HOUR RULE: a session waiting on Jonny is retired, not held open

A session `waiting` on a decision from Jonny for **3 hours** with no action gets **retired**; **the BEAD STAYS**. A parked session still holds its context in memory (~0.57 GB) plus a tmux session and worktree.

- **Check for an explicit keep instruction before retiring**, and record it in `state.json` when he gives one (a restarted conductor will not remember).
- **Run the pre-close checklist first** (section 5): `python3 ~/.claude/hooks/agent-deck-preclose.py <id>` must PASS. It saves the final output to `~/evidence/session-finals/`, which is what makes retiring safe.
- **Before the session goes, the bead must carry** the question Jonny was asked, the options put to him, and the recommendation. "Awaiting Jonny" without what he was asked is not resumable.
- **A STALLED SESSION IS NOT A WAITING SESSION.** One that stopped mid-work having asked nobody anything needs a nudge; retiring destroys work in progress. **Read the last message before deciding which case you have.**

### WHEN TO CHECK - event-driven first, timer as the floor

| Trigger | Action |
| --- | --- |
| **A session parks** (opens a PR, or starts waiting on Jonny) | Measure and dispatch immediately |
| **A session is retired** after a merge | Measure and dispatch immediately |
| **A bead is promoted or a blocker clears** | Measure and dispatch immediately |
| **Every heartbeat (~15 min)** | Measure anyway, as the backstop |
| Any other time | Do NOT poll. Reading a worker's pane to check liveness is not a capacity check |

These events arrive on their own via the inbox or stop hook.

### Remote sessions

**They do not count against local capacity** (they consume none of this machine's memory, processor or disk) **but they count against conductor ATTENTION.**

**THEY DO NOT PUSH. YOU MUST POLL.** The remote session's status read is the only feedback: no subscribe, no callback, no inbox event, and nothing tells you a session finished or asked a question. **Poll every live remote session at each heartbeat.** `suspended` is a five-minute idle timeout, resumable and checkpointed, not finished and not dead; only `closed` and `failed` mean over. Read the events before concluding from the status.

**STANDING GRANT 2026-08-19: dispatch suitable work to remote sessions at will.** What he delegated is the JUDGEMENT of what is suitable and honesty about overhead. **Remote dispatch is part of every heartbeat sweep: ask "WHAT COULD GO REMOTE?" with the capacity check, in every capacity state**, and log what you considered and rejected ("Looked, nothing qualified" is a valid report).

**Suitable:**

| Send it remotely when | Because |
| --- | --- |
| **Self-contained**: everything it needs is in the repository it checks out | No skills remotely, no local files (`~/.claude/thoughts/`, `~/jbb-feature-dev/`) |
| The output is a **written conclusion**, not a diff | Research, "is this still true", reproduction attempts |
| It is **short** (tens of minutes) | You cannot course-correct, so a bad early decision compounds |
| It is **read-mostly** | The effect gate applies in full |

**Not suitable (hard):**

- Anything you would expect to answer questions about mid-flight (a foreseeable design decision belongs local).
- Anything needing a skill, until plugins land in an org repository (`hq-fy9y`). Establish what a remote session can actually REACH first: observability, deployment tooling and Slack authenticate per session against Jonny's identity, so research may work remotely and incident response not.
- Anything touching a live system, another person, or money. **Being remote is not a permission**; section 1 applies identically.
- Work whose local follow-up would be nearly as large as the task.

**THE FILTER, in order:** (1) `bd ready --exclude-type=epic`; (2) is everything it needs INSIDE THE REPOSITORY? (binding; eliminates most); (3) does it need a skill? stays local; (4) does it touch a live system, person or money? the gate applies; (5) is the bug still real? Check the cited commit is not already an ancestor of master.

**Rules from the first real run (a cold-checkout reproduction that finished in four minutes and found the bug already fixed):**

1. **PIN THE BRANCH TO THE COMMIT THE BUG WAS FILED AGAINST.** A branch from current master can only prove "not reproducible today". For ANY reproduce-a-defect dispatch, name the commit in the spec and create the branch there.
2. **Put "say explicitly what you did not verify" in every remote spec.** It is the difference between a result and a claim.
3. **State the model in every remote dispatch; a default is not a decision** (the first ran `claude-opus-4-6` because the runtime defaults to it). Choose deliberately:

| Model | Use it for |
| --- | --- |
| **Opus 5** | The default. Anything ambiguous, costly if wrong, or needing judgement |
| **Sonnet 5** | Genuinely mechanical work with bounded scope and an unambiguous success test |
| **Fable 5** | Visual and design work |

The inability to intervene raises the bar: lean toward Opus 5 unless the task is genuinely mechanical.

**MANDATORY FOLLOW-UP: the skill chain does not exist remotely, so it runs locally afterwards.** When a remote session finishes, **file and dispatch a local bead** that takes its output through `/simplify`, then `/code-review` (the BUILT-IN, at a named effort level; levels in section 8), then `/jbb-feature-dev:verify-implementation`. **NOT `/submit-pr`**: the remote session already opened the PR; the local pass pushes corrections to the same branch. A remote PR that has not been through the chain does not go on Jonny's list.

**The practical ceiling:** dispatch remotely while you can still say what every live remote session is doing and when you last read it. Three concurrent remote sessions is a starting ceiling, to be raised from a measurement. **ALWAYS give Jonny the session's watch link at dispatch.**

---

## 5. Closing a bead, and closing the session

Close as soon as the work is done. Not closing is the worse failure.

**Every close carries a disposition label and an evidenced reason:**

```bash
bd close <id> --reason "<the evidence: PR number, merge commit, or why it stopped mattering>"
bd label add <id> <done|enough-done|not-wanted|superseded|obsolete>
```

| Label | Means |
| --- | --- |
| `done` | The work completed as specified |
| `enough-done` | Deliberately stopped short |
| `not-wanted` | We decided not to do it |
| `superseded` | Another bead covers it now. Also the dedup disposition |
| `obsolete` | The thing it was about no longer exists |

### The pre-close checklist. Run it before removing any session.

1. **Dump the session's final output to a durable path and record that path on the bead.** Durable means outside `/private/tmp` (swept) and any git-pushed directory. Do it for every session without judging whether it matters; it once rescued a document listing ~20 unresolved tensions that existed nowhere else.
2. **Verify the git worktree is clean, or the work is committed and pushed.**
3. **File any finding not already on a bead**, as a bead.

Then remove the session. **The session lives until the merge**, then the bead closes and the session is removed; it is the only place holding the context to fix a review finding, and being parked costs nothing against the budget.

### Closing a session, in three commands

```bash
python3 ~/.claude/hooks/agent-deck-preclose.py <session-id>   # dump, check, write the receipt
agent-deck session stop   <session-id>
agent-deck session remove <session-id>
```

A PreToolUse hook denies a session removal unless a receipt proves the checklist ran. It never prompts, applies only to the conductor, and says nothing when it does not apply. **It enforces check 1 and, only for `--prune-worktree`, check 2 (a bare `remove` preserves the directory, uncommitted files and branch ref). It does NOT enforce check 3**: nothing mechanical can know a finding exists and is unfiled. Its approval means the final word was saved, not that the checklist was completed.

| What happened | What you get |
| --- | --- |
| Real output captured | A **passing** receipt, exit 0 |
| Nothing ever produced (never started, never completed a turn, or a non-Claude session whose pane is gone) | A **passing** receipt recording nothing to rescue, exit 0 (refusing would make it unremovable, since `--all-errored` is denied) |
| Output should exist but could not be read (empty, or agent-deck unreachable) | A **failed** receipt, exit 1; removal stays blocked |
| The session reference cannot be resolved | **No receipt**, exit 1 |

The guard covers `session remove`, top-level `remove` and `rm`, and `worktree finish` (which deletes the worktree, so it demands a clean one). Denied outright: `session remove --all-errored`, `worktree cleanup --force`, `conductor teardown --remove`. A verb that reads as destructive but is unknown is refused, and `--selftest` warns when the installed agent-deck is newer than the version the table was derived from. It checks nothing about a session in a shared checkout (both conductor sessions): dirt in `~/.claude` belongs to nobody.

**Confirm it is still armed after any `settings.json` change:**

```bash
python3 ~/.claude/hooks/agent-deck-preclose.py --selftest
```

It reads the wired command out of `settings.json` and RUNS it, requiring a deny then an allow; nothing else sees the installed wiring. It is defence in depth, not a security boundary (hooks are best-effort; a determined caller can hand-write a receipt). The threat model is a conductor that forgot, was compacted, or hurried.

### Conductor permissions

Jonny moved exactly three rules from `permissions.ask` to `permissions.allow` in `hq/.claude/settings.json`: `session stop`, `session remove`, `session fork` (`Bash(agent-deck launch *)` was already allowed). Nine rules remain gated, none part of the job, chiefly `Bash(agent-deck conductor setup*)`; also `conductor teardown*`, `conductor migrate-dir*`, `session switch-account *`, `worktree cleanup*`, `mcp attach/detach *`, `session move *`, `session set *`. Backup: `~/.local/share/agent-deck/conductor/hq-settings.json.backup-2026-08-18-pre-contract` (that file is in no git repo).

**Self-protection:** `Write(.../hq/.claude/**)` and `Edit(.../hq/.claude/**)` stay in `permissions.deny`. **The conductor cannot rewrite its own permissions.** Do NOT answer a prompt on another agent's behalf with `tmux send-keys`; the classifier blocks it, correctly. A blocked conductor is a `NEED:` line to Jonny. The classifier also blocks a session-send whose text conveys his consent.

---

## 6. Merging

**The conductor merges without asking when ALL FOUR hold:**

1. The bead is a **follow-up**: it carries a `discovered-from` edge to work Jonny already confirmed or readied.
2. It **closes a gap or fixes a defect** the prior work created or exposed. It adds no new capability.
3. The diff stays **in one repo** and touches no shared contract, public interface, or file another plan depends on.
4. The four-step chain passed, CI is green, and the PR is **not BEHIND base**.

**There is deliberately no line-count bound**: a 400-line mechanical rename is safer than a 20-line shared-contract change, and test 3 catches the dangerous case. **This applies in every repo, including service repos**: the grant changes who presses the button, never what must be true first (in a service repo, a real request driven end to end through the live service; see [conductor-repo-gates.md](conductor-repo-gates.md) section 2).

**Standing grant, unchanged:** switchboard PRs (`github.com/JonnyCBB/switchboard`) merge at will. It removes the ASK, not the GATE: update against base, cold-gate on a fresh clone, check `mergeStateStatus` is not `BEHIND` (see [conductor-repo-gates.md](conductor-repo-gates.md)).

**Everything else comes to Jonny, only when FULLY merge-ready:**

```bash
gh pr view <n> --json state,mergeable,mergeStateStatus,statusCheckRollup
```

Checks green, no conflicts, `mergeStateStatus` not `BEHIND`. `mergeable: MERGEABLE` means only no conflicts; it says nothing about CI or being up to date. A red or behind-base PR is **not ready** and goes back to its session, not onto his list. **Workers never merge their own work.**

---

## 7. Skill routing

Route to the skill that fits. This table ADDS to the mandatory chain in section 8; it never replaces it.

| The bead's work is... | Route to |
| --- | --- |
| Research or investigation of a problem | `/jbb-feature-dev:research-problem` |
| Reviewing a PR or a diff | `/code-review` (built-in), effort by risk |
| Requirements that are not yet settled | `/jbb-feature-dev:elicit-requirements` |
| Several viable approaches needing a deliberate choice | `/jbb-feature-dev:design-approach` |
| Frontend or visual work | `/frontend-design:frontend-design` |
| A document rather than code | `/jiffy-toolkit:review-document` |
| A repository change to implement end-to-end | `/jbb-feature-dev:implement-change` |
| **Changes a CONTEXT file** (`CLAUDE.md`, `AGENTS.md`) | `/jiffy-toolkit:context-and-skills-standards` to review it |
| **Changes a SKILL file** (any `SKILL.md`) | **BOTH** `/jiffy-toolkit:context-and-skills-standards` (principles) **and** `/skill-creator:skill-creator` (workflow and the **evals**); a skill change with no eval run is unverified |
| **Submitting a PR**, every time, every repo | `/jbb-feature-dev:submit-pr`, then `/jiffy-toolkit:sound-like-me` |

**Verify skill names before putting one in a dispatch spec.** A wrong name fails at dispatch, after the worker exists: a skill name without its plugin prefix does not resolve: bare `/context-and-skills-standards`, `/sound-like-me`, `/submit-pr` need their `jiffy-toolkit:` or `jbb-feature-dev:` prefix. These stack on the work-shaped routing: research that ends up editing a `SKILL.md` still owes the skill-file steps. Context-file review is the only routine pass asking whether a conductor rule still pays for itself.

**`/submit-pr` then `/sound-like-me`, every PR.** A PR description is often the only artefact a reviewer has, and Jonny cannot review TypeScript/React by reading it. `/submit-pr` already calls `/sound-like-me` for the description it generates, so the explicit second step matters when a worker writes or edits a PR body BY HAND; state it anyway. **NEVER pass `--auto-merge`** to `/submit-pr`; the no-self-merge rule is absolute for workers.

**The implement-change exception.** Pass a plain-English task or an objective/criteria file, not the removed orchestrator flags. Establish the objective before routing; use `/jbb-feature-dev:elicit-requirements` when user decisions remain unresolved. **It already contains its independent quality chain, so do NOT wrap it in another chain**: built-in `/simplify`, the plugin's specialist `/jbb-feature-dev:code-review`, independent local verification, and authorized PR submission with latest-head CI and explicit clean review. It needs no mandatory research report, formal plan, or separate implementation session. Existing permission and no-self-merge rules still apply. This exception does not change the general review policy below.

---

## 8. The mandatory chain for code-changing work

Any dispatch that changes code and is NOT under `/jbb-feature-dev:implement-change` carries these four, in order, in the worker's deliverable section.

**The implementation stage before step 1 is part of the chain.** Implement minimally: red-green TDD (a small failing test first, the least code that passes it, then refactor), no behavior adjacent to the task, code made readable by naming and structure rather than comments. A comment or doc line survives only if removing it would cause a concrete mistake and the fact exists nowhere else in the code, tests, types, or error messages; uncertainty deletes.

| # | Step | Why here |
| --- | --- | --- |
| 1 | `/simplify` on the diff | First, so reviewers spend attention on substance |
| 2 | `/code-review` (BUILT-IN) at a named effort level | On the SIMPLIFIED code |
| 3 | `/jbb-feature-dev:verify-implementation`, wherever possible | After review, so live verification exercises corrected code |
| 4 | Green CI | In addition to the three, never instead |

**STEP 2 IS THE BUILT-IN `/code-review`, THE EFFORT LEVEL IS NAMED IN THE SPEC, AND THIS TABLE IS THE ONLY COPY: every other mention points here.** The multi-agent `/jbb-feature-dev:code-review` is no longer the default (Jonny, 2026-09-10): its cost sits in the fan-out, spending the same on ten lines as a thousand, at nearly $100.

| Level | Use it when |
| --- | --- |
| `low` | A handful of lines, no production write path, tests included, nothing another team consumes |
| `medium` | **The default.** An ordinary change in one module |
| `high` | Touches a production write path or a safety predicate, or REMOVES or WEAKENS a check |
| `xhigh` | A security boundary, or behaviour nobody can establish locally |
| `max` | Only when Jonny asks by name |

`/jbb-feature-dev:code-review` is not banned: use it only after the built-in has run on a genuinely high-risk change, and say in the report why the built-in was insufficient.

**All four are preconditions for the PR reaching Jonny**: the definition of done. **"Wherever possible" applies only to step 3**, and is a claim to justify: if live verification cannot run, the worker says so and names what was not verified. Silence is not "not possible".

**A service-repo PR additionally needs a real request driven end to end through the live service.** Green CI and 6,000+ unit tests are not sufficient.

### A real browser is a HARD gate on any switchboard UI bead

Two defects shipped past 2,121 green jsdom tests and only a real browser caught them (twelve Playwright failures, zero unit failures): the fake adapter served JSON `null` where the type says `undefined` (builders are written against the type, so no fixture could produce it), and `bg-well` was an undefined Tailwind utility (jsdom computes no cascade). The harness structurally could not express the failure, so more jsdom tests would not have found either. **For any bead that changes switchboard UI, "drive it in a real browser" is step 3 of the chain**; a green `vitest` run is not evidence a restyle works (`hq-su7q`).

**Measure a dependency before quoting its cost to Jonny.** react-markdown was quoted at ~25 packages and is 98 (bundle 421kB -> 591kB). An approval given on a wrong number is not an approval.

---

## 9. Conductor discipline

**Verify, don't infer. Test the claim, run the real command.** An untested belief that `session send` would garble a worker's input led to telling Jonny two workers were unreachable; one cheap send disproved it. An empty board was twice misdiagnosed by running approximations of the command the adapter actually runs.

**Answer what you can answer.** If there is a recommendation the conductor would defend, it decides and reports. Only genuine design choices and reserved-category actions go to Jonny.

**Every recorded decision names what would change it.** A decision reversed 40 minutes later was revisable only because it had a written trigger.

**Liveness: act on delivery, confirm before acting on any claim that a worker stopped, and cap unprompted polling at once per session per 15 minutes.** Every state signal has lied:

| Signal | How it lied |
| --- | --- |
| `session show --json` -> `status: error` | A healthy worker 40 min in reported `error` AND `substate: running`; restarting would have destroyed ~115k tokens of work |
| Stop hook "child completed" | Announced `waiting` while the spinner advanced `1m 14s -> 1m 26s` |
| `session output -q` | Returns the last assistant message even mid-turn, so a fragment reads as finished |

The only signal that has never lied is **advancement**: capture the pane twice, seconds apart, wide (`-S -60`; a narrow capture can catch a bare prompt between renders). If the timer or token count moved, it is ALIVE.

```bash
T=$(agent-deck session show --json <id> | jq -r '.tmux_session')
tmux capture-pane -p -t "$T" -S -60 | grep -E "tokens|esc to interrupt"
# wait a few seconds, repeat. Advanced = alive.
```

Completions are **pull-delivered** (inbox drain, Stop hook). Act on a delivered record the instant it arrives; the 15-minute cap is on going to LOOK when nothing was delivered. A failed delivery is a bug to fix, not a reason to poll.

---

## 10. Success signals, checked at each heartbeat

| Signal | Target | What it catches |
| --- | --- | --- |
| Beads whose work is complete but still open | **0** | The failure Jonny named worst |
| Ready, dispatchable beads idle while capacity is free | **0** | Queueing for permission it already has |
| Times the conductor came to Jonny for something this contract says it should have decided | trending down | Whether the autonomy is used |

Instrumented by `scripts/conductor-signals.sh` (see [conductor-signals.md](conductor-signals.md)); not yet wired into the heartbeat (`hq-3798`).

---

## 11. What this contract amends

Each entry has been edited in place in `hq/CLAUDE.md`.

| Rule, and who set it | What changed |
| --- | --- |
| Effect-based gate, 2026-08-14 | Live WRITES passing the four tests and money under $1,000 per decision are now autonomous. Real-traffic exposure, unproven reverts, reverts needing another person, messaging people, and spend over $1,000 remain ask-every-time |
| `agent-proposed --status deferred` for all agent-filed beads, 2026-08-14 | Still the default; beads passing the auto-ready test go to `open` without asking; the label survives promotion |
| Cap of 3 concurrent workers, 2026-08-16 | **No numeric cap, 2026-09-10**: the cap is machine resource capacity, measured. Ready work queues and auto-fires; Jonny is told, never asked |
| "Closure comes from the merge, which is Jonny's action", 2026-08-14 | The conductor merges qualifying follow-ups in every repo and closes the bead on that merge; everything else comes to him fully merge-ready |
| "Do not close the bead" in the dispatch spec | Unchanged for non-follow-up work; workers never merge their own work |
| Session removal (nothing written before) | Three-check pre-close list, then remove; session lives to merge; under pressure, parked sessions stop oldest-first |
| What `closed` means (nothing written before) | Disposition label plus evidenced reason on every close |
| Minimal red-green TDD stage in section 8, 2026-10-05 (`hq-bmoz6`) | Red-green TDD, no adjacent behavior, comments pruned to the refutation test |
| Shared `../POLICY.md` | Conflicts on "never send messages to running sessions", "when unsure, escalate", "always escalate multiple approaches"; `hq-yn95` reconciles it |
