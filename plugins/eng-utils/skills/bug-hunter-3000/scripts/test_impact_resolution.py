"""Tests for the impact-resolution accounting block and the two-denominator column.

Every test has BOTH ARMS: a case that passes under the defect and a case that
fails, so each test discriminates the fix from the bug. The label ABSENCE vs
DISCRIMINATION is stated in each class docstring.

Why these two live together: the accounting block makes impact figures arrive,
and the column change makes them readable. Shipping the first without the second
produces MORE bare percentages with no "of what", which the skill's own design
history lists as a measured failure.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from digest_model import Band, Exposure, validate_run_record
from render_digest import _render_exposure

from test_render_digest import _make_minimal_record


def _resolution(attempted=1, resolved=1, unresolved=None, resolver_agent_id=None):
    """A well-formed block.

    `resolver_agent_id` became required on 2026-08-28 (jbrooksbartlett-tstqk), after
    an orchestrator queried the metrics itself instead of dispatching the resolver.
    It defaults to a plausible id here so these tests keep exercising what they were
    written for; the field has its own coverage in test_bypass_and_masthead.py.
    """
    return {
        "attempted": attempted,
        "resolved": resolved,
        "unresolved": unresolved if unresolved is not None else [],
        "resolver_agent_id": resolver_agent_id or "aimpact-resolver-0123456789abcdef",
    }


def _with_resolution(record, block):
    record["exposure_resolution"] = block
    return record


# ---------------------------------------------------------------------------
# 1. exposure_resolution: proof the lookup was ATTEMPTED, separate from outcome
# ---------------------------------------------------------------------------


class TestExposureResolutionBlock:
    """DISCRIMINATION: today nothing distinguishes 'queried, no instrumentation'
    from 'never queried'. On real runs the column was almost entirely an absence
    while the rule says UNKNOWN is legitimate only after a query was attempted,
    and no validator stood behind that rule. Counts are canonical in
    references/design-history-and-failed-approaches.md section 8."""

    def test_well_formed_block_passes(self):
        """Control arm: a correct block must not trigger a false positive."""
        record = _with_resolution(_make_minimal_record(), _resolution())
        errors = [
            e for e in validate_run_record(record) if "exposure_resolution" in e.field
        ]
        assert not errors, f"a well-formed block was rejected: {errors}"

    def test_missing_block_is_rejected(self):
        """Defect arm: a record that omits the block entirely must fail. If the
        field is optional, a run can skip the lookup and render a clean page."""
        record = _make_minimal_record()
        record.pop("exposure_resolution", None)
        errors = [
            e for e in validate_run_record(record) if "exposure_resolution" in e.field
        ]
        assert errors, "a record with no exposure_resolution block validated"

    def test_attempted_below_finding_count_is_rejected(self):
        """Defect arm, the check that makes the block worth having: a block
        claiming 0 attempts beside 1 finding must not validate. This is the
        shape of the run that shipped 64 unexplained nulls."""
        record = _with_resolution(
            _make_minimal_record(), _resolution(attempted=0, resolved=0)
        )
        # NOT just "an error mentioning the field" -- the schema rejects unknown
        # keys by name, so that assertion is satisfied by the field not existing
        # yet and discriminates nothing.
        errors = [
            e
            for e in validate_run_record(record)
            if e.field == "exposure_resolution.attempted" and "finding" in e.message
        ]
        assert errors, "attempted=0 beside 1 finding validated"

    def test_outcomes_must_account_for_every_attempt(self):
        """Defect arm: {attempted: 1, resolved: 0, unresolved: []} is
        arithmetically impossible and is the original bug wearing the new
        field's clothes."""
        record = _with_resolution(
            _make_minimal_record(), _resolution(attempted=1, resolved=0, unresolved=[])
        )
        errors = [
            e
            for e in validate_run_record(record)
            if e.field == "exposure_resolution" and "accounts for" in e.message
        ]
        assert errors, "a block that accounts for 0 of 1 attempts validated"

    def test_unresolved_entry_needs_a_reason(self):
        """Defect arm: an unresolved candidate with no reason tells a reader
        nothing, which is the state the block exists to replace."""
        record = _with_resolution(
            _make_minimal_record(),
            _resolution(
                attempted=1,
                resolved=0,
                unresolved=[{"fingerprint": "0123456789abcdef"}],
            ),
        )
        errors = [
            e
            for e in validate_run_record(record)
            if e.field == "exposure_resolution" and "reason" in e.message
        ]
        assert errors, "an unresolved entry with no reason validated"

    def test_unresolved_with_reason_passes(self):
        """Control arm: a properly explained failure to resolve is a legitimate
        result and must pass. 'Nobody could measure this' is useful output."""
        record = _with_resolution(
            _make_minimal_record(),
            _resolution(
                attempted=1,
                resolved=0,
                unresolved=[
                    {
                        "fingerprint": "0123456789abcdef",
                        "reason": "no series exists for this path; confirmed against production",
                    }
                ],
            ),
        )
        errors = [
            e for e in validate_run_record(record) if "exposure_resolution" in e.field
        ]
        assert not errors, f"an explained failure was rejected: {errors}"


# ---------------------------------------------------------------------------
# 2. The column drops the component denominator, on BOTH branches
# ---------------------------------------------------------------------------


def _exposure(path, component, basis="MEASURED"):
    return Exposure(
        basis=basis,
        path_denominator=path,
        component_denominator=component,
        note="No note.",
    )


class TestTwoDenominatorColumn:
    """DISCRIMINATION: _render_exposure renders only path_denominator on both
    branches, so the component denominator never reached a reader. On one real
    finding the two point in OPPOSITE directions -- '100% of process
    terminations' shown while '0% of request traffic' is dropped. Counts are
    canonical in references/design-history-and-failed-approaches.md section 8."""

    def test_percentage_branch_carries_both(self):
        """Defect arm, the live instance from a real report. The reader sees
        100% and the component-level truth of 0% is invisible."""
        html = _render_exposure(
            _exposure(
                "100% of process terminations on the production branch",
                "0% of request traffic",
                basis="ESTIMATED",
            )
        )
        assert "100%" in html
        assert "0% of request traffic" in html, (
            "the component denominator was dropped; the column shows 100% and hides 0%"
        )

    def test_prose_branch_carries_both(self):
        """Defect arm: the non-percentage branch, fixed by PR #126 to render the
        path denominator, still drops the component denominator."""
        html = _render_exposure(
            _exposure(
                "database reads once more than ten run at once",
                "unmeasured share of component traffic",
            )
        )
        assert "database reads" in html
        assert "unmeasured share of component traffic" in html

    def test_basis_still_rendered(self):
        """Control arm: adding the second denominator must not lose the
        provenance label, which is the only thing distinguishing a measurement
        from an estimate."""
        html = _render_exposure(
            _exposure(
                "0.0058% of component RPCs",
                "84,174 requests per second",
                basis="MEASURED",
            )
        )
        assert "MEASURED" in html

    def test_empty_component_denominator_renders_path_alone(self):
        """Control arm: no empty tail when there is genuinely only one
        denominator.

        The `&middot;` this used to assert the absence of is gone from the cell
        entirely -- the denominators are block elements that stack, so there is
        no separator to dangle. Asserting the absence of a string the renderer
        can no longer emit is a check that cannot fail, so this now asserts the
        invariant that survives: the path renders, and no empty component
        element is emitted beside it."""
        html = _render_exposure(_exposure("0.5% of requests on /api/foo", "   "))
        assert "0.5%" in html
        assert 'class="cden"' not in html

    def test_genuinely_empty_still_states_the_absence(self):
        """Control arm carried over from PR #126: a truly empty exposure is
        still an absence and must say so.

        The literal moved from "not measured" to "no share measured" when the
        cell gained a percentage: the absence is now specifically of a share, and
        three named reasons produce it. The rule PR #126 established is unchanged
        and is asserted on the second line -- no provenance word above an absent
        figure, because one run shipped `n/a` above `ESTIMATED` on all 76 rows
        and it read as having measured nothing."""
        html = _render_exposure(_exposure("   ", "   "))
        assert "no share measured" in html
        assert (
            "ESTIMATED" not in html
            and "MEASURED" not in html.replace("no share measured", "").upper()
        )


# ---------------------------------------------------------------------------
# 3. The wiring itself. These guard a defect that ALL of the above missed.
# ---------------------------------------------------------------------------


_SKILL_DIR = Path(__file__).resolve().parent.parent
_PLUGIN_DIR = _SKILL_DIR.parent.parent


class TestPipelineWiring:
    """DISCRIMINATION: every test above passed while the resolver's output was
    never routed to the reconciler -- so the figure was produced, validated and
    accounted for, and still could not reach the band a reader sees. A schema
    test cannot catch that, because the defect is in prose the orchestrator
    follows. These assert the data path is STATED.
    """

    def _skill_md(self):
        return (_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    def test_reconciler_dispatch_carries_the_exposure_entry(self):
        """The reconciler's own contract tells it to adopt or downgrade the
        resolved figure. If the dispatch payload does not carry one, that
        instruction refers to data the agent was never handed and the band
        falls back to the packet's UNKNOWN silently."""
        lines = self._skill_md().splitlines()
        start = next(
            (
                i
                for i, line in enumerate(lines)
                if "spawn agents/bug-hunt-reconciler.md" in line
            ),
            None,
        )
        assert start is not None, "no reconciler dispatch line found in SKILL.md"
        # The dispatch STATEMENT only -- its own line plus any continuation up to
        # the closing brace. NOT a character window: the first version of this
        # test read a window and passed on the word "exposure" in an adjacent
        # comment, so it stayed green with the defect reintroduced.
        statement = []
        for line in lines[start : start + 4]:
            statement.append(line)
            if "}" in line:
                break
        payload = " ".join(statement)
        assert "}" in payload, (
            f"could not find the end of the dispatch payload: {payload!r}"
        )
        assert "exposure" in payload.lower(), (
            "the reconciler is dispatched without the resolved exposure entry; "
            f"its impact_exposure instruction cannot be carried out. Payload: {payload!r}"
        )

    def test_step_0_gate_names_every_dispatched_agent(self):
        """STEP 0 exists to fail fast when a pipeline component is missing,
        BEFORE finder fan-out is paid for. A new agent added to the run loop but
        not to that gate surfaces only deep into a run."""
        text = self._skill_md()
        dispatched = {
            line.split("agents/bug-hunt-")[1].split(".md")[0]
            for line in text.splitlines()
            if "spawn agents/bug-hunt-" in line
        }
        gate = text[text.index("subagents") - 200 : text.index("subagents") + 400]
        missing = sorted(a for a in dispatched if a not in gate)
        assert not missing, (
            f"agents dispatched in the run loop but absent from STEP 0's gate: {missing}"
        )

    def test_reconciler_declares_what_it_receives(self):
        """The receiving end must agree with the dispatching end. Measured: the
        two disagreed and nothing detected it."""
        recon = (_PLUGIN_DIR / "agents" / "bug-hunt-reconciler.md").read_text(
            encoding="utf-8"
        )
        start = recon.index("## What you receive")
        # THAT SECTION ONLY, and its bullets only. A 2000-character window was
        # the first version of this test and it passed with the declaration
        # deleted, because `impact_exposure` in the verdict-field list a few
        # paragraphs later satisfied it. Two of the three tests in this class
        # were first written backstopped by adjacent text.
        end = recon.index("\n## ", start + 1)
        bullets = [
            line for line in recon[start:end].splitlines() if line.startswith("- ")
        ]
        assert bullets, "could not find the input list in 'What you receive'"
        declared = " ".join(bullets).lower()
        assert "impact-resolver" in declared or "exposure entry" in declared, (
            "the reconciler does not declare the resolved exposure entry among "
            f"its inputs. Declared inputs: {declared[:300]!r}"
        )


class TestBasisEnum:
    """DISCRIMINATION: `basis` is documented as MEASURED or ESTIMATED and nothing
    validated it, so any string passed. Measured on a real resolution pass: an
    agent needed a third value for 15 of 26 candidates, invented `UNRESOLVED`,
    and it validated silently -- the majority of the output carried a value the
    schema does not define."""

    def _record_with_basis(self, basis):
        record = _make_minimal_record()
        record["findings"][0]["exposure"]["basis"] = basis
        # UNKNOWN basis is incompatible with a non-null share (the validator
        # rejects that combination), so clear the share for UNKNOWN tests.
        if basis == "UNKNOWN":
            record["findings"][0]["exposure"]["share"] = None
            record["findings"][0]["exposure"]["share_absent"] = "NOT_QUERIED"
            # Also align the resolution block: resolved=0 when the finding is UNKNOWN
            record["exposure_resolution"]["resolved"] = 0
            record["exposure_resolution"]["unresolved"] = [
                {"fingerprint": "0123456789abcdef", "reason": "no metric exists"}
            ]
        return [
            e for e in validate_run_record(record) if "basis" in (e.field + e.message)
        ]

    def test_measured_passes(self):
        """Control arm."""
        assert not self._record_with_basis("MEASURED")

    def test_unknown_passes(self):
        """Control arm: UNKNOWN is the legal third value, for a candidate nobody
        could resolve. It is the majority case on a real run."""
        assert not self._record_with_basis("UNKNOWN")

    def test_invented_value_is_rejected(self):
        """Defect arm: the exact value a real agent invented when the brief gave
        it only two and required a third."""
        assert self._record_with_basis("UNRESOLVED"), (
            "an undefined basis value validated silently"
        )

    def test_empty_basis_is_rejected(self):
        """Defect arm: the other way a producer satisfies a required key."""
        assert self._record_with_basis("")


class TestBandReason:
    """DISCRIMINATION: the rubric has always required 'one sentence naming which
    consideration decided it' and there was no field for it, so every reader got
    per-band boilerplate identical for every finding in the group. It became
    load-bearing on 2026-08-28: a finding demoted to Low on a measured dormancy
    must disclose the capability it still has, and a bare band cannot carry that.
    """

    def _errors(self, record):
        return [
            e
            for e in validate_run_record(record)
            if "band_reason" in (e.field + e.message)
        ]

    def test_banded_finding_without_a_reason_is_rejected(self):
        """Defect arm: today a banded finding needs no reason at all."""
        record = _make_minimal_record()
        record["findings"][0].pop("band_reason", None)
        assert self._errors(record), "a banded finding with no reason validated"

    def test_banded_finding_with_a_reason_passes(self):
        """Control arm."""
        record = _make_minimal_record()
        record["findings"][0]["band_reason"] = (
            "One occurrence can fail a request, and exposure is 0.048% of "
            "Influence traffic, MEASURED."
        )
        assert not self._errors(record)

    def test_not_checked_finding_needs_no_reason(self):
        """Control arm: a finding nobody looked at has no band to justify, and
        requiring a sentence there would invite one to be invented."""
        record = _make_minimal_record()
        record["findings"][0]["band"] = "Not checked"
        record["findings"][0]["state"] = "DEFERRED_UNVERIFIED"
        record["findings"][0]["band_reason"] = None
        assert not self._errors(record)

    def test_truncated_reason_is_rejected(self):
        """Defect arm: the field is prose, so it must be caught mid-sentence the
        way title now is -- 129 fields in one report once stopped mid-sentence
        because an orchestrator assembled them by slicing another field."""
        record = _make_minimal_record()
        record["findings"][0]["band_reason"] = "one occurrence can exhaust the"
        errors = [
            e
            for e in validate_run_record(record)
            if "band_reason" in e.field and "mid-sentence" in e.message
        ]
        assert errors, "a reason truncated mid-sentence validated"

    def test_reason_reaches_the_visible_row(self):
        """Recorded is not delivered. The field exists to be read, and it must be
        in the always-visible row: reasoning one click away is how the exposure
        column came to discard real impact statements while the page looked whole.
        """
        import dataclasses

        from render_digest import _render_row

        from test_render_digest import _make_not_checked_finding

        finding = dataclasses.replace(
            _make_not_checked_finding(),
            band=Band.LOW,
            band_reason=(
                "Harm currently 0% of the executor path, MEASURED. Capability "
                "confirmed: one occurrence pins a thread and is client-reachable."
            ),
        )
        html_out = _render_row(finding)
        assert "Capability confirmed" in html_out, (
            "the band reason did not reach the row a reader sees"
        )
        assert html_out.index("Capability confirmed") < html_out.index(
            'class="detail"'
        ), "the reason rendered only inside the expansion, not the visible row"
