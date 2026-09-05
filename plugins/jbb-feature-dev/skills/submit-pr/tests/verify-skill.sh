#!/usr/bin/env bash
# Entry point for submit-pr skill tests.
# Usage: bash tests/verify-skill.sh
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../../../agents/tests/lib/assertions.sh
source "$SKILL_DIR/../../agents/tests/lib/assertions.sh"

shopt -s nullglob
for test_file in "$SKILL_DIR/tests/test_"*.sh; do
  echo "Running ${test_file##*/}..."
  # shellcheck source=/dev/null
  source "$test_file"
done

summary
