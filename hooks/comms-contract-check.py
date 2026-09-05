#!/usr/bin/env python3
"""Enforce the conductor communication contract on outgoing messages.

Contract: ~/.claude/docs/conductor-communication-contract.md
Notes:    ~/.claude/docs/conductor-communication-check.md
Bead:     jbrooksbartlett-5r44

WHAT THIS IS FOR
The contract's core rule - "a bare identifier from the conductor is never
acceptable" - has been written twice (2026-08-14, re-issued 2026-08-15) and
broken twice. Jonny chose "templates plus an automatic check" over a self-check
for a stated reason: a self-check is the same kind of thing as the rule that
already failed. He also declined to be the safety net. So this file is the only
thing standing between the contract and a third failure.

HOW IT RUNS
As a Stop hook. The Stop payload carries `last_assistant_message` - the exact
outgoing text - so no transcript parsing is needed. Returning
{"decision": "block", "reason": ...} sends the violations back to the model,
which then re-issues a corrected message.

Honest limitation, verified empirically: the Stop hook fires AFTER the text has
been streamed to the terminal. This corrects the record inside the same turn; it
does not prevent the first display. No hook event can gate assistant text before
display - only tool calls can be gated pre-display (see jbrooksbartlett-g67x).

SELF-SCOPING
This hook is registered user-wide in ~/.claude/settings.json, so it fires in
every session. It decides for itself whether it applies - conductor sessions
only - and exits silently and immediately otherwise, before doing any work.
"""

from __future__ import annotations

import bisect
import json
import os
import re
import shutil
import subprocess
import sys
from functools import lru_cache
from collections.abc import Callable
from typing import Any, NamedTuple, TextIO

# --------------------------------------------------------------------------
# Scope
# --------------------------------------------------------------------------

# The conductor runs in agent-deck's conductor directory. Only its messages go
# to Jonny under this contract; every other session exits before doing work.
CONDUCTOR_PATH_MARKER = os.path.join(".local", "share", "agent-deck", "conductor")

# `bd` and `agent-deck` live in Homebrew's prefix, which is NOT on the minimal
# PATH a hook can inherit. Verified 2026-08-18: `env -i sh -c 'command -v bd'`
# finds nothing.
EXTRA_PATH_DIRS = ("/opt/homebrew/bin", "/usr/local/bin")

# Without BEADS_DIR, `bd list --json` exits non-zero with "no beads database
# found" - which would hand this check an EMPTY id list and pass every message.
# ~/.zshenv exports it, but a hook is not a login shell.
DEFAULT_BEADS_DIR = os.path.join(os.path.expanduser("~"), "beads-hq", ".beads")

# --------------------------------------------------------------------------
# Shared patterns and vocabularies
# --------------------------------------------------------------------------

FULL_FORM_RE = re.compile(
    r"(?<![A-Za-z0-9_-])jbrooksbartlett-[a-z0-9]+(?:\.[0-9]+)?(?![A-Za-z0-9_-])"
)
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'/-]*")
MARKUP_RE = re.compile(r"[`*_|#>\[\]()]")
FENCE_RE = re.compile(r"```.*?(?:```|\Z)", re.DOTALL)
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
TABLE_SEPARATOR_RE = re.compile(r"\|[\s:|-]*\|?")
PRECEDING_WORD_RE = re.compile(r"([A-Za-z]+)\W*$")

# Words that introduce an identifier without naming it. "bead `280`" supplies no
# more meaning than `280` alone, so these never count toward a description.
LEAD_WORDS = frozenset(
    """
bead beads issue issues session sessions pr prs id ids commit branch ticket worker
and or the a an in on at of to for is was it its this that with from by as closed open
""".split()
)

# The narrower "an identifier is being introduced here" set. A subset of
# LEAD_WORDS, kept separate because the two answer different questions: this one
# means "treat the next token as an id", LEAD_WORDS means "does not count as a
# description".
ID_LEAD_WORDS = frozenset("bead beads session issue pr id ticket".split())

# Commands are copy-paste targets, not prose he has to understand. Contract
# template 8.3 ends every dispatch with `agent-deck session output <id> -q`, so
# without this exemption the templates themselves would fail.
COMMAND_WORDS = frozenset(
    """
bd agent-deck git gh tmux cd claude python3 python bash sh jq curl make npm uv open cat less
""".split()
)

# Labels that mark a bare handle rather than prose, as in template 8.3's
# "Watch it: session <name> | ...".
HANDLE_LABELS = frozenset("watch session tmux branch worktree pr url chirp".split())

# A first mention needs a real description; a later mention in the same message
# may drop to a short plain name (contract section 2). Both still need the name
# BOUND to the identifier - "c39 flagged it" is prose next to a bare id, not a
# name for it.
FIRST_MENTION_MIN_WORDS = 3
REPEAT_MENTION_MIN_WORDS = 2

# --------------------------------------------------------------------------
# Habit words (contract section 3)
# --------------------------------------------------------------------------

# Jonny raised these himself: "I noticed the agent using a lot of terms like
# provenance and load-bearing. I don't really understand these terms." He was
# offered outright replacement and declined it, choosing "keep the precise word,
# always gloss it". So these are not banned - they are banned UNGLOSSED.
#
# Maintained here, per the bead, rather than read from the contract file (which
# is still untracked in ~/.claude and so cannot be depended on).
#
# Each word carries its OWN matching rules, so a word that needs part-of-speech
# sensitivity is a data row rather than a second code path. "surface" is the only
# one that needs it today - "the surface area" is ordinary English, "surface the
# finding" is the habit - and when Jonny names the next such word it is one row.
NOUN_LEADINS = frozenset("the a an its this that his her their our on per".split())

# Words that, when they follow an ambiguous noun/verb habit word, signal that the
# habit word is a noun (not a verb taking a direct object). A verb taking a direct
# object is followed by a noun phrase (determiner, adjective, noun); a noun is
# followed by a preposition, conjunction, clause starter, or another verb where the
# noun is the subject.
_NOUN_FOLLOWING = frozenset(
    # Prepositions
    "of in on for with from by to at into through between about after before "
    "against over under across behind along within without upon toward towards "
    "per as like since until during "
    # Conjunctions
    "and or but nor yet so "
    # Clause starters and relative pronouns
    "that which who whom whose where when while if although though because unless "
    "whether "
    # Common verbs (the habit word would be the subject of these)
    "is are was were has have had do does did can could will would shall should "
    "may might must need needs "
    # Subject and indefinite pronouns (typically start a relative clause)
    "i you he she we they "
    "nobody somebody everybody everyone anyone someone "
    "nothing something everything anything "
    "whoever whatever whichever".split()
)


def _following_word(text: str, pos: int) -> str:
    """The first alphabetic word after pos, within the same clause.

    WORD_RE matches apostrophes and hyphens, so contractions like "isn't" come
    back whole. Truncate at the first non-alpha so the base form ("isn") still
    matches the set entries ("is", "are", etc.). The truncation is safe: no
    entry in _NOUN_FOLLOWING contains an apostrophe or hyphen.
    """
    m = WORD_RE.search(text, pos)
    if not m or m.start() - pos > 30:
        return ""
    gap = text[pos:m.start()]
    if any(c in gap for c in ".!?;,\n"):
        return ""
    raw = m.group(0).lower()
    cut = next((i for i, c in enumerate(raw) if not c.isalpha()), len(raw))
    return raw[:cut] if cut > 0 else raw


def _is_noun_usage(masked: str, start: int, end: int,
                   skip_after: frozenset[str]) -> bool:
    """Determine if an ambiguous habit word is used as a noun rather than a verb.

    Returns True (skip) when the context suggests noun usage, False (flag) when
    it suggests verb usage. Called only for habit words with a non-empty
    skip_after set -- currently only "surface".

    COST ASYMMETRY (jbrooksbartlett-7qau): a false positive (flagging a noun,
    blocking a correct message) costs a re-send and erodes trust in the check.
    A false negative (missing a verb) is minor. Unambiguous verb forms (-ing,
    -ed) always flag. Ambiguous forms (base, plural) require the ABSENCE of
    noun evidence to flag.
    """
    matched = masked[start:end].lower()

    if _preceding_word(masked, start) in skip_after:
        return True

    if matched.endswith(("ing", "ed")):
        return False

    if end + 1 < len(masked) and masked[end] == "-" and masked[end + 1].isalpha():
        return True

    line_start = masked.rfind("\n", 0, start) + 1
    line_head = masked[line_start:start].lstrip()
    if line_head.startswith(("#", ">")):
        return True

    fw = _following_word(masked, end)
    if not fw:
        return True
    if fw in _NOUN_FOLLOWING:
        return True

    return False


# Stored as templates and rendered once per occurrence in check_habit_words. An
# f-string cannot be used here: it would evaluate at definition time, before the
# matched form and the word are known.
GLOSS_REMEDY = (
    'habit word "{seen}" used without a gloss. Keep the word if it is the most precise one, '
    'but explain it in brackets - "{seen} (what it means in his terms)".'
)
VERB_REMEDY = (
    'habit word "{seen}" used as a verb without a gloss. Prefer a plain verb here - '
    '"found", "raised", "brought up" - or gloss it.'
)


def _habit_pattern(word: str) -> re.Pattern[str]:
    """Match a habit word and its inflections.

    The earlier version allowed only `(?:s|ly)?`, which meant "The veto stands"
    was flagged while "He vetoed it" and "He vetoes it" were not - the noun
    caught, the verb habit missed. Words ending in "e" drop it before a suffix so
    "surface" reaches "surfacing" rather than "surfaceing".
    """
    if " " in word or "-" in word:
        return _phrase_habit_pattern(word)
    return _inflected_habit_pattern(word)


def _phrase_habit_pattern(word: str) -> re.Pattern[str]:
    """A multi-word or hyphenated habit word matches as a fixed phrase."""
    return re.compile(
        r"(?<![A-Za-z-])" + re.escape(word) + r"(?:es|s)?(?![A-Za-z])",
        re.IGNORECASE,
    )


def _inflected_habit_pattern(word: str) -> re.Pattern[str]:
    """A single-word habit word matches its stem plus any inflection."""
    if word.endswith("e"):
        stem, suffixes = word[:-1], ("e", "es", "ed", "ing", "ely")
    else:
        stem, suffixes = word, ("", "s", "es", "ed", "ing", "ly", "ally")
    body = "|".join(sorted(suffixes, key=len, reverse=True))
    return re.compile(
        r"(?<![A-Za-z-])" + re.escape(stem) + r"(?:" + body + r")(?![A-Za-z])",
        re.IGNORECASE,
    )


class HabitWord(NamedTuple):
    word: str
    pattern: re.Pattern[str]
    skip_after: frozenset[str]  # preceding words that make this an innocent usage
    remedy: str


HABIT_WORDS = tuple(
    HabitWord(word, _habit_pattern(word), skip_after, remedy)
    for word, skip_after, remedy in (
        ("provenance", frozenset(), GLOSS_REMEDY),
        ("load-bearing", frozenset(), GLOSS_REMEDY),
        ("orthogonal", frozenset(), GLOSS_REMEDY),
        ("blast radius", frozenset(), GLOSS_REMEDY),
        ("falsifier", frozenset(), GLOSS_REMEDY),
        ("affordance", frozenset(), GLOSS_REMEDY),
        ("cadence", frozenset(), GLOSS_REMEDY),
        ("veto", frozenset(), GLOSS_REMEDY),
        ("idempotent", frozenset(), GLOSS_REMEDY),
        # Contract section 3 records that the conductor used "load-bearing" twice
        # and "asymmetric" once inside the interview that agreed the contract.
        ("asymmetric", frozenset(), GLOSS_REMEDY),
        # Listed in the bead as a verb only.
        ("surface", NOUN_LEADINS, VERB_REMEDY),
    )
)

# --------------------------------------------------------------------------
# The other four kinds of identifier (contract section 1)
# --------------------------------------------------------------------------

# Contract section 1 lists six kinds, not just bead ids. These are safely
# matchable by SHAPE, so they need no live list:
#   PR numbers      #146
#   commit hashes   9efc494  - 7-40 hex chars WITH at least one digit, which
#                              excludes every English word (no word has digits)
#                              and so cannot collide the way a bare suffix does
#   constants       NON_OWNED_CONFIG_DENIED
SHAPE_KINDS = (
    ("pr", re.compile(r"(?<![A-Za-z0-9_])#[0-9]{1,6}(?![A-Za-z0-9_])")),
    (
        "commit",
        re.compile(
            r"""
            (?<![A-Za-z0-9_-])   # not glued to a longer token
            (?=[0-9a-f]*[0-9])   # must contain at least one digit
            [0-9a-f]{7,40}
            (?![A-Za-z0-9_-])
            """,
            re.VERBOSE,
        ),
    ),
    (
        "constant",
        re.compile(
            r"(?<![A-Za-z0-9_])[A-Z][A-Z0-9]{2,}(?:_[A-Z0-9]+)+(?![A-Za-z0-9_])"
        ),
    ),
)

# File paths and function names are the one kind deliberately narrowed. The
# conductor writes `hooks/comms-contract-check.py` many times a session, and
# demanding a description at every mention is how a check earns itself a
# disabling. So a path is flagged only when it stands completely alone - in a
# table cell or as a whole bullet - which is the shape that actually left him
# with nothing to read. Tracked for widening in jbrooksbartlett-0vfp.
# The leading segment is BOUNDED and lazy. An unbounded greedy `+` before a
# mandatory `/` is quadratic - the engine retries the slash search from every
# reduced prefix at every offset. Measured before this fix: 200,000 characters of
# "a.a.a..." containing no slash took 17.3 seconds, on a hook that runs every turn.
PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_/-])[A-Za-z0-9_.-]{1,64}?/[A-Za-z0-9_./-]{1,128}\.[a-z]{1,4}"
    r"(?::[0-9]+)?(?![A-Za-z0-9_-])"
)

# `compose.ts` is contract section 1's own example of an opaque identifier, and a
# path pattern requiring a "/" cannot see it. The name must be 2+ characters of
# [A-Za-z0-9_-] with no dot, so "e.g." does not qualify as name-plus-extension.
BARE_FILENAME_RE = re.compile(
    r"(?<![A-Za-z0-9_/.-])[A-Za-z0-9_-]{2,}\.[a-z]{2,4}(?::[0-9]+)?(?![A-Za-z0-9_-])"
)

KIND_LABEL = {
    "bead": "bead id",
    "session": "session name",
    "pr": "PR number",
    "commit": "commit hash",
    "constant": "error code or constant",
    "path": "file path",
}


class Violation(NamedTuple):
    """One contract breach, with enough context for the model to fix it.

    A NamedTuple like its siblings Found and HabitWord. Callers pass an
    already-stripped line; there are three construction sites.
    """

    kind: str
    token: str
    line_no: int
    line: str
    detail: str

    def render(self) -> str:
        # Windowed around the token rather than sliced from column 0. On a long
        # line the excerpt could otherwise be real text that does not contain the
        # thing being flagged, which is worse than no excerpt.
        excerpt = self.line
        if len(excerpt) > 160:
            at = excerpt.find(self.token)
            if at > 80:
                excerpt = "..." + excerpt[at - 80 :]
            excerpt = excerpt[:160]
        return f"  line {self.line_no}: {self.detail}\n    > {excerpt}"


class Found(NamedTuple):
    """One identifier occurrence located in the text."""

    start: int
    end: int
    token: str
    kind: str


# --------------------------------------------------------------------------
# Live identifier lists
# --------------------------------------------------------------------------


def _run(cmd: list[str]) -> str | None:
    """Run a command with a PATH and BEADS_DIR a hook can rely on."""
    env = dict(os.environ)
    inherited = [p for p in env.get("PATH", "").split(os.pathsep) if p]
    # PREPENDED, not appended. Appending trusts the tail of an inherited PATH, so
    # any earlier directory holding something called `bd` would win - the textbook
    # PATH-hijack shape. Resolving absolutely is better still, so try that first.
    env["PATH"] = os.pathsep.join(list(EXTRA_PATH_DIRS) + inherited)
    env.setdefault("BEADS_DIR", DEFAULT_BEADS_DIR)
    resolved = shutil.which(cmd[0], path=env["PATH"])
    argv = [resolved, *cmd[1:]] if resolved else cmd
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=20, env=env)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


BD_LIST_CMD = ["bd", "list", "--all", "--limit", "0", "--json"]
AGENT_DECK_LIST_CMD = ["agent-deck", "list", "--json"]


def _pull(cmd: list[str], populate: Callable[[Any], None], missed: str) -> str | None:
    """Run one live source and populate from it. Returns a degradation, or None.

    Shared so the two sources cannot drift: they previously repeated the same
    run / report-missing / parse / report-unparseable skeleton, differing only in
    the populate step, which is the shape where one branch's except clause gets
    tightened and the other is forgotten.
    """
    raw = _run(cmd)
    printable = " ".join(cmd)
    if raw is None:
        return f"could not run `{printable}` ({missed})"
    try:
        populate(json.loads(raw))
    except (ValueError, AttributeError, TypeError):
        return f"`{printable}` returned unparseable output ({missed})"
    return None


def load_live_identifiers() -> tuple[dict[str, str], list[str]]:
    """Pull bead ids and session names live. Never cached - session names rename
    themselves (`sb-detail-panel-build` became
    `feature-feat-2026-08-18-detail-panel-d1`), so a cached list goes stale.

    Returns (identifier -> kind, degradations). A degradation means one source
    could not be read, and the caller must surface it rather than pass silently -
    the live list is the ONLY thing that catches a bare short suffix.

    On the bd flags: `--all` because `bd list` hides CLOSED beads by default and a
    status report is largely ABOUT closed work. Measured 2026-08-18, the default
    view held 450 distinct suffixes against 559 with `--all`, and the difference
    included `cyi`, `c39` and `9oi` - three of the bare ids Jonny was actually
    shown on 2026-08-15. `--limit 0` because `bd list` caps at 50 by default; the
    JSON view does not appear to apply the cap, but an uncapped listing is the
    difference between a checked absence and an assumed one.
    """
    identifiers: dict[str, str] = {}

    def take_beads(records: Any) -> None:
        for rec in records:
            bead_id = rec.get("id", "")
            if not bead_id:
                continue
            identifiers[bead_id] = "bead"
            # The bare suffix is what he was actually shown on 2026-08-15 (`cyi`,
            # `6eh`, `c39`). It must be matched against this live list and never by
            # shape - a 3-char token pattern matches ordinary English constantly.
            if "-" in bead_id:
                identifiers.setdefault(bead_id.split("-", 1)[1], "bead")

    def take_sessions(records: Any) -> None:
        if isinstance(records, dict):
            records = records.get("sessions", [])
        for rec in records:
            for field in ("title", "name", "tmux_session", "id"):
                value = rec.get(field)
                if isinstance(value, str) and len(value) >= 3:
                    identifiers.setdefault(value, "session")

    degradations = [
        d
        for d in (
            _pull(
                BD_LIST_CMD, take_beads, "bare short-suffix bead ids were NOT checked"
            ),
            _pull(AGENT_DECK_LIST_CMD, take_sessions, "session names were NOT checked"),
        )
        if d is not None
    ]
    return identifiers, degradations


# --------------------------------------------------------------------------
# False-positive control
# --------------------------------------------------------------------------

# Bead suffixes are 3-4 characters, so they collide with ordinary English and
# with bare numbers. Measured against the live queue on 2026-08-18: of 450
# beads, `part` is a real suffix (`jbrooksbartlett-part`) and eleven suffixes are
# pure digits (`280`, `201`, `848`, `867`, ...). In six real 2026-08-15 conductor
# messages, all three occurrences of "part" were ordinary English ("the part
# that matters") and every genuine bead reference was written inside backticks.
#
# So there are two tiers:
#   - in an identifier context (backticks, bold, after a lead word, alone in a
#     table cell) a suffix from the live list is always an identifier;
#   - in plain prose it is one only if it could not plausibly be an English word
#     or a bare number.
#
# The English test is the system dictionary, not a hand-kept list: `bd` generates
# ids outside this repo, so the next word-shaped suffix it emits would otherwise
# turn this check into a false-positive machine until someone edited a literal.
# TECHNICAL_WORDS carries the non-dictionary tokens that must still be treated as
# risky, and doubles as the offline fallback when no dictionary is installed.
DICTIONARY_PATHS = ("/usr/share/dict/words", "/usr/dict/words")

TECHNICAL_WORDS = frozenset(
    """
env dir api cli url uri sdk cwd tmp src lib bin doc dev ops repo json yaml toml
csv sql http html css npm uid gid pid ttl dsn jwt ssh ssl tls dns cpu ram gpu
""".split()
)


@lru_cache(maxsize=1)
def _load_english_words() -> frozenset[str]:
    """Load the system dictionary once, lazily.

    Costs ~36ms for ~234k words, paid only inside a conductor session and only
    when a candidate token could plausibly be a word. Returns an EMPTY set when no
    dictionary is installed, falling back to TECHNICAL_WORDS alone - a much smaller
    substitute, so the precision the docs describe does not hold there.
    """
    for path in DICTIONARY_PATHS:
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                return frozenset(line.strip().lower() for line in fh if line.strip())
        except OSError:
            continue
    return frozenset()


def _is_english_word(token: str) -> bool:
    """True if this looks like an ordinary English word rather than an identifier."""
    if len(token) < 3 or not token.isalpha():
        return False
    lowered = token.lower()
    return lowered in TECHNICAL_WORDS or lowered in _load_english_words()


def _is_inside_own_gloss(masked: str, start: int) -> bool:
    """True only when this habit word is the term a parenthetical is defining.

    The earlier version excused ANY habit word immediately after an open bracket,
    whichever word's gloss that bracket belonged to. So in "The load-bearing
    (provenance-based reasoning) agreement", "provenance" collected a free pass off
    the back of load-bearing's gloss. The bracket now has to be defining this same
    word for the exemption to apply.
    """
    head = masked[:start].rstrip()
    if not head.endswith("("):
        return False
    before_bracket = head[:-1].rstrip()
    return _preceding_word(before_bracket, len(before_bracket)) == _preceding_word(
        masked, _word_end(masked, start)
    )


def _word_end(text: str, start: int) -> int:
    """End offset of the word beginning at `start`."""
    m = re.compile(r"[A-Za-z-]+").match(text, start)
    return m.end() if m else start


def _is_risky_bare_token(token: str) -> bool:
    """True if this token could plausibly be ordinary prose rather than an id."""
    if token.isdigit() or len(token) < 3:
        return True
    return _is_english_word(token)


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------


class LineIndex:
    """Offset -> (line number, whole line, column), precomputed once per message.

    Resolving each offset independently with `text.count("\n", 0, pos)` is O(pos),
    and there is one lookup per located identifier, so it degraded to
    O(matches x length): measured at 16 ms for 14.7 KB with 540 matches but 12.7 s
    for 1.47 MB with 54,000 matches. One pass plus a binary search is flat.
    """

    def __init__(self, text: str) -> None:
        self.text = text
        self.starts = [0] + [m.end() for m in re.finditer("\n", text)]

    def at(self, pos: int) -> tuple[int, str, int]:
        idx = bisect.bisect_right(self.starts, pos) - 1
        start = self.starts[idx]
        end = self.text.find("\n", start)
        if end == -1:
            end = len(self.text)
        return idx + 1, self.text[start:end], pos - start


def _fenced_spans(text: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in FENCE_RE.finditer(text)]


def _mask_code(text: str) -> str:
    """Blank out fenced blocks and inline code spans, preserving offsets.

    Used for habit words only. A branch named
    `eng-utils-0.11.0-provenance-and-prose-gate` is not the conductor saying
    "provenance" to Jonny. Identifier checks deliberately do NOT use this -
    backticks are exactly how the conductor writes bare ids.
    """
    out = list(text)

    def blank(start: int, end: int) -> None:
        for i in range(start, min(end, len(out))):
            if out[i] != "\n":
                out[i] = " "

    for start, end in _fenced_spans(text):
        blank(start, end)
    for m in CODE_SPAN_RE.finditer("".join(out)):
        blank(m.start(), m.end())
    return "".join(out)


def _content_words(fragment: str) -> int:
    """Count words that actually name something.

    Identifiers, markdown punctuation, numbers and lead words are all excluded,
    so "bead `280`" scores zero and "Blank namespace on the production config
    write path" scores high.
    """
    fragment = MARKUP_RE.sub(" ", FULL_FORM_RE.sub(" ", fragment))
    return sum(
        1
        for w in WORD_RE.findall(fragment)
        if len(w) >= 2 and w.lower() not in LEAD_WORDS
    )


def _preceding_word(text: str, pos: int) -> str:
    """The last alphabetic word before pos, tolerating trailing punctuation."""
    m = PRECEDING_WORD_RE.search(text[max(0, pos - 40) : pos])
    return m.group(1).lower() if m else ""


def _first_table_cell(line: str) -> str | None:
    """Return the first content cell of a markdown table row, if this is one.

    Contract section 5: "Never an ID leading a row." Tables were the format that
    most reliably produced bare ids, because a cell cannot hold a context
    sentence without wrapping into mush.
    """
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    if TABLE_SEPARATOR_RE.fullmatch(stripped):
        return None  # separator row
    return next((c for c in stripped.strip("|").split("|") if c.strip()), None)


def _is_copy_paste_handle(line: str, col: int) -> bool:
    """True if the identifier at `col` is a handle to open, not prose to read.

    Contract template 8.3 ends every dispatch with
    `Watch it: session <name> | agent-deck session output <id> -q | tmux <name>`,
    and the work contract requires that line, so without this the contract's own
    template would fail its own check.

    Scoped to the SEGMENT containing the identifier, deliberately. An earlier
    version exempted the whole line whenever it had three or more pipe-separated
    segments and any one of them was a command - which meant "`5r44` is done |
    agent-deck session output x -q | tmux foo" exempted the bare id in the prose
    segment. Pipe count says nothing about whether a token is a handle.
    """
    if line.strip().startswith("|"):
        return False  # a table row can never buy exemption this way
    pos = 0
    for segment in line.split("|"):
        start, end = pos, pos + len(segment)
        pos = end + 1
        if not (start <= col < end):
            continue
        tokens = segment.split()
        if not tokens:
            return False
        if os.path.basename(tokens[0]) in COMMAND_WORDS:
            return True  # a command invocation
        # The label form only counts on an actual handle LINE - a row of pipe-joined
        # handles, the shape template 8.3 prescribes. Without this requirement any
        # short fragment containing a label word escaped: "branch cyi", "pr cyi
        # merged" and "session cyi done" all passed with zero violations, which is
        # precisely the bare-identifier shape this check exists to catch.
        if "|" not in line:
            return False
        # "<label> <handle>", optionally prefixed as in "Watch it: session x"
        labels = {t.strip(":").lower() for t in tokens[:-1]}
        return len(tokens) <= 4 and bool(labels & HANDLE_LABELS)
    return False


def _has_bound_explanation(text: str, end: int, min_words: int) -> bool:
    """Is an explanation syntactically bound to the token ending at `end`?

    Two accepted shapes, shared by identifiers and habit words so the two can
    never drift apart on identical syntax:
        <token> - <explanation>
        <token> (<explanation>)      comma before the bracket is fine
    """
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    tail = text[end:line_end].lstrip("`*\"')")

    separated = re.match(r"\s*[-–—:]\s+(.*)$", tail)
    if separated and _content_words(separated.group(1)) >= min_words:
        return True

    parenthetical = re.match(r"[\s,]*\(([^)]*)\)", tail)
    if parenthetical and _content_words(parenthetical.group(1)) >= min_words:
        return True

    # A connector phrase is not an explanation on its own. Without a word count
    # here, "Closing `5r44` - that is, ok." satisfied the entire check - this was
    # the one accepted shape with no content requirement at all.
    connector = re.match(
        r"\s*[-–—]?\s*(?:that is|meaning|i\.e\.)[,: ]\s*(.*)$", tail, re.IGNORECASE
    )
    return bool(connector) and _content_words(connector.group(1)) >= min_words


# --------------------------------------------------------------------------
# The identifier check
# --------------------------------------------------------------------------


def _identifier_regex(identifiers: dict[str, str]) -> re.Pattern[str] | None:
    """Alternation over the LIVE list, longest first.

    Longest-first matters: `feature-feat-2026-08-18-detail-panel-d1` must win
    over any shorter id embedded inside it.
    """
    if not identifiers:
        return None
    body = "|".join(re.escape(a) for a in sorted(identifiers, key=len, reverse=True))
    return re.compile(r"(?<![A-Za-z0-9_-])(?:" + body + r")(?![A-Za-z0-9_-])")


def _is_alone_in(cell: str | None, token: str) -> bool:
    """True if `cell` holds nothing but `token` (and its markup)."""
    return cell is not None and cell.strip().strip("`*") == token


def _is_identifier_context(text: str, start: int, end: int, line: str) -> bool:
    """True if this token is written the way an identifier is written.

    Backticks, bold, a lead word in front, or standing alone in a table cell.
    Grounded in the corpus: every genuine bare bead reference across six real
    2026-08-15 messages was backticked; none of the "part" collisions were.
    """
    token = text[start:end]
    before = text[max(0, start - 12) : start]
    after = text[end : end + 12]
    if before.endswith("`") and after.startswith("`"):
        return True
    if before.rstrip().endswith("**") or after.lstrip().startswith("**"):
        return True
    if _preceding_word(text, start) in ID_LEAD_WORDS:
        return True
    return _is_alone_in(_first_table_cell(line), token)


def _has_bound_description(text: str, start: int, end: int, min_words: int) -> bool:
    """Is a name or title syntactically BOUND to this identifier?

    Three accepted shapes, from contract section 1:
      A  <id> - <title>          prose form, id first
      B  <plain name> (<id>)     list form, name first
      C  <id> (<description>)    parenthetical

    Adjacency alone is not enough. "c39 flagged it" puts two words beside a bare
    id without ever saying what c39 is, and contract section 2 asks for a plain
    NAME on repeat mentions, not merely nearby prose. So a repeat mention uses
    the same three shapes with a lower word threshold.
    """
    if _has_bound_explanation(text, end, min_words):  # shapes A and C
        return True

    line_start = text.rfind("\n", 0, start) + 1
    opener = text[line_start:start].rstrip("`*").rstrip()
    if opener.endswith(("(", "[")):  # shape B
        return _content_words(opener[:-1]) >= min_words
    return False


def _locate_identifiers(
    text: str, identifiers: dict[str, str], lines: LineIndex
) -> list[Found]:
    """Every identifier occurrence in the text, overlaps resolved longest-first."""
    found = [
        Found(m.start(), m.end(), m.group(0), "bead")
        for m in FULL_FORM_RE.finditer(text)
    ]

    live_re = _identifier_regex(identifiers)
    if live_re is not None:
        for m in live_re.finditer(text):
            token = m.group(0)
            if FULL_FORM_RE.fullmatch(token):
                continue  # already captured by shape
            _, line, _ = lines.at(m.start())
            if _is_risky_bare_token(token) and not _is_identifier_context(
                text, m.start(), m.end(), line
            ):
                continue  # plausibly ordinary prose - see _is_risky_bare_token
            found.append(Found(m.start(), m.end(), token, identifiers[token]))

    for kind, pattern in SHAPE_KINDS:
        for m in pattern.finditer(text):
            # The comment on SHAPE_KINDS claims no English word can match, because
            # no English word contains a digit. That holds for a word alone and
            # fails for a word glued to digits: "decade2020" is entirely
            # hex-alphabet characters and does contain one, so it was flagged as a
            # commit hash in a completely innocent sentence.
            if kind == "commit" and _is_english_word(m.group(0).rstrip("0123456789")):
                continue
            found.append(Found(m.start(), m.end(), m.group(0), kind))

    for m in _chain_path_matches(text):
        _, line, _ = lines.at(m.start())
        # Delegated rather than re-implemented as a second interpolated regex. The
        # two had already diverged: the regex version did not tolerate the trailing
        # markup that _is_alone_in strips.
        stripped = line.strip()
        bullet_body = stripped[1:] if stripped[:1] in "-*" else None
        if _is_alone_in(_first_table_cell(line), m.group(0)) or _is_alone_in(
            bullet_body, m.group(0)
        ):
            found.append(Found(m.start(), m.end(), m.group(0), "path"))

    found.sort(key=lambda f: (f.start, -(f.end - f.start)))
    kept: list[Found] = []
    for item in found:
        if kept and item.start < kept[-1].end:
            continue
        kept.append(item)
    return kept


def _chain_path_matches(text: str):
    """Path-shaped matches: with a directory, and the bare-filename form."""
    yield from PATH_RE.finditer(text)
    for m in BARE_FILENAME_RE.finditer(text):
        if "/" not in m.group(0):
            yield m


def check_identifiers(text: str, identifiers: dict[str, str]) -> list[Violation]:
    """Flag every identifier that reaches him with nothing beside it."""
    violations: list[Violation] = []
    fenced = _fenced_spans(text)
    lines = LineIndex(text)
    seen: set[str] = set()

    for item in _locate_identifiers(text, identifiers, lines):
        if any(s <= item.start < e for s, e in fenced):
            continue
        line_no, line, col = lines.at(item.start)
        if _is_copy_paste_handle(line, col):
            continue  # a handle to open, not prose (contract template 8.3)

        # A bead id can legitimately appear inside another bead's TITLE. Track
        # by the id itself so the same work mentioned twice is one identifier.
        key = item.token.split("-")[-1] if item.kind == "bead" else item.token
        first_mention = key not in seen
        seen.add(key)

        label = KIND_LABEL[item.kind]
        if (cell := _first_table_cell(line)) is not None and item.token in cell:
            # Contract section 5: never an ID leading a row. The description in
            # the next cell does not rescue it - this is the exact shape of the
            # 2026-08-15 status reports.
            violations.append(
                Violation(
                    "id-leads-table-row",
                    item.token,
                    line_no,
                    line.strip(),
                    f"{label} `{item.token}` leads a table row. Contract section 5: never an "
                    f"ID leading a row - rewrite this table as a short list with a bold lead line.",
                )
            )
            continue

        min_words = (
            FIRST_MENTION_MIN_WORDS if first_mention else REPEAT_MENTION_MIN_WORDS
        )
        if _has_bound_description(text, item.start, item.end, min_words):
            continue

        if first_mention:
            detail = (
                f"bare {label} `{item.token}` - first mention in this message, so it needs "
                f"the full treatment: the id, the title as filed, and a line saying what it means."
            )
        else:
            detail = (
                f"bare {label} `{item.token}` - a later mention may drop to the id plus a "
                f"short plain name, but never to a bare id (contract section 2)."
            )
        violations.append(
            Violation("bare-identifier", item.token, line_no, line.strip(), detail)
        )

    return violations


# --------------------------------------------------------------------------
# The habit-word check (contract section 3)
# --------------------------------------------------------------------------


def check_habit_words(text: str) -> list[Violation]:
    """Flag the conductor's own abstract vocabulary used without a gloss.

    He was offered outright replacement of these words and declined, choosing
    "keep the precise word, always explain it". So the word is never the
    violation - the missing gloss is.
    """
    violations: list[Violation] = []
    masked = _mask_code(text)  # a branch named ...-provenance-... is not prose
    lines = LineIndex(text)

    for habit in HABIT_WORDS:
        for m in habit.pattern.finditer(masked):
            if habit.skip_after and _is_noun_usage(
                masked, m.start(), m.end(), habit.skip_after
            ):
                continue
            if _has_bound_explanation(masked, m.end(), 2):
                continue
            if _is_inside_own_gloss(masked, m.start()):
                continue  # the word is the thing being defined, not the habit
            line_no, line, _ = lines.at(m.start())
            violations.append(
                Violation(
                    "unglossed-habit-word",
                    habit.word,
                    line_no,
                    line.strip(),
                    habit.remedy.format(seen=m.group(0), word=habit.word),
                )
            )

    return violations


# --------------------------------------------------------------------------
# Top level
# --------------------------------------------------------------------------


def check(
    text: str, identifiers: dict[str, str] | None = None
) -> tuple[list[Violation], list[str]]:
    """Run every contract check over one outgoing message."""
    degradations: list[str] = []
    if identifiers is None:
        identifiers, degradations = load_live_identifiers()
    violations = check_identifiers(text, identifiers)
    violations.extend(check_habit_words(text))
    violations.sort(key=lambda v: (v.line_no, v.kind))
    return violations, degradations


def format_report(violations: list[Violation], degradations: list[str]) -> str:
    """Build the text the model gets back, as instructions rather than a scolding."""
    lines = [
        "COMMUNICATION CONTRACT CHECK FAILED "
        f"({len(violations)} violation{'s' if len(violations) != 1 else ''}).",
        "Your message above went out with identifiers Jonny cannot resolve. Re-send it corrected.",
        "",
    ]
    for kind, header in (
        ("bare-identifier", "BARE IDENTIFIERS - no description beside them"),
        (
            "id-leads-table-row",
            "IDENTIFIER LEADING A TABLE ROW - contract section 5 forbids this",
        ),
        (
            "unglossed-habit-word",
            "HABIT WORDS USED WITHOUT A GLOSS - contract section 3",
        ),
    ):
        group = [v for v in violations if v.kind == kind]
        if not group:
            continue
        lines.append(header)
        lines.extend(v.render() for v in group)
        lines.append("")
    lines += [
        "THE ACCEPTED FORMS (contract section 1):",
        "  in prose:  <id> - <title exactly as filed>, then a line saying what it means",
        "  in a list: **<plain-language name>** (<id>), then a plain line",
        "  repeat mention in this same message: id plus a short plain name - never a bare id",
        "",
        "Length is meant to stay the same (contract section 6): pay for the descriptions by cutting",
        "restated decisions and raw command output, not by dropping items.",
    ]
    if degradations:
        lines.append("")
        lines.append(
            "PARTIAL CHECK - these sources could not be read, so their identifiers went unchecked:"
        )
        lines.extend(f"  - {d}" for d in degradations)
    return "\n".join(lines)


def _in_scope(cwd: str) -> bool:
    override = os.environ.get("COMMS_CONTRACT_CHECK_SCOPE")
    if override:
        # Say so. This replaces the real marker, so a value left in a shell profile
        # would otherwise disable the check for the real conductor with no signal
        # anywhere that coverage had been lost.
        print(
            f"comms-contract-check: COMMS_CONTRACT_CHECK_SCOPE override active ({override!r})",
            file=sys.stderr,
        )
        return override in (cwd or "")
    return CONDUCTOR_PATH_MARKER in (cwd or "")


USAGE = """usage:
  comms-contract-check.py                        run as a Stop hook (reads the hook payload on stdin)
  comms-contract-check.py --file DRAFT.md        check a draft by hand
  comms-contract-check.py --stdin                check a draft on stdin
  comms-contract-check.py --file D --identifiers IDS.json
                                                 check against a frozen id list, for reproducible runs
"""


def run_cli(argv: list[str]) -> int:
    """Check a draft by hand. Exits 1 when the draft would be refused."""
    identifiers: dict[str, str] | None = None
    if "--identifiers" in argv:
        with open(argv[argv.index("--identifiers") + 1], encoding="utf-8") as fh:
            identifiers = json.load(fh)

    # Validated here rather than relying on _dispatch's guard: run_cli is a public
    # function, and a direct caller passing [] would otherwise hit an IndexError
    # instead of the usage path this clearly intends.
    if not argv or argv[0] not in ("--file", "--stdin"):
        print(USAGE, file=sys.stderr)
        return 64
    if argv[0] == "--file":
        if len(argv) < 2:
            # Without this, the missing path raised IndexError, which main()'s
            # crash guard turned into a report plus exit 0 - a usage error dressed
            # up as an internal failure.
            print(USAGE, file=sys.stderr)
            return 64
        with open(argv[1], encoding="utf-8") as fh:
            text = fh.read()
    else:
        text = sys.stdin.read()

    violations, degradations = check(text, identifiers)
    if violations:
        print(format_report(violations, degradations))
        return 1
    message = "communication contract check PASSED - no bare identifiers, no unglossed habit words."
    if degradations:
        message += "\nPARTIAL: " + "; ".join(degradations)
    print(message)
    return 0


def run_stop_hook(payload: dict[str, Any]) -> int:
    """Gate one outgoing conductor message. Returns the process exit code."""
    # Self-scope: this hook is registered user-wide, so it fires in every
    # session. Say nothing and do no work anywhere but the conductor.
    if not _in_scope(payload.get("cwd", "")):
        return 0

    text = payload.get("last_assistant_message") or ""
    if not text.strip():
        return 0

    violations, degradations = check(text)
    if not violations and not degradations:
        return 0

    # A degradation means the live id list could not be read, and the live list is
    # the ONLY thing that can catch a bare session name or a bare 3-4 char bead
    # suffix. So "no violations found" while degraded does not mean the message is
    # clean - it means the check that would have caught the 2026-08-15 failure did
    # not run. Two independent reviewers found this swallowed, reproduced with
    # "Closing cyi now, it went fine." under a broken PATH, which is the exact
    # shape Jonny complained about.
    if not violations:
        print(
            "COMMUNICATION CONTRACT CHECK RAN PARTIALLY - no violations found, but:\n"
            + "\n".join(f"  - {d}" for d in degradations)
            + "\nSo this message was NOT fully checked. Treat it as unverified.",
            file=sys.stderr,
        )
        return 0

    report = format_report(violations, degradations)

    # `stop_hook_active` is true when this hook already blocked once this turn.
    # Verified 2026-08-18: it flips false -> true on the re-fire. Blocking again
    # would loop, so the second pass reports to stderr and lets the turn end.
    if payload.get("stop_hook_active"):
        print(report, file=sys.stderr)
        return 0

    print(json.dumps({"decision": "block", "reason": report}))
    return 0


CRASH_NOTICE = (
    "comms-contract-check FAILED TO RUN: {kind}: {exc}\n"
    "This message was NOT checked against the communication contract."
)


def _dispatch(argv: list[str], stdin: TextIO) -> int:
    """Route to the by-hand path or the hook path. Returns an exit code.

    Dispatch is explicit rather than "no arguments means hook mode". If the
    settings.json registration ever gains a flag or a wrapper, the blocking path
    must not quietly become the by-hand path and skip the check.
    """
    if argv and argv[0] != "--hook":
        return run_cli(argv)
    try:
        payload = json.load(stdin)
    except (ValueError, OSError) as exc:
        # Every other failure path in this file reports. This one returned 0 with
        # nothing on either stream, contradicting main()'s own docstring.
        print(CRASH_NOTICE.format(kind=type(exc).__name__, exc=exc), file=sys.stderr)
        return 0
    if not isinstance(payload, dict) or "hook_event_name" not in payload:
        print(USAGE, file=sys.stderr)
        return 64
    return run_stop_hook(payload)


def main(argv: list[str] | None = None, stdin: TextIO | None = None) -> int:
    """Entry point. Never raises: a crash here must not wedge the conductor.

    It does exit LOUD, which is where it parts company with the sibling Stop hook
    in plugins/jbb-feature-dev/hooks/followup_capture.py. That one swallows
    everything silently and says why: it is "a best-effort reminder". This check is
    not best-effort - it is the only thing standing between the contract and a
    third failure of a rule already broken twice, and a silent pass is precisely
    the failure it was built to prevent. So a crash is reported where someone will
    see it, and the turn is still allowed to end.
    """
    try:
        return _dispatch(sys.argv[1:] if argv is None else argv, stdin or sys.stdin)
    except BaseException as exc:  # noqa: BLE001 - deliberate; see the docstring
        print(CRASH_NOTICE.format(kind=type(exc).__name__, exc=exc), file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
