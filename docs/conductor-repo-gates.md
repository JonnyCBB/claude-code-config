# Repo-specific gates: switchboard, service repos, and PR readiness

These fire on specific repos and actions, not every conductor turn. **Read before dispatching into a service repo, before merging a `switchboard` PR, and before putting any PR on Jonny's list.** The merge authority is work contract section 6; this file is the gate that authority does not remove.

---

## 1. Switchboard: the standing merge grant, and the gate it does not remove

**Trigger: you are about to merge a PR in `github.com/JonnyCBB/switchboard`, or dispatch a bead that changes its UI.**

Standing grant (2026-08-16): switchboard PRs merge at will. Scope is that repo ONLY, not any other repo, not anything touching a live system, money or another team. **The grant removes the ASK, not the GATE.** Before every merge:

1. **Update the branch against current master** (`gh pr update-branch`); a PR gated before a rebase was not gated against what it merges into.
2. **Cold-gate on a fresh clone**, never a warm tree, never from `/private/tmp`: `npm ci`, `tsc --noEmit`, `eslint .`, `vitest run`. Confirm the invocation against switchboard's `package.json` scripts before pasting into a spec.
3. **Check `mergeStateStatus` is not `BEHIND`** and there are no conflicts.
4. **On any file with a known ownership exception** (`scripts/allowlist.js`, `src/client/outlets/outlets.dom.test.tsx`) verify the resolution is a union of operations: read the file and confirm no other plan's deletion was reverted.

Still bring him: a design decision rather than a merge; a risk-flagged plan (Plan 3 writes the live queue, Plan 5 can spend, Plan 14 can permanently delete); a contract change affecting undispatched plans; an escalation where the right answer is unclear. He re-engages at `w45.20`, the final live-verification pass.

**A real browser is a hard gate on any switchboard UI bead** (work contract section 8): "drive it in a real browser" is step 3 of the chain, and the step most easily dropped from a spec.

---

## 2. A service PR is not ready until a real end-to-end run has worked

**Trigger: you are writing a dispatch spec for, or reviewing a PR in, a repo whose product is a running service.**

Green CI plus passing unit tests is not sufficient. Before it reaches Jonny, a real request must have been driven end to end through the live service and shown to work, and the regression cases must still pass. A codebase can repeatedly produce checks that pass while being wrong.

**Scope the live run when you dispatch it.** It carries no authority to approve gates or write production config; those stay Jonny's under work contract section 1.

**Name a repo's mandatory reading as a hard instruction.** If a service repo has documents a worker must read before planning (how live verification is done, how its workflow state works), write "Read X and Y before you plan", not "you may find these useful". Workers skip optional reading on a large repo.

---

## 3. PR readiness: the checks, and the two that fooled the conductor

**Trigger: you are about to put a PR on Jonny's list, in any repo.** Rule: work contract section 6 (checks green, no conflicts, `mergeStateStatus` not `BEHIND`).

```bash
gh pr view <n> --json state,mergeable,mergeStateStatus,statusCheckRollup \
  --jq '"mergeable=\(.mergeable) state=\(.mergeStateStatus)", (.statusCheckRollup[] | "\(.name // .context)=\(.conclusion // .state)")'
```

**Trap 1 (work contract section 6): `mergeStateStatus`, not `mergeable`, says whether it is current with base.** If a PR is only behind, update it, let CI re-run and merge on green (Jonny authorised admin merge once green); do not hand him the chore.

**Trap 2: mentioning a red build is not withholding the PR.** A PR with a red build is not "ready with a caveat", it is not ready. It does not appear on his list; it goes back to the session that produced it.

**A green rollup can still hide a red build.** Check every check and ask what each would look like if broken. In one service repo a NEUTRAL `tests` check historically meant no tests ran (`hq-6eh`).
