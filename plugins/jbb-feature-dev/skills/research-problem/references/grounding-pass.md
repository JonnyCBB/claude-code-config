# Grounding Pass (Steps 8-9)

The pass works two kinds of input, and missing the second is the common failure:

- **Claims**: assertions in the synthesis, including unmarked ones, requested answers and
  scoped factual descriptions. The heuristics and Step 6 flags add detection signals; they do
  not limit which claims are eligible.
- **Questions**: the `## Candidate Open Questions` from Step 5. They assert nothing, so they
  match no heuristic, but each is a work item.

## What Legitimately Stays Open

Open Questions are a feature of an honest document and there is no target of zero. The test
is the reason a question is open. It may stay open when more research alone cannot answer it:

- **It needs a human decision.** "Should we widen the per-user path beyond `MCP_GATEWAY`?" is
  a product choice.
- **It needs someone's knowledge or consent.** Check directories, APIs or records first: role
  membership may be queryable, while permission to widen a role is a consent decision.
- **The instrument exists but is unreachable from this session.** Record the failed access.
  One failed route does not prove every source unavailable.
- **It can only be observed later.** "Does the 45-day archiver sweep this config?" cannot be
  answered before day 45.
- **The sources of truth disagree** and nothing available adjudicates.
- **It is immaterial** under the Materiality Filter; state why.

A question that names its own instrument ("one refresh call settles it", "a direct
`ListConfig` probe would confirm this", "this rests on a Slack index rather than the API",
"use the pricing calculator") needs an attempt, or a verified reason it could not be
attempted. The failure this guards against has recurred: the reader scans the Open Questions,
asks one back, and a single command answers it. Ask of each one: if the reader asked me this
now, could I answer it?

## Detection Signals

| # | Signal | Action |
| - | ------ | ------ |
| 1 | `mcp__*` tool + "not tested" / "not verified" / "unconfirmed" | Inspect the tool's actions, then make a read call with relevant input |
| 2 | "should be confirmed in [file]" / "not verified against [file]" | Read or search the file (Read, Grep) |
| 3 | Shell command + "not run" / "should be verified" | Inspect the command and its side effects, then run it if it only reads |
| 4 | URL + "not fetched" / "assumed from" | Fetch it |
| 5 | "release status unconfirmed" / "version unknown" | Query the registry or release records |
| 6 | Text names its instrument: "one X call settles it" / "a direct [probe] would confirm" / "rests on [weaker source], not [authoritative source]" / "could be confirmed by" | Use that instrument |

Signal 6 applies to questions as well as claims and has the highest yield: an audit of shipped
research documents found one to two answerable Open Questions per document, and in most the
text named its own instrument. The signals are prompts for judgement, not triggers: "not
tested" in a section about decommissioned tools does not call for a test. Document every
attempt, including failures.

## Classification Rules

Classify every detected uncertainty and every candidate Open Question:

| Classification | Criteria | Action |
| -------------- | -------- | ------ |
| **RESOLVABLE** | Available evidence can answer it within the attempt budget | Attempt it |
| **UNRESOLVABLE** | A reason from `## What Legitimately Stays Open` applies, and is verified | Record the reason, the evidence, and what would close it |
| **SKIP** | A stated scope or safety limit, or a verified budget limit, prevents pursuit. Uncertainty alone is not enough | Record the concrete reason. A material item skipped for budget leaves the run incomplete |

Classification is total. An Open Question in the final document without a classification is a
process defect.

## Materiality Filter

An item is **material** if resolving it could change a requested answer, a success criterion,
a scoped factual description, a conclusion, a recommendation or a tier. Resolve material items.
Incidental detail, and edits that leave meaning, evidence and recommendations unchanged, do not
reopen checks.

Example: "File X's line count was not verified" is material if the count feeds a planning
decision (a per-file task estimate), and not material if it is incidental colour.

This is the single definition of materiality in the skill.

## Per-Attempt Bounding Rules

- **At most 25 resolution attempts per Grounding Agent invocation.** One attempt per item you
  try to resolve, plus one per follow-on you pursue. Tool calls do not count: an item needing
  four greps is one attempt. The unit is fixed this tightly because two agents doing the same
  work under a looser unit self-reported 6 and 11 against one cap. If unsure whether something
  counted, say so rather than taking the flattering reading. Real passes need about 6-13; the
  Materiality Filter, not this number, should stop you. Near the cap, list the rest under
  "Follow-ons for the next iteration".
- Classify each error: access, invalid query or path, not found, timeout, or uncertain
  outcome. One corrected query or one independent read-only source is allowed per item. Never
  repeat an unchanged failure, and never retry a mutation or an uncertain outcome.
- An empty result proves absence only within the query's coverage. Record the query, scope,
  result and the checks not made.

## Grounding Agent Prompt

Fill every placeholder. On iteration 1 omit the Prior Verification Feedback block.

```markdown
You are the Grounding Agent for a research document. Resolve every material item and every
candidate Open Question that available evidence can answer. Assess every supplied ID, not only
the items that match a detection signal.

## Synthesized Findings
[SYNTHESIZED_FINDINGS]

## Step 6 Evaluator Flags
[STEP_6_FLAGS - per-question "Needs Verification: YES/NO"]

## Candidate Open Questions
[CANDIDATE_OPEN_QUESTIONS - from the synthesis, plus any gap a Step 7 reviewer asked to
document. Classify each. If this block is empty, say so in your report.]

[IF ITERATION 2+:]
## Prior Verification Feedback
[PRIOR_VERIFICATION_FEEDBACK - the verifier's "Remaining material gaps". This is your primary
work list; keep the unresolved IDs and earlier evidence from before.]
[/IF]

## Run Ledger
[RUN_LEDGER - IDs, originating links, evidence, errors, classifications, remaining counters]

## Policies
[WHAT_LEGITIMATELY_STAYS_OPEN, DETECTION_SIGNALS, CLASSIFICATION_RULES, MATERIALITY_FILTER,
PER_ATTEMPT_BOUNDING_RULES - each canonical section verbatim]

## Instructions

Collect evidence by reading only. Do not send messages, mutate records, connect servers or
change settings. Inspect a tool or command for side effects before running it; report any
needed mutation separately instead of doing it.

1. **Inventory** every supplied ID. Add items that match a detection signal.
2. **Classify** each item. For UNRESOLVABLE, name the reason from What Legitimately Stays Open;
   if you cannot name one, it is not UNRESOLVABLE, so attempt it.
3. **Resolve** each RESOLVABLE item. For a question that names its instrument, use that
   instrument. If resolving an item raises a material follow-on, pursue it within your attempt
   budget; if the budget will not cover it, list it under "Follow-ons for the next iteration".
   Do not write it into Open Questions and do not overrun the cap.
4. **Report** each item:

   ### Item [ID]
   - **Kind**: Requested answer / Success criterion / Claim / Evaluator flag / Reviewer gap /
     Candidate Open Question / Follow-on
   - **Originating IDs**:
   - **Original text**:
   - **Detection signal**: Signal [N] / Step 6 flag / Candidate Open Question / Prior gap /
     Surfaced while resolving [ID]
   - **Classification**: RESOLVABLE / UNRESOLVABLE / SKIP (with the qualifying reason)
   - **Action and evidence**: the exact call, command or query; the source; a response
     excerpt; the call ID if one exists
   - **Result**: the finding, or the classified error
   - **Coverage and limits**: what an absence claim covers, and the checks not made
   - **Updated text**: the revised claim or the answer, or "Remains open - [reason]"

5. **Self-check table**: Item ID | Kind | Classification | Action taken (Y/N) | Qualifying
   reason | Result. Every RESOLVABLE row shows Y with a result, and every UNRESOLVABLE row names
   a reason; flag any row that does not. State the number of candidate Open Questions received
   and the number classified; they must match. A separate Verification Agent checks this table
   next.

Document what you find; recommend only if the user asked. Never invent a recommendation.
```

## Verification Agent Prompt

The Grounding Agent's self-check is the same agent grading itself; this agent is the gate. It
gets text only (model: haiku, told not to use tools). Giving it tools would make it a second
grounding pass instead of a check on the first. Inline every policy section verbatim, and the
run ledger, not only this round's gaps. Its tool roster need not be empty.

```markdown
You are the Grounding Verification Agent. Judge whether the Grounding Agent's work is complete.
Do not call tools, read files or re-run any attempt: you are checking a report, not redoing it.
If input is missing, say so. You are separate from the agent that wrote the report because
models skew positive when grading their own work. When the report is ambiguous or looks
incomplete, choose ITERATE.

## Synthesized Findings
[SYNTHESIZED_FINDINGS]

## Step 6 Evaluator Flags
[STEP_6_FLAGS]

## Candidate Open Questions
[CANDIDATE_OPEN_QUESTIONS - every entry must appear in the report with a classification]

## Grounding Agent Report
[GROUNDING_AGENT_REPORT - per-item results and self-check table]

## Run Ledger
[RUN_LEDGER]

[IF ITERATION 2+:]
## Prior Verification Feedback
[PRIOR_VERIFICATION_FEEDBACK - your previous output]
[/IF]

## Policies
[WHAT_LEGITIMATELY_STAYS_OPEN, DETECTION_SIGNALS, CLASSIFICATION_RULES, MATERIALITY_FILTER,
PER_ATTEMPT_BOUNDING_RULES - verbatim]

## Instructions

Check for four failures:

1. **Unactioned resolutions**: a RESOLVABLE row with N, or updated text that is still
   uncertain.
2. **Coverage gaps**: a Step 6 flag, a signal-matching claim, a candidate question, a requested
   answer, a criterion, a reviewer gap or a follow-on that the report never mentions. Match IDs,
   not counts; list missing, duplicate or substituted IDs.
3. **Miscategorization**: a SKIP or UNRESOLVABLE item that available evidence could answer, or
   a pursued item that is not material.
4. **Unjustified Open Questions**: an UNRESOLVABLE item without a qualifying reason, or with one
   that does not fit. A question that names its instrument needs an attempt or a verified
   reason it could not be attempted.

### Coverage Check
- Step 6 flags addressed: YES/NO - [missed IDs]
- Signal-matched claims addressed: YES/NO - [missed IDs]
- Candidate Open Questions: [supplied IDs / classified IDs - missing, duplicate, substituted]
- Requested answers, criteria, reviewer gaps, follow-ons: [IDs and gaps]

### Resolution Quality Check
For each RESOLVABLE row: [item] - supported by the supplied evidence: YES/NO - [what is missing
or only self-reported]

### Open Question Justification Check
For each UNRESOLVABLE or SKIP item: [item] - reason given: [reason or NONE] - holds: YES/NO -
[if NO, the instrument its own text names]

### Decision
PROCEED - the evidence supports every material resolution and every UNRESOLVABLE/SKIP reason,
and no material item is unfinished for budget
OR
ITERATE - material gaps, missing decisive evidence, self-report-only evidence, or unfinished
material items remain

[If ITERATE:]
Remaining material gaps:
1. [item] - [why material] - [what the next round should do, e.g. "not attempted",
   "classified UNRESOLVABLE but its text names a `gh api` call that would settle it"]
```

## Grounding loop

1. Spawn the Grounding Agent, then the Verification Agent with the same inputs plus the report.
2. Display the verifier's verdict verbatim and read its Decision.
3. **PROCEED**: go to Step 9.
4. **ITERATE**: if under the Grounding Iteration Bound, start the next iteration with the
   "Remaining material gaps" as Prior Verification Feedback. At the bound, stop at an
   incomplete checkpoint.
5. Apply Agent Delivery Resilience (`SKILL.md`) to each agent. An earlier report or your own
   check never replaces a current verdict from the Verification Agent.

**Grounding Iteration Bound: at most 5 iterations** (one Grounding Agent spawn plus one
Verification Agent spawn each). This is a starting default, not a measured figure. It is
separate from the 25-attempt cap, which bounds one invocation.

## Synthesis Revision Instructions (Step 9)

Work from the run ledger of all grounding results, not only the last iteration's report.

1. For each resolved item, replace the uncertain claim with the grounded finding. Then check
   whether it changes a recommendation, conclusion or tier, and update those too. Typical
   cases: a tool marked "not tested" works (contingent becomes confirmed) or is broken
   (downgrade what assumed it worked); a code claim is wrong (correct it and re-check what was
   built on it).
2. For each UNRESOLVABLE or SKIP item that the PROCEED verdict accepted, replace the
   uncertainty marker with "Attempted: [action]. Result: [error]. Remains unresolved." or
   "Skipped: [qualifying reason]". Reaching a bound is never a qualifying reason.
3. Do not reopen Step 2's questions or spawn new research agents. But if applying a result
   raises a material follow-on that available evidence can answer, give it a linked ID and
   return it to the grounding loop. Example: grounding retires the claim "this gauge cannot
   support a growth rate", which raises "so what is the real count?" That question is one probe
   away and belongs in the loop, not in Open Questions.
4. Route substantive changes to re-checks as `SKILL.md` Step 9 says.
