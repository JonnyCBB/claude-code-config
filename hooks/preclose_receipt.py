#!/usr/bin/env python3
"""The pre-close receipt: machine-checkable proof that the checklist ran.

Written by the runner, read by the guard. One module owns the format so the
writer and the reader cannot drift apart - two implementations of one schema is
how a check silently stops matching.

WHY THE FRESHNESS CHECK IS A CONTENT HASH AND NOT A TRANSCRIPT FINGERPRINT.
An earlier design recorded the Claude transcript's (mtime, size) and required
them unchanged, on the strength of one observation that `agent-deck session stop`
leaves the transcript byte-identical. That was n=1 and the wider census killed it:
across 40 live transcripts the LAST record is an `assistant` message in exactly
one. The others end in `last-prompt` (26), `system`, `permission-mode`,
`queue-operation`, `pr-link` or `attachment` - all of which append bytes without
the session producing any new output. Byte identity would therefore invalidate
receipts for reasons unrelated to the rescued content, and the official docs also
warn the transcript "is written asynchronously and may lag".

So the receipt records the SHA-256 of what `agent-deck session output` returned,
and the guard re-runs that command and compares. That answers the actual question
- has this session produced new output since it was dumped - with no transcript
parsing, no path globbing and no race.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, NamedTuple, Optional

SCHEMA_VERSION = 1


class ReceiptVerdict(NamedTuple):
    """Whether a receipt proves the checklist ran, and if not, why not."""

    ok: bool
    reason: Optional[str] = None


def sha256_text(text: str) -> str:
    # Imported here rather than at module scope: this module is reachable from a
    # hook that runs on every Bash call, and nothing here is needed until a
    # removal has actually been detected. hashlib costs 2.1 ms, tempfile 5.5 ms.
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_write_text(path: Path, text: str) -> int:
    """Write text so a reader never sees a half-written file. Returns bytes written.

    Owner-only by construction. tempfile.mkstemp creates with mode 0600 whatever
    the umask, where Path.write_text uses 0666 & ~umask - measured 0644 on this
    machine, against 0600 for the receipt beside it. The file this writes holds a
    session's actual final output, so it is the MORE sensitive of the two
    artifacts and it had the weaker permissions.

    The temp file must live in the destination directory: os.replace is atomic
    only within one filesystem, so a crash leaves either the previous committed
    content or the new content, never a torn final file.
    """
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix="." + path.name + "."
    )
    try:
        with os.fdopen(handle, "w") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, str(path))
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return len(text.encode("utf-8"))


def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write JSON atomically, owner-only. Delegates so there is one policy."""
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def build_receipt(
    *,
    session_id: str,
    session_title: str,
    tool: str,
    status: str,
    reason: Optional[str],
    generated_at: str,
    dump_path: str,
    dump_bytes: int,
    output_sha256: str,
    worktree: Dict[str, Any],
) -> Dict[str, Any]:
    """Assemble a receipt. Keyword-only: a transposed status/reason would be silent."""
    if status not in ("passed", "failed"):
        raise ValueError("status must be 'passed' or 'failed', got %r" % (status,))
    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        # session_title and generated_at are for a HUMAN reading ~/evidence.
        # Nothing validates them. Do not make either load-bearing: titles drift
        # (a probe session renamed itself twice mid-test) and freshness is the
        # output hash, never a timestamp.
        "session_title": session_title,
        "generated_at": generated_at,
        "tool": tool,
        "status": status,
        "reason": reason,
        "dump": {"path": dump_path, "byte_size": dump_bytes},
        "output": {"sha256": output_sha256},
        "worktree": worktree,
    }


def _stat(path: Any) -> Optional[os.stat_result]:
    """Total: any unusable path yields None rather than raising.

    An earlier version caught only OSError, so a receipt whose path field was
    null raised TypeError out of validate_receipt and out of the guard's main -
    which the entry point then turned into a deny with an internal-error message.
    A malformed receipt must be an INVALID receipt, not a crash.
    """
    if not isinstance(path, (str, bytes, os.PathLike)):
        return None
    try:
        return os.stat(path)
    except (OSError, ValueError):
        return None


def _worktree_verdict(receipt, require_worktree_clean: bool) -> ReceiptVerdict:
    """The last gate: a removal that DELETES the worktree needs it clean."""
    if not require_worktree_clean:
        return ReceiptVerdict(True)
    worktree = receipt.get("worktree") or {}
    if not worktree.get("applicable"):
        return ReceiptVerdict(
            False,
            "this removal would DELETE the git worktree but the receipt records no "
            "worktree state: %s" % (worktree.get("reason") or "no reason recorded"),
        )
    if not worktree.get("clean"):
        return ReceiptVerdict(
            False,
            "this removal would DELETE the git worktree and it has uncommitted "
            "work: %s" % (worktree.get("reason") or "no reason recorded"),
        )
    return ReceiptVerdict(True)


def validate_receipt(
    path: Path,
    *,
    expected_session_id: str,
    expected_tool: str,
    live_output,
    require_worktree_clean: bool,
) -> ReceiptVerdict:
    """Decide whether `path` proves the checklist ran for `expected_session_id`.

    Never raises for a bad receipt: unreadable, malformed and nonsensical are all
    INVALID, because "cannot prove valid" and "invalid" are the same answer.

    `expected_tool` comes from the agent-deck registry, NOT from the receipt. A
    receipt that self-declared `tool: "shell"` could otherwise skip the freshness
    check entirely.

    `live_output` is a CALLABLE returning the session's current output as a
    SessionOutput. It is a callable rather than a value because obtaining it costs
    a ~25 ms subprocess, and most of the rejections below are decided without it.

    A receipt recording that there was NOTHING to rescue needs different treatment
    from one recording real content. If the runner saved a real answer, the guard
    must see that same answer now or refuse. But if the runner recorded an empty
    output - a session that never produced anything - then agent-deck answering
    "I cannot read that session" now is CONSISTENT with the receipt, not a
    contradiction: there was nothing then and there is nothing now. Demanding a
    readable hash in that case made every never-started session permanently
    unremovable, which is a check that cannot pass.

    The exception is the tool itself being unrunnable ("unreachable"), which tells
    us nothing about the session and still refuses.

    It is a callable rather than a value because obtaining it costs a ~25 ms
    subprocess, and five of the eight rejections below - missing receipt, bad
    JSON, unknown schema, wrong session, wrong tool, failed status, missing or
    resized dump - are decided without it. Passing the value eagerly spawned one
    agent-deck probe per target even when no receipt existed at all.
    """
    try:
        with open(str(path), "r") as stream:
            raw = stream.read()
    except OSError:
        return ReceiptVerdict(False, "no pre-close receipt at %s" % path)

    try:
        receipt = json.loads(raw)
    except ValueError as exc:
        return ReceiptVerdict(False, "receipt %s is not valid JSON: %s" % (path, exc))
    if not isinstance(receipt, dict):
        return ReceiptVerdict(False, "receipt %s is not a JSON object" % path)

    version = receipt.get("schema_version")
    if version != SCHEMA_VERSION:
        if isinstance(version, int) and version > SCHEMA_VERSION:
            return ReceiptVerdict(
                False,
                "receipt %s was written by a NEWER runner (schema %s, this guard "
                "understands %d). Re-running the runner will not help - reinstall "
                "~/.claude/hooks so guard and runner match."
                % (path, version, SCHEMA_VERSION),
            )
        return ReceiptVerdict(
            False,
            "receipt %s has unrecognised schema_version %r; this guard understands %d"
            % (path, version, SCHEMA_VERSION),
        )

    if receipt.get("session_id") != expected_session_id:
        return ReceiptVerdict(
            False,
            "receipt %s is for a different session (%r, expected %r)"
            % (path, receipt.get("session_id"), expected_session_id),
        )

    if receipt.get("tool") != expected_tool:
        return ReceiptVerdict(
            False,
            "receipt %s records tool %r but the registry says %r, so it does not "
            "describe this session as it is now"
            % (path, receipt.get("tool"), expected_tool),
        )

    if receipt.get("status") != "passed":
        return ReceiptVerdict(
            False,
            "the last pre-close run for %s did not pass: %s"
            % (expected_session_id, receipt.get("reason") or "no reason recorded"),
        )

    dump = receipt.get("dump") or {}
    dump_stat = _stat(dump.get("path"))
    if dump_stat is None:
        return ReceiptVerdict(
            False, "the recorded dump %r is missing or unreadable" % (dump.get("path"),)
        )
    if dump_stat.st_size == 0:
        return ReceiptVerdict(False, "the recorded dump %s is empty" % dump.get("path"))
    if dump_stat.st_size != dump.get("byte_size"):
        return ReceiptVerdict(
            False,
            "the recorded dump %s changed size (now %d, receipt says %r)"
            % (dump.get("path"), dump_stat.st_size, dump.get("byte_size")),
        )

    output = receipt.get("output") or {}
    recorded = output.get("sha256")
    if not isinstance(recorded, str) or not recorded:
        return ReceiptVerdict(
            False, "receipt %s records no output fingerprint to compare against" % path
        )
    live = live_output() if callable(live_output) else live_output
    recorded_nothing = recorded == sha256_text("")

    if live is None or not getattr(live, "ok", False):
        code = (
            getattr(live, "code", "unreachable") if live is not None else "unreachable"
        )
        if recorded_nothing and code in ("unknown", "screen"):
            # agent-deck answered and there is nothing readable, exactly as the
            # receipt says. Consistent, so this is not a reason to refuse.
            return _worktree_verdict(receipt, require_worktree_clean)
        return ReceiptVerdict(
            False,
            "could not read this session's current output, so this guard cannot "
            "confirm it has said nothing since the checklist ran. Usual causes: "
            "the agent-deck binary is not runnable from this hook, or agent-deck "
            "no longer recognises the session id.",
        )

    if sha256_text(live.content) != recorded:
        return ReceiptVerdict(
            False,
            "the session has produced new output since the checklist ran, so the "
            "saved copy is no longer its final word",
        )

    return _worktree_verdict(receipt, require_worktree_clean)
