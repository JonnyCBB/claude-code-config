#!/usr/bin/env python3
"""Unit tests for hooks/preclose_receipt.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import preclose_lib as lib  # noqa: E402
import preclose_receipt as receipt_mod  # noqa: E402
import receipt_helpers  # noqa: E402

OUTPUT = "the final answer"


def live(content=OUTPUT, ok=True, code="message"):
    """A stand-in for what the guard hands validate_receipt."""
    return lib.SessionOutput(ok=ok, content=content, code=code)


LIVE = live()


class ValidateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "r.json"

    def check(
        self, *, live=LIVE, tool="claude", prune=False, output_text=OUTPUT, **kwargs
    ):
        receipt_helpers.write_receipt(self.path, output_text=output_text, **kwargs)
        return receipt_mod.validate_receipt(
            self.path,
            expected_session_id=kwargs.get("session_id", "sess-1"),
            expected_tool=tool,
            live_output=live,
            require_worktree_clean=prune,
        )

    def test_default_fixture_is_genuinely_valid(self):
        verdict = self.check()
        self.assertTrue(verdict.ok, verdict.reason)

    def test_absent_receipt_is_rejected(self):
        verdict = receipt_mod.validate_receipt(
            self.root / "absent.json",
            expected_session_id="sess-1",
            expected_tool="claude",
            live_output=LIVE,
            require_worktree_clean=False,
        )
        self.assertFalse(verdict.ok)
        self.assertIn("no pre-close receipt", verdict.reason)

    def test_receipt_for_another_session_is_rejected(self):
        receipt_helpers.write_receipt(self.path, session_id="other", output_text=OUTPUT)
        verdict = receipt_mod.validate_receipt(
            self.path,
            expected_session_id="sess-1",
            expected_tool="claude",
            live_output=LIVE,
            require_worktree_clean=False,
        )
        self.assertFalse(verdict.ok)
        self.assertIn("different session", verdict.reason)

    def test_tool_is_taken_from_the_registry_not_the_receipt(self):
        # A receipt claiming a different tool must not be waved through.
        verdict = self.check(tool="shell")
        self.assertFalse(verdict.ok)
        self.assertIn("registry says", verdict.reason)

    def test_failed_status_is_rejected_and_echoes_the_reason(self):
        verdict = self.check(status="failed", reason="the dump was empty")
        self.assertFalse(verdict.ok)
        self.assertIn("the dump was empty", verdict.reason)

    def test_newer_schema_gets_its_own_message_not_a_rerun_loop(self):
        verdict = self.check(overrides={"schema_version": 99})
        self.assertFalse(verdict.ok)
        self.assertIn("reinstall", verdict.reason)

    def test_unknown_older_schema_is_rejected(self):
        verdict = self.check(overrides={"schema_version": "banana"})
        self.assertFalse(verdict.ok)

    def test_missing_dump_file_is_rejected(self):
        receipt_helpers.write_receipt(self.path, output_text=OUTPUT)
        (self.root / "sess-1-final.md").unlink()
        verdict = receipt_mod.validate_receipt(
            self.path,
            expected_session_id="sess-1",
            expected_tool="claude",
            live_output=LIVE,
            require_worktree_clean=False,
        )
        self.assertFalse(verdict.ok)
        self.assertIn("missing or unreadable", verdict.reason)

    def test_empty_dump_file_is_rejected(self):
        empty = self.root / "empty.md"
        empty.write_text("")
        verdict = self.check(dump_path=str(empty), dump_bytes=0)
        self.assertFalse(verdict.ok)
        self.assertIn("empty", verdict.reason)

    def test_truncated_dump_is_rejected(self):
        receipt_helpers.write_receipt(self.path, output_text=OUTPUT)
        (self.root / "sess-1-final.md").write_text("x")
        verdict = receipt_mod.validate_receipt(
            self.path,
            expected_session_id="sess-1",
            expected_tool="claude",
            live_output=LIVE,
            require_worktree_clean=False,
        )
        self.assertFalse(verdict.ok)
        self.assertIn("changed size", verdict.reason)

    def test_new_output_since_the_dump_is_rejected(self):
        verdict = self.check(live=live("something new"))
        self.assertFalse(verdict.ok)
        self.assertIn("new output since the checklist ran", verdict.reason)

    def test_unobtainable_live_output_is_rejected_not_allowed(self):
        verdict = self.check(live=lib.SessionOutput(False, code="unreachable"))
        self.assertFalse(verdict.ok)
        self.assertIn("cannot confirm", verdict.reason)

    def test_a_nothing_to_rescue_receipt_survives_an_unreadable_session(self):
        # A session that never produced output gets a passing "nothing to rescue"
        # receipt. agent-deck then answers "I cannot read that session", which is
        # CONSISTENT with the receipt, not a contradiction. Demanding a readable
        # hash here made every never-started session permanently unremovable - a
        # check that cannot pass.
        # Mirrors what the runner really writes: a non-empty NOTE explaining there
        # was nothing to rescue, plus an output hash of the empty string.
        verdict = self.check(
            overrides={"output": {"sha256": receipt_mod.sha256_text("")}},
            live=lib.SessionOutput(False, code="unknown"),
        )
        self.assertTrue(verdict.ok, verdict.reason)

    def test_a_receipt_with_REAL_content_still_needs_a_readable_session(self):
        # The asymmetry that makes the above safe: if the runner saved a real
        # answer, the guard must see that same answer now or refuse.
        verdict = self.check(live=lib.SessionOutput(False, code="unknown"))
        self.assertFalse(verdict.ok)
        self.assertIn("could not read", verdict.reason)

    def test_an_unrunnable_tool_refuses_even_a_nothing_to_rescue_receipt(self):
        # "unreachable" means the TOOL is broken, which says nothing about the
        # session, so it cannot be read as confirmation of anything.
        verdict = self.check(
            overrides={"output": {"sha256": receipt_mod.sha256_text("")}},
            live=lib.SessionOutput(False, code="unreachable"),
        )
        self.assertFalse(verdict.ok)

    def test_malformed_json_is_rejected_without_raising(self):
        self.path.write_text("{not json")
        verdict = receipt_mod.validate_receipt(
            self.path,
            expected_session_id="sess-1",
            expected_tool="claude",
            live_output=LIVE,
            require_worktree_clean=False,
        )
        self.assertFalse(verdict.ok)

    def test_null_dump_path_is_invalid_not_a_crash(self):
        # This raised TypeError out of validate_receipt in an earlier version,
        # which the guard turned into an internal-error deny.
        verdict = self.check(overrides={"dump": {"path": None, "byte_size": 3}})
        self.assertFalse(verdict.ok)
        self.assertIn("missing or unreadable", verdict.reason)

    def test_prune_worktree_requires_a_clean_recorded_worktree(self):
        self.assertFalse(self.check(prune=True).ok)
        verdict = self.check(
            prune=True,
            worktree={
                "applicable": True,
                "clean": False,
                "reason": "2 uncommitted files",
            },
        )
        self.assertFalse(verdict.ok)
        self.assertIn("uncommitted work", verdict.reason)
        verdict = self.check(
            prune=True, worktree={"applicable": True, "clean": True, "reason": "clean"}
        )
        self.assertTrue(verdict.ok, verdict.reason)

    def test_worktree_state_is_ignored_when_not_pruning(self):
        # A bare removal preserves the worktree (verified behaviourally), so a
        # dirty worktree must NOT block it.
        verdict = self.check(
            worktree={"applicable": True, "clean": False, "reason": "dirty"}
        )
        self.assertTrue(verdict.ok, verdict.reason)


class AtomicWriteTest(unittest.TestCase):
    def test_creates_parents_and_leaves_no_temp_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested" / "r.json"
            receipt_mod.atomic_write_json(target, {"a": 1})
            self.assertEqual(json.loads(target.read_text()), {"a": 1})
            self.assertEqual([p.name for p in target.parent.iterdir()], ["r.json"])


class BuildTest(unittest.TestCase):
    def test_rejects_a_status_outside_the_two_allowed(self):
        with self.assertRaises(ValueError):
            receipt_mod.build_receipt(
                session_id="s",
                session_title="t",
                tool="claude",
                status="ok",
                reason=None,
                generated_at="x",
                dump_path="/tmp/x",
                dump_bytes=1,
                output_sha256="a",
                worktree={},
            )


if __name__ == "__main__":
    unittest.main()
