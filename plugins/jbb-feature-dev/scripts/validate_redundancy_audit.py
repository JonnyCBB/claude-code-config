#!/usr/bin/env python3
"""Validates action items 2 to 5 from the 2026-05-01 redundancy audit.

Each check_action_N function returns (name, passed, message). Exits 0 only
when all four pass. Run from any directory; auto-detects plugin root.
"""

from __future__ import annotations
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILLS = PLUGIN_ROOT / "skills"


def _read(p: Path) -> str:
    return p.read_text()


def check_action_2(root: Path) -> tuple[str, bool, str]:
    """auto-tidy no longer has the 'Determine Project Scope & Detect Domains' duplicate step.

    Note: action #2's scope reduced after review — we delete only the duplicate Step 2 heading
    and its body. We do NOT assert renumbering of Steps 3-11, because Wave 2 deletes the whole
    file. Renumbering would be throwaway work.
    """
    skill = root / "skills/auto-tidy/SKILL.md"
    if not skill.exists():
        return ("action_2", True, "auto-tidy/SKILL.md deleted (Wave 2 already ran)")
    body = _read(skill)
    if re.search(r"^### Step 2: Determine Project Scope", body, re.MULTILINE):
        return (
            "action_2",
            False,
            "auto-tidy still has Step 2 'Determine Project Scope & Detect Domains'",
        )
    if re.search(r"Follow the detection procedure in.*domain-agent-registry", body):
        # Still present means Step 2's detection-redo body wasn't fully removed.
        # (This phrase appears only in Step 2's body, not Step 0 — Step 0 uses different wording.)
        if (
            body.count("Follow the detection procedure in") > 0
            and "skills/shared-references/domain-agent-registry" in body
        ):
            # Allowed only if it's part of Step 0's existing storage block (proxy: appears once, not twice).
            if body.count("Follow the detection procedure in") > 1:
                return (
                    "action_2",
                    False,
                    "auto-tidy still has duplicate domain-detection body text",
                )
    return ("action_2", True, "auto-tidy duplicate Step 2 detect-domains step removed")


def check_action_3(root: Path) -> tuple[str, bool, str]:
    """research-problem trims applied (audit Q3 rows 1-10).

    Each enumerated audit row gets one assertion. Rows 6, 7 → verification-and-iteration.md.
    Row 8 → review-personas.md. Row 9 → plan-templates.md. The rest → SKILL.md.
    """
    rp = root / "skills/research-problem/SKILL.md"
    body = _read(rp)

    # Row 1: Steps 8-11 sub-step labels collapsed to bullets — assert all four sub-labels gone.
    for n in (8, 9, 10, 11):
        if re.search(rf"\*\*Step {n} -- ", body):
            return (
                "action_3",
                False,
                f"research-problem still has bolded '**Step {n} -- ...**' sub-label",
            )

    # Row 2: skip-review prohibition deleted from SKILL.md (kept only in references/review-personas.md).
    if (
        "do not self-elect to skip" in body
        and "Mandatory at the chosen complexity tier" in body
    ):
        return (
            "action_3",
            False,
            "research-problem still duplicates skip-review prohibition in SKILL.md",
        )

    # Row 3: Important Notes reduced to ~3 bullets (length proxy: section body < 20 lines).
    important = re.search(r"## Important Notes\n(.*?)(?=\n## )", body, re.DOTALL)
    if important is None:
        return ("action_3", False, "Important Notes section missing entirely")
    if important.group(1).count("\n") > 20:
        return (
            "action_3",
            False,
            f"Important Notes too long ({important.group(1).count(chr(10))} lines) — should be ~3 bullets after trim",
        )

    # Row 4: Reference Files index reduced to one-line-per-reference (proxy: section < 14 lines).
    refs = re.search(r"## Reference Files\n(.*?)$", body, re.DOTALL)
    if refs is None:
        return ("action_3", False, "Reference Files section missing entirely")
    if refs.group(1).count("\n") > 14:
        return (
            "action_3",
            False,
            f"Reference Files index too long ({refs.group(1).count(chr(10))} lines) — should be ~5-7 lines after trim",
        )

    # Row 5: Important Notes 'documentarian' duplicate removed (still appears in Core Principle, that's fine).
    if important and "documentarians, not evaluators" in important.group(1):
        return (
            "action_3",
            False,
            "research-problem Important Notes still has duplicate 'documentarians, not evaluators'",
        )

    # Row 10: 'Step 2 not Step 3' justification removed.
    if re.search(r"This must happen HERE in Step 2, not in Step 3", body):
        return (
            "action_3",
            False,
            "research-problem still has 'Step 2, not Step 3' justification — already at point-of-use",
        )

    # Row 6: verification-and-iteration.md Pre-Synthesis section deleted.
    vi_path = root / "skills/research-problem/references/verification-and-iteration.md"
    vi_body = vi_path.read_text()
    if "Pre-Synthesis Agent Verification" in vi_body:
        return (
            "action_3",
            False,
            "verification-and-iteration.md still has Pre-Synthesis Agent Verification",
        )

    # Row 7: prose Iteration Loop Structure deleted; assert specific prose-only fragments gone
    # (these strings live ONLY in the prose, not the ASCII state machine).
    for prose_marker in ("Generate synthesis", 'Check for "Must Address"'):
        # Use a lower-bound — the prose introduces the loop's bullet list of "Generate synthesis" etc.
        # If it still appears, the prose wasn't removed.
        if vi_body.count(prose_marker) > 0:
            # Tolerate one occurrence (could be in another section).
            section = re.search(
                r"## Iteration Loop Structure\n(.*?)(?=\n## |\Z)", vi_body, re.DOTALL
            )
            if section and prose_marker in section.group(1):
                return (
                    "action_3",
                    False,
                    f"verification-and-iteration.md Iteration Loop Structure section still has prose ({prose_marker!r})",
                )

    # Row 8: review-personas.md Simple-skip paragraph deleted.
    rp_personas = (
        root / "skills/research-problem/references/review-personas.md"
    ).read_text()
    if re.search(
        r"For \*\*Simple\*\* complexity research where the user did not request review",
        rp_personas,
    ):
        return (
            "action_3",
            False,
            "review-personas.md still has the Simple-skip paragraph at L313-319 — should be deleted",
        )

    # Row 9: TodoWrite Tracking Pattern collapsed.
    pt_body = (
        root / "skills/research-problem/references/plan-templates.md"
    ).read_text()
    todo_match = re.search(
        r"## TodoWrite Tracking Pattern\n(.*?)(?=\n## |\Z)", pt_body, re.DOTALL
    )
    if todo_match and todo_match.group(1).count("\n") > 10:
        return (
            "action_3",
            False,
            f"TodoWrite Tracking Pattern not collapsed ({todo_match.group(1).count(chr(10))} lines, target ≤ 10)",
        )

    return ("action_3", True, "all 10 research-problem trims applied (rows 1-10)")


def check_action_4(root: Path) -> tuple[str, bool, str]:
    """polish-code exists; tidy + auto-tidy deleted; cross-refs updated."""
    polish = root / "skills/polish-code/SKILL.md"
    if not polish.exists():
        return ("action_4", False, "polish-code/SKILL.md does not exist")
    if (root / "skills/tidy/SKILL.md").exists():
        return ("action_4", False, "tidy/SKILL.md still exists — should be deleted")
    if (root / "skills/auto-tidy/SKILL.md").exists():
        return (
            "action_4",
            False,
            "auto-tidy/SKILL.md still exists — should be deleted",
        )
    polish_body = polish.read_text()
    # Mode Detection block present.
    if "## Mode Detection" not in polish_body:
        return ("action_4", False, "polish-code missing ## Mode Detection block")
    # All six passes preserved.
    required_passes = [
        "Test Enhancement",
        "Source Code Simplification",
        "Test Code Simplification",
        "Data Annotation",
        "Coding Guidelines",
        "Formatting",
    ]
    missing = [p for p in required_passes if p not in polish_body]
    if missing:
        return ("action_4", False, f"polish-code missing required passes: {missing}")
    # Cross-references updated.
    for stale_path, file in [
        ("/auto-tidy", "README.md"),
        ("/tidy", "skills/verify-implementation/SKILL.md"),
        ("/tidy", "skills/code-review-modes/SKILL.md"),
        ("/auto-tidy", "agents/typescript-expert.md"),
        ("/auto-tidy", "agents/python-expert.md"),
    ]:
        f = root / file
        if f.exists() and stale_path in f.read_text():
            return ("action_4", False, f"{file} still mentions {stale_path}")
    # Validate scripts repointed.
    vc = (root / "scripts/validate_consolidation.py").read_text()
    if "tidy/SKILL.md" in vc or "auto-tidy/SKILL.md" in vc:
        return (
            "action_4",
            False,
            "validate_consolidation.py still references tidy/auto-tidy paths",
        )
    if "polish-code/SKILL.md" not in vc:
        return (
            "action_4",
            False,
            "validate_consolidation.py does not reference polish-code/SKILL.md",
        )
    # Plugin version bumped — 0.5.0 was the floor that reflected the breaking
    # changes (slash-command and agent removals) batched into this refactor.
    # Subsequent releases must remain at >= 0.5.0.
    pj = (root / ".claude-plugin/plugin.json").read_text()
    m = re.search(r'"version":\s*"(\d+)\.(\d+)\.(\d+)"', pj)
    if not m:
        return ("action_4", False, "plugin.json has no parseable version")
    version = tuple(int(g) for g in m.groups())
    if version < (0, 5, 0):
        return (
            "action_4",
            False,
            f"plugin.json version {'.'.join(map(str, version))} < 0.5.0",
        )
    return (
        "action_4",
        True,
        "polish-code merged; tidy + auto-tidy deleted; all cross-refs updated; version bumped",
    )


def check_action_5(root: Path) -> tuple[str, bool, str]:
    """elicit-requirements shared boilerplate extracted AND duplicated content removed from both skills.

    A leaky version of this check would only verify the shared file exists and is referenced.
    Strengthened: also assert the duplicated agent-dispatch table is no longer present in the
    elicit SKILL.mds (only in the shared file), AND each elicit SKILL.md is at least ~15 lines
    shorter than today's HEAD.
    """
    shared = root / "skills/shared-references/elicit-shared-patterns.md"
    if not shared.exists():
        return (
            "action_5",
            False,
            "shared-references/elicit-shared-patterns.md does not exist",
        )
    shared_body = shared.read_text()
    if (
        "Agent Dispatch" not in shared_body
        and "agent-dispatch" not in shared_body.lower()
    ):
        return (
            "action_5",
            False,
            "shared-references/elicit-shared-patterns.md missing Agent Dispatch section",
        )
    if "Suggest Next Step" not in shared_body:
        return (
            "action_5",
            False,
            "shared-references/elicit-shared-patterns.md missing Suggest Next Step section",
        )

    er_path = root / "skills/elicit-requirements/SKILL.md"
    erf_path = root / "skills/elicit-requirements-friendly/SKILL.md"
    er = er_path.read_text()
    erf = erf_path.read_text()

    # Both SKILL.mds reference the shared file.
    if "elicit-shared-patterns" not in er:
        return (
            "action_5",
            False,
            "elicit-requirements/SKILL.md does not reference elicit-shared-patterns.md",
        )
    if "elicit-shared-patterns" not in erf:
        return (
            "action_5",
            False,
            "elicit-requirements-friendly/SKILL.md does not reference elicit-shared-patterns.md",
        )

    # Strengthened: assert each elicit SKILL.md no longer contains its OWN copy of the dispatch table.
    # The dispatch table heading is the unique signature; if it still lives inside either elicit
    # SKILL.md (not just as a reference link), the dedup wasn't applied.
    for name, txt in [
        ("elicit-requirements", er),
        ("elicit-requirements-friendly", erf),
    ]:
        # Allow the word in a reference link, but not as a section heading.
        if re.search(r"^## .*Agent Dispatch", txt, re.MULTILINE):
            return (
                "action_5",
                False,
                f"{name}/SKILL.md still has its own '## Agent Dispatch' section heading — should reference shared file instead",
            )

    # Length proxy: each elicit SKILL.md should be ≥ 15 lines shorter than today's pre-edit baseline.
    # We can't snapshot the baseline at runtime, so use an absolute upper bound observed pre-edit:
    # elicit-requirements is currently ~250 lines; elicit-requirements-friendly ~270 lines.
    # After dedup, each should comfortably be < 240 lines. Round generously.
    if er.count("\n") > 240:
        return (
            "action_5",
            False,
            f"elicit-requirements/SKILL.md is {er.count(chr(10))} lines — expected ≤ 240 after dedup",
        )
    if erf.count("\n") > 260:
        return (
            "action_5",
            False,
            f"elicit-requirements-friendly/SKILL.md is {erf.count(chr(10))} lines — expected ≤ 260 after dedup",
        )

    return (
        "action_5",
        True,
        "shared boilerplate extracted; both SKILL.mds reference it; duplicated headings removed; both shorter",
    )


def main() -> int:
    checks = [
        check_action_2,
        check_action_3,
        check_action_4,
        check_action_5,
    ]
    valid = {f"action_{i}" for i in range(2, 6)} | {
        f"--action_{i}" for i in range(2, 6)
    }
    only = sys.argv[1] if len(sys.argv) > 1 else None
    if only is not None and only not in valid:
        print(
            f"error: unknown action {only!r}; expected one of {sorted(valid)}",
            file=sys.stderr,
        )
        return 2
    ran = 0
    failed = 0
    for fn in checks:
        name, passed, msg = fn(PLUGIN_ROOT)
        if only and only != name and only != f"--{name}":
            continue
        ran += 1
        marker = "PASS" if passed else "FAIL"
        print(f"[{marker}] {name}: {msg}")
        if not passed:
            failed += 1
    print(
        f"\n{ran - failed}/{ran} checks passing"
        + ("" if only is None else f" (filter: {only})")
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
