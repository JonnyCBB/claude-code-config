# jbb-feature-dev

Complete feature development workflow for Claude Code — from requirements gathering through implementation, review, and delivery.

## Installation

```bash
claude plugins add github.com/JonnyCBB/claude-code-config/plugins/jbb-feature-dev
```

**This plugin is self-sufficient, and must stay that way.** Its skills and references may point at
this plugin's own files, but not at a sibling plugin's, because a user installs one without the
other. Where a sibling genuinely helps, name it and say what to do without it -
`skills/submit-pr/references/pr-prose-rules.md` is the worked example.

**If a plugin ever bundles an MCP server, know this:** Claude Code deduplicates MCP servers by URL
and registers only whichever plugin loaded first. On a machine where two plugins declare the same
server, the one that loads second has its `mcp__plugin_*` names resolve to nothing, and its agents
fall back to `Read`, `Grep`, `Glob` and `Bash`. Naming the sibling plugin's copy
(`mcp__plugin_<other>_*`) as an optional fallback in the agent's tool list keeps it working in
either load order. Do not add the same server with `claude mcp add`: a user-scope server outranks
both plugin copies and every plugin-prefixed name stops matching.

## Recommended process

Use `/jbb-feature-dev:implement-change` for a specified feature, fix, or approved task.
It works in the current session and checkout; no research report or formal plan is required.

1. Establish the objective, scope, checkout, fixed base, and permissions; implement minimally with runtime red-green TDD.
2. Run three independent passes in order: Claude's built-in `/simplify`, `/jbb-feature-dev:code-review`, then `/jbb-feature-dev:verify-implementation`.
3. Apply confirmed findings and keep direct local evidence. Submit only when authorized, then follow latest-head CI and explicit clean review.

```text
/jbb-feature-dev:implement-change Fix the stated bug; keep this as a local patch.
/jbb-feature-dev:implement-change path/to/task-criteria.md
```

A local-patch request does not authorize commits, pushes, or PR submission. The workflow never merges.
Progress and evidence stay in the task record so work can resume after a blocker.
See [implement-change](skills/implement-change/SKILL.md) for the procedure and
[submit-pr's monitoring policy](skills/submit-pr/references/build-monitoring.md) for post-submission completion.
`/simplify` is a Claude built-in, not a package shipped by this plugin.

The individual skills below remain available when requirements need clarification, research or planning is useful,
or only one operation is needed. They are not mandatory preparation stages for `/implement-change`.
Read each skill's arguments and interaction rules; there is no plugin-wide non-interactive flag.

---

## Skill Reference

### /implement-change

The recommended entry point for implementation. Accepts a task description or objective/criteria file.
Returns a verified local patch, or an authorized PR with current CI, review evidence, and explicit verification limits.
Follow the compact process above; [SKILL.md](skills/implement-change/SKILL.md) owns its guardrails.

### /elicit-requirements

Gather requirements through structured questioning before automated research begins. Spawns context-gathering agents when artifacts are provided. Only asks questions that automated tools cannot answer (business motivation, acceptance criteria, scope tradeoffs).

**Key features**:

- Context Sprint — detects artifacts in user input and spawns research agents before questioning
- Wave-based depth progression — Foundational → Nuances → Deep/Domain with synthesis checkpoints
- Premise challenge — validates the problem is worth solving before diving into details
- Scope mode selection — MVP, Complete, or Ambitious
- Relentless tree-walking — explores every branch of the design tree, resolving dependencies one-by-one
- Context-sharing protocol — presents running mental model to build shared understanding
- Mutual understanding confirmation — only the user's explicit confirmation ends the session

**Output**: `~/.claude/thoughts/shared/requirements/YYYY-MM-DD-description-requirements.md`

**Examples**:

```bash
/elicit-requirements                                                    # Start interactive interview
/elicit-requirements ~/.claude/thoughts/shared/tickets/ENG-1234.md      # Pre-load a ticket
/elicit-requirements --non-interactive ~/.claude/thoughts/shared/tickets/ENG-1234.md  # Auto-generate requirements
```

### /research-problem

Conduct comprehensive research across the codebase and beyond by spawning parallel sub-agents and synthesizing their findings into a research document.

**Key features**:

- Decomposes research into questions with dependency analysis
- Spawns parallel sub-agents (codebase-explorer, thoughts-explorer, web-search-researcher, domain experts)
- Batch execution with context passing between batches
- Iterative completeness review (max 2 iterations)
- Multi-persona review phase for Medium/Complex research (Gap Analyst, Devil's Advocate, Source Critic, Coherence Reviewer, Scope Guardian)
- Documentarian principle — documents what IS, not what SHOULD BE

**Output**: `~/.claude/thoughts/shared/research/YYYY-MM-DD-description.md`

**Examples**:

```bash
/research-problem How does the search ranking pipeline work?
/research-problem ~/.claude/thoughts/shared/requirements/2026-03-28-new-feature-requirements.md
/research-problem --non-interactive How does authentication work in this service?
```

### /map-feature-to-plans

Analyze a research document for a single feature and determine whether it should be split into multiple implementation plans.

**Key features**:

- Single plan by default; each extra plan must cite a justification (context fit, risk / landing order, checkpoint, separate delivery), never size alone
- Produces plan outlines with file lists, dependency graphs, and execution waves
- PR strategy decided separately from plan count (one PR per repo unless plans must merge separately)
- Redirects to `/break-down-initiative` if input is multi-feature

**Output**: `~/.claude/thoughts/shared/scoping/YYYY-MM-DD-description.md`

**Examples**:

```bash
/map-feature-to-plans ~/.claude/thoughts/shared/research/2026-03-28-search-feature.md
/map-feature-to-plans --non-interactive ~/.claude/thoughts/shared/research/2026-03-28-search-feature.md
```

### /design-approach

Multi-architect design exploration before planning. Spawns competing architect agents with different perspectives to generate genuinely different approaches, presents them in a comparison document, then facilitates interactive discussion where the user explores tradeoffs and makes key design decisions.

**Key features**:

- Tension and settlement analysis — scans research docs for unresolved architectural tensions vs already-settled decisions
- Variable architect count (2-4 agents) based on the number of open tensions detected
- Competing perspectives — each architect embodies a coherent philosophy that resolves tensions differently
- Settlement compliance — validates architect outputs against settled decisions, stripping violations
- Convergence detection — if all architects agree, skips comparison and goes straight to decision document
- Structured decision tree — presents divergent decisions one by one with tradeoffs for user selection
- Requirements compliance — flags when a chosen option conflicts with a stated requirement
- Fallback perspectives (Minimal Changes / Clean Architecture / Pragmatic Balance) when tensions are unclear

**Output**: `~/.claude/thoughts/shared/feature_designs/YYYY-MM-DD-description.md`

**Examples**:

```bash
/design-approach ~/.claude/thoughts/shared/research/2026-03-28-search-feature.md
/design-approach ~/.claude/thoughts/shared/research/2026-03-28-search-feature.md --requirements=~/.claude/thoughts/shared/requirements/2026-03-28-requirements.md
/design-approach --non-interactive ~/.claude/thoughts/shared/research/2026-03-28-search-feature.md
```

### /code-review

Single-pass review of a branch, working tree or PR against its objective: correctness, scope, tests, reuse, performance, minimal code, readability, naming and comments.

**Key features**:

- Two fresh read-only `general-purpose` assessors run concurrently on one snapshot: a general assessor (`checklist.md` plus `java.md`, `python.md` or `typescript.md`) and a bug assessor (`bug-review`)
- Fix mode on your own work: applies validated findings, runs the repo's tests and lint, and commits only when authorized
- Colleague mode on someone else's PR: read-only, gives an Approve / Request changes verdict and drafts comments; posts nothing
- Security and repo conventions are left to a dedicated review bot or reviewer

**Examples**:

```bash
/code-review                          # Review the current branch (fix mode)
/code-review 123                      # Review PR #123 (colleague mode if you are not the author)
```

### /polish-code

Final quality gate before `/submit-pr` with test enhancement, code simplification, data annotation review, coding guidelines, and formatting. Interactive by default; pass `--non-interactive` for autonomous mode that logs decisions instead of prompting.

**Key features**:

- 8-step pipeline: pre-flight → scope extraction → test enhancement → source simplification → test simplification → data annotation → coding guidelines → formatting → verification
- Checkpoint-and-revert strategy: each step creates a checkpoint commit; reverts on test failure
- Change-level scope enforcement: only analyzes code within the diff
- Decision framework (non-interactive): CRITICAL/HIGH always implement, MEDIUM/LOW use agent judgment
- Retry limit: 2 attempts when simplification breaks tests, then revert and continue

**Output**: Multiple atomic commits (tests, simplification, annotations, guidelines, formatting)

**Examples**:

```bash
/polish-code                                       # Tidy changes on current branch (interactive)
/polish-code --non-interactive                     # Autonomous mode — no prompts
/polish-code --branch master                       # Compare against master
/polish-code --staged                              # Only staged changes
/polish-code src/example/                          # Specific directory
/polish-code --non-interactive --branch master     # Autonomous mode against master
```

### /verify-implementation

Generate reproducible local evidence against a task objective, acceptance criteria, or implementation plan. No formal plan or commit is required.

**Key features**:

- Parses plan for testable assertions (command-based, behavioral, negative)
- Objective alignment check: maps every plan item to implementation evidence (PASS/FAIL/GAP)
- **Live service testing** (Backend API domain): automatically starts the service, generates a test scenario matrix (happy path, full input, field omission, feature toggles, error inputs, graceful degradation, before/after), executes all scenarios via gRPC/REST, and records PASS/FAIL per scenario with full request/response transcripts
- Before/after comparisons for behavioral changes
- Reuses existing local commands and records exact scenario inputs and outputs
- Verdicts: PASS (all required criteria verified), FAIL (incorrect behavior), PARTIAL (blocked or missing evidence)
- Optional requirements alignment check when requirements doc is provided

**Output**: `~/.claude/thoughts/shared/verification/YYYY-MM-DD-description.md`

**Examples**:

```bash
/verify-implementation
/verify-implementation ~/.claude/thoughts/shared/plans/2026-03-28-search-feature.md
/verify-implementation <plan-path> --requirements <requirements-path>
```

### /commit

Create structured git commits with co-authorship attribution.

**Key features**:

- Reviews conversation history and git diff to understand what changed
- Groups related changes into logical commits
- Drafts descriptive commit messages in imperative mood
- Adds AI co-authorship attribution

**Output**: Git commits

**Examples**:

```bash
/commit                    # Interactive — presents plan and asks for confirmation
/commit --non-interactive  # Auto-commit without confirmation
```

### /submit-pr

Full PR lifecycle management: create or update a GitHub PR with Jira integration, build monitoring, and Slack notifications.

**Key features**:

- 3-phase lifecycle (Pre-Submit, Submit, Post-Submit)
- Jira fuzzy transition matching with 0.6 confidence floor
- Latest-head CI and an explicit clean review via `/loop`
- Focused authorized corrections and refreshed verification evidence after each push
- Slack notifications only when authorized and requested
- Never merges or enables automatic merging
- Architecture diagram generation for complex PRs
- Discovers and follows repo-specific PR templates
- Embeds verification results from `/verify-implementation`

**Output**: GitHub PR (created or updated)

**Examples**:

```bash
/submit-pr                                    # Default: compare against master
/submit-pr develop                            # Compare against develop branch
/submit-pr --draft --no-jira                  # Draft PR, skip Jira
/submit-pr --monitor --notify #my-channel     # Monitor build, notify on completion
/submit-pr --monitor --non-interactive        # Authorized push and latest-head monitoring; never merges
```

### /break-down-initiative

Decompose a PRD, RFC, epic, or high-level initiative into independently-executable feature outlines using vertical slices.

**Key features**:

- Validates input level: redirects to `/map-feature-to-plans` if input is already a single-feature research doc
- Explores codebase to understand architecture and domain boundaries
- Slices by user value (vertical), not by code module (horizontal)
- Each feature classified as HITL (needs human decision) or AFK (fully automatable)
- Dependency mapping between features
- Each output feature enters its own full pipeline run

**Output**: `~/.claude/thoughts/shared/decomposition/YYYY-MM-DD-description.md`

**Examples**:

```bash
/break-down-initiative
/break-down-initiative ~/.claude/thoughts/shared/prd/search-redesign.md
/break-down-initiative --non-interactive ~/.claude/thoughts/shared/prd/search-redesign.md
```

---

### /sweep-followups

Re-reads the current session's transcript for follow-ups that were mentioned and never
filed, and files the keepers labelled `agent-proposed` at status `deferred`. The net underneath
the `Stop` hook below: the hook catches a deferral at the moment it happens, the sweep
catches whole turns, including work deferred before the hook existed.

**Key features**:

- Scans both the assistant's reply and the opening human prompt — a deferral is as often
  the user's ("that's a real bug but out of scope for this change"), and the assistant
  then summarises it in language that carries no cue at all
- Judgement stays with the model; the scanner only surfaces candidates
- Watermark makes a repeat sweep a no-op. `SKILL.md` states why in full; that is the one
  place the reason lives, so it cannot drift out of step with a copy here
- Two independent suppression mechanisms, verified separately: a cursor past already-swept
  turns, and a content hash per candidate that ignores which turn it came from
- Records dismissals as well as filings, so a candidate judged worthless is not re-offered
  on every future sweep
- Watermark state lives in `$XDG_STATE_HOME/followup-capture/` (default
  `~/.local/state/...`), outside `~/.claude` and `~/beads-hq` because both have git remotes

**Output**: Beads issues in the shared queue, all `deferred` and out of `bd ready` until
triaged.

**Examples**:

```bash
/sweep-followups
/sweep-followups --dry-run
```

---

## Hooks (1)

This is the first plugin in this marketplace to ship a hook, so
the convention it establishes is written down here rather than left to be re-derived.

| Event  | Command                                                          | Purpose                                                       |
| ------ | ---------------------------------------------------------------- | ------------------------------------------------------------- |
| `Stop` | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/followup_capture.py" hook` | Asks the model to file follow-ups it deferred but never filed |

### The convention

- **Hooks live at `<plugin-root>/hooks/hooks.json`.** The file is discovered by path; no
  `hooks` key in `.claude-plugin/plugin.json` is needed or wanted. Verified against
  enabled plugins from other marketplaces that already do this, such as `crit` and
  `openai-codex`, none of which declares the key.
- **Reference every script through `${CLAUDE_PLUGIN_ROOT}`.** Never glob
  `~/.claude/plugins/cache/*/<plugin>/*/`: that cache holds many versions plus at least
  one non-version directory (`0.20.0.mislabelled-backup`), so a glob can resolve to a
  real file from a version other than the one running, and fail silently.
- **Set a `timeout`.** Ours is 10s against a p95 two orders of magnitude below it (see
  Cost), so the timeout only ever fires on something pathological.
- **Never write hooks to `~/.claude/hooks/`.** A setup script or a `SessionStart` hook living
  there can move the whole of `~/.claude` aside and replace it, or destructively remove plugin
  cache directories that are not symlinks. Both have happened. A hook shipped inside the plugin
  survives them; one written into the user's hooks directory does not.

### Plugin hooks are additive, not shadowing

A plugin `Stop` hook does **not** replace `Stop` hooks registered in `settings.json`.
This matters because `~/.claude/settings.json` runs `agent-deck hook-handler` on `Stop`,
which is how the conductor learns that dispatched work finished. Verified live rather
than assumed: with this hook loaded via `--plugin-dir` and a settings-level `Stop` hook
wrapping `agent-deck hook-handler`, the settings-level hook ran on every stop and exited
0 — once on a turn with nothing to file, twice on a turn where this hook asked for a
filing and the model then stopped again.

### Cost

Measured over 63 real transcript invocations, largest input 33.4 MB: median **57-59 ms**,
p95 **63-74 ms**, max **106-112 ms**. Three runs of the snippet below gave medians of 58.5,
58.1 and 56.8 ms, maxima of 110.8, 106.1 and 112.4, and p95 of 74.1, 63.4 and 63.0 — so
read these as ranges rather than figures, treat that first p95 as the outlier it looks like,
and re-measure on the machine you care about. Of the median,
31 ms is bare `python3` interpreter startup, so the
hook's own work is ~28 ms. It reads only the last 512 KB of the transcript, which is why
a 33 MB file costs the same as a small one. It exits 0 and prints nothing when there is
no Beads queue, no transcript, or nothing to file, and it swallows every unexpected
exception rather than surfacing a hook failure at turn end.

The fire rate and per-pattern hit counts regenerate from the scanner itself, and that
command is their canonical source — nothing else in this repo restates them:

```bash
python3 plugins/jbb-feature-dev/hooks/followup_capture.py report ~/.claude/projects/*/*.jsonl
```

The latency figures above are a point-in-time measurement and `report` does not emit them,
so they are reproduced by timing the hook entry point directly:

```bash
python3 - <<'EOF'
import json, os, statistics, subprocess, sys, time, glob, random
S = "plugins/jbb-feature-dev/hooks/followup_capture.py"
random.seed(7)
files = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
if not files:
    sys.exit("no transcripts found - nothing to measure, so this is not a 0ms result")
sample = (sorted(files, key=os.path.getsize, reverse=True)[:3]
          + random.sample(files, min(60, len(files))))   # min(): a fresh machine has few
def run(p):
    t = time.perf_counter()
    subprocess.run([sys.executable, S, "hook"], text=True, capture_output=True,
                   input=json.dumps({"transcript_path": p, "session_id": "COSTPROBE"}))
    return (time.perf_counter() - t) * 1000
run(sample[0])                                   # warm the .pyc cache first
ts = sorted(run(p) for p in sample)
print(f"n={len(ts)} median={statistics.median(ts):.1f}ms "
      f"p95={ts[int(0.95*len(ts))]:.1f}ms max={ts[-1]:.1f}ms")
EOF
```

Subtract bare interpreter startup before reading anything into the result —
`python3 -c pass` alone is ~31 ms here, which is most of the median.

The unit suite and the description-triggering eval set are deliberately not carried here —
this marketplace ships markdown and shell, not a test tree. They live in the maintainer's own
working repository, so this figure is not reproducible from a plugin install.

## Agents (14)

Includes 4 research/discovery agents (codebase-explorer, thoughts-explorer, web-search-researcher, visual-aid-recommender), 8 code review agents (bug-catcher, security-reviewer, repo-rules-reviewer, general-code-reviewer, ml-pipeline-reviewer, quality-checker, review-calibrator, review-deduplicator; `/code-review` itself no longer dispatches them), and 2 mode-aware language experts (python-expert, typescript-expert).

## Agent-Loaded Skills

Knowledge loaded by agents rather than invoked directly: code style patterns (`code-style-common`, `python-code-style`, `typescript-code-style`), review modes (`code-review-modes`), and shared references and guidelines (`shared-references`, `diagram-standards`).

## Prerequisites

- The `gh` CLI, authenticated against the GitHub host your repositories live on, for `/submit-pr`, `/crit-pr-review` and `/rebase-stack`.
- The `bd` (beads) CLI for `/sweep-followups` and the `Stop` hook. Without a Beads queue the hook exits silently.

### Optional

- Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `~/.claude/settings.json` under `env` for agent team features
