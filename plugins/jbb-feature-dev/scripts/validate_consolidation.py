#!/usr/bin/env python3
"""Validate the language-expert agent consolidation against plan invariants.

Adapted from validate_skill_descriptions.py (REQUIRED/DELETED set pattern).
Frontmatter parser borrowed from quick_validate.py.

Usage:
    python3 scripts/validate_consolidation.py --task <id>
        where <id> = 0 | 1 | 1.5 | 1.6 | 2 | 3 | all

Phases (selected by --task):
    0    : Wave 0 invariants (goldens exist with comment headers)
    1    : All Wave 1 invariants (1.1 .. 1.9)
    1.5  : python-expert frontmatter
    1.6  : typescript-expert frontmatter
    2    : Wave 2 invariants (registries collapsed)
    3    : Wave 3 invariants (orchestrators rewritten, no old refs)
    all  : every phase, plus master grep + underscore-form guard
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Shared frontmatter parser; re-exported here for backwards-compat with any
# importer that does `from validate_consolidation import parse_frontmatter`.
sys.path.insert(0, str(Path(__file__).parent))
# pyyaml is required by `_lib.frontmatter` and the friendly missing-pyyaml
# error lives there (frontmatter.py:13-20) — no need for a guard here.
from _lib.frontmatter import parse_frontmatter, parse_skills_field  # noqa: E402,F401

PLUGIN_ROOT = Path(__file__).parent.parent
AGENTS_DIR = PLUGIN_ROOT / "agents"
SKILLS_DIR = PLUGIN_ROOT / "skills"
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
GOLDEN_DIR = SCRIPTS_DIR / "golden"

REQUIRED_AGENTS = {"python-expert", "typescript-expert"}

LANGUAGES = ("python", "typescript")

DELETED_AGENTS = {
    "python-test-reviewer",
    "python-code-simplification-reviewer",
    "typescript-test-reviewer",
    "typescript-code-simplification-reviewer",
}

OLD_AGENT_NAMES_REGEX = re.compile("|".join(re.escape(name) for name in DELETED_AGENTS))

# Mandatory tool surface per Reqs line 77 (must be present in every language-expert agent).
MANDATORY_TOOLS = {"Bash", "Edit", "MultiEdit", "Write"}

# Skills required per language (from plan §Wave 1.3-1.6).
REQUIRED_SKILLS_PER_AGENT = {
    "python-expert": {
        "code-review-modes",
        "code-style-common",
        "python-code-style",
    },
    "typescript-expert": {
        "code-review-modes",
        "code-style-common",
        "typescript-code-style",
    },
}

GOLDEN_FILE_PER_AGENT = {
    "python-expert": "python-tool-union.txt",
    "typescript-expert": "typescript-tool-union.txt",
}

# Plugin agents do not support these fields (silently ignored). Plan §Wave 1.3 RED.
FORBIDDEN_FRONTMATTER_KEYS = {"hooks", "mcpServers", "permissionMode"}

# Plan §Wave 1.2 / Arch-7: schemas must NOT use underscore-form block names.
UNDERSCORE_FORM_PATTERN = re.compile(r"\b(TEST_NEEDED|REDUNDANT_TEST|QUALITY_ISSUE)\b")


def _record(failures: list[tuple[str, str]], name: str, reason: str) -> None:
    failures.append((name, reason))


def assert_yaml_no_bare_colon_space_outside_examples(desc):
    """Per skill-creator: description must not contain ': ' outside <example>.

    A bare colon-space inside YAML scalar value is parsed as a key/value separator
    by YAML, even if quoted in some renderers. The skill-creator scan finds these
    by stripping <example>...</example> blocks and grepping for ': ' in what
    remains. Returns True if the desc is clean.
    """
    # Strip example blocks (non-greedy, multiline)
    stripped = re.sub(r"<example>.*?</example>", "", desc, flags=re.DOTALL)
    return ": " not in stripped


def parse_tools_field(tools_value: object) -> set[str]:
    """Tools may be a YAML list OR a comma-separated string (both seen in tree)."""
    if isinstance(tools_value, list):
        return {t.strip() for t in tools_value if isinstance(t, str) and t.strip()}
    if isinstance(tools_value, str):
        return {t.strip() for t in tools_value.split(",") if t.strip()}
    return set()


def load_golden(name: str) -> set[str] | None:
    path = GOLDEN_DIR / name
    if not path.exists():
        return None
    return {
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def validate_wave_0(failures: list[tuple[str, str]]) -> None:
    """Wave 0: goldens exist with comment headers; harness present."""
    for lang in LANGUAGES:
        gpath = GOLDEN_DIR / f"{lang}-tool-union.txt"
        if not gpath.exists():
            _record(failures, f"golden/{lang}-tool-union.txt", "missing")
            continue
        text = gpath.read_text()
        if not text.lstrip().startswith("#"):
            _record(failures, f"golden/{lang}-tool-union.txt", "missing comment header")
        if "Source agents" not in text:
            _record(
                failures,
                f"golden/{lang}-tool-union.txt",
                "comment header must cite source agents",
            )
    harness = AGENTS_DIR / "tests" / "verify-agents.sh"
    if not harness.exists():
        _record(failures, "agents/tests/verify-agents.sh", "missing")


def validate_agent_frontmatter(
    agent_name: str, failures: list[tuple[str, str]]
) -> None:
    """Wave 1.3-1.6: validate one consolidated language-expert agent file."""
    path = AGENTS_DIR / f"{agent_name}.md"
    if not path.exists():
        _record(failures, agent_name, f"agent file not found: {path}")
        return

    text = path.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        _record(failures, agent_name, "YAML frontmatter failed to parse")
        return

    if fm.get("name") != agent_name:
        _record(
            failures,
            agent_name,
            f"name field must be '{agent_name}', got {fm.get('name')!r}",
        )
    if not fm.get("model"):
        _record(failures, agent_name, "model field is missing")

    desc = fm.get("description", "")
    if not desc:
        _record(failures, agent_name, "description field is empty")
    elif not assert_yaml_no_bare_colon_space_outside_examples(desc):
        _record(
            failures,
            agent_name,
            "description contains bare colon-space outside <example> (skill-creator rule)",
        )

    for forbidden in FORBIDDEN_FRONTMATTER_KEYS:
        if forbidden in fm:
            _record(
                failures,
                agent_name,
                f"frontmatter must NOT include '{forbidden}' (silently ignored in plugin agents)",
            )

    declared_tools = parse_tools_field(fm.get("tools"))
    if not declared_tools:
        _record(failures, agent_name, "tools field is empty or missing")
    else:
        missing_mandatory = MANDATORY_TOOLS - declared_tools
        if missing_mandatory:
            _record(
                failures,
                agent_name,
                f"tools missing mandatory entries (Reqs line 77): {sorted(missing_mandatory)}",
            )
        golden_set = load_golden(GOLDEN_FILE_PER_AGENT[agent_name])
        if golden_set is None:
            _record(
                failures,
                agent_name,
                f"golden file missing: {GOLDEN_FILE_PER_AGENT[agent_name]}",
            )
        else:
            missing_from_union = golden_set - declared_tools
            if missing_from_union:
                _record(
                    failures,
                    agent_name,
                    f"tools NOT a superset of golden union (Constraint line 132); missing: {sorted(missing_from_union)}",
                )

    declared_skills = parse_skills_field(fm.get("skills"))
    expected_skills = REQUIRED_SKILLS_PER_AGENT[agent_name]
    missing_skills = expected_skills - declared_skills
    if missing_skills:
        _record(
            failures,
            agent_name,
            f"skills missing required entries: {sorted(missing_skills)}",
        )

    # Body must include 5 mode sections (Reqs terminology line 58).
    expected_modes = [
        "When invoked in plan mode",
        "When invoked in implement mode",
        "When invoked in test-review mode",
        "When invoked in code-style-review mode",
        "When invoked in deep-analysis mode",
    ]
    for mode in expected_modes:
        if mode not in text:
            _record(failures, agent_name, f"body missing mode section: '{mode}'")


def validate_wave_1(failures: list[tuple[str, str]]) -> None:
    skill_md = SKILLS_DIR / "code-review-modes" / "SKILL.md"
    if not skill_md.exists():
        _record(failures, "code-review-modes/SKILL.md", "missing")
    else:
        text = skill_md.read_text()
        for heading in [
            "## Plan Mode",
            "## Implement Mode",
            "## Test-Review Mode",
            "## Code-Style-Review Mode",
            "## Deep-Analysis Mode",
        ]:
            if heading not in text:
                _record(
                    failures,
                    "code-review-modes/SKILL.md",
                    f"missing heading: {heading}",
                )
        for token in ("Precedence", "caller-explicit-only", "## CHANGE_SCOPE"):
            if token not in text:
                _record(
                    failures, "code-review-modes/SKILL.md", f"missing token: {token!r}"
                )

    for lang in LANGUAGES:
        sch = SKILLS_DIR / "code-review-modes" / "schemas" / f"{lang}.md"
        if not sch.exists():
            _record(failures, f"schemas/{lang}.md", "missing")
            continue
        text = sch.read_text()
        for heading in ("## Test-Review Schema", "## Code-Style-Review Schema"):
            if heading not in text:
                _record(failures, f"schemas/{lang}.md", f"missing heading: {heading}")
        m = UNDERSCORE_FORM_PATTERN.search(text)
        if m:
            _record(
                failures,
                f"schemas/{lang}.md",
                f"underscore-form block name found: {m.group(0)!r} (Arch-7 guard)",
            )

    for agent in sorted(REQUIRED_AGENTS):
        validate_agent_frontmatter(agent, failures)

    common = SKILLS_DIR / "code-style-common" / "test-anti-patterns.md"
    if not common.exists():
        _record(failures, "code-style-common/test-anti-patterns.md", "missing")
    else:
        text = common.read_text()
        for token in (
            "Anti-Pattern 7",
            "MissingFeatureAssertion",
            "TestNameAssertionMismatch",
            "VagueNaming",
            "MissingContext",
        ):
            if token not in text:
                _record(
                    failures,
                    "code-style-common/test-anti-patterns.md",
                    f"missing token: {token!r}",
                )

    for lang_dir, marker in (
        ("python-code-style", "pytest"),
        ("typescript-code-style", "RTL|Vitest|@testing-library"),
    ):
        tp = SKILLS_DIR / lang_dir / "testing-patterns.md"
        if not tp.exists():
            _record(failures, f"{lang_dir}/testing-patterns.md", "missing")
            continue
        text = tp.read_text()
        if "code-style-common/test-anti-patterns.md" not in text:
            _record(
                failures,
                f"{lang_dir}/testing-patterns.md",
                "missing pointer to canonical test-anti-patterns.md",
            )
        if not re.search(marker, text):
            _record(
                failures,
                f"{lang_dir}/testing-patterns.md",
                f"missing language-flavored marker: {marker!r}",
            )


def validate_wave_2(failures: list[tuple[str, str]]) -> None:
    lang_reg = SKILLS_DIR / "shared-references" / "language-agent-registry.md"
    dom_reg = SKILLS_DIR / "shared-references" / "domain-agent-registry.md"
    if not lang_reg.exists():
        _record(failures, "language-agent-registry.md", "missing")
    else:
        text = lang_reg.read_text()
        if "Expert Agent" not in text:
            _record(
                failures,
                "language-agent-registry.md",
                "Expert Agent column heading missing",
            )
        m = OLD_AGENT_NAMES_REGEX.search(text)
        if m:
            _record(
                failures,
                "language-agent-registry.md",
                f"contains old agent ref: {m.group(0)!r}",
            )
        for new in REQUIRED_AGENTS:
            if new not in text:
                _record(
                    failures,
                    "language-agent-registry.md",
                    f"missing new agent ref: {new}",
                )

    if not dom_reg.exists():
        _record(failures, "domain-agent-registry.md", "missing")
    else:
        text = dom_reg.read_text()
        m = OLD_AGENT_NAMES_REGEX.search(text)
        if m:
            _record(
                failures,
                "domain-agent-registry.md",
                f"contains old agent ref: {m.group(0)!r}",
            )


def validate_wave_3(failures: list[tuple[str, str]]) -> None:
    """Wave 3: orchestrator skills must not reference deleted old agents.

    Orchestrator targets include polish-code/SKILL.md (merged from the previous
    tidy/ and auto-tidy/ skills in 0.5.0).
    """
    targets = [
        SKILLS_DIR / "polish-code" / "SKILL.md",
        SKILLS_DIR / "code-review" / "SKILL.md",
        SKILLS_DIR / "implement-plan-tdd" / "SKILL.md",
        SKILLS_DIR / "implement-plan-tdd" / "references" / "wave-execution-guide.md",
        SKILLS_DIR / "create-plan-tdd" / "SKILL.md",
        SKILLS_DIR / "research-problem" / "references" / "agent-guide.md",
    ]
    for path in targets:
        if not path.exists():
            _record(
                failures, str(path.relative_to(PLUGIN_ROOT)), "expected file not found"
            )
            continue
        text = path.read_text()
        m = OLD_AGENT_NAMES_REGEX.search(text)
        if m:
            _record(
                failures,
                str(path.relative_to(PLUGIN_ROOT)),
                f"references old agent {m.group(0)!r}",
            )

    code_review = SKILLS_DIR / "code-review" / "SKILL.md"
    if code_review.exists():
        text = code_review.read_text()
        if "Combined-invocation fallback" not in text:
            _record(
                failures,
                "code-review/SKILL.md",
                "combined-invocation fallback section missing",
            )
        if "issue #7406" not in text:
            _record(
                failures, "code-review/SKILL.md", "issue #7406 cross-reference missing"
            )


def validate_master_grep(failures: list[tuple[str, str]]) -> None:
    """Master grep: 0 hits across agents/ and skills/, excluding tests/ and scripts/."""
    matches = []
    for root in (AGENTS_DIR, SKILLS_DIR):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(PLUGIN_ROOT)
            parts = rel.parts
            if "tests" in parts or "scripts" in parts:
                continue
            if path.suffix not in {
                ".md",
                ".txt",
                ".yaml",
                ".yml",
                ".json",
                ".sh",
                ".py",
            }:
                continue
            try:
                text = path.read_text(errors="replace")
            except OSError:
                continue
            for old in DELETED_AGENTS:
                if old in text:
                    matches.append((str(rel), old))
                    break
    for rel, old in matches:
        _record(failures, rel, f"master grep: contains deleted agent name {old!r}")


def validate_underscore_form_guard(failures: list[tuple[str, str]]) -> None:
    schemas = SKILLS_DIR / "code-review-modes" / "schemas"
    if not schemas.exists():
        return
    for path in schemas.glob("*.md"):
        text = path.read_text()
        m = UNDERSCORE_FORM_PATTERN.search(text)
        if m:
            _record(
                failures,
                str(path.relative_to(PLUGIN_ROOT)),
                f"underscore-form: {m.group(0)!r}",
            )


PHASES = {
    "0": [validate_wave_0],
    "1": [validate_wave_1],
    "1.5": [lambda f: validate_agent_frontmatter("python-expert", f)],
    "1.6": [lambda f: validate_agent_frontmatter("typescript-expert", f)],
    "2": [validate_wave_2],
    "3": [validate_wave_3],
    "all": [
        validate_wave_0,
        validate_wave_1,
        validate_wave_2,
        validate_wave_3,
        validate_master_grep,
        validate_underscore_form_guard,
    ],
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--task", default="all", help="phase id (0|1|1.5|1.6|2|3|all)")
    args = p.parse_args()

    if args.task not in PHASES:
        print(
            f"ERROR: unknown --task {args.task!r}; allowed: {sorted(PHASES)}",
            file=sys.stderr,
        )
        sys.exit(2)

    failures = []
    for fn in PHASES[args.task]:
        fn(failures)

    print("=" * 60)
    print(f"Consolidation Validation Report (--task {args.task})")
    print("=" * 60)
    if not failures:
        print(f"PASS — phase {args.task} clean.")
        sys.exit(0)
    print(f"FAILURES ({len(failures)}):")
    for name, reason in failures:
        print(f"  FAIL  {name}: {reason}")
    sys.exit(1)


if __name__ == "__main__":
    main()
