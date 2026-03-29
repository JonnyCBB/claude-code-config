# Decision-Making Principles — Full Reference

Detailed guidance for each of the 14 decision-making principles. Each principle includes its
default stance, rationale, examples, override conditions, and a quick test.

Agent teams should treat these as heuristics, not rigid rules. When two principles conflict,
use the priority ordering from the main SKILL.md and the override conditions below.

---

## Principle 1: Safety First — Default to Not Sending

**Default**: If a safety mechanism (content filter, sensitivity classifier, toxicity detector)
fails or is unavailable, the system should **not send** the candidate result. Silence is safer
than an unvetted response.

**Rationale**: In systems that handle results which may be sensitive, explicit, or inappropriate,
a failed safety check means the result cannot be verified safe. Users experience a missing result
(minor UX degradation) rather than a harmful one (trust violation, brand risk, regulatory exposure).

**Applies to**:

- Content safety classifiers that gate search result candidates
- Toxicity/sensitivity filters on AI-generated text
- Age-gating or market-restriction checks
- Any system where false-positive cost (suppressing safe content) is orders of magnitude less
  than false-negative cost (surfacing unsafe content)

**Override**: Only when the safety mechanism has been explicitly evaluated and the failure mode
is known to be benign. For example, if a classifier fails but the content source is pre-vetted
(e.g., editorial playlists that have already passed human review), the fallback may be to send.

**Test**: "If this safety check fails, what's the worst that could surface?" If the answer
involves user harm, default to not sending.

**Priority**: This principle overrides all others. No amount of simplicity, precedent, or scope
reduction justifies bypassing safety.

---

## Principle 2: Follow Existing Codebase Precedent

**Default**: When implementing something new, find and follow the closest existing pattern in the
codebase. If a factory, client, or handler already solves a similar problem, model the new
solution after it rather than inventing a novel approach.

**Rationale**: Existing patterns have survived code review, testing, and production. They're
understood by the team. Novel approaches introduce review burden, learning curves, and unproven
failure modes.

**Example**: In the differentiated timeout research, the initial implementation followed the
`SearchInfluenceClientFactory` dual-client pattern because it was the established precedent.

**Override — when the simpler approach wins**: If an alternative is **significantly simpler** than
the precedent, prefer simplicity. The precedent pattern is a starting point, not a mandate.

**Override example**: A PR initially used the factory dual-client pattern. During review, feedback
suggested encapsulating timeout selection inside the client itself, eliminating the factory class
entirely. The simpler approach — fewer classes, better encapsulation, less code for the service
layer to manage — was accepted because it was strictly simpler.

**Test**: "Does the precedent pattern add complexity that this specific case doesn't need?"
If yes, the simpler approach wins. The precedent should be a floor, not a ceiling.

---

## Principle 3: Scope to Current Need, Not Future Vision

**Default**: Build the minimum needed for the current use case. Document the future-proof
approach but don't implement it.

**Rationale**: The future rarely arrives as predicted; document the future-proof approach but
don't build it.

**Override**: When the future need is **certain** (not speculative) and the cost of retrofitting
later is demonstrably high. For example, choosing a data format that supports backwards
compatibility is worth doing upfront because migration is expensive. But adding abstraction layers
"in case we need them" is not.

**Test**: "Can you name a specific, scheduled piece of work that will need the abstraction?"
If not, don't build it.

---

## Principle 4: "Too Complex for v1" Is a Valid Answer

**Default**: When an open question introduces significant complexity, the answer "no, not in this
iteration" is legitimate and often correct.

**Rationale**: Scope creep is the primary risk to shipping. "No for now" preserves focus.

**Example**: "Should cost/usage be included?" → "No — too complex for initial implementation."

**Override**: When the omitted feature is a **safety requirement** (see Principle 1) or when the
feature is trivially small and its absence would cause confusion or bugs.

**Test**: "Does saying 'no' to this question risk shipping something unsafe or confusing?"
If no, "too complex for v1" stands.

---

## Principle 5: Evidence Over Opinion

**Default**: Back decisions with concrete evidence — measurements, precedent code, paper findings,
incident data. "I think" is weaker than "the data shows."

**Rationale**: Decisions backed by evidence survive scrutiny, can be revisited when the evidence
changes, and transfer knowledge to future readers.

**Examples**:

- Timeout decisions reference actual latency measurements: "~16s average", "35s upstream budget"
- Skills efficacy research cites specific papers with confidence tiers (Tier 1/2/3)
- A 5s timeout decision references a specific incident where 30s timeouts caused cascading failures

**Override**: When the decision is low-stakes and aesthetic (see Principle 9), or when gathering
evidence would cost more than the decision is worth. For a font choice, "it looks better" is
fine. For a timeout value, it isn't.

**Test**: "If someone questions this decision in 6 months, can I point to data?" If not, find
the data before deciding.

---

## Principle 6: Prefer Consolidation Over Proliferation

**Default**: When multiple components serve the same purpose with slight variations, merge them
into one well-configured component.

**Rationale**: Fewer components = less maintenance. Merge when they share toolsets, behavioral
philosophy, and differ only in output focus.

**Example**: 4 ML agents merged into 1 unified expert; separate locator + analyzer agents merged
into single explorers.

**Override**: When the components genuinely serve different purposes, have different failure modes,
or different scaling requirements.

**Test**: "If I merge these, will the combined component need mode-switching logic that's more
complex than keeping them separate?" If yes, don't merge.

---

## Principle 7: Learn From Production Incidents

**Default**: Every timeout value, retry policy, circuit breaker, and error handling strategy
should be informed by real production incidents, not theoretical analysis.

**Rationale**: Production is the ultimate test environment. Incidents reveal failure modes that
design documents miss.

**Examples**:

- A 5s timeout was directly motivated by a previous incident where 30s timeouts caused
  cascading failures, resulting in empty results for 1.4% of requests
- An "execution duration as error signal" heuristic was learned from real on-call experience
- A gRPC context forking pattern was already in the codebase because a previous need required it

**Override**: None. This is an "always check" principle. Even when building something entirely new,
look for incident reports from analogous systems.

**Test**: "Have I checked for incidents in this area or analogous systems?" If not, check before
finalizing the design.

---

## Principle 8: Internal Tools Over External When Available

**Default**: Check if your organization already has a solution before looking externally. Internal
tools integrate better, have support channels, and are maintained by teams you can reach directly.

**Rationale**: External tools require integration work, may not support internal authentication
and infrastructure, and their maintainers don't know your context.

**Examples**:

- Research documents consistently check internal documentation before external sources
- Skills encode organization-specific knowledge that the model wouldn't know from training data

**Override**: When no internal tool exists for the need, or when the internal tool is
deprecated/unmaintained. Also when the external tool is an industry standard that the
organization explicitly supports (e.g., gRPC, Kubernetes, Ray).

**Test**: "Have I checked internal tools and documentation before recommending an
external solution?" If not, check first.

---

## Principle 9: Delegate Aesthetic and Low-Stakes Decisions

**Default**: For decisions that don't affect correctness, safety, or architecture, let the
agent/implementer decide. Reserve human review for structural and high-stakes choices.

**Rationale**: If the outcome is "improvement over current state" regardless of which option is
chosen, the decision doesn't need human input.

**Override**: When the "aesthetic" decision has downstream implications — e.g., choosing a CSS
framework that creates a dependency, or choosing a data format that other systems will need to
parse.

**Test**: "If we chose the other option, would we need to rewrite anything structural?"
If no, delegate. If yes, escalate.

---

## Principle 10: Document Rejected Approaches With Rationale

**Default**: Always document what was considered and why it was rejected. Never present only the
chosen approach.

**Rationale**: Without documented alternatives, future readers re-investigate the same options or
assume the chosen approach was the only one considered.

**Override**: None. This is a documentation practice, not a design choice. It costs very little
and its absence causes recurring pain.

**Test**: "Would a future reader understand why alternatives were rejected?" If not, document them.

---

## Principle 11: Optimize for Request Flow Efficiency

**Default**: When adding new operations to a request flow (new clients, service calls, processing
steps), run them concurrently with existing operations unless there's a data dependency.

**Rationale**: In latency-sensitive systems (especially search), sequential calls that could be
parallel add their full p99 to the critical path. A new client that takes 50ms p99 costs nothing
extra if run concurrently with an existing 200ms call, but adds 50ms if run sequentially.

**Example**: When implementing a new client in a search API service, run it concurrently with
other clients using the existing concurrent execution patterns (e.g., `CompletableFuture`,
executor-based concurrency). Don't insert it sequentially into the request flow simply because
that's easier to implement.

**Override**: When the new operation depends on the output of another operation (data dependency),
or when the system is resource-constrained and parallel calls would cause contention. Also when
the operation is trivially fast (< 1ms) and the concurrency overhead exceeds the benefit.

**Test**: "Does this operation need the output of any other operation that hasn't completed yet?"
If no, run it concurrently. If yes, it must be sequential — but only after the dependency, not
before all other operations.

---

## Principle 12: Verify Specification Completeness Before Proceeding

**Default**: Before planning implementation, verify you have acceptance criteria, scope
boundaries, success metrics, and at minimum the user's stated motivation. If any of these
are missing, gather them before proceeding.

**Rationale**: 70-80% of software knowledge is tacit (Code Digital Twin, Fudan 2025).
Agents that ask clarifying questions achieve up to 74% improvement over non-interactive
settings (Ambig-SWE, ICLR 2026). AI fills specification gaps with its own assumptions,
leading to "assumption drift" where earlier decisions silently shift as complexity grows
(Bockeler, Thoughtworks).

**Example**: interview.py's 5 categories (Objective, Context, Constraints, References,
Success Criteria) represent the minimum. The interview skill extends this with scope
classification, acceptance criteria in GIVEN/WHEN/THEN format, and domain-adaptive questions.

**Override**: Well-specified bug fix with clear reproduction steps and expected behavior
already documented. Pure refactoring with no behavior change. Tasks where acceptance
criteria are self-evident from the code change (e.g., "rename method X to Y").

**Test**: "Can I write a test that proves this feature is 'done'?" If not, acceptance
criteria are missing. Gather them before planning implementation.

**Priority**: After Safety (P1), before Evidence (P5). Without specifications, evidence-based
decisions have nothing to be evidence about.

---

## Principle 13: Confidence-Based Escalation

**Default**: When confidence in understanding the user's intent is below "high", ask
clarifying questions rather than making assumptions. Document confidence level for each
major decision.

**Rationale**: AI fills specification gaps with its own assumptions. A `priority: String`
field lacking specified values led a model to independently choose "1", "2", "3" then
silently change to "low", "medium", "high" in later iterations (Bockeler, Thoughtworks).
The cost of a wrong assumption that requires a rewrite far exceeds the cost of one
clarifying question.

**Example**: In non-interactive mode, use the structured assumption log format:
`ASSUMPTION: [what was assumed]. CONFIDENCE: [high/medium/low]. IF WRONG: [what would
need to change].` Low-confidence assumptions should be flagged prominently.

**Override**: In non-interactive mode where human input is unavailable — document assumptions
with the structured format and proceed. Also when the decision is easily reversible (a tweak,
not a rewrite) regardless of confidence.

**Test**: "If I'm wrong about this assumption, would it require a rewrite or just a tweak?"
If rewrite, ask. If tweak, proceed but document.

**Priority**: After Safety (P1), tied with Specification Completeness (P12). Both address
the "do we know enough to proceed?" question from different angles.

---

## Principle 14: Domain-Adaptive Questioning

**Default**: Adapt the depth and categories of clarifying questions based on the domain
being worked in. Different domains have different "gray areas" where ambiguity is most
costly.

**Rationale**: GSD's domain-adaptive approach (different questions for APIs vs. UIs vs.
content systems) outperforms generic question checklists. A 40+ question comprehensive
interview causes fatigue; 8-12 domain-targeted questions are more effective. The dimensions
that matter most vary by domain.

**Examples**:

- **Backend/APIs**: Timeout budgets, backwards compatibility, error response design,
  pagination strategy
- **Data Pipelines**: SLO targets, data freshness requirements, schema evolution strategy,
  data quality thresholds
- **ML Models**: Evaluation metrics and minimum thresholds, training data source and
  freshness, serving latency requirements, model versioning

**Override**: Pure infrastructure or refactoring tasks where no user-facing behavior changes.
Tasks where the domain is already well-specified in the ticket or research document.

**Test**: "Have I asked domain-appropriate questions, or am I using a one-size-fits-all
checklist?" If the questions would be the same regardless of whether this is a backend
service or a data pipeline, the questioning isn't domain-adapted enough.
