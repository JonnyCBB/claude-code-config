#!/usr/bin/env python3
"""Unit tests for aggregate_verify.py (Plan 2 replacement).

Tests the validation-state.json parsing interface:
- All-passed, any-failed, any-blocked, mixed statuses
- Per-assertion output with actual vs expected
- Empty assertions, missing file, malformed JSON
- main() argv path
- merge_recheck() and the `merge` CLI subcommand for superseding prior
  results with targeted live-recheck results (verify-fix loop)
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aggregate_verify import VERDICT_BLOCKED, aggregate, main, merge_recheck

ALL_PASSED = {
    "assertions": [
        {
            "id": "VAL-API-001",
            "status": "passed",
            "expected": "200",
            "actual": "200",
            "commands_executed": ["curl localhost:8080/health"],
            "evidence": "HTTP 200 OK",
        },
        {
            "id": "VAL-API-002",
            "status": "passed",
            "expected": "tracks field present",
            "actual": "tracks field present",
            "commands_executed": ["grpcurl ..."],
            "evidence": "response contains tracks",
        },
    ]
}

ANY_FAILED = {
    "assertions": [
        {"id": "VAL-API-001", "status": "passed", "expected": "200", "actual": "200"},
        {"id": "VAL-API-002", "status": "failed", "expected": "tracks", "actual": "empty response"},
    ]
}

ANY_BLOCKED = {
    "assertions": [
        {"id": "VAL-API-001", "status": "passed", "expected": "200", "actual": "200"},
        {"id": "VAL-DATA-001", "status": "blocked", "block_reason": "auth failure"},
    ]
}

MIXED_FAIL_BLOCK = {
    "assertions": [
        {"id": "VAL-API-001", "status": "failed", "expected": "200", "actual": "500"},
        {"id": "VAL-DATA-001", "status": "blocked", "block_reason": "missing service"},
    ]
}


class TestAggregate(unittest.TestCase):
    def test_all_passed(self):
        out = aggregate(ALL_PASSED)
        self.assertIn("Overall: PASS", out)
        self.assertIn("2/2 passed", out)

    def test_any_failed_yields_fail(self):
        out = aggregate(ANY_FAILED)
        self.assertIn("Overall: FAIL", out)
        self.assertIn("1/2 passed", out)

    def test_any_blocked_yields_blocked(self):
        out = aggregate(ANY_BLOCKED)
        self.assertIn("Overall: BLOCKED", out)

    def test_fail_overrides_blocked(self):
        out = aggregate(MIXED_FAIL_BLOCK)
        self.assertIn("Overall: FAIL", out)

    def test_per_assertion_table(self):
        out = aggregate(ANY_FAILED)
        self.assertIn("VAL-API-001", out)
        self.assertIn("VAL-API-002", out)
        self.assertIn("passed", out)
        self.assertIn("failed", out)

    def test_empty_assertions(self):
        out = aggregate({"assertions": []})
        self.assertRegex(out.lower(), r"no assertions")

    def test_evidence_in_output(self):
        out = aggregate(ALL_PASSED)
        self.assertIn("HTTP 200 OK", out)

    def test_block_reason_in_output(self):
        out = aggregate(ANY_BLOCKED)
        self.assertIn("auth failure", out)


class TestMain(unittest.TestCase):
    def test_main_reads_json_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "validation-state.json"
            p.write_text(json.dumps(ALL_PASSED))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main([str(p)])
        self.assertEqual(rc, 0)
        self.assertIn("Overall: PASS", buf.getvalue())

    def test_main_missing_file(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["/nonexistent/validation-state.json"])
        self.assertEqual(rc, 1)

    def test_main_malformed_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "validation-state.json"
            p.write_text("not json")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main([str(p)])
        self.assertEqual(rc, 1)


class TestMergeRecheck(unittest.TestCase):
    def test_recheck_supersedes_matching_id(self):
        base = {"assertions": [{"id": "VAL-API-008", "status": "failed", "actual": "old"}]}
        recheck = {"assertions": [{"id": "VAL-API-008", "status": "passed", "actual": "new"}]}
        merged = merge_recheck(base, recheck)
        self.assertEqual(len(merged["assertions"]), 1)
        self.assertEqual(merged["assertions"][0]["status"], "passed")
        self.assertEqual(merged["assertions"][0]["actual"], "new")

    def test_unmatched_base_ids_are_preserved(self):
        base = {
            "assertions": [
                {"id": "VAL-API-001", "status": "passed"},
                {"id": "VAL-API-008", "status": "failed"},
            ]
        }
        recheck = {"assertions": [{"id": "VAL-API-008", "status": "passed"}]}
        merged = merge_recheck(base, recheck)
        ids = [a["id"] for a in merged["assertions"]]
        self.assertEqual(ids, ["VAL-API-001", "VAL-API-008"])
        by_id = {a["id"]: a for a in merged["assertions"]}
        self.assertEqual(by_id["VAL-API-001"]["status"], "passed")
        self.assertEqual(by_id["VAL-API-008"]["status"], "passed")

    def test_recheck_ids_not_in_base_are_appended(self):
        base = {"assertions": [{"id": "VAL-API-001", "status": "passed"}]}
        recheck = {"assertions": [{"id": "GATE-TEST", "status": "passed"}]}
        merged = merge_recheck(base, recheck)
        ids = [a["id"] for a in merged["assertions"]]
        self.assertEqual(ids, ["VAL-API-001", "GATE-TEST"])

    def test_non_assertion_top_level_keys_preserved_from_base(self):
        base = {"assertions": [], "run_id": "example-run"}
        recheck = {"assertions": []}
        merged = merge_recheck(base, recheck)
        self.assertEqual(merged["run_id"], "example-run")


class TestMergeMain(unittest.TestCase):
    def test_merge_writes_superseded_state_to_output_path(self):
        with tempfile.TemporaryDirectory() as d:
            base_path = Path(d) / "validation-state.json"
            recheck_path = Path(d) / "recheck.json"
            out_path = Path(d) / "validation-state.json"
            base_path.write_text(json.dumps({"assertions": [{"id": "VAL-API-008", "status": "failed"}]}))
            recheck_path.write_text(json.dumps({"assertions": [{"id": "VAL-API-008", "status": "passed"}]}))
            rc = main(["merge", str(out_path), str(base_path), str(recheck_path)])
            self.assertEqual(rc, 0)
            merged = json.loads(out_path.read_text())
        self.assertEqual(merged["assertions"][0]["status"], "passed")

    def test_merge_applies_multiple_recheck_files_in_order(self):
        with tempfile.TemporaryDirectory() as d:
            base_path = Path(d) / "validation-state.json"
            recheck1_path = Path(d) / "recheck-1.json"
            recheck2_path = Path(d) / "recheck-2.json"
            out_path = Path(d) / "merged.json"
            base_path.write_text(json.dumps({"assertions": [{"id": "VAL-API-004", "status": "failed"}]}))
            recheck1_path.write_text(json.dumps({"assertions": [{"id": "VAL-API-004", "status": "failed"}]}))
            recheck2_path.write_text(json.dumps({"assertions": [{"id": "VAL-API-004", "status": "passed"}]}))
            rc = main(["merge", str(out_path), str(base_path), str(recheck1_path), str(recheck2_path)])
            self.assertEqual(rc, 0)
            merged = json.loads(out_path.read_text())
        self.assertEqual(merged["assertions"][0]["status"], "passed")

    def test_merge_missing_base_file_returns_error(self):
        with tempfile.TemporaryDirectory() as d:
            out_path = Path(d) / "merged.json"
            recheck_path = Path(d) / "recheck.json"
            recheck_path.write_text(json.dumps({"assertions": []}))
            rc = main(["merge", str(out_path), "/nonexistent/base.json", str(recheck_path)])
        self.assertEqual(rc, 1)

    def test_merge_requires_at_least_one_recheck_file(self):
        with tempfile.TemporaryDirectory() as d:
            base_path = Path(d) / "validation-state.json"
            out_path = Path(d) / "merged.json"
            base_path.write_text(json.dumps({"assertions": []}))
            rc = main(["merge", str(out_path), str(base_path)])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
