# Evidence Document Template

Use this template when generating the verification evidence document in Step 9.

---

````markdown
# Verification Suite: [Plan Title]

**Date**: YYYY-MM-DD HH:MM:SS TZ
**Plan**: ~/.claude/thoughts/shared/plans/YYYY-MM-DD-description.md
**Branch**: [feature-branch]
**Commit**: [short-hash]

## Plan Objective

[Extracted from plan Overview section]

## Verification Strategy

[Which example types were selected and why, referencing Step 6 criteria]

## Objective Alignment Results

| #   | Desired End State Item | Implementation Evidence | Status        |
| --- | ---------------------- | ----------------------- | ------------- |
| 1   | [Item from plan]       | [File/code reference]   | PASS/FAIL/GAP |
| 2   | ...                    | ...                     | ...           |

**Drift**: [Any code changes not mapped to plan items, or "None"]

## Requirements Alignment (from requirements doc)

> Included when a requirements doc was provided via `--requirements`. Omit this section otherwise.

### Acceptance Criteria Verification

| #    | Acceptance Criterion              | Evidence Type | Evidence                          | Status              |
| ---- | --------------------------------- | ------------- | --------------------------------- | ------------------- |
| AC-1 | GIVEN X WHEN Y THEN Z            | Live test     | Scenario 3: [name] — PASS        | PASS                |
| AC-2 | GIVEN A WHEN B THEN C            | Code + Live   | `file:line` + Scenario 5 — PASS  | PASS                |
| AC-3 | GIVEN D WHEN E THEN F            | Code only     | `file:line` — no live test       | GAP                 |
| AC-4 | GIVEN G WHEN H THEN latency < Xms| —             | Requires production load testing  | DEFERRED            |

**Evidence strength**: Live test > Code + Live test > Code only > Deferred

### Scope Verification

| Feature / Sub-task | Priority    | Expected           | Actual              | Status |
| ------------------ | ----------- | ------------------ | ------------------- | ------ |
| [Feature 1]        | Essential   | Implemented        | [evidence]          | PASS   |
| [Feature 2]        | Nice-to-have| Not over-built     | [evidence]          | PASS   |
| [Feature 3]        | Not needed  | Absent             | [evidence]          | PASS   |

### Success Criteria

| # | Success Criterion       | Evidence            | Status        |
|---|------------------------|---------------------|---------------|
| 1 | [metric/outcome]       | [evidence]          | PASS/DEFERRED |

## Automated Verification Results

| Phase             | Criterion   | Command     | Result    |
| ----------------- | ----------- | ----------- | --------- |
| Phase 1           | [Criterion] | `[command]` | PASS/FAIL |
| Phase 2           | ...         | ...         | ...       |
| Desired End State | [Criterion] | `[command]` | PASS/FAIL |

## Live Service Testing Results

> Included when Backend API domain is detected (Step 8). Omit this section if Step 8 was skipped.

### Service Startup

- **Build system**: [Maven/Bazel/SBT]
- **Startup command**: `[command used]`
- **Readiness**: [How readiness was confirmed — e.g., "gRPC health check returned SERVING after 8 seconds"]
- **Auth**: [Auth method used — e.g., "ADC with service account impersonation via <service>-user.conf"]

### Summary

| #   | Scenario        | Objective                 | Key Input Variations     | Result    |
| --- | --------------- | ------------------------- | ------------------------ | --------- |
| 1   | [Scenario name] | [Plan objective verified] | [What makes it distinct] | PASS/FAIL |
| 2   | ...             | ...                       | ...                      | ...       |

### Scenario Details

<details>
<summary><strong>Scenario 1: [Name]</strong></summary>

**Objective**: [Which plan objective/desired end state item this verifies]
**What this tests**: [Purpose — which code path/behavior is being verified]

**Request:**
\```bash
[exact grpcurl/curl command]
\```

**Response:**
\```json
[full JSON response]
\```

**Verified**: [Specific assertions about the response]

</details>

<details>
<summary><strong>Scenario N: [Before/After] [Name]</strong></summary>

**Objective**: [Which plan objective this verifies]
**What this tests**: [What behavioral change is expected]

**Request** (same for both):
\```bash
[exact command]
\```

**Before (base branch):**
\```json
[response on base branch]
\```

**After (feature branch):**
\```json
[response on feature branch]
\```

**Verified**: [e.g., "Before: offending results present. After: offending results absent."]

</details>

## Verification Examples

> **Format guide**: Each example has three layers:
>
> - **Expected Outcome** — natural language description of what success looks like (for the reviewer)
> - **Actual Result** — raw command output (for evidence)
> - **Assertions** — specific PASS/FAIL checks bridging actual result to expected outcome (for verdict)

### Example 1: [Happy Path] [Description]

**Purpose**: Demonstrates that [primary feature] works correctly.

**Request**:
\```bash
[exact command]
\```

**Expected Outcome**: [Natural language description of what success looks like. E.g., "Response contains exactly 3 items, all with status 'active', and no items from the blocked list appear in the results"]

**Actual Result** (raw output):
\```
[actual output from command]
\```

**Assertions**:

- PASS: [assertion 1]
- PASS: [assertion 2]

### Example 2: [Before/After] [Description]

**Purpose**: Proves that [change] is applied correctly.

#### Before (baseline):

**Command**: [command against base branch]
**Output**:
\```
[baseline output]
\```

#### After (implementation):

**Command**: [same command against feature branch]
**Output**:
\```
[feature branch output]
\```

**Assertions**:

- PASS: Before shows [X], After shows [Y]
- PASS: Other aspects remain unchanged

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

- PASS: [assertion]

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

- PASS: [assertion about error handling]

## Test Suite Verification

| Test Suite        | Command     | Tests Run | Passed | Failed |
| ----------------- | ----------- | --------- | ------ | ------ |
| Unit Tests        | `[command]` | [N]       | [N]    | 0      |
| Integration Tests | `[command]` | [N]       | [N]    | 0      |

## Negative Assertions (What We're NOT Doing)

| #   | Out-of-Scope Item | Verified Not Present | Status |
| --- | ----------------- | -------------------- | ------ |
| 1   | [Item from plan]  | [Evidence]           | PASS   |

## Summary

| Category                | Total | Pass  | Fail  | Skip     |
| ----------------------- | ----- | ----- | ----- | -------- |
| Objective Alignment     | X     | X     | 0     | 0        |
| Requirements Alignment  | X     | X     | 0     | DEFERRED |
| Plan Criteria           | X     | X     | 0     | 0        |
| Verification Examples | X     | X     | 0     | 0     |
| Test Suites           | X     | X     | 0     | 0     |
| Negative Assertions   | X     | X     | 0     | 0     |
| **Overall**           | **X** | **X** | **0** | **0** |

## Verdict: PASS / FAIL / PARTIAL

[Brief explanation of verdict. If PARTIAL, list what passed and what failed.]

## Reproduction Instructions

To reproduce this verification:

1. Checkout branch: `git checkout [branch]`
2. Build: `[build command]`
3. Start service (if applicable): `[start command]`
4. Run verification script: `~/.claude/thoughts/shared/verification/scripts/verify-[description].sh`

## Appendix: Raw Request/Response Transcripts

This section is MANDATORY for all Backend API verifications. Include the verbatim
request and response for every live test scenario. This allows reviewers to
independently assess the results without re-running tests.

Format each transcript as:

### Test N: [Scenario description] — "[query or key input]"

**Request:**
\`\`\`json
<exact request payload sent>
\`\`\`

**Response:**
\`\`\`json
<exact response received, unmodified>
\`\`\`

Guidelines:

- Include ALL live test scenarios, not just notable ones
- Include workaround/sanity-check requests if any were performed
- Do not truncate responses — include the full payload
- For non-deterministic content (LLM text), include the actual text received
  during this specific test run
- If a test returned an error, include the full error response
````
