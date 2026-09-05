---
name: crit-pr-review
description: >
  Post code review findings to a GitHub PR using crit. Fetches existing human reviewer
  comments and displays them alongside Claude's findings in the crit browser UI for unified
  review. Converts /code-review findings to friendly inline comments (line, file, and
  review-level scopes), lets the user edit interactively in crit, then posts to GitHub via
  crit push with optional Approve/Request Changes status. Use when the user asks to "post
  review to PR", "push review comments to GitHub", "submit review via crit", "show human
  comments with Claude's review", or says "/crit-pr-review". Typically invoked after
  /code-review completes.
argument-hint: "<pr-number-or-review-doc-path>"
---

# PR Review with Crit

Post code review findings to a GitHub PR using crit for interactive review and submission.

## Step 1: Parse Arguments

Argument: `$ARGUMENTS`

**If empty**: Ask "Please provide a PR number or path to an existing review document."

**If PR number** (matches `^[0-9]+$` or contains `pull/[0-9]+`):

- Extract PR number
- Validate: `gh pr view $PR_NUMBER --json number -q '.number'`
- Search for existing review doc:
  ```bash
  ls -t ~/.claude/thoughts/shared/reviews/review_*${PR_NUMBER}*.md 2>/dev/null | head -1
  ```
- If found, ask: "Found existing review: `<path>`. Use this or generate fresh?"
- If generating fresh: invoke `/code-review $PR_NUMBER` to produce the review doc
- Store `REVIEW_DOC_PATH` and `PR_NUMBER`

**If file path** (contains `/` or `.md`):

- Resolve: `realpath "$1"`
- Verify exists
- Extract PR number from filename (`grep -oE '_[0-9]+_' | tr -d '_'`) or content (`grep -oE 'PR #[0-9]+' | head -1`)
- If not found, ask user for PR number
- Store `REVIEW_DOC_PATH` and `PR_NUMBER`

**Get repo info** (used in later steps):

```bash
REPO_INFO=$(gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"')
```

## Step 2: Launch Crit Before Injecting Anything

Start the crit daemon now, before any `crit comment` call in Steps 3-4. This ordering
matters: `crit comment --json` resolves its target review file from live git/branch
context, but if no daemon is running yet, that resolution can fall back to a stale
cached context left over from an earlier, unrelated crit session in the same repo
clone (e.g., a different branch or a different PR reviewed previously). If that
happens, comments get written into a file the daemon never reads — they silently
never appear in the browser, even though `crit comment --json` reports success and
the count looks right. Starting the daemon first and confirming its resolved branch
guarantees every later `crit comment` call in Step 3/4 targets the same file the
daemon is actually serving.

### Ensure we're on the PR branch

Crit requires a git diff to display. If the current branch is not the PR branch, crit
will fail silently because there are no changes to show.

```bash
ORIGINAL_BRANCH=$(git branch --show-current)
PR_BRANCH=$(gh pr view $PR_NUMBER --json headRefName -q '.headRefName')
```

If `ORIGINAL_BRANCH` != `PR_BRANCH`, checkout the PR branch:

```bash
gh pr checkout $PR_NUMBER
```

Store `ORIGINAL_BRANCH` so we can restore it in Step 8 cleanup.

### Launch crit

Run `crit` **in the background** using `run_in_background: true`:

```bash
crit --no-open -p 0
```

**Do NOT pass `-o <dir>` here.** `crit comment --json` writes to crit's session
review file at `~/.crit/reviews/<hash>.json` (keyed by the current branch/repo).
Passing `-o <dir>` to the daemon makes it read a different file (`<dir>/.crit.json`),
so the UI will show zero comments even though the injection succeeded. Let both
commands use the default session review file.

### Confirm the daemon resolved the branch you expect

```bash
crit status
```

Check that `Branch:` matches `$PR_BRANCH` (or `$ORIGINAL_BRANCH` if no checkout was
needed) before injecting anything. If it doesn't match, or the daemon reports it
isn't running, stop and re-launch rather than injecting comments against a review
file you haven't verified — a mismatch here is exactly what causes comments to
vanish later with no error.

Resolve the session review file path for later steps:

```bash
REVIEW_FILE=$(crit status 2>&1 | awk '/^Review file:/ {print $3}')
```

Note the port from crit's startup output for opening the browser in Step 5.

## Step 3: Fetch Human PR Comments

Fetch existing human review comments from GitHub and inject them into crit so they appear
alongside Claude's findings in the browser UI.

### Fetch comments via gh api

```bash
# Get all inline review comments (all reviews combined)
gh api "repos/$REPO_INFO/pulls/$PR_NUMBER/comments" --hostname github.com --paginate

# Get review-level comments (top-level review bodies)
gh api "repos/$REPO_INFO/pulls/$PR_NUMBER/reviews" --hostname github.com --paginate
```

### Skip if no human comments or fetch fails

If both endpoints return empty arrays, proceed directly to Step 4. No warning needed.

If `gh api` fails (auth error, network issue, rate limit), warn the user and proceed
without human comments — the review can still be posted with Claude's findings only.

### Build the injection payload

For each inline review comment from `/pulls/{pr}/comments`, extract: `user.login`
(author), `path` (file), `line` or `original_line` (line number), `body`, `id`
(GitHub comment ID for mapping), and `in_reply_to_id` (reply thread detection).

Build a JSON array for `crit comment --json`. Group root comments and their replies:

- **Root comments** (no `in_reply_to_id`): Map to crit line comments
  ```json
  {"file": "<path>", "line": <line>, "body": "<body>", "author": "<user.login>"}
  ```
- **Reply comments** (`in_reply_to_id` is set): Will be added as replies after root
  comments are injected (need the crit ID of the parent first)

For review-level comments from `/pulls/{pr}/reviews` where `body` is non-empty and
`user.login` is not a bot (bot accounts end with `[bot]`, e.g., `gosling[bot]`):

```json
{ "body": "<review body>", "scope": "review", "author": "<user.login>" }
```

### Inject into crit

Clear any existing comments first:

```bash
crit comment --clear
```

Inject root comments (all human inline + review-level comments):

```bash
echo '<json-array>' | crit comment --json --author 'fallback'
```

The per-entry `author` field overrides the `--author` flag, so each comment displays
the actual reviewer's GitHub username.

### Map GitHub IDs to crit IDs

After injection, read `.crit.json` and match each injected comment back to its GitHub
comment ID. Match by `author` + `file path` + `start_line` (for line comments) or
`author` + body prefix (for review-level comments). This is more robust than relying
on injection order matching crit's sequential ID scheme (`c1`, `c2`, `r0`, etc.).

Store the mapping as `GITHUB_TO_CRIT` for use in Step 4 (replying to human comments).

### Inject reply threads

For reply comments (those with `in_reply_to_id`), use the mapping to find the crit
parent ID and inject as replies:

```bash
echo '[
  {"reply_to": "<crit_parent_id>", "body": "<reply body>", "author": "<user.login>"}
]' | crit comment --json --author 'fallback'
```

## Step 4: Convert Findings to Crit Comments

Read the review document FULLY. Parse each section to extract findings, assessments,
and metadata.

### Sections to SKIP (not for the PR author)

- **Incremental Review Status**: Process metadata for the person running the tool.
- **Quality checker output**: Meta-assessment of the review quality (identified by
  `source_agent` containing "quality-checker" or the quality dimensions section).

### Parse the Existing PR Comments Assessment section

If the review document contains "## Existing PR Comments Assessment":

For each assessment entry:

- **If Claude only agrees** ("I agree", "this is correct", "concurs", or similar
  agreement-only language with no additional insight): **Skip entirely** — no value added.
- **If Claude has a genuinely useful addition, question, or disagreement**: Post as a
  **reply** to the corresponding human comment in crit using the `GITHUB_TO_CRIT` mapping
  from Step 3.

```bash
echo '[
  {"reply_to": "<crit_id_of_human_comment>", "body": "<claude_assessment>", "author": "Claude"}
]' | crit comment --json --author 'Claude'
```

### Parse the Prioritized Issues section

For each finding in the review document, extract:

- File path and line number (from `file_path:line` references)
- Severity (Critical/Major/Minor/Enhancement)
- Issue description and fix suggestion
- `source_agent` (if present)

### Convert findings to three comment scopes

**Line comments** — findings with a specific `file_path:line` reference AND the file
is in the PR diff:

```json
{"file": "<path>", "line": <line>, "body": "<friendly-body>"}
```

**File-level comments** — findings about a file overall without a specific line, OR
findings where the line is not in the diff:

```json
{ "path": "<path>", "body": "<friendly-body>", "scope": "file" }
```

**Review-level comments** — architectural/cross-cutting findings not tied to a specific
file (e.g., "Large PR" finding, general design concerns):

```json
{ "body": "<friendly-body>", "scope": "review" }
```

### Tone conversion

Read and apply `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/comment-format.md`
for severity-to-label mapping and tone rules. Key points:

- CRITICAL/HIGH -> `issue (blocking):`, MEDIUM -> `suggestion (non-blocking):`, LOW/ENHANCEMENT -> `nit (non-blocking):`
- repo-rules-reviewer findings: preserve rule attribution ("Per your GOSLING.md: ...")
- Include at least one `praise:` comment from the review doc's Highlights section

### Inject Claude's comments

Use `--json` bulk mode to add all comments in one atomic operation:

```bash
echo '<json-array-of-all-scopes>' | crit comment --json --author 'Claude'
```

## Step 5: Interactive Review in Crit

The daemon is already running from Step 2, and Steps 3-4 have injected all comments
into the review file it's serving. Open the browser and wait.

```bash
open http://localhost:<port>
```

(Use the port noted from the daemon's startup output in Step 2.)

**Do NOT proceed until `crit` completes.** The background task started in Step 2
blocks until the user clicks "Finish Review" — that is how you know the human is
done reviewing.

Tell the user:
"Crit is open in your browser with both human reviewer comments and Claude's findings.

You can:

- **Edit** comment text to adjust tone or content
- **Resolve** comments you want to remove from the PR review
- **Add new** comments on any line
- Click **Finish Review** when done"

## Step 6: Process Review Edits

Read the session review file using the Read tool:

```bash
cat "$REVIEW_FILE"   # path resolved in Step 2 via `crit status`
```

Check all three kinds of user edits. Parse the JSON explicitly — do not rely on
`crit push --dry-run` alone, since replies and new comments inside threads are
easy to miss at a glance.

1. **Top-level user comments** — new entries under `files[*].comments[]` or
   `review_comments[]` whose `author` is not `Claude`. These are fresh feedback
   from the user; leave them as-is and they'll be pushed.
2. **Resolved comments** — entries where `resolved: true`. `crit push` will skip
   these automatically.
3. **Replies on Claude's comments** — entries under `files[*].comments[*].replies[]`
   whose `author` is not `Claude`. **The reply body is the user's instruction,
   not content to post.** Common patterns:
   - "Ignore this" / "drop this" / "skip" → resolve the parent via
     `crit comment --reply-to <parent-id> --resolve 'Resolved per reviewer'`
   - "Good point, keep this" → leave the parent active; do NOT post the reply body.
   - "Rephrase to say X" → edit the parent comment body (re-inject with
     `crit comment --json` after clearing the single comment, or edit the JSON in
     place) and leave it active.
   - Substantive addition the user wants posted → inline the user's addition into
     the parent comment body so it posts as a single comment.

   After processing all replies, re-run `crit push --dry-run $PR_NUMBER` to confirm
   the final count matches expectations.

If the user left comments asking for changes to the review itself (meta-comments),
address them:

1. Read the comment
2. Adjust other comments as needed using `crit comment` CLI
3. Re-run the **exact same `crit` command from Step 2** in the background using
   `run_in_background: true`:
   ```bash
   crit --no-open -p 0
   ```
   On re-run, `crit` signals round-complete to the existing daemon, then blocks again
   until the next "Finish Review" click. The daemon is keyed by arguments — the command
   must match Step 2 exactly (no `-o`).
4. Tell the user: "Changes applied. Review the diff in your browser and click Finish
   Review when ready."
5. **Do NOT proceed until `crit` completes.** Repeat until user clicks Finish Review
   with no meta-feedback.

## Step 7: Post to GitHub

### Build the review body

Construct the `--message` body from:

1. High-level summary from the review document (first 2-3 sentences)
2. Any unresolved review-level comments from `$REVIEW_FILE` — read the `review_comments`
   array, filter to entries where `resolved` is not `true`, and append their `body` text.
   `crit push` does NOT auto-include these, so they must go in the `--message` body.

### Preview

```bash
crit push --dry-run $PR_NUMBER
```

Show the preview to the user and ask for review status:

"Ready to post N comments to PR #$PR_NUMBER.

How would you like to submit?"

Options:

1. **Comment** (default) — feedback without approval or rejection
2. **Approve** — approve the PR with your comments
3. **Request Changes** — request changes before merge

### Post the review

**Comment** (default):

```bash
crit push --message '<review-body>' $PR_NUMBER
```

**Approve**:

```bash
crit push --event approve --message '<review-body>' $PR_NUMBER
```

**Request Changes**:

```bash
crit push --event request-changes --message '<review-body>' $PR_NUMBER
```

## Step 8: Cleanup and Summary

Kill any remaining crit process:

```bash
pkill -f "crit" 2>/dev/null || true
```

Restore the original branch if we switched in Step 2:

```bash
if [ "$ORIGINAL_BRANCH" != "$PR_BRANCH" ]; then
  git checkout "$ORIGINAL_BRANCH"
fi
```

Clear comments from the session review file:

```bash
crit comment --clear
```

Report:

```
## PR Review Posted

**PR**: #$PR_NUMBER
**Status**: $EVENT
**Inline comments**: N (line) + M (file-level)
**Review-level comments**: K
**Human comments shown**: H
**Review document**: $REVIEW_DOC_PATH

View: https://github.com/$REPO_INFO/pull/$PR_NUMBER
```

## Notes

- This skill orchestrates multiple tools and waits for user input at the crit review stage
- Resolved comments in crit are automatically excluded from `crit push`
- `crit push` uses file line numbers — no diff-position calculation needed
- The `--author` flag on `crit comment` is cosmetic in crit's UI; GitHub attributes the review to the authenticated `gh` user
- If `gh` is not authenticated, `crit push` will fail — tell the user to run `gh auth login`
- For GitHub Enterprise (e.g., `github.com`), **prefix `crit push` with `GH_HOST=<host>`**, otherwise crit will dispatch to `github.com` and `gh pr view`/review creation will return HTTP 404. Resolve the host from the git remote: `GH_HOST=$(git remote get-url origin | sed -n 's|.*@\([^:/]*\)[:/].*|\1|p')`
- `crit push` does NOT include `review_comments` from `.crit.json` — always use `--message` for the review body
- `crit pull` is unreliable (confirmed broken in v0.9.0) — use `gh api` directly to fetch human comments
- Crit IDs are sequential: `c1`, `c2`, `c3` for file/line comments; `r0`, `r1` for review-level; `c3-r1` for replies
- Line numbers in `crit push` must reference lines present in the PR diff — unchanged lines cause HTTP 422
- **Never launch the crit daemon with `-o <dir>`** when injecting comments via `crit comment --json` (which has no `-o`). The daemon's `-o` makes it read `<dir>/.crit.json` while `crit comment --json` writes to `~/.crit/reviews/<hash>.json` — the UI will silently show zero comments. Resolve the session review file path with `crit status | awk '/^Review file:/ {print $3}'` when you need to read it.
- **Never inject comments before the daemon is running** — a separate failure mode from the `-o` mismatch above, with no flags involved. Without a live daemon, `crit comment --json` can resolve to a stale review file from an earlier, unrelated crit session in the same repo clone. See Step 2 for why this ordering matters and how to verify it.
- **Never run `crit comment --help` or `crit comment --list`** — both are silently interpreted as adding a review-level comment with body `--help` or `--list`. Use `crit --help` (no `comment`) or `crit status` instead.
