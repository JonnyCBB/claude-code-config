# The outgoing-message check

Enforces `~/.claude/docs/conductor-communication-contract.md` section 9. Built for
`jbrooksbartlett-5r44 - Build the outgoing-message check that enforces the communication contract`.

- **The check:** `hooks/comms-contract-check.py`
- **Its tests:** `scripts/tests/test-comms-contract-check.py`
- **Its corpora:** `scripts/tests/fixtures/comms-contract/`
- **Registered as:** a `Stop` hook in `settings.json`

## Why a program and not a rule

The rule this enforces - a bare identifier from the conductor is never acceptable - was written on
2026-08-14, broken through 2026-08-15, re-issued, and broken again. Asked what would make it hold,
Jonny chose templates plus an automatic check over a self-check, because a self-check is the same
kind of thing as the rule that already failed. He also declined to be the safety net: *"Nothing,
it's my job to get it right unprompted."*

So this file is the only thing standing between the contract and a third failure of the same rule.

## Where it runs, and the one thing it cannot do

It runs as a `Stop` hook. The `Stop` payload carries `last_assistant_message` - the exact outgoing
text - so nothing has to be parsed out of a transcript. When the check finds violations it returns
`{"decision": "block", "reason": ...}`, and the model then re-issues the message corrected.

Hook mode is dispatched explicitly, not inferred from "no arguments were passed". If the
`settings.json` registration ever gains a flag or a wrapper, the blocking path must not quietly
become the by-hand path and skip the check - so `--hook` is accepted, and stdin that is not a hook
payload reports usage instead of passing in silence.

**It corrects, it does not prevent.** `Stop` fires *after* the text has been streamed to the
terminal, so the violating message appears once before the corrected one lands. Evidence for this and
for the block working at all is in `~/.claude/thoughts/shared/verification/2026-08-18-comms-check-evidence/` - `live-session-transcript.jsonl` holds a real session where
a message carrying two bare bead ids was refused and the check's report was injected back as `Stop
hook feedback:`, and `live-2-accept-terminal-output.txt` holds a compliant message passing in a
single turn with no interference. No hook event can gate assistant text before display; only tool calls can be gated
pre-display, which is why `jbrooksbartlett-g67x` proposes a second copy of this check on
`AskUserQuestion` - the tool the contract's decision template uses.

**A block re-runs the whole `Stop` registration, not just this hook.** Measured with a two-hook
probe - a co-registered non-blocking hook fired twice for one blocked message; the raw counter is at
`refire-probe-coregistered-hook-fires.log` in `~/.claude/thoughts/shared/verification/2026-08-18-comms-check-evidence/`. So each block costs a
second desktop notification and sound from `notify.sh`, a second `agent-deck` stop event and a second
knowledge-graph ingest. That is accepted rather than worked around - a contract violation being
noisy is not the wrong outcome - but it is a real cost and not a guess.

A wrapper the conductor called on its own drafts was rejected: it would depend on the conductor
remembering to call it, which is the failure this bead exists to remove.

## Self-scoping

`settings.json` is user-wide, so this hook fires in **every** session on this machine. It decides
for itself whether it applies - conductor sessions only, by `cwd` - and exits immediately and
silently everywhere else, before running any subprocess. Set `COMMS_CONTRACT_CHECK_SCOPE` to a path
fragment to point it somewhere else for testing - the hook prints a stderr breadcrumb whenever that
override is active, so a value left behind in a shell profile cannot silently disable the real check.

## What it refuses

| Check | Contract | Notes |
| --- | --- | --- |
| A bare identifier, first mention | section 1 | Needs the id, the title as filed, and a line of plain meaning |
| A bare identifier, later mention | section 2 | May shorten to id plus a plain name, never to a bare id |
| An identifier leading a table row | section 5 | Refused even when the next cell explains it - this was the exact shape of the 2026-08-15 reports |
| A habit word with no gloss | section 3 | The word is never the violation; the missing explanation is. Matched with inflections, so "vetoed" and "vetoing" count, not just "veto" and "vetos" |

Six kinds of identifier are covered. Bead ids and session names come from
`bd list --all --limit 0 --json` and `agent-deck list --json`, pulled **live on every run and never
cached** - session names rename themselves, so `sb-detail-panel-build` became
`feature-feat-2026-08-18-detail-panel-d1`.

**`--all` matters more than it looks.** `bd list` hides closed beads by default, and a status report
is largely *about* closed work. Measured on 2026-08-18: the default view held 450 distinct suffixes
and `--all` holds 559, and the ones it was missing included `cyi`, `c39` and `9oi` - three of the bare
ids Jonny was actually shown on 2026-08-15. With the default view the worst message in the corpus
lost four of its violations, all of them ids leading table rows. `--limit 0` is there for the same
reason: `bd list` caps at 50 by default, and grounding this on an uncapped listing is the difference
between a checked absence and an assumed one.

PR numbers, commit hashes and constants are matched by shape. File paths are narrowed; see the gaps
below.

Three description shapes are accepted, from contract section 1:

```
prose form           jbrooksbartlett-5r44 - Build the outgoing-message check ...
list form            **Outgoing-message check for how I write to you** (5r44) - it is built.
parenthetical form   **`5r44`** (the check that refuses an unexplained code)
```

Adjacency is not a description. `` `c39` flagged it`` puts two words beside a bare id without ever
saying what `c39` is, so it is refused.

## How it avoids crying wolf

False positives are how a check earns itself a disabling, and bead suffixes are three or four
characters, so they collide constantly. Measured against the live queue on 2026-08-18: of 450 beads,
`part` is a real suffix and eleven suffixes are pure digits.

The rule is two-tier. In an **identifier context** - backticks, bold, after a lead word like "bead",
or alone in a table cell - a suffix from the live list is always an identifier. In **plain prose** it
is one only if it could not plausibly be an English word or a bare number. This is grounded in the
corpus rather than guessed: across the six real 2026-08-15 messages in
`scripts/tests/fixtures/comms-contract/` every genuine bead reference was written in backticks, and
all three occurrences of "part" were ordinary English. That corpus is the primary source for this
section; the code comments cite it rather than restating the counts.

The English test is the **system dictionary** (`/usr/share/dict/words`, ~234k words, ~36 ms loaded
lazily and only inside a conductor session), not a hand-kept list. `bd` generates ids outside this
repo, so the next word-shaped suffix it emits would otherwise turn this check into a false-positive
machine until someone edited a literal - `part` was only safe because it had already caused a
failure. `TECHNICAL_WORDS` keeps the non-dictionary tokens that must still be treated as risky
(`env`, `dir`, `api`, `cli`). It is **not** an equivalent fallback: it is roughly forty words standing
in for 234,000, so on a machine with no system dictionary the precision described in this section
does not hold and ordinary English words that happen to be live bead suffixes become false positives
again. The test suite pins that degradation in all three directions rather than implying equivalence. Of 125
live alpha suffixes, the dictionary masks six in plain prose; all six are still caught in an
identifier context.

Two further exemptions, both needed to keep the contract's own templates passing:

- **Shell commands and handle segments.** Template 8.3 ends every dispatch with
  `agent-deck session output <id> -q | tmux <name>`. That line exists to give him something to open,
  not something to read. The exemption is scoped to the **segment** holding the identifier, not the
  line: an earlier version exempted a whole line whenever it had three or more pipe-separated
  segments and any one was a command, which let `` `5r44` is done | agent-deck session output x -q |
  tmux foo `` exempt the bare id sitting in the prose segment. Pipe count says nothing about whether
  a token is a handle. Table rows are excluded entirely, so a bare id leading a row can never buy
  its way out.
- **Code spans and fenced blocks, for habit words only.** A branch named
  `eng-utils-0.11.0-provenance-and-prose-gate` is not the conductor saying "provenance".

Commit hashes must contain a digit, which no English word does - so `facade` and `accede` are never
mistaken for hashes.

## Known gaps, stated rather than discovered later

- **It cannot judge whether a description is any good.** It enforces "never bare", which is the rule
  that was broken twice and the one measurable target in contract section 12. Whether the plain line
  actually lands in his terms is not mechanically decidable.
- **It only knows identifiers that exist now.** Bare short suffixes are matched against the live
  list, so an id from a closed session or a different bead queue is invisible to it. This is the
  design the bead mandated, chosen over shape-matching, because a three-character pattern matches
  ordinary English constantly. Full-form `jbrooksbartlett-...` ids are shape-matched and so are
  caught even when filed after the list was pulled.
- **File paths are narrowed, and function names are not detected at all.** A path or filename is
  flagged only when it stands completely alone in a table cell or as a whole bullet; the same path
  inside a sentence is ignored, because the conductor writes paths many times a session and demanding
  a description at every mention is how a check earns itself a disabling. `jbrooksbartlett-0vfp`
  tracks widening that. **Function names have no detection path whatsoever** - contract section 1
  asks for them and there is no reliable shape to match, so `jbrooksbartlett-2pys` tracks it. Do not
  read the narrowing as covering them.
- **One correction per turn.** `stop_hook_active` guards the loop; a second violation in the same
  turn is reported to stderr rather than blocked, so a message can never wedge.
- **Degraded rather than silent.** If `bd` or `agent-deck` cannot be read, the shape-matched checks
  and the habit-word check still run and the report says which source was missed. **A degradation is
  reported even when nothing else was flagged** - "no violations found" while the live list was
  unreadable does not mean the message was clean, it means the check that catches bare short suffixes
  did not run, so that is stated on stderr rather than passed over. Two independent reviewers found
  this swallowed before it was fixed.

## Running it by hand

```
python3 hooks/comms-contract-check.py --file draft.md
python3 hooks/comms-contract-check.py --stdin < draft.md
python3 hooks/comms-contract-check.py --file draft.md --identifiers frozen-ids.json   # reproducible
python3 scripts/tests/test-comms-contract-check.py
EXPECT_BOOTSTRAP_RED=1 python3 scripts/tests/test-comms-contract-check.py   # must exit 1
```

`--identifiers` takes a frozen id list, because a plain `--file` run is judged against a queue that
moves between runs. Each habit word carries its own matching rules, so a word needing
part-of-speech sensitivity - "surface" is the only one today - is a data row rather than a second
code path.

This repository runs no continuous integration, so that test suite is the only gate. The
bootstrap-RED sentinel exists so a harness that recorded zero assertions cannot print green.
