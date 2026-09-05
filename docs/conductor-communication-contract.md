# The communication contract: how the conductor writes to Jonny

Agreed 2026-08-18 in an interview with Jonny. This is the companion to
`~/.claude/docs/conductor-work-contract.md`. That one governs **what work gets done** - triage,
dispatch, merging, closing, capacity. This one governs **how work is described to him**. They do
not overlap, and neither overrides the other.

**Record of the interview:** `~/.claude/thoughts/shared/requirements/2026-08-18-conductor-communication-contract-requirements.md`
It carries what he actually said, the options he rejected, and why each rule is shaped the way it
is. Read it when a rule here looks fussy.

**Why this file lives here and not in the conductor folder:** `agent-deck conductor setup hq`
rewrites `hq/CLAUDE.md` and `hq/POLICY.md`, so anything written there can be destroyed without
warning. This file and `~/.claude/CLAUDE.md` (which points at it) are outside that command's reach.

---

## Why this file exists, and why writing the rule down is not enough

The core rule already existed twice before this contract.

- **2026-08-14** - Jonny: *"The Beads mean nothing to me, but the titles mean a lot more."*
  A section headed "NEVER write a bare ID to Jonny" went into `hq/CLAUDE.md`.
- **2026-08-15** - the conductor broke it in essentially every status report of the day. Jonny had
  to correct it a second time: *"don't just give me the three character ids because they mean
  nothing to me. Always give me either the title or the description of the session or the bead so
  that I know exactly what the work is."*

`hq/CLAUDE.md` even records why it failed: *"the rule is easy to honour in the first paragraph and
then drop once the IDs feel familiar TO ME. They never become familiar to him."*

So the useful question was never "what is the rule". It was **why a written rule does not hold**.
Two things came out of asking him.

**1. The cost is friction and lost continuity, not bad decisions.** Asked what actually goes wrong
when he gets a bare ID, he picked "you lose time" and "you lose the thread across time". He did
**not** pick "you decide worse" or "you skim past it". That sets the target: a message is only
correct when he never has to look anything up or ask, and it has to still be correct on the
fortieth mention and after a five-hour gap. A first-mention-only rule is guaranteed to fail him.

**2. He is a software engineer. The gap is context, not capability.** He is not dispatching the
workers and not writing the code, so he has no exposure to the specifics. Simplifying the
engineering is the wrong correction and he does not want it. Supplying the context he was never
given is the right one.

---

## 1. Every identifier carries what it is. A bare ID from the conductor is never acceptable.

**This is not asymmetric.** Jonny's own words when offered a rule that would have stopped the
conductor using IDs at all: *"I don't mind you using the bead id as well but it must in addition to
the title that you echo back."* Both of them keep using IDs. What changed is that the conductor's
never travel alone.

**In a sentence: ID, then the title exactly as filed, then a line saying what it means.**

```
cyi - config_admin/client.py:707 writes blank namespaces on the production write path
What that means: config_admin is the part of the system that saves Home configuration. Every
saved config carries a "namespace" field naming which section of Home it belongs to, and that
field is being saved empty. It happens on the code path that writes real production config, so
a broken record reaches live users.
```

Note what that example does and does not do. It still says "written empty" and "production write
path" - the engineering is intact. What it adds is what `config_admin` is for and what the
consequence is. **That is the whole distinction.** Do not simplify the mechanism; supply the
context.

**In a list: the plain-language name first, the ID in brackets after it, then the plain line.**

```
AWAITING YOU

**Blank namespace on the production config write path** (cyi)
Saved Home configs are missing the label saying which Home section they belong to, on the path
that writes live config.
Needs: your call on whether to fix before or after the alpha.
```

**ID first in a sentence, plain name first in a list.** Confirmed deliberate. In prose the ID reads
naturally at the front; in a list he scans the left edge for what things are, not for codes.

**When HE writes a bare ID, echo the title back once, then answer.** *"Yes - that's the one about
the blank namespace on the live config write path. Here's the answer..."* One clause, and it catches
the failure where the conductor resolves his ID to the wrong item and both of them work on a
misunderstanding.

### It applies to every kind of identifier, and none of them get dropped

His words: *"These can all be opaque but I don't want them completely dropped. Just explained
well."*

| Identifier | Why it is opaque to him | The form he gets |
| --- | --- | --- |
| **Bead IDs** (`cyi`, `w45.19`, `jbrooksbartlett-x698`) | No mapping in his head from the code to the work | ID, title as filed, what it means |
| **Session names** (`feature-feat-2026-08-18-detail-panel-d1`) | **Worse than beads: they rename themselves.** `sb-detail-panel-build` became `feature-feat-2026-08-18-detail-panel-d1`; `bug-hunt-targeting-research` became `claude-64` | What the session is DOING, then the name |
| **PR numbers** (`#146`) | A number with a title he has not seen, and **no way to open it** | **The full URL, always.** Number, PR title, what the change does, and the clickable link |
| **Commit hashes** (`9efc494`) | No accessible form exists beyond what it did | "the change that did X (`9efc494`)" |
| **File paths and function names** (`compose.ts`, `config_admin/client.py:707`) | Precise, searchable, and silent about what the file is for | Path, plus what that file is responsible for |
| **Error codes and constants** (`NON_OWNED_CONFIG_DENIED`, `NOT_LOADED_UNTIL_ENRICHED`, `readError`) | They read as if they explain themselves and they do not | Code, plus what it means when it fires and what triggers it |

---

## 2. Never drop below ID-plus-title. Every new message starts from cold.

| Where | What he gets |
| --- | --- |
| First mention in a message | Full treatment: ID, title, what it means |
| Later in the **same** message | ID plus a short plain name. **Never a bare ID** |
| A **new** message, even ten minutes later | Full treatment again, from scratch |

The third row is the one that costs something and it is the one he asked for. "You lose the thread
across time" was one of his two stated costs. He was never carrying the context the conductor feels
it shares with him.

---

## 3. Keep the precise word. Always explain it. Both kinds.

He raised this himself, unprompted, and it is broader than identifiers: *"I noticed the agent using
a lot of terms like provenance and load-bearing. I don't really understand these terms and I really
prefer if we use much more accessible language."*

Two kinds of word, and he chose the same treatment for both - **keep whichever word is most
precise, and always explain it.**

| Kind | Examples | Treatment |
| --- | --- | --- |
| **Engineering words** | namespace, descriptor, manifest, race condition, idempotent | Keep. Explain on first use in a message. There is often no short plain substitute |
| **The conductor's own abstract vocabulary** | provenance, load-bearing, orthogonal, blast radius, falsifier, affordance, cadence, veto | Keep if it is genuinely the most precise word, but ALWAYS gloss it: "provenance (where it came from)" |

He was offered the stricter option - replace the abstract words with plain English outright - and
**declined it**, choosing "explain both, don't replace anything". Precision preserved, nothing left
to decode.

**A note on how this rule gets broken:** the conductor used "load-bearing" twice and "asymmetric"
once inside the very interview that agreed this contract. This vocabulary is reflexive, which is
exactly why it needs a check rather than good intentions.

---

## 4. Reports stay complete, but tiered

He was offered permission to filter out items that do not need him. **He did not take it.** Nothing
vanishes from a report.

| Tier | What earns it | What he gets |
| --- | --- | --- |
| **Full** | Only he can do or decide it - a decision genuinely his, approving something, spending money, messaging another team | ID, title, what it means, and what is needed from him |
| **One line** | Everything else, including work going well and problems the conductor is handling itself | One line: what it is, and that it is fine |

He was offered wider full-treatment tiers ("plus anything stuck or broken", "plus anything I'm
unsure about") and chose the narrow one. Note the consequence honestly: **something can go wrong
and reach him as one line**, as long as the conductor is genuinely handling it.

---

## 5. No tables for anything that needs explaining

Tables are the format that most reliably produced bare IDs, and the reason is structural rather
than careless: a table cell physically cannot hold a context sentence without wrapping into mush in
a terminal, so the format itself pushes toward a bare code in a narrow column.

- **Tables only for things he scans** - counts, pass/fail columns, yes/no.
- **Never an ID leading a row.**
- Anything needing a "what that means" line becomes a short list with a bold lead line instead
  (the format in section 1).

---

### 5.1 A pull request without its URL is not actionable

Added 2026-08-18 at Jonny's request, after a status report listed PR #89 and PR #90 by number and
title with no link. His words: *"When I need to review a PR, I actually need to have the full URL so
I can go straight to it. Just seeing the numbers doesn't completely help me, especially if it's only
alongside the bead ID... If ever you refer to a PR it's fine if you print the PR number, but I need
the URL for it to be useful and for me to be able to go straight to the PRs and review them."*

**THE FORM, EXACTLY. Jonny picked this one out of a live message and asked for it by name.**

```
**<plain-language name, bold>** (<bead id>, PR #<n>)
<full URL on its own line>
```

Worked example, verbatim from the message he approved:

```
**Move the conductor's reference depth into two lazy-loaded docs** (`jbrooksbartlett-0vju`, PR #89)
https://github.com/JonnyCBB/claude-code-config/pull/89
```

Three things about this shape, and each is doing work:

1. **The bold name comes first**, so he scans the left edge for WHAT it is rather than for a code.
   This is the same list form section 1 already specifies - `**<plain name>** (<id>)` - simply
   extended with the pull-request number and the link. It is not a new convention to remember; it is
   the existing one, finished.
2. **Both identifiers sit together in the brackets**, bead first then PR. They are reference data,
   useful when he needs them and out of the way when he does not.
3. **The URL is on its own line, bare.** Not wrapped in markdown link syntax, not trailing a
   sentence - a bare URL on its own line is unambiguously clickable in a terminal, and nothing else
   competes with it for that line.

Follow it with the "what that means" line and whatever else the message needs. The block above is
the header, not the whole entry.

**Why the previous rule was insufficient rather than wrong.** Section 1 already required the number,
the title and what the change does - and a report following it exactly still left him unable to act,
because reviewing a pull request means OPENING it. Number-plus-title identifies the thing; only the
URL reaches it. This is the same shape as the bead-ID failure: the conductor supplied what identified
the work to someone who already knew where it lived.

**The rule:**

- **Every mention of a pull request carries its full URL.** Not the number alone, not
  `owner/repo#n`, not "the switchboard PR". The complete clickable link.
- **On its own line**, not buried mid-sentence, so it is one click from the terminal.
- **Get it from `gh`, do not construct it** - `gh pr view <n> --repo <owner>/<repo> --json url`.
  Repositories live on `github.com`, not `github.com`, and a hand-built github.com link 404s
  indistinguishably from a deleted branch.
- **Several at once means a list**, one per pull request, each with its own link. Never a table -
  a URL in a narrow column wraps into mush, which is the same structural reason section 5 bans
  tables for anything needing explanation.

**This applies to any identifier that has an openable address**, not only pull requests: a Honk
worker session has a Chirp URL, and a Google document has one. If he could act on it by opening it,
give him the thing that opens it.

---

## 6. Same total length. The descriptions are paid for, not added.

He chose "same length, better shaped" over "longer is fine if it's complete". So every description
added has to be funded by cutting something. He named what he will trade away, and - importantly -
what he will not.

| | |
| --- | --- |
| **CUT: restating decisions he already made** | Re-explaining a rule he set, re-justifying a decision he already took. Pure re-reading for him, and a large fraction of the conductor's output |
| **CUT: raw output and commands** | Pasted JSON, full command incantations, check-name lists, queue counts. Keep the conclusion; drop the evidence unless he asked or it is the proof of a claim |
| **KEEP: narration of what the conductor is doing** | Offered as a cut and **not taken** |
| **KEEP: every item in a report** | Offered as a cut and **not taken**. See the tiering in section 4 - complete, not filtered |

---

## 7. Decision messages get the most care

In his words: **"The decisions are the things that are most important to me."** Every decision he is
asked to make carries all four of these.

1. **What the decision is**, in one line.
2. **Each option with its pros AND cons, stated clearly** - in terms of what happens to him and
   what he would have to live with, **not** how the options differ mechanically. He asked for this
   explicitly, and the conductor's habit is the opposite: describe the mechanisms and leave him to
   derive the consequences.
3. **The conductor's own pick, with reasons.** Not a neutral survey. He overruled a recommendation
   on the morning of 2026-08-18 after hearing the risk stated plainly, and that is how it should
   work.
4. **What would change the conductor's mind** - the thing that, if true, flips the recommendation.
   A decision on retro-reviewing PR #146 (the switchboard pull request that was behind its base
   branch) was reversed 40 minutes after it was made when new evidence arrived, and that reversal
   was only possible because the original decision had a written trigger.

He was offered "what it costs to not decide now" as a fifth element and did not select it. Include
it when it is genuinely load-bearing (that is: when it changes what he should do), not as a
standing field.

---

## 8. Four message types have a fixed shape

He asked for all four to be pinned down. The shape is what makes the rule hold; a template where
an ID has nowhere to sit alone cannot be broken the way a remembered rule can.

### 8.1 The regular status check-in (the heartbeat report)

The worst historical offender - this is the message that was full of bare IDs all through
2026-08-15.

```
[STATUS] <one line: what changed since last time, or "nothing needs you">

NEEDS YOU
**<plain-language name>** (<id>)
<what it means, in his terms>
Needs: <the specific thing required from him>

EVERYTHING ELSE
- <plain name> (<id>) - <one line, what it is and that it is fine>
- <plain name> (<id>) - <one line>

QUEUED, WILL AUTO-FIRE
- <plain name> (<id>) - waiting on <what>
```

Empty sections are omitted, not printed empty.

### 8.2 Asking him to decide

```
DECISION: <the question, one line>

Option A - <name>
  What happens: <consequence for him>
  Pros: <...>
  Cons: <...>
Option B - <name>
  What happens: <consequence for him>
  Pros: <...>
  Cons: <...>

My pick: A, because <reason>.
What would change my mind: <the fact that would flip it>.
```

Use `AskUserQuestion` where the options are genuinely discrete, and put the recommendation in
option A with "(Recommended)" in the label. The prose form above is for the cases where options
would be artificial.

### 8.3 Announcing a worker has started

```
STARTED: <plain-language name of the work> (<bead id> - <bead title>)
Why now: <one line>
What it will produce: <the deliverable, usually a PR>
Watch it: session <name> | agent-deck session output <id> -q | tmux <tmux name>
```

For Honk (remote) workers the watch line is the Chirp URL:
the Chirp session URL for the run.

This section restates a rule from the work contract rather than replacing it: **every dispatch
gives him a way to open the worker himself, in the message that announces it.** Several in one turn
means a list, not a sentence each.

### 8.4 Something is finished and ready for him

```
READY: <plain-language name> (<bead id> - <bead title>)

**<pr title, bold>** (<bead id>, PR #<n>)
<full URL on its own line>
What changed: <in his terms>
What it means for you: <what is different now, or what you are approving>
Checked: <the four-step chain, CI, live verification - what actually ran>
NOT verified: <what could not be checked, and why - never silence>
```

The "NOT verified" line is mandatory when anything was skipped. The work contract's rule stands:
silence is not the same as "not possible", and a PR that quietly skipped live verification while
implying completeness is worse than one that admits the gap.

---

## 9. What makes it hold: an automatic check, not the conductor's memory

He was asked directly what would make this stick, given the rule has been written twice and broken
twice, and given he had just refused to be the safety net. He chose **templates plus an automatic
check**, over a self-check, over templates alone.

The reasoning he was given and accepted: a self-check pass is the same kind of thing as the rule
that already failed. It works right up until the conductor is busy or the IDs start feeling
familiar. Only something outside the conductor's memory catches it reliably.

**What the check does:**

1. Reads the conductor's draft before it reaches him.
2. Pulls the live list of bead IDs (`bd list`) and session names (`agent-deck list --json`).
3. Finds every appearance of one of those identifiers in the draft, and flags any that has no
   description beside it.
4. Flags a maintained list of the conductor's habit words (provenance, load-bearing, orthogonal,
   blast radius, falsifier, affordance, cadence) used without a gloss.

**This does not exist yet.** It is filed as `jbrooksbartlett-5r44 - Build the outgoing-message check
that enforces the communication contract`, at status `open` because it is his decision, not an
agent proposal. The bead carries the traps that matter, chief among them: a bare bead suffix is
three or four characters, so a regex on its shape matches ordinary English constantly - the check
must match against the live list of IDs, never against a pattern. Until it is built, the self-check is the fallback - and the fallback is known to be
the weaker thing, so the bead matters.

---

## 10. Nothing is required of him

He was offered three signals he could give - "too dense", "I've lost the thread", "short version" -
and chose **"Nothing - it's my job to get it right unprompted."**

That is a design constraint, not a courtesy. Any version of this contract that depends on him
noticing a failure has already failed. It is also why section 9 is not optional.

---

## 11. Relationship to the other rule files

| File | What it governs | Status |
| --- | --- | --- |
| `~/.claude/docs/conductor-work-contract.md` | What work gets done: triage, dispatch, merging, closing, capacity | Unaffected by this file |
| `hq/CLAUDE.md`, section "NEVER write a bare ID to Jonny" | The original rule, set 2026-08-14, re-issued 2026-08-15 | **Extended by this file.** The rule there is correct and insufficient: "ID plus title" only reaches the halfway point, because a title written by whoever filed the bead is in their vocabulary, not his. A pointer to this file has been added there |
| `../POLICY.md` (shared) | Response style, escalation | Where it conflicts on message format, this file wins - it is newer and he agreed it explicitly |

**Precedence, for the same reason the work contract gives:** `agent-deck conductor setup` writes
both POLICY files, so neither is durable. This file is loaded from `~/.claude/CLAUDE.md`, which
agent-deck does not manage at all.

---

## 12. How to tell whether this is working

| Signal | Target | What it catches |
| --- | --- | --- |
| Bare identifiers reaching him | **0** | The rule itself |
| Times he has to ask what something is | **0** | His actual stated cost: losing time |
| Times he says he has lost the thread | **0** | His other stated cost: losing continuity |
| Message length, before and after | **unchanged** | Whether the descriptions were paid for or just added |
| Times he corrects the conductor on this | trending to 0 | Whether the check is doing the work his attention used to |

The last one is the real test. He has corrected this twice by hand. A third time means section 9
did not work.
