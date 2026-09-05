# Model Selection Guide

Advisory guidance for choosing sub-agent models. This guide respects the user's default
model selection — it suggests alternatives only when there's a clear cost/quality benefit.

## Principle

Use the user's default model unless you have a specific reason to downgrade. When a task
is mechanical and fully specified, a lighter model saves cost without quality loss. When
a task requires judgment, creativity, or complex reasoning, use the strongest available.

## Task-to-Model Suggestions

| Task Type | Suggested Model | Rationale |
|-----------|----------------|-----------|
| Orchestration, architecture, complex reasoning | User's default | High stakes, needs best judgment |
| Review, synthesis, evaluation | Sonnet | Evaluative work with good quality/cost ratio |
| Implementation with detailed plan context | Sonnet | Mechanical execution guided by plan; quality preserved |
| Formatting, linting, simple checks | Sonnet | Fast, reliable for deterministic tasks |

## When to Override the Default

Only set the `model:` parameter on Agent tool calls when ALL of these are true:

1. The task is low-risk (failure is cheap to detect and fix)
2. The task has detailed instructions or plan context (less reasoning needed)
3. The suggested model is different from the user's default
4. You are optimizing for cost or speed, not quality

When in doubt, use the user's default model. The cost of a wrong answer from a weaker
model exceeds the savings.

## What This Guide Is NOT

- Not a mandate — skills should not enforce model choices
- Not a replacement for judgment — context matters more than rules
- Not applicable to user-facing responses — only to sub-agent spawning
