# Grounding Pass for Steps 8-9: Uncertainty Resolution

Reference for the grounding pass and synthesis revision steps. Read this file when
Steps 8-9 instruct you to `Read references/grounding-pass.md`.

## Table of Contents

- [Purpose](#purpose)
- [What Legitimately Stays Open](#what-legitimately-stays-open)
- [Heuristic Table: Detection Signals](#heuristic-table-detection-signals)
- [Classification Rules](#classification-rules)
- [Materiality Filter](#materiality-filter)
- [Grounding Agent Prompt Template](#grounding-agent-prompt-template)
- [Verification Agent](#verification-agent)
- [Grounding Loop: Orchestrator Handoff Protocol](#grounding-loop-orchestrator-handoff-protocol)
- [Grounding Iteration Bound](#grounding-iteration-bound)
- [Synthesis Revision Instructions (Step 9)](#synthesis-revision-instructions-step-9)

## Purpose

Resolve material items answerable through authorized, available evidence within budget
before the document is written. Several safe reads can form one attempt. Inventory stable
IDs for requested answers, success criteria, scoped claims (including unmarked claims),
evaluator flags, reviewer gaps, candidates, and follow-ons. Heuristics add items; they never
limit eligibility. Preserve IDs and link follow-ons to originating items.

The pass has two inputs of different shapes, and both must be worked — missing the second
is the common failure:

- **Claims** — assertions in the synthesis, including unmarked claims, requested answers,
  and scoped factual descriptions; heuristics and Step 6 flags add detection signals.
- **Questions** — the `## Candidate Open Questions` list drafted in Step 5. These assert
  nothing, so they match no heuristic; they are work items regardless. A candidate question
  may only reach the final document as an Open Question once this pass classifies it
  UNRESOLVABLE or SKIP.

## What Legitimately Stays Open

Open Questions are a feature of an honest research document, not a failure, and there is no
target of zero. The test is about the _reason_ a question is open, not the count.

**A question may stay open when more research alone cannot answer it:**

- **It needs a human decision.** "Should we widen the per-user path beyond `MCP_GATEWAY`?" is
  a product choice; no amount of searching settles it.
- **It needs someone's knowledge or consent.** Check authorized directories, APIs, or
  records before declaring knowledge human-only. For example, role membership may be
  queryable; permission to widen a role remains a consent or policy decision.
- **The instrument exists but is unreachable from this session.** Record access failures
  and safe availability checks. One failed route does not prove all sources unavailable;
  apply the Per-Attempt Bounding Rules before classifying the evidence as inaccessible.
- **It can only be observed later.** "Does the 45-day archiver actually sweep this config?"
  cannot be answered before day 45.
- **The sources of truth genuinely disagree** and nothing available adjudicates between them.
- **It is immaterial.** Per the Materiality Filter, incidental detail that changes no
  substantive answer or scoped finding is correctly left alone; state the scope reason.

**Named instruments require attempts or verified access, safety, scope, or budget constraints.**
Phrases like "one refresh call settles it", "a direct `ListConfig` probe would confirm this",
"this rests on a Slack index rather than the API", or "use the pricing calculator" identify
work to classify, not automatic authority to execute it. Inaccessibility can justify blocked
classification; budget-limited material evidence keeps the checkpoint incomplete.

The failure mode this guards against is specific and has recurred: a run ends, the reader
scans the Open Questions, asks one of them back, and a single command answers it. Every such
round-trip means the research stopped one call short and handed the remainder to the person
who commissioned it. Judge each Open Question by asking — _if the reader asked me this right
now, could authorized evidence answer it within budget, or is a qualifying limit verified?_
Record the limit rather than treating the presence or absence of one tool as decisive.

## Heuristic Table: Detection Signals

| #   | Detection Signal                                                                                                                                                                                                          | Resolution Action                                                          | Cost                  | False Positive Risk                                              | Handling on Failure                                                                       |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 1 | Tool name matching `mcp__*` + "not tested" / "not verified" / "unconfirmed" | Inspect the action, then use an authorized read with relevant input | Read cost depends on tool | Auth or input may be unavailable | Classify failure under Per-Attempt Bounding Rules; record action and response |
| 2 | "should be confirmed in [file]" / "not verified against [source file]" / "not checked in [file]" | Read or search the source via Grep, Glob, or Read | Bounded reads | File may move | Classify failure; check a corrected path or independent read-only route within the recovery allowance |
| 3 | Shell command + "not run" / "should be verified" / "recommended" | Inspect command, arguments, method, and side effects before an authorized read | Command-dependent | Missing binary, wrong repo, or mutation | Report required mutations separately; record failures and limits |
| 4 | URL + "not fetched" / "not verified" / "assumed from" | Fetch authorized content via WebFetch | Bounded fetch | Access denial or timeout | Classify failure; a failed URL does not prove all sources inaccessible |
| 5 | "release status unconfirmed" / "availability not verified" / "version unknown" | Query authoritative registry or release records | Bounded reads | Registry/query coverage may be incomplete | Empty results prove absence only within verified source/query coverage; record missing checks |
| 6 | Text names its instrument: "one X call settles it" / "a direct [probe] would confirm" / "rests on [weaker source], not [authoritative source]" / "use the [tool]" / "could be confirmed by" | Inspect authority, availability, safety, scope, and budget before reading | Instrument-dependent | Access or safety constraint | Attempt safely or record a verified constraint; unfinished material evidence blocks completion |

### Scope Notes

- These heuristics catch explicit uncertainty markers. Independently inventory unmarked
  claims, requested answers, success criteria, flags, reviewer gaps, candidates, and follow-ons.
  Absence of a heuristic match is never proof that an item is grounded.
- **Heuristic 6 applies to questions as well as claims**, and is the highest-yield signal in
  this table. An audit of shipped research documents found roughly one to two answerable Open
  Questions per document, and in most cases the text named its own instrument — the research
  had identified how to settle the question and wrote that down instead of doing it. Treat any
  such phrasing as an instruction addressed to you.
- Each heuristic has a **failure handling path** — on error, the resolution attempt is
  documented rather than silently dropped.
- The heuristics are **detection signals, not sufficient conditions**. The grounding agent
  applies judgment about whether a resolution attempt is worthwhile based on context (e.g.,
  "not tested" in a section about decommissioned tools should not trigger a test).

## Classification Rules

Classify **every detected uncertainty and every candidate Open Question** as:

| Classification   | Criteria                                                                                                                                       | Action                                           |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| **RESOLVABLE** | Authorized, available evidence can answer within budget; no heuristic match or single-call restriction applies | Attempt safe resolution |
| **UNRESOLVABLE** | A verified qualifying reason from `## What Legitimately Stays Open` prevents more research alone answering it | Document reason, evidence, and closure condition |
| **SKIP** | A stated scope, safety, or verified budget limit prevents pursuit; uncertainty alone is insufficient | Record the concrete reason and needed action; budget-limited material evidence stays incomplete |

Classification is mandatory and total: an item that reaches the final document as an Open
Question without a classification is a process defect, not a disclosure. UNRESOLVABLE is a
legitimate and expected outcome — it is the _unclassified_ item that signals the pass was
skipped.

## Materiality Filter

An item is **material** if resolving it could have a substantive effect on requested answers,
success criteria, scoped factual descriptions, conclusions, recommendations, or tiers.
Resolve material items answerable through authorized, available evidence within budget.
Incidental detail and edits that leave meaning, evidence, and recommendations unchanged do
not reopen checks.

Example: "File X's line count wasn't independently verified" is material if that count
feeds a downstream planning decision (e.g., a per-file task estimate) — pursue it. The
same claim is not material if the count is incidental color with no bearing on any
conclusion — skip it.

This is the single canonical definition of materiality; other steps and agents in this
skill that apply a materiality filter (including the Verification Agent below) point back
to this section rather than restating it.

## Grounding Agent Prompt Template

Use this template when spawning the Grounding Agent in Step 8. The template applies the
Materiality Filter defined above and the Per-Attempt Bounding Rules defined below. Replace
bracketed placeholders with actual values. On the first grounding iteration, omit the
"Prior Verification Feedback" block entirely; from the second iteration onward, include it.

```markdown
You are the Grounding Agent for a research document. Your job is to resolve every
material item AND every candidate Open Question answerable through authorized, available
evidence within budget. Several safe reads can form one attempt. Assess every supplied ID,
not only items matching a heuristic.

## Synthesized Findings to Ground

[SYNTHESIZED_FINDINGS]

## Step 6 Evaluator Assessment

[STEP_6_FLAGS — the per-question "Needs Verification: YES/NO" assessment from Step 6]

## Candidate Open Questions

[CANDIDATE_OPEN_QUESTIONS — the `## Candidate Open Questions` list from the Step 5 synthesis
file, plus any gap the Step 7 reviewers demanded be documented. Every entry is a work item,
not a disclosure. Classify each one and resolve the RESOLVABLE ones. An entry survives into
the final document only if you classify it UNRESOLVABLE or SKIP, and you must state which.
If this block is empty, say so in your report rather than assuming there were none.]

[IF ITERATION 2+:]

## Prior Verification Feedback (Iteration N-1)

[PRIOR_VERIFICATION_FEEDBACK — the Verification Agent's "Remaining material gaps" list
from the previous iteration. Treat this as your primary work list: focus resolution
effort on these gaps rather than re-scanning the full synthesis from scratch. You may
still pursue a newly-surfaced claim if resolving a listed gap reveals one that passes
the Materiality Filter.]
[/IF]

## Cumulative Ledgers

[CUMULATIVE_LEDGERS — full stable-ID inventory, originating links, evidence, errors,
classifications, superseding corrections, verification outcomes, and remaining run budget]

## Canonical Policies

[CLASSIFICATION_RULES — expand the complete canonical section verbatim]
[LEGITIMATE_OPEN_REASONS — expand the complete What Legitimately Stays Open section verbatim]
[MATERIALITY_FILTER — expand the complete canonical Materiality Filter section verbatim]

## Instructions

Collect evidence through authorized reads. Do not send messages, mutate records, connect
servers, or change settings. Artifact writes require explicit authority. Inspect mixed-action
tools and commands; report required mutations separately. These prompt rules do not enforce
technical permissions.

1. **Inventory** stable IDs for requested answers, success criteria, unmarked claims,
   evaluator flags, reviewer gaps, candidates, and follow-ons. Scan findings for heuristic
   signals as additions, not eligibility conditions. On iteration 2+, prioritize prior gaps
   without dropping unresolved IDs or earlier evidence.

2. **Classify** each detected uncertainty and each candidate Open Question as RESOLVABLE,
   UNRESOLVABLE, or SKIP using the classification rules. For anything you classify
   UNRESOLVABLE, name which of the qualifying reasons in `## What Legitimately Stays Open`
   applies — "needs a human decision", "unreachable from this session", and so on. If you
   cannot name one, it is not UNRESOLVABLE; attempt it.

3. **Resolve** each RESOLVABLE item by executing the resolution action:
   - For MCP tools: inspect available actions, then use an authorized relevant read within scope and budget; report required mutations separately
   - For file references: read or grep the file
   - For shell commands: inspect commands and arguments, then execute only authorized reads via Bash
   - For URLs: fetch via WebFetch
   - For version/availability: query the appropriate registry
   - For a question naming its own instrument (Heuristic 6): run that instrument

   If resolving one item surfaces a follow-on question that passes the Materiality Filter,
   pursue it within your remaining attempt budget — a question created inside this gate must not
   escape through it. If the budget will not cover it, do **not** overrun the cap and do not
   write it into Open Questions: list it under "Follow-ons for the next iteration" in your
   report. The Verification Agent reads that list and will ITERATE, which is what the loop is
   for. Handing work to the next round is in bounds; silently dropping it or busting the cap
   are not.

4. **Report** your results in this format for each item:

   ### Item [stable ID]
   - **Kind**: Requested answer / Success criterion / Claim / Evaluator flag / Reviewer gap /
     Candidate Open Question / Follow-on
   - **Originating IDs**: [linked question, criterion, claim, flag, or gap IDs]
   - **Location**: [section and line reference in findings, or "Candidate Open Questions"]
   - **Original text**: "[the uncertain claim, or the question as written]"
   - **Detection signal**: Heuristic [N] or "Step 6 flag" or "Candidate Open Question" or
     "Prior verification gap" or "Surfaced while resolving item N"
   - **Classification**: RESOLVABLE / UNRESOLVABLE / SKIP
   - **If UNRESOLVABLE, qualifying reason**: [which reason from `## What Legitimately Stays Open`]
   - **Action taken**: [what you did, or why you didn't act]
   - **Result**: [empirical finding, or classified error encountered]
   - **Execution evidence**: [exact action and arguments/query; source identity/version;
     response excerpt; available call ID, or explicitly unavailable; evidential limits]
   - **Coverage/limits**: [query scope, coverage supporting absence claims, and missing checks]
   - **History**: [prior evidence, errors, classifications, superseding correction, verification outcome]
   - **Updated text**: "[revised claim, or the answer to the question]" or "Remains open — [reason]"

5. **Self-check** your execution fidelity before finishing. Produce a table with columns
   Item ID | Kind | Originating IDs | Classification | Action Taken (Y/N) | Qualifying reason
   (if UNRESOLVABLE) | Result. Every RESOLVABLE row must show "Y" with a corresponding result, and
   every UNRESOLVABLE row must name a qualifying reason. A RESOLVABLE row showing "N", or an
   UNRESOLVABLE row with no qualifying reason, is a reporting defect — flag it explicitly
   rather than silently submitting the table as-is. Also state the count of candidate Open
   Questions you received and the count you classified; they must match. This table is the
   primary evidence a separate Verification Agent will check next, so completeness and honesty
   here matter more than in a report nobody double-checks. Match IDs to evidence and
   classifications; list missing, duplicate, or substituted IDs, not just totals.

## Heuristic Table

[HEURISTIC_TABLE_AND_SCOPE_NOTES — complete canonical detection table and scope notes verbatim]

## Per-Attempt Bounding Rules

- **Maximum 25 resolution attempts within this invocation.** One attempt per item you try to
  resolve, plus one per follow-on you pursue. Do **not** count tool calls, batches or reads
  made while reasoning — an item needing four greps to settle is one attempt. The unit is
  defined this tightly because an earlier version bounded "rounds" and left the unit open:
  two agents doing identical work self-reported 6 and 11 against the same cap, which makes a
  cap unenforceable and its overruns undiagnosable. If you are unsure whether something
  counted, say so rather than taking the flattering reading.

  The budget is deliberately generous — real passes have needed roughly 6-13 attempts, so 25
  is about double the high end, and the Materiality Filter rather than this number is what
  should stop you. Approaching it signals unusually many material gaps: hand the remainder to
  the next iteration under "Follow-ons for the next iteration" rather than overrunning or
  dropping them. This is separate from the orchestrator's Grounding Iteration Bound, which
  you are not responsible for.

- Use supported tool timeouts. Time limits execution, not answerability; checkpoint
  unfinished material items as incomplete.
- Classify errors as access, invalid query/path, not found, timeout/transient, or uncertain
  outcome. Allow one corrected query or independent read-only source for idempotent reads
  per item within budget. Never repeat unchanged failures or retry mutations or uncertain
  outcomes. Several safe reads may form one attempt; recovery does not reset it.
- One failed route does not prove all sources unavailable. Check evidence availability safely.
  SKIP requires a scope, safety, or verified budget reason, including the concrete cost when
  cost blocks pursuit. Uncertainty alone is insufficient.
- Empty results prove absence only within verified source/query coverage. Record the query,
  scope, result, and missing checks. Preserve consent, inaccessible-source,
  future-observation, and irreconcilable-source limits.

## Principles

- Document empirical findings by default; permit evidence-backed evaluation when explicitly
  requested within scope. Never invent a recommendation.
- If unsure whether an item is resolvable, check authorized evidence availability safely.
  Do not speculate or use uncertainty as a SKIP reason. State what is needed and the verified
  scope, safety, or budget constraint; material budget limits keep the run incomplete.
- Every resolution attempt must be documented, whether it succeeds or fails.
```

## Verification Agent

The Grounding Agent's self-check table is a first-line signal, but it is the same agent
grading itself. The Verification Agent is what actually gates whether Steps 8-9 are done.

### Verification Agent Prompt Template

Pass this prompt to the Verification Agent (model: haiku; told not to use tools). Replace bracketed
placeholders with actual values. Inline the complete canonical Classification Rules,
Materiality Filter, What Legitimately Stays Open, Heuristic Table and Scope Notes, and
Per-Attempt Bounding Rules in both delivered prompts. Expand blocks verbatim, not as paths
or paraphrases. Include cumulative ID/evidence and budget ledgers, not only this round's gaps.
Verify complete delivery before dispatch. The agent's tool roster need not be empty.

```markdown
You are the Grounding Verification Agent for a research document. Your job is to judge
whether the Grounding Agent's resolution work is genuinely complete. You do not call
tools, read files, or re-run any resolution attempt yourself — you are checking a report,
not redoing the work it describes. Assess only complete supplied evidence. Reject missing
input and report evidence limits. This verdict is not independent empirical reproduction.

You are a separate agent from the one that produced the grounding report. This
separation exists for the same reason Step 6 uses a dedicated evaluator: models reliably
skew positive when grading their own work — a standalone check catches gaps that
self-evaluation misses.

## Disposition

Default to ITERATE when the grounding report is ambiguous or looks incomplete. Triggering
one more grounding round is cheap relative to letting an unresolved material claim reach
the final document.

## Synthesized Findings

[SYNTHESIZED_FINDINGS — same input the Grounding Agent received]

## Step 6 Evaluator Assessment

[STEP_6_FLAGS — same input the Grounding Agent received]

## Candidate Open Questions

[CANDIDATE_OPEN_QUESTIONS — same input the Grounding Agent received. Every entry here must
appear in the grounding report with a classification. Any entry the report does not mention
is a coverage gap.]

## Grounding Agent Report (this iteration)

[GROUNDING_AGENT_REPORT — the full per-item results and self-check table for this iteration]

## Cumulative Ledgers

[CUMULATIVE_LEDGERS — full stable-ID inventory, evidence, errors, classifications,
superseding corrections, verification outcomes, and remaining run-budget counters]

[IF ITERATION 2+:]

## Prior Verification Feedback (Iteration N-1)

[PRIOR_VERIFICATION_FEEDBACK — your own output from the previous iteration, so you can
confirm whether the gaps you flagged before were actually closed this time]
[/IF]

## Instructions

Check the grounding report against the synthesized findings, Step 6 flags, and Candidate
Open Questions for four failure modes:

1. **Unactioned resolutions**: any row in the self-check table marked RESOLVABLE with
   "N" in Action Taken, or an "Updated text" that still reads as uncertain despite being
   marked resolved.
2. **Coverage gaps**: any claim matching a Heuristic Table signal, any Step 6 `Needs
Verification: YES` flag, or any Candidate Open Question that the grounding report never
   mentions at all, including unmarked claims, requested answers, criteria, reviewer gaps,
   and follow-ons. Match candidate IDs to classifications and evidence; list missing,
   duplicate, or substituted IDs. Counts alone do not establish coverage.
3. **Miscategorization**: any claim or question marked SKIP or UNRESOLVABLE that, on
   inspection, is answerable through authorized, available evidence within budget per the
   Classification Rules — or any item the report treats as worth pursuing that the
   Materiality Filter (below) would not actually classify as material.
4. **Unjustified Open Questions**: any item classified UNRESOLVABLE without naming a
   qualifying reason from `## What Legitimately Stays Open`, or naming one that does not fit.
   For a question naming its instrument, require an attempt or verified access, safety,
   scope, or budget constraint. A named instrument alone neither proves access nor forbids
   blocked classification. Budget-limited material evidence cannot support PROCEED.

## Materiality Filter

[MATERIALITY_FILTER — substitute this file's canonical `## Materiality Filter` section
verbatim here, not a paraphrase, so the Verification Agent judges against the exact same
definition the Grounding Agent and Step 6 use rather than a drifted restatement]

## Classification Rules

[CLASSIFICATION_RULES — complete canonical section verbatim]

## What Legitimately Stays Open

[LEGITIMATE_OPEN_REASONS — complete canonical section verbatim]

## Detection Signals

[HEURISTIC_TABLE_AND_SCOPE_NOTES — complete canonical detection table and scope notes verbatim]

## Per-Attempt Bounding Rules

[PER_ATTEMPT_BOUNDING_RULES — complete canonical section from the Grounding Agent template verbatim]

Produce your evaluation using EXACTLY this format:

### Coverage Check

- Step 6 `Needs Verification: YES` flags all addressed: [YES/NO — list any missed]
- Heuristic-matched claims all addressed: [YES/NO — list any missed]
- Candidate Open Questions: [supplied IDs / classified IDs — list missing, duplicate, or substituted IDs]
- Requested answers, criteria, unmarked claims, reviewer gaps, follow-ons: [IDs and coverage gaps]

### Resolution Quality Check

For each RESOLVABLE row in the grounding report's self-check table:
Claim or question: [text]
Supported by supplied evidence: [YES/NO — cite the response/item connection; list missing
or self-reported-only evidence, action/source/response/call-ID limits]

### Open Question Justification Check

For each item classified UNRESOLVABLE or SKIP:
Item: [text]
Qualifying reason given: [the reason, or NONE]
Reason holds: [YES/NO — if NO, say what instrument the text itself names]

### Decision

PROCEED — supplied evidence supports every material resolution or qualifying
UNRESOLVABLE/SKIP reason; no decisive evidence is missing and no material evidence remains
budget-limited
OR
ITERATE — material gaps, missing decisive evidence, unsupported self-reports, or unfinished
material evidence remain. Apply the supplied Materiality Filter; classify non-material limits
without reopening checks.

[If ITERATE:]
Remaining material gaps:

1. [specific claim or question] — [why it's material] — [what the next round should do
   differently, e.g. "not attempted," "attempted but result contradicts the updated text,"
   "never detected despite matching Heuristic 2," "classified UNRESOLVABLE but its own text
   names a `gh api` call that would settle it"]
```

### Spawning Instructions

- **Model**: haiku. This check is narrower and more mechanical than Step 6's
  completeness judgment — it's verifying a structured report against explicit flags and
  a fixed materiality test, not exercising open-ended domain judgment about whether
  research questions are answered. A faster, cheaper model fits the task; escalate to
  sonnet if verification quality issues show up in practice.
- **Tools**: none — the Verification Agent receives only text (the same inputs the
  orchestrator already has plus the Grounding Agent's report) and never calls tools,
  reads files, or re-runs resolution attempts. Giving it tools would just make it a
  second grounding pass, not a check on the first one.
- **Input**: full findings, flags, candidates, cumulative ID/evidence and budget ledgers,
  current grounding report, expanded canonical policies, and prior verification feedback
  (iteration 2+ only). Paths and summaries do not replace complete supplied input.

## Grounding Loop: Orchestrator Handoff Protocol

Steps 8-9 form a bounded loop between the Grounding Agent and the Verification Agent,
mirroring Step 6's separate-evaluator principle. This section covers the orchestrator's
responsibilities across that loop; the two prompt templates above cover what each agent
does within a single iteration.

1. **Spawn**: Deliver complete findings, flags, candidates, reviewer gaps, cumulative
   ID/evidence and budget ledgers, and expanded canonical policies to the Grounding Agent.
   Include prior verification feedback from iteration 2 onward.
2. **Spawn**: Deliver the same full inputs plus the current grounding report to the
   Verification Agent. Verify complete input delivery.
3. **Display**: Output the Verification Agent's verdict verbatim (no editing, no
   summarizing).
4. **Parse**: Read the Decision field — it starts with either "PROCEED" or "ITERATE".
5. **If PROCEED**: Proceed to Step 9 using the cumulative evidence ledger and current verdict.
6. **If ITERATE** and the Grounding Iteration Bound (below) has not been reached:
   increment the iteration counter and return to step 1, passing the Verification
   Agent's "Remaining material gaps" list as the next round's Prior Verification
   Feedback.
7. **If ITERATE** and a required run counter is exhausted: stop execution. Save an
   incomplete draft checkpoint with remaining IDs, attempts, evidence, and next actions.
   Bounds never pass gates or convert unfinished material evidence into completion.
8. **Delivery resilience**: Apply `SKILL.md`'s Agent Delivery Resilience ladder to both
   agents independently — it is the canonical statement, including which address form
   `SendMessage` accepts. Do not restate it here.

   Missing grounding or verification delivery prevents Step 8 completion and Step 9.
   Record failure, attempts, missing IDs, and next actions in an incomplete checkpoint.
   Earlier reports and self-checks never replace the current independent verdict.
9. **Task ownership**: All `TaskUpdate`/`TaskCreate` mutations are the orchestrator's
   responsibility. Neither agent modifies task state.
10. **Never substitute self-verification.** The orchestrator must never judge the
    Grounding Agent's completeness itself in place of spawning the Verification Agent —
    doing so defeats the reason this loop exists (see the Verification Agent's
    Disposition section above).

## Grounding Iteration Bound

- **Maximum 5 grounding iterations** (one iteration = one Grounding Agent spawn plus one
  Verification Agent spawn). A starting default, not a measured figure — no telemetry exists
  yet for how many iterations a real pass needs. It is deliberately above Step 6's max of 4
  because grounding gaps are narrower and cheaper to close per round.
- Distinct from the Per-Attempt Bounding Rules, which cap attempts *inside* one Grounding
  Agent invocation. One spawn's workload versus how many times the pair is re-spawned. Each
  number is stated once, in its own section; an earlier revision restated both here and one
  went stale, contradicting the bullet above it.
- This is the canonical location for this bound. `SKILL.md` points here.

## Synthesis Revision Instructions (Step 9)

After the grounding loop reaches independent PROCEED, the orchestrator uses cumulative
results to revise the synthesis. An exhausted bound with material gaps stops at an incomplete
checkpoint, not Step 9.

### When to Revise

Revise the synthesized findings when a grounding result changes the factual basis of a
section. Common triggers:

- A tool marked "NOT TESTED" turns out to **work** → update the finding from contingent
  to confirmed; if the tool's availability affected a recommendation tier, update the tier
- A tool marked "NOT TESTED" turns out to be **broken or return unexpected data** →
  update the finding to reflect actual behavior; if dependent recommendations assumed the
  tool worked, re-evaluate or downgrade them
- A code-verifiable claim turns out to be **wrong** (file doesn't contain what was
  described) → correct the claim and check whether downstream conclusions built on it
  still hold
- A URL or registry check **confirms or denies** an availability claim → update the
  finding accordingly

### How to Revise

1. Read the cumulative ledger of all grounding results and the current independent verdict
2. For each result with `Classification: RESOLVABLE` and a non-error `Result`:
   - Locate the section(s) in the synthesized findings that reference the resolved
     uncertainty
   - Replace the uncertain claim with the grounded finding
   - Check if the change affects recommendations, conclusions, or tier classifications
     in that section
   - If yes, update those dependent statements
3. For each failed resolution attempt or blocked item whose supported UNRESOLVABLE/SKIP
   classification permits completion under the current independent PROCEED verdict:
   - Replace the uncertainty marker with the grounding attempt annotation:
     "Attempted: [action]. Result: [error]. Remains unresolved." or
     "Skipped: [verified qualifying reason]".
     Bound exhaustion never qualifies; material gaps retain an incomplete checkpoint.
4. Do NOT re-open Step 2's research questions or spawn new research agents. Only update
   sections that reference grounded findings.

   **But**: if applying a result reveals a material follow-on answerable through authorized,
   available evidence within remaining budget, assign a linked stable ID and return it to
   grounding. Several safe reads may form one attempt. Do not silently expand scope.
   A question created inside a verification
   gate must not escape through it. The canonical example: grounding retires a metric-based
   claim ("this gauge cannot support a growth rate"), which creates the question "so what is
   the real count?" — that question is one probe away and belongs in the loop, not in the
   document's Open Questions.

### Bounding

- Revise affected sections and dependent requested answers/recommendations. Supply the
  cumulative ledgers to renewed checks; final-round gap reports are not cumulative.
- **No fixed time bound** for revision itself; user limits and required exhausted run
  counters still stop execution. Handle stalls with `SKILL.md`'s Agent Delivery Resilience.
- Do not re-review unchanged observations or edits that leave meaning, evidence, and
  recommendations unchanged. Substantively changed requested answers, scoped factual
  descriptions, conclusions, recommendations, or tiers require completeness evaluation and
  affected persona review of changed reasoning/evidence.
- The parent tracks completeness rounds, persona-review rounds, grounding pairs,
  per-invocation item attempts, and user limits in one cumulative run-budget ledger.
  Renewed checks consume remaining counters; handoffs and corrections never reset them.
  Keep artifacts incomplete until required checks pass or execution stops.
