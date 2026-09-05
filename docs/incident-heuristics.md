# Incident investigation heuristics

## Execution duration as error signal

If a recurring error (e.g., `MISSING_DEPS`, OOM, timeout) typically causes an execution to fail within X minutes, and the current execution has been running significantly longer than X minutes, then the error is likely no longer occurring. In that case, no manual intervention is needed — just monitor.

Always check how long the current execution has been running relative to the typical failure time before recommending remediation actions.

## A quiet alert is not evidence of health

Three reinforcing findings from the same investigation family — do not conclude a dependency is healthy from an aggregate.

- **Re-query per region.** A dependency-health check reported `searchrank` "fully healthy" from a global aggregate error ratio (0.03-0.29%, under its 0.3% threshold) while another agent simultaneously found active `gue1` `DEADLINE_EXCEEDED` against it. Global aggregation hid a single-region failure.
- **Check the dependency's OUTGOING error rate**, not just its incoming/served errors. A service can look fine on what it serves while failing on what it calls.
- **Treat a multi-service co-fire as a prior to falsify**, not as coincidence. Several services alerting together points at a shared dependency; go disprove that before investigating each service separately.

Also beware window truncation: an ongoing-incident metric query can false-negative purely because the query window cut off the affected period.

## Registration gaps that present as application bugs

A service that 503s with "no healthy upstream" while its own health checks pass is usually not
broken code - it is missing from service discovery. Check registration and routing labels before
reading the application. The same shape applies to an MCP server whose auth succeeds but whose
reconnect then fails with `-32000`: suspect network/route registration, not credentials.

## What is in master is not what is running

Read the manifest at the last SUCCEEDED deploy, not at HEAD. Deploy tooling routinely hash-skips
unchanged manifests (so you cannot force a reconcile without a real file change), deploys can sit
`IN_PROGRESS` for days, and slot deletes can fail silently. Any of the three leaves HEAD and the
running config disagreeing.
