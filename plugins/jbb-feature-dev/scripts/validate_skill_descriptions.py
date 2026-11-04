#!/usr/bin/env python3
"""Validate SKILL.md descriptions against best-practice criteria."""

import sys
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required. Install with: pip install pyyaml")
    sys.exit(2)

SKILLS_DIR = Path(__file__).parent.parent / "skills"

TRIGGER_PATTERNS = [
    r"Use when ",
    r"Use for ",
    r"Use this skill when ",
    r"Use (?:this skill )?whenever ",
    r"Loaded automatically",
    r"Trigger phrases",
    r"Not typically invoked",
    r"Use after ",
    r"Use as part of",
]

INDIRECT_PATTERN = r"^This skill should be used when"


def parse_frontmatter(text):
    """Extract YAML frontmatter from markdown."""
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    fm_text = text[3:end].strip()
    try:
        return yaml.safe_load(fm_text)
    except yaml.YAMLError:
        return None


def validate_skill(skill_dir):
    """Validate a single skill's SKILL.md. Returns (pass, reason)."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    text = skill_md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return False, "YAML frontmatter failed to parse"

    desc = fm.get("description", "")
    if not desc or desc in (">", "|"):
        return False, "description field is empty"

    # Check for trigger clause
    has_trigger = any(re.search(p, desc, re.IGNORECASE) for p in TRIGGER_PATTERNS)
    if not has_trigger:
        return False, "No trigger clause found (expected 'Use when...' or similar)"

    # Check for indirect phrasing
    if re.match(INDIRECT_PATTERN, desc, re.IGNORECASE):
        return (
            False,
            "Starts with 'This skill should be used when' (use 'Use when' instead)",
        )

    return True, "PASS"


def main():
    # Discover existing skills
    existing = sorted(
        s for s in SKILLS_DIR.iterdir() if s.is_dir() and (s / "SKILL.md").exists()
    )

    failures = []
    passes = []

    for skill_dir in existing:
        ok, reason = validate_skill(skill_dir)
        if ok:
            passes.append(skill_dir.name)
        else:
            failures.append((skill_dir.name, reason))

    print(f"\n{'=' * 60}")
    print("Skill Description Validation Report")
    print(f"{'=' * 60}")
    print(f"Passed: {len(passes)}/{len(passes) + len(failures)}")

    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for name, reason in failures:
            print(f"  FAIL  {name}: {reason}")
        print()
        sys.exit(1)
    else:
        print("All skills pass validation.")
        sys.exit(0)


if __name__ == "__main__":
    main()
