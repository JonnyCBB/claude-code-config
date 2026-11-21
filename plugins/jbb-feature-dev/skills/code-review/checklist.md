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
  A log line alone is not a degraded result.
- Check changed behaviour against comments, docstrings, error messages and schema/proto field contracts.
  Verify scope across data sources and actual formats, such as newline-delimited versus comma-separated text;
  do not leave an A/B-only contract describing a field now populated for rollouts.
- Keys for state that is stored, merged or compared across runs (history, caches, dedup maps): two distinct
  entries must not get the same key, and one entry's key must not depend on the other entries (a count, an
  order, a position). Build the two-entry case: two entries that share every key field, and two entries where
  one is fixed or removed. The survivor must keep its key and its value.
- Universal claims in the objective, PR body, commit message or comments ("every handler validates its input",
  "never writes without a lock"): list every instance in the code and check each one, in both directions.
  For each operation the claim covers, add a row: does it run, and does it have the promised effect? A row that runs
  without the effect breaks the claim.
- Several items (audiences, servers, pastes, rules) combined into one set or flag, then asked "any" or "exists":
  one item can hide another item's failure. Check the result per item, with one item that passes and one that fails.
  For a flag or summary set from one item's change (collapse, remove, finish one of two), check it still reflects
  the other items.
- Boundary conversions: exclusive versus inclusive bounds, instant versus calendar date, unit shifts.
  Test a value just inside and just outside the boundary after the conversion.
- Waits on a lock, queue or turn: a waiter must not block forever behind a holder that makes a network,
  model or other external call with no timeout.
- Cancellation: after a cancel, no queued callback may start new work, save data, or remove the way to retry.
  Check each event or flag the cancel path emits against the decision it actually took.
- A bug is a finding even when a test passes; state the input that breaks it.

## Objective and scope
- The objective requires something the diff does not do.
- The diff does something the objective did not ask for: drive-by refactor, extra feature, option or config.
  Formatting-only churn is never a finding.
- Hidden assumptions: units, time zones, nulls versus other falsy values, ordering, uniqueness.
- The title or description names work the diff does not do, says it does something it does not, or leaves
  out a change to behaviour, a contract, configuration, permissions, data or production settings. Quoted
  evidence the diff made stale counts. Stale counts or names alone are not a finding.

## Tests
- Assertions weakened, expected values changed, tests deleted or skipped, or guards narrowed (ignore lists,
  linter baselines, coverage exclusions) in the same diff as a code change.
- Would still pass if the implementation were subtly broken; feature claimed but not asserted.
- Mocks the unit under test, mocking outweighs the behaviour tested, or a stub returns the parameter mock.
- Flag low-value tests for removal or replacement when they only check:
  - Static mappings, e.g. `case X -> "Y"` returns `"Y"`.
  - Static configuration, e.g. configured filters produce their configured output.
  - Language implementation details, e.g. enum getters return their declared values.
  - Framework or library behaviour, e.g. streams filter or Jackson serializes.
  - Log or prompt text, e.g. a captured logger asserting a message.
  Valuable tests exercise conditional business behaviour that could realistically have bugs.
- New test function where an assertion on an existing test would do; the same fact asserted again, in this
  file or another, where both tests would fail for the same cause. A test at another layer that checks only
  what that layer adds is not a repeat.
- Dead setup: mocks or fixtures overwritten before use.
- Test name does not match what it asserts; vague or non-contextual names.
- Unit tests touch wall clock, randomness or network.
- New behaviour has no test of the branch or edge that could realistically break.
- Tests of code that compares, merges or tracks collections use one entry per key only; the two-entry
  cases under Correctness are missing.

## Minimal code
- Abstraction, parameter, default or option with no current consumer.
- Handling of impossible states; fallback with no concrete trigger; guessing a data shape instead of validating it.
- Symptom fix instead of root cause: raised limit, broad catch, retry, suppressed warning, debug logging left in,
  or a branch whose only effect is a log line.
- Re-implements what the framework guarantees.
- Dead code, unused parameters or build dependencies, deep nesting where an early return reads flatter.
- Comments narrating what the code used to do ("previously", "renamed from"); backwards compatibility for a
  surface that the diff and PR discussion show nothing still uses.
- Working notes committed as content: implementation plans, query logs, scratch output.

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

## Naming
- Name contradicts behaviour (worse than vague).
- Generic verb (process, handle, manage, do) or placeholder name outside a tight scope.
- Boolean that does not read as a question; abbreviation a newcomer would not know.
- Breaks the file's own convention. The file's convention beats any outside rule.

## Comments and contracts
- Read each comment with the code around it. Report only a concrete misleading or obscuring effect, and prefer
  a clearer name or helper as the fix.
- Preserve necessary context that clearer code cannot express: non-obvious reasons, workarounds, invariants
  and public API contracts. Do not remove a necessary contract merely because the implementation repeats it.
- Correct stale claims made wrong by the change, including in tests, protos and config.
- Docs or README text that restates the implementation step by step, so both must change together: suggest
  deleting it or replacing it with the reason.

## Do not report
- Security and repo-specific conventions: a dedicated review bot or reviewer owns these.
- Lint, formatter or compiler issues.
- Untouched code, unless the change makes it wrong.
- Preferences not tied to a rule above, including rules restated from the language rule file.
- Anything whose fix would be "acceptable as is".
