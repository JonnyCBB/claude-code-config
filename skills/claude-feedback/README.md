# claude-feedback skill

Generates a sensitive-data-preserving feedback report about a Claude Code session that
you can share with Anthropic. Claude reads the session transcript locally, then
writes a report describing *what happened and what went wrong* — with your code,
data, names, paths, and any other sensitive content redacted or generalized.
Nothing is sent anywhere: the report is saved to `~/claude-code-feedback/` for
you to review, edit, and share yourself.

## Install

**Easiest:** in any Claude Code session, ask:

> Install the skill in claude-feedback.zip into my user-level skills directory.

**Manually:**

1. Unzip so the folder lands at `~/.claude/skills/claude-feedback/`
   (Windows: `%USERPROFILE%\.claude\skills\claude-feedback\`):

   ```bash
   mkdir -p ~/.claude/skills
   unzip claude-feedback.zip -d ~/.claude/skills/
   ```

2. Verify the layout — `SKILL.md` must be directly inside the folder:

   ```
   ~/.claude/skills/claude-feedback/SKILL.md
   ~/.claude/skills/claude-feedback/scripts/extract_timeline.py
   ```

3. Start a **new** Claude Code session (skills load at session start).

## Use

When something goes wrong in a session, run:

```
/claude-feedback Claude kept editing the wrong file and ignored my correction
```

Claude will build a sanitized report, show it to you, and save it locally.
**Review it before sharing** — you are the final judge of what's sensitive.

## Requirements

- `python3` on PATH (standard library only, no packages). If missing, the skill
  falls back to Claude's in-session memory and notes this in the report.
