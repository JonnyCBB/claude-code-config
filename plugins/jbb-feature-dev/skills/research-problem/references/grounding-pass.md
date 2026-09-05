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

After research is complete and reviewed (Steps 1-7), scan the synthesized findings for
uncertainties that can be resolved with a single tool call, file read, or CLI command,
and resolve them empirically before generating the final document. A separate
Verification Agent checks that resolution genuinely happened before the pass is
considered done, rather than trusting the Grounding Agent's own self-report — see
`## Grounding Loop: Orchestrator Handoff Protocol` below for how the two agents iterate
together.

The pass has two inputs of different shapes, and both must be worked:

- **Claims** — assertions in the synthesis carrying uncertainty, detected by the heuristic
  table or flagged `Needs Verification: YES` by Step 6.
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
- **It needs someone's knowledge or consent.** "Who holds the `api_client_creator` role?"
  needs a person, not a query.
- **The instrument exists but is unreachable from this session.** Access denied, no
  credentials, a tool that 404s. Record the attempt and the error — a documented failure is a
  resolved classification, not an open loop.
- **It can only be observed later.** "Does the 45-day archiver actually sweep this config?"
  cannot be answered before day 45.
- **The sources of truth genuinely disagree** and nothing available adjudicates between them.
- **It is immaterial.** Per the Materiality Filter, a question whose answer changes no
  conclusion is correctly left alone — say so explicitly rather than implying it was pursued.

**A question may NOT stay open when the document itself names what would settle it.** Phrases
like "one refresh call settles it", "a direct `ListConfig` probe would confirm this", "this
rests on a Slack index rather than the API", or "use the pricing calculator" mark a work item
that got written down instead of done. Heuristic 6 exists to catch exactly this phrasing.

The failure mode this guards against is specific and has recurred: a run ends, the reader
scans the Open Questions, asks one of them back, and a single command answers it. Every such
round-trip means the research stopped one call short and handed the remainder to the person
who commissioned it. Judge each Open Question by asking — _if the reader asked me this right
now, would I reach for a tool, or would I have to ask someone?_ Only the second belongs here.

## Heuristic Table: Detection Signals

| #   | Detection Signal                                                                                                                                                                                                          | Resolution Action                                                          | Cost                  | False Positive Risk                                              | Handling on Failure                                                                       |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 1   | Text mentions a tool name matching `mcp__*` pattern + "not tested" / "not verified" / "unconfirmed"                                                                                                                       | Call the MCP tool with a minimal test input (e.g., a known component name) | Low (1 call, <15s)    | Tool requires auth not available in session                      | Skip on error; document as "Attempted: [tool call]. Result: [error]. Remains unresolved." |
| 2   | "should be confirmed in [file]" / "not verified against [source file]" / "not checked in [file]"                                                                                                                          | Read or grep the referenced file via CodeSearch MCP or direct Read         | Low (1 call, <5s)     | File doesn't exist or has moved                                  | Skip on 404; document as "File not found at referenced path."                             |
| 3   | Text contains a shell command (e.g., `gh api ...`, `curl ...`, `git ...`) + "not run" / "should be verified" / "recommended"                                                                                              | Execute the command via Bash                                               | Low (1 call, <30s)    | Command requires env not in session (missing binary, wrong repo) | Skip on non-zero exit; document command + error                                           |
| 4   | URL provided but content described as "not fetched" / "not verified" / "assumed from"                                                                                                                                     | Fetch the URL via WebFetch                                                 | Low (1 call, <10s)    | URL returns 403/404/timeout                                      | Skip on error; document as "URL inaccessible: [status code]."                             |
| 5   | "release status unconfirmed" / "availability not verified" / "version unknown"                                                                                                                                            | Query package registry, GitHub API, or AiKA search                         | Low (1-2 calls, <15s) | Registry doesn't carry the package; API returns no results       | Skip on empty/error; document as "Not found in [registry]."                               |
| 6   | The text **names the instrument that would settle it** — "one X call settles it" / "a direct [probe] would confirm" / "rests on [weaker source], not [authoritative source]" / "use the [tool]" / "could be confirmed by" | Execute the named instrument                                               | Low (1-2 calls, <30s) | The named instrument needs access unavailable in session         | Skip; document as "Attempted: [instrument]. Result: [error]. Remains unresolved."         |

### Scope Notes

- These heuristics catch **explicit uncertainty markers** — cases where the research agent
  flagged something as uncertain. They do not catch **silent unverified claims** (where the
  agent stated something as fact without noting it was unverified). Step 6's `Needs
Verification: YES` flags (passed into the Grounding Agent alongside the synthesis) close
  part of this gap by surfacing claims about tool behavior, API responses, or configuration
  effects that were never marked uncertain in prose but weren't empirically checked either.
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
| **RESOLVABLE**   | Matches a heuristic pattern AND the resolution action is available in the current session (tool connected, file accessible, command available) | Attempt resolution                               |
| **UNRESOLVABLE** | More research alone cannot answer it — see `## What Legitimately Stays Open` for the qualifying reasons                                        | Document as Open Question — do not attempt       |
| **SKIP**         | Resolution cost exceeds bounds (multi-step scaffolding, requires test data setup, needs staging environment)                                   | Document as "Skipped: [reason]" — do not attempt |

Classification is mandatory and total: an item that reaches the final document as an Open
Question without a classification is a process defect, not a disclosure. UNRESOLVABLE is a
legitimate and expected outcome — it is the _unclassified_ item that signals the pass was
skipped.

## Materiality Filter

A claim or question is **material** if resolving it could change a conclusion,
recommendation, or tier classification in the document. A claim is only pursued if it is
BOTH objectively verifiable (per the RESOLVABLE/UNRESOLVABLE/SKIP axis above) AND
material.

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
uncertainty AND every candidate Open Question that can be settled with a single tool call,
file read, or CLI command — so that what remains open is only what more research cannot
answer.

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

## Instructions

1. **Scan** three sources, not one: (a) the synthesized findings, for uncertainty markers
   matching any detection signal in the heuristic table below; (b) every Step 6 `Needs
Verification: YES` flag, even if it doesn't match a heuristic verbatim; (c) every entry in
   Candidate Open Questions. On iteration 2+, prioritize the Prior Verification Feedback
   gaps first. Heuristic 6 (the text naming its own instrument) applies to all three.

2. **Classify** each detected uncertainty and each candidate Open Question as RESOLVABLE,
   UNRESOLVABLE, or SKIP using the classification rules. For anything you classify
   UNRESOLVABLE, name which of the qualifying reasons in `## What Legitimately Stays Open`
   applies — "needs a human decision", "unreachable from this session", and so on. If you
   cannot name one, it is not UNRESOLVABLE; attempt it.

3. **Resolve** each RESOLVABLE item by executing the resolution action:
   - For MCP tools: call with a minimal test input
   - For file references: read or grep the file
   - For shell commands: execute via Bash
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

   ### Item [N]
   - **Kind**: Claim / Candidate Open Question
   - **Location**: [section and line reference in findings, or "Candidate Open Questions"]
   - **Original text**: "[the uncertain claim, or the question as written]"
   - **Detection signal**: Heuristic [N] or "Step 6 flag" or "Candidate Open Question" or
     "Prior verification gap" or "Surfaced while resolving item N"
   - **Classification**: RESOLVABLE / UNRESOLVABLE / SKIP
   - **If UNRESOLVABLE, qualifying reason**: [which reason from `## What Legitimately Stays Open`]
   - **Action taken**: [what you did, or why you didn't act]
   - **Result**: [empirical finding, or error encountered]
   - **Updated text**: "[revised claim, or the answer to the question]" or "Remains open — [reason]"

5. **Self-check** your execution fidelity before finishing. Produce a table with columns
   Item | Kind (Claim/Question) | Classification | Action Taken (Y/N) | Qualifying reason (if
   UNRESOLVABLE) | Result. Every RESOLVABLE row must show "Y" with a corresponding result, and
   every UNRESOLVABLE row must name a qualifying reason. A RESOLVABLE row showing "N", or an
   UNRESOLVABLE row with no qualifying reason, is a reporting defect — flag it explicitly
   rather than silently submitting the table as-is. Also state the count of candidate Open
   Questions you received and the count you classified; they must match. This table is the
   primary evidence a separate Verification Agent will check next, so completeness and honesty
   here matter more than in a report nobody double-checks.

## Heuristic Table

[HEURISTIC_TABLE]

## Per-Attempt Bounding Rules

- **Maximum 25 resolution attempts within this invocation.** Count one attempt per item you
  try to resolve, plus one per follow-on you pursue. Do **not** count tool calls, batches, or
  reads you make while reasoning — an item needing four greps to settle is one attempt. This
  unit is defined tightly on purpose: an earlier version bounded "rounds" and left the unit
  open, and two agents doing identical work self-reported 6 and 11 against the same cap, which
  makes a cap unenforceable and its overruns undiagnosable. Report the count using this
  definition, and if you are unsure whether something counted, say so rather than picking the
  flattering reading.

  The budget is deliberately generous — accuracy matters more here than finishing quickly, and
  the Materiality Filter, not this number, is what should stop you pursuing something. Observed
  real passes have needed roughly 6-13 attempts, so 25 is around double the high end. If you
  approach it, that is a signal the synthesis carries unusually many material gaps: hand the
  remainder to the next iteration via "Follow-ons for the next iteration" (see Instructions
  step 3) rather than overrunning or silently dropping them. This bound is separate from the
  orchestrator's Grounding Iteration Bound (how many times you get re-spawned) — you are not
  responsible for that count.

- **30-second timeout** per attempt — skip any attempt that takes longer
- On any error (MCP failure, command failure, 404, timeout): skip and document the
  attempt and error. Never retry a failed attempt.

## Principles

- You are a documentarian. Report what you observe empirically — do not evaluate,
  critique, or recommend.
- Prefer false negatives over false positives: if unsure whether an uncertainty is
  resolvable, classify as SKIP rather than attempting something speculative.
- Every resolution attempt must be documented, whether it succeeds or fails.
```

## Verification Agent

Step 8 uses a dedicated Verification Agent instead of trusting the Grounding Agent's own
self-check — for the same reason Step 6 uses a separate evaluator instead of
self-evaluation: models reliably skew positive when grading their own work. The
Grounding Agent's self-check table (above) is a useful first-line signal, but it is still
the same agent grading itself; the Verification Agent is what actually gates whether
Steps 8-9 are done.

### Verification Agent Prompt Template

Pass this prompt to the Verification Agent (model: haiku, no tools). Replace bracketed
placeholders with actual values — including `[MATERIALITY_FILTER]`, which must be this
file's canonical `## Materiality Filter` text verbatim, not a paraphrase.

```markdown
You are the Grounding Verification Agent for a research document. Your job is to judge
whether the Grounding Agent's resolution work is genuinely complete. You do not call
tools, read files, or re-run any resolution attempt yourself — you are checking a report,
not redoing the work it describes.

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

[GROUNDING_AGENT_REPORT — the full per-uncertainty results and self-check table produced
by this iteration's Grounding Agent]

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
   mentions at all. Compare the count of candidate questions supplied against the count the
   report classified — a mismatch is a coverage gap even if the report claims completeness.
3. **Miscategorization**: any claim or question marked SKIP or UNRESOLVABLE that, on
   inspection, looks resolvable with a single tool call, file read, or CLI command per the
   Classification Rules — or any item the report treats as worth pursuing that the
   Materiality Filter (below) would not actually classify as material.
4. **Unjustified Open Questions**: any item classified UNRESOLVABLE without naming a
   qualifying reason from `## What Legitimately Stays Open`, or naming one that does not fit.
   Watch specifically for a question whose own text names the instrument that would settle it
   (the disqualifying phrasings under `## What Legitimately Stays Open`) yet is classified
   UNRESOLVABLE — that is Heuristic 6 being missed, and it is the single most common way an
   answerable question reaches a finished document.

## Materiality Filter

[MATERIALITY_FILTER — substitute this file's canonical `## Materiality Filter` section
verbatim here, not a paraphrase, so the Verification Agent judges against the exact same
definition the Grounding Agent and Step 6 use rather than a drifted restatement]

Produce your evaluation using EXACTLY this format:

### Coverage Check

- Step 6 `Needs Verification: YES` flags all addressed: [YES/NO — list any missed]
- Heuristic-matched claims all addressed: [YES/NO — list any missed]
- Candidate Open Questions: [N supplied / N classified — list any unclassified]

### Resolution Quality Check

For each RESOLVABLE row in the grounding report's self-check table:
Claim or question: [text]
Genuinely resolved: [YES/NO — evidence]

### Open Question Justification Check

For each item classified UNRESOLVABLE or SKIP:
Item: [text]
Qualifying reason given: [the reason, or NONE]
Reason holds: [YES/NO — if NO, say what instrument the text itself names]

### Decision

PROCEED — every material, objectively-verifiable claim and question is genuinely resolved,
or correctly classified UNRESOLVABLE/SKIP with a qualifying reason that holds
OR
ITERATE — a material gap remains (apply the Materiality Filter above; a non-material gap
does not justify ITERATE — note it as an Open Question instead)

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
- **Input**: synthesized findings + Step 6 flags (identical to the Grounding Agent's
  input for this iteration) + the Grounding Agent's full report for this iteration +
  prior verification feedback (iteration 2+ only)

## Grounding Loop: Orchestrator Handoff Protocol

Steps 8-9 form a bounded loop between the Grounding Agent and the Verification Agent,
mirroring Step 6's separate-evaluator principle. This section covers the orchestrator's
responsibilities across that loop; the two prompt templates above cover what each agent
does within a single iteration.

1. **Spawn**: Spawn the Grounding Agent with the synthesized findings + Step 6 flags (+
   Prior Verification Feedback, iteration 2+ only).
2. **Spawn**: Once the Grounding Agent completes, spawn the Verification Agent with the
   same findings/flags plus the Grounding Agent's report.
3. **Display**: Output the Verification Agent's verdict verbatim (no editing, no
   summarizing).
4. **Parse**: Read the Decision field — it starts with either "PROCEED" or "ITERATE".
5. **If PROCEED**: Proceed to Step 9 using this iteration's grounding report as final.
6. **If ITERATE** and the Grounding Iteration Bound (below) has not been reached:
   increment the iteration counter and return to step 1, passing the Verification
   Agent's "Remaining material gaps" list as the next round's Prior Verification
   Feedback.
7. **If ITERATE** and the Grounding Iteration Bound has been reached: stop. Document
   every remaining gap from the Verification Agent's final report as an Open Question or
   a "Skipped: [reason] — Grounding Iteration Bound reached" annotation (the same
   bounded-out fallback used elsewhere in this skill), then proceed to Step 9 using the
   final iteration's grounding report.
8. **Delivery resilience**: Apply this skill's standard idle/recovery ladder to both
   agents independently. If either goes idle without delivering (`idle_notification`
   with no content message), prompt it via SendMessage using its agent ID, then respawn
   once if still idle. If the Verification Agent's respawn also fails, fall back to the
   Grounding Agent's own self-check table as the completeness signal, explicitly
   annotated as "unverified self-report — Verification Agent did not deliver," and
   proceed to Step 9. If the Grounding Agent's respawn also fails, document the gap and
   proceed to Step 9 with whatever the last successful iteration produced.
9. **Task ownership**: All `TaskUpdate`/`TaskCreate` mutations are the orchestrator's
   responsibility. Neither agent modifies task state.
10. **Never substitute self-verification.** The orchestrator must never judge the
    Grounding Agent's completeness itself in place of spawning the Verification Agent —
    doing so defeats the reason this loop exists (see the Verification Agent's
    Disposition section above).

## Grounding Iteration Bound

- **Maximum 5 grounding iterations** (one iteration = one Grounding Agent spawn plus one
  Verification Agent spawn). This is a starting default, not an empirically validated
  number — no telemetry yet exists for how many iterations a real grounding pass actually
  needs. It's set higher than Step 6's own "max 4" (see `verification-and-iteration.md`'s
  Maximum Iterations Rule) deliberately: grounding gaps are typically narrower and cheaper
  to close per round than the open-ended research gaps Step 6 iterates on, so a slightly
  larger budget before falling back to Open Questions is reasonable here. Revisit once a
  few real runs are instrumented for cost and time.
- This bound is distinct from the Grounding Agent Prompt Template's **Per-Attempt Bounding
  Rules**, which cap resolution attempts inside a single Grounding Agent invocation. The two
  answer different questions — how much resolution work one spawn gets, versus how many times
  the orchestrator re-spawns the Grounding-Agent-then-Verification-Agent pair — and each is
  stated once, in its own section, so they cannot drift into meaning the same thing. Neither
  number is repeated here; a previous revision of this bullet restated both and one of them
  went stale, contradicting the very bullet above it.
- This is the single canonical location for the grounding-iteration bound; `SKILL.md`'s
  Step 8 points here rather than restating the number.

## Synthesis Revision Instructions (Step 9)

After the grounding loop reaches PROCEED (or exhausts the Grounding Iteration Bound), the
main orchestrator reviews the final iteration's grounding results and revises the
synthesized findings. This is Step 9.

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

1. Read all grounding results from the final grounding iteration's report
2. For each result with `Classification: RESOLVABLE` and a non-error `Result`:
   - Locate the section(s) in the synthesized findings that reference the resolved
     uncertainty
   - Replace the uncertain claim with the grounded finding
   - Check if the change affects recommendations, conclusions, or tier classifications
     in that section
   - If yes, update those dependent statements
3. For each result with an error (tool failed, file not found, command failed), or a gap
   still open when the Grounding Iteration Bound was reached:
   - Replace the uncertainty marker with the grounding attempt annotation:
     "Attempted: [action]. Result: [error]. Remains unresolved." or "Skipped: [reason] —
     Grounding Iteration Bound reached."
4. Do NOT re-open Step 2's research questions or spawn new research agents. Only update
   sections that reference grounded findings.

   **But**: if applying a grounding result reveals a follow-on question that passes the
   Materiality Filter and is resolvable in a single action, route it back into the grounding
   loop rather than writing it into Open Questions. A question created inside a verification
   gate must not escape through it. The canonical example: grounding retires a metric-based
   claim ("this gauge cannot support a growth rate"), which creates the question "so what is
   the real count?" — that question is one probe away and belongs in the loop, not in the
   document's Open Questions.

### Bounding

- **Single revision pass** — revise affected sections once, then proceed to Step 10
- **No fixed time bound** — Step 9 runs until synthesis revision is genuinely complete.
  The only cutoff is a stall: if the agent sends an `idle_notification` with no further
  content, apply this skill's standard recovery ladder (nudge once via SendMessage using
  the agent's ID, respawn once if still idle, then halt and document the gap if the
  respawn also stalls).
- **No re-review** — grounding results, confirmed by the Verification Agent, are
  empirical facts, not prose claims; they do not need persona review
