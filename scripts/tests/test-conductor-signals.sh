#!/usr/bin/env bash
# Tests for scripts/conductor-signals.sh
#
# Every case here answers one of the two questions the bead demands:
#   - a case that SHOULD fire, proving the signal fires
#   - a case that SHOULD NOT fire, proving it stays silent
#
# The script's three external readers (bd, gh, agent-deck) are stubbed on PATH.
# The capacity read is supplied with --resources-from, the same flag the
# conductor can use to re-evaluate a captured reading.
#
# Run: bash scripts/tests/test-conductor-signals.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUT="$SCRIPT_DIR/conductor-signals.sh"

PASS=0
FAIL=0

# Bootstrap-RED sentinel, matching the convention in plugins/*/tests/verify-*.sh.
# Without it a harness that recorded zero assertions would print "0 passed,
# 0 failed" and exit 0 - green. This repo has no CI (jbrooksbartlett-sqmi), so
# this suite is the only gate and it has to prove it can report a failure.
#   EXPECT_BOOTSTRAP_RED=1 bash scripts/tests/test-conductor-signals.sh
# must exit non-zero and show exactly one FAIL.
BOOTSTRAP_RED=${EXPECT_BOOTSTRAP_RED:-0}

fail() {
  FAIL=$((FAIL + 1))
  printf '  FAIL  %s\n' "$1"
  [ $# -gt 1 ] && printf '        %s\n' "$2"
  return 0
}

pass() {
  PASS=$((PASS + 1))
  printf '  ok    %s\n' "$1"
}

assert_contains() {
  local haystack=$1 needle=$2 what=$3
  case "$haystack" in
  *"$needle"*) pass "$what" ;;
  *) fail "$what" "expected to find: $needle" ;;
  esac
}

assert_not_contains() {
  local haystack=$1 needle=$2 what=$3
  case "$haystack" in
  *"$needle"*) fail "$what" "expected NOT to find, but did: $needle" ;;
  *) pass "$what" ;;
  esac
}

# ---------------------------------------------------------------------------
# Fixture rig
# ---------------------------------------------------------------------------

if [ "$BOOTSTRAP_RED" = "1" ]; then
  fail "bootstrap-RED sentinel: deliberate FAIL (verifies the harness reports failures)"
else
  pass "harness sanity"
fi

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

FIX="$WORK/fixtures"
STUBS="$WORK/stubs"
mkdir -p "$FIX" "$STUBS"

# bd stub: serves bd-list.json for `bd list`, bd-ready.json for `bd ready`.
cat >"$STUBS/bd" <<'STUB'
#!/usr/bin/env bash
sub=$1
shift
case "$sub" in
list)
  case "$*" in
  *--label*) cat "$FIXTURE_DIR/bd-acked.json" ;;
  *) cat "$FIXTURE_DIR/bd-list.json" ;;
  esac
  ;;
ready) cat "$FIXTURE_DIR/bd-ready.json" ;;
# bd show is the only read that reports a truthful dependent_count; bd list
# answers 0 for every bead. The fixtures reproduce that split on purpose.
# It takes many ids at once, so the stub filters on all non-flag arguments.
show)
  ids=""
  for a in "$@"; do case "$a" in --*) ;; *) ids="$ids $a" ;; esac; done
  jq -c --arg ids "$ids" \
    '($ids | split(" ")) as $want | [.[] | select(.id as $i | $want | index($i))]' \
    "$FIXTURE_DIR/bd-show.json"
  ;;
*) echo "[]" ;;
esac
STUB

# gh stub: `gh pr list --state merged` serves gh-merged.json;
# `gh pr list --head X --state open` serves gh-open-X.json, or [] when absent.
cat >"$STUBS/gh" <<'STUB'
#!/usr/bin/env bash
head=""
merged=0
while [ $# -gt 0 ]; do
  case "$1" in
  --head)
    head=$2
    shift
    ;;
  merged) merged=1 ;;
  esac
  shift
done
if [ "$merged" = 1 ]; then
  cat "$FIXTURE_DIR/gh-merged.json"
elif [ -n "$head" ] && [ -f "$FIXTURE_DIR/gh-open-$head.json" ]; then
  cat "$FIXTURE_DIR/gh-open-$head.json"
else
  echo "[]"
fi
STUB

# agent-deck stub: `agent-deck list --json` serves sessions.json.
cat >"$STUBS/agent-deck" <<'STUB'
#!/usr/bin/env bash
cat "$FIXTURE_DIR/sessions.json"
STUB

chmod +x "$STUBS"/*
export PATH="$STUBS:$PATH"
export FIXTURE_DIR="$FIX"

# A real git worktree per fake worker session, so the branch resolution under
# test is the real `git rev-parse`, not a stub of it.
make_worker_repo() {
  local name=$1 branch=$2
  local dir="$WORK/repos/$name/.worktrees/$branch"
  mkdir -p "$dir"
  git -C "$dir" init -q -b "$branch" 2>/dev/null
  git -C "$dir" -c user.email=t@t -c user.name=t -c commit.gpgsign=false commit -q --allow-empty -m init
  printf '%s' "$dir"
}

write_resources() {
  cat >"$FIX/resources-$1.json"
}

# Pull the number off a signal line, so assertions test the computed value
# rather than the dot leaders. Nine assertions used to break on a cosmetic
# change to the padding.
# Returns the rendered token, which is deliberately NOT always a number:
#   5     a real measurement
#   >=5   measured, but blind somewhere - a floor
#   ?     could not be measured at all
# A test that only ever accepted digits would let "?" regress to "0" unnoticed,
# which is the exact confusion this script exists to prevent.
signal_value() { # <output> <signal number> -> the rendered token, or "" if absent
  sed -n "s/^$2  [a-z-]* *\.* *\([^ ]*\).*/\1/p" <<<"$1" | head -1
}

assert_equals() {
  local got=$1 want=$2 what=$3
  if [ "$got" = "$want" ]; then pass "$what"; else fail "$what" "got [$got], wanted [$want]"; fi
}

# Fixture PR dates are generated relative to today. Hardcoded dates were a time
# bomb: the SUT filters merged PRs to a rolling CONDUCTOR_SIGNALS_PR_DAYS window,
# so absolute 2026-08-15 fixtures would have silently aged out on 2026-08-29 and
# taken all eight "signal 1 fires" assertions red for no code reason.
days_ago_iso() { date -u -v-"$1"d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d "$1 days ago" +%Y-%m-%dT%H:%M:%SZ; }
days_ago_date() { date -u -v-"$1"d +%Y-%m-%d 2>/dev/null || date -u -d "$1 days ago" +%Y-%m-%d; }
D3=$(days_ago_iso 3)
D2=$(days_ago_iso 2)
D1=$(days_ago_iso 1)
D40=$(days_ago_iso 40)

# Fixtures are written in QUOTED heredocs and dated afterwards through these
# placeholders. An unquoted heredoc would expand the fixtures' own backticks:
# "Closes `jbrooksbartlett-fire1`." ran as command substitution and produced
# "Closes ." - still valid JSON, so the validator below could not see it, and
# four signal-1 assertions went red for a reason nowhere near the code.
date_the_fixtures() {
  sed -i '' -e "s/@D3@/$D3/g" -e "s/@D2@/$D2/g" -e "s/@D1@/$D1/g" -e "s/@D40@/$D40/g" \
    "$FIX/gh-merged.json" 2>/dev/null || true
}

run_sut() {
  date_the_fixtures
  # A malformed fixture makes the SUT report 0 hits, which reads exactly like a
  # clean queue. That happened during development - a trailing comma in
  # gh-merged.json turned every signal-1 assertion green-adjacent and silent.
  # Fail loudly instead.
  local f
  for f in "$FIX"/*.json; do
    [ -e "$f" ] || continue
    case "$f" in *resources-garbage.json) continue ;; esac
    jq -e . "$f" >/dev/null 2>&1 || fail "fixture is not valid JSON: ${f##*/}"
  done
  # Valid JSON is not enough: check no placeholder survived and no date is empty.
  if grep -q '@D[0-9]*@' "$FIX/gh-merged.json" 2>/dev/null; then
    fail "fixture still contains an unsubstituted date placeholder"
  fi
  CONDUCTOR_SIGNALS_REPOS="$1" \
    CONDUCTOR_SIGNALS_STATE_DIR="$WORK/state" \
    "$SUT" --resources-from "$FIX/resources-$2.json" 2>&1
}

# ---------------------------------------------------------------------------
# SIGNAL 1
# ---------------------------------------------------------------------------

printf '\nSIGNAL 1 - complete but open\n'

REPO="$WORK/repos/demo"
mkdir -p "$REPO"

# Beads:
#   fire1  in_progress, closed by a merged PR via an explicit closure verb   -> SHOULD FIRE
#   fire2  in_progress, mutually cited with merged PR #77                    -> SHOULD FIRE
#   quiet1 in_progress, merely MENTIONED by a merged PR (a follow-up it
#          filed), cites no PR of its own                                    -> SHOULD STAY SILENT
#   quiet2 in_progress, named by an OPEN PR only                             -> SHOULD STAY SILENT
#   quiet3 already closed, named by a merged PR with a closure verb          -> SHOULD STAY SILENT
cat >"$FIX/bd-list.json" <<'JSON'
[
  {"id":"jbrooksbartlett-fire1","status":"in_progress","dependent_count":0,
   "title":"silent auth failure reports success",
   "description":"A revoked token yields DRAFT_CREATED with no experiment.","notes":""},
  {"id":"jbrooksbartlett-fire2","status":"in_progress","dependent_count":0,
   "title":"composed workflow namespaces resolve blank",
   "description":"Namespaces fold wrong.","notes":"Do not close it until PR #77 merges."},
  {"id":"jbrooksbartlett-quiet1","status":"open","dependent_count":0,
   "title":"follow-up filed by the fire1 PR",
   "description":"Cache the gRPC channel per provider call.","notes":""},
  {"id":"jbrooksbartlett-quiet2","status":"open","dependent_count":1,
   "title":"work still in review",
   "description":"Not merged yet.","notes":""},
  {"id":"jbrooksbartlett-quiet3","status":"closed","dependent_count":0,
   "title":"already closed",
   "description":"Done.","notes":""},
  {"id":"jbrooksbartlett-quiet4","status":"open","dependent_count":0,
   "title":"partially addressed, deliberately still open",
   "description":"Master is red from two distinct causes.",
   "notes":"All nine PASSED in PR #55's green build, but the other half is untouched."},
  {"id":"jbrooksbartlett-quiet5","status":"open","dependent_count":0,
   "title":"a merged PR that explicitly does not resolve it",
   "description":"The JUnit report is still absent.",
   "notes":"*** THE JUnit FIX (PR #66) DOES NOT RESOLVE THIS BEAD. Leave it standing. ***"},
  {"id":"jbrooksbartlett-quiet6","status":"open","dependent_count":0,
   "title":"raised against a PR that did not fix it",
   "description":"A2A transport has no equivalent check.",
   "notes":"Raised by independent review as M6 against PR #42. NOT fixed on that branch."},
  {"id":"jbrooksbartlett-quiet7","status":"open","dependent_count":0,
   "title":"the natural English negation on the bead side",
   "description":"Still broken.",
   "notes":"This is NOT resolved by PR #77. Not closed by PR #77 either - the branch was abandoned."},
  {"id":"jbrooksbartlett-quiet8","status":"open","dependent_count":0,
   "title":"judged and deliberately kept open",
   "description":"Half of it landed.","notes":"RESOLVED BY PR #91, but only the first half."},
  {"id":"jbrooksbartlett-quiet9","status":"open","dependent_count":7,
   "title":"a parent whose children are still open",
   "description":"Seven children remain.","notes":""},
  {"id":"jbrooksbartlett-fire3","status":"open","dependent_count":0,
   "title":"a clear declaration plus an unrelated denial elsewhere",
   "description":"The gates do not run on master.",
   "notes":"Two neutral checks and nothing can resolve which. WHY PR #77 matters is separate. *** RESOLVED BY switchboard PR #77. ***"}
]
JSON

# quiet8 is a hit the conductor has judged and chosen to keep open.
cat >"$FIX/bd-acked.json" <<'JSON'
[{"id":"jbrooksbartlett-quiet8"}]
JSON

cat >"$FIX/gh-merged.json" <<'JSON'
[
  {"number":42,"mergedAt":"@D3@","headRefName":"feature/fix-toolset",
   "title":"fix(c4s): a toolset that fails to load must not report DRAFT_CREATED",
   "body":"Closes `jbrooksbartlett-fire1`.\n\nFollow-up filed: jbrooksbartlett-quiet1 covers channel caching.\n\nAlso raised in review: jbrooksbartlett-quiet6, out of scope here."},
  {"number":77,"mergedAt":"@D2@","headRefName":"feature/fix-namespaces",
   "title":"fix: resolve composed-workflow namespaces",
   "body":"Namespace folding, per jbrooksbartlett-fire2. No closure verb anywhere in this body.\n\nAlso touches jbrooksbartlett-quiet7 and jbrooksbartlett-fire3."},
  {"number":91,"mergedAt":"@D1@","headRefName":"feature/already-done",
   "title":"chore: tidy",
   "body":"Closes jbrooksbartlett-quiet3. Related: jbrooksbartlett-quiet8.\n\ncannot close jbrooksbartlett-quiet9: 7 open child issue(s); close children first"},
  {"number":55,"mergedAt":"@D2@","headRefName":"feature/partial",
   "title":"test(ci): join the xdist group (PARTIAL fix for jbrooksbartlett-quiet4)",
   "body":"> **This is a PARTIAL fix. It does not close jbrooksbartlett-quiet4.**\n\nRefs: jbrooksbartlett-quiet4 (stays open)"},
  {"number":66,"mergedAt":"@D1@","headRefName":"feature/junit",
   "title":"ci: emit a JUnit report",
   "body":"Touches the same area as jbrooksbartlett-quiet5."}
]
JSON

# bd show tells the truth about dependents where bd list does not.
cat >"$FIX/bd-show.json" <<'JSON'
[
  {"id":"jbrooksbartlett-fire1","dependent_count":6},
  {"id":"jbrooksbartlett-fire2","dependent_count":2},
  {"id":"jbrooksbartlett-fire3","dependent_count":0}
]
JSON

echo '[]' >"$FIX/bd-ready.json"
echo '[]' >"$FIX/sessions.json"
write_resources ok <<'JSON'
{"mem_free_pct":58,"swap_free_mb":9000,"load1":3.34,"swapouts_delta":0,"sampled":true}
JSON

OUT=$(run_sut "$REPO" ok)

assert_contains "$OUT" "jbrooksbartlett-fire1" \
  "fires on a bead whose merged PR declares it closed"
assert_contains "$OUT" "#42" \
  "names the merged PR that is the evidence"
assert_contains "$OUT" "jbrooksbartlett-fire2" \
  "fires on a bead mutually cited with a merged PR"
assert_contains "$OUT" "#77" \
  "names the mutually cited PR"
assert_not_contains "$OUT" "jbrooksbartlett-quiet1" \
  "stays silent on a bead a merged PR merely MENTIONS as a follow-up"
assert_not_contains "$OUT" "jbrooksbartlett-quiet3" \
  "stays silent on a bead that is already closed"
assert_not_contains "$OUT" "jbrooksbartlett-quiet4" \
  "stays silent when the merged PR says it does NOT close the bead"
assert_not_contains "$OUT" "jbrooksbartlett-quiet5" \
  "stays silent when the bead says the merged PR does NOT resolve it"
assert_not_contains "$OUT" "jbrooksbartlett-quiet6" \
  "stays silent on a bead raised against a PR that did not fix it"
assert_not_contains "$OUT" "jbrooksbartlett-quiet7" \
  "stays silent on the natural English negation: 'This is NOT resolved by PR #77'"
assert_not_contains "$OUT" "jbrooksbartlett-quiet8" \
  "stays silent on a hit already labelled signal1-ack"
# Verbatim from switchboard PR #30, which quotes a UI error in its body. Found
# by running against the live queue; "not" inside "cannot" is preceded by a
# letter, so the word-boundary guard alone does not catch it.
assert_not_contains "$OUT" "jbrooksbartlett-quiet9" \
  "stays silent on 'cannot close <id>: 7 open child issue(s)'"
assert_contains "$OUT" "jbrooksbartlett-fire3" \
  "a denial in one clause does not veto a declaration in another"
assert_contains "$OUT" "1  complete-but-open .......... 3" \
  "counts exactly the three beads that should fire"
assert_contains "$OUT" "6 dependents blocked" \
  "reports the dependent count from bd show, not the 0 that bd list answers"
assert_contains "$OUT" "signal1-ack" \
  "tells the reader how to silence a hit it should keep reporting otherwise"

# An UNMERGED PR that declares closure must not fire. The earlier version of
# this case fed the SUT an empty merged list and a separate gh-open-* fixture,
# which signal 1 never reads - so both assertions passed without exercising
# anything, and would still have passed if `--state merged` became `--state all`.
# The PR now sits in the merged-PR fixture with mergedAt null, so the SUT's own
# `select(.mergedAt >= $since)` filter is the thing under test.
printf '\nSIGNAL 1 - an unmerged PR is not evidence of completion\n'
cat >"$FIX/gh-merged.json" <<'JSON'
[
  {"number":42,"mergedAt":null,"headRefName":"feature/fix-toolset",
   "title":"fix(c4s): a toolset that fails to load must not report DRAFT_CREATED",
   "body":"Closes `jbrooksbartlett-fire1`."}
]
JSON
OUT=$(run_sut "$REPO" ok)
assert_equals "$(signal_value "$OUT" 1)" "0" \
  "a PR declaring closure but not merged does not fire the signal"
assert_not_contains "$OUT" "jbrooksbartlett-fire1" \
  "stays silent while the PR is unmerged"

# And a PR merged before the window must age out rather than linger.
#
# Run with a POSITIVE CONTROL first. On its own, "out of window -> 0 hits" is
# unfalsifiable: an empty or broken fixture scores 0 too. The control uses a
# byte-identical fixture that differs only in the date, so a passing pair means
# the date is genuinely what moved.
printf '\nSIGNAL 1 - the merge window is what decides scope\n'
window_fixture() { # <date placeholder, substituted by date_the_fixtures>
  cat >"$FIX/gh-merged.json" <<'JSON'
[
  {"number":42,"mergedAt":"@DATE@","headRefName":"feature/fix-toolset",
   "title":"old","body":"Closes `jbrooksbartlett-fire1`."}
]
JSON
  sed -i '' "s/@DATE@/$1/" "$FIX/gh-merged.json"
}

window_fixture '@D1@'
OUT=$(run_sut "$REPO" ok)
assert_equals "$(signal_value "$OUT" 1)" "1" \
  "CONTROL: the same PR merged yesterday does fire"

window_fixture '@D40@'
OUT=$(run_sut "$REPO" ok)
assert_equals "$(signal_value "$OUT" 1)" "0" \
  "the same PR merged 40 days ago falls outside the 14-day window"

# ---------------------------------------------------------------------------
# SIGNAL 2
# ---------------------------------------------------------------------------

printf '\nSIGNAL 1 - an unreadable repo is a gap, not a clean zero\n'
# GHE was unreachable for ~16 hours on 2026-08-15/16. A signal that reports 0
# because it could not read anything is worse than no signal.
printf 'not json\n' >"$FIX/gh-merged.json"
OUT=$(CONDUCTOR_SIGNALS_REPOS="$REPO" CONDUCTOR_SIGNALS_STATE_DIR="$WORK/state" \
  "$SUT" --resources-from "$FIX/resources-ok.json" 2>&1)
assert_contains "$OUT" "NOT A CLEAN READ" \
  "says the merged-PR read failed instead of reporting a clean zero"
assert_contains "$OUT" "demo" \
  "names the repo it could not read"

printf '\nSIGNAL 2 - ready work idle while capacity is free\n'

cat >"$FIX/gh-merged.json" <<'JSON'
[]
JSON
rm -f "$FIX/gh-open-feature-fix-toolset.json"

# 5 ready beads, 1 active worker, 1 parked worker, cap 3 -> 2 free -> signal 2.
cat >"$FIX/bd-ready.json" <<'JSON'
[{"id":"a"},{"id":"b"},{"id":"c"},{"id":"d"},{"id":"e"}]
JSON

ACTIVE_DIR=$(make_worker_repo demo active-branch)
PARKED_DIR=$(make_worker_repo demo parked-branch)
cat >"$FIX/gh-open-parked-branch.json" <<'JSON'
[{"number":143,"body":"awaiting review"}]
JSON

cat >"$FIX/sessions.json" <<JSON
[
  {"id":"s1","title":"worker-active","status":"running","path":"$ACTIVE_DIR"},
  {"id":"s2","title":"worker-parked","status":"waiting","path":"$PARKED_DIR"},
  {"id":"s3","title":"conductor-hq","status":"running","path":"$WORK/not-a-worktree"}
]
JSON

OUT=$(run_sut "$REPO" ok)
assert_contains "$OUT" "2  dispatchable-now ........... 2" \
  "fires with the number of dispatches that should happen now"
assert_contains "$OUT" "parked 1" \
  "a session with an open PR on its branch is parked, not active"
assert_contains "$OUT" "active 1" \
  "only the worktree session without an open PR counts against the cap"

printf '\nSIGNAL 2 - stays silent when the cap is full\n'
B1=$(make_worker_repo demo w1)
B2=$(make_worker_repo demo w2)
B3=$(make_worker_repo demo w3)
cat >"$FIX/sessions.json" <<JSON
[
  {"id":"s1","title":"w1","status":"running","path":"$B1"},
  {"id":"s2","title":"w2","status":"running","path":"$B2"},
  {"id":"s3","title":"w3","status":"waiting","path":"$B3"}
]
JSON
OUT=$(run_sut "$REPO" ok)
assert_contains "$OUT" "2  dispatchable-now ........... 0" \
  "stays silent when three active workers hold the cap"

printf '\nSIGNAL 2 - stays silent when the machine is vetoed\n'
write_resources veto <<'JSON'
{"mem_free_pct":58,"swap_free_mb":1007,"load1":3.34,"swapouts_delta":0,"sampled":true}
JSON
cat >"$FIX/sessions.json" <<'JSON'
[]
JSON
OUT=$(run_sut "$REPO" veto)
assert_contains "$OUT" "2  dispatchable-now ........... 0" \
  "the contract's swap-free veto suppresses the signal"
assert_contains "$OUT" "swapouts delta 0" \
  "reports the live swapouts delta alongside the contract reading"
assert_contains "$OUT" "jbrooksbartlett-cjxs" \
  "names the open bead when the two capacity readings disagree"

printf '\nSIGNAL 2 - an unreadable capacity read is a veto, not a pass\n'
printf 'not json at all\n' >"$FIX/resources-garbage.json"
OUT=$(run_sut "$REPO" garbage)
assert_contains "$OUT" "UNREADABLE" \
  "says so when a reading could not be parsed"
assert_equals "$(signal_value "$OUT" 2)" "?" \
  "reports readings it could not parse as unmeasured, not as a measured zero"

printf '\nSIGNAL 2 - an unsampled run says the disagreement check could not run\n'
# Same swap veto as the disagreement case, but with no swapouts sample taken -
# which is what --fast produces. The note must not appear, and its absence must
# be explained rather than silent.
write_resources notsampled <<'JSON'
{"mem_free_pct":58,"swap_free_mb":1007,"load1":3.34,"swapouts_delta":-1,"sampled":false}
JSON
OUT=$(run_sut "$REPO" notsampled)
assert_contains "$OUT" "NOT SAMPLED" \
  "names the check it skipped rather than silently omitting it"
assert_not_contains "$OUT" "READINGS DISAGREE" \
  "does not claim a disagreement it did not measure"

printf '\nSIGNAL 1 - an unreadable bd is a gap, not a clean zero\n'
# Observed live: one run reported 0 complete-but-open beads when the true answer
# was 5, because bd returned a short array and nothing noticed. Dolt lock
# contention and a bd upgrade changing --json both produce this.
cat >"$FIX/gh-merged.json" <<'JSON'
[]
JSON
printf 'not json at all\n' >"$FIX/bd-list-broken.json"
cat >"$STUBS/bd" <<'STUB'
#!/usr/bin/env bash
echo "database is locked" >&2
exit 1
STUB
chmod +x "$STUBS/bd"
OUT=$(run_sut "$REPO" ok)
assert_contains "$OUT" "NOT A CLEAN READ" \
  "says the bead queue could not be read instead of reporting a clean 0"
assert_contains "$OUT" "bd list returned nothing usable" \
  "names which read failed"
assert_contains "$OUT" "FLOOR" \
  "labels the numbers as a floor, not an answer"

printf '\nSIGNAL 2 - an unreadable session list vetoes dispatch\n'
# ACTIVE=0 would mean the whole cap is free, so the signal would urge dispatch
# while real workers run - the one error that can break the cap.
cat >"$STUBS/bd" <<'STUB'
#!/usr/bin/env bash
sub=$1
shift
case "$sub" in
list)
  case "$*" in
  *--label*) cat "$FIXTURE_DIR/bd-acked.json" ;;
  *) cat "$FIXTURE_DIR/bd-list.json" ;;
  esac
  ;;
ready) cat "$FIXTURE_DIR/bd-ready.json" ;;
show)
  ids=""
  for a in "$@"; do case "$a" in --*) ;; *) ids="$ids $a" ;; esac; done
  jq -c --arg ids "$ids" \
    '($ids | split(" ")) as $want | [.[] | select(.id as $i | $want | index($i))]' \
    "$FIXTURE_DIR/bd-show.json"
  ;;
*) echo "[]" ;;
esac
STUB
cat >"$STUBS/agent-deck" <<'STUB'
#!/usr/bin/env bash
echo "connection refused" >&2
exit 1
STUB
chmod +x "$STUBS/bd" "$STUBS/agent-deck"
cat >"$FIX/bd-ready.json" <<'JSON'
[{"id":"a"},{"id":"b"},{"id":"c"},{"id":"d"},{"id":"e"}]
JSON
OUT=$(run_sut "$REPO" ok)
assert_equals "$(signal_value "$OUT" 2)" "?" \
  "reports an unknown session count as unmeasured, not as a measured zero"
assert_contains "$OUT" "agent-deck list returned nothing usable" \
  "names the session list as the read that failed"

# Restore a working agent-deck for the remaining cases.
cat >"$STUBS/agent-deck" <<'STUB'
#!/usr/bin/env bash
cat "$FIXTURE_DIR/sessions.json"
STUB
chmod +x "$STUBS/agent-deck"
cat >"$FIX/sessions.json" <<'JSON'
[]
JSON

printf '\nSIGNAL 2 - the memory and load thresholds can actually fire\n'
# Every earlier fixture used mem 58 / load 3.34, so only the swap arm was ever
# exercised. A threshold that can never trip would pass the suite.
write_resources lowmem <<'JSON'
{"mem_free_pct":9,"swap_free_mb":9000,"load1":3.34,"swapouts_delta":0,"sampled":true}
JSON
OUT=$(run_sut "$REPO" lowmem)
assert_contains "$OUT" "memory-free-9%" \
  "the memory threshold vetoes when free memory is below 25 percent"
assert_equals "$(signal_value "$OUT" 2)" "0" \
  "a memory veto suppresses the dispatch signal"

write_resources highload <<'JSON'
{"mem_free_pct":58,"swap_free_mb":9000,"load1":14.2,"swapouts_delta":0,"sampled":true}
JSON
OUT=$(run_sut "$REPO" highload)
assert_contains "$OUT" "load-14.2" \
  "the load threshold vetoes above 9"

printf '\nSIGNAL 2 - no disagreement note when both readings agree\n'
write_resources both <<'JSON'
{"mem_free_pct":58,"swap_free_mb":9000,"load1":3.34,"swapouts_delta":0,"sampled":true}
JSON
OUT=$(run_sut "$REPO" both)
assert_not_contains "$OUT" "jbrooksbartlett-cjxs" \
  "stays silent about the disagreement when there is none"

# ---------------------------------------------------------------------------
# SIGNAL 3
# ---------------------------------------------------------------------------

printf '\nSIGNAL 3 - escalation counter\n'

OUT=$(run_sut "$REPO" ok)
assert_equals "$(signal_value "$OUT" 3)" "0" \
  "reads a measured zero before anything is recorded"

CONDUCTOR_SIGNALS_STATE_DIR="$WORK/state" "$SUT" escalate 6 "asked about merging a follow-up PR" >/dev/null 2>&1
CONDUCTOR_SIGNALS_STATE_DIR="$WORK/state" "$SUT" escalate 3 "announced a dispatch and waited" >/dev/null 2>&1
OUT=$(run_sut "$REPO" ok)
assert_equals "$(signal_value "$OUT" 3)" "2" \
  "counts the escalations the conductor recorded"
assert_contains "$OUT" "section 6" \
  "names the contract section that should have been applied"

# The steady state on every day after the first escalation: the log has prior
# entries but none today. `grep -c` prints 0 AND exits 1, so a `|| echo 0`
# fallback appended a SECOND count - splitting the line and erroring to stderr.
printf '\nSIGNAL 3 - prior-day entries with none today\n'
cat >"$WORK/state/escalations.jsonl" <<JSON
{"ts":"$D40","section":"6","what":"outside the 7-day window"}
{"ts":"$D2","section":"6","what":"a"}
{"ts":"$D1","section":"3","what":"b"}
JSON
OUT=$(run_sut "$REPO" ok)
assert_equals "$(signal_value "$OUT" 3)" "0" \
  "reports today's count as 0 when only prior days have entries"
assert_equals "$(grep -c 'escalations \.\.\.' <<<"$OUT")" "1" \
  "keeps the signal-3 line intact instead of splitting it across two lines"
# The average is the whole point of the prior-7d window and nothing checked it.
# Two of the three entries are inside the window (the third is 40 days old), so
# the reported rate must be 2/7 = 0.3.
assert_contains "$OUT" "prior 7d: 0.3/day" \
  "computes the prior-7-day average, excluding today and anything older"

# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# ALL THREE NUMBERS: measured zero must be distinguishable from unmeasured
# ---------------------------------------------------------------------------
#
# This is the property the whole script exists for. A 0 printed next to
# "target 0" reads as reassurance, so a 0 that means "I did not look" is worse
# than no signal at all. Each signal is checked BOTH ways: a real zero renders
# as 0, and an unmeasurable one renders as something a reader cannot mistake
# for it.

printf '\nALL THREE - a measured zero renders as 0\n'
cat >"$FIX/gh-merged.json" <<'JSON'
[]
JSON
cat >"$FIX/bd-ready.json" <<'JSON'
[]
JSON
cat >"$FIX/sessions.json" <<'JSON'
[]
JSON
: >"$WORK/state/escalations.jsonl"
OUT=$(run_sut "$REPO" ok)
assert_equals "$(signal_value "$OUT" 1)" "0" "signal 1 measured zero renders as 0"
assert_equals "$(signal_value "$OUT" 2)" "0" "signal 2 measured zero renders as 0"
assert_equals "$(signal_value "$OUT" 3)" "0" "signal 3 measured zero renders as 0"
assert_not_contains "$OUT" "NOT A CLEAN READ" \
  "a fully measured run carries no gap banner"

printf '\nALL THREE - an unmeasurable signal never renders as 0\n'
# bd down takes signal 1 (no bead set) and signal 2 (no ready queue);
# agent-deck down takes signal 2; an unreadable log takes signal 3.
cat >"$STUBS/bd" <<'STUB'
#!/usr/bin/env bash
echo "database is locked" >&2
exit 1
STUB
cat >"$STUBS/agent-deck" <<'STUB'
#!/usr/bin/env bash
exit 1
STUB
chmod +x "$STUBS/bd" "$STUBS/agent-deck"
printf 'not json\n' >"$WORK/state/escalations.jsonl"
OUT=$(run_sut "$REPO" ok)
assert_equals "$(signal_value "$OUT" 1)" "?" "signal 1 unmeasured renders as ? not 0"
assert_equals "$(signal_value "$OUT" 2)" "?" "signal 2 unmeasured renders as ? not 0"
assert_equals "$(signal_value "$OUT" 3)" "?" "signal 3 unmeasured renders as ? not 0"
assert_contains "$OUT" "NOT A CLEAN READ" \
  "the gap banner says the run was not clean"
assert_contains "$OUT" "could not be measured at all" \
  "the banner explains what the marker means"

printf '\nALL THREE - a partial blind spot renders as a floor, not a clean count\n'
# bd and the escalation log are fine; one configured repo does not exist, so
# signal 1 has looked at some PRs but not all of them.
cat >"$STUBS/bd" <<'STUB'
#!/usr/bin/env bash
sub=$1
shift
case "$sub" in
list)
  case "$*" in
  *--label*) cat "$FIXTURE_DIR/bd-acked.json" ;;
  *) cat "$FIXTURE_DIR/bd-list.json" ;;
  esac
  ;;
ready) cat "$FIXTURE_DIR/bd-ready.json" ;;
show) echo '[]' ;;
*) echo "[]" ;;
esac
STUB
cat >"$STUBS/agent-deck" <<'STUB'
#!/usr/bin/env bash
cat "$FIXTURE_DIR/sessions.json"
STUB
chmod +x "$STUBS/bd" "$STUBS/agent-deck"
: >"$WORK/state/escalations.jsonl"
OUT=$(run_sut "$REPO:$WORK/no-such-repo" ok)
assert_equals "$(signal_value "$OUT" 1)" ">=0" \
  "signal 1 renders a floor when one repo could not be searched"
assert_equals "$(signal_value "$OUT" 3)" "0" \
  "a signal with no gap of its own stays a plain measured zero"
assert_contains "$OUT" "no such directory" \
  "names the repo path it could not search"

printf '\nALL THREE - a read that fails PART WAY still marks its signal\n'
# Three reads used to fail without leaving any trace, because the failure
# happened before the file the collector looks for was ever created.

# (a) a repo directory that exists but cannot be entered
BLOCKED="$WORK/blocked-repo"
mkdir -p "$BLOCKED"
chmod 000 "$BLOCKED"
OUT=$(run_sut "$REPO:$BLOCKED" ok)
chmod 755 "$BLOCKED"
assert_equals "$(signal_value "$OUT" 1)" ">=0" \
  "a repo that cannot be entered makes signal 1 a floor, not a clean count"
assert_contains "$OUT" "could not enter directory" \
  "names the repo it could not enter"

# (b) a live worker session whose branch cannot be resolved. agent-deck says it
# is running, so it holds a slot whether or not we can classify it.
NOTREPO="$WORK/repos/demo/.worktrees/not-a-repo"
mkdir -p "$NOTREPO"
cat >"$FIX/sessions.json" <<JSON
[{"id":"s1","title":"worker","status":"running","path":"$NOTREPO"}]
JSON
cat >"$FIX/bd-ready.json" <<'JSON'
[{"id":"a"},{"id":"b"},{"id":"c"},{"id":"d"},{"id":"e"}]
JSON
OUT=$(run_sut "$REPO" ok)
assert_contains "$OUT" "active 1 of cap 3" \
  "an unclassifiable live session still counts against the cap"
assert_equals "$(signal_value "$OUT" 2)" ">=2" \
  "signal 2 is a floor when a session could not be classified - counting it\
 active under-estimates free capacity, so the true number can only be higher"
assert_not_contains "$OUT" "Dispatch 3 now" \
  "does not urge dispatch past the cap on sessions it could not classify"

# (c) the ack list failing INFLATES signal 1 rather than zeroing it, so it needs
# words rather than a >= or ? marker.
cat >"$FIX/sessions.json" <<'JSON'
[]
JSON
cat >"$STUBS/bd" <<'STUB'
#!/usr/bin/env bash
sub=$1
shift
case "$sub" in
list)
  case "$*" in
  *--label*) echo "unknown flag --label" >&2; exit 1 ;;
  *) cat "$FIXTURE_DIR/bd-list.json" ;;
  esac
  ;;
ready) cat "$FIXTURE_DIR/bd-ready.json" ;;
show) echo '[]' ;;
*) echo "[]" ;;
esac
STUB
chmod +x "$STUBS/bd"
OUT=$(run_sut "$REPO" ok)
assert_contains "$OUT" "may reappear below" \
  "says dismissed hits may reappear when the ack list cannot be read"

# ===========================================================================
# Tunable validation: every numeric setting is validated before any signal work
# ===========================================================================
#
# THE SEVEN SETTINGS AND THEIR FAILURE DIRECTIONS UNDER A MALFORMED VALUE
#
# LOAD_MAX is DESTRUCTIVE (analogous to NO_PR_MIN_AGE_DAYS in reclaim-worktrees):
#   awk's (l>=lt) does string comparison when lt="abc". Since digits < letters
#   in ASCII, load_high is always 0 -- the load guard is silently disabled, and
#   dispatch proceeds under any load. A setting that exists to cap machine
#   utilisation becomes the opposite of a cap.
#
# CAP fails safe:
#   bash arithmetic treats a non-numeric as variable lookup; if unset, 0.
#   FREE = 0 - ACTIVE = negative, clamped to 0. No dispatch urged.
#
# SWAP_VETO_MB and MEM_FREE_MIN_PCT fail safe:
#   awk's (s<st) and (m<mt) do string comparison when the threshold is
#   non-numeric. Since digits < letters in ASCII, the condition always fires,
#   vetoing dispatch -- the wrong answer, but the safe direction.
#
# PR_LIMIT fails safe:
#   gh pr list --limit abc errors, the repo's PR list is unreadable, and
#   signal 1 records a coverage gap (floor, not a clean zero).
#
# PR_DAYS fails safe:
#   days_ago falls back to epoch, so signal 1 searches all merged PRs rather
#   than just the recent window -- more coverage, not less.
#
# SAMPLE_SECONDS fails safe:
#   sleep abc fails immediately. The swapout delta is measured over ~0 seconds
#   (garbage), but the dispatch decision does not use the delta -- only the
#   informational "READINGS DISAGREE" note does.

printf '\nTunable validation\n'

# Restore JSON fixtures to a known state. The stubs (bd, gh, agent-deck) are NOT
# restored here because every test below exits at validation, before the SUT calls
# any external tool. Only the JSON fixtures matter -- run_sut validates them.
cat >"$FIX/gh-merged.json" <<'JSON'
[]
JSON
cat >"$FIX/bd-ready.json" <<'JSON'
[{"id":"a"},{"id":"b"},{"id":"c"},{"id":"d"},{"id":"e"}]
JSON
cat >"$FIX/sessions.json" <<'JSON'
[]
JSON

# ---------------------------------------------------------------------------
# THE CONTROL: a non-numeric LOAD_MAX disables the load guard
# ---------------------------------------------------------------------------
#
# This is the destructive defect (analogous to jbrooksbartlett-lngd). A machine
# at load 14.2 -- well above the default threshold of 9 -- with free capacity
# and ready work. At LOAD_MAX=9, the load veto fires and signal 2 is 0 (tested
# above in "the load threshold vetoes above 9"). With LOAD_MAX=abc:
#
#   awk: (l>=lt) where l="14.2", lt="abc"
#   string comparison: '1' (ASCII 49) < 'a' (ASCII 97) -> FALSE
#   load_high = 0, no veto
#   signal 2 fires, dispatch urged under heavy load
#
# The resource guard becomes the opposite of a guard. This test must go RED on
# the unfixed code and GREEN after validation is added. If it passes on both,
# it is not testing the defect.

printf '\nCONTROL: non-numeric LOAD_MAX disables the load guard\n'

OUT=$(CONDUCTOR_SIGNALS_LOAD_MAX=abc run_sut "$REPO" highload 2>&1)
rc=$?
assert_equals "$rc" "2" "a non-numeric LOAD_MAX is refused with exit 2"
assert_contains "$OUT" "CONDUCTOR_SIGNALS_LOAD_MAX" "...naming the variable"
assert_not_contains "$OUT" "CONDUCTOR SIGNALS" "...before any signal is computed"
assert_not_contains "$OUT" "integer expression expected" \
  "...cleanly, with no raw shell error leaking into the report"

# ---------------------------------------------------------------------------
# Validation: all seven tunables
# ---------------------------------------------------------------------------

assert_tunable_refused() { # <env-var=value> <message>
  OUT=$(export "$1"; run_sut "$REPO" ok 2>&1)
  rc=$?
  assert_equals "$rc" "2" "$2"
  assert_not_contains "$OUT" "CONDUCTOR SIGNALS" "...before any signal is computed"
}

printf '\nCAP validation\n'

assert_tunable_refused CONDUCTOR_SIGNALS_CAP=abc "a non-numeric CAP is refused with exit 2"
assert_contains "$OUT" "CONDUCTOR_SIGNALS_CAP" "...naming the variable"
assert_tunable_refused CONDUCTOR_SIGNALS_CAP=0 "CAP=0 is refused"
assert_tunable_refused CONDUCTOR_SIGNALS_CAP=-5 "CAP=-5 is refused"
assert_tunable_refused CONDUCTOR_SIGNALS_CAP=9999 "CAP with too many digits is refused"

printf '\nSWAP_VETO_MB validation\n'

assert_tunable_refused CONDUCTOR_SIGNALS_SWAP_VETO_MB=abc "a non-numeric SWAP_VETO_MB is refused with exit 2"
assert_contains "$OUT" "CONDUCTOR_SIGNALS_SWAP_VETO_MB" "...naming the variable"
assert_tunable_refused CONDUCTOR_SIGNALS_SWAP_VETO_MB=0 "SWAP_VETO_MB=0 is refused"
assert_tunable_refused CONDUCTOR_SIGNALS_SWAP_VETO_MB=9999999 "SWAP_VETO_MB with too many digits is refused"

printf '\nMEM_FREE_MIN_PCT validation\n'

assert_tunable_refused CONDUCTOR_SIGNALS_MEM_FREE_MIN_PCT=abc "a non-numeric MEM_FREE_MIN_PCT is refused with exit 2"
assert_contains "$OUT" "CONDUCTOR_SIGNALS_MEM_FREE_MIN_PCT" "...naming the variable"
assert_tunable_refused CONDUCTOR_SIGNALS_MEM_FREE_MIN_PCT=0 "MEM_FREE_MIN_PCT=0 is refused"
assert_tunable_refused CONDUCTOR_SIGNALS_MEM_FREE_MIN_PCT=150 "MEM_FREE_MIN_PCT=150 is refused (percentage > 100)"
assert_tunable_refused CONDUCTOR_SIGNALS_MEM_FREE_MIN_PCT=9999 "MEM_FREE_MIN_PCT with too many digits is refused"

printf '\nLOAD_MAX validation\n'

assert_tunable_refused CONDUCTOR_SIGNALS_LOAD_MAX=abc "a non-numeric LOAD_MAX is refused with exit 2"
assert_contains "$OUT" "CONDUCTOR_SIGNALS_LOAD_MAX" "...naming the variable"
assert_tunable_refused CONDUCTOR_SIGNALS_LOAD_MAX=0 "LOAD_MAX=0 is refused"
assert_tunable_refused CONDUCTOR_SIGNALS_LOAD_MAX=-5 "LOAD_MAX=-5 is refused"
assert_tunable_refused CONDUCTOR_SIGNALS_LOAD_MAX=9999 "LOAD_MAX with too many digits is refused"

printf '\nPR_LIMIT validation\n'

assert_tunable_refused CONDUCTOR_SIGNALS_PR_LIMIT=abc "a non-numeric PR_LIMIT is refused with exit 2"
assert_contains "$OUT" "CONDUCTOR_SIGNALS_PR_LIMIT" "...naming the variable"
assert_tunable_refused CONDUCTOR_SIGNALS_PR_LIMIT=0 "PR_LIMIT=0 is refused"
assert_tunable_refused CONDUCTOR_SIGNALS_PR_LIMIT=9999 "PR_LIMIT with too many digits is refused"

printf '\nPR_DAYS validation\n'

assert_tunable_refused CONDUCTOR_SIGNALS_PR_DAYS=abc "a non-numeric PR_DAYS is refused with exit 2"
assert_contains "$OUT" "CONDUCTOR_SIGNALS_PR_DAYS" "...naming the variable"
assert_tunable_refused CONDUCTOR_SIGNALS_PR_DAYS=0 "PR_DAYS=0 is refused"
assert_tunable_refused CONDUCTOR_SIGNALS_PR_DAYS=9999 "PR_DAYS with too many digits is refused"

printf '\nSAMPLE_SECONDS validation\n'

assert_tunable_refused CONDUCTOR_SIGNALS_SAMPLE_SECONDS=abc "a non-numeric SAMPLE_SECONDS is refused with exit 2"
assert_contains "$OUT" "CONDUCTOR_SIGNALS_SAMPLE_SECONDS" "...naming the variable"
assert_tunable_refused CONDUCTOR_SIGNALS_SAMPLE_SECONDS=0 "SAMPLE_SECONDS=0 is refused"
assert_tunable_refused CONDUCTOR_SIGNALS_SAMPLE_SECONDS=9999 "SAMPLE_SECONDS with too many digits is refused"

# ---------------------------------------------------------------------------

printf '\n%s passed, %s failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
