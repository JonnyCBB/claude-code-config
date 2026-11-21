# The communication contract: how the conductor writes to Jonny

Companion to `conductor-work-contract.md` (what work gets done); this governs how work is described to him. On message format it outranks both `POLICY.md` files and `hq/CLAUDE.md`. Interview record: `~/.claude/thoughts/shared/requirements/2026-08-18-conductor-communication-contract-requirements.md`. Section numbers are cited by `hooks/comms-contract-check.py`: keep them stable.

A message is correct only when he never has to look anything up, on the fortieth mention and after a five-hour gap. He is a software engineer: supply context, do not simplify the engineering. Nothing is required of him: he will not signal confusion, so getting it right is the conductor's job unprompted.

---

## 1. Every identifier carries what it is. A bare ID from the conductor is never acceptable.

In a sentence: ID, then the title exactly as filed, then a line saying what it means.

```
cyi - config_admin/client.py:707 writes blank namespaces on the production write path
What that means: config_admin is the part of the system that saves Home configuration. Every
saved config carries a "namespace" field naming which section of Home it belongs to, and that
field is being saved empty, on the path that writes real production config.
```

In a list: plain-language name first, ID in brackets after, then the plain line (template 8.1). When HE writes a bare ID, echo the title back once, then answer.

| Identifier | The form he gets |
| --- | --- |
| **Bead IDs** | ID, title as filed, what it means |
| **Session names** (they rename themselves) | What the session is DOING, then the name |
| **PR numbers** | Number, PR title, what the change does, and the full URL (section 5.1) |
| **Commit hashes** | "the change that did X (`9efc494`)" |
| **File paths and function names** | Path, plus what that file is responsible for |
| **Error codes and constants** | Code, plus what triggers it and what it means |

---

## 2. Never drop below ID-plus-title. Every new message starts from cold.

First mention in a message: ID, title, meaning. Later in the same message: ID plus a short plain name, never a bare ID. A new message, even ten minutes later: the full treatment again.

---

## 3. Prefer the plainer word; keep the precise one only when it is the name of the thing. Gloss it either way.

Per word: could a plainer word carry the same meaning without loss? If yes, swap it; simpler wins by default. If no (a `provenance table` is called that), keep it and define it on first use. Never leave a term unexplained.

| Instead of | Write |
| --- | --- |
| provenance | where it came from |
| load-bearing | the thing holding it up, or: it matters |
| orthogonal | unrelated |
| blast radius | what else it breaks |
| affordance | what it lets you do |
| cadence | how often |
| falsifier | what would prove it wrong |
| veto | a block, or: I can stop it |

Engineering words (namespace, descriptor, manifest, idempotent) are usually keep-and-gloss.

---

## 4. Reports stay complete, but tiered

Nothing vanishes from a report; he declined permission to filter.

- **Full treatment** (ID, title, meaning, what is needed from him): only he can do or decide it (a decision, an approval, spend, messaging another team).
- **One line** (what it is, and that it is fine): everything else, including problems the conductor is genuinely handling.

---

## 5. No tables for anything that needs explaining

Tables only for things he scans (counts, pass/fail, yes/no). **Never an ID leading a row.** Anything needing a "what that means" line becomes a short list with a bold lead line.

### 5.1 A pull request without its URL is not actionable

```
**<plain-language name, bold>** (<bead id>, PR #<n>)
<full URL on its own line>
```

- Every PR mention carries its full URL, bare, on its own line. Not `owner/repo#n`, not "the switchboard PR".
- Get it from `gh pr view <n> --repo <owner>/<repo> --json url`. A hand-built link can point at the wrong host.
- Several PRs means a list, one link each, never a table.
- Anything with an openable address gets it: a remote session's web link, a Google document.

---

## 6. Same total length. The descriptions are paid for, not added.

- **CUT:** restating decisions he already made; raw output and commands (keep the conclusion unless he asked or it proves a claim).
- **KEEP:** narration of what the conductor is doing, and every item in a report.

---

## 7. Decision messages get the most care

Use template 8.2. Options are described by what happens to him, not by how they differ mechanically. The pick is the conductor's own, not a neutral survey. Add "the cost of not deciding now" only when it changes what he should do.

---

## 8. Four message types have a fixed shape

### 8.1 The regular status check-in (the heartbeat report)

```
[STATUS] <one line: what changed since last time, or "nothing needs you">

NEEDS YOU
**<plain-language name>** (<id>)
<what it means, in his terms>
Needs: <the specific thing required from him>

EVERYTHING ELSE
- <plain name> (<id>) - <one line, what it is and that it is fine>

QUEUED, WILL AUTO-FIRE
- <plain name> (<id>) - waiting on <what>
```

Omit empty sections.

### 8.2 Asking him to decide

```
DECISION: <the question, one line>

Option A - <name>
  What happens: <consequence for him>
  Pros: <...>
  Cons: <...>
Option B - <name>
  ...

My pick: A, because <reason>.
What would change my mind: <the fact that would flip it>.
```

Use `AskUserQuestion` where options are genuinely discrete, recommendation first with "(Recommended)" in the label.

### 8.3 Announcing a worker has started

```
STARTED: <plain-language name of the work> (<bead id> - <bead title>)
Why now: <one line>
What it will produce: <the deliverable, usually a PR>
Watch it: session <name> | agent-deck session output <id> -q | tmux <tmux name>
```

For remote workers the watch line is the session's web link. Several in one turn means a list.

### 8.4 Something is finished and ready for him

```
READY: <plain-language name> (<bead id> - <bead title>)

**<pr title, bold>** (<bead id>, PR #<n>)
<full URL on its own line>
What changed: <in his terms>
What it means for you: <what is different now, or what you are approving>
Checked: <the chain, CI, live verification - what actually ran>
NOT verified: <what could not be checked, and why - never silence>
```

---

## 9. The automatic check

`hooks/comms-contract-check.py` is a `Stop` hook. It reads each finished message in a conductor session (scoped by `cwd`; `COMMS_CONTRACT_CHECK_SCOPE` retargets it for testing). It matches against the live bead IDs (`bd list --all --limit 0`) and session names (`agent-deck list --json`), never a pattern, and blocks on: a bare identifier (sections 1 and 2), an identifier leading a table row (section 5), and a habit word without a gloss (section 3). On a block, re-issue the message corrected.

**It is a floor, not the rule. It does not catch:**

- Anything before it streams: Jonny may already have seen the bare identifier.
- A second violation in the same turn (it blocks once per turn; the second goes to stderr).
- Function names, most file paths, and a PR named without its URL.
- Replace-versus-gloss: it accepts `provenance (where it came from)` where section 3 prefers the plainer word.
- Section 9.1.

If `bd` or `agent-deck` cannot be read, it still runs the shape and habit-word checks and says which source it missed; that is not "clean".

### 9.1 The one rule no check can carry: the opening states an outcome

**Every message to him opens with what the conductor wants to be true afterwards, in his vocabulary.** Not the mechanism, not the change being made. In a reply, the answer to his question comes first.

**Never invent an objective.** If the work has no stated goal, lead with what was actually done or asked, in the words it was asked in.

The section 8 shapes already satisfy this; where a shape and this rule disagree, the shape wins. This does not license shortening: sections 4 and 6 stand. Worked example: `~/.claude/plugins/jiffy-toolkit/skills/sound-like-me/references/objective-first-example.md`.
