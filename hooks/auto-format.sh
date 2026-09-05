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

# Find the nearest ancestor that has OPTED IN to prettier.
#
# Without this, prettier ran on every .ts/.js/.json/.css/.md file anywhere on disk,
# imposing its defaults on projects that never chose it. Two real regressions:
#   - a repo with a deliberate house style (single quotes, no semicolons) had 32 files
#     / 591 lines silently rewritten against that style
#   - hand-authored markdown outside any JS project (~/.claude docs, memory files) was
#     reformatted on every edit
# Opting in means a prettier config file, or a package.json declaring prettier.
find_prettier_root() {
    local current="$1"

    while [ "$current" != "/" ]; do
        for cfg in .prettierrc .prettierrc.json .prettierrc.json5 .prettierrc.yml \
                   .prettierrc.yaml .prettierrc.toml .prettierrc.js .prettierrc.cjs \
                   .prettierrc.mjs prettier.config.js prettier.config.cjs \
                   prettier.config.mjs; do
            if [ -f "$current/$cfg" ]; then
                echo "$current"
                return 0
            fi
        done

        if [ -f "$current/package.json" ] && jq -e \
            '(.prettier != null) or (.devDependencies.prettier != null) or (.dependencies.prettier != null)' \
            "$current/package.json" >/dev/null 2>&1; then
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
        # TypeScript/JavaScript/Web: prettier, but ONLY where the project opted in.
        # Run FROM the opted-in root so the local config and local binary are picked up.
        # --no-install stops npx silently downloading prettier into a project that
        # never asked for it; a globally installed prettier is used as the fallback.
        PRETTIER_ROOT=$(find_prettier_root "$DIR") || true
        if [ -n "${PRETTIER_ROOT:-}" ]; then
            (cd "$PRETTIER_ROOT" \
                && { npx --no-install prettier --write "$ABS_FILE" 2>/dev/null \
                     || prettier --write "$ABS_FILE" 2>/dev/null; }) || true
        fi
        ;;
    *.scala)
        # Scala: find build.sbt and run scalafmtAll
        PROJECT_ROOT=$(find_project_root "$DIR" "build.sbt") || true
        if [ -n "$PROJECT_ROOT" ]; then
            (cd "$PROJECT_ROOT" && sbt scalafmtAll 2>/dev/null) || true
        fi
        ;;
    *.java)
        # Java: find pom.xml and run fmt-maven-plugin
        PROJECT_ROOT=$(find_project_root "$DIR" "pom.xml") || true
        if [ -n "$PROJECT_ROOT" ]; then
            (cd "$PROJECT_ROOT" && mvn com.example.fmt:fmt-maven-plugin:format -q 2>/dev/null) || true
        fi
        ;;
esac

exit 0
