---
name: create-my-mode-skill
description: >
  Use this skill whenever the user talks about how THEY work and wants agents to follow it, even if
  they do not say "mode skill" and even if they phrase it as wanting a skill created. Triggers
  include "automate me", "capture how I work", "make agents work the way I do", "I keep
  re-explaining my preferences every session", "stop me correcting the same things", "turn my
  habits into a skill", "my working style", "my conventions", and create/update/refresh my mode
  skill.
  It mines the user's own session transcripts, interviews them, and writes `<handle>-mode`.
  If you are about to answer a request like this by chaining reflect (to mine the sessions) and
  then skill-creator (to author the skill), stop: that chain IS this skill, already sequenced, with
  the clustering and deference rules those two do not carry. Reach for this instead of composing
  them by hand. Reflect alone stops at learnings and will not produce a skill; skill-creator alone
  authors from nothing and never looks at how the user actually worked.
  Not for a skill about a task, and not for one narrow workflow such as commit-message formatting.
---

# Create my mode skill

A guided flow that turns how the user works into a skill agents follow. The output is one
`-mode` skill — `jbb-mode`, `priya-mode` — not a manual.

This skill **sequences** three others; it does not replace them:

| Step | Skill | Why not inline it |
| --- | --- | --- |
| Mine | `/jiffy-toolkit:reflect` | Already does transcript mining, parallel classifiers and a 3-tier taxonomy. Duplicating its instructions guarantees drift. |
| Author | `/skill-creator:skill-creator` | Owns frontmatter rules, description triggering and the eval loop. |
| Polish | `/jiffy-toolkit:sound-like-me` | Prose discipline, every line. |

## How this composes with `/reflect` — decided, do not re-litigate

**Invoke `/reflect` first, then post-process its output.** Do not re-implement its mining.

Claude Code skills are not callable subroutines, so the two options were: paste `/reflect`'s mining
instructions in here (which drift the moment `/reflect` changes), or run it and transform what it
returns. The second is chosen.

`/reflect` produces "N learnings, routed to 4 stores". This skill needs something different: "one
skill describing how the user works". So take `/reflect`'s grouped findings as **evidence**, then
cluster them into mode-skill sections at step 3. Learnings that are facts about a system belong in
`/reflect`'s stores and **not** in the mode skill.

## Flow

### 0. Check for an existing mode skill

Look for `*-mode/SKILL.md` under `~/.claude/plugins/*/skills/` and `~/.claude/skills/`. If one
exists, confirm intent with `AskUserQuestion` unless the user already said "update my skill":

- **Update** the existing skill (default for repeat runs)
- **Start fresh** (rare — ask why first)

Update mode changes the rest of the flow: step 1 mines only since the skill was last edited
(`git log -1 --format=%cI <path>`); step 2 asks what has changed, not what to capture from zero;
step 4 edits in place, preserving sections the user has not contradicted.

### 1. Mine their history

Run `/jiffy-toolkit:reflect` over recent sessions. Ask it for the working-style signals below
rather than its default learning extraction.

> **Scope the transcript read to the current project slug.** Claude Code transcripts live at
> `~/.claude/projects/<slugified-cwd>/<session-uuid>.jsonl`, and there are **357 project
> directories** on this machine. Globbing `~/.claude/projects/*/` crosses into unrelated
> projects and reads private conversations that have nothing to do with the user's working style.
> Name the slug explicitly.

Signals worth hunting:

- **Response preferences** — length, tone, format; "dumb it down" corrections
- **Delegation habits** — agent teams, model-to-task, parallelism
- **Verification posture** — what "done" means; unit tests versus live repro
- **Code and prose discipline** — style, principles cited, lint and format tools
- **Process conventions** — worktrees, commits, PRs, review and merge tooling
- **Meta preferences** — fixing a skill mid-task, proposing new ones

**Cross-check before elevating.** A pattern seen across 2+ sessions is high-confidence. A lone
signal is noise and usually gets dropped.

### 2. Ask the user directly

Mining misses intent that has not come up yet. Use `AskUserQuestion` with structured options rather
than free text: less effort to answer, and sharper answers. `multiSelect: true` when the question
is which categories apply.

Start broad ("which of these areas matter most?"), follow up only on what they picked, and finish
with an open question to catch what the options missed.

**Ask until you could draft every section without guessing, then stop.** How many rounds that takes
is yours to judge and depends on what the mining already settled: a consistent transcript history
needs one round, a sparse or contradictory one needs several. Still guessing means ask again;
asking to be thorough rather than because an answer is missing means stop.

### 3. Cluster findings

Group signals into sections. Use only what applies:

Response style · Autonomy · Understand-first · Subagents · Prose and code discipline · Review and
verify · Process · Skills

**Only add a section where the user has a specific, non-default rule.** "Communicate clearly" is
not a section. "Short paragraphs. Tables when comparing options. Bullets only when items are
genuinely parallel." is.

### 4. Draft the skill

Author via `/skill-creator:skill-creator`.

- **Path:** `~/.claude/plugins/jbb-feature-dev/skills/<handle>-mode/SKILL.md`. **Never
  `~/.claude/skills/`** — `apply-to-user.sh` replaces that whole directory and the skill would
  vanish.
- **Description:** trigger on the handle and `/<handle>-mode`, never on generic words like "write
  code" or "review PR".
- **Sticky by default.** Once entered, the mode stays active across turns until explicitly exited.
  State that in the skill body — it is behaviour the skill asserts, not frontmatter Claude Code
  enforces. The accepted costs are a persistent context footprint and possible interaction with a
  directly-invoked skill.
- **Deference rule, required.** An explicitly invoked skill wins over the mode's routing. Without
  this the sticky mode competes with `/code-review` and similar, which is the known failure of the
  sticky choice.

### 5. Review the draft, then iterate on prose

**Run `/jiffy-toolkit:context-and-skills-standards` against the draft and apply what it finds.** A
mode skill is exactly the shape that goes wrong: it is written once, loads on every turn it is
active, and accretes rules nobody re-reads. The standards catch the two failures that causes,
instructions that do not earn their tokens and a number restated in two places that will drift.

Then apply `/jiffy-toolkit:sound-like-me` for the prose.

Show the draft, take feedback, expect several rounds. Cut ruthlessly: the review will tell you what
is not pulling its weight, and the answer to that is deletion rather than rewording.

### 6. Land it

Work in a worktree off master. Commit, open a PR. Never push to master.

## Guardrails

- **Do not overfit to one conversation.** A preference stated once and contradicted later is noise.
- **Do not be clever.** Restating other skills, inventing metaphors, or writing "poetic" prose for
  an agent reader is cost with no benefit.
- **Reference, do not inline.** Other skills appear as paths, never as pasted excerpts.
- **Name conventions generically.** "The user", not the handle, inside imperatives.
- **Do not force symmetry.** No process rules worth writing? Skip the section. Sparse is fine.

## Evaluation

A `-mode` skill is subjective output, so a scored benchmark adds little. **Vibe-check it with the
user:** does it read like them, and what did it miss?

Run `/skill-creator`'s description-optimisation loop only if trigger accuracy turns out to be a
problem in practice.

## When not to use

- A task-specific skill → `/skill-creator:skill-creator` alone, no mining
- One narrow workflow ("how I write commit messages") → a regular skill, not a mode skill
