#!/usr/bin/env python3
"""Run the work-contract section 5 pre-close checklist and write the receipt.

    python3 ~/.claude/hooks/agent-deck-preclose.py <session-id|prefix|title>
    python3 ~/.claude/hooks/agent-deck-preclose.py --selftest

This is the half that makes the guard cheap to satisfy. A guard that costs more
than the convention it replaces gets designed around, and a routed-around guard
is worse than none because it still looks like protection.

Exit codes: 0 a passing receipt was written; 1 the checklist could not pass; 2 a
usage error.

FAILS LOUDLY. If the dump comes back empty, or the session cannot be resolved, or
a worktree that is about to be DELETED has uncommitted work, this writes a
receipt whose status is "failed" and exits non-zero. It never writes a passing
receipt it cannot justify - an empty dump that yields a valid receipt is exactly
the check-that-cannot-fail this project keeps producing.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import preclose_lib as lib  # noqa: E402
import preclose_receipt as receipt_mod  # noqa: E402

_GIT_TIMEOUT = 10.0


def _git(work: str, *args: str) -> subprocess.CompletedProcess:
    """Read-only git, never touching the index lock, never prompting."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    return subprocess.run(
        ["git", "-C", work, "--no-optional-locks", *args],
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT,
        env=env,
    )


def worktree_state(worktree_path: str) -> Dict[str, Any]:
    """Describe a session-owned git worktree.

    Only consulted when a removal passes --prune-worktree, which is the only form
    that deletes the worktree. A bare `remove`, even with --force, leaves the
    directory, its uncommitted files and its branch ref intact - verified
    behaviourally on 2026-08-18 - so blocking a bare removal on worktree state
    would refuse a removal that destroys nothing.

    Deliberately does NOT treat "HEAD is on no remote branch" as unclean. After a
    SQUASH merge, which is this repo's convention, a fully-merged branch's HEAD is
    contained in no remote branch, so that test would refuse the most common
    legitimate removal. The remote-containment count is recorded for a human, not
    enforced. What IS enforced is uncommitted work, which is the part a worktree
    deletion genuinely destroys.
    """
    if not worktree_path:
        return {
            "applicable": False,
            "reason": "shared checkout, not session-owned - nothing here belongs to "
            "this session alone",
        }
    if not os.path.isdir(worktree_path):
        return {
            "applicable": False,
            "reason": "recorded worktree %s no longer exists, so there is nothing "
            "left to lose" % worktree_path,
        }
    try:
        inside = _git(worktree_path, "rev-parse", "--is-inside-work-tree")
    except (OSError, subprocess.SubprocessError) as exc:
        return {"applicable": False, "reason": "could not run git: %s" % exc}
    if inside.returncode != 0:
        return {
            "applicable": False,
            "reason": "recorded worktree %s is no longer a git repository (already "
            "cleaned up)" % worktree_path,
        }

    porcelain = _git(worktree_path, "status", "--porcelain")
    if porcelain.returncode != 0:
        return {
            "applicable": True,
            "clean": False,
            "reason": "could not read git status: %s" % porcelain.stderr.strip(),
        }
    dirty = [line for line in porcelain.stdout.splitlines() if line.strip()]

    remote = _git(worktree_path, "branch", "-r", "--contains", "HEAD")
    on_remote = [line for line in remote.stdout.splitlines() if line.strip()]

    state: Dict[str, Any] = {
        "applicable": True,
        "path": worktree_path,
        "clean": not dirty,
        "uncommitted_paths": dirty[:20],
        "remote_branches_containing_head": len(on_remote),
    }
    if dirty:
        state["reason"] = "%d uncommitted or untracked path(s), including %s" % (
            len(dirty),
            ", ".join(entry[3:] or entry for entry in dirty[:3]),
        )
    else:
        state["reason"] = "clean (%d remote branch(es) contain HEAD)" % len(on_remote)
    return state


def _nothing_to_rescue(row: Dict[str, Any], env: Dict[str, str], probe=None) -> bool:
    """True when this session has never written a conversation to disk.

    Covers two cases the registry alone cannot separate, both of which would
    otherwise be permanently unremovable - since --all-errored is denied outright,
    that would cost the conductor the ability to clean up errored sessions at all:

      * added and never started: no claude_session_id
      * started but never completed a turn: claude_session_id registered, no
        transcript file, and `session output` returns the terminal pane

    Only applies to Claude sessions. A shell session's pane IS its output, so
    there is always something to record.

    Never true when the probe itself could not be RUN. That says nothing about
    whether the session produced output, so recording it as "nothing to rescue"
    would attest to the health of the tool rather than of the session - and a
    shell session would earn a passing receipt on a broken agent-deck.
    """
    if probe is not None and probe.code == "unreachable":
        return False
    if row["tool"] != "claude":
        # A non-Claude session has no transcript, so its pane is the only record
        # that ever existed. If the pane cannot be read the record is already gone,
        # and refusing achieves nothing except making the session unremovable
        # forever. Observed on a dead shell session: "failed to capture terminal
        # output: failed to capture history: exit status 1".
        return True
    return not lib.transcript_exists(row, env)


def _run_checklist(
    ref: str, env: Dict[str, str], run=None, out=sys.stdout, err=sys.stderr
) -> int:
    db_path = lib.state_db_path(env)
    try:
        row = lib.resolve_session(ref, db_path)
    except lib.AmbiguousReference as exc:
        err.write(
            "FAILED: %s\nName one session exactly; no receipt was written.\n" % exc
        )
        return 1
    except lib.RegistryUnavailable as exc:
        err.write("FAILED: cannot read the agent-deck registry: %s\n" % exc)
        return 1
    if row is None:
        err.write(
            "FAILED: no session matches %r in %s.\nNo receipt was written - there is "
            "no session id to key one on.\n" % (ref, db_path)
        )
        return 1

    session_id = row["id"]
    receipt_path = lib.receipt_path(session_id, env)
    dump_path = lib.dump_path(session_id, env)
    probe = lib.probe_session_output(session_id, run, 20.0, row["tool"])
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def write(
        status: str, reason: Optional[str], dump_bytes: int = 0, output_sha: str = ""
    ) -> None:
        """Closes over `worktree`, which is the same object at every call site."""
        receipt_mod.atomic_write_json(
            receipt_path,
            receipt_mod.build_receipt(
                session_id=session_id,
                session_title=row["title"],
                tool=row["tool"],
                status=status,
                reason=reason,
                generated_at=generated_at,
                dump_path=str(dump_path),
                dump_bytes=dump_bytes,
                output_sha256=output_sha,
                worktree=worktree,
            ),
        )

    worktree = worktree_state(row.get("worktree_path") or "")

    nothing_to_rescue = _nothing_to_rescue(row, env, probe)

    if (
        not probe.ok
        and probe.code != "screen"
        and not (nothing_to_rescue and row["tool"] != "claude")
    ):
        write("failed", "could not read the session's final output: %s" % probe.reason)
        err.write(
            "FAILED: could not read the final output of %s (%s): %s\n"
            "Wrote a FAILED receipt at %s. The removal stays blocked.\n"
            % (session_id, row["title"], probe.reason, receipt_path)
        )
        return 1

    content = probe.content
    output_sha = receipt_mod.sha256_text(content)
    screen_only = probe.code == "screen"

    if screen_only or not content.strip():
        if nothing_to_rescue:
            body = (
                "# %s (%s)\n\nThis session never produced any output.\n\n"
                "%s There is nothing to rescue, and this receipt records that "
                "rather than pretending a dump happened.\n"
                % (
                    row["title"],
                    session_id,
                    "It has no Claude conversation transcript on disk, so it was "
                    "either never started or never completed a turn."
                    if row["tool"] == "claude"
                    else "It is not a Claude session, so it has no transcript, and "
                    "its terminal pane is no longer readable: %s"
                    % (probe.reason or "no output available"),
                )
            )
            note_bytes = receipt_mod.atomic_write_text(dump_path, body)
            write(
                "passed",
                "nothing to rescue: session never produced output",
                note_bytes,
                output_sha,
            )
            out.write(
                "PASSED: %s (%s) never produced output; nothing to rescue.\n"
                "  note:    %s\n  receipt: %s\n"
                % (session_id, row["title"], dump_path, receipt_path)
            )
            return 0
        reason = (
            probe.reason
            if screen_only
            else "the session's final output came back empty"
        )
        write("failed", reason, output_sha=output_sha)
        err.write(
            "FAILED: could not capture a final answer from %s (%s).\n  %s\n"
            "This session HAS a transcript, so it has spoken before - refusing "
            "rather than recording nothing.\n"
            "Wrote a FAILED receipt at %s. The removal stays blocked.\n"
            % (session_id, row["title"], reason, receipt_path)
        )
        return 1

    dump_bytes = receipt_mod.atomic_write_text(dump_path, content)

    write("passed", None, dump_bytes, output_sha)
    out.write(
        "PASSED: pre-close checklist complete for %s (%s)\n"
        "  output:   %d bytes -> %s\n"
        "  worktree: %s\n"
        "  receipt:  %s\n"
        % (
            session_id,
            row["title"],
            dump_bytes,
            dump_path,
            worktree.get("reason", "n/a"),
            receipt_path,
        )
    )
    return 0


def selftest(env: Dict[str, str], out=sys.stdout, err=sys.stderr) -> int:
    """Prove the INSTALLED guard still refuses a removal.

    The unit tests exercise this worktree's copy. They cannot see the wiring in
    settings.json, which is the part that can silently go missing - a conflict
    resolution that drops it leaves a guard that is installed, inert and
    indistinguishable from a working one.

    So this reads the wired command STRING and EXECUTES IT, rather than checking
    that some entry mentions the filename. A typo in the wrapper would pass the
    weaker check.
    """
    home = Path(env.get("HOME", ""))
    settings_path = Path(
        env.get("PRECLOSE_SETTINGS") or (home / ".claude" / "settings.json")
    )
    checks: List[str] = []

    try:
        settings = json.loads(settings_path.read_text())
    except (OSError, ValueError) as exc:
        err.write("SELFTEST FAIL: cannot read %s: %s\n" % (settings_path, exc))
        return 1

    wired = None
    for entry in (settings.get("hooks", {}) or {}).get("PreToolUse", []) or []:
        for hook in entry.get("hooks", []) or []:
            command = hook.get("command", "")
            if "preclose_guard.py" in command or "agent-deck-preclose-guard" in command:
                wired = command
    if wired is None:
        err.write(
            "SELFTEST FAIL: no PreToolUse entry in %s invokes the pre-close guard.\n"
            "The guard is NOT armed. Removals are unguarded right now.\n"
            % settings_path
        )
        return 1
    checks.append("wiring present in %s" % settings_path)

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        conductor, target = "selftest-conductor", "selftest-target"
        db = lib.fixture_registry(
            [
                {"id": conductor, "title": "selftest-conductor", "is_conductor": 1},
                {"id": target, "title": "selftest-target", "tool": "shell"},
            ],
            root / "reg",
        )
        # The guard checks freshness by asking agent-deck for the target's current
        # output. These session ids are synthetic, so the real binary answers
        # NOT_FOUND and the guard correctly refuses - which would make the ALLOW
        # leg impossible and this command useless for its actual purpose. So the
        # selftest supplies a stub `agent-deck` first on PATH. What is being
        # proved here is that the INSTALLED WIRING reaches the guard and that the
        # guard refuses and permits on the receipt; agent-deck's own behaviour is
        # not what this check is for.
        stub_dir = root / "stub-bin"
        stub_dir.mkdir()
        stub = stub_dir / "agent-deck"
        stub.write_text(
            "#!/bin/sh\n"
            'printf \'{"content": "", "role": "assistant", "success": true}\'\n'
        )
        stub.chmod(0o755)

        probe_env = dict(env)
        probe_env.update(
            {
                "AGENTDECK_INSTANCE_ID": conductor,
                "PRECLOSE_STATE_DB": str(db),
                "PRECLOSE_EVIDENCE_ROOT": str(root / "evidence"),
                "PATH": "%s:%s" % (stub_dir, env.get("PATH", "/usr/bin:/bin")),
            }
        )
        payload = json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "agent-deck session remove %s" % target},
                "cwd": str(root),
            }
        )

        def drive() -> subprocess.CompletedProcess:
            return subprocess.run(
                ["bash", "-c", wired],
                input=payload,
                capture_output=True,
                text=True,
                env=probe_env,
                timeout=30,
            )

        denied = drive()
        if denied.returncode != 2:
            err.write(
                "SELFTEST FAIL: the wired guard did NOT deny a removal with no receipt.\n"
                "  exit=%s stdout=%r stderr=%r\n"
                "A guard that cannot refuse is not a guard.\n"
                % (denied.returncode, denied.stdout[:200], denied.stderr[:300])
            )
            return 1
        checks.append("wired command DENIED a removal with no receipt (exit 2)")

        dump = lib.dump_path(target, probe_env)
        dump.parent.mkdir(parents=True, exist_ok=True)
        dump.write_text("selftest output\n")
        receipt_mod.atomic_write_json(
            lib.receipt_path(target, probe_env),
            receipt_mod.build_receipt(
                session_id=target,
                session_title="selftest-target",
                tool="shell",
                status="passed",
                reason=None,
                generated_at="1970-01-01T00:00:00Z",
                dump_path=str(dump),
                dump_bytes=dump.stat().st_size,
                output_sha256=receipt_mod.sha256_text(""),
                worktree={"applicable": False, "reason": "selftest"},
            ),
        )
        allowed = drive()
        if allowed.returncode != 0:
            err.write(
                "SELFTEST FAIL: the wired guard did NOT allow a removal WITH a valid "
                "receipt.\n  exit=%s stderr=%r\n"
                "A guard that cannot be satisfied will be worked around.\n"
                % (allowed.returncode, allowed.stderr[:400])
            )
            return 1
        checks.append("wired command ALLOWED the same removal once a receipt existed")

    installed = lib.installed_agent_deck_version()
    if installed and installed != lib.PINNED_AGENT_DECK_VERSION:
        out.write(
            "  WARN: agent-deck is %s but the destructive-command table was derived\n"
            "        from %s. Re-check `agent-deck --help` for new commands that\n"
            "        destroy a session. Unrecognised destructive verbs still fail\n"
            "        closed, so this is a staleness warning, not a hole.\n"
            % (installed, lib.PINNED_AGENT_DECK_VERSION)
        )

    for check in checks:
        out.write("  ok: %s\n" % check)
    out.write("SELFTEST PASS: the installed guard refuses and permits correctly.\n")
    return 0


def main(argv: Sequence[str], env: Dict[str, str], run=None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-deck-preclose",
        description="Run the pre-close checklist for an agent-deck session and "
        "write the receipt the removal guard checks.",
    )
    parser.add_argument("session", nargs="?", help="session id, id prefix, or title")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="prove the INSTALLED guard still refuses a removal",
    )
    try:
        args = parser.parse_args(list(argv))
    except SystemExit as exc:
        return int(exc.code or 2)

    if args.selftest:
        return selftest(env)
    if not args.session:
        parser.print_usage(sys.stderr)
        sys.stderr.write("agent-deck-preclose: a session reference is required\n")
        return 2
    return run_checklist(args.session, env, run)


def run_checklist(ref, env, run=None, out=sys.stdout, err=sys.stderr) -> int:
    """Wrapper that turns an unwritable evidence tree into a clean failure.

    Without it a PermissionError on ~/evidence escapes as a traceback, which
    contradicts this module's promise to fail loudly rather than messily. The
    removal stays blocked either way - no receipt is written - but an operator
    mid-task deserves a sentence rather than a stack.
    """
    try:
        return _run_checklist(ref, env, run, out, err)
    except OSError as exc:
        err.write(
            "FAILED: could not write evidence for %r: %s\n"
            "Nothing was recorded, so the removal stays blocked. Check that %s is\n"
            "writable.\n" % (ref, exc, lib.evidence_root(env))
        )
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], dict(os.environ)))
