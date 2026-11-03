#!/usr/bin/env python3
"""Resolve one verified, sha-pinned source permalink per finding, and account for the rest.

A link may be emitted only after proving the file at that sha is byte-identical to the
checkout the finder read. `null` is the legitimate answer when that proof fails.

How a ref is chosen:

1. Local HEAD, but only if `git branch -r --contains <sha>` is non-empty. A link to an
   unpushed sha 404s for every reader but the author, which is worse than no link --
   it looks like the report cites a deleted file.
2. Otherwise a pushed ref, `origin/master` by default, `--ref` to override, resolved to
   a full 40-hex sha.
3. Either way `git diff --quiet <sha> -- <path>` must pass before a link is emitted.

When no candidate ref matches, the `permalink_resolution.unlinked` entry carries a
reason naming the ref and the failure -- "file differs from origin/master at the
examined checkout", never "could not verify". A generic reason is the same silence as
no reason.

**`attempted` is derived from `len(findings)`**, so a loop that skipped every finding
reports 64 attempted against 0 linked and cannot spell itself as clean. A record with
zero findings is a clean sweep and exits 0; that is distinct from the check never running.

**Read-only by construction.** Only `rev-parse`, `branch -r --contains`, `cat-file -e`
and `diff --quiet` are run, each with `--no-optional-locks` so not even the index stat
cache is rewritten. The anchor is built from the parsed range, never from
`line.split("-")[0]`, which shipped `#L177` for a defect declared at `:177-181`.

Usage:
    python3 resolve_permalinks.py --repo <checkout> < run.json > resolved.json

    --repo        required; the local checkout root the finders read.
    --record      read the record from this path instead of stdin.
    --ref         pushed ref to fall back to. Default `origin/master`.
    --host        used only when the record's `repo.host` is absent.
    --full-name   used only when the record's `repo.full_name` is absent.

The updated record goes to stdout; a human summary, including every distinct unlinked
reason with its count, goes to stderr.

Exit codes:
    0  OK        every finding was attempted; nulls among them are legitimate.
    1  SELF_CHECK_FAILED  a link was built that `digest_model` would reject. A bug here,
                 not in the record.
    2  usage error, or no input at all -- the check never ran.
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# The consumer's own pattern, imported rather than copied. A copy would drift,
# and the drift would surface as a record this script called finished and
# `digest_model` refuses to render. Importing also makes this file a version
# tripwire in the same way `write_artifact.py` is: run against an older plugin
# tree that has no `digest_model`, and this fails loudly at import instead of
# quietly emitting links nothing downstream will accept.
from digest_model import _PERMALINK, validate_run_record  # noqa: E402

# `path:118` or `path:177-181`. The range is kept whole and reassembled into
# `#L177-L181`; collapsing it to its start is the exact defect
# `digest_model._check_finding` was added to catch.
_SITE = re.compile(r"^(?P<start>\d+)(?:-(?P<end>\d+))?$")

_SHA = re.compile(r"^[0-9a-f]{40}$")

_DEFAULT_REF = "origin/master"


@dataclass(frozen=True, slots=True)
class Site:
    path: str
    start: str
    end: str | None

    @property
    def anchor(self) -> str:
        return f"#L{self.start}" if self.end is None else f"#L{self.start}-L{self.end}"


@dataclass(frozen=True, slots=True)
class Candidate:
    """A ref that could be linked to, already resolved to a full sha."""

    label: str
    sha: str


@dataclass(frozen=True, slots=True)
class FileVerdict:
    """The sha this file can be linked at, or the reason it cannot be."""

    sha: str | None
    reason: str | None


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """Run one read-only git command.

    `--no-optional-locks` is not decoration. `git diff` will otherwise refresh
    the index to speed up later calls, which takes `index.lock` and rewrites
    `.git/index`. That is a write to a repo this script promised not to touch,
    and it can collide with whatever else the operator is doing in that
    checkout.
    """
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )


def _fail(message: str, code: int = 2) -> None:
    print(f"resolve_permalinks: {message}", file=sys.stderr)
    sys.exit(code)


def parse_site(defect_site: object) -> Site | None:
    """`path:118` or `path:177-181` into its parts, or None if it is neither.

    Paths in the record are repo-root-relative, so an absolute path or one that
    climbs out with `..` is not a site this can resolve -- and following it would
    read outside the checkout under audit.
    """
    if not isinstance(defect_site, str) or ":" not in defect_site:
        return None
    path, _, tail = defect_site.rpartition(":")
    match = _SITE.fullmatch(tail.strip())
    if not path.strip() or match is None:
        return None
    path = path.strip()
    if path.startswith("/") or ".." in Path(path).parts:
        return None
    return Site(path=path, start=match["start"], end=match["end"])


def head_candidate(repo: Path) -> tuple[Candidate | None, str | None]:
    """Local HEAD, but only when some remote branch contains it.

    A link to an unpushed sha 404s. That is strictly worse than emitting null:
    null renders as plain text and says why, while a 404 tells the reader the
    report cites code that does not exist.
    """
    rev = _git(repo, "rev-parse", "HEAD")
    if rev.returncode != 0:
        return None, f"HEAD could not be resolved ({rev.stderr.strip()})"
    sha = rev.stdout.strip()
    if not _SHA.fullmatch(sha):
        return None, f"HEAD resolved to {sha!r}, which is not a 40-hex sha"
    contains = _git(repo, "branch", "-r", "--contains", sha)
    if contains.returncode != 0 or not contains.stdout.strip():
        return None, "HEAD is unpushed"
    return Candidate(label="HEAD", sha=sha), None


def pushed_candidate(repo: Path, ref: str) -> Candidate:
    """`--ref` resolved to a full sha, or a usage error.

    Failing here is fatal rather than degrading to "no candidates": a typo in
    `--ref`, or a checkout with no `origin`, would otherwise produce a complete
    run in which every finding is honestly-worded and uniformly null. That is
    the shape of the incident this script exists to prevent, so it must not be
    reachable by misconfiguration.
    """
    rev = _git(repo, "rev-parse", f"{ref}^{{commit}}")
    if rev.returncode != 0:
        _fail(
            f"--ref {ref!r} does not resolve in {repo} ({rev.stderr.strip()}). "
            "Without a pushed ref every finding would be unlinked for a reason "
            "that has nothing to do with the findings."
        )
    sha = rev.stdout.strip()
    if not _SHA.fullmatch(sha):
        _fail(f"--ref {ref!r} resolved to {sha!r}, which is not a 40-hex sha")
    return Candidate(label=ref, sha=sha)


def verify_file(
    repo: Path, path: str, candidates: list[Candidate], preamble: str | None
) -> FileVerdict:
    """The first candidate whose copy of this file matches the checkout.

    Byte-identity is the whole precondition for linking. Line numbers are what
    the anchor asserts, and a file that differs by one inserted import has moved
    every line below it.
    """
    if not (repo / path).is_file():
        return FileVerdict(
            None,
            f"{path} is not present in the examined checkout, so byte-identity "
            "with any ref is unprovable",
        )

    parts = [preamble] if preamble else []
    for candidate in candidates:
        exists = _git(repo, "cat-file", "-e", f"{candidate.sha}:{path}")
        if exists.returncode != 0:
            parts.append(f"path not found at {candidate.label}")
            continue
        diff = _git(repo, "diff", "--quiet", candidate.sha, "--", path)
        if diff.returncode == 0:
            return FileVerdict(candidate.sha, None)
        if diff.returncode == 1:
            parts.append(
                f"file differs from {candidate.label} at the examined checkout"
            )
        else:
            parts.append(
                f"git diff against {candidate.label} failed "
                f"({diff.stderr.strip() or diff.returncode})"
            )
    return FileVerdict(
        None, " and ".join(parts) if parts else "no candidate ref was available"
    )


def resolve(
    record: dict,
    repo: Path,
    candidates: list[Candidate],
    preamble: str | None,
    host: str,
    full_name: str,
) -> dict:
    """Rewrite every `permalink`, and account for every finding either way.

    Existing permalinks are recomputed rather than preserved. A stale link from
    an earlier run is pinned to an earlier sha, and this is the step that is
    supposed to prove the pin still holds.

    The candidate refs are resolved once by the caller and passed in, so every
    finding in one record is judged against the same set. Re-deriving them per
    finding would let a push landing mid-run split one record across two
    answers to "is HEAD pushed", and nothing in the output would show it.
    """
    findings = record["findings"]
    cache: dict[str, FileVerdict] = {}
    linked = 0
    unlinked: list[dict] = []

    for index, finding in enumerate(findings):
        fingerprint = finding.get(
            "fingerprint", f"<findings[{index}] has no fingerprint>"
        )
        site = parse_site(finding.get("defect_site"))
        if site is None:
            finding["permalink"] = None
            unlinked.append(
                {
                    "fingerprint": fingerprint,
                    "reason": f"defect_site {finding.get('defect_site')!r} is not a "
                    "repo-relative path ending in :<line> or :<start>-<end>, so no "
                    "anchor could be built from it",
                }
            )
            continue

        verdict = cache.get(site.path)
        if verdict is None:
            verdict = verify_file(repo, site.path, candidates, preamble)
            cache[site.path] = verdict

        if verdict.sha is None:
            finding["permalink"] = None
            unlinked.append({"fingerprint": fingerprint, "reason": verdict.reason})
            continue

        link = f"https://{host}/{full_name}/blob/{verdict.sha}/{site.path}{site.anchor}"
        # Refusing to emit a link this shape check rejects keeps the failure at
        # the producer. The alternative is a record that validates as "no link
        # available" downstream while this script reported it as linked.
        if not _PERMALINK.fullmatch(link):
            finding["permalink"] = None
            unlinked.append(
                {
                    "fingerprint": fingerprint,
                    "reason": f"the URL built for this site ({link}) does not match "
                    "the pinned-sha permalink shape the digest validates, so it was "
                    "withheld rather than emitted",
                }
            )
            continue

        finding["permalink"] = link
        linked += 1

    # `attempted` is derived from the findings list, never accumulated. A
    # counter can be incremented zero times by a loop that never ran, and that
    # is precisely how a run reports "attempted: 0, all null" as a success.
    record["permalink_resolution"] = {
        "attempted": len(findings),
        "linked": linked,
        "unlinked": unlinked,
    }
    return record


def summarise(record: dict, repo: Path, ref: str, candidates_note: str) -> None:
    resolution = record["permalink_resolution"]
    print(f"resolve_permalinks: repo {repo}", file=sys.stderr)
    print(f"  {candidates_note}", file=sys.stderr)
    print(
        f"  attempted {resolution['attempted']}, linked {resolution['linked']}, "
        f"unlinked {len(resolution['unlinked'])}",
        file=sys.stderr,
    )

    ranged = sum(
        1
        for f in record["findings"]
        if isinstance(f.get("permalink"), str)
        and "-L" in f["permalink"].rsplit("#L", 1)[-1]
    )
    print(
        f"  anchors: {ranged} ranged (#L<start>-L<end>), "
        f"{resolution['linked'] - ranged} single-line",
        file=sys.stderr,
    )

    reasons: dict[str, int] = {}
    for entry in resolution["unlinked"]:
        reasons[entry["reason"]] = reasons.get(entry["reason"], 0) + 1
    for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  unlinked x{count}: {reason}", file=sys.stderr)

    # The record's own `repo.ref` is left exactly as the run wrote it -- it
    # records the checkout that was examined, which is a different fact from the
    # ref the links are pinned to. Saying so is cheaper than letting a reader
    # discover the two shas differ and assume one of them is wrong.
    recorded = (record.get("repo") or {}).get("ref")
    linked_shas = {
        f["permalink"].split("/blob/", 1)[1][:40]
        for f in record["findings"]
        if isinstance(f.get("permalink"), str)
    }
    if recorded and linked_shas and recorded not in linked_shas:
        print(
            f"  note: repo.ref in the record is {recorded[:12]} (the examined "
            f"checkout); links are pinned to {', '.join(s[:12] for s in sorted(linked_shas))} "
            f"via {ref}",
            file=sys.stderr,
        )


def self_check(record: dict) -> list[str]:
    """Every permalink the digest validator would reject. Empty means good.

    Only `findings[N].permalink` errors are gating. `permalink_resolution` is
    not yet a field of `_RECORD_CHECKS`, so the validator reports it as an
    unknown key; that is a schema gap to close, not a defect in the links, and
    conflating the two would make this script fail on every correct run.
    """
    return [
        f"{e.field}: {e.message}"
        for e in validate_run_record(record)
        if e.field.endswith(".permalink")
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Resolve verified, sha-pinned source permalinks for a bug-hunt run record.",
    )
    parser.add_argument(
        "--repo", required=True, help="local checkout root the finders read"
    )
    parser.add_argument("--record", help="run record JSON; default stdin")
    parser.add_argument(
        "--ref", default=_DEFAULT_REF, help=f"pushed ref; default {_DEFAULT_REF}"
    )
    parser.add_argument("--host", help="used only when the record has no repo.host")
    parser.add_argument(
        "--full-name", help="used only when the record has no repo.full_name"
    )
    args = parser.parse_args(argv)

    repo = Path(args.repo).expanduser()
    if not (repo / ".git").exists():
        _fail(f"--repo {repo} is not a git checkout (no .git)")

    if args.record:
        source_path = Path(args.record).expanduser()
        if not source_path.is_file():
            _fail(f"--record {source_path} does not exist")
        raw = source_path.read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    if not raw.strip():
        _fail("no record on stdin and no --record; nothing was attempted")

    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        _fail(f"record is not valid JSON: {exc}")
    if not isinstance(record, dict):
        _fail("record must be a JSON object")

    findings = record.get("findings")
    if not isinstance(findings, list):
        _fail("record has no `findings` array, so the check cannot run at all")
    # An empty `findings` list is NOT an error. "Nothing to attempt" is a clean
    # sweep, which still requires a digest; "attempted nothing" is the 64-null
    # bug this script prevents, and `attempted = len(findings)` below is what
    # distinguishes them. Rejecting the empty record would conflate the two --
    # the same class of error the script exists to stop -- and would take the
    # whole section 9 pipeline down with it under `set -o pipefail`.
    non_objects = [i for i, f in enumerate(findings) if not isinstance(f, dict)]
    if non_objects:
        _fail(f"findings at {non_objects} are not objects")

    repo_block = record.get("repo") or {}
    host = (repo_block.get("host") or args.host or "").strip()
    full_name = (repo_block.get("full_name") or args.full_name or "").strip()
    if not host:
        _fail("no repo.host in the record and no --host")
    if not full_name:
        _fail("no repo.full_name in the record and no --full-name")

    head, head_note = head_candidate(repo)
    pushed = pushed_candidate(repo, args.ref)
    candidates = [c for c in (head, pushed) if c is not None]
    # `head_note` becomes the preamble of every unlinked reason, because "file
    # differs from origin/master" alone leaves the reader wondering why HEAD was
    # not tried; "HEAD is unpushed and file differs from origin/master" is the
    # whole answer.
    record = resolve(
        record, repo, candidates, head_note if head is None else None, host, full_name
    )

    candidates_note = (
        f"HEAD {head.sha[:12]} is on a remote branch, so it is preferred"
        if head
        else f"{head_note}, so links fall back to {args.ref}"
    )
    summarise(record, repo, args.ref, candidates_note)

    problems = self_check(record)
    if problems:
        print(
            "resolve_permalinks: SELF_CHECK_FAILED -- links were built that the "
            "digest validator rejects, so the record on stdout is not fit to render:",
            file=sys.stderr,
        )
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        sys.exit(1)

    json.dump(record, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
