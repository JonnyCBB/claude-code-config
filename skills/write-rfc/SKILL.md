---
name: write-rfc
description: Write a high-quality RFC following RFC best practices. Use when the user wants to create an RFC document with visual aids, editorial review, and technical review.
argument-hint: [brief RFC topic description]
---

# Write RFC

You are tasked with writing a high-quality RFC (Request for Comments) document following RFC best practices, based on the quality dimensions research in `~/.claude/thoughts/shared/research/2025-11-13-rfc-quality-dimensions.md`.

## Initial Setup:

When this skill is invoked, respond with:

```
I'm ready to write an RFC. Please provide:
1. The problem you're trying to solve
2. Any relevant context (tickets, docs, existing code, related RFCs)
3. Any constraints or requirements

I'll guide you through creating a high-quality RFC that follows RFC best practices.
```

Then wait for the user's input.

## Steps to follow after receiving the RFC context:

### 1. Read all referenced materials first

- **CRITICAL**: Read the RFC quality dimensions guide first: `~/.claude/thoughts/shared/research/2025-11-13-rfc-quality-dimensions.md`
- Read all user-mentioned files, tickets, docs, Google Docs FULLY
- Google docs should be read using the google-drive MCP tool

### 2. Synthesize the information

- **ULTRATHINK deeply** about how to synthesize all provided information
- Plan the main text vs appendix division:
  - Main text (5-10 pages, 2000-3000 words max): Decision-critical information
  - Appendix (unlimited): Implementation details and supporting information
  - **Litmus test**: If removing this section would prevent understanding whether the proposal is sound → MAIN TEXT. Otherwise → APPENDIX.

### 3. Draft RFC structure with user

- Confirm problem statement accuracy, scope, stakeholders, timeline
- Ask: "Does this structure capture what you need?"

### 4. Write the RFC markdown file

Follow the template structure:

- RFC metadata (Published, Authors, Decision by, Consulted, Informed, Status)
- Executive Summary
- Need (problem + impact + what happens if we do nothing)
- Guiding Principles (3-5 constraints)
- Proposed Solution (high-level, PM-accessible)
- Case Studies (if applicable)
- Alternatives Considered (at least 2)
- Risks and Tradeoffs
- Out of Scope
- Open Questions / Unknowns (optional)
- Resources (Related RFCs, Strategy Documents)
- Appendix (Detailed Design, Configuration Examples, Implementation Plan, Additional Context)

Save to: `rfcs/YYYY-MM-DD-rfc-topic-name.md`

**Apply the 15 Quality Dimensions**: Brevity, Visual Communication, Explicit Scope, Concrete Examples, Case Studies, Alternatives, Risk Assessment, Resources, Appendices, Accessibility, Clear Problem Statement, Guiding Principles, Implementation Path, Metadata, Configuration Examples.

### 5. Identify visual aid opportunities

- Use the **visual-aid-recommender** agent to analyze the RFC
- Present recommendations to user

### 6. Add visual aids (if requested)

- Create diagrams using Mermaid or PlantUML
- Insert inline in appropriate sections

### 7. Review and reference visual aids in text

- Add explicit references to diagrams
- Remove or condense redundant text that diagrams already explain

### 8. Run document editorial review

- Use the **document-editor-reviewer** agent
- Present findings and ask: "Would you like me to apply these editorial recommendations?"

### 9. Apply editorial improvements (if approved)

### 10. Add emojis to headers (optional)

- Ask user if they want emojis for visual navigation

### 11. Run RFC technical reviews (in parallel)

- **rfc-reviewer** agent
- **gemini-rfc-reviewer** agent
- Domain expert agents (if detected per the procedure in `skills/shared-references/domain-agent-registry.md` — file triggers first, then content signals)

### 12. Synthesize and present technical review findings

### 13. Apply technical improvements (if approved)

### 14. Present RFC for user review

- Ask for confirmation before converting to Google Docs

### 15. Iterate based on feedback

### 16. Convert to Google Docs

- Use the `google-docs` skill
- Remind user to set sharing permissions and share in appropriate Slack channel

### 17. Validate Google Doc Formatting Visually

- Use the **google-docs-visual-formatter** subagent for automated comparison and fixing

### 18. Final steps

- Keep markdown version in `rfcs/`
- Offer to create Jira ticket, draft Slack message, or link from code

## Quality Checklist

Before presenting for user review, verify:

- [ ] Main text: 2000-3000 words max (Appendix unlimited)
- [ ] Main text vs Appendix: Each section in the right place
- [ ] Visual Communication: Diagrams for complex concepts
- [ ] Explicit Scope: Clear in/out of scope
- [ ] Concrete Examples: Real configs, code, data
- [ ] Alternatives: At least 2 with pros/cons
- [ ] Risk Assessment: Honest risks with mitigations
- [ ] Resources: Links to related RFCs, docs, code
- [ ] Appendices: Implementation details moved out of main flow
- [ ] Accessibility: Core ideas before technical details
- [ ] Problem Statement: Clear why with concrete examples
- [ ] Guiding Principles: 3-5 design constraints
- [ ] Implementation Path: Migration, rollout, rollback
- [ ] Metadata: DACI model with deadline
- [ ] Configuration Examples: Copy-pastable snippets
- [ ] Editorial Quality: Reviewed by document-editor-reviewer agent
- [ ] Technical Merit: Reviewed by both rfc-reviewer and gemini-rfc-reviewer agents

## Anti-Patterns to Avoid

1. **The Encyclopedia** - Too much detail in main text
2. **The Mystery** - Not explaining the problem
3. **The Fait Accompli** - Only one solution
4. **The Technical Deep Dive** - Leading with implementation
5. **The Optimist** - Ignoring risks
6. **The Hand-Waver** - Hiding unknowns
7. **The Orphan** - No clear owners
8. **The Scope Creep** - Too many problems
9. **The Text Wall** - No visual aids
10. **The Abstract** - No concrete examples
11. **The Stale Doc** - Not planning updates
