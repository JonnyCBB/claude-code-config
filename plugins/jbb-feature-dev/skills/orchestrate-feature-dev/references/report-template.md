# Final Report Template

This reference file defines the 6-section report structure and the
report-generator agent prompt template for generating `final-report.md`.
Read this file when the report generation section of SKILL.md instructs
you to.

## Report Sections

The final report MUST contain all six sections in order. Each section has a
success variant and a failure variant.

### Section 1: Executive Summary

1-3 sentences: what was built, the outcome (success/failure), and the pipeline
configuration (how many plans, which stages ran).

**Success variant**:

```markdown
## 1. Executive Summary

Pipeline completed successfully. [Brief description of what was built based on
the requirements doc title/objective]. Executed [N] plan(s) across [M] wave(s),
with [K] code review findings addressed and [F] filed for later.
```

**Failure variant**:

```markdown
## 1. Executive Summary

Pipeline **failed** at stage **[stage name]** with reason: [escalation reason].
[N] of [M] stages completed before the failure. See Key Decisions and Artifacts
sections for partial results.
```

### Section 2: Stage Timeline

A markdown table showing each pipeline stage, its status, and duration. Derive
duration from log file modification times in `$LOG_DIR/`.

```markdown
## 2. Stage Timeline

| Stage                          | Status   | Duration | Log File                           |
| ------------------------------ | -------- | -------- | ---------------------------------- |
| research-problem               | complete | ~Xm      | research-problem.log               |
| operational-context            | complete | ~Xm      | operational-context.log            |
| design-approach                | skipped  | —        | —                                  |
| requirements-reconciliation    | complete | ~Xm      | reconciliation.log                 |
| validation-contract-generation | complete | ~Xm      | validation-contract-generation.log |
| create-plan-tdd                | complete | ~Xm      | [plan]-create-plan.log             |
| implement-plan-tdd             | complete | ~Xm      | [plan]-implement.log               |
| simplify                       | complete | ~Xm      | simplify.log                       |
| code-review                    | complete | ~Xm      | code-review.log                    |
| code-review-fix                | complete | ~Xm      | code-review-fix.log                |
| validation                     | complete | ~Xm      | —                                  |
| commit                         | complete | ~Xm      | commit.log                         |
| submit-pr                      | complete | ~Xm      | submit-pr.log                      |
```

For stages after a failure point, show status as `not reached`.

**How to derive duration**: For each log file, compute `end_time - start_time`
where `start_time` is the file creation time and `end_time` is the last
modification time. Use `stat` on the log file. If a log file does not exist for
a stage, the stage was skipped.

### Section 3: Key Decisions

Bullets sourced from the `decisions[]` array in the state file.

```markdown
## 3. Key Decisions

{{For each entry in state_file.decisions[]:}}

- **[stage]**: [summary]
```

If `decisions[]` is empty or absent, show:

```markdown
## 3. Key Decisions

No key decisions were recorded during this pipeline run.
```

### Section 4: Code Review Summary

Sourced from `code_review` in the state file. There is no per-plan `review`
object to merge in — plans are planned, implemented and committed; review
happens once, afterwards, over the cumulative diff.

```markdown
## 4. Code Review Summary

- **Total findings**: [code_review.total_findings]
- **Addressed**: [code_review.addressed]
- **Filed as deferred beads**: [code_review.filed]
- **Code-style findings**: [style_findings.addressed] of [style_findings.in_scope] addressed, [style_findings.skipped | length] skipped with reasons
- **Files reviewed**: [code_review.files] ([code_review.scope])
```

One pass, so one set of counts — there is no per-cycle table because there are no
cycles. **State the filed count even when it is zero**, and never fold it into
"resolved": a reader judging whether one review pass was enough needs to see what
shipped unfixed, and a report showing only what was fixed reads identically
whether two findings were filed or silently dropped. Omit this section entirely
when `code_review` is absent.

If no code review data exists, show:

```markdown
- Code review data not recorded (pipeline may have failed before review).
```

### Section 5: Verification Outcome

Sourced from `verification_outcome` in the state file.

```markdown
## 5. Verification Outcome

| Metric           | Count     |
| ---------------- | --------- |
| Total assertions | [total]   |
| Passed           | [passed]  |
| Failed           | [failed]  |
| Blocked          | [blocked] |

**Result**: [PASS if failed==0 and blocked==0, else FAIL]
```

If `verification_outcome` is absent (pipeline failed before verification):

```markdown
## 5. Verification Outcome

Verification was not reached — pipeline failed at an earlier stage.
```

### Section 6: Artifacts

List all output files in the project directory.

```markdown
## 6. Artifacts

| File       | Description                                      |
| ---------- | ------------------------------------------------ |
| [filename] | [inferred description based on filename pattern] |
```

**Filename-to-description mapping**:

- `*-research.md` → Research findings
- `*-operational-context.md` → Operational context analysis
- `*-design-approach.md` → Design approach exploration
- `*-scoping.md` → Feature scoping and plan decomposition
- `*-verification-contract.md` → Validation contract
- `*-plan-*.md` → Implementation plan
- `*code-review*.md` → Code review findings (one per run — step 9 runs once)
- `*-reconciliation-summary.md` → Requirements reconciliation summary
- `validation-state.json` → Validator assertion results
- `final-report.md` → This report
- `input/` → Archived input files

## Report Generator Prompt Template (Success Path)

The orchestrator uses this prompt (as a direct background Agent call) for
the success-path report generation:

```
You are a pipeline report generator. Your task is to produce a concise,
human-readable final report summarizing the orchestrator pipeline run.

## Instructions

1. Read the state file at {{STATE_FILE}} using the Read tool.
2. Read the log directory listing at {{LOG_DIR}} to derive stage durations
   from file modification times.
3. Read the project directory listing at {{RUNS_BASE}} for the artifacts section.
4. Generate a report with all 6 sections defined in the template below.
5. Write the report to {{REPORT_PATH}} using the Write tool.

## Report Template

Use the section templates from the report-template.md reference file.
Populate each section with actual data from the state file and log files.

## Rules

- Keep the executive summary to 1-3 sentences.
- Use "~Xm" format for durations (round to nearest minute).
- For stages without log files, mark as "skipped" in the timeline.
- For missing state file fields, use the fallback text specified in the template.
- Do not editorialize or add recommendations — this is a factual summary.
```
