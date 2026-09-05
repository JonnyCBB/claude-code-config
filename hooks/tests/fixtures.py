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
