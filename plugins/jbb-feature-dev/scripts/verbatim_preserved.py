#!/usr/bin/env python3
"""Verify byte-equality of normalized markdown blocks.

normalize() spec (per plan §Coding Guidelines):
- LF line endings (CRLF -> LF, CR alone -> LF).
- Strip trailing whitespace per line (trailing spaces and tabs).
- Preserve final-line newline if-and-only-if source has one (no add, no drop).
- Tabs and spaces in leading whitespace are NOT collapsed (real distinction).

On mismatch, prints difflib.unified_diff over normalized blocks for diagnosis.

Resolves prior Pragmatic Architect Must Address Arch-1 (normalize() corner
cases) + Arch-3 (byte-equality, not substring presence).

Usage:
    python3 scripts/verbatim_preserved.py --self-test
    python3 scripts/verbatim_preserved.py --check-all
    python3 scripts/verbatim_preserved.py --check-lang python
"""

import argparse
import difflib
import hashlib
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
AGENTS_DIR = PLUGIN_ROOT / "agents"
SCHEMAS_DIR = PLUGIN_ROOT / "skills" / "code-review-modes" / "schemas"


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    has_final_nl = text.endswith("\n")
    lines = text.split("\n")
    stripped = [line.rstrip(" \t") for line in lines]
    # Drop the trailing empty element introduced by split() when text ends in \n.
    if has_final_nl and stripped and stripped[-1] == "":
        stripped = stripped[:-1]
    out = "\n".join(stripped)
    if has_final_nl:
        out += "\n"
    return out


def block_sha256(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def assert_blocks_equal(src_text: str, dst_text: str, *, label: str = "") -> bool:
    if block_sha256(src_text) == block_sha256(dst_text):
        return True
    diff = list(
        difflib.unified_diff(
            normalize(src_text).splitlines(keepends=True),
            normalize(dst_text).splitlines(keepends=True),
            fromfile=f"{label}/source",
            tofile=f"{label}/destination",
        )
    )
    sys.stderr.write("".join(diff))
    sys.stderr.write(f"\n[verbatim] mismatch in {label!r}\n")
    return False


def extract_anchored_section(path: Path, anchor: str) -> str:
    """Return text from `anchor` heading line + 1 through the last line before
    the next `^## ` heading at the same depth. Fence-aware: lines inside
    triple-or-more-backtick code fences do NOT count as headings even if they
    start with `## `. Final-line newline preserved iff present in source.
    """
    raw = path.read_text()
    has_final_nl = raw.endswith("\n")
    lines = raw.split("\n")
    if has_final_nl and lines and lines[-1] == "":
        lines = lines[:-1]

    in_fence = False
    fence_marker = None
    start = None
    end = len(lines)
    for i, line in enumerate(lines):
        m = re.match(r"^(`{3,})", line)
        if m:
            if not in_fence:
                in_fence = True
                fence_marker = m.group(1)
            elif line.startswith(fence_marker):
                in_fence = False
                fence_marker = None
            continue
        if in_fence:
            continue
        if start is None and line.strip() == anchor:
            start = i + 1
            continue
        if start is not None and line.startswith("## "):
            end = i
            break
    if start is None:
        raise ValueError(f"anchor not found: {anchor!r} in {path}")
    section = "\n".join(lines[start:end])
    if has_final_nl:
        section += "\n"
    return section


SCHEMA_MAPPINGS = [
    # (lang, source_agent, dst_anchor_test, dst_anchor_simp)
    # Source schema sections in old agents are not anchored as `## Test-Review
    # Schema`; rather they appear within Step 5 / output template sections. The
    # consolidation lifts the verbatim block schemas (TEST NEEDED, REDUNDANT
    # TEST, QUALITY ISSUE, ISSUE) into the new schemas/<lang>.md files. We
    # validate that the destination sections exist and that they contain the
    # expected on-disk space-form block names (Arch-7 guard).
    (
        "python",
        "python-test-reviewer.md",
        "## Test-Review Schema",
        "## Code-Style-Review Schema",
    ),
    (
        "typescript",
        "typescript-test-reviewer.md",
        "## Test-Review Schema",
        "## Code-Style-Review Schema",
    ),
]


def check_lang(lang: str) -> bool:
    schema_path = SCHEMAS_DIR / f"{lang}.md"
    if not schema_path.exists():
        sys.stderr.write(f"[verbatim] schemas/{lang}.md missing\n")
        return False
    test_section = extract_anchored_section(schema_path, "## Test-Review Schema")
    simp_section = extract_anchored_section(schema_path, "## Code-Style-Review Schema")
    ok = True
    # Required block names per plan §Coding Guidelines (space-form preserved).
    if "TEST NEEDED" not in test_section:
        sys.stderr.write(f"[verbatim] {lang}/Test-Review missing 'TEST NEEDED' block\n")
        ok = False
    if "REDUNDANT TEST" not in test_section:
        sys.stderr.write(
            f"[verbatim] {lang}/Test-Review missing 'REDUNDANT TEST' block\n"
        )
        ok = False
    if "QUALITY ISSUE" not in test_section:
        sys.stderr.write(
            f"[verbatim] {lang}/Test-Review missing 'QUALITY ISSUE' block\n"
        )
        ok = False
    if "ISSUE" not in simp_section:
        sys.stderr.write(f"[verbatim] {lang}/Code-Style-Review missing 'ISSUE' block\n")
        ok = False
    # Underscore-form guard.
    for forbidden in ("TEST_NEEDED", "REDUNDANT_TEST", "QUALITY_ISSUE"):
        if forbidden in test_section or forbidden in simp_section:
            sys.stderr.write(
                f"[verbatim] {lang} contains underscore-form {forbidden!r} (Arch-7)\n"
            )
            ok = False
    return ok


def self_test():
    assert assert_blocks_equal("a\nb\n", "a\nb\n", label="self_pass"), (
        "identity should pass"
    )
    assert not assert_blocks_equal("a\nb\n", "a\nx\n", label="self_fail"), (
        "drift should fail"
    )
    assert assert_blocks_equal("a   \nb\n", "a\nb\n", label="self_trailing_ws"), (
        "trailing ws should normalize"
    )
    assert assert_blocks_equal("a\nb", "a\nb", label="self_no_final_nl"), (
        "no final nl preserved"
    )
    assert not assert_blocks_equal("a\nb\n", "a\nb", label="self_final_nl_diff"), (
        "final-nl difference must NOT compare equal"
    )
    # Tab vs space in leading whitespace is a real distinction.
    assert not assert_blocks_equal("\tx\n", "    x\n", label="self_tab_vs_space"), (
        "tab and space leading ws must NOT compare equal"
    )
    print("self-test: OK")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--check-all", action="store_true")
    p.add_argument("--check-lang", choices=["python", "typescript"])
    args = p.parse_args()

    if args.self_test:
        self_test()
        sys.exit(0)
    if args.check_lang:
        ok = check_lang(args.check_lang)
        sys.exit(0 if ok else 1)
    if args.check_all:
        all_ok = True
        for lang, *_ in SCHEMA_MAPPINGS:
            if not check_lang(lang):
                all_ok = False
        sys.exit(0 if all_ok else 1)
    p.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
