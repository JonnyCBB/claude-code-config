#!/usr/bin/env python3
"""Validate a bug-hunt run record and normalise it for rendering.

Two passes, deliberately. Validation returns every problem it finds rather than
raising on the first, because a caller fixing a malformed record wants the whole
list -- and the caller here is an agent, which will repair exactly what it is
told about and re-run. Only a clean validation proceeds to normalisation, so the
frozen dataclasses downstream can assume their fields are present and
well-formed.

The verdict vocabulary here is the reader-facing one. The ten internal
dispositions never reach the digest -- see
references/verdicts-and-bands.md section 3 for the schema this
translates from, and references/run-record.md for the input contract.

Usage:
    python3 digest_model.py < run_record.json      # normalised JSON on stdout

Exit codes:
    0  OK             record valid; normalised JSON on stdout
    1  INVALID        validation failed; every problem listed on stderr
    2  NO_INPUT       nothing on stdin, or unparseable JSON. Never a pass.

Nothing but the payload ever reaches stdout, and nothing at all reaches it on an
error exit: this is the head of a three-stage pipe, and a bash pipeline reports
only the last command's status, so a partial payload here would be rendered and
written as though the run had succeeded.
"""

import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from types import MappingProxyType
from typing import Callable, Final, Mapping


class FindingState(Enum):
    """The ten dispositions, plus DEFERRED_UNVERIFIED.

    DEFERRED_UNVERIFIED is deliberately included even though the schema is
    explicit that it is NOT a disposition: it occupies the same slot in a
    portfolio file, so a run record has to be able to carry it.
    """

    DISCARDED_REFUTED = "DISCARDED_REFUTED"
    DISCARDED_INTENDED = "DISCARDED_INTENDED"
    HOLD_MECHANISM_INCONCLUSIVE = "HOLD_MECHANISM_INCONCLUSIVE"
    HOLD_INTENT_AMBIGUOUS = "HOLD_INTENT_AMBIGUOUS"
    READY_LOCAL_CANDIDATE = "READY_LOCAL_CANDIDATE"
    READY_CROSS_SYSTEM_DOSSIER = "READY_CROSS_SYSTEM_DOSSIER"
    PRODUCT_EXPERIENCE_DOSSIER = "PRODUCT_EXPERIENCE_DOSSIER"
    DUPLICATE = "DUPLICATE"
    KNOWN_ACCEPTED_RISK = "KNOWN_ACCEPTED_RISK"
    BACKLOGGED = "BACKLOGGED"
    DEFERRED_UNVERIFIED = "DEFERRED_UNVERIFIED"


class Verdict(Enum):
    """Reader-facing verdicts. These exact strings are the canonical form.

    Owned by this module; every other file cites them verbatim, apostrophe
    included. Three files independently normalising a shared quote is a measured
    divergence in this repo.
    """

    BUG = "Bug"
    YOUR_CALL = "Your call"
    COULDNT_VERIFY = "Couldn't verify"
    NOT_CHECKED = "Not checked"
    NOT_A_BUG = "Not a bug"


class Band(Enum):
    """How closely to read a finding. The digest's primary grouping, in this order.

    These name the READER'S effort, not an action on the code. `Act Now / Important / Low` was measured training readers to ignore the top band: runs produced
    several reports and very few fixes, and an "act now" nobody acts on devalues
    the next one. The final judgement is a human's, so the band sizes the reading.
    """

    READ_CLOSELY = "Read closely"
    WORTH_A_LOOK = "Worth a look"
    SKIM = "Skim"
    NOT_TRIAGED = "Not triaged"


_VERDICT_BY_STATE: dict[FindingState, Verdict] = {
    FindingState.READY_LOCAL_CANDIDATE: Verdict.BUG,
    FindingState.READY_CROSS_SYSTEM_DOSSIER: Verdict.BUG,
    FindingState.PRODUCT_EXPERIENCE_DOSSIER: Verdict.BUG,
    FindingState.HOLD_INTENT_AMBIGUOUS: Verdict.YOUR_CALL,
    FindingState.HOLD_MECHANISM_INCONCLUSIVE: Verdict.COULDNT_VERIFY,
    FindingState.DEFERRED_UNVERIFIED: Verdict.NOT_CHECKED,
    FindingState.DISCARDED_REFUTED: Verdict.NOT_A_BUG,
    FindingState.DISCARDED_INTENDED: Verdict.NOT_A_BUG,
    # The three human-assigned states below all mean "no action needed now".
    # They collapse with the discards, and the renderer prints the state name
    # so the human decision stays visible rather than being flattened away.
    FindingState.DUPLICATE: Verdict.NOT_A_BUG,
    FindingState.KNOWN_ACCEPTED_RISK: Verdict.NOT_A_BUG,
    FindingState.BACKLOGGED: Verdict.NOT_A_BUG,
}

# Fires at import time, so a future edit adding a state without a mapping fails
# at collection rather than silently rendering the wrong verdict. This is the
# mechanical guarantee that stands in for a type checker: no mypy or pyright is
# configured anywhere in this tree, so match/assert_never would be decorative.
assert set(_VERDICT_BY_STATE) == set(FindingState), "every state needs a verdict"

_FINGERPRINT = re.compile(r"[0-9a-f]{16}")
# A full commit SHA. Short SHAs are rejected in the record even though the digest
# displays one: an abbreviation that is unique today can collide as the repository
# grows, and the record is the thing a reader resolves a link from years later.
_SHA40 = re.compile(r"[0-9a-f]{40}")
_EFFORTS = frozenset({"S", "M", "L"})

# Tier is a closed set so that the fold rule is enforceable rather than
# advisory. `scope-and-safety.md` section 5 forbids folding `UNTIERED` into Tier 4
# -- but while this field validated as free text, nothing stopped a run doing
# exactly that, and the schema could not tell. Now `4` and `UNTIERED` are distinct
# values and anything else is rejected by name.
#
# Bare digits rather than "Tier 2" because the value is data and "Tier 2" is
# presentation: `UNTIERED` has no natural "Tier N" spelling, so accepting the
# prefixed form would make the set inconsistent with its own absence case. The
# renderer formats for display. Measured need: the canonical fixture used
# "Tier 1"/"Tier 2" while a real run emitted "2", so two producers had already
# diverged on format under the free-text rule.
_TIERS = frozenset({"1", "2", "3", "4", "UNTIERED"})

# A source permalink, and the ONLY value in this document that reaches an href.
#
# The 40-hex commit SHA is mandatory, and that is the whole point of the pattern
# rather than an incidental strictness: a branch-name link silently rots as the
# branch moves, so the line it points at stops being the line the finding is
# about. Measured on the run that prompted this field -- a local review branch
# put the defect at FeedModule.java:164 while the pushed ref had the same
# `@Provides` at :168, and :164 there was an unrelated `.build();`. A reader
# following that link lands on the wrong code and correctly stops trusting the
# report. Pinning to a SHA makes that class of link unrepresentable.
#
# Validating here rather than in the renderer keeps render_digest.py's rule --
# that no finding-derived text reaches an attribute unvalidated -- structural. By
# the time a permalink is rendered it has already been proven to match this
# shape, so `javascript:` and quote-breakout payloads cannot be expressed.
_PERMALINK = re.compile(
    r"https://[A-Za-z0-9.\-]+/[A-Za-z0-9._\-]+/[A-Za-z0-9._\-]+"
    r"/blob/[0-9a-f]{40}/[A-Za-z0-9._/\-]+#L\d+(?:-L\d+)?"
)

# The bound on `observed_symptom`, which renders in the ALWAYS-VISIBLE row.
# 120 characters is what that row shows in full at the sheet's mono size.
#
# Measured: the field is specified "verbatim, mono, one line", and an
# orchestrator filled it with 200-400 character multi-line stack traces. Every
# symptom in that digest rendered clipped mid-token -- the reader saw a broken
# fragment where the evidence was supposed to be, on every single row. The
# renderer now clamps to two lines as a safety net, but a clamp still truncates;
# the fix is that an unrenderable value cannot be represented at all. The
# complete capture has its own field, `observed_full`, which is rendered in the
# expansion where it has room.
_SYMPTOM_MAX_CHARS = 120


# The exposure figure as it appears at the head of `path_denominator`, and the
# bound on the whole phrase. 80 characters is what the manifest's exposure column
# shows without pushing the finding text out of its own column.
_EXPOSURE_FIGURE = re.compile(r"^[<>~]?\d+(?:\.\d+)?%")
_DENOMINATOR_MAX_CHARS = 80

# The four keys a percentage needs, plus the hash that binds it to the harm it
# answers, and the bounds on the two prose ones.
_SHARE_KEYS = ("numerator", "denominator", "unit", "of", "harm_hash", "figure_kind")
_SHARE_UNIT_MAX_CHARS = 24
_SHARE_OF_MAX_CHARS = 52
_SHARE_DETAIL_MAX_CHARS = 72

# What the number counts, which is a different question from how it was obtained.
#
# `basis` says where a figure came from; this says what population it is a share
# OF, and the two are orthogonal. Before this field existed the column rendered
# both kinds identically as a percentage with a bar, so a reader could not tell
# "3% of requests are harmed" from "3% of requests reach this code, and nobody
# checked whether they are harmed". On the character-pro run that was 52 figures
# of the second kind in a column that reads as the first.
#
# HARM_SHARE   the share of the population the finding's CONFIRMED harm actually
#              damages. Only reachable after a reconciler has settled the harm
#              statement, which is why it is the re-resolve stage that produces
#              it.
# PATH_EXPOSURE how much traffic REACHES the defective code. Legitimate and
#              useful, and not the same claim -- it is an upper bound on the harm
#              rather than a measurement of it.
_FIGURE_KIND_VALUES: Final[tuple[str, ...]] = ("HARM_SHARE", "PATH_EXPOSURE")

# The reconciler's structured judgement on the figure it was handed, replacing a
# hand-written fingerprint allowlist that a run wrote into its own assembler.
#
# Fingerprints are content-derived and run-scoped, so an allowlist of literal
# fingerprints matches nothing on the next run and every figure is silently
# blanked -- an empty allowlist intersection is not an error. Reaching a verifier
# was what deleted the figure; `run-record.md`'s `figure_disposition`
# section is canonical for the accounting and it is not restated here, because a
# count in two files is a count that will drift.
#
# The replacement is a value the reconciler states, on the finding, in a closed
# set -- checked by equality against that set and never by substring containment.
# Deriving this from reconciler prose was tried in the same assembler ("downgrad"
# anywhere in the note, or "estimated" within the first 60 characters) and is
# what produced ESTIMATED over an absent figure on most of the findings it
# touched; `run-record.md` has the count.
# `NO_FIGURE` was added after checking the closed set against the real
# reconciler verdicts on the 2026-09-05 run: a substantial minority had no
# resolver figure to judge at all, and every one of the other three values
# would have been a false claim about work nobody did. A closed set that forces
# a lie on real cases is how a field starts being filled in arbitrarily.
# `run-record.md`'s `figure_disposition` section has the counts.
_FIGURE_DISPOSITION_VALUES: Final[tuple[str, ...]] = (
    "ADOPTED",
    "DOWNGRADED",
    "REPLACED",
    "NO_FIGURE",
)

# The two that send a figure back to be re-measured against the corrected harm.
# Named once, because three call sites test for exactly this pair and a fourth
# reader has to be able to see that they agree.
_FIGURE_REJECTED: Final[frozenset[str]] = frozenset({"DOWNGRADED", "REPLACED"})

# Whether a finding's harm is CONFIRMED, which is what a harm share is a share
# OF. Keyed on the state rather than derived by excluding DEFERRED_UNVERIFIED,
# because "a reconciler looked at it" and "the harm is real" are different
# facts and only the second licenses the claim. Excluding by hand let
# HARM_SHARE sit on DISCARDED_REFUTED -- a harm share for a harm that did not
# reproduce, which is this change's own bug class -- and sent a re-resolve
# agent off to measure the harm rate of a non-bug.
#
# Every member is listed, and a test fails if a new one is added without being
# classified: a state that gets its answer by exclusion is a state nobody
# decided about.
_HARM_CONFIRMED_STATES: Final[frozenset[FindingState]] = frozenset(
    {
        # Mechanism CONFIRMED and intent VIOLATION_SUPPORTED: a real harm.
        FindingState.READY_LOCAL_CANDIDATE,
        FindingState.READY_CROSS_SYSTEM_DOSSIER,
        FindingState.PRODUCT_EXPERIENCE_DOSSIER,
        # Mechanism CONFIRMED, intent unclear. The behaviour reproduces, so the
        # population it damages is measurable; whether anyone MEANT it is the
        # open question, and that does not change the arithmetic.
        FindingState.HOLD_INTENT_AMBIGUOUS,
        # Human-assigned over a finding already judged real. Set aside
        # administratively, not refuted.
        FindingState.KNOWN_ACCEPTED_RISK,
        FindingState.BACKLOGGED,
    }
)

# The rest, spelled out rather than implied. DISCARDED_* did not reproduce or
# was intended; HOLD_MECHANISM_INCONCLUSIVE never reproduced at all, so there is
# no confirmed harm to be a share of; DUPLICATE's harm belongs to the finding it
# duplicates; DEFERRED_UNVERIFIED nobody looked at.
_HARM_UNCONFIRMED_STATES: Final[frozenset[FindingState]] = frozenset(
    {
        FindingState.DISCARDED_REFUTED,
        FindingState.DISCARDED_INTENDED,
        FindingState.HOLD_MECHANISM_INCONCLUSIVE,
        FindingState.DUPLICATE,
        FindingState.DEFERRED_UNVERIFIED,
    }
)


def _is_count(value: object) -> bool:
    """A non-negative integer that is not a bool.

    `bool` is an `int` subclass, and `"attempted": true` is exactly the stand-in
    a producer reaches for when it has no real count -- so every count check in
    this file has to exclude it. The predicate is spelled out at nine older
    sites; new ones call this.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def harm_hash(statement: str) -> str:
    """The identity of a harm statement, so a figure can be bound to one.

    A share answers a question. The pipeline's whole purpose is to CORRECT the
    question -- a verifier that changes what the harm is has invalidated any
    figure computed against the old wording -- and until this existed nothing
    recorded which wording a figure answered. The stage that re-measures could
    be added and then silently stop running, or a later change could mutate a
    harm statement in place, and the digest would render a stale percentage with
    no signal at all.

    So the producer records this hash on the share at the moment it computes the
    figure, and `validate_run_record` recomputes it from the finding's
    `harm_statement` and REFUSES the record if the two differ. That turns a
    process obligation into a machine-checked invariant.

    Whitespace-insensitive and case-sensitive: re-wrapping a paragraph must not
    invalidate a figure, but changing a word must. Truncated to 16 hex
    characters, matching the fingerprint width this skill already uses.

    The resolver holds no Bash and cannot hash anything, so it does not: it
    echoes back the harm statement it measured against, verbatim, and the
    orchestrator hashes THAT. The echo is the evidence; this is just its
    identity. Hashing the finding's current statement instead of the echoed one
    would satisfy the check while defeating it, and nothing inside a single
    record can tell the two apart -- so the schema says that outright rather
    than implying otherwise. What the check buys is that the stale-figure case
    cannot ship by accident, and that the remaining bypass is a deliberate false
    statement rather than an omission: the same bargain `resolver_agent_id`
    already strikes.
    """
    return hashlib.sha256(" ".join(statement.split()).encode()).hexdigest()[:16]


# A harm statement is a sentence, and both bounds are loose on purpose: they
# reject a placeholder and a pasted evidence trail, not a wording choice.
_HARM_STATEMENT_MIN_CHARS = 12
_HARM_STATEMENT_MAX_CHARS = 400

# The absence of a share is not one thing, and the three cases are not
# interchangeable for a reader setting priority.
#
# On a real run the column rendered all of them identically. `NO_INSTRUMENT` is a
# priority input in its own right: no instrument separates a harmed state from a
# healthy one, which is the same fact a band_reason cites as "harm undetectable".
# `NOT_QUERIED` says only that nobody looked. `NOT_REQUEST_SCOPED` says an
# instrument exists but cannot attribute harm to requests -- a gauge written on a
# timer, whose `0` is therefore not a measured zero. That last distinction is
# about the INSTRUMENT, not about whether the harm feels request-shaped; wording
# it the other way sent a resolver to `NO_INSTRUMENT` for the very case this
# value was added for. `run-record.md`'s `share_absent` section is
# canonical for the counts and works all three through real findings.
_SHARE_ABSENT_VALUES: Final[tuple[str, ...]] = (
    "NOT_QUERIED",
    "NO_INSTRUMENT",
    "NOT_REQUEST_SCOPED",
)


@dataclass(frozen=True, slots=True)
class ValidationError:
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class Share:
    """The percentage, carried as data because it cannot be derived from prose.

    A reader setting priority wants a percentage: 1% of requests and 25% of
    requests are different problems. The two prose denominators cannot supply
    one, and a renderer that took the leading figure from each and divided would
    have been wrong more often than right on a real run -- sometimes because the
    two sides count different things, and twice by producing a confident figure
    from no measurement at all. `run-record.md`'s `share` section is
    canonical for those counts and this docstring does not restate them, because
    a count in two files is a count that will drift.

    Two failure shapes are worth knowing at this site, because the validation
    below exists to refuse exactly them: the component population copied into
    the numerator's slot, which divides to 100% on a finding nobody measured; and
    a denominator chosen from prose that named two populations, where the choice
    moves the answer by more than the figure's own precision.

    `unit` is the load-bearing field, and it is deliberately ONE field rather
    than one per side: a single unit for both numerator and denominator is the
    commensurability proof, and it makes "N metric series of M grpc pairs"
    impossible to express rather than merely discouraged. The impact resolver's brief
    already asks for units "inside `note`, in the form `numerator (per X) /
    denominator (per Y)`" and states outright that "there is no separate unit
    key, so a unit stated anywhere else is dropped silently". This is that key.

    `of` supplies the noun, for the same reason `path_denominator` must: the
    renderer cannot know whether 63,000 counts searches, requests or items, and a
    noun hardcoded in the renderer would be wrong everywhere except where it was
    written.
    """

    numerator: float
    denominator: float
    unit: str
    of: str
    # The `harm_hash()` of the harm statement this figure was computed against,
    # recorded by the stage that queried. `validate_run_record` recomputes it
    # from the finding's `harm_statement` and refuses a mismatch, so a figure
    # cannot outlive the question it answers.
    harm_hash: str
    # What this figure counts -- see `_FIGURE_KIND_VALUES`. It lives here rather
    # than on `Exposure` because it describes a figure: inside `share` it cannot
    # be stated without one or omitted with one, which is a stronger guarantee
    # than a validator refusing both shapes.
    figure_kind: str


# The three phrases `exposure_block.py` writes when the resolver produced
# nothing. WRITER AND READER MUST AGREE: the renderer drops a line by recognising
# these phrases, so rewording a value here prints it to the reader as a finding.
# A read-only view, not a dict -- two modules import it, and `Final` stops
# rebinding but not `EXPOSURE_PLACEHOLDERS[k] = v`.
EXPOSURE_PLACEHOLDERS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "path_denominator": "not established",
        "component_denominator": "not established for this problem",
        "note": "No figure was resolved for this one.",
    }
)


@dataclass(frozen=True, slots=True)
class Exposure:
    basis: str
    path_denominator: str
    component_denominator: str
    note: str
    # The reconciler's verdict on the figure it was handed -- see
    # `_FIGURE_DISPOSITION_VALUES`. Null exactly when no reconciler saw this
    # finding, which is `DEFERRED_UNVERIFIED` and nothing else.
    figure_disposition: str | None = None
    # Optional, and optional permanently. Most findings on a real run have no
    # numerator to divide, and forcing a figure there is what produces the
    # fabricated 100% above. At most one of `share` and `share_absent` carries a
    # value; both being None is how a record written before this field existed
    # still renders, and is read as NOT_QUERIED.
    share: "Share | None" = None
    share_absent: str | None = None
    # The finding-specific sentence, when the producer has one. The reason code
    # only selects a generic sentence; this replaces it. Short because it renders
    # in a narrow column, and optional because the generic sentence is honest on
    # its own.
    share_absent_detail: str | None = None


@dataclass(frozen=True, slots=True)
class AxisTrail:
    verdict: str
    trail: str


@dataclass(frozen=True, slots=True)
class Verification:
    metric_query: str
    reads_today: str
    expected_after: str
    expectation_basis: str
    artifact_form: str


@dataclass(frozen=True, slots=True)
class Provenance:
    """The commit that last wrote the finding's line, and its pull request.

    Written by `resolve_provenance.py`, never by hand and never by an agent: it
    is a mechanical fact about the checkout, and the same reasoning that keeps
    `permalink` out of an agent's hands applies unchanged.

    There is no author field and there is not going to be one.
    `run-record.md` has why.
    """

    commit: str
    commit_short: str
    commit_url: str
    date: str | None
    pull_request: dict | None


@dataclass(frozen=True, slots=True)
class Method:
    """What was actually done to check one finding, as opposed to what it found.

    This exists because a reader asked, on seeing the report presented, whether
    the checking had included re-running the code at the commit before the
    change. That question has a real answer per finding and the report was
    throwing it away.

    Both fields are honest about absence. `before_after` is null when no
    before/after re-run happened, and the digest says so in as many words --
    printing the method only when it flatters the finding would make the block
    an advertisement rather than a disclosure. `history_read` is an empty list
    when the contract check settled the question without reading history.
    """

    before_after: str | None
    history_read: list


@dataclass(frozen=True, slots=True)
class Finding:
    fingerprint: str
    state: FindingState
    verdict: Verdict
    band: Band | None
    band_reason: str | None
    title: str
    consequence: str
    # The harm any exposure figure on this finding answers, in the wording that
    # survived verification. Required, and required on every finding rather than
    # only the ones carrying a figure: an optional field is one a producer omits,
    # and the guard that compares it against `share.harm_hash` would then simply
    # cease to exist rather than fail. It is not rendered as a field of its own --
    # `consequence` is the reader's sentence -- it exists so a figure can be
    # bound to a question.
    harm_statement: str
    observed_symptom: str
    observed_full: str | None
    defect_site: str
    component: str
    tier: str
    exposure: Exposure
    effort: str
    mechanism: AxisTrail
    intent: AxisTrail
    fix_prompt: str | None
    verification: Verification | None
    provenance: Provenance | None
    method: Method | None
    permalink: str | None
    # Derived in _build_finding from permalink_resolution.unlinked, never an
    # input field. The renderer states the recorded reason a finding has no
    # link; before this existed it printed one hardcoded cause instead, and on
    # the measured run that cause was false for all 64 findings.
    permalink_unlinked_reason: str | None
    # Derived the same way from provenance_resolution.unresolved, and present for
    # the same reason: the digest must state the recorded cause rather than
    # inventing one, and a record written before this stage existed has neither.
    provenance_unresolved_reason: str | None
    symptom_collapsed: bool


@dataclass(frozen=True, slots=True)
class RenderModel:
    """What normalise() returns and render_digest.py consumes.

    `grouped` always carries all four Band keys, empty lists included, so an
    empty band cannot silently vanish from the digest. `discarded` is separate
    because a discarded candidate has no band: SKILL.md section 6 assigns a
    threat level only to non-discarded dispositions.

    The run-level fields after `discarded` exist for the empty-run rule: a run finding nothing
    still has to prove what it searched, and coverage, the degraded-path sweep,
    dead surface and cost are that proof. An earlier draft of this contract named
    only the first four fields, which could not have rendered the empty state.
    """

    run_id: str
    scope_label: str
    components: list
    grouped: dict[Band, list[Finding]]
    discarded: list[Finding]
    coverage: list[dict]
    degraded_paths: list[dict]
    dead_surface: list[dict]
    cost: dict
    shortfall: dict | None
    gate: dict
    repo: dict | None


def _text(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return "must be a non-empty string"
    return None


def _optional_text(value: object) -> str | None:
    return None if value is None else _text(value)


def _fingerprint(value: object) -> str | None:
    if not isinstance(value, str) or not _FINGERPRINT.fullmatch(value):
        return "must match ^[0-9a-f]{16}$ (lowercase hex, exactly 16 chars)"
    return None


def _permalink(value: object) -> str | None:
    """A verified source link, or None when the orchestrator could not verify one.

    None is a legitimate and expected value, not a degraded one: the orchestrator
    emits a permalink only after confirming the file at the pinned ref is
    byte-identical to the checkout the finder actually read. A file that differs
    -- an unpushed branch, a local edit -- gets None, and the digest shows the
    path as plain text rather than a link that would point at the wrong line.
    """
    if value is None:
        return None
    if not isinstance(value, str) or not _PERMALINK.fullmatch(value):
        return (
            "must be null, or an https URL pinned to a 40-char commit SHA "
            "ending in #L<line> (branch-ref links are rejected because their "
            "line numbers drift away from the finding)"
        )
    return None


def _observed_symptom(value: object) -> str | None:
    """The one line of evidence on the always-visible row.

    The message below states the SEMANTIC rule and not merely the bound, because
    an author told only "make it shorter" truncates the stack trace they already
    had and ships exactly the defect this rejects: a fragment that breaks
    mid-token where the evidence should be. Naming what the line is FOR is what
    redirects them to `observed_full` instead of to a slice.
    """
    problem = _text(value)
    if problem:
        return problem
    assert isinstance(value, str)  # _text already proved this
    if "\n" in value or "\r" in value:
        broke = "contains a line break"
    elif len(value) > _SYMPTOM_MAX_CHARS:
        broke = (
            f"is {len(value)} characters, past the {_SYMPTOM_MAX_CHARS}-character bound"
        )
    else:
        return None
    return (
        f"{broke}. This field is the single most diagnostic line of real output "
        "-- the exception and its message, or the assertion that failed -- on "
        f"ONE line of at most {_SYMPTOM_MAX_CHARS} characters. It is NOT the "
        "opening fragment of a stack trace: slicing a trace to fit is how the "
        "measured run produced a digest where every symptom broke off mid-token. "
        "Put the complete multi-line capture in `observed_full`, which renders "
        "in the expansion where it has room, and write this line yourself"
    )


# A sentence may legitimately close on a bracket, a code span or a quotation as
# well as on a full stop, so all of them end a field cleanly. A colon, a comma or
# a bare word does not: those are the shapes a slice leaves behind.
_PROSE_ENDINGS: Final[tuple[str, ...]] = (".", "!", "?", ")", "]", "`", '"', "'")

# The prose an agent WRITES, as opposed to the output it CAPTURES. `observed_full`
# and `observed_symptom` are excluded on purpose: a stack trace or an assertion
# message ends wherever the runtime ended it, and demanding a full stop there
# would push an author into editing real evidence to satisfy a validator.
_PROSE_FIELDS: Final[frozenset[str]] = frozenset(
    {"title", "band_reason", "consequence", "fix_prompt", "trail", "note"}
)

# `reason` is deliberately absent from that set, in all three places it appears.
# `shortfall.reason` is specified as a lowercase clause completing a sentence the
# renderer supplies ("These were never looked at, because ..."), with no trailing
# full stop; the reasons in `permalink_resolution.unlinked` and
# `provenance_resolution.unresolved` are fragments for the same reason. Requiring
# terminal punctuation there would reject a correctly written field and, worse,
# push an author into breaking the rendered sentence to satisfy a validator.


def _complete_prose(value: object) -> str | None:
    """Reject a field that stops mid-sentence.

    Every rule this file enforces about prose was written down before it was
    enforced, and the ones that stayed written-down-only are the ones that got
    violated. `run-record.md` holds the measured counts from the run that
    prompted this check and is the only place they live; the short version is
    that most of one record's reader-facing prose was sliced out of another field.

    The fix prompt is where this hurts most, because it is the artifact the
    report exists to hand over: a reader who copies one that stops at
    `has no arti` has copied something that cannot be run. But the trails matter
    for the same reason in a quieter way -- a sentence of evidence that breaks
    off is evidence a reader cannot check.

    This is deliberately a block rather than a warning. A warning about prose is
    a rule that is still only written down.
    """
    if not isinstance(value, str) or not value.strip():
        return None  # emptiness is _text's job, and reporting it twice is noise
    text = value.rstrip()
    if text.endswith(_PROSE_ENDINGS):
        return None
    tail = text[-40:]
    return (
        f"stops mid-sentence, ending {tail!r}. This field is read by a person, "
        "and the fix prompt in particular is copied and run, so it must be a "
        "complete thought that ends in punctuation. Do NOT satisfy this by "
        "appending a full stop to a slice: the usual cause is building the field "
        'as `f"...{other_field[:300]}"`, and the fix is to write the field as '
        "its own sentence rather than to paste a truncated copy of another one"
    )


def _permalink_resolution(value: object) -> str | None:
    """Proof that link resolution was ATTEMPTED, separate from its outcome.

    A null permalink is legitimate -- see `_permalink`. But "nobody attempted
    resolution" and "attempted, and the file did not match" are both spelled
    `null` on the finding, and until this field existed the schema could not
    tell them apart. Measured: a run emitted `null` for all 64 findings with the
    check never run, validation passed, and the digest asserted a specific cause
    nobody had established -- one that was false for every one of them.

    `attempted` is cross-checked against the findings count in
    `validate_run_record`, so a record cannot claim a clean resolution pass over
    findings it never looked at.
    """
    required = ("attempted", "linked", "unlinked")
    if not isinstance(value, dict):
        return f"must be an object with keys {list(required)}"
    missing = [key for key in required if key not in value]
    if missing:
        return f"is missing {missing}"
    for key in ("attempted", "linked"):
        count = value[key]
        # bool is an int subclass, and `"attempted": true` is exactly the kind
        # of stand-in a producer reaches for when it has no real count.
        if isinstance(count, bool) or not isinstance(count, int):
            return f"{key} must be an integer"
    return _objects_with(("fingerprint", "reason"))(value["unlinked"])


def _state(value: object) -> str | None:
    if not isinstance(value, str) or value not in FindingState.__members__:
        return f"must be one of {sorted(FindingState.__members__)}"
    return None


def _band_reason(value: object) -> str | None:
    """The one sentence naming what decided the band. Null only where no band.

    The rubric has required this sentence since bands existed
    (`references/verdicts-and-bands.md` section 4) and there was
    no field for it, so what reached a reader was per-band boilerplate identical
    for every finding in the group -- "Ordered only where the order can be
    justified in writing." on every top-band row alike.

    It stopped being cosmetic on 2026-08-28. A finding demoted to `Low` on a
    measured dormancy has to disclose the capability it still has, or the
    demotion hides a real defect behind a reassuring word, and a bare band cannot
    carry that. The cross-check in `validate_run_record` is what makes it a
    requirement rather than an aspiration.
    """
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return "must be a non-empty sentence, or null where the finding has no band"
    return None


def _band(value: object) -> str | None:
    if value is None:
        return None
    allowed = [b.value for b in Band]
    if value not in allowed:
        return f"must be null or one of {allowed}"
    return None


def _effort(value: object) -> str | None:
    if value not in _EFFORTS:
        return "must be one of ['S', 'M', 'L']"
    return None


def _tier(value: object) -> str | None:
    if value not in _TIERS:
        return (
            "must be one of ['1', '2', '3', '4', 'UNTIERED'] -- 'UNTIERED' is the "
            "ABSENCE of a tier and is never folded into Tier 4. Use the bare "
            "value, not 'Tier 2'; the renderer formats it for display"
        )
    return None


def _list_of_objects(value: object) -> str | None:
    if not isinstance(value, list) or any(not isinstance(i, dict) for i in value):
        return "must be a list of objects"
    return None


def _coverage_entries(value: object) -> str | None:
    """Coverage entries, whose `files` must be the file NAMES, not a count.

    It was a count. The digest could then say how many files were searched but
    never WHICH, and the one question a service owner brings to this section is
    "was the file I am worried about searched?" -- which a count cannot answer,
    and which is the only way to tell a searched-and-clean result from a file
    nobody looked at. Recording the names also forces the orchestrator to know
    what it actually covered rather than asserting a total.
    """
    if not isinstance(value, list) or not value:
        return "must be a non-empty list of objects"
    for i, entry in enumerate(value):
        if not isinstance(entry, dict):
            return f"[{i}] must be an object"
        missing = [
            k
            for k in ("component", "mandate", "files", "lines", "packets_returned")
            if k not in entry
        ]
        if missing:
            return f"[{i}] is missing {missing}"
        files = entry["files"]
        if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
            return (
                f"[{i}].files must be the list of file paths searched, not a "
                "count -- the report answers 'was my file searched?' by name"
            )
    return None


def _objects_with(required: tuple[str, ...]) -> Callable[[object], str | None]:
    """A list of objects, each carrying a fixed key set.

    Validating only the outer shape was not enough. `render_digest.py` indexes
    these inner keys directly, and `render()` is called outside `main()`'s
    try/except -- so a record missing one produced an uncaught traceback with
    empty stdout rather than the clean INVALID naming the field that every other
    validation failure produces. Found by an eval agent reading the two scripts
    against each other, not by the test suite.
    """

    def check(value: object) -> str | None:
        shape = _list_of_objects(value)
        if shape:
            return shape
        for index, item in enumerate(value):
            missing = [key for key in required if key not in item]
            if missing:
                return f"[{index}] is missing {missing}"
        return None

    return check


def component_name(entry: object) -> str:
    """A component's name, or "" when it has none. NEVER a repr.

    Both real shapes resolve here: a bare `"character-pro"` and a
    `{"name": ..., "tier": ...}`. `"id"` is not a third -- no producer writes it.
    """
    if isinstance(entry, str):
        return entry.strip()
    if isinstance(entry, dict) and isinstance(entry.get("name"), str):
        return entry["name"].strip()
    return ""


# SKILL.md section 8's ceiling, and the ONLY number of candidates a run is
# allowed to stop short at. Named here because the gate below does arithmetic
# with it: a run claiming it hit the ceiling while verifying fewer than this
# did not hit the ceiling, it stopped for something else.
_VERIFICATION_CEILING: Final[int] = 20

# The closed set of legitimate reasons a run verified fewer candidates than it
# selected. ELAPSED TIME IS NOT IN IT AND MUST NOT BE ADDED: a run that judges
# itself short of time has no value to write and must keep going.
#
# A THIRD VALUE FOR "stopped from outside" WAS CONSIDERED AND REFUSED. `CEILING`
# is held honest by arithmetic and `ENDED_EXTERNALLY` by `selected`; a new value
# would be checkable by nothing, which makes it the easiest thing to reach for
# and hands back the banned excuse under a new name. Glosses live in
# `references/run-record.md`; a second copy here would drift unrendered.
_ENDED_EXTERNALLY: Final[str] = "ENDED_EXTERNALLY"
_SHORTFALL_CAUSE_VALUES: Final[tuple[str, ...]] = ("CEILING", _ENDED_EXTERNALLY)

# `reason` and `cause` are both REQUIRED. `selected` is required only alongside
# `ENDED_EXTERNALLY` -- that pairing is in `_selected_errors`, because it needs
# the findings count.
_SHORTFALL_KEYS: Final[tuple[str, ...]] = ("reason", "cause")


def _attempted_mismatch(field: str, attempted: int, found: int, why: str) -> ValidationError:
    """A resolution counter disagreeing with the findings array. WHICH WAY matters.

    OVER-COUNT is the laundering shape: a stage saw candidates that are now absent
    from the record, so the repair is the findings and never the counter -- trimming
    it lands on a record that renders a truncated run as a complete one.

    UNDER-COUNT is a stage that did not run: `{attempted: 0}` beside 64 findings is
    the shape this check was written for, and there the counter is not the lie, the
    skipped work is. A single message for both directions gets one of them wrong --
    it printed "-64 candidate(s)" and told a producer to LOWER `attempted`, when
    the repair here raises it.
    """
    if attempted > found:
        return ValidationError(
            field,
            f"is {attempted} but the record carries only {found} finding(s). "
            "**The repair is the missing findings, not this number.** A stage "
            f"attempted {attempted}, so {attempted - found} candidate(s) it saw are "
            "absent from `findings`: write them in, every unstarted one as "
            '`DEFERRED_UNVERIFIED` with `band: "Not triaged"`, and state a '
            f"`shortfall`. Lowering `attempted` to {found} also silences this, and "
            f"lands on a record that renders a truncated run as a complete one. {why}",
        )
    return ValidationError(
        field,
        f"is {attempted} but the record carries {found} finding(s), so "
        f"{found - attempted} were never attempted. **The repair is the skipped "
        "work, not the number**: run the stage over every finding and let the "
        f"count follow. Raising `attempted` to {found} on its own reports work "
        f"nobody did. {why}",
    )


def _shortfall(value: object) -> str | None:
    """The shortfall object, and the closed vocabulary of its `cause`.

    The VALUE check lives here beside the shape check: a vocabulary policed only
    from a cross-field rule is not closed. Measured with the check inside that rule instead -- a
    record carrying `cause: "WALL_CLOCK"` and no unchecked finding validated
    clean, which is the one value this whole mechanism exists to make unwritable.
    """
    shape = _optional_mapping(_SHORTFALL_KEYS)(value)
    if shape is not None or value is None:
        return shape
    cause = value["cause"]  # type: ignore[index]
    if cause not in _SHORTFALL_CAUSE_VALUES:
        return (
            f"cause must be one of {list(_SHORTFALL_CAUSE_VALUES)}, not {cause!r}. "
            "Elapsed time and agent count are not stopping conditions and have no "
            "value here: run every selected candidate through every stage, however "
            "long that takes"
        )
    selected = value.get("selected")  # type: ignore[union-attr]
    if selected is not None and (not _is_count(selected) or selected < 0):
        return (
            f"selected must be a non-negative integer, not {selected!r}. It is how "
            "many candidates went to verification -- the bound's fill AND the "
            "controls, which is what `to_verify` holds"
        )
    return None


def _ceiling_claim_errors(shortfall: object, verified: int) -> list[ValidationError]:
    """`CEILING` is an arithmetic claim, not a label.

    The bound fills to `_VERIFICATION_CEILING`, so a run that hit it verified at
    least that many. This needs the findings list, which is why it cannot live in
    `_shortfall`: moved there for tidiness, it stops being able to count.
    """
    cause = shortfall.get("cause") if isinstance(shortfall, dict) else None
    if cause == "CEILING" and verified < _VERIFICATION_CEILING:
        return [
            ValidationError(
                "shortfall.cause",
                f"claims {cause}, but only {verified} candidate(s) completed the "
                f"pipeline "
                f"and the ceiling fills to {_VERIFICATION_CEILING}; a run that "
                "stopped below it did not reach the bound. Finish the selected "
                f"candidates, or say {_ENDED_EXTERNALLY} if the run was ended "
                "rather than choosing to stop",
            )
        ]
    return []


def _selected_errors(
    shortfall: object, verified: int, total: int
) -> list[ValidationError]:
    """The arithmetic that holds `ENDED_EXTERNALLY`, and which half `CEILING` skips.

    **Controls are IN `selected`.** It is the band fill PLUS the controls, and
    `verified` here counts every finding that is not
    `DEFERRED_UNVERIFIED`, controls included. Count them on one side only and the
    gap is under-reported, rejecting an honest record at the boundary.

    - `verified < selected`, exempt only at `0` from `0` -- never on `selected: 0`
      alone, which accepts a run that picked nothing and then completed candidates.
    - `selected <= total` -- it cannot have picked what the record does not carry.

    ONLY THE FIRST IS `CEILING`-EXEMPT -- a run that filled its bound has no gap of
    that kind. The second sits ABOVE the cause gate deliberately and fires whatever
    the cause: a count larger than the record is incoherent whoever wrote it.
    """
    if not isinstance(shortfall, dict):
        return []
    selected = shortfall.get("selected")
    if selected is not None and selected > total:
        return [
            ValidationError(
                "shortfall.selected",
                f"is {selected} but the record carries {total} finding(s); the "
                "bound cannot have picked candidates the record does not carry. "
                "**The repair is the missing findings, not this number**: write "
                f"the {selected - total} absent one(s) in, every unstarted one as "
                '`DEFERRED_UNVERIFIED` with `band: "Not triaged"`. Lowering '
                f"`selected` to {total} also silences this, and lands on a record "
                "that renders a truncated run as a complete one",
            )
        ]
    if shortfall.get("cause") != _ENDED_EXTERNALLY:
        return []
    if selected is None:
        return [
            ValidationError(
                "shortfall.selected",
                f"is required with `{_ENDED_EXTERNALLY}`: state how many "
                "candidates went to verification, controls included, so the "
                "digest can say how many of "
                "them were never started. Without it the record says a run was "
                "ended and gives the reader no way to see by how much it fell "
                "short -- and the claim carries no arithmetic consequence",
            )
        ]
    # THE EXEMPTION IS `0 AND 0`, NOT `selected == 0`. A run ended during the
    # search selected nothing, so `selected: 0` is its honest record. Exempting
    # on `selected` alone accepted `selected: 0` beside candidates that DID
    # complete -- the bound picked nothing and then verified three of them.
    if selected == 0 and verified == 0:
        return []
    if verified >= selected:
        return [
            ValidationError(
                "shortfall.selected",
                f"is {selected} and {verified} candidate(s) completed the "
                f"pipeline, so every selected candidate was finished and "
                f"`{_ENDED_EXTERNALLY}` claims a gap that is not there. Say "
                "`CEILING` if the bound is what left the rest unchecked",
            )
        ]
    return []


def _components(value: object) -> str | None:
    """Every entry must be nameable, because the `<h1>` is one of these names.

    This checked only that the list was non-empty, leaving the ELEMENT shape
    unchecked, so the 2026-09-12 run's `{"name": ...}` met a renderer looking up
    `"id"` and `str(dict)` put a Python repr in the heading. Refusing it here is
    what makes the renderer's fallback unreachable rather than merely unlikely.
    """
    if not isinstance(value, list) or not value:
        return "must be a non-empty list"
    for index, entry in enumerate(value):
        if not component_name(entry):
            return (
                f"[{index}] cannot be named: every entry must be a non-empty "
                "string, or an object carrying a non-empty 'name'"
            )
    return None


def _any_list(value: object) -> str | None:
    """A run that found nothing is valid, so an empty findings list is allowed.

    The empty-run rule: a clean component and an unsearched one must not look alike, which
    means zero findings has to reach the renderer rather than being rejected here.
    """
    return None if isinstance(value, list) else "must be a list"


def _mapping(required: tuple[str, ...]) -> Callable[[object], str | None]:
    """Build a validator for a nested object with a fixed key set."""

    def check(value: object) -> str | None:
        if not isinstance(value, dict):
            return f"must be an object with keys {list(required)}"
        missing = [key for key in required if key not in value]
        return f"is missing {missing}" if missing else None

    return check


def _optional_mapping(required: tuple[str, ...]) -> Callable[[object], str | None]:
    inner = _mapping(required)
    return lambda value: None if value is None else inner(value)


# `figure_disposition` is a required KEY carrying a legitimately null VALUE,
# which is the rule `method` already follows. An optional key is one a producer
# leaves out, and this one decides what the column claims: left out, it would
# restore exactly the silence the fingerprint allowlist created, and the check
# below would pass by having nothing to check.
#
# `figure_kind` is NOT here -- it lives inside `share`, because it describes a
# figure. That placement is what makes "a kind with no figure" and "a figure with
# no kind" unrepresentable rather than rejected, and it deleted a two-directional
# validator and two paragraphs of error prose.
_EXPOSURE_KEYS = (
    "basis",
    "path_denominator",
    "component_denominator",
    "note",
    "figure_disposition",
)

# Provenance, not magnitude. `UNKNOWN` is the legitimate value for a candidate the
# impact stage attempted and could not resolve -- which is the majority case on a
# real component, so it must be nameable rather than improvised.
_BASIS_VALUES: Final[tuple[str, ...]] = ("MEASURED", "ESTIMATED", "UNKNOWN")


def _exposure(value: object) -> str | None:
    """The exposure object, including the one field whose value carries meaning.

    `_mapping` checks that keys are present and never what they hold, so `basis`
    accepted any string at all. Measured: an agent given a two-value vocabulary
    and a requirement that needed a third invented `UNRESOLVED`, applied it to 15
    of 26 candidates, and the record validated -- the majority of one run's
    provenance labels were a value the schema does not define. A provenance label
    nobody constrains is not provenance.
    """
    shape = _mapping(_EXPOSURE_KEYS)(value)
    if shape is not None:
        return shape
    basis = value["basis"]  # type: ignore[index]
    if basis not in _BASIS_VALUES:
        return (
            f"basis must be one of {list(_BASIS_VALUES)}, not {basis!r}. "
            "Use UNKNOWN for a candidate the impact stage attempted and could "
            "not resolve; do not invent a fourth value"
        )
    share, absent = value.get("share"), value.get("share_absent")  # type: ignore[union-attr]
    if share is not None and absent is not None:
        return (
            "carries both share and share_absent. At most one can be true: a "
            "measured share and a named reason for having none are mutually "
            "exclusive claims about the same quantity"
        )
    if share is not None:
        if basis == "UNKNOWN":
            return (
                "has basis UNKNOWN and also a share. UNKNOWN means no numerator "
                "was established, so there is nothing to divide. This is the "
                "shape a reused component figure takes: put the population in "
                "the numerator's slot and it renders a 100% nobody measured, on "
                "a finding nobody checked"
            )
        problem = _share_object(share)
        if problem is not None:
            return f"share {problem}"
    if absent is not None and absent not in _SHARE_ABSENT_VALUES:
        return (
            f"share_absent must be one of {list(_SHARE_ABSENT_VALUES)}, not "
            f"{absent!r}. The three are not interchangeable for a reader setting "
            "priority, so do not invent a fourth"
        )
    detail = value.get("share_absent_detail")  # type: ignore[union-attr]
    if detail is not None:
        if not isinstance(detail, str) or not detail.strip():
            return "share_absent_detail must be a non-empty string when present"
        if absent is None:
            return (
                "carries share_absent_detail with no share_absent for it to "
                "qualify; the detail replaces a generic sentence chosen by the "
                "reason code, so without the code there is nothing to replace"
            )
        if len(detail.strip()) > _SHARE_DETAIL_MAX_CHARS:
            return (
                f"share_absent_detail is {len(detail.strip())} characters; "
                f"{_SHARE_DETAIL_MAX_CHARS} is what the column fits without "
                "pushing the finding text out of its own column"
            )
    return _figure_disposition(value.get("figure_disposition"))  # type: ignore[union-attr]


def _figure_disposition(value: object) -> str | None:
    """The reconciler's verdict on the figure, checked against a closed set.

    Null is legitimate and means no reconciler saw this finding;
    `validate_run_record` is what ties null to `DEFERRED_UNVERIFIED` and nothing
    else, because only the record knows the finding's state.
    """
    if value is None:
        return None
    if value not in _FIGURE_DISPOSITION_VALUES:
        return (
            f"figure_disposition must be null or one of "
            f"{list(_FIGURE_DISPOSITION_VALUES)}, not {value!r}. This replaced a "
            "run-scoped allowlist of literal fingerprints and a substring match "
            "on reconciler prose, both of which decided the column silently"
        )
    return None


def _harm_statement(value: object) -> str | None:
    """The harm a figure on this finding answers, as one sentence.

    Both bounds are loose because their job is to refuse a placeholder and a
    pasted evidence trail, not to police wording. What actually constrains this
    field is the hash comparison in `validate_run_record`: change a word here
    after a figure was computed and the record is refused.
    """
    if not isinstance(value, str) or not value.strip():
        return (
            "must be one sentence naming the harm any exposure figure on this "
            "finding is a share of -- the wording that survived verification, not "
            "the finder's original where a reconciler corrected it"
        )
    text = value.strip()
    if len(text) < _HARM_STATEMENT_MIN_CHARS:
        return (
            f"is {len(text)} characters, which is too short to be a harm "
            f"statement ({_HARM_STATEMENT_MIN_CHARS} minimum). A share computed "
            "against a placeholder is a share of nothing"
        )
    if len(text) > _HARM_STATEMENT_MAX_CHARS:
        return (
            f"is {len(text)} characters; {_HARM_STATEMENT_MAX_CHARS} is the "
            "bound. This is the sentence a figure divides, not an evidence "
            "trail -- the trails have their own fields"
        )
    return None


_AXIS_KEYS = ("verdict", "trail")


def _share_object(value: object) -> str | None:
    """The keys in `_SHARE_KEYS`, and the arithmetic and units between them.

    Every rule here refuses a specific figure that a real run produced or that a
    prose-parsing renderer would have produced from one.
    """
    shape = _mapping(_SHARE_KEYS)(value)
    if shape is not None:
        return shape
    numerator, denominator = value["numerator"], value["denominator"]  # type: ignore[index]
    for name, figure in (("numerator", numerator), ("denominator", denominator)):
        if isinstance(figure, bool) or not isinstance(figure, (int, float)):
            return f"{name} must be a number, not {type(figure).__name__}"
        if figure < 0:
            return f"{name} is {figure}; neither side of a share is negative"
    if denominator == 0:
        return (
            "denominator is 0, so there is no population to be a share of. That "
            "is not a share of zero, it is the absence of a denominator -- use "
            "share_absent with NOT_REQUEST_SCOPED"
        )
    if numerator > denominator:
        return (
            f"numerator {numerator} exceeds denominator {denominator}. A share "
            "cannot be larger than the population it is a share of, and this is "
            "the shape a reused component figure takes when it lands in the "
            "numerator's slot"
        )
    unit = value["unit"]  # type: ignore[index]
    if not isinstance(unit, str) or not unit.strip():
        return (
            "unit must be a non-empty string. It is ONE field covering both "
            "sides on purpose: a shared unit is the only proof the two figures "
            "are commensurable, and it is what makes 'N metric series of M "
            "grpc pairs' impossible to write rather than merely discouraged"
        )
    if len(unit.strip()) > _SHARE_UNIT_MAX_CHARS:
        return (
            f"unit is {len(unit.strip())} characters; {_SHARE_UNIT_MAX_CHARS} is "
            "the bound because it renders inline between two figures. 'req/s' "
            "and 'items/s' are the shape; a sentence belongs in note"
        )
    of = value["of"]  # type: ignore[index]
    if not isinstance(of, str) or not of.strip():
        return (
            "of must complete the phrase '<numerator> of <denominator> <unit> "
            "___', for example 'reaching this component'. The renderer cannot "
            "supply it, for the same reason path_denominator carries its own "
            "noun: 63,000 counts searches in one service and items in the next"
        )
    if len(of.strip()) > _SHARE_OF_MAX_CHARS:
        return (
            f"of is {len(of.strip())} characters; {_SHARE_OF_MAX_CHARS} is what "
            "the column fits. Put the rest in note"
        )
    kind = value["figure_kind"]  # type: ignore[index]
    if kind not in _FIGURE_KIND_VALUES:
        return (
            f"figure_kind must be one of {list(_FIGURE_KIND_VALUES)}, not "
            f"{kind!r}. HARM_SHARE is the share of the population the confirmed "
            "harm damages; PATH_EXPOSURE is how much traffic reaches the "
            "defective code, which is an upper bound on the harm rather than a "
            "measurement of it. `run-record.md` has what rendering both "
            "as a bare percentage cost a reader"
        )
    bound = value["harm_hash"]  # type: ignore[index]
    if not isinstance(bound, str) or not _HARM_HASH.fullmatch(bound):
        return (
            "harm_hash must be the 16-character hex identity of the harm "
            "statement this figure was computed against, as produced by "
            "digest_model.harm_hash(). It is what stops a figure outliving the "
            "question it answers: the pipeline exists to CORRECT the harm "
            "statement, and until this field existed nothing recorded which "
            "wording a percentage was a share of"
        )
    return None


# Sixteen hex characters, which is a root-cause fingerprint's shape too -- so a
# producer that pastes the wrong id is caught by the comparison in
# `validate_run_record` rather than by this format check. A hash that merely
# LOOKS right is the case this field has to survive.
_HARM_HASH = _FINGERPRINT


def _path_denominator(value: object) -> str | None:
    """`X% of <what>`, or prose saying it was not established.

    A figure with no noun after it is the failure this rejects. The renderer
    cannot supply the noun -- a percentage is a share of searches in one service
    and of something else in the next -- so a bare `0.072%` reaches the reader as
    a number of nothing. Measured: it did, next to a Read-closely finding, and the
    first-time reader who met it named this column as the part of the report they
    could not understand.

    Prose with no figure is fine and is the common case: "not measured -- the
    share of the path this sits on was not queried" is a complete answer, and the
    renderer shows it as "not measured" with no provenance word attached.
    """
    if not isinstance(value, str) or not value.strip():
        return "must be a non-empty string"
    text = value.strip()
    if len(text) > _DENOMINATOR_MAX_CHARS:
        return (
            f"is {len(text)} characters; the exposure column shows at most "
            f"{_DENOMINATOR_MAX_CHARS} without crowding the finding text. Put the "
            "detail in exposure.note, which renders in the expansion"
        )
    figure = _EXPOSURE_FIGURE.match(text)
    if figure and " of " not in text:
        return (
            f"leads with {figure.group(0)!r} but never says what that is a share "
            "OF. Write it as 'X% of <the path or page this sits on>' -- the "
            "renderer cannot supply the noun, because the same figure means a "
            "different thing in every service"
        )
    return None


_VERIFICATION_KEYS = (
    "metric_query",
    "reads_today",
    "expected_after",
    "expectation_basis",
    "artifact_form",
)

_PROVENANCE_KEYS = ("commit", "commit_short", "commit_url", "date", "pull_request")
_METHOD_KEYS = ("before_after", "history_read")


def _provenance_resolution(value: object) -> str | None:
    """Proof that commit tracing was ATTEMPTED, separate from its outcome.

    Required rather than optional, for the reason `_permalink_resolution` records
    at length: a field that may be omitted is one an orchestrator omits, and a
    record with no commit lines then looks the same whether the history was
    unreadable or nobody ran the stage. `resolve_provenance.py` writes this
    block, so satisfying it is a pipeline step rather than an authoring task.
    """
    required = ("attempted", "resolved", "unresolved")
    if not isinstance(value, dict):
        return (
            f"must be an object with keys {list(required)}, written by "
            "resolve_provenance.py; run it between resolve_permalinks.py and "
            "this script rather than filling the block in by hand"
        )
    missing = [key for key in required if key not in value]
    if missing:
        return f"is missing {missing}"
    if not isinstance(value["unresolved"], list):
        return "unresolved must be a list of {fingerprint, reason} objects"
    return _objects_with(("fingerprint", "reason"))(value["unresolved"])


#: Values an orchestrator would plausibly write into `resolver_agent_id` when it
#: did the resolver's work itself. Not exhaustive and not meant to be: it closes the
#: honest-shorthand case, where an orchestrator records what it actually did without
#: intending to deceive. A fabricated agent id is a different act and is not
#: something a schema can catch.
_NOT_A_RESOLVER = frozenset(
    {
        # Names an orchestrator would honestly write having done the work itself.
        "orchestrator",
        "self",
        "main",
        "n/a",
        "na",
        "none",
        "null",
        "-",
        "unknown",
        # Placeholders. Added 2026-08-29 after a real run wrote
        # `"resolver_agent_id": "PLACEHOLDER"` into its run-record template while
        # assembling the record in stages. That is not a lie told to cover a bypass;
        # it is what an honest run leaves behind and forgets to replace. It validated
        # clean, which is the worse outcome: the field exists to prove an independent
        # agent ran, and a placeholder proves nothing while looking like it does.
        "placeholder",
        "tbd",
        "todo",
        "xxx",
        "fixme",
        "example",
        "changeme",
        "<agent-id>",
        "agent-id",
        "agent_id",
        "your-agent-id",
        "id",
    }
)


def _exposure_resolution(value: object) -> str | None:
    """Proof that the impact lookup was ATTEMPTED, separate from its outcome.

    `references/verdicts-and-bands.md` states that `UNKNOWN`
    exposure "is legitimate only after a query was actually attempted and either
    failed or found no instrumentation", and until this block existed nothing
    stood behind that sentence: "queried, and there is no instrumentation" and
    "nobody queried" produced the identical empty cell.

    Measured on two runs across two components: the column was almost entirely an
    absence while a substantial minority of those findings had already named the
    metric that would settle it and were banded most-urgent anyway. The verbatim case
    and the counts are canonical in
    # Measured across two runs on two components: 7 of 26 checked findings named a metric artifact in their own packet, 6 of those cited it with a file and line, and 0 were resolved - while 9 were banded most-urgent with no impact figure behind them.

    `attempted` is cross-checked against the findings count in
    `validate_run_record`, so a record cannot claim a clean impact pass over
    findings nobody looked at.
    """
    required = ("attempted", "resolved", "unresolved", "resolver_agent_id")
    if not isinstance(value, dict):
        return (
            f"must be an object with keys {list(required)}, written by the "
            "impact-resolution stage from the candidate list it was handed -- "
            "never from a counter, which can be incremented zero times by a "
            "loop that never ran"
        )
    missing = [key for key in required if key not in value]
    if missing:
        return f"is missing {missing}"

    # `resolver_agent_id` names the agent that produced these figures.
    #
    # Measured 2026-08-28: an orchestrator holding metric tools from STEP 0's
    # pre-flight decided to query the metrics ITSELF rather than dispatch the
    # resolver, reasoning that a named subagent might drop its output. It obtained
    # real production figures. The run would have scored its headline criterion
    # ("resolved > 0") as PASS for a stage that never executed, and the resulting
    # document was internally consistent and cited live metrics. A human reading
    # the pane is the only thing that caught it.
    #
    # This cannot make the bypass impossible -- an orchestrator can invent an id.
    # It converts a silent shortcut into a deliberate false statement, and it makes
    # the omission detectable by a script rather than by whoever happens to watch.
    # resolver_agent_id accepts a single string OR a list of strings (for chunked
    # dispatch where multiple resolver agents each handle ~30 candidates).
    raw_id = value["resolver_agent_id"]
    agent_ids: list[str] = []
    if isinstance(raw_id, str):
        agent_ids = [raw_id]
    elif isinstance(raw_id, list):
        agent_ids = raw_id
    else:
        return (
            "resolver_agent_id must be a non-empty string or list of strings "
            "identifying the agent(s) that produced these figures"
        )
    if not agent_ids:
        return (
            "resolver_agent_id must contain at least one agent id; an empty "
            "value passes a presence check while carrying no information"
        )
    for agent_id in agent_ids:
        if not isinstance(agent_id, str) or not agent_id.strip():
            return (
                "resolver_agent_id must be non-empty id(s) of the agent(s) that "
                "produced these figures; an empty value passes a presence check "
                "while carrying no information"
            )
        if agent_id.strip().lower() in _NOT_A_RESOLVER:
            return (
                f"resolver_agent_id contains {agent_id!r}, which names the "
                "orchestrator rather than a resolver agent. What this block "
                "certifies is that an INDEPENDENT stage did the lookup; figures "
                "the orchestrator gathered itself prove only that its own session "
                "can reach the metric tools, which STEP 0 already established"
            )

    for key in ("attempted", "resolved"):
        count = value[key]
        # bool is an int subclass, and `"attempted": true` is exactly the
        # stand-in a producer reaches for when it has no real count.
        if isinstance(count, bool) or not isinstance(count, int):
            return f"{key} must be an integer"
    if not isinstance(value["unresolved"], list):
        return "unresolved must be a list of {fingerprint, reason} objects"
    problem = _objects_with(("fingerprint", "reason"))(value["unresolved"])
    if problem is not None:
        return problem
    return _accounts_for(value, "resolved", "unresolved") or _resolved_fingerprints(
        value
    )


def _accounts_for(block: dict, ok_key: str, list_key: str) -> str | None:
    """Every attempt ends in a result or a named reason, on all four blocks.

    `{attempted: 26, resolved: 0, unresolved: []}` is the shape a stage takes
    when it silently did nothing, and three of the four resolution blocks
    rejected it with the same inline arithmetic written three times. The fourth
    -- `reresolution` -- had no guard at all until this became one function,
    which is the usual cost of a copied check: the copy that never got made.
    """
    attempted, ok, unresolved = (
        block.get("attempted"),
        block.get(ok_key),
        block.get(list_key),
    )
    if not (_is_count(attempted) and _is_count(ok) and isinstance(unresolved, list)):
        return None  # shape errors are the per-key checks' job, not this one
    if ok + len(unresolved) != attempted:
        return (
            f"attempted {attempted} but accounts for {ok + len(unresolved)} "
            f"({ok} {ok_key} + {len(unresolved)} {list_key}); every attempt must "
            "end in a figure or a named reason"
        )
    return None


def _resolved_fingerprints(value: dict) -> str | None:
    """Which candidates the resolver actually produced a conforming share for.

    The counts alone cannot answer the question a reader has. `resolved` counts
    a candidate that came back with a named `share_absent` too, so a record can
    report 83 resolved and still render an empty column without contradicting
    itself -- which is what one run did, having deleted 27 real figures between
    the resolver and the record. This list is what makes the check
    per-candidate instead of a smoke test over the whole run.
    """
    listed = value.get("resolved_fingerprints")
    if not isinstance(listed, list) or any(_fingerprint(fp) for fp in listed):
        return (
            "resolved_fingerprints must be the list of root-cause fingerprints "
            "the resolver returned a CONFORMING four-key share for -- an empty "
            "list where it returned none. It is required because `resolved` "
            "counts named absences too, so the counts alone cannot say which "
            "candidates had a figure, and a figure deleted between the resolver "
            "and the record is invisible without it"
        )
    if len(set(listed)) != len(listed):
        return "resolved_fingerprints contains a duplicate fingerprint"
    resolved = value.get("resolved")
    if _is_count(resolved) and len(listed) > resolved:
        return (
            f"lists {len(listed)} resolved_fingerprints but reports only "
            f"{resolved} resolved; a candidate with a share is a resolved one, "
            "so the list can never be longer than the count"
        )
    return None


def _reresolution(value: object) -> str | None:
    """The second measurement pass, over the figures a reconciler rejected.

    Null is legitimate and means no reconciler rejected a figure -- but only
    that, and `validate_run_record` is what ties null to a count of zero
    rejections. Without that tie this block is the stage A1 describes: one that
    has to remember to run, and whose omission looks exactly like a run with
    nothing to re-resolve.

    Same shape as `exposure_resolution` because it is the same agent doing the
    same job against a corrected question, and a second shape would be a second
    thing to keep in step.
    """
    if value is None:
        return None
    return _exposure_resolution(value)


def _provenance(value: object) -> str | None:
    """Shape check only: the contents come from git, not from an agent.

    `date` and `pull_request` are both legitimately null -- a commit subject that
    names no pull request is common in history predating the merge tooling. A
    missing pull request is a fact about that commit, not a resolution failure,
    so it must not be spelled the same way as one. `run-record.md` has how
    often that happens in practice, and is canonical for why no author is
    recorded here.
    """
    if value is None:
        return None
    if not isinstance(value, dict):
        return f"must be null or an object with keys {list(_PROVENANCE_KEYS)}"
    missing = [k for k in _PROVENANCE_KEYS if k not in value]
    if missing:
        return f"is missing {missing}; resolve_provenance.py writes all of them"
    if not isinstance(value["commit"], str) or not _SHA40.fullmatch(value["commit"]):
        return "commit must be a 40-character lowercase hex SHA"
    pull = value["pull_request"]
    if pull is not None and not (
        isinstance(pull, dict) and {"number", "url"} <= set(pull)
    ):
        return "pull_request must be null or an object with number and url"
    return None


def _method(value: object) -> str | None:
    """Shape check for the per-finding record of what was actually done.

    Null is legitimate and means nobody recorded the method for this finding --
    which the digest renders as exactly that, rather than as silence. The
    distinction matters for the same reason `permalink_resolution` exists: "not
    done" and "not recorded" look identical once they reach a reader, and only
    one of them is a gap in the run.
    """
    if value is None:
        return None
    if not isinstance(value, dict):
        return f"must be null or an object with keys {list(_METHOD_KEYS)}"
    missing = [k for k in _METHOD_KEYS if k not in value]
    if missing:
        return f"is missing {missing}"
    if value["before_after"] is not None and not isinstance(value["before_after"], str):
        return (
            "before_after must be null when no before/after re-run happened, or "
            "a sentence naming what was re-run and what changed"
        )
    if not isinstance(value["history_read"], list):
        return "history_read must be a list, empty when no history was read"
    return None


# Words this skill invented, which no reader of the digest has a definition for.
# `run-record.md` holds the substitution table and is canonical; this is the
# executable half of the same rule.
#
# It exists because the prose form of the rule demonstrably does not hold. A reader
# running this skill for the first time asked "What is a band?" of their own report,
# and a separate published digest carried `packet` four times -- every instance
# inside a verifier trail, which is the route the schema file already warns is the
# hardest to police, because the text is pasted from an agent that writes in this
# skill's vocabulary rather than composed for a reader.
#
# Deliberately checked here rather than in the renderer. Almost none of this text
# comes from the renderer: it arrives in the run record, so the renderer is the one
# place that cannot see the problem.
_JARGON: Final[tuple[tuple[re.Pattern[str], str], ...]] = tuple(
    (re.compile(rf"(?i)\b{pattern}\b"), name)
    for pattern, name in (
        (r"mandates?", "mandate"),
        (r"packets?", "packet"),
        (r"bands?", "band"),
        (r"candidates?", "candidate"),
        (r"ax[ei]s", "axis"),
        (r"dispositions?", "disposition"),
        (r"fingerprints?", "fingerprint"),
        (r"defect\s+sites?", "defect site"),
        (r"finders?", "finder"),
        (r"(?:mechanism|intent)[\s-]verifiers?", "verifier"),
        (r"deferred", "deferred"),
        (r"degraded[\s-]path", "degraded-path"),
    )
)

# Stripped before the scan, because each one is a place these words appear as
# themselves rather than as this skill's vocabulary. Without this the check fires
# on honest text: one measured digest names `Candidate.java` in a file list and
# prints `RESTRICTED uri ranked above >=1 clean candidate` inside captured test
# output, and neither is the jargon the rule is about. A checker that cries wolf on
# real output teaches its user to bypass it.
_CODEISH: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"`[^`]*`"),  # anything the author already marked as code
    re.compile(r"\S*[/\\]\S*"),  # paths
    re.compile(r"\b\w+\.(?:java|py|scala|kt|ts|js|json|yaml|yml|xml|proto)\b"),
    re.compile(r"\b(?:[a-z]+[A-Z]|[A-Z][a-z]+[A-Z])\w*\b"),  # camelCase, CamelCase
    re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b"),  # SCREAMING_CASE
)

# Fields whose value is a VERBATIM capture or an identifier, exempt by nature: the
# rule governs prose written for the reader, and rewriting captured output to avoid
# a word would falsify the evidence.
_VERBATIM_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "observed_symptom",
        "observed_full",
        "defect_site",
        "component",
        "permalink",
        "fingerprint",
        "metric_query",
        # `harm_statement` is not reader-facing: it exists so a figure can be
        # bound to a question, and `consequence` is the sentence a reader gets.
        # Scanned, it fails a whole record over a word the reader never meets --
        # and the collision is real rather than hypothetical, because "candidate"
        # is this skill's jargon AND ordinary vocabulary in a recommender, where
        # candidate generation is what the code under search does.
        "harm_statement",
        # The same argument for the hash: sixteen hex characters cannot contain
        # invented vocabulary, so scanning it can only ever cost time.
        "harm_hash",
    }
)


def _jargon_hits(text: str) -> list[str]:
    for stripper in _CODEISH:
        text = stripper.sub(" ", text)
    return sorted({name for pattern, name in _JARGON if pattern.search(text)})


def _scan_prose(value: object, path: str, field: str) -> list[ValidationError]:
    """Walk a value and check any written prose it carries is a finished thought.

    Recurses the same way `_scan_jargon` does, because the fields this applies to
    are nested at three different depths -- `consequence` on the finding,
    `trail` inside `mechanism` and `intent`, `note` inside `exposure` -- and a
    flat check over the finding's own keys would have missed every nested one and
    reported the record clean. `run-record.md` has the per-field counts.
    """
    if isinstance(value, str):
        if field not in _PROSE_FIELDS:
            return []
        problem = _complete_prose(value)
        return [ValidationError(path, problem)] if problem else []
    if isinstance(value, dict):
        return [
            error
            for key, inner in value.items()
            for error in _scan_prose(inner, f"{path}.{key}", str(key))
        ]
    if isinstance(value, list):
        return [
            error
            for index, inner in enumerate(value)
            for error in _scan_prose(inner, f"{path}[{index}]", field)
        ]
    return []


def _scan_jargon(value: object, path: str, field: str) -> list[ValidationError]:
    """Walk a value's prose and report any invented vocabulary it carries."""
    if field in _VERBATIM_FIELDS:
        return []
    if isinstance(value, str):
        hits = _jargon_hits(value)
        if not hits:
            return []
        return [
            ValidationError(
                path,
                "carries wording no reader of this report can define: "
                + ", ".join(hits)
                + ". run-record.md has what to write instead.",
            )
        ]
    if isinstance(value, dict):
        return [
            error
            for key, inner in value.items()
            for error in _scan_jargon(inner, f"{path}.{key}", str(key))
        ]
    if isinstance(value, list):
        return [
            error
            for index, inner in enumerate(value)
            for error in _scan_jargon(inner, f"{path}[{index}]", field)
        ]
    return []


# Dispatch tables rather than if/elif chains, mirroring redact_scan.py's
# _PATTERNS and diff_fields.py's _NORMALIZERS. A new field is a new row here,
# never a new branch inside the validator.
_FINDING_CHECKS: dict[str, Callable[[object], str | None]] = {
    "fingerprint": _fingerprint,
    "state": _state,
    "band": _band,
    "band_reason": _band_reason,
    "title": _text,
    "consequence": _text,
    "harm_statement": _harm_statement,
    "observed_symptom": _observed_symptom,
    "observed_full": _optional_text,
    "defect_site": _text,
    "component": _text,
    "tier": _tier,
    "exposure": _exposure,
    "effort": _effort,
    "mechanism": _mapping(_AXIS_KEYS),
    "intent": _mapping(_AXIS_KEYS),
    "fix_prompt": _optional_text,
    "permalink": _permalink,
    "verification": _optional_mapping(_VERIFICATION_KEYS),
    "provenance": _provenance,
    "method": _method,
}

_RECORD_CHECKS: dict[str, Callable[[object], str | None]] = {
    "run_id": _text,
    "scope_strategy": _text,
    "scope_label": _text,
    "components": _components,
    "findings": _any_list,
    "coverage": _coverage_entries,
    "degraded_paths": _objects_with(
        ("discriminator", "downstream_decision", "branches_on_it")
    ),
    "dead_surface": _objects_with(("surface", "requests_30d", "note")),
    "cost": _mapping(("agents", "wall_clock_minutes")),
    # `reason` only. This carried `unverified_count` and a prose `statement` too,
    # and both were restatements of numbers the renderer already computes from
    # `findings`: the count duplicates the Not-checked band header, and the
    # statement spelled out per-band counts in words. Measured: after one finding
    # was reblanded post-publication the statement still read "all ten in the most
    # urgent group" while the header rendered 9, because nothing links a
    # hand-authored sentence to the array it describes. The reason cannot go the
    # same way -- it is a fact about the run, not a count of it.
    "shortfall": _shortfall,
    "repo": _optional_mapping(("host", "full_name", "ref")),
    "gate": _mapping(("dossiers_scanned", "leaks_found", "redaction_hits")),
    "permalink_resolution": _permalink_resolution,
    "provenance_resolution": _provenance_resolution,
    "exposure_resolution": _exposure_resolution,
    "reresolution": _reresolution,
}


# Keys whose absence has one specific repair, which "is required" does not convey.
_MISSING: Final[dict[str, str]] = {
    "provenance_resolution": (
        "is required and is written by scripts/resolve_provenance.py. Run that "
        "stage against the checkout, between resolve_permalinks.py and this "
        "script, rather than composing the block by hand"
    ),
    "provenance": (
        "is required and comes from git, never from you. Running "
        "scripts/resolve_provenance.py fills it on every finding at once; a "
        "hand-written commit is a guess wearing a link"
    ),
    "method": (
        "is required, and null is a legitimate value meaning nobody recorded how "
        "this finding was checked. Set it from the two verifiers' reports -- "
        "whether a before/after re-run happened, and which history the blind "
        "check read -- or set it to null, but the key must be present"
    ),
}


def _check_keys(
    payload: dict, checks: dict[str, Callable[[object], str | None]], prefix: str
) -> list[ValidationError]:
    """Apply every check, then report unexpected keys by name.

    An unknown key is reported rather than ignored or passed through to a
    dataclass constructor: a bare TypeError names the dataclass, not the key,
    which tells the agent that produced the record nothing it can act on.

    A few missing keys get a longer message than "is required", because the
    generic one invites the wrong repair. An agent told 76 times that
    `findings[N].provenance` is required will write 76 of them by hand, which is
    precisely what the schema forbids -- the value has to come from git. Naming
    the stage that produces it converts a wall of errors into one action.
    """
    errors = [
        ValidationError(f"{prefix}{key}", message)
        for key, check in checks.items()
        for message in [
            check(payload[key]) if key in payload else _MISSING.get(key, "is required")
        ]
        if message
    ]
    errors.extend(
        ValidationError(f"{prefix}{key}", "is not a field of this schema")
        for key in payload
        if key not in checks
    )
    return errors


def _check_finding(raw: dict, index: int) -> list[ValidationError]:
    errors = _check_keys(raw, _FINDING_CHECKS, f"findings[{index}].")
    # A multi-line defect site must link to the whole range. `#L177` for a site
    # declared `:177-181` is a link that silently drops the rest of the defect,
    # and it reads as correct -- the anchor resolves, it just lands on one line.
    # Measured: an orchestrator built its permalinks with `line.split("-")[0]`
    # and every ranged finding in the run shipped truncated. The permalink regex
    # already ALLOWS `#L<start>-L<end>`; allowing was not enough, so this
    # requires it.
    site, link = raw.get("defect_site"), raw.get("permalink")
    if isinstance(site, str) and isinstance(link, str) and "#L" in link:
        tail = site.rsplit(":", 1)[-1]
        if "-" in tail and "-L" not in link.rsplit("#L", 1)[-1]:
            start, _, end = tail.partition("-")
            errors.append(
                ValidationError(
                    f"findings[{index}].permalink",
                    f"defect_site spans lines {start}-{end}, so the anchor must "
                    f"be #L{start}-L{end}; a single-line anchor drops the rest "
                    "of the defect while still resolving, which is why this is "
                    "rejected rather than warned about",
                )
            )
    state = FindingState.__members__.get(raw.get("state", ""))
    if (
        state
        and _VERDICT_BY_STATE[state] is not Verdict.NOT_A_BUG
        and raw.get("band") is None
    ):
        errors.append(
            ValidationError(
                f"findings[{index}].band",
                "is required for a finding that is not discarded, because a "
                "banded section is the only place it could be rendered",
            )
        )
    # Nested one level down, so it cannot live in the per-key table, which
    # validates the exposure object's shape rather than its contents.
    exposure = raw.get("exposure")
    if isinstance(exposure, dict) and "path_denominator" in exposure:
        problem = _path_denominator(exposure["path_denominator"])
        if problem:
            errors.append(
                ValidationError(f"findings[{index}].exposure.path_denominator", problem)
            )
    for key, value in raw.items():
        errors.extend(_scan_jargon(value, f"findings[{index}].{key}", str(key)))
        errors.extend(_scan_prose(value, f"findings[{index}].{key}", str(key)))
    return errors


def validate_run_record(raw: object) -> list[ValidationError]:
    """Every problem in the record, in reading order. Empty list means valid."""
    if not isinstance(raw, dict):
        return [ValidationError("<root>", "must be a JSON object")]
    errors = _check_keys(raw, _RECORD_CHECKS, "")
    # Only the record-level strings a reader actually sees. `scope_strategy` and
    # the coverage file lists are bookkeeping and never render as prose.
    for key in ("scope_label", "shortfall"):
        if key in raw:
            errors.extend(_scan_jargon(raw[key], key, key))
            errors.extend(_scan_prose(raw[key], key, key))
    findings = raw.get("findings")
    if isinstance(findings, list):
        for index, finding in enumerate(findings):
            if isinstance(finding, dict):
                errors.extend(_check_finding(finding, index))
            else:
                errors.append(
                    ValidationError(f"findings[{index}]", "must be an object")
                )
    # Cross-field, so it cannot live in the per-key table. This is the check
    # that makes `permalink_resolution` worth having: without it a record can
    # declare `attempted: 0` beside 64 findings and still validate, which is
    # precisely the shape of the run that shipped 64 unexplained nulls.
    resolution = raw.get("permalink_resolution")
    if isinstance(resolution, dict) and isinstance(findings, list):
        attempted = resolution.get("attempted")
        if (
            isinstance(attempted, int)
            and not isinstance(attempted, bool)
            and attempted != len(findings)
        ):
            errors.append(
                _attempted_mismatch(
                    "permalink_resolution.attempted",
                    attempted,
                    len(findings),
                    "A null permalink is only meaningful once it is known that "
                    "somebody looked.",
                )
            )
        # And the outcomes must account for every attempt. Measured: an
        # orchestrator satisfied the required field by hand with
        # `{attempted: 3, linked: 0, unlinked: []}` -- arithmetically impossible,
        # since three findings were then neither linked nor explained -- and the
        # record validated. Counting attempts without counting outcomes rebuilds
        # the exact hole this field exists to close, because
        # `{attempted: 64, linked: 0, unlinked: []}` is the original bug wearing
        # the new field's clothes.
        linked, unlinked = resolution.get("linked"), resolution.get("unlinked")
        if (
            isinstance(attempted, int)
            and not isinstance(attempted, bool)
            and isinstance(linked, int)
            and not isinstance(linked, bool)
            and isinstance(unlinked, list)
            and linked + len(unlinked) != attempted
        ):
            errors.append(
                ValidationError(
                    "permalink_resolution",
                    f"attempted {attempted} but accounts for "
                    f"{linked + len(unlinked)} ({linked} linked + "
                    f"{len(unlinked)} unlinked); every attempt must end in a "
                    "link or a named reason, or the count is not evidence that "
                    "anybody looked",
                )
            )
    # The same arithmetic guard over provenance, which is optional as a block but
    # must be internally honest when present. A record from before this stage
    # existed simply has no block and renders without commit lines; a record that
    # claims 76 attempts and accounts for 3 is the failure this catches.
    prov = raw.get("provenance_resolution")
    if isinstance(prov, dict):
        attempted, resolved = prov.get("attempted"), prov.get("resolved")
        unresolved = prov.get("unresolved")
        if (
            isinstance(attempted, int)
            and not isinstance(attempted, bool)
            and isinstance(resolved, int)
            and not isinstance(resolved, bool)
            and isinstance(unresolved, list)
            and resolved + len(unresolved) != attempted
        ):
            errors.append(
                ValidationError(
                    "provenance_resolution",
                    f"attempted {attempted} but accounts for "
                    f"{resolved + len(unresolved)} ({resolved} resolved + "
                    f"{len(unresolved)} unresolved); every attempt must end in a "
                    "commit or a named reason",
                )
            )
    # Same two checks for the impact lookup, for the same reason. Without them
    # `{attempted: 0, resolved: 0, unresolved: []}` validates beside a page of
    # Read-closely findings whose urgency nothing evidences -- which is the state
    # measured on two real runs before this block existed.
    # A band without a stated reason is the state this field exists to end. Not
    # required on `Not checked`: there is no band decision to justify there, and
    # demanding a sentence would invite one to be invented.
    if isinstance(findings, list):
        unjustified = [
            f.get("fingerprint", f"findings[{i}]")
            for i, f in enumerate(findings)
            if isinstance(f, dict)
            and f.get("band") not in (None, Band.NOT_TRIAGED.value)
            and not (isinstance(f.get("band_reason"), str) and f["band_reason"].strip())
        ]
        if unjustified:
            errors.append(
                ValidationError(
                    "findings[].band_reason",
                    f"is missing on {len(unjustified)} banded finding(s) "
                    f"({', '.join(unjustified[:4])}"
                    f"{', ...' if len(unjustified) > 4 else ''}); the rubric "
                    "requires one sentence naming what decided the band, and a "
                    "finding demoted on a measured dormancy must disclose the "
                    "capability it still has",
                )
            )
    # `DEFERRED_UNVERIFIED` and `Not triaged` are the same fact stated in the two
    # columns the digest groups by, so a record carrying one without the other is
    # rejected. SKILL.md section 9 has required the pairing since the band existed;
    # nothing enforced it, and on 2026-09-11 a run wrote scrutiny bands on all 46
    # candidates nobody had checked. The band decides which section renders the
    # finding, so the whole unchecked tail rendered as 46 expanded rows carrying
    # the "Not checked" verdict instead of collapsing into the one-click list
    # `_render_spill` exists to produce -- 46,227 characters of visible page
    # against 6,237 once corrected.
    #
    # Both directions, because each is a different lie: a scrutiny band on an
    # unchecked candidate promises a judgement nobody made, and `Not triaged` on a
    # checked one hides a real verdict behind a fold.
    #
    # **The correspondence is total, and that is not a reason to delete this.**
    # `DEFERRED_UNVERIFIED` is the only state mapping to `Verdict.NOT_CHECKED`, so
    # the band carries no information the state does not. Deriving it in
    # `_build_finding` instead would produce a correct digest sitting on top of
    # portfolio files that still say `Read closely` -- measured: all 46 deferred
    # files from that run carry the wrong band under a "Band:" heading -- with
    # nothing anywhere reporting the divergence.
    #
    # Rejecting rather than silently rebanding follows the rule this module states
    # at the top and applies everywhere else: a caller repairing a record is an
    # agent, and it repairs exactly what it is told about. The record is written
    # minutes before rendering, so the cost of the error is one edit and a
    # re-render, not the 121-minute run.
    if isinstance(findings, list):
        mismatched = [
            f'{f.get("fingerprint", f"findings[{i}]")} '
            f'({f.get("state")} / {f.get("band")})'
            for i, f in enumerate(findings)
            if isinstance(f, dict) and (_pairing_broken(f) or _unjustifiable(f))
        ]
        if mismatched:
            errors.append(
                ValidationError(
                    "findings[].band vs findings[].state",
                    f"pairs {FindingState.DEFERRED_UNVERIFIED.value} with a band "
                    f"other than {Band.NOT_TRIAGED.value!r}, or the reverse, or "
                    f"justifies a {Band.NOT_TRIAGED.value!r} band nobody decided, "
                    f"on {_counted_list(mismatched)}; a candidate nobody verified "
                    "has no scrutiny to assign and no reason to give for it, and "
                    "the band is what decides whether it renders as a row or "
                    "inside the collapsed unchecked list. Fix them together, in "
                    "the record AND in the candidate's portfolio file: the "
                    "pre-verification band ordered the fill and neither it nor its "
                    "reason survives into either",
                )
            )
    # A RUN THAT LEFT CANDIDATES UNCHECKED MUST SAY WHY, and `_render_counts` is
    # where the saying happens: its gap link renders only when `shortfall` is
    # present, so a null one puts the reader back at a bare "6 of 106" with
    # nothing suggesting the run stopped early.
    if isinstance(findings, list):
        shortfall = raw.get("shortfall")
        unchecked = [
            f.get("fingerprint", f"findings[{i}]")
            for i, f in enumerate(findings)
            if isinstance(f, dict)
            and f.get("state") == FindingState.DEFERRED_UNVERIFIED.value
        ]
        # `"shortfall" in raw`, not `is None`: `raw.get` collapses absent and
        # explicitly null, and the key check above already names an absent one.
        # The shape check accepts a BLANK reason -- hence `stated` below.
        shape_accepted = "shortfall" in raw and _shortfall(shortfall) is None
        if shape_accepted:
            reason = shortfall.get("reason") if isinstance(shortfall, dict) else None
            stated = isinstance(reason, str) and bool(reason.strip())
            # INDEPENDENT `if`s, never an `elif` chain. Chained, the coherence
            # branch swallowed the ceiling check on exactly the record that
            # check exists to reach.
            #
            # `findings` NON-EMPTY is the third condition and is not padding: a
            # run whose context died during finder fan-out has no candidates to
            # defer and must still be able to say why it stopped.
            if shortfall is not None and findings and not unchecked:
                # BOUNDING NEVER DISCARDS, AND NEITHER DOES SELF-TRUNCATION. A
                # record stating a shortfall with no DEFERRED_UNVERIFIED finding
                # says both "some were not checked" and "there are none".
                #
                # THE LIMIT: every guard here compares two fields ONE producer
                # writes, so a record omitting BOTH validates clean. Do not
                # extend this block believing it can close that.
                errors.append(
                    ValidationError(
                        "shortfall",
                        "is stated, but no finding is DEFERRED_UNVERIFIED. Every "
                        "candidate that did not complete the pipeline keeps its "
                        "packet and is written into `findings` by name -- "
                        "otherwise the digest renders as a complete run, because "
                        "the masthead's gap link and the unchecked band both need "
                        "those findings to exist",
                    )
                )
            if unchecked and not stated:
                errors.append(
                    ValidationError(
                        "shortfall",
                        f"states no reason, but {_counted_list(unchecked)} were "
                        "never checked; write the clause saying why, in the "
                        "reader's language, so the digest can state it beside "
                        "the verified count rather than leaving the reader to "
                        "infer a cause",
                    )
                )
            if shortfall is not None:
                # UNCONDITIONAL on the other two checks, both of these. Nested
                # under the reason check, each was unreachable on exactly the
                # record it exists to catch -- it happened twice.
                verified = len(findings) - len(unchecked)
                errors += _ceiling_claim_errors(shortfall, verified)
                errors += _selected_errors(shortfall, verified, len(findings))
    exposure = raw.get("exposure_resolution")
    if isinstance(exposure, dict) and isinstance(findings, list):
        attempted = exposure.get("attempted")
        if (
            isinstance(attempted, int)
            and not isinstance(attempted, bool)
            and attempted != len(findings)
        ):
            errors.append(
                _attempted_mismatch(
                    "exposure_resolution.attempted",
                    attempted,
                    len(findings),
                    "An UNKNOWN exposure is only meaningful once it is known that "
                    "somebody queried.",
                )
            )
        resolved = exposure.get("resolved")
        # Smoke test: if the resolver claims any resolved, at least ONE finding
        # must show evidence of integration (a non-null share or a share_absent
        # other than NOT_QUERIED). This catches complete non-wiring (resolved=N,
        # actually_resolved=0) but NOT partial wiring (resolved=N,
        # actually_resolved=M where 0 < M < N). The partial case is left
        # unchecked because exposure_resolution counts are accumulated pre-banding
        # from the original groups list, while findings may reflect post-
        # disposition state -- a resolved candidate that gets merged or discarded
        # before landing in findings could legitimately make the counts diverge.
        if (
            isinstance(resolved, int)
            and not isinstance(resolved, bool)
            and resolved > 0
            and isinstance(findings, list)
        ):
            actually_resolved = sum(
                1
                for f in findings
                if isinstance(f, dict)
                and isinstance(f.get("exposure"), dict)
                and (
                    f["exposure"].get("share") is not None
                    or f["exposure"].get("share_absent") not in (None, "NOT_QUERIED")
                )
            )
            if actually_resolved == 0:
                errors.append(
                    ValidationError(
                        "exposure_resolution vs findings",
                        f"exposure_resolution.resolved is {resolved} but no "
                        "finding has a non-null share or a share_absent other "
                        "than NOT_QUERIED. The resolver results were not "
                        "integrated into the findings -- the resolver ran but "
                        "its output was never wired into the run record",
                    )
                )
    errors.extend(_check_figure_bindings(raw))
    return errors


def _check_figure_bindings(raw: dict) -> list[ValidationError]:
    """The four cross-record invariants that keep the exposure column honest.

    Each one refuses a shape a real run shipped. They live together because they
    are one property split across three fields -- a figure answers a stated
    harm, somebody judged whether it fits, and a rejected figure was re-measured
    rather than deleted -- and reading them apart is how the first version of
    this column ended up with 12 of its 15 actionable figures silently blanked.
    """
    errors: list[ValidationError] = []
    findings = raw.get("findings")
    if not isinstance(findings, list):
        return errors

    rejected: list[str] = []
    # Built once, above the loop: which candidates the resolver actually
    # produced a conforming figure for. Used by the survival check inside the
    # loop, which is the only thing that check needed the caller's guards for.
    resolution = raw.get("exposure_resolution")
    listed = (
        resolution.get("resolved_fingerprints")
        if isinstance(resolution, dict)
        else None
    )
    with_figure = (
        {fp for fp in listed if isinstance(fp, str)}
        if isinstance(listed, list)
        else set()
    )
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            continue
        exposure = finding.get("exposure")
        if not isinstance(exposure, dict):
            continue
        prefix = f"findings[{index}]"
        statement = finding.get("harm_statement")
        share = exposure.get("share")

        # A5. The figure is bound to THE QUESTION IT ANSWERS, and a figure whose
        # question has changed is refused rather than rendered. Without this the
        # re-resolve stage is a step that must remember to run: mutate the harm
        # statement anywhere downstream and the percentage silently becomes an
        # answer to a superseded question, which is the shape the whole column
        # was in.
        #
        # HARM_SHARE ONLY, and the restriction is the point rather than a
        # loosening. A path-exposure figure does not answer the harm statement --
        # it answers "how much traffic reaches this code" -- so comparing its
        # hash to the harm statement was a category error, and it made a
        # documented shape unwritable: a reconciler that DOWNGRADES a figure AND
        # corrects the harm's wording, where the second pass then cannot measure
        # the corrected harm, is exactly what "retained but relabelled as path
        # exposure" means, and it was refused every time the wording actually
        # changed. Found in review, reproduced, and untested before then because
        # the retention test used an UNCHANGED statement.
        #
        # This is not an escape hatch. A producer cannot dodge the comparison by
        # relabelling a harm share as path exposure: ADOPTED and REPLACED imply
        # HARM_SHARE on any harm-confirmed finding, checked below, and on a
        # finding whose harm is not confirmed there is no harm for a figure to
        # be a stale answer to.
        if (
            isinstance(share, dict)
            and share.get("figure_kind") == "HARM_SHARE"
            and isinstance(statement, str)
            and statement.strip()
        ):
            recorded = share.get("harm_hash")
            expected = harm_hash(statement)
            if isinstance(recorded, str) and recorded != expected:
                errors.append(
                    ValidationError(
                        f"{prefix}.exposure.share.harm_hash",
                        f"is {recorded!r} but this finding's harm_statement "
                        f"hashes to {expected!r}. The figure was computed against "
                        "a different harm than the one recorded, so it answers a "
                        "superseded question: re-resolve it against the current "
                        "statement, or drop the share and name a share_absent. "
                        "Do NOT reconcile this by recomputing the hash from the "
                        "new statement -- that keeps a stale number and removes "
                        "the only signal that it is stale",
                    )
                )

        # A2. The reconciler's judgement on the figure is stated as data, and it
        # is stated exactly when a reconciler saw the finding. Both directions
        # are checked: a missing value on a verified finding is the silence the
        # fingerprint allowlist produced, and a value on an unverified one claims
        # a judgement nobody made.
        state = finding.get("state")
        disposition = exposure.get("figure_disposition")
        reconciled = state != FindingState.DEFERRED_UNVERIFIED.value
        if reconciled and disposition is None:
            errors.append(
                ValidationError(
                    f"{prefix}.exposure.figure_disposition",
                    f"is null on a finding in state {state!r}, which reached a "
                    "reconciler. Every reconciled finding carries ADOPTED, "
                    "DOWNGRADED or REPLACED, because the reconciler is the only "
                    "actor that can see whether the queried metric governs the "
                    "harm it just confirmed. Null here is what a run-scoped "
                    "fingerprint allowlist degrades to on its second run: no "
                    "match, no error, and every figure blanked",
                )
            )
        elif not reconciled and disposition is not None:
            errors.append(
                ValidationError(
                    f"{prefix}.exposure.figure_disposition",
                    f"is {disposition!r} on a DEFERRED_UNVERIFIED finding. "
                    "Nobody reconciled this one, so there is no judgement to "
                    "record -- its figure is PATH_EXPOSURE and the column says so",
                )
            )
        if (
            disposition in _FIGURE_REJECTED
            and FindingState.__members__.get(str(state)) in _HARM_CONFIRMED_STATES
        ):
            rejected.append(str(finding.get("fingerprint")))

        # `figure_kind` is DERIVABLE from `figure_disposition` for three of its
        # four values, and stored anyway for the fourth. ADOPTED and REPLACED
        # both mean the figure answers the confirmed harm, so both imply
        # HARM_SHARE -- and until these two checks existed, ADOPTED beside
        # PATH_EXPOSURE validated with no error at all, which is redundant state
        # silently contradicting the field it duplicates.
        #
        # DOWNGRADED is the value that earns the field: the first-pass figure
        # may be RETAINED as an execution rate (PATH_EXPOSURE) or re-measured by
        # the second pass (HARM_SHARE), and nothing in the record distinguishes
        # those without being told. That case is real -- one reconciler on the
        # 2026-09-05 run wrote exactly it, "retained but relabelled as path
        # exposure, not harm".
        # Only where the harm is CONFIRMED. Found by running a real verdict
        # through this: a DISCARDED_REFUTED finding whose reconciler ADOPTED a
        # measured ZERO -- "0% of the path, THE PATH DOES NOT EXIST" -- is a
        # real and useful figure, and it is path exposure, because a refuted
        # finding has no harm for anything to be a share of. Without this
        # condition the two rules contradicted each other and no record
        # carrying that shape could be written at all.
        if (
            isinstance(share, dict)
            and disposition in ("ADOPTED", "REPLACED")
            and FindingState.__members__.get(str(state)) in _HARM_CONFIRMED_STATES
        ):
            if share.get("figure_kind") != "HARM_SHARE":
                errors.append(
                    ValidationError(
                        f"{prefix}.exposure.share.figure_kind",
                        f"is {share.get('figure_kind')!r} beside "
                        f"figure_disposition {disposition!r}, which says the "
                        "figure answers the confirmed harm -- so it is a "
                        "HARM_SHARE. Only DOWNGRADED leaves the kind open, "
                        "because a downgraded figure may be retained as an "
                        "execution rate or replaced by a re-measured one",
                    )
                )
        elif disposition == "NO_FIGURE" and isinstance(share, dict):
            errors.append(
                ValidationError(
                    f"{prefix}.exposure.figure_disposition",
                    "is NO_FIGURE beside a share. NO_FIGURE says the resolver "
                    "produced nothing for this candidate, so there was nothing "
                    "to adopt, downgrade or replace -- a figure here means one "
                    "of the other three describes what happened",
                )
            )

        # A6. A harm share needs a CONFIRMED harm to be a share of. Keyed on
        # the state rather than on whether a reconciler looked: a figure for a
        # harm that was refuted, or that never reproduced, is the same error as
        # a figure for a harm nobody checked.
        if (
            isinstance(share, dict)
            and share.get("figure_kind") == "HARM_SHARE"
            and FindingState.__members__.get(str(state)) not in _HARM_CONFIRMED_STATES
        ):
            errors.append(
                ValidationError(
                    f"{prefix}.exposure.share.figure_kind",
                    f"claims HARM_SHARE on a finding in state {state!r}, whose "
                    "harm is not confirmed. A harm share needs a harm to be a "
                    "share OF; what was measured here is the traffic reaching "
                    "the code, which is PATH_EXPOSURE",
                )
            )

        # A3. A figure the resolver produced does not vanish without a named
        # reason. The pre-existing smoke test below fires only when NO finding
        # shows any integration at all, and its own comment records the partial
        # case as unchecked -- on the run this was written for, the partial case
        # was almost all of it. Figures: `run-record.md`.
        if finding.get("fingerprint") in with_figure and share is None:
            if disposition in _FIGURE_REJECTED:
                # Judged and rejected, which is this pipeline working. It still
                # owes the reader a reason in place of the figure.
                if exposure.get("share_absent") is None:
                    errors.append(
                        ValidationError(
                            f"{prefix}.exposure.share_absent",
                            "is null on a finding whose resolver figure a "
                            "reconciler rejected. A rejected figure leaves a "
                            "named absence, not a blank cell -- 'no share "
                            "measured' over a figure that WAS measured and then "
                            "discarded is the one sentence this column must "
                            "never print",
                        )
                    )
            else:
                errors.append(
                    ValidationError(
                        f"{prefix}.exposure.share",
                        f"is null, but the resolver returned a conforming share "
                        f"for {finding.get('fingerprint')!r} and "
                        f"figure_disposition is {disposition!r} rather than a "
                        "rejection. A figure that reached the resolver and not "
                        "the record was deleted by the assembly step, which is "
                        "the defect this check exists to catch: carry the share "
                        "through, or record the reconciler's DOWNGRADED or "
                        "REPLACED judgement that removed it",
                    )
                )

    errors.extend(_check_reresolution_ran(raw, rejected))
    return errors


def _pairing_broken(finding: dict) -> bool:
    """`DEFERRED_UNVERIFIED` and `Not triaged` must both hold, or neither."""
    unverified = finding.get("state") == FindingState.DEFERRED_UNVERIFIED.value
    not_triaged = finding.get("band") == Band.NOT_TRIAGED.value
    return unverified != not_triaged


def _unjustifiable(finding: dict) -> bool:
    """A `Not triaged` finding explaining a band decision nobody made.

    The `band_reason` check above only stops a sentence being MISSING, and skips
    `Not triaged` because there is nothing to justify there. That left the other
    direction open, and the renderer prints any truthy `band_reason` into the
    always-visible row. Measured on the 2026-09-11 record: all 46 unverified
    candidates carry one, each justifying the scrutiny band they should never
    have had -- so correcting only the band would have moved the fabricated
    judgement one column left rather than removing it.
    """
    reason = finding.get("band_reason")
    return finding.get("band") == Band.NOT_TRIAGED.value and bool(reason)


def _counted_list(fingerprints: list[str]) -> str:
    """`3 finding(s) (a, b, c)` -- the names, not just the count.

    The rejected fingerprints were being collected and then only counted, which
    made the list ceremony over an integer. Naming them is what an operator
    repairing the record actually needs: the count says a stage did not run, the
    names say which rows to re-measure.
    """
    shown = ", ".join(sorted(fingerprints)[:6])
    if len(fingerprints) > 6:
        shown += ", ..."
    return f"{len(fingerprints)} finding(s) ({shown})"


def _check_reresolution_ran(raw: dict, rejected: list[str]) -> list[ValidationError]:
    """Every rejected figure was re-measured against the corrected harm.

    A1 as an invariant rather than a step. The re-resolve stage exists because a
    figure computed from the finder's harm description answers a question
    verification is designed to supersede; tying its `attempted` count to the
    number of rejections is what stops it from quietly not running, because a
    stage that did not run and a run with nothing to re-resolve otherwise look
    identical in the record.
    """
    errors: list[ValidationError] = []
    block = raw.get("reresolution")
    if not rejected:
        if block is not None:
            errors.append(
                ValidationError(
                    "reresolution",
                    "is present but no finding carries figure_disposition "
                    "DOWNGRADED or REPLACED, so there was nothing to re-measure. "
                    "Set it to null, or state the rejections it answers",
                )
            )
        return errors
    if block is None:
        errors.append(
            ValidationError(
                "reresolution",
                f"is null but {_counted_list(rejected)} had a figure rejected by "
                "a reconciler. Each rejection is a figure computed against a harm "
                "statement the verifiers then corrected, so it must be re-measured "
                "against the corrected statement -- spawn the impact resolver "
                "over the rejected candidates and record the pass here. Recording "
                "an attempt that failed is a valid outcome; recording nothing is "
                "how the figure stayed deleted",
            )
        )
        return errors
    if isinstance(block, dict):
        attempted = block.get("attempted")
        if _is_count(attempted) and attempted != len(rejected):
            errors.append(
                ValidationError(
                    "reresolution.attempted",
                    f"is {attempted} but {_counted_list(rejected)} carry "
                    "figure_disposition DOWNGRADED or REPLACED. Every rejected "
                    "figure is re-measured against the corrected harm statement, "
                    "so the two counts are the same number written twice",
                )
            )
    return errors


def _build_finding(
    raw: dict,
    unlinked_reasons: dict[str, str],
    unresolved_reasons: dict[str, str] | None = None,
) -> Finding:
    state = FindingState[raw["state"]]
    band = Band(raw["band"]) if raw["band"] is not None else None
    verification = raw.get("verification")
    provenance = raw.get("provenance")
    method = raw.get("method")
    return Finding(
        fingerprint=raw["fingerprint"],
        state=state,
        verdict=_VERDICT_BY_STATE[state],
        band=band,
        band_reason=raw["band_reason"],
        title=raw["title"],
        consequence=raw["consequence"],
        harm_statement=raw["harm_statement"],
        observed_symptom=raw["observed_symptom"],
        observed_full=raw.get("observed_full"),
        defect_site=raw["defect_site"],
        component=raw["component"],
        tier=raw["tier"],
        exposure=_exposure_from_raw(raw["exposure"]),
        effort=raw["effort"],
        mechanism=AxisTrail(**{k: raw["mechanism"][k] for k in _AXIS_KEYS}),
        intent=AxisTrail(**{k: raw["intent"][k] for k in _AXIS_KEYS}),
        fix_prompt=raw.get("fix_prompt"),
        provenance=(
            Provenance(**{k: provenance.get(k) for k in _PROVENANCE_KEYS})
            if provenance
            else None
        ),
        method=(
            Method(
                before_after=method.get("before_after"),
                history_read=method.get("history_read") or [],
            )
            if method
            else None
        ),
        permalink=raw.get("permalink"),
        permalink_unlinked_reason=unlinked_reasons.get(raw["fingerprint"]),
        provenance_unresolved_reason=(unresolved_reasons or {}).get(raw["fingerprint"]),
        verification=(
            Verification(**{k: verification[k] for k in _VERIFICATION_KEYS})
            if verification
            else None
        ),
        # Read closely carries all three lines on the always-visible row; everything
        # below it drops the symptom into the expansion. A run has been measured
        # producing 44 candidates, which is unreadable otherwise.
        symptom_collapsed=band is not Band.READ_CLOSELY,
    )


def normalise(raw: dict) -> RenderModel:
    """Group a validated record by band. Call only after validate_run_record."""
    # Flattened onto each finding here rather than carried run-level into the
    # model, because the renderer needs the reason at the one place it prints
    # "no source link" -- next to that finding's own path.
    unlinked_reasons = {
        entry["fingerprint"]: entry["reason"]
        for entry in raw["permalink_resolution"]["unlinked"]
    }
    # Same shape, same reason. A record predating resolve_provenance.py has no
    # block at all, which is distinct from one whose resolution found nothing.
    unresolved_reasons = {
        entry["fingerprint"]: entry["reason"]
        for entry in (raw.get("provenance_resolution") or {}).get("unresolved", [])
    }
    findings = [
        _build_finding(f, unlinked_reasons, unresolved_reasons) for f in raw["findings"]
    ]
    discarded = [f for f in findings if f.verdict is Verdict.NOT_A_BUG]
    # O(n x 4) rather than itertools.groupby, which yields only keys present in
    # the data. An empty band must still render, or a systematic blind spot looks
    # identical to a clean component.
    grouped = {
        band: sorted(
            (
                f
                for f in findings
                if f.verdict is not Verdict.NOT_A_BUG and f.band is band
            ),
            key=lambda f: f.fingerprint,
        )
        for band in Band
    }
    return RenderModel(
        run_id=raw["run_id"],
        scope_label=raw["scope_label"],
        components=raw["components"],
        grouped=grouped,
        discarded=sorted(discarded, key=lambda f: f.fingerprint),
        coverage=raw["coverage"],
        degraded_paths=raw["degraded_paths"],
        dead_surface=raw["dead_surface"],
        cost=raw["cost"],
        shortfall=raw.get("shortfall"),
        gate=raw["gate"],
        repo=raw.get("repo"),
    )


def _finding_to_dict(finding: Finding) -> dict:
    payload = asdict(finding)
    payload["state"] = finding.state.value
    payload["verdict"] = finding.verdict.value
    payload["band"] = finding.band.value if finding.band else None
    return payload


def model_to_dict(model: RenderModel) -> dict:
    """The wire form carried by the pipe to render_digest.py."""
    return {
        "run_id": model.run_id,
        "scope_label": model.scope_label,
        "components": model.components,
        "grouped": {
            band.value: [_finding_to_dict(f) for f in model.grouped[band]]
            for band in Band
        },
        "discarded": [_finding_to_dict(f) for f in model.discarded],
        "coverage": model.coverage,
        "degraded_paths": model.degraded_paths,
        "dead_surface": model.dead_surface,
        "cost": model.cost,
        "shortfall": model.shortfall,
        "gate": model.gate,
        "repo": model.repo,
    }


def _exposure_from_raw(raw: dict) -> Exposure:
    """Build an Exposure from a record, tolerating the absence of the share keys.

    A record written before `share` existed has none of the three keys, and must
    still build and render. `.get()` rather than a strict comprehension is what
    keeps an already-normalised model re-renderable without a re-run.

    **THAT TOLERANCE IS NARROWER THAN IT READS, and the wider claim was wrong.**
    This function has two callers with two different postures. Through
    `normalise()` it is reached only AFTER `validate_run_record` has passed, so
    a raw record predating this schema never arrives here at all -- it fails
    validation on the required keys and exits 1. The tolerant path is only
    exercised through `model_from_dict`, the wire format between this script's
    stdout and `render_digest.py`'s stdin, which the documented pipeline never
    persists. So: a run record produced before 0.25.0 CANNOT be re-rendered
    without regenerating it, and only an already-normalised model dict can skip
    re-validation.

    That tolerance stops at the two keys `_EXPOSURE_KEYS` names. `figure_kind`
    and `figure_disposition` are read strictly, because a record that reaches
    here has passed validation and validation requires both -- and a `.get()`
    here would let a re-render of an older record produce a column that silently
    cannot tell a harm share from a path-exposure figure, which is the state this
    change exists to leave behind.
    """
    share = raw.get("share")
    return Exposure(
        **{key: raw[key] for key in _EXPOSURE_KEYS},
        share=Share(**{key: share[key] for key in _SHARE_KEYS}) if share else None,
        share_absent=raw.get("share_absent"),
        share_absent_detail=raw.get("share_absent_detail"),
    )


def _finding_from_dict(payload: dict) -> Finding:
    fields = dict(payload)
    fields["state"] = FindingState[payload["state"]]
    fields["verdict"] = Verdict(payload["verdict"])
    fields["band"] = Band(payload["band"]) if payload["band"] else None
    fields["exposure"] = _exposure_from_raw(payload["exposure"])
    fields["mechanism"] = AxisTrail(**payload["mechanism"])
    fields["intent"] = AxisTrail(**payload["intent"])
    fields["verification"] = (
        Verification(**payload["verification"]) if payload["verification"] else None
    )
    fields["provenance"] = (
        Provenance(**payload["provenance"]) if payload.get("provenance") else None
    )
    fields["method"] = Method(**payload["method"]) if payload.get("method") else None
    return Finding(**fields)


def model_from_dict(payload: dict) -> RenderModel:
    """Rebuild the model on the far side of the pipe."""
    return RenderModel(
        run_id=payload["run_id"],
        scope_label=payload["scope_label"],
        components=payload["components"],
        grouped={
            band: [_finding_from_dict(f) for f in payload["grouped"][band.value]]
            for band in Band
        },
        discarded=[_finding_from_dict(f) for f in payload["discarded"]],
        coverage=payload["coverage"],
        degraded_paths=payload["degraded_paths"],
        dead_surface=payload["dead_surface"],
        cost=payload["cost"],
        shortfall=payload["shortfall"],
        gate=payload["gate"],
        repo=payload.get("repo"),
    )


def _fail(status: str, problems: list[str], code: int) -> None:
    json.dump({"status": status, "problems": problems}, sys.stderr, indent=2)
    sys.exit(code)


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if args:
        _fail("USAGE", [f"unexpected argument(s): {' '.join(args)}"], 2)

    source = sys.stdin.read()
    if not source.strip():
        _fail("NO_INPUT", ["nothing on stdin; the digest is unrendered"], 2)

    try:
        raw = json.loads(source)
    except json.JSONDecodeError as error:
        _fail("BAD_JSON", [f"stdin is not valid JSON: {error}"], 2)

    errors = validate_run_record(raw)
    if errors:
        _fail("INVALID", [f"{e.field}: {e.message}" for e in errors], 1)

    json.dump(model_to_dict(normalise(raw)), sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
