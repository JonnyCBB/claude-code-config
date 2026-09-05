---
name: research-problem-fable
description: >
  Fable-native variant of /research-problem: conduct comprehensive research
  across the codebase and beyond by spawning parallel sub-agents and
  synthesizing their findings into a research document. Outcome-gated rather
  than step-scripted — hard evidence gates (approved plan, independent
  completeness evaluation, independent multi-persona review, empirically
  grounded findings, evidence-complete document) with researcher freedom over
  decomposition, routing, batching, and iteration. Same output location and
  document contract as the sibling, so downstream skills
  (/map-feature-to-plans, /design-approach, /create-plan-tdd) work unchanged.
  Use this INSTEAD of /research-problem when the session runs on Fable; use
  the sibling on Sonnet/Opus sessions. Trigger phrases: (1) "research with
  fable" (2) "fable research" (3) "research problem fable"
  (4) "investigate with fable".
argument-hint: "[query] [--non-interactive]"
---

# /research-problem-fable

One invocation takes a research question to an evidence-complete research
document in `~/.claude/thoughts/shared/research/`. Same destination as
`/research-problem`, different contract with you: that skill scripts fifteen
steps with task choreography, pre-spawn verification tables, and a state
machine because its orchestrator needed the script. You do not. This skill
fixes the **outcomes and their evidence** (the gates) and hands you the
**route** — over-prescription measurably degrades Fable-class output, and
the sibling's process scaffolding was compensation for planning weaknesses
you don't have.

The trade you are accepting: freedom over the route, zero freedom over the
gates. The gates encode two things the user has learned the hard way and
recorded as durable feedback: **independent agents judge your work — never
you** (models reliably skew positive grading their own output), and
**claims about tool behavior get verified empirically before they reach the
document**. Auto mode and `--non-interactive` never waive a gate; they only
change who confirms the plan.

## Operating model

You are a documentarian. Document and explain what exists — where it lives,
how it works, how components interact. No recommendations, critiques, or
root-cause analysis unless the user explicitly asked. Every sub-agent you
spawn inherits this: remind them they are documentarians, not evaluators.
(Empirically testing a tool and reporting the observed result IS
documentation; suggesting the tool be improved is not.)

Sub-agents do the reading and searching; your context is for decomposing,
routing, judging evidence, and synthesizing. Read a source yourself only
when the decision it informs is yours: files the user named (read those
fully, first, before decomposing — including Google Docs via the Drive
MCP), and Direct lookups (a single grep/glob/read with a deterministic
answer needs no agent).

Before declaring any gate passed, audit the claim against an artifact from
this session — an agent report, a verdict, a tool result you can point to.
If something is not yet verified, say so; never report a gate as passed on
the strength of remembering it happened.

## The gates

| Gate | Outcome that must be true                                                                                                        | Waivable?                                                         |
| ---- | -------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| G1   | Research plan produced (questions, assumptions, success criteria, scope, complexity, domain-expert check) and approved           | Confirmation mode varies; the plan itself never                   |
| G2   | Every question answered with evidence from its committed agent type (or a Direct lookup), with confidence assessments and links  | Routing and batching are yours                                    |
| G3   | Independent completeness evaluator returns PROCEED (or the iteration bound is reached, gaps documented)                          | **Never** — self-evaluation is never a substitute                 |
| G4   | Independent complexity-scaled persona review passed, domain expert verifier included on domain match                             | Simple complexity skips; otherwise only the user's explicit words |
| G5   | Grounding/verification loop returns PROCEED (or bound reached); synthesis revised with grounded facts                            | **Never**                                                         |
| G6   | Research document written with the required frontmatter, evidence, reproducibility record, and open questions; summary presented | No                                                                |

All prompt templates, output formats, bounds, and decision rules live in the
sibling's references (`../research-problem/references/`) — they are
contracts, not process, and this skill reuses them verbatim. The references
speak in the sibling's step numbers; the mapping is: Step 2 → G1,
Steps 3–4 → G2, Steps 5–6 → G3, Step 7 → G4, Steps 8–9 → G5,
Steps 10–15 → G6.

### G1 — Approved plan

Decompose the question using the templates and decision rules in
`../research-problem/references/plan-templates.md`: research questions with
assigned agent types, assumptions, success criteria, scope, research
context, execution plan (default to parallel when dependency is unclear;
Direct lookups resolved in main context before any spawn), the MANDATORY
Domain Expert Check against the table in
`../research-problem/references/agent-guide.md`, and a
Simple/Medium/Complex classification (signal table in
`../research-problem/references/review-personas.md`) that sets G4's scope.

- **Interactive (default)**: render the full plan in the UI — no file, no
  summarizing — then gate on `AskUserQuestion` (proceed / request changes /
  cancel) and wait. This is a user-input gate; auto mode does not authorize
  you to answer it yourself.
- **`--non-interactive`**: write the plan to
  `~/.claude/thoughts/shared/research_plans/YYYY-MM-DD-description-plan.md`
  (frontmatter spec in plan-templates.md, status: approved) and proceed.
  From here the run is autonomous: never end a turn on a promise or a
  question — decide within your freedom and keep going.

The approved plan's agent-type commitments are a contract: G2 is not
passable while a committed agent type was never spawned.

### G2 — Evidence gathered

Spawn researchers per the routing rules and Domain Expert Table in
`../research-problem/references/agent-guide.md`. Two routing facts there
are empirical, not stylistic: analysis of 69 research plans showed
live-system questions routinely misrouted to doc-searchers and left
unanswered (route production/deployment/topology/data questions to
`web-search-researcher`), and `codebase-explorer` is the custom agent,
not the built-in `Explore`. Domain experts beat generalists as primary
researchers when the question is HOW a domain technology works, not WHERE
code lives.

Every agent prompt carries the documentarian reminder, the Confidence
Assessment requirement, and (for external researchers) the links
requirement. Pass discovered context forward between dependent batches —
key findings, terminology, dead ends.

Yours to decide: batch composition and ordering, combining closely related
questions into one agent (tell the user what you combined and why), agent
count, and whether a failed or thin result warrants a retry, a respawn
with a sharper prompt, or a different agent type.

### G3 — Independent completeness verdict

Synthesize all findings per the synthesis instructions in
`../research-problem/references/verification-and-iteration.md`: live
codebase over historical context, file paths and line numbers, assumption
validation (CONFIRMED / INVALIDATED / UNCERTAIN), and contradictions
surfaced as Competing Findings — never silently resolved.

Then spawn the Completeness Evaluator (model: sonnet, no tools; prompt
template in the same file), passing the plan, the synthesis, and any prior
verdict. Display its verdict verbatim and act on the Decision field. On
ITERATE, return to G2 with the evaluator's gap list; the materiality filter
and the max-4-round bound in that file are canonical. You never evaluate
completeness yourself — an idle evaluator gets the recovery ladder (below),
then a respawn, never a self-assessment.

### G4 — Independent review

Reviewer selection scales with the G1 complexity classification
(`../research-problem/references/review-personas.md`): Simple skips this
gate; Medium spawns Gap Analyst, Devil's Advocate, and Source Critic;
Complex spawns all five personas. A matching domain expert flagged in G1
joins as Technical Accuracy Verifier (default model — it reads code;
generic personas run sonnet). Reviewers get the plan, the synthesis, and
the G3 verdict; feedback is synthesized in the file's format, Must Address
items are fixed, and the auto-approve threshold (zero Must Address, zero
disagreements, ≤2 Should Consider) closes the gate.

The skip rules in that file are fixed because the failure they guard
against is yours: every tempting justification ("the reports were
internally consistent", "marginal value is low", "token budget") is a
self-assessment of work you just produced. The only skip paths are the
user's explicit words, or a genuine reclassification to Simple — surfaced
to the user before you act on it. Non-interactive mode runs one review
iteration, auto-resolves Must Address, and records Should Consider as
advisory notes; it never converts review into self-review.

### G5 — Grounded findings

Uncertainties about tool behavior, API responses, file contents, and
availability get resolved empirically before the document is written — and
so does every candidate Open Question. Draft a `## Candidate Open
Questions` list into the synthesis before this gate opens: it is a work
list, and this is the last gate before the reader sees the document, so a
question that skips it escapes unexamined. Run the Grounding Agent /
Verification Agent loop exactly as specified in
`../research-problem/references/grounding-pass.md`: the detection
heuristics, RESOLVABLE/UNRESOLVABLE/SKIP classification applied to claims
AND questions, the canonical Materiality Filter, the Grounding Agent
prompt (fed the G3 evaluator's Needs-Verification flags plus the candidate
questions), and the haiku no-tools Verification Agent that gates the loop.
A question surfaced while resolving another one goes back into the loop,
not into the document. Both bounds — resolution attempts per grounding
spawn, and loop iterations — are stated once in that file; read them there
and do not restate them here. On PROCEED (or
bound exhaustion with gaps annotated), revise the synthesis per that file's
Step 9 instructions: grounded facts replace uncertain claims, dependent
conclusions get rechecked, failed attempts get documented verbatim. Never
retry a failed resolution attempt; never verify the grounding report
yourself in place of the Verification Agent.

### G6 — Document shipped

Before writing, verify the gate artifacts are actually present in your
context, not just remembered — synthesis, G3 verdict, G4 review (or
documented skip), grounding report, revised synthesis. Long runs get
compacted; a missing artifact means returning to the gate that produced it.
Also confirm every candidate Open Question carries a G5 classification with
a qualifying reason; an unclassified one means G5 did not close.

Then produce the document per
`../research-problem/references/document-template.md`: metadata script,
file naming, the full template (frontmatter MUST include
`review_phase_status` — `completed` or `skipped_simple_complexity` — and
`complexity`; downstream orchestrators parse these), GitHub permalinks when
on a pushed commit, MCP call documentation so findings are reproducible,
Open Questions that each name why research alone cannot close them, and the
operational-context / design-exploration recommendations. Preserve exact directory structure under
`~/.claude/thoughts/`; always run fresh research rather than recycling old
research documents.

Present a concise summary with key file references. Interactive mode then
offers follow-ups: append to the same document using the follow-up format
in document-template.md, spawning new agents as needed, until the user
confirms the research is complete. Non-interactive mode ends here.

## What is fixed besides the gates

Empirical facts are not rigidity — they are paid-for knowledge:

- **Agent delivery resilience.** The harness has a known bug family where
  subagents go idle without delivering (GitHub Issues #61547, #54323,
  #29163, #47930). On an `idle_notification` with no content: wait
  briefly, nudge once via SendMessage using the **agent ID from the spawn
  result** (name routing can silently fail, Issue #42999), then respawn
  once. If a judge agent (evaluator, reviewer, verification agent) still
  fails, document the non-delivery — never substitute your own judgment
  for the missing verdict. For research agents you may gather the data
  directly and note the non-delivery in the methodology.
- **Spawn hygiene.** Prefer `subagent_type` agents over bare `model`
  overrides; record each spawn's agent ID; parallel batches larger than
  5 have cascade-failed (Issue #57037) — split into sub-batches of 3–5.
- **Task tracking is yours to size.** The sibling's TaskCreate choreography
  existed to stop step-skipping; the gates replace it. Use TaskCreate where
  external visibility helps a long run — it is no longer a compliance
  mechanism.

## Inputs

Parse `$ARGUMENTS`: `--non-interactive` sets the mode; a file path is read
fully as the research query input; otherwise the arguments are the query.
With no query at all, ask for one and wait.
