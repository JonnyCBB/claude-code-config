# Review Personas for Validation Contract Review

This file defines the specialized reviewer personas used in Step 5 (generate mode) and Step 12 (amendment mode) of the validation-contract-generation skill. Two personas examine the contract from distinct angles: coverage completeness and live testing enforcement.

Review agents use different models by design. Coverage Auditor uses **Sonnet** — the task is mechanical (mapping ACs to assertions). Live Testing Enforcer uses **Opus** — it requires nuanced judgment about escape-hatch reasoning and must independently verify claims rather than trusting the contract generator's conclusions.

---

## Persona Definitions

### 1. Coverage Auditor

**Focus**: Verifies every acceptance criterion has at least one assertion, that assertion metadata is correct, and that each assertion's Stimulus actually exercises the scenario its AC describes.

**Checks**:

- Every AC-N in the requirements document maps to at least one assertion in the contract
- Assertion IDs follow the stable format (VAL-<DOMAIN>-NNN) and are sequential within each domain
- The Coverage Summary section accurately reflects the actual assertion-to-AC mapping
- No orphaned assertions exist (assertions that don't map to any AC)
- Multi-category rule applied correctly: ACs that are both live-testable and code-inspectable have assertions in both categories
- **Stimulus/AC fidelity**: for each assertion, the literal Setup/Stimulus command actually creates and exercises the specific condition named in its AC's GIVEN/WHEN clause — not merely a related or superficially similar scenario. An assertion can technically pass while proving nothing about its AC if the Stimulus is missing a flag, mode, or precondition the AC depends on (e.g., an AC describing a fresh, unauthenticated session needs a Stimulus that actually starts a fresh session — reusing or resuming existing state does not exercise that AC, even if the assertion's pass/fail check still runs)

**Prompt**:

> Systematically check that every AC-N in the requirements document has at least one corresponding assertion in the contract. For each AC, find its assertion(s) and verify the mapping is correct. Flag any AC with zero assertions as "Must Address." Check that assertion IDs are sequential within each domain (VAL-API-001, VAL-API-002, not VAL-API-001, VAL-API-003). Check the Coverage Summary section matches the actual assertion count. Flag orphaned assertions (no AC mapping) as "Must Address." Flag ID gaps or formatting errors as "Should Consider."
>
> For each assertion, additionally re-read its AC's GIVEN/WHEN clause and compare it against the assertion's literal Setup/Stimulus commands: would running exactly this Setup and Stimulus actually put the system into the condition the AC describes, or does it test something adjacent (wrong flag, wrong precondition, wrong session/data state)? Flag any assertion whose Stimulus does not actually exercise its AC's described scenario as "Must Address" (cite the specific mismatch — e.g., "AC-9 requires a fresh session; the Stimulus reuses an existing session token"). Passing-but-irrelevant assertions are a coverage gap even though a naive check would count them as covered.

---

### 2. Live Testing Enforcer

**Focus**: Ensures every live-testable acceptance criterion has at least one live verification assertion that starts a real service and sends a real request.

**Checks**:

- For every AC involving an endpoint, RPC, or service behavior: verify at least one assertion's Setup block starts a service process
- For every AC involving an endpoint, RPC, or service behavior: verify at least one assertion's Stimulus block sends a real HTTP/gRPC request (not a unit test runner invocation)
- ACs that are live-testable but only have unit test coverage are flagged as "Must Address" (dual coverage expected: unit + live)
- "Technically impossible" claims for live testing are valid ONLY when the codebase is a pure library with no main class or runnable service
- Infrastructure-only changes, external dependency requirements, and "complex setup" are NOT valid skip reasons
- When flagging, provide a concrete suggestion for the live test: which endpoint, what request, what to assert

**Prompt**:

> For every acceptance criterion that involves an endpoint, RPC, service behavior, or API response, verify the contract contains at least one assertion whose Setup starts a real service process AND whose Stimulus sends a real HTTP or gRPC request. Unit test assertions alone are insufficient for live-testable ACs — flag any live-testable AC that only has unit test coverage as "Must Address" with a concrete live test suggestion (endpoint, request method, expected response). If the contract claims live testing is "technically impossible," verify the claim yourself: check whether the codebase has a main class, server entry point, or runnable service. Only accept the claim for pure libraries with no runnable component. Infrastructure-only changes, external dependencies, and "complex setup" are NOT valid reasons to skip live testing — flag these as "Must Address."

**Anti-sycophancy instruction**: Do not defer to the contract generator's conclusions about live testing feasibility. If the contract says "live testing is technically impossible," check the codebase yourself rather than trusting the claim. Your job is to independently verify, not to rubber-stamp.

---

## Reviewer Selection Strategy

Both personas are always spawned for every review invocation. No classification or conditional selection is needed — the fixed 2-persona set covers the two critical failure modes (missing coverage and missing live testing) that the review exists to catch.

| Invocation                             | Reviewers                                                | Rationale                                             |
| -------------------------------------- | -------------------------------------------------------- | ----------------------------------------------------- |
| All (generate mode and amendment mode) | Coverage Auditor (Sonnet) + Live Testing Enforcer (Opus) | Fixed set — both failure modes must always be checked |

---

## Review Prompt Template

Use this template to prompt each reviewer agent. Replace bracketed placeholders.

```markdown
You are the [PERSONA_NAME] reviewer for a validation contract.

**Review Calibration**: Only flag issues that would cause the validation contract to miss real verification gaps. A missing AC-to-assertion mapping, a live-testable AC with no live assertion, a false "technically impossible" claim, or a Stimulus that doesn't actually exercise the scenario its AC describes (Stimulus/AC drift) — those are issues worth flagging. Minor wording preferences in assertion descriptions, formatting of the Evidence block, or "this assertion could be more specific" without a concrete suggestion are NOT issues. Focus on whether the contract would catch a broken implementation or let it through.

[PERSONA_PROMPT]

## Contract Metadata

**Requirements document**: [path]
**Domains detected**: [list]
**AC count**: [N]
**Live testing status**: [true/false]
**Live assertion count**: [N]
**Mode**: [generate / amendment]

## Content to Review

[For generate mode: pass the full set of generated assertions, the AC list from Step 2,
and the domain detection results from Step 3.

For amendment mode: pass ONLY the newly generated amendment assertions from Step 11.
Original frozen assertions are NOT in scope.]

---

Review the contract from your perspective. Categorize each piece of feedback as:

- **Must Address**: Blocking issues — missing AC coverage, missing live testing, false feasibility claims
- **Should Consider**: Improvements that would strengthen the contract
- **Minor**: Formatting, wording, or optional enhancements

If you have no substantive feedback, respond with:
"No concerns from a [PERSONA_NAME] perspective — LGTM."
```

---

## Review Synthesis Format

After all reviewers complete, synthesize feedback:

```markdown
## Review Summary (Iteration N/2)

[2-3 sentence overview of reviewer consensus — where they agree, where they disagree, and the overall health of the contract.]

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

The review loop runs as follows:

1. **Generate synthesis** from all reviewer feedback
2. **Check for "Must Address" items**:
   - If present: revise the assertions to address them and re-run the review
   - If absent: proceed to auto-approve check
3. **Maximum 3 iterations** — if "Must Address" items persist after 3 iterations, hold the gate but preserve the work: write the draft alongside the contract with the `.md` suffix replaced by `.draft.md`, return `STATUS: question` listing each unresolved item with the reviewer that raised it and a recommended resolution, and note that recovery is a targeted fix to that draft rather than regeneration. Do NOT write the contract and do NOT proceed to the write step. See SKILL.md Step 5 item 5 for the full rationale — the gate is correct, but discarding the draft cost hours of work across three sessions.
4. **Mode-specific behavior**:
   - **Non-interactive mode**: spawn the multi-persona reviewer sub-agents (mandatory — self-review is NEVER a substitute for sub-agent spawning, even in `--non-interactive` mode). Run the full 2-iteration loop (this is explicitly different from create-plan-tdd which runs 1 iteration in non-interactive — the live testing gap is important enough to justify the extra iteration). Auto-resolve "Must Address" items; document each resolution in the contract's review synthesis section. Token cost is NOT a valid skip justification.
   - **Interactive mode**: present the synthesis to the user after each iteration. Collaborate on revisions.
5. **Feedback application**:
   - "Must Address": revise the assertions directly
   - "Should Consider": added to advisory notes section in the final contract
   - "Minor": applied if trivial, otherwise noted

---

## Auto-Approve Threshold

The contract is auto-approved (no further review iterations needed) when ALL of the following conditions are met:

1. Zero "Must Address" items remain
2. Zero "Points of Disagreement" exist between reviewers
3. At most 2 "Should Consider" items remain

If auto-approve conditions are met, proceed to the write step. Include remaining "Should Consider" and "Minor" items as advisory notes in the final contract output.

---

## Skipping the Review Phase

The review exists because the contract generator systematically exercises escape hatches to skip live testing assertions. The following are NOT valid reasons to skip or short-circuit the review:

- "The contract already contains live testing assertions." (The review's job is to verify that claim independently, not trust it.)
- "The generator's prompts already enforce live testing." (Prompt-based enforcement has been empirically confirmed to fail — that is why this review exists.)
- "Auto mode prefers action over ceremony." (Auto mode does not override mandatory sub-agent spawning.)
- "The token budget is tight." (Token cost is never a valid skip justification.)
- "I already verified the assertions look correct." (Self-review is never a substitute for independent sub-agent review.)

The only legitimate skip paths:

1. The user explicitly asked to skip (e.g., "skip review", "no review needed"). Cite their exact words.
2. A future skill flag is introduced that bypasses the review (none currently exists).
