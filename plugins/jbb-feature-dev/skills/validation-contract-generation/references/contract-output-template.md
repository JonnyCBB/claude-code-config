---
date: "2026-05-19"
requirements_path: "/path/to/requirements.md"
domains_detected:
  - Backend API
  - ML
assertion_count: 5
live_testing: true
live_testing_skip_reason: ""
live_assertion_count: 2
unit_assertion_count: 3
status: frozen
generator_model: "sonnet"
---

# Verification Contract

Generated from: `/path/to/requirements.md`

## Assertion Categories

Every contract MUST include assertions from these categories (when applicable):

1. **Live service assertions** — server started, request sent, response validated. Minimum 1 per distinct endpoint/RPC for Backend API domain.
2. **Baseline assertions** — test suite passes, build succeeds. Minimum 1.
3. **Behavioral assertions** — specific AC behavior verified via any method. As many as needed.

## Assertions

### VAL-API-000

- **Stable ID**: `VAL-API-000`
- **Source AC**: (lifecycle — no AC)
- **Domain**: Backend API
- **Category**: Live service test (server lifecycle)
- **Tolerance**: exact match (health check returns serving/200)
- **Notes**: All subsequent live assertions depend on this. If blocked, all live assertions are blocked.

#### Setup

```bash
mvn package -q -DskipTests
java -jar target/service.jar > /tmp/service.log 2>&1 &
SERVICE_PID=$!
```

#### Stimulus

```bash
for i in $(seq 1 30); do
  curl -sf http://localhost:8080/healthz && break || sleep 2
done
```

#### Assertion

Health endpoint returns HTTP 200. Service process is running (`kill -0 $SERVICE_PID`).

#### Evidence

```
curl -v http://localhost:8080/healthz 2>&1
```

- **Status**: `pending`

### VAL-API-001

- **Stable ID**: `VAL-API-001`
- **Source AC**: `AC-1`
- **Domain**: Backend API
- **Category**: Live service test
- **Tolerance**: exact match (HTTP 200, response contains `"status": "ok"`)
- **Notes**: —

#### Setup

Server already running from VAL-API-000 setup.

#### Stimulus

```bash
curl -s -X POST http://localhost:8080/api/resource \
  -H 'Content-Type: application/json' \
  -d '{"name": "test-resource"}'
```

#### Assertion

Response HTTP status is 200. Body contains `"id"` field with non-empty string value.

#### Evidence

```
curl -v ... 2>&1 (full request/response transcript)
```

- **Status**: `pending`

<!-- Repeat this block for each assertion. Use VAL-{DOMAIN_CODE}-{NNN} stable IDs.
     Domain codes: API, DATA, ML, GEN. Sequential per domain starting at 001. -->

## Coverage Summary

| Assertion ID  | Source AC   | Domain      | Category          | Tolerance                                    |
| ------------- | ----------- | ----------- | ----------------- | -------------------------------------------- |
| `VAL-API-000` | (lifecycle) | Backend API | Live service test | exact match                                  |
| `VAL-API-001` | `AC-1`      | Backend API | Live service test | exact match                                  |
| `VAL-ML-001`  | `AC-2`      | ML          | Unit/integration  | threshold (accuracy > 0.95)                  |
| `VAL-ML-002`  | `AC-3`      | ML          | Unit/integration  | retry-with-delay (convergence within 3 runs) |

## Amendments

When code review or a later implementation pass reveals that the contract needs additional assertions, use `--amend` mode to append new assertion blocks without disturbing the stable IDs already executed. Each amendment records its provenance so reviewers can trace why it was added.

> **Regeneration from scratch**: If the contract’s scope has changed so fundamentally that patching is misleading, delete the contract and regenerate with the standard (non-amend) flow. Amendments are for incremental additions, not rewrites.

<!-- When amending, update these frontmatter fields:
     status: amended
     amendment_count: <integer — total amendments added so far>
     amendment_phase: <phase that triggered the amendment, e.g. "post-code-review">
     total_assertion_count: <original assertion_count + amendment_count>
-->

### VAL-AMD-001

- **Stable ID**: `VAL-AMD-001`
- **Source AC**: `AC-4`
- **Domain**: Backend API
- **Category**: Behavioral assertion
- **Tolerance**: exact match
- **Provenance**:
  - `added_phase`: post-code-review
  - `added_reason`: "Code review identified an unverified error-handling path for invalid input on the /api/resource endpoint."
  - `amendment_of`: (original contract `VAL-API-001` scope — extends, does not replace)

#### Setup

Server already running from VAL-API-000 setup.

#### Stimulus

```bash
curl -s -X POST http://localhost:8080/api/resource \
  -H 'Content-Type: application/json' \
  -d '{"name": ""}'
```

#### Assertion

Response HTTP status is 400. Body contains `"error"` field describing the validation failure.

#### Evidence

```
curl -v ... 2>&1 (full request/response transcript)
```

- **Status**: `pending`

<!-- Repeat this block for each amendment. Use VAL-AMD-{NNN} stable IDs, sequential starting at 001. -->
