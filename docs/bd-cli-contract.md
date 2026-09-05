# The bd CLI contract

**Trigger: after any `bd` upgrade, and before writing a `bd` command into any instruction file,
skill, hook or doc.**

Every `bd` command this repo documents is a promise that the installed `bd` will accept it.
Nothing checked that promise until 2026-08-19, and by then three separate files were telling
agents to run a flag that no longer exists.

## Run it

```
python3 scripts/tests/test-bd-cli-contract.py
EXPECT_BOOTSTRAP_RED=1 python3 scripts/tests/test-bd-cli-contract.py   # must exit 1
```

It extracts every `bd <subcommand> --flags` shape from `CLAUDE.md`, `docs/`, `hooks/`,
`scripts/`, `agents/`, `skills/` and `plugins/`, and asks the installed binary's own `--help`
whether each one is real. It takes about 0.6 seconds.

## What went wrong, and why it was invisible

`bd` **v1.2.2 is a recovery re-release, not an upgrade.** Its release notes record that v1.2.0
and v1.2.1 were published by accident without release testing, and that v1.2.2 re-publishes the
tested 1.1 line under a higher version number, retracting v1.1.1, v1.2.0 and v1.2.1 in `go.mod`.

So `bd` went **forwards in version and backwards in features**. Anything written against 1.2.1
may simply not exist on 1.2.2. Four things here were:

| What                                  | Where it was assumed                               |
| ------------------------------------- | -------------------------------------------------- |
| the `--status` flag on `create`       | the follow-up capture rule, the stop hook, a skill |
| the `--if-status` flag on `update`    | the pre-triage agent (`jbrooksbartlett-k123`)      |
| `bd reclaim` / `leases` / `heartbeat` | the conductor docs (`jbrooksbartlett-m248`)        |
| the `revision` field                  | the pre-triage agent (`jbrooksbartlett-wal3`)      |

(Those first two are written as flag names rather than as whole commands on
purpose. Spelling them out as runnable commands would make this page fail its own
check - which is the check behaving correctly, since it cannot tell a command you
are meant to run from one you are meant to avoid.)

None of these were caught by review. They were caught by handing a command to a real binary.

## Two traps worth knowing

**A version number is the wrong thing to key off.** 1.2.2 is higher than 1.2.1 and has fewer
features. Ask the binary what it supports; never infer it from a version.

**A missing FLAG fails loudly. A missing FIELD does not.** `--if-status` produced
`Error: unknown flag` on the first call. `revision` just stopped appearing, and the guard that
read it silently stopped guarding. A flag sweep would never have found the second one, so when
`bd` changes, check the JSON shapes too - `test_bd_live_contract.py` in the `beads-hq` repo
does this for the fields that package depends on.

## Adding an exemption

`KNOWN_GAPS` in the test holds breakages that are real, filed and deliberately unfixed. **An
entry requires a bead id.** The list is checked in both directions, so an exemption that has
stopped being necessary fails the test too and cannot quietly outlive its cause.
