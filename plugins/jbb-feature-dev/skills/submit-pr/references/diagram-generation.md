# Diagram Generation

Reference for complexity analysis thresholds, exclusion criteria, metric calculation, and the visual-aid-recommender agent prompt template.

---

## Complexity Thresholds

Generate diagrams if **ANY** of these conditions are met:

| Condition | Threshold |
|-----------|-----------|
| `TOTAL_LINES > 500` AND `CHANGED_FILES > 5` | High volume of changes across multiple files |
| `CHANGED_FILES > 15` | Many files changed, regardless of line count |
| `NEW_MAIN_FILES >= 3` | Three or more new source files added |

---

## Exclusion Criteria

Skip diagram generation if **ALL** changed files match one of these patterns:

- **Config-only**: `.conf`, `.yaml`, `.yml`, `.json`, `.properties`, `.xml`, `.toml`
- **Test-only**: `**/test/**`, `**/tests/**`, `**/*Test.*`, `**/*Spec.*`
- **Documentation-only**: `.md`, `.rst`, `docs/**`, `README*`
- **Dependency-only**: `pom.xml`, `build.sbt`, `package.json`, `requirements.txt`, `Cargo.toml`
- **Simple hotfix**: Single file changed with `TOTAL_LINES < 100`

Also skip if the `--no-diagram` flag was specified by the user.

---

## Bash Metric Calculation Snippets

Run these commands to calculate PR complexity metrics:

```bash
# Lines added and deleted
ADDITIONS=$(git diff --numstat origin/{{TARGET_BRANCH:-master}}...HEAD | awk '{sum+=$1} END {print sum+0}')
DELETIONS=$(git diff --numstat origin/{{TARGET_BRANCH:-master}}...HEAD | awk '{sum+=$2} END {print sum+0}')
TOTAL_LINES=$((ADDITIONS + DELETIONS))

# Number of files changed
CHANGED_FILES=$(git diff --name-only origin/{{TARGET_BRANCH:-master}}...HEAD | wc -l | tr -d ' ')

# New source files added (potential new components)
NEW_MAIN_FILES=$(git diff --name-only --diff-filter=A origin/{{TARGET_BRANCH:-master}}...HEAD | grep -E 'src/main/.*\.(java|scala|py|ts|tsx|js|jsx)$' | wc -l | tr -d ' ')

# Check exclusion criteria — count files that do NOT match exclusion patterns
CHANGED_FILE_LIST=$(git diff --name-only origin/{{TARGET_BRANCH:-master}}...HEAD)
EXCLUDED_PATTERNS="^\.(conf|yaml|yml|json|properties|xml|toml)$|/test/|/tests/|Test\.|Spec\.|\.md$|\.rst$|^docs/|^README|^pom\.xml$|^build\.sbt$|^package\.json$|^requirements\.txt$|^Cargo\.toml$"
NON_EXCLUDED_FILES=$(echo "$CHANGED_FILE_LIST" | grep -vE "$EXCLUDED_PATTERNS" | wc -l | tr -d ' ')
```

---

## GENERATE_DIAGRAM Decision Logic

```
GENERATE_DIAGRAM = (
  NOT --no-diagram flag present
  AND NON_EXCLUDED_FILES > 0
  AND (
    (TOTAL_LINES > 500 AND CHANGED_FILES > 5) OR
    (CHANGED_FILES > 15) OR
    (NEW_MAIN_FILES >= 3)
  )
)
```

---

## Complexity Analysis Output Table

Show this table to the user for visibility before spawning the agent:

```
## PR Complexity Analysis

| Metric             | Value          | Threshold               |
|--------------------|----------------|-------------------------|
| Total lines changed | [TOTAL_LINES] | > 500                   |
| Files changed       | [CHANGED_FILES]| > 5 (with lines) or > 15|
| New source files    | [NEW_MAIN_FILES]| >= 3                   |

**Diagram generation**: [Will generate / Skipped — reason]
```

---

## Visual-aid-recommender Agent Prompt Template

When `GENERATE_DIAGRAM` is true, spawn the `visual-aid-recommender` agent using the Task tool with this prompt:

```
Analyze this PR to generate 1-2 diagrams that help explain the code changes.

## PR Context
- Title: {{SUGGESTED_PR_TITLE}}
- Files changed: {{CHANGED_FILES}}
- Lines: +{{ADDITIONS}} -{{DELETIONS}}

## Summary of Changes
{{SUMMARY_OF_KEY_CHANGES}}

## New/Modified Files of Interest
{{LIST_OF_KEY_NEW_OR_MODIFIED_FILES}}

## Requirements
1. Generate at most 2 diagrams (preferably 1 if it captures the essence)
2. Use Mermaid syntax (renders natively in GitHub)
3. Focus on HIGH-LEVEL flow, not implementation details
4. Prefer flowcharts for business logic, sequence diagrams for service integrations
5. Keep diagrams simple enough to read without zooming (max 10-15 nodes)
6. Include a brief caption for each diagram explaining what it shows
7. Do NOT include accessibility metadata (alt text, long description) — just the diagram and caption
8. Never use literal \n in node labels — Mermaid renders it as visible text. Use <br> for line breaks within labels (e.g., A["Line one<br>Line two"])

## Output Format
For each diagram, provide:

### Diagram [N]: [Brief Title]
**Caption**: [1-2 sentence explanation of what this diagram shows]

```mermaid
[Complete Mermaid diagram code]
```
```

**Wait for the agent to complete** before proceeding. Parse the response for diagram code and captions, then store for inclusion in the PR description.

---

## Notes on Unhelpful Diagrams

Diagram generation is best-effort — not all PRs benefit from visualization. If a generated diagram is not helpful, the "Architecture Overview" section can simply be deleted from the PR description before publishing.
