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


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->
