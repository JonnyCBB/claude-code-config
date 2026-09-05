#!/bin/bash
# Verify plugin setup is correct
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ERRORS=0

check() {
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $desc"
  else
    echo "  FAIL: $desc"
    ERRORS=$((ERRORS + 1))
  fi
}

echo "=== Plugin Setup Verification ==="

# Marketplace
echo "Marketplace:"
check "marketplace.json exists" test -f "$REPO_ROOT/.claude-plugin/marketplace.json"
check "marketplace.json is valid JSON" python3 -c "import json; json.load(open('$REPO_ROOT/.claude-plugin/marketplace.json'))"

# Plugin structure
for plugin in jbb-feature-dev eng-utils jiffy-toolkit; do
  echo "Plugin: $plugin"
  check "plugin dir exists" test -d "$REPO_ROOT/plugins/$plugin"
  check "plugin.json exists" test -f "$REPO_ROOT/plugins/$plugin/.claude-plugin/plugin.json"
  check ".mcp.json exists" test -f "$REPO_ROOT/plugins/$plugin/.mcp.json"
done

# Hook
echo "Hook:"
check "sync-plugins.sh exists and is executable" test -x "$REPO_ROOT/hooks/sync-plugins.sh"

# Gitignore
echo "Gitignore:"
check ".claude-plugin/ whitelisted" grep -q '!\.claude-plugin/' "$REPO_ROOT/.gitignore"
check "plugins/ whitelisted" grep -q '!plugins/' "$REPO_ROOT/.gitignore"
check "scripts/ whitelisted" grep -q '!scripts/' "$REPO_ROOT/.gitignore"

# Settings
echo "Settings:"
check "sync-plugins.sh in settings" grep -q 'sync-plugins.sh' "$REPO_ROOT/settings.json"

# No duplicates
echo "Duplicates:"
check "no duplicate skills" bash -c '
  for skill_dir in "$1"/plugins/*/skills/*/; do
    [ -d "$skill_dir" ] || continue
    skill=$(basename "$skill_dir")
    if [ -d "$1/skills/$skill" ]; then
      echo "DUPLICATE: skills/$skill"; exit 1
    fi
  done
' _ "$REPO_ROOT"

check "no duplicate agents" bash -c '
  for agent in "$1"/plugins/*/agents/*.md; do
    [ -f "$agent" ] || continue
    name=$(basename "$agent")
    if [ -f "$1/agents/$name" ]; then
      echo "DUPLICATE: agents/$name"; exit 1
    fi
  done
' _ "$REPO_ROOT"

check "no duplicate commands" bash -c '
  for cmd in "$1"/plugins/*/commands/*.md; do
    [ -f "$cmd" ] || continue
    name=$(basename "$cmd")
    if [ -f "$1/commands/$name" ]; then
      echo "DUPLICATE: commands/$name"; exit 1
    fi
  done
' _ "$REPO_ROOT"

# Symlinks (only if plugins are installed via marketplace)
CACHE="$HOME/.claude/plugins/cache/jbb-claude-code-plugins"
if [ -d "$CACHE" ]; then
  echo "Cache symlinks:"
  for plugin in jbb-feature-dev eng-utils jiffy-toolkit; do
    check "$plugin cache is symlinked" bash -c '
      version_dir=$(find "'"$CACHE/$plugin"'" -maxdepth 1 -mindepth 1 \( -type d -o -type l \) 2>/dev/null | head -1)
      [ -L "$version_dir" ]
    '
  done
else
  echo "Cache symlinks: SKIPPED (plugins not installed yet)"
fi

echo ""
if [ "$ERRORS" -eq 0 ]; then
  echo "ALL CHECKS PASSED"
else
  echo "$ERRORS CHECK(S) FAILED"
  exit 1
fi
