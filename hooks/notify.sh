#!/bin/bash
# Unified notification script for Claude Code events
# Usage: notify.sh "message"

MESSAGE="${1:-Claude Code notification}"
osascript -e "display notification \"$MESSAGE\" with title \"Claude Code\" sound name \"Glass\""
