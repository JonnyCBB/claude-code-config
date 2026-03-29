#!/bin/bash
# Load session context on startup: git status, branch, active TODOs

echo "## Session Context"
echo ""

# Git information
if git rev-parse --git-dir >/dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "N/A")
    echo "**Branch:** $BRANCH"

    # Count modified files
    MODIFIED=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    echo "**Modified files:** $MODIFIED"

    # Show recent commits
    echo ""
    echo "**Recent commits:**"
    git log --oneline -3 2>/dev/null || echo "  (none)"
else
    echo "**Git:** Not a git repository"
fi

# Check for TODO.md
if [ -f TODO.md ]; then
    echo ""
    echo "## Active TODOs"
    head -20 TODO.md
fi

exit 0
