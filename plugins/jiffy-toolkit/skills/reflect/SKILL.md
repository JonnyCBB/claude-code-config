---
name: reflect
description: >
  Extract non-obvious learnings from Claude Code session transcripts and route them
  to persistent storage (auto-memory, CLAUDE.md, Knowledge Graph, Infinite Memory).
  Filters noise with an evidence-based taxonomy — skips standard patterns and
  well-documented libraries; surfaces proprietary API discoveries, bug workarounds,
  user corrections, and tool discoveries. Presents grouped recommendations for user
  approval before storing anything. Supports current session or multi-session analysis
  with time/count filters.
  Does NOT auto-store without approval or auto-generate skills.
when_to_use: >
  Use when the user says "/reflect", "reflect on this session", "what did we learn",
  "extract learnings", "session retrospective", "save what we learned", "what should
  I remember from this", or asks to capture insights from recent work. Also use for
  "harvest learnings", "session review", or any request to extract persistent knowledge
  from one or more sessions.
argument-hint: "[--sessions=N] [--since=YYYY-MM-DD] [--project=<path>] [--non-interactive]"
---

# Reflect

Extract non-obvious learnings from session transcripts, deduplicate against existing
stores, and route approved items to the right storage destination.

## Arguments

- **No flags**: reflect on the current session
- `--sessions=N`: last N sessions for this project
- `--since=YYYY-MM-DD`: sessions since a date
- `--project=<path>`: sessions for a different project
- `--non-interactive`: auto-approve confidence >0.8, skip <0.5, log all decisions

Flags combine: `--sessions=5 --since=2026-06-25` processes up to 5 sessions since that date.

## Example

```
/reflect
```

Reflects on the current session — extracts learnings, deduplicates, presents for approval.

```
/reflect --sessions=5
```

Reflects on the 5 most recent sessions, cross-deduplicating recurring items.

## Workflow

Follow these 7 steps in order. Read reference files only when a step tells you to.

### Step 1: Discover Transcripts

Session transcripts are JSONL files at:
`~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`

`<encoded-cwd>` is the absolute working directory with each `/` replaced by `-`.
Example: `/Users/alice/myproject` → `-Users-alice-myproject`

**Current session (no flags):**

```bash
ls -t ~/.claude/projects/<encoded-cwd>/*.jsonl | head -1
```

Most-recently-modified is only a _candidate_, not an identifier. Anyone running several
Claude Code sessions concurrently in the same directory will have several transcripts being
appended to live, and mtime ordering between them is arbitrary.

**Prefer the exact identifier over the candidate.** The current session id is usually
already in the environment, and it is ground truth rather than a heuristic: the scratchpad
directory and every background-task output path both end in `<session-id>/...`
(`/private/tmp/claude-<uid>/<encoded-cwd>/<session-id>/scratchpad`,
`.../<session-id>/tasks/<task-id>.output`). If either is available, resolve the transcript
as `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl` directly and skip the mtime step.
Observed 2026-07-30: `ls -t | head -1` returned a concurrent session's 4225-turn transcript
whose mtime was identical to the real one's, while the scratchpad path named the correct
session outright.

**Verify the candidate before farming it out to classifiers.** Read its first and last few
user turns and check they match the work you are reflecting on. If they don't, re-resolve
before spending anything: pick the transcript whose content matches, or ask the user which
session they mean. If the user names a session id explicitly, use it and skip this check.

Also require every emitted learning to carry its source session id. That makes a
misattribution visible in the output rather than silently folded into "this session".

**Why this matters more than it looks:** picking the wrong transcript does not fail loudly —
the classifiers return well-formed, high-quality learnings about someone else's work, and
they read as plausible. It happened twice in one corpus: one run sent two of four
classifiers into a concurrent unrelated session, another analysed a parallel
account-linking session before the mistake was noticed. Each cost a full classification
pass, and the foreign learnings came close to being stored as this session's.

**Multi-session (`--sessions=N` and/or `--since=YYYY-MM-DD`):**

```bash
ls -lt ~/.claude/projects/<encoded-cwd>/*.jsonl
```

Sort by modification time, take the last N, and filter by date if `--since` is set.

**Different project (`--project=<path>`):**
Compute the encoded-cwd from the given path instead of the current working directory.

If no transcripts found, stop: "No session transcripts found for this project."

### Step 2: Parse Transcripts

Read each JSONL file. Each line is a JSON object with a `type` field.

**Message structure:**

- Each line has top-level keys including `type`, `message`, `timestamp`, `sessionId`
- The `message` field contains `role` ("user" or "assistant") and `content`
- `content` is either a string (user text) or an array of blocks (each with a `type` field:
  `text`, `tool_use`, `tool_result`, `thinking`)

**Extract these types** (high reflection value):

| Type                             | What to look for                                |
| -------------------------------- | ----------------------------------------------- |
| `user` (role=user, text content) | Corrections, decisions, preferences, questions  |
| `user` (tool_result content)     | Tool outputs revealing what worked or failed    |
| `assistant` (text content)       | What the model tried, conclusions reached       |
| `assistant` (tool_use content)   | Which tools were called and with what arguments |

**Skip these types** (no reflection value):
`mode`, `permission-mode`, `last-prompt`, `ai-title`, `queue-operation`,
`file-history-snapshot`, `system`

Also skip `attachment` lines and `user` messages containing only `<local-command-stdout>`
or `<command-name>` tags (these are UI metadata, not user intent).

Group extracted messages into conversation turns by following `parentUuid` chains or
sequential ordering.

**Large transcripts (>500 extracted messages):** chunk into groups of ~100 turns,
preserving turn boundaries. Each chunk is classified independently in Step 3.

**Size each chunk file so a classifier can actually read all of it.** There are two
independent ceilings, and they fail in opposite ways:

1. **The 2000-line default** — Read returns the first 2000 lines and does not announce the
   cut. A longer chunk gets silently half-analysed while the classifier reports success,
   because from its point of view it read the file it was given. This is the dangerous one.
2. **A per-call token cap (~25k tokens)** — an oversized read fails loudly and returns _no_
   content. Recoverable, but it burns a turn per attempt.

Line count alone does not protect you from the second: transcript chunks run dense
(~40 tokens/line observed), so an 800-line read can exceed the token cap while a
2000-line file passes the line check. **Size by bytes, then convert to lines**:

```bash
wc -lc <chunk-file>        # lines and bytes
# bytes_per_line = bytes / lines
# lines_per_read ≈ 40000 / bytes_per_line     (~40 KB per read leaves headroom)
```

For a chunk averaging ~90 bytes/line that lands near 450-500 lines per read. Give each
classifier the file's exact line count, the computed `limit`, and a requirement to report
which ranges it actually covered.

This is not hypothetical: on a 15-batch run, 12 batch files exceeded 2000 lines. One
classifier analysed roughly 2000 of 2904 lines, reported clean, and only surfaced 5
additional learnings after being told its real line count and asked to re-read the
uncovered range. Silent under-coverage is the worst failure mode available to this skill,
because a partial analysis is indistinguishable from a thorough one that found less.

**Prefer a file handoff for results.** Have each classifier write its JSON array to a path
you specify and confirm the path in its reply, rather than relying on the message channel.
A named agent that returns only text has its output dropped (see the delivery note in
Step 3), and a file you can count items in is verifiable.

If total extracted messages < 10, stop: "Nothing to reflect on — session too short."

### Step 3: Classify Learnings

Read `references/taxonomy.md` for the full 3-tier learning taxonomy before this step.

Spawn a classification agent (`subagent_type: general-purpose`) for each transcript
chunk. Include in the agent prompt:

1. The conversation turns for that chunk
2. The taxonomy from `references/taxonomy.md` (include it verbatim in the prompt)
3. Instructions to return a JSON array where each item has:

```json
{
  "learning": "One-line summary",
  "detail": "Full context — what happened, what was discovered or corrected",
  "tier": 1,
  "category": "bug_workaround",
  "confidence": 0.85,
  "source_quote": "Relevant transcript excerpt",
  "detection_signal": "user correction | empirical discovery | error-fix sequence | stated preference | decision rationale"
}
```

Tell the agent to focus on what the model cannot know from training data: internal API
behaviors discovered empirically, tool gotchas, user workflow preferences, infrastructure
quirks, bug workarounds for proprietary systems. Standard coding patterns and well-documented
library usage are Tier 3 noise — skip them entirely.

**Expect background delivery.** In practice these agents run in the background even
when spawned synchronously — the JSON arrives later as an agent message, not as an
inline tool result. Plan for it:

- Add to every classification-agent prompt: "Deliver the JSON array as your final
  message. If you are running as a background teammate, send it via SendMessage to
  'main' — plain text output is not visible to the spawner."
- After spawning, continue with preparation that doesn't need the results (e.g. read
  `references/storage-routing.md` for Step 4), then wait for the agent message.
- If an agent goes idle without delivering content (an idle notification with no
  JSON), nudge it once via SendMessage asking it to send the array to "main";
  respawn only if the nudge produces nothing within a few minutes. (Observed
  2026-07-08: a classifier idled twice before delivering — two nudges recovered it;
  waiting silently for an inline result costs ~10 minutes per chunk.)

Merge results from all chunk agents. Discard items with confidence < 0.3.

If no Tier 1 or Tier 2 learnings found, stop: "No non-obvious learnings detected in
this session."

### Step 4: Deduplicate

Read `references/storage-routing.md` for dedup thresholds and routing logic.

For each candidate learning, check all available stores:

1. **Infinite Memory** — `mcp__infinite-memory__recall(query=<3-5 key terms>, limit=3)`
   - Similarity >0.85 → DUPLICATE (skip)
   - Similarity 0.6-0.85 → RELATED (flag for user: "Similar to: [title]. Update?")

2. **Knowledge Graph** — `mcp__knowledge-graph__search(query=<key terms>)`
   - Matching node with same info → DUPLICATE
   - Matching node, new info to add → UPDATE candidate

3. **Auto-memory** — Read the project's `MEMORY.md` index, match descriptions
   - Found → DUPLICATE or UPDATE existing file

4. **CLAUDE.md** — Read `~/.claude/CLAUDE.md` and project `.claude/CLAUDE.md` (if exists)
   - Overlapping instruction → DUPLICATE

If an MCP is unavailable, skip that check with a warning and continue with the others.
If all candidates are duplicates, stop: "All learnings already captured in existing stores."

**Multi-session cross-dedup:** When processing multiple sessions, also deduplicate
across sessions before presenting. Group by semantic similarity >0.8, keep the most
detailed version, and note "Found in N sessions" — recurring items get a confidence boost.

### Step 5: Route

Read `references/storage-routing.md` for the routing decision tree.

Apply the tree to each UNIQUE or RELATED learning. A single learning can route to
multiple destinations when it fits multiple categories (e.g., a bug workaround that's
also a recurring tool issue → Auto-memory as bugfix AND CLAUDE.md as tool instruction).

### Step 6: Present and Approve

Display all learnings grouped by destination:

```
## Recommended Learnings (M items)

### CLAUDE.md (N items)
1. [0.92] "Use mcp__X for code search, not grep on large repos"
   Category: tool_command | Source: user correction

### Infinite Memory (N items)
2. [0.88] Bug: socket closed on edge proxy, fix: use disco resolution
   Category: bug_workaround | Source: empirical discovery

### Knowledge Graph (N items)
3. [0.72] Service X is owned by team Y (confirmed via the service catalog)
   Category: relationship | Source: conversation

### Auto-Memory (N items)
4. [0.90] User prefers uv over pip for Python packages
   Category: feedback | Source: user preference
```

**Routing accuracy**: The section heading for each learning MUST match its routed
destination from the Step 5 decision tree, not its category name. In particular,
`relationship` category items route to **Knowledge Graph**, not Infinite Memory —
do not group them under the "Infinite Memory" heading. Double-check each item's
heading against the routing tree before presenting.

For RELATED items, show the existing entry alongside:
"Similar to existing: '[title]'. Update the existing entry, or skip?"

**Interactive mode** — use AskUserQuestion:

- "Approve all high-confidence" (recommended)
- "Review individually" (present in chunks of 3-5 per question)
- "Custom selection"
- "Skip all"

**Non-interactive mode** (`--non-interactive`):

- confidence >0.8 → auto-approve and store
- confidence 0.5-0.8 → log to summary but do not store
- confidence <0.5 → skip silently
- Print a summary of all decisions at the end

### Step 7: Store

Execute storage for each approved learning at its routed destination(s).
See `references/storage-routing.md` for the API pattern per destination.

**Auto-memory:** Write a `.md` file with frontmatter to the project's memory directory.
Add a one-line entry to MEMORY.md. Warn if MEMORY.md would exceed 200 lines.

**CLAUDE.md:** Edit to append the instruction in the most relevant existing section.
Warn if the file would exceed 200 lines.

**Knowledge Graph:** `add_node` with type and properties. `add_edge` for relationships.
`update_node` for RELATED items the user chose to update.

**Infinite Memory:** `remember` with title, content, type, tags, scope, confidence,
and project_path.

After all operations, print a summary:

```
## Stored N of M learnings

- CLAUDE.md: 2 instructions added
- Infinite Memory: 3 items (1 bugfix, 1 decision, 1 pattern)
- Knowledge Graph: 1 node + 1 edge
- Auto-Memory: 1 feedback memory
- Skipped: 3 (user declined)
```

### Optional: Pattern Analysis

Scan for actionable skill/agent recommendations after Step 3. This analysis applies
to **any session count** — a single deep session can surface skill improvements just
as well as cross-session frequency analysis.

**Single-session signals** (1+ sessions):

- **Skill gap or wrong turn**: a skill was invoked but its instructions led to a wrong
  conclusion, missed a critical check, or lacked a step that the user/model had to
  improvise → **skill update recommendation**. Look for: the model following a skill's
  prescribed steps but reaching the wrong answer, then correcting course based on
  evidence the skill didn't tell it to gather.
- **Novel procedure discovered**: a multi-step investigation/fix sequence that isn't
  codified in any existing skill but proved effective → **new skill candidate**
- **User correction of skill behavior**: explicit "don't do X" or "always do Y" that
  applies to a specific skill's workflow → **skill update recommendation**

**Multi-session signals** (3+ sessions):

- **Recurring workflow**: same action sequence in 3+ sessions → new skill candidate
- **Repeated correction**: same skill corrected 2+ times → skill update recommendation
- **Repeated agent config**: same agent type+prompt in 3+ sessions → new agent type candidate

Present these as a separate section after the individual learnings. These are
recommendations only — not auto-stored. If the user wants to act on a skill
recommendation, point them to `/skill-creator` for eval-driven development, because
single-pass LLM-generated skills average -1.3pp without iteration (SkillsBench).
