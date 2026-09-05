#!/usr/bin/env python3
"""
Redaction scanner for portfolio write-ups produced by the bug-hunter-3000
skill.

This is a deterministic backstop for well-known secret/token/identifier
shapes (AWS access keys, GitHub PATs, bearer tokens, generic key
assignments, user URIs, external email addresses, raw user
identifiers) -- it is not a general DLP system. It will miss secrets that
don't match a known shape and may occasionally flag a coincidental
look-alike; treat a CLEAN result as "no known shape found," not as a
guarantee.

Usage:
    python3 redact_scan.py input.md            # report only, JSON on STDERR
    python3 redact_scan.py < input.md          # or stdin
    python3 redact_scan.py --mask input.md     # REDACTED TEXT on stdout, JSON on stderr

To write an artifact, use `write_artifact.py`, which owns the write and then
verifies what landed on disk. Do not implement masking in the caller: the
findings deliberately carry no raw span, so there is nothing for a caller to
match on, and an attempt to do so wrote a real identifier while reporting the hit
as handled.

JSON goes to stderr in BOTH modes, so stdout means one thing only: redacted
artifact text, and only under --mask. It used to carry report-mode JSON, which
made `redact_scan.py in.md > out.md` write a status blob over `out.md` and look
plausible doing it -- that is precisely how ten artifacts were destroyed on a
measured run. Under this rule the same mistake yields an empty file, which
nobody mistakes for an artifact.

Exit codes -- three outcomes, deliberately distinct:
    0  CLEAN     scanned real content, matched nothing
    1  BLOCKED   matched at least one shape; do not write this artifact
    2  NO_INPUT  given nothing to scan. NOT a pass. This means the caller
                 wired the gate up wrong, and the artifact is unscanned.
"""

import json
import re

# Email domain whose addresses are attribution-safe and must never be redacted.
ATTRIBUTION_SAFE_DOMAIN = r"example\.com"
import sys
from dataclasses import dataclass
from enum import Enum


class SecretCategory(Enum):
    AWS_ACCESS_KEY = "AWS_ACCESS_KEY"
    GITHUB_TOKEN = "GITHUB_TOKEN"
    BEARER_TOKEN = "BEARER_TOKEN"
    GENERIC_KEY_ASSIGNMENT = "GENERIC_KEY_ASSIGNMENT"
    USER_URI = "USER_URI"
    NON_ROLE_EMAIL = "NON_ROLE_EMAIL"
    RAW_USER_IDENTIFIER = "RAW_USER_IDENTIFIER"


class ScanStatus(Enum):
    CLEAN = "CLEAN"
    BLOCKED = "BLOCKED"
    NO_INPUT = "NO_INPUT"


@dataclass(frozen=True, slots=True)
class Finding:
    category: SecretCategory
    line_number: int
    masked_preview: str
    note: str | None = None


@dataclass(frozen=True, slots=True)
class ScanResult:
    status: ScanStatus
    findings: list[Finding]


# AWS's own documented example key -- matches the AWS access key shape
# byte-for-byte but is a published placeholder, not a real credential.
# Plain string equality, not regex: an allowlist entry is never a pattern to
# interpret, and routing a literal through re.fullmatch risks a future entry
# containing a metacharacter (e.g. a "." in an email-shaped example) silently
# behaving as a wildcard instead of matching literally.
_ALLOWLIST: frozenset[str] = frozenset({"AKIAIOSFODNN7EXAMPLE"})

# Mirrors diff_fields.py's _NORMALIZERS dispatch-table style: one place to
# add a new secret shape rather than a new branch in scan().
_PATTERNS: tuple[tuple[re.Pattern[str], SecretCategory], ...] = (
    (re.compile(r"AKIA[0-9A-Z]{16}"), SecretCategory.AWS_ACCESS_KEY),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"), SecretCategory.GITHUB_TOKEN),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{8,}"), SecretCategory.BEARER_TOKEN),
    (
        re.compile(
            r"(?i)(?:api[_-]?key|secret|token)\s*[=:]\s*['\"]?[A-Za-z0-9/+_-]{16,}"
        ),
        SecretCategory.GENERIC_KEY_ASSIGNMENT,
    ),
    # User-URI pattern: redact real user ids, keep obvious test fixtures.
    (
        re.compile(r"\buser:(?!test_user_|test_|user_\d)[a-zA-Z0-9_-]+"),
        SecretCategory.USER_URI,
    ),
    # Reused from validate_no_pii.py's email pattern (lines 22-24), with an
    # added negative lookahead: your own domain's addresses are attribution-safe
    # (write-ups naturally cite reviewers by address) and must never be
    # flagged -- only addresses outside ATTRIBUTION_SAFE_DOMAIN are.
    (
        # Also skips GCP service accounts. They match the address shape but name
        # no person, and one in a component's locus.yaml blocked a candidate's
        # portfolio file on a measured run.
        re.compile(
            r"[a-zA-Z0-9._%+-]+@(?!" + ATTRIBUTION_SAFE_DOMAIN + r"\b)"
            r"(?![a-zA-Z0-9.-]*\.gserviceaccount\.com\b)"
            r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        ),
        SecretCategory.NON_ROLE_EMAIL,
    ),
    # A raw user identifier bound to a user-ish name. Found by a real run: a
    # portfolio write-up quoted `WARMUP_USER_ID = "<32 hex>"` straight out of
    # production source and this scanner returned CLEAN, though the no-identifiers rule names
    # identifiers explicitly. Deliberately requires the *assignment context*
    # rather than matching bare hex: this skill's own artifacts are full of
    # 32-hex md5 version-gate digests and 12-16 hex root-cause fingerprints,
    # and a bare-hex rule would block nearly every write it is meant to guard.
    (
        # The separator must stay loose. A real run leaked this in prose --
        # "header naming a fixed user id `<32 hex>`" -- not as an assignment,
        # so an `=`-or-`:` requirement missed it. Allow quotes, backticks and
        # whitespace between the label and the value, and allow the label
        # itself to be spaced ("user id") as well as joined ("USER_ID").
        re.compile(
            # Leading `(?:\b|_)` rather than `\b`: an underscore is a word
            # character, so `\buser` cannot match the USER inside a constant
            # named WARMUP_USER_ID -- which is exactly the shape found in
            # production source.
            r"(?i)(?:\b|_)(?:user[_\s-]?(?:id|name)|uid|account[_\s-]?id)\b"
            r"[\s=:'\"`(]{1,6}"
            r"(?!test|example|dummy|placeholder|xxx|unknown|null|none)"
            # An opaque identifier contains at least one digit; a Java class name
            # usually does not, and is not followed by nothing. Without both
            # guards, prose like "the user ID (ReasonedHybridFeedPage.java:193)"
            # matched, because that class name is 22 characters of the value
            # class -- and on a measured run that false positive cost a verified
            # candidate its portfolio file entirely, since a blocked write is
            # deliberately never retried.
            r"(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]{16,}(?!\.java)"
        ),
        SecretCategory.RAW_USER_IDENTIFIER,
    ),
)


def _is_allowlisted(match: str) -> bool:
    return match in _ALLOWLIST


def _mask(match: str) -> str:
    if len(match) <= 8:
        return "*" * len(match)
    return f"{match[:4]}{'*' * (len(match) - 8)}{match[-4:]}"


def _scan_line(line: str, line_number: int) -> list[Finding]:
    return [
        Finding(category, line_number, _mask(m.group()))
        for pattern, category in _PATTERNS
        for m in pattern.finditer(line)
        if not _is_allowlisted(m.group())
    ]


def scan(text: str) -> ScanResult:
    findings = [
        finding
        for line_number, line in enumerate(text.splitlines(), 1)
        for finding in _scan_line(line, line_number)
    ]
    status = ScanStatus.BLOCKED if findings else ScanStatus.CLEAN
    return ScanResult(status=status, findings=findings)


def mask(text: str) -> tuple[str, list[Finding]]:
    """Return the text with every matched span replaced by its masked form.

    This exists because the caller must never be asked to do the masking itself.
    The findings carry `masked_preview`, which is already asterisked and appears
    nowhere in the source, so a caller implementing `replace(masked_preview, ...)`
    matches nothing -- and on a measured run that wrote a real user identifier
    straight into an artifact while the exit code reported the hit as handled.
    Redaction belongs in the redactor.
    """
    findings = scan(text).findings
    out_lines: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        for pattern, _category in _PATTERNS:
            line = pattern.sub(
                lambda m: m.group() if _is_allowlisted(m.group()) else _mask(m.group()),
                line,
            )
        out_lines.append(line)
    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(out_lines) + trailing, findings


def _finding_to_dict(finding: Finding) -> dict[str, object]:
    return {
        "category": finding.category.value,
        "line_number": finding.line_number,
        "masked_preview": finding.masked_preview,
        "note": finding.note,
    }


def main(argv: list[str] | None = None) -> None:
    # Accept a path argument as well as stdin. Reading stdin only looks tidier,
    # but `redact_scan.py file.md` is the invocation everyone reaches for first,
    # and under a stdin-only main it silently scanned an empty stream and
    # reported CLEAN for every file. Two measured runs gated dozens of
    # artifacts that way and reported a clean sweep; at least one of those
    # artifacts contained a real user identifier.
    #
    # argv is a parameter rather than a read of sys.argv so that a caller which
    # already owns sys.argv -- a test runner, most obviously -- can drive this
    # without the runner's own flags being mistaken for a path to scan.
    args = sys.argv[1:] if argv is None else argv
    mask_mode = "--mask" in args
    args = [a for a in args if a != "--mask"]

    # Reject unknown flags instead of treating them as filenames or ignoring
    # them. An older revision of this script had no --mask at all and silently
    # ignored it, falling back to report mode; the caller's redirect then wrote
    # status JSON over the artifact. A flag this script does not understand must
    # stop the run, not change its behaviour quietly.
    unknown = [a for a in args if a.startswith("-")]
    if unknown:
        json.dump(
            {"status": "USAGE", "unknown_arguments": unknown, "findings": []},
            sys.stderr,
        )
        sys.exit(2)

    if args:
        with open(args[0], encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    else:
        text = sys.stdin.read()

    # An empty input is NOT a clean input. A gate that cannot tell "found
    # nothing" from "was given nothing" reports success without having checked,
    # which is worse than no gate at all because it is recorded as a pass.
    if not text.strip():
        json.dump({"status": ScanStatus.NO_INPUT.value, "findings": []}, sys.stderr)
        sys.exit(2)

    if mask_mode:
        # Redacted text on stdout so the caller can write it verbatim; findings on
        # stderr so a naive `> out.md` cannot silently capture the JSON instead.
        redacted, findings = mask(text)
        sys.stdout.write(redacted)
        json.dump(
            {
                "status": (ScanStatus.BLOCKED if findings else ScanStatus.CLEAN).value,
                "findings": [_finding_to_dict(f) for f in findings],
            },
            sys.stderr,
        )
        sys.exit(1 if findings else 0)

    result = scan(text)
    output = {
        "status": result.status.value,
        "findings": [_finding_to_dict(f) for f in result.findings],
    }
    # stderr, not stdout -- see the module docstring. Report mode produces no
    # stdout at all, so redirecting it into a file yields an empty file rather
    # than something that reads like a successfully written artifact.
    json.dump(output, sys.stderr)
    sys.exit(1 if result.status == ScanStatus.BLOCKED else 0)


if __name__ == "__main__":
    main()
