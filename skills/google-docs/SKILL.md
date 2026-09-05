---
name: google-docs
description: >-
  Create, read, and modify Google Documents with native formatting. Converts markdown
  to Google Docs with proper styles (Title, Heading 1, tables, bold, code blocks).
  Use whenever the user mentions Google Docs, wants to publish markdown as a formatted
  doc, create an RFC or plan in Google Docs, convert markdown to Google Docs, share a
  document link, or update/append to an existing doc. Also use when the user pastes a
  Google Docs URL or document ID, asks to replace placeholders in a doc, or wants to
  read doc structure/content.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Google Docs Skill

## IMPORTANT: Choosing the Right Tool

**To create a formatted Google Doc from markdown**: use `gdocs.py create file.md` — this converts markdown to native Google Docs elements (Title, Heading 1, tables, bold, etc.).

**Do NOT use** the Enterprise Context Agent's `create_new_drive_file` MCP tool for formatted docs — it produces unformatted plain text with raw markdown syntax visible.

**To read a Google Doc**: Use the GDrive MCP tools (`get_document_structure`, `get_document_section`, etc.) — they already have auth and work without setup.

## Command Reference

The full invocation path for all commands is:

```bash
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py <command>
```

### Setup & Diagnostics

```bash
# Check all prerequisites (run this first)
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py doctor

# Create venv and install deps (one-time, requires uv)
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py setup
```

If the venv doesn't exist yet, bootstrap it manually first:

```bash
uv venv ~/.claude/skills/google-docs/.venv
uv pip install --python ~/.claude/skills/google-docs/.venv/bin/python \
  google-auth google-auth-httplib2 google-api-python-client
```

Additional one-time setup:

```bash
# Install pandoc
brew install pandoc

# Authenticate with correct scopes (re-run if you get 403 errors)
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/drive.file,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/cloud-platform
```

### Reading Documents

Via MCP Tools (recommended — no setup needed):

```
mcp__claude_ai_GDrive_MCP__get_document_structure(fileId: "DOC_ID")
mcp__claude_ai_GDrive_MCP__get_document_section(fileId: "DOC_ID", sectionIds: [...])
mcp__claude_ai_GDrive_MCP__get_document_preview(fileId: "DOC_ID")
mcp__claude_ai_GDrive_MCP__get_drive_file_content(fileId: "DOC_ID", offset: 0, limit: 1000)
```

Via script (for raw JSON with indices):

```bash
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py read DOC_ID
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py read DOC_ID --tab TAB_ID
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py list-tabs DOC_ID
```

### Creating Documents

```bash
# From markdown (converts, uploads, applies Proxima Nova font + table styling)
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py create file.md
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py create file.md --name "Custom Title"
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py create file.md --folder FOLDER_ID

# Empty document
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py create-empty "Document Title"
```

The `create` command will automatically:

1. Check prerequisites (pandoc, auth) — fail fast with actionable errors
2. Convert markdown to .docx via pandoc (no heading bookmarks)
3. Upload to Google Drive with auto-convert to native Google Doc
4. Apply post-upload formatting:
   - Shift heading levels: `#` becomes Title, `##` becomes Heading 1, etc.
   - Remove any residual bookmark anchors from pandoc
   - Set fonts: Proxima Nova for body text, Consolas for code
   - Style tables: 1pt borders, grey header row backgrounds
   - Italicize blockquotes

### Editing Existing Documents

```bash
# Append markdown to existing doc
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py append DOC_ID content.md
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py append DOC_ID content.md --tab TAB_ID

# Replace text
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py replace DOC_ID "find text" "replace text"
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py replace DOC_ID "{{PLACEHOLDER}}" "actual value" --tab TAB_ID

# Insert text at position
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py insert DOC_ID "new text" --index 42
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py insert DOC_ID "new text" --index 42 --tab TAB_ID

# Complex updates (batchUpdate from JSON)
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py update DOC_ID /tmp/changes.json
```

## Additional Reference

For the full markdown-to-Google-Docs translation table and API limitations, see `references/formatting-reference.md`.

## Troubleshooting

**"command not found: python" or "externally managed environment"** — Use the skill venv:

```bash
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py <command>
```

**403 "insufficient authentication scopes"** — Re-authenticate:

```bash
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/drive.file,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/cloud-platform
```

**"pandoc not found"** — `brew install pandoc`

**Run doctor to diagnose any issue:**

```bash
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py doctor
```
