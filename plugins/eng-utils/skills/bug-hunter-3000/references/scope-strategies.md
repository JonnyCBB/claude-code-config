# Scope Strategies

This file is the single source of truth for how a run decides which components to
investigate. `SKILL.md` section 3 points here and does not restate any of it.

Three strategies, and every one of them produces the same thing: **a flat list of
components**. The run loop iterates that list. There is no org traversal, no
squad nesting, and no `bandmanager-mcp` requirement in any of them.

## Before you pick: resolve the name the caller gave you

**A bare name does not tell you which strategy it selects.** "Run the bug hunt on
`home-music`" is satisfied by strategy 1 if `home-music` is a component, and by
strategy 2 if it is a squad's owner slug. Those are different runs: one
component against a squad's entire inventory, with the cost multiplied by however
many components that squad owns.

`home-music` is the live example, and it is genuinely ambiguous rather than a
hypothetical. Section 2 below records it as the owner slug for the squad
displayed as "Surfaces Music", which is why it appears throughout this skill's
fixtures and examples. A reader who has only seen it in a per-finding
`component:` field will reasonably read it as a component id.

**Resolve it before dispatching anything, in this order:**

1. Ask `component-metadata-mcp`'s `get_component_id_context` for the name. A hit
   means a component exists with that id, so strategy 1 is available.
2. Ask `list_components_by_owner` for the same name as an owner. A non-empty
   result means it is also a squad slug, so strategy 2 is available.
3. **If both return something, stop and ask the caller which they meant.** Do not
   pick the cheaper one to be helpful and do not pick the broader one to be
   thorough. Guessing here is not a scoping preference, it is the difference
   between a run that costs a handful of agents and one that costs a few hundred,
   and the caller is the only one who knows which they wanted.
4. If neither returns anything, the name is wrong. Say so rather than falling
   back to a repo sweep, which is the unbounded strategy and the worst place to
   land by accident.

This is the same class of mistake as the replacement-versus-reordering rule in
section 1: a caller's phrasing accidentally carrying a decision the skill never
actually made. The fix is the same too, which is to make the skill ask rather
than infer.

## 1. Named component list

The caller enumerates the components. This is the default and the one to reach
for.

**A bare list is a replacement, not a reordering.** A run naming three components
investigates exactly those three and nothing else. Do not infer a different
reading from whether the caller happened to say "limited to" -- a bare list is
still a replacement. A caller wanting named components _plus_ continued discovery
has to say so explicitly.

That distinction is written out because it was a real ambiguity: a caller's
phrasing was accidentally disambiguating it, which meant the rule had never
actually been decided. `design-history-and-failed-approaches.md` section 3
records it.

## 2. Single squad

Resolve one squad's components with `component-metadata-mcp`'s
`list_components_by_owner(owner=<squad-slug>, tier=1|2|3|4)`.

- **There is no all-tiers wildcard.** Call it once per tier: `tier=1`, `tier=2`,
  `tier=3`, `tier=4`.
- **Then make a separate call for components with no tier field at all.** They
  are returned by none of the four per-tier calls and must be collected
  independently. See section 5.
- **A display name is not an owner slug.** The squad displayed as "Surfaces
  Music" owns components under the slug `home-music`. Resolve the slug
  empirically -- cross-reference a component already known to belong to that
  squad -- rather than deriving it from the display name.
- **And an owner slug is not obviously an owner slug.** `home-music` reads as a
  component id to anyone who has not seen this bullet, which is exactly how a
  single-component run and a whole-squad run get confused. If the caller handed
  you a bare name, resolve it first -- see "Before you pick" at the top of this
  file.

## 3. Single system or repo

Sweep every component under one system or one repository path.

**This is the unbounded one.** See section 6 before using it on a large system.

## 4. Tier resolution, identical across all three strategies

Tier is resolved **per component** via `component-metadata-mcp`'s
`get_component_id_context`, which is already in `agents/bug-hunt-finder.md`'s
tool list. It therefore works the same way for a named list, a squad, or a
system -- there is no strategy that resolves tiers differently, and no strategy
in which tier is unavailable.

Tier is needed because the threat-level rubric's fourth consideration takes it as
context (`behavior-dossier-and-verdict-schema.md` section 6). It is not a score
and nothing multiplies it.

## 5. The UNTIERED stratum rule

Rehomed here from the archived org-traversal reference. It still binds.

A component with no `reliability_tier` catalog field is a **cataloguing gap, not
a scoping signal**. The absence of a tier says nothing about the component's real
importance -- it means the catalog entry is incomplete.

- Report these components as their own visible stratum, labelled `UNTIERED`.
- **Never fold `UNTIERED` into Tier 4.** Tier 4 is a real, assigned tier;
  `UNTIERED` is the absence of one, and merging them hides the gap.
- **Never silently exclude them.** A cataloguing gap must never be mistaken for a
  gap in the org's actual scope.

## 6. The per-squad cap is retired

**Do not reintroduce it.** The cap tripped once a squad had been given N
components, skipping that squad's remainder. It is gone, along with the org
traversal that supplied the squad membership it counted against.

Two reasons it is not worth restoring. `design-history-and-failed-approaches.md`
section 2 measured a success-triggered cap collapsing a squad-scoped run to a
single component. And two of the three strategies above have no squad concept at
all, so a per-squad counter has nothing to count in them.

`SKILL.md` section 8's bounded verification is the real cost lever, and it is
unaffected by this.

### The accepted risk this creates, stated plainly

**Nothing bounds a run's finder fan-out any more.** Bounded verification caps the
verification half, not this one. Named lists are bounded by the list and squads
by their membership, but a **system- or repo-scoped run over a large system is
unbounded**.

`design-history-and-failed-approaches.md` section 7 measured a 79-file component
whose unbounded fan-out overran the session's agent limit mid-run, and is canonical
for its figures.

The consequence worth understanding before choosing strategy 3: under the cap a
run always completed. **A session-limit overrun happens mid-run, and the digest is
written at the end, so an overrun now produces no readable artifact at all** --
worse than a bounded partial run, which would at least have produced a digest
naming what it skipped.

**Mitigation is guidance, not mechanism: for a large system, use the named
component list (strategy 1) and bound it yourself.**

## 7. `bandmanager-mcp` is no longer a pre-flight requirement

It was required while scope came from the org traversal, which is the only
thing that ever walked an org tree. None of the three strategies above does, so
the check has nothing left to guard and `SKILL.md` section 1 no longer makes it.

**Do not reinstate it.** A pre-flight that fails on a capability no live step uses
is the "cries wolf" failure `design-history-and-failed-approaches.md` section 6
records: a stop that is wrong often enough gets routed around, taking the
legitimate stops with it.

## 8. Where the org traversal went

`references/archive/surfaces-org-traversal.md`. Archived rather than deleted
because it holds four gotchas that each cost a live session to find -- the
diamond-shaped org graph, the `get_group_by_id` nesting-and-None trap, the
100-member pagination limit, and the ownership-slug mismatch. No live step reads
it. This pointer exists so the file stays reachable from a live document at all.
