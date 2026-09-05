---
name: orchestrate-feature-dev-fable
description: >
  Conducts a Fable-native end-to-end feature pipeline: the session model
  (Fable) orchestrates while Sonnet workers execute the jbb-feature-dev stage
  skills (research, validation contract, TDD planning, red-green
  implementation, code review, live service verification, commit, PR).
  Outcome-gated rather than step-scripted — hard evidence gates (frozen
  live-testing contract, red-green TDD, independent review, live verification)
  with conductor freedom over routing, decomposition, parallelism, and model
  selection. Use this INSTEAD of /orchestrate-feature-dev when the
  orchestrating session runs on Fable; use the sibling skill for Sonnet/Opus
  sessions. Typical input is a requirements file. Trigger phrases: (1)
  "orchestrate feature with fable" (2) "fable pipeline" (3) "run the fable
  pipeline" (4) "build this feature end-to-end with fable".
argument-hint: '[--requirements <path>] [--prompt "<text>"] [--design <path>] [--skip-research] [--slack-channel <id>] [--ticket <KEY>] [--branch <name>] [--no-worktree] [--restart]'
---

# /orchestrate-feature-dev-fable

One invocation takes a requirements file to a merged-ready PR: research,
validation contract, TDD plans, red-green implementation, independent review,
live service verification, commit, PR. Same destination as
`/orchestrate-feature-dev`, different contract with the orchestrator: that
skill scripts sixteen numbered steps because its orchestrator needed the script.
You do not. This skill fixes the **outcomes and their evidence** (the gates)
and hands you the **route** — because over-prescription measurably degrades
Fable-class output, and because most tokens should bill at the worker rate,
not yours.

The trade you are accepting: freedom over the route, zero freedom over the
gates. Two of them encode the user's acceptance bar and survive every
judgment call you will be tempted to make — a **frozen, live-testing-enforced
validation contract before implementation** and **live verification evidence
for every assertion before shipping**. A green unit-test suite is not
acceptance evidence; the user has said so explicitly.

## Operating model

You are the conductor. Workers — background Agent-tool subagents running the
stage skills or direct prompts — do all reading, writing, coding, testing,
and reviewing. Your tokens (~3× a Sonnet worker's, paid again every turn as
context) are for five things: decompose, decide, judge evidence, unblock
workers, accept or escalate. Anthropic's published Fable-orchestrator
pattern holds ~92–96% of solo-Fable quality at roughly half the cost because
the volume work bills at worker rates — protect that property:

- Worker reports and gate evidence enter your context; artifacts, source
  code, diffs, and test output do not. Read a document's key sections
  yourself only when the decision it informs is yours (contract assertions,
  design choice, disputed finding).
- Never produce a stage artifact, edit source, or run a test suite yourself.
  A "quick fix" by you is an unreviewed, un-TDD'd change — it breaks G4/G5
  and converts a worker failure into a conductor liability.
- Workers can escalate questions to you instead of grinding (the advisor
  channel). Answer decisively and briefly; record the decision.

Read `references/delegation.md` before spawning the first worker: economics,
worker prompt shape, question escalation, model/effort policy, parallelism
rules, and how to judge worker output. Raw wrapper mechanics (canonical
Agent call, milestone logs, timers, recovery ladder) are inherited unchanged
from `../orchestrate-feature-dev/references/stage-execution.md`.

## The gates

Full definitions, default routes, and evidence checks in
`references/gates.md` — read it at run start; it is the spec you are
executing against.

| Gate | Outcome that must be true                                                                                             | Waivable?                                                         |
| ---- | --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| G0   | Run grounded: state file, journal, worktree, inputs archived                                                          | No                                                                |
| G1   | Shared understanding: research + ops/design inputs where they matter, requirements reconciled                         | Depth is yours; skipping research needs the user's explicit words |
| G2   | Validation contract frozen, Live-Testing-Enforcer-reviewed, BEFORE implementation                                     | **Never**                                                         |
| G3   | Reviewed plan(s) covering every `VAL-*` assertion                                                                     | Decomposition is yours                                            |
| G4   | Red-green TDD implementation, failing-test evidence per task, suite green                                             | **Methodology never**; ordering is yours                          |
| G5   | `/simplify` run once, then ONE `/jbb-feature-dev:code-review` pass, every finding addressed or filed, contract amended  | You arbitrate every finding; you cannot skip the review           |
| G6   | Live verification: every assertion executed by an independent validator, live rechecks after fixes, evidence captured | **Never**                                                         |
| G7   | Shipped: report, commit, PR with evidence, CI green, Gosling resolved, cleanup, notification                          | No                                                                |

## Your freedom (use it, record it)

Between gates, route as the feature demands — these are decisions the
sibling skill hard-codes that are yours here:

- **Depth and breadth of G1** — proportional to novelty and blast radius.
- **Stage merging and ordering** — e.g. skip scoping for an obviously
  single-plan feature; start contract generation while ops-context still
  runs (the contract needs requirements, not ops data).
- **Design decisions** — prefer parallel Sonnet architects generating
  competing approaches with you judging, over delegating judgment to a
  pinned fable worker.
- **Worker task sizing, retry-vs-respawn, fix-loop grouping.**
- **Model per worker** — there is no default tier; choose per worker and record
  why (`references/delegation.md § Model and effort policy`). A fable worker is
  almost never right.
- **Parallelism within the constraints** (planning yes; same-worktree
  implementation no — `references/field-notes.md`).

Every exercised freedom gets one line in the state file's `decisions` array:
what you chose, over what, why. A resumed run — or the user reading the
final report — must be able to reconstruct the route. Freedom without a
recorded rationale is indistinguishable from a shortcut.

## What is fixed besides the gates

Empirical facts are not rigidity — they are paid-for knowledge. Read
`references/field-notes.md` before the first worker spawn and trust it over
intuition: the ~30-minute `claude -p` kill, unreliable wake events and the
SendMessage nudge, stage-skill argument quirks (positional paths, the
`--requirements=` equals form), the sequential-implementation constraint,
`dontAsk` vs `acceptEdits`, fallback artifact locations, the newest-file
rule, and why review-phase enforcement exists (non-interactive skills have
empirically skipped mandated reviews; prompt-level enforcement alone fails).

Also fixed: **review sub-agents are never optional.** When a stage skill
mandates spawning reviewers, the worker spawns them — auto mode suppresses
permission prompts, not mandatory steps, and token cost is never a valid
skip justification. Enforcement addendum + artifact check per
`../orchestrate-feature-dev/references/review-phase-enforcement.md`.

## Inputs

Parse `$ARGUMENTS`; unknown flags are a hard error. Flags and mutual
exclusions are identical to the sibling skill (`--prompt` XOR
`--requirements`; `--design` requires `--requirements`; at least one of
`--prompt`/`--requirements`). Typical invocation is a requirements file:

    /orchestrate-feature-dev-fable --requirements ~/path/to/requirements.md

Persist every parsed flag into the state file's `cli_args` verbatim. State
paths, run-id derivation (kebab slug from the requirements basename; for
`--prompt`, defer until research yields a title — never a hash or
timestamp), artifact layout, resumability, and atomic writes follow
`../orchestrate-feature-dev/references/state-file.md` unchanged, with
`pipeline: fable` recorded so runs are distinguishable.

## Run loop

1. **Ground** (G0): state file or resume, branch + worktree (default:
   worktree at `~/.claude/worktrees/<run-id>` — never under `/tmp` or
   `/private/tmp`, see `references/field-notes.md § Harness facts`),
   archive inputs.
2. **Plan the route**: read the requirements yourself (this document is
   short and every downstream decision depends on it — it is worth conductor
   tokens), sketch the route through G1–G7 for THIS feature, and record it
   as the first decision. Revise freely later; record revisions.
3. **Execute toward the next gate**: spawn workers per
   `references/delegation.md`, wait on completion notifications or fallback
   timers (never poll), run the gate's evidence check from
   `references/gates.md`.
4. **Judge**: gate passes → record evidence pointer, advance. Gate fails →
   diagnose from the milestone log and worker report; retry/respawn/re-route
   within your budget; escalate when the failure is systemic (see below).
5. **Ship** (G7) and send the user their notification: PR URL, verification
   summary (passed/failed/blocked counts), and the decisions that shaped the
   route.

Autonomy: after invocation this pipeline runs without a human in the loop.
Never block on a question to the user — decide within your freedom, or
escalate and stop.

## Escalation

Unrecoverable failure means stop and surface to a human — triggers and
procedure in `references/gates.md § Escalation`. Never auto-retry an
escalation. An honest failed run with a clear diagnostic is a better outcome
than a shipped PR with hollow evidence.

## References

- `references/gates.md` — gate definitions, default routes, evidence checks, escalation triggers
- `references/delegation.md` — economics, worker prompts, question escalation, model policy, parallelism, judging output
- `references/field-notes.md` — dated empirical harness + stage-skill facts

Inherited unchanged from `../orchestrate-feature-dev/references/` and
`../orchestrate-feature-dev/scripts/`: `stage-execution.md` (wrapper
mechanics), `state-file.md` (state schema), `agent-prompts.md` (validator,
recheck, TDD fix, reconciliation, report prompts, and how to file what ships
unfixed), `review-phase-enforcement.md`, `report-template.md`, `slack-routing.md`,
`escalation.md`, `aggregate_verify.py`, `validator-schema.json`.
