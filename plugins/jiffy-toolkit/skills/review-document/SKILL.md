---
name: review-document
description: >
  Multi-agent document review and editing pipeline. Analyzes technical documents
  (markdown, Google Docs, HTML) across 7 dimensions — structure, prose quality,
  visual aids, accessibility, agent-readability, engagement, and consistency — using
  specialist review agents with post-processing calibration and deduplication. Applies
  edits directly (default) or produces a review-only report.
  Does NOT handle code review (use /code-review), Confluence pages, or
  non-document files like images or spreadsheets.
when_to_use: >
  Use when the user says "/review-document", "review this document", "edit this
  document for quality", "check this doc", or provides a document path/URL and asks
  for editorial feedback.
argument-hint: "<path-or-url> [--review-only]"
---

# Review Document

Multi-agent document review and editing via a 4-phase pipeline.

**Default prose policy: ASD-STE100 Simplified Technical English (STE)-informed, outcome-first writing.**
Apply the [STE-informed review guidance](references/editorial-reference.md#ste-informed-review)
to findings, suggested edits, and the review summary. This is a clarity review, not formal STE
certification. Respect document type, audience, and edit-safety rules; restructuring and subjective
rewrites remain recommendations, not automatic edits.

## Arguments

- First argument (required): file path (`.md`, `.html`) or Google Docs URL
- `--review-only`: produce findings report without applying edits
- Natural language detection: "just review", "don't edit", "review only", "no changes" in the invocation also triggers review-only mode

## Example

```
/review-document ~/docs/search-rfc.md
```

Runs the full 4-phase pipeline on a markdown file: gathers context, spawns 7 specialist reviewers in parallel, calibrates and deduplicates findings, then applies safe edits and prints a summary with manual recommendations.

```
/review-document https://docs.google.com/document/d/1abc123/edit --review-only
```

Reviews a Google Doc without applying any edits — produces a findings report grouped by severity.

## Phase 1: Context Gathering

### Step 1: Parse arguments

Extract the path or URL and any flags from the invocation.

### Step 2: Detect format

Determine the document format from the argument:

- `.md` extension → **markdown**
- `docs.google.com` URL or Google Docs ID → **google-docs**
- `.html` or `.htm` extension → **html**
- Anything else → print "Unsupported format. /review-document supports: markdown (.md), Google Docs (URL), and HTML (.html/.htm)." and **stop**.

### Step 3: Read the document

Read the full document — no limit/offset:

- **Markdown or HTML**: use the `Read` tool
- **Google Docs**: use your Google Docs connector's document-read tool
  - This read is **required** before any update call in Phase 4. For a large document, read its outline first and then read it section by section if the connector supports that.

### Step 4: Auto-detect document type

Infer the document type from content patterns:

| Pattern                                                                         | Type                   |
| ------------------------------------------------------------------------------- | ---------------------- |
| Frontmatter with "RFC" or "Design Doc"; "Alternatives Considered", "Background" | RFC                    |
| First heading "# [Name]"; "Installation", "Usage", "Contributing" sections      | README                 |
| Sequential numbered steps; "Prerequisites", "Step 1"                            | Tutorial               |
| "Problem Statement", "Proposed Solution", "Trade-offs"                          | Design doc             |
| Endpoint descriptions; request/response examples                                | API doc                |
| YAML frontmatter with `name`, `description`, `tools`                            | Skill/agent definition |

Default to **technical document** if no pattern matches.

### Step 5: Determine target audience

Infer audience from:

- Frontmatter fields (`audience`, `level`)
- Content complexity and terminology density
- Document type conventions (README → developers, tutorial → beginners, RFC → technical peers)

Default to **technical peers** if ambiguous.

### Step 6: Detect review mode

- Default: **edit mode** (apply safe edits directly)
- `--review-only` flag → **review-only mode**
- Natural language in the invocation: "just review", "don't edit", "review only", "no changes" → **review-only mode**

### Step 7: Load reference files

Read these two files now (the other three are loaded by agents directly):

- `references/finding-schema.md` — the inter-agent contract
- `references/severity-and-safety-tiers.md` — for Phase 3 severity filter and Phase 4 edit safety

### Step 8: Construct evaluation context

Build the evaluation context block that all Phase 2 agents receive:

```
Evaluation context:
- Format type: [markdown | google-docs | html]
- Document type: [RFC | README | tutorial | design-doc | api-doc | skill-definition | technical-document]
- Target audience: [description]
- Review mode: [edit | review-only]
- Prose policy: STE-informed and outcome-first, per references/editorial-reference.md#ste-informed-review; not formal compliance validation
- Document length: [word count]
```

## Phase 2: Specialist Review

### Step 1: Construct agent prompts

For each of the 7 specialist agents, build a prompt containing:

- The full document content
- The evaluation context from Phase 1
- Instruction to emit findings in finding-schema format
- Instruction to read `references/editorial-reference.md` and apply its STE-informed review guidance to the assigned dimension

Do NOT embed reference file content in the prompt — each agent loads its own references per its definition.

### Step 2: Spawn all 7 agents in parallel

**Agent delivery resilience**: Subagents may go idle without delivering results (known Claude Code issue). If an agent sends an `idle_notification` without content: (1) prompt it via SendMessage using its agent ID (not name), (2) if still no delivery, respawn once, (3) if respawn fails, proceed with findings from remaining agents. When spawning all 7 agents, consider sequential sub-batches to reduce cascade-failure risk.

Send a single message with 7 Agent tool calls:

| Agent                                      | Dimension                                                                  |
| ------------------------------------------ | -------------------------------------------------------------------------- |
| `jiffy-toolkit:structure-reviewer`         | Section ordering, heading hierarchy, logical flow, missing sections, outcome-first opening        |
| `jiffy-toolkit:prose-quality-reviewer`     | Grammar, clarity, conciseness, acronym enforcement                         |
| `jiffy-toolkit:visual-aid-reviewer`        | Diagram opportunities, cluttered diagram rewrites, diagram code generation |
| `jiffy-toolkit:accessibility-reviewer`     | Alt text, heading levels, color contrast, link text, unexplained terms                        |
| `jiffy-toolkit:agent-readability-reviewer` | LLM parsability, structured data, cross-references                         |
| `jiffy-toolkit:engagement-reviewer`        | Examples, callouts, collapsible content (format-aware)                     |
| `jiffy-toolkit:consistency-checker`        | Terminology, formatting, style consistency                                 |

### Step 3: Collect findings

Wait for all 7 agents to complete. Consolidate their findings into a single list.

If an agent returns null or fails, proceed with findings from the remaining agents. Log which agents failed in the Phase 4 summary statistics.

## Phase 3: Post-Processing

### Step 1: Calibration

Spawn `jiffy-toolkit:doc-review-calibrator` with:

- All findings from Phase 2
- The full document text
- Evaluation context from Phase 1

The calibrator performs adversarial verification (reads actual document text to validate each finding), applies the editorial decision framework, filters false positives, normalizes severity, assigns confidence, and classifies `auto_edit_safe`.

**Timeout**: 2 minutes. If timeout, skip calibration — proceed with raw findings but **set `auto_edit_safe: false` on ALL findings** (the calibrator's adversarial verification is what validates edit safety).

### Step 2: Severity filter

Inline logic (not an agent):

- Keep all severities: CRITICAL, MAJOR, MINOR, ENHANCEMENT
- In edit mode: additionally keep ENHANCEMENT findings with `auto_edit_safe: true`
- Filter out findings with `confidence < 0.5`

### Step 3: Deduplication

Spawn `jiffy-toolkit:doc-review-deduplicator` with the calibrated, filtered findings.

The deduplicator handles same-section, cross-section, adjacent-paragraph, and cross-category consolidation.

**Timeout**: 2 minutes. If timeout, skip deduplication and proceed with calibrated findings.

### Step 4: Collect final findings

The deduplicated list is the input for Phase 4.

## Phase 4: Edit or Report

### Edit mode (default)

**1. Classify findings** by `auto_edit_safe`:

- `true` → **auto-apply**: mechanical edits (spelling fixes, acronym expansions, heading corrections, alt text additions, diagram insertions)
- `false` → **recommend only**: content removal, restructuring, tone changes, subjective rewrites

**2. Apply auto-edit-safe findings** (format-aware):

**Markdown / HTML**: Use the `Edit` tool with exact string replacement. For each auto-edit finding:

1. Locate the text at `section_reference` + `location`
2. Apply `suggested_edit` as a replacement
3. For insertions (diagram code, alt text), insert at the identified location

**Google Docs**: Use your Google Docs connector's document-update tool:

1. **Re-read before editing**: read the document again — the pipeline took several minutes and the document may have changed since Phase 1
2. Use a text-replace edit for text substitutions and acronym expansions
3. Use an insert edit for diagram insertions and heading additions
4. When the document is not the user's own, submit changes as suggestions if the connector supports it
5. Batch multiple edits into a single call where possible; each edit's target text must already exist before the call

**3. Print inline summary**:

```markdown
## Review Complete

**Document**: [filename or Google Doc title]
**Type**: [auto-detected type] | **Audience**: [audience] | **Mode**: edit

### Changes Applied ([N] edits)

- [Edit description] — [section_reference]

### Manual Recommendations ([M] items)

#### Critical

- [body] — [section_reference]
  **Rationale**: [rationale]

#### Major

- ...

#### Minor

- ...

#### Enhancement

- ...

### Statistics

| Category          | Findings | Auto-edited | Manual |
| ----------------- | -------- | ----------- | ------ |
| Structure         | N        | X           | Y      |
| Prose             | ...      | ...         | ...    |
| Visual            | ...      | ...         | ...    |
| Accessibility     | ...      | ...         | ...    |
| Agent Readability | ...      | ...         | ...    |
| Engagement        | ...      | ...         | ...    |
| Consistency       | ...      | ...         | ...    |
| **Total**         | **N**    | **X**       | **Y**  |
```

### Review-only mode

1. No edits applied
2. Present all findings grouped by severity (Critical → Major → Minor → Enhancement)
3. Same summary format minus "Changes Applied" section
4. Each finding includes: body, section_reference, location, rationale, suggested_edit (if available), source_agent

## Reference Files

| File                                      | When Read                                        |
| ----------------------------------------- | ------------------------------------------------ |
| `references/finding-schema.md`            | Phase 1 Step 7 (construct evaluation context)    |
| `references/severity-and-safety-tiers.md` | Phase 1 Step 7 (severity filter + edit safety)   |
| `references/editorial-reference.md`       | By specialist agents — not read by SKILL.md      |
| `references/diagram-reference.md`         | By visual-aid-reviewer — not read by SKILL.md    |
| `references/acronym-allowlist.md`         | By prose-quality-reviewer — not read by SKILL.md |

## Notes

- Phase 1 MUST complete before Phase 2 (context informs review)
- Phase 2 agents run in parallel; Phase 3 agents run sequentially
- Finding schema is the contract between Phase 2 and Phase 3
- The SKILL.md orchestrates — agent behavior is defined in agent definitions, not here
- All agents emit findings in finding-schema format
- Google Docs requires read before update (MCP constraint)
