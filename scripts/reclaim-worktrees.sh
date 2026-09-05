#!/usr/bin/env bash
#
# reclaim-worktrees.sh - the weekly SCHEDULED RECLAMATION, as a job.
#
# Contract: docs/conductor-work-contract.md section 4, "SCHEDULED RECLAMATION".
# Operator guide: docs/reclamation.md. Bead: jbrooksbartlett-e1ak.
# The measurements this design rests on, with verbatim probe output:
#   ~/evidence/jbrooksbartlett-e1ak/measurements-2026-08-19.md
#
#   ./reclaim-worktrees.sh --dry-run             classify everything, change nothing
#   ./reclaim-worktrees.sh                       the weekly run
#   ./reclaim-worktrees.sh --if-due              the weekly run, but only if one is overdue
#   ./reclaim-worktrees.sh --install-schedule    register the launchd job
#   ./reclaim-worktrees.sh --uninstall-schedule  remove it again
#
# Also: --no-caches (skip the cache pass), --root DIR
# (replace the search roots, repeatable), --maxdepth N, --evidence-dir DIR, and --sessions-from
# FILE (read a captured agent-deck registry instead of asking it). RECLAIM_DUE_AFTER_DAYS sets
# the --if-due window (default 6).
#
# WHY THIS EXISTS. On 2026-08-19 the disk reached 136 MB free on a 460 GB volume and every
# session's writes began failing. Of 35 worktrees audited, 34 needed no rescue at all: 25
# belonged to MERGED pull requests, 7 were stale auto-created copies, 2 were live sessions.
# Exactly one held uncommitted work. A manual sweep that same morning cleaned two repositories,
# reported the job done, and missed 45 GB in a third - because it had been scoped BY REPOSITORY
# from memory rather than sweeping all of them. Disk free went 49 GB -> 114 GB on the second
# pass. THAT is the argument for a job: a human sweeping from memory misses whole repositories.
#
# THE SAFETY ARGUMENT, and it is the whole design: removing a worktree does NOT delete its
# branch or its commits. Those live in the repository's object store and survive - verified on
# 2026-08-19 across all 35 removals. Only UNCOMMITTED files are ever at risk. So this job is
# safe if and only if it
#
#   (a) never touches a path held by a live agent-deck session, and
#   (b) rescues uncommitted work before it considers removing anything.
#
# Everything else is mechanical. Two consequences worth stating because reviewers ask:
#
#   - Unpushed commits are NOT checked, and do not need to be. A branch ahead of master keeps
#     its commits after its worktree is gone. Checking commit counts would also be the wrong
#     test for the wrong question: a squash-merged branch still reads as ahead of master, which
#     is why pull request STATE is what decides removal here, never a commit count.
#   - `git worktree remove` is called WITHOUT --force. Measured on git 2.54.0: a worktree
#     holding only gitignored paths (a 200 MB node_modules) removes cleanly, while one holding
#     an untracked or modified file is refused with "contains modified or untracked files".
#     The gigabytes are all in the first case, so declining to force costs no disk - it only
#     protects the dirty worktrees, where git's own refusal becomes a second line of defence
#     behind this script's own dirty check. The 2026-08-19 manual sweep forced all 35; it did
#     not need to.
#
# IT REPORTS WHAT IT DID NOT DO. Every worktree it kept is named with the reason, every
# repository it could not read is named, and every capped or failed lookup downgrades the
# verdict to "undetermined" rather than passing silently. A cleanup that reports success having
# examined half the machine is the defect class this codebase produces most often; the whole
# bottom half of the report exists to make that impossible to do quietly.

set -uo pipefail

if [ "${BASH_VERSINFO[0]:-0}" -lt 4 ] ||
   { [ "${BASH_VERSINFO[0]:-0}" -eq 4 ] && [ "${BASH_VERSINFO[1]:-0}" -lt 3 ]; }; then
  echo "reclaim-worktrees: needs bash 4.3+ (macOS /bin/bash is 3.2; try /opt/homebrew/bin/bash)" >&2
  exit 2
fi

SELF_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SELF="$SELF_DIR/$(basename "${BASH_SOURCE[0]}")"

# ---------------------------------------------------------------------------
# Configuration. Every path is overridable so the suite can run the real code
# against real git repositories without touching the real machine.
# ---------------------------------------------------------------------------

EVIDENCE_ROOT=${RECLAIM_EVIDENCE_ROOT:-$HOME/evidence}
MAXDEPTH=${RECLAIM_MAXDEPTH:-4}

# How long a worktree with NO pull request must have sat untouched before it is reclaimed. Jonny set
# the rule and this number on 2026-08-19; it is now the fourth row of the contract's SCHEDULED
# RECLAMATION table (jbrooksbartlett-e6ne), which had no rule for the class before that.
# See the NONE branch of the sweep for the argument that it is as safe as the merged-PR rule.
NO_PR_MIN_AGE_DAYS=${RECLAIM_NO_PR_MIN_AGE_DAYS:-14}

# A rescue larger than this is not attempted, and says so. Nothing is lost when it trips: a
# dirty worktree is kept in place either way, so the copy is belt-and-braces, not the only copy.
RESCUE_MAX_BYTES=${RECLAIM_RESCUE_MAX_BYTES:-536870912} # 512 MiB

LAUNCHD_LABEL=${RECLAIM_LAUNCHD_LABEL:-com.jonnybrooks.reclaim-worktrees}
LAUNCHD_DIR=${RECLAIM_LAUNCHD_DIR:-$HOME/Library/LaunchAgents}

DRY_RUN=0
DO_CACHES=1
SESSIONS_FILE=""
ROOTS=()

# --if-due: sweep only if the last COMPLETED run is older than the window. The launchd job passes
# it; nothing else does, so a run started by hand is never suppressed. See "The catch-up guard".
IF_DUE=0
DUE_AFTER_DAYS=${RECLAIM_DUE_AFTER_DAYS:-6}

usage() {
  # Stop at the first non-comment line so the range cannot drift as the header grows.
  sed -n '2,${/^#/!q; s/^# \{0,1\}//p;}' "$SELF"
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

ACTION=run

while [ $# -gt 0 ]; do
  case "$1" in
  --dry-run) DRY_RUN=1 ;;
  --if-due) IF_DUE=1 ;;
  --no-caches) DO_CACHES=0 ;;
  --root)
    ROOTS+=("${2:?--root needs a directory}")
    shift
    ;;
  --evidence-dir)
    EVIDENCE_ROOT=${2:?--evidence-dir needs a directory}
    shift
    ;;
  --sessions-from)
    SESSIONS_FILE=${2:?--sessions-from needs a file of agent-deck JSON}
    shift
    ;;
  --maxdepth)
    MAXDEPTH=${2:?--maxdepth needs a number}
    shift
    ;;
  --install-schedule) ACTION=install ;;
  --uninstall-schedule) ACTION=uninstall ;;
  -h | --help)
    usage
    exit 0
    ;;
  *)
    echo "unknown argument: $1" >&2
    echo "try --help" >&2
    exit 2
    ;;
  esac
  shift
done

# Roots are REPLACED by --root, never appended to. A suite that meant to point the job at a
# fixture and instead pointed it at a fixture PLUS the whole home directory would delete real
# worktrees while reporting a green test.
if [ ${#ROOTS[@]} -eq 0 ]; then
  ROOTS=("$HOME")
fi

RESCUE_ROOT="$EVIDENCE_ROOT/rescued-worktree-files"
LOG_DIR="$EVIDENCE_ROOT/reclamation"
# The durable record of directories known to be unreadable. Only NEW ones raise a gap;
# see discover_repos for why a constant warning destroys the gap list it lives in.
UNREADABLE_BASELINE="$LOG_DIR/unreadable-baseline.txt"
# WHEN THE LAST SWEEP FINISHED, and the only thing --if-due is allowed to read. It lives here,
# beside the reports and the unreadable baseline, for three reasons that each rule out somewhere
# else: it survives a reboot (so not $TMPDIR, which is where a missed week would be re-missed),
# it is outside every git repository (so no checkout, `git clean` or worktree removal can take
# it - and note that THIS JOB SWEEPS ~/.claude ITSELF, so state kept in the repo would be state
# the job can delete out from under its own guard), and it moves with --evidence-dir, so the
# suite fences it in rather than clobbering the real machine's record.
LAST_RUN_FILE="$LOG_DIR/last-run"

# ---------------------------------------------------------------------------
# The launchd schedule
# ---------------------------------------------------------------------------
#
# Sunday 03:00, PLUS at load, guarded by --if-due.
#
# ASLEEP AT 03:00 IS FINE: launchd starts the job at the next wake, which in practice means Monday
# morning - the moment disk pressure matters most, because that is when a week of dispatches
# starts. The job is safe whenever it runs, so that drift costs nothing.
#
# POWERED OFF AT 03:00 IS NOT FINE, and this is what RunAtLoad is here for. The occurrence is
# skipped outright and the next run is the FOLLOWING Sunday: no error, no log line, nothing to
# notice, and a week of reclamation that silently did not happen. `man launchd.plist` documents
# only the sleep case; `launchctl print` shows why the powered-off case differs - the schedule is
# a `com.apple.launchd.calendarinterval` event stream monitored by UserEventAgent, which exists
# only for the boot session it is in, so an occurrence with no session to fire into is simply
# gone. RunAtLoad gives the job a second trigger that a power cycle cannot miss, because loading
# the agent is the first thing the next login does.
#
# WHY --if-due IS PASSED IN THE PLIST AND NOT LEFT OUT. Logins are frequent and this job DELETES
# DIRECTORIES; an unguarded RunAtLoad would sweep several times a day. --if-due makes the run
# conditional on the last COMPLETED run being older than the window.
#
# launchd has ONE ProgramArguments per job and no way to tell a job which trigger started it, so
# the flag applies to the calendar occurrence too. That is deliberate and it self-corrects: 7 days
# between Sundays always reaches the 6-day window, so a normal weekly run is never
# suppressed, and if a login catch-up ran on the Saturday, the Sunday occurrence 1 day later is
# correctly skipped - that week has already been swept, and the Sunday after is 8 days out and due.
#
# WHY NOT XPC ACTIVITY, which does express "every N seconds, catching up" directly. It is real -
# LaunchEvents > com.apple.xpc.activity > {Interval, Repeating, Priority}, used by
# com.apple.applessdstatistics and other system daemons on this machine - but `man launchd.plist`
# is explicit that with LaunchEvents "the job promises to use the xpc_set_event_stream_handler(3)
# API to consume events", and a bash script cannot call it or mark an activity done. It also
# replaces a fixed 03:00 with an opaque tolerance window at the system's discretion, and
# `launchctl` has no verb that fires an activity, so it could not be verified the way every other
# change to this job has been: by installing a temporary copy and firing it. Rejected on the API
# requirement, not on taste. (`pmset repeat wakeorpoweron` is the other real option and it powers
# the machine on at 02:55 - a change to the laptop, not to this job. Out of scope.)

plist_path() { printf '%s/%s.plist' "$LAUNCHD_DIR" "$LAUNCHD_LABEL"; }

write_plist() { # <destination>
  # The script path is templated into an executable file, so it has to be absolute: launchd has
  # no shell, no PATH resolution for ProgramArguments[1], and no working directory of its own.
  case "$SELF" in
  /*) ;;
  *)
    echo "refusing to install: the script path is not absolute ($SELF)" >&2
    return 1
    ;;
  esac

  # THE LABEL GOES STRAIGHT INTO XML THAT LAUNCHD PARSES AND EXECUTES, so validate it first. It
  # comes from RECLAIM_LAUNCHD_LABEL and went unchecked before 2026-08-20, when a review
  # reproduced a label of the form
  #   com.x</string><key>RunAtLoad</key><true/><key>Injected</key><string>proof
  # which yields a plist that is still VALID (confirmed with both `xmllint --noout` and
  # `plutil -lint`) carrying an injected RunAtLoad key that was never in this template. A
  # MALFORMED payload would have been caught by the launchctl verification below; a well-formed
  # one would not, and the result is an attacker-shaped scheduled job wearing this script's name.
  case "$LAUNCHD_LABEL" in
  '' | *[!A-Za-z0-9._-]*)
    printf 'refusing to install: the launchd label may contain only letters, digits, dot,\n' >&2
    printf 'underscore and hyphen, because it is written into an XML plist that launchd runs.\n' >&2
    printf 'Got: %s\n' "$LAUNCHD_LABEL" >&2
    return 1
    ;;
  esac
  mkdir -p "$(dirname "$1")" "$LOG_DIR" || return 1
  cat >"$1" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LAUNCHD_LABEL</string>

    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/bash</string>
        <string>$SELF</string>
        <string>--if-due</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$LOG_DIR/launchd.log</string>

    <key>StandardErrorPath</key>
    <string>$LOG_DIR/launchd.log</string>

    <key>WorkingDirectory</key>
    <string>$HOME</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>$HOME</string>
    </dict>

    <key>LowPriorityIO</key>
    <true/>

    <key>Nice</key>
    <integer>5</integer>
</dict>
</plist>
PLIST
}

install_schedule() {
  local plist
  plist=$(plist_path)
  write_plist "$plist" || return 1

  # bootout first so a re-install replaces rather than silently keeping the old definition.
  launchctl bootout "gui/$(id -u)/$LAUNCHD_LABEL" >/dev/null 2>&1
  launchctl bootstrap "gui/$(id -u)" "$plist" >/dev/null 2>&1 ||
    launchctl load "$plist" >/dev/null 2>&1

  # VERIFY, rather than trust the exit code. An install that wrote a plist nobody loaded is a
  # schedule that never fires, and it looks exactly like one that does. This is the positive
  # marker: launchctl listing the label is a signal only a real registration produces.
  if launchctl list "$LAUNCHD_LABEL" >/dev/null 2>&1; then
    printf 'scheduled: %s\n' "$LAUNCHD_LABEL"
    printf '  plist   %s\n' "$plist"
    printf '  when    Sundays 03:00, or the next wake if the machine was asleep\n'
    printf '  also    at load, so a Sunday missed with the machine POWERED OFF is caught up -\n'
    printf '          but only when it has not run in the last %s days (--if-due)\n' \
      "$DUE_AFTER_DAYS"
    printf '  record  %s\n' "$LAST_RUN_FILE"
    printf '  log     %s/launchd.log\n' "$LOG_DIR"
    printf '  reports %s/reclaim-<timestamp>.md\n' "$LOG_DIR"
    # BECAUSE RunAtLoad IS TRUE, `launchctl bootstrap` STARTS THE JOB - installing is no longer
    # inert until Sunday. Measured 2026-08-21 while building this: a probe install registered the
    # label and launchd started the script the same second. UNCONDITIONAL on purpose: an OLD record
    # also means a sweep is about to run, so a note gated on the record being MISSING would go
    # quiet in one of the two cases it exists to announce.
    printf '\n  NOTE: RunAtLoad means launchd has just STARTED this job. If it was due it is\n'
    printf '  sweeping for real right now; if not, it logged NOT DUE and stopped. Either way the\n'
    printf '  answer is the END of the log, which launchd APPENDS to and never truncates:\n'
    printf '    tail -n 20 %s/launchd.log\n' "$LOG_DIR"
    return 0
  fi
  printf 'INSTALL FAILED: %s was written but launchctl does not list %s.\n' \
    "$plist" "$LAUNCHD_LABEL" >&2
  printf 'The job would never have fired. Try:  launchctl bootstrap gui/%s %s\n' \
    "$(id -u)" "$plist" >&2
  return 1
}

uninstall_schedule() {
  local plist
  plist=$(plist_path)
  launchctl bootout "gui/$(id -u)/$LAUNCHD_LABEL" >/dev/null 2>&1
  launchctl unload "$plist" >/dev/null 2>&1
  rm -f "$plist"
  if launchctl list "$LAUNCHD_LABEL" >/dev/null 2>&1; then
    printf 'UNINSTALL FAILED: launchctl still lists %s\n' "$LAUNCHD_LABEL" >&2
    return 1
  fi
  printf 'unscheduled: %s (plist removed)\n' "$LAUNCHD_LABEL"
}

# THE WINDOW IS VALIDATED HERE, unconditionally and above the action dispatch, NOT beside its
# consumer. It was originally inside `if [ "$IF_DUE" = 1 ]`, which is below this dispatch, and an
# independent review reproduced the consequence: --install-schedule with a malformed window printed
# "scheduled:", wrote the plist and exited 0, and then every launchd trigger of the job it had just
# installed refused with exit 2. A schedule that can never fire, reported as installed, is the exact
# defect the install's own launchctl verification exists to prevent - one layer up.
#
# The value comes from the environment, so it is checked rather than trusted: a value the arithmetic
# cannot use would decide the guard by accident, in whichever direction the error fell. Three bad
# outcomes, one message, because to an operator they are one mistake: non-numeric aborts the
# arithmetic (and with it the command list, so the guard is SKIPPED rather than decided), over 6
# digits wraps it, and 0 makes the window 0 seconds - which makes EVERY login due and turns this
# guard back into the unguarded deletion job it exists to prevent.
refuse_tunable() {
  local name=$1 val=$2 lo=$3 hi=$4
  printf 'reclaim-worktrees: %s must be a whole number from %d to %s, got: %s\n' \
    "$name" "$lo" "$hi" "$val" >&2
  exit 2
}

# validate_tunable VAR_NAME ENV_NAME MIN MAX
#   Checks the variable named by VAR_NAME (via nameref) for: digits-only, length bounded by MAX,
#   and value >= MIN after base-10 normalisation. Refuses with exit 2 on any violation. The ''
#   arm is carried even though every default uses :- (making empty unreachable today), because the
#   thing standing between this line and a silent bypass would otherwise be a two-character choice
#   (:- versus -) hundreds of lines away.
validate_tunable() {
  local -n _val=$1
  local name=$2 lo=$3 hi=$4
  case "$_val" in '' | *[!0-9]*) refuse_tunable "$name" "$_val" "$lo" "$hi" ;; esac
  [ "${#_val}" -le "${#hi}" ] || refuse_tunable "$name" "$_val" "$lo" "$hi"
  _val=$((10#$_val))
  [ "$_val" -ge "$lo" ] || refuse_tunable "$name" "$_val" "$lo" "$hi"
}

# ALL FOUR TUNABLES ARE VALIDATED HERE, unconditionally and above the action dispatch. Placement
# matters: the DUE_AFTER_DAYS validation was originally inside `if [ "$IF_DUE" = 1 ]`, which is
# below the dispatch, and an independent review reproduced the consequence: --install-schedule with
# a malformed window wrote the plist and exited 0, then every launchd trigger refused with exit 2.
#
# NO_PR_MIN_AGE_DAYS is the dangerous one (jbrooksbartlett-lngd): if non-numeric, the -lt
# comparison at the sweep's keep branch returns non-zero, the keep is SKIPPED, and the worktree is
# REMOVED. A setting that exists to protect recent work turns into the opposite of a protection.
# The other two are less harmful today but carry the same class of bug one edit away.
validate_tunable DUE_AFTER_DAYS          RECLAIM_DUE_AFTER_DAYS          1 999999
validate_tunable NO_PR_MIN_AGE_DAYS      RECLAIM_NO_PR_MIN_AGE_DAYS      1 999999
validate_tunable MAXDEPTH                RECLAIM_MAXDEPTH                1 999999
validate_tunable RESCUE_MAX_BYTES        RECLAIM_RESCUE_MAX_BYTES        1 999999999999999

case "$ACTION" in
install)
  install_schedule
  exit $?
  ;;
uninstall)
  uninstall_schedule
  exit $?
  ;;
esac

# ---------------------------------------------------------------------------
# The catch-up guard (--if-due)
# ---------------------------------------------------------------------------
#
# THE ASYMMETRY IS THE WHOLE DESIGN, and it runs one way: only positive, readable evidence that a
# sweep COMPLETED may suppress a run. Everything else - no record, an empty record, a record full
# of prose, a number too long to be a timestamp, a timestamp in the future - is absence of
# evidence, and reads as DUE.
#
# It runs one way because the two failure modes are not symmetric:
#
#   always "ran recently"     -> the weekly job never runs again, silently. Strictly WORSE than
#                                the bug this flag fixes, which loses one week and not every week.
#   always "did not run"      -> it runs on every login. Noisy, and it deletes things - but
#                                visible in the launchd log the same day.
#
# So this errs toward running. It sits ABOVE the preflight on purpose: a not-due run needs no git,
# no jq, no temporary directory and does not take the lock, so it costs a file read and exits.

# BSD form, then GNU form, then the epoch itself - the same hedge mtime_epoch uses, and for the
# same reason: on GNU coreutils `-r` means "reference file", so the BSD spelling fails outright and
# the verdict line would degrade to "epoch 1755712800" just when someone is reading it.
iso_utc() {
  date -u -r "$1" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null ||
    date -u -d "@$1" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null ||
    printf 'epoch %s' "$1"
}

human_age() { # <seconds> -> "8.0 days", "3 hours", "1 minute"
  awk -v s="$1" 'BEGIN{
    if (s >= 172800) printf "%.1f days", s/86400
    else if (s >= 3600) { n = int(s/3600); printf "%d hour%s", n, (n == 1 ? "" : "s") }
    else if (s >= 60) { n = int(s/60); printf "%d minute%s", n, (n == 1 ? "" : "s") }
    else { n = int(s); printf "%d second%s", n, (n == 1 ? "" : "s") }
  }'
}

# Prints the verdict, always, so the launchd log records which way it went and why. Returns 0 due,
# 1 not due.
catch_up_check() {
  local now last age window readable=1
  now=$(date +%s)
  window=$((DUE_AFTER_DAYS * 86400))

  last=$(head -1 "$LAST_RUN_FILE" 2>/dev/null | tr -d '[:space:]')
  case "$last" in
  '' | *[!0-9]*) readable=0 ;;
  esac
  # An epoch second is 10 digits until the year 2286 and 11 until 5138. Anything longer is not a
  # timestamp, and would OVERFLOW the arithmetic below rather than lose a comparison - a guard
  # that errors out where it meant to decide is a guard with an undefined verdict.
  [ "${#last}" -le 11 ] || readable=0
  if [ "$readable" = 0 ]; then
    printf 'catch-up check: DUE - no readable record of a previous run at %s\n' "$LAST_RUN_FILE"
    return 0
  fi
  # 10#, because a leading zero makes a number OCTAL in bash arithmetic, and the failure is not
  # the misreading - it is that the guard DISAPPEARS. Measured 2026-08-21 with the prefix removed
  # and a record of 0999999999 (all digits, so it passes the check above, but 9 is not an octal
  # digit): bash prints "value too great for base" and ABORTS the enclosing command list, so this
  # function returns before printing any verdict, the `catch_up_check || exit 0` beside it never
  # runs, and the sweep proceeds UNGUARDED. Verified in isolation - a statement after a failed
  # $(( )) does not execute, and neither branch of an `if` around such a function runs. A guard
  # whose failure mode is "no guard, and nothing in the log" is the one defect class this file
  # exists to avoid, so the reading is forced decimal and a test pins that a verdict is stated.
  last=$((10#$last))

  if [ "$last" -gt "$now" ]; then
    printf 'catch-up check: DUE - the recorded last run is in the future (%s).\n' "$(iso_utc "$last")"
    printf '  That is a clock that moved, not a run that happened, so it suppresses nothing.\n'
    return 0
  fi

  age=$((now - last))
  if [ "$age" -ge "$window" ]; then
    printf 'catch-up check: DUE - the last run finished %s ago (%s), past the %s-day window.\n' \
      "$(human_age "$age")" "$(iso_utc "$last")" "$DUE_AFTER_DAYS"
    return 0
  fi

  printf 'catch-up check: NOT DUE - the last run finished %s ago (%s).\n' \
    "$(human_age "$age")" "$(iso_utc "$last")"
  printf '  --if-due sweeps once that reaches the %s-day window, so an ordinary login is not\n' \
    "$DUE_AFTER_DAYS"
  printf '  a weekly run. Next due %s. Nothing examined, nothing removed.\n' \
    "$(iso_utc "$((last + window))")"
  return 1
}

if [ "$IF_DUE" = 1 ]; then
  catch_up_check || exit 0
fi

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

for tool in git jq; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "reclaim-worktrees: $tool is required and is not on PATH" >&2
    exit 2
  }
done

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

: >"$TMP/gaps"
: >"$TMP/rows"
: >"$TMP/gitdirs"
: >"$TMP/sessions"
: >"$TMP/unresolved-sessions"

# A gap is a place this run could not look. It is NOT an error - the run continues - but it
# caps what the run is allowed to claim, and it is printed above the numbers rather than below
# them so it cannot be read as a footnote.
gap() { printf '%s\n' "$1" >>"$TMP/gaps"; }

# US (0x1f) as the field separator, NOT a tab, and this is not a style choice.
#
# Tab is an IFS WHITESPACE character, so bash COLLAPSES a run of them: with IFS=$'\t', a record
# whose third field is empty reads back with every later field shifted one place left. Measured
# while writing this: a detached worktree (empty branch) was parsed as a LOCKED worktree whose
# lock reason was "0", so it was kept for the wrong reason and the report said the wrong thing.
# A separator that is not IFS-whitespace preserves empty fields, and no filesystem path can
# contain 0x1f.
SEP=$'\037'

# verdict, path, branch, size in KB, detail
row() { printf '%s%s%s%s%s%s%s%s%s\n' "$1" "$SEP" "$2" "$SEP" "$3" "$SEP" "$4" "$SEP" "$5" >>"$TMP/rows"; }

count() { awk -F'\037' -v v="$1" '$1==v' "$TMP/rows" | wc -l | tr -d ' '; }

sum_kb() { # <verdict>...
  awk -F'\037' -v want="$*" 'BEGIN{split(want,w," ");for(i in w)k[w[i]]=1}
    k[$1]{s+=$4} END{printf "%d", s+0}' "$TMP/rows"
}

# Handles a NEGATIVE input, because the volume delta legitimately is one: other processes write to
# this disk while the sweep runs, so a run can reclaim 200 MB and still end with less free than it
# started. Without the sign split that rendered as "-204800 KB" next to two tidy GB figures.
human_kb() {
  awk -v kb="${1:-0}" 'BEGIN{
    sign = ""; if (kb < 0) { sign = "-"; kb = -kb }
    if (kb >= 1048576) printf "%s%.1f GB", sign, kb/1048576
    else if (kb >= 1024) printf "%s%.0f MB", sign, kb/1024
    else printf "%s%d KB", sign, kb
  }'
}

process_alive() { # <pid>
  case "$1" in
  '' | *[!0-9]*) return 1 ;;
  esac
  [ "$1" -gt 0 ] || return 1
  ps -p "$1" >/dev/null 2>&1
}

# In KB, not GB. `df -g` rounds to whole gigabytes, so the first live run reclaimed 212 MB and
# reported "111 GB -> 111 GB" - a true statement that hides the entire result. The number this line
# exists to show is usually in the hundreds of MB.
disk_free_kb() { df -k /System/Volumes/Data 2>/dev/null | awk 'NR==2 {print $4; exit}'; }

# ---------------------------------------------------------------------------
# The lock. Two concurrent runs would race on the same `git worktree remove`.
# ---------------------------------------------------------------------------

LOCK_DIR=${RECLAIM_LOCK_DIR:-${TMPDIR:-/tmp}/reclaim-worktrees.lock}
LOCK_HELD=0

release_lock() {
  [ "$LOCK_HELD" = 1 ] || return 0
  rm -f "$LOCK_DIR/pid" 2>/dev/null
  rmdir "$LOCK_DIR" 2>/dev/null
  LOCK_HELD=0
}

acquire_lock() {
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    printf '%s\n' "$$" >"$LOCK_DIR/pid"
    LOCK_HELD=1
    return 0
  fi
  # A lock left behind by a process that is gone is stale - the same `ps -p` reasoning the
  # contract applies to a locked worktree, applied to this script's own lock. Two runs both
  # deciding a lock is stale at the same instant is possible and bounded: git refuses
  # concurrent worktree operations on the same repository.
  local other
  other=$(cat "$LOCK_DIR/pid" 2>/dev/null)
  if [ -n "$other" ] && process_alive "$other"; then
    printf 'another reclamation is running (pid %s). Nothing done.\n' "$other" >&2
    return 1
  fi
  rm -f "$LOCK_DIR/pid" 2>/dev/null
  rmdir "$LOCK_DIR" 2>/dev/null
  mkdir "$LOCK_DIR" 2>/dev/null || {
    printf 'could not take the lock at %s. Nothing done.\n' "$LOCK_DIR" >&2
    return 1
  }
  printf '%s\n' "$$" >"$LOCK_DIR/pid"
  LOCK_HELD=1
  gap "a stale lock from pid $other was cleared before this run"
}

trap 'release_lock; rm -rf "$TMP"' EXIT
acquire_lock || exit 2

# ---------------------------------------------------------------------------
# The live-session set. THE MOST IMPORTANT FUNCTION IN THIS FILE.
# ---------------------------------------------------------------------------
#
# TRAP 1, measured 2026-08-19 and the reason this is written out at length. The obvious
# implementation collects live session paths and asks whether a worktree path MATCHES any of
# them. Done as a substring or regex match it fails silently and totally: one live session's
# path is the REPOSITORY ROOT, which is a prefix of every worktree beneath it, so all 37
# worktrees were classified LIVE. Measured: substring match gave 37 LIVE / 0 stale; exact
# match gave 2 LIVE / 35 stale. The 45 GB would have stayed and the report would have read
# "nothing to clean", which is indistinguishable from a clean machine. A guard that silently
# protects everything is the worst kind, because its failure looks like success.
#
# On this machine it is worse than the bead describes: one live session's path is $HOME itself,
# a prefix of every path that exists.
#
# BUT A PURE EXACT MATCH IS ALSO WRONG, in the opposite direction, and nothing in the bead says
# so. A session whose working directory is a SUBDIRECTORY of its worktree - `<worktree>/src`
# after a cd - matches no worktree exactly, so its worktree reads as stale and gets removed
# underneath it. That is the failure that loses live work rather than merely disk.
#
# So the test is DIRECTIONAL: a worktree is held if some session path IS the worktree, or lies
# BENEATH it. $HOME is neither, so it protects nothing spuriously; `<worktree>/src` is beneath,
# so it protects correctly. Never the other direction.
#
# EVERY session in the registry counts, whatever its status. `stopped` and `error` sessions are
# excluded elsewhere in this repo (conductor-signals.sh) because there the question is capacity;
# here the question is whether removing a directory could surprise anyone, and the safe answer
# to a session this script cannot interpret is "leave it alone". Retired sessions leave the
# registry, so this costs almost nothing.

SESSIONS_REFRESH_WARNED=0

read_sessions() {
  local json
  if [ -n "$SESSIONS_FILE" ]; then
    json=$(cat "$SESSIONS_FILE" 2>/dev/null)
  else
    json=$(agent-deck list --json 2>/dev/null)
  fi
  [ -n "$json" ] || return 1
  jq -e 'type == "array"' <<<"$json" >/dev/null 2>&1 || return 1

  local id path real
  while IFS="$SEP" read -r id path; do
    [ -n "$path" ] || continue
    # Both sides of the comparison are resolved the same way, because a fixture under /tmp and
    # the same fixture under /private/tmp are the same directory and must compare equal.
    if real=$(cd "$path" 2>/dev/null && pwd -P); then
      printf '%s%s%s\n' "${id:-unnamed}" "$SEP" "$real" >>"$TMP/sessions"
    else
      # A path that cannot be resolved cannot be compared, so it protects nothing. It is
      # counted separately at report time rather than passed off as a session that was checked.
      printf '%s%s%s\n' "${id:-unnamed}" "$SEP" "$path" >>"$TMP/unresolved-sessions"
      printf '%s%s%s\n' "${id:-unnamed}" "$SEP" "$path" >>"$TMP/sessions"
    fi
  # 0x1f, NOT @tsv. Measured 2026-08-20: `@tsv` ESCAPES a tab inside a value, emitting the two
  # characters \t, so a session path containing a tab came back as a path that does not exist,
  # failed to resolve, and protected nothing. A live session's worktree was one guard away from
  # being removed underneath it. Proof:
  #     jq -r '.[] | [.id, .path] | @tsv'   ->  s1<TAB>/a/wt\tb      (the tab is now backslash-t)
  #     jq -r '.[] | .id + "\u001f" + .path' ->  s1<0x1f>/a/wt<TAB>b  (the tab survives)
  # Same lesson as SEP itself, one layer earlier in the pipeline.
  done < <(jq -r '.[] | ((.id // .name // "unnamed") | tostring) + "\u001f" + (.path // "")' <<<"$json")
  sort -u "$TMP/sessions" -o "$TMP/sessions" 2>/dev/null
  return 0
}

# Re-read the registry immediately before a removal, because the set read at the start of the
# run goes stale: a sweep takes a minute or two of `gh` calls, and a session can be created in
# that window. The protected set only ever GROWS within a run - a refresh that fails keeps the
# previous set, and a session that ended mid-run keeps its protection, because its files may
# still be settling and reclaiming its worktree can wait a week.
refresh_sessions() {
  local before after
  before=$(wc -l <"$TMP/sessions" | tr -d ' ')
  if ! read_sessions; then
    if [ "$SESSIONS_REFRESH_WARNED" = 0 ]; then
      SESSIONS_REFRESH_WARNED=1
      gap "a mid-run re-read of the session list failed; the set read at startup was used instead"
    fi
    return
  fi
  after=$(wc -l <"$TMP/sessions" | tr -d ' ')
  [ "$after" -gt "$before" ] &&
    gap "$((after - before)) session(s) appeared mid-run and were protected"
  return 0
}

live_holder() { # <resolved worktree path> -> the id of the first session holding it
  local wt=$1
  local id path
  while IFS="$SEP" read -r id path; do
    [ -n "$path" ] || continue
    if [ "$path" = "$wt" ]; then
      printf '%s' "$id"
      return 0
    fi
    # Quoted in a case pattern, so a glob character in a real path stays literal.
    case "$path" in "$wt"/*)
      printf '%s' "$id"
      return 0
      ;;
    esac
  done <"$TMP/sessions"
  return 1
}

# An unreadable registry is NOT an empty registry, and this is the one place where guessing
# would delete a live session's worktree. Refuse the whole run: nothing is lost by retrying
# once agent-deck answers, and the report says why.
if ! read_sessions; then
  printf 'REFUSED: the agent-deck session list could not be read, so this run cannot tell a\n' >&2
  printf 'stale worktree from a live one. Nothing was examined and nothing was removed.\n' >&2
  printf 'Retry after:  agent-deck list --json\n' >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# Repository discovery. NOT scoped by repository - that is the whole point.
# ---------------------------------------------------------------------------

NOT_A_REPO=0

discover_repos() {
  local root main dir found
  for root in "${ROOTS[@]}"; do
    if [ ! -d "$root" ]; then
      gap "search root $root (no such directory)"
      continue
    fi
    # find's stderr is READ, not discarded. A subtree it could not enter is a place this run
    # did not look, and the failure this job exists to prevent is precisely a sweep that did
    # not look somewhere and did not mention it.
    find "$root" -maxdepth "$MAXDEPTH" -name .git -print 2>"$TMP/find.err" >>"$TMP/gitdirs"
    if [ -s "$TMP/find.err" ]; then
      cat "$TMP/find.err" >>"$TMP/find-errors.log"
    fi
  done

  # `git worktree list` names the MAIN worktree first, whatever directory it is asked from, so
  # every .git found - a real directory in a repository, or the one-line file in a worktree -
  # collapses to the same key and the repository is examined exactly once.
  # ONLY NEW UNREADABLE DIRECTORIES ARE A GAP. Measured 2026-08-20: the set is 121 paths and
  # byte-identical across consecutive runs, mostly macOS TCC-protected Library subtrees. A constant
  # printed as a warning every week is the same defect as the uv artifact above: two permanent
  # entries in a three-entry gap list teach the reader to skip the list, and the list is the only
  # thing that can ever say a sweep was incomplete.
  #
  # So the known set lives in a durable baseline, the count is always stated as a plain fact, and
  # only paths not seen before raise a gap. A newly-unreadable directory is reported exactly once,
  # and the full set stays auditable on disk rather than in a weekly warning nobody reads.
  UNREADABLE_TOTAL=0
  UNREADABLE_NEW=0
  if [ -s "$TMP/find-errors.log" ]; then
    sort -u "$TMP/find-errors.log" >"$TMP/unreadable-now"
    UNREADABLE_TOTAL=$(grep -c . "$TMP/unreadable-now" || true)
    # READ unconditionally, WRITE only on a real run. A --dry-run that updated the baseline would
    # silently spend the "reported exactly once" guarantee this feature exists to provide: the
    # preview marks the paths as known, and the real run that follows never reports them. The
    # script's own header and docs/reclamation.md both promise --dry-run "changes nothing", and
    # every other side effect here is already gated the same way.
    if [ "$DRY_RUN" = 0 ]; then
      mkdir -p "$(dirname "$UNREADABLE_BASELINE")" 2>/dev/null
      [ -f "$UNREADABLE_BASELINE" ] || : >"$UNREADABLE_BASELINE"
    fi
    sort -u "$UNREADABLE_BASELINE" 2>/dev/null >"$TMP/baseline.sorted" || : >"$TMP/baseline.sorted"
    comm -23 "$TMP/unreadable-now" "$TMP/baseline.sorted" >"$TMP/unreadable-new" 2>/dev/null
    UNREADABLE_NEW=$(grep -c . "$TMP/unreadable-new" || true)
    if [ "${UNREADABLE_NEW:-0}" -gt 0 ]; then
      gap "$UNREADABLE_NEW newly-unreadable directory/directories (listed at the end of this report)"
      if [ "$DRY_RUN" = 0 ]; then
        cat "$TMP/unreadable-now" "$TMP/baseline.sorted" | sort -u >"$TMP/baseline.new" &&
          mv "$TMP/baseline.new" "$UNREADABLE_BASELINE"
      fi
    fi
  fi

  while IFS= read -r found; do
    [ -n "$found" ] || continue
    dir=$(dirname "$found")
    main=$(git -C "$dir" worktree list --porcelain 2>/dev/null |
      awk '/^worktree /{print substr($0, 10); exit}')
    # A .git that `find` entered cleanly but git then refuses to read is a REPOSITORY THIS RUN DID
    # NOT EXAMINE, and it used to vanish here with no gap - contradicting this file's own header
    # claim that every repository it could not read is named. Reproduced 2026-08-20 by writing
    # garbage into a repo's .git/HEAD: find reports nothing on stderr, `git worktree list` says
    # "fatal: not a git repository", and the repo silently contributed zero worktrees. That is
    # exactly the corruption a crash under disk pressure produces, which is when this job matters.
    if [ -z "$main" ]; then
      # IS THIS A REPOSITORY AT ALL? Only a real one earns a gap, and the test is structural
      # rather than a reading of git's verdict, because git reports BOTH cases as failures and
      # cannot tell them apart for us. Measured 2026-08-20:
      #
      #   ~/.cache/uv/sdists-v9   .git is a ZERO-BYTE FILE   -> "fatal: invalid gitfile format"
      #   a repo with garbage in .git/HEAD                   -> "fatal: not a git repository"
      #
      # A valid `.git` FILE contains `gitdir: <path>`; a zero-byte or malformed one is a build
      # artifact that cannot hold a worktree, so nothing can hide there and its unexaminability
      # is not a blindness. A `.git` DIRECTORY could hold worktrees and we cannot tell, so it
      # stays a gap.
      #
      # A constant in the gap list destroys the gap list; see the baseline block below for the
      # argument. There are 32 `.git` entries under ~/.cache on this machine alone.
      if [ -d "$found" ] || head -c 8 "$found" 2>/dev/null | grep -q '^gitdir:'; then
        gap "the repository at $dir (git could not list its worktrees)"
      else
        NOT_A_REPO=$((NOT_A_REPO + 1))
      fi
      continue
    fi
    printf '%s\n' "$main"
    # NOT a pipeline. `done < file | sort` puts this whole loop in a SUBSHELL, and every
    # NOT_A_REPO increment dies with it - the same class of defect as the `local a=$1 b=$a`
    # expansion and the tab-collapsing IFS earlier in this file. Sort afterwards instead.
  done <"$TMP/gitdirs" >"$TMP/repos.raw"
  sort -u "$TMP/repos.raw" >"$TMP/repos"
}

discover_repos
REPO_COUNT=$(wc -l <"$TMP/repos" | tr -d ' ')

# ---------------------------------------------------------------------------
# Per-repository reads
# ---------------------------------------------------------------------------

# path, branch, locked, lock reason, detached, bare - 0x1f separated. Both `branch` and `reason`
# are routinely EMPTY (a detached worktree has no branch, a bare `locked` line has no reason), so
# the separator has to survive an empty field. See SEP above for what a tab did here.
parse_worktrees() { # <repo>
  git -C "$1" worktree list --porcelain 2>/dev/null | awk '
    function flush() {
      if (path != "")
        printf "%s\037%s\037%d\037%s\037%d\037%d\n", path, branch, locked, reason, detached, bare
      path=""; branch=""; locked=0; reason=""; detached=0; bare=0
    }
    /^worktree /  { flush(); path=substr($0, 10); next }
    /^branch /    { branch=substr($0, 8); next }
    /^detached$/  { detached=1; next }
    /^bare$/      { bare=1; next }
    /^locked/     { locked=1; if (length($0) > 7) reason=substr($0, 8); next }
    END { flush() }
  '
}

# PULL REQUEST STATE IS ASKED PER BRANCH, NOT PER REPOSITORY, and the first version of this file
# did the opposite. That looked like the cheap choice - one `gh pr list` per repository instead of
# one per worktree - and the live run on 2026-08-19 showed it was wrong twice over:
#
#   - IT IS CAPPED. 18 of 71 repositories returned a full page of 400 pull requests, so a branch
#     whose pull request sat further back read as having none. That is safe only because a capped
#     page downgrades the verdict to undetermined, and the cost was every worktree in those 18
#     repositories going unreclaimed forever. `--head <branch>` cannot be capped: a branch has a
#     handful of pull requests, not four hundred.
#   - IT WAS NOT EVEN CHEAPER. Most repositories on this machine have nothing but their main
#     working tree, so batching bought 71 calls to answer roughly 20 questions. Asking lazily,
#     only for a worktree that actually reaches this stage, is fewer calls AND exact.
#
# Returns OPEN | MERGED | CLOSED | NONE | UNREADABLE. UNREADABLE is never conflated with NONE:
# GHE was unreachable for ~16 hours on 2026-08-15/16, and "I could not ask" must not read as
# "there is no pull request, so nobody minds if this goes".
pr_state_for() { # <repo> <branch>
  command -v gh >/dev/null 2>&1 || {
    printf 'UNREADABLE'
    return
  }
  local out states
  out=$( (cd "$1" 2>/dev/null && gh pr list --head "$2" --state all --limit 20 --json state) 2>/dev/null )
  if [ -z "$out" ] || ! jq -e 'type == "array"' <<<"$out" >/dev/null 2>&1; then
    printf 'UNREADABLE'
    return
  fi
  states=$(jq -r '.[].state // empty' <<<"$out")
  if [ -z "$states" ]; then
    printf 'NONE'
    return
  fi
  # An open pull request outranks a merged one: a branch reused for a follow-up has both, and the
  # open one is the live work.
  if grep -qx 'OPEN' <<<"$states"; then printf 'OPEN'; return; fi
  if grep -qx 'MERGED' <<<"$states"; then printf 'MERGED'; return; fi
  printf 'CLOSED'
}

lock_pid() { # <lock reason> -> the pid it names, or nothing
  # The reason is free text, so a pid is only recoverable when the word "pid" is there to
  # anchor it. A bare integer is NOT treated as a pid: a reason like "keep until 2026" would
  # otherwise yield 2026, `ps -p 2026` would say gone, and the lock would be broken on the
  # strength of a year. A lock this cannot read is reported, never forced.
  #
  # "pid" MUST BE A WHOLE WORD. The first version matched it as a substring, and English is full
  # of words containing it: rapid, stupid, tepid, insipid, intrepid, lipid. Reproduced against the
  # real script 2026-08-20: a worktree locked with the reason "keep during rapid123 rollout, do
  # not touch" yielded pid 123, `ps -p 123` said gone, and the lock was broken and the worktree
  # removed - "lock held by pid 123, which is gone". That is the same trap the paragraph above
  # already guards for a BARE integer, arriving by a path the guard did not cover, and
  # `git worktree lock` is the third of this job's three independent protections.
  #
  # POSIX ERE has no \b, so the boundary is spelled out: start of string, or a non-alphanumeric.
  local frag
  frag=$(grep -oE '(^|[^A-Za-z0-9])[Pp][Ii][Dd][^0-9]{0,3}[0-9]+' <<<"$1" | head -1)
  [ -n "$frag" ] || return 0
  # Everything up to the last non-digit removed, leaving the trailing run of digits.
  printf '%s' "${frag##*[!0-9]}"
}

worktree_dirty() { # <worktree> -> 0 dirty, 1 clean, 2 could not tell
  local tracked untracked
  tracked=$(git -C "$1" status --porcelain --untracked-files=no 2>/dev/null) || return 2
  untracked=$(git -C "$1" ls-files --others --exclude-standard 2>/dev/null) || return 2
  [ -n "$tracked" ] || [ -n "$untracked" ]
}

# Prints NOTHING when du fails, rather than a plausible 0, because a failed read rendering as
# "0 KB" is the same defect this whole file is written against: it understates the reclaim and
# raises no gap.
size_kb() {
  local out
  out=$(du -sk "$1" 2>/dev/null) || return 1
  printf '%s' "$out" | awk '{print $1; exit}'
}

# size_kb, or 0 AND a gap saying the size is not known. Every report call site uses this.
size_kb_or_gap() { # <path>
  local kb
  if kb=$(size_kb "$1") && [ -n "$kb" ]; then
    printf '%s' "$kb"
    return 0
  fi
  gap "the size of $1 (du failed, so it counts as 0 in the totals)"
  printf '0'
}

mtime_epoch() { # <path> -> seconds since the epoch, or nothing
  local v
  v=$(stat -f %m "$1" 2>/dev/null) && { printf '%s' "$v"; return; }
  stat -c %Y "$1" 2>/dev/null
}

# HOW OLD IS A WORKTREE NOBODY HAS A PULL REQUEST FOR?
#
# The question is "has anyone worked in this WORKING COPY recently", which is a property of the
# copy and not of the commit it points at. So two signals, and the NEWEST of them wins - any sign
# of recent life keeps the worktree:
#
#   - the worktree directory's own mtime
#   - `logs/HEAD` in the worktree's private git admin directory, which git touches on every
#     checkout, commit, reset or rebase performed IN THAT WORKTREE
#
# The HEAD commit's date is deliberately NOT one of them. It answers a different question and gets
# it wrong in both directions: a worktree created today from an ancient release commit would read
# as long-dead, and a branch whose last commit was pushed from somewhere else would read as alive
# while this copy sat untouched for a month.
#
# It does not need to be a precise idleness measure, because the two checks that actually protect
# work run BEFORE it: a worktree someone is sitting in is already kept as live, and a worktree
# with edits in it is already kept as uncommitted. By the time this runs, the worktree is clean
# and unoccupied, and the only question left is whether anyone would miss the directory.
worktree_idle_days() { # <worktree> -> whole days since the most recent sign of activity
  local newest="" candidate admin
  candidate=$(mtime_epoch "$1")
  [ -n "$candidate" ] && newest=$candidate

  admin=$(git -C "$1" rev-parse --absolute-git-dir 2>/dev/null)
  if [ -n "$admin" ] && [ -e "$admin/logs/HEAD" ]; then
    candidate=$(mtime_epoch "$admin/logs/HEAD")
    if [ -n "$candidate" ] && { [ -z "$newest" ] || [ "$candidate" -gt "$newest" ]; }; then
      newest=$candidate
    fi
  fi

  # No readable timestamp at all means "cannot tell how old this is", and the caller must treat
  # that as young. Printing a large number here would turn an unreadable stat into a deletion.
  [ -n "$newest" ] || return 1
  printf '%d' $((($(date +%s) - newest) / 86400))
}

# ---------------------------------------------------------------------------
# Rescue. TRAP 2 lives here.
# ---------------------------------------------------------------------------
#
# Measured 2026-08-19: a rescue loop copied each untracked path with plain `cp`, which SILENTLY
# SKIPS A DIRECTORY. One worktree's only uncommitted item was an untracked directory (`.claude/`)
# so the rescue produced an empty patch and no files - and reported success. Reproduced while
# writing this:
#
#     git status --porcelain            ->  ?? .claude/          (a DIRECTORY)
#     cp wt/.claude dest/               ->  cp: wt/.claude is a directory (not copied).
#
# Two defences, because one is not enough:
#
#   1. Enumerate with `git ls-files --others --exclude-standard`, which lists FILES and never
#      directories, instead of `git status --porcelain`, which collapses an untracked directory
#      to a single entry. The trap cannot arise from an input that is never a directory. `cp -R`
#      is still used, for a symlink-to-directory and for any future git that answers differently.
#   2. PROVE THE COPY LANDED. If the dirty check said there was something and the rescue
#      directory ends up with an empty patch and no files, that is trap 2 recurring and it is
#      reported as a failure. A rescue that cannot fail is not a rescue.

# Is this worktree's uncommitted state identical to the last time it was rescued? A dirty worktree
# is LEFT IN PLACE by design, so it reaches the rescue again on every weekly run. Without this it
# banks another full copy - up to RESCUE_MAX_BYTES, 512 MiB - every week for as long as it stays
# dirty, which relocates the unbounded disk growth this job exists to remove into the job's own
# evidence tree. Found by review 2026-08-20.
#
# The fingerprint is the patch plus the sorted list of untracked paths and their sizes. It is
# cheap, and being wrong in the conservative direction just means one redundant copy.
rescue_fingerprint() { # <worktree>
  {
    git -C "$1" diff HEAD 2>/dev/null
    git -C "$1" ls-files --others --exclude-standard 2>/dev/null | sort | while IFS= read -r f; do
      printf '%s %s\n' "$f" "$(wc -c <"$1/$f" 2>/dev/null | tr -d ' ')"
    done
  } | shasum -a 256 2>/dev/null | awk '{print $1; exit}'
}

# The most recent rescue directory for this worktree, whatever date it carries.
last_rescue_dir() { # <repo basename> <worktree basename>
  ls -dt "$RESCUE_ROOT"/*-"$1"-"$2" "$RESCUE_ROOT"/*-"$1"-"$2"-[0-9]* 2>/dev/null | head -1
}

rescue_dest() { # <repo basename> <worktree basename> -> a fresh directory path
  # Two statements, not one. `local a=x b=$a` expands EVERY argument before the builtin runs, so
  # `$a` there is the global - unset, and under `set -u` that aborts the run mid-rescue.
  local base="$RESCUE_ROOT/$(date -u +%Y-%m-%d)-$1-$2"
  local candidate=$base n=2
  while [ -e "$candidate" ]; do
    candidate="$base-$n"
    n=$((n + 1))
  done
  printf '%s' "$candidate"
}

# Sets RESCUE_DIR and RESCUE_NOTE. Returns 0 when the rescue is proved, 1 when it is not.
RESCUE_DIR=""
RESCUE_NOTE=""

rescue_uncommitted() { # <worktree> <repo> <branch>
  local wt=$1 repo=$2 branch=$3
  RESCUE_DIR=""
  RESCUE_NOTE=""

  local repo_base wt_base prior fp
  repo_base=$(basename "$repo")
  wt_base=$(basename "$wt")

  # Already rescued, byte for byte? Then say so and copy nothing.
  fp=$(rescue_fingerprint "$wt")
  prior=$(last_rescue_dir "$repo_base" "$wt_base")
  if [ -n "$fp" ] && [ -n "$prior" ] && [ -f "$prior/fingerprint" ] &&
    [ "$(cat "$prior/fingerprint" 2>/dev/null)" = "$fp" ]; then
    RESCUE_DIR=$prior
    RESCUE_NOTE="unchanged since the rescue already held at $prior, so nothing was copied again"
    printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$prior/unchanged-since.txt" 2>/dev/null
    return 0
  fi

  local dest
  dest=$(rescue_dest "$repo_base" "$wt_base")
  if ! mkdir -p "$dest/untracked"; then
    RESCUE_NOTE="could not create $dest"
    return 1
  fi
  # 700, NOT the ambient umask. This directory's whole purpose is consolidating untracked files
  # out of many worktrees into one predictable place, which is exactly where a stray .env or
  # credential file ends up. Measured 2026-08-20: ~/evidence was 0755 and $HOME is group `staff`,
  # the default group of every local macOS account, so any other account on the machine could
  # read the lot. chmod is applied to the rescue root too, not just this run's directory.
  chmod 700 "$RESCUE_ROOT" 2>/dev/null
  chmod 700 "$dest" 2>/dev/null
  RESCUE_DIR=$dest

  # `diff HEAD` carries staged and unstaged changes to tracked files in one patch.
  git -C "$wt" diff HEAD >"$dest/uncommitted.patch" 2>/dev/null

  local -a untracked=()
  local f
  while IFS= read -r -d '' f; do
    untracked+=("$f")
  done < <(git -C "$wt" ls-files --others --exclude-standard -z 2>/dev/null)

  local total=0 copied=0 skipped=0 symlinks=0 bytes
  for f in "${untracked[@]}"; do
    # A SYMLINK IS RECORDED, NOT COPIED, and that closes two separate defects found on 2026-08-20.
    #
    #   `cp -R` on macOS recreates a symlink AS a symlink rather than copying its target, so an
    #   untracked `.env -> ~/.config/secrets/.env` was reproduced landing in the evidence tree as
    #   a live pointer to a file outside the worktree. The rescue is meant to snapshot THIS
    #   worktree; a pointer to someone's SSH key is not that, and the README's own restore command
    #   would replant it.
    #
    #   And the byte cap measured the wrong thing: `wc -c <link` FOLLOWS the link, so a 189-byte
    #   symlink to a 2 GB dataset was measured as 2 GB, blew the cap, and turned the only
    #   uncommitted item in a worktree into a permanent weekly "rescue-failed / THESE NEED A
    #   HUMAN" - crying wolf about something that was never at risk, since the target is not in
    #   the worktree and is not going anywhere.
    #
    # Recording the link and its target preserves everything that is actually at risk here.
    if [ -L "$wt/$f" ]; then
      symlinks=$((symlinks + 1))
      printf '%s -> %s\n' "$f" "$(readlink "$wt/$f" 2>/dev/null)" >>"$dest/untracked-symlinks.txt"
      continue
    fi
    bytes=$(wc -c <"$wt/$f" 2>/dev/null | tr -d ' ')
    case "$bytes" in '' | *[!0-9]*) bytes=0 ;; esac
    if [ $((total + bytes)) -gt "$RESCUE_MAX_BYTES" ]; then
      skipped=$((skipped + 1))
      continue
    fi
    mkdir -p "$dest/untracked/$(dirname "$f")" 2>/dev/null
    if cp -R "$wt/$f" "$dest/untracked/$f" 2>/dev/null; then
      copied=$((copied + 1))
      total=$((total + bytes))
    else
      skipped=$((skipped + 1))
    fi
  done

  [ -n "$fp" ] && printf '%s\n' "$fp" >"$dest/fingerprint" 2>/dev/null

  local patch_bytes
  patch_bytes=$(wc -c <"$dest/uncommitted.patch" 2>/dev/null | tr -d ' ')
  case "$patch_bytes" in '' | *[!0-9]*) patch_bytes=0 ;; esac

  {
    printf '# Rescued uncommitted work\n\n'
    printf 'Rescued by `scripts/reclaim-worktrees.sh` (the weekly SCHEDULED RECLAMATION).\n\n'
    printf '| | |\n| --- | --- |\n'
    printf '| worktree | `%s` |\n' "$wt"
    printf '| repository | `%s` |\n' "$repo"
    printf '| branch | `%s` |\n' "${branch:-(detached HEAD)}"
    printf '| HEAD | `%s` |\n' "$(git -C "$wt" rev-parse HEAD 2>/dev/null)"
    printf '| rescued at | %s |\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '| tracked changes | %s bytes of patch |\n' "$patch_bytes"
    printf '| untracked files | %s copied, %s skipped |\n' "$copied" "$skipped"
    printf '\n## THE WORKTREE WAS LEFT IN PLACE\n\n'
    printf 'Nothing was removed. This copy exists so the uncommitted work survives even if the\n'
    printf 'worktree is later cleared by hand; the work itself is still where you left it.\n\n'
    printf '## To restore this elsewhere\n\n'
    printf '```\ngit -C <target> apply %s/uncommitted.patch\ncp -R %s/untracked/. <target>/\n```\n' \
      "$dest" "$dest"
  } >"$dest/README.md" 2>/dev/null

  local symnote=""
  [ "$symlinks" -gt 0 ] && symnote=", ${symlinks} symlink(s) recorded in untracked-symlinks.txt rather than copied"
  if [ "$skipped" -gt 0 ]; then
    RESCUE_NOTE="${copied} untracked files copied, ${skipped} NOT copied (over the ${RESCUE_MAX_BYTES}-byte cap or unreadable)${symnote}"
  else
    RESCUE_NOTE="${copied} untracked files, ${patch_bytes} bytes of patch${symnote}"
  fi

  # The proof. Nothing landed while the dirty check said there was something to land. A recorded
  # symlink COUNTS as something landing: the link and its target are preserved, which is the whole
  # of what was at risk, so a worktree whose only uncommitted item is a symlink is a success and
  # not a weekly false alarm.
  if [ "$patch_bytes" -eq 0 ] && [ "$copied" -eq 0 ] && [ "$symlinks" -eq 0 ]; then
    RESCUE_NOTE="RESCUED NOTHING - empty patch and no files copied, though the worktree reads as dirty (trap 2). ${RESCUE_NOTE}"
    return 1
  fi
  return 0
}

# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------

DISK_BEFORE=$(disk_free_kb)
WORKTREES_SEEN=0
MAIN_SKIPPED=0

while IFS= read -r repo; do
  [ -n "$repo" ] || continue

  main_seen=0
  while IFS="$SEP" read -r wt branch locked reason detached bare; do
    [ -n "$wt" ] || continue

    # The main working tree is the first entry of every list. git refuses to remove it anyway
    # ("is a main working tree"), but naming it explicitly means the report accounts for it
    # rather than leaving a silent difference between what was listed and what was examined.
    if [ "$main_seen" = 0 ]; then
      main_seen=1
      WORKTREES_SEEN=$((WORKTREES_SEEN + 1))
      # COUNTED, NOT LISTED. Every repository has exactly one, so listing them made 71 of the
      # ~95 lines in the KEPT section read "the repository's own working tree". That section
      # exists so nothing is skipped in silence; at that signal-to-noise ratio nobody reads it,
      # which defeats the purpose it was added for.
      MAIN_SKIPPED=$((MAIN_SKIPPED + 1))
      continue
    fi
    WORKTREES_SEEN=$((WORKTREES_SEEN + 1))

    # DEFENCE IN DEPTH, and its original comment gave the wrong reason - which is exactly how a
    # dead-code pass came to propose deleting it. It claimed a tabbed path would corrupt rows
    # downstream; SEP fixed that, so the stated reason was no longer true while the real one went
    # unwritten. The real exposure was in read_sessions above (jq's @tsv escaped the tab, so a
    # tabbed session path never resolved and protected nothing), and with that fixed a tabbed
    # worktree IS protected normally. This stays because git's non-NUL porcelain still cannot
    # express such a path unambiguously, so declining to reason about it is the honest answer.
    case "$wt" in *$'\t'*)
      gap "a worktree path containing a tab, under $(basename "$repo")"
      row kept-undetermined "$wt" "" 0 "path contains a tab and cannot be parsed safely"
      continue
      ;;
    esac

    resolved=$(cd "$wt" 2>/dev/null && pwd -P) || resolved=$wt
    short_branch=${branch#refs/heads/}

    # 1. Live sessions first. Nothing below this line may run against a held worktree.
    if holder=$(live_holder "$resolved"); then
      row kept-live "$wt" "$short_branch" 0 "held by agent-deck session $holder"
      continue
    fi

    # 2. Uncommitted work. Rescued, then LEFT IN PLACE - see docs/reclamation.md and
    #    jbrooksbartlett-trts for why this differs from the contract's "then remove".
    worktree_dirty "$wt"
    case $? in
    0)
      if [ "$DRY_RUN" = 1 ]; then
        # A dry run that writes is a dry run that lies. The first live run printed "nothing was
        # changed" while creating four rescue directories - harmless in itself, and exactly the
        # kind of small dishonesty that stops a --dry-run being trusted for the real decision.
        row would-rescue "$wt" "$short_branch" "$(size_kb_or_gap "$wt")" \
          "uncommitted work: it would be rescued under $RESCUE_ROOT and the worktree left in place"
        continue
      fi
      if rescue_uncommitted "$wt" "$repo" "$short_branch"; then
        row kept-uncommitted "$wt" "$short_branch" "$(size_kb_or_gap "$wt")" \
          "uncommitted work rescued to $RESCUE_DIR ($RESCUE_NOTE)"
      else
        gap "the rescue of $wt could not be proved"
        row rescue-failed "$wt" "$short_branch" "$(size_kb_or_gap "$wt")" \
          "$RESCUE_NOTE${RESCUE_DIR:+ (attempted at $RESCUE_DIR)}"
      fi
      continue
      ;;
    2)
      gap "the working state of $wt (git status failed)"
      row kept-undetermined "$wt" "$short_branch" 0 "git could not report its working state"
      continue
      ;;
    esac

    # 3. Locks. A lock whose process is gone is stale; a lock whose process is alive, or whose
    #    reason names no process at all, is not this job's to break.
    unlock_first=0
    if [ "$locked" = 1 ]; then
      pid=$(lock_pid "$reason")
      if [ -z "$pid" ]; then
        row kept-locked "$wt" "$short_branch" 0 \
          "locked, and the reason names no pid so the holder cannot be checked: ${reason:-(no reason given)}"
        continue
      elif process_alive "$pid"; then
        row kept-locked "$wt" "$short_branch" 0 "locked by pid $pid, which is running"
        continue
      fi
      unlock_first=1
    fi

    # 4. Pull request state. Never a commit count: a squash-merged branch still reads as ahead
    #    of master, and that distinction is what made the 2026-08-19 audit trustworthy.
    # Reset per worktree: this is a plain shell global, so a reason set for one worktree would
    # otherwise be reported against the next one that reaches the removal path without setting it.
    reason_detail=""
    if [ "$unlock_first" = 1 ]; then
      reason_detail="lock held by pid $pid, which is gone"
    else
      if [ "$detached" = 1 ]; then
        row kept-undetermined "$wt" "" 0 "detached HEAD, so there is no branch whose pull request could be checked"
        continue
      fi
      if [ -z "$short_branch" ]; then
        row kept-undetermined "$wt" "" 0 "git reported no branch for it"
        continue
      fi
      state=$(pr_state_for "$repo" "$short_branch")
      case "$state" in
      UNREADABLE)
        gap "pull request state for $short_branch in $(basename "$repo") (gh could not be asked)"
        row kept-undetermined "$wt" "$short_branch" 0 \
          "pull request state unknown - gh could not be asked about this branch"
        continue
        ;;
      OPEN)
        row kept-pr-open "$wt" "$short_branch" 0 "its pull request is still open"
        continue
        ;;
      NONE)
        # THE NO-PULL-REQUEST CLASS, and why age is the rule. Jonny, 2026-08-19: pull request
        # state is not a SAFETY signal at all, because a removed worktree keeps its branch and its
        # commits either way. It is only a signal about whether someone is still USING the working
        # copy. The safety comes from the live-session and uncommitted checks, both of which have
        # already run and both of which apply to a worktree with no pull request identically. So an
        # idle clean unoccupied copy can go on the same argument as a merged one.
        #
        # This class was 7 of the 35 worktrees cleared on 2026-08-19 - 20% of the reclaim - and
        # nothing else reaches it: those 7 were not locked, so the dead-lock rule missed them too.
        # Written into the contract's SCHEDULED RECLAMATION table on 2026-08-20 (jbrooksbartlett-e6ne).
        if ! idle=$(worktree_idle_days "$wt"); then
          gap "the age of $wt (no readable timestamp, so it was kept)"
          row kept-no-pr "$wt" "$short_branch" 0 \
            "no pull request, and its age could not be read - kept rather than guessed at"
          continue
        fi
        if [ "$idle" -lt "$NO_PR_MIN_AGE_DAYS" ]; then
          row kept-no-pr "$wt" "$short_branch" "$(size_kb_or_gap "$wt")" \
            "no pull request, but something touched it $idle day(s) ago (needs $NO_PR_MIN_AGE_DAYS)"
          continue
        fi
        reason_detail="no pull request, and nothing has touched it for $idle days"
        ;;
      esac
      # MERGED and CLOSED match no arm above and fall through to here.
      [ -n "$reason_detail" ] || reason_detail="pull request $state"
    fi

    # 5. Removal.
    kb=$(size_kb_or_gap "$wt")
    if [ "$DRY_RUN" = 1 ]; then
      if [ "$unlock_first" = 1 ]; then
        row would-remove-after-unlock "$wt" "$short_branch" "$kb" "$reason_detail"
      else
        row would-remove "$wt" "$short_branch" "$kb" "$reason_detail"
      fi
      continue
    fi

    # LAST CHECK BEFORE THE ONLY DESTRUCTIVE CALL IN THIS FILE. The session set read at startup
    # is minutes old by now. Re-read it and ask again: a session created into this worktree
    # while the sweep was running would otherwise lose it.
    refresh_sessions
    if holder=$(live_holder "$resolved"); then
      row kept-live "$wt" "$short_branch" 0 \
        "a session ($holder) took this worktree while the sweep was running"
      continue
    fi

    if [ "$unlock_first" = 1 ]; then
      if ! unlock_err=$(git -C "$repo" worktree unlock "$wt" 2>&1); then
        gap "the stale lock on $wt could not be released"
        row failed "$wt" "$short_branch" "$kb" "unlock refused: ${unlock_err//$'\n'/ }"
        continue
      fi
    fi

    # No --force. The dirty check above already decided this worktree is clean; git's own
    # refusal is the second opinion, and forcing would throw it away.
    if remove_err=$(git -C "$repo" worktree remove "$wt" 2>&1); then
      if [ "$unlock_first" = 1 ]; then
        row removed-after-unlock "$wt" "$short_branch" "$kb" "$reason_detail"
      else
        row removed "$wt" "$short_branch" "$kb" "$reason_detail"
      fi
    else
      gap "the removal of $wt (git refused)"
      row failed "$wt" "$short_branch" "$kb" "git refused: ${remove_err//$'\n'/ }"
    fi
  done < <(parse_worktrees "$repo")
done <"$TMP/repos"

# ---------------------------------------------------------------------------
# Build caches. Tool-native commands only.
# ---------------------------------------------------------------------------
#
# The contract names Bazel, npm, yarn and pip, and says "tool-native commands where they exist".
# Recursive force-delete is not an option: the security-block hook rejects it, correctly, and a
# tool that knows its own cache layout is the safer instrument anyway.
#
# Bazel is REPORTED, NOT CLEARED, and that is deliberate rather than an omission. `bazel clean`
# needs a workspace to run in, so it cannot reach an output base whose workspace has been
# deleted - which is exactly the stale case worth reclaiming. Guessing at the layout with a
# recursive delete is the one thing the contract forbids. Measured 2026-08-19: no bazel output
# base exists on this machine, so a bazel branch here could not be tested and would be a check
# that cannot fail.

: >"$TMP/caches"

cache_row() { printf '%s%s%s%s%s\n' "$1" "$SEP" "$2" "$SEP" "$3" >>"$TMP/caches"; }

# WHERE A CACHE TOOL ACTUALLY LIVES, which `command -v` alone does not answer under launchd.
#
# MEASURED 2026-08-20, on the first real run of the installed job, and it had reclaimed NOTHING
# from any cache:
#
#     npm    not present   npm is not on PATH
#     yarn   not present   yarn is not on PATH
#     pip    not present   pip is not on PATH
#
# All three were installed. launchd gives the job the PATH written into its plist and nothing
# else - no shell, no profile, no nvm shim - and on this machine npm and yarn live under
# ~/.nvm/versions/node/<version>/bin, which no fixed PATH can name because the version moves.
# So the job cleared 0 of 11 GB of cache and reported it as "not present", which reads as
# "nothing to do". Interactively it worked, because an interactive shell has the nvm path.
#
# Hence: look on PATH, then look in the places launchd's PATH cannot reach.
# THE FALLBACK LIST IS OVERRIDABLE, and that is not decoration. Searching outside PATH lets this
# function walk straight past a test harness's stubs: the suite puts its fakes first on PATH, but a
# hardcoded /opt/homebrew/bin fallback found the REAL pip3 and the suite purged a real 7.3 GB pip
# cache. A script that can escape its own tests has to hand the test a way to fence it in.
RECLAIM_TOOL_DIRS=${RECLAIM_TOOL_DIRS:-}

resolve_tool() { # <command name> -> an absolute path, or nothing
  local name=$1 found d
  found=$(command -v "$name" 2>/dev/null)
  if [ -n "$found" ]; then
    printf '%s' "$found"
    return 0
  fi
  local -a dirs
  if [ -n "$RECLAIM_TOOL_DIRS" ]; then
    IFS=: read -ra dirs <<<"$RECLAIM_TOOL_DIRS"
  else
    dirs=("$HOME"/.nvm/versions/node/*/bin /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin")
  fi
  for d in "${dirs[@]}"; do
    if [ -x "$d/$name" ]; then
      printf '%s' "$d/$name"
      return 0
    fi
  done
  return 1
}

# Which live processes hold the uv cache lock? Prints one "pid command" per verified holder.
# Returns non-zero when it cannot establish an answer, so a caller can fail closed.
uv_lock_holders() {
  local uvbin cache pid
  command -v lsof >/dev/null 2>&1 || return 1
  uvbin=$(resolve_tool uv) || return 1
  cache=$("$uvbin" cache dir 2>/dev/null | tail -1)
  [ -n "$cache" ] || cache=${UV_CACHE_DIR:-$HOME/.cache/uv}
  # Exported, because the caller must be able to require that uv's own error names THIS path.
  UV_LOCK_PATH="$cache/.lock"
  [ -e "$UV_LOCK_PATH" ] || return 1
  local holders=""
  HOLDER_COUNT=0
  while read -r pid; do
    [ -n "$pid" ] || continue
    # ps -p, not merely lsof: a stale lsof entry for a dead pid must not read as a live holder.
    process_alive "$pid" || continue
    # AND IT HAS TO BE A UV PROCESS. lsof naming *some* live pid holding the file is not evidence
    # that uv failed because of a lock: any process could hold it. A holder this cannot confirm is
    # uv does not count, so the benign reading cannot be reached on its strength. Fail closed.
    local comm
    comm=$(basename "$(ps -o comm= -p "$pid" 2>/dev/null | tr -d ' ')")
    case "$comm" in uv | uv-*) ;; *) continue ;; esac
    HOLDER_COUNT=$((HOLDER_COUNT + 1))
    holders="$holders$comm "
  done < <(lsof -t -- "$UV_LOCK_PATH" 2>/dev/null | sort -u)
  # Print NOTHING and fail when there are no holders. Printing a bare newline made the
  # caller's `[ -s ]` test true with zero holders, which is precisely the quiet false green
  # this whole branch exists to avoid.
  [ -n "$holders" ] || return 1
  # A COUNT AND A FEW NAMES. The first live run listed 69 pids in one report line, which is
  # not a report, and the pids are the least durable part of the fact.
  printf '%s live process(es), including %s' "$HOLDER_COUNT" \
    "$(printf '%s' "$holders" | tr ' ' '\n' | grep -v '^$' | sort -u | head -3 | tr '\n' ' ' | sed 's/ *$//')"
}

run_caches() {
  # An array of argv arrays, not strings put through `eval`. A cache command assembled by
  # string interpolation is a shell injection waiting for someone to add a path to it, and this
  # file already runs unattended as a launchd job.
  local name out bin candidate
  local -a cands args
  for name in npm yarn pip uv; do
    case "$name" in
    npm)
      cands=(npm)
      args=(cache clean --force)
      ;;
    yarn)
      cands=(yarn)
      args=(cache clean)
      ;;
    # pip3 FIRST. This machine has pip3 and no `pip` at all, so a single-name lookup reported
    # the pip cache as absent while 7.3 GB of it sat there.
    pip)
      cands=(pip3 pip)
      args=(cache purge)
      ;;
    # `prune` and not `clean`, decided 2026-08-20 (jbrooksbartlett-di8u). This cache measured
    # 3.7 GB, roughly ten times the other three combined, but `clean` empties it and then charges
    # most of it straight back on the next resolve, so the real saving is much smaller than the
    # number suggests. `prune` drops only what nothing is using.
    uv)
      cands=(uv)
      args=(cache prune)
      ;;
    esac

    bin=""
    for candidate in "${cands[@]}"; do
      bin=$(resolve_tool "$candidate") && [ -n "$bin" ] && break
      bin=""
    done

    # A TOOL THAT CANNOT BE FOUND IS A GAP, not a footnote. The old wording - "not present" with
    # no gap raised - meant a run that cleared nothing still exited 0 and read as clean.
    if [ -z "$bin" ]; then
      cache_row "$name" "NOT FOUND" \
        "none of [${cands[*]}] could be located, on PATH or in the nvm/homebrew/.local locations launchd's PATH misses - this cache was NOT cleared"
      gap "the $name cache (its tool could not be found, so nothing was cleared)"
      continue
    fi
    local -a cmd=("$bin" "${args[@]}")
    # THE TOOL'S OWN DIRECTORY GOES ON PATH FOR THE CALL, and finding the binary was not enough
    # without it. Measured 2026-08-20 under a faithful launchd environment: npm and yarn were now
    # located correctly under nvm and then both died with
    #     env: node: No such file or directory
    # because nvm's `npm` and `yarn` are shell scripts that shell out to their SIBLING `node`,
    # which launchd's plist PATH does not contain either. Prepending the directory the tool was
    # found in fixes the whole class in one line.
    #
    # UV_LOCK_TIMEOUT is bounded because the default is 300 seconds and it was spent in full:
    # `uv cache prune` waits on a lock another uv process holds, and an unattended weekly job must
    # fail fast and report rather than block for five minutes.
    #
    # Which nvm version supplies npm is left to glob order on purpose. The npm cache is shared at
    # ~/.npm/_cacache regardless of the node version that cleans it, so picking a specific version
    # would be effort spent on something invisible.
    if out=$(PATH="$(dirname "$bin"):$PATH" \
      UV_LOCK_TIMEOUT="${RECLAIM_UV_LOCK_TIMEOUT:-30}" "${cmd[@]}" 2>&1); then
      cache_row "$name" "cleaned" "${cmd[*]}"
    elif [ "$name" = uv ] && uv_lock_holders >"$TMP/uvholders" &&
      [ -s "$TMP/uvholders" ] &&
      grep -qE 'Cache is currently in-use|waiting for lock on' <<<"$out"; then
      # EXPECTED, THEREFORE NOT A FAILURE - but only on both counts, and both are checked.
      #
      # BOTH conditions are required deliberately. A message that merely looks like a lock is not
      # enough, because then any uv failure whose text happened to mention a lock would go quiet,
      # which trades a noisy true signal for a quiet false green. And a held lock alone is not
      # enough either, because uv could be failing for an unrelated reason while other processes
      # happen to hold it. So: lsof must name at least one process holding <cache>/.lock, `ps -p`
      # must confirm it is alive, the holder must BE a uv process, AND uv's own output must name
      # THIS LOCK FILE BY PATH.
      #
      # THE MATCH IS ON UV'S LOCK-SPECIFIC PHRASES, and getting to that took two wrong answers.
      #
      # First it tested for the substring "lock|in-use", which a review broke: `filelock` is one of
      # the most common transitive Python dependencies and this cache holds entries for it, so a
      # genuine unrelated failure reading "failed to remove directory .../filelock-3.13.1:
      # Directory not empty" matched "lock" and was silently excused with exit 0.
      #
      # Then it required uv's output to name the lock file by absolute path. That never fires:
      # measured on uv 0.11.19, the message abbreviates it to a RELATIVE path -
      #     waiting for lock on `/Users/x/.cache/uv` at `.cache/uv/.lock`
      # - so the absolute form is not in the text and every held lock read as a hard failure. The
      # regression shipped because the TEST STUB emitted a message uv does not actually produce.
      #
      # The phrases below are what uv really writes, and they separate the cases cleanly: the
      # filelock error contains neither, so it still fails closed.
      #
      # Anything else stays a FAILED row with a gap and exit 1. If lsof is unavailable the check
      # cannot be made, so this branch does not fire and the failure stands - fail closed.
      cache_row "$name" "SKIPPED" \
        "its cache lock is held by $(tr -d '\n' <"$TMP/uvholders"); expected while they run, so not counted as a failure"
    else
      cache_row "$name" "FAILED" "${cmd[*]} -> ${out//$'\n'/ }"
      gap "the $name cache (its own clean command failed)"
    fi
  done

  local base found=0
  for base in "/private/var/tmp/_bazel_$(id -un)" "$HOME/.cache/bazel"; do
    if [ -d "$base" ]; then
      found=1
      cache_row bazel "NOT CLEARED" \
        "$base exists ($(human_kb "$(size_kb "$base")")). No tool-native command reaches an output base whose workspace is gone; clear it by hand or run 'bazel clean --expunge' inside each workspace."
      gap "the bazel cache at $base (reported, not cleared)"
    fi
  done
  [ "$found" = 0 ] && cache_row bazel "nothing to do" "no bazel output base on this machine"
}

if [ "$DO_CACHES" = 1 ] && [ "$DRY_RUN" = 0 ]; then
  run_caches
elif [ "$DO_CACHES" = 1 ]; then
  cache_row all "not attempted" "--dry-run"
else
  cache_row all "not attempted" "--no-caches"
fi

DISK_AFTER=$(disk_free_kb)

# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

removed_kb=$(sum_kb removed removed-after-unlock)
would_kb=$(sum_kb would-remove would-remove-after-unlock)

report() {
  printf 'WORKTREE RECLAMATION  %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'work contract section 4, SCHEDULED RECLAMATION%s\n\n' \
    "$([ "$DRY_RUN" = 1 ] && printf '   ***  DRY RUN - nothing was changed  ***')"

  # Printed FIRST, because it caps what every number below is allowed to mean.
  if [ -s "$TMP/gaps" ]; then
    printf 'NOT A CLEAN SWEEP. This run could not examine:\n'
    sort -u "$TMP/gaps" | sed 's/^/  - /'
    printf 'Anything listed there was NOT reclaimed and NOT ruled out. The counts below are\n'
    printf 'what was examined, not what exists.\n\n'
  fi

  local sessions unresolved
  sessions=$(wc -l <"$TMP/sessions" | tr -d ' ')
  unresolved=$(sort -u "$TMP/unresolved-sessions" | grep -c . || true)
  printf 'repositories swept ......... %s\n' "$REPO_COUNT"
  printf 'worktrees examined ......... %s  (%s of them a repository main tree, never removable)\n' \
    "$WORKTREES_SEEN" "$MAIN_SKIPPED"
  printf 'unreadable directories ..... %s known%s\n' "${UNREADABLE_TOTAL:-0}" \
    "$([ "${UNREADABLE_NEW:-0}" -gt 0 ] && printf ', %s NEW (see the gap above)' "$UNREADABLE_NEW")"
  printf 'not git repositories ....... %s (a .git that is not a repository, so it cannot hold a worktree)\n' \
    "${NOT_A_REPO:-0}"
  printf 'live sessions consulted .... %s%s\n' "$sessions" \
    "$([ "${unresolved:-0}" -gt 0 ] && printf ' (%s path(s) unresolvable, so they protected nothing)' "$unresolved")"
  printf '\n'

  if [ "$DRY_RUN" = 1 ]; then
    printf 'would remove ............... %-4s  %s\n' \
      "$(($(count would-remove) + $(count would-remove-after-unlock)))" "$(human_kb "$would_kb")"
  else
    printf 'removed .................... %-4s  %s\n' "$(count removed)" \
      "$(human_kb "$(sum_kb removed)")"
    printf 'removed after unlocking .... %-4s  %s\n' "$(count removed-after-unlock)" \
      "$(human_kb "$(sum_kb removed-after-unlock)")"
    printf 'reclaimed .................. %s\n' "$(human_kb "$removed_kb")"
    if [ -n "${DISK_BEFORE:-}" ] && [ -n "${DISK_AFTER:-}" ]; then
      # The whole-volume delta is not the same number as the sum of what was removed, and saying so
      # is the point: other processes write to this disk while the sweep runs.
      printf 'disk free .................. %s -> %s  (volume delta %s)\n' \
        "$(human_kb "$DISK_BEFORE")" "$(human_kb "$DISK_AFTER")" \
        "$(human_kb $((DISK_AFTER - DISK_BEFORE)))"
    else
      printf 'disk free .................. could not be read\n'
    fi
  fi
  printf '\n'

  printf 'caches\n'
  while IFS="$SEP" read -r name status detail; do
    printf '  %-6s %-13s %s\n' "$name" "$status" "$detail"
  done <"$TMP/caches"
  printf '\n'

  # EVERY worktree that was not removed, with the reason. A run that quietly skipped something
  # is the failure this section exists to make impossible: if it is not here, it was not seen.
  printf 'KEPT, AND WHY - every one, so nothing is skipped in silence\n'
  local any=0
  while IFS="$SEP" read -r verdict path branch kb detail; do
    # EVERY REMOVAL VERDICT CONTAINS "remove", AND NO OTHER VERDICT DOES. That convention is what
    # makes this one pattern sufficient, and it replaced a hardcoded list of the four removal
    # verdicts that had to be kept in step with the fourteen this file emits. The coupling was the
    # problem: add a fifth removal verdict later, forget this line, and the removal is reported
    # under KEPT - in the one section whose entire purpose is that nothing is skipped in silence.
    # A test pins the convention so it cannot rot.
    case "$verdict" in
    *remove*) continue ;;
    esac
    any=1
    printf '  [%s] %s\n' "$verdict" "$path"
    printf '      %s\n' "$detail"
  done <"$TMP/rows"
  [ "$any" = 0 ] && printf '  (nothing was kept)\n'
  printf '\n'

  if [ -s "$TMP/unreadable-new" ]; then
    # ONLY THE NEW ONES. The summary line carries the total; this section carries what actually
    # raised the gap. Printing all 121 buried the two that mattered, so "listed at the end" pointed
    # at something unsearchable - the same defect one layer down.
    printf 'NEWLY-UNREADABLE DIRECTORIES, so any worktree inside them was not examined.\n'
    printf 'New since the last run. The full known set of %s is recorded at\n' "${UNREADABLE_TOTAL:-0}"
    printf '  %s\n' "$UNREADABLE_BASELINE"
    sed 's/^/  /' "$TMP/unreadable-new"
    printf '\n'
  fi

  if [ "$(count failed)" != 0 ] || [ "$(count rescue-failed)" != 0 ]; then
    printf 'THESE NEED A HUMAN\n'
    awk -F'\037' '$1 == "failed" || $1 == "rescue-failed" {printf "  %s\n      %s\n", $2, $5}' \
      "$TMP/rows"
    printf '\n'
  fi

  # Tests the VERDICT FIELD, not the line. A lock reason and a git error message are both free
  # text that reaches the detail field, and either could contain the word "remove" - git's own
  # refusal literally does. A whole-line grep would print this section with nothing in it.
  if awk -F'\037' '$1 ~ /remove/ {found = 1} END {exit !found}' "$TMP/rows" 2>/dev/null; then
    printf 'REMOVED (branches and commits are untouched and still in the object store)\n'
    awk -F'\037' '$1 ~ /remove/ {printf "  [%s] %s\n      %s, %s\n", $1, $2, $3, $5}' "$TMP/rows"
    printf '\n'
  fi
}

mkdir -p "$LOG_DIR" 2>/dev/null
REPORT_FILE="$LOG_DIR/reclaim-$(date -u +%Y-%m-%dT%H%M%SZ).md"

# Rendered once, then written twice, because the durable copy and the copy on screen must be
# the same text. The gap list is finalised before rendering, so a failure to write the report
# cannot appear inside the report - it goes to stderr where a launchd log will pick it up.
report >"$TMP/report" 2>&1
if ! cp "$TMP/report" "$REPORT_FILE" 2>/dev/null; then
  printf 'WARNING: the report could not be written to %s\n' "$REPORT_FILE" >&2
  REPORT_FILE="(not written)"
fi

cat "$TMP/report"
printf 'report: %s\n' "$REPORT_FILE"

# WHAT COUNTS AS A RUN, for --if-due. Written HERE - after the sweep, not before it - and that is
# a decision with a live tradeoff either way:
#
#   at START:      a run that crashes in its first minute suppresses itself for a week. That
#                  reproduces the exact defect being fixed (a silently skipped week) and adds a
#                  new way to reach it.
#   at COMPLETION: a run that HANGS never records, so the next login runs it again.
#
# Completion wins because the hang is already bounded and the crash is not. This script takes a
# lock (LOCK_DIR) for the whole sweep, so a second run while the first is still going refuses at
# once with exit 2 and removes nothing - a hung run costs a refusal per login, not a second
# deletion pass. Nothing bounds the crash case.
#
# And it is reached only from below the sweep, which is what makes "a run that started and failed
# is not a run" true by construction rather than by a flag: every exit-2 path above - a missing
# tool, a lock another run holds, a session registry that could not be read - leaves the record
# untouched, so the next --if-due run is still due. Exit 1 DOES record: "swept, with gaps" swept.
record_run() {
  # --dry-run changes nothing, and this record is a change. A preview that stamped the run would
  # spend the next real one - the same defect the unreadable-baseline write gate exists to prevent.
  [ "$DRY_RUN" = 0 ] || return 0
  # No mkdir: the report write above already created $LOG_DIR unconditionally, on this same
  # straight-line path with no exit or conditional in between, so a retry here could only fail
  # identically. A failed redirection makes the command fail without running it, so `if !` still
  # catches a write this cannot do.
  if ! date +%s >"$LAST_RUN_FILE"; then
    printf 'WARNING: the last-run record could not be written to %s\n' "$LAST_RUN_FILE" >&2
    printf 'The next --if-due run will sweep rather than skip, which is the safe direction.\n' >&2
  fi
}
record_run

# 0 clean sweep, 1 swept but with gaps, 2 refused before doing anything.
# A --if-due run that decided NOT DUE also exits 0: it is not a failure, and the reason is in the
# log above rather than in the exit code, so `launchctl list` does not read a normal skip as a
# broken job.
[ -s "$TMP/gaps" ] && exit 1
exit 0
