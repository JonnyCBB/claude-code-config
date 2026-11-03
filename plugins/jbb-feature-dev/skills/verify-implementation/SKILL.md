---
name: verify-implementation
description: >
  Generate reproducible verification evidence against a task objective, acceptance criteria,
  or implementation plan. Produces before/after comparisons, behavioral examples, and
  structured evidence documents at ~/.claude/thoughts/shared/verification/.
  Use when asked to "verify the plan", "generate verification evidence", "run verification",
  or verify an implementation. No formal plan, polish step, or commit is required.
---

# Verify

Generate reproducible evidence that an implementation meets its objective and acceptance criteria.

## Step 1: Establish the Verification Contract

Use the supplied plan, task objective, and acceptance criteria. A formal plan is not required.
If no source was supplied, inspect branch-linked plan references and task context; ask only if the objective remains unknown.
Read the source completely. Confirm it belongs to this repository and task, not merely the newest file with a similar topic.
In the steps below, "plan" includes the task objective and acceptance criteria; map outcomes by meaning when headings differ.
Record the repository root, branch, target branch, base commit, and current head. Include uncommitted changes in the verified diff.
Use the existing evidence document to record the actual assessor, input state, instructions actually read, and evidence.
Do not claim that earlier evidence verifies edits made after its capture.

Honor any caller requirement for independent assessment. An independent assessor does not implement the changes it verifies.
If this skill already runs in a fresh assessor worker, perform verification there; do not spawn another verifier solely for independence.
Otherwise, when independence is required, delegate assessment to a fresh worker with the objective, criteria, repository, base, and working-tree scope.
The implementer's own results can inform that worker, but cannot replace its assessment. Report a blocker if no independent worker is available.

If a requirements doc path is provided (via `--requirements <path>` or as a second argument),
read it fully. The requirements doc is optional — if not provided, skip all
requirements-based verification (Steps 2b, 4b, and the Requirements Alignment section
in the evidence document).

## Live Testing Philosophy

Verify the changed behavior directly through a relevant local interface. For a service,
start it locally and call the changed endpoint. For UI changes, use a browser against the local application.
For a library, run a focused executable example or behavioral test with actual inputs and outputs.
For documentation or build-only changes, inspect the changed instructions or run the relevant local build or validation command;
do not start an unrelated service.

Keep verification local-only, including dependencies. Use existing local fixtures, fakes,
or emulators where appropriate, and state what they do not verify. Do not call deployed
or production services as a workaround. Do not copy secrets or weaken authentication automatically.

Record commands, expected outcomes, actual output, and reproducible setup and cleanup.
If a required local check cannot run, record the exact blocker and the criterion left unverified.
An unavailable check is not a passing check.
Before declaring an environmental blocker, trace the actual error through the local code and configuration.
Missing implementation is FAIL, not an unavailable prerequisite. A permission denial needs the exact error
and a request for the missing user action, not an assumption that verification is impossible.
When a fix addresses a failed live scenario, repeat that scenario's setup, inputs, and action locally;
a passing unit test alone does not confirm timing, state, or event-ordering behavior.

## Step 2: Parse Plan for Testable Assertions

Read the plan and extract testable assertions from these sections:

- `## Overview` — high-level objective (used for objective alignment in Step 4)
- `## Desired End State` — specific numbered outcomes with verification criteria
- `### Verification:` or equivalent heading under Desired End State — explicit checks, often with commands
- `### Success Criteria:` per phase — split into:
  - `#### Automated Verification:` — machine-executable commands (e.g., `mvn compile`, `test -f <path>`)
  - `#### Manual Verification:` — human-observable outcomes
- `## Testing Strategy` — test scenarios, edge cases, integration tests
- `## What We're NOT Doing` — negative assertions (verify these didn't happen)

Categorize extracted assertions as: command-based, behavioral, structural, or negative.
Structural outcomes include reuse, simpler control flow, naming, and comment changes; inspect them against their stated objective.

## Step 2b: Parse Requirements for Verifiable Criteria (if requirements doc provided)

If a requirements doc was provided in Step 1, extract verifiable criteria from:

- `## Acceptance Criteria` — GIVEN/WHEN/THEN scenarios (highest priority — user-confirmed
  before implementation began)
- `## Success Criteria` — measurable outcomes
- `## Scope` — Essential/Nice-to-have/Not needed classification
- `## Non-Functional Requirements` — latency budgets, throughput targets

Categorize each criterion by verification method:

- **Live-testable**: Can be verified by sending a request and inspecting the response
  (e.g., GIVEN a search query WHEN the user submits THEN results contain X)
- **Code-inspectable**: Can be verified by examining code changes
  (e.g., "uses the existing AbstractHandler base class")
- **Metric-observable**: Requires production data or load testing to verify
  (e.g., "P99 latency < 200ms") — mark as DEFERRED with explanation

## Step 3: Analyze Code Changes

Use the base commit recorded in Step 1, honoring any task-supplied base. If no base was
supplied, establish it from the task's actual target branch and record the resolved commit;
ask if the target is ambiguous. Do not assume `origin/master` or silently substitute another base.

Compare that commit directly with the current working tree, not only with HEAD or a
three-dot committed diff. Git's diff against a commit includes tracked staged and unstaged
changes. Inspect repository status and separately list and read relevant untracked files,
which Git diff does not include. Record excluded unrelated files and why they are outside
this task. Include modified, added, and deleted files in the scope summary.

Record the actual comparison commands and working-tree state with the evidence. If that
state changes during verification, identify affected checks and rerun them.

## Step 4: Objective Alignment Check

Compare the code changes (Step 3) against the plan's Overview and Desired End State (Step 2).

For each desired end state item:

- Identify the implementation evidence (file paths, code changes)
- Mark implementation alignment as PASS (evidence exists), FAIL (contradictory evidence), or GAP (missing/partial).
  This is not a behavioral verdict; link required execution evidence before claiming verification PASS.

Flag any **drift** — code changes that don't map to any plan item.
Flag any **gaps** — plan items without corresponding implementation.

Independently check ALL recorded review and simplification candidates against the final diff and evidence,
including applied, rejected, filtered, duplicate, skipped, and blocked outcomes, not only admitted findings.
Check each outcome's reason: an evidence-backed invalid premise or inapplicability can justify rejection;
low priority alone cannot justify leaving a valid, safe, in-scope recommendation unapplied.
Verify structural outcomes by source inspection as well as runtime outcomes by direct local checks.
Keep unsafe fixes and unresolved design/scope decisions blocked, without weakening tests or contracts.
Record this assessment in the existing objective alignment/evidence sections. Unresolved required recommendations,
material concerns, or required coverage gaps prevent PASS, even when no bug finding is admitted.

## Step 4b: Requirements Alignment Check (if requirements doc provided)

For each acceptance criterion from Step 2b:

1. **Find implementation evidence** — file paths, code changes that implement this criterion
2. **Map to live test scenario** — if Step 8 (Live Service Testing) applies, identify which
   test scenario(s) will directly verify this criterion. A live test that exercises the
   GIVEN/WHEN/THEN path is stronger evidence than code inspection alone.
3. **Assign status**:
   - PASS: Direct local evidence meets the criterion; inspection alone suffices only for an inspection-based criterion
   - FAIL: Observed behavior contradicts the criterion
   - GAP: Missing or partial evidence, including required behavior supported only by code inspection
   - BLOCKED: A required local check cannot run; include its exact prerequisite or error
   - DEFERRED: Cannot be verified locally (e.g., requires production metrics); do not send production requests

For scope items:

- **Essential**: Must have PASS status
- **Nice-to-have**: PASS or not implemented (verify no over-building)
- **Not needed**: Must NOT be implemented (negative assertion)

## Step 5: Domain Detection

Follow the detection procedure in `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` — check changed file names/paths against file triggers first, then check content for strong and corroborating signals.

For v1, the following domains produce verification examples:

- **Backend API** — gRPC/REST services with request/response verification
- **Infrastructure/Skills** — file existence, content matching, command output verification

Use the changed behavior, not the domain label, to select the relevant local interface
in Step 8. A runnable service elsewhere in the repository does not make service testing relevant.

## Step 6: Verification Strategy Selection

Based on plan content, determine which example types to include:

| Type                     | When to Include                                                                                                                        | Minimum                                                                               |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **Happy Path**           | Always                                                                                                                                 | 1 per desired end state item                                                          |
| **Before/After**         | Filtering, removal, transformation, behavioral changes                                                                                 | As warranted                                                                          |
| **Edge Cases**           | Special inputs, boundary conditions, format variations                                                                                 | As warranted                                                                          |
| **Failure Modes**        | Error handling, timeouts, retries, fallbacks                                                                                           | As warranted                                                                          |
| **Direct Local Verification** | Always, using an interface relevant to the change | Service request, local browser interaction, executable library example, or relevant document/build validation |
| **Regression**           | Relevant existing checks | Select suites that cover the affected behavior; record blockers |

Use agent judgement to determine relevance — do not rely on rigid keyword matching.

Document the selected strategy and rationale in the evidence document.

## Step 7: Execute Automated Verification

Collect the required local commands from the plan's automated verification sections and existing formatter/lint checks.
Use `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/language-agent-registry.md` to identify relevant existing test
suites from changed languages and test files. Deduplicate overlapping commands and scenarios
across Steps 7–9; reuse results from the same verified state rather than rerunning suites.

Run the selected commands and record their output, exit status, and expected result.
If a command fails, capture the error and continue with independent checks. Attribute the
failure to the change or establish an independent cause before calling it unrelated.
A successful test count alone does not demonstrate the changed behavior; retain the
scenario-level evidence required in Step 9.

## Step 8: Live Service Testing

Start a local service when its changed behavior requires request/response verification.
For other changes, use the relevant local interface defined in Live Testing Philosophy
and Step 9. Record the selected interface and rationale; do not substitute an unrelated endpoint.

For service checks, read `references/live-testing-guide.md`. Start the service yourself
using the repository's documented local setup. Verify dependencies are local before sending requests.

### Direct Testing Requirement

The new or modified RPC/endpoint from the PR MUST be tested directly — not via a
different, pre-existing endpoint as a proxy. Testing `SendMessage` to "validate the
underlying dependencies" when the PR adds a `Search` RPC does not verify the new code
path and produces misleading evidence.

If local startup is blocked, inspect the error and documented local test setup.
Use an existing in-process integration test or local fake only if it exercises the changed
behavior directly. Record its limits, especially any untested transport or authentication behavior.
Do not copy secrets, change global credentials, weaken authentication, or route to remote services.
If no safe local route exists, report the exact error, attempted local remedies, and unverified
criteria as BLOCKED. Ask for the missing prerequisite when user action is required; continue
independent checks without claiming that they replace the blocked check.

### Phase 1: Service Startup

1. Inspect documented local configuration, authentication, and dependency targets.
2. Detect the relevant build target and entry point.
3. Build only if an earlier check has not already produced the required artifacts.
4. Start the service locally; retain its process handle and logs.
5. Check readiness with a bounded timeout using the service's documented local interface.
6. On failure, inspect the error and safe local remedies in the guide. Record a behavior
   failure as FAIL or an unavailable prerequisite as BLOCKED, then continue independent checks.

### Phase 2: Test Scenario Generation

1. Re-read plan objectives — every scenario maps to a desired end state item
2. Proto analysis — identify request/response fields
3. Handler analysis — identify branches, toggles, degradation paths
4. Generate scenario matrix (Happy path, Full input, Field omission, Feature toggle,
   Mixed list items, Error input, Graceful degradation, Before/After)
5. Interactive: confirm scenarios with user. Non-interactive: log and proceed.

### Phase 3: Execute Scenarios

- Before/After scenarios: capture after in the unchanged feature checkout, then capture before
  in a separate baseline worktree at the recorded base commit. Follow the guide's isolation procedure.
- Standard scenarios: construct request → send → capture response → validate (objective alignment, field presence, values) → record PASS/FAIL

### Phase 4: Record Results and Cleanup

- Stop only the service processes started for verification, using retained process handles.
- Preserve feature checkout changes and report retained baseline worktrees; deletion requires explicit authorization.
- Format: summary table + expandable details per scenario (see output-template.md)

## Step 9: Execute and Record Verification Examples

For each example type selected in Step 6, reuse existing repository commands and evidence
from Steps 7–8. Execute only missing scenarios. Record each unique execution once and link
it to every criterion it covers. Rerun only when the verified state changes or a check needs confirmation.
After later fixes, independently refresh affected candidate conclusions and scenarios, including structural outcomes;
do not rerun the entire implementation/review chain. Reuse unaffected evidence with its original provenance.

A wrapper script is optional. Create one outside the repository only when existing commands
cannot express the required sequence clearly. Do not use `references/script-template.sh`.
If needed, record its path and full reproduction commands. It must retain actual command
output and exit status, compare results with explicit expectations, list failed and blocked
checks, and return nonzero for any required failed, blocked, or missing check.

Zero required checks executed cannot produce PASS, even when a command or wrapper exits zero.
Record this as PARTIAL with the missing coverage. PASS requires every required criterion to
have relevant passing evidence, not merely a successful command exit.

### Before/After Examples

Read `references/domain-strategies.md` for domain-specific before/after procedures:

- **Infrastructure/Skills**: Compare file contents and command outputs between base and feature branch
- **Backend API**: Capture local responses in the feature checkout and isolated baseline worktree

### Happy Path / Edge Cases / Failure Modes

- **Infrastructure/Skills**: Execute relevant commands and capture output
- **Backend API**: Send requests to the running service and capture responses

### Per-Check Recording

For each scenario, connect the objective to precise setup, inputs, action, expected output, and observed output.
Cover relevant boundary, failure, and unchanged-behavior scenarios as well as the happy path.
For coupled calculations, include accepted inputs where their limits differ; check that their advice remains consistent.
For libraries without a runnable service, execute the changed behavior through a focused example or behavioral test.
Include its actual input and output, not only a test name or pass count.
A reviewer must understand what the evidence proves without opening the code or a local report.
Distinguish observed results from expectations, code inspection, and unverified claims.

For each check, record in the evidence document (and optional wrapper output):

- **Description** — natural language sentence: what scenario is being verified
- **Expected outcome** — what success looks like
- **Command** — exact command executed and working directory; for UI checks, include browser actions and local URL
- **Actual result** — observed output and exit status, or browser observations and screenshots, with sensitive values explicitly redacted
- **Verdict** — PASS/FAIL/BLOCKED with the description repeated for identification

## Step 10: Generate Evidence Document

Write the evidence document to:
`~/.claude/thoughts/shared/verification/YYYY-MM-DD-description.md`

Create the directory if needed:

```bash
mkdir -p ~/.claude/thoughts/shared/verification
```

Follow the template in `references/output-template.md`. The document includes:

- Header with objective/criteria/plan source, repository root, branch, target branch, recorded base, head, working-tree scope, and date
- Task objective and acceptance criteria (from the supplied source)
- Actual assessor, independence when required, input state, instructions actually read, and evidence
- Verification strategy (from Step 6)
- Objective alignment results table, including every recorded candidate outcome and remaining concerns/coverage limits (from Step 4)
- Automated verification results table (from Step 7)
- All verification examples with assertions (from Step 9)
- Test suite results table
- Negative assertions (from "What We're NOT Doing")
- Summary table with category counts
- Verdict: **PASS** only when all required criteria have passing evidence and at least one required check executes;
  **FAIL** when a required check demonstrates incorrect behavior; otherwise **PARTIAL** for blocked, deferred, or missing coverage
- Reproduction instructions using exact existing commands, with an optional wrapper only when needed
- Actual inputs and outputs for direct behavioral checks, including local request/response transcripts for service scenarios

## Step 11: Report Results

Write the user-facing report in ASD-STE100 Simplified Technical English (STE). Give findings first, then open questions.
Use active voice, one idea per sentence, at most 20 words per instruction and 25 per description.
Define technical terms on first use. Keep paths, identifiers, and verbatim output exact.

Present to the user:

- The verdict (PASS / FAIL / PARTIAL) and its meaning for the task objective
- Summary table from the evidence document
- Path to the full evidence document
- If any FAIL: highlight what needs attention and suggest next steps
- If PARTIAL: list what passed and what remains

## Reference Files

- **Output template**: `references/output-template.md` — full evidence document structure with all sections
- **Domain strategies**: `references/domain-strategies.md` — domain-specific verification procedures for Infrastructure/Skills and Backend API domains
- **Live testing guide**: `references/live-testing-guide.md` — detailed procedures for service startup, auth, scenario generation, request construction, response validation, and result formatting
