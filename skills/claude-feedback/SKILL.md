---
name: claude-feedback
description: Generate a sensitive-data-preserving feedback report about a Claude Code session to share with Anthropic. Redacts trade secrets, PII, code, and sensitive data while preserving the behavioral gist of what went wrong. Use when the user runs /claude-feedback, /feedback, or says things like "report this to Anthropic", "share feedback about Claude Code", "file feedback about this session".
---

# Claude Code Feedback (sensitive-data-preserving)

You are producing a feedback report the user can safely send to Anthropic about a
problem they hit in a Claude Code session. The report must let Anthropic understand
and ideally reproduce the *behavior* without learning anything about the user's
*content*: no trade secrets, no PII, no code, no business logic.

**Golden rule: Anthropic needs the behavior, not the content.** When in doubt about
whether something is sensitive, generalize it. A vaguer report is always acceptable;
a leaked secret is not.

## Workflow

### 1. Understand the complaint

The skill argument (text after `/claude-feedback`) is the user's description of the
problem. If no argument was given, infer the problem from the recent conversation
(e.g. the user just expressed frustration about something); if you genuinely can't
tell, ask one question: "What went wrong that you'd like to report?"

### 2. Extract the session timeline

Run the bundled extractor (stdlib-only, no dependencies):

```bash
python3 ~/.claude/skills/claude-feedback/scripts/extract_timeline.py
```

- Default: digests the newest transcript for the current working directory — i.e.
  this session. If the user is reporting a *previous* session, run with `--list`
  to show recent sessions and `--session <id-prefix>` to pick one.
- The digest output is **raw and sensitive**. It exists only for you to reason
  over. Never copy lines from it into the report. Never write the digest to a file.
- You also have your own in-context memory of this session. Use both: the digest is
  ground truth for ordering, timing, tool sequences, and error counts; your memory
  fills in intent and nuance. If the digest fails (transcript not found), fall back
  to in-context memory alone and say so in the report's metadata section.

### 3. Write the sanitized report

Create the output directory and write the report to
`~/claude-code-feedback/feedback-YYYY-MM-DD-HHMM.md` using the template below.

#### Report template

```markdown
# Claude Code Feedback Report

> Prepared by Claude on behalf of the user. Sensitive content has been redacted or
> generalized; placeholders like [Company], [internal service] mark redactions.
> The user has reviewed this report before sharing.

## TL;DR
<2-5 sentences: what the user was trying to do (abstracted), what Claude Code did
wrong, and the impact. This is the most important section — make it concrete about
the BEHAVIOR even though the content is abstracted.>

## Environment
- Claude Code version: <from digest>
- Model: <from digest>
- OS/platform: <from digest>
- Permission mode: <from digest>
- Session duration / turns: <duration, N user prompts, N tool calls, N tool errors>
- Context compactions during session: <N>
- Notable config: <MCP servers by category not name (e.g. "an internal ticketing
  MCP server"), hooks present yes/no, subagents used yes/no>

## Timeline
<Chronological, timestamped (HH:MM:SS), one line per meaningful step. Collapse
routine stretches ("14:02–14:15 — Claude explored the codebase with ~20
Read/Grep calls, no issues"). Expand the failure region in detail: every tool
call, error, retry, and user correction around the problem.>

## What went wrong
<Detailed but sanitized account of the failure: the pattern of behavior, what the
user expected instead, whether it recovered, whether it was reproducible.>

## Verbatim Claude Code errors (if any)
<API errors, crashes, permission-system messages, hook failures — these come from
Claude Code itself and are safe to quote EXCEPT any embedded user paths/content,
which you must still mask.>

## Additional context Claude thinks is relevant
<Anything diagnostic: "this happened right after a context compaction", "the file
being edited was very large (~4k lines)", "the same request worked earlier in the
session", patterns across the session, plausible triggers.>

## Redaction notes
<Bullet list of what was generalized and roughly why, so Anthropic knows what
detail is unavailable rather than nonexistent. E.g. "- All file paths replaced
with generic descriptions (proprietary project structure)".>
```

#### Sanitization rules

**Always redact / generalize (replace with bracketed placeholders or abstract descriptions):**

- Company, product, project, repo, branch, and codename references → `[Company]`,
  `[internal project]`, `[feature branch]`
- People: names, emails, usernames, handles → "the user", "a teammate"
- File paths and directory structures → describe by role and language only: "a
  ~400-line TypeScript service file", "the test file for that module"
- Code in any form: source, diffs, snippets, function/class/variable names, SQL,
  schemas, API routes, config values, prompts the user wrote for their own product
  → describe abstractly ("a function implementing pricing rules")
- Secrets: API keys, tokens, passwords, connection strings — never even placeholder
  them with partial values; if one appeared in the session, note "a credential
  appeared in tool output" in redaction notes
- Infrastructure: internal hostnames, IPs, URLs, bucket/queue/database names,
  cloud account IDs
- Business data: customer records, financial figures, metrics, document contents
- Error messages from the USER'S code/tools → keep the error *category* ("a type
  error in their build", "a failing integration test"), drop the message body
- Tech stack, if the stack itself could identify the company or is confidential →
  generalize to "a compiled backend language", "a JS frontend framework".
  Default is to KEEP generic stack info (see below) — generalize only when it's
  identifying.

**Always preserve (this is the diagnostic signal Anthropic needs):**

- Claude Code version, model ID, OS, permission mode, session stats
- Tool names and the *sequence* of tool calls (Read → Edit → Bash …)
- Counts, sizes, and durations: how many retries, how large the file, how long the
  hang
- Claude Code's own error messages verbatim (API errors, "Context low" warnings,
  crash output, permission denials) — masking any embedded user paths first
- Behavioral patterns: loops, ignored instructions, wrong-file edits, forgotten
  context, premature stopping, over-asking for permission
- Generic tech stack (language, mainstream framework, package manager) unless
  identifying — "TypeScript/React monorepo with pnpm" is usually fine and very
  useful
- What the user asked for, abstracted one level: "asked Claude to refactor a
  module to a new internal API" not the actual API

**Judgment calls:** the user's problem description itself may contain sensitive
terms — sanitize it too when quoting. Timestamps are fine. The working directory
name is NOT fine (often contains the company/project name).

### 4. Self-audit pass (mandatory)

Re-read the full draft report from top to bottom as a hostile reviewer whose only
job is to find leaks. Check specifically for:

- Proper nouns that aren't Anthropic/Claude/mainstream-OSS names
- Anything in backticks or quotes — quoted strings are where leaks hide
- Paths, URLs, emails, anything with `/`, `@`, `://`, or domain-like dots
- Identifiers in the "verbatim errors" section (paths embedded in stack traces)
- The TL;DR — it's written first and most likely to echo the user's raw words

Fix every hit, then update the file.

### 5. Present for user review

Show the user the full report inline (not just the path), then tell them:

1. Where it's saved.
2. That **they must review it before sharing** — Claude sanitized it, but they are
   the final judge of what's sensitive; anything they remove or generalize further
   is fine, the report degrades gracefully.
3. How to share: send the reviewed file to their Anthropic contact (e.g. the
   shared Slack channel with their account team), or attach it to a GitHub issue
   at https://github.com/anthropics/claude-code/issues if the issue isn't
   account-specific. Do NOT use the built-in `/bug` command for this — it shares
   the actual conversation data with Anthropic, which defeats the purpose.

Then hand them the file so they don't have to dig for it. Once they confirm the
report looks good (or immediately, if they say so), reveal it in their file
manager so it's one drag-and-drop away from Slack/email:

- macOS: `open -R <path>`   • Windows: `explorer /select,<path>`   • Linux: `xdg-open <dir>`

Also offer to copy the report text to the clipboard (macOS `pbcopy < <path>`,
Windows `clip`, Linux `xclip`/`wl-copy` if available) for users who'd rather
paste it as a message than attach a file.

If the user asks for changes ("also remove X", "that framework name is
sensitive"), apply them, re-run the self-audit on the edited report, and treat the
request as a signal to generalize *more* aggressively elsewhere too.

## Notes

- Never send the report anywhere yourself (no gh issue creation, no Slack, no
  email) unless the user explicitly asks after reviewing.
- If the transcript contains a `/claude-feedback` invocation itself, exclude that
  tail from the timeline — the report should cover the session up to the complaint.
- Very long sessions: keep the timeline under ~60 lines by collapsing routine
  stretches; never collapse the failure region.
