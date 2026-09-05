#!/usr/bin/env python3
"""Run the agent-deck pre-close checklist. Entry point only.

    python3 ~/.claude/hooks/agent-deck-preclose.py <session-id|prefix|title>
    python3 ~/.claude/hooks/agent-deck-preclose.py --selftest

Named for the command a human types, so the guard's refusal message can quote
something readable. The logic is in preclose_checklist.py, which tests import.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from preclose_checklist import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], dict(os.environ)))
