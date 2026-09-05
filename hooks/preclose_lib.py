#!/usr/bin/env python3
"""Shared primitives for the agent-deck pre-close guard and its runner.

Path resolution, agent-deck registry reads, and recognition of the commands that
destroy a session. Standard library only.

Kept 3.9-compatible on purpose: /usr/bin/python3 on this machine is 3.9.6 while
/opt/homebrew/bin/python3 is 3.14.5, and the hook wiring resolves `python3` from
PATH. A PEP 604 annotation would raise at import under 3.9, which exits 1, which
the harness treats as a non-blocking error - so the guard would fail open
silently with no diagnosis. Hence `from __future__ import annotations`, which
has precedent in plugins/jbb-feature-dev/hooks/followup_capture.py.
"""

from __future__ import annotations

import json
import os
import re
import shlex
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

# Every command that destroys a session, verified against `agent-deck --help`
# and the per-command --help on v1.9.73, 2026-08-18. Longest tuple first: a
# segment starting `session remove` must not match the bare `remove` entry.
_DESTRUCTIVE: Tuple[Tuple[str, ...], ...] = (
    ("session", "remove"),
    ("worktree", "finish"),
    ("wt", "finish"),
    ("remove",),
    ("rm",),
)

# `agent-deck worktree finish --help`: "Merge a worktree branch, remove the
# worktree, and delete the session." It deletes the worktree UNCONDITIONALLY -
# none of its flags gate that, and --prune-worktree does not exist on it. So the
# worktree-clean check has to be demanded by the VERB here, not by a flag that
# can never appear.
_ALWAYS_DELETES_WORKTREE = frozenset({("worktree", "finish"), ("wt", "finish")})

# Destroys sessions in bulk, or destroys something that is not a single session.
# These are denied outright rather than approved per target: approving a group
# means agreeing with agent-deck about set membership, and disagreeing silently
# would let one through.
# Each entry is a verb plus the flags that make it actually destroy something.
# An empty set means "always destructive". Verified against each command's own
# --help on v1.9.73:
#   worktree cleanup   "By default, runs in dry-run mode... Use --force to
#                       actually perform the cleanup" - so a bare call LISTS
#   conductor teardown "Stop a conductor session and optionally remove its
#                       directory" - --remove is what removes; --all only widens
#                       the scope of the stop
# Denying either without those flags refused a harmless command, and told the
# operator it "destroys several sessions at once", which was not true.
_BULK: Tuple[Tuple[Tuple[str, ...], frozenset], ...] = (
    (("worktree", "cleanup"), frozenset({"force"})),
    (("wt", "cleanup"), frozenset({"force"})),
    (("conductor", "teardown"), frozenset({"remove"})),
)

# Global flags that consume the NEXT token, so it is not the subcommand.
# `agent-deck --help` documents exactly these three.
_GLOBAL_VALUE_FLAGS = frozenset({"-p", "--profile", "-g", "--group", "--select"})

_SHELL_WRAPPERS = frozenset({"bash", "sh", "zsh", "dash", "ksh"})

# `eval` takes its command directly rather than behind -c, so it needs its own
# branch. Verified: `eval "agent-deck session remove x"` was allowed silently,
# because shlex yields the whole invocation as one opaque token and no token
# equals "agent-deck".
_EVAL_WRAPPERS = frozenset({"eval"})

# shlex does NOT treat shell operators as tokens: shlex.split("a; b") yields
# ['a;', 'b'], so `;` stays glued to the preceding word and no split happens.
# Normalise them into standalone tokens first. Verified 2026-08-18; without this
# `agent-deck session stop x; agent-deck session remove x` parses as a stop and
# the removal is silently allowed.
_OPERATOR_RE = re.compile(r"(\|\||&&|[;|&])")
_OPERATORS = frozenset({"&&", "||", "|", ";", "&"})

# Words that only appear in a command that destroys something. The exact verb
# TABLE above governs the precise path; this set is the backstop, so a verb a
# future agent-deck version adds fails closed rather than being allowed in
# silence. Checked against the full `agent-deck --help` surface on v1.9.73: none
# of these appears as a positional in any non-destructive command, so the
# backstop cannot fire on `list`, `status`, `show`, `output` and friends.
# A command whose verb or binary name is produced by shell substitution cannot be
# matched lexically: `VERB=remove; agent-deck session $VERB x` runs a real removal
# while every token comparison fails. This is not only an adversarial shape - it is
# an ordinary thing for a scripting agent to write by habit.
_SUBSTITUTION_RE = re.compile(r"[$`]")

_DESTRUCTIVE_WORDS = frozenset(
    {
        "remove",
        "rm",
        "finish",
        "cleanup",
        "teardown",
        "delete",
        "destroy",
        "purge",
        "prune",
        "wipe",
    }
)

_DESTRUCTIVE_WORD_RE = re.compile(r"\b(%s)\b" % "|".join(sorted(_DESTRUCTIVE_WORDS)))

# Heredoc bodies are data, not commands. A dispatch brief that mentions
# `agent-deck session remove` in prose must not trigger the guard.
_HEREDOC_OPEN_RE = re.compile(r"<<(-?)\s*\\?(['\"]?)(\w+)\2")

# fd-to-fd redirects (2>&1, >&2, 2>&-) contain '&' which _OPERATOR_RE would
# split into an operator token, creating a phantom '2>' that becomes a ref.
_FD_REDIRECT_RE = re.compile(r"(?<!\S)\d*>&[\d-]+")

# Post-tokenisation redirect filters for standalone operators (>, >>, 2>)
# and attached forms (2>/dev/null, >/file).
_REDIR_STANDALONE_RE = re.compile(r"^\d*(?:>>?|<(?!<))$")
_REDIR_ATTACHED_RE = re.compile(r"^\d*(?:>>?|<(?!<))\S")


def _strip_heredoc_bodies(command: str) -> str:
    """Remove heredoc body lines from a command string.

    A heredoc body is data being written, not a command being executed. Without
    this, prose that mentions session commands triggers the guard's backstop.
    """
    if "\n" not in command or "<<" not in command:
        return command
    lines = command.split("\n")
    result: List[str] = []
    skip_until: Optional[Tuple[str, bool]] = None
    for line in lines:
        if skip_until is not None:
            delim, is_dash = skip_until
            test_line = line.lstrip("\t") if is_dash else line
            if test_line.rstrip() == delim:
                skip_until = None
                result.append(line)
            continue
        match = _HEREDOC_OPEN_RE.search(line)
        if match:
            skip_until = (match.group(3), match.group(1) == "-")
        result.append(line)
    return "\n".join(result)


def _strip_redirect_tokens(tokens: Sequence[str]) -> List[str]:
    """Remove I/O redirect operators and their targets from a token list.

    Shell redirections are not command arguments. Without this, a file
    descriptor like '2>' becomes a positional that the guard treats as a ref.
    """
    result: List[str] = []
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if _REDIR_STANDALONE_RE.match(token):
            skip_next = True
            continue
        if _REDIR_ATTACHED_RE.match(token):
            continue
        result.append(token)
    return result


class Removal(NamedTuple):
    """A session-destroying command found in a shell command string."""

    refs: List[str]
    bulk: bool = False
    prune_worktree: bool = False
    unparsed: bool = False


class RegistryUnavailable(Exception):
    """The agent-deck registry could not be read. Carries `transient`."""

    def __init__(self, message: str, transient: bool = False) -> None:
        super().__init__(message)
        self.transient = transient


def _is_agent_deck(token: str) -> bool:
    """True for `agent-deck`, `/opt/homebrew/bin/agent-deck`, `./agent-deck`.

    The binary really does live at /opt/homebrew/bin/agent-deck, so an absolute
    invocation is not hypothetical.
    """
    # rpartition rather than PurePath: this runs on the hot path, and importing
    # pathlib costs 3.3 ms on every Bash tool call in every session.
    return token.rpartition("/")[2] == "agent-deck"


def _segments(tokens: Sequence[str]) -> List[List[str]]:
    """Split a token stream on shell operators into per-command segments."""
    current: List[str] = []
    out: List[List[str]] = []
    for token in tokens:
        if token in _OPERATORS:
            out.append(current)
            current = []
        else:
            current.append(token)
    out.append(current)
    return out


def _flag_name(token: str) -> str:
    """`--prune-worktree=true` -> `prune-worktree`. `-q` -> `q`.

    agent-deck uses Go's flag package, which accepts `-x`, `--x`, `-x=v` and
    `--x=v` interchangeably - verified: `--prune-worktree=true` is accepted while
    `--not-a-real-flag=true` errors. Reading flags without truncating at `=` made
    `--prune-worktree=true` invisible, which silently dropped the worktree check
    on the one removal form that deletes the worktree.
    """
    return token.lstrip("-").split("=", 1)[0]


def _strip_global_flags(words: Sequence[str]) -> List[str]:
    """Drop global value-taking flags and the values they consume."""
    kept: List[str] = []
    skip_next = False
    for token in words:
        if skip_next:
            skip_next = False
            continue
        if token in _GLOBAL_VALUE_FLAGS:
            skip_next = True
            continue
        if (
            token.startswith("-")
            and _flag_name(token) in {f.lstrip("-") for f in _GLOBAL_VALUE_FLAGS}
            and "=" in token
        ):
            continue
        kept.append(token)
    return kept


def _match_invocation(words: Sequence[str]) -> Optional[Removal]:
    """Match one `agent-deck ...` invocation. `words` excludes the binary."""
    kept = _strip_global_flags(words)
    positional = [w for w in kept if not w.startswith("-")]
    flags = [_flag_name(w) for w in kept if w.startswith("-")]
    if not positional:
        return None

    for verb, required_flags in _BULK:
        if tuple(positional[: len(verb)]) == verb:
            if required_flags and not (required_flags & set(flags)):
                return None
            return Removal(refs=[], bulk=True)

    for verb in _DESTRUCTIVE:
        if tuple(positional[: len(verb)]) == verb:
            if "all-errored" in flags:
                return Removal(refs=[], bulk=True)
            return Removal(
                refs=list(positional[len(verb) :]),
                prune_worktree=(
                    "prune-worktree" in flags or verb in _ALWAYS_DELETES_WORKTREE
                ),
            )

    # Tier 2. An agent-deck invocation carrying a destructive-sounding word that
    # the table does not recognise. The table governs the precise path; this
    # governs everything else, so a verb added by a future agent-deck version
    # fails CLOSED and loudly rather than open and silently. Without it,
    # `agent-deck session delete abc` was simply allowed.
    if any(word in _DESTRUCTIVE_WORDS for word in positional):
        return Removal(refs=[], unparsed=True)
    return None


def _scan_segment(segment: Sequence[str], depth: int) -> List[Removal]:
    """Find every session-destroying invocation in one command segment."""
    if not segment or segment[0].startswith("#"):
        return []
    segment = _strip_redirect_tokens(segment)
    if not segment:
        return []

    found: List[Removal] = []

    # `bash -c '<command>'` hides a whole command inside a single token. Recurse
    # rather than miss it, and rather than substring-screening every token,
    # which would deny `echo "agent-deck session remove"`.
    leader = segment[0].rpartition("/")[2]
    if depth < 2 and leader in _SHELL_WRAPPERS:
        for index, token in enumerate(segment[1:], start=1):
            if token == "-c" and index + 1 < len(segment):
                found.extend(_find(segment[index + 1], depth + 1))
                break
    elif depth < 2 and leader in _EVAL_WRAPPERS:
        # eval joins its arguments and runs the result.
        found.extend(_find(" ".join(segment[1:]), depth + 1))

    # EVERY occurrence, not just the first: `agent-deck session stop x ;
    # agent-deck session remove x` has a harmless first one, and
    # `remove a && remove b` must not check only `a`.
    for index, token in enumerate(segment):
        if _is_agent_deck(token):
            match = _match_invocation(segment[index + 1 :])
            if match is not None:
                found.append(match)
    return found


def _find(command: str, depth: int = 0) -> List[Removal]:
    command = _strip_heredoc_bodies(command)
    command = _FD_REDIRECT_RE.sub("", command)
    normalised = _OPERATOR_RE.sub(r" \1 ", command)
    try:
        tokens = shlex.split(normalised)
    except ValueError:
        # Unbalanced quoting: cannot tokenize. If a bare agent-deck token and a
        # destructive word are both plausibly present, deny rather than miss.
        if re.search(
            r"(^|[\s/])agent-deck(\s|$)", command
        ) and _DESTRUCTIVE_WORD_RE.search(command):
            return [Removal(refs=[], unparsed=True)]
        return []
    out: List[Removal] = []
    for segment in _segments(tokens):
        out.extend(_scan_segment(segment, depth))
    if out:
        return out

    # Nothing matched lexically. If the command nonetheless mentions agent-deck and
    # a destructive word AND contains an unresolved substitution, the verb or the
    # binary name may be hidden behind it - so refuse rather than allow in silence.
    # `agent-deck session remove $TARGET` does NOT reach here: that matches
    # normally and is denied with a message about the unexpanded variable.
    if (
        _SUBSTITUTION_RE.search(command)
        and "agent-deck" in command
        and _DESTRUCTIVE_WORD_RE.search(command)
    ):
        return [Removal(refs=[], unparsed=True)]
    return out


def find_removal(command: str) -> Optional[Removal]:
    """Return an aggregated Removal if `command` destroys any session, else None.

    Errs toward matching. A false match costs one runner invocation; a false miss
    costs a session's only copy of its final output.
    """
    matches = _find(command)
    if not matches:
        return None
    refs = list(dict.fromkeys(ref for match in matches for ref in match.refs))
    return Removal(
        refs=refs,
        bulk=any(m.bulk for m in matches),
        prune_worktree=any(m.prune_worktree for m in matches),
        unparsed=any(m.unparsed for m in matches),
    )


# ---------------------------------------------------------------- paths


def evidence_root(env: Dict[str, str]) -> Path:
    """Root for durable pre-close evidence.

    Durable means outside /private/tmp, which is swept, and outside any
    git-pushed directory - the property the work contract defines in section 5.
    Falls back to expanduser rather than env["HOME"] alone: with HOME unset the
    naive form yields a RELATIVE path, so the guard would write evidence into
    whatever directory the calling session happened to be in.
    """
    from pathlib import Path
    import os.path

    override = env.get("PRECLOSE_EVIDENCE_ROOT")
    if override:
        return Path(override)
    home = env.get("HOME") or os.path.expanduser("~")
    return Path(home) / "evidence"


def receipt_path(session_id: str, env: Dict[str, str]) -> Path:
    """Where the machine-checkable proof for one session lives."""
    return evidence_root(env) / "preclose" / (session_id + ".json")


def dump_path(session_id: str, env: Dict[str, str]) -> Path:
    """Where the session's rescued final output lives. Keyed on the session id,
    never the title: titles drift, and one renamed itself twice mid-test."""
    return evidence_root(env) / "session-finals" / (session_id + "-final.md")


def guard_log_path(env: Dict[str, str]) -> Path:
    """Where the guard records its own internal problems.

    This is the only trace a silently-degraded guard leaves, so it is deliberately
    somewhere a human already looks rather than somewhere tidier.
    """
    return evidence_root(env) / "preclose" / "guard-errors.log"


def state_db_candidates(env: Dict[str, str]) -> List[Path]:
    """Where agent-deck's registry might be.

    `agent-deck migrate-paths` copies the legacy ~/.agent-deck layout into XDG
    directories, so prefer XDG and fall back to legacy rather than hardcoding
    either. Both are returned so an error message can name both.
    """

    from pathlib import Path

    override = env.get("PRECLOSE_STATE_DB")
    if override:
        return [Path(override)]
    home = Path(env.get("HOME", ""))
    profile = env.get("AGENTDECK_PROFILE") or "default"
    xdg = Path(env.get("XDG_DATA_HOME") or (home / ".local" / "share"))
    return [
        xdg / "agent-deck" / "profiles" / profile / "state.db",
        home / ".agent-deck" / "profiles" / profile / "state.db",
    ]


def state_db_path(env: Dict[str, str]) -> Path:
    """The first agent-deck registry that exists, else the legacy location so the
    error message names a real path."""
    candidates = state_db_candidates(env)
    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except OSError:
            continue
    return candidates[-1]


# ------------------------------------------------------------- registry


def _connect(db_path: Path):
    """Read-only connection with a bounded wait.

    sqlite3 is imported here, not at module scope. This module is imported by a
    hook that runs on EVERY Bash tool call, and the registry is touched only on
    the rare path where a session removal was actually detected. Measured: 3.0 ms
    of import that the common case does not need.

    mode=ro, never immutable=1: agent-deck writes this database continuously and
    it is in WAL mode (verified: journal_mode='wal', a growing state.db-wal), so
    immutable=1 would skip locking and could read torn data.
    """
    import sqlite3

    try:
        conn = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True, timeout=1.5)
        conn.execute("PRAGMA query_only=1")
        return conn
    except sqlite3.OperationalError as exc:
        raise RegistryUnavailable(
            "cannot read %s: %s" % (db_path, exc), transient=_is_busy(exc)
        ) from exc


def _is_busy(exc: BaseException) -> bool:
    """A lock we could win by waiting, versus a database that is not there."""
    return "locked" in str(exc).lower() or "busy" in str(exc).lower()


def is_conductor(instance_id: str, db_path: Path) -> Optional[bool]:
    """True/False when the row exists, None when there is no such row.

    None is NOT False. A missing row means a stale environment variable or a
    creation race, so the caller needs another signal; a row saying 0 is a
    confirmed negative.
    """
    import sqlite3

    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT is_conductor FROM instances WHERE id = ?", (instance_id,)
        ).fetchone()
    except sqlite3.Error as exc:
        raise RegistryUnavailable(str(exc), transient=_is_busy(exc)) from exc
    finally:
        conn.close()
    return None if row is None else bool(row[0])


_ROW_COLUMNS = (
    "id",
    "title",
    "status",
    "tool",
    "worktree_path",
    "project_path",
    "tool_data",
)


class AmbiguousReference(Exception):
    """A reference matched more than one session, so it cannot be checked."""


def _escape_like(text: str) -> str:
    """LIKE treats % and _ as wildcards; an id or title may contain either."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def resolve_session(ref: str, db_path: Path) -> Optional[Dict[str, Any]]:
    """Resolve an id, id prefix, or title to one registry row.

    agent-deck accepts all three (verified: `session show 0105c6f6` and
    `session show conductor-hq` both resolve), so the guard must too, or it would
    refuse a removal it merely failed to look up.

    Raises AmbiguousReference when a prefix matches more than one session. Taking
    the first row would let the guard validate one session's receipt while
    agent-deck destroys another - a silent false allow.
    """
    import sqlite3

    columns = ", ".join(_ROW_COLUMNS)
    conn = _connect(db_path)
    try:
        for sql, args in (
            ("SELECT %s FROM instances WHERE id = ?" % columns, (ref,)),
            ("SELECT %s FROM instances WHERE title = ?" % columns, (ref,)),
        ):
            row = conn.execute(sql, args).fetchone()
            if row is not None:
                return dict(zip(_ROW_COLUMNS, row))
        rows = conn.execute(
            "SELECT %s FROM instances WHERE id LIKE ? ESCAPE '\\'" % columns,
            (_escape_like(ref) + "%",),
        ).fetchall()
        if len(rows) > 1:
            raise AmbiguousReference(
                "%r matches %d sessions: %s"
                % (ref, len(rows), ", ".join(sorted(r[0] for r in rows)))
            )
        if rows:
            return dict(zip(_ROW_COLUMNS, rows[0]))
        return None
    except sqlite3.Error as exc:
        raise RegistryUnavailable(str(exc), transient=_is_busy(exc)) from exc
    finally:
        conn.close()


# ---------------------------------------------- fixture registry (for --selftest)

# Narrower than the live table on purpose: only the columns this code reads.
# Re-derive with:
#   sqlite3 ~/.agent-deck/profiles/default/state.db ".schema instances"
INSTANCES_DDL = """
CREATE TABLE instances (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    project_path TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'error',
    tool TEXT NOT NULL DEFAULT 'shell',
    worktree_path TEXT NOT NULL DEFAULT '',
    tool_data TEXT NOT NULL DEFAULT '{}',
    is_conductor INTEGER NOT NULL DEFAULT 0
)
"""


def fixture_registry(rows, directory) -> Path:
    """Build a throwaway registry. Used by --selftest and by the tests.

    Lives in production rather than in the test helpers so that --selftest, which
    IS production functionality, does not have to import a test module. The
    dependency runs one way: tests import this, never the reverse.
    """

    from pathlib import Path
    import sqlite3 as _sqlite3

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    db_path = directory / "state.db"
    conn = _sqlite3.connect(str(db_path))
    try:
        conn.execute(INSTANCES_DDL)
        for row in rows:
            conn.execute(
                "INSERT INTO instances (id, title, project_path, status, tool, "
                "worktree_path, tool_data, is_conductor) VALUES (?,?,?,?,?,?,?,?)",
                (
                    row["id"],
                    row.get("title", "untitled"),
                    row.get("project_path", ""),
                    row.get("status", "stopped"),
                    row.get("tool", "claude"),
                    row.get("worktree_path", ""),
                    json.dumps(row.get("tool_data", {})),
                    int(row.get("is_conductor", 0)),
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return db_path


# --------------------------------------------- reading `session output --json`


class SessionOutput(NamedTuple):
    """What `agent-deck session output <id> --json` told us.

    `code` is the discriminator, because three different situations must take
    three different branches:

      "message"     a real final answer (or a genuinely empty one)
      "screen"       the session's terminal pane, not its final word
      "unreachable"  agent-deck itself could not be run at all
      "unknown"      agent-deck answered but unusably (NOT_FOUND, unparseable)

    "unreachable" is separate from "unknown" because it says nothing about the
    SESSION - only about the tool. Collapsing them let a shell session earn a
    passing "nothing to rescue" receipt when the truth was that the probe was
    broken.

    "screen" and "unknown" are both not-ok, but only "screen" can mean "there was
    never anything to rescue". Collapsing them is how an empty dump earns a
    passing receipt, or how a session becomes permanently unremovable.
    """

    ok: bool
    content: str = ""
    reason: str = ""
    code: str = "unknown"


def parse_session_output(stdout_text: str, tool: str = "claude") -> SessionOutput:
    """Extract a trustworthy final answer, or explain why there is none.

    Four traps, all observed live on 2026-08-18:

    1. The exit code is 0 for a real answer, for empty output, AND for a session
       that does not exist. It carries no information, so it is not consulted.
    2. `success: true` means the CLI call worked, not that there is output. A
       never-started session returns success true with content "".
    3. For a RUNNING Claude session that has not answered yet, `content` is the
       tmux pane - 648 characters of box-drawing and "Accessing workspace:" -
       with `success: true`. A non-empty check accepts that as a rescued dump and
       an alphanumeric heuristic does not catch it either. What separates them is
       `timestamp`: a real assistant message carries one
       ('2026-08-18T17:09:32.867Z'), terminal chrome carries ''.
    4. BUT that rule must not be applied to a non-Claude session. A shell session
       ALWAYS returns its pane with an empty timestamp, because it has no concept
       of an assistant message - its pane IS its output, and it is the best
       agent-deck offers. Applying the timestamp rule to those would make every
       shell session permanently unremovable.
    """
    try:
        payload = json.loads(stdout_text)
    except ValueError:
        return SessionOutput(False, reason="agent-deck did not return JSON")
    if not isinstance(payload, dict):
        return SessionOutput(
            False, reason="agent-deck returned JSON that is not an object"
        )
    if payload.get("success") is not True:
        detail = payload.get("error") or payload.get("code") or "unknown error"
        return SessionOutput(False, reason=str(detail))

    content = payload.get("content")
    if not isinstance(content, str):
        return SessionOutput(False, reason="agent-deck returned no content field")

    if tool == "claude" and not payload.get("timestamp") and content.strip():
        return SessionOutput(
            False,
            reason="agent-deck returned terminal output rather than an assistant "
            "message (no timestamp), so this is the session's screen, not its "
            "final word",
            code="screen",
        )
    return SessionOutput(True, content=content, code="message")


def transcript_exists(row: Dict[str, Any], env: Dict[str, str]) -> bool:
    """Has this Claude session ever written a conversation to disk?

    Absence is the cleanest "there was never anything to rescue" signal, and it
    covers two cases the registry alone cannot separate: a session added and never
    started (no claude_session_id at all), and one started that never completed a
    turn - which HAS a claude_session_id registered but no transcript file.
    """

    from pathlib import Path

    try:
        tool_data = json.loads(row.get("tool_data") or "{}")
    except ValueError:
        return False
    claude_session_id = tool_data.get("claude_session_id")
    if not claude_session_id:
        return False
    projects = Path(env.get("HOME", "")) / ".claude" / "projects"
    try:
        return any(projects.glob("*/%s.jsonl" % claude_session_id))
    except OSError:
        return False


# ----------------------------------------- asking agent-deck for a session's output

# agent-deck lives at /opt/homebrew/bin/agent-deck. A hook inherits whatever PATH
# its parent had, which in this session includes that directory - but a peer
# session reported a hook that could not resolve it, so do not rely on PATH alone.
_AGENT_DECK_FALLBACKS = (
    "/opt/homebrew/bin/agent-deck",
    "/usr/local/bin/agent-deck",
)


def agent_deck_binary() -> Optional[str]:
    import shutil

    found = shutil.which("agent-deck")
    if found:
        return found
    for candidate in _AGENT_DECK_FALLBACKS:
        if os.access(candidate, os.X_OK):
            return candidate
    return None


def default_run(argv: Sequence[str], timeout: float):
    import subprocess

    return subprocess.run(list(argv), capture_output=True, text=True, timeout=timeout)


def probe_session_output(
    session_id: str, run=None, timeout: float = 20.0, tool: str = "claude"
) -> SessionOutput:
    """Ask agent-deck for a session's final output. THE single owner of this.

    Binary resolution, the argv, the subprocess-error catch and the response
    interpretation all live here together. They used to be written twice - once in
    the guard and once in the runner - and the copies drifted: deferring
    `import subprocess` in one of them left a dangling `subprocess.SubprocessError`
    in its except clause, so the "could not run agent-deck" branch became a
    NameError that Stage B's broad catch turned into an internal-error deny. The
    import and the except clause that needs it are now in the same function, where
    they cannot come apart.
    """
    import subprocess

    binary = agent_deck_binary()
    if binary is None:
        return SessionOutput(
            False, reason="agent-deck could not be found on PATH", code="unreachable"
        )
    runner = run if run is not None else default_run
    try:
        done = runner([binary, "session", "output", session_id, "--json"], timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        return SessionOutput(
            False, reason="could not run agent-deck: %s" % exc, code="unreachable"
        )
    return parse_session_output(done.stdout, tool)


# The verb table above was derived from `agent-deck --help` at this version. If
# agent-deck moves on, the table may be missing a command. --selftest compares
# and warns; the tier-2 backstop is what keeps the gap fail-closed meanwhile.
PINNED_AGENT_DECK_VERSION = "1.9.73"


def installed_agent_deck_version(run=None) -> Optional[str]:
    """Best-effort `agent-deck version`, or None. Never raises."""
    import subprocess

    binary = agent_deck_binary()
    if binary is None:
        return None
    runner = run if run is not None else default_run
    try:
        done = runner([binary, "version"], 10.0)
    except (OSError, subprocess.SubprocessError):
        return None
    for token in (done.stdout or "").split():
        stripped = token.lstrip("v")
        if stripped and stripped[0].isdigit():
            return stripped
    return None
