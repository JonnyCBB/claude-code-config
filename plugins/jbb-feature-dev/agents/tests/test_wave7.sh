#!/usr/bin/env bash
# Wave 7: model ID pinning -- no bare aliases in agent frontmatter.
#
# Measurement (2026-08-25): bare alias 'opus' resolves to the PARENT session's
# model, not "latest Opus". From a sonnet session it became claude-opus-4-6;
# from an opus session it became claude-opus-5. Opus 4.6 silently clamps xhigh
# effort to high. Neither failure produces any warning.
#
# Both arms: assert bare aliases are ABSENT AND full model IDs (claude-*) are
# PRESENT. A one-sided test would pass if you deleted every model line.
#
# Effort guard: xhigh must be paired with a model measured to support it.

PLUGIN_ROOT="$(cd "$TESTS_DIR/../.." && pwd)"
PLUGINS_ROOT="$(cd "$PLUGIN_ROOT/.." && pwd)"

BARE_ALIASES=(opus sonnet haiku fable)

# --- 7.1 Negative arm: no bare alias on any agent ---
for agent_file in "$PLUGINS_ROOT"/*/agents/*.md; do
  [[ -f "$agent_file" ]] || continue
  rel="${agent_file#"$PLUGINS_ROOT/"}"
  for alias in "${BARE_ALIASES[@]}"; do
    assert_not_contains "$agent_file" "^model: ${alias}$" "${rel}: no bare '${alias}' alias"
  done
done

# --- 7.2 Positive arm: every agent has a full model ID (claude-*) ---
# Prevents the negative arm from passing vacuously when model lines are deleted.
for agent_file in "$PLUGINS_ROOT"/*/agents/*.md; do
  [[ -f "$agent_file" ]] || continue
  rel="${agent_file#"$PLUGINS_ROOT/"}"
  assert_contains "$agent_file" "^model: claude-" "${rel}: has full model ID (claude-*)"
done

# --- 7.3 Effort guard: xhigh requires claude-opus-5 (only model measured to support it) ---
for agent_file in "$PLUGINS_ROOT"/*/agents/*.md; do
  [[ -f "$agent_file" ]] || continue
  rel="${agent_file#"$PLUGINS_ROOT/"}"
  if grep -qE "^effort: xhigh" "$agent_file" 2>/dev/null; then
    assert_contains "$agent_file" "^model: claude-opus-5$" "${rel}: xhigh effort requires claude-opus-5"
  fi
done
