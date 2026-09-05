#!/usr/bin/env python3
"""Attach the commit and pull request that last wrote each finding's line.

Runs between `resolve_permalinks.py` and `digest_model.py`. It reads a run
record on stdin, adds a `provenance` object to every finding it can resolve, and
writes the record back out. Findings it cannot resolve get `provenance: null`
with a specific reason recorded in `provenance_resolution.unresolved`.

**Why this is a script and not something an agent reports.** The introducing
commit is a mechanical fact about the checkout, derivable with two git calls, and
a mechanical fact should never be produced by a model that can approximate it.
The same reasoning already applies to `resolve_permalinks.py`, and for the same
measured reason: 64 findings once shipped with a null link that nobody had
attempted to resolve, because "the agent will fill this in" is indistinguishable
from "the agent forgot".

**This never records an author, and that is deliberate.** `git blame` hands back
a name and an email for free, and a report that prints them next to the word
"bug" reads as an accusation however it is worded. The pull request link reaches
the same person in one click for a reader who genuinely needs them, without the
artifact itself attributing fault. Squad ownership was considered and dropped for
the same reason, plus a second one: ownership moves, so a squad resolved today is
a claim about now attached to a commit from two years ago.

**Blame is pinned to `repo.ref`, not to HEAD.** The record's line numbers were
read at that commit, and blaming a moving ref would silently attribute a line
that has since shifted. A file that does not exist at the pinned ref is an
unresolved finding with that reason, never a guess.

Exit codes match the rest of the pipeline: `0` resolved (including partial),
`1` the record failed its own self-check, `2` usage or environment error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

# The line half of `path/to/File.java:66` or `path/to/File.java:66-89`. A range
# resolves from its first line: the whole point is to name one commit, and a
# range spanning two commits has no single answer worth printing.
_SITE: Final[re.Pattern[str]] = re.compile(r"^(?P<path>.+):(?P<start>\d+)(?:-\d+)?$")

# Two pull-request reference forms appear in this monorepo's history and both
# resolve on the enterprise host. `(#141416)` is a same-repo reference written by
# the monorepo's own merge tooling. `(search-platform/search-influence#319)` is a
# cross-repo reference preserved from before that component migrated in, and it
# points at a repository that still exists. Handling only the first form silently
# drops the older half of the history, which is exactly the half where a reader
# most wants to know why a line looks the way it does.
_PR_SAME_REPO: Final[re.Pattern[str]] = re.compile(r"\(#(\d+)\)\s*$")
_PR_CROSS_REPO: Final[re.Pattern[str]] = re.compile(
    r"\((?P<repo>[\w.-]+/[\w.-]+)#(?P<number>\d+)\)\s*$"
)

_SHA: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{40}$")
_SHORT: Final[int] = 8


def _fail(message: str, code: int = 2) -> None:
    print(f"resolve_provenance: {message}", file=sys.stderr)
    sys.exit(code)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", "-C", str(repo), *args),
        capture_output=True,
        text=True,
        check=False,
    )


def parse_site(defect_site: object) -> tuple[str, int] | None:
    if not isinstance(defect_site, str):
        return None
    match = _SITE.match(defect_site.strip())
    if not match:
        return None
    return match.group("path"), int(match.group("start"))


def blame_file(repo: Path, ref: str, path: str) -> dict[int, str]:
    """Every line of one file mapped to the commit that last wrote it.

    The whole file is blamed rather than the single line each finding needs,
    because blame's cost is dominated by walking history for the file and is
    almost identical either way, so a component whose findings cluster in shared
    files pays once instead of once per finding. `SKILL.md` section 9 states the
    measured per-call cost and is the only place that figure lives.

    `--porcelain` is used rather than the human format because the human format
    interleaves the author name into the same line as the SHA, and parsing it
    out invites accidentally keeping it. Here the name is never read at all.
    """
    blame = _git(repo, "blame", "--porcelain", ref, "--", path)
    if blame.returncode != 0 or not blame.stdout.strip():
        return {}
    lines: dict[int, str] = {}
    for entry in blame.stdout.splitlines():
        # A header line opens each blamed hunk: "<sha> <orig> <final> [<count>]".
        # Content lines are tab-prefixed and metadata lines are lowercase words,
        # so neither can be mistaken for one.
        head = entry.split()
        if len(head) >= 3 and _SHA.fullmatch(head[0]) and head[2].isdigit():
            lines[int(head[2])] = head[0]
    return lines


def commit_subject(repo: Path, sha: str) -> str | None:
    shown = _git(repo, "log", "-1", "--format=%s", sha)
    if shown.returncode != 0:
        return None
    return shown.stdout.strip()


def commit_date(repo: Path, sha: str) -> str | None:
    shown = _git(repo, "log", "-1", "--format=%ad", "--date=format:%-d %b %Y", sha)
    if shown.returncode != 0:
        return None
    return shown.stdout.strip() or None


def pull_request(subject: str, host: str, full_name: str) -> dict | None:
    """The pull request named at the end of a commit subject, or None.

    Only a reference at the END of the subject counts. A number written mid
    sentence ("revert of #900 broke the build") is a mention of a pull request,
    not the one that merged this commit, and linking it would point a reader at
    an unrelated change with full confidence.
    """
    cross = _PR_CROSS_REPO.search(subject)
    if cross:
        number = cross.group("number")
        return {
            "number": int(number),
            "url": f"https://{host}/{cross.group('repo')}/pull/{number}",
        }
    same = _PR_SAME_REPO.search(subject)
    if same:
        number = same.group(1)
        return {
            "number": int(number),
            "url": f"https://{host}/{full_name}/pull/{number}",
        }
    return None


def resolve(record: dict, repo: Path) -> tuple[int, int, list[dict]]:
    repo_block = record.get("repo") or {}
    host = repo_block.get("host")
    full_name = repo_block.get("full_name")
    ref = repo_block.get("ref")
    if not (host and full_name and ref):
        _fail("record needs repo.host, repo.full_name and repo.ref to build links")

    attempted = resolved = 0
    unresolved: list[dict] = []
    # Keyed by path and by sha respectively. Findings cluster heavily in a few
    # files and a few commits, so both caches earn their keep on any real run.
    blames: dict[str, dict[int, str]] = {}
    commits: dict[str, tuple[str | None, str | None]] = {}

    for finding in record.get("findings", []):
        attempted += 1
        fingerprint = finding.get("fingerprint", "?")
        finding["provenance"] = None

        site = parse_site(finding.get("defect_site"))
        if site is None:
            unresolved.append(
                {
                    "fingerprint": fingerprint,
                    "reason": "the recorded location is not a file and line, "
                    "so there is no single line to trace",
                }
            )
            continue

        path, line = site
        if path not in blames:
            blames[path] = blame_file(repo, ref, path)
        sha = blames[path].get(line)
        if sha is None:
            # Two distinguishable causes share this branch on purpose: the file
            # is absent at the pinned commit, or it is present and shorter than
            # the recorded line. Both mean the same thing to a reader -- the
            # location in this record does not exist in the code that was
            # examined -- and separating them would invite a second git call to
            # tell apart two outcomes with one response.
            unresolved.append(
                {
                    "fingerprint": fingerprint,
                    "reason": f"git could not trace {path} line {line} at the "
                    f"commit this run examined",
                }
            )
            continue

        if sha not in commits:
            commits[sha] = (commit_subject(repo, sha), commit_date(repo, sha))
        subject, date = commits[sha]
        finding["provenance"] = {
            "commit": sha,
            "commit_short": sha[:_SHORT],
            "commit_url": f"https://{host}/{full_name}/commit/{sha}",
            "date": date,
            "pull_request": pull_request(subject or "", host, full_name),
        }
        resolved += 1

    record["provenance_resolution"] = {
        "attempted": attempted,
        "resolved": resolved,
        "unresolved": unresolved,
    }
    return attempted, resolved, unresolved


def self_check(record: dict) -> list[str]:
    """Every attempt must end in exactly one of the two outcomes.

    The same arithmetic guard `permalink_resolution` carries, for the same
    reason: `{attempted: 76, resolved: 0, unresolved: []}` is the shape a stage
    takes when it silently did nothing, and without this check it renders as a
    report where no finding happens to have a commit.
    """
    block = record.get("provenance_resolution")
    if not isinstance(block, dict):
        return ["provenance_resolution is missing"]
    attempted = block.get("attempted")
    resolved = block.get("resolved")
    unresolved = block.get("unresolved")
    if not (
        isinstance(attempted, int)
        and isinstance(resolved, int)
        and isinstance(unresolved, list)
    ):
        return ["provenance_resolution needs integer counts and a list"]
    if resolved + len(unresolved) != attempted:
        return [
            f"provenance_resolution says {attempted} attempted but accounts for "
            f"{resolved + len(unresolved)} ({resolved} resolved + "
            f"{len(unresolved)} unresolved); every attempt must end in one or "
            f"the other"
        ]
    return []


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Attach the commit and pull request behind each finding's line."
    )
    parser.add_argument("--repo", required=True, help="path to the checkout")
    parser.add_argument("--record", help="run record JSON; default stdin")
    args = parser.parse_args(argv)

    repo = Path(args.repo).expanduser()
    if not (repo / ".git").exists():
        _fail(f"{repo} is not a git checkout")

    raw = Path(args.record).read_text() if args.record else sys.stdin.read()
    if not raw.strip():
        _fail("no run record on stdin")
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        _fail(f"run record is not valid JSON: {exc}")

    attempted, resolved, unresolved = resolve(record, repo)

    problems = self_check(record)
    if problems:
        for problem in problems:
            print(f"resolve_provenance: {problem}", file=sys.stderr)
        sys.exit(1)

    print(
        f"resolve_provenance: {resolved}/{attempted} findings traced to a commit",
        file=sys.stderr,
    )
    for miss in unresolved[:5]:
        print(f"  {miss['fingerprint']}: {miss['reason']}", file=sys.stderr)
    if len(unresolved) > 5:
        print(f"  ... and {len(unresolved) - 5} more", file=sys.stderr)

    json.dump(record, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
