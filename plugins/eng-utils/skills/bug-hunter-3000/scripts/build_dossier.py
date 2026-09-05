#!/usr/bin/env python3
"""Build a Behavior Dossier from a Finder Packet, withholding every conclusion.

WHY THIS EXISTS
---------------
There was a script to CHECK a dossier (`dossier_leak_scan.py`) and no script to BUILD
one. SKILL.md said "Build the dossier, then PROVE it withholds", and building it was an
inline prose step -- so every run reimplemented the withholding rules by hand, from the
closed five-item list in `references/behavior-dossier-and-verdict-schema.md` section 2,
under time pressure.

Measured 2026-08-29 on the character-pro run: **7 of 8 dossiers failed the gate**, 18
leaks, and the run stopped there without verifying a single candidate. The largest cause
was that the hand-rolled stripper never removed the appendix -- 11 of the 18 leaks were
the word "refuted" inside the Coverage record's sweep table, where the finder describes
hypotheses it considered and discarded. The finder contract puts that content below a
`--- APPENDIX ---` marker precisely so it can be separated mechanically, and nothing was
using the marker.

That is the same defect as `index_to_disk` before it: a step a run ACTS on, specified
only in prose, reimplemented differently and wrongly each time.

WHY THE DOSSIER MATTERS MORE THAN MOST ARTEFACTS
------------------------------------------------
The intent-verifier's whole value is that it is blind. It answers "what current contract
or product intent explains this behavior?" without knowing anyone thinks it is a bug. One
leaked word -- "refuted", "incorrectly", a severity label -- turns an independent second
axis into an expensive echo of the first, and nothing downstream can detect that it
happened. The gate exists because the failure is silent.

THE APPROACH: allowlist, then re-check with the gate's own patterns
-------------------------------------------------------------------
Two passes, deliberately.

1. **Build by ALLOWLIST, never by blocklist.** Only the five permitted items are emitted.
   The schema is explicit that there is "no 'everything neutral-looking, minus a
   blocklist' reading", and a blocklist is what fails on the field nobody anticipated.
2. **Then run the gate's own pattern set** over the result. Importing the patterns rather
   than restating them is the point: a builder validated against a different set than the
   one that gates it drifts, and the drift shows up as a blocked run three stages later.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dossier_leak_scan  # noqa: E402
from index_packets import APPENDIX_MARKER, _sections  # noqa: E402

#: The closed five-item list, section 2 of
#: references/behavior-dossier-and-verdict-schema.md. Each entry maps a permitted dossier
#: item to the Finder Packet field names that may satisfy it. Anything not named here does
#: not travel -- including fields tagged NEUTRAL, because eligible is not the same as
#: included.
PERMITTED: dict[str, tuple[str, ...]] = {
    "Component and code locations": ("Component", "Code locations"),
    "Observed inputs, outputs, and conditions": ("Observed behavior", "Conditions"),
    "Reproduction artifacts and test names": ("Relevant tests and config",),
    "Known callers, siblings, configuration, and integration boundaries": (
        "Boundary and call-graph info",
    ),
}

#: Asked verbatim so the verifier is answering the question the design poses, not a
#: paraphrase of it that has drifted.
QUESTION = "What current contract or product intent explains this behavior?"

#: Withheld outright. Listed for the reader, NOT used to strip: stripping is done by the
#: allowlist above. If this list were the mechanism, a field absent from it would travel
#: by default, which is exactly the reading the schema forbids.
WITHHELD_FOR_REFERENCE = (
    "Candidate mechanism hypothesis",
    "Proposed safe reproduction plan",
    "Defect description",
    "Impact and exposure evidence",
    "Scope",
    "Root-cause fingerprint",
    "Defect site",
    "Coverage record",
    "Evidence links",
)


#: A field starts at a line naming it, as a bullet (`- **Component** (NEUTRAL): ...`) or a
#: heading (`### Component (NEUTRAL)`). Both shapes appear on real packets.
_FIELD_START = re.compile(
    r"^\s*(?:[-*]\s+)?(?:#{1,4}\s*)?(?:\*\*)?"
    r"(?P<name>[A-Z][A-Za-z][A-Za-z ,/'-]{2,60}?)"
    # The colon is optional WHEN a (NEUTRAL)/(INTERPRETIVE) tag is present. Measured on
    # a real packet: "**Defect description** (INTERPRETIVE)" was written with no colon,
    # so it was not recognised as a field start and its body was absorbed into the
    # PRECEDING permitted field -- carrying a withheld field into the dossier. Requiring
    # a tag when there is no colon keeps ordinary prose from matching.
    r"(?:\*\*)?\s*(?:\((?P<tag>NEUTRAL|INTERPRETIVE)\)\s*:?|:)\s*(?P<rest>.*)$",
    re.M,
)


def _fields(section: str) -> dict[str, str]:
    """Split a packet section into {field name: body}.

    Explicit splitting rather than a per-field lookahead. The lookahead version ran past
    the end of its own field and swallowed the following one, so a PERMITTED field
    silently carried WITHHELD content into the dossier -- measured against real packets,
    where "Defect description (INTERPRETIVE)" arrived inside an allowed field.
    """
    starts = [(m.start(), m.group("name").strip(), m.end(), m.group("rest"))
              for m in _FIELD_START.finditer(section)]
    out: dict[str, str] = {}
    for i, (pos, name, end, rest) in enumerate(starts):
        stop = starts[i + 1][0] if i + 1 < len(starts) else len(section)
        body = (rest + "\n" + section[end:stop]).strip()
        out.setdefault(name, body)
    return out


def _field(section: str, name: str) -> str:
    """One permitted field's body, or empty."""
    fields = _fields(section)
    if name in fields:
        return fields[name]
    low = name.lower()
    for k, v in fields.items():
        if k.lower() == low:
            return v
    return ""


def build(packet_text: str, fingerprint: str | None = None) -> str:
    """Return the dossier for one candidate. Appendix never travels."""
    body = packet_text.split(APPENDIX_MARKER)[0]

    section = body
    if fingerprint:
        for s in _sections(body):
            if fingerprint in s:
                section = s
                break

    out = ["# Behavior Dossier", ""]
    out.append(
        "Investigate whether the behavior described below is intended. Nothing here "
        "states or implies a judgement about it, and no judgement has been reached."
    )
    out.append("")
    for item, fields in PERMITTED.items():
        parts = [t for t in (_field(section, f) for f in fields) if t]
        if not parts:
            continue
        out.append(f"## {item}")
        out.append("")
        out.extend(["\n".join(parts), ""])
    out.append("## The question to answer")
    out.append("")
    out.append(QUESTION)
    out.append("")
    return "\n".join(out)


def scan(text: str) -> list:
    """Run the GATE's own patterns. Imported, never restated."""
    for name in ("scan_text", "scan", "find_leaks", "_scan"):
        fn = getattr(dossier_leak_scan, name, None)
        if callable(fn):
            try:
                return list(fn(text) or [])
            except TypeError:
                continue
    # Fall back to the module's pattern table directly, so a rename upstream degrades
    # into "checked with the real patterns" rather than "silently checked nothing".
    hits = []
    for entry in getattr(dossier_leak_scan, "_PATTERNS", ()):
        pattern, label = (
            (entry[0], entry[1]) if isinstance(entry, tuple) else (entry, "LEAK")
        )
        for m in pattern.finditer(text):
            hits.append({"label": label, "match": m.group(0)})
    return hits


def build_checked(packet_text: str, fingerprint: str | None = None) -> tuple[str, list]:
    """Build, then check with the gate's patterns. Both, always."""
    dossier = build(packet_text, fingerprint)
    return dossier, scan(dossier)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--packet", required=True, help="Path to the finder packet file.")
    ap.add_argument("--fingerprint", default=None, help="Which candidate to build for.")
    ap.add_argument("--out", default=None, help="Write here instead of stdout.")
    args = ap.parse_args()

    dossier, leaks = build_checked(Path(args.packet).read_text(), args.fingerprint)
    if leaks:
        print(
            f"LEAKED: {len(leaks)} conclusion(s) survived the build. NOT written.\n"
            + "\n".join(f"  {l}" for l in leaks[:20]),
            file=sys.stderr,
        )
        return 1
    if args.out:
        Path(args.out).write_text(dossier)
        print(json.dumps({"written": args.out, "bytes": len(dossier.encode())}))
    else:
        print(dossier)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
