# Domain Verification Templates

Templates for domain-specific verification patterns. Every domain has a template below —
use it instead of generating assertions from scratch.

---

## Data Engineering

### Setup

1. Build the project using the detected build system:
   - sbt: `sbt pack` or `sbt compile`
   - Maven: `mvn package -q -DskipTests`
   - Python: `pip install -e .` or verify virtualenv
2. Prepare test data or dry-run configuration:
   - Copy fixture files to expected input paths
   - Set pipeline config to use local/test mode

### Stimulus

1. Execute the workflow or pipeline test:
   - Python: `pytest tests/ -v` or `python -m workflow --dry-run`
2. For dry-run validation, execute with `--dryRun` or equivalent flag.
3. For error-path validation: supply malformed input (wrong schema, corrupt file, empty partition) and verify the pipeline fails gracefully with a meaningful error message rather than silent data loss.

### Assertion

1. **Exact match**: Process exit code equals 0
2. **Output existence**: Expected output files or partitions exist at target path
3. **Schema validation**: Output schema matches expected Avro/Parquet definition
4. **Annotation correctness**: Data annotations include required semantic types
5. **Counter checks**: Pipeline counters (row counts, error counts) within expected range
6. **Threshold**: Row count within 5% of expected value

### Evidence

1. Capture test suite stdout/stderr verbatim
2. Record execution logs showing pipeline stages completed
3. List output files with sizes: `ls -la output/`
4. Show counter summary from pipeline log output

---

## ML

### Setup

1. Initialize local training environment:
   - Ray: `ray start --head --num-cpus=2` or use `ray.init(local_mode=True)`
   - PyTorch: verify CUDA/CPU availability
2. Prepare synthetic dataset:
   - Generate minimal synthetic data (100-1000 samples) matching expected schema
   - Place in expected data directory or configure data loader override
3. Set training config to minimal epochs (1-3) for fast verification.

### Stimulus

1. Run training with synthetic data:
   - `python train.py --config test_config.yaml --max-epochs 2`
   - Or via Ray: `python -m trainer --num-workers 1 --use-gpu false`
2. Execute inference on a known test input:
   - `python predict.py --input test_sample.json --checkpoint latest`
3. Run the test suite: `pytest tests/ -v -k "not integration"`
4. For robustness checks: run inference with degenerate input (empty features, out-of-range values) and verify the model returns a sensible default or error rather than crashing.

### Assertion

1. **Parameter update**: Training loss decreased between epoch 1 and final epoch
2. **Metric threshold**: Accuracy/F1 exceeds baseline on synthetic data (loss < 1.0)
3. **Artifact produced**: Model checkpoint file exists at expected path
4. **Reproducibility**: Two runs with same seed produce identical metrics
5. **Retry tolerance**: Convergence may require 2-3 runs; pass if any run meets threshold

### Evidence

1. Capture MLflow metrics or training log showing loss curve
2. Record checkpoint file path and size: `ls -la checkpoints/`
3. Show inference output on test sample
4. Include training duration and resource usage from logs

---

## Backend API

### Setup

1. Detect build system from project root:
   - `pom.xml` → Maven: `mvn package -q -DskipTests`
   - `BUILD` / `BUILD.bazel` → Bazel: `bazel build //path:target`
   - `build.sbt` → SBT: `sbt pack` or `sbt assembly`
   - `pyproject.toml` → Python: `pip install -e .`
   - `package.json` → Node: `npm install && npm run build`
2. Start the service as a background process:
   - Maven uberjar: `java -jar target/*.jar &`
   - Python (FastAPI/Starlette): `uvicorn app:app --port 8080 &`
   - Python (Flask): `python -m flask run --port 8080 &`
   - Python (custom): `python -m <module> &`
   - Node: `node dist/server.js &` or `npm start &`
3. Poll for readiness (up to 60 seconds):
   - gRPC: `grpcurl -plaintext -max-time 2 localhost:5990 grpc.health.v1.Health/Check`
   - HTTP: `curl -sf http://localhost:8080/healthz`
4. For common local startup blockers, include workaround flags:
   - ServiceAuth: `-Dserviceauth.enabled=false`
   - EventSender: `-Devent-sender.enabled=false`
   - RemoteConfig: `-Dremoteconfig.enabled=false`

### Stimulus

1. For each AC, construct a request that exercises the GIVEN/WHEN/THEN path:
   - gRPC: `grpcurl -plaintext -d '{...}' localhost:5990 package.Service/Method`
   - REST: `curl -s -X POST http://localhost:8080/api/endpoint -H 'Content-Type: application/json' -d '{...}'`
2. Include requests for:
   - Happy path: the expected positive case from the AC
   - Edge case: boundary or special inputs mentioned in the AC
   - Negative case: what should NOT happen (from scope items marked "Not needed")

### Assertion

1. **Response field match**: Specific JSON fields match expected values
2. **Status code check**: HTTP status or gRPC status code matches expected
3. **Structural validation**: Response contains required fields (even if values are non-deterministic)
4. **Behavioral check**: Side effects observed (log entries, counter increments, state changes)

### Evidence

1. Capture the full request/response transcript: `curl -v ... 2>&1`
2. Record the service startup log: `tail -n 50 /tmp/service.log`
3. Include cleanup: `kill $SERVICE_PID`

### Server Lifecycle

Live service assertions share a single server lifecycle to avoid repeated start/stop overhead:

1. The first live assertion (e.g., `VAL-API-000`) handles startup and health-check as its own tracked assertion. If startup fails, this assertion is `blocked` and all dependent live assertions are also `blocked`.
2. Subsequent live assertions' Setup sections say: "Server already running from VAL-API-000 setup."
3. The last live assertion's Evidence section includes cleanup (`kill $SERVICE_PID`).

---

## Unknown Domain (On-the-Fly Protocol)

When no pre-built template matches the detected domain, use this universal protocol.
The 4-phase structure applies to any domain — adapt the specific tools to what the
project uses.

### Setup

1. Build the project using the detected build system (check for pom.xml, BUILD,
   build.sbt, pyproject.toml, package.json, Makefile)
2. If a runnable service or server exists: start it as a background process and
   poll for readiness
3. If no service exists: prepare test data or configuration

### Stimulus

1. If a service is running: send requests that exercise the changed functionality
2. If no service: run the test suite, execute CLI commands, or run scripts that
   demonstrate the changed behavior
3. Include at least one positive case (expected to succeed) and one negative case
   (expected to fail gracefully)

### Assertion

1. Process exit code equals 0 (for commands and tests)
2. Expected output produced at expected location
3. No regressions in existing test suite
4. Changed behavior matches the AC's THEN clause

### Evidence

1. Capture command stdout/stderr verbatim
2. Show output files with sizes: `ls -la output/`
3. Record diff of changed behavior if applicable
