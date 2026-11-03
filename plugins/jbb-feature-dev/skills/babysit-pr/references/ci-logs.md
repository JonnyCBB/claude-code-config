# Getting a CI log, and reading it

**Find out which CI system the repo uses before you look for a log.** On a repo whose CI is not
GitHub Actions (Jenkins, BuildKite, CircleCI and similar), `gh run list` exits 0 with no output
at all, which looks exactly like a repo with no CI rather than like the wrong tool.
(`gh run view` is not the probe: with no run ID it fails on the argument, which at least
announces itself.) For GitHub Actions, `gh run view <run-id> --log-failed` gives the log.

## Finding the log

Every check on the commit usually shares one build ID, so take it from whichever URL carries one:
`gh pr view "$PR" --repo "$REPO" --json statusCheckRollup --jq '.statusCheckRollup[] |
(.detailsUrl // .targetUrl // "")'`. **Read both URL fields**: a CheckRun carries `detailsUrl`
and a StatusContext `targetUrl`, and both sit in one rollup. **Do not filter on the CI system's
name in the URL:** a check can link through a catalog or dashboard URL with no such segment.
Match the build-ID shape (for example a UUID).

The check name routes nothing here either: an aggregate check can be renamed to replace several
older postings, so it names a rollup, not a system. Try the build ID first; escalate only with
no build ID and no artifact URL. If the CI system's logs are restricted, put the build URL in
the escalation for a human.

If the CI system stores logs in a Google Cloud Storage bucket, an artifact URL under
`storage.cloud.google.com/<bucket>/` can be used directly. Otherwise:

```bash
set -o pipefail
ERR=$(mktemp); LOG=$(mktemp)   # not fixed paths: one babysit run could otherwise read
                               # another's build log
gsutil cat "gs://<ci-artifact-bucket>/<org>/<repo>/<build-id>/console.log" \
  2>"$ERR" | tail -300 > "$LOG"
echo "fetch exit: $?"; wc -l < "$LOG"
grep -Eio 'Reauth[A-Za-z]*Error|Reauthentication required|No URLs matched' "$ERR" | sort -u
grep -Eio 'ServiceException: 40[13]|Anonymous caller' "$ERR" | sort -u
head -3 "$ERR"
```

Print the discriminating lines in that same call — `mktemp` paths do not survive to your next
tool call, so "read the error file later" cannot be followed. **Grep and `head`, never `cat`:**
the reauth traceback is over a hundred Python frames, and `cat` puts all of them in your
context in place of the log, which is the very thing redirecting stderr was for.

**`set -o pipefail` is the load-bearing line.** Without it the pipeline reports `tail`'s status,
and `tail` succeeds at reading an empty stream — so a hard authentication failure arrives as
`exit 0` and an empty file. Measured: bare exits `0`, with `pipefail` exits `1`.

## An empty log has two causes wanting opposite responses

| stderr contains | Meaning | Do |
| --- | --- | --- |
| nothing, or `No URLs matched` | cannot tell a truly missing log from a lookup that failed quietly | UNMEASURED; escalate as ambiguous |
| `ReauthUnattendedError`, `Reauthentication required` | **your credentials, not the build** | stop; a human runs `gcloud auth login` |
| `ServiceException: 401`/`403`, `Anonymous caller` | **also your credentials** — no usable ones were presented at all | stop; a human runs `gcloud auth login` |
| `gsutil: command not found` | the tool is absent, which is not a fact about the build | escalate; a human installs the Google Cloud SDK |

**`gcloud auth list` is not a usable pre-check** — measured twice, it printed the account as
active (`*`) in the same session where `gsutil cat` demanded reauth. Trust only the `gsutil`
attempt.

**A credentials failure can word itself as a missing object.** Measured against the real bucket
with no usable credentials: `ServiceException: 401 Anonymous caller does not have
storage.objects.get access to the Google Cloud Storage object ... (or it may not exist)`. That
trailing clause is the trap — the fetch never reached the object, so the message is a fact about
your credentials and says nothing about whether the log is there. Route it by the `401`/`403`,
never by the parenthetical.

**The reauth row masks the other row rather than excluding it.** The failure happens during the
credential refresh, so the object was never checked — after `gcloud auth login` the fetch may
still come back empty because the log genuinely is absent. That second empty result is not a
regression.

## Confirm the log belongs to the failing build

A Jenkins-backed log carries `[Pipeline] End of Pipeline` and then
`Finished: SUCCESS` (or `FAILURE`) — the most reliable single line in the file. Match the two
independently: measured, an unrelated line sat between them, so an adjacency check fails on a
log that is perfectly good. **`Finished: SUCCESS` while the
rollup says failing means you have the wrong log**: a stale UUID fetched a real log for someone
else's build, and every pattern you then match is a fact about their run. Treat it as ambiguous.

## Classifying from the text

These strings name **tools, not failures**, so they appear in passing builds too — `checkstyle`
matched once in a green log. Search near the failure, and only after the check above.

| In the log | Fix class |
| --- | --- |
| `spotless`, `checkstyle`, `eslint`, `prettier`, `black`, `scalafmt`, `ktlint`, `ruff` | `lint` |
| `BUILD FAILED`, `COMPILATION ERROR`, `javac.*error`, `scalac.*error`, `cannot find symbol` | `build` |
| `Test.*FAILED`, `expected.*but was`, `AssertionError`, `FAILED.*::.*test` | `test` |
| `timed out`, `deadline exceeded`, `resource exhausted`, `OOMKilled`, `No space left` | none — escalate |
| nothing matched | none — escalate |

One build can hit several. **Fix lint → build → test in that order:** a compile error makes every
downstream test failure unreadable, and a formatter run after a test edit reformats the edit.
Infrastructure failures are never auto-fixed — retrigger **once**, since a timeout is often
transient, and escalate if it recurs.
