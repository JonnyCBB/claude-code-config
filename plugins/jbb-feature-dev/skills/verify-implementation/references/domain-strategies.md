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

1. Capture relevant file contents and command output from the feature working tree,
   including the recorded staged, unstaged, and untracked scope. Preserve exit statuses.
2. Create a separate detached baseline worktree at the recorded base commit using Git's
   worktree add operation and detach option. Record its path and commit. Do not stash,
   switch, reset, or clean the feature checkout, and do not copy secrets into the baseline.
3. Run the same relevant local commands in the baseline directory with separate output paths.
   Record missing files or commands as actual observations. Do not suppress failures or
   claim a comparison if the baseline cannot execute the required check.
4. Compare expected differences and relevant unchanged behavior against the captured output.
   Confirm the feature checkout and its changes remain intact. Retain the baseline worktree
   and report its path; do not delete it or its artifacts without explicit authorization.

## Backend API Domain

For changes to gRPC or REST services.

For local service startup, scenario generation, validation, and isolated baseline comparison,
see `live-testing-guide.md` (invoked in Step 8). Reuse those results in Step 9 rather than
restarting services or repeating requests. Keep both service calls and dependencies local.

### Verification Techniques

- **gRPC requests**: `spgrpcurl` or `grpcurl` request/response pairs
- **REST requests**: `curl` request/response pairs
- **Response field extraction**: Use `jq` or `grpcurl -format json` for targeted comparison (skip timestamps, request IDs, trace IDs)

### Before/After Procedure

Follow the Before/After Execution Procedure in `live-testing-guide.md`. Capture feature
responses from the recorded working-tree state and baseline responses from the separate
worktree at the recorded base commit. Use identical local inputs and separate logs, build
artifacts, and ports. Preserve raw responses and exit statuses. A baseline startup blocker
leaves the comparison unverified. Do not switch the feature checkout or remove either
worktree without authorization.

## Common Patterns

### Retry Logic

Retry only when captured evidence supports a transient local failure. Preserve each
attempt's output and status; do not hide an earlier failure behind a later success.
Use bounded retries with a timeout, not an indefinite wait.

### Assertion Format

Use consistent assertion format in evidence documents and any optional local wrapper:

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
