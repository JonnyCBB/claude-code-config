---
name: verify-implementation
description: >
  Generate reproducible verification evidence that an implementation plan was correctly
  executed. Produces before/after comparisons, happy path demonstrations, edge case tests,
  and structured evidence documents at ~/.claude/thoughts/shared/verification/.
  Use when asked to "verify the plan", "generate verification evidence", "run verification",
  or at the /verify-implementation step in the workflow after /tidy and /commit.
---

# Verify

Generate reproducible evidence that an implementation plan was correctly executed.

## Step 1: Locate Plan

- If plan path provided as argument, use it
- Otherwise find most recent plan in `~/.claude/thoughts/shared/plans/` matching the current branch topic
- Otherwise check `git log --oneline -20` for plan references
- Otherwise ask user

Read the plan completely before proceeding.

If a requirements doc path is provided (via `--requirements <path>` or as a second argument),
read it fully. The requirements doc is optional — if not provided, skip all
requirements-based verification (Steps 2b, 4b, and the Requirements Alignment section
in the evidence document).

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

Categorize extracted assertions as: command-based, behavioral, or negative.

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

Identify what changed relative to the base branch:

```bash
BASE_BRANCH=$(git merge-base --fork-point origin/master HEAD 2>/dev/null || echo "origin/master")
git diff --name-only $BASE_BRANCH...HEAD
git diff --stat $BASE_BRANCH...HEAD
```

Summarize: files modified, files added, files deleted. Note the scope of changes.

## Step 4: Objective Alignment Check

Compare the code changes (Step 3) against the plan's Overview and Desired End State (Step 2).

For each desired end state item:

- Identify the implementation evidence (file paths, code changes)
- Mark as PASS (evidence exists), FAIL (no evidence), or GAP (partial)

Flag any **drift** — code changes that don't map to any plan item.
Flag any **gaps** — plan items without corresponding implementation.

## Step 4b: Requirements Alignment Check (if requirements doc provided)

For each acceptance criterion from Step 2b:

1. **Find implementation evidence** — file paths, code changes that implement this criterion
2. **Map to live test scenario** — if Step 8 (Live Service Testing) applies, identify which
   test scenario(s) will directly verify this criterion. A live test that exercises the
   GIVEN/WHEN/THEN path is stronger evidence than code inspection alone.
3. **Assign status**:
   - PASS: Verified by live test scenario (strongest) or code evidence (sufficient)
   - FAIL: No evidence found
   - GAP: Partial evidence — code exists but no live test covers it
   - DEFERRED: Cannot be verified locally (e.g., requires production metrics)

For scope items:

- **Essential**: Must have PASS status
- **Nice-to-have**: PASS or not implemented (verify no over-building)
- **Not needed**: Must NOT be implemented (negative assertion)

## Step 5: Domain Detection

Scan changed files for domain patterns.

For v1, only two domains produce verification examples:

- **Backend API** — gRPC/REST services with request/response verification.
  Triggers Step 8 (Live Service Testing) for comprehensive scenario-based testing.
- **Infrastructure/Skills** — file existence, content matching, command output verification

Other detected domains are noted in the evidence document but not actively verified.

## Step 6: Verification Strategy Selection

Based on plan content, determine which example types to include:

| Type                     | When to Include                                        | Minimum                                                                               |
| ------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| **Happy Path**           | Always                                                 | 1 per desired end state item                                                          |
| **Before/After**         | Filtering, removal, transformation, behavioral changes | As warranted                                                                          |
| **Edge Cases**           | Special inputs, boundary conditions, format variations | As warranted                                                                          |
| **Failure Modes**        | Error handling, timeouts, retries, fallbacks           | As warranted                                                                          |
| **Live Service Testing** | Backend API domain detected in Step 5                  | Agent determines count based on code complexity, branching paths, and plan objectives |
| **Regression**           | Always                                                 | Existing test suites must pass                                                        |

Use agent judgement to determine relevance — do not rely on rigid keyword matching.

Document the selected strategy and rationale in the evidence document.

## Step 7: Execute Automated Verification

Run each command from the plan's `#### Automated Verification:` sections across all phases.
Record PASS/FAIL for each with the command output.

Also run test suites identified via `${CLAUDE_PLUGIN_ROOT}/commands/shared/language-agent-registry.md`:

- Detect languages from changed file extensions
- Find test files using the Test File Detection patterns
- Execute the appropriate test commands

If a command fails, capture the error output and continue with remaining commands.

## Step 8: Live Service Testing (Backend API Only)

If Step 5 detected the Backend API domain, execute live service testing. Otherwise skip
to Step 9.

Read `references/live-testing-guide.md` for the full procedure.

The agent starts the service itself — do NOT ask the user to start it.

### Direct Testing Requirement

The new or modified RPC/endpoint from the PR MUST be tested directly — not via a
different, pre-existing endpoint as a proxy. Testing `SendMessage` to "validate the
underlying dependencies" when the PR adds a `Search` RPC does not verify the new code
path and produces misleading evidence.

If the service cannot be started locally (e.g., missing secrets, infrastructure
dependencies):

1. **Investigate and resolve** — common blockers have known solutions (see
   "Common Local Startup Blockers" in `references/live-testing-guide.md`):
   - PubSub → run `gcloud beta emulators pubsub start`
   - Service auth → disable auth enforcement for local testing
   - Service discovery → configure service domain for local environment
2. **If unresolvable**, stop and ask the user:
   - Explain what is blocking direct testing
   - Propose workarounds (e.g., testing a related endpoint, calling the deployed
     service if the branch is deployed)
   - Get explicit confirmation before proceeding with any workaround
3. **If a workaround is used**, the evidence document MUST:
   - Label the section "Live Service Testing (Workaround)" not "Live Service Testing"
   - State clearly what was tested and why it is NOT a direct test of the new code
   - Explain what the workaround does and does not verify
   - List what remains unverified and would need direct testing post-deploy

### Phase 1: Service Startup

1. Auth pre-flight check (ADC, service account impersonation)
2. Detect build system and Main class
3. Build the project
4. Start the service as a background process
5. Poll for readiness (up to 60 seconds via gRPC health check)
6. On failure: capture error, record as FAIL, proceed to Step 9

### Phase 2: Test Scenario Generation

1. Re-read plan objectives — every scenario maps to a desired end state item
2. Proto analysis — identify request/response fields
3. Handler analysis — identify branches, toggles, degradation paths
4. Generate scenario matrix (Happy path, Full input, Field omission, Feature toggle,
   Mixed list items, Error input, Graceful degradation, Before/After)
5. Interactive: confirm scenarios with user. Non-interactive: log and proceed.

### Phase 3: Execute Scenarios

- Before/After scenarios: capture after → checkout base → build → start → capture before → compare → return to feature branch
- Standard scenarios: construct request → send → capture response → validate (objective alignment, field presence, values) → record PASS/FAIL

### Phase 4: Record Results and Cleanup

- Stop the service (`kill $SERVICE_PID`)
- Format: summary table + expandable details per scenario (see output-template.md)

## Step 9: Execute Verification Examples and Generate Script

For each example type selected in Step 6:

1. Build a standalone verification script at:
   `~/.claude/thoughts/shared/verification/scripts/verify-DESCRIPTION.sh`
   following the structure in `references/script-template.sh`
2. Execute the script and capture output
3. Record results for the evidence document

Create the `scripts/` directory if it doesn't exist:

```bash
mkdir -p ~/.claude/thoughts/shared/verification/scripts
```

### Script Structure Requirements

Each check in the verification script MUST include:

- **Description**: A natural language sentence explaining what scenario is being verified (e.g., "SKILL.md has valid YAML frontmatter with name field")
- **Expected outcome**: What the successful result looks like (e.g., "Frontmatter contains name: verify")
- **PASS/FAIL output**: Using the `run_check` function from `references/script-template.sh`

The script MUST:

- Run ALL checks even if some fail (don't stop on first failure)
- Print a summary at the end listing total/passed/failed counts
- List failed checks by name in the summary
- Exit with code 1 if any check failed, 0 if all passed

### Before/After Examples

Read `references/domain-strategies.md` for domain-specific before/after procedures:

- **Infrastructure/Skills**: Compare file contents and command outputs between base and feature branch
- **Backend API**: Capture responses from running service, then checkout base branch to capture baseline

### Happy Path / Edge Cases / Failure Modes

- **Infrastructure/Skills**: Execute relevant commands and capture output
- **Backend API**: Send requests to the running service and capture responses

### Per-Check Recording

For each check, record (in both the script output AND the evidence document):

- **Description** — natural language sentence: what scenario is being verified
- **Expected outcome** — what success looks like
- **Command** — exact command executed
- **Actual result** — what was observed
- **Verdict** — PASS/FAIL with the description repeated for identification

## Step 10: Generate Evidence Document

Write the evidence document to:
`~/.claude/thoughts/shared/verification/YYYY-MM-DD-description.md`

Create the directory if needed:

```bash
mkdir -p ~/.claude/thoughts/shared/verification
```

Follow the template in `references/output-template.md`. The document includes:

- Header with plan reference, branch, commit, and date
- Plan objective (from Overview)
- Verification strategy (from Step 6)
- Objective alignment results table (from Step 4)
- Automated verification results table (from Step 7)
- All verification examples with assertions (from Step 9)
- Test suite results table
- Negative assertions (from "What We're NOT Doing")
- Summary table with category counts
- Verdict: **PASS** (all pass), **FAIL** (any critical failure), or **PARTIAL** (non-critical failures)
- Reproduction instructions referencing the verification script
- Raw request/response transcripts appendix (mandatory for Backend API — see output-template.md)

## Step 11: Report Results

Present to the user:

- The verdict (PASS / FAIL / PARTIAL)
- Summary table from the evidence document
- Path to the full evidence document
- If any FAIL: highlight what needs attention and suggest next steps
- If PARTIAL: list what passed and what remains

## Reference Files

- **Output template**: `references/output-template.md` — full evidence document structure with all sections
- **Domain strategies**: `references/domain-strategies.md` — domain-specific verification procedures for Infrastructure/Skills and Backend API domains
- **Live testing guide**: `references/live-testing-guide.md` — detailed procedures for service startup, auth, scenario generation, request construction, response validation, and result formatting
