# Live Service Testing Guide

Detailed procedures for Phase 1-4 of Step 8 (Live Service Testing).
Read this file when Step 8 instructs you to `Read references/live-testing-guide.md`.

## Authentication Prerequisites

Pre-flight auth checks before starting the service.

### Auth Failure Handling

If any auth check fails:

1. Report which check failed and the exact error
2. **Investigate common fixes first** — try the remediation command (e.g.,
   `gcloud auth application-default login`), check for integration test configs
   that bypass auth, or write an in-process integration test with a fake gRPC
   stub. Setting `serviceauth.enabled: false` in `-user.conf` requires explicit
   user permission in auto-mode (classified as auth-weakening)
3. **Re-run the failed check** after attempting fixes
4. Only if ALL remediation attempts fail: abort live testing and proceed to Step 9
5. Record the auth failure as a FAIL in the evidence document, listing each
   remediation attempted and why it failed

## Service Startup Procedures

### Build System Detection

Detect the project's build system from its manifest, then use its own documented run command:

| Marker                        | Build system | Build                    | Run locally                |
| ----------------------------- | ------------ | ------------------------ | -------------------------- |
| `package.json`                | Node/npm     | `npm ci`                 | `npm start` / `npm run dev` |
| `pyproject.toml` / `setup.py` | Python       | `uv sync` / `pip install -e .` | the project's entry point or `uvicorn`/`flask` command |
| `Makefile`                    | make         | `make build`             | `make run`                 |
| `docker-compose.yml`          | compose      | `docker compose build`   | `docker compose up`        |

Read the project's own README or `scripts` block before inventing a command.

### Standard Ports

| Port | Protocol | Purpose                 |
| ---- | -------- | ----------------------- |
| 5990 | gRPC     | Primary gRPC server     |
| 8080 | HTTP     | HTTP server / REST API  |
| 5700 | HTTP     | Health/metrics |

### Readiness Polling

Poll for up to 60 seconds (30 attempts, 2 seconds apart):

```bash
for i in $(seq 1 30); do
  if grpcurl -plaintext -max-time 2 localhost:5990 grpc.health.v1.Health/Check 2>/dev/null | grep -q SERVING; then
    echo "Service ready"
    break
  fi
  sleep 2
done
```

Fallback checks if gRPC health check is not available:

- HTTP: `curl -s -o /dev/null -w '%{http_code}' localhost:8080/_meta/0/info` returns `200`
- HTTP health endpoint: `curl -s -o /dev/null -w '%{http_code}' localhost:5700/readiness` returns `200`

### Startup Failure Handling

If the service fails to start within 60 seconds:

1. Capture stderr from `/tmp/service-stdout.log`
2. **Consult the Common Local Startup Blockers table below** — check each row
   against the error output and attempt any matching fixes
3. **Retry startup** after applying fixes (allow another 60 seconds)
4. Only if startup still fails after consulting the blockers table and retrying:
   proceed to Step 9
5. Include the error in the evidence document as a FAIL result, listing each
   blocker checked and fix attempted

### Common Local Startup Blockers

Before falling back to workarounds, try these solutions for common issues:

| Blocker                 | Symptom                                     | Solution                                                                                                                                   |
| ----------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Secret-store lookup failure | `MissingSecretException`             | Point the client at a local secret override in the service config, and set a local namespace |
| PubSub connection       | Publisher creation fails                    | Run `gcloud beta emulators pubsub start --project=<project> --host-port=localhost:8085` and set `pubsub.use-emulator: true` in user conf   |
| Service discovery resolution | Channel creation fails for internal service targets | Point the client at the right discovery domain in the service config, or via its documented env var |
| Service auth            | Auth enforcement blocks local calls         | *Primary:* write an in-process integration test wiring the real handler with a hand-rolled fake gRPC stub — this avoids the auth layer entirely and is the most robust local verification. *Manual fallback:* set `serviceauth.enabled: false` in `-user.conf` — ⚠️ auto-mode classifies this as auth-weakening and will deny it; the agent must ask the user for explicit permission before applying this fix. |
| Event sender            | EventSender initialization fails            | Set `event-sender.enabled: false` in user conf                                                                                             |
| Remote config           | RemoteConfig resolution fails               | Set `remoteconfig.enabled: false` in user conf                                                                                             |

Look for patterns in the project's integration test (often `ContainerIT.java` or
similar) — it typically contains all the config overrides needed for local execution.
Also check if a `-user.conf` file exists (often `.gitignored`) or look at other
services in the monorepo for examples.

## Test Scenario Generation Heuristics

### Step 1: Objective Alignment

Re-read the plan's Overview and Desired End State. For each desired end state item,
determine what request(s) would demonstrate it works correctly. **Every scenario must
map back to at least one plan objective.** The request/response signature is the
strongest verification signal — it proves the implementation does what it's supposed to
do more reliably than static code analysis alone.

If a requirements doc was provided, also map acceptance criteria (GIVEN/WHEN/THEN) to
test scenarios. Each live-testable acceptance criterion should have at least one scenario
that directly exercises its GIVEN/WHEN/THEN path. Tag these scenarios with the acceptance
criterion ID (e.g., "AC-1") in the scenario matrix so the evidence document can trace
live test results back to specific acceptance criteria.

### Step 2: Proto Analysis

Read the proto file(s) for new/modified RPCs. For each request message:

- Identify required vs optional fields
- Identify repeated fields (lists) and oneof fields
- Identify enum fields and their values
- Note the response message structure for validation

### Step 3: Handler Analysis

Read the handler/implementation code. Identify:

- Conditional branches (if/else, switch, ternary) — each branch should have a scenario
- Feature flags or boolean parameters that gate behavior
- Graceful degradation paths (try/catch that continues without failing)
- External dependencies called (test with and without their data)

### Step 4: Generate Scenario Matrix

| Category             | Heuristic                                                                     | Minimum                        |
| -------------------- | ----------------------------------------------------------------------------- | ------------------------------ |
| Happy path           | Simplest valid request with only required fields                              | 1 per RPC                      |
| Full input           | All fields populated                                                          | 1 per RPC                      |
| Field omission       | Each optional field absent while others present                               | 1 per optional field (up to 3) |
| Feature toggle       | Each boolean/config flag in both states                                       | 1 per toggle                   |
| Mixed list items     | List items with varying optional sub-fields                                   | 1 if applicable                |
| Error input          | Invalid/empty required fields                                                 | 1 per RPC                      |
| Graceful degradation | Conditions where dependencies fail silently                                   | As warranted                   |
| Before/After         | Implementation changes existing behavior (filtering, removal, transformation) | 1 per behavioral change        |

Prioritize scenarios that exercise distinct code paths over exhaustive field permutation.
The agent determines the appropriate number based on handler complexity, conditional
branches, and plan objectives.

### Step 5: Present Scenario Plan

- **Interactive mode**: Show the planned scenarios and ask for confirmation. The user
  may add, remove, or modify scenarios.
- **Non-interactive mode**: Log the planned scenarios and proceed directly to execution.

## Request Construction Patterns

### gRPC Requests

```bash
grpcurl -plaintext -max-time 60 -d '{
  "field_name": "value",
  "repeated_field": [
    {"sub_field": "value1"},
    {"sub_field": "value2"}
  ],
  "bool_field": true
}' localhost:5990 package.ServiceName/MethodName
```

### REST Requests

```bash
curl -s -X POST http://localhost:8080/api/path \
  -H "Content-Type: application/json" \
  -d '{
    "field": "value"
  }'
```

### Field Type Placeholder Values

| Proto Type       | Placeholder Value                             | Notes                                        |
| ---------------- | --------------------------------------------- | -------------------------------------------- |
| string           | `"test-value"`                                | Use descriptive values related to the domain |
| int32/int64      | `42`                                          | Use realistic values                         |
| bool             | `true` / `false`                              | Test both states                             |
| enum             | Use first and last enum values                | Cover range                                  |
| repeated         | `[]` (empty) and `[item1, item2]` (populated) | Test empty and populated                     |
| message (nested) | Full sub-message or omit entirely             | Test present and absent                      |

## Response Validation Rules

### Deterministic Fields

For fields with predictable values:

- **Exact match**: Compare field value against expected value
- **Enum check**: Verify field is one of the expected enum values
- **Count check**: Verify array length matches expectations

### Non-Deterministic Fields

For fields with unpredictable values (LLM output, timestamps, IDs):

- **Structural validation**: Verify field exists and is non-null
- **Type check**: Verify field is the expected type (string, number, array)
- **Length check**: Verify string length is reasonable (e.g., > 10 chars for LLM text)
- **Do NOT compare exact content** — it will differ between runs

### Presence/Absence Checks

- Verify expected fields ARE present in the response
- Verify omitted optional request fields result in corresponding response fields being absent
- Verify gating behavior (e.g., `debug_info` absent when `include_debug_info=false`)

### Before/After Comparison

For scenarios where behavior changes between base and feature branch:

1. Strip non-deterministic fields before comparison:
   ```bash
   jq 'del(.timestamp, .requestId, .traceId)' response.json
   ```
2. Compare the specific field(s) that should differ
3. Assert: Before contains X, After does not contain X (or vice versa)

## Before/After Execution Procedure

When Before/After scenarios are present in the scenario matrix:

1. **Capture "after" responses** on the feature branch (service already running from Phase 1)
2. **Stop the service**: `kill $SERVICE_PID`
3. **Checkout base branch**: `git stash && git checkout <base-branch>`
4. **Build on base branch**: Run the build command
5. **Start service on base branch**: Launch and poll for readiness
6. **Capture "before" responses**: Send the same requests
7. **Stop the base branch service**: `kill $SERVICE_PID`
8. **Return to feature branch**: `git checkout <feature-branch> && git stash pop`
9. **Rebuild and restart**: Build and start service for remaining standard scenarios
10. **Compare**: Verify the behavioral change between before and after responses

## Result Formatting

For result formatting templates (summary table, expandable scenario details, Before/After
details), see `references/output-template.md` — that file is the canonical source for all
evidence document formatting. Do not duplicate templates here; reference output-template.md
instead.
