#!/usr/bin/env python3
"""Build receipts for tests THROUGH the production builder.

Deliberately not a hand-written dict: the schema has one owner
(preclose_receipt.build_receipt) so a test fixture cannot drift from the format
the guard actually validates.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import preclose_receipt as receipt_mod  # noqa: E402

NOT_APPLICABLE = {"applicable": False, "reason": "test fixture"}


def write_receipt(
    path,
    *,
    session_id="sess-1",
    session_title="a-session",
    tool="claude",
    status="passed",
    reason=None,
    generated_at="2026-08-18T00:00:00Z",
    dump_path=None,
    dump_bytes=None,
    output_text="the final answer",
    worktree=None,
    overrides=None,
):
    """Write a receipt that is VALID by default.

    Writes a real non-empty dump file next to the receipt unless dump_path is
    given, so the default genuinely passes validation. An earlier fixture
    defaulted to /dev/null, which is size 0 and was rejected by the empty-dump
    check - so every caller had to override it and a naive caller got a deny and
    went debugging the guard.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if dump_path is None:
        dump = path.parent / (session_id + "-final.md")
        dump.write_text(output_text)
        dump_path = str(dump)
        dump_bytes = dump.stat().st_size
    elif dump_bytes is None:
        dump_bytes = Path(dump_path).stat().st_size if Path(dump_path).exists() else 0

    payload = receipt_mod.build_receipt(
        session_id=session_id,
        session_title=session_title,
        tool=tool,
        status=status,
        reason=reason,
        generated_at=generated_at,
        dump_path=dump_path,
        dump_bytes=dump_bytes,
        output_sha256=receipt_mod.sha256_text(output_text),
        worktree=worktree if worktree is not None else dict(NOT_APPLICABLE),
    )
    if overrides:
        payload.update(overrides)
    receipt_mod.atomic_write_json(path, payload)
    return payload
