#!/usr/bin/env python3
"""Unit tests for scripts/_lib/frontmatter.py.

The shared utility now has 3+ consumers (validate_consolidation,
validate_plan_b_contract_artifacts, validate_plan_c_orchestrator); pin its
contract directly so a regression in any consumer surfaces here first.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# scripts/ is the import root for the _lib package.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _lib.frontmatter import parse_frontmatter, parse_skills_field  # noqa: E402


class TestParseFrontmatter(unittest.TestCase):
    def test_happy_path_dict(self):
        text = "---\nname: foo\nmodel: opus\n---\nbody"
        self.assertEqual(parse_frontmatter(text), {"name": "foo", "model": "opus"})

    def test_no_opening_fence_returns_none(self):
        self.assertIsNone(parse_frontmatter("name: foo\n"))

    def test_no_closing_fence_returns_none(self):
        self.assertIsNone(parse_frontmatter("---\nname: foo\nbody-without-close"))

    def test_yaml_error_returns_none(self):
        # Unbalanced braces parse as a YAMLError.
        self.assertIsNone(parse_frontmatter("---\n{unbalanced: \n---\nbody"))

    def test_list_payload_returns_none(self):
        # A YAML list at the top level violates the declared return contract;
        # consumer code does fm.get(...) which would AttributeError on a list.
        self.assertIsNone(parse_frontmatter("---\n- a\n- b\n---\nbody"))

    def test_scalar_payload_returns_none(self):
        # A bare scalar (string) is not a mapping either.
        self.assertIsNone(parse_frontmatter("---\nfoo\n---\nbody"))

    def test_empty_frontmatter_returns_none(self):
        # Empty frontmatter (yaml.safe_load -> None) is not a dict.
        self.assertIsNone(parse_frontmatter("---\n---\nbody"))


class TestParseSkillsField(unittest.TestCase):
    def test_list_payload(self):
        self.assertEqual(parse_skills_field(["foo", "bar"]), {"foo", "bar"})

    def test_string_payload_comma_split(self):
        self.assertEqual(parse_skills_field("foo, bar, baz"), {"foo", "bar", "baz"})

    def test_string_payload_single(self):
        self.assertEqual(parse_skills_field("foo"), {"foo"})

    def test_none_payload(self):
        self.assertEqual(parse_skills_field(None), set())

    def test_empty_list(self):
        self.assertEqual(parse_skills_field([]), set())

    def test_empty_string(self):
        self.assertEqual(parse_skills_field(""), set())

    def test_dict_payload_returns_empty(self):
        self.assertEqual(parse_skills_field({"a": 1}), set())


if __name__ == "__main__":
    unittest.main()
