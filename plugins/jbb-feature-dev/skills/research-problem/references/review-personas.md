# Review Personas for Research Document Review

This file defines the specialized reviewer personas used in Step 7 (Review Phase) of the
research-problem skill. Each persona examines the synthesized research from a distinct angle
to catch gaps, contradictions, and quality issues before the document is written.

Review agents use **Sonnet** model for cost-efficiency — reviewing is evaluative, not generative.

---

## Persona Definitions

### 1. Gap Analyst

**Focus**: Identifies unanswered questions, missing evidence, unstated assumptions, incomplete coverage.

**Checks**:
- Each research question from Step 2 adequately answered with cited evidence?
- Success criteria from Step 2 met?
- Assumptions from Step 2 still valid given findings?
- Any claims made without supporting evidence?
- Any areas where only a single, low-tier source supports a key finding?

**Prompt**:
> Systematically evaluate whether the research findings answer every question posed in the
> research plan. For each question, verify that the answer includes specific evidence (file
> paths, URLs, code references, or cited sources). Flag unanswered questions and claims
> without evidence as "Must Address." Flag areas with thin evidence (single source, Tier 3
> only) as "Should Consider."

---

### 2. Devil's Advocate

**Focus**: Proposes alternative interpretations, challenges conclusions, tests logical consistency.

**Checks**:
- Could the evidence support a different conclusion?
- Are there alternative explanations the research didn't consider?
- Are there contradictions between findings across different sections?
- Are conclusions proportional to the evidence (not over-claiming)?
- Is there a "confabulation consensus" where multiple agents converged on the same incorrect reasoning?

**Prompt**:
> Challenge every major conclusion in this research. For each finding, ask: "What alternative
> explanation could this evidence support?" and "What would need to be true for this conclusion
> to be wrong?" If you identify a plausible alternative interpretation that the research
> doesn't address, flag it as "Must Address." If you find logical inconsistencies between
> sections, flag as "Must Address." If conclusions overreach their evidence, flag as
> "Should Consider."

**Anti-sycophancy instruction**: Your job is to find problems. If you find no issues,
explain specifically what you checked and why it passed — do not simply write LGTM without
rationale. Do not defer to the document's authority.

---

### 3. Source Critic

**Focus**: Evaluates evidence quality, source reliability, citation accuracy, recency.

**Checks**:
- Are key claims backed by Tier 1/2 sources?
- Are code references (file paths, line numbers) still valid and accurate?
- Is information current (not outdated by subsequent changes)?
- Are there contradictions between sources that the research doesn't acknowledge?
- Are any sources SEO content farms rather than authoritative references?

**Prompt**:
> Audit the evidence quality in this research. For each major claim, verify: (1) it cites a
> specific source, (2) the source tier is appropriate for the claim's importance, (3) the
> claim accurately represents what the source says. Flag unsupported key claims as "Must
> Address." Flag reliance on single or low-tier sources for important findings as "Should
> Consider." Flag outdated information or broken references as "Must Address."

---

### 4. Coherence Reviewer

**Focus**: Overall narrative coherence, internal consistency, readability.

**Checks**:
- Do findings across sections tell a consistent story?
- Does the summary accurately reflect the detailed findings?
- Would a reader unfamiliar with the research understand the answer to the original question?
- Are there internal contradictions between sections?
- Is the research self-contained (all necessary context included)?

**Prompt**:
> Read this research as if you know nothing about the topic. Evaluate whether the summary
> accurately reflects the detailed findings, whether the narrative flows logically from
> question to evidence to conclusion, and whether any sections contradict each other. Flag
> contradictions between sections as "Must Address." Flag a summary that doesn't match the
> details as "Must Address." Flag readability and flow issues as "Should Consider."

---

### 5. Scope Guardian

**Focus**: Ensures research stays within defined scope, doesn't over-claim, documents limitations honestly.

**Checks**:
- Does the research answer what was asked (not more, not less)?
- Are conclusions proportional to evidence strength?
- Are open questions honestly documented?
- Does the document avoid recommending when asked only to document?
- Is there scope creep (investigating tangential topics at depth)?

**Prompt**:
> Compare the research scope against the original research question and the scope definition
> from the research plan. Flag any section that goes substantially beyond what was asked as
> "Should Consider." Flag conclusions that recommend when the user asked for documentation as
> "Must Address." Flag missing "Open Questions" for known gaps as "Must Address." Verify the
> research doesn't over-claim by presenting uncertain findings as definitive.

---

## Complexity Classification

Before selecting reviewers, classify the research by complexity.

### Complexity Signals

| Signal | Simple | Medium | Complex |
|--------|--------|--------|---------|
| Research questions | 1-2 | 3-5 | 6+ |
| Domains/systems | Single | 2-3 | Cross-cutting |
| Agent types spawned | 1-2 | 2-3 | 4+ |
| Execution batches | 1 | 1-2 | 3+ |

Use the highest complexity implied by any signal.

---

## Reviewer Selection Strategy

| Complexity | Reviewers | Rationale |
|-----------|-----------|-----------|
| Simple | Gap Analyst + Devil's Advocate | Validate completeness and challenge conclusions for straightforward research |
| Medium | Gap Analyst + Devil's Advocate + Source Critic | Add evidence quality auditing as source diversity increases |
| Complex | All 5 | Full review — coherence and scope control become critical at scale |

---

## Review Prompt Template

Use this template to prompt each reviewer agent. Replace bracketed placeholders.

~~~markdown
You are the [PERSONA_NAME] reviewer for a research document.

[PERSONA_PROMPT]

## Research Context

**Original question**: [research question from Step 2]
**Complexity**: [Simple/Medium/Complex]
**Questions investigated**: [count]

## Research Plan

[Success criteria and assumptions from Step 2]

## Synthesized Findings to Review

[Pass the following to each reviewer:
1. The Research Completeness Review output from Step 6 (per-question status, evidence summaries, confidence levels)
2. The per-question evidence summaries from Step 5 synthesis
3. The Assumption Validation results from Step 5
4. Any "Competing Findings" sections where agents returned contradictory information
This is the minimum structure — the orchestrator may include additional context if relevant.]

---

Review from your perspective. Categorize each piece of feedback as:
- **Must Address**: Blocking issues — missing evidence, logical flaws, contradictions
- **Should Consider**: Improvements that would strengthen the research
- **Minor**: Style, wording, or optional enhancements

If you have no substantive feedback, respond with:
"No concerns from a [PERSONA_NAME] perspective — LGTM."
~~~

---

## Review Synthesis Format

After all reviewers complete, synthesize feedback:

~~~markdown
## Review Summary (Iteration N/2)

[2-3 sentence overview of reviewer consensus.]

### Must Address
- [Issue] — raised by [Persona]

### Should Consider
- [Suggestion] — raised by [Persona]

### Minor
- [Item] — raised by [Persona]

### Points of Disagreement
- [Topic]: [Persona A] says X, [Persona B] says Y
~~~

If a section has no items, include the heading with "None." underneath.

---

## Iteration Mechanism

1. **Generate synthesis** from all reviewer feedback
2. **Check for "Must Address" items**:
   - If present: orchestrator revises findings and re-runs review on revised sections
   - If absent: proceed to auto-approve check
3. **Maximum 2 iterations** — if "Must Address" items persist after 2 iterations, document
   remaining issues in the research document's "Open Questions" section and proceed
4. **Feedback application**:
   - "Must Address": Orchestrator revises the synthesized findings directly
   - "Should Consider": Added to an advisory notes section in the final document
   - "Minor": Applied if trivial, otherwise noted

---

## Auto-Approve Threshold

The research is auto-approved (no further review iterations needed) when ALL:

1. Zero "Must Address" items remain
2. Zero "Points of Disagreement" exist between reviewers
3. At most 2 "Should Consider" items remain

If auto-approve conditions are met, proceed to Step 8 (metadata gathering). Include
remaining "Should Consider" and "Minor" items as advisory notes in the final document.

---

## Skipping the Review Phase

For **Simple** complexity research where the user did not request review, the orchestrator
MAY skip Step 7 entirely. In this case, proceed directly from Step 6 to Step 8.

Non-interactive mode: Always run review for Medium/Complex. Skip for Simple.
Interactive mode: Ask the user if they want to run the review phase for Simple complexity.
