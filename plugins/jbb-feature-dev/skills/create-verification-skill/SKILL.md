---
name: create-verification-skill
description: >
  AUTHORS A NEW REUSABLE SKILL. Interviews a repo and writes `.claude/skills/verify-<app>/` plus a
  feature map, so the repo gains a permanent, scripted way for anyone to drive the service and
  capture evidence later. The deliverable is the skill file, not a test run. Use whenever someone
  wants to "set up", "build", "generate" or "create" a way to prove a service works, wants a
  verification or control skill for a repo, says a repo's only proof of behaviour is its unit
  tests, or asks for a feature map. Reach for this even when they phrase it as wanting to drive or
  prove the app, because the ask is for the durable harness.
  NOT for launching the app once to see a change working now (that is /run), NOT for checking one
  plan's implementation (that is /jbb-feature-dev:verify-implementation), NOT for auditing a
  verification skill that already exists (that is /jbb-feature-dev:maintain-verification-skill), and
  NOT for writing unit tests.
---

# Create a verification skill

Every serious service needs a scripted way to drive the real thing and prove behaviour: start it,
exercise a path a caller actually takes, capture evidence. This skill generates that as a
**project-local** skill at `.claude/skills/verify-<app>/`, tailored to the repo.

**Write the output for the next agent, not for a human.** It will be read cold, mid-task, by an
agent that has never seen this service.

## How this differs from `/verify-implementation`

They are complements, and both should exist.

| | `/verify-implementation` | the skill this generates |
| --- | --- | --- |
| Driven by | one TDD plan | the repo's user-facing features |
| Lifetime | one-shot, per change | persistent, maintained |
| Answers | "did this plan land correctly?" | "does this service still work?" |

`/verify-implementation` stays the pipeline step. This adds the project-persistent layer it does
not cover.

## 1. Interview the repo, not the user

Answer these from the codebase. Ask only what you genuinely cannot observe.

- **Surface — what does a caller actually touch?** Usually one of: an HTTP/gRPC service, a data
  pipeline, a served ML model, a search index, or a web frontend. A repo can have several — pick
  the primary and note the rest.
- **Run — how does it start locally?** Prefer the repo's own documented command, and note ports,
  env vars, seed data and auth. **Local, not deployed** — the standing rule in `~/.claude/CLAUDE.md`
  is to verify against local services.

  **A service inside a monorepo often has no per-service run command, and does not need one.**
  Where that is the case, the answer is
  uniform:

  ```sh
  bazel run //system/component        # builds and runs the Java process locally, outside Docker
  ```

  That works when `BUILD.bazel` carries a target named the same as the directory, which is the
  convention; when it does not, name it (`bazel run //system/component:target-name`). Read the
  `BUILD.bazel` for the service target rather than guessing. Look in the repo's own docs for how it
  runs a component locally, sets env vars, and exposes a debug port.

  Three rules that hold in a large Bazel monorepo (check the repo's own `CLAUDE.md` or
  `AGENTS.md` for its version), each a trap an agent walks into unprompted:

  - *"Target specific packages — never `bazel build //...`"*. At monorepo scale an unscoped
    build is unusable rather than merely slow. The same reasoning applies to `bazel test //...`.
  - *"NEVER use `bazel clean` — the cache handles invalidation"*. This is the one to remember,
    because a service that will not start is exactly when reaching for `clean` feels right.
  - *"NEVER modify `.bazelrc` files or shared build configuration"*.

  Do not write "no documented start command" into the generated skill when the service is in the
  monorepo. Write the `bazel run` line, and say which target it resolves to.
- **Drive — how can an agent interact programmatically?** Existing harnesses first: integration
  tests, curl-able endpoints, `grpcurl`, a debug port, a local pipeline runner.
  Only then a generic recipe.
- **Observe — what evidence can be captured?** Response bodies, gRPC status codes, log lines,
  emitted rows, BigQuery output, index documents, exit codes, screenshots.
- **Isolate — can two instances run side by side?** Ports, data dirs, profiles. If not, say so in
  the generated skill: refusing to double-drive a shared instance beats corrupting a live one.

If the checkout does not build or start as-is, **fix that first or report it precisely** before
generating. A skill written against a broken base teaches wrong steps. When an irrelevant missing file blocks startup, the generated skill may create it, only if it is absent, marked as verification scaffolding. The skill records that it created the file and removes it in Cleanup only if this run created it. It never overwrites an existing file.

### Surfaces worth naming explicitly

- **HTTP/gRPC service** — health endpoint plus one real request. A health check alone proves the process
  is up, not that it serves.
- **Data pipeline** — a local run over a small fixture partition, then assert on the output rows,
  not on "the job exited 0".
- **Served model** — a real inference request with a known input, asserting on the response
  shape and slot version.
- **Search index** — feed one document, then query it back. Feed success is not queryability.

## 2. Generate the skill

Write `.claude/skills/verify-<app>/SKILL.md` with YAML frontmatter (`name: verify-<app>`, and a
`description` naming the service, the surface and when to reach for it — **without frontmatter the
skill never registers**). Every section must be grounded in what the interview actually found. No
placeholders.

- **Launch** — the exact command, and how to tell it is ready (a log line, a port answering). It must reach a usable state from an empty data directory, including migrations and seed data. Ready means usable, not that a process answers: a database health check can pass while its init scripts still run. Record the process ID of each process you start. Check that the tools the scripts need are installed, and stop with a clear message if one is missing. For a short-lived job there is no server: launch means build once, then drive each run in isolation.
  Include teardown.
- **Doctor** — one read-only check answering "is this instance worth driving?": process up, right
  build, port owned by us, auth valid. Run it first whenever anything looks off.
- **Drive** — the harness recipe with real endpoints, real RPC names and real fixtures from this
  repo. Prefer stable handles (route paths, method names, data attributes) over positional ones.
- **Evidence** — what to capture and where it goes. State the proof standards: exercise the real
  caller path, not internal setters or test-only endpoints; capture the action *and* the resulting
  state; verify side effects (rows written, messages published) alongside what is returned; mock
  only where a production boundary already isolates the external system. Where the safe path is a
  dry-run, **verify what it actually skips by observing** rather than trusting its name.
- **Cleanup** — tear down what this run started. **Never kill by process name; kill what you started.** Stop each recorded process and its child processes, because a dev server often starts a child that owns the port. Cleanup removes instances and scratch state, never the evidence — proof artifacts
  survive teardown, at a location the skill names.
- **Helpers** — any script the skill ships is executable and its invocation is shown in the skill
  body. A helper the reader must reverse-engineer is not a helper.

## 3. Seed the feature map

Create `.claude/skills/verify-<app>/features/README.md` as an index, plus one file per user-facing
feature, taken from routes, RPC methods, pipeline outputs or docs. Seed the ones a caller would
actually notice breaking, and stop when the next one you would add is not one of those. The map is
meant to grow through `/jbb-feature-dev:maintain-verification-skill`, so an honest partial map beats a padded one. Start with three to five features. The shape is in [references/feature-map-example](references/feature-map-example/README.md).

Each feature file uses these four H2s:

- `## Sub-features`
- `## How to get to it (caller POV)`
- `## Driving it with <harness>`
- `## Gotchas`

If the seed data lacks a precondition a journey needs, the journey reports a failure and the reason goes in that feature's `Gotchas`. Never weaken the journey to make it pass.

The map is the repo's maintained verification source. **A proof that drives one convenient entry
point is incomplete when the map lists others.**

## 4. Review and prove the generated skill before handing it over

**Review it with `/jiffy-toolkit:context-and-skills-standards` and apply what it finds.** What you
have just written is a single-pass generated skill, which is the one kind the evidence says
underperforms; the standards exist to catch that before it ships. Expect the findings to be
instructions that do not earn their tokens and any limit stated in two places.

**Then run its own instructions end to end, once:** launch, doctor, drive **one** mapped feature
(one is enough; the map exists so later runs can cover the rest), capture evidence, clean up. After cleanup, confirm the evidence still exists at the named location.
A cleanup that eats its own proof fails this step.

Fix what fails, and run the generated cleanup after every failed iteration too, so broken attempts
do not strand processes and ports. If you proved the skill in a stand-in for the real target, list every setup step the stand-in did that the target will not do. Those steps stay unverified until a run on the real target covers them.

**A generated skill that was never reviewed and never executed is a draft, not a deliverable.**

## 5. Offer the maintenance loop

Point the user at `/jbb-feature-dev:maintain-verification-skill`, which keeps the map honest as the
service changes. A feature map without maintenance decays into a confident lie. Suggest a cadence
only if asked.
