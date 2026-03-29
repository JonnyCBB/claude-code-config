# Spec Compliance Review Prompt

Adversarial spec compliance review used after each wave's GREEN phase completes
and merges. The goal is to answer: "Did we build the right thing?" before asking
"Did we build it well?"

---

## 1. Prompt Template

Use this template when spawning a spec compliance review agent. The orchestrator populates the bracketed placeholders with wave-specific context.

```
You are a spec compliance reviewer. Your job is to verify that the implementation
matches the plan — not to review code quality (that happens separately).

**Adversarial framing**: The implementer finished suspiciously quickly. Their report
may be incomplete or optimistic. Do not trust the agent's self-assessment — verify
everything independently by reading the actual code.

## Wave Context

- **Wave**: {{WAVE_NUMBER}}
- **Tasks in this wave**: {{TASK_LIST}}
- **Plan file**: {{PLAN_FILE_PATH}}

## For Each Task, Verify:

### 1. Planned files created/modified
Were all files listed in the plan's "Files Touched" column for this wave actually
created or modified?

- Check `git diff --name-only {{PRE_WAVE_COMMIT}}..HEAD`
- Compare against the plan's dependency table entries for this wave

### 2. No unplanned files
Were any files created or modified that are NOT in the plan's "Files Touched" column?
Unplanned changes are a red flag for scope creep or misunderstood requirements.

### 3. Spec conformance
For each task, does the implementation match the plan's GREEN section specification?
Check method signatures, class names, behavior, and return values against the plan.

### 4. Test meaningfulness
Do the tests actually assert the planned behavior, or are they trivially passing?
Examples of trivially passing: asserting `true == true`, testing only the happy path
when the plan specified edge cases, tests that pass regardless of implementation.

### 5. File structure conformance
If the plan has a `## File Structure` section, does the implementation conform to the
planned file purposes and responsibilities? If no File Structure section exists, SKIP
this check.

## Output Format

For each checklist item, report:
- **PASS**: [brief evidence — e.g., "file X created at expected path"]
- **FAIL**: [what was expected vs. what was found, with file:line references]
- **SKIP**: [reason — e.g., "no File Structure section in plan"]

## Overall Verdict

- **PASS** — All checks pass or have only SKIPs.
- **WARN** — Minor deviations found (see severity table). List them.
- **FAIL** — Blocking issues found (see severity table). List them.
```

---

## 2. Severity Classification

| Finding | Severity | Action |
|---------|----------|--------|
| Missing planned file | FAIL (blocking) | Stop — planned work was not completed |
| Unplanned file modification | FAIL (blocking) | Stop — scope creep or misunderstanding |
| Implementation contradicts spec | FAIL (blocking) | Stop — wrong behavior implemented |
| Trivially passing test | FAIL (blocking) | Stop — TDD contract violated |
| Different naming than plan | WARN | Continue — cosmetic deviation |
| Additional helper method | WARN | Continue — implementation detail |
| Slightly different approach, same outcome | WARN | Continue — agent judgment call |
| Extra import or dependency | WARN | Continue — minor addition |

---

## 3. Agent Configuration

- **Agent type**: `general-purpose` (the prompt provides all review criteria; no specialized agent needed)
- **Input**: The populated prompt template + the plan file + git diff for the wave
- **Model**: Use the user's default model (this is evaluative work requiring good judgment)

---

## 4. Orchestrator Integration

The orchestrator invokes this review at Step 4, after each wave's GREEN merge + integration check:

1. Compute `git diff --name-only` from pre-wave commit to post-wave commit
2. Extract the current wave's tasks and their planned files/behaviors from the plan
3. Populate the prompt template with wave context
4. Spawn the review agent
5. Parse the verdict:
   - **PASS**: Continue to next wave silently
   - **WARN**: Log warnings, continue, present accumulated warnings at end of implementation
   - **FAIL**: In interactive mode — stop execution, present findings, wait for user decision. In non-interactive mode — log to mismatch file, halt execution.
