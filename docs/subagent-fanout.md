# Subagent fan-out over many files

For "split a large input into N chunks, spawn N agents, merge the results". The dominant failure: **an agent analyses part of its input, reports success, and nothing in the output reveals the gap.**

## The Read tool has two independent truncation ceilings

| Ceiling | What happens | How it fails |
| --- | --- | --- |
| **2000-line default** | Returns the first 2000 lines only | **Silently.** The agent believes it read the file. |
| **~25k tokens per call** | The call errors, no content | Loudly; costs a turn per attempt. |

## Size chunks by bytes, not lines

Density varies (transcript-like text is ~40 tokens per line, so 800 lines can exceed 25k tokens). Measure, then convert:

```bash
wc -lc chunk.txt          # lines and bytes
# bytes_per_line = bytes / lines
# lines_per_read ~= 40000 / bytes_per_line     # ~40 KB per read leaves headroom
```

At ~90 bytes per line that is ~450-500 lines per read. Compute it to stay clear of both ceilings.

## Coverage accountability is the fix that actually works

Sizing alone is not enough. Give every agent:

1. **Its file's exact line count**, measured by you, not inferred.
2. **A requirement to state which ranges it actually read.**

What suppresses coverage is a **scarcity instruction** ("be ruthless, 10 excellent findings beat 60 mediocre ones") alongside a large input: 26 good items feels like success and nothing signals the missed tail. On a 15-agent run a classifier delivering 26 items recovered to 31 once told its real line count and asked to re-read the uncovered range. A fan-out prompt that asks for quality over quantity needs the coverage requirement.

## Deliver results by file, not by message

Have each agent write its result to a path you specify, then block on one wait:

```bash
until [ "$(ls results/*.json 2>/dev/null | wc -l)" -ge 15 ]; do sleep 15; done
```

- **One resume point** instead of a stream of idle pings, many stale echoes from agents that already delivered.
- **Delivery cannot be silently lost.** A named teammate that produces only text has its output dropped.
- **Partial progress is inspectable mid-flight.**

## Check the partitioning before trusting a merge metric

417 merged candidates showing **zero** cross-batch duplicates looked like a broken similarity threshold; each batch covered a disjoint input set, so the items were distinct. Retuning would have caused false merges. Verify the assumption that makes the metric expected before treating it as a bug.

## Comparing two variants

The traps in [skill authoring traps](skill-authoring-traps.md) apply. Fan-out specific: use a proxy the arms are not told about (for coverage, input that appears only in the final third).
