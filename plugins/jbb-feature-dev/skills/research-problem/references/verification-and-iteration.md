# Validation, Synthesis and Completeness (Steps 4-6)

## Step 4 Validation Checklist

Show this before synthesis:

```
## Step 4 Validation Checklist

- [ ] Every Step 2 question ID maps to its assigned agent type, that agent's delivered
      report, and its evidence. Direct-question answers are listed separately.
- [ ] Missing, duplicate or substituted assignments are listed. Equal planned and spawned
      counts do not prove coverage.
- [ ] At least one researcher delivered. A zero-delivery run is never valid, even when the
      counts match.
- [ ] Any missing delivery went through Agent Delivery Resilience; what is still missing is
      recorded.
```

## Synthesis Instructions (Step 5)

- Synthesize only when all agents of the current phase are done.
- Use the most direct source for each claim: live systems for state, code for
  implementation, original records for decisions, public sources for external facts.
  `~/.claude/thoughts/` is supplementary history.
- Connect findings across components, with file paths and line numbers.
- Name the services and components found (for the Operational Context Recommendation).
- Mark each Step 2 assumption CONFIRMED, INVALIDATED or UNCERTAIN. An INVALIDATED assumption
  that changes the scope goes to Step 6 as needing re-research.
- When agents contradict each other, show both positions with their evidence. If one has the
  better source, say so; if neither does, list both under "Competing Findings". Never pick one
  silently.

## Evaluator Prompt (Step 6)

Deliver the plan, the synthesis, the run ledger and the full `## Materiality Filter` section
of `references/grounding-pass.md` inline. The evaluator uses no tools, so a path delivers
nothing. Its tool roster need not be empty.

```
You are the Completeness Evaluator for a research document. Judge whether the synthesized
findings adequately answer every question in the research plan. You are a separate agent from
the one that produced the findings, because models skew positive when grading their own work.

When evidence for a question is ambiguous or incomplete, choose NEEDS MORE INFO over
ADEQUATELY ANSWERED.

## Research Plan
[RESEARCH_PLAN - questions, success criteria, assumptions, with IDs]

## Synthesized Findings
[SYNTHESIZED_FINDINGS]

## Run Ledger
[RUN_LEDGER - IDs, evidence, classifications, prior outcomes, remaining counters]

## Materiality Filter
[MATERIALITY_FILTER - the canonical section, verbatim]

[IF ITERATION 2+:]
## Prior Evaluation
[PRIOR_EVALUATION - your previous output, so you can check whether its gaps were closed]
[/IF]

## Instructions

Judge only the supplied text. Do not call tools. If input is missing, say so. Keep every ID in
your output and give new gaps and flags their own IDs.

### Success Criteria Evaluation
- [ ] [criterion ID]: MET/NOT MET - Evidence: [claim/source IDs, brief summary]

### Assumption Validation
- [assumption]: CONFIRMED/INVALIDATED/UNCERTAIN - [evidence]

### Per-Question Assessment
[question ID]: [question]
   Status: ADEQUATELY ANSWERED / NEEDS MORE INFO
   Evidence: [what was found, or what is missing]
   Confidence: High/Medium/Low
   Needs Verification: YES/NO - YES when a claim about tool behaviour, API responses or
   configuration effects is not empirically verified. Do not verify it yourself; Step 8 does.
   Verification flag ID: [ID]

### Decision
PROCEED - all questions adequately answered and all success criteria met
OR
ITERATE - a NEEDS MORE INFO gap is material under the Materiality Filter, or decisive
evidence is missing or only self-reported. A non-material gap does not justify ITERATE;
record its ID for Step 8.

[If ITERATE:]
Missing information:
1. [gap ID, originating IDs] [gap] - [why it is material]
Additional subagents to spawn:
1. [jbb-feature-dev:agent-type] to answer: [question]
```

## After the verdict

Display it verbatim under `## Research Completeness Review (Iteration N of 4)`; it already
has the format.

- **PROCEED**: mark Step 6 `completed`; go to Step 7.
- **ITERATE**: mark this round's Step 6 `completed`, create tasks for the new agents,
  synthesis and validation, and return to Step 3 with "Additional subagents to spawn".
  Re-synthesize with all findings, old and new, then evaluate again.

The evaluator only returns a verdict; you own all task state.

## Maximum Iterations Rule

At most 4 completeness rounds and, separately, 4 persona-review rounds per run. This is the
one place these bounds are stated. Iterate only while a gap is material. If a material gap or a
blocking review item remains at the bound, the run stops at an incomplete checkpoint
(`SKILL.md`, Run ledger and stopping).
