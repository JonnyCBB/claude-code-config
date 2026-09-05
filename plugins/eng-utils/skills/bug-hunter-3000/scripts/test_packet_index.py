"""Tests for the packet index -- the fix for `index_to_disk` being undefined.

THE DEFECT (jbrooksbartlett-n26cg). `index_to_disk` was named exactly once, in
SKILL.md's dispatch pseudocode, and defined nowhere: no script, no contract, no
statement of what it returns. The line it appeared on read

    packets += index_to_disk(flatten(spawn agents/bug-hunt-finder.md ...))

which ACCUMULATES, into a variable named `packets`, directly contradicting
references/mandate-partitioning.md: "Index each batch to disk as it lands, and do not
carry packets forward."

The measured consequence: 32 finders returned ~2.2MB through the orchestrator's
context, the orchestrator exhausted its working memory, and the impact resolver
received 14 of 116 candidates. A separate consequence surfaced later -- the per-packet
byte sizes needed to calibrate project_cost.py were never persisted anywhere, so that
calibration cannot be re-derived from any run performed without this index.

WHAT THE FIX RESTS ON. The finder holds no `Write` tool but does hold `Bash`, which can
write anywhere `Write` can. So the packet can be written by the FINDER, and never enter
the orchestrator's context at all. That is a stronger fix than indexing on arrival,
which still pays the context cost once.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import index_packets  # noqa: E402


PACKET = """\
## Finder Packet -- candidate 1

- **Component** (NEUTRAL): character-pro, example-org/services, squad kipp, tier 2.
- **Code locations** (NEUTRAL): services/character-pro/src/characterpro/Predict.java:448
- **Observed behavior** (NEUTRAL): the handler returns the unfiltered list when the
  downstream filter reports an error.
- **Defect description** (INTERPRETIVE): discards a successfully computed removal list
  when an unrelated filter fails
- **Candidate mechanism hypothesis** (INTERPRETIVE): confidence moderate-to-high.
- **Impact and exposure evidence, or `UNKNOWN`** (INTERPRETIVE): apollo_error_counter_total
  on the HomeSections path.
- **Scope** (INTERPRETIVE): LOCAL
Defect site: services/character-pro/src/characterpro/Predict.java:104
- **Root-cause fingerprint** (INTERPRETIVE): 127abe64618df552
- Proposed severity: medium. Effort: M.

## Finder Packet -- candidate 2

- **Component** (NEUTRAL): character-pro, example-org/services, squad kipp, tier 2.
- **Observed behavior** (NEUTRAL): a per-key warning is emitted without rate limiting.
- **Defect description** (INTERPRETIVE): logs once per key with no ceiling
- **Impact and exposure evidence, or `UNKNOWN`** (INTERPRETIVE): UNKNOWN
- **Scope** (INTERPRETIVE): LOCAL
Defect site: services/character-pro/src/characterpro/Scores.java:160
- **Root-cause fingerprint** (INTERPRETIVE): 595bd489b877f4fc
- Proposed severity: low-medium. Effort: S.

--- APPENDIX ---

## Coverage record

Files read: Predict.java, Scores.java, Selection.java
Set aside: Selection.java -- no branching on the discriminator

| Discriminator | Downstream decision | Effective config | Can it see the discriminator? |
|---|---|---|---|
| locale | ranking | default | yes |
""" + ("\nfiller line to make the appendix genuinely large.\n" * 400)


@pytest.fixture()
def run_dir(tmp_path):
    return tmp_path / "run-abc123"


def _write(run_dir, mandate="m01", text=PACKET, agent_id="a0123456789abcdef"):
    return index_packets.write_and_index(
        run_dir=run_dir, mandate=mandate, packet_text=text, agent_id=agent_id
    )


class TestThePacketReachesDisk:
    def test_full_packet_is_written_verbatim(self, run_dir):
        _write(run_dir)
        stored = run_dir / "packets" / "finder-m01.md"
        assert stored.exists()
        assert stored.read_text() == PACKET, (
            "The stored packet must be byte-identical. It is the only surviving copy "
            "once the finder's context is gone, and it is what the dossier and the "
            "portfolio are rebuilt from."
        )

    def test_appendix_is_kept_not_stripped(self, run_dir):
        """The appendix is the coverage record -- search accounting the portfolio needs.

        It is the bulk of the bytes, which makes it the tempting thing to drop. But
        without it "searched and found nothing" and "never looked" are indistinguishable.
        """
        _write(run_dir)
        stored = (run_dir / "packets" / "finder-m01.md").read_text()
        assert "--- APPENDIX ---" in stored
        assert "Coverage record" in stored
        assert "Can it see the discriminator?" in stored


class TestTheIndexIsSmall:
    """The whole point: what comes back must not scale with packet size."""

    def test_index_is_a_small_fraction_of_the_packet(self, run_dir):
        index = _write(run_dir)
        emitted = len(json.dumps(index).encode())
        assert emitted < len(PACKET.encode()) * 0.25, (
            f"Index is {emitted} bytes against a {len(PACKET.encode())}-byte packet. "
            f"If the index scales with the packet, the orchestrator's context is spent "
            f"anyway and this script buys nothing."
        )

    def test_index_carries_no_appendix_text(self, run_dir):
        index = _write(run_dir)
        blob = json.dumps(index)
        assert "APPENDIX" not in blob
        assert "filler line" not in blob, (
            "Appendix content leaked into the index. The appendix is the majority of "
            "the bytes and the entire reason the packet goes to disk."
        )

    def test_index_carries_no_mechanism_hypothesis(self, run_dir):
        """INTERPRETIVE prose belongs on disk, not in the carried index."""
        index = _write(run_dir)
        blob = json.dumps(index)
        assert "confidence moderate-to-high" not in blob


class TestTheIndexCarriesWhatGroupingNeeds:
    """Grouping compares defect sites mechanically. Drop that and grouping dies."""

    def test_every_candidate_has_a_fingerprint(self, run_dir):
        index = _write(run_dir)
        fps = [c["fingerprint"] for c in index["candidates"]]
        assert fps == ["127abe64618df552", "595bd489b877f4fc"]

    def test_every_candidate_has_a_full_path_defect_site(self, run_dir):
        index = _write(run_dir)
        for c in index["candidates"]:
            assert c["defect_site"].startswith("promotions-serving/"), (
                f"Defect site {c['defect_site']!r} is not a repository-root path. "
                f"Partial paths broke a spec-anchored parse on five real packets, and "
                f"grouping compares these mechanically."
            )
            assert ":" in c["defect_site"]

    def test_candidate_count_matches_the_candidate_list(self, run_dir):
        index = _write(run_dir)
        assert index["candidate_count"] == len(index["candidates"]) == 2, (
            "The count must be derived from the list, never incremented by a loop -- "
            "a counter can be incremented zero times by a loop that never ran."
        )

    def test_metric_citation_is_detected_per_candidate(self, run_dir):
        """The resolver needs to know which candidates named a metric."""
        index = _write(run_dir)
        by_fp = {c["fingerprint"]: c for c in index["candidates"]}
        assert by_fp["127abe64618df552"]["has_metric_citation"] is True
        assert by_fp["595bd489b877f4fc"]["has_metric_citation"] is False, (
            "A candidate whose exposure evidence is literally UNKNOWN must not be "
            "recorded as carrying a metric citation."
        )

    def test_coverage_files_are_recorded(self, run_dir):
        index = _write(run_dir)
        assert index["coverage_files"], (
            "Coverage must survive into the index. A mandate searched with no "
            "candidates still has to be distinguishable from one never searched."
        )


class TestReadBack:
    """The orchestrator re-reads from disk when building a dossier."""

    def test_packet_can_be_recovered_by_fingerprint(self, run_dir):
        _write(run_dir)
        got = index_packets.read_packet(run_dir=run_dir, fingerprint="595bd489b877f4fc")
        assert "Scores.java:160" in got
        assert "595bd489b877f4fc" in got

    def test_recovering_an_unknown_fingerprint_raises(self, run_dir):
        _write(run_dir)
        with pytest.raises(KeyError):
            index_packets.read_packet(run_dir=run_dir, fingerprint="0000000000000000")

    def test_read_back_returns_only_that_candidates_section(self, run_dir):
        """Returning the whole file would put the appendix back in context."""
        _write(run_dir)
        got = index_packets.read_packet(run_dir=run_dir, fingerprint="127abe64618df552")
        assert "Predict.java" in got
        assert "Scores.java:160" not in got, (
            "Read-back returned a sibling candidate's section too. Re-reading is "
            "supposed to be surgical; returning the file undoes the indexing."
        )


class TestPerPacketSizeIsRecorded:
    """So project_cost.py can eventually be re-calibrated.

    The coefficients in project_cost.py are ESTIMATED from one run and cannot be
    re-derived, because no run has ever persisted per-packet byte sizes. This is the
    field that fixes that, and it costs nothing to record.
    """

    def test_packet_bytes_are_recorded(self, run_dir):
        index = _write(run_dir)
        assert index["packet_bytes"] == len(PACKET.encode())

    def test_recorded_size_is_the_packet_not_the_index(self, run_dir):
        index = _write(run_dir)
        assert index["packet_bytes"] > len(json.dumps(index).encode()) * 3


class TestCollect:
    def test_collect_merges_every_mandate(self, run_dir):
        _write(run_dir, mandate="m01")
        _write(run_dir, mandate="m02")
        merged = index_packets.collect(run_dir=run_dir)
        assert merged["mandates"] == 2
        assert merged["candidate_count"] == 4

    def test_collect_reports_zero_candidate_mandates(self, run_dir):
        """A searched-and-clean mandate must appear, not vanish."""
        _write(run_dir, mandate="m01")
        empty = (
            PACKET.split("## Finder Packet")[0]
            + "\n--- APPENDIX ---\nCoverage record\nFiles read: X.java\n"
        )
        _write(run_dir, mandate="m02", text=empty)
        merged = index_packets.collect(run_dir=run_dir)
        assert merged["mandates"] == 2
        by_m = {m["mandate"]: m for m in merged["by_mandate"]}
        assert by_m["m02"]["candidate_count"] == 0, (
            "A mandate that found nothing must be recorded with zero, not omitted. "
            "Omitting it makes a clean slice and an unsearched slice look alike."
        )


class TestCLI:
    def test_writes_from_stdin_and_prints_only_the_index(self, run_dir):
        out = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "index_packets.py"),
                "--run-dir",
                str(run_dir),
                "--mandate",
                "m07",
            ],
            input=PACKET,
            capture_output=True,
            text=True,
            check=True,
        )
        assert (run_dir / "packets" / "finder-m07.md").exists()
        parsed = json.loads(out.stdout)
        assert parsed["candidate_count"] == 2
        assert len(out.stdout.encode()) < len(PACKET.encode()) * 0.25, (
            "The CLI printed something proportional to the packet. The finder pipes "
            "its packet into this and returns ONLY what this prints."
        )

    def test_read_mode_prints_one_section(self, run_dir):
        subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "index_packets.py"),
                "--run-dir",
                str(run_dir),
                "--mandate",
                "m07",
            ],
            input=PACKET,
            capture_output=True,
            text=True,
            check=True,
        )
        out = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "index_packets.py"),
                "--run-dir",
                str(run_dir),
                "--read",
                "595bd489b877f4fc",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scores.java:160" in out.stdout
        assert "Predict.java:104" not in out.stdout


class TestTheSkillNoLongerAccumulatesPackets:
    """The pseudocode is the thing an orchestrator actually follows."""

    def _skill(self):
        return (SCRIPTS.parent / "SKILL.md").read_text()

    def test_dispatch_loop_does_not_accumulate_into_packets(self):
        skill = self._skill()
        assert "packets += " not in skill, (
            "SKILL.md still accumulates finder output into a `packets` variable. That "
            "line is what an orchestrator follows, and it contradicts "
            "mandate-partitioning.md's 'do not carry packets forward'."
        )

    def test_index_to_disk_is_no_longer_an_undefined_name(self):
        skill = self._skill()
        assert "index_to_disk(" not in skill, (
            "`index_to_disk(` is still called as an undefined function. It has no "
            "definition anywhere in the skill; a run reaching it has to invent one, "
            "and the measured run invented a 68-line script mid-flight."
        )

    def test_skill_names_the_real_script(self):
        assert "index_packets.py" in self._skill()

    def test_finder_dispatch_supplies_run_and_skill_dirs(self):
        """The write command is not runnable without them.

        Found by executing the block rather than reading it, per the
        context-and-skills-standards rule that an embedded block must be
        self-contained. The finder's Inputs listed neither, and the dispatch passed
        neither, so a finder following the instruction would invent a path -- and
        packets scattered across invented paths read downstream as "searched nothing".
        """
        skill = self._skill()
        for token in ("run_dir", "skill_dir", "mandate_id"):
            assert token in skill, (
                f"the finder dispatch never passes {token}; the write command in "
                f"agents/bug-hunt-finder.md cannot be run without it"
            )

    def test_finder_is_told_to_stop_rather_than_invent_a_path(self):
        finder = (
            SCRIPTS.parent.parent.parent / "agents" / "bug-hunt-finder.md"
        ).read_text()
        assert "say so and stop" in finder, (
            "A finder given no run directory must halt, not guess. Guessing produces "
            "a run that looks complete and has written its evidence nowhere findable."
        )


class TestCoverageFilesParsing:
    """Found by an eval run, not by these tests.

    The first version split the `Files read:` line on commas. Real coverage records
    put parenthetical notes after each path -- "Foo.java (mandate file, read in full)"
    -- so a comma split produced entries like "read in full)" and "found none)".
    Three consequences, in increasing order of seriousness: the index carried junk;
    the index grew to 14.8% of the packet against a 3.7% design target, eroding the
    saving that is the whole point; and `coverage_files` is what distinguishes
    "searched and found nothing" from "never looked", so filling it with fragments
    corrupts the one record that makes a negative result trustworthy.
    """

    NOISY = (
        "## Finder Packet -- candidate 1\n"
        "- **Scope** (INTERPRETIVE): LOCAL\n"
        "Defect site: svc/src/main/java/A.java:10\n"
        "- **Root-cause fingerprint** (INTERPRETIVE): 1111111111111111\n"
        "--- APPENDIX ---\n"
        "Files read: svc/src/main/java/A.java (mandate file, read in full), "
        "svc/src/test/java/ATest.java (context: coverage, found none), "
        "svc/src/main/java/B.java\n"
    )

    def test_parenthetical_notes_do_not_become_entries(self, run_dir):
        idx = index_packets.write_and_index(run_dir, "m01", self.NOISY, None)
        for entry in idx["coverage_files"]:
            assert not entry.strip().endswith(")") or "/" in entry, (
                f"{entry!r} is a fragment of a parenthetical note, not a file."
            )
            assert "/" in entry, f"{entry!r} is not a path"

    def test_every_path_is_still_captured(self):
        """Both arms: stripping noise must not drop real files."""
        import tempfile, pathlib
        d = pathlib.Path(tempfile.mkdtemp())
        idx = index_packets.write_and_index(d, "m01", self.NOISY, None)
        got = " ".join(idx["coverage_files"])
        for wanted in ("A.java", "ATest.java", "B.java"):
            assert wanted in got, f"{wanted} was dropped from coverage"

    def test_noise_does_not_inflate_the_index_on_a_realistic_packet(self, run_dir):
        """Share is only meaningful against a realistically-sized packet.

        The first version of this test asserted a share bound against the 340-byte
        NOISY fixture, where the JSON scaffolding alone exceeds the packet and the
        share is 116% -- a number that says nothing about anything. Measure on the
        large fixture instead, which is the shape a real packet has.
        """
        import json as _j

        noisy_tail = self.NOISY[self.NOISY.index("Files read:"):]
        big = PACKET.replace(
            "Files read: Predict.java, Scores.java, Selection.java", noisy_tail.strip()
        )
        idx = index_packets.write_and_index(run_dir, "m01", big, None)
        share = len(_j.dumps(idx).encode()) / len(big.encode())
        assert share < 0.10, (
            f"index is {share:.1%} of the packet even on a realistic one; parenthetical "
            f"noise is still reaching it"
        )


class TestAMismatchIsLoudNotSilent:
    """Found on the 2026-08-29 live run, at a cost nothing else would have revealed.

    Four finders spent 24-33 minutes each, and up to 290k tokens each, in loops the
    tmux pane labelled "Debugging heading regex in finder-m27.md" and "Reformatting
    Finder Packet candidate headings". They were reverse-engineering this parser by
    trial and error: nothing told them what section heading it needs, and a packet it
    cannot parse returns candidate_count 0 with no explanation. A silent zero is
    indistinguishable from "this mandate found nothing", which is the exact confusion
    this whole skill exists to prevent -- reproduced inside its own tooling.

    All 32 packets eventually parsed. The defect is not that the output was wrong; it
    is that converging on it cost more than the search did.
    """

    NO_HEADINGS = (
        "Component: character-pro\n"
        "Defect site: svc/src/main/java/A.java:10\n"
        "Root-cause fingerprint: 1111111111111111\n"
        "--- APPENDIX ---\nFiles read: svc/src/main/java/A.java\n"
    )

    def test_fingerprints_without_parseable_sections_are_reported(self, run_dir):
        """The packet names a fingerprint but no section heading exists to attach it to."""
        idx = index_packets.write_and_index(run_dir, "m01", self.NO_HEADINGS, None)
        assert idx.get("parse_warning"), (
            "A packet carrying a fingerprint but no recognisable candidate section "
            "returned no warning. The finder sees candidate_count 0 and cannot tell "
            "whether it found nothing or wrote the wrong shape."
        )
        assert "1111111111111111" in idx["parse_warning"] or "1" in str(
            idx["parse_warning"]
        )

    def test_the_warning_says_what_shape_is_expected(self, run_dir):
        idx = index_packets.write_and_index(run_dir, "m01", self.NO_HEADINGS, None)
        assert "Finder Packet" in idx["parse_warning"], (
            "The warning must name the heading the parser needs. Telling a finder it "
            "failed without telling it what to write is what produced the loops."
        )

    def test_a_genuinely_empty_mandate_does_not_warn(self, run_dir):
        """Both arms. Searched-and-clean must stay distinct from wrote-wrong-shape."""
        empty = "No candidates found in this mandate.\n--- APPENDIX ---\nFiles read: A.java\n"
        idx = index_packets.write_and_index(run_dir, "m01", empty, None)
        assert idx["candidate_count"] == 0
        assert not idx.get("parse_warning"), (
            "A mandate that genuinely found nothing was flagged as a parse failure. "
            "That inverts the distinction this warning exists to draw."
        )

    def test_a_well_formed_packet_does_not_warn(self, run_dir):
        idx = index_packets.write_and_index(run_dir, "m01", PACKET, None)
        assert idx["candidate_count"] == 2
        assert not idx.get("parse_warning")

    def test_finder_file_states_the_required_heading(self):
        finder = (
            SCRIPTS.parent.parent.parent / "agents" / "bug-hunt-finder.md"
        ).read_text()
        assert "## Finder Packet" in finder, (
            "The finder is never told the heading the parser splits on, so it has to "
            "discover it by trial and error against a silent failure."
        )
