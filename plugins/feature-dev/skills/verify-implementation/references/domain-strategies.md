# Domain-Specific Verification Strategies

Procedures for v1 domains: Infrastructure/Skills and Backend API.

## Infrastructure/Skills Domain

For changes to files, configurations, skills, and commands within `~/.claude/` or similar infrastructure.

### Verification Techniques

- **File existence**: `test -f <path>` — verify expected files were created/deleted
- **Content matching**: `grep <pattern> <file>` — verify expected content in files
- **Command execution**: Run commands and compare output against expectations
- **Script validation**: Execute any included scripts and verify they succeed

### Before/After Procedure

1. Record current state (feature branch):

   ```bash
   # Capture file contents and command outputs on feature branch
   cat <file> > /tmp/verify-after-<label>.txt
   <command> > /tmp/verify-after-<label>-output.txt 2>&1
   ```

2. Capture baseline (base branch):

   ```bash
   git stash  # if uncommitted changes
   git checkout <base-branch>
   cat <file> > /tmp/verify-before-<label>.txt 2>/dev/null || echo "FILE_NOT_FOUND"
   <command> > /tmp/verify-before-<label>-output.txt 2>&1 || true
   ```

3. Return to feature branch:

   ```bash
   git checkout <feature-branch>
   git stash pop  # if stashed
   ```

4. Compare:
   ```bash
   diff /tmp/verify-before-<label>.txt /tmp/verify-after-<label>.txt
   ```

## Backend API Domain

For changes to gRPC or REST services.

For comprehensive live service testing including startup, scenario generation, and
validation, see `references/live-testing-guide.md` (invoked in Step 8). Step 8 handles
service startup, Before/After comparison, and cleanup autonomously — the "ask user to
restart" steps below apply only to Step 9's non-live Before/After verification.

### Verification Techniques

- **gRPC requests**: `grpcurl` request/response pairs
- **REST requests**: `curl` request/response pairs
- **Response field extraction**: Use `jq` or `grpcurl -format json` for targeted comparison (skip timestamps, request IDs, trace IDs)

### Before/After Procedure

1. Capture "after" responses (service running on feature branch):

   ```bash
   # Send requests and capture responses
   curl -s <endpoint> | jq '.' > /tmp/verify-after-<label>.json
   # or
   grpcurl <service> <method> '<request>' > /tmp/verify-after-<label>.json
   ```

2. Record all responses before switching branches.

3. Switch to base branch and rebuild:

   ```bash
   git stash  # if uncommitted changes
   git checkout <base-branch>
   <build-command>  # e.g., mvn compile, sbt compile
   ```

4. Ask user to restart service on base branch (Step 9 only — Step 8 handles this autonomously). Wait for confirmation.

5. Capture "before" responses:

   ```bash
   curl -s <endpoint> | jq '.' > /tmp/verify-before-<label>.json
   # or
   grpcurl <service> <method> '<request>' > /tmp/verify-before-<label>.json
   ```

6. Return to feature branch:

   ```bash
   git checkout <feature-branch>
   git stash pop  # if stashed
   ```

7. Ask user to restart service on feature branch (Step 9 only — Step 8 handles this autonomously). Wait for confirmation.

8. Compare:
   ```bash
   diff /tmp/verify-before-<label>.json /tmp/verify-after-<label>.json
   ```

## Common Patterns

### Retry Logic

For transient service failures, retry up to 3 times with 2-second backoff:

```bash
for attempt in 1 2 3; do
  result=$(<command> 2>&1) && break
  echo "Attempt $attempt failed, retrying in 2s..."
  sleep 2
done
```

### Assertion Format

Use consistent assertion format in both verification scripts and evidence documents:

- `PASS: <description of what was verified>`
- `FAIL: <description of what failed> — Expected: <X>, Got: <Y>`

Each assertion's description must be a complete natural language sentence that explains both the scenario being verified and what constitutes success. A reviewer reading only the assertion line should understand what was tested and whether the outcome is correct.

### Response Comparison

When comparing responses, exclude non-deterministic fields:

```bash
# Strip timestamps and IDs before comparison
jq 'del(.timestamp, .requestId, .traceId)' before.json > before-clean.json
jq 'del(.timestamp, .requestId, .traceId)' after.json > after-clean.json
diff before-clean.json after-clean.json
```
