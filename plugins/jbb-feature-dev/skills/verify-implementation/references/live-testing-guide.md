# Live Service Testing Guide

Detailed procedures for Phase 1-4 of Step 8 (Live Service Testing).
Read this file when Step 8 instructs you to `Read references/live-testing-guide.md`.

## Local Configuration and Authentication

Use this guide only when a local service request directly verifies the changed behavior.
For libraries, documentation, or build-only changes, use the relevant local interface in SKILL.md.

Before startup, inspect the repository's documented local setup and all dependency targets.
A localhost listener can still call production dependencies. Use existing local fixtures,
fakes, or emulators; do not route dependencies to a real environment to make startup succeed.
Do not call deployed services, remote model gateways, or cloud token endpoints as a workaround.

Use only the authentication setup already documented for local verification. Do not copy
secrets, print tokens, change global credentials, or disable authentication automatically.
If the setup requires unavailable credentials, record the exact error and affected criterion
as BLOCKED and ask for the missing prerequisite. Continue independent local checks.

An existing in-process integration test with local fake dependencies can verify the real
handler. State that it does not verify transport or authentication when it bypasses those layers.

## Service Startup Procedures

### Build System Detection

Detect the project's build system from its manifest, then use its own documented run command.
If the repository has its own `CLAUDE.md` or contributor guide at its root, read it before running anything.

| Marker                        | Build system | Build                                  | Run locally                                            |
| ----------------------------- | ------------ | -------------------------------------- | ------------------------------------------------------ |
| `package.json`                | Node/npm     | `npm ci`                               | `npm start` / `npm run dev`                            |
| `pyproject.toml` / `setup.py` | Python       | `uv sync` / `pip install -e .`         | the project's entry point or `uvicorn`/`flask` command |
| `pom.xml`                     | Maven        | Use the documented local build target  | Use the documented local entry point and local dependency configuration |
| `BUILD` / `BUILD.bazel`       | Bazel        | `bazel build //path:target`            | `bazel run //path:target`                              |
| `build.sbt`                   | SBT          | Use the documented local build target  | Use the documented local run target; report a blocker if unavailable |
| `Makefile`                    | make         | `make build`                           | `make run`                                             |
| `docker-compose.yml`          | compose      | `docker compose build`                 | `docker compose up`                                    |

Read the project's own README or `scripts` block before inventing a command.

#### Large Bazel monorepos

A service in a large Bazel monorepo often has no documented per-service run command.
`bazel run //path/to/component` usually works when `BUILD.bazel` has a target named the same as the
directory. When it does not, read the `BUILD.bazel` and name the service target explicitly rather than guessing.

Three traps an agent walks into unprompted:

- Target specific packages; never `bazel build //...` or `bazel test //...`. In a large monorepo an
  unscoped build is not a slow command, it is an unusable one.
- Never use `bazel clean`; the cache handles invalidation. A service that will not start is precisely
  when reaching for `clean` feels productive.
- Do not modify `.bazelrc` files or shared build configuration.

A service that dies immediately on a missing environment variable is usually a local-setup step,
not a broken build. Check the repository's guide for setting environment variables before concluding otherwise.

### Standard Ports

Common defaults; confirm against the service's own configuration.

| Port | Protocol | Purpose                 |
| ---- | -------- | ----------------------- |
| 5990 | gRPC     | Primary gRPC server     |
| 8080 | HTTP     | HTTP server / REST API  |
| 5700 | HTTP     | Health/metrics          |

### Starting the Service

Launch the repository's documented local command as a background process. Record its PID,
working directory, ports, configuration, and unique log path in the evidence.
Persist these values for later commands; do not assume shell variables persist between tool calls.
Do not reuse a fixed log path that can overwrite another verification run.

### Readiness Polling

Use the service's documented local readiness interface with a bounded timeout.
Preserve the response and exit status. Report a timeout as a startup blocker, not success.
Readiness alone does not verify the changed endpoint.

### Startup Failure Handling

If startup fails or readiness times out, capture the actual error from the retained log.
Inspect the matching local setup below and retry only after a relevant safe change.
Record unavailable prerequisites as BLOCKED and observed incorrect behavior as FAIL.
Continue independent checks in Step 9; do not replace a blocked endpoint with an unrelated one.

### Common Local Startup Blockers

| Blocker | Safe local investigation |
| ------- | ------------------------ |
| Missing secrets or authentication | Inspect the documented local test setup; do not copy credentials or weaken authentication. |
| PubSub or another external dependency | Use a repository-supported local emulator or fake and verify its target address. |
| Service discovery or name resolution | Use documented local routing; do not select a real region as a workaround. |
| Event sender or remote configuration | Use documented local fixtures; do not disable behavior that a required criterion needs. |

Inspect existing integration tests and local configuration for supported setups. Record
which dependency is fake and which behavior remains unverified. If no safe local setup
exists, report the prerequisite as BLOCKED rather than guessing configuration overrides.

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

### Authenticated Requests

Use the repository's documented local authenticated client, if available without remote
token requests. Do not invent impersonation settings or disable service authentication.
If authenticated local calls are unavailable, record the blocker and the coverage limits
of any existing in-process behavioral test.

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

1. Record the feature checkout's HEAD, status, and tracked/untracked verification scope.
   Capture all "after" scenarios there, including relevant uncommitted and untracked changes.
2. Create a separate detached baseline worktree at the exact base commit recorded in Step 1
   of SKILL.md. Use Git's worktree add operation with its detach option and a new local path.
   Record that path and resolved commit. Do not stash, checkout, reset, or clean the feature checkout.
3. Build and run the baseline from its own directory with separate artifacts, logs, and ports.
   If ports cannot differ, stop only the owned feature process before starting the baseline.
   Do not copy feature changes or secrets into the baseline.
4. Send identical local inputs and capture baseline output and exit status. Record missing
   baseline interfaces as observed absence, not an invented successful response. If the
   baseline cannot run, record the blocker and do not claim a verified comparison.
5. Compare the expected changed fields and relevant unchanged behavior. Preserve raw responses;
   normalize nondeterministic fields only in separate comparison copies.
6. Stop only processes started for verification using their recorded process identifiers. Confirm the
   feature checkout and its changes remain intact. Keep the baseline worktree and report
   its path; do not remove worktrees, files, or artifacts without explicit authorization.

## Result Formatting

For result formatting templates (summary table, expandable scenario details, Before/After
details), see `references/output-template.md` — that file is the canonical source for all
evidence document formatting. Do not duplicate templates here; reference output-template.md
instead.
