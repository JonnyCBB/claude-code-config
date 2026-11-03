# Scope resolution and outbound safety

## 1. Resolve the name before picking a strategy

**A bare name does not tell you which strategy it selects.** "Run the bug hunt on `music`" is
satisfied by strategy 1 if that is a component and by strategy 2 if it is a team's slug - one
component against a team's entire inventory. A team slug that matches a component directory name is
genuinely ambiguous, and a reader who has only seen it in a per-finding `component:` field will read
it as a component.

1. Look for a component of that name: a local checkout, a GitHub repository (`gh repo view
   <owner>/<name>`), or a directory in the monorepo you are in. A hit means strategy 1 is available.
2. Look for a team of that name in the ownership source: `CODEOWNERS` entries naming `@<org>/<name>`,
   or `gh api orgs/<org>/teams/<name>/repos`. A non-empty result means strategy 2 is too.
3. **If both return something, stop and ask the caller which they meant.** Do not pick the cheaper
   one to be helpful or the broader one to be thorough: this is the difference between a handful of
   agents and a few hundred, and the caller is the only one who knows.
4. If neither returns anything the name is wrong. Say so rather than falling back to a repo sweep,
   which is the unbounded strategy and the worst place to land by accident.

## 2. The three strategies

Every one produces the same thing: **a flat list of components**. No org traversal, no team
nesting, no org-directory lookup.

**1. Named component list.** The default. Each entry is a local checkout path, a GitHub
`owner/repo`, or a service directory inside a monorepo. **A bare list is a replacement, not a
reordering** - a run naming three components investigates exactly those three. Do not infer
otherwise from whether the caller said "limited to". A caller wanting named components *plus*
continued discovery has to say so.

**2. Single team.** Every component the ownership source assigns to that team: the directories its
`CODEOWNERS` entries cover in a monorepo, or the repositories `gh api orgs/<org>/teams/<team>/repos`
returns. **A display name is not a team slug**; resolve it empirically by cross-referencing a
component already known to belong to that team. Clone any repository not already on this machine
with `gh repo clone <owner>/<repo> -- --depth 1` into the run directory, read-only.

**3. Single system or repo.** **This is the unbounded one** - see section 4.

**Tier resolves per component**, identically across all three, from whatever the component declares
(a `tier` or criticality field in its catalog descriptor) or a component-to-tier mapping the caller
supplies. It is context for the banding rubric's fourth consideration, not a score, and nothing
multiplies it.

**The UNTIERED stratum rule.** A component with no tier anywhere is a **cataloguing gap, not a
scoping signal**. Report these as their own visible stratum labelled `UNTIERED`; **never fold them
into Tier 4**, which is a real assigned tier where `UNTIERED` is the absence of one; **never silently
exclude them**, or a cataloguing gap is mistaken for a gap in the org's actual scope. On a machine with
no tier source at all, every component is `UNTIERED`, and that is a correct run.

## 3. Two checks that must not come back

**Do not reintroduce the per-team cap.** It tripped once a team had been given N components. It is
gone along with the org traversal that supplied the membership it counted against, a
success-triggered cap was measured collapsing a team-scoped run to a single component, and two of
the three strategies have no team concept to count. Bounded verification is the real cost lever.

**Do not reinstate an org-directory lookup as a pre-flight requirement.** It was required only while
scope came from an org traversal, which is the only thing that ever walked an org tree. A pre-flight
that fails on a capability no live step uses gets routed around, taking the legitimate stops with it.

**Match pre-flight on capability, not on a namespaced tool name.** A measured run found the declared
tool names did not resolve in every runtime while the same capabilities were present under a
different prefix. Only a capability nothing provides is a stop.

## 4. The accepted risk: nothing bounds finder fan-out

Bounded verification caps the verification half, not this one. Named lists are bounded by the list
and teams by their membership, but **a system- or repo-scoped run over a large system is
unbounded**, and a 79-file component's unbounded fan-out was measured overrunning the session's
agent limit mid-run.

Under the retired cap a run always completed. **An overrun happens mid-run and the digest is written
at the end, so an overrun now produces no readable artifact at all** — worse than a bounded partial
run. **Mitigation is guidance, not mechanism: for a large system, use
a named component list and bound it yourself.**

## 5. Zero outbound actions, in three layers

The guarantee has to come from the runtime not having the tools, not from instructions.

**Layer 1 - `SKILL.md`'s `disallowed-tools`. Turn-scoped**, so it covers only the invoking turn and
clears at the next message. This skill's run is multi-turn by construction, so every turn after the
first is unprotected by it alone. **`SKILL.md`'s `disallowed-tools` is the only copy of the list**:
the message-sending tools of the common connectors (Slack send, schedule and draft; Gmail send).
This plugin registers no MCP server, so the list is defensive against co-installation. **Whenever
you connect a server with a write tool (tickets, incidents, chat, email), add its write tools here**,
established by reading the server's tool list rather than assuming from naming.

**Take the union of prefixes, not a substitution.** A dead name in a deny list fails open - the
guard protects nothing while reading as though it protects everything. MCP prefix resolution shifts
between sessions, so denying only the currently-live prefix leaves a hole whenever it changes.

**Layer 2 — each subagent's own `tools:` list. The durable layer**, applying to every spawn for the
life of the run. The actual investigation happens inside these agents, so this is the layer to
trust. **It only exists if the children really are the declared types.** Spawning as
`general-purpose` — the usual workaround when a type does not resolve — inherits **every** tool the
session holds, including any ticket, chat or incident creation, and the guarantee degrades to
instruction alone. Measured on seven consecutive runs. The fallback is sometimes the only way to
finish, so it is not forbidden; what must not happen is finishing such a run and **describing it as
structurally safe**. Say prominently in the run summary that the declared types did not resolve.

**Layer 3 — session and scheduler configuration**, not enforceable by the skill. Subagents inherit
the session's tool allowlist regardless of mode, so that allowlist should itself deny the Layer 1
list; and the scheduling substrate should be configured without write-capable chat or ticket servers
in the first place, since a tool that is never registered cannot be called.

**Residual risk, stated honestly.** `Bash` (needed for code search and local reproduction) is not
itself outbound, but a sufficiently capable shell could reach an external endpoint. The layers close
every named-MCP-tool path completely; they do not close raw network egress. That would need
sandboxing outside this skill's scope.

**Re-check `disallowed-tools` whenever a server is connected to the session or an existing one
gains a mutating tool.**

## 6. The digest, `open`, and the two disclosed wrinkles

The write is local, through `write_artifact.py`, exactly like every portfolio file. **`open <file>`
is a local process invocation, not a network write** — it creates nothing, comments on nothing and
notifies nobody, which is the whole of what the rule prohibits.

**Publishing stays a human step.** The digest is deliberately one self-contained file so a human can
publish it by dropping it somewhere. Adding a publish tool would move the guarantee out of the
durable Layer 2 and into the weakest layer. **Do not add one** — print the command if you like,
never perform it.

Two things are disclosed rather than hidden, in the same spirit:

- **A mechanism-verifier's build can upload to a remote cache or build-event service** when the
  repository's build config enables one by default (a `.bazelrc` with a remote BES or cache endpoint,
  a Gradle build scan). Nothing is created, commented on or notified, but it is a network write nobody explicitly chose, so it
  goes in the evidence trail.
- **The digest's stylesheet links three webfonts from `fonts.googleapis.com`.** The skill writes a
  local file and the *browser* fetches the font when a human opens it, so the browser is acting, not
  the skill. Two consequences are recorded rather than left to be discovered: a digest opened
  offline falls back to system fonts, and opening one is not a zero-network event.

## 7. `disable-model-invocation` is deliberately unset

The Skills docs recommend it for exactly this kind of side-effecting workflow, but as of Claude Code
v2.1.196 it **also blocks a scheduled-task prompt from executing the skill at all** — such fires
reach Claude as plain text. Since this skill exists to be schedulable, leaving it unset is correct.
**Do not add it**: its absence is deliberate, and adding it silently disables every scheduled fire.

The resulting risk of an unwanted auto-trigger is mitigated by the description's specificity, so
**the name must not be casually matchable** — that specificity is the only trigger guard.
