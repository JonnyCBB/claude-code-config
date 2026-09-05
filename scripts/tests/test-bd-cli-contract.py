#!/usr/bin/env python3
"""Every `bd` command this repo documents must be one the installed `bd` accepts.

WHY THIS EXISTS. On 2026-08-19 three separate files were found telling agents to
run `bd create ... --status deferred`, a flag bd 1.2.2 does not have. One of them
was the follow-up capture rule in CLAUDE.md, which loads on every task; another
was the stop hook that exists to catch a missed follow-up, printing the broken
command as its own remediation text. The same upgrade had already broken the
pre-triage agent (`--if-status`) and switchboard. Nothing noticed, because
nothing ever handed a documented command to a real bd.

So this is not a unit test of a function. It is an ACCEPTANCE test of the
instructions: it reads what we tell agents to type, and asks bd whether it would
accept it.

WHAT IT CANNOT DO. It checks that a subcommand exists and that its flags are
real. It does not check that the command means what the prose claims, and it
cannot check argument VALUES - `bd update -s frobnicate` passes here.

Run: python3 scripts/tests/test-bd-cli-contract.py
"""

from __future__ import annotations

import functools
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from typing import NamedTuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

# `bd` lives in a Homebrew prefix that ~/.zshenv puts on PATH, and a hook, a
# launchd job or `env -i` is not a login shell. Without this the `shutil.which`
# gate below finds nothing, the run SKIPS, and it exits 0 - a test whose entire
# premise is "nothing ever handed a documented command to a real bd" quietly
# checking nothing. Verified: `env -i PATH=/usr/bin:/bin` skips without it.
# Prepended rather than appended, matching hooks/comms-contract-check.py:57,
# because appending would let a hijacked PATH entry answer first.
EXTRA_PATH_DIRS = ("/opt/homebrew/bin", "/usr/local/bin")


def _path() -> str:
    return os.pathsep.join([*EXTRA_PATH_DIRS, os.environ.get("PATH", "")])


def _bd_binary() -> str | None:
    return shutil.which("bd", path=_path())


# Files that tell a human or an agent to run `bd`. scripts/tests/ is excluded on
# purpose: fixtures there contain deliberately malformed commands.
SCAN_GLOBS = (
    "CLAUDE.md",
    "README.md",
    "docs/*.md",
    "hooks/*.py",
    "scripts/*.sh",
    "agents/*.md",
    "skills/*/SKILL.md",
    "plugins/*/README.md",
    "plugins/*/hooks/*.py",
    "plugins/*/skills/*/SKILL.md",
    "plugins/*/commands/*.md",
)

# Breakages that are real, already filed, and deliberately NOT fixed here. The
# bead id is required: a bare "known bad" list is how a gap becomes permanent.
#
# This list is checked in BOTH directions. An entry that has stopped being broken
# fails the test too, so a fixed bd release cannot leave stale exemptions behind.
KNOWN_GAPS: dict[tuple[str, str], str] = {
    ("reclaim", ""): "jbrooksbartlett-m248 - work leases are 1.2.x-only and "
    "v1.2.2 withdrew them; the conductor docs still prescribe them",
    ("heartbeat", ""): "jbrooksbartlett-m248 - as above",
    # `bd leases` is broken the same way and is covered by the same bead, but it
    # is deliberately NOT listed: it appears only as unbackticked prose, which
    # this scanner does not read as a command. An exemption for something never
    # checked is worse than no exemption, and the both-directions check above
    # rejected it - which is the check earning its place on its first run.
}

# Flags bd accepts on every subcommand; they never appear in a subcommand's own
# flag table, so checking them against it would report false breakages.
GLOBAL_FLAGS = frozenset(
    {
        "--json",
        "--db",
        "--quiet",
        "-q",
        "--verbose",
        "-v",
        "--readonly",
        "--actor",
        "--directory",
        "-C",
        "--global",
        "--sandbox",
        "--help",
        "-h",
        "--profile",
        "--dolt-auto-commit",
        "--ignore-schema-skew",
    }
)

# `bd` followed by a word. The lookbehind keeps `$bd`, `./bd` and `foo-bd` out.
_INVOCATION = re.compile(r"(?<![\w./$-])bd\s+([a-z][a-z-]*)(.*)$")
_FLAG = re.compile(r"(?<![\w-])(--?[a-zA-Z][\w-]*)")
# A flag list ends at a pipe, a statement separator, or another command. Without
# this, `bd show $(cut -f1 ...)` reports `-f1` as a flag of `bd show`.
_BOUNDARY = re.compile(r"[|;]|&&|\bgrep\b|\bxargs\b|\bpython3\b|\bjq\b")
# A command substitution is REMOVED, not treated as a boundary. Truncating at it
# threw away the outer command's own flags: on the real line
#   bd show $(cut -f1 ... | tr '\n' ' ') --json
# from scripts/conductor-signals.sh, everything from `$(` onward was discarded and
# the trailing `--json` was never checked. A removed flag written that way would
# have been invisible to this whole file - which is the exact failure it exists to
# catch. Non-greedy, so nested substitutions leave a harmless remnant rather than
# eating the rest of the line.
_SUBSTITUTION = re.compile(r"\$\([^)]*\)|`[^`]*`")


def _outer_flags(rest: str) -> list[str]:
    """Flags belonging to THIS bd command, with substitutions cut out first."""
    rest = _SUBSTITUTION.sub(" ", rest)
    return [f for f in _FLAG.findall(_BOUNDARY.split(rest)[0]) if f not in GLOBAL_FLAGS]


# Bootstrap-RED sentinel, matching scripts/tests/test-comms-contract-check.py and
# test-conductor-signals.sh. This repo has NO continuous integration
# (jbrooksbartlett-sqmi), so these suites are the only gate and each has to prove
# it can report a failure:
#   EXPECT_BOOTSTRAP_RED=1 python3 scripts/tests/test-bd-cli-contract.py
# must exit non-zero. `self_test` below proves something stronger and narrower -
# that the SCANNER detects a specific historical break - but it says nothing
# about whether the harness around it can still fail, which is what this covers.
BOOTSTRAP_RED = os.environ.get("EXPECT_BOOTSTRAP_RED") == "1"

FAILURES = 0


def fail(message: str) -> None:
    global FAILURES
    print(f"FAIL: {message}")
    FAILURES += 1


# -- reading the installed bd -------------------------------------------------


def _run_bd(*args: str) -> subprocess.CompletedProcess[str]:
    """Every `bd` call in this file, so neither the PATH fix above nor the timeout
    below can be forgotten at one of three call sites.

    The timeout matches scripts/tests/test-comms-contract-check.py, which puts one
    on every subprocess call it makes. This file's whole premise is that the
    installed bd may not behave the way we expect, and a bd that hangs or waits on
    input would otherwise hang a hand-run suite with no recourse but Ctrl-C.
    """
    try:
        return subprocess.run(
            [_bd_binary() or "bd", *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            env={**os.environ, "PATH": _path()},
        )
    except subprocess.TimeoutExpired:
        fail(f"`bd {' '.join(args)}` did not return within 30s; treating as broken")
        return subprocess.CompletedProcess(
            args=list(args), returncode=124, stdout="", stderr="timeout"
        )


@functools.cache
def bd_help(subcommand: str) -> tuple[int, str]:
    """`bd <sub> --help`, once per subcommand.

    Most of this test's wall time is bd process startup, so the cache is the
    difference between 13 spawns and 37. Memoized on the subcommand ALONE, which
    is only correct because PATH and os.environ never change within one run of
    this script - a future self-test that stubs PATH would need to take it as a
    parameter instead.
    """
    done = _run_bd(subcommand, "--help")
    return done.returncode, done.stdout + done.stderr


def known_subcommands() -> frozenset[str]:
    """Every verb in `bd --help`, so prose like "bd or" is not read as a command."""
    done = _run_bd("--help")
    return frozenset(
        m.group(1) for m in re.finditer(r"(?m)^  ([a-z][a-z-]*)\s{2,}\S", done.stdout)
    )


def subcommand_exists(subcommand: str) -> bool:
    code, text = bd_help(subcommand)
    return not (code != 0 and "unknown command" in text)


def flag_exists(subcommand: str, flag: str) -> bool:
    """Whether `flag` appears in the subcommand's own flag table.

    Matched against the start of a help line so that a flag named in a
    DESCRIPTION - `--claim` is mentioned in several - is not mistaken for a flag
    the subcommand accepts.
    """
    _, text = bd_help(subcommand)
    return bool(re.search(rf"(?m)^\s+(-\w,\s+)?{re.escape(flag)}[\s,=]", text))


# -- reading this repo --------------------------------------------------------


_FENCE = re.compile(r"^(`{3,})(.*)$")
# Hot: called once per markdown line across every scanned file.
_BACKTICK_SPAN = re.compile(r"`([^`]+)`")


class CodeSpans(NamedTuple):
    """What one line contributed, matching the Found/Violation/HabitWord
    NamedTuples in hooks/comms-contract-check.py rather than a bare 3-tuple."""

    spans: list[str]
    fence: int
    is_prose: bool


def code_spans(path: str, line: str, fence: int) -> CodeSpans:
    """The parts of `line` that are code, the fence state, and whether it is prose.

    Returns SPANS, not one joined string. Joining them with a space invented a
    command: "`bd`, `gh` and `agent-deck` are stubbed on PATH" became `bd gh`,
    reported as a missing subcommand that nobody had ever written.

    In markdown, prose mentioning a command is not an instruction to run it, so
    only fenced blocks and backticked spans count - and being inside one is
    itself the evidence that it is a command, so a bare `bd reclaim` with no
    arguments still counts. In .py and .sh every line is scanned, because the
    CLAUDE.md command was found verbatim inside a Python string; there the
    argument shape is the only signal available.
    """
    if not path.endswith(".md"):
        return CodeSpans([line], fence, True)
    marker = _FENCE.match(line.lstrip())
    if marker:
        width = len(marker.group(1))
        # CommonMark: a CLOSING fence may carry nothing but whitespace. "``` end
        # example" inside an open block does not close it. Treating it as a close
        # silently drops every later line out of the fence, and an unbackticked
        # command there is then scanned as prose and never seen at all.
        if fence and marker.group(2).strip():
            return CodeSpans([line], fence, False)
        # Track the OPENING width rather than toggling on any ```. A four-backtick
        # fence legitimately wraps three-backtick blocks - there is one in
        # plugins/eng-utils/skills/mma-tune-alerts/SKILL.md:143 - and a plain
        # toggle inverts its state at the inner fences, so from there on prose is
        # read as code and code as prose. Only a marker at least as wide as the
        # one that opened the block closes it.
        if fence and width >= fence:
            return CodeSpans([], 0, False)
        if not fence:
            return CodeSpans([], width, False)
        return CodeSpans([], fence, False)
    if fence:
        return CodeSpans([line], fence, False)
    return CodeSpans(_BACKTICK_SPAN.findall(line), fence, False)


def join_continuations(text: str) -> Iterator[tuple[int, str]]:
    """Yield (line number, logical line), joining shell `\\` continuations.

    The capture command spans two lines; without this its `--deps` half is
    attributed to nothing and the break on line one is still found, but a future
    two-line command could hide a flag entirely.
    """
    buffer, start = "", 0
    for number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.rstrip()
        if stripped.endswith("\\"):
            start = start or number
            buffer += stripped[:-1] + " "
            continue
        yield (start or number, buffer + stripped)
        buffer, start = "", 0
    if buffer:
        yield (start, buffer)


def scan(paths: list[str], valid: frozenset[str]) -> dict[tuple[str, str], set[str]]:
    """Map (subcommand, flag) -> {"file:line"} for everything the repo documents."""
    found: dict[tuple[str, str], set[str]] = {}
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        fence = 0
        for number, line in join_continuations(text):
            spans, fence, needs_arg_shape = code_spans(path, line, fence)
            for span in spans:
                for match in _INVOCATION.finditer(span):
                    subcommand, rest = match.group(1), match.group(2) or ""
                    # In a file scanned line-by-line, an unrecognised word is only
                    # a subcommand when what follows reads as arguments. That
                    # catches a REMOVED verb without a list of English words. In
                    # markdown the backticks already said it was a command.
                    if (
                        subcommand not in valid
                        and needs_arg_shape
                        and not _looks_like_a_command(rest)
                    ):
                        continue
                    flags = _outer_flags(rest)
                    where = f"{os.path.relpath(path, REPO)}:{number}"
                    for flag in flags or [""]:
                        found.setdefault((subcommand, flag), set()).add(where)
    return found


def _looks_like_a_command(rest: str) -> bool:
    """Whether what follows reads as arguments rather than English."""
    return bool(re.match(r"\s*(--?[a-zA-Z]|[\w-]+-[a-z0-9]{3,}|\"|')", rest))


def repo_files() -> list[str]:

    paths: list[str] = []
    for pattern in SCAN_GLOBS:
        paths += sorted(glob.glob(os.path.join(REPO, pattern)))
    return [p for p in paths if os.path.isfile(p)]


# -- the checks ---------------------------------------------------------------


# The follow-up capture command is deliberately written out in three places
# rather than centralised: CLAUDE.md is always in context and the rule it states
# is "do not pause to go and read something first"; the hook renders it into a
# process that cannot resolve a pointer, and ships as a plugin installable
# without this CLAUDE.md; the skill already delegates the three surrounding rules
# and repeats only the command. That triplication is the right call, but it is
# only SAFE if something asserts the copies still agree - and the flag check
# above cannot, because it discards argument values. One copy drifting to
# `-s open` would leave every agent-filed bead live on creation and every check
# in this file would still pass.
class Ambiguous(Exception):
    """More than one block in a file looks like the capture command."""

    def __init__(self, path: str, count: int) -> None:
        super().__init__(path)
        self.path, self.count = path, count


CAPTURE_RULE_SITES = (
    "CLAUDE.md",
    "plugins/jbb-feature-dev/hooks/followup_capture.py",
    "plugins/jbb-feature-dev/skills/sweep-followups/SKILL.md",
)


def capture_rule_shape(path: str) -> tuple[tuple[str, ...], ...]:
    """The (verb, arg-or-flag...) skeleton of the capture command in one file.

    Placeholders differ between copies on purpose - `<current-id>` in the hook,
    `<the bead this session is working, if any>` in the skill - so quoted strings
    and angle-bracket placeholders are dropped and only the command SHAPE is
    compared: which verbs, which flags, which literal status values.

    Compared on the RENDERED text, not on source lines, because the hook's copy is
    split across three adjacent Python string literals - so a line-based reading
    sees `bd create` and `--deps` as unrelated commands and the two markdown
    copies as a third thing again.
    """
    with open(os.path.join(REPO, path), encoding="utf-8", errors="replace") as handle:
        text = handle.read()

    # The QUOTING CONSTRUCT is part of the shape, and has to be read before the
    # quote-stripping below destroys it. Without this the check compared only
    # verbs and flags, so CLAUDE.md moving its title into a quoted heredoc while
    # the other two copies still interpolated it inline - a real difference, and
    # the difference between executing a pasted title and not - compared equal.
    heredocs = sorted(set(re.findall(r"<<'([A-Za-z_][A-Za-z0-9_]*)'", text)))

    # Strip the plumbing each copy is wrapped in: Python escapes and quotes,
    # shell continuations, and the placeholders that differ on purpose.
    text = text.replace("\\n", " ").replace("\\", " ")
    text = re.sub(r"""['"]""", " ", text)
    text = re.sub(r"<[^>]*>", "X", text)
    text = re.sub(r"\$\{?\w+\}?|\$\(", " ", text)

    # EVERY `bd create`, not the first. All three files discuss the rule in prose
    # before stating it - the skill's very first mention is "`bd create` calls
    # make two issues" - so anchoring on the first hit reads the commentary and
    # concludes the command is missing.
    windows = []
    for match in re.finditer(r"bd create", text):
        candidate = text[match.start() : match.start() + 400]
        # A real invocation carries flags straight away. A prose mention -
        # "`bd create` ran", "`bd create` calls make two issues" - does not, and
        # both of those sit within 400 characters of the real command, so a
        # looser test picks up the commentary and reports a phantom difference.
        if not re.match(r"bd create\s+\S*\s+-[a-zA-Z]", candidate):
            continue
        if "agent-proposed" in candidate[:300] and "deferred" in candidate:
            windows.append(candidate)
    if not windows:
        return ()
    # MORE THAN ONE candidate is reported, never silently resolved. The obvious
    # rules - take the first, take the last - both quietly lock onto the wrong
    # block the moment someone adds a "do not write it like this any more"
    # counter-example, and a wrong window either invents a drift that is not there
    # or hides one that is. Ambiguity is a question for a human.
    if len(windows) > 1:
        raise Ambiguous(path, len(windows))
    window = windows[0]
    end = window.find("deferred")

    # Verbs, flags and literal status words in order - everything that decides
    # what the command DOES, and nothing that differs between copies by design.
    interesting = re.findall(
        r"(?<![\w-])(--?[a-zA-Z][\w-]*|\bcreate\b|\bupdate\b|\bdeferred\b|\bopen\b)",
        window[: end + len("deferred")],
    )
    return tuple([(f"heredoc:{h}",) for h in heredocs] + [(t,) for t in interesting])


def check_capture_rule_copies_agree() -> None:
    shapes = {}
    for path in CAPTURE_RULE_SITES:
        try:
            shapes[path] = capture_rule_shape(path)
        except Ambiguous as ambiguous:
            fail(
                f"{ambiguous.path} contains {ambiguous.count} blocks that all look "
                f"like the follow-up capture command, so this check cannot tell "
                f"which one is authoritative. If one of them is a counter-example, "
                f"reword it so it does not parse as a runnable command."
            )
            return
    empty = [p for p, s in shapes.items() if not s]
    if empty:
        fail(
            f"the follow-up capture command was not found in {empty}. Either it "
            f"moved and this check is now blind, or a copy was deleted."
        )
        return
    distinct = set(shapes.values())
    if len(distinct) > 1:
        rendered = "\n".join(
            f"        {p}: {' | '.join(' '.join(c) for c in s)}"
            for p, s in shapes.items()
        )
        fail(
            "the three copies of the follow-up capture command have drifted "
            "apart:\n" + rendered + "\n        They must stay the same command; "
            "a copy that differs is a copy that will file beads wrongly."
        )


def _scan_sample(
    sample: str, valid: frozenset[str], name: str = "sample.md"
) -> dict[tuple[str, str], set[str]]:
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(sample)
        return scan([path], valid)


# A flag run that includes `-l agent-proposed` is the capture rule being described
# even when no `bd` verb precedes it, because that label exists for exactly one
# purpose. plugins/jbb-feature-dev/README.md said "files the keepers as
# `-l agent-proposed --status deferred`" - a real, already-broken mention that the
# invocation scanner cannot see, in one of the very files this change had to fix.
_IMPLIED_CREATE = re.compile(
    r"-l\s+agent-proposed((?:\s+--?[a-zA-Z][\w-]*(?:\s+\S+)?)*)"
)


def check_implied_create_flags() -> None:
    """Flags written beside `-l agent-proposed` must be ones `bd create` accepts."""
    for path in repo_files():
        with open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        for match in _IMPLIED_CREATE.finditer(text):
            for flag in _FLAG.findall(match.group(1)):
                if flag in GLOBAL_FLAGS or flag_exists("create", flag):
                    continue
                fail(
                    f"`{flag}` is written beside `-l agent-proposed` in "
                    f"{os.path.relpath(path, REPO)}, but `bd create` has no such "
                    f"flag. Prose describing the capture rule has to stay as true "
                    f"as the command itself - this is how a dead flag survives in "
                    f"a file the command was already fixed in."
                )


# A title an agent might plausibly write, carrying both shell substitution forms.
# The backticked half is the realistic one: describing a command in a bead title is
# ordinary technical prose, and under the old wording it EXECUTED the command and
# stored its stdout in the title, at exit 0.
_HOSTILE_TITLE = "the `bd ready` query broke $(touch pwned) after the upgrade"


def _capture_block(text: str) -> list[str]:
    """The fenced bash block that states the capture command."""
    blocks: list[list[str]] = []
    current: list[str] | None = None
    fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            if fence and current is not None:
                blocks.append(current)
            current, fence = ([] if not fence else None), not fence
            continue
        if fence and current is not None:
            current.append(line)
    for block in blocks:
        joined = "\n".join(block)
        if "bd create" in joined and "agent-proposed" in joined:
            return list(block)
    return []


def check_capture_rule_is_injection_safe() -> None:
    """RUN the documented capture command against a hostile title.

    CLAUDE.md's block is a program: it templates text an agent supplies into a shell
    command, and that text is routinely quoted from a transcript - the user's words,
    a pasted log line, a colleague's message. Under the first version of this fix the
    text was interpolated inside double quotes, so backticks and `$(...)` in it ran.
    Measured, with a stub bd: a title reading "the `bd ready` query misses deferred
    beads" executed `bd ready` and filed the bead with its stdout spliced into the
    title, exiting 0.

    Checked by executing the block, not by reading it. A quoting bug is invisible to
    inspection and obvious to bash.
    """
    with open(os.path.join(REPO, "CLAUDE.md"), encoding="utf-8") as handle:
        block = _capture_block(handle.read())
    if not block:
        fail("could not find the capture command block in CLAUDE.md to execute")
        return

    script = "\n".join(block)
    # Fill the placeholders the way an agent would, hostile title included.
    script = re.sub(r"<what you noticed[^>]*>", _HOSTILE_TITLE, script)
    script = script.replace("<0-4>", "2").replace("<current-id>", "x-1")
    script = re.sub(r"<[^>]*>", "x", script)

    with tempfile.TemporaryDirectory() as directory:
        binary = os.path.join(directory, "bin")
        os.makedirs(binary)
        with open(os.path.join(binary, "bd"), "w", encoding="utf-8") as handle:
            handle.write(
                # APPENDS. The block calls bd twice, and an overwriting stub keeps
                # only the second call, then reports the title as missing when it
                # was passed correctly all along.
                '#!/bin/bash\nprintf "%s\\n" "$@" >> "$BD_ARGV_OUT"\necho stub-id\n'
            )
        os.chmod(os.path.join(binary, "bd"), 0o755)
        argv_out = os.path.join(directory, "argv.txt")
        subprocess.run(
            ["bash", "-c", script],
            cwd=directory,
            capture_output=True,
            check=False,
            timeout=30,
            env={
                **os.environ,
                "PATH": f"{binary}:{os.environ.get('PATH', '')}",
                "BD_ARGV_OUT": argv_out,
            },
        )
        executed = os.path.exists(os.path.join(directory, "pwned"))
        received = ""
        if os.path.exists(argv_out):
            with open(argv_out, encoding="utf-8") as handle:
                received = handle.read()

    if executed:
        fail(
            "the capture command in CLAUDE.md EXECUTED shell from its title text. "
            "A bead title quoting someone else's words now runs them."
        )
    if _HOSTILE_TITLE not in received:
        fail(
            "the capture command did not pass its title through verbatim. bd received:\n"
            + "".join(f"        {line}\n" for line in received.splitlines()[:4])
            + f"        expected to contain: {_HOSTILE_TITLE!r}"
        )


def _classify_broken(
    found: dict[tuple[str, str], set[str]],
) -> dict[tuple[str, str], set[str]]:
    """Which documented shapes the installed bd rejects, and where they are written.

    A missing SUBCOMMAND collapses to one entry keyed `(sub, "")` however many
    flags were written beside it - reporting `bd reclaim --foo` as a broken flag
    would send the reader chasing the wrong half.
    """
    broken: dict[tuple[str, str], set[str]] = {}
    for (subcommand, flag), places in found.items():
        if not subcommand_exists(subcommand):
            broken.setdefault((subcommand, ""), set()).update(places)
        elif flag and not flag_exists(subcommand, flag):
            broken[(subcommand, flag)] = places
    return broken


def _report_gap_mismatches(broken: dict[tuple[str, str], set[str]]) -> None:
    """Reconcile what is broken against what is exempt, in BOTH directions."""
    for (subcommand, flag), places in sorted(broken.items()):
        if (subcommand, flag) in KNOWN_GAPS:
            continue
        printed = f"bd {subcommand} {flag}".strip()
        fail(
            f"`{printed}` is documented here but the installed bd rejects it.\n"
            + "".join(f"        {p}\n" for p in sorted(places))
            + "        Fix the command, or add it to KNOWN_GAPS with a bead id."
        )

    for key, reason in sorted(KNOWN_GAPS.items()):
        if key not in broken:
            printed = f"bd {key[0]} {key[1]}".strip()
            fail(
                f"`{printed}` is listed in KNOWN_GAPS but the installed bd now "
                f"accepts it (or nothing documents it any more). Remove the "
                f"exemption.\n        Filed as: {reason}"
            )


def self_test(valid: frozenset[str]) -> None:
    """The extractor must see breaks it is already known to have missed.

    Each case below pins a bug this scanner actually had. A scanner that cannot
    fail is worth nothing, so it proves it can before anything else is believed.
    """
    sample = (
        "```bash\n"
        'bd create "<what you noticed>" -p 2 -l agent-proposed --status deferred \\\n'
        "  --deps discovered-from:x-1\n"
        "```\n"
    )
    found = _scan_sample(sample, valid)

    # (1) An earlier version anchored flags immediately after the subcommand, so
    # the quoted issue title ended the match and it reported a clean sweep with
    # `--status deferred` sitting in its input.
    if ("create", "--status") not in found:
        fail(
            "self-test: the scanner did not see `bd create --status` in a sample "
            f"that plainly contains it. It found {sorted(found)}. Every other "
            "result below is meaningless until this passes."
        )

    # (2) `--deps` is on the CONTINUATION line. This is the only assertion that
    # can distinguish a working `join_continuations` from a no-op: case (1) passes
    # either way, because `--status` sits on the first physical line.
    if ("create", "--deps") not in found:
        fail(
            "self-test: the scanner missed `--deps`, which is on the second line "
            "of a backslash-continued command. Continuation joining is broken, and "
            "a flag on a continuation line can now hide from this check entirely."
        )

    # (3) A four-backtick fence legitimately wraps three-backtick blocks. A plain
    # toggle inverts the fence state at the inner fence, after which prose reads
    # as code and code as prose for the rest of the file.
    nested = (
        "````markdown\n```bash\nbd reclaim\n```\n````\nprose `bd create -p 1` here\n"
    )
    nested_found = _scan_sample(nested, valid, "nested.md")
    if ("reclaim", "") not in nested_found or ("create", "-p") not in nested_found:
        fail(
            "self-test: nested fence tracking is broken. Expected to find both "
            "`bd reclaim` inside the inner fence and `bd create -p` in the prose "
            f"after the outer fence closed; found {sorted(nested_found)}."
        )
    else:
        print("  self-test: scanner detects a known-broken flag  OK")


def main() -> int:
    # BEFORE the bd gate. Neither of these needs the binary - one is pure text
    # comparison across three files, the other feeds synthetic markdown to the
    # scanner - and the copy-drift check is the one that catches a copy silently
    # drifting to `-s open`. Gating it behind `bd` being on PATH would skip it
    # green in exactly the non-login-shell case this file already had to fix once.
    check_capture_rule_copies_agree()
    check_capture_rule_is_injection_safe()

    if _bd_binary() is None:
        print(
            "SKIPPED the bd-dependent checks: `bd` is not on PATH, so no "
            "documented command could be checked against it. The copy-drift "
            "check above still ran."
        )
        return 1 if FAILURES else 0

    version = _run_bd("version").stdout.strip()
    print(f"checking documented `bd` commands against: {version}\n")

    if BOOTSTRAP_RED:
        fail(
            "EXPECT_BOOTSTRAP_RED=1 - deliberate failure, proving this suite can "
            "report one. Unset it to run the real checks."
        )

    valid = known_subcommands()
    if len(valid) < 20:
        fail(f"only {len(valid)} subcommands parsed from `bd --help`; parser is stale")
        print("\n1 failure(s)")
        return 1
    self_test(valid)

    found = scan(repo_files(), valid)

    # A COVERAGE FLOOR, not a nicety. `SCAN_GLOBS` is a hand-written list of
    # single-level patterns; a moved file or a new subdirectory silently drops out
    # of it, `found` shrinks, and every check below passes vacuously while printing
    # a success line. Until the KNOWN_GAPS entries are fixed they happen to fail an
    # empty run, which disguises this - but that list is meant to shrink to nothing,
    # and the day it does, a zero-coverage run would go green.
    if len(found) < 15:
        fail(
            f"only {len(found)} bd command(s) found across {len(repo_files())} "
            f"file(s). This repo documents far more than that, so SCAN_GLOBS has "
            f"almost certainly stopped matching. A run that checks nothing must "
            f"not report success."
        )
    check_implied_create_flags()
    broken = _classify_broken(found)
    _report_gap_mismatches(broken)

    print(
        f"\n  {len(found)} documented (subcommand, flag) pair(s) checked, "
        f"{len(broken)} broken, {len(KNOWN_GAPS)} exempted by bead"
    )
    if FAILURES:
        print(f"\n{FAILURES} failure(s)")
        return 1
    print("\nAll documented bd commands are accepted by the installed bd.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
