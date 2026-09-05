# Learning Taxonomy

Three tiers based on impact evidence. Only extract Tier 1 and Tier 2 learnings.

## Tier 1 — Highest Value

Things the model cannot know from training data. These show the largest gains when
stored as persistent context (+42-52pp for low-training-coverage domains, SkillsBench).

| Category | Detection Signal in Transcript |
|----------|-------------------------------|
| `proprietary_api` | User corrects model's API usage; model discovers internal framework behavior empirically; "it turns out the API actually..." |
| `bug_workaround` | Error → investigation → fix sequence; "the fix was..."; "it was actually caused by..."; stack trace followed by resolution |
| `tool_discovery` | Tool calls that succeed/fail unexpectedly; "you can actually use X for Y"; undocumented tool behavior; MCP tool capabilities verified empirically |
| `user_correction` | "No", "don't", "stop doing X", "that's wrong", explicit redirects; ALSO positive confirmations of non-obvious approaches: "yes exactly", "perfect, keep doing that" |
| `infrastructure_gotcha` | Env-specific behavior that differs from docs, config differences between environments, auth quirks, expiry dates, network topology surprises |

### Tier 1 Examples

**proprietary_api:**
"ADK 2.3.0 has a SEPARATE validator rejecting non-START static edges into mode='chat'
LlmAgents — discovered empirically, not documented anywhere"
Signal: empirical discovery, contradicts assumptions

**bug_workaround:**
"SEAL fresh-session harness `_child_environment` stripped Vertex AI env vars causing
'No API key' error — fix: allowlist env forwarding in fresh-session mode only"
Signal: error → investigation → fix sequence

**tool_discovery:**
"Agent-tool subagents CAN spawn nested agents and have the Skill tool — verified
empirically, contradicts the assumption that nesting doesn't work"
Signal: empirical verification of undocumented capability

**user_correction:**
"Auto mode only suppresses tool-use prompts, NOT skill interactive gates — stop
skipping the wave-structure approval step in create-plan-tdd"
Signal: explicit user correction of model behavior

**infrastructure_gotcha:**
"service_auth.grpc.authenticated_channel constructs insecure_channel (plaintext),
while service.internal.example:443 is the HTTPS edge proxy — plaintext there gets socket closed"
Signal: environment behavior differs from expectation

## Tier 2 — Medium Value

Encoded preferences and decisions. Valuable for continuity across sessions.

| Category | Detection Signal in Transcript |
|----------|-------------------------------|
| `decision_rationale` | "Because...", "we chose X over Y", "the reason is...", explicit comparison of alternatives |
| `workflow_preference` | User corrects process or approach; "I prefer...", "always do X before Y", "don't bother with..." |
| `confirmed_approach` | "Yes exactly", "perfect", accepted non-obvious choices without pushback — the user validating a judgment call |
| `project_context` | Timelines, ownership, deadlines, strategic context; convert relative dates to absolute (e.g., "Thursday" → "2026-07-03") |
| `relationship` | "X is owned by Y", "talk to Z about this", team boundaries, system ownership |

### Tier 2 Examples

**decision_rationale:**
"We use Agent-tool wrappers instead of claude -p for stage invocation because subagents
can spawn nested agents and have the Skill tool"
Signal: explicit "because" with alternatives considered

**workflow_preference:**
"Edit plugins/<name>/, never plugins/marketplaces/ (those are untracked clones)"
Signal: user correction about where to make changes

**confirmed_approach:**
"Yeah the single bundled PR was the right call here, splitting this one would've just
been churn"
Signal: user validates a non-default approach

**project_context:**
"Merge freeze begins 2026-03-05 for mobile release cut"
Signal: timeline info (relative date already converted to absolute)

**relationship:**
"HBM is owned by surf-formation, not Home Assembly"
Signal: organizational ownership statement

## Tier 3 — DO NOT EXTRACT

Skip these entirely. Standard SE skills show zero improvement 80% of the time
(SWE-Skills-Bench), and comprehensive documentation actively hurts (-2.9pp, SkillsBench).

| Category | Why skip |
|----------|---------|
| Standard language patterns | Model knows Python, Java, Scala idioms from training |
| Well-documented library usage | Redundant with training data (e.g., pandas, React, gRPC basics) |
| Architecture overviews | Model explores the filesystem directly when needed |
| Generic best practices | Can conflict with model's already-correct approach |
| Session-specific ephemera | No future value ("let me check that file", "reading now") |
| Code written or read this session | Already in the codebase; no need to re-store |
| Things already in CLAUDE.md or docs | Redundancy causes -2 to -3% performance penalty |

## Confidence Scoring

| Score | Criteria |
|-------|---------|
| 0.9-1.0 | Explicit user correction or stated preference; empirically verified fact with evidence |
| 0.7-0.89 | Clear pattern in transcript; unambiguous discovery or decision with rationale |
| 0.5-0.69 | Implicit preference (accepted without pushback); plausible inference from context |
| 0.3-0.49 | Weak signal; single occurrence; could be session-specific rather than durable |
| <0.3 | Too ambiguous to extract — discard |
