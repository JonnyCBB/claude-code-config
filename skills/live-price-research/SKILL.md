---
name: live-price-research
description: Method for gathering real, comparable prices from multiple live booking or quote engines — holidays, flights, hotels, insurance, energy, car hire, equipment — and turning them into a decision-grade comparison. Use this whenever the user wants prices researched or compared across more than one provider, hands you a spreadsheet/tracker/shortlist to fill in, or asks things like "what's the cheapest", "compare these options", "find me the best deal", "check these prices" or "fill this in". Also use it when extending or sanity-checking an earlier comparison. It exists to prevent four specific failures that look like success: comparing headline prices that bundle different things, pricing only the options someone already listed instead of every option the rules permit, letting a deliverable's schema decide what evidence you keep, and quietly inventing a number when a lookup fails.
---

# Live price research

Price research feels like data entry and isn't. The hard part is never "find a number" — it's making sure the numbers mean the same thing, that you searched the whole space rather than the part someone already wrote down, and that every figure can be traced back to something real.

The failure mode to fear is a full, tidy, confident spreadsheet that is wrong. It looks finished. Nobody checks it. The decision gets made on it.

## The order matters more than the effort

Most of the value comes from doing these in the right sequence. Doing them in the wrong order means re-doing them.

### 0. Derive the option space from the rules, not from the grid you were handed

If someone gives you a tracker, a shortlist, or a set of named scenarios, **treat it as a sample of the option space, not its definition**. Before pricing anything, write out what the underlying constraints actually permit, then diff that against what you were given. If it's a subset, say so explicitly and ask whether to expand.

This is the highest-leverage five minutes in the whole task. The option someone forgot to list is frequently the cheapest one, because grids get built from habit and round numbers while prices are driven by demand.

> Worked example: a holiday tracker listed six date patterns. The brief's rules permitted about twenty-five. One unlisted-but-legal departure date was ~£900 cheaper than the best of the six, and a later sweep showed that date was cheaper on _every single candidate_ — the grid had systematically excluded the cheapest region of the space.

The same applies to the candidate list. If the shortlist was inherited, check whether cheaper qualifying candidates exist outside it.

### 1. Run disqualifying screens before pricing anything

If candidates can be eliminated on non-price grounds — safety, eligibility, availability, compliance, hard requirements — screen first. Screening is cheap; pricing is expensive. Pricing a candidate you'll later disqualify is pure waste, and worse, a cheap disqualified option anchors everyone's expectations.

Check availability early too. A provider that can't sell the thing at all is a fast, valuable finding.

### 2. One reconnaissance pass across _all_ providers before any depth

Take one candidate, one configuration, and price it on **every** provider before going deep on any of them.

The purpose is not the prices. It's to learn:

- **What each price includes** — the single most important thing, see below
- **Which providers can even supply it** on the dates/spec required
- **The URL and query structure** of each engine, so later sweeps are cheap
- **Which providers are worth depth at all**

Skipping this is the most expensive mistake available. Building a large dataset on one provider before discovering its prices aren't comparable means the dataset has to be rebuilt or heavily caveated.

### 3. Normalise before you compare — build the inclusions matrix

**A headline price is not a comparable price.** Providers bundle differently and advertise the same word for different things. Before any cross-provider comparison, build an explicit table:

| Provider | Component A | Component B | Component C | Is this a landed total? |
| -------- | ----------- | ----------- | ----------- | ----------------------- |

Fill it from the provider's own "what's included" panel, not from assumption or brand reputation. Two findings that recur:

- The cheapest headline is often the least inclusive. Adding the missing pieces back can reverse the ranking entirely.
- **Corporate ownership does not imply parity.** Sister brands on the same platform routinely bundle differently. Verify each separately.

Until this table exists, any "cheapest" claim is unsafe. State plainly which prices are landed totals and which aren't.

### 4. Sweep the axis that moves price most and costs least to sweep

Identify which variable actually drives price, then find the cheapest way to explore it. Engines frequently expose a whole axis in one request — a month calendar, a price grid, a matrix view. When they do, one page load can replace thirty searches.

Sweep that axis across all candidates before refining anything else. Optimising candidate-by-candidate across a fixed set of the other variable is backwards and much slower.

### 5. Never narrow data at capture time

**Capture everything the source gives you; filter at reporting time.** If a page hands you a whole month, store the whole month even if your output only has room for four dates.

This is not tidiness — it's what makes step 0 recoverable. If your capture is shaped by your output schema, then the moment the schema turns out to be wrong, the evidence to notice it has already been thrown away.

> Worked example: an extractor pulled full-month calendars and kept only the four dates the grid asked for. The winning price passed through that filter and was discarded — invisible until the user found it independently.

## Never invent a number

If a lookup fails, the cell stays **empty** and the failure gets logged. An estimate that looks like a retrieved price is worse than a blank, because blanks get chased and estimates get trusted.

Each gap should record: what was being priced, which provider, what went wrong, and **the exact URL or query to retry**. A well-logged gap is a two-minute job for the user; a vague one is a re-run of the whole task.

This matters most under pressure. When a task is nearly complete and one cell is stubborn, the pull toward "reasonable estimate" is strongest and the damage is highest.

Flag when a figure comes from a different configuration than requested — a nearby date, a different room class, a flexible-dates toggle you didn't notice was on. Silently substituting is the same error as estimating.

## Record provenance as you go, not afterwards

Every figure needs: **source URL · retrieval date · what it includes · the exact spec quoted**. Retrofitting provenance is far more expensive than capturing it inline, and unsourced numbers get silently dropped by whoever checks the work.

Prices are **snapshots, not quotes**. They move — sometimes by meaningful amounts within hours. Date-stamp everything and say so.

## Before recommending: check what could invert the ranking

A price ranking is provisional until you've checked the attributes that can flip it. The pattern to watch for: **a small price difference hiding a large quality difference**.

Ask what a cheaper option might be cheaper _for_. Then check that specific thing on the leading candidates before recommending.

> Worked example: two dates differed by £6, so the cheaper one looked strictly better. Checking flight times showed the cheaper option returned at 01:40; buying a civilised return cost +£567, reversing the ranking completely. The £6 was an artefact of comparing on one axis while ignoring the one that actually mattered.

Also confirm the hard requirements — the pass/fail gates — on the leading candidate before optimising further down the list. A front-runner that fails a stated dealbreaker isn't a front-runner. Gates first, optimisation second.

## Deliverable shape

Whatever the output format, it should let a reader answer three questions without asking you:

1. **What's the recommendation, and what would change it?**
2. **Where did each number come from?** (source, date, inclusions)
3. **What's missing, and how would I get it?**

If you're filling someone's template, match its conventions — its columns, formats, and any colour coding for input vs derived cells. Add columns rather than restructuring, and say what you added and why. If the template can't express something important — like whether a price is a landed total — add that rather than letting the format hide it.

Make incompleteness visible in the artefact itself, not just in your message. A total that silently omits components should be labelled as such in the cell or an adjacent column, because the message gets forgotten and the file gets forwarded.

## Reporting

Lead with what changes the decision, not with volume of work done. Coverage stats matter, but they're not the finding.

State the uncomfortable conclusion plainly. If everything found is far outside budget, if the premise turns out to be wrong, or if the cheapest option fails a stated requirement — that _is_ the deliverable. Padding it with technically-complete-but-unusable rows helps nobody.

Separate confirmed from inferred, and be specific about what would resolve each open question.

## References

- **`references/booking-engine-craft.md`** — practical techniques for driving live booking/quote engines: finding reusable URL templates, the four DOM traps that make prices unreadable (content-visibility, virtualised lists, shadow DOM, cross-origin iframes), per-person vs total price handling, and free-child-place style pricing anomalies. Read this before automating any engine; these cost hours to rediscover.
- **`references/checklist.md`** — a condensed pre-flight and pre-delivery checklist to run against the method above.
