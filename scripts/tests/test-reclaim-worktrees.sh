#!/usr/bin/env bash
# Tests for scripts/reclaim-worktrees.sh
#
# Every case answers one of the two questions a deletion job has to answer:
#   - a worktree that SHOULD be reclaimed is reclaimed
#   - a worktree that SHOULD be protected is protected, and the report says why
#
# The repositories are REAL git repositories with REAL worktrees, so the classification runs
# against real `git worktree list --porcelain`, real `git status`, real `git ls-files` and a
# real `git worktree remove` - not a stub of any of them. Only the three external readers are
# stubbed on PATH: agent-deck (the session registry), gh (pull request state) and ps (whether a
# lock holder is alive). That split is deliberate: the two measured traps both live in how git's
# own output is interpreted, so stubbing git would test nothing.
#
# Run: bash scripts/tests/test-reclaim-worktrees.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUT="$SCRIPT_DIR/reclaim-worktrees.sh"

PASS=0
FAIL=0

# Bootstrap-RED sentinel, matching scripts/tests/test-conductor-signals.sh. Without it a harness
# that recorded zero assertions would print "0 passed, 0 failed" and exit 0 - green. This repo
# has no CI (jbrooksbartlett-sqmi), so this suite is the only gate and it has to prove it can
# report a failure at all.
#   EXPECT_BOOTSTRAP_RED=1 bash scripts/tests/test-reclaim-worktrees.sh
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
  case "$1" in
  *"$2"*) pass "$3" ;;
  *) fail "$3" "expected to find: $2" ;;
  esac
}

assert_not_contains() {
  case "$1" in
  *"$2"*) fail "$3" "expected NOT to find, but did: $2" ;;
  *) pass "$3" ;;
  esac
}

assert_exists() {
  if [ -e "$1" ]; then pass "$2"; else fail "$2" "expected to exist: $1"; fi
}

assert_absent() {
  if [ -e "$1" ]; then fail "$2" "expected to be GONE, but it is still there: $1"; else pass "$2"; fi
}

assert_eq() {
  if [ "$1" = "$2" ]; then pass "$3"; else fail "$3" "expected [$2], got [$1]"; fi
}

if [ "$BOOTSTRAP_RED" = "1" ]; then
  fail "bootstrap-RED sentinel: deliberate FAIL (verifies the harness reports failures)"
else
  pass "harness sanity"
fi

# `pwd -P` at creation, because mktemp hands back /var/folders/... which is a symlink to
# /private/var/folders/... The script resolves both sides of every path comparison, so a suite
# that did not resolve its own fixtures would be testing the resolver rather than the guard.
WORK=$(cd "$(mktemp -d)" && pwd -P)
trap 'rm -rf "$WORK"' EXIT

FIX="$WORK/fixtures"
STUBS="$WORK/stubs"
mkdir -p "$FIX" "$STUBS"

# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

# agent-deck: `agent-deck list --json` serves sessions.json. If sessions.fail exists it fails,
# which is how the "registry unreadable" case is reached through the production code path
# rather than through a test-only flag.
cat >"$STUBS/agent-deck" <<'STUB'
#!/usr/bin/env bash
[ -f "$FIXTURE_DIR/sessions.fail" ] && exit 1
cat "$FIXTURE_DIR/sessions.json" 2>/dev/null || echo '[]'
STUB

# gh: `gh pr list` is always run with the repository as the working directory, so the stub keys
# on that basename. A missing fixture means "no pull requests"; a .fail marker means gh could
# not be read at all, which must NEVER be confused with "no pull requests".
cat >"$STUBS/gh" <<'STUB'
#!/usr/bin/env bash
repo=$(basename "$PWD")
[ -f "$FIXTURE_DIR/gh-$repo.fail" ] && exit 1
head=""
while [ $# -gt 0 ]; do
  case "$1" in --head) head=${2:-}; shift ;; esac
  shift
done
# Filters on --head, like the real thing. A stub that ignored it would hand every branch every
# pull request in the repository, and a per-branch lookup would test nothing.
if [ -f "$FIXTURE_DIR/gh-$repo.json" ]; then
  jq -c --arg h "$head" '[.[] | select(.headRefName == $h)]' "$FIXTURE_DIR/gh-$repo.json"
else
  echo '[]'
fi
STUB

# ps: answers for the pids named in live-pids and nothing else, so "the lock holder is gone" is
# a decision the test controls rather than a coincidence of the machine's process table.
cat >"$STUBS/ps" <<'STUB'
#!/usr/bin/env bash
pid=""
want_comm=0
while [ $# -gt 0 ]; do
  case "$1" in
  -p)
    pid=${2:-}
    shift
    ;;
  -o)
    case "${2:-}" in comm=*) want_comm=1 ;; esac
    shift
    ;;
  esac
  shift
done
grep -qx "$pid" "$FIXTURE_DIR/live-pids" 2>/dev/null || exit 1
# The command name the holder check reads. Defaults to uv; a test can make it something else to
# prove a non-uv holder cannot excuse a uv failure.
if [ "$want_comm" = 1 ]; then
  if [ -f "$FIXTURE_DIR/ps-comm" ]; then cat "$FIXTURE_DIR/ps-comm"; else echo uv; fi
fi
exit 0
STUB

# The cache tools record that they were called, with their arguments. `bazel` is stubbed too,
# precisely so the suite can assert it is NEVER invoked - the script reports the bazel cache
# rather than clearing it, and a stub that records calls is the only way to prove that.
# uv is stubbed richly, because the lock discrimination has three distinct outcomes to drive.
cat >"$STUBS/uv" <<'STUB'
#!/usr/bin/env bash
if [ "$1" = cache ] && [ "$2" = dir ]; then printf '%s\n' "$FIXTURE_DIR/uvcache"; exit 0; fi
if [ -f "$FIXTURE_DIR/uv-lockfail" ]; then
  # VERBATIM uv 0.11.19 output, including the fact that it abbreviates the lock path to a RELATIVE
  # form. An earlier version of this stub invented an absolute path, the script was tightened to
  # require it, and the regression shipped green because only the stub ever said that.
  echo "Cache is currently in-use, waiting for other uv processes to finish (use \`--force\` to override)" >&2
  echo "error: Timeout (30s) when waiting for lock on \`$FIXTURE_DIR/uvcache\` at \`.cache/uv/.lock\`, is another uv process running?" >&2
  exit 2
fi
if [ -f "$FIXTURE_DIR/uv-otherfail" ]; then
  echo "error: failed to remove directory: Input/output error" >&2
  exit 2
fi
if [ -f "$FIXTURE_DIR/uv-filelockfail" ]; then
  # A GENUINE unrelated failure whose text contains "lock" only as part of `filelock`, one of the
  # most common transitive Python dependencies. The uv cache on the real machine holds 7 of them.
  echo "error: failed to remove directory \`$FIXTURE_DIR/uvcache/archive-v0/x/filelock-3.13.1\`: Directory not empty (os error 66)" >&2
  exit 2
fi
echo "uv $*" >>"$FIXTURE_DIR/cache-calls"
STUB

# lsof is stubbed so "a live process holds the lock" is a fact the test states, not a coincidence
# of whatever happens to be running on the machine under test.
cat >"$STUBS/lsof" <<'STUB'
#!/usr/bin/env bash
[ -f "$FIXTURE_DIR/lsof-holder" ] && cat "$FIXTURE_DIR/lsof-holder"
exit 0
STUB
chmod +x "$STUBS/uv" "$STUBS/lsof"

for tool in npm yarn pip pip3 bazel; do
  cat >"$STUBS/$tool" <<STUB
#!/usr/bin/env bash
printf '$tool %s\n' "\$*" >>"\$FIXTURE_DIR/cache-calls"
STUB
done

# launchctl: stubbed so installing a schedule NEVER registers a real weekly job on the machine
# running the suite. `list` answers from a file the stub itself maintains, so the verification
# step in install_schedule is exercised for real - including its failure path, which is the one
# that matters. An install that writes a plist nobody loaded is a schedule that never fires.
cat >"$STUBS/launchctl" <<'STUB'
#!/usr/bin/env bash
verb=${1:-}
case "$verb" in
bootstrap | load)
  printf 'launchctl %s\n' "$*" >>"$FIXTURE_DIR/launchctl-calls"
  [ -f "$FIXTURE_DIR/launchctl.fail" ] && exit 1
  printf '%s\n' "${RECLAIM_LAUNCHD_LABEL:-}" >>"$FIXTURE_DIR/launchctl-registered"
  ;;
bootout | unload)
  printf 'launchctl %s\n' "$*" >>"$FIXTURE_DIR/launchctl-calls"
  if [ -f "$FIXTURE_DIR/launchctl-registered" ]; then
    grep -vxF "${RECLAIM_LAUNCHD_LABEL:-}" "$FIXTURE_DIR/launchctl-registered" \
      >"$FIXTURE_DIR/launchctl-registered.tmp" 2>/dev/null
    mv "$FIXTURE_DIR/launchctl-registered.tmp" "$FIXTURE_DIR/launchctl-registered"
  fi
  ;;
list)
  grep -qxF "${2:-}" "$FIXTURE_DIR/launchctl-registered" 2>/dev/null || exit 1
  ;;
esac
exit 0
STUB

chmod +x "$STUBS"/*
export PATH="$STUBS:$PATH"
export FIXTURE_DIR="$FIX"

: >"$FIX/live-pids"
echo '[]' >"$FIX/sessions.json"

# ---------------------------------------------------------------------------
# Fixture rig
# ---------------------------------------------------------------------------

ROOTS="$WORK/roots"

make_repo() { # <name>  -> $ROOTS/<name>, one commit on master
  # Two statements: `local a=$1 b="$a"` expands every argument before the builtin runs, so `$a`
  # is the unset global and `set -u` kills the suite. The same slip was in the script itself.
  local name=$1
  local repo="$ROOTS/$name"
  mkdir -p "$repo"
  # -b master, not whatever init.defaultBranch happens to be: a fixture whose default branch
  # name drifts would change which pull request fixtures match.
  git init -q -b master "$repo" 2>/dev/null
  git -C "$repo" config user.email t@t
  git -C "$repo" config user.name t
  git -C "$repo" config commit.gpgsign false
  printf 'node_modules/\n' >"$repo/.gitignore"
  echo base >"$repo/tracked.txt"
  git -C "$repo" add -A
  git -C "$repo" commit -qm init
  printf '%s' "$repo"
}

add_worktree() { # <repo> <dirname> <branch>
  local repo=$1 dir=$2 branch=$3
  git -C "$repo" worktree add -q "$repo/.worktrees/$dir" -b "$branch" >/dev/null 2>&1
  printf '%s' "$repo/.worktrees/$dir"
}

age_worktree() { # <worktree> <days>  -> make every activity signal look that old
  local wt=$1
  local days=$2
  local stamp admin
  # BSD (macOS) first, then GNU (Linux) - the same hedge iso_utc uses in the script itself.
  stamp=$(date -v-"${days}"d +%Y%m%d%H%M 2>/dev/null) || \
    stamp=$(date -d "$days days ago" +%Y%m%d%H%M 2>/dev/null)
  admin=$(git -C "$wt" rev-parse --absolute-git-dir 2>/dev/null)
  [ -n "$admin" ] && [ -e "$admin/logs/HEAD" ] && touch -t "$stamp" "$admin/logs/HEAD"
  # The directory LAST: touching anything inside it would bump its own mtime again.
  touch -t "$stamp" "$wt"
}

sessions_json() { # <path>...  -> a registry naming one session per path
  local first=1
  {
    printf '['
    for p in "$@"; do
      [ "$first" = 1 ] || printf ','
      first=0
      printf '{"id":"sess-%s","status":"running","path":"%s"}' "$(basename "$p")" "$p"
    done
    printf ']\n'
  } >"$FIX/sessions.json"
}

# Every run is pointed at the fixture roots and a fixture evidence directory, and gets its own
# lock, so no test can reach the real machine or collide with a real weekly run.
# RECLAIM_TOOL_DIRS fences the script's out-of-PATH tool search to the stub directory. Without it
# `resolve_tool` reaches /opt/homebrew/bin and runs the REAL tool: measured 2026-08-20, the suite
# purged a real 7.3 GB pip cache that way. A harness whose subject can step outside it is not a
# harness.
export RECLAIM_TOOL_DIRS="$STUBS"

run_sut() {
  RECLAIM_LOCK_DIR="$WORK/lock.$RANDOM" \
    "$SUT" --root "$ROOTS" --evidence-dir "$WORK/evidence" --no-caches "$@" 2>&1
}

reset_fixtures() {
  rm -rf "$ROOTS" "$WORK/evidence"
  mkdir -p "$ROOTS"
  rm -f "$FIX"/gh-*.json "$FIX"/gh-*.fail "$FIX/sessions.fail" "$FIX/cache-calls" \
    "$FIX/launchctl-calls" "$FIX/launchctl-registered" "$FIX/launchctl.fail" \
    "$FIX/uv-lockfail" "$FIX/uv-otherfail" "$FIX/uv-filelockfail" "$FIX/lsof-holder" \
    "$FIX/ps-comm"
  mkdir -p "$FIX/uvcache"
  : >"$FIX/uvcache/.lock"
  echo '[]' >"$FIX/sessions.json"
  # The suite's own pid is always "alive" to the ps stub. Without it the lock test defeats
  # itself: the script would ask `ps -p <suite pid>`, the stub would say gone, and the lock it
  # was supposed to respect would be cleared as stale.
  echo $$ >"$FIX/live-pids"
}

pr_fixture() { # <repo name> <branch> <state> [<branch> <state> ...]
  local name=$1
  shift
  {
    printf '['
    local first=1 n=1
    while [ $# -gt 0 ]; do
      [ "$first" = 1 ] || printf ','
      first=0
      printf '{"number":%d,"state":"%s","headRefName":"%s"}' "$n" "$2" "$1"
      n=$((n + 1))
      shift 2
    done
    printf ']\n'
  } >"$FIX/gh-$name.json"
}

# ===========================================================================
# TRAP 1 - the live-session guard. Measured 2026-08-19: a substring match gave
# 37 LIVE / 0 stale, a directional match gave 2 LIVE / 35 stale.
# ===========================================================================

printf '\nTRAP 1: the live-session check is directional, not a substring match\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" merged-one feature/merged-one)
pr_fixture alpha feature/merged-one MERGED
# THE MEASURED FAILURE, exactly: a live session sitting at the REPOSITORY ROOT, which is a
# prefix of every worktree path beneath it.
sessions_json "$repo"
out=$(run_sut)
assert_absent "$wt" "a session at the repository root does NOT protect the worktrees beneath it"
assert_contains "$out" "[removed]" "...and the merged worktree is reported as removed"

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" merged-one feature/merged-one)
pr_fixture alpha feature/merged-one MERGED
# An ancestor further up still - the shape of the real registry, which holds a session whose
# path is $HOME and therefore a prefix of every path on the machine.
sessions_json "$ROOTS"
out=$(run_sut)
assert_absent "$wt" "a session at an ancestor of the whole search root protects nothing"

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" live-one feature/live-one)
pr_fixture alpha feature/live-one MERGED
sessions_json "$wt"
out=$(run_sut)
assert_exists "$wt" "a session whose path IS the worktree protects it, merged PR or not"
assert_contains "$out" "kept-live" "...and the report says it was kept as live"

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" live-sub feature/live-sub)
mkdir -p "$wt/src"
pr_fixture alpha feature/live-sub MERGED
# The opposite-direction failure, which a pure exact match would cause and which nothing in the
# bead warns about: a session that has cd'd into a subdirectory of its own worktree.
sessions_json "$wt/src"
out=$(run_sut)
assert_exists "$wt" "a session BENEATH the worktree protects it (exact match alone would not)"

reset_fixtures
repo=$(make_repo alpha)
# `wt-foo` is a string prefix of `wt-foobar`, but it is not a parent directory of it. A prefix
# test without a path boundary would protect the wrong worktree.
wt_short=$(add_worktree "$repo" wt-foo feature/foo)
wt_long=$(add_worktree "$repo" wt-foobar feature/foobar)
pr_fixture alpha feature/foo MERGED feature/foobar MERGED
sessions_json "$wt_long"
out=$(run_sut)
assert_absent "$wt_short" "a worktree that is only a STRING prefix of a live path is not protected"
assert_exists "$wt_long" "...while the live one itself is"

printf '\nan unreadable session registry is a hard stop, never an empty set\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" merged-one feature/merged-one)
pr_fixture alpha feature/merged-one MERGED
: >"$FIX/sessions.fail"
out=$(run_sut)
rc=$?
assert_exists "$wt" "nothing is removed when the session registry cannot be read"
assert_eq "$rc" "2" "...and the run refuses with exit 2"
assert_contains "$out" "REFUSED" "...and says REFUSED rather than reporting a clean sweep"

# ===========================================================================
# TRAP 2 - rescuing uncommitted work must handle untracked DIRECTORIES
# ===========================================================================

printf '\nTRAP 2: an untracked DIRECTORY is rescued with its contents, not silently skipped\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" dirty-dir feature/dirty-dir)
pr_fixture alpha feature/dirty-dir MERGED
# The measured case: the worktree's ONLY uncommitted item is an untracked directory. A rescue
# loop using plain `cp` skips it, produces an empty patch and no files, and reports success.
mkdir -p "$wt/newdir/nested"
echo "the work that must not be lost" >"$wt/newdir/nested/deep.txt"
echo "shallow" >"$wt/newdir/shallow.txt"
out=$(run_sut)
assert_exists "$wt" "a dirty worktree is LEFT IN PLACE (bead acceptance, not the contract's remove)"
assert_contains "$out" "kept-uncommitted" "...and is reported as kept-uncommitted"
rescued=$(find "$WORK/evidence/rescued-worktree-files" -name deep.txt 2>/dev/null | head -1)
assert_eq "$(cat "$rescued" 2>/dev/null)" "the work that must not be lost" \
  "...and the file inside the untracked directory is rescued byte-for-byte"
assert_eq "$(find "$WORK/evidence/rescued-worktree-files" -name shallow.txt | wc -l | tr -d ' ')" "1" \
  "...and so is the file at the top of that directory"
readme=$(find "$WORK/evidence/rescued-worktree-files" -name README.md | head -1)
assert_contains "$(cat "$readme" 2>/dev/null)" "$wt" \
  "...and a README records the worktree it came from"
assert_contains "$(cat "$readme" 2>/dev/null)" "LEFT IN PLACE" \
  "...and states that the worktree was left alone"

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" dirty-tracked feature/dirty-tracked)
pr_fixture alpha feature/dirty-tracked MERGED
echo "a local edit" >>"$wt/tracked.txt"
out=$(run_sut)
assert_exists "$wt" "a worktree with a modified tracked file is left in place"
patch=$(find "$WORK/evidence/rescued-worktree-files" -name uncommitted.patch | head -1)
assert_contains "$(cat "$patch" 2>/dev/null)" "a local edit" \
  "...and the modification is in the rescued patch"

printf '\nthe rescue proves it copied something, so it cannot report a success it did not have\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" dirty-capped feature/dirty-capped)
pr_fixture alpha feature/dirty-capped MERGED
mkdir -p "$wt/newdir"
echo content >"$wt/newdir/file.txt"
# A 1-byte cap makes every untracked file unrescuable and leaves the patch empty, which is
# exactly the state trap 2 produced. The detector has to notice rather than claim success.
out=$(RECLAIM_RESCUE_MAX_BYTES=1 run_sut)
rc=$?
assert_contains "$out" "rescue-failed" "an empty rescue is reported as a failure, not a success"
assert_contains "$out" "RESCUED NOTHING" "...and says so in words"
assert_exists "$wt" "...and the worktree is still there, so nothing was lost"
assert_eq "$rc" "1" "...and the run exits 1 because it has a gap"

# ===========================================================================
# Pull request state decides removal - never a commit count
# ===========================================================================

printf '\npull request state, and the squash-merge trap that commit counts fall into\n'

reset_fixtures
repo=$(make_repo alpha)
wt_merged=$(add_worktree "$repo" pr-merged feature/pr-merged)
wt_closed=$(add_worktree "$repo" pr-closed feature/pr-closed)
wt_open=$(add_worktree "$repo" pr-open feature/pr-open)
wt_nopr=$(add_worktree "$repo" pr-none feature/pr-none)
# The squash-merge shape: this branch is genuinely AHEAD of master, so any commit-count test
# reads it as unmerged. Its pull request says otherwise, and the pull request is right.
echo extra >"$wt_merged/extra.txt"
git -C "$wt_merged" add -A
git -C "$wt_merged" commit -qm "work that was squash-merged"
pr_fixture alpha feature/pr-merged MERGED feature/pr-closed CLOSED feature/pr-open OPEN
out=$(run_sut)
assert_absent "$wt_merged" "a MERGED pull request means remove, even 1 commit ahead of master"
assert_absent "$wt_closed" "a CLOSED pull request means remove"
assert_exists "$wt_open" "an OPEN pull request means keep"
assert_contains "$out" "its pull request is still open" "...and the report gives that reason"
assert_exists "$wt_nopr" "a freshly-made branch with NO pull request is kept"
assert_contains "$out" "needs 14" "...and the report names the age it would have to reach"

# THE SAFETY ARGUMENT, asserted rather than asserted-about: the worktree above is gone, and its
# branch and its commit are still here. If this ever fails, the premise the whole job rests on
# is false and nothing else in this suite matters.
printf '\nremoving a worktree does not remove its branch or its commits\n'
if git -C "$repo" rev-parse --verify --quiet feature/pr-merged >/dev/null; then
  pass "the branch of the removed worktree still resolves"
else
  fail "the branch of the removed worktree still resolves" "feature/pr-merged is gone"
fi
assert_eq "$(git -C "$repo" log --oneline feature/pr-merged 2>/dev/null | grep -c 'squash-merged')" "1" \
  "...and its commit is still in the object store - the whole safety argument"

printf '\ngh being unreadable is not "no pull requests"\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" merged-one feature/merged-one)
: >"$FIX/gh-alpha.fail"
out=$(run_sut)
rc=$?
assert_exists "$wt" "a worktree is kept when gh cannot be read"
assert_contains "$out" "kept-undetermined" "...as undetermined"
assert_contains "$out" "NOT A CLEAN SWEEP" "...and the run declares itself not a clean sweep"
assert_eq "$rc" "1" "...and exits 1"

printf '\npull request state is asked per branch, so a neighbouring branch cannot answer for it\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" pr-none feature/pr-none)
# The repository is full of merged pull requests - none of them for THIS branch. The first
# version of this script asked per repository and would have had to scan a capped page; asking
# per branch cannot be confused by a neighbour.
pr_fixture alpha other/one MERGED other/two MERGED other/three CLOSED
out=$(run_sut)
assert_exists "$wt" "a branch with no pull request of its own is kept"
assert_contains "$out" "no pull request, but something touched it" \
  "...on its own account, not a neighbouring branch's"

printf '\ntwo pull requests on one branch: the open one wins, because it is the live work\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" reused feature/reused)
pr_fixture alpha feature/reused MERGED feature/reused OPEN
out=$(run_sut)
assert_exists "$wt" "a branch reused for a follow-up is kept while that follow-up is open"
assert_contains "$out" "its pull request is still open" "...and the open one is the reason given"

# ===========================================================================
# Locks: ps -p first, and never a blanket force
# ===========================================================================

printf '\nlocks: a lock whose process is gone is stale, one whose process is alive is not\n'

reset_fixtures
repo=$(make_repo alpha)
wt_dead=$(add_worktree "$repo" lock-dead feature/lock-dead)
wt_alive=$(add_worktree "$repo" lock-alive feature/lock-alive)
wt_nopid=$(add_worktree "$repo" lock-nopid feature/lock-nopid)
git -C "$repo" worktree lock --reason "held by agent-deck pid 9978" "$wt_dead"
git -C "$repo" worktree lock --reason "held by agent-deck pid 4242" "$wt_alive"
git -C "$repo" worktree lock --reason "keep this until 2026" "$wt_nopid"
# Appended, not written: reset_fixtures put the suite's own pid there and the lock test needs it.
# Note the third reason contains the bare integer 2026 and NO pid - a reason-parser that took
# any integer as a pid would ask `ps -p 2026`, be told it is gone, and break the lock on the
# strength of a year.
echo 4242 >>"$FIX/live-pids"
# Deliberately NO pull request for any of them: a dead lock is its own removal reason, so this
# also proves the two rules are independent.
out=$(run_sut)
assert_absent "$wt_dead" "a lock naming a pid that is gone is stale: unlocked and removed"
assert_contains "$out" "removed-after-unlock" "...and reported as removed-after-unlock"
assert_exists "$wt_alive" "a lock naming a live pid is not this job's to break"
assert_contains "$out" "locked by pid 4242, which is running" "...with the pid in the reason"
assert_exists "$wt_nopid" "a lock whose reason names no pid is kept, not forced"
assert_contains "$out" "names no pid" "...and the report says the holder could not be checked"

# ===========================================================================
# Safety properties and the report contract
# ===========================================================================

printf '\nsafety: the main worktree, --dry-run, and gitignored bulk\n'

reset_fixtures
repo=$(make_repo alpha)
pr_fixture alpha master MERGED
out=$(run_sut)
assert_exists "$repo/tracked.txt" "the repository's own working tree is never removed"
assert_contains "$out" "a repository main tree, never removable" \
  "...and is counted in the report, not silently dropped"

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" merged-one feature/merged-one)
pr_fixture alpha feature/merged-one MERGED
out=$(run_sut --dry-run)
assert_exists "$wt" "--dry-run removes nothing"
assert_contains "$out" "DRY RUN" "...and says so at the top of the report"
assert_contains "$out" "would-remove" "...and reports what it would have done"
assert_not_contains "$out" "[removed]" "...and never claims to have removed anything"

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" dirty-one feature/dirty-one)
pr_fixture alpha feature/dirty-one MERGED
mkdir -p "$wt/newdir"
echo content >"$wt/newdir/file.txt"
out=$(run_sut --dry-run)
# The first live run printed "nothing was changed" and created four rescue directories.
assert_absent "$WORK/evidence/rescued-worktree-files" "--dry-run writes NO rescue copies at all"
assert_contains "$out" "would-rescue" "...and reports that it would have rescued the work"
assert_contains "$out" "left in place" "...and that the worktree would stay"

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" merged-one feature/merged-one)
pr_fixture alpha feature/merged-one MERGED
# The gigabytes are all gitignored dependency trees. Measured on git 2.54.0: these do NOT block
# `git worktree remove`, which is why the job never needs --force. If that ever changes, this
# test fails and the whole reclaim silently drops to nothing.
mkdir -p "$wt/node_modules/pkg"
echo junk >"$wt/node_modules/pkg/index.js"
out=$(run_sut)
assert_absent "$wt" "a worktree holding only gitignored bulk is removed WITHOUT --force"

printf '\ndiscovery sweeps every repository under the root, not the ones it thought of\n'

reset_fixtures
# The measured failure this job exists to prevent: a manual sweep cleaned two repositories,
# reported the job done, and never examined a third holding 45 GB.
repo_a=$(make_repo alpha)
repo_b=$(make_repo beta)
repo_c=$(make_repo gamma)
wt_a=$(add_worktree "$repo_a" m feature/m-a)
wt_b=$(add_worktree "$repo_b" m feature/m-b)
wt_c=$(add_worktree "$repo_c" m feature/m-c)
pr_fixture alpha feature/m-a MERGED
pr_fixture beta feature/m-b MERGED
pr_fixture gamma feature/m-c MERGED
out=$(run_sut)
assert_absent "$wt_a" "the first repository is swept"
assert_absent "$wt_b" "the second repository is swept"
assert_absent "$wt_c" "the third repository is swept too - discovery is not scoped by repository"
swept=$(printf '%s\n' "$out" | awk '/^repositories swept/{print $NF; exit}')
assert_eq "$swept" "3" "...and the report names how many it swept"

printf '\nthe report names every worktree it kept, so nothing is skipped in silence\n'

reset_fixtures
repo=$(make_repo alpha)
wt_open=$(add_worktree "$repo" pr-open feature/pr-open)
wt_live=$(add_worktree "$repo" live-one feature/live-one)
wt_dirty=$(add_worktree "$repo" dirty-one feature/dirty-one)
echo edit >>"$wt_dirty/tracked.txt"
pr_fixture alpha feature/pr-open OPEN feature/live-one MERGED feature/dirty-one MERGED
sessions_json "$wt_live"
out=$(run_sut)
kept_lines=$(printf '%s\n' "$out" | grep -c '^  \[kept-')
assert_eq "$kept_lines" "3" "each of the three kept worktrees appears in the KEPT, AND WHY section"
assert_contains "$out" "KEPT, AND WHY" "...under a heading that says that is what it is"

printf '\nexit codes distinguish a clean sweep from one with gaps\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" merged-one feature/merged-one)
pr_fixture alpha feature/merged-one MERGED
run_sut >/dev/null 2>&1
assert_eq "$?" "0" "a sweep with nothing unexamined exits 0"

reset_fixtures
repo=$(make_repo alpha)
add_worktree "$repo" merged-one feature/merged-one >/dev/null
pr_fixture alpha feature/merged-one MERGED
RECLAIM_LOCK_DIR="$WORK/lock.rc" "$SUT" --root "$ROOTS" --root "$WORK/no-such-root" \
  --evidence-dir "$WORK/evidence" --no-caches >/dev/null 2>&1
assert_eq "$?" "1" "a sweep that could not read a search root exits 1"

printf '\na detached worktree has no branch to ask about, and says so\n'

reset_fixtures
repo=$(make_repo alpha)
git -C "$repo" worktree add -q --detach "$repo/.worktrees/detached" >/dev/null 2>&1
out=$(run_sut)
assert_exists "$repo/.worktrees/detached" "a detached worktree is kept"
assert_contains "$out" "detached HEAD" "...and the report names detachment as the reason"

printf '\na cache tool that cannot be found is a GAP, not a quiet "not present"\n'

reset_fixtures
repo=$(make_repo alpha)
# Hide every cache tool by fencing the out-of-PATH search at an empty directory AND removing the
# stubs from PATH. Measured 2026-08-20 on the first real launchd run: npm, yarn and pip all
# reported "not present" because launchd's hardcoded plist PATH does not reach nvm, so the job
# cleared 0 of 11 GB and still exited 0. "not present" read as "nothing to do".
mkdir -p "$WORK/empty-tooldir" "$WORK/minimal-bin"
# git and jq must stay reachable or the run dies in preflight at exit 2 and proves nothing about
# caches. Link just those two, so no cache tool is on PATH or in the fenced fallback.
# bash too: the shebang is `#!/usr/bin/env bash`, so a PATH without Homebrew resolves to macOS's
# /bin/bash 3.2 and the version guard correctly refuses at exit 2 before reaching any cache code.
for need in git jq bash; do ln -sf "$(command -v $need)" "$WORK/minimal-bin/$need" 2>/dev/null; done
# The session registry comes from a file rather than the fenced-out agent-deck stub: an unreadable
# registry is a deliberate hard refusal at exit 2, which would mask the cache behaviour under test.
echo '[]' >"$WORK/no-sessions.json"
out=$(RECLAIM_LOCK_DIR="$WORK/lock.notools" RECLAIM_TOOL_DIRS="$WORK/empty-tooldir" \
  PATH="$WORK/minimal-bin:/usr/bin:/bin" "$SUT" --root "$ROOTS" \
  --sessions-from "$WORK/no-sessions.json" --evidence-dir "$WORK/evidence" 2>&1)
rc=$?
assert_contains "$out" "NOT FOUND" "a tool that cannot be located is reported as NOT FOUND"
assert_contains "$out" "was NOT cleared" "...saying explicitly that the cache was not cleared"
# Specifically this gap, not merely any gap. /usr/bin/pip3 exists on macOS, so the pip branch
# raises "its own clean command failed" and a generic NOT-A-CLEAN-SWEEP assertion would pass even
# with the not-found gap deleted. Mutation testing caught exactly that.
assert_contains "$out" "its tool could not be found" \
  "...and the gap list names the missing tool as the reason"
assert_contains "$out" "NOT A CLEAN SWEEP" "...and the run declares itself not a clean sweep"
assert_eq "$rc" "1" "...and exits 1 rather than 0"

printf '\na tool found outside PATH can still reach its own siblings\n'

reset_fixtures
repo=$(make_repo alpha)
# nvm's npm is a shell script that shells out to its SIBLING node. Measured 2026-08-20 under a
# faithful launchd environment: npm was located correctly and then died with
# "env: node: No such file or directory". So a tool reached through the fallback list must get its
# own directory on PATH for the call. This fixture reproduces that shape exactly: a tool in a
# directory that is NOT on PATH, which needs a sibling that is also not on PATH.
mkdir -p "$WORK/siblingdir"
printf '#!/bin/sh\nexec node-sibling "$@"\n' >"$WORK/siblingdir/npm"
# echo, not printf: a %s in the stub body gets consumed by the printf that WRITES the stub.
printf '#!/bin/sh\necho "npm $*" >>"$FIXTURE_DIR/cache-calls"\n' >"$WORK/siblingdir/node-sibling"
chmod +x "$WORK/siblingdir/npm" "$WORK/siblingdir/node-sibling"
# PATH is restricted for this call, not just the stub removed. With the stub gone but the suite's
# inherited PATH intact, `command -v npm` found the operator's REAL nvm npm and ran it - the same
# escape-the-harness problem as the pip3 one, arriving by PATH instead of the fallback list.
mkdir -p "$WORK/minimal-bin"
for need in git jq bash; do ln -sf "$(command -v $need)" "$WORK/minimal-bin/$need" 2>/dev/null; done
echo '[]' >"$WORK/no-sessions.json"
out=$(RECLAIM_LOCK_DIR="$WORK/lock.sibling" RECLAIM_TOOL_DIRS="$WORK/siblingdir" \
  PATH="$WORK/minimal-bin:/usr/bin:/bin" \
  "$SUT" --root "$ROOTS" --sessions-from "$WORK/no-sessions.json" \
  --evidence-dir "$WORK/evidence" 2>&1)
assert_contains "$(cat "$FIX/cache-calls" 2>/dev/null)" "npm cache clean --force" \
  "a tool reached via the fallback list can still find its sibling"
assert_not_contains "$out" "npm    FAILED" "...so it does not fail with a missing-sibling error"


printf '\npip resolves through pip3, which is the only one that exists on some machines\n'

reset_fixtures
repo=$(make_repo alpha)
rm -f "$STUBS/pip"
out=$(RECLAIM_LOCK_DIR="$WORK/lock.pip3" "$SUT" --root "$ROOTS" \
  --evidence-dir "$WORK/evidence" 2>&1)
assert_contains "$(cat "$FIX/cache-calls" 2>/dev/null)" "pip3 cache purge" \
  "with no pip on the machine, pip3 is used instead"
assert_not_contains "$out" "NOT FOUND" "...and the pip cache is not reported as missing"
cp "$STUBS/pip3" "$STUBS/pip"
chmod +x "$STUBS/pip"

printf '\nthe verdict naming convention: every removal verdict contains "remove", nothing else does\n'

# THIS TEST EXISTS TO STOP A COUPLING COMING BACK. The report decides what belongs in "KEPT, AND
# WHY" by testing the verdict against *remove*, which replaced a hardcoded list of the four removal
# verdicts. That list had to be kept in step with the fourteen verdicts the script emits, and
# forgetting it would have printed a removal under KEPT - in the one section whose whole purpose is
# that nothing is skipped in silence. The convention is only safe while it holds, so assert it.
emitted=$(grep -oE '^[[:space:]]*row [a-z-]+' "$SUT" | awk '{print $2}' | sort -u)
removal_verdicts=$(printf '%s\n' "$emitted" | grep 'remove' | sort)
expected=$(printf '%s\n' removed removed-after-unlock would-remove would-remove-after-unlock | sort)
assert_eq "$removal_verdicts" "$expected" \
  "exactly the four removal verdicts contain \"remove\", and no other verdict does"
if [ -z "$emitted" ]; then
  fail "the verdict scan found something to check" "no 'row <verdict>' calls matched in $SUT"
else
  pass "the verdict scan actually found verdicts to check"
fi

# ALL FOUR removal verdicts have to be exercised here, not just the easy one. Mutation-testing this
# suite caught the gap: reverting the filter to a hardcoded `removed | would-remove` list - dropping
# both after-unlock verdicts - left the suite green, because nothing produced one and checked it.
# The fixture therefore carries a merged worktree AND a dead-locked one, and runs twice.
build_all_four() { # a repo whose sweep yields a removal, an unlock-removal, and a keeper
  reset_fixtures
  repo=$(make_repo alpha)
  wt_gone=$(add_worktree "$repo" merged-one feature/merged-one)
  wt_lock=$(add_worktree "$repo" lock-dead feature/lock-dead)
  wt_kept=$(add_worktree "$repo" pr-open feature/pr-open)
  git -C "$repo" worktree lock --reason "held by agent-deck pid 9978" "$wt_lock"
  pr_fixture alpha feature/merged-one MERGED feature/pr-open OPEN
}

build_all_four
out=$(run_sut)
kept_section=$(printf '%s\n' "$out" | sed -n '/KEPT, AND WHY/,/^$/p')
assert_contains "$out" "[removed]" "a merged worktree reports under REMOVED"
assert_contains "$out" "[removed-after-unlock]" "...and so does a dead-locked one"
assert_not_contains "$kept_section" "remove" "and NEITHER removal verdict leaks into KEPT"
assert_contains "$kept_section" "kept-pr-open" "...while the genuinely kept worktree is listed there"

build_all_four
out=$(run_sut --dry-run)
kept_section=$(printf '%s\n' "$out" | sed -n '/KEPT, AND WHY/,/^$/p')
assert_contains "$out" "[would-remove]" "the dry run reports would-remove"
assert_contains "$out" "[would-remove-after-unlock]" "...and would-remove-after-unlock"
assert_not_contains "$kept_section" "remove" "and neither of THOSE leaks into KEPT either"

printf '\nthe REMOVED heading tests the verdict field, not the whole line\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" lock-live feature/lock-live)
# A lock REASON is free text and lands in the detail field. So does git's own refusal message,
# which contains the word "remove" verbatim. A whole-line grep for "remove" would therefore print
# the REMOVED heading on a run that removed nothing - a section header with nothing under it, which
# is precisely the "reports something it did not do" failure the report exists to avoid.
# The reason must be one that reaches the DETAIL field, which is the no-pid case: a live-pid lock
# reports only "locked by pid N, which is running" and never echoes the reason, so a reason chosen
# there would prove nothing.
git -C "$repo" worktree lock --reason "do not remove this by hand" "$wt"
out=$(run_sut)
assert_exists "$wt" "the locked worktree is kept"
assert_contains "$out" "do not remove this by hand" "and its reason reaches the report verbatim"
assert_not_contains "$out" "REMOVED (branches and commits" \
  "...yet the REMOVED heading is absent, because the word was in a detail, not a verdict"

printf '\nthe disk line resolves a few hundred MB, which is the usual size of a reclaim\n'

reset_fixtures
repo=$(make_repo alpha)
add_worktree "$repo" merged-one feature/merged-one >/dev/null
pr_fixture alpha feature/merged-one MERGED
out=$(run_sut)
# The first live run reclaimed 212 MB and reported "111 GB -> 111 GB", because df -g rounds to
# whole gigabytes. A true statement that hides the entire result is not a report.
assert_contains "$out" "volume delta" "the disk line carries the delta, not just two totals"
# Whole gigabytes were the defect, not the gigabyte unit. Assert the figures carry sub-GB
# resolution: a decimal GB, or an MB/KB figure on a smaller volume.
if printf '%s\n' "$out" | grep -qE 'disk free \.+ ([0-9]+\.[0-9]+ GB|[0-9]+ (MB|KB)) ->'; then
  pass "...and the free figures resolve below a whole gigabyte"
else
  fail "...and the free figures resolve below a whole gigabyte" \
    "$(printf '%s\n' "$out" | grep 'disk free')"
fi

printf '\nthe durable report is written, and matches what was printed\n'

reset_fixtures
repo=$(make_repo alpha)
add_worktree "$repo" merged-one feature/merged-one >/dev/null
pr_fixture alpha feature/merged-one MERGED
out=$(run_sut)
saved=$(find "$WORK/evidence/reclamation" -name 'reclaim-*.md' | head -1)
assert_exists "$saved" "a timestamped report is written under the evidence directory"
assert_contains "$out" "$(head -1 "$saved" 2>/dev/null)" "...and its first line matches the printed report"

printf '\ncaches use tool-native commands, and bazel is reported rather than guessed at\n'

reset_fixtures
repo=$(make_repo alpha)
out=$(RECLAIM_LOCK_DIR="$WORK/lock.cache" "$SUT" --root "$ROOTS" \
  --evidence-dir "$WORK/evidence" 2>&1)
calls=$(cat "$FIX/cache-calls" 2>/dev/null)
assert_contains "$calls" "npm cache clean --force" "npm is cleaned with its own command"
assert_contains "$calls" "yarn cache clean" "yarn is cleaned with its own command"
# pip3 FIRST, because some machines (this one) have pip3 and no pip at all. The suite stubs both,
# so pip3 is what gets called; the pip fallback has its own case below.
assert_contains "$calls" "pip3 cache purge" "the pip cache is purged, via pip3"
assert_contains "$calls" "uv cache prune" "uv is PRUNED, not cleaned"
assert_not_contains "$calls" "uv cache clean" "...because clean empties a 3.7 GB cache the next resolve refills"
# The contract says "tool-native commands where they exist". For bazel one does not: `bazel
# clean` needs a workspace, so it cannot reach an output base whose workspace has been deleted,
# which is the stale case worth reclaiming. The job must therefore report bazel and touch it.
assert_not_contains "$calls" "bazel" "bazel is NEVER invoked - it is reported, not cleared"
assert_contains "$out" "bazel" "...but it does appear in the cache report, so it is not omitted"

reset_fixtures
repo=$(make_repo alpha)
out=$(RECLAIM_LOCK_DIR="$WORK/lock.dryc" "$SUT" --root "$ROOTS" \
  --evidence-dir "$WORK/evidence" --dry-run 2>&1)
assert_absent "$FIX/cache-calls" "--dry-run touches no cache at all"
assert_contains "$out" "not attempted" "...and the report says the caches were not attempted"

printf '\na second run while one is in progress does nothing rather than racing it\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" merged-one feature/merged-one)
pr_fixture alpha feature/merged-one MERGED
mkdir -p "$WORK/held.lock"
echo $$ >"$WORK/held.lock/pid"
out=$(RECLAIM_LOCK_DIR="$WORK/held.lock" "$SUT" --root "$ROOTS" \
  --evidence-dir "$WORK/evidence" --no-caches 2>&1)
rc=$?
assert_exists "$wt" "a run that cannot take the lock removes nothing"
assert_eq "$rc" "2" "...and exits 2"
assert_contains "$out" "another reclamation is running" "...saying which pid holds it"

printf '\nthe launchd schedule: a valid weekly plist, and an install that verifies itself\n'

reset_fixtures
LAUNCH_DIR="$WORK/launchagents"
plist="$LAUNCH_DIR/com.test.reclaim.plist"
install_env=(RECLAIM_LAUNCHD_DIR="$LAUNCH_DIR" RECLAIM_LAUNCHD_LABEL=com.test.reclaim)

out=$(env "${install_env[@]}" "$SUT" --evidence-dir "$WORK/evidence" --install-schedule 2>&1)
rc=$?
if [ -f "$plist" ]; then
  body=$(cat "$plist")
  assert_contains "$body" "$SUT" "the plist names the script by absolute path"
  assert_contains "$body" "<key>StartCalendarInterval</key>" "...on a calendar interval"
  assert_contains "$body" "<key>Weekday</key>" "...keyed on a weekday, so it is weekly"
  assert_contains "$body" "/opt/homebrew/bin/bash" "...run by a bash new enough for the script"
  if command -v plutil >/dev/null 2>&1; then
    if plutil -lint "$plist" >/dev/null 2>&1; then
      pass "...and it parses as a real plist (plutil -lint)"
    else
      fail "...and it parses as a real plist (plutil -lint)" "$(plutil -lint "$plist" 2>&1)"
    fi
  fi
  assert_eq "$rc" "0" "...and the install reports success once launchctl lists the label"
  assert_contains "$out" "Sundays 03:00" "...telling the operator when it will fire"
else
  fail "the plist is written" "expected $plist"
fi

# THE CASE THAT MATTERS: the plist is written but launchctl never registers it. That is a
# schedule which will never fire, and on disk it is indistinguishable from one that will. The
# install has to call that a failure - checking a positive marker, not an absent error.
reset_fixtures
: >"$FIX/launchctl.fail"
out=$(env "${install_env[@]}" "$SUT" --evidence-dir "$WORK/evidence" --install-schedule 2>&1)
rc=$?
assert_eq "$rc" "1" "an install launchctl did not register exits non-zero"
assert_contains "$out" "INSTALL FAILED" "...and says INSTALL FAILED"
assert_contains "$out" "would never have fired" "...explaining the consequence"
rm -f "$FIX/launchctl.fail"

env "${install_env[@]}" "$SUT" --evidence-dir "$WORK/evidence" --install-schedule >/dev/null 2>&1
env "${install_env[@]}" "$SUT" --uninstall-schedule >/dev/null 2>&1
assert_absent "$plist" "--uninstall-schedule removes the plist again"

# ===========================================================================
# The no-pull-request class: reclaimed on age, and only when nothing else claims it
# ===========================================================================

printf '\nno pull request: reclaimed once nothing has touched it for the threshold\n'

reset_fixtures
repo=$(make_repo alpha)
wt_old=$(add_worktree "$repo" nopr-old feature/nopr-old)
wt_new=$(add_worktree "$repo" nopr-new feature/nopr-new)
age_worktree "$wt_old" 20
out=$(run_sut)
assert_absent "$wt_old" "a no-PR worktree untouched for 20 days is reclaimed"
assert_contains "$out" "nothing has touched it for" "...and the report gives its age as the reason"
assert_exists "$wt_new" "a no-PR worktree touched today is kept"
assert_contains "$out" "needs 14" "...and the report says how old it would have to be"

# Age is the LAST question asked, and both checks that actually protect work come first. If either
# of these two ever fails, the age rule has been moved ahead of a guard and it is no longer safe.
printf '\n...but age never overrides the two checks that protect work\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" nopr-dirty feature/nopr-dirty)
echo "a local edit" >>"$wt/tracked.txt"
age_worktree "$wt" 60
out=$(run_sut)
assert_exists "$wt" "an ancient no-PR worktree holding uncommitted work is still left in place"
assert_contains "$out" "kept-uncommitted" "...and rescued, not reclaimed on age"

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" nopr-live feature/nopr-live)
age_worktree "$wt" 60
sessions_json "$wt"
out=$(run_sut)
assert_exists "$wt" "an ancient no-PR worktree a session is sitting in is still untouched"
assert_contains "$out" "kept-live" "...and reported as live, not as old"

printf '\nage takes the NEWEST signal, so a recent git operation keeps a stale-looking directory\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" nopr-reflog feature/nopr-reflog)
age_worktree "$wt" 40
# The directory looks 40 days old, but git was used in it a moment ago. A rule reading only the
# directory mtime would delete a worktree somebody had just checked a branch out in.
admin=$(git -C "$wt" rev-parse --absolute-git-dir 2>/dev/null)
touch "$admin/logs/HEAD"
out=$(run_sut)
assert_exists "$wt" "a recent git operation in the worktree keeps it, whatever the directory says"

printf '\nthe threshold is configurable, and the report quotes the one in force\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" nopr-five feature/nopr-five)
age_worktree "$wt" 5
out=$(run_sut)
assert_exists "$wt" "5 days old is kept at the default threshold of 14"
out=$(RECLAIM_NO_PR_MIN_AGE_DAYS=3 run_sut)
assert_absent "$wt" "...and reclaimed once the threshold is lowered to 3"

# ===========================================================================
# Flags that nothing else exercises
# ===========================================================================

printf '\n--maxdepth bounds discovery, and the report says how many repositories it found\n'

reset_fixtures
repo_shallow=$(make_repo alpha)
mkdir -p "$ROOTS/deep/deeper/deepest"
repo_deep=$(make_repo deep/deeper/deepest/beta)
wt_shallow=$(add_worktree "$repo_shallow" m feature/m-a)
wt_deep=$(add_worktree "$repo_deep" m feature/m-b)
pr_fixture alpha feature/m-a MERGED
pr_fixture beta feature/m-b MERGED
out=$(RECLAIM_LOCK_DIR="$WORK/lock.depth" "$SUT" --root "$ROOTS" --maxdepth 2 \
  --evidence-dir "$WORK/evidence" --no-caches 2>&1)
assert_absent "$wt_shallow" "a repository within --maxdepth is swept"
assert_exists "$wt_deep" "one deeper than --maxdepth is not reached"
assert_eq "$(printf '%s\n' "$out" | awk '/^repositories swept/{print $NF; exit}')" "1" \
  "...and the count reports only what was actually examined"

printf '\n--sessions-from reads a captured registry instead of asking agent-deck\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" merged-one feature/merged-one)
pr_fixture alpha feature/merged-one MERGED
# The live registry says nothing protects it; the captured file says a session holds it. If the
# flag were ignored the worktree would be removed, so this proves the file is what was read.
echo '[]' >"$FIX/sessions.json"
printf '[{"id":"captured-1","status":"running","path":"%s"}]\n' "$wt" >"$WORK/captured.json"
out=$(run_sut --sessions-from "$WORK/captured.json")
assert_exists "$wt" "a worktree named in the captured registry is protected"
assert_contains "$out" "captured-1" "...and the report names the session from that file"


# ===========================================================================
# The five defects the first real launchd run and the independent review found
# ===========================================================================

printf '\nan ordinary word containing "pid" is not a pid\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" word-pid feature/word-pid)
# Reproduced against the real script 2026-08-20: the reason below yielded pid 123, ps said gone,
# and the lock was broken and the worktree removed. English is full of words containing "pid" -
# rapid, stupid, tepid, insipid - and a lock is one of only three protections this job respects.
git -C "$repo" worktree lock --reason "keep during rapid123 rollout, do not touch" "$wt"
out=$(run_sut)
assert_exists "$wt" "a lock reason saying 'rapid123' does NOT read as pid 123"
assert_contains "$out" "names no pid" "...and the report says the holder could not be checked"
assert_not_contains "$out" "removed-after-unlock" "...and nothing was unlocked on that basis"

printf '\na hostile launchd label is refused before it reaches the plist\n'

reset_fixtures
LAUNCH_DIR2="$WORK/launchagents2"
# A well-formed injection: the resulting plist stays VALID (verified with plutil -lint during
# review) and carries an injected RunAtLoad key that was never in the template, so the install's
# own launchctl verification cannot catch it.
HOSTILE='com.test</string><key>RunAtLoad</key><true/><key>X</key><string>y'
out=$(env RECLAIM_LAUNCHD_DIR="$LAUNCH_DIR2" RECLAIM_LAUNCHD_LABEL="$HOSTILE" \
  "$SUT" --evidence-dir "$WORK/evidence" --install-schedule 2>&1)
rc=$?
assert_eq "$rc" "1" "an install with a hostile label exits non-zero"
assert_contains "$out" "may contain only letters" "...saying why it was refused"
assert_eq "$(find "$LAUNCH_DIR2" -name '*.plist' 2>/dev/null | wc -l | tr -d ' ')" "0" \
  "...and NO plist was written at all"

printf '\na repository git cannot read is named, not silently skipped\n'

reset_fixtures
repo=$(make_repo alpha)
add_worktree "$repo" m feature/m >/dev/null
pr_fixture alpha feature/m MERGED
broken=$(make_repo broken)
# Garbage in HEAD is exactly the corruption a crash under disk pressure leaves, which is when this
# job runs. `find` enters the .git fine and reports nothing on stderr, so nothing else notices.
echo "garbage not a ref" >"$broken/.git/HEAD"
out=$(run_sut)
rc=$?
assert_contains "$out" "git could not list its worktrees" \
  "a repo whose worktree list fails appears in the gap list"
assert_contains "$out" "NOT A CLEAN SWEEP" "...so the run does not read as complete"
assert_eq "$rc" "1" "...and it exits 1"

printf '\nan untracked symlink is recorded, never copied into the evidence tree\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" symlinked feature/symlinked)
pr_fixture alpha feature/symlinked MERGED
mkdir -p "$WORK/outside"
echo "a secret that lives elsewhere" >"$WORK/outside/secret.txt"
ln -s "$WORK/outside/secret.txt" "$wt/dot-env-link"
out=$(run_sut)
assert_exists "$wt" "the worktree is kept, as any dirty one is"
manifest=$(find "$WORK/evidence/rescued-worktree-files" -name untracked-symlinks.txt | head -1)
assert_contains "$(cat "$manifest" 2>/dev/null)" "dot-env-link -> " \
  "the symlink and its target are recorded in a manifest"
copied=$(find "$WORK/evidence/rescued-worktree-files" -name 'dot-env-link' | wc -l | tr -d ' ')
assert_eq "$copied" "0" "...and the link itself is NOT reproduced in the evidence tree"
assert_not_contains "$out" "rescue-failed" \
  "...and a worktree whose only uncommitted item is a symlink is not a weekly false alarm"

printf '\nthe rescue directory is not world-readable\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" dirty-perm feature/dirty-perm)
pr_fixture alpha feature/dirty-perm MERGED
echo edit >>"$wt/tracked.txt"
run_sut >/dev/null 2>&1
d=$(find "$WORK/evidence/rescued-worktree-files" -maxdepth 1 -type d -name '*dirty-perm*' | head -1)
assert_eq "$(stat -f '%Lp' "$d" 2>/dev/null)" "700" \
  "a rescue directory is 700, not whatever the ambient umask gives"

printf '\na worktree that stays dirty is not re-copied in full every week\n'

reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" persistent feature/persistent)
pr_fixture alpha feature/persistent MERGED
echo edit >>"$wt/tracked.txt"
run_sut >/dev/null 2>&1
first=$(find "$WORK/evidence/rescued-worktree-files" -maxdepth 1 -type d -name '*persistent*' | wc -l | tr -d ' ')
out=$(run_sut)
second=$(find "$WORK/evidence/rescued-worktree-files" -maxdepth 1 -type d -name '*persistent*' | wc -l | tr -d ' ')
assert_eq "$first" "1" "the first sweep banks one rescue"
assert_eq "$second" "1" "...and the second banks NO second copy of identical content"
assert_contains "$out" "unchanged since" "...reporting that it was already held"


# ===========================================================================
# The gap list is the only channel that can say a sweep was incomplete, so a
# permanently-recurring entry in it is a defect, not noise. Three of those.
# ===========================================================================

printf '\na .git that is not a repository is counted, not gapped\n'

reset_fixtures
repo=$(make_repo alpha)
add_worktree "$repo" m feature/m >/dev/null
pr_fixture alpha feature/m MERGED
# THE POSITIVE CONTROL. ~/.cache/uv/sdists-v9 is a build artifact whose .git is a ZERO-BYTE FILE,
# and it appeared in the gap list of the first real run. It cannot hold a worktree, so nothing can
# hide there and its unexaminability is not a blindness. There are 32 such .git entries under
# ~/.cache on this machine.
mkdir -p "$ROOTS/artifact"
: >"$ROOTS/artifact/.git"
out=$(run_sut)
rc=$?
assert_not_contains "$out" "the repository at $ROOTS/artifact" \
  "a zero-byte .git file does NOT appear in the gap list"
assert_contains "$out" "not git repositories ....... 1" "...it is counted as a non-repository instead"
assert_eq "$rc" "0" "...and the run is still a clean sweep"

printf '\n...while a real repository git cannot read is STILL gapped\n'

reset_fixtures
repo=$(make_repo alpha)
add_worktree "$repo" m feature/m >/dev/null
pr_fixture alpha feature/m MERGED
broken=$(make_repo broken)
echo "garbage not a ref" >"$broken/.git/HEAD"
out=$(run_sut)
rc=$?
assert_contains "$out" "git could not list its worktrees" \
  "a .git DIRECTORY git cannot read is still a gap: it could hold a worktree and we cannot tell"
assert_eq "$rc" "1" "...and still exits 1"

printf '\nonly NEWLY-unreadable directories are gapped; a stable set is a stated fact\n'

reset_fixtures
repo=$(make_repo alpha)
mkdir -p "$ROOTS/locked-away/inner"
chmod 000 "$ROOTS/locked-away"
first=$(run_sut)
second=$(run_sut)
rc=$?
chmod 755 "$ROOTS/locked-away"
assert_contains "$first" "newly-unreadable" "the first sweep gaps a directory it could not enter"
assert_not_contains "$second" "newly-unreadable" \
  "...and the second does NOT, because it is now a known constant"
assert_contains "$second" "unreadable directories ....." \
  "...but the count is still stated in the report every run"
assert_eq "$rc" "0" "...and a run whose only unreadable paths are known is a clean sweep"

printf '\nthe uv cache lock: expected when a live process holds it, a failure otherwise\n'

reset_fixtures
repo=$(make_repo alpha)
: >"$FIX/uv-lockfail"
echo $$ >"$FIX/lsof-holder"   # the ps stub reports the suite's own pid as alive
out=$(RECLAIM_LOCK_DIR="$WORK/lock.uvskip" "$SUT" --root "$ROOTS" \
  --evidence-dir "$WORK/evidence" 2>&1)
rc=$?
assert_contains "$out" "SKIPPED" "a lock held by a VERIFIED live process is reported SKIPPED"
assert_not_contains "$out" "the uv cache (its own clean command failed)" "...raising no gap"
assert_eq "$rc" "0" "...and not setting exit 1"

printf '\n...but a lock message with NO verifiable holder still fails, closed\n'

reset_fixtures
repo=$(make_repo alpha)
: >"$FIX/uv-lockfail"
# No lsof-holder file, so lsof reports nothing: the benign reading cannot be established.
out=$(RECLAIM_LOCK_DIR="$WORK/lock.uvnoholder" "$SUT" --root "$ROOTS" \
  --evidence-dir "$WORK/evidence" 2>&1)
rc=$?
assert_contains "$out" "FAILED" "an unverifiable lock claim is still a FAILED row"
assert_contains "$out" "its own clean command failed" "...with its gap"
assert_eq "$rc" "1" "...and exit 1. A quiet false green is worse than a noisy true failure."

printf '\n...and a NON-lock failure fails even while the lock is genuinely held\n'

reset_fixtures
repo=$(make_repo alpha)
: >"$FIX/uv-otherfail"
echo $$ >"$FIX/lsof-holder"
out=$(RECLAIM_LOCK_DIR="$WORK/lock.uvother" "$SUT" --root "$ROOTS" \
  --evidence-dir "$WORK/evidence" 2>&1)
rc=$?
assert_contains "$out" "Input/output error" "an unrelated uv failure is reported verbatim"
assert_not_contains "$out" "uv     SKIPPED" "...and is NOT excused by the lock being held"
assert_eq "$rc" "1" "...and exits 1"


printf '\n...and a failure that merely CONTAINS "lock" in a path is not excused\n'

reset_fixtures
repo=$(make_repo alpha)
: >"$FIX/uv-filelockfail"
echo $$ >"$FIX/lsof-holder"
# Reproduced by review 2026-08-20: the message match was a substring test on "lock", and `filelock`
# is a very common Python dependency sitting in the uv cache. A real I/O error naming that path was
# downgraded to SKIPPED with exit 0 - a genuine failure erased, under disk pressure of all times.
out=$(RECLAIM_LOCK_DIR="$WORK/lock.uvfilelock" "$SUT" --root "$ROOTS" \
  --evidence-dir "$WORK/evidence" 2>&1)
rc=$?
assert_contains "$out" "Directory not empty" "an unrelated failure mentioning filelock is reported"
assert_not_contains "$out" "uv     SKIPPED" "...and NOT excused, because it never names the lock file"
assert_eq "$rc" "1" "...and it exits 1"

printf '\n...and a holder that is not a uv process cannot excuse a uv failure\n'

reset_fixtures
repo=$(make_repo alpha)
: >"$FIX/uv-lockfail"
echo $$ >"$FIX/lsof-holder"
echo "bash" >"$FIX/ps-comm"   # something holds the lock, but it is not uv
out=$(RECLAIM_LOCK_DIR="$WORK/lock.uvnonuv" "$SUT" --root "$ROOTS" \
  --evidence-dir "$WORK/evidence" 2>&1)
rc=$?
assert_not_contains "$out" "uv     SKIPPED" \
  "a non-uv holder is no evidence that uv failed because of the lock"
assert_eq "$rc" "1" "...so the failure stands and exits 1"

printf '\n--dry-run does not spend the report-once guarantee\n'

reset_fixtures
repo=$(make_repo alpha)
mkdir -p "$ROOTS/hidden-away/inner"
chmod 000 "$ROOTS/hidden-away"
# The log directory is pre-created deliberately. Without it, ungating only the baseline WRITE is
# masked: the mv fails because the parent does not exist yet, so the mutation goes undetected and
# only one of the two gates is really pinned. Mutation testing found exactly that.
mkdir -p "$WORK/evidence/reclamation"
dry=$(run_sut --dry-run)
baseline="$WORK/evidence/reclamation/unreadable-baseline.txt"
# Reproduced by review 2026-08-20: the baseline write was ungated, so a preview marked the paths as
# known and the real run that followed never reported them. The one notification this feature
# exists to deliver was spent by a run documented as changing nothing.
assert_absent "$baseline" "--dry-run writes NO baseline"
real=$(run_sut)
chmod 755 "$ROOTS/hidden-away"
assert_contains "$real" "newly-unreadable" \
  "...so the real run that follows still reports the directory as new"
assert_exists "$baseline" "...and only the real run records it"


printf '\na session path containing a tab still protects its worktree\n'

reset_fixtures
repo=$(make_repo alpha)
# jq's @tsv ESCAPES a tab inside a value, emitting the two characters \t. Measured 2026-08-20: a
# session path containing a tab therefore came back as a path that does not exist, failed to
# resolve, and protected nothing - a live session's worktree was one guard away from being removed
# underneath it. The only thing catching it was a tab guard whose own comment gave a reason that was
# no longer true, so a dead-code pass proposed deleting it and nearly took the guard with it. This
# pins the CAUSE (the 0x1f join in read_sessions) rather than the workaround.
wt_tab="$repo/.worktrees/wt$(printf '\t')tabbed"
git -C "$repo" worktree add -q "$wt_tab" -b feature/tabbed >/dev/null 2>&1
pr_fixture alpha feature/tabbed MERGED
sessions_json "$wt_tab"
out=$(run_sut)
assert_exists "$wt_tab" "a worktree whose path contains a tab is not removed"
assert_not_contains "$out" "protected nothing" \
  "...and the session path RESOLVES, so it protects rather than silently failing to"

# ===========================================================================
# --if-due: the catch-up guard.
#
# The bug: StartCalendarInterval occurrences that fall while the machine is POWERED OFF are
# skipped outright - launchd only carries a pending calendar event for the boot session it is
# in (`launchctl print` shows the schedule as a com.apple.launchd.calendarinterval event stream
# owned by UserEventAgent). Asleep is fine, it fires on wake; off is a silently lost week.
#
# RunAtLoad closes that, and needs a guard, because logins are frequent and this job DELETES
# DIRECTORIES. The guard's two failure modes are not symmetric and these cases pin the
# asymmetry: anything that is not positive evidence of a completed run must read as DUE.
# ===========================================================================

DUE_STAMP="$WORK/evidence/reclamation/last-run"
DAY=86400

stamp_raw() { # <exact contents>  -> a last-run record written verbatim, nothing appended
  # THE mkdir IS LOAD-BEARING, on every single write: due_fixture calls reset_fixtures, which
  # recursively deletes $WORK/evidence. A case that wrote the record without first recreating the
  # directory would leave NO record at all, which the guard reads as DUE - the same verdict several
  # of these cases assert. The test would PASS while pinning nothing. One helper means one place to
  # lose that rather than four.
  mkdir -p "$(dirname "$DUE_STAMP")"
  printf '%s' "$1" >"$DUE_STAMP"
}

stamp_ago() { # <signed seconds from now>  -> positive is the past, NEGATIVE is the future
  stamp_raw "$(($(date +%s) - $1))"
}

# A merged worktree in every case, so "did it sweep" is answered by whether a directory is gone
# rather than by whether a string appeared. The string can be right while the behaviour is wrong.
due_fixture() {
  reset_fixtures
  repo=$(make_repo alpha)
  wt=$(add_worktree "$repo" merged-one feature/merged-one)
  pr_fixture alpha feature/merged-one MERGED
}

printf '\n--if-due, case 1: a week was missed (last run 8 days ago) - it MUST run\n'

due_fixture
stamp_ago $((8 * DAY))
out=$(run_sut --if-due)
rc=$?
assert_absent "$wt" "a last run 8 days ago is due, and the sweep really happens"
assert_contains "$out" "repositories swept" "...and the report is produced"
assert_contains "$out" "catch-up check: DUE" "...and the log says it decided the run was due"
assert_eq "$rc" "0" "...and it exits 0"

# AND IT RECORDS ITSELF, which is the half that closes the loop. launchd is the only caller of
# --if-due, so if a due run sweeps without recording, RunAtLoad sweeps again on the next login and
# on every login after that, forever, and the catch-up never converges. Nothing pinned this until
# an independent mutation showed `record_run` skipping when IF_DUE=1 passed the whole suite: every
# other recording assertion in this file uses a plain run, never a guarded one.
# The VALUE, not the existence: stamp_ago already created this file, so `assert_exists` here would
# pass whether or not record_run ever ran - it did, and mutation testing caught it.
recorded=$(cat "$DUE_STAMP" 2>/dev/null)
if [ -n "$recorded" ] && [ "$recorded" != "$(($(date +%s) - 8 * DAY))" ] &&
  [ "$(($(date +%s) - recorded))" -lt 300 ]; then
  pass "a DUE --if-due run records the run it just completed (record moved to $recorded)"
else
  fail "a DUE --if-due run records the run it just completed" \
    "the record still reads [$recorded], i.e. the 8-day-old value stamp_ago wrote"
fi
# No -b: the branch outlived its worktree, which is the safety argument this whole job rests on.
git -C "$repo" worktree add -q "$repo/.worktrees/merged-two" feature/merged-one >/dev/null 2>&1
out=$(run_sut --if-due)
assert_contains "$out" "catch-up check: NOT DUE" \
  "...and the record it just wrote is read back by the very next --if-due run"
assert_exists "$repo/.worktrees/merged-two" "...which therefore sweeps nothing the second time"

printf '\n--if-due, case 2: an ordinary login (last run 1 hour ago) - it MUST skip\n'

due_fixture
stamp_ago 3600
out=$(run_sut --if-due)
rc=$?
assert_exists "$wt" "a last run 1 hour ago is not due, so NOTHING is removed"
assert_not_contains "$out" "repositories swept" "...and no sweep is even attempted"
assert_contains "$out" "catch-up check: NOT DUE" "...and it says so, rather than going quiet"
assert_contains "$out" "1 hour ago" \
  "...naming the age in words an operator reads, singular where it should be"
assert_eq "$rc" "0" "...and exits 0, because not due is not a failure"

printf '\n--if-due, case 3: no record at all (fresh machine, or a lost stamp) - it MUST run\n'

due_fixture
rm -f "$DUE_STAMP"
out=$(run_sut --if-due)
assert_absent "$wt" "NO record reads as DUE, never as ran recently"
assert_contains "$out" "catch-up check: DUE - no readable record" \
  "...and STATES that verdict, naming the missing record as the reason"
assert_not_contains "$out" "invalid integer constant" \
  "...rather than falling through on an arithmetic error"

printf '\n--if-due, case 4: a record it cannot parse is not evidence of a run\n'

due_fixture
stamp_raw 'the day before yesterday'
out=$(run_sut --if-due)
assert_absent "$wt" "a long non-numeric record reads as DUE"
assert_contains "$out" "catch-up check: DUE" "...having STATED that verdict"

# SHORT and non-numeric, which is the input that isolates the digit check from the length bound.
# "the day before yesterday" is 21 characters, so the length bound catches it and the case says
# nothing about the digit check - verified by mutation on 2026-08-21, which dropped the digit check
# and left the suite green. "abc" is 3 characters, so only the digit check stands between it and
# $((10#abc)), and that aborts the enclosing command list rather than returning a verdict.
due_fixture
stamp_raw 'abc'
out=$(run_sut --if-due)
assert_absent "$wt" "a SHORT non-numeric record reads as DUE"
assert_contains "$out" "catch-up check: DUE" \
  "...having STATED a verdict, not fallen through an aborted arithmetic"
assert_not_contains "$out" "invalid integer constant" "...and without an arithmetic error"

due_fixture
stamp_raw ''
out=$(run_sut --if-due)
assert_absent "$wt" "an EMPTY record reads as DUE"
assert_contains "$out" "catch-up check: DUE - no readable record" "...having STATED that verdict"

# THE GUARD MUST HAVE A DEFINED VERDICT FOR EVERY INPUT, not just a correct one for good input.
# Both records below are all-digits, so they pass the character check and reach the arithmetic.
#
# THE INPUTS ARE CHOSEN, NOT ILLUSTRATIVE. Mutation testing on 2026-08-21 killed the first two
# attempts at these cases because both were accidentally benign: "01755000000" contains no digit
# above 7, so it is VALID octal and bare $(( )) merely misreads it as 1978 - still DUE, so the
# case could not fail; and "99999999999999999999" wraps to a far-FUTURE value, so it was caught by
# the future branch instead of the one under test. A case that passes with the guard removed is
# decoration. These two do not.

# 1. LEADING ZERO CONTAINING A 9, so it is not valid octal. Without the 10# prefix, measured:
#      bash: 0999999999: value too great for base (error token is "0999999999")
#      bash: age: unbound variable
#    - the assignment fails, the comparison fails, `age` is never assigned, and `set -u` kills the
#    script INSIDE the guard. No verdict, no sweep, and a launchd log full of bash errors.
due_fixture
stamp_raw 0999999999
out=$(run_sut --if-due)
# THE ASSERTION THAT MATTERS IS THIS ONE. Measured 2026-08-21: a failed arithmetic expansion does
# not merely misread the number, it ABORTS the enclosing command list - so catch_up_check returns
# before printing anything, the `|| exit 0` beside it never runs, and the script proceeds to sweep
# with the guard SKIPPED rather than decided. Verified in isolation: a line after the failed
# $(( )) never executes, and neither branch of an `if` around the function runs.
# The guard's failure mode is that the guard vanishes, which is the whole defect class here, so
# what has to be pinned is that a verdict is always STATED - not merely that the outcome was lucky.
assert_contains "$out" "catch-up check:" \
  "the guard STATES a verdict for a leading-zero record rather than falling through silently"
assert_absent "$wt" "...and that verdict is DUE"
assert_not_contains "$out" "value too great for base" \
  "...reached without an arithmetic error where a decision should be"

# 2. TOO LONG TO BE A TIMESTAMP. bash wraps a literal wider than 64 bits SILENTLY rather than
#    failing, so a 20-digit record can land exactly on "now" - the NOT DUE direction, which is the
#    catastrophic one. Measured 2026-08-21: $((10#18446744075496852011)) == 1787300395 == the
#    second it was computed. The value is built at test time because it is now + 2^64 and now moves.
due_fixture
now_s=$(date +%s)
overflow=""
if command -v python3 >/dev/null 2>&1; then
  overflow=$(python3 -c "print($now_s + 2**64)" 2>/dev/null)
elif command -v bc >/dev/null 2>&1; then
  overflow=$(echo "$now_s + 18446744073709551616" | bc 2>/dev/null | tr -d '\\\n')
fi
if [ -z "$overflow" ]; then
  fail "a 20-digit record is rejected on LENGTH" \
    "neither python3 nor bc is available, so the fixture could not be built - NOT a pass"
else
stamp_raw "$overflow"
# PROVE THE PREMISE rather than assume it. If this string did not wrap into the window on this
# bash, the assertion below would pass for the wrong reason and pin nothing.
wrapped=$((10#$overflow))
if [ "$wrapped" -gt 0 ] && [ "$((now_s - wrapped))" -ge 0 ] &&
  [ "$((now_s - wrapped))" -lt $((6 * DAY)) ]; then
  pass "premise: a 20-digit record really does wrap into the not-due window ($overflow -> $wrapped)"
else
  fail "premise: a 20-digit record really does wrap into the not-due window" \
    "$overflow wrapped to $wrapped, outside the window - the case below would prove nothing"
fi
out=$(run_sut --if-due)
assert_absent "$wt" "a 20-digit record is rejected on LENGTH, before it can wrap into the window"
fi

# A padded or CR-terminated record is still a record. stamp_raw writes with printf '%s' and never a
# newline, so nothing exercised the `tr -d '[:space:]'` in the reader - deleting it left the suite
# green. This matters in the suppressing direction: a real record written by record_run ends in a
# newline, so if the trim were lost, every genuine record would read as unparseable and the job
# would sweep on EVERY login.
due_fixture
stamp_raw "$(printf ' %s \r\n' "$(($(date +%s) - 3600))")"
out=$(run_sut --if-due)
assert_exists "$wt" "a record padded with spaces and a CRLF is still read as a recent run"
assert_contains "$out" "catch-up check: NOT DUE" "...and yields NOT DUE, not 'unreadable'"

printf '\n--if-due, case 5: a record in the future is a moved clock, not a completed run\n'

due_fixture
stamp_ago $((-3 * DAY))
out=$(run_sut --if-due)
assert_absent "$wt" "a record 3 days in the FUTURE reads as DUE, not as suppressed for a week"
assert_contains "$out" "future" "...and says the record is in the future"

printf '\n--if-due, case 6: the window itself. 5 days is not a week, 7 days is\n'

due_fixture
stamp_ago $((5 * DAY))
out=$(run_sut --if-due)
assert_exists "$wt" "5 days is inside the 6-day window: not due"

due_fixture
stamp_ago $((7 * DAY))
out=$(run_sut --if-due)
assert_absent "$wt" "7 days is outside it: due. A weekly job must never read its own week as recent"

# AND THE BOUNDARY ITSELF, an hour either side of 6 days. Without this pair the 5/7-day cases only
# bracket the window to "6 or 7", and a default of 7 passes the entire suite - verified by mutation
# on 2026-08-21. 6 is the number the docs, the install message and the "7 days between Sundays
# always reaches the window" argument all rest on, so it is pinned to 6 and not to a range.
due_fixture
stamp_ago $((6 * DAY - 3600))
out=$(run_sut --if-due)
assert_exists "$wt" "an hour SHORT of 6 days is not due"

due_fixture
stamp_ago $((6 * DAY + 3600))
out=$(run_sut --if-due)
assert_absent "$wt" "...and an hour PAST 6 days is due, so the window is exactly 6 days"

printf '\n--if-due, case 7: the guard exists ONLY on the guarded path\n'

due_fixture
stamp_ago 3600
out=$(run_sut)
assert_absent "$wt" "without --if-due a run 1 hour ago is NOT suppressed: manual runs are unguarded"
assert_not_contains "$out" "catch-up check" "...and the guard says nothing at all"

printf '\n--if-due, case 8: what counts as a run. Only a sweep that finished records one\n'

# A completed sweep records itself.
due_fixture
rm -f "$DUE_STAMP"
run_sut >/dev/null 2>&1
assert_exists "$DUE_STAMP" "a completed run records the time it finished"
after=$(tr -d '[:space:]' <"$DUE_STAMP" 2>/dev/null)
case "$after" in
'' | *[!0-9]*) fail "...as epoch seconds the guard can read back" "got [$after]" ;;
*) pass "...as epoch seconds the guard can read back" ;;
esac

# --dry-run changes nothing, and that includes the stamp. The same defect as the unreadable
# baseline: a preview that spends the next real run is a preview with a side effect.
due_fixture
rm -f "$DUE_STAMP"
run_sut --dry-run >/dev/null 2>&1
assert_absent "$DUE_STAMP" "--dry-run records NO run, so a preview cannot suppress a real one"

# A run that REFUSED before sweeping (exit 2) did not run. This is the case Jonny named: a run
# that started and failed must not buy itself a week of silence.
due_fixture
rm -f "$DUE_STAMP"
: >"$FIX/sessions.fail"
out=$(run_sut)
rc=$?
assert_eq "$rc" "2" "a run that cannot read the session registry refuses with exit 2"
assert_absent "$DUE_STAMP" "...and records NO run, because it never swept"
rm -f "$FIX/sessions.fail"
out=$(run_sut --if-due)
assert_absent "$wt" "...so the very next --if-due run is still due, and sweeps"

# ...but a sweep that FINISHED with gaps did sweep. Exit 1 is "swept, with gaps", not "refused".
due_fixture
rm -f "$DUE_STAMP"
: >"$FIX/gh-alpha.fail"
out=$(run_sut)
rc=$?
assert_eq "$rc" "1" "a sweep that could not read gh exits 1 with a gap"
assert_exists "$DUE_STAMP" "...and DOES record a run, because the sweep itself completed"

printf '\n--if-due, case 8b: a record that CANNOT be written warns, and fails safe\n'

# A directory where the record should be is the cheapest way to make the write fail for real.
# Deleting record_run's entire warning block left the suite green before this case existed.
due_fixture
rm -f "$DUE_STAMP" 2>/dev/null
mkdir -p "$DUE_STAMP"
out=$(run_sut)
rc=$?
assert_contains "$out" "could not be written" "a record that cannot be written says so, loudly"
assert_eq "$rc" "0" "...without failing the sweep, which did complete"
rmdir "$DUE_STAMP" 2>/dev/null
out=$(run_sut --if-due)
assert_contains "$out" "catch-up check: DUE" \
  "...and the next --if-due run is DUE, which is the safe direction the warning promises"

printf '\n--if-due, case 9: a skip must not slide the window forward\n'

# THE CATASTROPHIC FAILURE MODE, pinned. If the skip path touched the stamp, every login would
# refresh it, the window would never elapse, and the weekly job would never run again - silently,
# and strictly worse than the bug being fixed here.
reset_fixtures
stamp_ago $((5 * DAY))
before=$(cat "$DUE_STAMP")
run_sut --if-due >/dev/null 2>&1
assert_eq "$(cat "$DUE_STAMP")" "$before" \
  "a not-due run leaves the record ALONE; refreshing it would suppress the job forever"

printf '\n--if-due, case 9b: a not-due run does not touch the lock a real sweep is holding\n'

# The guard sits ABOVE the preflight and ABOVE the lock on purpose, so a login during a long Sunday
# sweep costs a file read rather than a refusal. Move it below acquire_lock and every such login
# exits 2 - which launchd records as a failing job - and nothing in this suite would have noticed.
reset_fixtures
mkdir -p "$WORK/held-lock"
echo $$ >"$WORK/held-lock/pid" # the suite's own pid, which the ps stub reports as alive
stamp_ago 3600
out=$(RECLAIM_LOCK_DIR="$WORK/held-lock" "$SUT" --root "$ROOTS" \
  --evidence-dir "$WORK/evidence" --no-caches --if-due 2>&1)
rc=$?
assert_contains "$out" "catch-up check: NOT DUE" "a not-due run decides before it reaches the lock"
assert_eq "$rc" "0" "...exiting 0 rather than 2, so launchd does not log a failing job"
assert_not_contains "$out" "another reclamation is running" "...never consulting the lock at all"
assert_exists "$WORK/held-lock/pid" "...and leaving the running sweep's lock untouched"

printf '\n--if-due, case 10: the plist wires both halves, or neither half works\n'

reset_fixtures
LAUNCH_DIR3="$WORK/launchagents3"
plist3="$LAUNCH_DIR3/com.test.catchup.plist"
out=$(env RECLAIM_LAUNCHD_DIR="$LAUNCH_DIR3" RECLAIM_LAUNCHD_LABEL=com.test.catchup \
  "$SUT" --evidence-dir "$WORK/evidence" --install-schedule 2>&1)
if [ -f "$plist3" ]; then
  body3=$(cat "$plist3")
  assert_contains "$body3" "<key>RunAtLoad</key>" "the installed plist runs the job at load"
  # RunAtLoad WITHOUT the flag is an unguarded deletion job firing on every login. The two keys
  # are one feature and this asserts them together on purpose.
  assert_contains "$body3" "<string>--if-due</string>" \
    "...and passes --if-due, so a login is guarded rather than an unguarded sweep"
  assert_contains "$body3" "<key>StartCalendarInterval</key>" \
    "...while keeping the Sunday calendar occurrence"
  if command -v plutil >/dev/null 2>&1; then
    if plutil -lint "$plist3" >/dev/null 2>&1; then
      pass "...and the plist with the new keys still parses (plutil -lint)"
    else
      fail "...and the plist with the new keys still parses (plutil -lint)" \
        "$(plutil -lint "$plist3" 2>&1)"
    fi
    # ORDER MATTERS: launchd passes ProgramArguments verbatim, so the flag has to land after the
    # script path. A plist whose argv reads "bash --if-due script" runs bash with the flag.
    # plutil's JSON escapes every forward slash as \/ - undo exactly that, rather than deleting
    # every backslash (which also trips shellcheck SC1003).
    argv=$(plutil -extract ProgramArguments json -o - "$plist3" 2>/dev/null | sed 's|\\/|/|g')
    assert_contains "$argv" "\"$SUT\",\"--if-due\"" \
      "...with the flag AFTER the script path, where it reaches the script and not bash"
  fi
  assert_contains "$out" "not run in" "the install tells the operator what the login run is gated on"
else
  fail "the catch-up plist is written" "expected $plist3"
fi

printf '\n--if-due, case 11: the window comes from the environment, so it is validated\n'

# THIS BLOCK HAD NO COVERAGE AT ALL until an independent review pointed it out: cases 1-10 never
# set RECLAIM_DUE_AFTER_DAYS, so every line of its validation was unexercised. The value reaches
# arithmetic that decides whether a deletion job runs, and each rejected shape fails differently.

# 0 IS THE DANGEROUS ONE, and it is why the range check exists rather than just a digit check. A
# window of 0 seconds makes EVERY invocation due, which turns --if-due back into the unguarded
# RunAtLoad this whole feature exists to avoid - the failure mode is the guard silently ceasing
# to guard, in the deletion direction.
due_fixture
stamp_ago 3600
out=$(RECLAIM_DUE_AFTER_DAYS=0 run_sut --if-due 2>&1)
rc=$?
assert_exists "$wt" "a window of 0 is REFUSED, not treated as 'everything is always due'"
assert_eq "$rc" "2" "...refusing with exit 2"
assert_contains "$out" "from 1 to" "...and saying what the value has to be"

# NON-NUMERIC, AND DELIBERATELY SHORT. "fortnight" is 9 characters, so it is caught by the LENGTH
# bound and says nothing about the digit check - mutation testing on 2026-08-21 removed the digit
# check and this case still passed. "abc" is 3 characters, so only the digit check stands between it
# and $((10#abc)) - which does not merely misread the value, it ABORTS the enclosing command list,
# so `catch_up_check || exit 0` never runs and the sweep proceeds with the guard SKIPPED. Hence the
# assertion below is that the worktree SURVIVES, not merely that the exit code is 2: an unguarded
# sweep is the failure this check prevents.
due_fixture
stamp_ago 3600
out=$(RECLAIM_DUE_AFTER_DAYS=abc run_sut --if-due 2>&1)
rc=$?
assert_exists "$wt" "a short non-numeric window is refused BEFORE any sweep can happen"
assert_eq "$rc" "2" "...with exit 2"
assert_contains "$out" "whole number from" "...naming the problem"
assert_not_contains "$out" "value too great for base" \
  "...and refuses CLEANLY, with no raw arithmetic error in the launchd log"
assert_not_contains "$out" "integer expected" "...and no raw test-builtin error either"

# ...and the long non-numeric value too, which the length bound catches. Kept as a separate case so
# that neither bound can be removed without a test going red.
due_fixture
stamp_ago 3600
out=$(RECLAIM_DUE_AFTER_DAYS=fortnight run_sut --if-due 2>&1)
rc=$?
assert_exists "$wt" "a long non-numeric window is also refused before sweeping"
assert_eq "$rc" "2" "...with exit 2"

# AND THE INSTALL PATH IS VALIDATED TOO, which is the bug this placement fixes. The validation
# originally sat inside `if [ "$IF_DUE" = 1 ]`, which is BELOW the --install-schedule dispatch, so an
# install with a malformed window printed "scheduled:", wrote the plist and exited 0 - and then every
# launchd trigger of the job it had just installed refused with exit 2. A schedule that can never
# fire, reported as installed, is the same defect the install's own launchctl verification exists to
# catch, one layer up. Reproduced by an independent review on 2026-08-21.
reset_fixtures
LAUNCH_DIR4="$WORK/launchagents4"
out=$(env RECLAIM_LAUNCHD_DIR="$LAUNCH_DIR4" RECLAIM_LAUNCHD_LABEL=com.test.badwindow \
  RECLAIM_DUE_AFTER_DAYS=abc "$SUT" --evidence-dir "$WORK/evidence" --install-schedule 2>&1)
rc=$?
assert_eq "$rc" "2" "--install-schedule REFUSES a malformed window instead of installing"
assert_contains "$out" "whole number from" "...saying why"
assert_not_contains "$out" "scheduled:" "...and never claiming the job was scheduled"
assert_eq "$(find "$LAUNCH_DIR4" -name '*.plist' 2>/dev/null | wc -l | tr -d ' ')" "0" \
  "...and writing NO plist, so there is no job that can never fire"

# Too many digits: $(( )) wraps a value wider than 64 bits silently, so the length bound is what
# stops a window that is not a window. Same lesson as the record, one layer out.
due_fixture
stamp_ago 3600
out=$(RECLAIM_DUE_AFTER_DAYS=99999999999999999999 run_sut --if-due 2>&1)
rc=$?
assert_eq "$rc" "2" "a window too long to be a number of days is refused with exit 2"
assert_exists "$wt" "...before any sweep could happen"

# AND THE POSITIVE CASE, without which the three above would pass on a script that ignored the
# variable entirely. A 1-day window must make a 1-hour-old record still not due, and a 2-hour-old
# record due - so the value is demonstrably WIRED to the comparison, not merely validated.
due_fixture
stamp_ago 3600
out=$(RECLAIM_DUE_AFTER_DAYS=1 run_sut --if-due 2>&1)
assert_exists "$wt" "with a 1-day window a 1-hour-old record is still not due"
assert_contains "$out" "reaches the 1-day window" \
  "...and the message reports the window it was given, grammatically"

due_fixture
stamp_ago $((2 * DAY))
out=$(RECLAIM_DUE_AFTER_DAYS=1 run_sut --if-due 2>&1)
assert_absent "$wt" "...and a 2-day-old record IS due under that window, so the value is wired in"

# ===========================================================================
# Tunable validation: every numeric setting is validated before the sweep
# ===========================================================================
#
# DUE_AFTER_DAYS was validated first (see "the window is validated" above). These three were not,
# and the NO_PR_MIN_AGE_DAYS omission is destructive: the -lt comparison in the sweep returns
# non-zero on a non-numeric operand, the keep branch is SKIPPED, and the worktree is REMOVED.
# The control test below proves this on the unfixed code; the validation tests prove the fix.

# ---------------------------------------------------------------------------
# THE CONTROL: a non-numeric NO_PR_MIN_AGE_DAYS removes a worktree it should keep
# ---------------------------------------------------------------------------
#
# This is the defect (jbrooksbartlett-lngd). A worktree with no pull request, touched today, should
# be kept because it is younger than any sane threshold. But with NO_PR_MIN_AGE_DAYS=abc:
#
#   [ "$idle" -lt "abc" ]   ->  "integer expression expected", exit 2
#   if branch NOT taken     ->  continue is skipped
#   falls through           ->  worktree is removed
#
# The protection becomes the opposite of a protection. This test must go RED on the unfixed code
# and GREEN after validation is added. If it passes on both, it is not testing the defect.

printf '\nCONTROL: non-numeric NO_PR_MIN_AGE_DAYS destroys work it should protect\n'

# A worktree aged 5 days with no pull request. At the default threshold of 14, this is well within
# the keep window. With NO_PR_MIN_AGE_DAYS=abc, the -lt comparison fails silently, the keep branch
# is skipped, and the worktree falls through to removal. Aged to 5 days so worktree_idle_days
# returns a real number and the comparison is actually reached.
reset_fixtures
repo=$(make_repo alpha)
wt=$(add_worktree "$repo" nopr-young feature/nopr-young)
age_worktree "$wt" 5
out=$(RECLAIM_NO_PR_MIN_AGE_DAYS=abc run_sut 2>&1)
rc=$?
assert_eq "$rc" "2" "a non-numeric NO_PR_MIN_AGE_DAYS is refused with exit 2"
assert_exists "$wt" "...and the worktree is NOT removed"
assert_contains "$out" "RECLAIM_NO_PR_MIN_AGE_DAYS" "...naming the variable"
assert_not_contains "$out" "integer expression expected" \
  "...cleanly, with no raw shell error leaking into the report"

# ---------------------------------------------------------------------------
# Validation: NO_PR_MIN_AGE_DAYS
# ---------------------------------------------------------------------------

assert_tunable_refused() { # <env-var=value> <slug> <message>
  reset_fixtures
  local repo wt
  repo=$(make_repo alpha)
  wt=$(add_worktree "$repo" "$2" "feature/$2")
  out=$(export "$1"; run_sut 2>&1)
  rc=$?
  assert_eq "$rc" "2" "$3"
  assert_exists "$wt" "...before any sweep"
}

printf '\nNO_PR_MIN_AGE_DAYS validation\n'

assert_tunable_refused RECLAIM_NO_PR_MIN_AGE_DAYS=abc     nopr-abc  "a non-numeric NO_PR_MIN_AGE_DAYS is refused"
assert_contains "$out" "RECLAIM_NO_PR_MIN_AGE_DAYS" "...naming the variable"
assert_tunable_refused RECLAIM_NO_PR_MIN_AGE_DAYS=0       nopr-zero "NO_PR_MIN_AGE_DAYS=0 is refused (a 0-day threshold removes everything)"
assert_tunable_refused RECLAIM_NO_PR_MIN_AGE_DAYS=-5      nopr-neg  "NO_PR_MIN_AGE_DAYS=-5 is refused"
assert_tunable_refused RECLAIM_NO_PR_MIN_AGE_DAYS=9999999 nopr-long "NO_PR_MIN_AGE_DAYS with too many digits is refused"

printf '\nMAXDEPTH validation\n'

assert_tunable_refused RECLAIM_MAXDEPTH=abc     maxd-abc  "a non-numeric MAXDEPTH is refused with exit 2"
assert_contains "$out" "RECLAIM_MAXDEPTH" "...naming the variable"
assert_tunable_refused RECLAIM_MAXDEPTH=0       maxd-zero "MAXDEPTH=0 is refused (find -maxdepth 0 finds nothing)"
assert_tunable_refused RECLAIM_MAXDEPTH=9999999 maxd-long "MAXDEPTH with too many digits is refused"

printf '\nRESCUE_MAX_BYTES validation\n'

assert_tunable_refused RECLAIM_RESCUE_MAX_BYTES=abc              rescue-abc  "a non-numeric RESCUE_MAX_BYTES is refused with exit 2"
assert_contains "$out" "RECLAIM_RESCUE_MAX_BYTES" "...naming the variable"
assert_tunable_refused RECLAIM_RESCUE_MAX_BYTES=0                rescue-zero "RESCUE_MAX_BYTES=0 is refused (a zero cap rescues nothing)"
assert_tunable_refused RECLAIM_RESCUE_MAX_BYTES=9999999999999999 rescue-long "RESCUE_MAX_BYTES with too many digits is refused"

# ---------------------------------------------------------------------------

printf '\n%s passed, %s failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
exit 0
