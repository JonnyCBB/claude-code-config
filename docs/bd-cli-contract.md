# The bd CLI contract

**Trigger: after any `bd` upgrade, and before writing a `bd` command into any instruction file, skill, hook or doc.** Every documented `bd` command is a promise that the installed `bd` accepts it.

## Run it

```
python3 scripts/tests/test-bd-cli-contract.py
EXPECT_BOOTSTRAP_RED=1 python3 scripts/tests/test-bd-cli-contract.py   # must exit 1
```

It extracts every `bd <subcommand> --flags` shape from `CLAUDE.md`, `docs/`, `hooks/`, `scripts/`, `agents/`, `skills/` and `plugins/` and asks the installed binary's `--help` whether each is real (~0.6s).

## Why a version cannot be trusted

`bd` **v1.2.2 is a recovery re-release**: v1.2.0 and v1.2.1 were published without release testing, and v1.2.2 re-publishes the tested 1.1 line under a higher version, retracting them in `go.mod`. It went forwards in version and backwards in features, so anything written against 1.2.1 may not exist. Four things were assumed that do not: the `--status` flag on `create`, the `--if-status` flag on `update`, `bd reclaim` / `leases` / `heartbeat`, and the `revision` field. (The first two are written as flag names, not whole commands, because spelling them as runnable commands would fail this page's own check, which cannot tell a command to run from one to avoid.) Review caught none; handing a command to a real binary did.

- **Ask the binary what it supports; never infer it from a version.**
- **A missing FLAG fails loudly; a missing FIELD does not.** `--if-status` errored on the first call; `revision` simply stopped appearing and the guard reading it stopped guarding. When `bd` changes, check JSON shapes too (`test_bd_live_contract.py` in the `beads-hq` repo does this).

## Adding an exemption

`KNOWN_GAPS` in the test holds breakages that are real, filed and deliberately unfixed. **An entry requires a bead id.** The list is checked both ways, so an exemption that is no longer needed fails the test.
