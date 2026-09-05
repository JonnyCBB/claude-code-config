# Finder Lenses

The second finder pass. `SKILL.md` section 4 dispatches it and defers here.

A **lens mandate** is a bug _class_ over the whole component, where a file-slice
mandate is a set of files. Same agent, same Finder Packet contract; only the
mandate's shape differs.

## Why a second pass exists at all

File partitioning has a structural blind spot that no amount of resizing fixes:
**a defect whose two halves live in different mandates belongs to neither finder.**

Measured on the run that added this file: both DI-scoping defects spanned three
modules -- a provider in `InfluenceModule.java` and ~14 consumers elsewhere. They
were found only because that provider file happened to be a solo mandate. Had it
been bin-packed, the finder that owned it would have had 40 other files to read
and the consumers would still have been outside its mandate. That is luck, not
method, and the lens pass is what replaces the luck.

## The five lenses

Each is derived from a class this method has actually produced, not invented.

| Lens                                 | What it hunts                                                                                     | Measured instance                                                                                                                                                            |
| ------------------------------------ | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Resource lifecycle & scoping**     | Providers, factories, pools, clients whose scope or shutdown does not match how they are consumed | Two `@Provides` methods missing `@Singleton`, creating ~14 and 4 redundant thread pools                                                                                      |
| **API-shape consistency**            | Every call site of one API compared against the others; the outlier is the finding                | `Collectors.toMap` without a merge function at one site where four siblings had one; an SLF4J call with one placeholder and two arguments                                    |
| **Asymmetric siblings**              | Parallel implementations that should behave alike and diverge                                     | `convertTrack` omitting a field `convertEpisode` sets; a counterfactual pipeline with 2 stages against a served pipeline with 4                                              |
| **Contract drift across boundaries** | Two sides of a boundary reading or writing different fields, defaults, or units                   | A gate reading `semSensitivityLabel` while the path it gates reads `isSemSensitiveContent`; a `1.0f` default on one side of a component boundary against `1.7f` on the other |
| **Dead / inert declarations**        | Configuration, guards, retries, metrics that cannot take effect as written                        | A Resilience4j retry that can never fire, because the wrapped call converts every failure into a success                                                                     |

**API-shape consistency is the cheapest and should not be dropped as trivial.** It
is grep-shaped rather than read-shaped -- enumerate call sites, compare argument
shapes, flag the outlier -- so it scales to a whole component for a fraction of a
reading finder's budget. Both defects it caught had _correct_ sibling usages in
the same repo, and one had already survived a hand-written sweep commit that was
explicitly looking for that exact pattern.

## This is not the degraded-path sweep

`agents/bug-hunt-finder.md` Process step 3 mandates a degraded-path parity sweep,
and the **Asymmetric siblings** and **Dead declarations** lenses look adjacent to
it. They are not the same and neither replaces the other:

- The sweep is **within a mandate**, run by every finder, on the slice it owns.
- A lens is **whole-component**, run once, across every mandate boundary.

The sweep would not have found the counterfactual-pipeline asymmetry from a
mandate that owned only half of it. Do not delete either believing the other
covers it.

## Lenses run blind to the file pass

Do not tell a lens finder what the file-partitioned finders returned.

The temptation is to pass the file pass's findings so lenses "skip what is already
covered" -- but a lens told a region is covered searches it less, and recall is the
only reason this pass exists. Deduplication happens after both passes, where it
costs nothing but arithmetic. Blindness costs one duplicate packet; anchoring
costs a defect.

## Duplicates are corroboration, not noise

A lens packet and a file packet describing the same defect will carry the **same
root-cause fingerprint** (`agents/bug-hunt-finder.md` computes it from the
normalized component plus the one-sentence mechanism summary).

Merge them into one candidate and **record both finders on it**. Two independent
finders reaching one defect from different directions is real evidence about that
candidate's strength, and collapsing it silently throws that away. Verify the
merged candidate once -- paying 3 more verification agents for a defect already
found twice buys nothing.

**Fingerprint merging is NOT the grouping rule.** `grouping-rule.md` consolidates
packets describing one defect found from two _sides_ via mutual defect-site
citation, and explicitly forbids declaration-against-declaration matching. This is
exact fingerprint equality on packets describing the _same_ site. They run at
different moments on different tests. Keep them apart; conflating them re-breaks a
the most-rewritten rule in this skill (`grouping-rule.md` records how often, and why).

Disclosed limitation, inherited from the fingerprint: it is exact-match hashing of
free text. Two finders phrasing one defect differently produce different
fingerprints and will not merge, surfacing as two candidates. A human reading the
portfolio can still see it. This is the same acceptable gap the `DUPLICATE`
disposition already carries, not a new one.

## No new agent type

Lens mandates are dispatched to `agents/bug-hunt-finder.md`, the same declared
type as file mandates.

This is deliberate and load-bearing for the zero-outbound guarantee. `SKILL.md` section 2 notes that the
zero-outbound guarantee is structural only while children are spawned as the four
declared agent types, each carrying a read-only tool list -- and that the usual
workaround when a type fails to resolve is `general-purpose`, which inherits
ticket, Slack and incident creation and degrades the guarantee to prose. A fifth
type is a fifth chance to hit that fallback for no benefit, since the Finder
Packet contract is identical either way.
