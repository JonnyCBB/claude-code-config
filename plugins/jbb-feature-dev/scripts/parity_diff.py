#!/usr/bin/env python3
"""Compare OLD-agent and NEW-agent /code-review outputs by finding-category coverage.

Resolves iter-3 Arch SC-3: Wave 4.1 §Section 2 behavioral parity must not
rely on human eyeballing alone.

Strategy: parse each output for block headers (TEST NEEDED, REDUNDANT TEST,
QUALITY ISSUE, ISSUE) and their Priority/Severity tags. Build a Counter of
(block_name, severity) pairs. Compare new vs baseline: flag any category
that's MISSING from new, and any category that dropped >20% in count.

This catches the dominant regression mode (silent loss of a finding category)
without requiring exact match (which would over-trigger on minor LLM-output
variation).

Usage:
    python3 scripts/parity_diff.py --self-test
    python3 scripts/parity_diff.py --baseline <path> --new <path>
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

BLOCK_PATTERN = re.compile(
    r"^(TEST NEEDED|REDUNDANT TEST|QUALITY ISSUE|ISSUE)\s*#?\d*\s*:?",
    re.MULTILINE,
)
SEVERITY_PATTERN = re.compile(
    r"^(?:Priority|Severity):\s*(\w+)",
    re.MULTILINE,
)

# NEW must be >= 80% of OLD per category (20% drift tolerated).
REGRESSION_THRESHOLD = 0.80


def extract_categories(text: str) -> Counter:
    """Return Counter({(block_name, severity): count})."""
    categories: Counter = Counter()
    chunks = re.split(
        r"(?=^(?:TEST NEEDED|REDUNDANT TEST|QUALITY ISSUE|ISSUE))",
        text,
        flags=re.MULTILINE,
    )
    for chunk in chunks:
        block_match = BLOCK_PATTERN.search(chunk)
        if not block_match:
            continue
        block = block_match.group(1)
        sev_match = SEVERITY_PATTERN.search(chunk)
        sev = sev_match.group(1) if sev_match else "Unspecified"
        categories[(block, sev)] += 1
    return categories


def compare(baseline: Counter, new: Counter) -> list:
    """Return list of regression strings (empty list = parity acceptable)."""
    regressions = []
    for cat, old_count in baseline.items():
        new_count = new.get(cat, 0)
        if new_count == 0:
            regressions.append(
                f"MISSING category {cat!r}: baseline had {old_count}, new has 0"
            )
            continue
        if new_count < old_count * REGRESSION_THRESHOLD:
            regressions.append(
                f"DROP >20% in {cat!r}: baseline {old_count}, new {new_count}"
            )
    return regressions


def self_test():
    a = "TEST NEEDED #1:\nPriority: High\n...\nISSUE #1:\nSeverity: Medium\n..."
    assert compare(extract_categories(a), extract_categories(a)) == [], (
        "identical inputs must produce no regressions"
    )

    # New is missing the TEST NEEDED block -> regression flagged.
    b = "ISSUE #1:\nSeverity: Medium\n..."
    regs = compare(extract_categories(a), extract_categories(b))
    assert any("MISSING" in r for r in regs), f"expected MISSING regression, got {regs}"

    # New has fewer than 80% in a category -> DROP regression flagged.
    big_baseline = "\n".join(
        f"TEST NEEDED #{i}:\nPriority: High\n..." for i in range(10)
    )
    small_new = "\n".join(
        f"TEST NEEDED #{i}:\nPriority: High\n..." for i in range(5)
    )  # 50% retention
    regs2 = compare(extract_categories(big_baseline), extract_categories(small_new))
    assert any("DROP" in r for r in regs2), f"expected DROP regression, got {regs2}"

    print("self-test: OK")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--baseline", type=Path)
    p.add_argument("--new", type=Path)
    args = p.parse_args()

    if args.self_test:
        self_test()
        sys.exit(0)
    if not (args.baseline and args.new):
        print("usage: parity_diff.py --baseline <path> --new <path>", file=sys.stderr)
        sys.exit(2)

    baseline = extract_categories(args.baseline.read_text())
    new = extract_categories(args.new.read_text())
    regs = compare(baseline, new)
    if regs:
        print("PARITY REGRESSIONS:", file=sys.stderr)
        for r in regs:
            print(f"  - {r}", file=sys.stderr)
        sys.exit(1)
    print(f"parity OK: {len(baseline)} categories, all within threshold")
    sys.exit(0)


if __name__ == "__main__":
    main()
