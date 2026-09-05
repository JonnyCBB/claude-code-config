---
name: sweep-followups
# This description is the measured winner, not a draft. A longer, "pushier" rewrite that
# front-loaded intent and buried the trigger phrases mid-sentence scored WORSE on the same
# 20-query eval set: accuracy 65% vs 70%, recall 30% vs 40%, and it lost the literal-phrase
# query "sweep for follow-ups" outright (2/2 -> 0/2). Keep the trigger phrases early and the
# sentences short. The eval set and the probe that measured this are not in this repo; see
# jbrooksbartlett-tlf for both paths, and re-measure before changing this.
#
# RE-MEASURED 2026-08-19, when the dead `--status` flag had to come out of the first sentence.
# Both wordings run in one session, 20 queries x 2: old TP=3, new TP=2 - which looks like a
# regression and is not one. Both arms fire on the SAME three queries; one coin-flip query went
# 1/2 -> 0/2, and the 0.5 threshold turns that into a whole TP. The old wording itself scored
# TP=4 in tlf and TP=3 today, so the baseline moves by the same one query against itself.
# Indistinguishable at this sample size. That the eval cannot resolve a one-query difference is
# jbrooksbartlett-yuql; raw logs in ~/work-evidence/2026-08-19-klse-description-ab/.
description: >
  Reads back over the current session's transcript, finds follow-ups that were mentioned
  but never filed as Beads issues, and files the ones worth keeping labelled
  `agent-proposed` at status `deferred`. Carries a watermark, so running it a second
  time re-files nothing. Use when the user says "/sweep-followups", "sweep for
  follow-ups", "did we miss anything", "what did we not file", "catch up the queue", or
  before ending a long session. Does NOT triage, confirm, dispatch or close anything -
  everything it files stays out of `bd ready` until Jonny confirms it.
argument-hint: "[--dry-run]"
---

# Sweep follow-ups

The turn-end `Stop` hook catches follow-ups at the moment they are deferred. This is the
net underneath it: it re-reads whole turns, so it catches what the hook missed, what was
deferred before the hook existed, and what the model said it would file and then didn't.

**The one thing that must not go wrong: `bd` does not deduplicate.** Two identical
`bd create` calls make two issues. Nothing downstream will merge them. So step 4 is not
bookkeeping — it is the only reason a second sweep is safe to run.

## Step 1 — locate the scanner

The scanner ships in this plugin, two directories above this skill:

```bash
SCAN="<this skill's base directory>/../../hooks/followup_capture.py"
if [ -f "$SCAN" ]; then echo "scanner ok: $SCAN"; else echo "SCANNER NOT FOUND at $SCAN"; fi
```

Substitute the base directory that was printed when this skill loaded. Deriving it that
way is correct by construction — the loaded skill and its sibling scanner are the same
install. Do not instead glob `~/.claude/plugins/cache/*/jbb-feature-dev/*/`: that cache
holds many versions of this plugin plus at least one non-version directory
(`0.20.0.mislabelled-backup`), so a glob can resolve to a real file belonging to a
version other than the one running, and fail silently (jbrooksbartlett-u7c).

The `else` branch is not decoration. `test -f "$SCAN" && echo ok` prints **nothing** when
the path is wrong, which is indistinguishable from never having run the check — so a wrong
base directory reads as a silent pass and you would go on to debug the next step instead.
Stop here if it reports NOT FOUND.

**Then paste the resolved path, not `$SCAN`, into every later step.** Steps 2 and 4 show
`"$SCAN"` for readability, but shell variables do not survive between tool calls — if you
run step 2 as its own call, `$SCAN` is unset and `python3 "$SCAN" scan` becomes
`python3 "" scan`, which dies with `can't find '__main__' module`. It fails loudly rather
than silently, so it costs a wasted call rather than a wrong answer, but substituting the
literal path avoids it entirely.

## Step 2 — scan

```bash
python3 "$SCAN" scan
```

With no `--transcript` it resolves this working directory's newest transcript itself.
Output is JSON:

```json
{
  "session_id": "2aedd1a3-...",
  "turns_scanned": 12,
  "already_swept_turns": 4,
  "suppressed_keys": 7,
  "unfiled": [
    {
      "turn": "a1b2...",
      "candidates": [
        {
          "key": "9f2c1a04bb3d7e58",
          "pattern": "explicit-followup",
          "source": "assistant",
          "text": "The doc is stale on that point - worth a follow-up amendment."
        }
      ]
    }
  ]
}
```

`source` is `assistant` or `user` — a deferral is as often the user's, and step 3 treats
both the same. `"unfiled": []` means there is nothing to do: say so in one line and stop,
without running step 4 and without hunting for candidates by hand to justify the
invocation.

Sweeping twice in a row re-files nothing. Two mechanisms, and both are needed: step 4
moves a cursor past the turn the sweep itself ran in, and it records a content hash per
candidate. The cursor alone is not enough — your own report in step 4 repeats every item
you just filed, and a later turn restating a follow-up has to collide with the earlier
one. That is why the hash deliberately ignores which turn a candidate came from.

A turn that _did_ file a bead is still shown, tagged `"turn_already_filed_a_bead": true`.
It filed something, not necessarily this — a long agentic turn routinely files one
follow-up and defers five more. For those candidates, check the queue before filing,
because `bd` will happily create a duplicate:

```bash
bd list --label agent-proposed --status deferred | grep -i "<subject>" \
  || echo "(no match - nothing filed on that subject yet)"
```

Both filters are required. Confirmed items keep the `agent-proposed` label as a
provenance trail, so filtering on the label alone returns everything ever confirmed.

## Step 3 — judge each candidate, then file the keepers

The scanner matches deferral-shaped _language_, and a meaningful minority of matches are
not real follow-ups. Your judgement is the filter, so read the surrounding turn before
deciding. To see the current hit rate and the families it fires on, run
`python3 "$SCAN" report ~/.claude/projects/*/*.jsonl --samples 40` — that command is the
canonical source for those numbers, so this file does not restate them and cannot go
stale against them.

File it when a person would want it later:

- a bug found and deliberately not fixed on that branch
- a doc, comment or requirements line that the work just made wrong
- a missing test, or a test that only passes in isolation
- a decision only Jonny can make
- work explicitly pushed to a separate PR or ticket

Do **not** file:

- the assistant narrating its own reporting scope ("out of scope for correctness-only review")
- something it went on to do in the same session
- an offer to act ("want me to do X?") — that is a question, not a deferral
- a finding it investigated and refuted

For each keeper, file it per the standing rule in `~/.claude/CLAUDE.md`:

```bash
TITLE=$(cat <<'BD_TITLE'
<what you noticed - verbatim, any characters>
BD_TITLE
)
ID=$(bd create "$TITLE" -p <0-4> -l agent-proposed \
  --deps discovered-from:<the bead this session is working, if any> --silent)
[ -n "$ID" ] || { echo "bd create failed - follow-up NOT filed"; exit 1; }
bd update "$ID" -s deferred
```

The heredoc matters here more than anywhere: a swept title is quoted from the transcript, so it
is someone else's words by construction. Inline, backticks and `$(...)` in it would run.

That rule already states the three things people get wrong here — explicit flags on a
`--parent` child, rescuing ephemeral evidence, and the description bar — so read them
there rather than from a paraphrase. `~/.claude/CLAUDE.md` is always in context, which
makes restating them here pure cost and a second place for them to drift.

One thing the rule does not cover, because it is specific to sweeping: a candidate the
scanner surfaced from the **user's** own words counts. Do not skip it because Jonny
already knows — a queue nobody had to remember is the entire point.

If invoked with `--dry-run`, stop here: report what you would file and skip step 4, so
the watermark does not advance past candidates that were never filed.

## Step 4 — commit the watermark (mandatory, one call)

```bash
python3 "$SCAN" commit --session-id <session_id from step 2> \
  --filed <key>=<bead-id> \
  --filed <key>=<bead-id> \
  --dismissed <key>
```

Every key from step 2 must appear exactly once, as `--filed` or `--dismissed`. Then
report what was filed, with IDs.

Why both, and why all of them:

- A key you omit is offered again by the next sweep and filed a second time. `bd` will
  not stop you.
- `--dismissed` is not a lesser outcome. A candidate you judged worthless and did not
  record is re-proposed on every future sweep forever, which is the same failure wearing
  different clothes.

`commit` also clears the `Stop` hook's nudge budget for this session, so the hook stops
asking about anything this sweep resolved.

Re-read `session_id` from step 2's output rather than expecting a captured value to still
be set — same reason step 1 tells you to paste the scanner's literal path.
