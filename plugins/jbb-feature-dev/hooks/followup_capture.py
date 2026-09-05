#!/usr/bin/env python3
"""Mechanical half of the follow-up capture rule (see ~/.claude/CLAUDE.md).

One scanner, two callers:

  hook    Stop-hook entry point. Reads hook JSON on stdin. Decides whether the turn
          that just ended deferred something without filing it, and if so asks the
          model to file it before stopping. Silent otherwise.
  scan    /sweep-followups entry point. Prints every un-swept candidate in the
          transcript as JSON for the model to judge.
  commit  Advances the watermark and records what was filed or dismissed, so a
          second sweep re-files nothing. Beads does not deduplicate.
  report  Corpus measurement: fire rate and per-pattern hit counts. Used to justify
          the detector's cost, not used at runtime.
  resolve Prints the newest transcript path for the current working directory. A
          convenience for driving `scan` by hand; `scan` already does this itself.

Design constraints this file is built to (all from the requirements doc,
~/.claude/thoughts/shared/requirements/2026-08-14-followup-capture-and-dispatch-requirements.md):

* Runs at every turn end in every session across ~34 repos, so it must be cheap and
  must never raise. Every entry point is wrapped; any unexpected error exits 0 silently.
* State lives OUTSIDE any git-pushed directory. ~/.claude and ~/beads-hq both have
  remotes, so the watermark goes under $XDG_STATE_HOME (default ~/.local/state).
* The detector only gates whether to spend a turn; the model does the extraction.
  A false positive costs one extra turn, so precision matters for cost, not correctness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time

# Only the tail of a transcript is ever read. Tool results can be megabytes, and the
# hook only cares about the turn that just ended.
TAIL_BYTES = 512 * 1024

# A nudge is worth at most one extra turn, so it must be rare. If the same turn is
# still unresolved after this many stops, drop it -- the sweep skill is the net.
MAX_NUDGES_PER_TURN = 1

# How much of the opening human prompt to scan. Prompts routinely carry a pasted
# requirements document; a scope table inside one is not this turn's deferral.
HUMAN_PROSE_LIMIT = 4000

# Detection is two-tier, and that split is the whole reason precision is usable.
#
# TIER1 fires on its own: language that appears only when the speaker is explicitly
# consigning something to a later unit of work.
#
# CUES + WORK_NOUN must co-occur in one sentence. A cue alone is far too loose.
# Measured over 405 real transcripts (1,947 turns): a bare "out of scope" match fired
# on 110 turns and was almost always the assistant describing the boundary of its own
# report -- "out of scope for correctness-only reporting" -- rather than deferring a
# discovered problem. Requiring a concrete noun of work is what separates the two.

TIER1: list[tuple[str, re.Pattern[str]]] = [
    (
        "explicit-followup",
        re.compile(
            r"\b(worth|deserves?|needs?|wants?|should (be|get|have))\b[^.!?\n]{0,40}"
            r"\b(a )?(follow.?up|separate (ticket|bead|issue|PR)|its own (ticket|bead|issue|PR))\b",
            re.I,
        ),
    ),
    (
        "should-be-filed",
        re.compile(
            r"\b(should|ought to|needs? to|must) be (filed|tracked|captured|ticketed|logged)\b",
            re.I,
        ),
    ),
    (
        "filing-later",
        re.compile(
            r"\b(fil(e|ing)|rais(e|ing)|open(ing)?|track(ing)?) (a|another|one) "
            r"(follow.?up|bead|ticket|issue)\b",
            re.I,
        ),
    ),
]

# A cue says "not now". On its own it means nothing.
CUES: list[tuple[str, re.Pattern[str]]] = [
    (
        "out-of-scope",
        re.compile(
            r"\b(out of scope|outside (the |this )?scope|beyond (the |this )?scope)\b",
            re.I,
        ),
    ),
    (
        "not-here",
        re.compile(
            r"\b(not|won'?t|will not|isn'?t|rather than)\b[^.!?\n]{0,60}"
            r"\b(fix|fixing|change|changing|touch|touching|address|addressing|handl\w+)\b"
            r"[^.!?\n]{0,60}"
            r"\b(here|now|this (branch|PR|change|plan)|on this branch|in this PR)\b",
            re.I,
        ),
    ),
    (
        "leave-for-later",
        re.compile(
            r"\b(leav(e|ing)|defer(red|ring)?|park(ed|ing)?|set(ting)? aside)\b[^.!?\n]{0,40}"
            r"\b(for (a )?(later|another|follow.?up|separate)|to a follow.?up)\b",
            re.I,
        ),
    ),
    (
        # "branch" and "commit" are deliberately absent. Measured: they matched
        # ordinary narration -- "each session works in its own worktree with its own
        # commit", "HEAD is now on a different branch" -- which is a statement about
        # mechanics, not a unit of deferred work. PR / ticket / bead / issue are.
        "separate-change",
        re.compile(
            r"\b(separate|its own|a different|another)\s+(PR|pull request|ticket|bead|issue)\b",
            re.I,
        ),
    ),
    (
        "someone-must-decide",
        re.compile(
            r"\b(needs? (a )?(decision|human decision)"
            r"|someone (needs to|should|must|has to)\s+(decide|choose|confirm|pick)"
            r"|Jonny (needs to|should|must) (decide|choose|confirm))\b",
            re.I,
        ),
    ),
]

# "Pre-existing" needs a tighter test than the other cues, because it is the most
# common word in this corpus and almost never a deferral. Measured: as a bare cue it
# fired 106 times, on stashes, research docs and refuted findings. It earns a nudge
# only when a DEFECT and an explicit statement of not-fixing appear beside it --
# "a pre-existing bug, deliberately not fixed" is a follow-up; "mirrors a pre-existing
# SQLite defect" is a refutation, and the two are otherwise indistinguishable here.
PRE_EXISTING = re.compile(r"\bpre.?exist(s|ing|ed)\b", re.I)
DEFECT = re.compile(
    r"\b(bug|defect|regression|breakage|crash|leak|race|deadlock|failure|broken|fails?|failing)\b",
    re.I,
)
NOT_FIXED = re.compile(
    r"\b(not fix\w*|didn'?t fix|do(es)? not fix|won'?t fix|without fixing|unfixed"
    r"|deliberately (not|did not|dropped)|left (unfixed|as.is|alone)"
    r"|not (fixed|addressed|handled|reported|filed)|no fix)\b",
    re.I,
)

# A work noun says "there is a thing". The conjunction is the signal.
WORK_NOUN = re.compile(
    r"\b(bug|defect|regression|breakage|crash|leak|race|deadlock|failure|fails?|failing|flaky"
    r"|broken|incorrect"
    r"|test|tests|coverage|assertion"
    r"|docs?|documentation|README|comment|typo|stale"
    r"|decision"
    r"|dead code|unreachable|duplicat\w+|refactor\w*|cleanup|tech(nical)? debt"
    r"|deprecat\w+|hard.?coded|workaround|hack|TODO|FIXME"
    r"|missing|unimplemented|not implemented)\b",
    re.I,
)

# Sentences the cues match for reasons that are never a follow-up. Both families here
# are measured failure modes: the assistant narrating the boundary of its own report,
# and the assistant explicitly saying something is NOT worth pursuing. Each reads as a
# deferral to a regex and as the opposite to a human.
NOT_A_DEFERRAL = re.compile(
    # The assistant narrating the boundary of its own report or plan.
    r"(out of scope [^.!?\n]{0,40}"
    r"(review|report|reporting|analysis|correctness|pass|command|skill|exercise|prompt)"
    # A scope declaration: "Out of scope: no metric, no holdout, ...".
    r"|out of scope:?\**\s*(no |none|nothing)"
    # An explicit refusal to follow up, which reads identically to a deferral.
    r"|not worth|no follow.?up|nothing (to (file|capture)|needs)|already (filed|captured|tracked|covered)"
    r"|rather than (a|its own|one of its own)? ?(ticket|bead|issue|follow.?up|PR)"
    r"|zero files touched|no files? (outside|beyond))",
    re.I,
)

# The assistant asking rather than deferring. "Want me to commit this as a separate PR
# now?" is an offer to do the work immediately; filing a bead for it is wrong.
ASKING = re.compile(
    r"(\?\s*$|^\s*\**(want me to|shall i|should i|do you want|would you like|let me know))",
    re.I,
)

# A cue inside a quotation is someone else's words -- a docstring, a requirements
# line, a prior agent's report being cited. Measured: two firings were the same
# docstring quoted back, "Step 4.2 ('missing executors'), explicitly out of scope here".
QUOTED_SPAN = re.compile(r"[\"“”][^\"“”]{15,}[\"“”]")

# Turns that already obeyed the rule, and turns that ARE the sweep, must not be
# nudged or re-surfaced. Both look the same from here: a bd write ran in the turn.
BD_WRITE = re.compile(r"\bbd\s+(create|q|quick)\b")
SWEEP_MARKER = re.compile(r"followup_capture\.py")

# Sentences that only *discuss* capture (this feature's own code, docs about the
# rule) trip every pattern above. Suppress the ones that are quoting rather than
# deferring.
# `--status deferred` is kept deliberately, even though bd 1.2.2 removed that flag
# and the capture rule now says `-s deferred`: transcripts still quote the old form
# when discussing the change. `-s deferred` is NOT added alongside it. This
# alternation suppresses the nudge, so every term added to it is a way for a real
# deferral to go unreported, and the new command form is already matched here by
# `agent-proposed`, `discovered-from` and `bd create "`.
QUOTING = re.compile(
    r"(agent-proposed|--status deferred|discovered-from|bd create \"|standing capture rule"
    r"|sweep-followups|followup_capture)",
    re.I,
)
FENCE = re.compile(r"```.*?```", re.S)


# --------------------------------------------------------------------------- state


def state_dir() -> str:
    """Watermark home. Deliberately outside ~/.claude and ~/beads-hq: both are pushed."""
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "state"
    )
    return os.path.join(base, "followup-capture")


def _state_path(session_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", session_id or "unknown")
    return os.path.join(state_dir(), f"{safe}.json")


def load_state(session_id: str) -> dict:
    try:
        with open(_state_path(session_id), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(session_id: str, state: dict) -> None:
    path = _state_path(session_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    os.replace(tmp, path)


def candidate_key(text: str) -> str:
    """Stable id for a candidate sentence, robust to whitespace and case drift.

    This is what makes a repeated sweep idempotent. It must NOT include the turn
    index: the same follow-up restated in a later turn has to collide with the
    earlier one, otherwise the sweep's own report re-files everything it just filed.
    """
    norm = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    norm = " ".join(norm.split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


# ----------------------------------------------------------------------- transcript


def read_tail(path: str, limit: int = TAIL_BYTES) -> list[dict]:
    """Parse the last `limit` bytes of a JSONL transcript into records.

    A partial first line is expected when the file is larger than the window and is
    dropped. Unparseable lines are skipped rather than raising -- a transcript being
    appended to while we read it is normal, not an error.
    """
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            if size > limit:
                fh.seek(size - limit)
                fh.readline()  # discard the partial record
            raw = fh.read()
    except OSError:
        return []
    out = []
    for line in raw.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def is_human_turn_start(rec: dict) -> bool:
    """True for a real user prompt, false for a tool result.

    Both arrive as type=user. The discriminator is promptSource, which tool results
    never carry. Verified against a live transcript on 2026-08-14: typed prompts have
    promptSource='typed' and origin={'kind':'human'}; tool results have neither and
    their content is a list of tool_result blocks.
    """
    if rec.get("type") != "user":
        return False
    if rec.get("isMeta"):
        return False
    return (
        bool(rec.get("promptSource"))
        or (rec.get("origin") or {}).get("kind") == "human"
    )


def split_turns(records: list[dict]) -> list[list[dict]]:
    """Group records into turns, each starting at a human prompt."""
    turns: list[list[dict]] = []
    for rec in records:
        if is_human_turn_start(rec) or not turns:
            turns.append([rec])
        else:
            turns[-1].append(rec)
    return turns


def assistant_prose(turn: list[dict]) -> str:
    """The assistant's user-visible text for a turn.

    Thinking blocks and tool output are excluded on purpose. Thinking is where the
    model reasons about hypotheticals it then rejects, and treating that as a
    deferral produces noise; tool output is someone else's words.
    """
    parts = []
    for rec in turn:
        if rec.get("type") != "assistant":
            continue
        content = (rec.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text") or "")
    return "\n".join(parts)


def _tool_inputs(turn: list[dict]):
    for rec in turn:
        if rec.get("type") != "assistant":
            continue
        content = (rec.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                yield json.dumps(block.get("input") or {})


def turn_wrote_a_bead(turn: list[dict]) -> bool:
    """True if a `bd create` / `bd q` ran anywhere in this turn."""
    return any(BD_WRITE.search(blob) for blob in _tool_inputs(turn))


def turn_is_a_sweep(turn: list[dict]) -> bool:
    """True if this turn ran the scanner, i.e. the turn IS the machinery.

    Excluding these is what stops sweep 2 from re-filing sweep 1's report, which
    necessarily repeats every follow-up sweep 1 just filed.
    """
    return any(SWEEP_MARKER.search(blob) for blob in _tool_inputs(turn))


def human_prose(turn: list[dict], limit: int = HUMAN_PROSE_LIMIT) -> str:
    """The human prompt that opened this turn, truncated.

    Scanned as well as the assistant's reply, because a deferral is just as often the
    user's: "that's a real bug but it's out of scope for this change" is a follow-up
    nobody has filed. Found by live test -- the assistant complied and summarised with
    "left unchanged as requested", which carries no deferral cue at all, so scanning
    only the reply missed a textbook case.

    Truncated because prompts routinely carry a pasted requirements document, and a
    scope table inside one is not this turn's deferral.
    """
    for rec in turn:
        if not is_human_turn_start(rec):
            continue
        content = (rec.get("message") or {}).get("content")
        if isinstance(content, str):
            return content[:limit]
        if isinstance(content, list):
            parts = [
                b.get("text") or ""
                for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            ]
            return "\n".join(parts)[:limit]
    return ""


def turn_filed_already(turn: list[dict]) -> bool:
    """Hook-only test: this turn already obeyed the rule, so do not nudge it.

    NOT used by the sweep. A long agentic turn routinely files one follow-up and
    defers five more; treating "filed something" as "filed everything" would lose the
    five. Measured on a real session: one `bd create` in a 40-tool-call turn hid the
    entire turn from the sweep, which is the exact failure the sweep exists to prevent.
    """
    return turn_wrote_a_bead(turn) or turn_is_a_sweep(turn)


def turn_id(turn: list[dict]) -> str:
    for rec in turn:
        if rec.get("uuid"):
            return str(rec["uuid"])
    return ""


def sentences(text: str) -> list[str]:
    """Sentence-ish split with fenced code removed.

    Code fences are dropped before splitting because a diff or a config sample
    containing the word TODO is not the assistant deferring anything.
    """
    text = FENCE.sub(" ", text)
    text = re.sub(r"`[^`\n]*`", " ", text)
    out = []
    for chunk in re.split(r"(?<=[.!?])\s+|\n+", text):
        chunk = " ".join(chunk.split())
        if 20 <= len(chunk) <= 400:
            out.append(chunk)
    return out


def match_sentence(sentence: str) -> str | None:
    """Name of the pattern this sentence trips, or None.

    Tier 1 stands alone. A cue needs a work noun beside it. Anything the
    NOT_A_DEFERRAL or QUOTING families claim is rejected before either tier runs.
    """
    if len(sentence.split()) < 6:
        return None  # headings and list stubs carry no deferral
    if (
        QUOTING.search(sentence)
        or NOT_A_DEFERRAL.search(sentence)
        or ASKING.search(sentence)
    ):
        return None
    # Strip quoted spans before matching, so a cue that only appears inside a citation
    # no longer counts. The sentence is still reported in full if something else fires.
    probe = QUOTED_SPAN.sub(" ", sentence)
    for name, rx in TIER1:
        if rx.search(probe):
            return name
    if PRE_EXISTING.search(probe) and DEFECT.search(probe) and NOT_FIXED.search(probe):
        return "pre-existing-unfixed"
    if not WORK_NOUN.search(probe):
        return None
    for name, rx in CUES:
        if rx.search(probe):
            return name
    return None


def find_candidates(turn: list[dict]) -> list[dict]:
    """Deferral-shaped sentences in one turn, from the reply and from the prompt."""
    found: list[dict] = []
    seen: set[str] = set()
    for source, text in (
        ("assistant", assistant_prose(turn)),
        ("user", human_prose(turn)),
    ):
        for sentence in sentences(text):
            name = match_sentence(sentence)
            if not name:
                continue
            key = candidate_key(sentence)
            if key in seen:
                continue
            seen.add(key)
            found.append(
                {"key": key, "pattern": name, "source": source, "text": sentence}
            )
    return found


def queue_present() -> bool:
    """Cheap check that there is a Beads queue to file into."""
    if os.environ.get("BEADS_DIR"):
        return True
    return os.path.isdir(os.path.join(os.path.expanduser("~"), "beads-hq", ".beads"))


# ------------------------------------------------------------------------ entrypoints


def cmd_hook() -> int:
    """Stop-hook entry. Silent unless the turn deferred something and filed nothing."""
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if not isinstance(payload, dict):
        return 0

    # Never loop. Claude Code sets this once a Stop hook has already blocked.
    if payload.get("stop_hook_active"):
        return 0

    transcript = payload.get("transcript_path") or ""
    session_id = payload.get("session_id") or ""
    if not transcript or not os.path.isfile(transcript) or not queue_present():
        return 0

    turns = split_turns(read_tail(transcript))
    if not turns:
        return 0
    turn = turns[-1]

    if turn_filed_already(turn):
        return 0

    state = load_state(session_id)
    seen: dict = state.get("seen") or {}
    nudges: dict = state.get("nudges") or {}

    fresh = [c for c in find_candidates(turn) if c["key"] not in seen]
    if not fresh:
        return 0

    tid = turn_id(turn)
    if nudges.get(tid, 0) >= MAX_NUDGES_PER_TURN:
        return 0
    nudges[tid] = nudges.get(tid, 0) + 1
    state["nudges"] = nudges
    state["session_id"] = session_id
    save_state(session_id, state)

    quoted = "\n".join(
        f'  - [said by the {c.get("source", "assistant")}] "{c["text"]}"'
        for c in fresh[:5]
    )
    reason = (
        "Follow-up capture rule (~/.claude/CLAUDE.md): this turn deferred work but no "
        "`bd create` ran. Sentences that read as deferrals:\n"
        f"{quoted}\n\n"
        "For each one that is a real follow-up somebody would want later, file it now:\n"
        "  TITLE=$(cat <<'BD_TITLE'\n"
        "  <what you noticed - verbatim, any characters>\n"
        "  BD_TITLE\n"
        "  )\n"
        '  ID=$(bd create "$TITLE" -p <0-4> -l agent-proposed \\\n'
        "    --deps discovered-from:<current-id> --silent)\n"
        '  [ -n "$ID" ] || { echo "bd create failed - follow-up NOT filed"; exit 1; }\n'
        '  bd update "$ID" -s deferred\n'
        "Run that as ONE shell call: $ID does not survive between tool calls, and\n"
        '`bd update "" -s deferred` prints an error and then exits 0. The heredoc is\n'
        "load-bearing: the titles this hook quotes are somebody else's words, and\n"
        "inline they would be interpolated, so backticks and $(...) in them would run.\n"
        "Meet the description bar: a stranger must be able to reproduce it without asking "
        "Jonny anything. Rescue evidence that lives only in /private/tmp or your context to a "
        "durable path first, and record that path on the bead.\n\n"
        "A deferral the USER stated counts, and counts fully. Do not skip it on the grounds "
        "that they already know or that filing it back at them would be noise -- the queue "
        "exists precisely so that nobody has to remember, and 'Jonny mentioned it once in "
        "chat' is the exact thing it is built to stop losing. Over-capture is cheap; "
        "under-capture is the failure mode.\n"
        "Genuine reasons to skip: you went on to do it in this session, it is already in the "
        "queue, or the sentence is you describing the boundary of your own report rather than "
        "deferring real work.\n"
        "If none is a real follow-up, say which of those reasons applies, in one line, and "
        "stop. Do not restart the task you just finished."
    )
    json.dump({"decision": "block", "reason": reason}, sys.stdout)
    sys.stdout.write("\n")
    return 0


def resolve_transcript(cwd: str | None = None) -> str:
    """Newest transcript for this working directory, or "" if there is none.

    Claude Code stores transcripts at ~/.claude/projects/<mangled-cwd>/<session>.jsonl,
    where the mangling replaces every "/" and "." with "-".

    Newest-by-mtime is the right choice here specifically because the caller is the
    live session: it is being appended to as we look. The known trap is elsewhere --
    the requirements doc records that resolving a session by title or by a derived
    claude_session_id silently returns a *different* session's transcript when two
    sessions share a working directory. That failure does not apply to "which file was
    written most recently", but it is why this does not try to match on a session id.
    """
    cwd = os.path.abspath(cwd or os.getcwd())
    mangled = cwd.replace("/", "-").replace(".", "-")
    proj = os.path.join(os.path.expanduser("~"), ".claude", "projects", mangled)
    try:
        entries = [
            os.path.join(proj, f)
            for f in os.listdir(proj)
            if f.endswith(".jsonl") and os.path.isfile(os.path.join(proj, f))
        ]
    except OSError:
        return ""
    if not entries:
        return ""
    return max(entries, key=os.path.getmtime)


def _resolve_transcript(args: argparse.Namespace) -> str:
    if args.transcript:
        return args.transcript
    found = resolve_transcript()
    if not found:
        raise SystemExit(
            "no transcript found for this working directory; pass --transcript explicitly"
        )
    return found


def cmd_resolve(_args: argparse.Namespace) -> int:
    path = resolve_transcript()
    if not path:
        sys.stderr.write("no transcript found for this working directory\n")
        return 1
    sys.stdout.write(path + "\n")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    """Print un-swept candidates for /sweep-followups, and stage the new watermark."""
    transcript = _resolve_transcript(args)
    session_id = args.session_id or os.path.splitext(os.path.basename(transcript))[0]
    state = load_state(session_id)
    seen: dict = state.get("seen") or {}
    cursor = state.get("cursor") or ""

    turns = split_turns(read_tail(transcript, limit=args.max_bytes))

    # Everything up to and including the cursor turn was swept before. If the cursor
    # is no longer in the window (long session, small window) fall back to scanning
    # what we have -- the seen-set still prevents re-filing.
    start = 0
    if cursor:
        for i, turn in enumerate(turns):
            if turn_id(turn) == cursor:
                start = i + 1
                break

    # No sweep-turn exclusion here, deliberately. `commit` sets the cursor to the turn
    # the sweep itself ran in, so the sweep's own report is already below the cursor on
    # the next run. Excluding "any turn that ran the scanner" as well was measured to
    # swallow an entire working turn in a long agentic session -- one that had run the
    # scanner once and deferred real work in the same turn.
    out = []
    for turn in turns[start:]:
        fresh = [c for c in find_candidates(turn) if c["key"] not in seen]
        if not fresh:
            continue
        entry = {"turn": turn_id(turn), "candidates": fresh}
        if turn_wrote_a_bead(turn):
            # Deliberately still surfaced. The turn filed SOMETHING, not necessarily
            # this. Check the queue before filing, since bd will not deduplicate.
            entry["turn_already_filed_a_bead"] = True
        out.append(entry)

    if turns:
        state["pending_cursor"] = turn_id(turns[-1])
        state["session_id"] = session_id
        save_state(session_id, state)

    json.dump(
        {
            "session_id": session_id,
            "turns_scanned": len(turns) - start,
            "already_swept_turns": start,
            "suppressed_keys": len(seen),
            "unfiled": out,
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_commit(args: argparse.Namespace) -> int:
    """Advance the watermark. Every key passed here stops being offered again.

    `--filed key=bead-id` for what became a bead, `--dismissed key` for what was
    judged not worth one. Both are recorded: a candidate re-offered every sweep is
    the same failure as one filed twice.
    """
    session_id = args.session_id
    state = load_state(session_id)
    seen: dict = state.get("seen") or {}
    now = int(time.time())

    for item in args.filed or []:
        key, _, bead = item.partition("=")
        seen[key.strip()] = {
            "bead": bead.strip() or None,
            "at": now,
            "outcome": "filed",
        }
    for key in args.dismissed or []:
        seen[key.strip()] = {"bead": None, "at": now, "outcome": "dismissed"}

    state["seen"] = seen
    if state.get("pending_cursor"):
        state["cursor"] = state.pop("pending_cursor")
    state["nudges"] = {}  # a completed sweep clears the hook's nudge budget
    state["session_id"] = session_id
    save_state(session_id, state)

    json.dump(
        {
            "session_id": session_id,
            "cursor": state.get("cursor", ""),
            "suppressed_keys": len(seen),
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Measure fire rate and per-pattern hits over a corpus of real transcripts."""
    from collections import Counter

    per_pattern: Counter[str] = Counter()
    turns_total = 0
    turns_fired = 0
    turns_filed = 0
    files = 0
    samples: list[tuple[str, str]] = []
    t0 = time.time()

    for path in args.transcripts:
        if not os.path.isfile(path):
            continue
        files += 1
        for turn in split_turns(read_tail(path, limit=args.max_bytes)):
            turns_total += 1
            if turn_filed_already(turn):
                turns_filed += 1
                continue
            cands = find_candidates(turn)
            if args.only:
                cands = [c for c in cands if c["pattern"] == args.only]
            if cands:
                turns_fired += 1
                for c in cands:
                    per_pattern[c["pattern"]] += 1
                    if len(samples) < args.samples:
                        samples.append(
                            (c["pattern"], c.get("source", "assistant"), c["text"])
                        )

    elapsed = time.time() - t0
    if not files:
        # "0% of nothing" and "0% of real data" serialise identically, and a reader
        # skimming for fire_rate_pct will not notice files:0. Say it on stderr so the
        # two are distinguishable without having to know to look.
        sys.stderr.write(
            "warning: no transcripts matched, so every count below is 0 because nothing "
            "was scanned -- not because the detector found nothing. Check the glob.\n"
        )
    json.dump(
        {
            "files": files,
            "turns_total": turns_total,
            "turns_with_bd_write_or_sweep": turns_filed,
            "turns_that_would_nudge": turns_fired,
            "fire_rate_pct": round(100.0 * turns_fired / turns_total, 2)
            if turns_total
            else 0.0,
            "per_pattern_hits": dict(per_pattern.most_common()),
            "wall_seconds_total": round(elapsed, 3),
            "ms_per_transcript": round(1000.0 * elapsed / files, 2) if files else 0.0,
            "samples": [
                {"pattern": p, "source": src, "text": t} for p, src, t in samples
            ],
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="followup_capture.py", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("hook", help="Stop-hook entry point (reads hook JSON on stdin)")

    sub.add_parser(
        "resolve", help="print this working directory's newest transcript path"
    )

    p_scan = sub.add_parser("scan", help="print un-swept candidates as JSON")
    p_scan.add_argument(
        "--transcript", default="", help="default: auto-resolve from cwd"
    )
    p_scan.add_argument("--session-id", default="")
    p_scan.add_argument("--max-bytes", type=int, default=4 * 1024 * 1024)

    p_commit = sub.add_parser("commit", help="advance the watermark")
    p_commit.add_argument("--session-id", required=True)
    p_commit.add_argument("--filed", action="append", metavar="KEY=BEAD-ID")
    p_commit.add_argument("--dismissed", action="append", metavar="KEY")

    p_report = sub.add_parser("report", help="measure fire rate over real transcripts")
    p_report.add_argument("transcripts", nargs="+")
    p_report.add_argument("--max-bytes", type=int, default=4 * 1024 * 1024)
    p_report.add_argument("--samples", type=int, default=12)
    p_report.add_argument(
        "--only", default="", help="show samples for one pattern only"
    )

    args = ap.parse_args(argv)
    if args.cmd == "hook":
        return cmd_hook()
    if args.cmd == "resolve":
        return cmd_resolve(args)
    if args.cmd == "scan":
        return cmd_scan(args)
    if args.cmd == "commit":
        return cmd_commit(args)
    return cmd_report(args)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException:
        # This runs at the end of every turn in every session. A traceback on stderr
        # would be noise in ~34 repos, and a non-zero exit would surface as a hook
        # failure. Failing silent is the correct trade for a best-effort reminder.
        sys.exit(0)
