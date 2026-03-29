---
name: crit-pr-review
description: Post code review findings to a GitHub PR using crit. Converts /code-review findings to friendly inline comments, lets the user review interactively in crit, then posts to GitHub via crit push with optional Approve/Request Changes status.
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

## Step 2: Convert Findings to Crit Comments

Read the review document FULLY. Parse each recommendation to extract:
- File path and line number (from `file_path:line` references)
- Severity (Critical/Major/Minor/Enhancement)
- Issue description and fix suggestion

Clear any existing comments:
```bash
crit comment --clear
```

For each finding, convert to friendly tone.

**Tone conversion rules** (from `${CLAUDE_PLUGIN_ROOT}/skills/code-review/references/comment-format.md`):
- CRITICAL/HIGH severity -> `issue (blocking):` prefix
- MEDIUM severity -> `suggestion (non-blocking):` prefix
- LOW severity -> `nit (non-blocking):` prefix
- Use "we" not "you" in the explanation
- Frame as questions when possible: "Have we considered..." not "You need to..."

Also add at least one `praise:` comment highlighting something done well in the PR (extract from the review doc's Highlights section).

For findings about files not in the diff (architectural/cross-cutting), collect them into a `BODY_COMMENTS` list — these will go in the review body message, not as inline comments.

**Use `--json` bulk mode** to add all comments in one atomic operation:

```bash
echo '[
  {"file": "src/auth.go", "line": 42, "body": "issue (blocking): Missing null check..."},
  {"file": "src/auth.go", "line": 50, "end_line": 55, "body": "suggestion (non-blocking): Have we considered..."},
  {"file": "src/handler.go", "line": 10, "body": "praise: Nice error handling here"}
]' | crit comment --json --author 'Claude'
```

**Fallback for single comments**: If only 1-2 findings, individual calls are fine:
```bash
crit comment --author 'Claude' '<file>:<line>' '<friendly-body>'
crit comment --author 'Claude' '<file>:<start>-<end>' '<friendly-body>'
```

**Shell quoting**: Use single quotes for the body. If the body contains single quotes, use `$'...'` syntax or write to a temp file.

## Step 3: Interactive Review in Crit

Get the repo root for the output directory:
```bash
OUTPUT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
```

Launch crit with the pre-populated `.crit.json`. Run **in the background** using `run_in_background: true`:
```bash
crit -o "$OUTPUT_DIR"
```

Note the port from crit's startup output.

**CRITICAL — you MUST run `crit listen` next. Do NOT skip it. Do NOT proceed without it.**

Run `crit listen <port>` **in the background** using `run_in_background: true`:
```bash
crit listen <port>
```

Tell the user:
"Crit is open in your browser with the review comments pre-loaded.

You can:
- **Edit** comment text to adjust tone or content
- **Resolve** comments you want to remove from the PR review
- **Add new** comments on any line
- Click **Finish Review** when done"

**Do NOT proceed until `crit listen` completes.** Do NOT ask the user to type anything. Do NOT read `.crit.json` early. Wait for the background task to finish — that is how you know the human is done reviewing.

**Fallback:** If `crit listen` fails immediately, tell the user: **"Type 'done' here when you're finished."** and wait for their response instead.

## Step 4: Process Review Edits

Read `.crit.json` from `$OUTPUT_DIR/.crit.json` using the Read tool.

Check for unresolved comments that the user added (new comments not from Step 2). These are additional feedback from the user — leave them as-is for posting.

Check for resolved comments — these are findings the user chose to exclude. They will be automatically skipped by `crit push`.

If the user left comments asking for changes to the review itself (meta-comments), address them:
1. Read the comment
2. Adjust other comments as needed using `crit comment` CLI (e.g., `crit comment --reply-to <id> --resolve --author 'Claude' '<response>'`)
3. Signal a new round: `crit go <port>`
4. **CRITICAL — immediately run `crit listen <port>` in the background again.** Do NOT skip this.
5. Wait for `crit listen` to complete. Repeat until user clicks Finish Review with no meta-feedback

## Step 5: Post to GitHub

Preview what will be posted:
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

### Post inline comments

```bash
crit push --message '<review-summary>' $PR_NUMBER
```

The `--message` flag sets the top-level review body. Include:
- High-level summary from the review document (first 2-3 sentences)
- Any `BODY_COMMENTS` that couldn't be attached as inline comments

### Post review status (if not Comment)

If the user chose Approve or Request Changes, submit a follow-up review:

```bash
REPO_INFO=$(gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"')

gh api "repos/$REPO_INFO/pulls/$PR_NUMBER/reviews" \
  -X POST \
  -f event=APPROVE \
  -f body='Looks good! See inline comments above.'
```

Replace `APPROVE` with `REQUEST_CHANGES` if that was selected. For Request Changes, use body: `'Please address the inline comments above.'`

## Step 6: Cleanup and Summary

Kill any remaining crit process:
```bash
pkill -f "crit" 2>/dev/null || true
```

Clear comments from `.crit.json` (preserves share state if any):
```bash
crit comment --clear
```

Report:

```
## PR Review Posted

**PR**: #$PR_NUMBER
**Status**: $EVENT
**Inline comments**: N
**Body comments**: M
**Review document**: $REVIEW_DOC_PATH

View: https://github.com/$REPO_INFO/pull/$PR_NUMBER
```

## Notes

- This skill orchestrates multiple tools and waits for user input at crit stages
- Resolved comments in crit are automatically excluded from `crit push`
- `crit push` uses file line numbers via GitHub's `line`/`side` API — no diff-position calculation needed
- The `--author` flag on `crit comment` is cosmetic in crit's UI; GitHub attributes the review to the authenticated `gh` user
- If `gh` is not authenticated, `crit push` will fail — tell the user to run `gh auth login`
