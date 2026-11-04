# Follow-up capture: the rules around the command

The command block and its core rules are in `CLAUDE.md`. Over-capture is cheap and under-capture is the failure mode: work that exists only in chat scrollback is lost with the session.

- **One shell invocation.** `$ID` does not survive between tool calls, and `bd update "" -s deferred` prints an error and exits 0, so a split leaves the bead `open`.
- **The quoted heredoc is not ceremony.** A title routinely quotes someone else's words and goes straight into a shell command. Written inline it is interpolated: a title reading ``the `bd ready` query misses deferred beads`` once executed `bd ready` and spliced the output into the title. `<<'BD_TITLE'` turns off expansion and `"$TITLE"` is not re-expanded.
- **`-l agent-proposed` plus `bd update -s deferred` keep the item out of `bd ready` until Jonny confirms it.** `bd create` has no status flag on bd 1.2.2, so the bead is dispatchable until the update lands; closing that window is `hq-l7qs`. Anything Jonny files carries no flags and is live immediately.

1. **A child (`--parent`)**: pass `-l agent-proposed` and run the `bd update -s deferred` step explicitly. Beads inherits labels parent-to-child, not status, so a child of a confirmed parent would default to `open` untriaged.
2. **Confirmation is a status transition** (`deferred` to `open`), never a `confirmed` label, which children nobody looked at would inherit.
3. **Rescue ephemeral evidence.** If the proof lives in `/private/tmp`, a scratchpad, or only your context, copy it outside any git-pushed directory and record the absolute path on the bead. Durable evidence (git paths, PR numbers, merged commits) is referenced, never copied.

**The description bar:** a stranger opening it later must understand and reproduce the problem without asking Jonny. Include the fact you learned at cost and any trap that would mislead someone who has not done the digging. "Re-phase the injectors" is not delegatable; the same line plus the file path, the gate name and how to verify is.
