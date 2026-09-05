"""Shared YAML frontmatter helpers for plugin validators.

Extracted from validate_consolidation.py once a second consumer
(validate_plan_b_contract_artifacts.py) appeared. Both validators import from
here so changes to the parser stay in one place.
"""

from __future__ import annotations

import sys
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised when pyyaml missing
    print(
        "ERROR: pyyaml is required. Install with: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)


def parse_frontmatter(text: str) -> dict[str, Any] | None:
    """Extract YAML frontmatter from a markdown document.

    Returns the parsed YAML mapping, or None if the document has no frontmatter,
    the frontmatter cannot be parsed, or the parsed payload is not a mapping
    (e.g., a YAML list at the top level violates the declared return contract).
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm_text = text[3:end].strip()
    try:
        result = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        return None
    if not isinstance(result, dict):
        return None
    return result


def parse_skills_field(skills_value: Any) -> set[str]:
    """Coerce a frontmatter `skills:` value to a set of skill names.

    Accepts a YAML list (`skills: [a, b]`) or a comma-separated string
    (`skills: a, b`). Anything else (None, dict, scalar non-string) yields an
    empty set so callers can detect missing/typo'd fields uniformly.
    """
    if isinstance(skills_value, list):
        # Filter to strings only — `skills: [foo, 123]` parses 123 as int and
        # would raise AttributeError on .strip() without the isinstance guard.
        return {s.strip() for s in skills_value if isinstance(s, str) and s.strip()}
    if isinstance(skills_value, str):
        return {s.strip() for s in skills_value.split(",") if s.strip()}
    return set()
