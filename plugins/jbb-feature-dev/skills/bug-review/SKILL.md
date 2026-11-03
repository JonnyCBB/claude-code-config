---
name: bug-review
description: >
  Checks change-caused bugs against accepted inputs, reachable states, and authoritative contracts.
  Supplies the existing bug-catcher's read-only assessment within code-review, not another worker or a replacement review pipeline.
  Use when the bug-catcher agent runs inside /code-review and needs the bug evidence contract.
---

# Bug review

Use the caller's objective, acceptance criteria, pinned base, head, diff, and relevant working-tree files.
If required scope or contract evidence is missing, report that limit instead of inventing intent.
Keep the reviewed checkout unchanged. Security findings belong to the existing security-reviewer.

## Establish the failure

For each candidate:

1. Name a concrete accepted input or reachable state. Trace validation, callers, transitions, and consumers;
   do not infer reachability from a branch alone. Include boundary values and malformed-but-accepted present data.
2. Read the authoritative objective or contract that establishes the expected outcome, such as an approved criterion,
   schema, API contract, or caller guarantee. Reconcile contradictory comments, messages, tests, and sibling behavior;
   none alone proves intent when stronger evidence conflicts.
3. Trace how a scoped change introduces the failure or makes an existing path wrong. Compare the pinned base;
   a pre-existing pattern alone is not a change-caused bug.
4. State expected versus actual behavior and the consequence. Separate an observed result from a source-supported
   conclusion and from uncertainty. Never describe a predicted result as executed evidence.
5. Run a safe isolated local probe when feasible. Use local fixtures or fakes, bounded execution, and separate
   scratch/build outputs. Do not contact deployed systems, copy secrets, weaken authentication, or run destructive probes.
   Do not edit reviewed files or race other reviewers on shared build/test outputs. If isolation is unavailable,
   return the proposed check to the coordinator rather than executing it in the shared checkout.
6. Record the actual setup, inputs, action, expected result, output, and exit status for an executed probe.
   If execution is missing, say why and identify what remains unverified. Source evidence can support a finding
   without execution, but cannot prove an observed failure.

For example, an accepted zero limit that reaches a new division path needs a contract for zero's meaning,
its caller path, and the expected result. An isolated probe can confirm the exception; an unreachable zero cannot.

## Return findings and limits separately

Use the caller's finding schema and confidence/admission rules. Within code-review, use
[the finding schema](../code-review/references/finding-schema.md) and
[comment format](../code-review/references/comment-format.md).
Put the input/state, contract, change-caused path, expected/actual distinction, evidence, and execution limit
in the finding body; do not add fields or change severity/category values. Leave calibration and false-positive
filtering to the existing pipeline.

Do not admit an uncertain bug merely to preserve it. Return material unresolved concerns separately with
supporting evidence, the missing fact or probe, and what would confirm or refute them. Report coverage separately:
paths/contracts inspected, probes executed, and missing execution or context. Zero admitted findings does not mean
an unqualified clean result when material concerns or required coverage remain unresolved.
