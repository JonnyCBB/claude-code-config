## Skills vs MCP Tools

- **IMPORTANT**: When a user request could be handled by either a skill (in `~/.claude/skills/`) or an MCP tool, ALWAYS check for and prefer using skills first. Skills are custom, well-documented approaches specifically designed for common tasks.
- Before using MCP tools for complex tasks, check if there's a relevant skill file that provides better instructions or approaches.
- Skills are documentation/instructions to read and follow, not commands to invoke.

## Test Writing Guidelines

When writing tests, avoid these LOW-VALUE patterns that reviewers will reject:

1. **Testing language implementation details** - Don't test that enums have `fromValue()`, `getValue()`, `toString()` methods that work
2. **Replicating static configuration** - Don't test that a static filter/mapping produces its configured output
3. **Testing static mappings** - Don't test that `case X -> "Y"` returns `"Y"`
4. **Testing framework behavior** - Don't test that Java streams filter correctly or Jackson serializes properly

A test is valuable when it verifies BUSINESS LOGIC with CONDITIONAL BEHAVIOR that could realistically have bugs.

## Implementation Pattern Discovery

When planning or implementing new features, **ALWAYS** search for existing reusable patterns in the codebase before writing new code:

1. **Search for existing abstractions** - Look for interfaces, abstract classes, protocols, traits, or base classes that new code should extend/implement
2. **Search patterns**: `abstract class`, `interface`, `extends`, `implements`, `Protocol`, `trait`, `ABC` (Python), `@abstractmethod`
3. **If an existing pattern is found**, the implementation MUST use it unless there's a documented reason not to
4. **If the approach differs from a prior research doc**, explicitly call out the deviation and explain why

Example: If implementing a new gRPC tool and `AbstractGrpcTool` exists with 10+ usages, extend it rather than implementing the raw `Tool` interface.

## Formatting Preferences

- When numbering steps, phases, or sections, always use integers only (1, 2, 3...). Never use fractional numbers like "Phase 5.5" or "Step 2.1".

## Incident Investigation Heuristics

- **Execution duration as error signal**: If a recurring error (e.g., MISSING_DEPS, OOM, timeout) typically causes an execution to fail within X minutes, and the current execution has been running significantly longer than X minutes, then the error is likely no longer occurring. In that case, no manual intervention is needed — just monitor. Always check how long the current execution has been running relative to the typical failure time before recommending remediation actions.
