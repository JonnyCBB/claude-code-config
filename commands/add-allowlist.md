# Add to Global Allowlist

You are tasked with adding command patterns to Claude Code's global permission allowlist.

## Arguments

The user may provide patterns in various formats:
- Single pattern: `/add-allowlist sbt*`
- Multiple patterns: `/add-allowlist sbt*, pytest*, tox*`
- Bash patterns: `/add-allowlist "Bash(npm run *)"`

## Process:

1. **Parse the user's request:**
   - Extract command patterns from the request
   - For simple commands (e.g., `sbt*`), convert to Bash format: `Bash(sbt *)`
   - For already-formatted patterns (e.g., `Bash(npm run *)`), use as-is
   - Handle wildcards: `*` in user input should become ` *` in the pattern

2. **Read current settings:**
   - Read `~/.claude/settings.json`
   - Identify the `permissions.allow` array

3. **Check for duplicates:**
   - Compare new patterns against existing entries
   - Report any patterns that already exist (skip adding them)

4. **Present the plan:**
   ```
   I'll add the following patterns to your global allowlist:
   - Bash(sbt *)
   - Bash(pytest *)

   Already exists (skipping):
   - Bash(git status *)

   Shall I proceed?
   ```

5. **Upon confirmation:**
   - Add new patterns to `permissions.allow` array
   - Maintain existing formatting and order
   - Write updated settings.json
   - Report success

## Pattern Format Guidelines:

| User Input | Converted Pattern |
|------------|-------------------|
| `sbt*` | `Bash(sbt *)` |
| `npm run *` | `Bash(npm run *)` |
| `git commit*` | `Bash(git commit *)` |
| `mcp__tool__*` | `mcp__tool__*` (no conversion) |
| `Bash(custom *)` | `Bash(custom *)` (already formatted) |

## Important:
- Always show the user what will be added before making changes
- Preserve the existing structure and formatting of settings.json
- Use proper JSON formatting (trailing commas handled correctly)
- Patterns starting with `mcp__` or other non-Bash prefixes should not be wrapped

## Remember:
- The allowlist uses glob-style wildcards
- Space before `*` is required for proper matching (e.g., `sbt *` not `sbt*`)
- Changes take effect in the current session (no restart needed for permissions)
