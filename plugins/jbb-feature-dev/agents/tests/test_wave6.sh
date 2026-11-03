#!/usr/bin/env bash
# Wave 6: reviewer tool-list invariants.
#
# Review/analysis agents must not hold mutating tools (Edit, Write,
# NotebookEdit, MultiEdit). Implementation agents must retain them.
# Both arms are tested — absence from reviewers AND presence on implementers —
# so deleting all tools from every agent would fail, not pass.

PLUGIN_ROOT="$(cd "$TESTS_DIR/../.." && pwd)"
PLUGINS_ROOT="$(cd "$PLUGIN_ROOT/.." && pwd)"

# --- Absence arm: no mutating tools on review/analysis agents ---

# eng-utils reviewers/verifiers/finders/reconcilers
ENG_REVIEWERS=(bug-hunt-finder bug-hunt-intent-verifier bug-hunt-mechanism-verifier bug-hunt-reconciler)
for name in "${ENG_REVIEWERS[@]}"; do
  file="$PLUGINS_ROOT/eng-utils/agents/${name}.md"
  assert_not_contains "$file" "^tools:.*\bEdit\b" "${name}: no Edit"
  assert_not_contains "$file" "^tools:.*\bWrite\b" "${name}: no Write"
  assert_not_contains "$file" "^tools:.*\bNotebookEdit\b" "${name}: no NotebookEdit"
  assert_not_contains "$file" "^tools:.*\bMultiEdit\b" "${name}: no MultiEdit"
done

# jiffy-toolkit reviewers/checkers/calibrators/deduplicators
JT_REVIEWERS=(accessibility-reviewer agent-readability-reviewer consistency-checker context-and-skills-reviewer doc-review-calibrator doc-review-deduplicator engagement-reviewer prose-quality-reviewer structure-reviewer visual-aid-reviewer)
for name in "${JT_REVIEWERS[@]}"; do
  file="$PLUGINS_ROOT/jiffy-toolkit/agents/${name}.md"
  assert_not_contains "$file" "^tools:.*\bEdit\b" "${name}: no Edit"
  assert_not_contains "$file" "^tools:.*\bWrite\b" "${name}: no Write"
  assert_not_contains "$file" "^tools:.*\bNotebookEdit\b" "${name}: no NotebookEdit"
  assert_not_contains "$file" "^tools:.*\bMultiEdit\b" "${name}: no MultiEdit"
done

# jbb-feature-dev reviewers/checkers/calibrators/deduplicators
SPF_REVIEWERS=(bug-catcher general-code-reviewer ml-pipeline-reviewer quality-checker repo-rules-reviewer review-calibrator review-deduplicator security-reviewer visual-aid-recommender)
for name in "${SPF_REVIEWERS[@]}"; do
  file="$PLUGINS_ROOT/jbb-feature-dev/agents/${name}.md"
  assert_not_contains "$file" "^tools:.*\bEdit\b" "${name}: no Edit"
  assert_not_contains "$file" "^tools:.*\bWrite\b" "${name}: no Write"
  assert_not_contains "$file" "^tools:.*\bNotebookEdit\b" "${name}: no NotebookEdit"
  assert_not_contains "$file" "^tools:.*\bMultiEdit\b" "${name}: no MultiEdit"
done

# --- Presence arm: implementation agents must retain mutating tools ---
# This prevents a naive "delete all tools from every agent" from passing.

IMPL_AGENTS=(python-expert typescript-expert)
for name in "${IMPL_AGENTS[@]}"; do
  file="$PLUGINS_ROOT/jbb-feature-dev/agents/${name}.md"
  assert_contains "$file" "^tools:.*\bEdit\b" "${name}: retains Edit"
  assert_contains "$file" "^tools:.*\bWrite\b" "${name}: retains Write"
  assert_contains "$file" "^tools:.*\bNotebookEdit\b" "${name}: retains NotebookEdit"
  assert_contains "$file" "^tools:.*\bMultiEdit\b" "${name}: retains MultiEdit"
done
