# Install Language Server Protocol Support

You are tasked with installing and configuring LSP support for Claude Code.

## Arguments

The user may specify a language:
- `/install-lsp typescript`
- `/install-lsp python`
- `/install-lsp` (no argument - list available options)

## Supported Language Servers:

| Language | Server | Installation Command | Plugin |
|----------|--------|---------------------|--------|
| TypeScript/JavaScript | vtsls | `npm install -g @vtsls/language-server typescript` | typescript-lsp@claude-plugins-official |
| Python | pyright | `npm install -g pyright` | pyright-lsp@claude-plugins-official |
| Java | jdtls | Managed by plugin | jdtls-lsp@claude-plugins-official |

## Process:

### If no argument provided:
1. Show available language servers and their status
2. Ask which language server to install

### If language specified:

1. **Check current status:**
   - Read `~/.claude/settings.json`
   - Check if the corresponding plugin is enabled in `enabledPlugins`
   - Check if the language server binary is installed

2. **Present the plan:**
   ```
   To enable [Language] LSP support:

   1. Install server: [command]
   2. Enable plugin: [plugin-name]

   Current status:
   - Server installed: Yes/No
   - Plugin enabled: Yes/No

   Shall I proceed?
   ```

3. **Install the language server:**
   - Run the appropriate npm/pip install command
   - Handle installation errors gracefully

4. **Enable the plugin (if needed):**
   - Update `enabledPlugins` in settings.json
   - Set the plugin to `true`

5. **Verify installation:**
   - Find a file of the target language type in the current project
   - Read the file to trigger LSP
   - Report success/failure

## Important:
- Always verify the installation actually works
- Provide clear error messages if something fails
- Suggest troubleshooting steps if verification fails
- Note that a session restart may be needed for full effect

## Troubleshooting:

If verification fails:
1. Check if npm/node is installed and in PATH
2. Verify the language server binary exists: `which [server-binary]`
3. Restart Claude Code session
4. Check plugin is enabled in settings.json
