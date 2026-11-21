---
name: optimize-for-opus-5-5
description: >
  Scans a prompt, skill directory or context file (CLAUDE.md, AGENTS.md) for the documented
  behaviour changes in Claude Opus 5.5 and proposes specific, cited edits. Separates stylistic
  rules (convert to judgment) from rules an API or validator enforces (keep literal). Use only
  when adapting, migrating or checking instructions for Opus 5.5, for example "optimize for
  opus 5.5", "migrate this prompt from Opus 5", "is this skill Opus 5.5 compatible". Do not use
  for general prompt or skill review (use context-and-skills-standards), for other models, or
  for skill-trigger tuning (use skill-creator).
---

# Optimize for Opus 5.5

Produce a report, not a rewrite. Every finding traces to one delta below and carries its source URL.

Sources:
- [P2] https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5
- [W] https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5
- [M] https://platform.claude.com/docs/en/models/opus-5-5/migration-guide
- [E] https://platform.claude.com/docs/en/build-with-claude/effort
- [P1] https://claude.com/resources/articles/using-claude-opus-5-5-as-your-daily-driver-for-knowledge-work
- [P3] https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5

## Workflow

1. Read the whole input. For a skill directory, read `SKILL.md` and every file it links to.
2. Scan against each delta. Report each instance separately, with its location and exact text.
3. Classify each matched rule:
   - **Stylistic**: a preference or habit. Propose a judgment-based rewrite.
   - **Enforced**: an API rejects it, a validator or CI check fails on it, or it guards security,
     safety or an irreversible action. Keep it literal. When you cannot tell which, say so and
     ask the user to confirm before they apply the change.
4. Flag a rule the input itself breaks; it cannot be followed literally.
5. Write the report.

## Deltas

1. **Reasoning prompts** ("think hard", "think carefully", "think step by step"). Remove.
   Thinking is always on and the model sets its own depth from the request and effort. [P1] [P2]
2. **Thinking switched off, or "do not think" rules.** `thinking: {"type": "disabled"}` returns a
   400 at every effort level (enforced). Remove the no-thinking rule. If short answers matter,
   the optional line is "Answer directly without deliberating."; measure quality when added. [W] [E] [P2]
3. **Asks to reproduce reasoning in the reply** ("show your reasoning", `<thinking>` in output).
   May be refused as `reasoning_extraction`. Read reasoning from `display: "summarized"` instead. [P2]
4. **Effort.** Unset effort now runs at `medium` (Opus 5 default was `high`). Recommend setting it
   explicitly and a sweep on the user's own evals. Keep `xhigh`/`max` only with a measured gain.
   To get less thinking, lower effort first. [P2] [E] [W]
5. **Generic style instructions** ("be concise", "write naturally"). These mostly swap one default
   for another. Rewrite to name the specific patterns to avoid. [P2]
6. **Unattended or long runs without stop rules.** Add the specific kinds of early stop to avoid,
   and that a still-running background command or subagent means the task is not done. [P2]
7. **No time signal on long work.** The model responds strongly to elapsed time and a time budget.
   The budget is advisory; nothing stops the model at the limit, so do not rely on it as a cap. [P2]
8. **Edits to earlier turns, or a prefilled final assistant turn.** Keep the conversation
   append-only; prefill is rejected (enforced). [P2] [M]
9. **`temperature`, `top_p`, `top_k`, or forced tool use.** Omit sampling parameters and steer with
   the prompt; forced tool use returns an error (enforced). [M] [W]
10. **Pasted material mixed with instructions.** Wrap it in `<pasted_content>` tags. [P2]
11. **Instructions tuned for Opus 5** (re-check or verify your work, "deliver only what was asked",
    caps on subagents, length limits). These come from the Opus 5 guide [P3]; the 5.5 pages [P2] [M] do not restate them; existing
    Opus 5 prompts "should perform well without changes" [P2], and instructions tuned for Opus 5
    "might no longer be needed" [M]. Do not remove or add them on this basis alone: recommend
    an A/B run with and without each one.

## Report

```
## Opus 5.5 Optimization Report
N findings: X stylistic to convert, Y enforced to keep, Z missing additions.

### 1. <delta name> (High | Medium | Low)
- Found in: <location>
- Original text: "<exact quote>"
- Classification: Stylistic | Enforced
- Change: <exact rewrite>  OR  Keep: <what enforces it>
- Source: <URL>

### Deltas checked, not found
### Effort recommendation
### Apply in this order   (state where one fix resolves several findings)
```

High: deltas 2, 3, 8, 9 (requests fail or get refused) and 1. Medium: 4, 5, 6. Low: 7, 10, 11.
