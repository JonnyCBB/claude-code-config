#!/bin/bash
# SessionStart hook: symlink plugin cache to local source for instant updates
# When plugins are installed via marketplace, Claude Code copies them to cache.
# This hook replaces cache dirs with symlinks so edits are reflected immediately.

REPO="$HOME/.claude"
MARKETPLACE="jbb-claude-code-plugins"
CACHE="$HOME/.claude/plugins/cache/$MARKETPLACE"

# Only run if cache directory exists (plugins have been installed)
[ -d "$CACHE" ] || exit 0

for plugin_dir in "$REPO"/plugins/*/; do
  [ -d "$plugin_dir" ] || continue
  plugin_name=$(basename "$plugin_dir")

  # Find the version directory in cache
  version_dir=$(find "$CACHE/$plugin_name" -maxdepth 1 -mindepth 1 \( -type d -o -type l \) 2>/dev/null | head -1)

  if [ -n "$version_dir" ]; then
    if [ ! -L "$version_dir" ]; then
      # Replace cached copy with symlink to source
      rm -rf "$version_dir"
      ln -sfn "$plugin_dir" "$version_dir"
    elif [ "$(readlink "$version_dir")" != "$plugin_dir" ]; then
      # Symlink exists but points elsewhere — update it
      ln -sfn "$plugin_dir" "$version_dir"
    fi
  fi
done
