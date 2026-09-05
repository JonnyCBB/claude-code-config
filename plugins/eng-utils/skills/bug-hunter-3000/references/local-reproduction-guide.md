# Local Reproduction Guide

Procedures for the mechanism-verifier subagent to build, start, and test a
service locally for safe, non-mutating reproduction of a candidate
bug's mechanism hypothesis. Ported from the jbb-feature-dev plugin's
verify-implementation live-testing methodology so this skill has no
cross-plugin dependency.

## Authentication prerequisites

### Auth failure handling

If any auth check fails:

1. Report which check failed and the exact error.
2. Investigate common fixes first -- try the remediation command (e.g.
   `gcloud auth application-default login`), check for integration test
   configs that bypass auth, or reproduce out of tree against the component's
   classpath (see "Reproducing without writing into the source tree" below).
   Do not reach for a config change first: the real key is
   `serviceauth.enforcing`, not `serviceauth.enabled`, and it is already false
   in the checked-in conf, so there is usually nothing to weaken. Setting it
   yourself requires explicit user permission in auto-mode (classified as
   auth-weakening).
3. Re-run the failed check after attempting fixes.
4. Only if ALL remediation attempts fail: report the auth failure as
   INCONCLUSIVE with the exact error and each remediation attempted.

## Service startup procedures

### Build system detection

Detect the project's build system from its manifest, then use its own documented run command:

| Marker                        | Build system | Build                    | Run locally                |
| ----------------------------- | ------------ | ------------------------ | -------------------------- |
| `package.json`                | Node/npm     | `npm ci`                 | `npm start` / `npm run dev` |
| `pyproject.toml` / `setup.py` | Python       | `uv sync` / `pip install -e .` | the project's entry point or `uvicorn`/`flask` command |
| `Makefile`                    | make         | `make build`             | `make run`                 |
| `docker-compose.yml`          | compose      | `docker compose build`   | `docker compose up`        |

Read the project's own README or `scripts` block before inventing a command.

### Standard ports

| Port | Protocol | Purpose                 |
| ---- | -------- | ----------------------- |
| 5990 | gRPC     | Primary gRPC server     |
| 8080 | HTTP     | HTTP server / REST API  |
| 5700 | HTTP     | Health/metrics |

### Reproducing without writing into the source tree

Your agent definition forbids adding files to the component's test tree. Reproduce **out of tree**
instead: build or install the component, then drive it from a scratch directory that imports the
real production modules. The goal is to exercise real production code with nothing written inside
the checkout.

```bash
PROBE="$(mktemp -d /tmp/probe-XXXXXX)"   # unique dir; NOT a shared /tmp/probe -- see below
# write your probe script into "$PROBE", then run it against the installed package
```

Two gotchas that will cost you a cycle each. **Do not guess test target or module names** -- ask the
build system what exists (`pytest --collect-only`, `npm run -l`, or the equivalent query) rather than
inferring a name from the class or file. And **a successful build proves nothing about a name you
passed to a dynamic import** (`importlib.import_module`, `require()`, `Class.forName`), since that
argument is just a string: confirm the module path from the source file itself, or your probe will
build cleanly and then fail at runtime.

**Give the directory a per-invocation name.** Verifiers run concurrently by design, and a fixed
shared path is a collision: on one run two verifiers both used `/tmp/probe` and one deleted the
other's files mid-reproduction. Use `mktemp -d`, which is guaranteed unique. Do **not** use `$$`: in
a subshell it reports the *parent* shell's PID, so two concurrent probes started that way land in the
same directory -- verified, and it was the first fix attempted here. Name the probe neutrally too
(`LocalProbe`, not `M3P3SlotRestrictionProbe`) and keep it under `/tmp` or the session scratchpad. A
candidate-named file is a blindness leak even when it sits outside the repo, and one measured run
recovered this exact pattern only by inventing it from scratch.

If your build tool uploads build events to a remote cache or analytics service by default, note that
a build makes a network write you did not explicitly choose. That is not an outbound action in the
sense section 2 prohibits -- nothing is created, commented on, or notified -- but say so in your
evidence trail rather than leaving it undisclosed.


### Readiness polling

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

## Common local startup blockers

Before giving up, check each row against the error output and attempt any
matching fixes, then retry startup (allow another 60 seconds).

| Blocker                 | Symptom                                     | Solution                                                                                                                                                                                                                                             |
| ----------------------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Secret-store lookup failure | `MissingSecretException`             | Point the client at a local secret override in the service config, and set a local namespace |
| PubSub connection       | Publisher creation fails                    | Run `gcloud beta emulators pubsub start --project=<project> --host-port=localhost:8085` and set `pubsub.use-emulator: true` in user conf                                                                                                             |
| Service discovery resolution | Channel creation fails for internal service targets | Point the client at the right discovery domain in the service config, or via its documented env var |
| Service auth            | Auth enforcement blocks local calls         | Prefer an out-of-tree probe against the component classpath (avoids the auth layer entirely, and does not add a file to the test tree, which your definition forbids); the real key is `serviceauth.enforcing`, already false in the checked-in conf |
| Event sender            | EventSender initialization fails            | Set `event-sender.noop-enabled: false` in user conf                                                                                                                                                                                                  |
| Remote config           | RemoteConfig resolution fails               | Set `remoteconfig.enabled: false` in user conf                                                                                                                                                                                                       |

Also check the project's integration tests (often `ContainerIT.java` or
similar) for config overrides needed for local execution, and look for an
existing `-user.conf` file (often `.gitignored`).

## Request construction patterns

### gRPC requests

```bash
grpcurl -plaintext -max-time 60 -d '{
  "field_name": "value"
}' localhost:5990 package.ServiceName/MethodName
```

### REST requests

```bash
curl -s -X POST http://localhost:8080/api/path \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}'
```

## Response validation

- Deterministic fields: exact match or enum check against expected values.
- Non-deterministic fields (LLM output, timestamps, IDs): verify presence,
  type, and reasonable length -- do not compare exact content.
- Before/after comparison: strip non-deterministic fields with
  `jq 'del(.timestamp, .requestId, .traceId)'` before diffing.

## Before/after execution procedure

When a before/after comparison would strengthen the evidence:

1. Capture "after" responses on the current state (service already running).
2. Stop the service: `kill "$(cat /tmp/service.pid)"`.
3. Checkout the base state: `git stash && git checkout <base>`.
4. Build and start service on the base state; poll for readiness. This rewrites
   `/tmp/service.pid`, so step 6 picks up the base-state process, not the one from step 2.
5. Capture "before" responses with the same requests.
6. Stop the base-state service: `kill "$(cat /tmp/service.pid)"`.
7. Return to the candidate state: `git checkout <branch> && git stash pop`.
8. Rebuild and restart for any remaining work.
9. Compare: verify the specific behavioral difference between before and after.

Never push, never open a PR. Local git commits only.
