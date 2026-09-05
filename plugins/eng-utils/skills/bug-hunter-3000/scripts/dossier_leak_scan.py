#!/usr/bin/env python3
"""
Blindness scanner for Behavior Dossiers produced by the bug-hunter-3000
skill.

The dossier handed to the intent-verifier deliberately withholds the finder's
conclusion (see references/behavior-dossier-and-verdict-schema.md section 2).
Withholding is easy to get wrong in ways that are invisible on a read-through:
a heading can leak a verdict as effectively as a sentence, and on one measured
run the field name `Defect site:` did exactly that -- five of seven
intent-verifiers noticed and reported it themselves.

Relying on the verifiers to notice is the wrong control. A run where nobody
flags a leak is ambiguous between "no leak" and "nobody looked". This makes the
check mechanical and deterministic.

Usage:
    python3 dossier_leak_scan.py dossiers/          # a directory of dossiers
    python3 dossier_leak_scan.py one-dossier.md     # a single file

Exit codes -- three outcomes, deliberately distinct:
    0  CLEAN     scanned real dossiers, found no withheld content
    1  LEAKED    at least one dossier carries withheld content; do not dispatch
    2  NO_INPUT  nothing to scan. NOT a pass -- the check did not run.
"""

import json
import re
import sys
from pathlib import Path

# `#` belongs in the leading-decoration class alongside `-*>|`. Without it every
# label pattern below missed the markdown heading form -- `## Defect site:`,
# `## Scope` and `## Confidence` all scanned CLEAN while their bulleted and bolded
# equivalents were caught. Dossiers are markdown, and the orchestrator on the
# measured run wrote every dossier section as a `##` heading, so the form the
# scanner could not see was the likeliest one in practice.
#
# Each entry: (compiled pattern, what it indicates). Patterns are deliberately
# about the FORM of a leak rather than any one wording, because the measured
# leak was a field label and the obvious guesses are all sentences.
_LEAKS: tuple[tuple[re.Pattern[str], str], ...] = (
    # The measured case: a labelled defect-site field. The label is the leak.
    (re.compile(r"(?im)^\s*[-*>|#\s]*\**\s*defect\s*site\b"), "DEFECT_SITE_LABEL"),
    # Any field label asserting the finder reached a conclusion -- that is, every
    # INTERPRETIVE field in agents/bug-hunt-finder.md. `defect description`,
    # `scope` and `impact and exposure` join the list now that the packet's
    # NEUTRAL/INTERPRETIVE classification is total: before that they were untagged,
    # absent from the dossier's withheld list, and matched by no pattern here, so a
    # dossier carrying them scanned CLEAN. `scope` is the sharpest of the three --
    # every one of its values is phrased as what a fix would cost, so stating any
    # scope asserts a defect exists.
    (
        re.compile(
            r"(?im)^\s*[-*>|#\s]*\**\s*"
            r"(?:candidate\s+mechanism|mechanism\s+hypothesis|hypothesis"
            r"|proposed\s+(?:fix|severity|remediation)|confidence"
            r"|root[- ]cause\s+fingerprint|fingerprint|severity"
            r"|defect\s*description|scope|impact\s+and\s+exposure"
            r"|proposed\s+safe\s+reproduction|reproduction\s+plan)\b"
        ),
        "INTERPRETIVE_FIELD_LABEL",
    ),
    # A verdict word applied to the behaviour under assessment.
    (
        re.compile(
            r"(?i)\b(?:this\s+is\s+a\s+bug|is\s+a\s+defect|the\s+defect\s+is"
            r"|the\s+bug\s+is|incorrectly|erroneously|should\s+(?:instead|have)"
            r"|violates\s+the\s+contract|clearly\s+wrong)\b"
        ),
        "VERDICT_LANGUAGE",
    ),
    # A mechanism verdict from the other axis.
    (
        re.compile(r"(?i)\b(?:CONFIRMED|REFUTED|INCONCLUSIVE)\b"),
        "MECHANISM_VERDICT",
    ),
    # A disposition, which only the reconciler may assign.
    (
        re.compile(
            r"(?i)\b(?:READY_LOCAL_CANDIDATE|READY_CROSS_SYSTEM_DOSSIER"
            r"|PRODUCT_EXPERIENCE_DOSSIER|HOLD_[A-Z_]+|DISCARDED_[A-Z_]+"
            r"|DEFERRED_UNVERIFIED)\b"
        ),
        "DISPOSITION",
    ),
    # A band, which is orchestrator judgement the verifier must not inherit.
    (re.compile(r"(?i)\b(?:Act-Now|Important|Low)\s*(?:band|severity)\b"), "BAND"),
    # An ORPHANED VALUE: a withheld field's value left behind when only its label
    # was deleted. `Confidence: high` becomes a bare `high` on its own line, which
    # every label-keyed pattern above misses -- and so did the strip's own
    # verification, which grepped for labels and returned zero on a run whose
    # dossiers still carried the values. Anchored to a whole line so ordinary prose
    # ("high traffic", "low latency") does not match.
    (
        re.compile(r"(?im)^\s*[-*>|#\s]*\**\s*(?:high|medium|low|S|M|L)\**\s*$"),
        "ORPHANED_VALUE",
    ),
)


def scan_text(text: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for number, line in enumerate(text.splitlines(), 1):
        for pattern, kind in _LEAKS:
            match = pattern.search(line)
            if match:
                findings.append(
                    {
                        "kind": kind,
                        "line_number": number,
                        "excerpt": line.strip()[:120],
                        "matched": match.group().strip()[:60],
                    }
                )
    return findings


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        json.dump({"status": "NO_INPUT", "scanned": 0, "findings": []}, sys.stdout)
        sys.exit(2)

    target = Path(args[0])
    files = (
        sorted(p for p in target.rglob("*.md") if p.is_file())
        if target.is_dir()
        else [target]
    )
    files = [p for p in files if p.read_text(errors="replace").strip()]

    if not files:
        # An empty directory is not a clean sweep. It means the check did not run,
        # which must never be recorded as evidence that withholding held.
        json.dump({"status": "NO_INPUT", "scanned": 0, "findings": []}, sys.stdout)
        sys.exit(2)

    out: list[dict[str, object]] = []
    for path in files:
        for finding in scan_text(path.read_text(errors="replace")):
            out.append({"file": path.name, **finding})

    status = "LEAKED" if out else "CLEAN"
    json.dump(
        {"status": status, "scanned": len(files), "findings": out},
        sys.stdout,
        indent=2,
    )
    sys.exit(1 if out else 0)


if __name__ == "__main__":
    main()
