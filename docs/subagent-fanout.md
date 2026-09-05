# Subagent fan-out over many files

Guidance for the shape "split a large input into N chunks, spawn N agents, merge the results". It is a productive pattern, and it has one dominant failure mode: **an agent analyses part of its input, reports success, and nothing in the output reveals the gap.**

## The Read tool has two independent truncation ceilings

| Ceiling                  | What happens                           | How it fails                                                                 |
| ------------------------ | -------------------------------------- | ---------------------------------------------------------------------------- |
| **2000-line default**    | Returns the first 2000 lines only      | **Silently.** No warning in the result. The agent believes it read the file. |
| **~25k tokens per call** | The call errors and returns no content | Loudly. Recoverable, but costs a turn per attempt.                           |

The silent one is what corrupts results. The loud one only costs time.

## Size chunks by bytes, not lines

Line count does not predict the token cap, because density varies. Transcript-like text runs around 40 tokens per line, so an 800-line read can exceed 25k tokens while a 2000-line file still passes a naive line check. Measure, then convert:

```bash
wc -lc chunk.txt          # lines and bytes
# bytes_per_line = bytes / lines
# lines_per_read ~= 40000 / bytes_per_line     # ~40 KB per read leaves headroom
```

At roughly 90 bytes per line that lands near 450-500 lines per read. Compute it rather than guessing; the point of the arithmetic is to stay clear of both ceilings at once.

## Coverage accountability is the fix that actually works

Sizing alone is not sufficient, and it is not the load-bearing half. Give every agent:

1. **Its file's exact line count**, measured by you, not inferred by the agent.
2. **A requirement to state which ranges it actually read** in its output.

Evidence that this is the effective intervention rather than the sizing: on a 15-agent run where 12 chunks exceeded the line default, one classifier delivered 26 items, then recovered to 31 after being told its real line count and asked to re-read the uncovered range. Two later controlled comparisons could not reproduce the failure using sizing guidance alone — a single agent given one file and told to be thorough paginates correctly. What suppresses coverage in the real case is a **scarcity instruction** ("be ruthless, 10 excellent findings beat 60 mediocre ones") running alongside a large input: returning 26 good items feels like success, and nothing signals a missed tail.

If your fan-out prompt asks for quality over quantity, it needs the coverage requirement.

## Deliver results by file, not by message

Have each agent write its result to a path you specify and confirm the path, then block on a single wait:

```bash
until [ "$(ls results/*.json 2>/dev/null | wc -l)" -ge 15 ]; do sleep 15; done
```

Three reasons this beats collecting results through the message channel:

- **One resume point.** A single completion notification replaces a stream of idle pings handled one turn at a time, many of which are stale post-completion echoes from agents that already delivered.
- **Delivery cannot be silently lost.** A named teammate that produces only text has its output dropped.
- **Partial progress is inspectable mid-flight**, which is how the truncation above was noticed and how output quality could be spot-checked before the whole fleet finished.

## Check the partitioning before trusting a merge metric

A surprising dedup number is often correct. On one run, 417 merged candidates showed **zero** cross-batch duplicates, which read as a broken similarity threshold; the real cause was that each batch covered a disjoint set of inputs, so the items were genuinely distinct. Retuning the threshold would have introduced false merges and destroyed real findings. Verify the assumption that would make the metric expected before treating it as a bug.

## Comparing two variants

When A/B-ing a change to a fan-out prompt or skill:

- **Do not ask both arms to produce the artifact that is the intervention.** Asking both for a coverage report, when requiring a coverage report _is_ the change, yields 100% for both and proves nothing.
- **Use a proxy the arms are not told about.** For coverage, pick input that appears only in the final third and check whether the output references it.
- **Attribute results per file.** Multi-file `grep` output ordering does not reliably map to the arms; read each output by name. Getting this backwards inverts the conclusion.
