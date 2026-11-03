#!/usr/bin/env bash
# Wave 0: test infrastructure invariants.
#
# - 0.1: Bash harness skeleton + lib/assertions.sh
# - 0.2: Python validator + tool-union goldens
# - 0.3: Verbatim helper passes self-test
# - 0.4: parity_diff helper passes self-test

PLUGIN_ROOT="$(cd "$TESTS_DIR/../.." && pwd)"
SCRIPTS_DIR="$PLUGIN_ROOT/scripts"
GOLDEN_DIR="$SCRIPTS_DIR/golden"

# 0.1 — harness pieces present
assert_file_exists "$TESTS_DIR/verify-agents.sh" "verify-agents.sh present"
assert_file_exists "$TESTS_DIR/lib/assertions.sh" "lib/assertions.sh present"

# 0.2 — Python validator + 2 hand-rolled tool-union goldens with comment headers
assert_file_exists "$SCRIPTS_DIR/validate_consolidation.py" "validate_consolidation.py present"
for lang in python typescript; do
  assert_file_exists "$GOLDEN_DIR/${lang}-tool-union.txt" "golden ${lang}-tool-union.txt present"
  assert_contains "$GOLDEN_DIR/${lang}-tool-union.txt" "^# Source agents" "${lang} golden has Source agents comment header"
done

# Validator phase 0 must pass.
if python3 "$SCRIPTS_DIR/validate_consolidation.py" --task 0 >/dev/null 2>&1; then
  pass "validate_consolidation.py --task 0 exits 0"
else
  fail "validate_consolidation.py --task 0 exits non-zero"
fi

# 0.3 — verbatim helper self-test
if python3 "$SCRIPTS_DIR/verbatim_preserved.py" --self-test >/dev/null 2>&1; then
  pass "verbatim_preserved.py --self-test exits 0"
else
  fail "verbatim_preserved.py --self-test exits non-zero"
fi

# 0.4 — parity_diff self-test
if python3 "$SCRIPTS_DIR/parity_diff.py" --self-test >/dev/null 2>&1; then
  pass "parity_diff.py --self-test exits 0"
else
  fail "parity_diff.py --self-test exits non-zero"
fi
