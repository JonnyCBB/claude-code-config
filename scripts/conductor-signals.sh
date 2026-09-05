#!/usr/bin/env bash
#
# conductor-signals.sh - the three work-contract success signals, as three numbers.
#
# Contract: docs/conductor-work-contract.md section 10.
# Run it at heartbeat time. Every signal targets 0 (signal 3 targets "trending down").
#
#   ./conductor-signals.sh                     the three signals
#   ./conductor-signals.sh --fast              skip the swapouts sample (20s faster)
#   ./conductor-signals.sh escalate 6 "why"    record a signal-3 escalation
#
# It reports. It never writes the queue, never dispatches, never closes anything.
#
# SIGNAL 1 IS A WORKLIST, NOT A VERDICT. Measured on the live queue 2026-08-18 it
# named 5 beads and all 5 were genuinely complete-but-open, but it reads English
# prose and trusts what an author wrote. docs/conductor-signals.md carries the
# measured rates, the three detections that were rejected, and - more importantly
# - the class it is structurally blind to.
#
# Silence a hit you have judged and want to keep open:  bd label add <id> signal1-ack

set -uo pipefail

if [ "${BASH_VERSINFO[0]:-0}" -lt 4 ] ||
   { [ "${BASH_VERSINFO[0]:-0}" -eq 4 ] && [ "${BASH_VERSINFO[1]:-0}" -lt 3 ]; }; then
  echo "conductor-signals: needs bash 4.3+ (macOS /bin/bash is 3.2; try /opt/homebrew/bin/bash)" >&2
  exit 2
fi

CAP=${CONDUCTOR_SIGNALS_CAP:-3}

# Contract section 4 thresholds. Named because jbrooksbartlett-cjxs is an open
# proposal to change the swap one, and a literal repeated at two call sites is
# how half a threshold change ships.
SWAP_VETO_MB=${CONDUCTOR_SIGNALS_SWAP_VETO_MB:-2000}
MEM_FREE_MIN_PCT=${CONDUCTOR_SIGNALS_MEM_FREE_MIN_PCT:-25}
LOAD_MAX=${CONDUCTOR_SIGNALS_LOAD_MAX:-9}

STATE_DIR=${CONDUCTOR_SIGNALS_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/conductor-signals}
ESCALATIONS="$STATE_DIR/escalations.jsonl"

# Repos searched for merged PRs. Live worker repos are added automatically, but
# the defaults never drop out - a repo whose sessions have all been retired is
# exactly where a merged-but-open bead hides.
DEFAULT_REPOS="$HOME/.claude:$HOME/src/switchboard:$HOME/src/beads-hq"
REPOS=${CONDUCTOR_SIGNALS_REPOS:-$DEFAULT_REPOS}

PR_LIMIT=${CONDUCTOR_SIGNALS_PR_LIMIT:-40}
PR_DAYS=${CONDUCTOR_SIGNALS_PR_DAYS:-14}
SAMPLE_SECONDS=${CONDUCTOR_SIGNALS_SAMPLE_SECONDS:-20}

RESOURCES_FILE=""
FAST=0

# ---------------------------------------------------------------------------
# escalate: the signal-3 write path
# ---------------------------------------------------------------------------

if [ "${1:-}" = "escalate" ]; then
  section=${2:-}
  what=${3:-}
  if [ -z "$section" ] || [ -z "$what" ]; then
    echo "usage: conductor-signals.sh escalate <contract-section> \"<what it was>\"" >&2
    exit 2
  fi
  mkdir -p "$STATE_DIR"
  # This is signal 3's ONLY write path and a dropped escalation is unrecoverable,
  # so the success message has to depend on the write actually happening.
  if jq -cn --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg section "$section" --arg what "$what" \
    '{ts:$ts, section:$section, what:$what}' >>"$ESCALATIONS"; then
    echo "recorded: contract section $section - $what"
    exit 0
  fi
  echo "escalation NOT recorded (could not write $ESCALATIONS)" >&2
  exit 1
fi

while [ $# -gt 0 ]; do
  case "$1" in
  --fast) FAST=1 ;;
  --resources-from)
    RESOURCES_FILE=${2:?--resources-from needs a file path}
    shift
    ;;
  --sample-seconds)
    SAMPLE_SECONDS=${2:?--sample-seconds needs a number}
    shift
    ;;
  -h | --help)
    # Stop at the first non-comment line so the range cannot drift as the
    # header grows.
    sed -n '2,${/^#/!q; s/^# \{0,1\}//p;}' "$0"
    exit 0
    ;;
  *)
    echo "unknown argument: $1" >&2
    exit 2
    ;;
  esac
  shift
done

refuse_tunable() {
  local name=$1 val=$2 lo=$3 hi=$4
  printf 'conductor-signals: %s must be a whole number from %d to %s, got: %s\n' \
    "$name" "$lo" "$hi" "$val" >&2
  exit 2
}

# validate_tunable VAR_NAME ENV_NAME MIN MAX
#   Checks the variable named by VAR_NAME (via nameref) for: digits-only, digit count bounded by
#   MAX, and value in [MIN, MAX] after base-10 normalisation. Refuses with exit 2 on any violation.
#   The digit-length check runs before normalisation (rejects pathologically long input); the value
#   check runs after (rejects out-of-range values even when digit count matches MAX). The ''
#   arm is carried even though every default uses :- (making empty unreachable today), because the
#   thing standing between this line and a silent bypass would otherwise be a two-character choice
#   (:- versus -) in the defaults above.
validate_tunable() {
  local -n _val=$1
  local name=$2 lo=$3 hi=$4
  case "$_val" in '' | *[!0-9]*) refuse_tunable "$name" "$_val" "$lo" "$hi" ;; esac
  [ "${#_val}" -le "${#hi}" ] || refuse_tunable "$name" "$_val" "$lo" "$hi"
  _val=$((10#$_val))
  [ "$_val" -ge "$lo" ] || refuse_tunable "$name" "$_val" "$lo" "$hi"
  [ "$_val" -le "$hi" ] || refuse_tunable "$name" "$_val" "$lo" "$hi"
}

# ALL SEVEN TUNABLES ARE VALIDATED HERE, unconditionally and above the signal logic. Placement
# matters: validation after argument parsing but before any work guarantees that --sample-seconds
# overrides are also checked, and the escalate subcommand (which uses none of these) exits before
# this point.
#
# LOAD_MAX is the dangerous one: if non-numeric, awk's (l>=lt) does string comparison. Since
# digits < letters in ASCII, load_high is always 0 -- the load guard is silently disabled, and
# dispatch proceeds under any load. The cap contract section 4 enforces the load limit, and a
# malformed threshold turns it off without anyone noticing.
#
# CAP, SWAP_VETO_MB, MEM_FREE_MIN_PCT, PR_LIMIT, PR_DAYS, and SAMPLE_SECONDS fail safe today
# (vetoing too aggressively, recording a coverage gap, or producing a garbage measurement that
# does not affect the dispatch decision), but each carries the same class of bug one edit away.
validate_tunable CAP                  CONDUCTOR_SIGNALS_CAP                  1 999
validate_tunable SWAP_VETO_MB         CONDUCTOR_SIGNALS_SWAP_VETO_MB         1 999999
validate_tunable MEM_FREE_MIN_PCT     CONDUCTOR_SIGNALS_MEM_FREE_MIN_PCT     1 100
validate_tunable LOAD_MAX             CONDUCTOR_SIGNALS_LOAD_MAX             1 999
validate_tunable PR_LIMIT             CONDUCTOR_SIGNALS_PR_LIMIT             1 999
validate_tunable PR_DAYS              CONDUCTOR_SIGNALS_PR_DAYS              1 999
validate_tunable SAMPLE_SECONDS       CONDUCTOR_SIGNALS_SAMPLE_SECONDS       1 999

days_ago() { # <n> <format> <fallback>
  date -u -v-"$1"d +"$2" 2>/dev/null ||
    date -u -d "$1 days ago" +"$2" 2>/dev/null ||
    printf '%s' "$3"
}

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Each signal carries how well it could be measured, and the NUMBER shows it.
#   ok       a real measurement          ->  5
#   floor    measured, but blind somewhere -> >=5
#   unknown  could not measure at all    ->  ?
#
# A zero that means "I did not look" is the failure this whole script exists to
# catch. Printing it as a bare 0 next to "target 0" reads as reassurance, which
# is worse than printing nothing.
S1_CONF=ok
S2_CONF=ok
S3_CONF=ok

render_count() { # <value> <confidence>
  case "$2" in
  floor) printf '>=%s' "$1" ;;
  unknown) printf '?' ;;
  *) printf '%s' "$1" ;;
  esac
}

# ---------------------------------------------------------------------------
# Shared reads, each taken exactly once
# ---------------------------------------------------------------------------

# Every bead that is not closed, as `id <TAB> title <TAB> prose`, with newlines
# flattened so one grep can reason about adjacency within a clause. Deferred
# beads are in scope: a merged PR closing an agent-proposed bead is the same
# failure as one closing an open bead.
#
# The `select` re-asserts bd's own --status filter. A closed bead reaching
# signal 1 would report the thing that went right as the failure.
# EVERY read below distinguishes "could not read" from "read a clean zero". A
# tool that is missing, locked, upgraded, or timing out must never render as an
# empty queue on a signal whose target IS zero. Observed live: one run reported
# 0 complete-but-open beads when the true answer was 5, because `bd list`
# returned a short array and nothing noticed.
: >"$TMP/gaps"

bd_json=$(bd list --status open,in_progress,blocked,deferred --json 2>/dev/null)
if [ -z "$bd_json" ] || ! jq -e 'type == "array" and length > 0' <<<"$bd_json" >/dev/null 2>&1; then
  echo "the bead queue: bd list returned nothing usable" >>"$TMP/gaps"
  # With no bead set there is nothing to match merged PRs against, so signal 1
  # is not a low number - it is no measurement.
  S1_CONF=unknown
  bd_json='[]'
fi
jq -r '.[] | select((.status // "") != "closed")
           | [.id, (.title // ""),
              ([(.description // ""), (.notes // "")] | join(" ") | gsub("[\r\n\t]"; " "))]
           | @tsv' <<<"$bd_json" 2>/dev/null >"$TMP/beads.tsv" || : >"$TMP/beads.tsv"

cut -f1 "$TMP/beads.tsv" | grep -v '^$' | sort -u >"$TMP/bead-ids"

# Hits the conductor has judged and chosen to keep open. Without this the one
# action the report recommends cannot silence the report, and a legitimately
# open bead becomes permanent noise - which is how a number stops being read.
# This read fails in the opposite direction from the others: losing it does not
# zero signal 1, it INFLATES it, because every hit already judged and dismissed
# comes back as if it were new. Neither >= nor ? describes that, so the gap line
# says it in words instead.
acked_json=$(bd list --label signal1-ack --json 2>/dev/null)
if [ -n "$acked_json" ] && jq -e 'type == "array"' <<<"$acked_json" >/dev/null 2>&1; then
  jq -r '.[].id' <<<"$acked_json" 2>/dev/null | sort -u >"$TMP/acked"
else
  : >"$TMP/acked"
  echo "the signal1-ack list (hits you already dismissed may reappear below)" >>"$TMP/gaps"
fi

# An unreadable session list is NOT zero sessions. Zero would mean the whole cap
# is free, so signal 2 would urge dispatch while real workers are running - the
# one direction that can actually break the cap contract section 4 enforces.
DECK_READABLE=1
if ! agent-deck list --json 2>/dev/null >"$TMP/deck.json" ||
  ! jq -e 'type == "array"' "$TMP/deck.json" >/dev/null 2>&1; then
  DECK_READABLE=0
  S2_CONF=unknown
  [ "$S1_CONF" = ok ] && S1_CONF=floor # live worker repos go undiscovered
  echo "the session list: agent-deck list returned nothing usable" >>"$TMP/gaps"
  echo '[]' >"$TMP/deck.json"
fi

bead_label() { # id -> "id - title", or flags that it is no longer open
  local t
  t=$(grep -m1 -F "$1"$'\t' "$TMP/beads.tsv" | cut -f2)
  if [ -n "$t" ]; then printf '%s - %s' "$1" "$t"; else printf '%s - (no longer open)' "$1"; fi
}

# ---------------------------------------------------------------------------
# SIGNAL 1: complete but open
# ---------------------------------------------------------------------------
#
# "Complete" is not a bd status, so it is inferred from a merged PR. One side or
# the other has to SAY SO. Two rules, both measured against the real queue:
#
#   pr-declares    the merged PR closes the bead in words ("Closes <id>")
#   bead-declares  the bead's own prose binds its closure to that PR number
#                  ("RESOLVED BY PR #6", "Do not close it until PR 142 merges")
#
# What is deliberately NOT a rule: a bead merely mentioned by a merged PR, or a
# bead merely mentioning a PR. Measured on the real queue, plain co-citation
# fired on 12 beads of which about 2 were genuinely complete - it is the
# signature of a follow-up, not of closure. Beads here cite PRs to say "raised
# against PR #142, NOT fixed on that branch" and "(PR #27) DOES NOT RESOLVE THIS
# BEAD", and PR bodies cite beads to record follow-ups they filed.

id_boundary() {
  # A bead id ends at a non-id character, but a dot followed by a digit is part
  # of the id: `-w45` must not match inside `-w45.20`.
  #
  # The id is ESCAPED before it becomes a pattern. Real ids carry dots, and an
  # unescaped dot is a wildcard: `-fx.9` otherwise matched `-fxA9` and `-fxZ9`,
  # so an unrelated token in the same PR could confirm a closure that was never
  # declared.
  printf '%s($|[^A-Za-z0-9.-]|\\.([^0-9]|$))' \
    "$(sed -E 's/[][(){}.*+?^$|\\]/\\&/g' <<<"$1")"
}

CLOSURE_VERBS='(clos(e|es|ed|ing)|fixes|fixed|resolv(e|es|ed))'
# Bare "fix" is excluded on purpose. It carries no completion claim: it opens
# every conventional-commit subject, and it is the word in "PARTIAL fix for
# <id>" - a real merged PR whose bead is legitimately still open.

# Both boundaries matter, and each side was a measured defect.
#   - A leading `[^A-Za-z]` stops "Reno closes <id>" and "Cabinet closes <id>"
#     from reading as denials.
#   - `n't` replaces an earlier `n.t`, which matched "net"/"nat"/"nut". bd mints
#     random id suffixes, so `jbrooksbartlett-9net closed by PR #12` was being
#     silently suppressed - a false negative on the signal that must not miss.
#   - `cannot` and `unable` are separate words, not reachable through `not`:
#     switchboard PR #30 quotes a UI error, "cannot close jbrooksbartlett-0s2:
#     7 open child issue(s); close children first", and that bead has seven open
#     children. Caught by running against the live queue, not by the suite.
NEGATORS="((^|[^A-Za-z])(not|never|without|no|cannot|unable)|n't)"

# Split prose into clauses so a denial in one sentence cannot veto a declaration
# in another. Measured: bead whd0 says "RESOLVED BY switchboard PR #27" AND, far
# away, "...cannot resolve which. WHY PR #27..." - a whole-document negation
# guard silenced a genuine hit on an unrelated phrase.
#
# A dot followed by a digit is NOT a clause break, because bead ids carry dots
# (`-w45.20`) and splitting there would make `-w45` match inside it.
clauses() { sed -E 's/(;)/\1\n/g; s/(\.)([^0-9])/\1\n\2/g' <<<"$1"; }

# Does some clause of <clause-split text> declare that this PR closes this target?
#   $1 text, already one clause per line   $2 the target ERE   $3 the ERE
#   allowed between the closure verb and the target
#
# grep is line-oriented, so the clause rule is enforced by the split alone. Doing
# this as three greps over the whole set rather than a shell loop per clause
# matters: the loop form took 2m43s on the real queue, this takes seconds.
declares_closure() {
  local hits
  hits=$(grep -iE "${CLOSURE_VERBS}$3$2" <<<"$1") || return 1
  # A clause carrying no denial is a declaration. A real merged PR reads "This
  # is a PARTIAL fix. It does not close jbrooksbartlett-av0."
  #
  # One word may sit between the negator and the verb, because English puts one
  # there: "does not ACTUALLY close", "does not FULLY resolve" both slipped past
  # a strictly adjacent guard. Two would be too greedy - "no changes were
  # needed, closes <id>" is a declaration, not a denial.
  grep -qvE "${NEGATORS}[[:space:]]+([A-Za-z]+[[:space:]]+)?${CLOSURE_VERBS}" -i <<<"$hits" && return 0
  # Every candidate clause was negated - except that "Do not close it until PR
  # 142 merges" is a pending closure whose condition the merge has now met, and
  # it is how this queue actually records one.
  grep -qiE "${CLOSURE_VERBS}[^0-9]{0,20}until[^0-9]{0,20}$2" <<<"$hits"
}

pr_declares() { # <pr clauses> <bead id boundary>
  declares_closure "$1" "$2" "[[:space:]:]*[\`\"'([]*"
}

bead_declares() { # <bead clauses> <pr number>
  # The verb has to come BEFORE the reference and stay within one clause of it,
  # so "(PR #27) DOES NOT RESOLVE THIS BEAD" cannot fire.
  declares_closure "$1" "(PR[[:space:]]*#?|pull/)0*$2([^0-9]|\$)" "[^0-9]{0,40}"
}

# Live worker repos join the search set for this run only.
while IFS= read -r p; do
  [ -z "$p" ] && continue
  case ":$REPOS:" in *":$p:"*) ;; *) REPOS="$REPOS:$p" ;; esac
done < <(jq -r '.[] | select(.path != null) | .path' "$TMP/deck.json" 2>/dev/null |
  sed -n 's#\(.*\)/\.\{0,1\}worktrees/.*#\1#p' | sort -u)

collect_merged_prs() {
  local since seen=":" path i=0
  since=$(days_ago "$PR_DAYS" %Y-%m-%dT%H:%M:%SZ 1970-01-01T00:00:00Z)

  # Read into an array rather than word-splitting. `for path in ${REPOS//:/ }`
  # split `/Users/me/My Repo` into two fragments, neither of which exists, so
  # the repo vanished from signal 1 with no warning at all.
  local repo_list
  IFS=: read -ra repo_list <<<"$REPOS"

  # The repos are independent network round trips, so fan them out.
  for path in "${repo_list[@]}"; do
    [ -n "$path" ] || continue
    case "$seen" in *":$path:"*) continue ;; esac
    seen="$seen$path:"
    if [ ! -d "$path" ]; then
      # A configured path that does not exist is a coverage hole, not a no-op.
      echo "$path (no such directory)" >>"$TMP/gaps"
      : >"$TMP/s1-blind"
      continue
    fi
    basename "$path" >"$TMP/repo.$i"
    # The cd runs INSIDE the subshell so a failure can record itself. Written as
    # `cd "$path" && gh ... >"$TMP/prs.$i" &`, a cd failure short-circuits before
    # the redirect, so no file is created, the collector loop skips the repo, and
    # signal 1 reports a confident 0 having searched nothing. Reproduced with a
    # chmod 000 repo directory.
    (
      if cd "$path" 2>/dev/null; then
        gh pr list --state merged --limit "$PR_LIMIT" \
          --json number,title,body,headRefName,mergedAt >"$TMP/prs.$i" 2>/dev/null
      else
        echo "$path (could not enter directory)" >>"$TMP/gaps"
        : >"$TMP/s1-blind"
      fi
    ) &
    i=$((i + 1))
  done
  wait

  for f in "$TMP"/prs.*; do
    # With no matches the glob yields its own literal text, which then reports
    # an unreadable repo whose name is the empty string.
    [ -e "$f" ] || continue
    # A repo whose PR list could not be read contributes nothing, and "GHE was
    # unreachable" must never read as "no complete-but-open beads". GHE was down
    # for ~16 hours on 2026-08-15/16; that must show as a gap, not a clean 0.
    if ! jq -e . "$f" >/dev/null 2>&1; then
      printf '%s (could not list merged PRs)\n' \
        "$(cat "$TMP/repo.${f##*/prs.}" 2>/dev/null)" >>"$TMP/gaps"
      : >"$TMP/s1-blind"
      continue
    fi
    jq -r --arg repo "$(cat "$TMP/repo.${f##*/prs.}")" --arg since "$since" \
      '.[] | select((.mergedAt // "") >= $since)
           | [$repo, (.number | tostring), (.mergedAt // "")[0:10],
              ([(.title // ""), (.headRefName // ""), (.body // "")] | join(" ") | gsub("[\r\n\t]"; " "))]
           | @tsv' "$f" 2>/dev/null
  done
}

: >"$TMP/signal1"
while IFS=$'\t' read -r repo number merged prtext; do
  [ -z "$number" ] && continue
  prclauses=$(clauses "$prtext")

  # Candidate ids: every non-closed bead id the PR text contains.
  while IFS= read -r bead; do
    [ -z "$bead" ] && continue
    grep -qxF "$bead" "$TMP/acked" && continue

    bound=$(id_boundary "$bead")
    # grep -F ignores word boundaries, so `-w45` surfaces inside `-w45.20`.
    grep -qE "$bound" <<<"$prtext" || continue

    row=$(grep -m1 -F "$bead"$'\t' "$TMP/beads.tsv") || continue
    IFS=$'\t' read -r _ title beadtext <<<"$row"

    # One bead is usually a candidate of several PRs; split its prose once.
    [ -s "$TMP/bc.$bead" ] || clauses "$beadtext" >"$TMP/bc.$bead"

    why=""
    pr_declares "$prclauses" "$bound" && why="pr-declares"
    bead_declares "$(cat "$TMP/bc.$bead")" "$number" && why="${why:+$why+}bead-declares"
    [ -z "$why" ] && continue

    printf '%s\t%s\t%s#%s\t%s\t%s\n' "$bead" "$why" "$repo" "$number" "$merged" "$title" \
      >>"$TMP/signal1"
  done < <(grep -oFf "$TMP/bead-ids" <<<"$prtext" 2>/dev/null | sort -u)
done < <(collect_merged_prs)

# collect_merged_prs runs inside a process substitution, so anything it assigns
# to a variable is lost with that subshell. It leaves a marker file instead, and
# the parent reads it back here.
[ -e "$TMP/s1-blind" ] && [ "$S1_CONF" = ok ] && S1_CONF=floor

sort -u -k1,1 "$TMP/signal1" >"$TMP/signal1.sorted"

# The dependent count has to come from `bd show`, which accepts every id in one
# call. `bd list --json` emits the key with a plausible 0 for every bead - on a
# bead `bd show` reports 6 dependents for - so the bulk read would present every
# blockage as costless. Filed as jbrooksbartlett-n9x6.
: >"$TMP/deps.tsv"
if [ -s "$TMP/signal1.sorted" ]; then
  # shellcheck disable=SC2046
  bd show $(cut -f1 "$TMP/signal1.sorted" | tr '\n' ' ') --json 2>/dev/null |
    jq -r '.[] | [.id, ((.dependent_count // 0) | tostring)] | @tsv' 2>/dev/null >"$TMP/deps.tsv"
fi

S1=$(wc -l <"$TMP/signal1.sorted" | tr -d ' ')

# ---------------------------------------------------------------------------
# SIGNAL 2: ready, dispatchable work idle while capacity is free
# ---------------------------------------------------------------------------

ready_json=$(bd ready --exclude-type=epic --json 2>/dev/null)
if [ -n "$ready_json" ] && READY=$(jq -e 'length' <<<"$ready_json" 2>/dev/null); then
  :
else
  echo "the ready queue: bd ready returned nothing usable" >>"$TMP/gaps"
  S2_CONF=unknown
  READY=0
fi

# Contract section 4: a session is Active or Parked, and Parked - a PR open
# awaiting review - does not count against the cap. The open-PR lookups are
# independent network calls, so they fan out too.
# A session agent-deck reports as alive must never fall out of the accounting.
# It used to: `[ -z "$branch" ] && continue`, and a `cd` failure short-circuiting
# before the redirect, both dropped the session before any openpr file existed,
# so it counted as neither active nor parked. Measured with one running worker
# whose directory was not a git repo: "active 0 of cap 3 ... Dispatch 3 now",
# which would have put four workers against a cap of three.
n=0
UNCLASSIFIED=0
while IFS= read -r spath; do
  [ -z "$spath" ] && continue
  case "$spath" in *worktrees/*) ;; *) continue ;; esac
  branch=""
  [ -d "$spath" ] && branch=$(git -C "$spath" rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [ -z "$branch" ]; then
    # Cannot ask whether it is parked, so assume it is working: over-counting
    # active holds the cap, under-counting breaks it.
    UNCLASSIFIED=$((UNCLASSIFIED + 1))
    echo "a worker session at $spath (no branch resolved, counted as active)" >>"$TMP/gaps"
    continue
  fi
  (
    cd "$spath" 2>/dev/null &&
      gh pr list --head "$branch" --state open --json number >"$TMP/openpr.$n" 2>/dev/null
  ) &
  n=$((n + 1))
done < <(jq -r '.[] | select((.status // "") != "stopped" and (.status // "") != "error") | .path // ""' \
  "$TMP/deck.json" 2>/dev/null)
wait

ACTIVE=0
PARKED=0
for f in "$TMP"/openpr.*; do
  [ -e "$f" ] || continue
  # Asking "is the array empty" does not need a jq process.
  case "$(cat "$f")" in
  *'"number"'*) PARKED=$((PARKED + 1)) ;;
  *) ACTIVE=$((ACTIVE + 1)) ;;
  esac
done

# Sessions that could not be classified still occupy the machine.
ACTIVE=$((ACTIVE + UNCLASSIFIED))
# Counting it active under-estimates free capacity, so signal 2 is a floor: if
# that session turns out to be parked, the true number is higher, never lower.
[ "$UNCLASSIFIED" -gt 0 ] && [ "$S2_CONF" = ok ] && S2_CONF=floor

# If the session list could not be read, ACTIVE=0 is not "the cap is free", it
# is "unknown". Treating unknown as free is the one error that can push the rig
# past the cap of 3, so it counts as fully occupied instead.
[ "$DECK_READABLE" = 0 ] && ACTIVE=$CAP

FREE=$((CAP - ACTIVE))
[ "$FREE" -lt 0 ] && FREE=0

read_resources() {
  if [ -n "$RESOURCES_FILE" ]; then
    cat "$RESOURCES_FILE" 2>/dev/null
    return
  fi
  local mem swap load a b delta sampled
  mem=$(memory_pressure 2>/dev/null | sed -n 's/.*free percentage: \([0-9]*\)%.*/\1/p' | tail -1)
  swap=$(sysctl -n vm.swapusage 2>/dev/null | sed -n 's/.*free = \([0-9.]*\)M.*/\1/p')
  load=$(uptime | sed -n 's/.*load averages\{0,1\}: \([0-9.]*\).*/\1/p')
  if [ "$FAST" = 1 ]; then
    delta=-1
    sampled=false
  else
    a=$(vm_stat | awk '/Swapouts/{print $2}' | tr -d '.')
    sleep "$SAMPLE_SECONDS"
    b=$(vm_stat | awk '/Swapouts/{print $2}' | tr -d '.')
    delta=$((b - a))
    sampled=true
  fi
  jq -cn --arg mem "${mem:-}" --arg swap "${swap:-}" --arg load "${load:-}" \
    --argjson delta "$delta" --argjson sampled "$sampled" \
    '{mem_free_pct:$mem, swap_free_mb:$swap, load1:$load, swapouts_delta:$delta, sampled:$sampled}'
}

RES=$(read_resources)
IFS=$'\t' read -r MEM SWAP LOAD DELTA SAMPLED < <(
  jq -r '[(.mem_free_pct // ""), (.swap_free_mb // ""), (.load1 // ""),
          (.swapouts_delta // -1), (.sampled // false)] | @tsv' <<<"$RES" 2>/dev/null
)

# An unreadable reading must not look like a healthy one. Before this guard a
# changed `memory_pressure` wording parsed to empty, defaulted to 0, and became
# a permanent silent veto indistinguishable from real exhaustion - or, with the
# thresholds skipped entirely, let signal 2 fire having checked nothing.
veto_reasons=""
unreadable=""
is_num() { [[ $1 =~ ^[0-9]+([.][0-9]+)?$ ]]; }
is_num "${MEM:-}" || unreadable="$unreadable memory"
is_num "${SWAP:-}" || unreadable="$unreadable swap"
is_num "${LOAD:-}" || unreadable="$unreadable load"
[[ ${DELTA:-} =~ ^-?[0-9]+$ ]] || DELTA=-1

SWAP_LOW=0
if [ -n "$unreadable" ]; then
  veto_reasons=" UNREADABLE:$unreadable"
  S2_CONF=unknown
  echo "the capacity read:$unreadable" >>"$TMP/gaps"
else
  read -r mem_low swap_low load_high < <(awk -v m="$MEM" -v s="$SWAP" -v l="$LOAD" \
    -v mt="$MEM_FREE_MIN_PCT" -v st="$SWAP_VETO_MB" -v lt="$LOAD_MAX" \
    'BEGIN{print (m<mt), (s<st), (l>=lt)}')
  [ "$mem_low" = 1 ] && veto_reasons="$veto_reasons memory-free-${MEM}%"
  [ "$swap_low" = 1 ] && veto_reasons="$veto_reasons swap-free-${SWAP}M"
  [ "$load_high" = 1 ] && veto_reasons="$veto_reasons load-${LOAD}"
  SWAP_LOW=$swap_low
fi

S2=0
if [ -z "$veto_reasons" ] && [ "$FREE" -gt 0 ]; then
  S2=$READY
  [ "$S2" -gt "$FREE" ] && S2=$FREE
fi

# ---------------------------------------------------------------------------
# SIGNAL 3: escalations the contract says the conductor should have decided
# ---------------------------------------------------------------------------

TODAY=$(date -u +%Y-%m-%d)
S3=0
S3_SECTIONS=""
S3_PRIOR_N=0
if [ -e "$ESCALATIONS" ] && [ ! -r "$ESCALATIONS" ]; then
  S3_CONF=unknown
  echo "the escalation log (unreadable)" >>"$TMP/gaps"
elif [ -s "$ESCALATIONS" ]; then
  IFS=$'\t' read -r S3 S3_PRIOR_N S3_SECTIONS < <(
    jq -rs --arg today "$TODAY" --arg from "$(days_ago 7 %Y-%m-%d "$TODAY")" '
      map(select(.ts != null)) as $all
      | ($all | map(select(.ts[0:10] == $today))) as $t
      | [ ($t | length),
          ($all | map(select(.ts[0:10] >= $from and .ts[0:10] < $today)) | length),
          ($t | map(.section) | unique | map("section " + .) | join(", ")) ]
      | @tsv' "$ESCALATIONS" 2>/dev/null
  )
fi
# A log that exists but does not parse is not "no escalations today". Coercing
# it to 0 here would put the same lie back that the guards above remove.
if [ -s "$ESCALATIONS" ] && ! [[ ${S3:-} =~ ^[0-9]+$ ]]; then
  S3_CONF=unknown
  echo "the escalation log (could not be parsed)" >>"$TMP/gaps"
fi
[[ ${S3:-} =~ ^[0-9]+$ ]] || S3=0
[[ ${S3_PRIOR_N:-} =~ ^[0-9]+$ ]] || S3_PRIOR_N=0
S3_PRIOR=$(awk -v n="$S3_PRIOR_N" 'BEGIN{printf "%.1f", n/7}')

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

printf 'CONDUCTOR SIGNALS  %s   (work contract section 10)\n\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Printed FIRST, because it governs all three numbers below. Joined with awk:
# `paste -sd', '` treats the delimiter as a ROUND-ROBIN LIST ("a,b c"), and a
# tr/sed pair on an escape character is worse - BSD sed reads \a as the letter a
# and rewrote "bead queue" to "be, d queue".
if [ -s "$TMP/gaps" ]; then
  printf 'NOT A CLEAN READ: %s.\n' \
    "$(sort -u "$TMP/gaps" | awk 'NR>1{printf ", "} {printf "%s", $0}')"
  printf 'A number below reading >=N is a FLOOR; ? means it could not be measured at all.\n\n'
fi

printf '1  complete-but-open .......... %-4s target 0\n' "$(render_count "$S1" "$S1_CONF")"
if [ "$S1" -gt 0 ]; then
  while IFS=$'\t' read -r bead why pr merged title; do
    deps=$(grep -m1 -F "$bead"$'\t' "$TMP/deps.tsv" | cut -f2)
    # id and title on ONE line. A line lifted out of this report and pasted into
    # a message to Jonny must not be a bare id (work contract section 3).
    printf '     %s - %s\n' "$bead" "$title"
    printf '       %s  %s merged %s   %s dependents blocked\n' \
      "[$why]" "$pr" "$merged" "${deps:-?}"
  done <"$TMP/signal1.sorted"
  printf '     Each is a worklist entry, not a verdict: close it, record why the merge did not\n'
  printf '     finish it, or silence it with  bd label add <id> signal1-ack\n'
fi
printf '     BLIND SPOT: only beads whose deliverable is a PR. Research, document and operator\n'
printf '     beads complete without one and are invisible here. See %s\n' "$(bead_label jbrooksbartlett-uixd)"

printf '\n2  dispatchable-now ........... %-4s target 0\n' "$(render_count "$S2" "$S2_CONF")"
printf '     ready(non-epic) %s | active %s of cap %s | parked %s (not counted, contract s4)\n' \
  "$READY" "$ACTIVE" "$CAP" "$PARKED"
if [ "$SAMPLED" = "true" ]; then
  sample_note="swapouts delta $DELTA over ${SAMPLE_SECONDS}s"
else
  sample_note="swapouts delta NOT SAMPLED (--fast), so the check below could not run"
fi
printf '     contract read: memory %s%% free, swap %sM free, load %s   |   live read: %s\n' \
  "${MEM:-?}" "${SWAP:-?}" "${LOAD:-?}" "$sample_note"
if [ -n "$veto_reasons" ]; then
  printf '     VETOED:%s\n' "$veto_reasons"
fi
if [ "$SWAP_LOW" = 1 ] && [ "$SAMPLED" = "true" ] && [ "$DELTA" -le 0 ]; then
  printf '     READINGS DISAGREE: swap-free vetoes but swapouts delta is %s, so the machine is not\n' "$DELTA"
  printf '     paging. swap-free is a high-water mark. The threshold Jonny agreed still governs\n'
  printf '     this run; the proposal to change it is %s\n' "$(bead_label jbrooksbartlett-cjxs)"
fi
if [ "$S2" -gt 0 ]; then
  printf '     Dispatch %s now. Contract s3: ready means dispatch - no approval, no announcement-and-wait.\n' "$S2"
fi

printf '\n3  escalations ................ %-4s today  (prior 7d: %s/day, target trending down)\n' \
  "$(render_count "$S3" "$S3_CONF")" "$S3_PRIOR"
if [ "$S3" -gt 0 ]; then
  printf '     should have applied: %s\n' "$S3_SECTIONS"
fi
printf '     Record one with: conductor-signals.sh escalate <section> "<what it was>"\n'
