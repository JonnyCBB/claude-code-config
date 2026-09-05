#!/usr/bin/env python3
"""Unit tests for hooks/preclose_lib.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import preclose_lib as lib  # noqa: E402
import fixtures  # noqa: E402
import registry_helpers  # noqa: E402


class FindRemovalTest(unittest.TestCase):
    def assertMatches(self, command, refs):
        found = lib.find_removal(command)
        self.assertIsNotNone(found, command)
        self.assertEqual(found.refs, refs, command)
        return found

    def test_matches_all_three_removal_spellings(self):
        self.assertMatches("agent-deck session remove abc123", ["abc123"])
        self.assertMatches("agent-deck remove abc123", ["abc123"])
        self.assertMatches("agent-deck rm abc123", ["abc123"])

    def test_worktree_finish_demands_the_worktree_check_by_verb_not_by_flag(self):
        # `worktree finish` deletes the worktree UNCONDITIONALLY per its own
        # --help, and --prune-worktree does not exist on it. Gating the
        # worktree-clean check on that flag meant the one command whose purpose is
        # deleting the worktree never triggered the check built to protect it.
        for command in (
            "agent-deck worktree finish my-session",
            "agent-deck wt finish my-session",
        ):
            found = self.assertMatches(command, ["my-session"])
            self.assertTrue(found.prune_worktree, command)

    def test_ignores_subcommand_flags_as_refs(self):
        found = self.assertMatches(
            "agent-deck session remove abc123 --force --prune-worktree -q", ["abc123"]
        )
        self.assertTrue(found.prune_worktree)

    def test_equals_form_flags_are_read(self):
        # agent-deck uses Go's flag package, which accepts --x=v. Reading flags
        # without truncating at '=' made --prune-worktree=true invisible, which
        # silently dropped the worktree check on the one form that deletes it.
        found = self.assertMatches(
            "agent-deck session remove abc --prune-worktree=true", ["abc"]
        )
        self.assertTrue(found.prune_worktree)
        self.assertTrue(
            lib.find_removal("agent-deck session remove --all-errored=true").bulk
        )

    def test_an_unrecognised_destructive_verb_fails_closed(self):
        # The verb table cannot know about a command a future agent-deck adds.
        # Unknown destructive-sounding verbs must deny, not be allowed in silence.
        for command in (
            "agent-deck session delete abc",
            "agent-deck session purge abc",
            "agent-deck session destroy abc",
        ):
            found = lib.find_removal(command)
            self.assertIsNotNone(found, command)
            self.assertTrue(found.unparsed, command)

    def test_the_backstop_does_not_fire_on_read_only_commands(self):
        # Checked against the full `agent-deck --help` surface: the backstop must
        # not make ordinary commands undeniable friction.
        for command in (
            "agent-deck list",
            "agent-deck status",
            "agent-deck session show abc",
            "agent-deck session output abc",
            "agent-deck session stop abc",
            "agent-deck rename old new",
            "agent-deck launch . -c claude",
        ):
            self.assertIsNone(lib.find_removal(command), command)

    def test_does_not_match_stop_or_a_bare_teardown(self):
        self.assertIsNone(lib.find_removal("agent-deck session stop abc123"))
        self.assertIsNone(lib.find_removal("agent-deck conductor teardown infra"))

    def test_bulk_forms_are_flagged_for_outright_denial(self):
        for command in (
            "agent-deck session remove --all-errored",
            "agent-deck worktree cleanup --force",
            "agent-deck wt cleanup --force",
            "agent-deck conductor teardown infra --remove",
            "agent-deck conductor teardown --all --remove",
        ):
            found = lib.find_removal(command)
            self.assertIsNotNone(found, command)
            self.assertTrue(found.bulk, command)

    def test_the_non_destructive_forms_of_those_commands_are_left_alone(self):
        # `worktree cleanup` is dry-run until --force; `conductor teardown` stops
        # until --remove, and --all only widens the scope of the stop. Denying
        # either told the operator it "destroys several sessions at once", which
        # was false, and is the friction that gets a guard routed around.
        for command in (
            "agent-deck worktree cleanup",
            "agent-deck wt cleanup",
            "agent-deck conductor teardown infra",
            "agent-deck conductor teardown --all",
        ):
            self.assertIsNone(lib.find_removal(command), command)

    def test_eval_does_not_hide_a_removal(self):
        # eval takes its command directly rather than behind -c, so the shell
        # wrapper branch missed it and shlex yields the whole invocation as one
        # opaque token. It was allowed silently.
        self.assertMatches('eval "agent-deck session remove x"', ["x"])
        self.assertMatches("eval 'agent-deck rm y'", ["y"])

    def test_does_not_match_quoted_or_commented_lookalikes(self):
        for command in (
            'echo "agent-deck session remove"',
            "grep 'session remove' notes.txt",
            "# agent-deck session remove x",
        ):
            self.assertIsNone(lib.find_removal(command), command)

    # --- the six bypasses found by review on 2026-08-18. Each was verified to
    # --- return None against the first implementation.

    def test_bypass_semicolon_glued_to_previous_token(self):
        # shlex.split leaves ';' attached: ['...','x;','agent-deck',...]. The
        # first agent-deck is a harmless `stop`, so scanning only the first
        # occurrence allowed the removal. This is the documented close sequence.
        self.assertMatches(
            "agent-deck session stop x; agent-deck session remove x", ["x"]
        )

    def test_bypass_no_spaces_around_operators(self):
        self.assertMatches(
            "agent-deck session stop x;agent-deck session remove x", ["x"]
        )
        self.assertMatches(
            "agent-deck session stop x&&agent-deck session remove x", ["x"]
        )

    def test_bypass_absolute_path_invocation(self):
        # The binary really is at /opt/homebrew/bin/agent-deck.
        self.assertMatches(
            "/opt/homebrew/bin/agent-deck session remove abc123", ["abc123"]
        )
        self.assertMatches("./agent-deck rm abc123", ["abc123"])

    def test_bypass_global_group_and_select_flags(self):
        self.assertMatches("agent-deck -g conductor remove abc123", ["abc123"])
        self.assertMatches("agent-deck --select abc123 remove def456", ["def456"])
        self.assertMatches("agent-deck --profile=work remove abc123", ["abc123"])

    def test_bypass_second_removal_in_the_same_command(self):
        # Returning on the first match left 'b' unchecked and destroyable.
        self.assertMatches(
            "agent-deck session remove a && agent-deck session remove b", ["a", "b"]
        )

    def test_bypass_nested_shell_invocation(self):
        self.assertMatches("bash -c 'agent-deck session remove x'", ["x"])
        self.assertMatches('sh -c "agent-deck rm y"', ["y"])

    def test_unbalanced_quotes_err_toward_denying(self):
        found = lib.find_removal("agent-deck session remove 'abc")
        self.assertIsNotNone(found)
        self.assertTrue(found.unparsed)

    def test_unbalanced_quotes_do_not_deny_on_a_substring_of_a_word(self):
        # 'rm' appears inside 'confirm'. A substring screen denied this.
        self.assertIsNone(lib.find_removal("agent-deck list && echo \"don't confirm"))

    # --- the three false positives measured 2026-08-27. Each was verified to
    # --- block before the fix and allow after it.

    def test_fd_redirect_does_not_become_a_phantom_ref(self):
        # Bug 1: `2>&1` was split by _OPERATOR_RE at the `&`, creating a `2>`
        # token that became a session ref. The guard refused a valid removal
        # because it tried to look up `2>` in the registry.
        found = self.assertMatches("agent-deck session remove abc 2>&1", ["abc"])
        self.assertFalse(found.unparsed)

    def test_other_redirects_are_not_refs(self):
        self.assertMatches("agent-deck session remove abc > /dev/null", ["abc"])
        self.assertMatches("agent-deck session remove abc 2>/dev/null", ["abc"])
        self.assertMatches("agent-deck remove abc >> log.txt", ["abc"])

    def test_heredoc_body_is_not_scanned_for_commands(self):
        # Bug 2: a heredoc writing a dispatch brief was refused because the
        # prose mentioned session commands. The body is data, not a command.
        self.assertIsNone(lib.find_removal(
            "cat <<'BRIEF' > /tmp/dispatch.md\n"
            "Worker instructions:\n"
            "1. Use agent-deck session send <id> to deliver results\n"
            "2. The conductor will remove your session when done\n"
            "BRIEF"
        ))

    def test_bd_command_quoting_removal_is_not_a_removal(self):
        # Bug 3: a bd command whose description text quoted a session-removal
        # command was blocked by the substitution fallback.
        self.assertIsNone(lib.find_removal(
            "TITLE=$(cat <<'BD_TITLE'\n"
            "the guard blocked agent-deck session remove for no reason\n"
            "BD_TITLE\n"
            ")\n"
            'bd create "$TITLE" -p 2 -l agent-proposed'
        ))

    def test_heredoc_with_real_removal_after_it_still_blocks(self):
        # Stripping heredoc bodies must not hide a real removal on a later line.
        self.assertMatches(
            "cat <<'EOF' > brief.md\n"
            "just some text\n"
            "EOF\n"
            "agent-deck session remove abc",
            ["abc"],
        )


class RegistryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = registry_helpers.temp_registry(
            [
                {"id": "cond-1111", "title": "conductor-hq", "is_conductor": 1},
                {"id": "work-2222", "title": "a-worker"},
                {"id": "work-2299", "title": "twin-worker"},
                {"id": "odd_id-33", "title": "has-underscore"},
            ],
            Path(self.tmp.name) / "does-not-exist-yet",
        )

    def test_is_conductor_distinguishes_true_false_and_absent(self):
        self.assertIs(lib.is_conductor("cond-1111", self.db), True)
        self.assertIs(lib.is_conductor("work-2222", self.db), False)
        self.assertIsNone(lib.is_conductor("ghost", self.db))

    def test_unreadable_db_raises_rather_than_reporting_not_conductor(self):
        with self.assertRaises(lib.RegistryUnavailable):
            lib.is_conductor("cond-1111", Path(self.tmp.name) / "absent.db")

    def test_resolves_full_id_unique_prefix_and_title(self):
        for ref in ("work-2222", "a-worker"):
            self.assertEqual(lib.resolve_session(ref, self.db)["id"], "work-2222", ref)
        self.assertEqual(lib.resolve_session("cond", self.db)["id"], "cond-1111")

    def test_ambiguous_prefix_raises_instead_of_picking_one(self):
        # Taking the first row let the guard validate one session's receipt
        # while agent-deck destroyed another.
        with self.assertRaises(lib.AmbiguousReference):
            lib.resolve_session("work-22", self.db)

    def test_like_metacharacters_are_escaped(self):
        # '_' is a LIKE wildcard, so '_ond-1111' matched the conductor.
        self.assertIsNone(lib.resolve_session("_ond-1111", self.db))
        self.assertIsNone(lib.resolve_session("%", self.db))
        self.assertEqual(lib.resolve_session("odd_id-33", self.db)["id"], "odd_id-33")

    def test_unknown_reference_returns_none(self):
        self.assertIsNone(lib.resolve_session("zzz", self.db))


class PathTest(unittest.TestCase):
    def test_state_db_candidates_names_both_xdg_and_legacy(self):
        candidates = lib.state_db_candidates({"HOME": "/h"})
        self.assertEqual(len(candidates), 2)
        self.assertIn(".local/share/agent-deck", str(candidates[0]))
        self.assertIn(".agent-deck", str(candidates[1]))

    def test_override_wins_and_is_the_only_candidate(self):
        self.assertEqual(
            lib.state_db_candidates({"PRECLOSE_STATE_DB": "/x/y.db"}), [Path("/x/y.db")]
        )


class ProbeSessionOutputTest(unittest.TestCase):
    def test_an_unrunnable_agent_deck_is_unknown_not_a_crash(self):
        # The dangling-import bug: this branch raised NameError instead of
        # returning, and Stage B's broad catch turned it into an internal-error
        # deny with the wrong diagnosis.
        result = lib.probe_session_output("s", fixtures.failing_run(), 1.0, "claude")
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "unreachable")
        self.assertIn("could not run agent-deck", result.reason)

    def test_a_subprocess_timeout_is_also_unknown(self):
        import subprocess

        result = lib.probe_session_output(
            "s",
            fixtures.failing_run(subprocess.TimeoutExpired("agent-deck", 1)),
            1.0,
            "claude",
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "unreachable")

    def test_a_missing_binary_is_unreachable(self):
        original = lib.agent_deck_binary
        lib.agent_deck_binary = lambda: None
        self.addCleanup(setattr, lib, "agent_deck_binary", original)
        result = lib.probe_session_output("s", fixtures.failing_run(), 1.0, "claude")
        self.assertFalse(result.ok)
        self.assertEqual(result.code, "unreachable")
        self.assertIn("could not be found", result.reason)


class DeferredImportTest(unittest.TestCase):
    """Deferring an import into one function while another still names it
    produced a live NameError that 96 tests did not catch, because no test drove
    that branch. This checks the whole class statically instead."""

    def test_no_module_names_a_deferred_import_it_did_not_import(self):
        import subprocess as sp

        hooks = Path(__file__).resolve().parents[1]
        checker = Path(__file__).resolve().parent / "check_deferred_imports.py"
        targets = [
            str(hooks / name)
            for name in (
                "preclose_lib.py",
                "preclose_guard.py",
                "preclose_receipt.py",
                "preclose_checklist.py",
            )
        ]
        done = sp.run(
            [sys.executable, str(checker), *targets], capture_output=True, text=True
        )
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_the_checker_can_actually_fail(self):
        # A checker nobody has watched refuse something is worth nothing.
        import subprocess as sp
        import tempfile as tf

        with tf.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.py"
            bad.write_text(
                "def f():\n"
                "    try:\n"
                "        pass\n"
                "    except (OSError, subprocess.SubprocessError):\n"
                "        pass\n"
            )
            checker = Path(__file__).resolve().parent / "check_deferred_imports.py"
            done = sp.run(
                [sys.executable, str(checker), str(bad)], capture_output=True, text=True
            )
        self.assertEqual(done.returncode, 1)
        self.assertIn("subprocess", done.stdout)


if __name__ == "__main__":
    unittest.main()
