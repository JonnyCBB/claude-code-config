# Evidence Document Template

Use this template when generating the verification evidence document in Step 10.
Use the task objective and acceptance criteria when no formal plan exists. Replace every
placeholder with observed evidence; examples and expected results are not successful runs.
Remove irrelevant sections and explain any required check that is blocked or missing.
Record each execution once and reference it from all applicable sections, not as extra checks.
Write user-facing explanations in STE as specified in SKILL.md; preserve exact commands and raw output.

---

````markdown
# Verification Evidence: [Task or Plan Title]

## Result

**Verdict**: [PASS / FAIL / PARTIAL and its meaning for the supplied objective]
**Findings**: [observed results in clear STE, before open questions]
**Limits and open questions**: [unverified criteria, exact blockers, and any required user action]

**Date**: [capture date and timezone]
**Source**: [supplied objective, acceptance criteria, and/or plan reference]
**Repository**: [absolute root]
**Branch**: [actual branch or detached HEAD]
**Base**: [recorded full base commit and how it was selected]
**Head**: [full verified HEAD commit]
**Working-tree scope**: [staged, unstaged, and relevant untracked files; exclusions and reasons]
**Assessor**: [role and independence when the caller requires independent assessment]
**Baseline worktree**: [path and commit if used; retained unless removal is authorized]

## Task Objective and Acceptance Criteria

[Objective and testable outcomes from the supplied source, without inventing plan headings]

## Verification Strategy

[Which example types were selected and why, referencing Step 6 criteria]

## Objective Alignment Results

| # | Objective or Criterion | Implementation Evidence | Alignment | Execution Evidence |
| --- | --- | --- | --- | --- |
| [ID] | [supplied outcome] | [file/code reference] | [PASS/FAIL/GAP] | [scenario reference or missing evidence] |

[Implementation alignment is not a behavioral verdict. Inspection alone verifies only inspection-based criteria.]

**Drift**: [Any changes not mapped to supplied outcomes, or "None"]

## Requirements Alignment (from requirements doc)

> Included when a requirements doc was provided via `--requirements`. Omit this section otherwise.

### Acceptance Criteria Verification

| #    | Acceptance Criterion              | Evidence Type | Evidence                         | Status   |
| ---- | --------------------------------- | ------------- | -------------------------------- | -------- |
| [ID] | [criterion] | [local execution / inspection / unavailable] | [evidence reference and limits] | [PASS/FAIL/GAP/BLOCKED/DEFERRED] |

**Evidence limits**: [Which criteria have direct behavioral evidence, inspection only, or no evidence.
Inspection and unit-suite counts do not replace required local behavioral scenarios.
Criteria that need production data remain DEFERRED; do not make production requests.]

### Scope Verification

| Feature / Sub-task | Priority     | Expected       | Actual     | Status |
| ------------------ | ------------ | -------------- | ---------- | ------ |
| [Feature] | [Essential/Nice-to-have/Not needed] | [expected scope] | [observed evidence] | [observed status] |

### Success Criteria

| #   | Success Criterion | Evidence   | Status        |
| --- | ----------------- | ---------- | ------------- |
| [ID] | [metric/outcome] | [evidence and limits] | [PASS/FAIL/GAP/BLOCKED/DEFERRED] |

## Automated Verification Results

| Phase             | Criterion   | Command     | Result    |
| ----------------- | ----------- | ----------- | --------- |
| [phase or task] | [criterion ID] | `[actual command]` | [PASS/FAIL/BLOCKED and execution reference] |

## Live Service Testing Results

> Include when service requests directly verify the changed behavior. Otherwise state the
> relevant local interface used in Verification Examples and why service startup is irrelevant.
> If required service testing is blocked, retain this section with the exact error,
> attempted safe local remedies, affected criteria, and BLOCKED status.

### Service Startup

- **Build system**: [Maven/Bazel/SBT]
- **Startup command**: `[command used]`
- **Readiness**: [How readiness was confirmed — e.g., "gRPC health check returned SERVING after 8 seconds"]
- **Local dependencies and auth**: [documented local setup, fake/emulator targets, and coverage limits; no secrets]
- **Captured output**: [verbatim startup/readiness output or exact blocker]

### Summary

| #   | Scenario        | Objective                 | Key Input Variations     | Result    |
| --- | --------------- | ------------------------- | ------------------------ | --------- |
| [ID] | [scenario name] | [supplied outcome or criterion ID] | [precise input variations] | [PASS/FAIL/BLOCKED] |

### Scenario Details

<details>
<summary><strong>Scenario 1: [Name]</strong></summary>

**Objective**: [Which objective or acceptance criterion this verifies]
**Setup and inputs**: [precise local configuration, working directory, data, and relevant input variations]
**Expected outcome**: [specific expected response and exit status, defined before execution]
**What this tests**: [Purpose — which code path/behavior is being verified]

**Execution evidence**: [scenario transcript ID in the appendix, containing the exact command, request, and response]

**Observed status**: [actual command exit status and response status]
**Verified and limits**: [assertions tied to actual response fields; what remains unverified]

</details>

<details>
<summary><strong>Scenario N: [Before/After] [Name]</strong></summary>

**Objective**: [Which supplied outcome or acceptance criterion this verifies]
**Setup and expected outcome**: [identical local inputs, expected changed fields, and expected unchanged behavior]

**Execution evidence**: [before and after transcript IDs in the appendix, with identical request inputs, exact commands, and recorded base/feature states]

**Observed statuses**: [actual exit and response status for each run]
**Verified and limits**: [specific before/after assertions and any unverified behavior]

</details>

## Verification Examples

> **Format guide**: Each example has three layers:
>
> - **Expected Outcome** — natural language description of what success looks like (for the reviewer)
> - **Actual Result** — raw command output (for evidence)
> - **Assertions** — specific PASS/FAIL checks bridging actual result to expected outcome (for verdict)

### Example 1: [Happy Path] [Description]

**Purpose**: Demonstrates that [primary feature] works correctly.

**Setup and inputs**: [working directory, local configuration, exact data, and criterion ID]

**Action**:
\```bash
[exact command; for UI checks, local URL and exact browser actions]
\```

**Expected Outcome**: [Natural language description of what success looks like. E.g., "Response contains exactly 3 items, all with status 'active', and no items from the blocked list appear in the results"]

**Actual Result** (raw output):
\```
[actual output, exit status, or browser observations and screenshot references]
\```

**Assertions**:

- [PASS/FAIL/BLOCKED]: [assertion, expected result, observed result, and evidence limits]

### Example 2: [Before/After] [Description]

**Purpose**: Proves that [change] is applied correctly.

#### Before (baseline):

**Command**: [exact command and working directory in baseline worktree at recorded base]
**Output**:
\```
[baseline output]
\```

#### After (implementation):

**Command**: [same command and working directory in recorded feature working-tree state]
**Output**:
\```
[feature branch output]
\```

**Assertions**:

- [PASS/FAIL/BLOCKED]: [expected before/after difference, actual output, and exit statuses]
- [PASS/FAIL/BLOCKED]: [specific unchanged behavior and actual evidence]

### Example 3: [Edge Case] [Description]

**Purpose**: Verifies handling of [boundary condition].

**Request**:
\```bash
[command]
\```

**Expected Outcome**: [Natural language description of what correct handling looks like for this edge case]

**Actual Result** (raw output):
\```
[output]
\```

**Assertions**:

- [PASS/FAIL/BLOCKED]: [criterion ID, exact inputs, assertion, actual output, exit status, and limits]

### Example 4: [Failure Mode] [Description]

**Purpose**: Confirms [error handling behavior].

**Request**:
\```bash
[command triggering error path]
\```

**Expected Outcome**: [Natural language description of what correct error handling looks like]

**Actual Result** (raw output):
\```
[output showing graceful handling]
\```

**Assertions**:

- [PASS/FAIL/BLOCKED]: [criterion ID, exact inputs, expected error handling, actual output, exit status, and limits]

## Test Suite Verification

| Test Suite        | Command     | Tests Run | Passed | Failed |
| ----------------- | ----------- | --------- | ------ | ------ |
| [relevant suite] | `[actual command]` | [observed count] | [observed count] | [observed count] |

[Reference existing execution records. Do not rerun suites just to fill this table.
Record skipped or blocked suites explicitly. Include actual inputs and outputs for any
focused library example or behavioral test, not only its name or pass count.]

## Negative Assertions (What We're NOT Doing)

| #   | Out-of-Scope Item | Verified Not Present | Status |
| --- | ----------------- | -------------------- | ------ |
| [ID] | [out-of-scope item] | [observed evidence] | [observed status] |

## Summary

| Category | Required | Pass | Fail | Blocked / Deferred / Missing |
| -------- | -------- | ---- | ---- | ---------------------------- |
| [category] | [actual count] | [actual count] | [actual count] | [actual count] |

[Report criterion coverage separately from unique execution counts. Do not sum duplicate
references as independent checks or fill absent results with zero failures.]

## Verdict: PASS / FAIL / PARTIAL

[PASS requires passing evidence for every required criterion and at least one executed
required check. FAIL means a required check demonstrates incorrect behavior. Otherwise
use PARTIAL for blocked, deferred, or missing coverage. Zero executed required checks
cannot PASS. List failures, exact blockers, and unverified criteria; distinguish expectations
and code inspection from observed behavior.]

## Reproduction Instructions

To reproduce this verification:

### Prerequisites

- [Language/runtime version — e.g., "Java 25 via SDKMAN (`sdk env`)"]
- [Required tools — e.g., "`spgrpcurl` installed", "`grpcurl` installed"]
- [Documented local authentication and fake/emulator setup, without copying secrets or weakening auth]
- [Local environment variables and dependency targets]
- [Working directories, recorded commits, and relevant working-tree inputs]

### Step 1: Run relevant existing checks and examples

\```bash
[exact commands, working directories, and local inputs used]
\```

Expected: [specific output and exit status for each command].
Observed: [reference actual output above, including failures or blockers].

[Run each unique command once. A wrapper is optional only when needed to express the
sequence; if used, include its local-only path and commands. Never infer PASS from an
empty wrapper run or an exit code without required criterion evidence.]

### Step 2: Start service only when relevant

\```bash
[exact startup command including env vars]
\```

Wait for startup (~[N] seconds). Verify with health check:

\```bash
[exact health check command]

# Expected: [expected output, e.g., {"status": "SERVING"}]

\```

### Step 3: Send local test requests or perform local browser actions when relevant

[For service scenarios, reference the appendix transcript containing the exact copy-pasteable command and expected outcome. Do not repeat its payloads.]

[For browser scenarios, reference Verification Examples for the local URL, exact actions, expected state, observed state, and screenshots.]

### Step 4: Stop owned processes and report retained artifacts

[Record process identifiers and exact stop commands used. Confirm feature checkout state is
preserved. List retained logs and baseline worktree paths. Do not delete worktrees, files,
or artifacts without explicit authorization.]

## Appendix: Raw Request/Response Transcripts

Include this appendix for service request/response checks. Keep each command and
verbatim request/response transcript here once, with its scenario ID and expected outcome.
Reference that ID from other sections rather than duplicating payloads. Record browser
actions, observed states, and screenshots in Verification Examples; browser checks do not
require unrelated service transcripts.
This allows reviewers to independently assess the results without re-running tests.
Include full payloads as received, except redact any secrets or personal data and label
each redaction. Do not publish tokens or credentials as evidence.

Format each transcript as:

### S[N]: [Scenario description] — "[query or key input]"

**Command and working directory**: [exact command and directory used]
**Expected outcome**: [specific response and exit status]
**Observed status**: [actual command exit status and response status]

**Request:**
\`\`\`json
<exact request payload sent>
\`\`\`

**Response:**
\`\`\`json
<exact response received, with any sensitive-data redactions labeled>
\`\`\`

Guidelines:

- Include all service request/response scenarios, not just notable ones
- Include workaround/sanity-check requests if any were performed
- Preserve full responses except explicitly labeled sensitive-data redactions
- For non-deterministic content (LLM text), include the actual text received
  during this specific test run
- If a test returned an error, include the full error response
````
