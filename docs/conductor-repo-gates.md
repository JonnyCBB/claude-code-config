# Repo-specific gates: switchboard and PR readiness

Migrated out of `~/.local/share/agent-deck/conductor/hq/CLAUDE.md` on 2026-08-18
(`jbrooksbartlett-0vju`). These fire on **specific repos and specific actions**, not on every
conductor turn, which is why they are lazy-loaded rather than always-present.

**Read this before merging a `switchboard` PR, and before putting any PR on Jonny's list.**

The merge authority itself is **work contract section 6**. This file is the gate that authority does
not remove.

---

## 1. Switchboard: the standing merge grant, and the gate it does not remove

**Trigger: you are about to merge a PR in `github.com/JonnyCBB/switchboard`, or to dispatch a bead that changes its UI.**

**Standing grant, 2026-08-16.** His words: *"let's just grant the standing rule. You can merge the
switchboard PRs at will. I'm not an expert at web dev or typescript/react. You'll be better than me
so until all of the plans land and I can see the UI I won't have anything to add that you couldn't
decide yourself. Let's make sure we get through the PRs."*

**Scope: `github.com/JonnyCBB/switchboard` ONLY.** It does not extend to
any other repo, to anything touching a live or production system, to spending money, or to
messaging another team.

**The grant removes the ASK, not the GATE.** Before every switchboard merge:

1. **Update the branch against current master** (`gh pr update-branch`). A PR gated before a rebase
   has not been gated against what it will actually merge into.
2. **Cold-gate on a fresh clone** - never a warm tree, and never from `/private/tmp`: `npm ci`,
   `tsc --noEmit`, `eslint .`, `vitest run`. (Reproduced as recorded in `hq/CLAUDE.md`; these four
   were not re-executed during the 2026-08-18 migration, so confirm the invocation against
   `switchboard`'s own `package.json` scripts before pasting them into a spec.)
3. **Check `mergeStateStatus` is not `BEHIND`** and there are no conflicts.
4. **On any file with a known ownership exception** - `scripts/allowlist.js`,
   `src/client/outlets/outlets.dom.test.tsx` - verify the resolution is a **union of operations**.
   Read the file and confirm no other plan's deletion was reverted.

**That gate is not ceremony.** It caught a stale plan-6 baseline, a wrong allowlist resolution and a
`/private/tmp` false red. The suite climbing 420 -> 491 -> 573 -> 589 -> 626 across one day is
integration signal a pre-update gate would have missed entirely.

**Still bring him:** anything that is a design decision rather than a merge; a risk-flagged plan
(Plan 3 writes the live queue, Plan 5 can spend, Plan 14 can permanently delete); a contract change
affecting plans not yet dispatched; or a worker escalation where the right answer is genuinely
unclear. "Merge at will" means not queueing for permission on green code. It is not licence to
decide things he would want to decide.

He re-engages at the end: **w45.20**, the final live-verification pass, is where he sees the UI.

### A real browser is a hard gate on any switchboard UI bead

This one is in **work contract section 8** with its full evidence, and it is named here because it
is the step most easily dropped from a switchboard dispatch spec: for any bead that changes
switchboard UI, "drive it in a real browser" is step 3 of the mandatory chain, not an optional
extra. Two defects shipped past 2,121 green jsdom tests and only Playwright caught them. Filed as
`jbrooksbartlett-su7q`.

---

## 2. PR readiness: the checks, and the two that fooled the conductor

**Trigger: you are about to put a PR on Jonny's list, in any repo.**

The rule is **work contract section 6**: checks green, no conflicts, `mergeStateStatus` not
`BEHIND`. This section is the commands and the two specific ways the conductor got it wrong, both of
which cost Jonny an interruption.

```bash
gh pr view <n> --json state,mergeable,mergeStateStatus,statusCheckRollup \
  --jq '"mergeable=\(.mergeable) state=\(.mergeStateStatus)", (.statusCheckRollup[] | "\(.name // .context)=\(.conclusion // .state)")'
```

**Trap 1: `mergeable: MERGEABLE` means "no merge conflicts" and nothing else.** It says nothing
about CI and nothing about being up to date with base. A PR can read MERGEABLE, have every check
green, and still be behind. `mergeStateStatus` is the field that says so.

Set 2026-08-16 after PR #146, in his words: *"PR 146 needs to be updated to the base branch -
therefore it shouldn't be ready to present to me. Remember this. The PRs need to be fully merge
ready before they come to my attention."* He granted the fix in the same breath: *"Let's make sure
we update against the base branch. If it goes green then you can use admin privileges to merge the
PR."* So if a PR is only behind, update it, let CI re-run and merge on green - do not hand him the
chore.

**Trap 2: mentioning a red build is not the same as withholding the PR.** On PR #144 the conductor
knew the build was red and still listed it among the items awaiting him, flagging the redness as a
footnote. His rule: *"A PR should never be presented to me if the build is broken. This should
always be checked before asking anything of me. If it's broken it needs to go back to the relevant
session for it to be fixed."*

A PR with a red build is not "ready with a caveat", it is **not ready**. It does not appear on his
list at all; it goes back to the session that produced it.

**And a green rollup can still hide a red build.** Check every check, and ask what each one would
look like if it were broken. On one repo a NEUTRAL `tests` check historically meant *no
tests ran at all* (`jbrooksbartlett-6eh`) - the same defect class as a check that cannot fail.
