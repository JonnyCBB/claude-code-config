---
name: validation-contract-generation
description: >
  Generate a validation contract from acceptance criteria in a requirements document.
  Produces testable assertions with stable IDs grouped by detected domain (Backend API,
  Data Engineering, ML). Called by /orchestrate-feature-dev before planning. Trigger
  phrases: (1) "generate validation contract" (2) "contract from requirements"
  (3) "validation-contract-generation".
argument-hint: "--requirements <path> [--non-interactive] | --amend --contract <path> --review-doc <path> [--review-doc <path2>] [--non-interactive]"
---

# Validation Contract Generation

Generate a validation contract that maps acceptance criteria from a requirements document
into domain-aware, testable assertions. Each assertion follows the 4-phase protocol
(Setup/Stimulus/Assertion/Evidence) and receives a stable ID for traceability.

## Step 1: Mode Detection

Parse `$ARGUMENTS` for flags and input:

- `--requirements <path>`: path to the requirements document (mandatory in generate mode)
- `--non-interactive`: skip interactive clarification gates, choose conservative interpretations autonomously
- `--amend`: activates amendment mode (mutually exclusive with `--requirements`)
- `--contract <path>`: path to existing frozen contract (mandatory in amend mode)
- `--review-doc <path>`: path to a code review document; can be specified multiple times (mandatory in amend mode, at least one required)

**Mode branching**:

- If `--amend` is present: validate that `--contract` and at least one `--review-doc` are provided. If either is missing, halt with an error. Then skip Steps 2-6 and jump directly to Step 7 (Amendment Steps).
- If `--requirements` is present: proceed with Steps 2-6 (Generate mode).
- If neither `--amend` nor `--requirements` is present, halt immediately with an error:

      ERROR: Either --requirements <path> (generate mode) or --amend --contract <path>
      --review-doc <path> (amendment mode) is required.

## Step 2: Read and Parse Requirements

1. Read the requirements document fully using Read without limit/offset.

2. Extract all acceptance criteria blocks matching the pattern `AC-N:` followed by GIVEN/WHEN/THEN clauses. Collect each AC's identifier (e.g., `AC-1`, `AC-2`) and its full text.

3. If no `AC-N:` blocks are found, halt with an error:

   ERROR: No acceptance criteria found. The requirements document must contain
   AC-N: blocks with GIVEN/WHEN/THEN clauses.

4. Print a summary of discovered ACs:

   Found N acceptance criteria: AC-1, AC-2, ..., AC-N

## Step 3: Domain Detection

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` and run the 4-pass domain detection procedure against the codebase (changed files, referenced files, and files mentioned in the requirements document). Use file triggers first, then strong signals, then corroborating signals, then fallback.

2. Read `references/domain-templates.md` for all domain templates: Data Engineering, ML, Backend API, and Unknown Domain. Every domain has a template -- use it.

3. Print detected domains:

   Detected domains: [Backend API, Data Engineering, ML, ...]
   Loaded domain templates: [list of templates loaded]

If no domains are detected, note that the Unknown Domain template will be used for all assertions.

## Step 3b: Verification Strategy Classification

Each acceptance criterion can produce **multiple** assertions across different categories. Categories are NOT mutually exclusive -- a single AC can be both live-testable AND code-inspectable, and in that case BOTH assertion types are generated.

| Category                  | What It Proves                                                       | When to Generate                                                                                                     |
| ------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Live service test**     | The feature works end-to-end when you actually use it                | Always for Backend API / Frontend when a runnable service exists. At least one per distinct endpoint/RPC under test. |
| **Unit/integration test** | The code logic is correct in isolation                               | Always as baseline -- test suite must pass                                                                           |
| **Code inspection**       | The code follows required patterns, files exist, schemas are correct | When AC specifies structural requirements (uses base class X, file at path Y)                                        |
| **Deferred**              | Requires production data or traffic                                  | When AC involves metrics, latency budgets, A/B test neutrality                                                       |

**Multi-category rule**: For each AC, consider ALL categories. If an AC says "GIVEN a search query WHEN the user submits THEN results contain track URIs AND the handler uses the AbstractSearchHandler base class" -- that AC gets both a live service test assertion (send request, check response) AND a code inspection assertion (grep for base class usage).

**Live testing policy**: Live testing -- starting the service locally and sending real requests -- is the strongest form of verification evidence. It proves the implementation works end-to-end in a way that unit tests cannot.

- **Default**: ALWAYS attempt live testing for Backend API and Frontend domains.
- **Minimum**: At least one live service test per distinct endpoint/RPC being modified.
- **Exception**: Only skip when technically impossible (pure library with no runnable service, data pipeline with no server). When skipping, set `live_testing: false` in the contract frontmatter with `live_testing_skip_reason`.

## Step 4: Generate Assertions (single-agent -- no negotiation loop)

For each acceptance criterion (`AC-N`), generate one or more assertions following the 4-phase protocol. Read `references/contract-output-template.md` for the output structure.

For each AC:

1. **Map AC to detected domain(s)**: determine which domain(s) the AC pertains to based on the entities, operations, and vocabulary used in the GIVEN/WHEN/THEN clauses.

2. **Select assertion template**: use the matching section from `references/domain-templates.md`:
   - Backend API -> Backend API template
   - Data Engineering -> Data Engineering template
   - ML -> ML template
   - Any other domain or no detected domain -> Unknown Domain template

3. **Assign stable ID**: use the format `VAL-<DOMAIN>-NNN` where:
   - `<DOMAIN>` is a short domain code: `API` for Backend API, `DATA` for Data Engineering, `ML` for ML, `GEN` for generic/unknown
   - `NNN` is a zero-padded sequential number within that domain, starting at 001
   - Examples: `VAL-API-001`, `VAL-DATA-001`, `VAL-ML-001`, `VAL-GEN-001`

4. **Specify tolerance** for each assertion:
   - Exact match: for deterministic outputs (status codes, schema fields, boolean conditions)
   - Threshold range: for numeric outputs with acceptable variance (latency P99 < 200ms, accuracy > 0.95)
   - Retry-with-delay: for eventually-consistent operations (data pipeline completion, async event propagation)

5. **Fill in all 4 phases** for each assertion:
   - **Setup**: preconditions, test data, environment state
   - **Stimulus**: the action or command that triggers the behavior under test
   - **Assertion**: the expected outcome with tolerance specification
   - **Evidence**: the execution command, log snippet, or output that proves the assertion passed

   **Stimulus/AC fidelity self-check**: before finalizing each assertion, re-read the AC's GIVEN/WHEN clause and confirm the literal Setup/Stimulus command actually creates that exact condition (not a related-but-different one). A command missing a flag, mode, or precondition the AC depends on (e.g., an AC describing a fresh session tested with a Stimulus that reuses existing session state) can pass its own Assertion check while proving nothing about the AC — Step 5's Coverage Auditor review checks for this independently, but do not rely on it to catch what a moment of re-reading would have caught here.

6. **Handle ambiguity**: if an AC is genuinely ambiguous (multiple contradictory interpretations exist):
   - Interactive mode: halt and ask the user to clarify that specific AC before proceeding
   - Non-interactive mode: document the ambiguity in the assertion's notes field and choose the most conservative interpretation (the one that requires the strictest verification)

7. **Live testing enforcement** (Backend API / Frontend domains): after generating all assertions, count the live service test assertions (those whose Setup block starts a service process). If the count is zero and a runnable service exists, generate additional live testing assertions using the Backend API template from `references/domain-templates.md` until at least one live assertion exists per distinct endpoint/RPC under test. If no service can be started (the codebase is a pure library with no main class), set `live_testing: false` in the frontmatter with an explanation in `live_testing_skip_reason`.

## Step 5: Review Generated Contract

Run multi-persona review on the generated assertions before writing the contract.

See `references/review-personas.md` for persona definitions, prompt template, and iteration rules.

1. **Spawn both reviewer agents in parallel**: Coverage Auditor (model: sonnet) and Live Testing Enforcer (model: opus). Pass each reviewer: the generated assertions from Step 4, the AC list from Step 2, the domain detection results from Step 3, and the live testing policy from Step 3b. **Agent delivery resilience**: if a reviewer sends an `idle_notification` without content, prompt it via SendMessage using its agent ID (not name); if still no delivery, respawn once; if respawn fails, document the gap and proceed with the other reviewer's findings.

2. **Collect and synthesize feedback** using the Review Synthesis Format from `references/review-personas.md`. Categorize each item as Must Address / Should Consider / Minor.

3. **If "Must Address" items exist**: revise the assertions to address them and re-run the review (max 3 total iterations).

4. **If no "Must Address" items after any iteration**: auto-approve and proceed to Step 6 (Write Contract).

5. **If "Must Address" items persist after 3 iterations**: hold the gate, but preserve the work.

   The gate itself is right and stays: no contract is written past an unresolved Must Address, and assertions may be added but never weakened to pass review. What must change is what the halt leaves behind. Do all three:

   1. **Write the iteration-N draft to a durable path** derived from the intended contract path by replacing the `.md` suffix with `.draft.md` — so `…-verification-contract.md` becomes `…-verification-contract.draft.md`, sitting alongside the contract it will become. Never leave it only in session-scoped scratch. Include the review synthesis and which items are unresolved.
   2. **Return `STATUS: question`**, not a silent non-zero exit. Enumerate each unresolved Must Address item, the reviewer that raised it, the draft path, and your recommended resolution, so the caller can adjudicate.
   3. **State that recovery is a targeted fix to the preserved draft, not regeneration.**

   **Why:** this halt fired in three sessions and each time returned `STATUS: failed. ARTIFACT: none written`, parking hours of work — one 11-assertion draft survived only in scratch that the agent itself flagged as non-durable. In every case the correct recovery was a small targeted fix (one was simply replacing a `<fresh-double-issued-code>` placeholder with a real code captured from a 302 `Location` header). In the third session the caller responded by respawning the whole stage, which regenerated an entire 8-assertion contract from scratch before discovering the original had already self-corrected and written a valid artifact. The reviewer loop was working correctly; only the artifact-discard policy was harmful. A halt should stop the pipeline, not destroy the draft.

**Non-interactive mode**: Spawn reviewer sub-agents (mandatory — self-review is NEVER a substitute). Run the full 2-iteration loop. Auto-resolve "Must Address" items; document each resolution in the contract's review synthesis section.

## Step 6: Write Contract

1. Construct the output filename: `~/.claude/thoughts/shared/contracts/YYYY-MM-DD-<slug>-verification-contract.md` where `<slug>` is derived from the requirements document filename (lowercase, hyphens, no extension).

2. Create `~/.claude/thoughts/shared/contracts/` if it does not exist.

3. Write the contract file using the structure from `references/contract-output-template.md`. Include YAML frontmatter with:
   - `requirements_path`: absolute path to the source requirements document
   - `domains_detected`: list of detected domains
   - `assertion_count`: total number of assertions generated
   - `live_testing`: `true` if at least one live service test assertion exists, `false` otherwise
   - `live_testing_skip_reason`: mandatory explanation if `live_testing: false` (e.g., "pure library -- no runnable service")
   - `live_assertion_count`: number of assertions whose Setup starts a service process
   - `unit_assertion_count`: number of assertions that use test frameworks (pytest, mvn test, etc.)
   - `status: frozen`

4. Print the absolute path to stdout:

   Contract written: /absolute/path/to/verification-contract.md
   Assertions: N total (X API, Y DATA, Z ML, W GEN)
   Status: frozen

## Amendment Steps (--amend mode only)

The following steps execute only when `--amend` is present. They append new assertions to an existing frozen contract based on code review findings. Original assertions MUST NOT be modified -- only new ones are appended.

### Step 7: Read Existing Contract and Inputs

1. Read the existing contract at the `--contract` path fully using Read without limit/offset.
2. Extract all existing assertion IDs (e.g., `VAL-API-001`, `VAL-DATA-002`) and the files they reference.
3. Read all `--review-doc` files fully.
4. Read `references/ignorelist.md` for default trivial file patterns to filter out.

### Step 8: Idempotent Cleanup

If the contract already contains a `## Amendments` section, delete it and everything below it to regenerate from scratch. This ensures the amendment process is idempotent -- running `--amend` multiple times with the same inputs produces the same output. Restore the contract to its pre-amendment state before proceeding.

### Step 9: Layer 1 -- Uncovered File Detection

1. Determine the base branch dynamically: `BASE=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')`; fall back to `main` if the symbolic ref is unset. Then run `git diff ${BASE}...HEAD --name-only` to get all changed files in the current branch.
2. Filter out files matching ignorelist patterns (from `references/ignorelist.md`).
3. Filter out files already referenced by existing assertions (extracted in Step 7).
4. Remaining files are "uncovered" -- they were changed but have no assertion coverage.

### Step 10: Layer 2 -- Actioned Recommendation Detection

1. Parse each `--review-doc` for recommendations under severity headings. Handle BOTH heading formats:
   - Canonical: `### Critical`, `### Major`, `### Minor`, `### Enhancement`
   - Variant: `### High`, `### Medium`, `### Low`
   - Mapping: High is equivalent to Major, Medium is equivalent to Minor, Low is equivalent to Enhancement

2. For each recommendation, extract: sequential number, file path (backtick-quoted), source agent, and description. Match by the presence of a sequential number and a backtick-quoted file path rather than rigid format matching.

3. Cross-reference against the diff: identify recommendations where the file appears in the diff AND has existing assertions that do not already cover the recommendation.

4. Deduplicate across multiple review docs when the same file appears in recommendations from multiple documents. Keep the highest-severity instance.

### Step 11: Generate Amendment Assertions

For each uncovered file (Layer 1) and each actioned recommendation (Layer 2):

1. **Assign stable ID**: use the format `VAL-AMD-NNN` where `NNN` is a zero-padded sequential number starting at 001 (e.g., `VAL-AMD-001`, `VAL-AMD-002`).

2. **Apply 4-phase protocol** (Setup/Stimulus/Assertion/Evidence) using the domain template from `references/domain-templates.md` that best matches the file's domain.

3. **Add provenance metadata** to each assertion:
   - `added_phase: post-code-review`
   - `added_reason`: For Layer 1: `"Uncovered file: <filename>"`. For Layer 2: `"Recommendation N (agent-name): summary text"`
   - `amendment_of: <original contract path>`

4. **Preserve originals**: MUST NOT modify original assertions -- only append new amendment assertions.

### Step 12: Review Amendment Assertions

Run multi-persona review on the newly generated amendment assertions only. Original frozen assertions are NOT in scope for this review.

See `references/review-personas.md` for persona definitions, prompt template, and iteration rules.

1. **Spawn both reviewer agents in parallel**: Coverage Auditor (model: sonnet) and Live Testing Enforcer (model: opus). Pass each reviewer ONLY the newly generated amendment assertions from Step 11. Include the amendment provenance metadata (added_phase, added_reason). Do NOT include the original frozen assertions.

2. **Collect and synthesize feedback** using the Review Synthesis Format from `references/review-personas.md`.

3. **If "Must Address" items exist**: revise the amendment assertions and re-run the review (max 3 total iterations).

4. **If no "Must Address" items**: auto-approve and proceed to Step 13 (Write Amendments to Contract).

5. **If "Must Address" items persist after 3 iterations**: hold the gate and preserve the work, exactly as in Step 5 — write the amendment draft to `<contract-path>.amendments-draft.md`, return `STATUS: question` enumerating each unresolved item with the reviewer that raised it and a recommended resolution, and state that recovery is a targeted fix to the preserved draft rather than regeneration. The amendments are not appended to the contract until the gate clears.

**Non-interactive mode**: Identical to Step 5 — spawn sub-agents (mandatory), run full 2-iteration loop, auto-resolve and document decisions.

### Step 13: Write Amendments to Contract

1. Append a `## Amendments` section after the `## Coverage Summary` section in the contract.

2. Write all amendment assertions under `## Amendments` using the same format as the original assertions.

3. Update the YAML frontmatter:
   - `status: amended` (changed from `frozen`)
   - `amendment_count: N` (number of new amendment assertions)
   - `amendment_phase: post-code-review`
   - `total_assertion_count: M` (original assertion count + amendment count)

4. Print summary to stdout:

   Contract amended: /absolute/path/to/verification-contract.md
   Original assertions: X
   Amendment assertions: N
   Total assertions: M
   Status: amended

## Reference Files

- **`references/review-personas.md`** -- Read at Steps 5 and 12 for review persona definitions, prompt template, synthesis format, and iteration rules.
- **`references/domain-templates.md`** -- Read at Step 3 for all domain verification templates (Backend API, Data Engineering, ML, Unknown Domain).
- **`references/contract-output-template.md`** -- Read at Step 4 for the output structure including YAML frontmatter schema and assertion block format.
- **`references/ignorelist.md`** -- Read at Step 9 for default trivial file patterns to exclude from uncovered file detection.

## Shared Registries (by path)

- `${CLAUDE_PLUGIN_ROOT}/skills/shared-references/domain-agent-registry.md` -- Read at Step 3 for the 4-pass domain detection procedure and domain expert agent definitions.
