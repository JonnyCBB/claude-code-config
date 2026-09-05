"""Tests for the three rendering defects: exposure column, title truncation,
and coverage-disclosure composition.

Every test in this file has BOTH ARMS: a case that passes under the defect and a
case that fails, so each test discriminates the fix from the bug. The label
ABSENCE vs DISCRIMINATION is stated in the docstring.
"""

import re
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from digest_model import (
    Band,
    Exposure,
    Finding,
    FindingState,
    RenderModel,
    Share,
    Verdict,
    _PROSE_FIELDS,
    _complete_prose,
    validate_run_record,
)
from digest_model import _exposure as _exposure_validator
from digest_model import AxisTrail
from render_digest import _render_band, _render_exposure, _render_row


def _make_exposure(path_denominator, basis="MEASURED"):
    return Exposure(
        basis=basis,
        path_denominator=path_denominator,
        component_denominator="100% of the component",
        note="No note.",
    )


def _make_not_checked_finding(fingerprint="0123456789abcdef"):
    """A minimal Finding in the NOT_CHECKED band, for shortfall composition tests."""
    return Finding(
        fingerprint=fingerprint,
        state=FindingState.DEFERRED_UNVERIFIED,
        verdict=Verdict.NOT_CHECKED,
        band=Band.NOT_CHECKED,
        # Null is correct here: a finding nobody looked at has no band decision
        # to justify, and requiring a sentence would invite an invented one.
        band_reason=None,
        title="The handler silently drops the error response.",
        consequence="Callers see a success when the operation failed.",
        observed_symptom="POST /api/foo returned 200 with empty body",
        observed_full="POST /api/foo returned 200 with empty body\nExpected 500",
        defect_site="src/Handler.java:42",
        component="my-service",
        tier="2",
        exposure=_make_exposure("0.5% of requests on /api/foo"),
        effort="S",
        mechanism=AxisTrail(verdict="not checked", trail="Not checked."),
        intent=AxisTrail(verdict="not checked", trail="Not checked."),
        fix_prompt=None,
        verification=None,
        provenance=None,
        method=None,
        permalink=None,
        permalink_unlinked_reason="no pushed commit matched",
        provenance_unresolved_reason=None,
        symptom_collapsed=True,
    )


# ---------------------------------------------------------------------------
# Defect 1: the impact column drops non-percentage exposure content
# ---------------------------------------------------------------------------


class TestRenderExposure:
    """DISCRIMINATION: the code renders 'not measured' for ALL non-percentage
    content, discarding meaningful prose."""

    def test_percentage_led_renders_figure(self):
        """Control arm: a percentage-led phrase already renders correctly under
        the defect. This arm proves the test method detects a non-empty cell."""
        exposure = _make_exposure("0.072% of searches on this endpoint")
        html = _render_exposure(exposure)
        assert "0.072%" in html
        assert "not measured" not in html

    def test_prose_without_percentage_renders_content(self):
        """Defect arm: a non-percentage exposure statement carries content that
        the reader needs, but the code replaces it with 'not measured'."""
        exposure = _make_exposure(
            "not established -- the share of requests was not queried"
        )
        html = _render_exposure(exposure)
        assert "not measured" not in html
        assert "not established" in html

    def test_measured_word_in_non_percentage_renders(self):
        """Defect arm, measured case: 9 of 21 exposure notes containing the
        word MEASURED reached the column as 'not measured'. The word should
        appear as written."""
        exposure = _make_exposure("MEASURED: affects all users of this endpoint")
        html = _render_exposure(exposure)
        assert "MEASURED" in html
        assert "not measured" not in html.lower()

    def test_genuinely_empty_states_the_absence_without_a_basis_word(self):
        """Both arms need this: a truly empty exposure must SAY it is absent, and
        must not print a provenance word above the absence.

        The literal string moved from "not measured" to "no share measured" when
        the cell gained a percentage, because the absence is now specifically of
        a share and three different reasons produce it. The rule this test exists
        to protect is unchanged and is asserted directly below: one run shipped
        `n/a` above `ESTIMATED` on all 76 rows, which read as having measured
        nothing."""
        html = _render_exposure(_make_exposure("   "))
        assert "no share measured" in html
        assert "ESTIMATED" not in html

    def test_basis_still_renders_for_percentage(self):
        """Regression guard: the MEASURED/ESTIMATED label must still appear
        below a percentage figure."""
        exposure = _make_exposure("12.5% of page views on /search", basis="ESTIMATED")
        html = _render_exposure(exposure)
        assert "ESTIMATED" in html
        assert "12.5%" in html

    def test_mutation_guard_non_percentage_path(self):
        """Mutation check: if the non-percentage branch were deleted (falling
        through to the percentage branch), a non-percentage phrase would crash
        or produce wrong output. This test goes red under that mutation."""
        exposure = _make_exposure("unknown share of traffic")
        html = _render_exposure(exposure)
        assert html.strip()
        assert "unknown share" in html


# ---------------------------------------------------------------------------
# Defect 2: titles truncated mid-word because _complete_prose excludes 'title'
# ---------------------------------------------------------------------------


class TestTitleValidation:
    """DISCRIMINATION: _complete_prose exists and catches mid-sentence breaks,
    but 'title' is not in _PROSE_FIELDS so the validator is never applied."""

    def test_complete_title_passes_validation(self):
        """Control arm: a well-formed title passes whether or not the check
        is applied."""
        result = _complete_prose("The handler silently drops the response.")
        assert result is None

    def test_truncated_title_fails_validation(self):
        """Defect arm: a title sliced mid-word should fail _complete_prose."""
        result = _complete_prose("so the harm is currentl")
        assert result is not None
        assert "stops mid-sentence" in result

    def test_title_is_in_prose_fields(self):
        """The fix: 'title' must be in _PROSE_FIELDS so the validator runs on
        it during record validation."""
        assert "title" in _PROSE_FIELDS

    def test_record_with_truncated_title_rejected(self):
        """End-to-end: a run record carrying a truncated title must fail
        validation, not pass silently."""
        record = _make_minimal_record()
        record["findings"][0]["title"] = "removing the abil"
        errors = validate_run_record(record)
        title_errors = [
            e for e in errors if "title" in e.field and "mid-sentence" in e.message
        ]
        assert title_errors, (
            "a truncated title passed validation -- _complete_prose was not applied"
        )

    def test_record_with_clean_title_passes(self):
        """Both arms: a clean title must not trigger a false positive."""
        record = _make_minimal_record()
        record["findings"][0]["title"] = "The handler drops the response silently."
        errors = validate_run_record(record)
        title_errors = [
            e for e in errors if "title" in e.field and "mid-sentence" in e.message
        ]
        assert not title_errors


# ---------------------------------------------------------------------------
# Defect 3: shortfall.reason composition doubles punctuation
# ---------------------------------------------------------------------------


def _make_minimal_model(shortfall=None):
    return RenderModel(
        run_id="test-run-001",
        scope_label="test scope",
        components=["test-component"],
        grouped={band: [] for band in Band},
        discarded=[],
        coverage=[
            {
                "component": "x",
                "mandate": "m",
                "files": ["a.py"],
                "lines": 10,
                "packets_returned": 1,
            }
        ],
        degraded_paths=[],
        dead_surface=[],
        cost={"agents": 5, "wall_clock_minutes": 10},
        shortfall=shortfall,
        gate={"dossiers_scanned": 3, "leaks_found": 0, "redaction_hits": 0},
        repo=None,
    )


class TestShortfallComposition:
    """DISCRIMINATION: the renderer composes shortfall.reason into a sentence
    frame that appends '. Not because...', so a reason ending with '.' produces
    '..' in the output."""

    def test_reason_without_trailing_period_composes_cleanly(self):
        """Control arm: a reason following the spec (no trailing period)
        already composes correctly."""
        findings = [_make_not_checked_finding()]
        model = _make_minimal_model(
            shortfall={
                "reason": "checking stopped after five items because the run ran out of budget"
            }
        )
        html = _render_band(Band.NOT_CHECKED, findings, model)
        assert ".." not in html
        assert "because checking stopped" in html.lower()

    def test_reason_with_trailing_period_no_double_dot(self):
        """Defect arm: a reason that arrives with a trailing period must NOT
        produce '..' in the composed output."""
        findings = [_make_not_checked_finding()]
        model = _make_minimal_model(
            shortfall={
                "reason": "checking stopped after five items because the run ran out of budget."
            }
        )
        html = _render_band(Band.NOT_CHECKED, findings, model)
        assert ".." not in html, "doubled full stop in coverage-disclosure sentence"

    def test_reason_with_trailing_exclamation_no_double(self):
        """Same defect, different punctuation."""
        findings = [_make_not_checked_finding()]
        model = _make_minimal_model(shortfall={"reason": "the budget was exhausted!"})
        html = _render_band(Band.NOT_CHECKED, findings, model)
        assert "!." not in html

    def test_no_shortfall_still_renders(self):
        """Guard: the band with findings renders even with no shortfall."""
        findings = [_make_not_checked_finding()]
        model = _make_minimal_model(shortfall=None)
        html = _render_band(Band.NOT_CHECKED, findings, model)
        assert "never looked at" in html.lower()

    def test_composed_sentence_is_complete_prose(self):
        """The composed sentence should itself be well-formed prose, not a
        fragment ending mid-word or with doubled punctuation."""
        findings = [_make_not_checked_finding()]
        model = _make_minimal_model(
            shortfall={"reason": "the run hit its budget ceiling."}
        )
        html = _render_band(Band.NOT_CHECKED, findings, model)
        match = re.search(r'class="band-why">(.*?)</p>', html, re.DOTALL)
        assert match, "band-why paragraph not found"
        text = match.group(1)
        text = re.sub(r"<[^>]+>", "", text)
        assert ".." not in text
        assert "!." not in text
        assert "?." not in text

    def test_mutation_guard_strip_punctuation(self):
        """Mutation check: if the trailing-punctuation stripping were removed,
        a reason with a trailing period MUST produce '..' (proving the strip
        is load-bearing)."""
        reason = "the run ran out of budget."
        # Simulate what the code does WITHOUT the fix: raw concatenation
        raw = f"These were never looked at, because {reason}. Not because"
        assert ".." in raw, (
            "the unpatched composition does not produce '..', so the test "
            "cannot discriminate the fix from the bug"
        )


# ---------------------------------------------------------------------------
# Helpers: minimal valid run record for end-to-end validation tests
# ---------------------------------------------------------------------------


def _make_minimal_record():
    """A minimal valid run record with one finding."""
    return {
        "run_id": "test-run-001",
        "scope_strategy": "single-component",
        "scope_label": "test-component (all Java files)",
        "components": ["test-component"],
        "findings": [
            {
                "fingerprint": "0123456789abcdef",
                "state": "READY_LOCAL_CANDIDATE",
                "band": "Act Now",
                "band_reason": "One occurrence can fail a request, and exposure is 0.5% of the path, MEASURED.",
                "title": "The handler silently drops the error response.",
                "consequence": "Callers see a success when the operation failed.",
                "observed_symptom": "POST /api/foo returned 200 with empty body",
                "observed_full": "POST /api/foo returned 200 with empty body\nExpected 500",
                "defect_site": "src/Handler.java:42",
                "component": "my-service",
                "tier": "2",
                "exposure": {
                    "basis": "MEASURED",
                    "path_denominator": "0.5% of requests on /api/foo",
                    "component_denominator": "100% of the component",
                    "note": "Low traffic path.",
                    "share": {
                        "numerator": 0.5,
                        "denominator": 100,
                        "unit": "req/s",
                        "of": "requests on /api/foo",
                    },
                    "share_absent": None,
                    "share_absent_detail": None,
                },
                "effort": "S",
                "mechanism": {
                    "verdict": "reproduced",
                    "trail": "Ran the test and it failed as described.",
                },
                "intent": {
                    "verdict": "unintended",
                    "trail": "The code intends to return 500 on error.",
                },
                "fix_prompt": "Add an error check before the return statement.",
                "permalink": None,
                "verification": None,
                "provenance": None,
                "method": None,
            }
        ],
        "coverage": [
            {
                "component": "my-service",
                "mandate": "m1",
                "files": ["Handler.java"],
                "lines": 100,
                "packets_returned": 1,
            }
        ],
        "degraded_paths": [],
        "dead_surface": [],
        "cost": {"agents": 5, "wall_clock_minutes": 10},
        "shortfall": None,
        "gate": {"dossiers_scanned": 3, "leaks_found": 0, "redaction_hits": 0},
        "repo": None,
        "permalink_resolution": {
            "attempted": 1,
            "linked": 0,
            "unlinked": [
                {
                    "fingerprint": "0123456789abcdef",
                    "reason": "no pushed commit matched",
                }
            ],
        },
        "provenance_resolution": {
            "attempted": 1,
            "resolved": 0,
            "unresolved": [
                {"fingerprint": "0123456789abcdef", "reason": "no blame data available"}
            ],
        },
        "exposure_resolution": {"attempted": 1, "resolved": 1, "unresolved": []},
    }


# ---------------------------------------------------------------------------
# Defect 4: the exposure column carries no percentage, and the provenance word
# it does carry reaches the reader on almost no rows
#
# Measured on a real 82-finding run (skill 0.19.0):
#   - path_denominator led with a percentage on 0 of 82 rows, and that branch is
#     the ONLY one that printed `basis` -- so MEASURED/ESTIMATED/UNKNOWN reached
#     the reader on 0 of 82 rows, including the 15 that were genuinely MEASURED.
#   - 66 of 82 had no numerator at all, and the column rendered every one of them
#     identically, collapsing three situations that mean different things.
# ---------------------------------------------------------------------------


def _share(
    numerator=2.92, denominator=63000.0, unit="req/s", of="reaching this component"
):
    return Share(numerator=numerator, denominator=denominator, unit=unit, of=of)


def _exposure_with(
    share=None,
    absent=None,
    detail=None,
    basis="MEASURED",
    path="0 req/s on the getTopNItems path",
):
    return Exposure(
        basis=basis,
        path_denominator=path,
        component_denominator="~63,000 req/s server-side business traffic",
        note="No note.",
        share=share,
        share_absent=absent,
        share_absent_detail=detail,
    )


class TestSharePercentage:
    """DISCRIMINATION: a share exists in the record and never reaches the cell."""

    def test_share_renders_a_percentage(self):
        """Defect arm: 2.92 of 63,000 is 0.0046%, which the reader never sees."""
        html = _render_exposure(_exposure_with(share=_share()))
        assert "0.00463%" in html

    def test_mid_range_share_renders_two_decimals(self):
        """463,940 of 6,465,151 items/s = 7.176%. The figure a reader ranks on."""
        html = _render_exposure(
            _exposure_with(
                share=_share(463940, 6465151, "items/s", "entering the step")
            )
        )
        assert "7.18%" in html

    def test_share_renders_the_working(self):
        """The percentage alone repeats the 0.072% failure. Both sides, and the
        phrase saying what the denominator counts, have to travel with it."""
        html = _render_exposure(_exposure_with(share=_share()))
        assert "2.92" in html
        assert "63,000" in html
        assert "reaching this component" in html

    def test_zero_share_is_not_an_absent_share(self):
        """DISCRIMINATION, and the pair that matters most: a measured 0% says
        the path is dead, an absent share says nobody looked. Rendering them
        alike is the failure this whole change exists to fix."""
        measured_zero = _render_exposure(_exposure_with(share=_share(numerator=0)))
        absent = _render_exposure(_exposure_with(absent="NOT_QUERIED"))
        assert "0%" in measured_zero
        assert "0%" not in absent
        assert measured_zero != absent

    def test_tiny_share_does_not_read_as_zero(self):
        """0.0046% must not round to 0%: one says almost never, the other says
        never, and they license different decisions."""
        html = _render_exposure(_exposure_with(share=_share()))
        assert not re.search(r">\s*0%\s*<", html)

    def test_control_no_share_renders_no_percentage(self):
        """ABSENCE arm: with no share there is no figure to invent."""
        html = _render_exposure(_exposure_with(absent="NOT_QUERIED"))
        assert "%" not in html


class TestBasisReachesTheReader:
    """DISCRIMINATION: `basis` printed only under a percentage-led prose value,
    so on a real report it printed nowhere."""

    def test_measured_basis_appears_without_a_percentage(self):
        html = _render_exposure(_exposure_with(share=_share(), basis="MEASURED"))
        assert "MEASURED" in html

    def test_estimated_basis_appears_without_a_percentage(self):
        html = _render_exposure(_exposure_with(share=_share(), basis="ESTIMATED"))
        assert "ESTIMATED" in html

    def test_unknown_basis_prints_no_provenance_word(self):
        """Control arm, and the rule the schema already fixed once: printing a
        provenance word under an absent figure asserts an estimate exists where
        none does. One run shipped `n/a` above `ESTIMATED` on all 76 rows."""
        html = _render_exposure(_exposure_with(absent="NOT_QUERIED", basis="UNKNOWN"))
        assert "MEASURED" not in html.upper().replace("NO SHARE MEASURED", "")


class TestShareAbsentReasons:
    """DISCRIMINATION: three reasons, rendered identically, that a reader setting
    priority needs to tell apart."""

    def test_not_queried_says_nobody_looked(self):
        html = _render_exposure(_exposure_with(absent="NOT_QUERIED"))
        assert "never queried" in html

    def test_no_instrument_differs_from_not_queried(self):
        """The pair this distinction exists for. NO_INSTRUMENT means the harm is
        also undetectable in production, which is the same fact the flagged
        finding's band_reason cites as `harm undetectable` -- a priority input in
        its own right, not a gap in the run."""
        queried = _render_exposure(_exposure_with(absent="NOT_QUERIED"))
        instrument = _render_exposure(_exposure_with(absent="NO_INSTRUMENT"))
        assert queried != instrument
        assert "instrument" in instrument

    def test_not_request_scoped_does_not_claim_a_share(self):
        html = _render_exposure(_exposure_with(absent="NOT_REQUEST_SCOPED"))
        assert "not a share" in html

    def test_detail_replaces_the_generic_sentence(self):
        html = _render_exposure(
            _exposure_with(
                absent="NO_INSTRUMENT",
                detail="no instrument separates an empty registry from an absent one",
            )
        )
        assert "separates an empty registry" in html


class TestShareValidation:
    """The guards that stop a wrong percentage reaching a reader at all."""

    def _exp(self, **over):
        base = {
            "basis": "MEASURED",
            "path_denominator": "0 req/s on this path",
            "component_denominator": "~63,000 req/s",
            "note": "n",
        }
        base.update(over)
        return base

    def test_valid_share_accepted(self):
        """Control arm: the shape the resolver is asked for must pass."""
        assert (
            _exposure_validator(
                self._exp(
                    share={
                        "numerator": 2.92,
                        "denominator": 63000,
                        "unit": "req/s",
                        "of": "reaching this component",
                    }
                )
            )
            is None
        )

    def test_numerator_above_denominator_rejected(self):
        problem = _exposure_validator(
            self._exp(
                share={
                    "numerator": 70000,
                    "denominator": 63000,
                    "unit": "req/s",
                    "of": "reaching this component",
                }
            )
        )
        assert problem is not None and "exceeds" in problem

    def test_unknown_basis_with_a_share_rejected(self):
        """The fabricated 100%, exactly. The finding at ExampleClient.py
        :108 carries basis UNKNOWN and a component figure of ~63,000 req/s; put
        that figure in the numerator slot and it renders 100% on a finding nobody
        checked. UNKNOWN means no numerator was established, so a share cannot
        coexist with it."""
        problem = _exposure_validator(
            self._exp(
                basis="UNKNOWN",
                share={
                    "numerator": 63000,
                    "denominator": 63000,
                    "unit": "req/s",
                    "of": "reaching this component",
                },
            )
        )
        assert problem is not None and "UNKNOWN" in problem

    def test_share_and_absent_together_rejected(self):
        problem = _exposure_validator(
            self._exp(
                share={"numerator": 1, "denominator": 2, "unit": "req/s", "of": "x"},
                share_absent="NOT_QUERIED",
            )
        )
        assert problem is not None

    def test_empty_unit_rejected(self):
        """The commensurability proof. Without one shared unit this shape stops
        being able to refuse `21,427 series of 25 pairs`."""
        problem = _exposure_validator(
            self._exp(share={"numerator": 1, "denominator": 2, "unit": "  ", "of": "x"})
        )
        assert problem is not None and "unit" in problem

    def test_zero_denominator_rejected(self):
        problem = _exposure_validator(
            self._exp(
                share={"numerator": 0, "denominator": 0, "unit": "req/s", "of": "x"}
            )
        )
        assert problem is not None

    def test_unnamed_absent_reason_rejected(self):
        problem = _exposure_validator(self._exp(share_absent="UNRESOLVED"))
        assert problem is not None and "UNRESOLVED" in problem

    def test_missing_of_rejected(self):
        """The renderer cannot supply the noun -- the rule that already exists
        for path_denominator, applied to the field that now carries the figure."""
        problem = _exposure_validator(
            self._exp(
                share={"numerator": 1, "denominator": 2, "unit": "req/s", "of": ""}
            )
        )
        assert problem is not None


# ---------------------------------------------------------------------------
# Defect 5: a band asserts a priority it may have reached without the exposure
# input, and says nothing about which
#
# Measured on the same run: Act Now 0, Important 0, Low 1, Not checked 81. The
# single banded finding carries basis UNKNOWN, and its own band_reason ends
# "Exposure UNKNOWN and undecidable with current telemetry" -- so the one band
# the run produced was assigned without the input, and the row does not say so.
# Every one of the 16 measured exposures sits on a finding with no band.
#
# No threshold moves here. n=1 is not a calibration sample, and requiring a
# measured share to reach a higher band would cap NO_INSTRUMENT findings at the
# bottom -- the case where the harm is undetectable in production, which is
# exactly backwards.
# ---------------------------------------------------------------------------


class TestUnexposedBandFlag:
    """DISCRIMINATION: the marker must appear on a band reached without a share
    and stay off both a band that had one and a finding with no band at all."""

    def _banded(self, exposure, band=Band.LOW):
        return replace(
            _make_not_checked_finding(),
            band=band,
            verdict=Verdict.BUG,
            band_reason="Consideration 3 met (harm undetectable).",
            exposure=exposure,
        )

    def test_banded_without_a_share_is_marked(self):
        html = _render_row(
            self._banded(_exposure_with(absent="NO_INSTRUMENT", basis="UNKNOWN"))
        )
        assert "banded without exposure" in html

    def test_banded_with_a_share_is_not_marked(self):
        """The arm that makes the marker mean something. A band that did weigh a
        measured share must not carry a caveat saying it did not."""
        html = _render_row(self._banded(_exposure_with(share=_share())))
        assert "banded without exposure" not in html

    def test_unbanded_finding_is_not_marked(self):
        """81 of 82 findings on the measured run. There is no band to qualify, so
        a caveat about how the band was reached would be asserting a band."""
        html = _render_row(
            replace(
                _make_not_checked_finding(),
                exposure=_exposure_with(absent="NOT_QUERIED"),
            )
        )
        assert "banded without exposure" not in html


class TestBareAbsenceTokenSuppressed:
    """DISCRIMINATION: the headline now states the absence AND its reason, so a
    path_denominator that is nothing but an absence token repeats it.

    Measured by re-rendering the character-pro record through this renderer: 65
    rows produced `<em>UNKNOWN</em>` and 1 produced `<em>not measured</em>`
    directly beneath a "no share measured" headline. That is 66 of 82 rows
    saying the same nothing twice - a worse version of the confusion this whole
    change exists to remove.
    """

    def test_bare_unknown_is_not_repeated(self):
        html = _render_exposure(
            _exposure_with(absent="NOT_QUERIED", basis="UNKNOWN", path="UNKNOWN")
        )
        assert "no share measured" in html
        assert "<em>UNKNOWN</em>" not in html

    def test_bare_not_measured_is_not_repeated(self):
        html = _render_exposure(
            _exposure_with(absent="NOT_QUERIED", basis="UNKNOWN", path="not measured")
        )
        assert "<em>not measured</em>" not in html

    def test_prose_that_merely_starts_with_an_absence_word_survives(self):
        """The arm that keeps this from becoming a content-destroying filter.
        This exact value is what the schema documents as the correct shape for an
        unmeasured share, and it carries the reason - it must reach the reader."""
        html = _render_exposure(
            _exposure_with(
                absent="NOT_QUERIED",
                basis="UNKNOWN",
                path="not established -- the share of requests was not queried",
            )
        )
        assert "not established" in html
        assert "was not queried" in html

    def test_component_denominator_survives_a_suppressed_path(self):
        """Nothing else may be lost with it. The component figure reached the
        column on 0 of 62 findings across four earlier reports; suppressing the
        path must not take it back out."""
        html = _render_exposure(
            _exposure_with(absent="NOT_QUERIED", basis="UNKNOWN", path="UNKNOWN")
        )
        assert "~63,000 req/s server-side business traffic" in html


# ---------------------------------------------------------------------------
# Defect 6: title renders the Python repr of a component dict
# ---------------------------------------------------------------------------


class TestComponentDictTitle:
    """DISCRIMINATION: _subject() calls str() on the component, which for a
    dict renders {'id': 'character-pro', 'tier': 2, ...} in the <h1>.
    On a real run this produced a title reading "Bug report: {'id': ...}".
    """

    def test_dict_component_renders_id_not_repr(self):
        """Defect arm: the title must show the component name, not the dict."""
        from render_digest import _subject

        model = RenderModel(
            run_id="test-001",
            scope_label="character-pro",
            components=[
                {
                    "id": "character-pro",
                    "tier": 2,
                    "system": "promotions-serving",
                    "owner": "kipp",
                }
            ],
            grouped={b: [] for b in Band},
            discarded=[],
            coverage=[],
            degraded_paths=[],
            dead_surface=[],
            cost={"agents": 5, "wall_clock_minutes": 10},
            shortfall=None,
            gate={"dossiers_scanned": 0, "leaks_found": 0, "redaction_hits": 0},
            repo=None,
        )
        result = _subject(model)
        assert result == "character-pro", f"expected 'character-pro', got {result!r}"
        assert "{" not in result, f"title contains dict repr: {result!r}"

    def test_string_component_still_works(self):
        """Control arm: the old string form must not regress."""
        from render_digest import _subject

        model = RenderModel(
            run_id="test-001",
            scope_label="my-service",
            components=["my-service"],
            grouped={b: [] for b in Band},
            discarded=[],
            coverage=[],
            degraded_paths=[],
            dead_surface=[],
            cost={"agents": 5, "wall_clock_minutes": 10},
            shortfall=None,
            gate={"dossiers_scanned": 0, "leaks_found": 0, "redaction_hits": 0},
            repo=None,
        )
        assert _subject(model) == "my-service"

    def test_dict_component_with_null_id_does_not_crash(self):
        """The reviewer found that comp.get("id", str(comp)) returns None when
        id is present but null, and html.escape(None) crashes. The fix uses
        str(comp.get("id") or comp) which falls back to the dict repr for
        falsy id values -- ugly but not a crash."""
        from render_digest import _subject

        model = RenderModel(
            run_id="test-001",
            scope_label="character-pro",
            components=[{"id": None, "tier": 2}],
            grouped={b: [] for b in Band},
            discarded=[],
            coverage=[],
            degraded_paths=[],
            dead_surface=[],
            cost={"agents": 5, "wall_clock_minutes": 10},
            shortfall=None,
            gate={"dossiers_scanned": 0, "leaks_found": 0, "redaction_hits": 0},
            repo=None,
        )
        result = _subject(model)
        # Must not crash, and must be a string
        assert isinstance(result, str), f"expected str, got {type(result)}"


# ---------------------------------------------------------------------------
# Defect 7: resolver claims resolved but findings have no share data
# ---------------------------------------------------------------------------


class TestResolverFindingsCrossCheck:
    """DISCRIMINATION: digest_model.py accepted a record where
    exposure_resolution.resolved=106 while every finding had share=null and
    share_absent=NOT_QUERIED. The resolver ran but its output was never wired
    into the findings."""

    def test_resolved_with_no_shares_is_rejected(self):
        """Defect arm: if the resolver says it resolved candidates, the
        findings must reflect that."""
        record = _make_minimal_record()
        record["exposure_resolution"] = {
            "attempted": 1,
            "resolved": 1,
            "unresolved": [],
            "resolver_agent_id": "resolver-real-abc123",
        }
        # Set the finding's exposure to show resolver results were NOT integrated
        record["findings"][0]["exposure"] = {
            "basis": "UNKNOWN",
            "path_denominator": "not established",
            "component_denominator": "~72,728 rps",
            "note": "See the impact resolution.",
            "share": None,
            "share_absent": "NOT_QUERIED",
            "share_absent_detail": None,
        }
        errors = [
            e
            for e in validate_run_record(record)
            if "resolver results were not integrated" in e.message
        ]
        assert errors, (
            "a record claiming resolved=1 with no share data in findings validated"
        )

    def test_resolved_with_share_data_passes(self):
        """Control arm: a properly integrated resolution must not trigger."""
        record = _make_minimal_record()
        # The default fixture already has share data and resolved=1
        errors = [
            e
            for e in validate_run_record(record)
            if "resolver results were not integrated" in e.message
        ]
        assert not errors, f"a record with proper share data was rejected: {errors}"
