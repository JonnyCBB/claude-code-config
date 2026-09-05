# Google Docs Skill

A comprehensive Claude Code skill for creating, reading, and modifying Google Documents.

## Features

- **Create** documents from markdown with automatic formatting
- **Read** existing documents (structure, content, tabs)
- **Edit** documents (insert, replace, format, append)
- **Multi-tab** support for reading and editing
- **Custom formatting** (Proxima Nova text, Consolas code, styled tables)

## Quick Start

### Prerequisites

```bash
# Install dependencies
brew install pandoc

# Set up skill venv and install Python packages
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py setup

# If the venv doesn't exist yet, bootstrap it first:
uv venv ~/.claude/skills/google-docs/.venv
uv pip install --python ~/.claude/skills/google-docs/.venv/bin/python \
  google-auth google-auth-httplib2 google-api-python-client

# Configure Google Cloud
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/drive.file,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/cloud-platform
```

### Verify Installation

```bash
~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py doctor
```

## Usage Examples

```bash
GDOCS="~/.claude/skills/google-docs/.venv/bin/python ~/.claude/skills/google-docs/scripts/gdocs.py"

# Create from markdown
$GDOCS create document.md

# Read document
$GDOCS read DOC_ID

# Append markdown to existing doc
$GDOCS append DOC_ID more-content.md

# Replace text
$GDOCS replace DOC_ID "old" "new"

# List tabs
$GDOCS list-tabs DOC_ID
```

## Command Reference

| Command                             | Description                                  |
| ----------------------------------- | -------------------------------------------- |
| `doctor`                            | Check all prerequisites                      |
| `setup`                             | Create skill venv and install deps (uses uv) |
| `create <file.md>`                  | Create new doc from markdown                 |
| `create-empty <title>`              | Create empty document                        |
| `read <doc_id>`                     | Read document content                        |
| `list-tabs <doc_id>`                | List all tabs in document                    |
| `append <doc_id> <file.md>`         | Append markdown to existing doc              |
| `replace <doc_id> <find> <replace>` | Replace all occurrences                      |
| `insert <doc_id> <text>`            | Insert text at position                      |
| `update <doc_id> <json_file>`       | Apply batchUpdate from JSON                  |

## See Also

- [SKILL.md](./SKILL.md) - Full skill instructions for Claude
- [Formatting Reference](./references/formatting-reference.md) - Markdown to Google Docs translation table
- [Google Docs API Reference](https://developers.google.com/docs/api/reference/rest)
