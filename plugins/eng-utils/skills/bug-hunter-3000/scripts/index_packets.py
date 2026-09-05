#!/usr/bin/env python3
"""Write a Finder Packet to disk and return only a small index of it.

WHY THIS EXISTS
---------------
`index_to_disk` was named exactly once, in SKILL.md's dispatch pseudocode, and
defined nowhere -- no script, no contract, no statement of what it returned. The
line calling it also ACCUMULATED its result into a variable named `packets`, which
is the opposite of what `references/mandate-partitioning.md` prescribes: "Index each
batch to disk as it lands, and do not carry packets forward."

Measured consequence, 2026-08-28: 32 finders returned ~2.2MB of packets through one
orchestrator's context. The orchestrator exhausted its working memory, the impact
resolver received 14 of 116 candidates, and the run reached the verification stage
with too little room to use it. A second consequence surfaced later: the per-packet
byte sizes needed to calibrate `project_cost.py` were never written anywhere, so that
calibration cannot be re-derived from any run performed without this script.

THE KEY FACT THAT MAKES THE STRONG FIX POSSIBLE
-----------------------------------------------
The finder holds no `Write` tool, and the packet contract used to explain the context
cost as an unavoidable consequence of that. It is not: **the finder holds `Bash`,
which can write anywhere `Write` can.** So the packet is written by the FINDER, and
never enters the orchestrator's context at all.

That is strictly better than indexing on arrival, which still pays the context cost
once per packet. Nothing about the zero-outbound guarantee changes -- this writes to a
local run directory, and the guarantee rests on the absence of outbound MCP tools, not
on the absence of a filesystem.

WHAT COMES BACK
---------------
Only what the orchestrator needs before it decides anything: per candidate, the
fingerprint, the full-path defect site, a one-line title, scope, confidence, severity,
effort, and whether a metric was cited. Grouping compares defect sites mechanically,
so those must be repository-root paths; everything interpretive stays on disk and is
re-read surgically by `read_packet` when a dossier or portfolio entry is built.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

APPENDIX_MARKER = "--- APPENDIX ---"

#: A packet section starts at a Finder Packet heading. Candidates are emitted once
#: per forwarded candidate, so the heading is the section boundary.
_SECTION_RE = re.compile(r"^#{1,4}\s*Finder Packet\b.*$", re.M)

#: `Defect site: <path>:<line>` on its own line, path from the repository root. The
#: contract says "nothing else on it", which is what makes this parseable at all.
_DEFECT_SITE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*)?Defect site(?:\*\*)?\s*(?:\([A-Z]+\))?\s*:\s*(\S+)",
    re.M,
)

_FINGERPRINT_RE = re.compile(r"Root-cause fingerprint.*?([0-9a-f]{16})", re.S | re.I)

_SCOPE_RE = re.compile(r"Scope(?:\*\*)?\s*(?:\([A-Z_]+\))?\s*:\s*`?([A-Z_]+)`?")
_CONFIDENCE_RE = re.compile(r"confidence\s+([a-z][a-z -]*?)(?:[.,]|$)", re.I | re.M)
_SEVERITY_RE = re.compile(r"severity[:\s]+([a-z][a-z-]*)", re.I)
_EFFORT_RE = re.compile(r"Effort[:\s]+([SML])\b")
_TITLE_RE = re.compile(
    r"Defect description(?:\*\*)?\s*(?:\([A-Z]+\))?\s*:\s*(.+?)(?:\n\s*\n|\n\s*[-*]\s*\*\*)",
    re.S,
)

#: Exposure evidence that is literally UNKNOWN is not a citation. Recording it as one
#: is how the resolver came to believe the hard part was already done for candidates
#: that had named nothing.
_EXPOSURE_RE = re.compile(
    r"Impact and exposure evidence[^:]*:\s*(.+?)(?:\n\s*[-*]\s*\*\*|\Z)", re.S
)


def _body(packet_text: str) -> str:
    """Everything above the appendix marker. The appendix is search accounting."""
    idx = packet_text.find(APPENDIX_MARKER)
    return packet_text if idx < 0 else packet_text[:idx]


def _first(pattern: re.Pattern[str], text: str, default: str = "") -> str:
    m = pattern.search(text)
    return m.group(1).strip() if m else default


def _one_line(text: str, limit: int = 160) -> str:
    collapsed = " ".join(text.split())
    return collapsed[:limit].rstrip()


def _sections(packet_text: str) -> list[str]:
    body = _body(packet_text)
    starts = [m.start() for m in _SECTION_RE.finditer(body)]
    if not starts:
        return []
    bounds = starts + [len(body)]
    return [body[bounds[i] : bounds[i + 1]] for i in range(len(starts))]


def _has_metric_citation(section: str) -> bool:
    m = _EXPOSURE_RE.search(section)
    if not m:
        return False
    value = " ".join(m.group(1).split())
    if not value:
        return False
    # `UNKNOWN` is the contract's explicit way of saying "I could not find it".
    return "UNKNOWN" not in value.upper()


def parse_index(packet_text: str) -> list[dict]:
    """Candidate index entries, in packet order."""
    out = []
    for section in _sections(packet_text):
        fingerprint = _first(_FINGERPRINT_RE, section)
        if not fingerprint:
            # A candidate with no fingerprint cannot be attributed downstream --
            # `exposure_resolution.unresolved` is keyed by it, and grouping merges on
            # it. Record it rather than dropping it silently.
            fingerprint = ""
        out.append(
            {
                "fingerprint": fingerprint,
                "defect_site": _first(_DEFECT_SITE_RE, section),
                "title": _one_line(_first(_TITLE_RE, section)),
                "scope": _first(_SCOPE_RE, section),
                "confidence": _one_line(_first(_CONFIDENCE_RE, section), 40),
                "severity": _first(_SEVERITY_RE, section),
                "effort": _first(_EFFORT_RE, section),
                "has_metric_citation": _has_metric_citation(section),
            }
        )
    return out


def _coverage_files(packet_text: str) -> list[str]:
    idx = packet_text.find(APPENDIX_MARKER)
    if idx < 0:
        return []
    appendix = packet_text[idx:]
    m = re.search(r"Files read:\s*(.+)", appendix)
    if not m:
        return []
    # Extract PATHS, never comma-split.
    #
    # A real coverage record annotates each path -- "A.java (mandate file, read in
    # full), B.java (context: coverage, found none)" -- so splitting on commas yields
    # entries like "read in full)" and "found none)". Measured on an eval run: junk
    # entries pushed the index to 14.8% of the packet against a 3.7% target, eroding
    # the saving this script exists for. Worse, coverage_files is what separates
    # "searched and found nothing" from "never looked", so fragments corrupt the one
    # record that makes a negative result trustworthy.
    # Requires an extension, which is what separates a filename from a fragment
    # of prose: "A.java" and "svc/main/A.java" match, "read in full)" and
    # "found none)" do not. Bare filenames are accepted because coverage records
    # legitimately use them -- only `Defect site:` is required to be a full path.
    return re.findall(r"[A-Za-z0-9._/\-]*[A-Za-z0-9_\-]\.[A-Za-z][A-Za-z0-9]*", m.group(1))


def _packets_dir(run_dir: Path) -> Path:
    d = Path(run_dir) / "packets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_and_index(
    run_dir: Path | str,
    mandate: str,
    packet_text: str,
    agent_id: str | None = None,
) -> dict:
    """Persist the packet verbatim; return the small index.

    Verbatim matters: this becomes the only surviving copy once the finder's context
    is gone, and both the dossier and the portfolio are rebuilt from it.
    """
    run_dir = Path(run_dir)
    d = _packets_dir(run_dir)
    (d / f"finder-{mandate}.md").write_text(packet_text)

    candidates = parse_index(packet_text)

    # A packet the parser cannot split returns zero candidates, which reads exactly
    # like a mandate that found nothing. Measured 2026-08-29: four finders spent 24-33
    # minutes and up to 290k tokens each reverse-engineering this parser against that
    # silent zero. Say what happened and what shape is wanted, so nobody has to guess.
    body_fingerprints = set(re.findall(r"\b[0-9a-f]{16}\b", _body(packet_text)))
    found = {c["fingerprint"] for c in candidates if c["fingerprint"]}
    orphans = body_fingerprints - found
    parse_warning = None
    if orphans:
        parse_warning = (
            f"{len(orphans)} fingerprint(s) appear in the packet but sit in no "
            f"parseable candidate section: {sorted(orphans)}. Each candidate must "
            f"start with a heading line beginning '## Finder Packet' (any level 1-4, "
            f"any trailing text -- '# Finder Packet -- mandate m04 -- candidate 2 of 3' "
            f"is fine). Everything from one such heading to the next is one candidate. "
            f"The packet HAS been written to disk unchanged; only the index is affected."
        )

    index = {
        "mandate": mandate,
        "agent_id": agent_id,
        "candidate_count": len(candidates),  # from the list, never a counter
        "candidates": candidates,
        "coverage_files": _coverage_files(packet_text),
        # Recorded so project_cost.py can eventually be calibrated against real data.
        # No run has ever persisted this, which is why its coefficients are ESTIMATED
        # from a single run and cannot be re-derived.
        "packet_bytes": len(packet_text.encode()),
        "parse_warning": parse_warning,
    }
    (d / f"mandate-{mandate}-index.json").write_text(json.dumps(index, indent=1))
    return index


def read_packet(run_dir: Path | str, fingerprint: str) -> str:
    """Return ONLY the section for one candidate.

    Surgical on purpose. Returning the whole file would put the appendix back into
    the orchestrator's context and undo the indexing.
    """
    d = _packets_dir(Path(run_dir))
    for path in sorted(d.glob("finder-*.md")):
        text = path.read_text()
        for section in _sections(text):
            if fingerprint and fingerprint in section:
                return section
    raise KeyError(
        f"no packet section carries fingerprint {fingerprint!r} under {d}. "
        f"Either the finder never wrote its packet, or the fingerprint is wrong; "
        f"both are run failures rather than things to work around."
    )


def collect(run_dir: Path | str) -> dict:
    """Merge every mandate index. A zero-candidate mandate still appears."""
    d = _packets_dir(Path(run_dir))
    by_mandate = []
    for path in sorted(d.glob("mandate-*-index.json")):
        by_mandate.append(json.loads(path.read_text()))
    merged = {
        "mandates": len(by_mandate),
        "candidate_count": sum(m["candidate_count"] for m in by_mandate),
        "packet_bytes_total": sum(m.get("packet_bytes", 0) for m in by_mandate),
        "by_mandate": by_mandate,
    }
    (d / "all-packets-index.json").write_text(json.dumps(merged, indent=1))
    return merged


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-dir", required=True)
    ap.add_argument(
        "--mandate", help="Mandate id, e.g. m01. Reads the packet on stdin."
    )
    ap.add_argument("--agent-id", default=None)
    ap.add_argument(
        "--read", metavar="FINGERPRINT", help="Print one candidate section."
    )
    ap.add_argument("--collect", action="store_true", help="Merge every mandate index.")
    args = ap.parse_args()

    if args.read:
        print(read_packet(args.run_dir, args.read))
        return 0
    if args.collect:
        print(json.dumps(collect(args.run_dir), indent=1))
        return 0
    if not args.mandate:
        ap.error("--mandate is required when writing a packet")
    packet_text = sys.stdin.read()
    if not packet_text.strip():
        ap.error("no packet on stdin; refusing to write an empty packet file")
    print(
        json.dumps(
            write_and_index(args.run_dir, args.mandate, packet_text, args.agent_id),
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
