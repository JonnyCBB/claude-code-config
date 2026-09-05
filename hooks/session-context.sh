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

# Check for thoughts/tickets with recent files
TICKETS_DIR="$HOME/.claude/thoughts/tickets"
if [ -d "$TICKETS_DIR" ]; then
    RECENT_TICKETS=$(find "$TICKETS_DIR" -name "*.md" -mtime -7 2>/dev/null | head -3)
    if [ -n "$RECENT_TICKETS" ]; then
        echo ""
        echo "## Recent Tickets (last 7 days)"
        echo "$RECENT_TICKETS" | while read ticket; do
            basename "$ticket" .md
        done
    fi
fi

exit 0
