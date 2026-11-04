# Verification doctrine and instrument traps

These apply across every phase rather than at one step, which is why they are here rather than
inline. Read before phase 9.

## Liveness: never a single sample, never the status field

**`status: error` from agent-deck lies.** Confirm liveness by **advancement across two reads** —
token count or elapsed timer moving — never by the status field and never by one sample.

**`read -t <n>` does not reliably sleep in this harness.** Two "separate" reads taken an instant
apart produce identical values, which look exactly like a frozen worker. Use **separate tool
calls with a printed timestamp**, and check the wall clock advanced as much as the thing you are
measuring:

```
13:15:17  (11m 42s · ↓ 31.2k tokens)
13:15:20  (11m 45s · ↓ 31.2k tokens)      3s elapsed, 3s on the timer -> ALIVE
```

## Instrument traps, measured

**`bd show --json` returns an array, not an object.** A `.status` selector on it yields uniformly
`NOT FOUND`, which reads exactly like a set of deleted beads. `bd list --json` also has a
narrower projection than `bd show --json`.

**Run `bd <cmd> --help` before writing any `bd` command into a file, and record the version the
file was written against.** This rule matters more than any specific flag fact — flag facts go
stale between release candidates. A worked example of exactly that: a setup record written on
2026-09-10 states that `bd create` has no `--status` flag; against `bd 1.3.0-rc.1` on the Mac,
`bd create --help` prints `-s, --status string  Initial status`. Whichever of those was measured
on a different binary, the durable lesson is the rule, not the flag.

## MCP reality on a fresh VM

- **The startup warning line under-reports.** It said "9 MCP servers need authentication" where
  `/mcp` enumerated 50 servers across connected, needing-auth and hard-failed. **Count from
  `/mcp`.**
- **Several servers are dual-registered, and the first-party copy is live while the plugin copy
  is not.** Slack and several other servers have all been connected under `claude.ai` while
  auth-gated under `plugin:jbb-feature-dev`. Those capabilities are not missing, they are under a
  different name — **name the connected one in dispatch specs.**
- **One server can fail under two distinct plugin registrations, not one**
  (`plugin:jbb-feature-dev:<server>` and `plugin:eng-utils:<server>`),
  and agent definitions depend on them. A connection failure is not a missing capability.

## Codex on a headless VM (optional)

**Install without root.** npm's global prefix here is `/usr`, so `npm install -g @openai/codex`
needs sudo. This does not, and lands the binary on an existing PATH entry:

```bash
npm install -g --prefix "$HOME/.local" @openai/codex
```

**Run the egress check before touching auth** — it is the decisive one, and its good answer is a
failure code:

| host | result | meaning |
| --- | --- | --- |
| `api.openai.com/v1/models` | **401** | reachable, just unauthenticated — the good answer |
| `auth.openai.com` | 403 | the browser sign-in flow cannot complete |
| `chatgpt.com` | 403 | as above |

A bare `curl` can draw a 403 from bot protection rather than a corporate block, so do not
over-read those two. The 401 is what matters.

**The interactive sign-in cannot complete on a remote box; two stdin paths can:**

```bash
printenv OPENAI_API_KEY     | codex login --with-api-key
printenv CODEX_ACCESS_TOKEN | codex login --with-access-token
```

**Script only the API key route.** A copied token expires and needs a human again.

**`codex doctor` is worth running as a setup gate.** It has reported everything green except auth
plus one warning that matters — *"Responses WebSocket failed; HTTPS fallback may still work"* — so
Codex may run degraded even once authenticated. That is a second, independent problem from the
credential, and worth stating separately in the report.

`agent-deck` supports Codex natively (`launch -c codex --model <id>` creates the worktree and
registers the parent), so the gap is purely the credential.
