# Local reproduction

For the mechanism-verifier: building, starting and exercising a service locally for safe,
non-mutating reproduction. Self-contained so this skill has no cross-plugin dependency.

## Auth

If the service talks to a cloud provider, verify local credentials before anything else (for GCP,
`gcloud auth application-default print-access-token >/dev/null 2>&1`; for AWS, `aws sts
get-caller-identity`). If that fails the developer needs to log in; you do not. Then look for a
local, often `.gitignore`d, override config (`*-user.conf`, `.env.local`, `application-local.yml`)
in the project root or its resources directory.

For services that call an LLM gateway or another identity-checked service, the credential is usually
an impersonated service-account token or an API key named in config. Find the variable names in the
service's own config and README; never invent one.

| Variable | Purpose | Required? |
| --- | --- | --- |
| Service-discovery or environment variable the service reads at boot | Selects the environment or region it resolves dependencies in | When the service reads one |
| `GOOGLE_APPLICATION_CREDENTIALS` (or the provider's equivalent) | Path to a key or ADC file | If not using the default credential path |
| LLM or gateway credentials named in the service's config | Token generation for model calls | LLM-backed services only |

**On an auth failure, do not reach for a config change first.** Check whether enforcement is already
off in the checked-in local config, since there is usually nothing to weaken, and changing an
enforcement flag yourself needs explicit user permission in auto-mode. Try the remediation command,
check integration-test configs that bypass auth, or reproduce out of tree (below). Only when every
attempt fails, report INCONCLUSIVE with the exact error and each remediation tried.

## Build detection and startup

**Scan the component's own directory, walking up only until you hit a build file. Do not scan the
repository root:** in a monorepo the root may carry no build file while dozens of unrelated
`pom.xml` or `package.json` files sit in test fixtures elsewhere, so a repo-wide search routes you
to the wrong build tool for a component another one actually builds. Measured: a component built by
Bazel had no `pom.xml` at any level, while 62 fixture `pom.xml` files elsewhere pointed at Maven.

| File | Build | Build command | Startup |
| --- | --- | --- | --- |
| `pom.xml` | Maven | `mvn clean compile -U` | `mvn exec:java -Dexec.mainClass="<pkg>.Main"` |
| `build.gradle(.kts)` | Gradle | `./gradlew build -x test` | `./gradlew run` |
| `BUILD` / `BUILD.bazel` | Bazel | `bazel build //path:target` | `bazel run //path:target` |
| `pyproject.toml` / `setup.py` | Python | `uv sync` or `pip install -e .` in a fresh venv | the entry point the project declares |
| `package.json` | Node | `npm ci` | the `start` script |
| `build.sbt` | SBT | Not supported | Report INCONCLUSIVE |

For a JVM service, find the main class with `find . -name "Main.java" -path "*/main/java/*" | head
-5` and take the fully qualified name from the package declaration. Read the ports from the
service's own config rather than assuming: common defaults are 50051 or 5990 for gRPC, 8080 for
HTTP, and a separate health/metrics port.

**Often you should not start the service at all.** If the reproduction plan is unit-level - one
method, one class, a config parse - booting a server and sending a request through it is the proxy
the method section tells you not to use. Reproduce at the level the plan names and record which
level you chose.

Run **one** startup command, matching the build system you detected. Never two: they bind the same
ports and the second would orphan the first process.

```bash
mvn exec:java -Dexec.mainClass="<pkg>.Main" > /tmp/service-stdout.log 2>&1 &
echo $! > /tmp/service.pid
```

**The PID goes to a file, not a shell variable, because your shell state does not survive between
tool calls** - a later teardown reading `$SERVICE_PID` finds it empty and kills nothing. Check the
file exists on teardown so "there was nothing to stop" stays distinguishable from "stopped it": a
teardown you believe succeeded but which left the process running is the usual cause of the port
collision the next candidate's verifier hits.

```bash
if [ -s /tmp/service.pid ]; then
  kill "$(cat /tmp/service.pid)" && rm -f /tmp/service.pid
else
  echo "NO PID FILE -- service was never started, or a previous teardown already ran"
fi
```

Poll readiness for up to 60 seconds:

```bash
for i in $(seq 1 30); do
  if grpcurl -plaintext -max-time 2 localhost:"$GRPC_PORT" grpc.health.v1.Health/Check 2>/dev/null | grep -q SERVING; then
    echo "Service ready"; break
  fi
  sleep 2
done
```

Fallback for an HTTP service: poll its health or readiness endpoint with
`curl -s -o /dev/null -w '%{http_code}'` until it returns `200`.

## Reproducing without writing into the source tree

Your agent definition forbids adding files to the component's test tree. Compile out of tree
against the component's own classpath where the build can give you one - a Bazel deploy jar or a
Maven/Gradle runtime classpath already contains every production class:

```bash
cd "$CHECKOUT"        # the repo root the finders read; not a fixed path
bazel build //path/to/component:component_deploy.jar
CP=bazel-bin/path/to/component/component_deploy.jar
PROBE="$(mktemp -d /tmp/probe-XXXXXX)"   # unique dir; NOT a shared /tmp/probe
mkdir -p "$PROBE"          # write "$PROBE/LocalProbe.java" first
javac -cp "$CP" -d "$PROBE" "$PROBE/LocalProbe.java"
java -cp "$CP:$PROBE" LocalProbe
```

For Python, the same idea is a probe script in a `mktemp -d` directory run with the project's own
interpreter and `PYTHONPATH` pointing at the checkout; for Node, a probe file outside the tree that
`require`s or imports the module by absolute path.

That sequence exercises real production code with nothing written inside the checkout. Four traps,
each costing a cycle:

- **Some Bazel repos label test targets by source path.** A label like `//pkg:ConfigUtilsTest` may
  not exist while `//pkg:src/test/java/com/example/utils/config/ConfigUtilsTest` does. Run
  `bazel query 'kind("java_test", //<pkg>:*)'` rather than guessing.
- **`javac` succeeding proves nothing about a name you passed to `Class.forName`**, since that
  argument is just a string. Confirm the package from the source file's own declaration, or your
  probe compiles cleanly and fails at runtime.
- **Give the probe directory a per-invocation name.** Verifiers run concurrently by design, and on
  one run two both used `/tmp/probe` and one deleted the other's files mid-reproduction. Use
  `mktemp -d`. **Do not use `$$`**: in a subshell it reports the *parent* shell's PID, so two
  concurrent probes land in the same directory - verified, and it was the first fix attempted.
- **Name the class neutrally** (`LocalProbe`, not `CheckoutSlotRestrictionProbe`). A candidate-named
  file is a blindness leak even outside the repo.

If the repository's build config uploads build events or uses a remote cache by default (a
`.bazelrc` with a BES endpoint, a Gradle build scan), a build makes a network write you did not
choose. Not an outbound action in the prohibited sense, but say so in your evidence trail rather
than leaving it undisclosed.

## Common startup blockers

Check each against the error output, attempt the fix, retry startup with another 60 seconds.

| Blocker | Symptom | Fix |
| --- | --- | --- |
| Secrets-manager lookup | A missing-secret exception at boot | Use the override the service's local config documents, or an in-memory/local backend for the store that needs it |
| PubSub connection | Publisher creation fails | `gcloud beta emulators pubsub start --project=<project> --host-port=localhost:8085`, then point the client at the emulator |
| Service discovery | Channel creation fails for a discovery-scheme target | Set the environment/region variable the service reads, or override the target with a `localhost` address |
| Service auth | Auth enforcement blocks local calls | Prefer an out-of-tree probe (avoids the auth layer and adds no file to the test tree); check whether enforcement is already off locally |
| Event or telemetry sender | Sender initialization fails | Use the no-op sender the local config offers |
| Remote config | Remote config resolution fails | Disable remote config in the local override |

Also check the project's integration tests for config overrides, and look for an existing, often
`.gitignore`d, local config file.

## Requests, validation, and before/after

```bash
grpcurl -plaintext -max-time 60 -d '{"field_name": "value"}' localhost:"$GRPC_PORT" package.ServiceName/MethodName
curl -s -X POST http://localhost:8080/api/path -H "Content-Type: application/json" -d '{"field": "value"}'
```

Validate deterministic fields by exact match or enum check; for non-deterministic ones (LLM output,
timestamps, IDs) verify presence, type and reasonable length rather than exact content. Strip them
with `jq 'del(.timestamp, .requestId, .traceId)'` before diffing.

**Before/after**, when the comparison would strengthen the evidence: capture "after" on the current
state; stop the service; `git stash && git checkout <base>`; build, start, poll (this rewrites
`/tmp/service.pid`, so the next stop picks up the base-state process); capture "before" with the
same requests; stop; `git checkout <branch> && git stash pop`; rebuild. Then verify the specific
behavioural difference.

**Never push and never open a PR. Local git commits only.**
