# Eval fixtures

`source-hashes.txt` pins the sha256 prefix of each source document so drift is detectable.

**Bead fixtures are regenerated locally, not committed.** Before running an eval that needs one:

```bash
bd show <bead-id> --json > fixtures/<bead-id>.json
```

They are deliberately absent from version control because bead notes carry named individuals and
local filesystem paths, and committing them would breach artifact hygiene for a reproducibility gain
that a one-line command already provides. Pin them locally rather than reading the tracker live during
a run: `bd update --notes` replaces the whole field and is not audit-logged, so a bead's notes can
change under an eval with no trace.
