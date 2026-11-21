---
name: bug-review
description: >
  Assesses correctness as code-review's read-only bug assessor: change-caused bugs against accepted inputs,
  reachable states, and authoritative contracts. Does not orchestrate reviews or apply fixes.
---

# Bug review

Use the caller's objective, acceptance criteria, pinned base, head, diff, and relevant working-tree files.
If required scope or contract evidence is missing, report that limit instead of inventing intent.
Keep the reviewed checkout unchanged. Security belongs to a dedicated security reviewer.

Running the probe in step 5 is required, not optional, for each medium or higher candidate when the repository has a runnable test harness.
The author's description of a rule ("same as the old system", "intended") is a claim to test, not evidence.
When a change decides a request is done from what is on a shared surface, list in your coverage every write the same
actor makes to that surface, including code outside the diff. Judge each by its path, not its text: a write the actor
can follow with another write for the same request must not count as done, and one that does is a finding.

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

Use the caller's output format and severities.
Put the input/state, contract, change-caused path, expected/actual distinction, evidence, and execution limit
in each finding; do not add fields.

Do not admit an uncertain bug merely to preserve it. Return material unresolved concerns separately with
supporting evidence, the missing fact or probe, and what would confirm or refute them. Report coverage separately:
paths/contracts inspected, probes executed, and missing execution or context. Zero admitted findings does not mean
an unqualified clean result when material concerns or required coverage remain unresolved.
