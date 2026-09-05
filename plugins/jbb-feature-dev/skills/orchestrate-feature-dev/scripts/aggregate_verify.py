#!/usr/bin/env python3
"""Aggregate validator results from validation-state.json into a markdown summary.

Optionally cross-references against the verification contract to detect
assertions the validator omitted from its output.

Also provides the canonical merge path for the verify-fix loop's targeted
live rechecks (see `merge_recheck` and the `merge` subcommand): a recheck
run's results supersede prior entries for the same assertion ID rather than
being hand-merged with ad hoc `jq`/`python3`.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VERDICT_BLOCKED = "BLOCKED"


def aggregate(state: dict, contract_path: Path | None = None) -> str:
    assertions = state.get("assertions", [])
    if not assertions:
        return "## Verification Summary\n\nNo assertions in validation state.\n"
    rows: list[str] = []
    passed = failed = blocked = 0
    commands: list[str] = []
    state_ids = {a.get("id", "") for a in assertions}
    missing_ids: set[str] = set()
    if contract_path and contract_path.exists():
        contract_ids = set(re.findall(r"VAL-[A-Z]+-\d+", contract_path.read_text()))
        missing_ids = contract_ids - state_ids
    for a in assertions:
        aid = a.get("id", "?")
        status = a.get("status", "unknown")
        expected = a.get("expected", "")
        actual = a.get("actual", "")
        evidence = a.get("evidence", "")
        reason = a.get("block_reason", "")
        detail = reason if status == "blocked" else evidence
        if status == "passed":
            passed += 1
        elif status == "failed":
            failed += 1
        elif status == "blocked":
            blocked += 1
        rows.append(f"| {aid} | {status} | {expected} | {actual} | {detail} |")
        for cmd in a.get("commands_executed", []):
            commands.append(cmd)
    if missing_ids:
        failed += len(missing_ids)
        for mid in sorted(missing_ids):
            rows.append(f"| {mid} | failed | (from contract) | not evaluated by validator | |")
    overall = "FAIL" if failed else (VERDICT_BLOCKED if blocked else "PASS")
    total = len(assertions) + len(missing_ids)
    parts = [
        "## Verification Summary",
        "",
        f"{passed}/{total} passed",
        "",
    ]
    if missing_ids:
        parts.append(f"WARNING: {len(missing_ids)} assertions not evaluated: {', '.join(sorted(missing_ids))}")
        parts.append("")
    parts += [
        "| Assertion | Status | Expected | Actual | Detail |",
        "|-----------|--------|----------|--------|--------|",
        *rows,
        "",
        f"Overall: {overall}",
        "",
    ]
    if commands:
        parts += ["## Reproduction Commands", ""]
        for cmd in commands:
            parts.append(f"```bash\n{cmd}\n```")
        parts.append("")
    return "\n".join(parts)


def merge_recheck(base: dict, recheck: dict) -> dict:
    """Merge a targeted recheck's assertion results into a base validation state.

    Recheck entries supersede base entries sharing the same assertion `id`
    (in place, preserving base ordering); recheck ids absent from base are
    appended. Non-`assertions` top-level keys are preserved from `base`.
    Used by the verify-fix loop so a fresh live recheck's verdict for an
    assertion always wins over the earlier failing verdict it followed up
    on — that class of bug (timing, state, event-ordering) has repeatedly
    passed unit tests while still failing live, so the recheck result is
    the one that counts.
    """
    merged_assertions = list(base.get("assertions", []))
    index_by_id = {a.get("id"): i for i, a in enumerate(merged_assertions)}
    for a in recheck.get("assertions", []):
        aid = a.get("id")
        if aid in index_by_id:
            merged_assertions[index_by_id[aid]] = a
        else:
            index_by_id[aid] = len(merged_assertions)
            merged_assertions.append(a)
    return {**base, "assertions": merged_assertions}


def merge_main(argv: list[str]) -> int:
    if len(argv) < 3:
        sys.stderr.write(
            "Usage: aggregate_verify.py merge <output.json> <base.json> <recheck1.json> [<recheck2.json> ...]\n"
        )
        return 1
    out_path = Path(argv[0])
    base_path = Path(argv[1])
    recheck_paths = [Path(p) for p in argv[2:]]
    try:
        state = json.loads(base_path.read_text(encoding="utf-8"))
        for recheck_path in recheck_paths:
            recheck = json.loads(recheck_path.read_text(encoding="utf-8"))
            state = merge_recheck(state, recheck)
    except (OSError, json.JSONDecodeError) as e:
        sys.stderr.write(f"Error reading input: {e}\n")
        return 1
    out_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] == "merge":
        return merge_main(argv[1:])
    if not argv:
        sys.stderr.write("Usage: aggregate_verify.py <validation-state.json> [verification-contract.md]\n")
        return 1
    path = Path(argv[0])
    contract_path = Path(argv[1]) if len(argv) > 1 else None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.stderr.write(f"Error reading {path}: {e}\n")
        return 1
    sys.stdout.write(aggregate(state, contract_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
