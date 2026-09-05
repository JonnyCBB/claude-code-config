"""Tests for the dossier builder -- the fix for the gate that stopped a whole run.

THE DEFECT (jbrooksbartlett-o468l). There was a script to CHECK a dossier and none to
BUILD one, so every run reimplemented the withholding rules by hand. On 2026-08-29 the
character-pro run built 8 dossiers, `dossier_leak_scan.py` returned LEAKED on 7 of them,
and the run stopped without verifying a single one of its 103 candidates.

Eleven of the eighteen leaks were the word "refuted", from the Coverage record's sweep
table where the finder lists hypotheses it discarded. The finder contract puts that below
a `--- APPENDIX ---` marker so it can be separated mechanically; the hand-rolled stripper
was not using the marker.

Two further defects in the builder itself were found only by running it over the 32 real
packets from that run, not by reading it:
  - its own preamble said "it is a defect", tripping the gate's verdict-language pattern
  - the field extractor ran past its own field and swallowed the next, so a PERMITTED
    field carried a WITHHELD one into the dossier
Both are covered below.
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import build_dossier  # noqa: E402

PACKET = """\
## Finder Packet -- candidate 1

- **Component** (NEUTRAL): character-pro, example-org/services, squad kipp, tier 2.
- **Code locations** (NEUTRAL): promotions-serving/character-pro/src/main/java/P.java:448
- **Observed behavior** (NEUTRAL): returns the unfiltered list when the filter errors.
- **Conditions** (NEUTRAL): any request where the downstream filter reports an error.
- **Defect description** (INTERPRETIVE): discards a computed removal list
- **Candidate mechanism hypothesis** (INTERPRETIVE): confidence high. This is a bug.
- **Boundary and call-graph info** (NEUTRAL): called by HomeSectionsProvider.
- **Relevant tests and config** (NEUTRAL): PTest.java; feature.filter.enabled
- **Impact and exposure evidence** (INTERPRETIVE): 3% of traffic
- **Scope** (INTERPRETIVE): LOCAL
- **Proposed safe reproduction plan** (INTERPRETIVE): craft a request that errors.
Defect site: promotions-serving/character-pro/src/main/java/P.java:104
- **Root-cause fingerprint** (INTERPRETIVE): 127abe64618df552
- Proposed severity: medium.

--- APPENDIX ---

## Coverage record

Files read: P.java, S.java
Refuted: the null-check variant was REFUTED after tracing all four call sites.
The defect is clearly wrong here and violates the contract.

| Discriminator | Downstream decision | Can it see the discriminator? |
|---|---|---|
| locale | ranking | yes |
"""


@pytest.fixture()
def dossier():
    return build_dossier.build(PACKET, "127abe64618df552")


class TestTheAppendixNeverTravels:
    """11 of the 18 real leaks came from here."""

    def test_appendix_content_is_absent(self, dossier):
        for leaked in ("Refuted", "REFUTED", "Coverage record", "Discriminator"):
            assert leaked not in dossier, (
                f"{leaked!r} reached the dossier from the appendix. The finder contract "
                f"puts the coverage record below --- APPENDIX --- so it can be split off "
                f"mechanically; not using that marker is what blocked a whole run."
            )

    def test_appendix_verdict_prose_is_absent(self, dossier):
        assert "clearly wrong" not in dossier
        assert "violates the contract" not in dossier


class TestWithheldFieldsNeverTravel:
    @pytest.mark.parametrize(
        "field",
        [
            "Defect description",
            "Candidate mechanism hypothesis",
            "Scope",
            "Root-cause fingerprint",
            "Defect site",
            "Impact and exposure evidence",
            "Proposed safe reproduction plan",
            "Proposed severity",
        ],
    )
    def test_withheld_field_absent(self, dossier, field):
        assert field not in dossier, (
            f"{field!r} is INTERPRETIVE and must not reach a blind verifier."
        )

    def test_withheld_field_VALUES_are_absent_not_just_labels(self, dossier):
        """Stripping a label while keeping its body is the subtler failure."""
        assert "discards a computed removal list" not in dossier
        assert "confidence high" not in dossier.lower()
        assert "127abe64618df552" not in dossier

    def test_a_field_without_a_colon_is_still_recognised(self):
        """Measured on a real packet: a tagged field written with NO colon was absorbed
        into the preceding permitted field, carrying it into the dossier."""
        packet = PACKET.replace(
            "- **Defect description** (INTERPRETIVE): discards a computed removal list",
            "**Defect description** (INTERPRETIVE)\ndiscards a computed removal list",
        )
        got = build_dossier.build(packet, "127abe64618df552")
        assert "Defect description" not in got
        assert "discards a computed removal list" not in got


class TestPermittedContentSurvives:
    """Both arms. A dossier that withholds everything is useless, not safe."""

    def test_the_five_permitted_items_carry_their_content(self, dossier):
        for wanted in (
            "character-pro",
            "P.java:448",
            "unfiltered list",
            "HomeSectionsProvider",
            "PTest.java",
        ):
            assert wanted in dossier, f"{wanted!r} is permitted and was dropped"

    def test_the_question_is_asked_verbatim(self, dossier):
        assert (
            "What current contract or product intent explains this behavior?" in dossier
        )


class TestTheBuilderChecksItselfWithTheGatesPatterns:
    def test_a_clean_packet_produces_no_leaks(self):
        _, leaks = build_dossier.build_checked(PACKET, "127abe64618df552")
        assert leaks == [], f"builder emitted a dossier its own gate rejects: {leaks}"

    def test_the_scan_can_actually_fail(self):
        """Negative control.

        Without this, `leaks == []` is indistinguishable from a scanner that returns
        nothing for everything -- which is exactly the shape of bug this codebase keeps
        finding.
        """
        planted = "# Behavior Dossier\n\nDefect site: A.java:1\nThis is a bug.\n"
        assert build_dossier.scan(planted), (
            "the scan found nothing in text containing a defect-site label AND verdict "
            "language, so it is not actually checking anything"
        )

    def test_the_preamble_itself_does_not_leak(self):
        """The builder's own framing text tripped the gate on the first version."""
        empty, leaks = build_dossier.build_checked("## Finder Packet\n", None)
        assert leaks == [], f"the dossier's own boilerplate leaks: {leaks}"


class TestCLI:
    def test_writes_a_dossier_and_exits_zero(self, tmp_path):
        pkt = tmp_path / "finder-m01.md"
        pkt.write_text(PACKET)
        out = tmp_path / "d.md"
        r = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "build_dossier.py"),
                "--packet",
                str(pkt),
                "--fingerprint",
                "127abe64618df552",
                "--out",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stderr
        assert out.exists()
        assert "Defect description" not in out.read_text()

    def test_refuses_to_write_a_leaking_dossier(self, tmp_path):
        """A builder that writes a leaking dossier and merely warns has shipped one.

        The leak is planted INSIDE a permitted field, which is the case the allowlist
        cannot catch and the second pass exists for: a finder writing conclusion
        language into `Observed behavior`, a NEUTRAL field that legitimately travels.
        An earlier version of this test planted `Defect site:` instead and passed
        vacuously -- the allowlist drops that field before any scan runs, so there was
        never anything to detect.
        """
        pkt = tmp_path / "finder-m02.md"
        pkt.write_text(
            "## Finder Packet\n"
            "- **Component** (NEUTRAL): character-pro\n"
            "- **Observed behavior** (NEUTRAL): the handler drops the list. "
            "This is a bug and the code incorrectly returns early.\n"
        )
        out = tmp_path / "d.md"
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / "build_dossier.py"), "--packet", str(pkt),
             "--out", str(out)],
            capture_output=True, text=True,
        )
        assert r.returncode == 1, f"exited 0 on a leaking dossier: {r.stdout}"
        assert "LEAKED" in r.stderr
        assert not out.exists(), "a leaking dossier was written to disk anyway"
