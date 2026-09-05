# Delegation

How the conductor uses workers. Raw wrapper mechanics (canonical Agent call,
milestone log contract, Output Location Override, fallback timers, recovery
ladder) are unchanged from the sibling skill — read
`../../orchestrate-feature-dev/references/stage-execution.md` for those. This
file covers what is different when the conductor is Fable: economics, worker
prompt shape, the question-escalation channel, and the model policy.

## Economics

Per-tier rates live in
`../../orchestrate-feature-dev/references/stage-execution.md § Choosing a model
per stage` — one table, so the two pipelines cannot drift on pricing. What
matters here is your position in it: **you are the most expensive tier**, which
is the whole reason the coordinator pattern below pays.

Every token in your context costs several times a Sonnet worker's token — the
exact multiple depends on which introductory rates are still live, so read it
off that table rather than from a figure here — and you pay it again on every
subsequent turn of a long run. Anthropic's published
coordinator pattern — Fable plans and synthesizes but never touches the raw
material; cheap workers do all the reading — measured ~2.5× cheaper and ~3×
faster than solo Fable, with 84–98% of input tokens billed at the worker rate
(cookbook "Plan Big, Execute Small"; Anthropic-reported hybrid benchmarks:
orchestrator ≈96% of solo quality at ~46% cost on research, advisor ≈92% at
~63% on coding). The practical rules:

1. **Artifacts stay out of your context.** Workers write files and return
   short structured reports (status, artifact path, key findings, anomalies).
   You read reports, the run journal, and targeted excerpts — not documents,
   not source code, not diffs, not test output.
2. **Read deeply only when the decision is yours.** Judging conflicting
   research findings, choosing between design approaches, deciding whether a
   disputed review finding is real — these justify reading the relevant
   sections yourself. Routine progress does not.
3. **Never do worker work.** You do not edit source, write tests, run test
   suites, or produce stage artifacts. If you catch yourself about to, that
   is a delegation, not a task.
4. **Batch your judgment.** Prefer one decision pass over a set of worker
   reports to interleaving yourself into each worker's loop.
5. **Brief granularity has an optimum.** Each worker pays a fixed setup
   overhead; Anthropic's own cookbook bill went UP when they split the same
   work into narrower briefs. Size each brief as a meaningful token-heavy
   chunk (a whole stage skill, a root-cause fix group), and don't spawn a
   worker for a narrow low-token question — a quick targeted read that
   informs your own decision is cheaper done directly (producing artifacts
   or code is still always worker work).

## Worker prompt shape

Fable-era guidance applies to your workers too, in moderation: Sonnet workers
executing a well-understood stage skill benefit from precise instructions
(the skill itself is the procedure), while workers doing open-ended work
(research synthesis, fix loops, validation) do better with a goal, the why,
and constraints than with enumerated steps. Every worker prompt carries:

1. **Goal and why** — what outcome the worker owns and why the pipeline needs
   it (workers make better local decisions when they know the intent).
2. **Skill invocation or task spec** — for stage skills: "Invoke the Skill
   tool with skill `<plugin:skill>` and args `<exact args>`, then execute its
   instructions faithfully, including spawning every sub-agent the skill
   mandates." Argument quirks are load-bearing facts — copy them exactly from
   `field-notes.md § Stage-skill argument quirks`.
3. **Context pointers** — absolute paths to input artifacts. Workers read
   files themselves; never inline document content into the prompt.
4. **Output contract** — Output Location Override (canonical artifact path),
   milestone log path, and the final-message contract: STATUS
   (complete/failed/question), ARTIFACT (absolute path), SUBAGENT_ANOMALIES,
   NOTES (one line). No artifact content in the final message.
5. **Grounded progress claims** — include verbatim: "Before reporting
   progress or completion, audit each claim against a tool result from this
   session. Only report work you can point to evidence for; if something is
   not yet verified, say so explicitly." In Anthropic's testing this nearly
   eliminated fabricated status reports — and this pipeline's gate checks
   assume worker reports are honest.
6. **Question escalation** (below) and the active-checking line from
   `field-notes.md § Harness facts`.
7. **Enforcement addenda** where the gate requires them (review-phase
   addendum for the three gated stages — see `gates.md`).
8. **Checkout anchor** — verbatim: "You are operating in the git worktree at
   `<absolute worktree path>`. Confirm `git rev-parse --show-toplevel`
   matches that path before doing any work. Every sub-agent you spawn must be
   given this absolute path in its prompt and must confirm its own toplevel
   matches before reporting any finding."

   Your own `cd` into the worktree does not propagate to the sub-agents a
   worker spawns, so a reviewer or verification agent can resolve to the main
   clone on `master` and report internally-consistent findings about the wrong
   tree. The sibling pipeline lost a full Sonnet+Opus review cycle to exactly
   this: a Coverage Auditor raised 5 "fabrication" items that all evaporated
   once the worktree path was anchored in the prompt.

## Live writes to shared services

A background worker structurally cannot perform a real write to an externally
shared service, and no amount of prompt wording changes that. The permission
classifier scopes consent to the acting agent's own transcript, so relaying
the user's verbatim authorization through a worker prompt is rejected as
another agent's output rather than a direct user instruction — re-relaying or
rewording never flips it.

Do not respond by weakening the assertion. Split it: the **worker prepares**
the exact command blocks plus what output would prove each assertion, the
**user-present session (you, with the user) executes them**, and the worker
then **verifies read-only** — SQL against the run state, transcripts, audit
events. This matters most at G6, where live evidence is non-waivable: without
the split, a blocked write turns into a post-merge human follow-up and the
gate silently degrades into the unit-test-only evidence G6 exists to reject.

Relatedly, treat "blocked on VPN / credentials / permissions" from a worker as
a question to put to the user, never a terminal classification to record. The
user is frequently on VPN and available; a permission denial means _that
agent_ cannot do the write, not that it is impossible.

## Question escalation (the advisor channel)

A stuck Sonnet worker grinding on a judgment call wastes worker tokens and
produces a worse decision than thirty seconds of your attention. Invert
Anthropic's advisor pattern: you are the on-demand advisor, workers are the
executors, and the escalation costs little because the exchange is short.

Include in every worker prompt:

> If you hit a decision you cannot resolve from your inputs — contradictory
> requirements, a fork in approach with materially different costs, missing
> access you cannot obtain — do NOT grind or guess. Deliver a final message
> with STATUS: question, the decision needed, the options you see, and your
> recommendation. You will receive guidance and can be resumed.

When a worker escalates: answer with a short, decisive SendMessage (decision +
one sentence of rationale). Record the decision in the run journal. One
guidance exchange resolves most escalations; a worker needing a third
exchange is mis-scoped — reclaim the task, re-decompose, respawn.

Prefer follow-ups to a live worker over killing and respawning: a long-lived
worker keeps its context across the exchange (cache reads instead of
re-establishing everything), and Anthropic's guidance is explicit that
asynchronous orchestrator↔subagent communication outperforms
spawn-and-block. Respawn is for dead or mis-scoped workers, not for workers
that merely asked a question.

This channel is for judgment calls only. Workers still handle their own
mechanical retries, and the recovery ladder (idle workers, dropped
deliveries) is a separate mechanism.

## Model and effort policy

**There is no default worker tier. You choose one per worker and record why.**

The sibling skill's `../../orchestrate-feature-dev/references/stage-execution.md
§ Choosing a model per stage` has the tier costs and the reasoning about what
actually varies between stages — read it rather than re-deriving. The same
judgement applies here, with two differences specific to you:

- **You are already the expensive tier.** Every token in your own context costs
  ~10/50, and you pay it again on every turn of a long run. The coordinator
  pattern's saving comes from keeping raw material out of your context, not from
  choosing cheap workers — so do not economise on a worker's tier in a way that
  sends its findings back to you for re-derivation. That is the more expensive
  mistake.
- **A `fable` worker is almost never right.** You can review judgment directly,
  so prefer Sonnet or Opus workers generating competing analyses in parallel with
  you judging. Reserve a fable worker for judgment that needs deep isolated
  exploration you cannot afford in your own context — and record why.

**Pin the tier on any worker that spawns children.** Unpinned children inherit
the parent's model (verified 2026-07-04), so an unpinned worker bills its whole
subtree at whatever the worker ran — and an unpinned `fable` worker bills its
subtree at fable rates.

**Effort**: the Agent tool exposes no per-call effort knob — workers run at
their model's session default, which is appropriate. Where an effort knob does
exist (Workflow-tool `agent()` calls, custom agent definitions), use `low` for
mechanical stages and the default elsewhere; don't buy `xhigh` for work a stage
skill already proceduralizes.

Record each choice in the state file's `decisions` array: the worker, the tier,
and the reason in a clause.

## Parallelism

Run in parallel (spawn in a single message, one shared fallback timer sized
to the slowest):

- Research-phase inputs: `/operational-context` + `/design-approach`
- Per-plan `/create-plan-tdd` within a wave
- Independent reviewer/validator agents, competing design-option workers

Run strictly sequentially:

- Plan implementations in a shared worktree (CPU saturation + cross-plan test
  noise — `field-notes.md § Execution constraints`)
- Anything mutating the state file: you are the single writer

Never re-attempt a stage while a prior attempt may still be running, and
never parallelize two workers whose write sets overlap.

## Judging worker output

Accept a stage on evidence, not prose:

1. Completion report says complete AND artifact exists at the canonical path
   (fallback search per `field-notes.md § Output locations` if not).
2. Gate-specific evidence checks pass (`gates.md`).
3. Spot-check proportional to blast radius: cheap look at a research doc's
   section headings; a real read of the contract's assertion list (it
   constrains everything downstream); the validator's raw evidence for any
   assertion you find surprising.

When a worker's claim and its evidence disagree, the evidence wins and the
worker's stage is not complete. Never patch over a failed gate yourself —
that converts a worker failure into an unreviewed conductor edit.
