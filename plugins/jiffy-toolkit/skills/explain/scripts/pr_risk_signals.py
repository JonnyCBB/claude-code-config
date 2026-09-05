#!/usr/bin/env python3
"""pr_risk_signals.py - emit a deterministic, tiered signal sheet for one pull request.

This script computes evidence. It renders no verdict and makes no judgement.

Exit codes, monotonic by severity:
    0  OK           - a complete computed tier was collected
    1  PARTIAL      - some signal or harvest source could not be collected; the
                      affected fields are null and `tiers_omitted` records it
    2  UNRESOLVABLE  - the reference is invalid or ambiguous, or no PR was found

NOTE: this script deliberately INVERTS the discipline of the scripts it otherwise
imitates (eng-utils bug-hunter-3000), whose docstring says "nothing at all
reaches stdout on an error exit". Here, valid JSON is emitted on EVERY exit,
because the caller needs the `errors` array and the partial sheet in order to
render fields as `unverifiable` rather than silently omitting them. There is
exactly one json.dumps call, at the end, on every path including the top-level
exception handler.

DETERMINISM: given the same reference and the same observed API response, no
unordered iteration reaches the output. Every emitted collection is sorted at
construction and the single dump uses sort_keys. This is NOT a claim of
byte-identity across time - `pr_state` and `mergeStateStatus` both change while
the head SHA does not, so byte-identity across two runs is not achievable and is
not asserted.

Do NOT memoise subprocess calls at module scope. A cache would make a second
in-process call reuse the first result and would defeat the harvest's freshness.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

SCHEMA_VERSION = "1"
DEFAULT_HOST = "github.com"
TIMEOUT = 20  # seconds per subprocess call; not a flag - one caller, one shape

# --------------------------------------------------------------------------- #
# Reference parsing. Accepts a full PR URL or owner/name#N. A BARE NUMBER IS
# REJECTED: it would resolve against the current directory's git remote, so the
# same reference in two worktrees yields two different pull requests, and the
# output would be internally consistent in each - meaning nothing downstream
# could detect the error.
# --------------------------------------------------------------------------- #
RE_URL = re.compile(
    r"^https?://(?P<host>[A-Za-z0-9.\-]+)/(?P<owner>[A-Za-z0-9._\-]+)/"
    r"(?P<repo>[A-Za-z0-9._\-]+)/pull/(?P<num>\d+)/?$"
)
RE_SHORT = re.compile(
    r"^(?P<owner>[A-Za-z0-9._\-]+)/(?P<repo>[A-Za-z0-9._\-]+)#(?P<num>\d+)$"
)

# Ordered, first match wins. A TUPLE rather than a dict: a tuple's order cannot
# silently drift when someone reorders entries "for readability".
#
# `iface` deliberately precedes `config` and `docs`, which is a considered
# deviation from the order named in the research. An OpenAPI or schema file is
# usually YAML, so a config-first order would bucket an interface change as
# configuration - understating the single highest-risk signal this script emits.
# Mis-bucketing in that direction is the wrong failure for a risk instrument.
ROLE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "test",
        re.compile(
            r"(^|/)(tests?|__tests__|testdata)/|(^|/)test_[^/]*$|_test\.[A-Za-z0-9]+$"
            r"|\.(test|spec)\.[jt]sx?$|Test\.java$|Tests\.java$|Spec\.scala$"
            r"|(^|/)conftest\.py$"
        ),
    ),
    (
        "generated",
        re.compile(
            r"\.(pb|pb2|generated)\.[A-Za-z0-9]+$|(^|/)(generated|__generated__)/"
            r"|(^|/)(package-lock\.json|yarn\.lock|poetry\.lock|Cargo\.lock)$"
            r"|\.snap$|\.min\.(js|css)$"
        ),
    ),
    (
        "iface",
        re.compile(
            r"\.proto$|\.thrift$|\.avsc$|\.graphql$|(^|/)api/"
            r"|(^|/)(openapi|swagger)[^/]*\.(ya?ml|json)$"
        ),
    ),
    (
        "docs",
        re.compile(
            r"\.(md|mdx|rst|adoc|txt)$|(^|/)docs?/"
            r"|(^|/)(LICENSE|CHANGELOG|CONTRIBUTING|README)[^/]*$"
        ),
    ),
    (
        "config",
        re.compile(
            r"\.(ya?ml|toml|ini|cfg|properties|env|json)$|(^|/)\.[A-Za-z0-9]+rc$"
            r"|(^|/)(Dockerfile|Makefile|Justfile)[^/]*$"
        ),
    ),
)
ROLE_ORDER: tuple[str, ...] = tuple(name for name, _ in ROLE_PATTERNS) + ("source",)

DEPLOY_INFRA = re.compile(
    r"(^|/)kubernetes/|(^|/)k8s/|(^|/)(gantry|deployment-info|build-info|monitoring-info)\.ya?ml$"
    r"|\.tf$|\.tfvars$|(^|/)helm/|(^|/)terraform/"
)

# gh's documented changeType vocabulary. Anything outside it is reported rather
# than silently dropped into no bucket.
KNOWN_CHANGE_TYPES = frozenset(
    {"ADDED", "MODIFIED", "REMOVED", "RENAMED", "COPIED", "CHANGED"}
)

# mergeStateStatus values that genuinely mean "current". Anything else -
# including UNKNOWN, which is what a merged PR returns - is unverifiable, never
# a pass. Measured: PR #98 in this repo returns UNKNOWN.
CURRENCY_GOOD = frozenset({"CLEAN", "HAS_HOOKS", "UNSTABLE"})
CURRENCY_STALE = frozenset({"BEHIND", "DIRTY", "BLOCKED", "DRAFT"})


# --------------------------------------------------------------------------- #
# Schema. The dataclasses ARE the emitted vocabulary; nothing else declares it.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RoleChurn:
    role: str
    files: int
    additions: int
    deletions: int


@dataclass(frozen=True, slots=True)
class CheckState:
    # `neutral` is a first-class count and is NEVER folded into `passed`.
    # A neutral conclusion is not a pass; treating it as one is how a suite that
    # never ran reads as green.
    total: int
    passed: int
    failed: int
    neutral: int
    pending: int


@dataclass(frozen=True, slots=True)
class HarvestSource:
    source: str
    lookup_attempted: str
    resolved_path: str | None
    # How the path was established. "resolved" means the lookup key uniquely
    # identifies this artifact. "unverified-mention" means free text merely
    # referenced the PR, which does NOT establish that this artifact is the
    # PR's own - see the bead branch below. A consumer must not treat the two
    # the same, and nothing but this field distinguishes them.
    relation: str = "resolved"


@dataclass(frozen=True, slots=True)
class Computed:
    files_changed: int
    role_churn: list[RoleChurn]
    diffusion_top_level_dirs: int
    distinct_extensions: list[str]
    test_file_touched: bool
    test_to_source_churn_ratio: float | None
    touches_interface_surface: bool
    touches_deploy_infra: bool
    branch_currency: str
    branch_currency_raw: str
    check_state: CheckState


@dataclass(frozen=True, slots=True)
class Asserted:
    field_name: str
    value: str
    attempted_lookup: str


@dataclass(frozen=True, slots=True)
class Sheet:
    schema_version: str
    pr_ref: str
    resolved_host: str
    resolved_repo: str
    pr_number: int | None
    pr_state: str | None
    head_commit_sha: str | None
    tiers_included: list[str]
    tiers_omitted: list[str]
    computed: Computed | None
    asserted: list[Asserted]
    harvest: list[HarvestSource]
    errors: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Subprocess boundary. Every argument is a literal list element; no shell string
# is ever built, so a reference containing shell metacharacters cannot execute.
# --------------------------------------------------------------------------- #
def run(cmd: list[str], host: str, errors: list[str]) -> str | None:
    env = {**os.environ, "GH_HOST": host}
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=TIMEOUT, env=env, check=False
        )
    except subprocess.TimeoutExpired:
        errors.append(
            f"timeout after {TIMEOUT}s: {cmd[0]} {cmd[1] if len(cmd) > 1 else ''}"
        )
        return None
    except OSError as e:
        errors.append(f"{type(e).__name__}: {e}")
        return None
    if p.returncode != 0:
        # Name the host. A public github.com lookup 404s indistinguishably from
        # "this path does not exist", so the host must appear in the error.
        errors.append(
            f"{cmd[0]} exited {p.returncode} (host {host}): "
            f"{(p.stderr or '').strip().splitlines()[0] if p.stderr.strip() else 'no stderr'}"
        )
        return None
    return p.stdout


# --------------------------------------------------------------------------- #
# Pure classification. No I/O.
# --------------------------------------------------------------------------- #
def classify_role(path: str) -> str:
    for name, pat in ROLE_PATTERNS:
        if pat.search(path):
            return name
    return "source"


def touches_any(paths: list[str], pattern: re.Pattern[str]) -> bool:
    return any(pattern.search(p) for p in paths)


def bucket_churn(files: list[dict]) -> list[RoleChurn]:
    acc = {r: [0, 0, 0] for r in ROLE_ORDER}
    for f in files:
        r = classify_role(f["path"])
        acc[r][0] += 1
        acc[r][1] += int(f.get("additions") or 0)
        acc[r][2] += int(f.get("deletions") or 0)
    # All six roles, always, zero-filled: a consumer never has to distinguish
    # "absent" from "zero". Emitted in ROLE_ORDER, never in dict-iteration order.
    return [RoleChurn(r, acc[r][0], acc[r][1], acc[r][2]) for r in ROLE_ORDER]


def churn_ratio(rows: list[RoleChurn]) -> float | None:
    by = {r.role: r for r in rows}
    src = by["source"].additions + by["source"].deletions
    tst = by["test"].additions + by["test"].deletions
    if src == 0:
        # Normal for a docs-only or test-only PR. Emitting inf here would be
        # caught by allow_nan=False, but null is the honest value.
        return None
    return round(tst / src, 4)


def diffusion(paths: list[str]) -> tuple[int, list[str]]:
    tops = {p.split("/")[0] for p in paths if "/" in p}
    exts = {p.rsplit(".", 1)[1].lower() for p in paths if "." in p.rsplit("/", 1)[-1]}
    # sorted() at construction. A set iterated into output reorders across
    # processes because string hashing is salted per interpreter.
    return len(tops), sorted(exts)


def summarize_checks(rollup: list[dict] | None) -> CheckState:
    if not rollup:
        return CheckState(0, 0, 0, 0, 0)
    passed = failed = neutral = pending = 0
    for c in rollup:
        concl = (c.get("conclusion") or "").upper()
        status = (c.get("status") or "").upper()
        if concl == "SUCCESS":
            passed += 1
        elif concl in ("FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED"):
            failed += 1
        elif concl == "NEUTRAL" or concl == "SKIPPED":
            neutral += 1
        elif status in ("IN_PROGRESS", "QUEUED", "PENDING", "") and not concl:
            pending += 1
        else:
            neutral += 1
    return CheckState(len(rollup), passed, failed, neutral, pending)


def currency(raw: str | None) -> tuple[str, str]:
    r = (raw or "").upper() or "MISSING"
    if r in CURRENCY_GOOD:
        return "current", r
    if r in CURRENCY_STALE:
        return "stale", r
    # UNKNOWN lands here. A "not BEHIND" test would read it as current, which is
    # the failure this branch exists to prevent.
    return "unverifiable", r


# --------------------------------------------------------------------------- #
# Harvest. Every source reports {source, lookup_attempted, resolved_path|null},
# so "declares what it looked for and could not find" is a mechanical fact
# rather than a claim the caller has to be trusted to make.
#
# The path rules below are MEASURED, not assumed. Revision 1 of the plan
# asserted them from a single exemplar each and all three were wrong.
# --------------------------------------------------------------------------- #
def harvest(
    repo: str, number: int, host: str, errors: list[str]
) -> list[HarvestSource]:
    out: list[HarvestSource] = []
    home = Path.home()

    # 1. Bead. The PR-to-bead join is free text: 199 of 874 beads reference a PR
    # at all, across description/notes/title in two syntaxes, and external_ref is
    # populated on 0 of 874. Best-effort by construction.
    # A substring match on "#<n>" hits every bead that MENTIONS the PR in passing,
    # not the bead whose work IS the PR. Measured while building this: searching
    # for "#98" returned a research bead that merely quoted PR #98 as an example,
    # and picking sorted()[0] presented that arbitrary choice as a confident
    # answer. Two guards: the bead must also name the repository, and MULTIPLE
    # matches resolve to null with the count reported rather than to a guess.
    bead_id: str | None = None
    short_repo = repo.split("/")[-1]
    lookup = (
        f"bd list --json: description/notes/title must contain 'PR #{number}' or "
        f"'/pull/{number}' AND also name {short_repo!r}; ambiguous matches resolve to null"
    )
    raw = run(["bd", "list", "--json", "--limit", "1000"], host, errors)
    if raw:
        try:
            rows = json.loads(raw)
            rows = rows if isinstance(rows, list) else rows.get("issues", [])
            pats = (f"pr #{number}", f"/pull/{number}")
            hits = sorted(
                b["id"]
                for b in rows
                if any(
                    p
                    in (
                        blob := " ".join(
                            str(b.get(k) or "")
                            for k in ("description", "notes", "title")
                        ).lower()
                    )
                    for p in pats
                )
                and short_repo.lower() in blob
            )
            if len(hits) == 1:
                bead_id = hits[0]
            elif len(hits) > 1:
                lookup += f" - AMBIGUOUS: {len(hits)} beads matched ({', '.join(hits[:4])})"
        except (ValueError, KeyError, TypeError) as e:
            errors.append(f"bead search failed: {type(e).__name__}: {e}")
    # A free-text hit establishes "this bead REFERENCES PR N", never "this bead's
    # own work IS PR N". Measured while building this: searching for PR #98
    # returned a research bead that quotes #98 as a worked example and also names
    # the repository, so neither the number nor a repo corroboration separates a
    # mention from ownership. Until something writes a structured pointer at
    # PR-creation time, the relation is reported as unverified rather than
    # asserted, and the caller decides what to do with a mention.
    out.append(
        HarvestSource(
            "bead",
            lookup,
            bead_id,
            relation="unverified-mention" if bead_id else "resolved",
        )
    )

    # 2. Dispatch spec. MEASURED: the directory holds 26 .txt and 5 .md, so a
    # *.md glob misses 84%. Filenames carry the bead-id SUFFIX at variable length,
    # sometimes dotted, and many carry none at all.
    suffix = bead_id.rsplit("-", 1)[-1] if bead_id else None
    d = home / "evidence" / "dispatch-specs"
    lookup = f"{d}/*.txt and *.md, matching bead-id suffix {suffix!r} as a substring"
    hit = None
    if suffix and d.is_dir():
        cands = sorted(p for p in d.iterdir() if p.suffix in (".txt", ".md"))
        hit = next((str(p) for p in cands if suffix in p.name), None)
    out.append(HarvestSource("dispatch_spec", lookup, hit))

    # 3. Verification evidence. MEASURED: branch appears in ZERO filenames, so
    # this is a body grep, and the directory holds 10 subdirectories a *.md glob
    # would never see.
    v = home / ".claude" / "thoughts" / "shared" / "verification"
    lookup = f"{v}/**: grep bodies for PR #{number}; branch is in no filename"
    hit = None
    if v.is_dir():
        for p in sorted(v.rglob("*.md")):
            try:
                if f"#{number}" in p.read_text(errors="replace"):
                    hit = str(p)
                    break
            except OSError:
                continue
    out.append(HarvestSource("verification", lookup, hit))

    # 4. Review findings. MEASURED: review_<N>_<date>.md is NOT repo-qualified,
    # and the store spans 4+ repos, so a match on <N> alone can return ANOTHER
    # repo's PR #N. A wrong-artifact hit feeding a merge verdict is worse than a
    # miss, so a corroborating repo mention inside the file is required.
    r = home / ".claude" / "thoughts" / "shared" / "reviews"
    short_repo = repo.split("/")[-1]
    lookup = (
        f"{r}/review_{number}_*.md, requiring the file to also mention {short_repo!r} "
        f"because review_<N> is not repo-qualified"
    )
    hit = None
    if r.is_dir():
        for p in sorted(r.glob(f"review_{number}_*.md")):
            try:
                if short_repo.lower() in p.read_text(errors="replace").lower():
                    hit = str(p)
                    break
            except OSError:
                continue
    out.append(HarvestSource("review", lookup, hit))

    return out


# --------------------------------------------------------------------------- #
def to_json(sheet: Sheet) -> str:
    # The ONLY json.dumps in this module. allow_nan=False turns any leaked
    # inf/nan into a crash rather than technically-invalid JSON on the wire.
    return json.dumps(
        asdict(sheet), sort_keys=True, allow_nan=False, ensure_ascii=True, indent=2
    )


def unresolvable(ref: str, host: str, repo: str, msg: str) -> int:
    sheet = Sheet(
        schema_version=SCHEMA_VERSION,
        pr_ref=ref,
        resolved_host=host,
        resolved_repo=repo,
        pr_number=None,
        pr_state=None,
        head_commit_sha=None,
        tiers_included=[],
        tiers_omitted=["asserted", "computed", "judgment"],
        computed=None,
        asserted=[],
        harvest=[],
        errors=[msg],
    )
    print(to_json(sheet))
    print(f"pr_risk_signals: {msg}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print(
            "usage: pr_risk_signals.py <pr-url | owner/name#N>\n"
            "  A bare PR number is rejected: it would resolve against the current\n"
            "  directory's git remote, so the same reference in two worktrees would\n"
            "  silently describe two different pull requests.",
            file=sys.stderr,
        )
        return 2

    ref = args[0]
    m = RE_URL.match(ref) or RE_SHORT.match(ref)
    if not m:
        return unresolvable(
            ref,
            DEFAULT_HOST,
            "",
            f"reference {ref!r} is not a PR URL or owner/name#N. A bare number is "
            f"ambiguous and is rejected deliberately.",
        )
    g = m.groupdict()
    host = g.get("host") or DEFAULT_HOST
    repo = f"{g['owner']}/{g['repo']}"
    number = int(g["num"])

    errors: list[str] = []
    fields = "files,state,headRefOid,mergeStateStatus,statusCheckRollup"
    raw = run(
        ["gh", "pr", "view", str(number), "--repo", repo, "--json", fields],
        host,
        errors,
    )
    if raw is None:
        return unresolvable(
            ref, host, repo, f"no PR found for {repo}#{number}; " + "; ".join(errors)
        )

    try:
        data = json.loads(raw)
    except ValueError as e:
        return unresolvable(ref, host, repo, f"gh returned unparseable JSON: {e}")

    files = data.get("files") or []
    # Validate before using. Report every problem rather than raising on the first.
    for f in files:
        for k in ("path", "additions", "deletions"):
            if k not in f:
                errors.append(
                    f"file record missing {k!r}: {f.get('path', '<no path>')}"
                )
        ct = (f.get("changeType") or "").upper()
        if ct and ct not in KNOWN_CHANGE_TYPES:
            errors.append(f"unknown changeType {ct!r} on {f.get('path')}")
    files = [f for f in files if "path" in f]
    paths = sorted(f["path"] for f in files)

    if len(paths) in (100, 300, 3000):
        errors.append(
            f"files_changed is exactly {len(paths)}, a known API page boundary; "
            "the file list may be truncated and composition may be incomplete"
        )

    rows = bucket_churn(files)
    tops, exts = diffusion(paths)
    cur, cur_raw = currency(data.get("mergeStateStatus"))
    computed = Computed(
        files_changed=len(paths),
        role_churn=rows,
        diffusion_top_level_dirs=tops,
        distinct_extensions=exts,
        test_file_touched=any(r.role == "test" and r.files > 0 for r in rows),
        test_to_source_churn_ratio=churn_ratio(rows),
        touches_interface_surface=any(r.role == "iface" and r.files > 0 for r in rows),
        touches_deploy_infra=touches_any(paths, DEPLOY_INFRA),
        branch_currency=cur,
        branch_currency_raw=cur_raw,
        check_state=summarize_checks(data.get("statusCheckRollup")),
    )

    asserted = [
        Asserted(
            "code_review_ran",
            "unverifiable",
            "no machine-readable receipt is written by /code-review; a filesystem "
            "lookup that finds nothing is indistinguishable from a review that "
            "never ran",
        ),
        Asserted(
            "live_verification_ran",
            "unverifiable",
            "same: /verify-implementation writes no receipt at run time",
        ),
    ]

    sheet = Sheet(
        schema_version=SCHEMA_VERSION,
        pr_ref=ref,
        resolved_host=host,
        resolved_repo=repo,
        pr_number=number,
        pr_state=(data.get("state") or None),
        head_commit_sha=(data.get("headRefOid") or None),
        tiers_included=["asserted", "computed"],
        # `judgment` is ALWAYS omitted: this script renders no verdict by design.
        # Stated explicitly so a consumer seeing two of three tiers cannot read it
        # as a complete profile.
        tiers_omitted=["judgment"],
        computed=computed,
        asserted=asserted,
        harvest=harvest(repo, number, host, errors),
        errors=sorted(errors),
    )
    print(to_json(sheet))
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001 - last resort; must still emit JSON
        ref = sys.argv[1] if len(sys.argv) > 1 else ""
        sys.exit(unresolvable(ref, DEFAULT_HOST, "", f"{type(e).__name__}: {e}"))
