---
name: rfc-review
description: Comprehensive RFC review using specialized subagents with context gathering, technical analysis, and synthesis. Use when the user wants a thorough review of an RFC document.
argument-hint: [google-doc-url-or-file-path]
---

# RFC Review

Conduct a comprehensive review of an RFC (Request for Comments) by gathering context, researching domain-specific terminology, running specialized review subagents in parallel, and generating a structured review report.

**IMPORTANT**: This is a review skill. DO NOT modify the RFC. Only provide constructive, actionable analysis and recommendations.

## Workflow Overview

```
Step 1: Get RFC Input & Read Fully
   ↓
Step 2: Summarize Linked Documents ← BLOCKING
   └─ linked-document-summarizer (all document types)
   ↓
Step 3: Extract Terms/Systems for Research
   ↓
Step 4: Spawn Context-Gathering Agents ← BLOCKING
   ├─ web-search-researcher (internal/unfamiliar terms)
   ├─ web-search-researcher (external concepts)
   └─ repo-discovery (systems mentioned in RFC)
   ↓
Step 5: Spawn Codebase Exploration Agents (if repos discovered) ← BLOCKING
   └─ codebase-explorer (local, indexed, or external repos)
   ↓
Step 6: Spawn Review Agents ← BLOCKING
   ├─ rfc-reviewer
   ├─ gemini-rfc-reviewer
   └─ visual-aid-recommender (generates diagram CODE)
   ↓
Step 7: Synthesize All Findings
   ↓
Step 8: Generate Review Report
   ↓
Step 9: Present Review to User
```

## Instructions

### 1. Get RFC Input & Read Fully

**Arguments**:

- `[google-doc-url-or-file-path]` (required): The RFC to review
- `--skip-linked-docs` (optional): Skip summarization of linked documents

**Read the RFC completely** before proceeding. For Google Docs, use the google-drive MCP tools. For local files, use Read without limit/offset.

### 2. Summarize Linked Documents

By DEFAULT, summarize all linked documents via the **linked-document-summarizer** subagent.

> **CRITICAL**: Do NOT read linked documents into main context. Delegate ALL reading to the subagent.
> **CRITICAL**: Do NOT pre-filter documents by type. Send ALL linked documents to the subagent.

If more than 10 linked documents found, ask user to prioritize.

### 3. Extract Terms/Systems for Research

Analyze RFC content to identify:

- **organisation-specific terms** that need research
- **External concepts** that may need research
- **Systems/services** mentioned that may need codebase exploration

**Detect technical domains** for specialized review:

Follow the detection procedure in `skills/shared-references/domain-agent-registry.md` — check file names/paths against file triggers first, then check content for strong and corroborating signals.

**Required: Agent Type Verification**

After detecting domains, create an explicit agent contract.
Reference: See `skills/shared-references/agent-verification-pattern.md` for the full pattern.

### 4. Spawn Context-Gathering Agents

**BLOCKING STEP** - Launch IN PARALLEL:

- **web-search-researcher** (if unfamiliar internal terms found)
- **web-search-researcher** (if external concepts found)
- **repo-discovery** (if systems/services mentioned)

Wait for ALL to complete before Step 5.

### 5. Spawn Codebase Exploration Agents

Only runs if repo-discovery found repositories. If >5 repos found, ask user to prioritize.

For each repository, spawn **codebase-explorer** IN PARALLEL.

### 6. Spawn Review Agents

**BLOCKING STEP** - Launch IN PARALLEL:

**REQUIRED: Pre-Spawn Verification Table** (see `skills/shared-references/agent-verification-pattern.md`)

- **rfc-reviewer**: Technical merit, problem-solution fit, assumptions, evidence
- **gemini-rfc-reviewer**: Alternative perspective using Gemini model
- **visual-aid-recommender**: Diagram code generation (Mermaid/PlantUML)
- **Domain expert reviewers** (if detected in Step 3)

### 7. Synthesize All Findings

**REQUIRED: Pre-Synthesis Agent Verification**

- Consolidate and deduplicate review findings
- Prioritize: Critical → Major → Minor → Enhancement
- Build the Glossary from research findings
- Process visual aids from visual-aid-recommender

### 8. Generate Review Report

Write to `~/.claude/thoughts/shared/reviews/rfc-review_{{RFC_TITLE_KEBAB_CASE}}_{{TIMESTAMP}}.md`

Report structure:

- Executive Summary
- RFC At-a-Glance (Problem, Solution, Key Decisions, Findings Summary)
- Visual Aids (Mermaid diagrams)
- Glossary (terms with citations)
- Technical Review Findings (Strengths, Critical/Major/Minor Issues)
- Risk Analysis
- Open Questions & Concerns
- Context Completeness Assessment
- Overall Recommendation (Approve / Approve with Changes / Request Revision)
- Review Methodology

### 9. Present Review to User

Display summary, list visual aids generated, ask for follow-up.

## Important Notes

- **No RFC modifications**: Only review and generate a report
- **NEVER read linked documents in main context**: Delegate to subagent
- **NEVER pre-filter documents by type**: Send ALL to subagent
- **Sequential phase execution**: Complete context-gathering before reviews, reviews before synthesis
- **Parallel execution within phases**: Launch all agents per phase in parallel
- **Include context in prompts**: Review agent prompts MUST include findings from context-gathering
- **Constructive feedback**: All feedback must be actionable, specific, and constructive
- **Deduplication**: Consolidate duplicate findings from multiple reviewers
- **Glossary citations**: Every term must include a source/documentation link
- **Diagram code**: All diagrams as Mermaid/PlantUML code blocks, no external rendering
- **Repository discovery delegation**: NEVER search for repos in main agent context
- **Repository exploration limits**: If >5 repos, MUST ask user to prioritize

## Review Dimensions Checklist

Before finalizing, ensure these are assessed:

- [ ] Problem-Solution Fit
- [ ] Technical Soundness
- [ ] Assumptions
- [ ] Evidence
- [ ] Alternatives
- [ ] Risks
- [ ] Impact Analysis
- [ ] Scope
- [ ] Implementation Path
- [ ] Backwards Compatibility
- [ ] Security Implications
- [ ] Operational Concerns
- [ ] Context Completeness
