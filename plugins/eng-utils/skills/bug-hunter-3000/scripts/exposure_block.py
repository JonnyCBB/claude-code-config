#!/usr/bin/env python3
"""Build each finding's `exposure` block from the two resolver passes.

Derives `figure_kind`, `share.harm_hash` and `resolved_fingerprints`, which must never
be hand-written. `references/run-record.md` states the rules this implements; the
mapping it applies, so a reader can check it rather than trust it:

    nobody reconciled it                     -> PATH_EXPOSURE
    harm not confirmed                       -> PATH_EXPOSURE (whatever the disposition)
    second pass measured the corrected harm  -> HARM_SHARE
    second pass could not, first pass kept   -> PATH_EXPOSURE
    reconciler ADOPTED on a confirmed harm   -> HARM_SHARE

It builds the exposure block and nothing else. A general record assembler would have to
own all forty-odd fields of the schema, which is a much larger claim.

Usage:
    python3 exposure_block.py --resolver <first-pass.json> --verdicts <dir> \
        --states <states.json> [--reresolve <second-pass.json>] [--out <path>]

Both resolver arguments accept either the agent's own
`{attempted, resolved, unresolved, candidates: [...]}` shape or an already-merged
`{fingerprint: entry}` map, because a run has both on disk.

Exit codes:
    0  OK       blocks written; nothing else reached stdout
    1  REFUSED  a contradiction that must be fixed upstream, listed on stderr
"""

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).resolve().parent))

from digest_model import (  # noqa: E402
    _HARM_CONFIRMED_STATES,
    EXPOSURE_PLACEHOLDERS,
    FindingState,
    harm_hash,
)

# Imported rather than restated: the renderer recognises these phrases and drops
# them, so a local copy that drifted in WORDING would render as prose.
#
# The fallbacks state an ABSENCE and never a CAUSE. `share_absent` owns the
# cause, and a default that guesses one contradicts it: "not established, no
# metric measures this" over a NOT_QUERIED cell told a reader both that no
# instrument exists and that nobody looked, in the same cell, two lines apart.
# Caught by reading the rendered page, not the code.
#
# `path_denominator` defaults to a BARE absence token on purpose: the cell states
# the absence in its headline and names the cause underneath, so a fallback
# phrase there is the same nothing said three times. `component_denominator`
# keeps its phrase -- it renders always, by a rule about the two denominators
# pointing opposite ways.
_REJECTED = frozenset({"DOWNGRADED", "REPLACED"})
_SHARE_FIGURES = ("numerator", "denominator")
_SHARE_PROSE = ("unit", "of")


def _load(path: Path) -> object:
    if not path.exists():
        _die(f"{path} does not exist", 2)
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        _die(f"{path} is not valid JSON: {exc}", 2)


def _die(message: str, code: int) -> NoReturn:
    """Print and exit. `NoReturn`, not `None`.

    Declared `-> None`, every caller looked to a type checker like it might
    continue -- which reported `_load` as able to fall off its end, and forced
    an unreachable `return {}` into `_entries` purely to satisfy that. A
    function whose only exit is an exception should say so.
    """
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _entries(payload: object, label: str) -> dict:
    """Accept the agent's own shape or an already-merged map, interchangeably."""
    if isinstance(payload, dict) and isinstance(payload.get("candidates"), list):
        out = {}
        for entry in payload["candidates"]:
            if not isinstance(entry, dict) or not entry.get("fingerprint"):
                _die(f"{label}: a candidate entry carries no fingerprint", 1)
            out[entry["fingerprint"]] = entry
        return out
    if isinstance(payload, dict):
        return payload
    _die(f"{label}: expected an object, got {type(payload).__name__}", 1)


def _share(entry: dict, kind: str, statement: str | None) -> dict | None:
    """The four-key share, plus the two keys that bind it to a question.

    Returns None where the resolver produced no conforming figure. The shape
    check is deliberately the same one the orchestrator runs on receipt: a
    string, a bare number or a three-key object is real information the renderer
    cannot use, and it must land as a named absence rather than as a guess.
    """
    if not isinstance(statement, str) or not statement.strip():
        # No statement means nothing to bind a figure to, which is the same
        # outcome as no conforming figure. Every caller reaches this through a
        # `.get()`, so the parameter is genuinely optional and says so.
        return None
    share = entry.get("share")
    if not isinstance(share, dict):
        return None
    if not all(key in share for key in _SHARE_FIGURES + _SHARE_PROSE):
        return None
    try:
        numerator = float(share["numerator"])
        denominator = float(share["denominator"])
    except (TypeError, ValueError):
        return None
    if denominator <= 0 or not 0 <= numerator <= denominator:
        return None
    if not (str(share["unit"]).strip() and str(share["of"]).strip()):
        return None
    return {
        "numerator": numerator,
        "denominator": denominator,
        "unit": str(share["unit"]).strip(),
        "of": str(share["of"]).strip(),
        # Computed here, from the statement the resolver echoed back as the one
        # it measured against -- never from the finding's current statement.
        # Hashing the current statement would satisfy the validator's comparison
        # while removing the only signal that a figure has gone stale.
        "harm_hash": harm_hash(statement),
        "figure_kind": kind,
    }


def _harm_confirmed(state: str) -> bool:
    """Whether this finding's harm is established, per `digest_model`.

    Imported rather than restated: the classification of all eleven states is
    one table there, and a second copy here is the drift this whole change is
    about.
    """
    return FindingState.__members__.get(state) in _HARM_CONFIRMED_STATES


def _kind(disposition: object, state: str) -> str:
    """What a figure counts, derived rather than asked for.

    A lookup table, which is why no agent is asked to decide it:

    - the harm is not confirmed -> PATH_EXPOSURE, whatever the disposition says.
      A refuted finding has no harm for anything to be a share of, and a
      reconciler can still legitimately ADOPT a figure there -- one adopted a
      measured ZERO, "0% of the path, the path does not exist", which is a
      genuine and useful path figure.
    - nobody reconciled it      -> PATH_EXPOSURE; nothing checked what it counts
    - otherwise                 -> HARM_SHARE, by what ADOPTED and REPLACED mean

    A RETAINED first-pass figure never comes through here; the caller labels it
    PATH_EXPOSURE outright, because what the first pass measured is the traffic
    reaching the code and no reconciler accepted it as the harm.
    """
    if disposition is None or not _harm_confirmed(state):
        return "PATH_EXPOSURE"
    return "HARM_SHARE"


def _second_pass_figures(reresolve: dict) -> list[str]:
    """Which second-pass candidates came back with a conforming figure.

    `reresolution.resolved_fingerprints` is required by the validator and the
    resolver's own output does not carry it, so somebody has to derive it. Both
    eval runs derived it correctly and both recorded having had to work it out,
    which is a judgement call the caller should not have been left holding: it
    is the same four-key check this file already runs.
    """
    return sorted(
        fp
        for fp, entry in reresolve.items()
        if _share(entry, "PATH_EXPOSURE", entry.get("harm_measured"))
    )


def _shape_refusal(
    fingerprint: str, state: str, verdict: "dict | None", disposition: object
) -> str | None:
    """The refusals that need nothing but the verdict and the state.

    Extracted from `build`, which was over Ruff's branch and statement ceilings
    with all seven refusals inline. That matters more here than as a style
    point: seven defects have been found in this file, and a 160-line function
    with seven `continue` sites is one nobody can check by reading.
    """
    reconciled = state != "DEFERRED_UNVERIFIED"
    if reconciled and verdict is None:
        return (
            f"{fingerprint}: state is {state} but there is no verdict file. "
            "Every reconciled finding has one; a missing verdict is a "
            "reconciler whose output was lost, not a finding with no figure."
        )
    if reconciled and disposition is None:
        return (
            f"{fingerprint}: the verdict states no figure_disposition. One of "
            "ADOPTED, DOWNGRADED, REPLACED or NO_FIGURE, per "
            "agents/bug-hunt-reconciler.md."
        )
    if not reconciled and disposition is not None:
        return (
            f"{fingerprint}: carries figure_disposition {disposition!r} but "
            "nobody reconciled it."
        )
    return None


def _figure_refusal(
    fingerprint: str,
    disposition: object,
    share: "dict | None",
    statement: str,
    echo: object,
    offered: object,
    absent: object,
) -> str | None:
    """The refusals that need the resolved figure in hand.

    Each one is a contradiction between what the reconciler said and what the
    resolver produced, and each names its own cause -- because left to the
    record validator two stages later they surface as something else. The
    ADOPTED one in particular reads there as "the figure answers a superseded
    question", which sends a reader hunting a stale figure rather than a
    retyped sentence.
    """
    if share is not None and disposition == "ADOPTED":
        if harm_hash(str(echo or "")) != harm_hash(statement):
            return (
                f"{fingerprint}: ADOPTED, but the reconciler's harm statement "
                "is not the one the resolver measured against. ADOPTED means "
                "the figure fits the harm AS STATED, so a reworded statement "
                "is DOWNGRADED or REPLACED -- see "
                "agents/bug-hunt-reconciler.md. If the wording changed only "
                "cosmetically, restore the dispatched sentence."
            )
    if share is not None and disposition == "NO_FIGURE":
        return (
            f"{fingerprint}: the verdict says NO_FIGURE, but the resolver "
            "returned a conforming share. NO_FIGURE means there was nothing to "
            "judge, so one of ADOPTED, DOWNGRADED or REPLACED describes what "
            "happened to this figure."
        )
    if share is None and absent is None:
        # NEVER INVENT THE CAUSE OF AN ABSENCE. This defaulted to NOT_QUERIED
        # -- "nobody looked" -- which on a real candidate contradicted that
        # finding's own reconciler, who had recorded "a recorded and attributed
        # failed attempt". Someone did look. Reading the reconciler's prose
        # instead is the substring-matching trap that caused the original
        # defect, so the two upstream causes get named and sent back.
        if offered is not None:
            return (
                f"{fingerprint}: the resolver returned a share in a form the "
                "renderer cannot use, so there is no figure and no named "
                'reason. Reclassify it as unresolved with "resolver returned '
                'a non-conforming share" -- that is a fact about the '
                "pipeline, and laundering it into one of the three "
                "world-claims would tell a reader something nobody "
                "established."
            )
        return (
            f"{fingerprint}: no figure and no named reason for its absence. "
            "The resolver owes one of NOT_QUERIED, NO_INSTRUMENT or "
            "NOT_REQUEST_SCOPED on every candidate, and this file will not "
            "guess: 'nobody looked' over a candidate somebody did look at is "
            "the misstatement the column exists to stop."
        )
    return None


def _resolve_share(
    first: dict, second: dict, covered: bool, disposition: object, state: str
) -> "tuple[dict | None, bool]":
    """The figure, and whether it is a RETAINED first-pass one.

    THREE CASES, AND THEY ARE NOT TWO.

    The second pass wins where it measured the harm. Where it RAN and could
    not, the first pass's figure is retained and relabelled rather than
    deleted: it is a real queried number for how much traffic reaches the
    defective code, which is what PATH_EXPOSURE is for. Deleting it is what the
    old assembler did to 27 figures, and one reconciler wrote the rule out in
    its own note -- "retained but relabelled as path exposure, not harm" --
    which reached no reader.

    Where no second pass was owed, the first pass's figure stands with the kind
    the disposition implies. Collapsing this into the retention case
    mislabelled every ADOPTED figure as path exposure, because an adopted
    figure has no second pass to come from.
    """
    if covered:
        share = _share(second, _kind(disposition, state), second.get("harm_measured"))
        if share is not None:
            return share, False
        retained = _share(first, "PATH_EXPOSURE", first.get("harm_measured"))
        return retained, retained is not None
    return _share(first, _kind(disposition, state), first.get("harm_measured")), False


def build(
    resolver: dict, reresolve: dict, verdicts: dict, states: dict
) -> tuple[dict, list[str]]:
    """One exposure block per fingerprint, plus every contradiction found.

    Refusals are collected rather than raised on the first, because the caller
    fixing them is an agent and it will repair exactly what it is told about.
    """
    blocks: dict = {}
    problems: list[str] = []
    for fingerprint, state in sorted(states.items()):
        verdict = verdicts.get(fingerprint)
        disposition = (verdict or {}).get("figure_disposition")
        problem = _shape_refusal(fingerprint, state, verdict, disposition)
        if problem:
            problems.append(problem)
            continue

        first = resolver.get(fingerprint) or {}
        second = reresolve.get(fingerprint) or {}
        prose_source = second or first

        statement = (verdict or {}).get("corrected_harm_statement") or (
            prose_source.get("harm_measured") or first.get("harm_measured")
        )
        if not (isinstance(statement, str) and statement.strip()):
            problems.append(
                f"{fingerprint}: no harm statement. A reconciled finding takes "
                "the reconciler's corrected_harm_statement; an unreconciled "
                "one takes the harm_measured the resolver echoed back."
            )
            continue

        # A rejected figure the second pass never covered cannot be labelled at
        # all: the reconciler said it does not measure the harm, and nothing has
        # measured what does. Falling through to `_resolve_share`'s
        # no-second-pass case labelled it HARM_SHARE -- the exact opposite of
        # that judgement.
        covered = fingerprint in reresolve
        if disposition in _REJECTED and not covered:
            problems.append(
                f"{fingerprint}: figure_disposition is {disposition!r}, so its "
                "figure was rejected and must be re-measured, but the "
                "second-pass input carries no entry for it. Dispatch the "
                "re-resolve pass over every rejected candidate, or record the "
                "attempt that failed -- a rejected figure with no second pass "
                "has no honest label."
            )
            continue

        share, retained = _resolve_share(first, second, covered, disposition, state)
        absent = (
            None
            if share
            else (prose_source.get("share_absent") or first.get("share_absent"))
        )
        problem = _figure_refusal(
            fingerprint,
            disposition,
            share,
            statement,
            (second or first).get("harm_measured"),
            prose_source.get("share") or first.get("share"),
            absent,
        )
        if problem:
            problems.append(problem)
            continue

        blocks[fingerprint] = {
            "harm_statement": statement.strip(),
            "exposure": _exposure(first, second, share, retained, absent, disposition),
        }

    return blocks, problems


def _exposure(
    first: dict,
    second: dict,
    share: "dict | None",
    retained: bool,
    absent: object,
    disposition: object,
) -> dict:
    """The block itself, once every contradiction has been ruled out."""
    prose_source = second or first
    detail = prose_source.get("share_absent_detail") if absent else None
    note = prose_source.get("note") or EXPOSURE_PLACEHOLDERS["note"]
    if retained:
        # The second pass's reasoning is why there is no HARM figure, and the
        # cell now shows a PATH figure instead. That reasoning is what a reader
        # needs in order to read the number correctly, so it goes in `note`
        # rather than being dropped with the absence it was written to explain.
        why = second.get("share_absent_detail") or second.get("note")
        if isinstance(why, str) and why.strip() and why.strip() not in note:
            # `share_absent_detail` is a 72-character fragment by
            # specification, so it arrives with no terminal punctuation and the
            # prose gate rejects a field that stops mid-sentence.
            # NEVER PREFIX THE PLACEHOLDER. With no resolver note, `note` IS
            # `EXPOSURE_PLACEHOLDERS["note"]`, and composing onto it produced
            # "No figure was resolved for this one. Harm rate not measurable:
            # ..." -- a placeholder sentence under a column showing a figure.
            lead = "" if note == EXPOSURE_PLACEHOLDERS["note"] else f"{note.rstrip('.')}. "
            note = f"{lead}Harm rate not measurable: {why.strip().rstrip('.')}."
    # `basis` describes THE FIGURE, so it comes from whichever pass produced the
    # figure -- not from whichever wrote the prose. Taking it from the prose
    # source put a retained MEASURED figure under the second pass's UNKNOWN,
    # which the validator refuses because UNKNOWN asserts no numerator was
    # established.
    figure_source = first if (retained or not second) else second
    return {
        "basis": (figure_source if share else prose_source).get("basis") or "UNKNOWN",
        **{
            key: (prose_source.get(key) or default)
            for key, default in EXPOSURE_PLACEHOLDERS.items()
            if key != "note"
        },
        "note": note,
        "figure_disposition": disposition,
        "share": share,
        "share_absent": absent,
        "share_absent_detail": detail if isinstance(detail, str) else None,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resolver", required=True, type=Path)
    parser.add_argument("--reresolve", type=Path)
    parser.add_argument("--verdicts", required=True, type=Path)
    parser.add_argument("--states", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    resolver = _entries(_load(args.resolver), "resolver")
    reresolve = _entries(_load(args.reresolve), "reresolve") if args.reresolve else {}
    if not args.verdicts.is_dir():
        _die(f"{args.verdicts} is not a directory", 2)
    verdicts = {p.stem: json.loads(p.read_text()) for p in args.verdicts.glob("*.json")}
    states = _load(args.states)
    if not isinstance(states, dict) or not states:
        _die("--states must be a non-empty {fingerprint: state} object", 2)
    assert isinstance(states, dict)  # narrowed by the check above

    blocks, problems = build(resolver, reresolve, verdicts, states)
    if problems:
        json.dump({"status": "REFUSED", "problems": problems}, sys.stderr, indent=2)
        raise SystemExit(1)

    rejected = sorted(
        fp
        for fp, block in blocks.items()
        if block["exposure"]["figure_disposition"] in _REJECTED
    )
    payload = {
        "findings": blocks,
        # Both derived from what actually validated, so neither can disagree
        # with the blocks above. These are the two record-level figures the
        # validator cross-checks, and hand-writing either is how they drift.
        "resolved_fingerprints": sorted(
            fp for fp, block in blocks.items() if block["exposure"]["share"]
        ),
        "reresolution_attempted": len(rejected),
        "rejected_fingerprints": rejected,
        # The second pass's own resolved list, for the `reresolution` block.
        "reresolution_resolved_fingerprints": _second_pass_figures(reresolve),
    }
    text = json.dumps(payload, indent=1)
    if args.out:
        args.out.write_text(text)
    else:
        print(text)


if __name__ == "__main__":
    main()
