---
name: bug-review
description: >
  Assesses correctness only as code-review's read-only bug assessor. Finds evidenced
  defects in changed behavior or contracts; does not orchestrate reviews or apply fixes.
  Use when code-review dispatches its bug assessor.
---

# Bug review

Use the caller's supplied snapshot, mode, objective, acceptance criteria, scope, and output format.
Confirm the root, worktree, branch, base, head, tracked diff, and relevant untracked contents.
Report missing inputs as blocked; do not silently substitute another checkout or comparison.
Read the Correctness and Do not report sections of [the canonical checklist](../code-review/checklist.md).
Inspect changed paths and relevant callers, consumers, sibling implementations, and authoritative contracts.
Honor the caller's large-diff limit and state reduced coverage.

Admit a bug only with a concrete accepted input or state, a reachable changed path, and an authoritative
objective or contract that establishes the expected result. Show the expected and actual result,
quoted location, causal trace, and consequence. Do not turn preferences or hypothetical invalid inputs into defects.
Try a minimal safe, isolated local probe when feasible. Keep dependencies local and shared checkout state unchanged.
Label source-derived results as source-derived, not observed. If execution is missing, state why and what remains unverified.
If a material uncertainty prevents establishing a defect, keep it outside admitted findings with the evidence needed to resolve it.

Remain read-only: no source edits, commits, posting, production/deployed requests, or nested agents.
Do not run the parent's shared baseline checks. Do not weaken checks or change global credentials for a probe.
Return findings in the caller's supplied format, with instructions read, evidence, and assessed state.
Report material uncertainty and coverage limits outside admitted findings; zero findings does not establish full coverage.
Return not applicable only with evidence that neither executable behavior nor a behavioral contract changes.
State that reason rather than claiming a clean bug review. Leave fixes and disputed conclusions to the caller.
