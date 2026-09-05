# Field Notes

Dated, empirically-verified facts about this harness and the jbb-feature-dev
stage skills. These are not style preferences — each one was learned from a
real pipeline failure or a deliberate probe. Trust them over intuition; when
you have newer contradicting evidence, note it in the run journal and act on
the newer evidence.

## Harness facts

Transport, waiting discipline, and recovery are documented in full in
`../../orchestrate-feature-dev/references/stage-execution.md` — it is
authoritative for why workers are background Agent-tool subagents and not
`claude -p` (tracked `claude -p` is killed at ~30 minutes; Agent workers
verified to survive 55+ minutes with Skill-tool and nested-agent support,
plus the detached escape hatch in its `§ Appendix`), for wake-event
unreliability and the SendMessage-nudge recovery ladder (`§ Waiting
Discipline`), for externally-killable watchdog timers, and for permission
modes (writing stages need `dontAsk` — `acceptEdits` still blocks
`~/.claude/` writes; read-only stages run `auto`). Two operational lines
from that body of evidence belong in your own behavior:

- Include verbatim in every worker prompt: "Prefer actively checking any
  subagents or background tasks you spawn over idle-waiting; wake events are
  unreliable."
- **Pin a tier on any worker that spawns children** — unpinned children
  inherit the parent worker's model (verified 2026-07-04), so an unpinned
  fable worker quietly bills its whole subtree at fable rates. There is no
  default worker tier: choose per worker and record why
  (`delegation.md § Model and effort policy`).
- **Never ground the run's worktree under `/tmp` or `/private/tmp`**
  (verified 2026-07-10, complete-hexagonal-migration run): macOS cleaning
  `/private/tmp` coinciding with a session restart destroyed an entire
  implementer wave's uncommitted work twice in one long-running run before
  the worktree was relocated to `~/.claude/worktrees/<run-id>`, which
  survived the rest of a 12+ hour run through many more restarts. Shorter,
  single-restart runs may not hit this — the risk scales with wall-clock
  duration and restart count, exactly the profile of an autonomous
  multi-gate Fable pipeline. Pair this with the next fact: even a durable
  worktree location doesn't help if a worker batches multiple waves of work
  before its first commit.
- **Every implementer worker must commit immediately once its gates go
  green, never batch waves before committing** (same 2026-07-10 run): a
  committed change on the branch survives worktree loss; uncommitted
  changes do not, regardless of location. Include this as an explicit,
  unconditional instruction in every implementation-stage wrapper prompt —
  do not rely on the stage skill's own end-of-run commit step alone, since a
  session restart can kill the worker before it gets there.

## Stage-skill argument quirks

These skills predate this orchestrator and parse arguments idiosyncratically.
Getting them wrong produces empty output or literal-flag-as-search-term bugs,
not error messages.

| Skill                             | Correct invocation                                                                                | Trap                                                                                                                                                                     |
| --------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/research-problem`               | `<input-path> --non-interactive` (positional)                                                     | `--requirements <path>` is treated as a literal search term → empty research                                                                                             |
| `/operational-context`            | `<component> [<component>...] --non-interactive` (positional names)                               | Takes no `--requirements`; extract component names from the research doc's own recommendation text                                                                       |
| `/design-approach`                | `<research-doc-path> --requirements=<path> --non-interactive`                                     | Requires the **equals** form; space form is not parsed. Pass YOUR canonical research-doc path, not the path the research doc suggests                                    |
| `/validation-contract-generation` | `--requirements <path> --non-interactive`; amend: `--amend --contract <path> --review-doc <path>` | —                                                                                                                                                                        |
| `/map-feature-to-plans`           | `<research-doc-path> --non-interactive` (positional; only file it reads)                          | No `--requirements` flag                                                                                                                                                 |
| `/create-plan-tdd`                | `<plan-input-path> --contract <path> --non-interactive`                                           | Single-feature planner: no `--plan-id`, no multi-plan concept. To scope one plan out of a multi-plan wave, extract that plan's outline into a standalone input doc first |
| `/jbb-feature-dev:code-review`     | `<branch-name> --non-interactive` + Output Location Override                                      | First arg is a bare PR number or BRANCH NAME - never a path, never a URL; it checks that arg out. Without `--non-interactive` an unresolvable scope stalls the run on an unseen prompt |
| `/implement-plan-tdd`             | `<plan-path> --non-interactive --skip-final-review`                                               | `--skip-final-review` because its Steps 6-7 are quality/guideline passes that G5's single `/jbb-feature-dev:code-review` covers once, and cleanup by G5's `/simplify`     |
| `/submit-pr`                      | `--verification <path> --requirements <path> [--scoping-doc <path>] --non-interactive`            | Auto-detects the Jira key from the branch name; do NOT forward `--ticket`                                                                                                |

## Output locations

- Skills default to writing under `~/.claude/thoughts/shared/<topic>/`.
  Append the Output Location Override (see
  `../../orchestrate-feature-dev/references/stage-execution.md`) to every
  worker prompt so artifacts land at the run's canonical paths.
- **Skills sometimes ignore the override.** When the canonical artifact is
  missing after a completed stage, search the default locations (research →
  `~/.claude/thoughts/shared/research/`, scoping → `.../scoping/`, plans →
  `.../plans/` or `.../research_plans/`, contract → `.../contracts/`, review
  → `.../reviews/`) for files modified in the last 60 minutes and **always
  pick the newest** (`ls -t`). Skills that rewrite the same base name append
  `_2`, `_3` counter suffixes — name-sorted `find` picks the stale one, which
  caused a re-review of already-fixed findings. Review documents are exempt:
  the review writes to an explicit path under the run directory, so they are
  addressed rather than discovered.

## Execution constraints

- **Never implement plans in parallel in the same worktree** — not even with
  disjoint file sets. Concurrent implementations run concurrent test suites,
  which caused CPU saturation and cross-plan test noise (2026-06-30).
  Parallel implementation is defensible only with fully isolated worktrees
  AND a reason it beats sequential; record the justification if you try it.
- **Planning parallelizes safely** (read-only, API-bound). So do research /
  ops-context / design-approach and independent review agents.
- **Research legitimately runs for hours.** Duration alone is NEVER a stall
  signal for any stage — follow the milestone log. Size fallback timers at
  ~2× the stage's historical duration with a 30-minute floor; research gets
  4h minimum. Historical durations (2026-06-30 run): plan ~49 min,
  implementation ~75 min per plan.

## Verification facts

- **Unit tests are not live evidence.** Timing, state, and event-ordering
  bugs have repeatedly passed unit tests while still failing live. For any
  assertion that originally failed during a live validator pass, a fix is
  confirmed only by re-running the exact Setup/Stimulus/Assertion live
  (Verify-Fix Recheck prompt in
  `../../orchestrate-feature-dev/references/agent-prompts.md`).
- **Merge recheck results with the script, not by hand**:
  `../../orchestrate-feature-dev/scripts/aggregate_verify.py merge <state>
<state> <recheck>`. Hand-rolled `jq`/`python3` merges have corrupted
  validation state.
- **"Blocked" claims need root-cause proof.** A missing credential or
  unreachable host can be a red herring when the code under test was never
  wired to a real dependency in the first place. The validator prompt
  encodes this — don't soften it.

## Review-phase enforcement

Non-interactive skills have empirically skipped their mandatory multi-persona
review phases when the model judged the artifact "good enough" — prompt-level
enforcement alone fails. Three stages are gated (`/research-problem`,
`/map-feature-to-plans`, `/create-plan-tdd`): append the verbatim addendum
AND run the post-stage artifact evidence check, both defined in
`../../orchestrate-feature-dev/references/review-phase-enforcement.md`.
A detected skip is a hard escalation, never a retry — a skipped review means
the model is not respecting the contract, and a blind retry burns tokens
without addressing the cause.
