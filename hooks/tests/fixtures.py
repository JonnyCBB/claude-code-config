#!/usr/bin/env python3
"""Shared test fixtures: hook payloads and fake agent-deck output."""

from __future__ import annotations

import json
import subprocess


def payload(command, tool_name="Bash", cwd="/tmp"):
    """A PreToolUse payload with the fields observed live on 2026-08-18."""
    return json.dumps(
        {
            "session_id": "11111111-2222-3333-4444-555555555555",
            "transcript_path": "/dev/null",
            "cwd": cwd,
            "permission_mode": "acceptEdits",
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {"command": command, "description": "test"},
            "tool_use_id": "toolu_test",
        }
    )


def fake_output(content, success=True, not_found=False, chrome=False):
    """Stand in for `agent-deck session output <id> --json`.

    Mirrors the real shape including its three traps: exit code 0 in every case,
    `success: true` with empty content for a session that never spoke, and - when
    chrome=True - the tmux pane returned as `content` with an EMPTY timestamp for
    a running session that has not answered yet.
    """
    if not_found:
        body = {"code": "NOT_FOUND", "error": "session not found", "success": False}
    elif chrome:
        body = {
            "content": "\u2500" * 80 + "\n Accessing workspace:\n",
            "role": "assistant",
            "success": True,
            "timestamp": "",
        }
    else:
        body = {
            "content": content,
            "role": "assistant",
            "success": success,
            # A real assistant message carries a timestamp; terminal chrome does
            # not. That is what separates them.
            "timestamp": "2026-08-18T17:09:32.867Z" if content else "",
        }

    def run(argv, timeout):
        return subprocess.CompletedProcess(list(argv), 0, json.dumps(body), "")

    return run


def failing_run(exc=None):
    """A runner that RAISES, standing in for agent-deck being unrunnable.

    Nothing covered this until 2026-08-18, which is how a dangling
    `subprocess.SubprocessError` reference survived in the guard: every existing
    fake returned a CompletedProcess, so the except clause was never reached.
    """
    error = exc if exc is not None else OSError("simulated exec failure")

    def run(argv, timeout):
        raise error

    return run


ACTIVITY = "100"


def fake_deck(
    content="",
    *,
    panes=None,
    activity=ACTIVITY,
    live=None,
    capture_rc=0,
    list_rc=0,
    not_found=False,
    chrome=False,
):
    """One runner standing in for both binaries the checklist shells out to.

    Dispatches on the tmux VERB appearing anywhere in argv, never on a fixed
    position: with a socket name set the argv is [tmux, "-L", sock, "has-session",
    ...], so keying on argv[1] sent the tmux calls to the agent-deck stub.

    It models tmux's TARGET rules, because the code under test is built around
    them: `-t=NAME` matches an exact session name only, plain `-t NAME` falls back
    to a unique prefix, and capture-pane and list-panes reject the `=` form
    outright. Pass `live={...}` to describe which sessions exist and the prefix
    hazard becomes expressible; leave it out and any name resolves.

    `panes` is the successive results of `capture-pane`; the last one repeats.
    `panes=None` means the terminal is gone. `panes=[""]` means it reads empty,
    which is a different thing and must not be spelled `panes=[]`.
    """
    deck = fake_output(content, not_found=not_found, chrome=chrome)
    reads = list(panes) if panes else []
    names = set(live) if live else set()

    def done(argv, code=0, stdout="", stderr=""):
        return subprocess.CompletedProcess(list(argv), code, stdout, stderr)

    def target(argv):
        for index, token in enumerate(argv):
            if token.startswith("-t="):
                return token[3:], True
            if token == "-t" and index + 1 < len(argv):
                return argv[index + 1], False
        return "", False

    def resolves(name, exact_form):
        if not names:
            return bool(reads)
        if name in names:
            return True
        if exact_form:
            return False
        return len([n for n in names if n.startswith(name)]) == 1

    def run(argv, timeout):
        if "has-session" in argv:
            name, exact_form = target(argv)
            if resolves(name, exact_form):
                return done(argv)
            return done(argv, 1, "", "can't find session: %s" % name)
        if "capture-pane" in argv or "list-panes" in argv:
            name, exact_form = target(argv)
            if exact_form:
                return done(argv, 1, "", "can't find pane: =%s" % name)
            if "capture-pane" in argv:
                if capture_rc:
                    return done(argv, capture_rc, "", "no current client")
                return done(argv, 0, reads.pop(0) if len(reads) > 1 else reads[0])
            if list_rc:
                return done(argv, list_rc, "", "no server running")
            return done(argv, 0, activity + "\n")
        return deck(argv, timeout)

    return run
