#!/usr/bin/env python3
"""PreToolUse hook: refuse an agent-deck session removal until the pre-close
checklist has provably run for every target.

THE FAIL DIRECTION IS DELIBERATE AND ASYMMETRIC. Read this before changing it.

  Stage A -- applicability. Is this a Bash call, is it a session removal, and is
             the caller the conductor? ANY error here ALLOWS, silently. A bug in
             this stage must never wedge unrelated commands in unrelated
             sessions, and this hook is wired globally.

  Stage B -- proof. Does every target session have a valid receipt? ANY error
             here DENIES. By this point the guard has established that the
             conductor is destroying a session, so an error means "I cannot prove
             this is safe", and the honest answer to that is no.

The bead asked for fail-open on internal errors, which protects against wedging.
This split protects against wedging AND against silent disarmament - a guard that
has quietly become a no-op is indistinguishable from one that works, which is the
worse of the two failures. Catching broadly into a DENY is not the trap; the trap
is catching broadly into an ALLOW.

Deny is exit 2 with a message on stderr, which the harness passes to the model
verbatim. Never a prompt. Nothing is ever written to stdout: the harness treats
malformed stdout JSON as a non-blocking error, and exit 2 blocks unconditionally
only when stdout is not competing with it.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import preclose_lib as lib  # noqa: E402
import preclose_receipt as preclose_receipt  # noqa: E402

# The wiring sets "timeout": 10. Stay well inside it: a hook the harness kills
# renders no decision and the tool call proceeds, so overrunning the budget is a
# silent fail-open. One connection per target plus one subprocess per target
# means the budget has to be shared, not per-call.
_TOTAL_BUDGET_SECONDS = 7.0

RUNNER = "python3 ~/.claude/hooks/agent-deck-preclose.py"


def _log(env: Dict[str, str], message: str) -> None:
    """Record a guard-internal problem. Must never raise, for any reason.

    This is the only trace a silently-degraded guard leaves, so a full disk or a
    permissions problem here must not turn a clean fail-open into an unhandled
    exception.
    """
    try:
        path = lib.guard_log_path(env)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(path), "a") as stream:
            stream.write("%s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), message))
    except BaseException:
        pass


def live_output(session_id: str, run, deadline: float, tool: str = "claude"):
    """What this session's final output is RIGHT NOW, as a SessionOutput.

    Returns None only when there was no budget left to ask. The receipt validator
    needs the whole record, not just a hash: "agent-deck says it cannot read that
    session" is consistent with a receipt that recorded nothing to rescue, and
    contradicts one that recorded real content.
    """
    remaining = deadline - time.monotonic()
    if remaining <= 0.2:
        return None
    return lib.probe_session_output(session_id, run, min(remaining, 5.0), tool)


# Stage A's three possible answers. "unverifiable" is not an error in the guard;
# it is a determination that the removal cannot be checked - and, crucially, could
# not have succeeded either.
APPLIES = "applies"
NOT_APPLICABLE = "not-applicable"
UNVERIFIABLE = "unverifiable"


def guard_applies(env: Dict[str, str]) -> str:
    """Decide whether this caller's removal must be checked.

    The signal is the calling session's own agent-deck row: AGENTDECK_INSTANCE_ID
    from the environment, looked up against `is_conductor` in the registry.

    There is deliberately NO working-directory fallback. `cwd` follows a `cd` -
    the harness has a CwdChanged event because of it - so a guard scoped on cwd
    silently stops applying the moment someone changes directory, and nobody
    notices. A signal that can quietly switch off is worse than no signal.

    What replaces it: if the registry cannot be read AT ALL, deny regardless of
    caller. `agent-deck session remove` needs that same database to delete the
    row, so a removal this guard cannot check is one that could not have succeeded
    anyway. Denying refuses nothing that would have worked, and it closes the hole
    where an unreadable registry silently disarms the guard.

    A LOCKED database is different and must not deny. agent-deck writes this file
    constantly, so SQLITE_BUSY is transient and waiting fixes it - refusing a
    worker's removal over a passing lock is the false refusal that gets a guard
    routed around.

    Never raises: every failure resolves to one of the three answers here, because
    this is the only place allowed to turn an error into "allow".
    """
    instance_id = env.get("AGENTDECK_INSTANCE_ID")
    try:
        if not instance_id:
            # Not launched by agent-deck, so not the conductor. Nothing to check.
            return NOT_APPLICABLE
        verdict = lib.is_conductor(instance_id, lib.state_db_path(env))
    except lib.RegistryUnavailable as exc:
        if exc.transient:
            _log(env, "registry busy, allowing (a lock is transient): %s" % exc)
            return NOT_APPLICABLE
        _log(env, "registry unreadable, denying: %s" % exc)
        return UNVERIFIABLE
    except BaseException as exc:
        _log(env, "unexpected error in applicability, allowing: %r" % exc)
        return NOT_APPLICABLE
    if verdict is None:
        # Registry readable, but this session is not in it - a stale environment
        # variable or a creation race. No evidence this is the conductor, and the
        # removal would work fine, so stay out of the way.
        _log(env, "instance %s absent from a readable registry, allowing" % instance_id)
        return NOT_APPLICABLE
    return APPLIES if verdict else NOT_APPLICABLE


def _deny(message: str) -> int:
    sys.stderr.write(message if message.endswith("\n") else message + "\n")
    return 2


def _bulk_denial() -> int:
    return _deny(
        "BLOCKED: pre-close checklist not verified.\n"
        "This command destroys several sessions at once, and this guard will not "
        "approve them as a group - each one may hold output that exists nowhere "
        "else.\n"
        "Close them one at a time:\n"
        "  agent-deck list --json\n"
        "  %s <session-id>\n"
        "  agent-deck session remove <session-id>\n" % RUNNER
    )


def _check_targets(
    removal: lib.Removal, env: Dict[str, str], run, deadline: float
) -> List[Tuple[str, str]]:
    """Return (ref, problem) for every target that cannot be proved safe."""
    db_path = lib.state_db_path(env)
    problems: List[Tuple[str, str]] = []
    for ref in removal.refs:
        if ref.startswith("$"):
            problems.append(
                (
                    ref,
                    "looks like an unexpanded shell variable, so no session could "
                    "be identified",
                )
            )
            continue
        try:
            row = lib.resolve_session(ref, db_path)
        except lib.AmbiguousReference as exc:
            problems.append((ref, "ambiguous reference - %s" % exc))
            continue
        except lib.RegistryUnavailable as exc:
            problems.append(
                (
                    ref,
                    "cannot read the agent-deck registry, so the checklist cannot "
                    "be confirmed (%s)" % exc,
                )
            )
            continue
        if row is None:
            problems.append((ref, "no such session in the agent-deck registry"))
            continue
        verdict = preclose_receipt.validate_receipt(
            lib.receipt_path(row["id"], env),
            expected_session_id=row["id"],
            expected_tool=row["tool"],
            live_output=lambda row=row: live_output(
                row["id"], run, deadline, row["tool"]
            ),
            require_worktree_clean=removal.prune_worktree,
        )
        if not verdict.ok:
            problems.append((row["id"], verdict.reason or "receipt is not valid"))
    return problems


def main(stdin_text: str, env: Dict[str, str], run=None) -> int:
    """Return 0 to allow, 2 to deny. See the module docstring for fail direction."""
    deadline = time.monotonic() + _TOTAL_BUDGET_SECONDS

    # ---------- Stage A. Any failure here ALLOWS, silently. ----------
    try:
        payload = json.loads(stdin_text)
        if not isinstance(payload, dict):
            return 0
        if payload.get("tool_name") != "Bash":
            return 0
        tool_input = payload.get("tool_input")
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        if not isinstance(command, str) or not command.strip():
            return 0
        removal = lib.find_removal(command)
        if removal is None:
            return 0
        applicability = guard_applies(env)
        if applicability == NOT_APPLICABLE:
            return 0
    except BaseException as exc:
        _log(env, "Stage A error, allowing (fail open): %r" % exc)
        return 0

    # ---------- Stage B. Confirmed: the conductor is destroying a session. ----
    # Any failure from here DENIES. Do not add a branch that returns 0.
    try:
        if applicability == UNVERIFIABLE:
            return _deny(
                "BLOCKED: the agent-deck registry could not be read, so this guard\n"
                "cannot confirm the pre-close checklist ran.\n"
                "Removing a session needs that same database to delete its row, so\n"
                "this removal could not have succeeded either. Nothing is lost by\n"
                "retrying once the registry is readable.\n"
                "Looked in:\n%s\n"
                % "\n".join("  %s" % c for c in lib.state_db_candidates(env))
            )
        if removal.bulk:
            return _bulk_denial()
        if removal.unparsed or not removal.refs:
            return _deny(
                "BLOCKED: pre-close checklist not verified.\n"
                "This guard could not work out which sessions the command targets, so "
                "it cannot confirm their final output was saved. Remove them one at a "
                "time:\n"
                "  %s <session-id>\n"
                "  agent-deck session remove <session-id>\n" % RUNNER
            )

        problems = _check_targets(removal, env, run, deadline)
        if not problems:
            return 0

        lines = [
            "BLOCKED: pre-close checklist not verified for this removal.",
            "",
            "Work-contract section 5 requires a session's final output to be saved to a",
            "durable path before the session is destroyed. On 2026-08-18 that rescued the",
            "only copy of three sessions' output.",
            "",
        ]
        for ref, problem in problems:
            lines.append("  %s" % ref)
            lines.append("      %s" % problem)
        lines.append("")
        lines.append("Run the checklist, then retry the removal:")
        for ref, _problem in problems:
            lines.append("  %s %s" % (RUNNER, ref))
        return _deny("\n".join(lines))
    except BaseException as exc:
        _log(env, "Stage B error, DENYING (fail closed): %r" % exc)
        return _deny(
            "BLOCKED: the pre-close guard hit an internal error, so it cannot confirm\n"
            "the checklist ran. This is a bug in the guard, not in your command.\n"
            "Details: %s\n"
            "`agent-deck session stop` is NOT guarded, so capacity can still be freed.\n"
            % lib.guard_log_path(env)
        )


if __name__ == "__main__":
    try:
        sys.exit(main(sys.stdin.read(), dict(os.environ)))
    except SystemExit:
        raise
    except KeyboardInterrupt:
        sys.exit(130)
    except BaseException as exc:
        # Only reachable if Stage A's own wrapper failed, i.e. before the guard
        # knew whether it applied. Fail OPEN and stay silent; the log is how a
        # persistently broken guard is discovered.
        _log(dict(os.environ), "entry-point error, allowing (fail open): %r" % exc)
        sys.exit(0)
