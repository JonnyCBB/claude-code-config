#!/usr/bin/env python3
"""
Write one bug-hunt artifact: redact it, put it on disk, then prove what landed
on disk is the artifact.

Why this owns the write instead of leaving it to the caller
-----------------------------------------------------------
The caller used to do this in three steps -- mask to stdout, redirect into the
destination, then re-scan the destination. Every step was a place to go wrong,
and on a measured run all three failed at once:

    cat << 'EOF' | python3 redact_scan.py --mask > portfolio/x.md

Mid-run, the plugin tree was replaced with an older revision whose
`redact_scan.py` had no `--mask` mode. An unknown flag is silently ignored, so
the script fell back to report mode, whose stdout is status JSON -- and the
redirect wrote that JSON over the artifact. Ten artifacts became 35 identical
bytes:

    {"status": "CLEAN", "findings": []}

The re-scan step then read that blob, found no secrets in it, and reported
CLEAN for all ten. The run summary recorded "written through --mask and
re-verified on disk (all CLEAN)", which was false in every clause.

Two properties follow from putting the write in here:

1. There is no redirect to misroute. The destination is an argument, not a
   shell redirection, so stdout carries nothing a typo can turn into content.
2. This file is itself a version tripwire. An older tree does not contain it,
   so the write fails with "No such file or directory" instead of succeeding
   against a script that quietly does something else.

And the verification asks the question that actually matters. "Does this file
contain secrets?" is not the same question as "is this file the artifact I
wrote?" -- a status blob passes the first and fails the second. The sentinel
check is what distinguishes them, which is why `--sentinel` is required rather
than optional: an optional integrity check is one that gets omitted on the run
where it would have mattered.

Usage:
    python3 write_artifact.py --sentinel <FINGERPRINT> <DEST> < draft.md

Findings and verification detail are reported as JSON on stderr. Nothing is
written to stdout, so a stray `> file` cannot capture anything meaningful.

Exit codes -- three outcomes, deliberately distinct:
    0  OK             written, and the bytes on disk verified as this artifact.
                      Check the JSON's `redacted` field: true means a secret
                      shape was masked and the run summary owes a gate hit.
    1  VERIFY_FAILED  something landed, but it is not this artifact -- wrong
                      content, truncated, or rewritten after the write. Do not
                      record this candidate as written.
    2  NO_INPUT / usage error. The gate did not run. Never a pass.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from redact_scan import _finding_to_dict, mask, scan  # noqa: E402

# A formatter hook may legitimately rewrite markup after the write (measured:
# `*emphasis*` to `_emphasis_`), so byte-identical comparison would fail on a
# healthy run. Size is therefore a coarse "was this replaced by a stub" check
# and the sentinel carries the real weight. Half is far below anything reflowing
# produces and far above the 0.2% that the status-blob substitution produced.
_MIN_SIZE_RATIO = 0.5

# A constant, not a flag -- this is a narrow fix, not a retry framework. One
# retry covers the failure this was measured against (a downstream process
# replacing the file between the write and the read-back) and nothing else. A
# deterministic failure fails twice and is reported, which is the honest reading:
# retrying further would turn a genuine write failure into a hang, and retrying
# with regenerated content would be the redraft-and-rescan loop
# design-history section 13 prohibits, because a reworded redraft can launder a
# real identifier through the gate.
_MAX_ATTEMPTS = 2


def _write_and_read_back(dest: Path, content: str) -> str:
    """Write, then re-read rather than trusting the write.

    Anything downstream of this process -- a formatter, an editor hook, a sync
    agent -- can alter the file after the write returns and before anyone looks
    at it.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest.read_text(encoding="utf-8", errors="replace")


def _verify(landed: str, written: str, sentinel: str) -> list[str]:
    """Every reason the bytes on disk are not this artifact. Empty means good."""
    problems: list[str] = []
    if not landed.strip():
        problems.append("file on disk is empty")
    if sentinel not in landed:
        problems.append(
            f"sentinel {sentinel!r} is absent from the file on disk, so what "
            "landed is not this artifact"
        )
    if len(landed) < len(written) * _MIN_SIZE_RATIO:
        problems.append(
            f"file on disk is {len(landed)} bytes against {len(written)} "
            "written, which is too small to be a reformatting"
        )
    residual = scan(landed).findings
    if residual:
        problems.append(f"{len(residual)} secret shape(s) present on disk after masking")
    return problems


def _fail(status: str, detail: str, code: int) -> None:
    json.dump({"status": status, "detail": detail}, sys.stderr)
    sys.exit(code)


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv

    sentinel: str | None = None
    if "--sentinel" in args:
        index = args.index("--sentinel")
        if index + 1 >= len(args):
            _fail("USAGE", "--sentinel needs a value", 2)
        sentinel = args[index + 1]
        args = args[:index] + args[index + 2 :]

    # Unknown flags are rejected rather than ignored. Silently dropping one is
    # exactly how `--mask` became a no-op on the run described above.
    unknown = [a for a in args if a.startswith("-")]
    if unknown:
        _fail("USAGE", f"unknown argument(s): {' '.join(unknown)}", 2)
    if len(args) != 1:
        _fail("USAGE", "usage: write_artifact.py --sentinel TEXT DEST < draft", 2)
    if sentinel is None:
        _fail(
            "USAGE",
            "--sentinel is required: without it this cannot tell the artifact "
            "from any other clean text that happens to be on disk",
            2,
        )
    # An empty sentinel is a substring of every possible document, so it would
    # satisfy both the pre-write check and the post-write verification while
    # proving nothing at all. Rejected explicitly rather than left to the
    # `in` operator, because `--sentinel "$RUN_ID"` with RUN_ID unset expands to
    # exactly this and looks like a correct invocation in a shell transcript.
    if not sentinel.strip():
        _fail(
            "USAGE",
            "--sentinel is empty, which would match any file and verify nothing. "
            "This usually means the variable holding the run id was unset.",
            2,
        )

    dest = Path(args[0])
    source = sys.stdin.read()

    if not source.strip():
        _fail("NO_INPUT", "nothing on stdin; the artifact is unwritten", 2)
    if sentinel not in source:
        _fail(
            "USAGE",
            f"sentinel {sentinel!r} does not appear in the drafted artifact, so "
            "it cannot verify the write",
            2,
        )

    # The ONLY call to mask(), ever, and deliberately outside the loop below.
    # Masking inside the retry would mean the second attempt writes freshly
    # generated bytes, which is a redraft -- and a redraft is exactly what can
    # launder a real identifier through in reworded form. Retrying the same
    # bytes cannot.
    redacted, findings = mask(source)

    attempts = 0
    problems: list[str] = []
    landed = ""
    while attempts < _MAX_ATTEMPTS:
        attempts += 1
        landed = _write_and_read_back(dest, redacted)
        problems = _verify(landed, redacted, sentinel)
        if not problems:
            break

    report = {
        "status": "VERIFY_FAILED" if problems else "OK",
        "dest": str(dest),
        "redacted": bool(findings),
        "findings": [_finding_to_dict(f) for f in findings],
        "bytes_written": len(redacted),
        "bytes_on_disk": len(landed),
        "attempts": attempts,
        "problems": problems,
    }
    json.dump(report, sys.stderr, indent=2)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
