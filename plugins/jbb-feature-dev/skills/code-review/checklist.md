# Review checklist

Report a finding only if you can quote the line, name the rule, and state the consequence. Zero findings is valid.

## Correctness
- Wrong result for an input the code accepts: off-by-one, inverted condition, wrong operator, unhandled null or empty.
- Behaviour removed or narrowed without the objective asking: dropped guard, error path, validation or field.
- Trace coupled calculations with accepted boundary inputs, not just default values. Check that derived values,
  thresholds and classifications agree. For example, runtime 21 minus ramp 10 leaves 11 at full population;
  a recommendation requiring 14 must not produce contradictory too-short and partial classifications.
- Compare results through sibling implementations, caller and consumer paths, and config; report inconsistent
  behaviour caused or carried into a new path by the change, not unrelated pre-existing bugs.
- Errors swallowed, lost or reported with the wrong code; async work not awaited; resources not released.
- Unreadable external data silently becomes a normal absence or a weaker check. Trace malformed present
  timestamps and unknown enum values to their fallback; require an observable failure or degraded result.
  Expected absence needs no warning or log; use an existing result, diagnostic or metric where appropriate.
- Check changed behaviour against comments, docstrings, error messages and schema/proto field contracts.
  Verify scope across data sources and actual formats, such as newline-delimited versus comma-separated text;
  do not leave an A/B-only contract describing a field now populated for rollouts.
- A bug is a finding even when a test passes; state the input that breaks it.

## Objective and scope
- The objective requires something the diff does not do.
- The diff does something the objective did not ask for: drive-by refactor, extra feature, option or config.
  Formatting-only churn is never a finding.
- Hidden assumptions: units, time zones, nulls versus other falsy values, ordering, uniqueness.

## Tests
- Assertions weakened, expected values changed, or tests deleted or skipped in the same diff as a code change.
- Would still pass if the implementation were subtly broken; feature claimed but not asserted.
- Mocks the unit under test, mocking outweighs the behaviour tested, or a stub returns the parameter mock.
- Flag low-value tests for removal or replacement when they only check:
  - Static mappings, e.g. `case X -> "Y"` returns `"Y"`.
  - Static configuration, e.g. configured filters produce their configured output.
  - Language implementation details, e.g. enum getters return their declared values.
  - Framework or library behaviour, e.g. streams filter or Jackson serializes.
  Valuable tests exercise conditional business behaviour that could realistically have bugs.
- New test function where an assertion on an existing test would do; assertion redundant with one beside it.
- Dead setup: mocks or fixtures overwritten before use.
- Test name does not match what it asserts; vague or non-contextual names.
- Unit tests touch wall clock, randomness or network.
- New behaviour has no test of the branch or edge that could realistically break.

## Minimal code
- Abstraction, parameter, default or option with no current consumer.
- Handling of impossible states; fallback with no concrete trigger; guessing a data shape instead of validating it.
- Symptom fix instead of root cause: raised limit, broad catch, retry, suppressed warning, debug logging left in.
- Re-implements what the framework guarantees.
- Dead code, unused imports or parameters, deep nesting where an early return reads flatter.

## Reuse and performance
- Search existing code for equivalent helpers, constants and components, then compare new diff paths for
  duplicate logic. Name both locations and suggest one shared operation when they express the same decision,
  such as repeated nullable-integer conversion to an optional integer; do not combine merely similar syntax.
- Check collection mutability against the contract and sibling return paths when relevant. Keep immutable
  results consistent; prefer a standard immutable-list operation when appropriate, but verify callers need no mutation.
- Hand-rolled logic for something the standard library or an existing dependency already provides.
- Repeated I/O or queries inside a loop; work that could be batched or done once.
- Sequential independent calls that could run concurrently; blocking calls on a hot or request path.
- Unbounded growth: collections, caches, retries or log volume with no limit.
- Only report performance when the consequence is concrete at the code's realistic scale.

## Zero-context readability
- Invariant or gate stated only in prose or a comment when code, a type or a test could enforce it.
- Needs outside context to understand: ticket or defect numbers, review history, names of past incidents.
- Dense inline lookups, predicates or calculations hide a domain decision. Identify the hidden decision and
  suggest a meaningful named helper, such as a device-key lookup, when its name makes the caller clearer.
- Logic split across needless indirection; helpers that only rename syntax without exposing intent.
- Mixed responsibilities obscure the flow. Judge comprehension, not function or file length.
- Literal or intermediate value with domain meaning but no name, such as a severity target; boolean parameter
  that switches behaviour. Add parentheses where mixed operators hide grouping or precedence.
- Default or else branch over a closed set; side effects inside map, filter or comprehensions.

## Naming (name the rule broken, or skip)
- Name contradicts behaviour (worse than vague).
- Generic verb (process, handle, manage, do) or placeholder name outside a tight scope.
- Boolean that does not read as a question; abbreviation a newcomer would not know.
- Breaks the file's own convention. The file's convention beats any outside rule.

## Comments and contracts
- Prefer clearer code and names over explanatory comments during implementation; review comments with the
  surrounding logic, not in a separate pruning pass. Report only a concrete misleading or obscuring effect.
- Preserve necessary context that clearer code cannot express: non-obvious reasons, workarounds, invariants
  and public API contracts. Do not remove a necessary contract merely because the implementation repeats it.
- Correct stale claims made wrong by the change, including in tests, protos and config.

## Do not report
- Security and repo-specific conventions: a dedicated review bot or reviewer owns these.
- Lint, formatter or compiler issues.
- Untouched code, unless the change makes it wrong.
- Preferences not tied to a rule above, including rules restated from the language rule file.
- Anything you cannot confirm by quoting a line.
- Anything whose fix would be "acceptable as is".
