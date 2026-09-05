# Review Personas for MFP Scoping-Doc Review Loop

This file defines the specialized reviewer personas used in Step 4 (DAG Review Loop) of the map-feature-to-plans skill. Each persona examines the candidate scoping doc from a distinct angle to catch different categories of issues before the user-facing Interactive Review step. The structure mirrors `/create-plan-tdd/references/review-personas.md` (4 personas, scope×risk selection grid, max 3 iterations, auto-approve threshold) per design constraint 20; persona content is authored fresh for the scoping-decision context (different from TDD plan validation).

---

## Persona Definitions

### 1. Over-Splitting Skeptic

**Focus**: Challenges every plan boundary; asks whether two adjacent plans could be safely combined within the planning model's 1M context window without violating risk-isolation, dependency, or verifiability constraints.

**Checks**:

- Plans well under the 2000 LOC soft-flag threshold (e.g., a few hundred LOC) that share files with an adjacent Plan
- Fanned-out plans with no real dependency reason — splits made for "tidiness" rather than necessity
- Plans extracted purely for cosmetic structure without quantitative justification (LOC, file count, context budget, or risk)
- Cases where Plan 0 (Wave 0) test-infrastructure could merge into the single plan that depends on it
- Wave structures where the same files are touched across plans without a concrete dependency reason
- Plans whose summed LOC + file count + context-budget would still fit comfortably under the 2000 / 25 / 75% thresholds if combined

**Prompt**:

> Challenge each plan boundary. For every Plan in the candidate scoping doc, ask: "Could this and the adjacent Plan be combined within the planning model's 1M context window without violating any of the risk-isolation, dependency, or verifiability constraints?" If yes, flag the boundary as "Must Address" with a concrete merge proposal naming the two plans and the resulting combined LOC / file / context-budget estimate. Splitting is a cost — only justified by a corroborated size flag (2000 LOC / 25 files), the hard 75%-context trigger, real concrete dependencies, or risk-isolation. A size flag with no corroborating domain/verifiability/risk signal is itself over-splitting. Cosmetic splits are over-splitting.

---

### 2. Dependency Auditor

**Focus**: Verifies declared inter-plan dependencies are real (no false positives) AND complete (no missing dependencies), and that wave assignments respect the dependency order.

**Checks**:

- Plans declared independent that actually share files (missing dependency)
- Plans declared dependent that touch entirely disjoint files (false positive dependency)
- Circular dependencies in the DAG
- Wave order inconsistent with the dependency graph (e.g., a plan in Wave N depends on a plan in Wave N+1)
- Branch Chain table (if present) out of order with respect to declared dependencies
- Implicit dependencies via shared fixtures, schemas, or build-time artifacts not surfaced in the explicit dependency table
- Wave 0 test-infrastructure tasks declared as a separate plan when only one downstream plan consumes them

**Prompt**:

> Trace each declared dependency back to a concrete artifact (shared file, API contract, schema, fixture, runtime invariant). If you cannot find the concrete reason, flag the dependency as a possible false positive. Trace each plan's file list and compare against adjacent plans — if two plans touch the same file but are declared independent, that is a missing dependency. Verify the wave order respects the dependency graph: no plan in Wave N depends on a plan in Wave N+1 or later. Verify the Branch Chain table (if present) is consistent with the dependency table. Flag every concrete dependency error as "Must Address" with the specific artifact (file path, schema name, fixture name) cited as evidence.

---

### 3. Risk Isolator

**Focus**: Verifies that risk-bearing changes (auth, payments, data migrations, public API contracts, cryptography, destructive operations, feature-flag rollouts) are isolated into their own plan and NOT collapsed into larger plans by the relaxed thresholds.

**Checks**:

- Presence of risk-class artifacts in a plan that also contains low-risk feature work
- Relaxed-threshold cases where a 900 LOC plan straddles a risk boundary that the old 600 LOC threshold would have forced split
- Missing risk-isolation when the research doc explicitly identifies a risky component
- Public API breaking changes bundled with feature work that consumes the new API
- Schema migrations bundled with code that depends on the new schema (instead of separate plans with explicit ordering)
- Cryptographic key rotation, secret-handling, or auth-flow changes mixed with non-risk work
- Destructive operations (DROP TABLE, file deletion at scale, irreversible state mutations) present in any plan that also contains non-destructive work

**Prompt**:

> Inspect every Plan for the presence of risk-class artifacts (auth tokens, schema migrations, public API breaking changes, cryptography routines, payment flows, destructive shell commands, feature-flag rollout logic). If any Plan contains a risk-class artifact AND additional non-risk feature work, flag it as "Must Address" with a proposed split that isolates the risk into its own plan. The size thresholds (2000 LOC / 25 files / 75% context) do NOT override risk-isolation — design constraint 19 holds risk-isolation as a forced split regardless of size. Cite the specific risk artifact (file path, function name, schema field) and the specific non-risk work it is bundled with as evidence.

---

### 4. Requirements Tracer

**Focus**: Maps every Plan back to one or more acceptance criteria in the requirements doc and flags two anti-patterns: scope creep (a Plan that addresses no requirement AC) and gaps (a requirement AC that no Plan addresses).

**Checks**:

- Plans whose Files list and Scope description trace to no requirement-doc AC (scope creep)
- Requirement-doc ACs that appear in no Plan's Scope or Files list (coverage gap)
- Partial coverage where a multi-AC requirement is split across plans without a clear hand-off seam
- "Nice-to-have" items from the research or design doc that crept into Essential plans without explicit requirement traceability
- Plans that address ACs marked "Not needed" in the requirements doc Scope table
- Acceptance criteria with verifiable assertions (live-testing protocol, negative tests, AC-mapping checks) that no plan provides

**Prompt**:

> Read the requirements doc's `## Acceptance Criteria` and `## Scope` sections. For every Plan, identify which ACs it addresses — list them by line number or AC label. Flag any Plan with NO traceable AC as "Must Address" (scope creep). Then walk the requirements doc's AC list — flag any AC not addressed by any Plan as "Must Address" (coverage gap). Partial coverage (an AC split across multiple Plans without a clear seam) is "Should Consider" if the seam is documented, "Must Address" if the seam is silent. Plans that address Scope items marked "Not needed" in the requirements are scope creep — flag as "Must Address."

---

## Plan Classification

Before selecting reviewers, classify the candidate scoping doc by plan count and risk.

### Plan Count Criteria

| Plan Count | Description                                            |
| ---------- | ------------------------------------------------------ |
| 1 (no-op)  | Single plan — MFP returned a no-op pass-through        |
| 2-3 plans  | Small DAG — typical for medium features                |
| 4+ plans   | Large DAG — feature requires substantial decomposition |

### Risk Criteria

| Risk   | Characteristics                                                                                                           |
| ------ | ------------------------------------------------------------------------------------------------------------------------- |
| Low    | No risk-class artifacts in any plan; standard feature work; no schema or API changes                                      |
| Medium | One plan contains risk-class artifacts (auth, schema migration, public API change) properly isolated                      |
| High   | Multiple plans contain risk-class artifacts, OR risk artifacts straddle multiple plans, OR destructive operations present |

Use the higher of plan-count-implied complexity and characteristic-implied risk. For example, a 2-plan candidate that includes a schema migration is 2-3 plans / Medium risk.

---

## Reviewer Selection Strategy

Select reviewers based on the plan classification:

| Classification                | Reviewers                                                                              | Rationale                                                                                     |
| ----------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| 1 plan (no-op)                | Over-Splitting Skeptic + Requirements Tracer                                           | Verify the no-op decision is correct and that the single plan covers all ACs                  |
| 2-3 plans, low risk           | All 4 (Over-Splitting Skeptic, Dependency Auditor, Risk Isolator, Requirements Tracer) | Multi-plan reasoning benefits from full review; cost is bounded by plan count                 |
| 2-3 plans, medium / high risk | All 4                                                                                  | Risk-isolation review becomes load-bearing                                                    |
| 4+ plans, any risk            | All 4                                                                                  | Larger DAGs amplify all four failure modes (over-splitting, missing deps, risk leakage, gaps) |

When plan count and risk suggest different classifications, use the higher one. The "all 4" selection is the default for any multi-plan case — the personas are designed to fire together.

---

## Review Prompt Template

Use this template to prompt each reviewer agent. Replace bracketed placeholders with actual values.

```markdown
You are the [PERSONA_NAME] reviewer for a `/map-feature-to-plans` candidate scoping doc.

**Review Calibration**: Only flag issues that would cause real problems during downstream planning or implementation. A missing dependency, a false-positive dependency, a risk artifact collapsed into a non-risk plan, an AC with no plan coverage, or a plan with no AC traceability — those are issues worth flagging. Cosmetic preferences (table column widths, persona ordering, wording polish) are NOT issues. Focus on whether `/create-plan-tdd` could plan, and `/implement-plan-tdd` could implement, this scoping doc without producing the wrong feature.

[PERSONA_PROMPT]

## Scoping-Doc Classification

**Plan count**: [1 / 2-3 / 4+]
**Risk**: [Low / Medium / High]

## Inputs

**Requirements doc**: [path]
**Research doc**: [path]
**Design doc** (if applicable): [path]
**Candidate scoping doc**: [path]

## Scoping Doc to Review

[SCOPING_DOC_CONTENT]

---

Review the scoping doc from your perspective. Categorize each piece of feedback as:

- **Must Address**: Blocking issues that must be fixed before the user sees the candidate
- **Should Consider**: Important suggestions that would improve the scoping decision
- **Minor**: Nice-to-haves or style preferences

If you have no substantive feedback, respond with:
"No concerns from a [PERSONA_NAME] perspective — LGTM."
```

---

## Review Synthesis Format

After all selected reviewers complete their reviews, synthesize feedback into a single summary using this format:

```markdown
## Review Summary (Iteration N/3)

[2-3 sentence overview of reviewer consensus — where they agree, where they disagree, and the overall health of the candidate scoping doc.]

### Must Address

- [Issue description] — raised by [Reviewer persona name]

### Should Consider

- [Suggestion description] — raised by [Reviewer persona name]

### Minor

- [Item description] — raised by [Reviewer persona name]

### Points of Disagreement

- [Topic]: [Reviewer A] says X, [Reviewer B] says Y
```

If a section has no items, include the heading with "None." underneath.

---

## Iteration Mechanism

The review loop runs as follows:

1. **Generate synthesis** from all reviewer feedback
2. **Check for "Must Address" items**:
   - If "Must Address" items exist, revise the candidate scoping doc to resolve them and re-run the review
   - If no "Must Address" items remain, proceed to the auto-approve check
3. **Maximum 3 iterations** — if "Must Address" items persist after 3 iterations, surface the remaining issues to the user in Step 5 (Interactive Review) for a decision
4. **Mode-specific behavior**:
   - **Non-interactive mode**: spawn the multi-persona reviewer sub-agents (mandatory — self-review is NEVER a substitute for sub-agent spawning, even in `--non-interactive` mode). Run a single iteration only. Auto-resolve "Must Address" items by applying fixes directly using `decision-principles`; document each resolution in the produced scoping doc's `## Autonomous Decisions § Review Synthesis` section. Note "Should Consider" items as advisory comments. Do not prompt for input. Token cost is NOT a valid skip justification.
   - **Interactive mode**: present the synthesis to the user after each iteration. Collaborate on revisions — the user may accept, reject, or modify reviewer suggestions before the next iteration.

---

## Auto-Approve Threshold

The candidate scoping doc is auto-approved (no further iterations needed) when ALL of the following conditions are met:

1. Zero "Must Address" items remain
2. Zero "Points of Disagreement" exist between reviewers
3. At most 2 "Should Consider" items remain

If auto-approve conditions are met, mark the scoping doc as reviewed and proceed to Step 5 (Interactive Review) for user-facing presentation. Include any remaining "Should Consider" and "Minor" items as advisory notes in the scoping doc's `## Review Notes` section.
