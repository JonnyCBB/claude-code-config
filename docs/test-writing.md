# Test writing guidelines

Avoid these LOW-VALUE patterns when writing tests — reviewers will reject them:

1. **Testing language implementation details** — Don't test that enums have `fromValue()`, `getValue()`, `toString()` methods that work.
2. **Replicating static configuration** — Don't test that a static filter/mapping produces its configured output.
3. **Testing static mappings** — Don't test that `case X -> "Y"` returns `"Y"`.
4. **Testing framework behavior** — Don't test that Java streams filter correctly or Jackson serializes properly.

A test is valuable when it verifies BUSINESS LOGIC with CONDITIONAL BEHAVIOR that could realistically have bugs.
