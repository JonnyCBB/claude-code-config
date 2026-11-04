# The bd CLI contract

**Trigger: after any `bd` upgrade, and before writing a `bd` command into any instruction file, skill, hook or doc.** Every documented `bd` command is a promise that the installed `bd` accepts it.

## Check it

Ask the installed binary's `--help` whether each `bd <subcommand> --flags` shape you document is real.

## Why a version cannot be trusted

`bd` **v1.2.2 is a recovery re-release**: v1.2.0 and v1.2.1 were published without release testing, and v1.2.2 re-publishes the tested 1.1 line under a higher version, retracting them in `go.mod`. It went forwards in version and backwards in features, so anything written against 1.2.1 may not exist. Four things were assumed that do not: the `--status` flag on `create`, the `--if-status` flag on `update`, `bd reclaim` / `leases` / `heartbeat`, and the `revision` field. Review caught none; handing a command to a real binary did.

- **Ask the binary what it supports; never infer it from a version.**
- **A missing FLAG fails loudly; a missing FIELD does not.** `--if-status` errored on the first call; `revision` simply stopped appearing and the guard reading it stopped guarding. When `bd` changes, check JSON shapes too (`test_bd_live_contract.py` in the `beads-hq` repo does this).
