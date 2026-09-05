#!/bin/bash
# SessionStart hook: symlink plugin cache to local source for instant updates
# When plugins are installed via marketplace, Claude Code copies them to cache.
# This hook replaces cache dirs with symlinks so edits are reflected immediately.
#
# FIXED 2026-08-20 (jbrooksbartlett-dbzg). The previous version picked ONE version
# directory per plugin with `find ... | head -1` and only converted it when it was
# not already a symlink. On this machine that returned the stale `0.3.0` symlink,
# which satisfied the guard, so the hook exited having done nothing -- and the
# ACTIVE versions (jiffy-toolkit 0.13.1, eng-utils 0.11.0, jbb-feature-dev 0.22.0)
# were never converted. Editing canonical source therefore never went live, which
# is the cause behind the standing "merged to master is not live" note.
#
# Three changes:
#   1. Iterate over EVERY version directory rather than only the first.
#   2. Decide per directory by comparing the symlink target, not by testing
#      whether it happens to be a symlink at all.
#   3. Displaced real directories are MOVED ASIDE, never deleted. A SessionStart
#      hook runs unattended on every session, so it should not hold a recursive
#      delete; and cached copies can contain content that exists nowhere else
#      (measured: an untracked reference file in the active jiffy-toolkit copy).
#      Quarantined copies are left for a human to inspect or remove.

set -u

REPO="$HOME/.claude"
MARKETPLACE="jbb-claude-code-plugins"
CACHE="$HOME/.claude/plugins/cache/$MARKETPLACE"
QUARANTINE="$HOME/.claude/plugins/.cache-replaced"

# Only run if cache directory exists (plugins have been installed)
[ -d "$CACHE" ] || exit 0

changed=0
quarantined=0

for plugin_dir in "$REPO"/plugins/*/; do
  [ -d "$plugin_dir" ] || continue
  plugin_name=$(basename "$plugin_dir")
  plugin_cache="$CACHE/$plugin_name"

  # No cache entry means this plugin is not installed from the marketplace.
  [ -d "$plugin_cache" ] || continue

  # Every version directory, not just the first. A stale symlinked version must
  # not stop newer real directories from being converted.
  for version_path in "$plugin_cache"/*; do
    [ -e "$version_path" ] || [ -L "$version_path" ] || continue

    # Refuse to touch anything whose parent is not the expected cache directory.
    # Cheap guard against a surprising glob expansion reaching outside the cache.
    [ "$(dirname "$version_path")" = "$plugin_cache" ] || continue

    version_name=$(basename "$version_path")

    if [ -L "$version_path" ]; then
      # Already a symlink. Rewrite only if it points somewhere else.
      if [ "$(readlink "$version_path")" != "$plugin_dir" ]; then
        ln -sfn "$plugin_dir" "$version_path"
        echo "sync-plugins: repointed $plugin_name/$version_name"
        changed=$((changed + 1))
      fi
      continue
    fi

    # A real directory. Move it aside, then link canonical source in its place.
    if [ -d "$version_path" ]; then
      dest="$QUARANTINE/$plugin_name"
      mkdir -p "$dest" || continue
      target="$dest/$version_name"
      # Never clobber an existing quarantined copy.
      if [ -e "$target" ]; then
        target="$dest/$version_name.$(date +%Y%m%d%H%M%S)"
      fi
      if mv "$version_path" "$target"; then
        ln -sfn "$plugin_dir" "$version_path"
        echo "sync-plugins: linked $plugin_name/$version_name (previous copy moved to $target)"
        changed=$((changed + 1))
        quarantined=$((quarantined + 1))
      else
        echo "sync-plugins: WARNING could not move $version_path aside; leaving it alone"
      fi
    fi
  done
done

# Report only when something changed. A steady state stays silent, but the hook no
# longer reports success while having done nothing -- which is how the defect above
# survived unnoticed across every session for months.
if [ "$changed" -gt 0 ]; then
  echo "sync-plugins: $changed cache path(s) now symlinked to canonical source"
  if [ "$quarantined" -gt 0 ]; then
    echo "sync-plugins: $quarantined displaced copy/copies kept under $QUARANTINE (safe to delete once reviewed)"
  fi
fi

exit 0
