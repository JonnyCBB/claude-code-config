#!/usr/bin/env python3
"""Project packet volume before dispatching finders.

WHY THIS IS A SCRIPT AND NOT A LINE OF PROSE
--------------------------------------------
It used to be two lines of pseudocode in `references/mandate-partitioning.md`:

    finders   = len(mandates) + len(LENSES)
    packet_mb = finders * 0.055

That formula decides whether a run is dispatched as-is, bounded, or split, so it is
code. Left in prose it could not be tested and it drifted from the measurement it
claimed. The same thing happened one section later to `index_to_disk`, which is named
once in the dispatch pseudocode and defined nowhere -- a run following the prose
silently accumulated packets in context instead. A formula that a run acts on belongs
in a file that can be executed and asserted against.

WHAT WAS WRONG WITH THE OLD ONE
-------------------------------
It had one term, keyed on finder count. Roughly 90% of returned packet volume scales
with CANDIDATES FOUND, not with the number of finders looking. Two components with
identical file counts and identical partitions return very different volumes if one
is buggier than the other, and the old formula projected them identically. It was
calibrated on a single run and reported 55KB per finder where that same run measured
68.7KB -- so it understated by about a quarter on the very run it came from.

THE MODEL
---------
    kb = finders * FIXED_KB_PER_FINDER
       + finders * candidates_per_finder * KB_PER_CANDIDATE

The fixed term is the coverage record and sweep table a finder returns whatever it
finds. The candidate term is the per-candidate evidence, which is where the volume
actually lives.

ON THE COEFFICIENTS -- READ THIS BEFORE TRUSTING A NUMBER
---------------------------------------------------------
They come from ONE run and they cannot currently be re-derived. See CALIBRATION
below. The projection is therefore reported as a RANGE, and callers should treat the
expected value as the middle of a wide band rather than a figure to plan against.

The right way to improve this is not to re-analyse the 2026-08-28 run -- that has
been attempted and the data does not exist. It is to land the disk index
(jbrooksbartlett-n26cg) so that a future run persists per-packet sizes at all.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

#: Bytes a finder returns regardless of how many candidates it finds: the coverage
#: record, the sweep table, the mandate restatement.
FIXED_KB_PER_FINDER = 4.9

#: Bytes per candidate: the mechanism hypothesis, the evidence excerpts, the
#: falsification note. This is the term the old formula omitted entirely.
KB_PER_CANDIDATE = 17.6

#: Largest single packet actually observed. The projection's high end must reach it;
#: a bound that sits below something that has already happened is not a bound.
OBSERVED_MAX_KB_PER_FINDER = 76.0

#: Candidate density prior, used when the caller cannot supply one.
#:
#: `expected` is MEASURED: 116 candidates / 32 finders on the source run.
#: `low` and `high` are CHOSEN, not measured. One run yields one density, so there is
#: no observed spread to derive them from. They are set wide enough that the band is
#: visibly a band, and skewed high because the asymmetry matters: an under-projection
#: produces a run that quietly exceeds its budget and degrades silently, whereas an
#: over-projection merely prompts a conversation. Narrow them against a second run's
#: measured density, never against intuition.
DENSITY_PRIOR = {"low": 1.5, "expected": 3.6, "high": 8.0}

#: Multipliers applied when the caller DOES supply a density. Also CHOSEN, for the
#: same reason: a supplied density is one observation and carries its own error,
#: which nothing here has measured.
SUPPLIED_DENSITY_LOW_MULT = 0.65
SUPPLIED_DENSITY_HIGH_MULT = 1.55

#: Minimum low-to-high span for any projection. Shared with the tests so the two
#: cannot drift. Exists because a band can be technically present and practically
#: meaningless: a mutation sweep on 2026-08-28 found the range tests passed with the
#: band collapsed to 0.99x-1.01x of the point estimate, asserting ordering and
#: nothing else. CHOSEN, not derived.
MIN_BAND_RATIO = 2.0

#: Share of a packet that survives into the returned index once the finder writes its
#: packet to disk (`scripts/index_packets.py`).
#:
#: MEASURED on a REAL packet, not a fixture: 1,532 bytes of index against a 15,333-byte
#: packet produced by a finder actually following the instruction, on 2026-08-29. An
#: earlier value of 0.037 came from a synthetic fixture whose appendix was padded to
#: 400 filler lines, which flattered the ratio -- a fixture is not a measurement.
#:
#: This is what makes the projection honest after jbrooksbartlett-n26cg. Packet volume
#: was only ever a PROXY for the orchestrator's context; once packets land on a
#: filesystem instead, the proxy measures the wrong thing and the warning fires on runs
#: that will be fine. One sample, so treat it as indicative -- but 10% against 100% is
#: not a difference that hinges on precision.
INDEX_SHARE_OF_PACKET = 0.10

#: Volume beyond which a run has historically reached verification degraded.
#: DERIVED, not directly measured: the recorded boundary is in finders (~22
#: survivable in one session, ~42 not), converted here at the measured mean of
#: 68.7KB per finder -- 22 * 68.7 = 1511KB, rounded to 1500. The conversion is what
#: lets the warning key on volume rather than finder count, which is the point; but
#: it inherits every uncertainty in the coefficients above.
DEGRADE_THRESHOLD_KB = 1500.0

CALIBRATION = {
    "basis": "ESTIMATED",
    "source_run": "2026-08-28 character-pro / promotions-serving "
    "(32 file-slice finders, 116 candidates)",
    "sample_size_runs": 1,
    "re_derivable": False,
    "why_not_re_derivable": (
        "The finder holds no Write tool, so every packet returned through the "
        "orchestrator's context and was never written to disk. That context is gone. "
        "Four sources were checked on 2026-08-28: the orchestrator transcript holds "
        "notification stubs (max 1103 bytes, ~100x too small and plausible-looking); "
        "the 44 subagent transcripts yield 2 real packet returns, both with a single "
        "fingerprint; tool-results/ holds 5 files, none of them packets; the rescued "
        "artifacts hold extracts rather than packets. Re-calibration requires a run "
        "performed WITH the disk index (jbrooksbartlett-n26cg), not more analysis of "
        "this one."
    ),
}


@dataclass(frozen=True)
class Projection:
    finders: int
    candidates_per_finder: float
    low_kb: float
    expected_kb: float
    high_kb: float
    #: What the ORCHESTRATOR actually carries. Equals expected_kb when packets come
    #: back inline; a small fraction of it when the finder writes them to disk.
    context_kb: float
    will_degrade: bool
    warning: str

    @property
    def expected_mb(self) -> float:
        return self.expected_kb / 1024.0


def _kb(finders: int, density: float) -> float:
    return finders * (FIXED_KB_PER_FINDER + density * KB_PER_CANDIDATE)


def candidate_driven_share(candidates_per_finder: float) -> float:
    """Fraction of projected volume attributable to candidates rather than finders.

    Exposed because it is the claim the whole correction rests on. If this drops
    well below ~0.9 at the observed density, the coefficients no longer reflect the
    measurement they came from.
    """
    per_finder = FIXED_KB_PER_FINDER + candidates_per_finder * KB_PER_CANDIDATE
    return (candidates_per_finder * KB_PER_CANDIDATE) / per_finder


def project(
    finders: int,
    candidates_per_finder: float | None = None,
    index_to_disk: bool = True,
) -> Projection:
    """Project packet volume for a run of `finders` finders.

    `candidates_per_finder` is the density prior. Supply it when a comparable run on
    the same component exists; otherwise the prior range is used and the band widens
    accordingly, which is the honest representation of not knowing.
    """
    if finders < 0:
        raise ValueError("finders must not be negative")

    if candidates_per_finder is None:
        low = _kb(finders, DENSITY_PRIOR["low"])
        expected = _kb(finders, DENSITY_PRIOR["expected"])
        high = _kb(finders, DENSITY_PRIOR["high"])
        density = DENSITY_PRIOR["expected"]
    else:
        if candidates_per_finder < 0:
            raise ValueError("candidates_per_finder must not be negative")
        density = candidates_per_finder
        expected = _kb(finders, density)
        # A supplied density is still one sample. Band it rather than pretend.
        low = expected * SUPPLIED_DENSITY_LOW_MULT
        high = expected * SUPPLIED_DENSITY_HIGH_MULT

    # The high end must never sit below a packet size already observed.
    high = max(high, finders * OBSERVED_MAX_KB_PER_FINDER)

    # The budget is the orchestrator's context, never the filesystem's.
    context = expected * INDEX_SHARE_OF_PACKET if index_to_disk else expected
    will_degrade = context > DEGRADE_THRESHOLD_KB
    if will_degrade:
        warning = (
            f"Projected ~{context / 1024:.1f}MB carried in context against a "
            f"~{DEGRADE_THRESHOLD_KB / 1024:.1f}MB survivable budget. This run is "
            f"likely to reach verification degraded. Options: bound it, split the "
            f"component, or accept a partial run and say so in the digest. Deciding "
            f"now is the point -- the failure is silent otherwise."
        )
    else:
        warning = ""

    return Projection(
        finders=finders,
        candidates_per_finder=density,
        low_kb=low,
        expected_kb=expected,
        high_kb=high,
        context_kb=context,
        will_degrade=will_degrade,
        warning=warning,
    )


def format_projection(p: Projection) -> str:
    lines = [
        f"Finders:            {p.finders}",
        f"Candidate density:  {p.candidates_per_finder:.2f} per finder"
        + (
            "  (prior -- none supplied)"
            if p.candidates_per_finder == DENSITY_PRIOR["expected"]
            else ""
        ),
        f"Packet volume:      {p.expected_kb / 1024:.2f}MB expected "
        f"({p.low_kb / 1024:.2f}-{p.high_kb / 1024:.2f}MB)",
        f"Carried in context: {p.context_kb / 1024:.2f}MB"
        + (
            "  (packets written to disk by the finder)"
            if p.context_kb < p.expected_kb
            else "  (packets returned INLINE -- this is the budget that binds)"
        ),
        f"Candidate-driven:   {candidate_driven_share(p.candidates_per_finder):.0%} "
        f"of projected volume",
        f"Basis:              {CALIBRATION['basis']}, {CALIBRATION['sample_size_runs']} run "
        f"({CALIBRATION['source_run']})",
    ]
    if p.will_degrade:
        lines.append("")
        lines.append(f"WARNING: {p.warning}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--finders", type=int, required=True, help="len(mandates) + len(LENSES)"
    )
    ap.add_argument(
        "--candidates-per-finder",
        type=float,
        default=None,
        help="Density prior. Omit to use the built-in range.",
    )
    ap.add_argument(
        "--no-index-to-disk",
        action="store_true",
        help="Model finders returning packets INLINE. For comparing against "
             "pre-2026-08-28 runs, or when a finder cannot write to disk.",
    )
    args = ap.parse_args()
    print(format_projection(project(
            args.finders,
            args.candidates_per_finder,
            index_to_disk=not args.no_index_to_disk,
        )))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
