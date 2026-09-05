# Opus 5 Behavioral Delta Checklist

Analysis framework for the optimize-for-opus5 skill. Each item describes a
pattern to detect, the recommended action, the official Anthropic source, and
the rationale. The skill scans input text against these items and reports
findings.

## How to Use This Checklist

For each item, scan the input for the described pattern. When found, classify
the matched text as **stylistic** (safe to convert) or **compliance-enforced**
(must preserve). Items marked ADD are about missing content — flag these as
recommended additions.

---

## Detection Items

### 1. Verification and Self-Check Instructions

**Pattern**: Instructions that tell the model to verify its own work, re-check
answers, double-check results, or run a self-validation step before responding.
Examples: "verify your answer," "double-check the output," "include a final
verification step," "use a subagent to verify," "re-verify before responding."

**Direction**: REMOVE

**Why**: Opus 5 completes full tasks rather than leaving stubs. These
instructions cause over-verification — the model wastes tokens re-checking
work that was already correct, with no quality improvement.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5

**Example rewrite**:

- Before: "After generating the response, verify each claim against the source material and correct any errors."
- After: Remove entirely. Opus 5's native thoroughness handles this without prompting.

---

### 2. Worked Examples for Tool Usage

**Pattern**: Step-by-step examples showing the model how to use a specific
tool, with sample inputs and expected outputs. Distinct from _conceptual_
examples that illustrate a pattern or convention.

**Direction**: REMOVE

**Why**: Worked tool-usage examples constrain the model's exploration space.
Opus 5 handles tools more effectively when given a well-designed tool interface
(clear parameter names, good descriptions) rather than prescriptive examples.

**Source**: https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models

**Example rewrite**:

- Before: "To search code, call the tool like this: `search_code(query='auth middleware', lang='python')`. The result will contain..."
- After: Remove the example. Ensure the tool's own description and parameter names are clear enough to be self-explanatory.

---

### 3. Anti-Laziness Instructions

**Pattern**: Instructions designed to prevent the model from being lazy,
truncating output, or producing incomplete work. Examples: "don't be lazy,"
"write complete code," "don't truncate," "provide the full implementation,"
"be thorough and complete," "above and beyond."

**Direction**: REPLACE

**Why**: Opus 5's failure mode is over-work, not laziness. Anti-laziness
instructions are unnecessary and can amplify over-verification. Replace with
anti-over-work guidance if needed.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5

**Example rewrite**:

- Before: "Always provide complete, production-ready code. Never use placeholders or stubs."
- After: "Don't add features, refactor, or introduce abstractions beyond what the task requires. A bug fix doesn't need surrounding cleanup."

---

### 4. Rigid Stylistic Rules Without Rationale

**Pattern**: Rules stated as absolute prescriptions (with or without ALL-CAPS
emphasis) that govern style, convention, or approach — without explaining _why_
the rule exists. The emphasis format itself is not the problem; the absence
of rationale is.

**Direction**: CONVERT to judgment-based principle with rationale

**Why**: Opus 5 follows rules literally, including ones that don't apply to the
current context. A rigid rule without rationale gets followed even when
judgment would produce a better result. Adding the "why" lets the model apply
the principle intelligently.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

**How to classify**: If the rule is stylistic (naming conventions, comment
density, formatting preferences), convert to judgment. If it's
compliance-enforced (CI validator, security policy, API contract), preserve
as-is — see item 5.

**Example rewrite**:

- Before: "NEVER use abbreviations in variable names."
- After: "Prefer descriptive variable names over abbreviations — abbreviated names make code harder to review and are a common source of confusion in this codebase's PR reviews."

---

### 5. Compliance-Enforced Hard Constraints

**Pattern**: Rules that are enforced by external systems (CI validators, API
contracts, security scanners, legal requirements) or that protect safety
(child safety, PII handling). These must stay literal regardless of the
target model.

**Direction**: PRESERVE

**Why**: Converting these to judgment risks silent failures. A CI validator
doesn't care about rationale — it rejects the build. Safety constraints exist
for non-negotiable reasons.

**Source**: https://platform.claude.com/docs/en/release-notes/system-prompts (Opus 5 system prompt retains NEVER/MUST NOT for child safety)

**How to identify**: Look for rules that reference specific tooling (linters,
validators, CI checks), API specifications, security policies, legal
requirements, or safety protections. When uncertain, flag for user review
rather than recommending conversion.

**Examples of hard constraints to preserve**:

- "No non-ASCII characters in YAML comments" (CI validator rejects)
- "Never commit .env files" (security)
- "All API responses must include the X-Request-Id header" (API contract)

---

### 6. Duplicated Instructions

**Pattern**: The same instruction appearing in both the system prompt (or
CLAUDE.md) and a tool description, or repeated across multiple sections of
a skill.

**Direction**: CONSOLIDATE into the tool description

**Why**: Opus 5 reads tool descriptions carefully. Duplicating instructions
wastes tokens and creates maintenance burden — when one copy is updated and
the other isn't, the model gets conflicting guidance.

**Source**: https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models

---

### 7. Missing Scope Constraints

**Pattern**: Instructions that tell the model what to do but not where to
stop. No explicit boundaries on what is in-scope vs out-of-scope.

**Direction**: ADD scope constraints

**Why**: Opus 5 expands scope — it adds unrequested steps, refactors adjacent
code, or investigates tangential questions. Without explicit scope limits, it
will do more than asked.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5

**Example addition**:

- Add: "Scope: only modify files in the `src/auth/` directory. Do not refactor adjacent modules even if you notice opportunities."

---

### 8. Subagent Delegation Without Caps

**Pattern**: Instructions that encourage or allow the model to delegate work
to subagents without specifying limits on how many or when.

**Direction**: ADD delegation limits

**Why**: Opus 5 over-delegates — it spawns more subagents than needed,
increasing cost and latency without proportional quality gain.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5

**Example addition**:

- Add: "Use at most 3 subagents for this task. Prefer doing work directly over delegating when the task is straightforward."

---

### 9. Explicit Chain-of-Thought / "Show Your Reasoning"

**Pattern**: Instructions that tell the model to show its reasoning, think
step by step in the response, or produce `<thinking>` / `<answer>` XML
structures in the output text.

**Direction**: REMOVE

**Why**: With thinking enabled (default on Opus 5), explicit CoT in the
response is redundant. With thinking disabled, Opus 5 can leak internal XML
tags (`<thinking>`, `<answer>`) into the response text. Instructions telling
the model "not to think" or "not to reason" increase tag leakage.

**Source**: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5

**Example rewrite**:

- Before: "Think step by step. First analyze the problem, then propose a solution, then verify your solution."
- After: Remove entirely if thinking is enabled. If thinking is disabled, remove and accept that reasoning happens internally.

---

### 10. Effort Defaults at xhigh

**Pattern**: Explicit effort settings of `xhigh` or `max` carried over from
Opus 4.7/4.8 era guidance.

**Direction**: LOWER to `high` (default) and recommend an effort sweep

**Why**: Opus 4.7/4.8 guidance was "start with xhigh for coding and agentic
use cases." Opus 5 guidance is "start at high (default), use low and medium
liberally." Opus 5 converts additional effort into better results more
reliably, but the starting point shifted down.

**Source**: https://platform.claude.com/docs/en/build-with-claude/effort

**Note**: Effort controls thinking volume, not visible response length.
Lowering effort will not shorten responses — prompt for length separately.
Changing effort mid-conversation invalidates prompt caching.

---

### 11. Token-Based Thresholds

**Pattern**: Any hardcoded token count used for budgeting, truncation,
context window management, or cost estimation. Examples: "limit to 4000
tokens," "if the response exceeds 8192 tokens."

**Direction**: RECOUNT for the new tokenizer

**Why**: The tokenizer introduced in Opus 4.7 (used by all Claude 5 models)
produces ~1x-1.35x more tokens for the same text compared to Claude 4.6 and
earlier. Token-based thresholds set for older models will be hit earlier
than intended.

**Source**: https://platform.claude.com/docs/en/about-claude/models/migration-guide

**Note**: Line-based thresholds (e.g., "SKILL.md under 500 lines") are
unaffected. Only token-based numbers need recounting.

---

### 12. Upfront Context Dumps

**Pattern**: Large blocks of context, documentation, or reference material
loaded at the start of the prompt regardless of whether the current task
needs it.

**Direction**: CONVERT to progressive disclosure

**Why**: Opus 5 works better with context loaded on demand. Large upfront
dumps dilute attention and waste tokens on context that may not be relevant
to the current task.

**Source**: https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models

**Example rewrite**:

- Before: Including a 200-line API reference at the top of every prompt
- After: Move the reference to a `references/` file and add a pointer: "Read `references/api-reference.md` when the task involves API endpoints."
