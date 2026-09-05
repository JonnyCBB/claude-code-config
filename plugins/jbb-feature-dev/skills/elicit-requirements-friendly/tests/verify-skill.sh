#!/usr/bin/env bash
# Entry point for elicit-requirements-friendly skill tests.
# Usage: bash tests/verify-skill.sh
#
# Discovers tests/test_*.sh siblings and sources each in order. Sourcing (rather
# than executing) lets the per-file scripts share PASSES/FAILS counters from
# lib/assertions.sh. nullglob ensures an empty match is not treated as a literal.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib/assertions.sh
source "$SKILL_DIR/tests/lib/assertions.sh"

# BOOTSTRAP_RED: deliberately failing assertion to prove the harness reports failures.
# Set EXPECT_BOOTSTRAP_RED=1 before invoking to enable. Leave unset for normal runs.
if [[ "${EXPECT_BOOTSTRAP_RED:-0}" == "1" ]]; then
  assert_contains /dev/null "SENTINEL" "bootstrap RED (should fail)"
fi

shopt -s nullglob
for test_file in "$SKILL_DIR/tests/test_"*.sh; do
  echo "Running ${test_file##*/}..."
  # shellcheck source=/dev/null
  source "$test_file"
done

summary
