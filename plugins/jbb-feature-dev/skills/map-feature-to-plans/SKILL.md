---
name: map-feature-to-plans
description: >
  Analyze a research document for a single feature and decide whether it needs more than
  one implementation plan. Every extra plan must cite a named justification; otherwise the
  output is "single plan" (a no-op pass-through). When it splits, produces plan outlines
  with file lists, a dependency graph, execution waves, and a PR strategy. Use after
  research completes and before implement-change. Trigger phrases (1) "feature to plans"
  (2) "split into plans" (3) "split feature for implementation" (4) "how many plans"
  (5) "plan from feature". Outputs to ~/.claude/thoughts/shared/scoping/.
---

# Map Feature to Plans

Decide how many implementation plans a researched feature needs. Each plan outline feeds
`implement-change` directly.

## Step 0: Check the input level

This skill takes one researched feature. If the document describes several independent
features, subsystems or user journeys, or reads like a PRD/epic with no file-level detail,
say so and point to `break-down-initiative`, which splits an initiative into features that
each get their own research.

_Non-interactive: log the observation and proceed if only one feature is present; otherwise
raise an escalation._

## Mode

- `--non-interactive`: auto-approve every decision by
  choosing the safest, best-evidenced, simplest option and log each one. The research-doc path
  is required.
- A file path: read it fully (no limit/offset), plus any requirements and design docs it
  names — the reviewers trace plans to their acceptance criteria — and begin.
- No arguments: ask for the research-doc path.

## Step 1: Decide the split

**One plan is the default, and the burden of proof sits on every additional plan.** Each
extra plan costs a full planning and review pass, a strictly sequential implementation
pass, and an interface decision split across agents that do not share context. Splits
have produced wiring gaps between sibling plans that existed only because the work was
split.

A plan beyond the first is allowed only when it cites one of these, with evidence from the
research doc:

| Justification            | Holds when                                                                                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Context fit**          | The research doc plus the files the plan must read would exceed ~75% of the planning model's context window. Cite the estimate in tokens (bytes ÷ 4 for prose and code), not LOC.     |
| **Risk / landing order** | A risk-class change (auth, payments, cryptography, data migration, destructive operation, public API break) has to land and be verified before its consumers, or be revertable alone. |
| **Checkpoint**           | Later work cannot be designed until an earlier result is observed: a probe of a live system, a spike, a migration's real data shape.                                                  |
| **Separate delivery**    | The parts must ship separately: different repos, different owning teams, or different release timing.                                                                                 |

These are **not** justifications on their own: estimated LOC or file count, the number of
domains or layers crossed, mirroring the design doc's component list, tidiness, and diff
reviewability (a PR decision; see Step 3). A large feature with none of the four is one
plan.

Dependencies decide ordering once a split exists; they are never a reason to split. Two
plans that touch the same file depend on each other and never share a wave. Shared
test infrastructure goes in the earliest plan that needs it, never in a plan of its own;
every other plan that uses it declares that plan as a dependency. Each plan must be independently verifiable (tests, lint and build pass after it lands), so
a slice that cannot be verified alone is merged into its neighbour.

**If no justification holds**, the output is "single plan": write a minimal scoping doc
recording the decision and which justifications were checked, then proceed.

## Step 2: Outline the plans

For each plan: name, scope, files it touches, the justification it cites (every plan after
the first), and its dependencies on other plans. Then group plans into execution waves:
plans with no dependency between them share a wave; dependent plans follow in later waves.

## Step 3: Choose the PR strategy

Plan count does not decide PR count. Default to **one PR per repo**, including multi-plan
work split for context fit or a checkpoint, which lands on one branch. Choose **Stacked
PRs** only when plans must merge separately: a risk / landing-order or separate-delivery
split, or a combined diff that reviewers in this repo would not accept as one PR (check the
repo's recent merged PRs for precedent). Stacking adds rebase work on every change to a
lower branch. Each repo gets its own chain; stacking never spans repos.

## Step 4: Review the candidate

Spawn reviewer sub-agents in parallel using `references/review-personas.md`: the Risk
Isolator alone for a single-plan result, all four personas for any split. Pass each the
requirements doc, research doc, design doc (if any) and the candidate scoping doc.
Self-review never substitutes for spawning them, in either mode, and token cost is not a
reason to skip.

If a reviewer goes idle without delivering: prompt it once via SendMessage, respawn once,
then gather the data directly and record the gap.

Synthesize the feedback, resolve every Must Address item, and re-review. Stop after 3
iterations, or when there are zero Must Address items, zero disagreements and at most 2
Should Consider items. Unresolved Must Address items go to Step 5.

_Non-interactive: one iteration only. Resolve Must Address items by choosing the safest, best-evidenced, simplest option
and record each under `## Autonomous Decisions` → `### Review Synthesis` in the scoping doc
(the orchestrator checks for that heading). Record Should Consider items as advisory
notes._

## Step 5: Confirm with the user

Present the scoping doc and ask whether the plan boundaries, cited justifications,
dependencies, waves and PR strategy are right. Iterate until approved.

_Non-interactive: auto-approve by choosing the safest, best-evidenced, simplest option and log the decision._

## Step 6: Write the scoping doc

Write `~/.claude/thoughts/shared/scoping/YYYY-MM-DD-<kebab-description>.md` from
`references/output-template.md`. `submit-pr` and `rebase-stack` parse
its Branch Chain table, so keep those headings and columns exactly.

Then list the next command for each plan, e.g.
`/implement-change "Plan 2 outline"` (after Plan 1).

If a plan later fails during implementation, re-run this skill with the failure context to
revise the outlines.
