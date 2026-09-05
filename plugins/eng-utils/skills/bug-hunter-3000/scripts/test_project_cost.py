"""Tests for the pre-dispatch packet-volume projection.

The projection this covers decides whether a run is dispatched as-is, bounded, or
split. It is therefore code, not documentation, and it earns tests: a wrong number
here does not fail loudly, it produces a run that degrades at the verification stage
having promised it would not.

The defect these tests were written against (jbrooksbartlett-a7cqk): the projection
was `finders * 0.055`, a single term keyed on finder count. Roughly 90% of returned
volume scales with CANDIDATES FOUND, not with finders, so the formula silently
mis-projected on any component whose candidate density differed from the single run
it was calibrated on.

Every test below fails against that one-term formula. That is the point -- several of
them are written specifically so that a model ignoring candidate density cannot pass.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import project_cost  # noqa: E402


# The 2026-08-28 live run, the only run with both numbers recorded.
OBSERVED_FINDERS = 32
OBSERVED_CANDIDATES = 116
OBSERVED_DENSITY = OBSERVED_CANDIDATES / OBSERVED_FINDERS  # 3.625


class TestVolumeScalesWithCandidates:
    """The core defect. Finder count alone must not determine the projection."""

    def test_same_finders_different_density_gives_different_volume(self):
        sparse = project_cost.project(finders=20, candidates_per_finder=1.0)
        dense = project_cost.project(finders=20, candidates_per_finder=6.0)
        assert dense.expected_kb > sparse.expected_kb, (
            "Identical finder counts at 1 vs 6 candidates each projected the same "
            "volume. This is exactly the one-term defect: the dominant driver of "
            "packet volume is not being modelled."
        )

    def test_density_difference_is_material_not_cosmetic(self):
        """A 6x density difference must move the projection by more than rounding.

        Guards against a 'fix' that adds a candidate term with a token coefficient
        so the previous test passes while the projection stays finder-dominated.
        """
        sparse = project_cost.project(finders=20, candidates_per_finder=1.0)
        dense = project_cost.project(finders=20, candidates_per_finder=6.0)
        ratio = dense.expected_kb / sparse.expected_kb
        assert ratio > 2.5, (
            f"6x the candidates moved the projection only {ratio:.2f}x. The candidate "
            f"term exists but is not carrying the volume the measurement attributes "
            f"to it (~90%)."
        )

    def test_candidate_term_dominates_at_observed_density(self):
        """At the density actually measured, most volume must come from candidates."""
        share = project_cost.candidate_driven_share(
            candidates_per_finder=OBSERVED_DENSITY
        )
        assert 0.80 <= share <= 0.97, (
            f"At the observed density of {OBSERVED_DENSITY:.2f} candidates per finder, "
            f"the candidate term accounts for {share:.1%} of projected volume. The "
            f"measurement puts it near 90%."
        )


class TestReproducesTheMeasuredRun:
    """The model must land on the run it is calibrated from."""

    def test_matches_observed_run_within_tolerance(self):
        got = project_cost.project(
            finders=OBSERVED_FINDERS, candidates_per_finder=OBSERVED_DENSITY
        )
        expected_kb = OBSERVED_FINDERS * 68.7  # measured mean per finder
        assert got.expected_kb == pytest.approx(expected_kb, rel=0.10), (
            f"Projected {got.expected_kb:.0f}KB for the 2026-08-28 run; the measured "
            f"mean of 68.7KB per finder over {OBSERVED_FINDERS} finders is "
            f"{expected_kb:.0f}KB."
        )

    def test_old_formula_understated_the_measured_run(self):
        """Documents the size of the error being corrected."""
        old_kb = OBSERVED_FINDERS * 55.0
        new = project_cost.project(
            finders=OBSERVED_FINDERS, candidates_per_finder=OBSERVED_DENSITY
        )
        assert new.expected_kb > old_kb * 1.15, (
            "The corrected projection should exceed the old one by a margin that "
            "matters. If it does not, either the correction is too timid or the old "
            "formula was not actually wrong."
        )


class TestRangeRatherThanPoint:
    """Density is unknown before dispatch, so a point estimate overclaims."""

    #: A band narrower than this is not representing single-run uncertainty, it is
    #: decorating a point estimate. Chosen, not measured -- see MIN_BAND_RATIO in
    #: project_cost.py, which the code and these tests share so they cannot drift.
    MIN_RATIO = project_cost.MIN_BAND_RATIO

    def test_projection_without_density_returns_a_range(self):
        r = project_cost.project(finders=25)
        assert r.low_kb < r.expected_kb < r.high_kb, (
            "With no density supplied the projection must bracket its own "
            "uncertainty. A bare point estimate is what made the old formula look "
            "authoritative while being wrong."
        )

    def test_range_without_density_is_wide_enough_to_mean_something(self):
        """Ordering alone is a vacuous assertion: +/-1% satisfies it.

        Added after a mutation sweep found the previous test passed with the band
        collapsed to 0.99x-1.01x of the point estimate -- i.e. it did not test the
        band at all.
        """
        r = project_cost.project(finders=25)
        ratio = r.high_kb / r.low_kb
        assert ratio >= self.MIN_RATIO, (
            f"Range spans only {ratio:.2f}x from low to high. The coefficients come "
            f"from ONE run; a band this tight claims a precision the calibration "
            f"cannot support."
        )

    def test_band_is_two_sided_not_just_a_long_upper_tail(self):
        """The low end must sit meaningfully below expected, not hug it.

        A mutation sweep found the low prior could be raised until the band was
        effectively one-sided while the low-to-high ratio stayed above its floor,
        because the high end is far out. That direction is the benign one -- it
        overstates the floor rather than understating the ceiling -- but an
        unpinned constant drifts, and the next edit may not be benign.
        """
        r = project_cost.project(finders=25)
        assert r.expected_kb / r.low_kb >= 1.5, (
            f"Low end is {r.expected_kb / r.low_kb:.2f}x below expected. The band "
            f"has collapsed on the low side and is no longer bracketing anything."
        )

    def test_supplied_density_still_carries_a_wide_range(self):
        """Even a measured density is one sample, not a guarantee."""
        r = project_cost.project(finders=25, candidates_per_finder=3.6)
        ratio = r.high_kb / r.low_kb
        assert ratio >= self.MIN_RATIO, (
            f"Supplying a density collapsed the band to {ratio:.2f}x. A density "
            f"taken from one prior run does not make the projection precise."
        )

    def test_high_end_reaches_the_worst_packet_observed(self):
        """At LOW density, where the clamp is the only thing enforcing this.

        The previous version of this test used the default density, whose prior high
        (8.0 candidates per finder) already exceeded the observed maximum -- so it
        passed with the clamp deleted entirely. Density 1.0 puts the unclamped high
        at ~35KB per finder, well under the 76KB actually seen, so only the clamp
        can satisfy it.
        """
        r = project_cost.project(finders=10, candidates_per_finder=1.0)
        assert r.high_kb >= 10 * project_cost.OBSERVED_MAX_KB_PER_FINDER, (
            "The observed maximum packet was 76KB. On a sparse component the model "
            "projects ~35KB and the high end must still reach 76KB: a bound that "
            "sits below a packet size that has already happened is not a bound."
        )

    def test_clamp_is_load_bearing_at_low_density(self):
        """Proves the previous test is exercising the clamp rather than the prior."""
        unclamped_high = (
            10
            * (project_cost.FIXED_KB_PER_FINDER + 1.0 * project_cost.KB_PER_CANDIDATE)
            * 1.55
        )
        assert unclamped_high < 10 * project_cost.OBSERVED_MAX_KB_PER_FINDER, (
            "At density 1.0 the model's own high end already exceeds the observed "
            "maximum, so the clamp is not being tested and this fixture is stale."
        )


class TestInputGuards:
    def test_negative_finders_rejected(self):
        with pytest.raises(ValueError):
            project_cost.project(finders=-1)

    def test_negative_density_rejected(self):
        with pytest.raises(ValueError):
            project_cost.project(finders=10, candidates_per_finder=-1.0)

    def test_zero_finders_is_zero_volume_not_an_error(self):
        """A component with nothing to search is legitimate, not a bad input."""
        r = project_cost.project(finders=0)
        assert r.expected_kb == 0
        assert r.will_degrade is False


class TestDegradationWarning:
    def test_warns_when_projection_exceeds_survivable_volume(self):
        # index_to_disk=False models the INLINE case, which is what the threshold was
        # measured on, and what a finder falls back to if it cannot write its packet.
        r = project_cost.project(
            finders=42, candidates_per_finder=OBSERVED_DENSITY, index_to_disk=False
        )
        assert r.will_degrade is True
        assert r.warning, "A degrading run must carry a sentence saying so."

    def test_does_not_warn_on_a_small_run(self):
        r = project_cost.project(finders=6, candidates_per_finder=OBSERVED_DENSITY)
        assert r.will_degrade is False

    def test_warning_triggers_on_volume_not_finder_count(self):
        """A few finders on a very dense component must still warn.

        The old guidance keyed the warning to 'roughly 30 finders'. Finder count is
        the wrong trigger for the same reason it is the wrong projection.
        """
        r = project_cost.project(
            finders=12, candidates_per_finder=25.0, index_to_disk=False
        )
        assert r.will_degrade is True, (
            "12 finders returning 25 candidates each is ~5MB of packets. A warning "
            "keyed to finder count would stay silent through it."
        )


class TestCalibrationProvenance:
    """The coefficients are single-run estimates. The script must say so."""

    def test_coefficients_declare_their_basis(self):
        basis = project_cost.CALIBRATION["basis"]
        assert basis in {"MEASURED", "ESTIMATED", "UNKNOWN"}

    def test_calibration_names_its_single_source_run(self):
        assert project_cost.CALIBRATION.get("source_run"), (
            "A coefficient with no named source cannot be re-derived or challenged."
        )

    def test_calibration_records_that_it_cannot_be_re_derived(self):
        """The per-packet data no longer exists; that must not be discovered twice."""
        note = project_cost.CALIBRATION.get("re_derivable")
        assert note is False, (
            "The 2026-08-28 packets were never written to disk and the orchestrator "
            "context that held them is gone. Recording this stops the next person "
            "repeating a four-source search that cannot succeed."
        )


class TestTheOldConstantIsGone:
    def test_old_formula_is_not_presented_as_an_instruction(self):
        """The one-term formula must not appear as a runnable indented block.

        Naming it inline while explaining why it was wrong is legitimate and the
        rationale is worth keeping. What must not survive is the form a run would
        follow: an indented code block assigning packet volume from finder count.
        """
        ref = (SCRIPTS.parent / "references" / "mandate-partitioning.md").read_text()
        offending = [
            line
            for line in ref.splitlines()
            if re.match(r"^\s{4,}packet_mb\s*=\s*finders\s*\*", line)
        ]
        assert not offending, (
            f"The one-term formula is still printed as an instruction block in "
            f"mandate-partitioning.md: {offending}. A run following the prose will "
            f"use it regardless of what the script does."
        )

    def test_the_correction_is_explained_not_just_applied(self):
        """Silently swapping the formula loses why it was wrong."""
        ref = (SCRIPTS.parent / "references" / "mandate-partitioning.md").read_text()
        assert "0.055" in ref, (
            "The old constant is not mentioned anywhere. Someone comparing an old "
            "run's projection against a new one needs to find out here why they "
            "differ, rather than assuming one of the runs was broken."
        )

    def test_script_invocation_is_the_runnable_block(self):
        ref = (SCRIPTS.parent / "references" / "mandate-partitioning.md").read_text()
        runnable = [
            line
            for line in ref.splitlines()
            if re.match(r"^\s{4,}python3 scripts/project_cost\.py", line)
        ]
        assert runnable, (
            "The reference names the script but never shows it as a runnable block, "
            "so there is nothing for a run to copy."
        )

    def test_reference_points_at_the_script(self):
        ref = (SCRIPTS.parent / "references" / "mandate-partitioning.md").read_text()
        assert "project_cost.py" in ref, (
            "The reference must name the script, or the formula drifts back into "
            "prose -- which is how index_to_disk came to be defined nowhere."
        )


class TestRunnableAsAScript:
    def test_cli_prints_a_projection(self):
        out = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "project_cost.py"),
                "--finders",
                "20",
                "--candidates-per-finder",
                "3.6",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "MB" in out.stdout or "KB" in out.stdout

    def test_cli_reports_degradation_risk(self):
        out = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "project_cost.py"),
                "--finders",
                "42",
                "--candidates-per-finder",
                "3.6",
                "--no-index-to-disk",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "degrade" in out.stdout.lower()


class TestDiskIndexChangesWhatIsProjected:
    """The two fixes interact, and the interaction inverts the warning.

    project_cost.py projects packet volume as a proxy for the ORCHESTRATOR'S CONTEXT.
    Once the finder writes its packet to disk (jbrooksbartlett-n26cg) that proxy is
    wrong: the packet volume still exists, but it lands on a filesystem rather than in
    a context window. Left unchanged, the projection warns that a run will degrade
    when it will not -- and an operator acting on that warning bounds or splits a run
    for no reason, losing coverage to a false alarm.

    Measured 2026-08-28 on the test fixture: an index is 813 bytes against a
    22,221-byte packet, 3.7%. For the 32-finder run that actually exhausted a context,
    that is 25KB carried instead of 2,198KB.
    """

    def test_disk_index_run_is_not_projected_to_degrade(self):
        r = project_cost.project(
            finders=OBSERVED_FINDERS,
            candidates_per_finder=OBSERVED_DENSITY,
            index_to_disk=True,
        )
        assert r.will_degrade is False, (
            "The run that exhausted a context inline is still projected to degrade "
            "with the packets written to disk. That is a false alarm on exactly the "
            "run the disk index was built to rescue."
        )

    def test_inline_run_of_the_same_size_still_degrades(self):
        """Both arms: the warning must still fire where it should."""
        r = project_cost.project(
            finders=OBSERVED_FINDERS,
            candidates_per_finder=OBSERVED_DENSITY,
            index_to_disk=False,
        )
        assert r.will_degrade is True

    def test_context_cost_is_far_below_disk_volume(self):
        r = project_cost.project(finders=32, candidates_per_finder=3.6,
                                 index_to_disk=True)
        # At most a fifth. The measured ratio is a tenth; the bound is loose enough
        # that a future re-calibration on a second real packet does not fail this
        # test for moving a few points, and tight enough that losing the separation
        # entirely does.
        assert r.context_kb <= r.expected_kb / 5, (
            "Context cost is not materially below packet volume, so either the index "
            "ratio is wrong or the two are not actually being separated."
        )

    def test_disk_volume_is_still_reported(self):
        """Writing to disk does not make the bytes free -- they are still produced."""
        r = project_cost.project(finders=32, candidates_per_finder=3.6,
                                 index_to_disk=True)
        assert r.expected_kb > 1000

    def test_default_matches_what_the_skill_now_does(self):
        """The skill writes to disk. A default that models the old behaviour would
        warn on every run."""
        assert project_cost.project(finders=32, candidates_per_finder=3.6).will_degrade is False
