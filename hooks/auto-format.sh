#!/bin/bash
# Auto-format files after edits based on file extension
# Reads tool input from stdin, extracts file_path, runs appropriate formatter

set -euo pipefail

# Read input from stdin
input=$(cat)

# Extract file path
FILE=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
    exit 0
fi

# Get absolute path and find project root
ABS_FILE=$(realpath "$FILE" 2>/dev/null || echo "$FILE")
DIR=$(dirname "$ABS_FILE")

# Function to find project root (directory with build file)
find_project_root() {
    local search_dir="$1"
    local build_file="$2"
    local current="$search_dir"

    while [ "$current" != "/" ]; do
        if [ -f "$current/$build_file" ]; then
            echo "$current"
            return 0
        fi
        current=$(dirname "$current")
    done
    return 1
}

case "$FILE" in
    *.py)
        # Python: try ruff first (faster), fall back to black
        ruff format "$FILE" 2>/dev/null || black "$FILE" 2>/dev/null || true
        ;;
    *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.scss|*.md)
        # TypeScript/JavaScript/Web: use prettier
        npx prettier --write "$FILE" 2>/dev/null || true
        ;;
    *.java)
        # Java: find pom.xml and run fmt-maven-plugin
        PROJECT_ROOT=$(find_project_root "$DIR" "pom.xml") || true
        if [ -n "$PROJECT_ROOT" ]; then
            (cd "$PROJECT_ROOT" && mvn com.coveo:fmt-maven-plugin:format -q 2>/dev/null) || true
        fi
        ;;
esac

exit 0
