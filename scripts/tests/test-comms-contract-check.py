#!/usr/bin/env python3
"""Tests for hooks/comms-contract-check.py.

Every case answers one of the two questions the bead demands:
  - something that MUST be refused, proving the check can fail a message
  - something that MUST pass, proving it does not fire on ordinary prose

The false-positive half is not padding. Bead suffixes are three or four
characters, so they collide with English words and bare numbers, and a check
that cries wolf gets switched off. The collisions tested here are real: `part` is
a live bead suffix, and so are eleven pure-digit suffixes.

Run: python3 scripts/tests/test-comms-contract-check.py
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SUT_PATH = os.path.join(REPO, "hooks", "comms-contract-check.py")
FIXTURES = os.path.join(HERE, "fixtures", "comms-contract")

# The single most important strings in the wiring tests: what counts as the
# conductor, and what does not.
CONDUCTOR_CWD = "/Users/bethphipps/.local/share/agent-deck/conductor/hq"
OUTSIDE_CWD = "/Users/bethphipps/src/some-service"

_spec = importlib.util.spec_from_file_location("comms_contract_check", SUT_PATH)
sut = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sut)

# Bootstrap-RED sentinel, matching scripts/tests/test-conductor-signals.sh.
# Without it, a harness that recorded zero assertions would print "0 passed, 0
# failed" and exit 0 - green. This repo has NO continuous integration
# (jbrooksbartlett-sqmi), so this suite is the only gate and it has to prove it
# can report a failure:
#   EXPECT_BOOTSTRAP_RED=1 python3 scripts/tests/test-comms-contract-check.py
# must exit non-zero and show exactly one FAIL.
BOOTSTRAP_RED = os.environ.get("EXPECT_BOOTSTRAP_RED") == "1"

PASS = 0
FAIL = 0

# A frozen list, so the unit cases do not move when the real queue does. The
# live-list cases below deliberately use the real thing instead.
FROZEN = {
    "jbrooksbartlett-5r44": "bead",
    "5r44": "bead",
    "jbrooksbartlett-part": "bead",
    "part": "bead",
    "jbrooksbartlett-280": "bead",
    "280": "bead",
    "jbrooksbartlett-c39": "bead",
    "c39": "bead",
    "feature-feat-2026-08-18-comms-check": "session",
    "jbrooksbartlett-tram": "bead",
    "tram": "bead",
    "jbrooksbartlett-cyi": "bead",
    "cyi": "bead",
}


def ok(what: str) -> None:
    global PASS
    PASS += 1
    print(f"  ok    {what}")


def bad(what: str, detail: str = "") -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {what}")
    if detail:
        print(f"        {detail}")


def assert_flags(
    text: str,
    what: str,
    kind: str | None = None,
    token: str | None = None,
    line_no: int | None = None,
) -> None:
    violations, _ = sut.check(text, dict(FROZEN))
    matched = [
        v
        for v in violations
        if (kind is None or v.kind == kind)
        and (token is None or v.token == token)
        and (line_no is None or v.line_no == line_no)
    ]
    if matched:
        ok(what)
    else:
        bad(
            what,
            f"expected a violation (kind={kind}, token={token}, line_no={line_no}); "
            f"got {[(v.kind, v.token, v.line_no) for v in violations]!r}",
        )


def assert_clean(text: str, what: str, kind: str | None = None) -> None:
    violations, _ = sut.check(text, dict(FROZEN))
    matched = [v for v in violations if kind is None or v.kind == kind]
    if not matched:
        ok(what)
    else:
        bad(what, "expected no violation, got: " + "; ".join(v.detail for v in matched))


def fixture(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return fh.read()


# The sentinel runs BEFORE any real case, the position test-conductor-signals.sh
# uses, so it still reports even if a later case raises. The default path records
# a positive assertion, so "0 passed, 0 failed" can never read as green.
if BOOTSTRAP_RED:
    bad(
        "bootstrap-RED sentinel (EXPECT_BOOTSTRAP_RED=1 is set)",
        "deliberate failure, proving this harness can report one",
    )
else:
    ok("harness sanity - this suite can record a result")


# ---------------------------------------------------------------------------
print("\nKNOWN-BAD CORPUS - six verbatim conductor messages from 2026-08-15,")
print("the day the rule was broken in essentially every status report.")
# ---------------------------------------------------------------------------
live_ids, live_degradations = sut.load_live_identifiers()
if live_degradations:
    print("  NOTE partial live list: " + "; ".join(live_degradations))

for i in range(1, 7):
    name = f"known-bad-2026-08-15-{i}.md"
    text = fixture(name)
    violations, _ = sut.check(text, live_ids)
    if violations:
        kinds = sorted({v.kind for v in violations})
        ok(f"{name} refused ({len(violations)} violations: {', '.join(kinds)})")
    else:
        bad(
            f"{name} refused",
            "the check passed a message that is known to violate the contract",
        )

# The single worst shape in the corpus: a status table with ids leading rows.
text = fixture("known-bad-2026-08-15-2.md")
violations, _ = sut.check(text, live_ids)
if any(
    "**The Beads queue has never been pushed" in v.line
    or v.token in ("3co", "qab", "71v")
    for v in violations
):
    ok("known-bad-2 names the specific bare ids in its prose")
else:
    bad("known-bad-2 names the specific bare ids in its prose", repr(violations))

# ---------------------------------------------------------------------------
print("\nCONTRACT TEMPLATES - the four message shapes from section 8 must pass")
print("clean, instantiated with real live identifiers.")
# ---------------------------------------------------------------------------
for name in (
    "good-template-8.1-status.md",
    "good-template-8.2-decision.md",
    "good-template-8.3-started.md",
    "good-template-8.4-ready.md",
):
    text = fixture(name)
    violations, _ = sut.check(text, live_ids)
    if violations:
        bad(
            f"{name} passes clean",
            "; ".join(f"line {v.line_no}: {v.detail}" for v in violations),
        )
    else:
        ok(f"{name} passes clean")

# ---------------------------------------------------------------------------
print("\nFALSE POSITIVES - real collisions between bead suffixes and English.")
# ---------------------------------------------------------------------------
# `jbrooksbartlett-part` is a live bead. All three occurrences of "part" across
# the 2026-08-15 corpus are ordinary English.
assert_clean(
    "Playwright is collecting, and - the part that matters - all four lint rules exit 1.",
    "the word 'part' in prose is not read as bead `part`",
    kind="bare-identifier",
)
assert_clean(
    "And the part it cannot close, it handled the way I wanted.",
    "'the part it cannot close' is not read as an id",
    kind="bare-identifier",
)
# Eleven live suffixes are pure digits.
assert_clean(
    "The suite collected 280 tests across 19 files and every one of them passed.",
    "a bare number matching a digit-only suffix is not read as an id",
    kind="bare-identifier",
)
assert_flags(
    "I hit bead `280` while writing this and it cost real work.",
    "the same digits DO flag when written as an identifier (backticked, after 'bead')",
    kind="bare-identifier",
    token="280",
)
# Commit hashes need a digit, which no English word has.
assert_clean(
    "The facade in front of the cache accedes to whatever the caller asked for.",
    "all-letter words are not mistaken for commit hashes",
    kind="bare-identifier",
)
assert_flags(
    "Merged as d40c7871 under your grant.",
    "a real commit hash with no description is flagged",
    kind="bare-identifier",
)
# A bead title may legitimately contain a file path - do not double-flag it.
assert_clean(
    "jbrooksbartlett-5r44 - config_admin/client.py:707 writes blank namespaces on "
    "the production write path\nWhat that means: saved configs lose their section label.",
    "a bead title containing a file path is not double-flagged",
)

# ---------------------------------------------------------------------------
print("\nBARE vs DESCRIBED - the rule itself, in each accepted form.")
# ---------------------------------------------------------------------------
assert_flags(
    "Closing `5r44` now.", "a bare id in prose is refused", kind="bare-identifier"
)
assert_clean(
    "jbrooksbartlett-5r44 - Build the outgoing-message check that enforces the communication contract",
    "prose form: id, then the title as filed",
)
assert_clean(
    "- **Outgoing-message check for how I write to you** (5r44) - built, and going fine.",
    "list form: plain name first, id in brackets after",
)
assert_clean(
    "**`5r44`** (the check that refuses a message containing an unexplained code)",
    "parenthetical form: id, then a description",
)
assert_flags(
    "| `5r44` | Answered its three design decisions and is now implementing. |",
    "an id leading a table row is refused even though the next cell explains it",
    kind="id-leads-table-row",
)
# Contract section 2: repeat mentions may shorten, but never to bare.
assert_clean(
    "**Outgoing-message check for how I write to you** (5r44) - it is built.\n"
    "Later on: **the outgoing-message check** (5r44) is what I mean.",
    "a repeat mention may drop to id plus a short plain name",
)
assert_flags(
    "**Outgoing-message check for how I write to you** (5r44) - it is built.\n"
    "Later on: `5r44` is what I mean.",
    "a repeat mention may NOT drop to a bare id",
    kind="bare-identifier",
)
assert_flags(
    "The queue was never pushed. `c39` flagged it.",
    "prose merely adjacent to an id is not a description of it",
    kind="bare-identifier",
)
# A bead filed after the live list was pulled is still caught, by shape.
assert_flags(
    "Closing `jbrooksbartlett-zzz9` now.",
    "a full-form id absent from the live list is still caught by shape",
    kind="bare-identifier",
    token="jbrooksbartlett-zzz9",
)
# Contract template 8.3's handle line is a copy-paste target, not prose.
assert_clean(
    "Watch it: session feature-feat-2026-08-18-comms-check | "
    "agent-deck session output 0086a558-6a42 -q | tmux agentdeck_5r44",
    "the 'Watch it' handle line does not need descriptions",
)

# ---------------------------------------------------------------------------
print("\nHABIT WORDS - contract section 3. The word is never the violation;")
print("the missing explanation is.")
# ---------------------------------------------------------------------------
assert_flags(
    "The load-bearing agreement is that the counts match.",
    "'load-bearing' unglossed is refused",
    kind="unglossed-habit-word",
)
assert_clean(
    "The load-bearing (the part the conclusion actually rests on) agreement is that the counts match.",
    "'load-bearing' with a gloss passes",
    kind="unglossed-habit-word",
)
assert_flags(
    "I checked its provenance before trusting it.",
    "'provenance' unglossed is refused",
    kind="unglossed-habit-word",
)
assert_clean(
    "I checked its provenance (where it came from) before trusting it.",
    "'provenance' with a gloss passes",
    kind="unglossed-habit-word",
)
assert_flags(
    "That decision was asymmetric and I should have said so.",
    "'asymmetric' is on the list - it was used in the interview that agreed the contract",
    kind="unglossed-habit-word",
)
# "surface" is a habit word as a VERB only.
assert_clean(
    "The surface area of the change is small.",
    "'the surface' as a noun passes",
    kind="unglossed-habit-word",
)
assert_flags(
    "A mistake of mine surfaced, and it has cost real work.",
    "'surfaced' as a verb is refused",
    kind="unglossed-habit-word",
)

# ---------------------------------------------------------------------------
print("\nNOUN vs VERB - the four sentences from jbrooksbartlett-7qau.")
print("The old check flagged all four. The first three are nouns (false positives); the fourth IS a verb.")
# ---------------------------------------------------------------------------
# Case 1: a heading. "second" is an adjective modifying "surface" the noun.
assert_clean(
    "A second surface nobody has ever counted",
    "a heading: 'A second surface' - adjective before a noun is not the verb habit",
    kind="unglossed-habit-word",
)
# Case 2: in prose. "a live Home surface" - the noun at the end of a noun phrase.
assert_clean(
    "nothing in the default page assembly can select them on a live Home surface",
    "in prose: 'a live Home surface' - noun at the end of a noun phrase",
    kind="unglossed-habit-word",
)
# Case 3: quoting a bead title. "surfaces" is the object of "flags", a plain noun.
assert_clean(
    "comms-contract-check flags surfaces as an ungossed verb when it is a plain noun",
    "quoting a title: 'flags surfaces as' - noun followed by a preposition",
    kind="unglossed-habit-word",
)
# Case 4: this IS a genuine verb and SHOULD still be caught.
assert_flags(
    "the knowledge graph surfaces prior research",
    "a genuine verb: 'surfaces prior research' - verb taking a direct object",
    kind="unglossed-habit-word",
)

# Code is not the conductor talking.
assert_clean(
    "The branch is `eng-utils-0.11.0-provenance-and-prose-gate` and it is merged.",
    "a habit word inside a branch name in backticks is not prose",
    kind="unglossed-habit-word",
)
assert_clean(
    "Here is the command:\n```\ngit log --format=%H provenance.md\n```\n",
    "a habit word inside a fenced code block is not prose",
    kind="unglossed-habit-word",
)

# ---------------------------------------------------------------------------
print("\nDEGRADED MODE - if a live list cannot be read, the check must say so")
print("rather than pass everything in silence.")
# ---------------------------------------------------------------------------
original_run = sut._run
sut._run = lambda cmd: None
try:
    violations, degradations = sut.check(
        "Closing `jbrooksbartlett-zzz9` now, and its provenance is unclear."
    )
    if len(degradations) >= 2:
        ok("both unreadable sources are reported as degradations")
    else:
        bad("both unreadable sources are reported as degradations", repr(degradations))
    if any(v.kind == "bare-identifier" for v in violations):
        ok("shape-matched full-form ids are still checked with no live list")
    else:
        bad(
            "shape-matched full-form ids are still checked with no live list",
            repr(violations),
        )
    if any(v.kind == "unglossed-habit-word" for v in violations):
        ok("habit words are still checked with no live list")
    else:
        bad("habit words are still checked with no live list", repr(violations))
    report = sut.format_report(violations, degradations)
    if "PARTIAL CHECK" in report:
        ok("the report tells the reader the check was partial")
    else:
        bad("the report tells the reader the check was partial", report[-200:])
finally:
    sut._run = original_run

# ---------------------------------------------------------------------------
print("\nHOOK WIRING - self-scoping, blocking, and the loop guard.")
# ---------------------------------------------------------------------------


def run_hook(
    message: str,
    cwd: str = CONDUCTOR_CWD,
    stop_hook_active: bool = False,
    env_extra: dict | None = None,
) -> subprocess.CompletedProcess:
    """Drive the hook the way Claude Code does, as a subprocess over stdin JSON."""
    env = dict(os.environ)
    env.pop("COMMS_CONTRACT_CHECK_SCOPE", None)
    if env_extra:
        env.update(env_extra)
    payload = {
        "hook_event_name": "Stop",
        "cwd": cwd,
        "last_assistant_message": message,
        "stop_hook_active": stop_hook_active,
    }
    return subprocess.run(
        [sys.executable, SUT_PATH],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=90,
        env=env,
    )


VIOLATING = "Closing `jbrooksbartlett-zzz9` now."

# Out of scope: this hook is registered user-wide, so it fires in every session.
# It must do nothing, and say nothing, anywhere but the conductor.
res = run_hook(VIOLATING, cwd=OUTSIDE_CWD)
if res.returncode == 0 and not res.stdout.strip() and not res.stderr.strip():
    ok("a non-conductor session is untouched - exit 0, no output at all")
else:
    bad(
        "a non-conductor session is untouched",
        f"rc={res.returncode} stdout={res.stdout[:120]!r} stderr={res.stderr[:120]!r}",
    )

# In scope, first fire: block, and hand the model the violations.
res = run_hook(VIOLATING)
try:
    decision = json.loads(res.stdout)
except ValueError:
    decision = {}
if decision.get("decision") == "block" and "bare bead id" in decision.get("reason", ""):
    ok("the conductor's violating message is blocked, with the reason attached")
else:
    bad(
        "the conductor's violating message is blocked",
        f"rc={res.returncode} stdout={res.stdout[:200]!r}",
    )

# In scope, second fire: blocking again would loop forever.
res = run_hook(VIOLATING, stop_hook_active=True)
if (
    res.returncode == 0
    and "decision" not in res.stdout
    and "CONTRACT CHECK FAILED" in res.stderr
):
    ok("a second fire in the same turn warns instead of blocking, so it cannot loop")
else:
    bad(
        "a second fire warns instead of blocking",
        f"rc={res.returncode} stdout={res.stdout[:120]!r} stderr={res.stderr[:120]!r}",
    )

# In scope and compliant: silence.
res = run_hook(fixture("good-template-8.1-status.md"))
if res.returncode == 0 and not res.stdout.strip():
    ok("a compliant conductor message passes in silence")
else:
    bad(
        "a compliant conductor message passes in silence",
        f"rc={res.returncode} stdout={res.stdout[:200]!r}",
    )

# ---------------------------------------------------------------------------
print("\nREGRESSIONS FIXED BY REVIEW - each of these used to behave wrongly.")
# ---------------------------------------------------------------------------
# Habit words used to match only (?:s|ly)?, so the noun was caught and the verb
# habit - the actual complaint - was missed.
for text, what in (
    (
        "He vetoed it without saying why.",
        "'vetoed' is caught (was missed: only s/ly matched)",
    ),
    ("He vetoes anything that costs money.", "'vetoes' is caught (was missed)"),
    ("She is vetoing the whole approach.", "'vetoing' is caught (was missed)"),
    ("I am surfacing this now.", "'surfacing' is caught (was missed)"),
    (
        "The two paths are orthogonally different.",
        "'orthogonally' is caught (was missed)",
    ),
    ("We made the writes idempotently.", "'idempotently' is caught"),
):
    assert_flags(text, what, kind="unglossed-habit-word")
assert_clean(
    "The veto (his right to refuse) still stands.",
    "a glossed noun still passes",
    kind="unglossed-habit-word",
)

# The handle-line exemption used to apply to the WHOLE line whenever it had three
# or more pipe-separated segments and any one was a command.
assert_flags(
    "`5r44` is done | agent-deck session output x -q | tmux foo",
    "a bare id in the PROSE segment of a handle line is still flagged",
    kind="bare-identifier",
)
assert_clean(
    "Watch it: tmux agentdeck_5r44 | agent-deck session output 0086a558-6a42 -q | "
    "session feature-feat-2026-08-18-comms-check",
    "a handle line is still exempt when the command segment is not first",
)

# _has_gloss and description shape C disagreed on a comma before the bracket.
assert_clean(
    "**`5r44`**, (the check that refuses an unexplained code) is built.",
    "a comma before the bracket is accepted for an identifier",
)
assert_clean(
    "Its provenance, (where it came from), is clear.",
    "a comma before the bracket is accepted for a habit word",
    kind="unglossed-habit-word",
)

# The English-word test is the system dictionary, not a hand-kept list.
assert_clean(
    "The tram arrives every ten minutes without fail.",
    "a dictionary word matching a live suffix is not read as an id in prose",
    kind="bare-identifier",
)
assert_flags(
    "I hit bead `tram` while writing this.",
    "the same word DOES flag in an identifier context",
    kind="bare-identifier",
)
assert_flags(
    "Closing `cyi` now.",
    "a NON-dictionary suffix is still flagged in plain prose",
    kind="bare-identifier",
)

# ---------------------------------------------------------------------------
print("\nENTRY POINTS - the blocking path must not degrade into the CLI.")
# ---------------------------------------------------------------------------
res = run_hook(
    VIOLATING, env_extra={"COMMS_CONTRACT_CHECK_SCOPE": "some-service"}, cwd=OUTSIDE_CWD
)
if json.loads(res.stdout or "{}").get("decision") == "block":
    ok(
        "COMMS_CONTRACT_CHECK_SCOPE redirects the scope, so the guard is testable elsewhere"
    )
else:
    bad(
        "COMMS_CONTRACT_CHECK_SCOPE redirects the scope", f"stdout={res.stdout[:160]!r}"
    )

res = subprocess.run(
    [sys.executable, SUT_PATH, "--hook"],
    input=json.dumps(
        {
            "hook_event_name": "Stop",
            "cwd": CONDUCTOR_CWD,
            "last_assistant_message": VIOLATING,
            "stop_hook_active": False,
        }
    ),
    capture_output=True,
    text=True,
    timeout=90,
)
if json.loads(res.stdout or "{}").get("decision") == "block":
    ok("an explicit --hook flag still blocks, so the registration may gain arguments")
else:
    bad(
        "an explicit --hook flag still blocks",
        f"rc={res.returncode} stdout={res.stdout[:160]!r}",
    )

res = subprocess.run(
    [sys.executable, SUT_PATH],
    input='{"not": "a hook payload"}',
    capture_output=True,
    text=True,
    timeout=90,
)
if res.returncode == 64 and "usage" in res.stderr.lower():
    ok("stdin that is not a hook payload reports usage rather than silently passing")
else:
    bad(
        "stdin that is not a hook payload reports usage",
        f"rc={res.returncode} stderr={res.stderr[:160]!r}",
    )

frozen_path = os.path.join(HERE, "fixtures", "comms-contract", ".frozen-ids.json")
draft_path = os.path.join(HERE, "fixtures", "comms-contract", ".draft.md")
try:
    with open(frozen_path, "w", encoding="utf-8") as fh:
        json.dump(FROZEN, fh)
    with open(draft_path, "w", encoding="utf-8") as fh:
        fh.write("Closing `5r44` now.\n")
    res = subprocess.run(
        [sys.executable, SUT_PATH, "--file", draft_path, "--identifiers", frozen_path],
        capture_output=True,
        text=True,
        timeout=90,
    )
    if res.returncode == 1 and "bare bead id" in res.stdout:
        ok(
            "--identifiers checks against a frozen list, so a by-hand run is reproducible"
        )
    else:
        bad(
            "--identifiers checks against a frozen list",
            f"rc={res.returncode} stdout={res.stdout[:160]!r}",
        )
finally:
    for path in (frozen_path, draft_path):
        if os.path.exists(path):
            os.remove(path)

# ---------------------------------------------------------------------------
print("\nCRASH BEHAVIOUR - a broken check must fail loudly, not silently.")


# ---------------------------------------------------------------------------
# The sibling Stop hook (plugins/jbb-feature-dev/hooks/followup_capture.py) swallows
# every exception in silence, and says why: it is a best-effort reminder. This one
# is not, so it says so on stderr and still lets the turn end.
def _boom(_payload):
    raise RuntimeError("simulated internal failure")


original_run_stop_hook = sut.run_stop_hook
original_stderr = sys.stderr
sut.run_stop_hook = _boom
sys.stderr = io.StringIO()
try:
    rc = sut.main(
        ["--hook"],
        stdin=io.StringIO(
            json.dumps({"hook_event_name": "Stop", "cwd": CONDUCTOR_CWD})
        ),
    )
    captured = sys.stderr.getvalue()
finally:
    sut.run_stop_hook = original_run_stop_hook
    sys.stderr = original_stderr

if rc == 0:
    ok("a crashing check exits 0, so it cannot wedge the conductor's turn")
else:
    bad("a crashing check exits 0", f"got exit code {rc}")
if "FAILED TO RUN" in captured and "NOT checked" in captured:
    ok("a crashing check says so on stderr, rather than passing the message in silence")
else:
    bad("a crashing check reports on stderr", f"stderr was {captured[:200]!r}")

# ---------------------------------------------------------------------------
print("\nTHE SIX IDENTIFIER KINDS - contract section 1 lists six, so all six")
print("need a case that actually fires. Three had none.")
# ---------------------------------------------------------------------------
# Before this block, deleting the whole file-path branch would not have failed a
# single case: every path in the suite was mid-sentence, which never reaches it.
assert_flags(
    "See the fix:\n- config_admin/client.py:707\n",
    "a file path alone in a bullet is flagged",
    kind="bare-identifier",
    token="config_admin/client.py:707",
)
assert_flags(
    "| config_admin/client.py:707 | fixed |",
    "a file path alone in a table cell is flagged",
)
assert_clean(
    "The fix in config_admin/client.py:707 stops blank namespaces reaching production.",
    "a file path inside a sentence is NOT flagged - the deliberate narrowing",
    kind="bare-identifier",
)
# compose.ts is contract section 1's own worked example of an opaque identifier,
# and a pattern requiring a "/" could not see it in any position.
assert_flags(
    "- compose.ts",
    "a bare filename with no directory is flagged when it stands alone",
    token="compose.ts",
)
assert_clean(
    "We rewrote compose.ts this morning to drop the shim.",
    "the same filename inside a sentence is not flagged",
    kind="bare-identifier",
)
assert_clean(
    "- e.g.",
    "prose punctuation is not read as a filename",
    kind="bare-identifier",
)
assert_flags("See #142 for context.", "a bare PR number is flagged", token="#142")
assert_flags(
    "The write failed with NON_OWNED_CONFIG_DENIED.",
    "a bare constant is flagged",
    token="NON_OWNED_CONFIG_DENIED",
)
assert_clean(
    "It failed with NON_OWNED_CONFIG_DENIED - the write is refused because the config "
    "belongs to another team.",
    "a described constant passes",
)

# ---------------------------------------------------------------------------
print("\nSILENT-PASS REGRESSIONS - every one of these let a violation through,")
print("and each was reproduced before it was fixed.")
# ---------------------------------------------------------------------------
# Found independently by two reviewers. A degradation means the live id list could
# not be read, and that list is the only thing that catches a bare short suffix.
original_run = sut._run
sut._run = lambda cmd: None
try:
    violations, degradations = sut.check("Closing cyi now, it went fine.")
    if not violations and len(degradations) == 2:
        ok("degraded run finds nothing, because the list it needed was unreadable")
    else:
        bad("degraded run finds nothing", f"{violations!r} {degradations!r}")

    captured = io.StringIO()
    saved_stderr, sys.stderr = sys.stderr, captured
    try:
        rc = sut.run_stop_hook(
            {
                "cwd": CONDUCTOR_CWD,
                "last_assistant_message": "Closing cyi now, it went fine.",
                "stop_hook_active": False,
            }
        )
    finally:
        sys.stderr = saved_stderr
    if rc == 0 and "RAN PARTIALLY" in captured.getvalue():
        ok(
            "a degraded run with NO violations still reports, instead of passing in silence"
        )
    else:
        bad(
            "a degraded run with no violations still reports",
            f"rc={rc} stderr={captured.getvalue()[:200]!r}",
        )
finally:
    sut._run = original_run

# A short fragment containing a handle label is not a handle line.
for fragment in ("branch cyi", "pr cyi merged", "session cyi done"):
    assert_flags(
        fragment,
        f"{fragment!r} is flagged - a label word does not make a fragment a handle",
        kind="bare-identifier",
    )

# A connector phrase is not an explanation.
assert_flags(
    "Closing `5r44` - that is, ok.",
    "'that is, ok.' does not satisfy the check",
    kind="bare-identifier",
)
assert_clean(
    "Closing `5r44` - that is, the outgoing-message contract check is now built.",
    "a real explanation after the connector does pass",
)

# A habit word only gets a pass inside its OWN gloss.
assert_flags(
    "The load-bearing (provenance is unclear) agreement holds.",
    "a habit word inside another word's gloss is still flagged",
    kind="unglossed-habit-word",
    token="provenance",
)
assert_clean(
    "The veto (his right to refuse) still stands.",
    "a genuine gloss still passes",
    kind="unglossed-habit-word",
)
# Hyphenated compounds used to escape the pattern entirely.
assert_flags(
    "provenance-based reasoning drove the decision.",
    "a habit word inside a hyphenated compound is flagged",
    kind="unglossed-habit-word",
    token="provenance",
)
assert_clean(
    "The surface-level fix is fine.",
    "'surface-level' after an article is still an innocent noun",
    kind="unglossed-habit-word",
)

# The commit-hash shape claimed no English word could match it.
assert_clean(
    "The decade2020 rollout was smooth.",
    "an English word glued to digits is not read as a commit hash",
    kind="bare-identifier",
)
assert_flags(
    "Merged as d40c7871 under your grant.",
    "a real commit hash is still flagged",
    token="d40c7871",
)

# ---------------------------------------------------------------------------
print("\nASSERTION STRENGTH - pin the line and the token, not just the kind.")
# ---------------------------------------------------------------------------
assert_flags(
    "**Outgoing-message check** (5r44) - it is built.\nLater on: `5r44` is what I mean.",
    "the repeat-mention violation is reported on line 2, not line 1",
    kind="bare-identifier",
    token="5r44",
    line_no=2,
)
for text, seen, canonical in (
    ("He vetoed it without saying why.", "vetoed", "veto"),
    ("She is vetoing the whole approach.", "vetoing", "veto"),
    ("I am surfacing this now.", "surfacing", "surface"),
    ("The two paths are orthogonally different.", "orthogonally", "orthogonal"),
):
    assert_flags(
        text,
        f"{seen!r} is reported as habit word {canonical!r}, not some other word",
        kind="unglossed-habit-word",
        token=canonical,
    )

# ---------------------------------------------------------------------------
print("\nCORPUS - each fixture pins one catch that only the LIVE id list can make,")
print("so a broken live-list integration cannot hide behind habit words.")
# ---------------------------------------------------------------------------
# Five of six fixtures previously passed on habit words and shape matches alone, so
# they would still have reported "refused" with bd and agent-deck both failing.
for name, expected in (
    ("known-bad-2026-08-15-2.md", {"3co", "qab", "71v"}),
    ("known-bad-2026-08-15-4.md", {"o26", "201"}),
    ("known-bad-2026-08-15-5.md", {"qab"}),
):
    found_tokens = {v.token for v in sut.check(fixture(name), live_ids)[0]}
    hit = expected & found_tokens
    if hit:
        ok(f"{name} pins a live-list catch ({', '.join(sorted(hit))})")
    else:
        bad(
            f"{name} pins a live-list catch",
            f"expected one of {sorted(expected)}; got {sorted(found_tokens)}",
        )

# A CLOSED bead is exactly what a status report is about, and `bd list` hides
# closed work by default. Before the pull was widened, the four bare ids leading
# rows in the worst message of the corpus were invisible.
table_report = fixture("known-bad-2026-08-15-2.md")
row_led = {
    v.token
    for v in sut.check(table_report, live_ids)[0]
    if v.kind == "id-leads-table-row"
}
if {"cyi", "c39", "9oi"} <= row_led:
    ok("closed beads leading table rows are caught (cyi, c39, 9oi - all CLOSED)")
else:
    bad(
        "closed beads leading table rows are caught",
        f"expected cyi, c39 and 9oi among the row-leading violations; got {sorted(row_led)}",
    )

# ---------------------------------------------------------------------------
print("\nENVIRONMENT AND ENTRY POINTS")
# ---------------------------------------------------------------------------
# The no-dictionary fallback had never executed: every machine that ran this suite
# had /usr/share/dict/words. TECHNICAL_WORDS alone is a far smaller substitute, so
# pin what actually happens rather than assume it is equivalent.
sut._load_english_words.cache_clear()
original_paths = sut.DICTIONARY_PATHS
sut.DICTIONARY_PATHS = ("/nonexistent/dictionary",)
try:
    if sut._load_english_words() == frozenset():
        ok("with no dictionary installed the loader returns empty rather than raising")
    else:
        bad("with no dictionary the loader returns empty", "got a non-empty set")
    if sut._is_risky_bare_token("env"):
        ok("TECHNICAL_WORDS still protects technical tokens with no dictionary")
    else:
        bad("TECHNICAL_WORDS still protects technical tokens", "'env' judged not risky")
    if not sut._is_risky_bare_token("tram"):
        ok("but an ordinary word is NO LONGER protected - the documented degradation")
    else:
        bad("an ordinary word is no longer protected", "'tram' still judged risky")
finally:
    sut.DICTIONARY_PATHS = original_paths
    sut._load_english_words.cache_clear()

res = run_hook("   ")
if res.returncode == 0 and not res.stdout.strip():
    ok("a blank message short-circuits before any subprocess work")
else:
    bad(
        "a blank message short-circuits",
        f"rc={res.returncode} out={res.stdout[:120]!r}",
    )

res = subprocess.run(
    [sys.executable, SUT_PATH],
    input="not valid json {{{",
    capture_output=True,
    text=True,
    timeout=90,
)
if res.returncode == 0 and "FAILED TO RUN" in res.stderr:
    ok("malformed stdin reports rather than being the one silent path in the file")
else:
    bad("malformed stdin reports", f"rc={res.returncode} stderr={res.stderr[:160]!r}")

res = subprocess.run(
    [sys.executable, SUT_PATH, "--file"], capture_output=True, text=True, timeout=90
)
if res.returncode == 64:
    ok("--file with no path reports usage instead of crashing")
else:
    bad("--file with no path reports usage", f"rc={res.returncode}")

if sut.run_cli([]) == 64:
    ok("run_cli defends its own argv rather than trusting its caller")
else:
    bad("run_cli defends its own argv", "expected exit 64")

# PATH_RE was quadratic: 200,001 characters with no slash took 17.3 seconds.
big = "a." * 100_000 + "a"
started = time.perf_counter()
sut.PATH_RE.findall(big)
elapsed = time.perf_counter() - started
if elapsed < 1.0:
    ok(
        f"PATH_RE stays linear on 200k characters with no slash ({elapsed * 1000:.0f} ms)"
    )
else:
    bad("PATH_RE stays linear on 200k characters", f"took {elapsed:.1f}s")

# ---------------------------------------------------------------------------
print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
