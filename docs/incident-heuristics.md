# Incident investigation heuristics

## Execution duration as error signal

If a recurring error (`MISSING_DEPS`, OOM, timeout) typically fails an execution within X minutes and the current execution has run well past X, the error is likely no longer occurring: just monitor. Check duration against typical failure time before recommending remediation.

## A quiet alert is not evidence of health

- **Re-query per region.** A global aggregate error ratio (0.03-0.29%, under its 0.3% threshold) called a dependency healthy while one region was returning `DEADLINE_EXCEEDED`.
- **Check the dependency's OUTGOING error rate**, not just what it serves.
- **Treat a multi-service co-fire as a prior to falsify**: several services alerting together points at a shared dependency; try to disprove that before investigating each separately.
- **Window truncation** can false-negative an ongoing incident when the query window cuts off the affected period.

## Registration gaps that present as application bugs

- **503 "no healthy upstream" while the service's own health checks pass** = missing from service discovery (registration or routing labels), not an app defect.
- **MCP auth succeeds, then reconnect fails with `-32000`** = missing network route registration, not an auth problem.

## What is in master is not what is running

Read the manifest at the last SUCCEEDED deploy, not HEAD. Drift comes from deploy tooling hash-skipping unchanged manifests (so a reconcile needs a real file change), deploys sitting `IN_PROGRESS` for days, and slot deletes failing silently.
