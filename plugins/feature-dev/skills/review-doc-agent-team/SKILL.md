---
name: review-doc-agent-team
description: >
  Review research documents and implementation plans using a dynamically composed
  agent team with deliberation. Supports agent teams (primary) and sub-agent
  fallback. Use when asked to "review a research document", "review a plan",
  "review this document with an agent team", or when reviewing files in
  ~/.claude/thoughts/shared/research/ or ~/.claude/thoughts/shared/plans/.
---

# Document Review Agent Team

Review research documents and implementation plans using a team of 4-10
specialized reviewers who deliberate, challenge each other's findings, and
produce a structured decision record.

## Reference Files

| File | When to Read |
|------|-------------|
| `references/roles.md` | Phase 3 (Compose Team) — to get persona prompts |
| `references/dynamic-composition.md` | Phase 2 (Classify) — to determine team composition |
| `references/decision-record-template.md` | Phase 6 (Decision Record) — to format output |

Teammates are told to use the `decision-principles` skill for judgement calls —
the skill is referenced by name, not embedded into prompts.

---

## Workflow

### Phase 1: Read Document

1. Accept document path as argument (or ask user if not provided)
2. Read the entire document into context (no limit/offset — full file)
3. Note: this skill reviews local markdown files, not Google Docs

### Phase 2: Classify & Compose

1. Read `references/dynamic-composition.md`
2. Classify document type: `research_document` or `implementation_plan`
   - Use location signals (research/ vs plans/ directory) and content signals
   - If ambiguous, ask the user
3. Classify complexity: `simple`, `moderate`, or `complex`
   - Count words, top-level sections (## headers), and cross-references
4. Determine base team (4 core roles by document type)
5. Scan document for content signals from the Signal Detection Table
6. Add extended roles up to the complexity limit, in priority order
7. Present classification and team composition to the user (use the output
   format from `references/dynamic-composition.md`)

### Phase 3: Determine Coordination Mechanism

Check if agent teams are available:

**Detection**: Check for `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` environment
variable. If set to `1` or `true`, use the agent team path. Otherwise, use the
sub-agent fallback.

```bash
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
```

Branch to Phase 4A (agent team) or Phase 4B (sub-agent fallback).

### Phase 4A: Agent Team Path

> Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

1. Read `references/roles.md` for persona prompts
2. Create an agent team with the Synthesis Lead as team lead (Opus model)
3. Spawn teammates (Sonnet model) with:
   - Their full persona prompt from `references/roles.md`
   - Instruction: "Use the `decision-principles` skill when making judgement calls"
   - The document to review (full path)
   - Review criteria specific to document type
4. Pre-allocate ALL triggered extended roles at creation time (agent teams
   cannot add teammates mid-session). Extended roles whose concerns don't arise
   should declare their stand-down message and disengage.
5. Review lifecycle:
   a. **Independent review** — all teammates read the document and post findings
   b. **Deliberation** — Critical Analyst challenges findings; teammates debate
   c. **Moderation** — Synthesis Lead identifies agreement and disagreement
   d. **Consensus** — team votes on proposed changes and verdict
6. Proceed to Phase 5

### Phase 4B: Sub-Agent Fallback Path

> Used when agent teams are not enabled (current default)

1. Read `references/roles.md` for persona prompts
2. Display notice to user:
   ```
   Agent teams not enabled. Using sub-agent fallback — reviewers will not
   deliberate directly with each other. To enable agent teams, set
   CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 in your environment.
   ```
3. Spawn all determined roles as **parallel sub-agents** (Agent tool,
   subagent_type: `general-purpose`, model: `sonnet`):
   - Each receives: their persona prompt + instruction to use `decision-principles`
     skill + the full document text + review criteria for the document type
   - Each returns: structured findings with severity tags (Critical / High /
     Medium / Low) and their stand-down declaration if no concerns
4. Collect and synthesise initial findings:
   - **Agreement**: Issues flagged by >=2 reviewers
   - **Disagreement**: Conflicting assessments on the same topic
   - **Unique concerns**: Issues flagged by only one reviewer
5. **Deliberation round** (simulated):
   - For each major disagreement, spawn a targeted sub-agent with the Critical
     Analyst persona, providing BOTH positions and asking it to evaluate which
     is stronger using the `decision-principles` skill
   - This simulates the debate that agent teams handle natively
   - Minor disagreements (Low severity from both sides) are recorded but not
     deliberated
6. Proceed to Phase 5

### Phase 5: Apply Changes (if any)

The review team applies document changes autonomously — no user approval needed
per change. All changes are documented in the decision record for traceability.

**If changes are proposed:**
1. Team deliberates on each proposed change (agent team) or the main session
   evaluates consensus from reviewer findings (sub-agent fallback)
2. Changes with consensus are applied directly to the document
3. All changes are recorded: section, original text, new text, proposed by,
   consensus method, rationale

**If the team cannot reach consensus on a specific change:**
- Categorise the blocker: **lack of information** or **requires user judgement**
- Lack of information: at least one reviewer runs a research task to find the
  answer, then the team re-deliberates
- Requires user judgement: do NOT block the review. Document the unresolved
  question in the decision record ("Dissenting Opinions" and "Conditions for
  Re-Review" sections) and highlight it in the Phase 7 summary
- The review team should never wait for the user to finish deliberating

**If no changes are proposed:** Record "No changes were made to the original document."

### Phase 6: Produce Decision Record

The Synthesis Lead (agent team path) or the main orchestrator session (sub-agent
fallback) produces the decision record:

1. Read `references/decision-record-template.md`
2. Create output directory: `mkdir -p ~/.claude/thoughts/shared/decision_records/`
3. Generate the decision record following the template, filling in all sections:
   - All metadata (document path, date, team composition, type, complexity)
   - Executive summary (synthesised from all reviewer findings)
   - Discussion points table (from deliberation)
   - Dissenting opinions (if any reviewer disagreed with final verdict)
   - Changes made table (from Phase 5)
   - Principles applied table
   - Confidence assessment
   - Conditions for re-review
   - Review metadata (iterations, duration, mechanism used)
4. Save to: `~/.claude/thoughts/shared/decision_records/YYYY-MM-DD-{doc-name}.md`

### Phase 7: Present Results

Display to user:
- **Verdict**: Approved / Approved with Revisions / Rejected
- **Key discussion points** (top 3)
- **Dissenting opinions** (if any)
- **Unresolved questions** (if any, from Phase 5 consensus failures)
- **Decision record path**
- Ask: "Would you like me to elaborate on any finding?"

---

## Human Escalation Protocol

**Interactive mode** — escalate to the human when:
- Critical Analyst reaches max iterations (4 rounds) without resolution
- Fundamental disagreement that consensus can't resolve
- Review requires judgement beyond the team's scope

**Non-interactive mode** (e.g., background execution) — continue deliberating.
Write blockers in the decision record's "Confidence Assessment" and "Conditions
for Re-Review" sections rather than interrupting.
