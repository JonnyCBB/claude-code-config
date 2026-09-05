#!/usr/bin/env python3
"""Unit and subprocess tests for the pre-close guard."""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fixtures  # noqa: E402
import preclose_guard as guard  # noqa: E402
import receipt_helpers  # noqa: E402
import registry_helpers  # noqa: E402

ENTRY = Path(__file__).resolve().parents[1] / "preclose_guard.py"
CONDUCTOR = "cond-1111"
WORKER = "work-2222"
TARGET = "targ-3333"
OUTPUT = "the final answer"


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = registry_helpers.temp_registry(
            [
                {"id": CONDUCTOR, "title": "conductor-hq", "is_conductor": 1},
                {"id": WORKER, "title": "a-worker"},
                {"id": TARGET, "title": "a-target", "tool": "claude"},
            ],
            self.root / "reg",
        )

    def env(self, instance_id, db=None):
        return {
            "HOME": str(self.root),
            "AGENTDECK_INSTANCE_ID": instance_id,
            "PRECLOSE_STATE_DB": str(db or self.db),
            "PRECLOSE_EVIDENCE_ROOT": str(self.root / "evidence"),
        }

    def run_guard(self, command, instance_id, cwd="/tmp", output=OUTPUT, db=None):
        return guard.main(
            fixtures.payload(command, cwd=cwd),
            self.env(instance_id, db),
            run=fixtures.fake_output(output),
        )

    def give_receipt(self, session_id=TARGET, **kwargs):
        receipt_helpers.write_receipt(
            self.root / "evidence" / "preclose" / (session_id + ".json"),
            session_id=session_id,
            output_text=OUTPUT,
            **kwargs,
        )

    # ---- the three observations, as unit cases ----

    def test_a_conductor_removal_without_a_receipt_is_denied(self):
        self.assertEqual(
            self.run_guard("agent-deck session remove %s" % TARGET, CONDUCTOR), 2
        )

    def test_b_the_same_removal_is_allowed_once_a_receipt_exists(self):
        self.give_receipt()
        self.assertEqual(
            self.run_guard("agent-deck session remove %s" % TARGET, CONDUCTOR), 0
        )

    def test_c_a_worker_removal_passes_through_and_says_nothing(self):
        stderr = io.StringIO()
        stdout = io.StringIO()
        with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
            code = self.run_guard("agent-deck session remove %s" % TARGET, WORKER)
        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(stdout.getvalue(), "")

    # ---- scope ----

    def test_stop_is_never_guarded(self):
        self.assertEqual(
            self.run_guard("agent-deck session stop %s" % TARGET, CONDUCTOR), 0
        )

    def test_non_bash_tools_are_ignored(self):
        code = guard.main(
            fixtures.payload("anything", tool_name="Read"), self.env(CONDUCTOR)
        )
        self.assertEqual(code, 0)

    def test_bulk_removal_is_denied_outright_and_says_why(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = self.run_guard("agent-deck session remove --all-errored", CONDUCTOR)
        self.assertEqual(code, 2)
        # Must be the BULK message, not the generic "could not work out which
        # sessions" one - both return 2, so the exit code alone cannot tell them
        # apart and a regression routing bulk through the generic path would pass.
        self.assertIn("one at a time", stderr.getvalue())
        self.assertEqual(
            self.run_guard("agent-deck worktree cleanup --force", CONDUCTOR), 2
        )

    def test_a_dry_run_cleanup_is_not_treated_as_destructive(self):
        # `worktree cleanup` lists until --force; denying it told the operator it
        # "destroys several sessions at once", which was false.
        self.assertEqual(self.run_guard("agent-deck worktree cleanup", CONDUCTOR), 0)
        self.assertEqual(
            self.run_guard("agent-deck conductor teardown infra", CONDUCTOR), 0
        )

    def test_an_unrecognised_destructive_verb_denies_through_main(self):
        # The tier-2 backstop is this feature's stated reason for existing, and it
        # was only ever driven through find_removal in isolation.
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = self.run_guard("agent-deck session delete %s" % TARGET, CONDUCTOR)
        self.assertEqual(code, 2)
        self.assertIn("could not work out which sessions", stderr.getvalue())

    def test_worktree_finish_demands_a_clean_worktree(self):
        # It deletes the worktree unconditionally, so a valid receipt is not
        # enough - the worktree state has to have been recorded and clean.
        self.assertEqual(
            self.run_guard("agent-deck worktree finish %s" % TARGET, CONDUCTOR), 2
        )
        self.give_receipt()  # worktree not applicable by default
        self.assertEqual(
            self.run_guard("agent-deck worktree finish %s" % TARGET, CONDUCTOR), 2
        )
        self.give_receipt(
            worktree={"applicable": True, "clean": True, "reason": "clean"}
        )
        self.assertEqual(
            self.run_guard("agent-deck worktree finish %s" % TARGET, CONDUCTOR), 0
        )

    def test_semicolon_chained_removal_is_guarded(self):
        self.assertEqual(
            self.run_guard(
                "agent-deck session stop %s; agent-deck session remove %s"
                % (TARGET, TARGET),
                CONDUCTOR,
            ),
            2,
        )

    # ---- proof ----

    def test_new_output_since_the_dump_denies(self):
        self.give_receipt()
        code = self.run_guard(
            "agent-deck session remove %s" % TARGET, CONDUCTOR, output="something newer"
        )
        self.assertEqual(code, 2)

    def test_terminal_chrome_is_treated_as_unknown_not_as_new_output(self):
        self.give_receipt()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = guard.main(
                fixtures.payload("agent-deck session remove %s" % TARGET),
                self.env(CONDUCTOR),
                run=fixtures.fake_output("", chrome=True),
            )
        self.assertEqual(code, 2)
        # Both classifications deny, so the exit code cannot tell them apart. The
        # WRONG one here would be "has produced new output".
        self.assertIn("could not read this session's current output", stderr.getvalue())
        self.assertNotIn("has produced new output", stderr.getvalue())

    def test_no_agent_deck_probe_is_spawned_when_no_receipt_exists(self):
        # The freshness probe costs a ~25 ms subprocess and is needed only for
        # the freshness comparison. Passing it eagerly spawned one per target even
        # when the receipt file did not exist, which is the most common denial.
        import subprocess as sp

        calls = []

        def counting_run(argv, timeout):
            calls.append(argv)
            return sp.CompletedProcess(
                argv, 0, '{"content": "x", "success": true, "timestamp": "t"}', ""
            )

        with contextlib.redirect_stderr(io.StringIO()):
            code = guard.main(
                fixtures.payload("agent-deck session remove %s" % TARGET),
                self.env(CONDUCTOR),
                run=counting_run,
            )
        self.assertEqual(code, 2)
        self.assertEqual(calls, [])

    def test_the_probe_IS_spawned_when_freshness_must_be_checked(self):
        self.give_receipt()
        calls = []
        import subprocess as sp

        def counting_run(argv, timeout):
            calls.append(argv)
            return sp.CompletedProcess(
                argv,
                0,
                '{"content": "%s", "success": true, "timestamp": "t"}' % OUTPUT,
                "",
            )

        code = guard.main(
            fixtures.payload("agent-deck session remove %s" % TARGET),
            self.env(CONDUCTOR),
            run=counting_run,
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 1)

    def test_unrunnable_agent_deck_denies_with_an_accurate_reason(self):
        # Must say it could not read the output, NOT "the guard hit an internal
        # error" - which is what the dangling-import bug produced.
        self.give_receipt()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = guard.main(
                fixtures.payload("agent-deck session remove %s" % TARGET),
                self.env(CONDUCTOR),
                run=fixtures.failing_run(),
            )
        self.assertEqual(code, 2)
        self.assertIn("could not read this session's current output", stderr.getvalue())
        self.assertNotIn("internal error", stderr.getvalue())

    def test_ambiguous_prefix_denies_rather_than_guessing(self):
        db = registry_helpers.temp_registry(
            [
                {"id": CONDUCTOR, "title": "conductor-hq", "is_conductor": 1},
                {"id": "twin-1", "title": "twin-a"},
                {"id": "twin-2", "title": "twin-b"},
            ],
            self.root / "reg2",
        )
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = self.run_guard("agent-deck rm twin-", CONDUCTOR, db=db)
        self.assertEqual(code, 2)
        # Removing the AmbiguousReference handler leaves the exit code at 2 but
        # changes the message to a generic internal error.
        self.assertIn("ambiguous reference", stderr.getvalue())
        self.assertNotIn("internal error", stderr.getvalue())

    def test_unresolvable_target_denies(self):
        self.assertEqual(
            self.run_guard("agent-deck session remove ghost", CONDUCTOR), 2
        )

    def test_unexpanded_variable_is_diagnosed_not_just_denied(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = self.run_guard("agent-deck session remove $TARGET", CONDUCTOR)
        self.assertEqual(code, 2)
        self.assertIn("unexpanded shell variable", stderr.getvalue())

    def test_prune_worktree_requires_a_clean_worktree(self):
        self.give_receipt()  # worktree not applicable by default
        self.assertEqual(
            self.run_guard(
                "agent-deck session remove %s --prune-worktree" % TARGET, CONDUCTOR
            ),
            2,
        )
        self.give_receipt(
            worktree={"applicable": True, "clean": True, "reason": "clean"}
        )
        self.assertEqual(
            self.run_guard(
                "agent-deck session remove %s --prune-worktree" % TARGET, CONDUCTOR
            ),
            0,
        )

    # ---- the deny message is an acceptance requirement, so assert on it ----

    def test_the_denial_names_the_target_and_a_runnable_fix(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.run_guard("agent-deck session remove %s" % TARGET, CONDUCTOR)
        text = stderr.getvalue()
        self.assertIn(TARGET, text)
        self.assertIn("agent-deck-preclose.py", text)
        self.assertIn("BLOCKED", text)

    # ---- fail direction ----

    def test_stage_b_bug_denies_rather_than_silently_allowing(self):
        # The trap this whole structure exists to avoid. An earlier version left
        # this call outside any try, so the KeyError escaped main() and this test
        # ERRORED instead of observing a deny.
        original = guard.preclose_receipt.validate_receipt

        def exploding(*_args, **_kwargs):
            raise KeyError("simulated bug in validation")

        guard.preclose_receipt.validate_receipt = exploding
        self.addCleanup(setattr, guard.preclose_receipt, "validate_receipt", original)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = self.run_guard("agent-deck session remove %s" % TARGET, CONDUCTOR)
        self.assertEqual(code, 2)
        self.assertIn("internal error", stderr.getvalue())

    def test_stage_a_bug_allows_rather_than_wedging_an_unrelated_session(self):
        # A non-string command used to raise out of find_removal, escape main(),
        # and be turned into a DENY by the entry point - wedging a worker.
        broken = fixtures.payload("x").replace('"command": "x"', '"command": {"a": 1}')
        self.assertEqual(guard.main(broken, self.env(WORKER)), 0)

    def test_malformed_payload_allows(self):
        self.assertEqual(guard.main("{not json", self.env(CONDUCTOR)), 0)

    def test_an_absent_registry_denies_regardless_of_caller(self):
        # There is no working-directory fallback: cwd follows a `cd`, so a guard
        # scoped on it silently stops applying and nobody notices. Instead, a
        # registry that cannot be read at all denies for everyone - `agent-deck
        # session remove` needs that same database to delete the row, so the
        # removal could not have succeeded either. Denying refuses nothing that
        # would have worked.
        env = self.env(WORKER, db=self.root / "absent.db")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = guard.main(
                fixtures.payload("agent-deck session remove %s" % TARGET),
                env,
                run=fixtures.fake_output(OUTPUT),
            )
        self.assertEqual(code, 2)
        self.assertIn("could not be read", stderr.getvalue())
        self.assertIn("could not have succeeded either", stderr.getvalue())

    def test_a_busy_registry_allows_because_a_lock_is_transient(self):
        # agent-deck writes this file constantly, so SQLITE_BUSY is a lock we
        # could win by waiting. Refusing a worker over a passing lock is the
        # false refusal that gets a guard routed around.
        original = guard.lib.is_conductor

        def busy(*_args, **_kwargs):
            raise guard.lib.RegistryUnavailable("database is locked", transient=True)

        guard.lib.is_conductor = busy
        self.addCleanup(setattr, guard.lib, "is_conductor", original)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = self.run_guard("agent-deck session remove %s" % TARGET, CONDUCTOR)
        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")

    def test_a_caller_with_no_agentdeck_identity_is_left_alone(self):
        env = {
            "HOME": str(self.root),
            "PRECLOSE_STATE_DB": str(self.db),
            "PRECLOSE_EVIDENCE_ROOT": str(self.root / "evidence"),
        }
        code = guard.main(
            fixtures.payload("agent-deck session remove %s" % TARGET),
            env,
            run=fixtures.fake_output(OUTPUT),
        )
        self.assertEqual(code, 0)

    def test_an_instance_absent_from_a_readable_registry_is_left_alone(self):
        self.assertEqual(
            self.run_guard("agent-deck session remove %s" % TARGET, "ghost-id"), 0
        )

    # --- the three false positives measured 2026-08-27 ---

    def test_redirect_does_not_block_a_valid_removal(self):
        # Bug 1: `2>&1` was parsed as a session ref. The guard refused a
        # removal whose checklist had already passed, because `2>` was looked
        # up in the registry and (correctly) not found.
        #
        # The binary check in probe_session_output must pass for the fake
        # runner to be used; monkey-patch it so this test works in any
        # environment (agent-deck is not installed here).
        self.give_receipt()
        original = guard.lib.agent_deck_binary
        guard.lib.agent_deck_binary = lambda: "/usr/bin/true"
        self.addCleanup(setattr, guard.lib, "agent_deck_binary", original)
        self.assertEqual(
            self.run_guard(
                "agent-deck session remove %s 2>&1" % TARGET, CONDUCTOR
            ),
            0,
        )

    def test_heredoc_body_is_not_treated_as_a_command(self):
        # Bug 2: a heredoc writing a dispatch brief was blocked because the
        # prose mentioned session commands.
        code = self.run_guard(
            "cat <<'BRIEF' > /tmp/dispatch.md\n"
            "Worker instructions:\n"
            "1. Use agent-deck session send <id> to deliver results\n"
            "2. The conductor will remove your session when done\n"
            "BRIEF",
            CONDUCTOR,
        )
        self.assertEqual(code, 0)

    def test_bd_description_quoting_removal_is_not_blocked(self):
        # Bug 3: a bd command whose description quoted a session-removal
        # command was blocked by the guard.
        code = self.run_guard(
            "TITLE=$(cat <<'BD_TITLE'\n"
            "the guard blocked agent-deck session remove for no reason\n"
            "BD_TITLE\n"
            ")\n"
            'bd create "$TITLE" -p 2 -l agent-proposed',
            CONDUCTOR,
        )
        self.assertEqual(code, 0)


class LiveOutputTest(unittest.TestCase):
    def test_empty_content_and_not_found_are_distinguished_from_real_output(self):
        deadline = guard.time.monotonic() + 5
        self.assertEqual(
            guard.live_output("s", fixtures.fake_output("hello"), deadline).content,
            "hello",
        )
        # success=true with empty content is a real answer: nothing was said.
        self.assertEqual(
            guard.live_output("s", fixtures.fake_output(""), deadline).content, ""
        )
        # NOT_FOUND is success=false, which is unknowable, not empty.
        probe = guard.live_output(
            "s", fixtures.fake_output("", not_found=True), deadline
        )
        self.assertFalse(probe.ok)
        self.assertEqual(probe.code, "unknown")


class EntryPointContractTest(unittest.TestCase):
    """Drives the real script the way settings.json does: stdin in, code out."""

    def _run(self, payload_text, env):
        return subprocess.run(
            [sys.executable, str(ENTRY)],
            input=payload_text,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_a_non_conductor_exits_zero_with_no_output_at_all(self):
        result = self._run(
            fixtures.payload("agent-deck session remove whatever"),
            {"HOME": "/nonexistent-home-for-test", "PATH": "/usr/bin:/bin"},
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_a_conductor_denial_exits_two_with_stderr_and_empty_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = registry_helpers.temp_registry(
                [
                    {"id": CONDUCTOR, "title": "c", "is_conductor": 1},
                    {"id": TARGET, "title": "t", "tool": "claude"},
                ],
                root / "reg",
            )
            result = self._run(
                fixtures.payload("agent-deck session remove %s" % TARGET),
                {
                    "HOME": str(root),
                    "PATH": "/usr/bin:/bin",
                    "AGENTDECK_INSTANCE_ID": CONDUCTOR,
                    "PRECLOSE_STATE_DB": str(db),
                    "PRECLOSE_EVIDENCE_ROOT": str(root / "evidence"),
                },
            )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("BLOCKED", result.stderr)


if __name__ == "__main__":
    unittest.main()
