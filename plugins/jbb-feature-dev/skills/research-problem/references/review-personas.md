# Review Personas for Research Document Review

This file defines the specialized reviewer personas used in Step 7 (Review Phase) of the
research-problem skill. Each persona examines the synthesized research from a distinct angle
to catch gaps, contradictions, and quality issues before the document is written.

Review agents use **Sonnet** model for cost-efficiency — reviewing is evaluative, not generative.

---

## Table of Contents

- [Persona Definitions](#persona-definitions)
- [Reviewer Selection Strategy](#reviewer-selection-strategy)
- [Review Prompt Template](#review-prompt-template)
- [Review Synthesis Format](#review-synthesis-format)
- [Iteration Mechanism](#iteration-mechanism)
- [Auto-Approve Threshold](#auto-approve-threshold)
- [There Is No Skip](#there-is-no-skip)

---

## Persona Definitions

Each persona's **Prompt** is the text dispatched to that reviewer. It is the whole
definition — there is no separate checklist, because a check that lives outside the
dispatched prompt is a check the reviewer never sees.

---

### 1. Gap Analyst

**Focus**: Unanswered questions, missing evidence, unstated assumptions, incomplete coverage.

**Prompt**:

> Systematically evaluate whether the research findings answer every question posed in the
> research plan. For each question, verify that the answer includes specific evidence (file
> paths, URLs, code references, or cited sources). Check also that every success criterion
> in the plan is met, and that every assumption it lists still holds given the findings.
> Flag unanswered questions, unmet success criteria, invalidated assumptions and claims
> without evidence as "Must Address." Flag areas resting on thin evidence — a single source,
> or Tier 3 only — as "Should Consider."

---

### 2. Devil's Advocate

**Focus**: Alternative interpretations, challenged conclusions, logical consistency.

**Prompt**:

> Challenge every major conclusion in this research. For each finding, ask: "What
> alternative explanation could this evidence support?" and "What would need to be true for
> this conclusion to be wrong?" Flag a plausible alternative interpretation the research
> does not address as "Must Address." Flag logical inconsistencies or contradictions between
> sections as "Must Address." Flag conclusions that overreach their evidence as "Should
> Consider." Watch specifically for a confabulation consensus — several agents converging on
> the same incorrect reasoning, which reads as corroboration and is not.

**Anti-sycophancy instruction**: Your job is to find problems. If you find no issues,
explain specifically what you checked and why it passed — do not simply write LGTM without
rationale. Do not defer to the document's authority.

---

### 3. Source Critic

**Focus**: Evidence quality, source reliability, citation accuracy, recency.

**Prompt**:

> Audit the evidence quality in this research. For each major claim verify: (1) it cites a
> specific source, (2) the source tier suits the claim's importance, (3) the claim
> accurately represents what the source says, and (4) the code references — file paths and
> line numbers — are still valid. Flag unsupported key claims as "Must Address." Flag
> outdated information, broken references, and contradictions between sources that the
> research does not acknowledge as "Must Address." Flag reliance on a single or low-tier
> source for an important finding, or on an SEO content farm rather than an authoritative
> reference, as "Should Consider."

---

### 4. Coherence Reviewer

**Focus**: Narrative coherence, internal consistency, readability.

**Prompt**:

> Read this research as if you know nothing about the topic. Evaluate whether the summary
> accurately reflects the detailed findings, whether the narrative flows logically from
> question to evidence to conclusion, whether a reader unfamiliar with the topic could
> understand the answer to the original question, and whether the document is self-contained
> or leans on context it never supplies. Flag contradictions between sections as "Must
> Address." Flag a summary that does not match the details as "Must Address." Flag
> readability and flow issues as "Should Consider."

---

### 5. Scope Guardian

**Focus**: Scope discipline, proportionate claims, honest limitations.

**Prompt**:

> Compare the research scope against the original question and the plan's scope definition.
> Flag any section going substantially beyond what was asked, or deep-diving a tangential
> topic, as "Should Consider." Flag conclusions that recommend when the user asked only for
> documentation as "Must Address." Verify the research does not over-claim by presenting
> uncertain findings as definitive, and that conclusions stay proportional to evidence
> strength.
>
> On open questions, apply the test in both directions — this persona is the one most likely
> to make the problem worse by pushing only one way:
>
> - Flag a **known gap that is not documented** as "Must Address".
> - Flag a **material documented gap that authorized, available evidence could close within
>   budget** as "Must Address" too. A question naming its instrument requires an attempt or
>   verified access, safety, scope, or budget constraint. Preserve consent, inaccessible-source,
>   future-observation, and irreconcilable-source limits; unfinished material evidence at a
>   budget limit keeps the checkpoint incomplete. Use the qualifying reasons in
>   `references/grounding-pass.md` `## What Legitimately Stays Open`; a named tool alone
>   neither proves access nor makes the question invalid.
>
> Demanding that a gap be _listed_ is only correct once it is established the gap cannot be
> _closed_. Open questions are healthy — there is no target of zero — but every one must have
> a reason it survived that is not "nobody tried".

---

### 6. Domain Expert Verifier

**Focus**: Technical accuracy of domain-specific claims, using deep knowledge of the
relevant system (an ML training stack, a data pipeline framework, and so on). Not a generic reviewer: it checks that
the research correctly describes how the domain's technology actually works.

**When to include**: when Step 2's Domain Expert Check identified a matching expert. See
`references/agent-guide.md` for the table and spawning rules.

**Prompt**:

> You are a [DOMAIN] expert verifying research findings for technical accuracy. The research
> was conducted by generalist agents and may contain errors or omissions that only a domain
> specialist would catch.
>
> For each major technical claim in the findings:
>
> 1. Verify it against the actual code/config — check the files referenced, and confirm they
>    do what the finding says they do
> 2. Check whether the research missed related systems, indexes, pipelines or configs in this
>    domain that should have been examined
> 3. Look for in-progress work — open PRs, recent commits — that might invalidate a finding
> 4. Identify domain-specific nuances and edge cases a generalist would not know to check
>
> Categorize feedback as:
>
> - **Must Address**: factual errors, missed systems, incorrect technical descriptions
> - **Should Consider**: additional context, edge cases, related systems worth checking
> - **Minor**: terminology, precision of descriptions

**Anti-sycophancy instruction**: You have deep domain expertise. Do not defer to the
research document's conclusions — verify them independently. If a claim says "field X is
not indexed," check the schema yourself rather than trusting the generalist's reading.

**Key difference from Source Critic**: the Source Critic checks whether claims are
well-sourced. This persona checks whether they are **technically correct**, by independently
examining the same code. Complementary, not redundant.

---

## Complexity Classification

Before selecting reviewers, classify the research by complexity.

### Complexity Signals

| Signal              | Simple | Medium | Complex       |
| ------------------- | ------ | ------ | ------------- |
| Research questions  | 1-2    | 3-5    | 6+            |
| Domains/systems     | Single | 2-3    | Cross-cutting |
| Agent types spawned | 1-2    | 2-3    | 4+            |
| Execution batches   | 1      | 1-2    | 3+            |

Use the highest complexity implied by any signal.

---

## Reviewer Selection Strategy

| Complexity | Reviewers                                                       | Rationale                                    |
| ---------- | --------------------------------------------------------------- | -------------------------------------------- |
| Simple     | Gap Analyst + Devil's Advocate                                  | Completeness and challenge, always           |
| Medium     | + Source Critic                                                 | Evidence quality, as source diversity grows  |
| Complex    | + Coherence Reviewer + Scope Guardian                           | Coherence and scope control matter at scale  |

Complexity chooses the **roster size**. It never reduces the roster to zero: the smallest
legal review is two personas. An earlier version of this skill let Simple skip the phase
outright while this table said Simple got two reviewers, and four other files backed the
skip — so the table was dead text and the phase was, in practice, optional whenever the
orchestrator classified its own work as Simple.

**Domain Expert Verifier** is added to the reviewer set when ALL of the following are true:

1. The Domain Expert Check in Step 2 identified a matching domain expert
2. The complexity is Medium or Complex
3. The domain expert was flagged for verification (not just primary research)

The Domain Expert Verifier is spawned as a regular sub-agent (not model: sonnet — use the
default model since verification requires reading and reasoning about code, not just
evaluating prose). It runs in parallel with the generic reviewer personas.

---

## Review Prompt Template

Use this template to prompt each reviewer agent. Replace bracketed placeholders.

```markdown
You are the [PERSONA_NAME] reviewer for a research document.

[PERSONA_PROMPT]

## Research Context

**Original question**: [research question from Step 2]
**Complexity**: [Simple/Medium/Complex]
**Questions investigated**: [count]

## Research Plan

[Success criteria and assumptions from Step 2, with stable question/criterion IDs and
cumulative gap/evidence dispositions and remaining review budget]

## Synthesized Findings to Review

[Pass the following to each reviewer:

1. The Research Completeness Review output from Step 6 (per-question status, evidence summaries, confidence levels)
2. The per-question evidence summaries from Step 5 synthesis
3. The Assumption Validation results from Step 5
4. Any "Competing Findings" sections where agents returned contradictory information
   This is the minimum structure — the orchestrator may include additional context if relevant.]

---

Retain originating question, criterion, and claim IDs. Assign stable IDs to reviewer gaps
and link them to the evidence and affected assignments; do not replace gaps with count-only
summaries. Review from your perspective. Categorize each piece of feedback as:

- **Must Address**: Blocking issues — missing evidence, logical flaws, contradictions
- **Should Consider**: Improvements that would strengthen the research
- **Minor**: Style, wording, or optional enhancements

If you have no substantive feedback, respond with:
"No concerns from a [PERSONA_NAME] perspective — LGTM."
```

---

## Review Synthesis Format

After all reviewers complete, synthesize feedback:

```markdown
## Review Summary (Iteration N)

[2-3 sentence overview of reviewer consensus.]

### Must Address

- [Issue] — raised by [Persona]

### Should Consider

- [Suggestion] — raised by [Persona]

### Minor

- [Item] — raised by [Persona]

### Points of Disagreement

- [Topic]: [Persona A] says X, [Persona B] says Y
```

If a section has no items, include the heading with "None." underneath.

---

## Iteration Mechanism

1. **Generate synthesis** from all reviewer feedback
2. **Check for "Must Address" items**:
   - If present: orchestrator revises findings and re-runs review on revised sections
   - If absent: proceed to auto-approve check
3. **Iteration bound**: Iterate per the same materiality-filtered round bound defined in
   `references/verification-and-iteration.md`'s `## Maximum Iterations Rule` — do not
   re-state the number here, so the two mechanisms cannot drift independently. If blocking
   items persist at the bound, save an incomplete draft checkpoint with IDs, attempts,
   evidence, and next actions. Bounds stop execution, not pass gates. Missing mandatory
   reviewer delivery also blocks approval after SKILL.md's bounded recovery.
4. **Feedback application**:
   - "Must Address": Orchestrator revises the findings and returns substantive fixes to
     affected independent reviewers, including in non-interactive mode. Keep stable gap IDs
     and originating question/claim IDs with evidence and disposition.
   - Substantive changes to requested answers, scoped facts, conclusions, recommendations,
     or tiers also return to completeness evaluation. Use remaining cumulative run counters;
     revisions and handoffs never reset them. Cosmetic edits and unchanged observations
     do not require re-review.
   - "Should Consider": Added to an advisory notes section in the final document
   - "Minor": Applied if trivial, otherwise noted

---

## Auto-Approve Threshold

The research is auto-approved (no further review iterations needed) only after every
mandatory reviewer delivers and ALL:

1. Zero "Must Address" items remain
2. Zero "Points of Disagreement" exist between reviewers
3. At most 2 "Should Consider" items remain

If auto-approve conditions are met, proceed to Step 8 (grounding pass). Include
remaining "Should Consider" and "Minor" items as advisory notes in the final document.

---

## There Is No Skip

The orchestrator is biased toward approving its own output. These will all feel persuasive
in the moment and none of them is a reason to drop the reviewer pass, at any complexity:

- "The five primary agent reports were internally consistent and well-cited."
- "The marginal value of generic reviewers is low here."
- "Auto mode prefers action over ceremony."
- "The user is in a hurry / token budget is tight."
- "I already ran a self-review and surfaced the issues I would have flagged."

Every one is a self-assessment of work the orchestrator just produced. Independent review is
the antidote to that bias, so dropping the review removes the antidote. Running the
reviewers is cheap — parallel, sonnet. If they find nothing, that cost was small; if they
find something, it paid for itself.

The one thing that changes the roster is the user asking, in their own words, for less
review ("no need for review", "skip Step 7"). Cite their words in the Review Methodology
section of the document. Nothing else does: not a mode flag, not a complexity tier, not your
own reading of how solid the findings look.
