#!/usr/bin/env python3
"""Unit tests for hooks/preclose_lib.py."""

from __future__ import annotations

import subprocess
import sys
import time
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

    def test_a_database_that_opens_but_cannot_be_queried_still_raises(self):
        # The failure that OPENS fine and fails on execute - a registry whose
        # schema has moved, say. It reaches a different except clause from the
        # missing-file case above, and nothing exercised it: replacing that
        # clause with one that catches ValueError left every test passing.
        import sqlite3

        empty = Path(self.tmp.name) / "schemaless.db"
        sqlite3.connect(str(empty)).close()
        for call in (
            lambda: lib.is_conductor("cond-1111", empty),
            lambda: lib.resolve_session("cond-1111", empty),
        ):
            with self.assertRaises(lib.RegistryUnavailable):
                call()

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


class SessionLivenessTest(unittest.TestCase):
    """A session is only finished when its terminal has stopped advancing."""

    def liveness(self, row, run):
        return lib.session_liveness(row, run=run, settle=0.0)

    def row(self, **overrides):
        row = {"id": "s1", "title": "a-session", "tmux_session": "agentdeck_a_1111"}
        row.update(overrides)
        return row

    def test_a_terminal_that_changes_between_two_reads_is_running(self):
        state = self.liveness(
            self.row(), fixtures.fake_deck(panes=["working 1h28m24s", "working 1h28m35s"])
        )
        self.assertEqual(state.state, "running")

    def test_a_terminal_identical_across_two_reads_is_quiet(self):
        state = self.liveness(self.row(), fixtures.fake_deck(panes=["done, nothing moving"]))
        self.assertEqual(state.state, "quiet")

    def test_an_empty_terminal_is_not_evidence_that_it_stopped(self):
        # The degenerate case that reads as "finished" if you only compare the
        # two captures: a pane that comes back empty twice is identical twice.
        state = self.liveness(self.row(), fixtures.fake_deck(panes=["   \n"]))
        self.assertEqual(state.state, "unknown")

    def test_a_terminal_that_no_longer_exists_is_quiet(self):
        state = self.liveness(self.row(), fixtures.fake_deck(panes=None))
        self.assertEqual(state.state, "quiet")

    def test_a_session_with_no_recorded_terminal_is_quiet(self):
        state = self.liveness(self.row(tmux_session=""), fixtures.fake_deck(panes=None))
        self.assertEqual(state.state, "quiet")

    def test_tmux_that_cannot_be_run_at_all_is_unknown(self):
        state = self.liveness(self.row(), fixtures.failing_run())
        self.assertEqual(state.state, "unknown")

    def test_a_capture_that_fails_is_unknown(self):
        run = fixtures.fake_deck(panes=["a pane"], capture_rc=1)
        self.assertEqual(self.liveness(self.row(), run).state, "unknown")

    def test_the_terminal_is_named_exactly_so_a_prefix_cannot_match_another_session(self):
        # Measured on tmux 3.5a: `has-session -t agentdeck_api-mcp` succeeds
        # against `agentdeck_api-mcp-drive_39547e77`, and `capture-pane` on the
        # same prefix returns THAT session's pane. Reading the wrong pane would
        # answer the liveness question about the wrong session.
        seen = []

        def run(argv, timeout):
            seen.append(argv)
            return subprocess.CompletedProcess(list(argv), 0, "quiet pane", "")

        self.liveness(self.row(), run)
        self.assertIn("-t=agentdeck_a_1111", seen[0])

    def test_activity_reads_window_activity_and_not_session_activity(self):
        # Measured on a pane repainting in place every 0.3s with no newline:
        # window_activity advanced every second, session_activity never moved.
        # No fake runner can tell the two format strings apart, so the choice is
        # pinned here or it is pinned nowhere.
        seen = []

        def run(argv, timeout):
            seen.append(argv)
            return subprocess.CompletedProcess(list(argv), 0, "1789321182\n", "")

        self.assertEqual(lib.last_activity_stamp(self.row(), run), "1789321182")
        self.assertIn("#{window_activity}", seen[-1])

    def test_activity_is_empty_when_the_terminal_is_gone_and_none_when_unaskable(self):
        self.assertEqual(lib.last_activity_stamp(self.row(), fixtures.fake_deck(panes=None)), "")
        self.assertIsNone(lib.last_activity_stamp(self.row(), fixtures.failing_run()))


    def argv_of(self, verb, call, **row):
        seen = []

        def run(argv, timeout):
            seen.append(argv)
            return subprocess.CompletedProcess(list(argv), 0, "1789321182\n", "")

        call(self.row(**row), run)
        return next(a for a in seen if verb in a)

    def test_the_reads_use_the_plain_target_form_that_tmux_accepts(self):
        # `-t=` is exact but capture-pane and list-panes REJECT it outright
        # ("can't find pane: =foo"), so sending it there makes every capture fail,
        # every session read "unknown", and every session permanently unremovable.
        name = "agentdeck_a_1111"
        capture = self.argv_of("capture-pane", lambda r, run: self.liveness(r, run))
        listed = self.argv_of("list-panes", lib.last_activity_stamp)
        for argv in (capture, listed):
            self.assertIn("-t", argv)
            self.assertIn(name, argv)
            self.assertNotIn("-t=" + name, argv)
        self.assertEqual(capture[capture.index("-S") + 1], "-60")
        self.assertIn("-s", listed)

    def test_the_two_reads_are_separated_by_a_real_interval_by_default(self):
        # Every other test overrides settle, so the production default is
        # constrained by this test alone: at 0.0 the two captures are taken
        # back-to-back, come back identical, and the original defect returns
        # while the suite stays green.
        stamps = []

        def run(argv, timeout):
            if "capture-pane" in argv:
                stamps.append(time.monotonic())
            return subprocess.CompletedProcess(list(argv), 0, "a quiet pane", "")

        lib.session_liveness(self.row(), run)
        self.assertGreaterEqual(stamps[1] - stamps[0], 1.0)

    def test_a_prefix_of_another_session_does_not_resolve(self):
        run = fixtures.fake_deck(
            panes=["quiet"], live={"agentdeck_a_1111-drive_39547e77"}
        )
        self.assertEqual(self.liveness(self.row(), run).state, "quiet")
        self.assertEqual(
            self.liveness(self.row(), run).reason.split()[0:2], ["its", "terminal"]
        )

    def test_only_tmux_saying_the_session_is_gone_reads_as_gone(self):
        # Measured on tmux 3.7c, all of these exit 1. Two are facts about the
        # session; the third says only that this process cannot reach the server,
        # and reading it as "gone" turns the gate off for every session at once.
        cases = {
            "can't find session: agentdeck_a_1111": ("quiet", ""),
            "no server running on /private/tmp/tmux-501/default": ("quiet", ""),
            "error connecting to /private/tmp/tmux-501/x (No such file or directory)": (
                "unknown",
                None,
            ),
            "": ("unknown", None),
        }
        for stderr, (state, stamp) in cases.items():

            def run(argv, timeout, stderr=stderr):
                return subprocess.CompletedProcess(list(argv), 1, "", stderr)

            self.assertEqual(self.liveness(self.row(), run).state, state, stderr)
            self.assertEqual(lib.last_activity_stamp(self.row(), run), stamp, stderr)

    def test_a_list_panes_that_exits_nonzero_is_unaskable_not_empty(self):
        # "" means "there is no terminal", which ALLOWS a removal. A failed read
        # must not spell itself the same way.
        run = fixtures.fake_deck(panes=["quiet"], list_rc=1)
        self.assertIsNone(lib.last_activity_stamp(self.row(), run))

    def test_every_pane_in_the_session_contributes_to_the_stamp(self):
        def run(argv, timeout):
            if "list-panes" in argv:
                return subprocess.CompletedProcess(
                    list(argv), 0, "1789321182\n1789321190\n", ""
                )
            return subprocess.CompletedProcess(list(argv), 0, "", "")

        self.assertEqual(
            lib.last_activity_stamp(self.row(), run), "1789321182,1789321190"
        )


    def test_a_pane_reprinting_identical_bytes_still_reads_as_running(self):
        # Measured: a pane reprinting the SAME bytes every 0.3s captures
        # identically while #{window_activity} advances. Certifying on the pane
        # alone hands the guard a stamp that has already moved, so the checklist
        # passes, the removal is refused, and re-running reproduces the pair
        # forever - a session that can never be retired.
        stamps = iter(["100", "200"])

        def run(argv, timeout):
            if "list-panes" in argv:
                return subprocess.CompletedProcess(list(argv), 0, next(stamps), "")
            return subprocess.CompletedProcess(list(argv), 0, "working", "")

        self.assertEqual(self.liveness(self.row(), run).state, "running")

    def test_a_quiet_verdict_carries_the_stamp_the_guard_will_re_read(self):
        state = self.liveness(self.row(), fixtures.fake_deck(panes=["still"]))
        self.assertEqual(state.state, "quiet")
        self.assertEqual(state.stamp, fixtures.ACTIVITY)

    def test_a_terminal_that_is_gone_carries_an_empty_stamp_not_a_missing_one(self):
        # "" compares equal to itself, so a session whose pane was already gone
        # stays removable. None would refuse forever.
        self.assertEqual(self.liveness(self.row(), fixtures.fake_deck(panes=None)).stamp, "")


    def test_a_socket_name_is_passed_through(self):
        seen = []

        def run(argv, timeout):
            seen.append(argv)
            return subprocess.CompletedProcess(list(argv), 0, "quiet pane", "")

        self.liveness(self.row(tmux_socket_name="alt"), run)
        self.assertEqual(seen[0][1:3], ["-L", "alt"])



if __name__ == "__main__":
    unittest.main()
