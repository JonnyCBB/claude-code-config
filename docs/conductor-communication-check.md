# The outgoing-message check

Enforces `conductor-communication-contract.md` section 9.

- **The check:** `hooks/comms-contract-check.py`
- **Its tests:** `scripts/tests/test-comms-contract-check.py`
- **Its corpora:** `scripts/tests/fixtures/comms-contract/`
- **Registered as:** a `Stop` hook in `settings.json`

A rule written twice was broken twice, and Jonny declined to be the safety net, so this program is the only thing between the contract and a third failure.

## Where it runs, and the one thing it cannot do

The `Stop` payload carries `last_assistant_message`, the exact outgoing text. On violations the hook returns `{"decision": "block", "reason": ...}` and the model re-issues the message corrected. Hook mode is dispatched explicitly: `--hook` is accepted, and stdin that is not a hook payload reports usage instead of passing silently, so a changed `settings.json` registration cannot turn the blocking path into the by-hand path.

- **It corrects, it does not prevent.** `Stop` fires after the text streamed, so the violating message appears once before the corrected one. No hook event can gate assistant text before display; only tool calls can be gated, which is why `hq-g67x` proposes a second copy on `AskUserQuestion`.
- **A block re-runs the whole `Stop` registration.** Each block costs a second `notify.sh` notification and sound, a second `agent-deck` stop event and a second run of every other `Stop` hook. Accepted.
- A wrapper the conductor calls on its own drafts was rejected: it depends on the conductor remembering.

## Self-scoping

`settings.json` is user-wide, so the hook fires in every session. It applies to conductor sessions only (by `cwd`) and otherwise exits immediately and silently, before any subprocess. `COMMS_CONTRACT_CHECK_SCOPE` (a path fragment) retargets it for testing; the hook prints a stderr breadcrumb whenever the override is active.

## What it refuses

| Check | Contract | Notes |
| --- | --- | --- |
| A bare identifier, first mention | section 1 | Needs id, title as filed, and a line of plain meaning |
| A bare identifier, later mention | section 2 | May shorten to id plus a plain name, never a bare id |
| An identifier leading a table row | section 5 | Refused even when the next cell explains it |
| A habit word with no gloss | section 3 | The missing explanation is the violation, not the word. Matched with inflections ("vetoed", "vetoing") |

Bead ids and session names come from `bd list --all --limit 0 --json` and `agent-deck list --json`, **pulled live on every run, never cached** (session names rename themselves). `--all` is required because `bd list` hides closed beads and reports are largely about closed work (it added 109 suffixes, including three bare ids Jonny was shown); `--limit 0` because `bd list` caps at 50. PR numbers, commit hashes and constants are matched by shape; commit hashes must contain a digit so `facade` is never a hash. File paths are narrowed (see gaps).

Accepted description shapes:

```
prose form           hq-5r44 - Build the outgoing-message check ...
list form            **Outgoing-message check for how I write to you** (5r44) - it is built.
parenthetical form   **`5r44`** (the check that refuses an unexplained code)
```

Adjacency is not a description: `` `c39` flagged it`` is refused.

## How it avoids crying wolf

Suffixes are 3-4 characters and collide with English (`part` is a live suffix; eleven are pure digits). The rule is two-tier. In an **identifier context** (backticks, bold, after a lead word like "bead", alone in a table cell) a live suffix is always an identifier. In **plain prose** it is one only if it could not be an English word or a bare number.

The English test is the system dictionary (`/usr/share/dict/words`, loaded lazily, only in a conductor session), not a hand-kept list, because `bd` generates ids outside this repo. `TECHNICAL_WORDS` (`env`, `dir`, `api`, `cli`) is roughly forty words and not an equivalent fallback: with no system dictionary, English-word suffixes become false positives again. Tests pin that degradation. Words the dictionary masks in prose are still caught in an identifier context.

Two exemptions:

- **Shell commands and handle segments** (template 8.3 ends with `agent-deck session output <id> -q | tmux <name>`). Scoped to the segment holding the identifier, never the whole line, so `` `5r44` is done | agent-deck session output x -q | tmux foo `` still flags the bare id. Table rows are excluded entirely.
- **Code spans and fenced blocks, for habit words only**: a branch named `...-provenance-...` is not the conductor saying "provenance".

## Known gaps

- It cannot judge whether a description is any good; it enforces "never bare".
- It knows only identifiers that exist now; ids from closed sessions or another queue are invisible. Full-form `hq-...` ids are shape-matched and always caught; set `COMMS_CHECK_BEAD_PREFIX` when the queue uses another bd prefix.
- File paths are flagged only when alone in a table cell or as a whole bullet (`hq-0vfp` tracks widening). Function names have no detection path (`hq-2pys`); the narrowing does not cover them.
- One correction per turn: `stop_hook_active` guards the loop, and a second violation in the same turn goes to stderr rather than blocking.
- **Degraded, not silent.** If `bd` or `agent-deck` cannot be read, shape-matched and habit-word checks still run and the report says which source was missed, even when nothing else was flagged. "No violations" with an unreadable live list is not "clean".

## Running it by hand

```
python3 hooks/comms-contract-check.py --file draft.md
python3 hooks/comms-contract-check.py --stdin < draft.md
python3 hooks/comms-contract-check.py --file draft.md --identifiers frozen-ids.json   # reproducible
python3 scripts/tests/test-comms-contract-check.py
EXPECT_BOOTSTRAP_RED=1 python3 scripts/tests/test-comms-contract-check.py   # must exit 1
```

`--identifiers` takes a frozen id list because the live queue moves between runs. Each habit word carries its own matching rules (only "surface" needs part-of-speech sensitivity) as a data row. This repository runs no CI, so the test suite is the only gate; the bootstrap-RED sentinel stops a harness with zero assertions printing green.
