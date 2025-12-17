---
description: Generate a comprehensive PR description by analyzing changes between current branch and target branch
argument-hint: [target-branch]
---

# Generate PR Description

Analyze the git changes between the current branch and the target branch (default: master) to generate a comprehensive pull request description.

## Instructions

1. **Fetch and analyze changes**:
   - Run `git fetch origin {{TARGET_BRANCH:-master}}`
   - Get diff summary: `git diff --name-status --stat origin/{{TARGET_BRANCH:-master}}...HEAD`
   - Get commit history: `git log --oneline --no-merges origin/{{TARGET_BRANCH:-master}}..HEAD`
   - Get changed files list: `git diff --name-only origin/{{TARGET_BRANCH:-master}}...HEAD`
   - Check for linked issues: `git log --grep="#[0-9]" --grep="fixes" --grep="closes" -i origin/{{TARGET_BRANCH:-master}}..HEAD`

2. **Auto-detect key information**:
   - **Context thoughts/ directory**: Look for additions/changes to documents in the `thoughts` directory. This files should contain complete context for the PR
   - **Breaking changes**: Look for changes in `api/`, `proto/`, public interfaces, database migrations
   - **Feature flags**: Search for feature flag patterns in the diff
   - **Performance-sensitive**: Changes in hot paths, caching, database queries, algorithms
   - **Tests**: Count added/modified test files
   - **Documentation**: Check for README, CHANGELOG, or docs/ changes

3. **Generate PR description** with these sections:

### Title
- Create a concise, outcome-focused title (<72 chars)
- Use imperative mood: "Add X", "Fix Y", "Refactor Z"
- Include measurable impact if applicable

### Summary
Brief 2-3 sentence overview of what this PR accomplishes and why it's needed.

### Context
- Problem being solved or feature being added
- User/system impact
- Link to related issues/tickets (auto-detect from commit messages)

### What Changed
Group changes by subsystem/area:
- **Core Logic**: Main business logic changes
- **API/Interface**: Public API modifications
- **Database**: Schema changes, migrations
- **Configuration**: Config file updates
- **Tests**: New or modified tests
- **Documentation**: Doc updates

For each group, provide 2-3 bullet points summarizing meaningful changes (not just file lists).

### Behavioral Impact
- [ ] Breaking API changes: [Yes/No - list if yes]
- [ ] Database migrations: [Yes/No - describe if yes]
- [ ] Feature flags: [List any feature flags and their defaults]
- [ ] Configuration changes: [List any new/modified configs]

### Risk Assessment
- **Risk Level**: [Low/Medium/High]
- **Key Risks**: [List main risks]
- **Mitigations**: [How risks are addressed]
- **Rollback Plan**: [How to rollback if needed]

### Performance Impact
- Performance-sensitive areas touched: [Yes/No]
- Expected impact: [Describe if applicable]
- Benchmarks/metrics: [Include if available]

### Testing
- **Test Coverage**:
  - [ ] Unit tests added/updated
  - [ ] Integration tests added/updated
  - [ ] Manual testing completed
- **Test Instructions**: [Steps for manual testing if needed]

### Screenshots/Demo
[Include if UI changes, otherwise mark as N/A]

### Review Guidance
- **Start here**: [Most important file/component to review first]
- **Review order**: [Suggested sequence for reviewing files]
- **Focus areas**: [Specific areas needing careful review]

### Pre-merge Checklist
- [ ] Tests passing
- [ ] Documentation updated (if public API changed)
- [ ] CHANGELOG updated (if user-facing)
- [ ] Feature flags documented
- [ ] Migration tested (if applicable)
- [ ] Performance validated (if sensitive areas touched)

## Implementation Notes

When generating the description:
1. Keep bullet points concise and scannable
2. Use technical terms appropriately but explain complex changes
3. Highlight anything that might surprise reviewers
4. For large PRs, consider suggesting it be split
5. Auto-tick checklist items that can be verified from the diff
6. If the diff is huge (>1000 lines), focus on architectural changes over implementation details

## Create or Update PR

4. **After generating the description, automatically push branch and create/update PR in GitHub**:
   - First, check if the current branch is pushed to remote: `git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>&1`
   - If the branch is not pushed to remote:
     - Automatically push the branch: `git push -u origin HEAD`
     - Confirm: "✓ Pushed branch to remote"
   - Check if a PR already exists for the current branch: `gh pr view --json number,url 2>&1`
   - If a PR exists:
     - Extract the PR number from the output
     - Update the PR body using: `gh pr edit <PR_NUMBER> --body "$(cat <<'EOF'\n<PR_DESCRIPTION>\nEOF\n)"`
     - Get the PR URL: `gh pr view --json url --jq .url`
   - If no PR exists:
     - Create a new PR: `gh pr create --title "<TITLE>" --body "$(cat <<'EOF'\n<PR_DESCRIPTION>\nEOF\n)" --base {{TARGET_BRANCH:-master}}`
     - The command will return the PR URL

   **Error Handling**:
   - If `gh` command is not available, inform the user and provide the raw markdown instead
   - If there are no commits ahead of the target branch, inform the user there's nothing to create a PR for
   - If authentication fails, inform the user they need to run `gh auth login`
   - For any other errors, explain what went wrong and provide the raw markdown as fallback

5. **Confirm success**:
   - If the PR was created/updated successfully, provide a confirmation message with the PR URL
   - Example: "✓ PR description updated successfully: https://github.com/org/repo/pull/123"
   - If it failed, explain why and provide the raw markdown in triple backticks for manual copy-paste

## Example Output

```markdown
## Fix playlist sync batching to reduce API calls by 40%

### Summary
Refactors the playlist synchronization logic to batch write operations, significantly reducing API calls and improving sync performance for large playlists.

### Context
Users with playlists >500 tracks were experiencing timeouts during sync operations. This PR implements batched writes to handle large playlists efficiently.

Fixes #2847

### What Changed
**Core Logic**:
- Introduced `ChunkedWriter` class to batch items in groups of 100
- Modified `PlaylistSyncJob` to use batched operations
- Added retry logic with exponential backoff for failed batches

**Tests**:
- Added unit tests for `ChunkedWriter` batching logic
- Updated integration tests to verify large playlist handling
- Added performance benchmarks

### Behavioral Impact
- [ ] Breaking API changes: No
- [ ] Database migrations: No
- [ ] Feature flags: `playlist_batch_sync` (default: enabled)
- [ ] Configuration changes: New `batch_size` config (default: 100)

### Risk Assessment
- **Risk Level**: Medium
- **Key Risks**: Potential for partial sync failures in batches
- **Mitigations**: Each batch is atomic; failed batches are retried individually
- **Rollback Plan**: Disable `playlist_batch_sync` feature flag

### Performance Impact
- Performance-sensitive areas touched: Yes
- Expected impact: 40% reduction in API calls, 60% faster sync for playlists >500 tracks
- Benchmarks: p95 latency reduced from 2.1s to 850ms on staging

### Testing
- **Test Coverage**:
  - [x] Unit tests added/updated
  - [x] Integration tests added/updated
  - [x] Manual testing completed
- **Test Instructions**: Create playlist with 1000+ tracks and trigger sync

### Review Guidance
- **Start here**: `ChunkedWriter.scala` - core batching logic
- **Review order**: ChunkedWriter → PlaylistSyncJob → tests
- **Focus areas**: Error handling in batch operations, retry logic correctness
```

## Important Notes

- This command works across different repositories - always read the local template
- Be thorough but concise - descriptions should be scannable
- Focus on the "why" as much as the "what"
- Include any breaking changes or migration notes prominently
- If the PR touches multiple components, organize the description accordingly
- Always attempt to run verification commands when possible
- Clearly communicate which verification steps need manual testing
