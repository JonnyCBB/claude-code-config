"""Two defects a fully-passing run still shipped.

DEFECT A (jbrooksbartlett-tstqk, P0). The orchestrator skipped the impact resolver and
queried Oliver itself. STEP 0's pre-flight leaves it holding metric tools, so it could;
it reasoned that a named subagent risked dropping its output, which is locally true.
Criterion 3 ("resolved > 0") would have read PASS, with real production figures, for a
stage that never ran. Caught only because a human was reading the pane.

DEFECT B (jbrooksbartlett-l383p). The digest masthead read
"1 act now . 11 important . 19 low . 0 not checked" on a run where 31 of 31 findings
carried verdict "Not checked". `Band.NOT_CHECKED` and `Verdict.NOT_CHECKED` share the
string, the counter counts only bands, and the one line a skimmer reads therefore
asserted the opposite of the truth. Seven pass criteria and every validator were green
with this on the page.

Both are honesty defects rather than crashes, which is why nothing caught them.
"""

import dataclasses
import html as _html
import re as _re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import render_digest  # noqa: E402
import test_render_digest as trd  # noqa: E402
from digest_model import Band, Verdict, validate_run_record  # noqa: E402

# ---------------------------------------------------------------------------
# Defect A: the resolver bypass
# ---------------------------------------------------------------------------


def _record_with_exposure(**overrides):
    record = trd._make_minimal_record()
    block = {
        "attempted": 1,
        "resolved": 1,
        "unresolved": [],
        "resolver_agent_id": "aimpact-resolver-999cdbe1afc71498",
    }
    block.update(overrides)
    record["exposure_resolution"] = block
    return record


def _exposure_errors(record):
    return [e for e in validate_run_record(record) if "exposure_resolution" in e.field]


class TestResolverIdentityIsRecorded:
    def test_block_without_a_resolver_agent_id_is_rejected(self):
        record = _record_with_exposure()
        del record["exposure_resolution"]["resolver_agent_id"]
        assert _exposure_errors(record), (
            "A run recorded impact figures without naming the agent that produced "
            "them. That is indistinguishable from an orchestrator that queried the "
            "metrics itself, which is the defect this field exists to expose."
        )

    def test_empty_resolver_agent_id_is_rejected(self):
        record = _record_with_exposure(resolver_agent_id="")
        assert _exposure_errors(record), (
            "An empty id satisfies a presence check while carrying no information -- "
            "the stand-in a producer reaches for when there is no real value."
        )

    def test_orchestrator_naming_itself_is_rejected(self):
        """The specific lie a bypass would have to tell.

        Requiring an id converts a silent shortcut into a deliberate false statement.
        Naming what an orchestrator would plausibly write closes the easy case.
        """
        for claimed in (
            "orchestrator",
            "self",
            "main",
            "n/a",
            "none",
            "ORCHESTRATOR",
            # Placeholder values, added 2026-08-29 after watching a real run write
            # `"resolver_agent_id": "PLACEHOLDER"` into its run-record template. That
            # is not a lie an orchestrator tells to cover a bypass -- it is what an
            # honest run leaves behind when it assembles the record in stages and
            # forgets to come back. It validated clean, which is worse: the field
            # exists to prove an independent agent ran, and a placeholder proves
            # nothing while looking like it does.
            "PLACEHOLDER",
            "placeholder",
            "TBD",
            "todo",
            "xxx",
            "FIXME",
            "<agent-id>",
            "agent-id",
            "example",
        ):
            record = _record_with_exposure(resolver_agent_id=claimed)
            assert _exposure_errors(record), (
                f"resolver_agent_id={claimed!r} was accepted. That is the "
                f"orchestrator declaring it did the resolver's work."
            )

    def test_a_real_agent_id_passes(self):
        """Both arms: the honest case must not become a false positive."""
        assert not _exposure_errors(_record_with_exposure())

    def test_list_of_agent_ids_passes(self):
        """Chunked resolver dispatch spawns multiple resolver agents, each handling
        ~30 candidates. The field accepts a list of their ids.

        On a real 132-candidate run, a single resolver resolved only 14 (10.6%).
        Chunking into 4-5 agents means each has a tractable workload."""
        record = _record_with_exposure(
            resolver_agent_id=[
                "aimpact-resolver-chunk0-abc123",
                "aimpact-resolver-chunk1-def456",
                "aimpact-resolver-chunk2-ghi789",
            ]
        )
        assert not _exposure_errors(record), (
            "a list of real agent ids was rejected; chunked resolver dispatch "
            "requires list-form resolver_agent_id"
        )

    def test_empty_list_is_rejected(self):
        """An empty list carries no information, same as an empty string."""
        record = _record_with_exposure(resolver_agent_id=[])
        assert _exposure_errors(record), (
            "an empty list for resolver_agent_id validated; it proves no agent ran"
        )

    def test_list_containing_orchestrator_name_is_rejected(self):
        """A list that includes an orchestrator self-reference is just as bad as a
        scalar one."""
        record = _record_with_exposure(
            resolver_agent_id=["aimpact-resolver-real-abc123", "self"]
        )
        assert _exposure_errors(record), (
            "a list containing 'self' validated; it should be rejected"
        )

    def test_list_containing_empty_string_is_rejected(self):
        """A blank entry in a list is the same gap as a scalar blank."""
        record = _record_with_exposure(
            resolver_agent_id=["aimpact-resolver-real-abc123", ""]
        )
        assert _exposure_errors(record), "a list containing an empty string validated"

    def test_required_even_when_nothing_resolved(self):
        """A resolver that resolved zero still ran, and still has an identity.

        Making the field conditional on resolved>0 would let a bypassing orchestrator
        report resolved=0 to dodge the check -- and resolved=0 is precisely what the
        previous run reported.
        """
        record = _record_with_exposure(
            attempted=1,
            resolved=0,
            unresolved=[{"fingerprint": "a" * 16, "reason": "no metric exists"}],
        )
        del record["exposure_resolution"]["resolver_agent_id"]
        assert _exposure_errors(record)


class TestTheSkillForbidsTheShortcut:
    def _skill(self):
        return (SCRIPTS.parent / "SKILL.md").read_text()

    def test_skill_forbids_the_orchestrator_querying_metrics(self):
        skill = self._skill().lower()
        assert "must not" in skill and "metric" in skill
        assert "yourself" in skill or "directly" in skill, (
            "SKILL.md does not tell the orchestrator, in terms, not to query metric "
            "tools directly. An instruction it can reason past is the weakest layer, "
            "but its absence is worse."
        )

    def test_skill_says_why_and_not_only_what(self):
        """An orchestrator reasoned past the absence of this once already.

        It will reason past a bare prohibition too. The instruction has to carry why
        the independence is the point, not just the rule.
        """
        skill = self._skill().lower()
        assert "certif" in skill or "proves nothing" in skill


# ---------------------------------------------------------------------------
# Defect B: the masthead
# ---------------------------------------------------------------------------


class _StubFinding:
    """Only the two fields the masthead reads."""

    def __init__(self, band, verdict):
        self.band = band
        self.verdict = verdict


def _plain(fragment: str) -> str:
    return " ".join(_html.unescape(_re.sub(r"<[^>]+>", " ", fragment)).split()).lower()


def _counts_text(bands: dict, verdict) -> str:
    """Render just the masthead counts for a run with the given band split.

    `verdict` applies to every finding, which is the shape both arms need: the proof
    run was uniformly NOT_CHECKED and the control is uniformly BUG.
    """
    grouped = {band: [] for band in Band}
    for band, count in bands.items():
        grouped[band] = [_StubFinding(band, verdict) for _ in range(count)]
    model = dataclasses.replace(trd._make_minimal_model(), grouped=grouped)
    return _plain(render_digest._render_counts(model))


class TestMastheadTellsTheTruthAboutVerification:
    #: The 2026-08-28 proof run exactly: 31 findings, none banded Not checked,
    #: every verdict Not checked.
    PROOF_RUN = {Band.ACT_NOW: 1, Band.IMPORTANT: 11, Band.LOW: 19}

    def test_all_unverified_run_does_not_claim_zero_unchecked(self):
        text = _counts_text(self.PROOF_RUN, Verdict.NOT_CHECKED)
        assert "0 not checked" not in text, (
            f"Masthead reads {text!r} on a run where every finding is unverified. "
            f"This is the line a reader quotes."
        )

    def test_masthead_states_how_many_were_verified(self):
        text = _counts_text(self.PROOF_RUN, Verdict.NOT_CHECKED)
        assert "verified" in text, (
            "The masthead reports urgency and never whether anything was checked. "
            "The urgency of an unverified finding is a conditional claim, and the "
            "condition is the part being omitted."
        )
        assert "0 of 31" in text, f"expected '0 of 31' in {text!r}"

    def test_a_fully_verified_run_says_so(self):
        """Both arms: it must distinguish, not merely always warn."""
        text = _counts_text({Band.ACT_NOW: 2, Band.IMPORTANT: 3}, Verdict.BUG)
        assert "5 of 5" in text, f"expected '5 of 5' in {text!r}"

    def test_band_counts_are_still_present(self):
        """Additive fix. Losing the band split trades one gap for another."""
        text = _counts_text(self.PROOF_RUN, Verdict.NOT_CHECKED)
        for fragment in ("1 act now", "11 important", "19 low"):
            assert fragment in text, f"missing {fragment!r} from {text!r}"

    def test_empty_run_does_not_divide_by_zero(self):
        assert "0 of 0" in _counts_text({}, Verdict.NOT_CHECKED)
