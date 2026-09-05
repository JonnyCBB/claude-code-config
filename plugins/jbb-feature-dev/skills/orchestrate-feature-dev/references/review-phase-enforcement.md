# Review-Phase Enforcement

Three downstream stages have mandatory multi-persona review phases that auto-mode (`--non-interactive`) is known to skip silently when the model judges the artifact "good enough" or wants to save tokens: `/research-problem`, `/map-feature-to-plans`, and `/create-plan-tdd`. The orchestrator enforces these review phases via two independent mechanisms — (1) a verbatim prompt addendum appended to every gated stage invocation, and (2) a post-stage artifact check that scans the canonical output for evidence the review actually ran. If either mechanism flags a skip, the orchestrator escalates and refuses to advance.

## Prompt Addendum

The orchestrator appends this exact string to the stage wrapper prompt of every invocation of `/research-problem`, `/map-feature-to-plans`, and `/create-plan-tdd`:

> Spawn the multi-persona reviewer sub-agents per the skill's review-phase step. Self-review is NEVER a substitute, even in --non-interactive mode. Token cost is NOT a valid skip justification.

The addendum sits below the skill-invocation instruction in the same wrapper prompt so it is read as part of the stage's initial prompt — not as a separate turn — and therefore cannot be elided by the conversation compactor.

Example wrapper prompt fragment (see `references/stage-execution.md § Wrapper Prompt Template` for the full assembly):

```
Invoke the Skill tool with skill "jbb-feature-dev:research-problem" and args
"<requirements-path> --non-interactive", then execute its instructions
faithfully, including spawning every sub-agent the skill mandates.

Spawn the multi-persona reviewer sub-agents per the skill's review-phase
step. Self-review is NEVER a substitute, even in --non-interactive mode.
Token cost is NOT a valid skip justification.
```

Apply identically when invoking `/map-feature-to-plans` and `/create-plan-tdd`. Stages outside this set (e.g., `/operational-context`, `/design-approach`, `/implement-plan-tdd`) do not get the addendum — their review phases are either absent or enforced internally.

## Post-Stage Artifact Check

After each gated stage produces its canonical artifact (research doc, scoping doc, or plan doc), the orchestrator inspects the file for evidence the review-phase ran. The check walks a priority-ordered evidence ladder — the first match passes; only total absence of all patterns triggers escalation.

### Evidence Ladder

**Tier 1 — Frontmatter (highest priority, most reliable).** `/research-problem` writes
a `review_phase_status` frontmatter field in its document template. This is the
authoritative signal for research artifacts:

- `review_phase_status: completed` → review ran (pass)
- `review_phase_status: skipped_simple_complexity` → legitimate skip for Simple
  complexity classification (pass — not a failure; Simple research skips Step 7 by design)
- A `review_phase:` field (legacy/informal variant of the above) describing reviewer
  personas and outcome → review ran (pass)

**Tier 2 — Heading patterns.** Skills that don't use frontmatter may emit review
evidence as document headings:

1. A `## Review Summary (Iteration N/M)` or `## Review Summary (Iteration N of M)`
   heading — emitted by skills that record reviewer iterations (tolerates both `/` and
   `of` separators, and optional suffixes like `— non-interactive`).
2. A `### Review Synthesis` subheading after a `## Autonomous Decisions` heading —
   emitted by `/map-feature-to-plans` and `/create-plan-tdd` in `--non-interactive`
   mode (the only heading pattern these two skills reliably emit).
3. A `## Review Process` or `## Advisory Notes (from Review Phase)` heading — accepted
   for backwards compatibility but not reliably emitted by any current skill version.

**Tier 3 — Milestone log fallback.** If neither frontmatter nor heading evidence is
found, check the stage's milestone log (`$LOG_DIR/<stage-name>.log`) for a
`REVIEW_LOOP` milestone entry containing reviewer names and resolution counts.
A milestone entry like `REVIEW_LOOP reviewers=X,Y,Z must_address=N resolved=true`
is empirical evidence the review ran, even if the artifact's format didn't leave a
heading.

Any single tier match is sufficient. Only when all three tiers find nothing does
the check treat the result as evidence of a skipped review.

```bash
ARTIFACT="$1"
STAGE="$2"
LOG_DIR="$3"

# Tier 1: Frontmatter
if grep -qE '^review_phase_status:\s*(completed|skipped_simple_complexity)' "$ARTIFACT"; then
  pass_review_phase_check
elif grep -qE '^review_phase:' "$ARTIFACT"; then
  pass_review_phase_check

# Tier 2: Heading patterns
elif grep -qE '^## Review Summary \(Iteration [0-9]+(\/| of )[0-9]+' "$ARTIFACT"; then
  pass_review_phase_check
elif awk '/^## Autonomous Decisions/,0' "$ARTIFACT" | grep -qE '^### Review Synthesis|Review Synthesis'; then
  pass_review_phase_check
elif grep -qE '^## Review Process|^## Advisory Notes \(from Review Phase\)' "$ARTIFACT"; then
  pass_review_phase_check

# Tier 3: Milestone log fallback
elif [ -f "$LOG_DIR/${STAGE}.log" ] && grep -qE 'REVIEW_LOOP\s+reviewers=' "$LOG_DIR/${STAGE}.log"; then
  pass_review_phase_check

else
  escalate_review_phase_skipped "$ARTIFACT" "$STAGE"
fi
```

How it works:

- **Tier 1**: The frontmatter check (`^review_phase_status:`) matches at column zero
  in the YAML frontmatter block. `review_phase_status: completed` confirms the review
  ran; `skipped_simple_complexity` confirms a legitimate skip (Simple research has no
  review by design). The legacy `review_phase:` field (without `_status` suffix) is
  accepted as an informal variant — research-problem has historically written review
  evidence in this field.
- **Tier 2**: Heading patterns cover `/map-feature-to-plans` and `/create-plan-tdd`
  (which reliably emit `## Autonomous Decisions` → `### Review Synthesis`) and
  historical format variants. The `## Review Summary` pattern tolerates both `N/M` and
  `N of M` separators (the latter observed from `/create-plan-tdd`).
- **Tier 3**: The milestone log is the orchestrator's own ground truth — a
  `REVIEW_LOOP` entry with named reviewers and resolution status is empirical evidence
  the review ran, independent of the artifact's format. This catches cases where the
  skill ran the review but its document template didn't produce a matching heading or
  frontmatter field.
- `pass_review_phase_check` is a no-op that lets the orchestrator advance.
  `escalate_review_phase_skipped` is invoked only when all three tiers find nothing.

## Failure Handling

When the artifact check finds neither evidence pattern, the orchestrator:

1. Writes a diagnostic doc to `~/.claude/thoughts/shared/escalations/<YYYY-MM-DD>-<run-id>-review-phase-skipped.md` capturing the stage name, artifact path, full artifact contents, and the addendum that was sent. The diagnostic is the artifact a human operator inspects to decide whether to re-run the stage with stricter prompting or accept the skip.
2. Refuses to advance to the next stage. The state file is left with the current stage marked `failed_review_phase_check` so a `--restart` resumes from this stage rather than the next one.
3. Routes a Slack escalation per the orchestrator's main escalation flow (see `SKILL.md` `## Escalation`). The Slack message links to the diagnostic doc and names the stage.

The orchestrator never auto-retries a skipped review phase. A skipped review indicates the model is not respecting the addendum, and a blind retry burns tokens without addressing the cause. Escalating to a human is the correct response.
