#!/usr/bin/env python3
"""Unit tests for hooks/preclose_checklist.py."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fixtures  # noqa: E402
import git_helpers  # noqa: E402
import preclose_checklist as checklist  # noqa: E402
import preclose_lib as lib  # noqa: E402
import preclose_receipt as receipt_mod  # noqa: E402
import registry_helpers  # noqa: E402

SESSION = "sess-1111"
ANSWER = "the final answer"


class ChecklistTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.out = io.StringIO()
        self.err = io.StringIO()
        self._regs = 0

    def plant_transcript(self, claude_session_id="abc"):
        """A transcript on disk means this session HAS spoken before.

        The runner now decides "was there ever anything to rescue" by transcript
        existence, because the registry cannot separate a session that was never
        started from one that started and never completed a turn.
        """
        d = self.root / ".claude" / "projects" / "encoded-path"
        d.mkdir(parents=True, exist_ok=True)
        (d / ("%s.jsonl" % claude_session_id)).write_text('{"type":"assistant"}\n')

    def registry(self, **overrides):
        row = {
            "id": SESSION,
            "title": "a-session",
            "tool": "claude",
            "status": "stopped",
            "tool_data": {"claude_session_id": "abc"},
        }
        row.update(overrides)
        self._regs += 1
        return registry_helpers.temp_registry([row], self.root / ("reg%d" % self._regs))

    def env(self, db):
        return {
            "HOME": str(self.root),
            "PRECLOSE_STATE_DB": str(db),
            "PRECLOSE_EVIDENCE_ROOT": str(self.root / "evidence"),
        }

    def run_it(self, db, content=ANSWER, not_found=False, ref=SESSION):
        return checklist.run_checklist(
            ref,
            self.env(db),
            run=fixtures.fake_output(content, not_found=not_found),
            out=self.out,
            err=self.err,
        )

    def receipt(self):
        path = self.root / "evidence" / "preclose" / (SESSION + ".json")
        return json.loads(path.read_text()) if path.exists() else None

    def test_real_output_writes_a_passing_receipt_and_a_dump(self):
        self.assertEqual(self.run_it(self.registry()), 0, self.err.getvalue())
        receipt = self.receipt()
        self.assertEqual(receipt["status"], "passed")
        dump = Path(receipt["dump"]["path"])
        self.assertEqual(dump.read_text(), ANSWER)
        self.assertEqual(receipt["dump"]["byte_size"], dump.stat().st_size)
        self.assertEqual(receipt["output"]["sha256"], receipt_mod.sha256_text(ANSWER))

    def test_the_receipt_it_writes_actually_validates(self):
        # End to end: writer and reader must agree about the format.
        self.run_it(self.registry())
        verdict = receipt_mod.validate_receipt(
            self.root / "evidence" / "preclose" / (SESSION + ".json"),
            expected_session_id=SESSION,
            expected_tool="claude",
            live_output=lib.SessionOutput(True, ANSWER, code="message"),
            require_worktree_clean=False,
        )
        self.assertTrue(verdict.ok, verdict.reason)

    def test_empty_output_writes_a_failed_receipt_and_exits_nonzero(self):
        self.plant_transcript()
        # agent-deck returns success=true with content="" for a session that never
        # spoke, so trusting `success` alone would attest to rescuing nothing.
        self.assertEqual(self.run_it(self.registry(), content=""), 1)
        self.assertEqual(self.receipt()["status"], "failed")
        self.assertIn("empty", self.receipt()["reason"])
        self.assertIn("came back empty", self.err.getvalue())

    def test_started_but_never_answered_session_can_earn_a_receipt(self):
        # HAS a claude_session_id but no transcript file: started, never completed
        # a turn, and `session output` returns the terminal pane. Without this it
        # would be permanently unremovable.
        db = self.registry(status="waiting", tool_data={"claude_session_id": "never"})
        self.assertEqual(
            checklist.run_checklist(
                SESSION,
                self.env(db),
                run=fixtures.fake_output("", chrome=True),
                out=self.out,
                err=self.err,
            ),
            0,
            self.err.getvalue(),
        )
        self.assertIn("nothing to rescue", self.receipt()["reason"])

    def test_a_shell_session_pane_is_accepted_as_its_output(self):
        # A shell session ALWAYS returns its pane with an empty timestamp. Applying
        # the Claude timestamp rule to it would make every shell session
        # permanently unremovable.
        db = self.registry(tool="shell", tool_data={})
        self.assertEqual(
            checklist.run_checklist(
                SESSION,
                self.env(db),
                run=fixtures.fake_output("", chrome=True),
                out=self.out,
                err=self.err,
            ),
            0,
            self.err.getvalue(),
        )
        self.assertEqual(self.receipt()["status"], "passed")

    def test_an_unrunnable_agent_deck_is_never_called_nothing_to_rescue(self):
        # The probe being broken says nothing about whether the session produced
        # output. Treating it as "nothing to rescue" made a shell session earn a
        # PASSING receipt attesting to the health of the tool, not of the session.
        db = self.registry(tool="shell", tool_data={})
        code = checklist.run_checklist(
            SESSION,
            self.env(db),
            run=fixtures.failing_run(),
            out=self.out,
            err=self.err,
        )
        self.assertEqual(code, 1)
        self.assertEqual(self.receipt()["status"], "failed")
        self.assertIn("could not run agent-deck", self.receipt()["reason"])

    def test_an_unwritable_evidence_tree_fails_cleanly_not_with_a_traceback(self):
        db = self.registry()
        evidence = self.root / "locked-evidence"
        evidence.mkdir()
        os.chmod(evidence, 0o500)
        self.addCleanup(os.chmod, evidence, 0o700)
        env = dict(self.env(db), PRECLOSE_EVIDENCE_ROOT=str(evidence))
        code = checklist.run_checklist(
            SESSION, env, run=fixtures.fake_output(ANSWER), out=self.out, err=self.err
        )
        self.assertEqual(code, 1)
        self.assertIn("could not write evidence", self.err.getvalue())

    def test_a_dead_shell_session_can_still_be_closed(self):
        # Observed live: a shell session whose tmux pane is gone returns
        # "failed to capture terminal output". It has no transcript either, so the
        # record is already gone and refusing would make it unremovable forever.
        db = self.registry(tool="shell", status="error", tool_data={})
        self.assertEqual(
            checklist.run_checklist(
                SESSION,
                self.env(db),
                run=fixtures.fake_output("", not_found=True),
                out=self.out,
                err=self.err,
            ),
            0,
            self.err.getvalue(),
        )
        receipt = self.receipt()
        self.assertEqual(receipt["status"], "passed")
        self.assertIn("nothing to rescue", receipt["reason"])

    def test_never_started_session_can_still_earn_a_receipt(self):
        # Otherwise errored sessions become permanently unremovable, because
        # --all-errored is denied outright, and the conductor loses the ability to
        # clean them up at all.
        db = self.registry(status="error", tool_data={})
        self.assertEqual(self.run_it(db, content=""), 0, self.err.getvalue())
        receipt = self.receipt()
        self.assertEqual(receipt["status"], "passed")
        self.assertIn("nothing to rescue", receipt["reason"])
        self.assertGreater(Path(receipt["dump"]["path"]).stat().st_size, 0)

    def test_a_started_session_with_empty_output_still_fails(self):
        self.plant_transcript()
        db = self.registry(status="error", tool_data={"claude_session_id": "abc"})
        self.assertEqual(self.run_it(db, content=""), 1)
        self.assertEqual(self.receipt()["status"], "failed")

    def test_terminal_chrome_is_not_accepted_as_a_rescued_dump(self):
        self.plant_transcript()
        # A RUNNING session that has not answered returns the tmux pane as
        # `content` with success=true and an EMPTY timestamp. A non-empty check
        # accepts 648 characters of box-drawing as the session's final word.
        code = checklist.run_checklist(
            SESSION,
            self.env(self.registry()),
            run=fixtures.fake_output("", chrome=True),
            out=self.out,
            err=self.err,
        )
        self.assertEqual(code, 1)
        self.assertEqual(self.receipt()["status"], "failed")
        self.assertIn("terminal output", self.receipt()["reason"])

    def test_not_found_writes_a_failed_receipt(self):
        self.assertEqual(self.run_it(self.registry(), not_found=True), 1)
        self.assertEqual(self.receipt()["status"], "failed")
        self.assertIn("could not read", self.receipt()["reason"])

    def test_unresolvable_reference_writes_no_receipt_at_all(self):
        self.assertEqual(self.run_it(self.registry(), ref="ghost"), 1)
        self.assertIsNone(self.receipt())
        self.assertIn("no session id to key one on", self.err.getvalue())

    def test_rerunning_is_idempotent(self):
        db = self.registry()
        self.assertEqual(self.run_it(db), 0)
        first = self.receipt()
        self.assertEqual(self.run_it(db), 0)
        second = self.receipt()
        self.assertEqual(first["dump"], second["dump"])
        self.assertEqual(first["output"]["sha256"], second["output"]["sha256"])

    def test_a_failed_receipt_is_replaced_by_a_passing_one_on_a_good_rerun(self):
        self.plant_transcript()
        db = self.registry()
        self.assertEqual(self.run_it(db, content=""), 1)
        self.assertEqual(self.receipt()["status"], "failed")
        self.assertEqual(self.run_it(db), 0)
        self.assertEqual(self.receipt()["status"], "passed")


class CliEntryPointTest(unittest.TestCase):
    """checklist.main() is the function agent-deck-preclose.py calls, and it is
    the command every denial message tells an operator to run. It had no test at
    all: renaming args.session to args.sessionn left the suite green while the
    real CLI crashed on every invocation."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = registry_helpers.temp_registry(
            [
                {
                    "id": SESSION,
                    "title": "a-session",
                    "tool": "claude",
                    "tool_data": {"claude_session_id": "abc"},
                }
            ],
            self.root / "reg",
        )
        self.env = {
            "HOME": str(self.root),
            "PRECLOSE_STATE_DB": str(self.db),
            "PRECLOSE_EVIDENCE_ROOT": str(self.root / "evidence"),
        }

    def test_a_session_reference_runs_the_checklist_and_writes_a_receipt(self):
        code = checklist.main([SESSION], self.env, run=fixtures.fake_output(ANSWER))
        self.assertEqual(code, 0)
        self.assertTrue(
            (self.root / "evidence" / "preclose" / (SESSION + ".json")).exists()
        )

    def test_no_argument_is_a_usage_error(self):
        self.assertEqual(checklist.main([], self.env), 2)

    def test_the_real_script_runs_end_to_end(self):
        entry = Path(__file__).resolve().parents[1] / "agent-deck-preclose.py"
        done = subprocess.run(
            [sys.executable, str(entry), SESSION],
            capture_output=True,
            text=True,
            env=dict(self.env, PATH="/usr/bin:/bin"),
        )
        # agent-deck is not on this PATH, so the checklist cannot pass - but it
        # must FAIL cleanly rather than traceback.
        self.assertEqual(done.returncode, 1, done.stderr)
        self.assertNotIn("Traceback", done.stderr)


class WorktreeStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_shared_checkout_is_not_applicable(self):
        state = checklist.worktree_state("")
        self.assertFalse(state["applicable"])
        self.assertIn("shared checkout", state["reason"])

    def test_absent_directory_is_not_applicable_rather_than_dirty(self):
        state = checklist.worktree_state(str(self.root / "gone"))
        self.assertFalse(state["applicable"])
        self.assertIn("nothing left to lose", state["reason"])

    def test_clean_worktree_is_clean(self):
        work = git_helpers.make_git_repo(self.root / "a")
        state = checklist.worktree_state(str(work))
        self.assertTrue(state["applicable"])
        self.assertTrue(state["clean"])

    def test_untracked_file_counts_as_dirty(self):
        work = git_helpers.make_git_repo(self.root / "b", dirty=True)
        state = checklist.worktree_state(str(work))
        self.assertTrue(state["applicable"])
        self.assertFalse(state["clean"])
        self.assertIn("uncommitted", state["reason"])

    def test_unpushed_commits_are_recorded_but_do_not_make_it_dirty(self):
        # After a squash merge - this repo's convention - a fully-merged branch's
        # HEAD is contained in no remote branch. Treating that as unclean would
        # refuse the most common legitimate removal.
        work = git_helpers.make_git_repo(self.root / "c", unpushed=True)
        state = checklist.worktree_state(str(work))
        self.assertTrue(state["clean"])
        self.assertEqual(state["remote_branches_containing_head"], 0)

    def test_a_plain_directory_is_reported_as_not_a_repo(self):
        plain = self.root / "plain"
        plain.mkdir()
        state = checklist.worktree_state(str(plain))
        self.assertFalse(state["applicable"])
        self.assertIn("no longer a git repository", state["reason"])


class SelftestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.out = io.StringIO()
        self.err = io.StringIO()

    def selftest(self, settings_path, extra=None):
        env = {"HOME": str(self.root), "PRECLOSE_SETTINGS": str(settings_path)}
        if extra:
            env.update(extra)
        return checklist.selftest(env, out=self.out, err=self.err)

    def write_settings(self, command=None):
        path = self.root / "settings.json"
        hooks = []
        if command is not None:
            hooks = [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": command}]}
            ]
        path.write_text(json.dumps({"hooks": {"PreToolUse": hooks}}))
        return path

    def test_missing_wiring_is_reported_as_not_armed(self):
        self.assertEqual(self.selftest(self.write_settings()), 1)
        self.assertIn("NOT armed", self.err.getvalue())

    def test_unreadable_settings_fails_loudly(self):
        self.assertEqual(self.selftest(self.root / "nope.json"), 1)
        self.assertIn("SELFTEST FAIL", self.err.getvalue())

    def test_a_wired_but_broken_command_is_caught(self):
        # This is the whole point of EXECUTING the wired string rather than
        # checking that some entry mentions the filename.
        path = self.write_settings("exit 0  # preclose_guard.py")
        self.assertEqual(self.selftest(path), 1)
        self.assertIn("did NOT deny", self.err.getvalue())

    def test_a_guard_that_never_permits_is_caught(self):
        # The other half of selftest's promise. A wired command that always denies
        # refuses the receiptless case correctly and then wrongly refuses the
        # receipted one - "a guard that cannot be satisfied will be worked around",
        # which is the failure selftest exists to catch.
        path = self.write_settings("exit 2  # preclose_guard.py")
        self.assertEqual(self.selftest(path), 1)
        self.assertIn("did NOT allow", self.err.getvalue())

    def test_the_real_wiring_shape_passes(self):
        guard = Path(__file__).resolve().parents[1] / "preclose_guard.py"
        path = self.write_settings(
            'H="%s"; [ -r "$H" ] || exit 0; exec python3 "$H"' % guard
        )
        code = self.selftest(path)
        self.assertEqual(code, 0, self.err.getvalue())
        self.assertIn("SELFTEST PASS", self.out.getvalue())


if __name__ == "__main__":
    unittest.main()
