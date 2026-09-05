# Fable 5 Behavioral Delta Checklist

Analysis framework for the optimize-for-fable5 skill. Each item describes a
pattern to detect, the recommended action, the official Anthropic source, and
the rationale. The skill scans input text against these items and reports
findings.

## How to Use This Checklist

For each item, scan the input for the described pattern. When found, classify
the matched text as **stylistic** (safe to simplify) or **compliance-enforced**
(must preserve). Items marked ADD are about missing content — flag these as
recommended additions.

---

## Detection Items

### 1. Prescriptive Multi-Step Procedures

**Pattern**: Detailed step-by-step instructions that specify exactly how to
accomplish a task, with numbered steps, sub-steps, and specific method
prescriptions. Distinct from high-level workflow outlines that describe _what_
to do without dictating _how_.

**Direction**: SIMPLIFY to brief goal statements

**Why**: Fable 5 follows instructions with strong fidelity. Prescriptive
skills developed for prior models are "often too prescriptive for Claude
Fable 5 and can degrade output quality." A brief goal statement is as
effective as a detailed procedure — and less likely to constrain the model
into a suboptimal path.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

**How to classify**: If the procedure is stylistic (a preferred workflow that
could be accomplished multiple ways), simplify to a goal. If it's
compliance-enforced (steps mandated by an external system or safety protocol),
preserve as-is — see item 8.

**Example rewrite**:

- Before: "Step 1: Read the file. Step 2: Parse the JSON. Step 3: Extract the 'name' field. Step 4: Validate the name against the schema. Step 5: Return the validated name."
- After: "Extract and validate the 'name' field from the JSON file against the schema."

---

### 2. "Show Your Reasoning" / Reflection Instructions

**Pattern**: Instructions that tell the model to echo, transcribe, explain,
or display its internal reasoning in the response text. Examples: "think step
by step," "show your reasoning," "explain your thought process,"
"before answering, analyze the problem," any `<thinking>` / `<answer>` XML
structure the model is told to produce in visible output.

**Direction**: REMOVE

**Why**: These instructions can trigger the `reasoning_extraction` refusal
category on Fable 5, "causing elevated fallbacks to Claude Opus 4.8." This
is a live migration risk — a skill that worked fine on Claude 4 may
intermittently fail on Fable 5 because of this.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

**Important**: This is the highest-priority item in the checklist. Flag any
match as Priority: High in the report.

**Example rewrite**:

- Before: "Think step by step. First, analyze the problem. Then, propose a solution. Finally, verify your solution and explain your reasoning."
- After: Remove entirely. Fable 5 uses adaptive thinking (always on, cannot be disabled) — reasoning happens internally without prompting.

---

### 3. Anti-Laziness Instructions

**Pattern**: Instructions designed to prevent lazy, truncated, or incomplete
output. Examples: "don't be lazy," "write complete code," "don't truncate,"
"provide the full implementation," "be thorough," "above and beyond."

**Direction**: REPLACE with anti-gold-plating guidance

**Why**: Fable 5's failure mode is the opposite of laziness — it gold-plates,
adding features, refactoring, and introducing abstractions beyond what was
asked. Anti-laziness instructions amplify this tendency.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

**Example rewrite**:

- Before: "Always provide complete, production-ready code. Don't cut corners or use placeholder implementations."
- After: "Don't add features, refactor, or introduce abstractions beyond what the task requires. A bug fix doesn't need surrounding cleanup."

---

### 4. Missing Explicit Action Boundaries

**Pattern**: Instructions that describe what to do but don't explicitly state
what NOT to do. No clear boundary on the scope of permitted actions.

**Direction**: ADD explicit boundaries

**Why**: Fable 5 occasionally takes unrequested actions — drafting emails,
creating defensive git-branch backups, modifying files outside the stated
scope. Without explicit "do not" boundaries, it may act beyond intent.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

**Example addition**:

- Add: "Only modify files in src/auth/. Do not create new files, send messages, or modify configuration outside this directory."

---

### 5. Missing Turn-Ending Verification

**Pattern**: Skills or prompts that involve multiple tool calls but don't
include a check for the turn-ending failure mode.

**Direction**: ADD turn-ending check

**Why**: Fable 5 can "occasionally end a turn with a text-only statement of
intent ('I'll now run X') without issuing the corresponding tool call." The
work described in the statement never happens, and the model moves on as if
it did.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

**Example addition**:

- Add: "Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ('I'll...'), do that work now with tool calls."

---

### 6. Missing Grounded Progress Claims

**Pattern**: Skills or prompts where the model reports progress or status
during execution, without requiring that claims be grounded in actual tool
results.

**Direction**: ADD grounded-claims instruction

**Why**: Fable 5 can fabricate progress claims — reporting that a step
succeeded when it was never executed. Grounding claims in tool results
"nearly eliminated fabricated status reports even on tasks designed to elicit
them."

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

**Example addition**:

- Add: "Before reporting progress, audit each claim against a tool result from this session. Do not report success for a step unless you can point to the tool output that confirms it."

---

### 7. Rigid Rules Without Context or Rationale

**Pattern**: Rules stated as absolute prescriptions without explaining why
they exist or what goal they serve. The emphasis format itself is not the
problem — the absence of context is.

**Direction**: CONVERT to judgment with context

**Why**: Fable 5 follows brief instructions effectively. When rules include
context ("I'm working on [task] for [who]. They need [what]. With that in
mind: [request]"), the model applies them more intelligently.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5 and https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models

**How to classify**: If the rule is stylistic (naming conventions, formatting
preferences), convert to judgment with rationale. If it's compliance-enforced
(CI validator, security policy), preserve as-is — see item 8.

**Example rewrite**:

- Before: "Always use snake_case for Python function names."
- After: "Use snake_case for Python function names — this codebase follows PEP 8 and the linter enforces it."

---

### 8. Compliance-Enforced Hard Constraints

**Pattern**: Rules enforced by external systems (CI validators, API contracts,
security scanners, legal requirements) or that protect safety. These must
stay literal regardless of the target model.

**Direction**: PRESERVE

**Why**: Converting these to judgment risks silent failures. Fable 5's strong
instruction following makes it reliable at obeying hard constraints — there
is no benefit to softening them and real risk in doing so.

**Source**: https://platform.claude.com/docs/en/release-notes/system-prompts (Fable 5 system prompt retains NEVER/MUST NOT for child safety)

**How to identify**: Look for rules that reference specific tooling, API
specifications, security policies, legal requirements, or safety protections.
When uncertain, flag for user review rather than recommending simplification.

---

### 9. Effort Defaults at xhigh

**Pattern**: Explicit effort settings of `xhigh` or `max` carried over from
Opus 4.7/4.8 era guidance.

**Direction**: LOWER to `high` (default)

**Why**: "Lower effort settings on Claude Fable 5 still perform well and
often exceed xhigh performance on prior models." The starting point shifted
down — `high` is the recommended default.

**Source**: https://platform.claude.com/docs/en/build-with-claude/effort and https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

**Note**: Changing effort mid-conversation invalidates prompt caching.

---

### 10. Token-Based Thresholds

**Pattern**: Any hardcoded token count used for budgeting, truncation,
context window management, or cost estimation.

**Direction**: RECOUNT for the new tokenizer

**Why**: The tokenizer introduced in Opus 4.7 (used by all Claude 5 models)
produces ~1x-1.35x more tokens for the same text. Token-based thresholds
set for older models will be hit earlier than intended.

**Source**: https://platform.claude.com/docs/en/about-claude/models/migration-guide

**Note**: Line-based thresholds are unaffected. Only token-based numbers
need recounting.

---

### 11. Worked Examples for Tool Usage

**Pattern**: Step-by-step examples showing the model how to use a specific
tool, with sample inputs and expected outputs.

**Direction**: REMOVE

**Why**: Fable 5 handles tools effectively from their descriptions alone.
Worked examples constrain the model's exploration space and add token
overhead without proportional benefit.

**Source**: https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models

---

### 12. Verbose Instructions That Could Be Brief

**Pattern**: Long, detailed instructions that enumerate multiple cases or
spell out each behavior individually, when a brief directional statement
would achieve the same result.

**Direction**: CONDENSE

**Why**: Fable 5's strong instruction following means a brief instruction
is "as effective as listing each pattern." Verbose instructions add token
cost, increase the chance of conflicting guidance, and can trigger the
prescriptive-skill degradation noted in item 1.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

**Example rewrite**:

- Before: "When writing responses, use short sentences. Avoid jargon. Use active voice. Don't use filler words. Keep paragraphs to 3 sentences maximum. Use bullet points for lists. Bold key terms."
- After: "Write concisely in plain language."

---

### 13. Missing send_to_user Tool Guidance

**Pattern**: Skills that involve mid-run user communication (progress updates,
intermediate results, approval gates) but don't include guidance for using a
`send_to_user` client-side tool.

**Direction**: ADD if applicable

**Why**: Fable 5 "rarely calls" send_to_user without system-prompt elicitation.
If the skill involves delivering verbatim mid-run content to the user,
defining the tool is insufficient — the skill must explicitly prompt its use.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

**When to flag**: Only when the skill's workflow includes mid-run user delivery.
Skills that run to completion without intermediate user interaction don't need
this.

---

### 14. Missing Context-Budget Reassurance

**Pattern**: Skills that involve long autonomous runs (multi-hour agent
sessions, large codebase sweeps) but don't surface remaining context budget
or session health.

**Direction**: ADD if applicable

**Why**: Surfacing a remaining-token countdown triggers Fable 5 to manage its
own context more effectively — suggesting new sessions or trimming work to
fit the budget. Without this reassurance, long runs may degrade silently.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

**When to flag**: Only when the skill's workflow involves autonomous runs
likely to approach context limits. Short, interactive skills don't need this.
