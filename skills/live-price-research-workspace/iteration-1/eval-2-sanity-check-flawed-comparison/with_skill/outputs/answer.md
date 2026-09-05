# Sanity-check: managed print supplier comparison

**Bottom line: I wouldn't send this to the board as it stands.** The ranking isn't wrong so much as it isn't a ranking — the three numbers don't measure the same thing, and the one at the top is at the top partly _because_ it excludes things the other two include. On the document's own figures, Vantage only stays cheapest if three years of toner and drums, installation at three sites, and mandatory end-of-term disposal certification come to under **£70 per device**. That's the whole margin.

There are four separate problems. The first one alone is enough to change the recommendation.

---

## 1. The prices aren't comparable

This is the big one. Reading the notes back into a table makes it obvious:

| Component                          | Vantage £68,400          | Norbury £71,200 | Castleford ~£79,950 _(est.)_ |
| ---------------------------------- | ------------------------ | --------------- | ---------------------------- |
| Hardware, 40 devices               | Yes                      | Yes             | Implied, not stated          |
| Servicing                          | Yes — "standard" tier    | Yes             | Yes                          |
| Consumables (toner, drums)         | **No** — billed at usage | Yes             | Yes                          |
| Installation, 3 sites              | **No** — quoted at order | Yes             | Yes                          |
| Secure-disposal cert _(mandatory)_ | **Not stated**           | Yes             | Yes                          |
| On-site engineer SLA               | Not stated               | Not stated      | Yes — 4 working hours        |
| **Is this a landed total?**        | **No**                   | **Yes**         | Yes, but estimated           |

Vantage's £68,400 is a partial figure being ranked against two complete ones. The gap to Norbury is £2,800 across 40 devices over three years — **£70 per device, or £1.94 per device per month**. For Vantage to actually be cheapest, everything in those three "No"/"Not stated" rows has to fit inside £70 per device.

I'm not going to put a figure on what consumables for 40 MFDs over three years cost — that needs a real quote, not my guess. But as a judgement: £70 per device is the sort of threshold a single toner cartridge clears. **My expectation is that equalising scope flips the recommendation from Vantage to Norbury**, and Norbury is also the one confirmed to include the certification the note calls mandatory. Treat that as an expectation, not a finding, until Vantage quotes it.

Two things that follow from this and matter independently of the arithmetic:

- **"Consumables billed at usage" isn't just a missing number, it's a different risk structure.** Norbury and Castleford absorb volume risk inside a fixed price; Vantage passes it to us. Even if the totals landed equal, those aren't the same deal, and a board should be told who carries that risk.
- **"Installation quoted separately at time of order"** means the final price isn't merely unknown — it isn't fixed. The board would be approving a supplier who prices a component _after_ the competitive decision is made, with no alternative left to price against.

The one genuinely like-for-like comparison in the document is **Norbury vs Castleford**: both landed, both inclusive. That gap is £8,750, or **£6.08 per device per month for a 4-working-hour on-site engineer SLA**. Whether that's worth it is a real question a board can answer. It just isn't the question the document asks.

## 2. Half the approved field wasn't priced

The framework lists six approved suppliers; three were approached, and the note says plainly they were chosen because "these are the three we used last time." So the shortlist was built from incumbency, not from the rules — and incumbency then appears _again_ as a reason to pick Vantage ("we've worked with them before"). The same factor is doing duty as both the sampling filter and the tie-breaker.

The observed spread across the three we do have is **17%** (£68,400 to £79,950). On a three-supplier sample with that much spread, the unpriced half of the field is not a rounding error. In my experience the option nobody got round to pricing is disproportionately often the cheap one, because shortlists get built from habit while prices are driven by whoever's hungry for the work.

There may also be a procurement-governance point here — some frameworks require a minimum number of returns or a documented rationale for restricting the field. Worth a five-minute check with procurement before this goes in a board pack, because it's the kind of thing that unwinds an award later.

## 3. One of the three numbers isn't a quote

Castleford's £79,950 is a construction: published list price scaled by volume, no site survey, "should be within 5%." Three problems:

- **It's sitting in a price column with a rank next to it.** The caveat is eight lines below the table. Tables get screenshotted into board packs; the paragraph underneath doesn't travel with them. If the estimate stays, it needs to be marked _in the cell_ — `~£79,950 (est., unquoted)` — not in prose.
- **The ±5% is itself unverified**, and the error isn't random. Scaling _list_ price by volume ignores volume discount, so it's biased high — and it's biased high against the supplier with the most inclusive scope and the only stated SLA. The estimating method penalises the most complete offer.
- **A tell worth fixing:** 40 × £1,999 = £79,960, not £79,950. It's £10 and it changes nothing, but a board member who spots it will discount every other number on the page.

For what it's worth, the stated ±5% band (£75,953–£83,948) doesn't overlap Norbury, so the estimate's _uncertainty_ doesn't change the Norbury/Castleford ordering. The objection isn't the range — it's ranking an estimate against quotes at all.

## 4. Nothing here can be traced back to a source

There's no quote reference, no date, and no contact against any of the three figures — and the only file in the folder is this one document. With S. Okafor gone, we can't tell how old these numbers are or whether either quote is still open. Managed print quotes typically carry a 30–90 day validity; if these are past it, the board would be approving a price no supplier is currently offering. Prices are snapshots, not standing offers, and this one isn't even date-stamped.

## 5. Things that could still flip it, that aren't in the document at all

Before recommending anyone, I'd want these on the page, because any of them can invert a 4% price gap:

- **Response SLA for Vantage and Norbury.** Castleford's 4-hour on-site is stated; the other two are silent. Across 40 devices and three sites this is the classic thing a cheaper bid is cheaper _for_.
- **Click charges and volume bands.** For Vantage this isn't a detail — with consumables at usage, the click rate _is_ the price.
- **Annual uplift / indexation.** A three-year "total" with an uncapped RPI clause isn't a total.
- **Lease vs purchase, end-of-term ownership, buy-out and auto-renewal clauses.** Completely different propositions with the same headline.
- **Equivalent hardware?** "40 multifunction devices" could be three different classes of machine. Mono/colour split, speed and finishing options need to match before any of these prices mean anything.
- **Break and exit terms.**

---

## What I'd do before this goes to the board

Roughly in this order — the first two are gates, not optimisations:

1. **Confirm in writing that Vantage can supply the mandatory secure-disposal certification.** If they can't, or it's chargeable, they're out before price is relevant. A front-runner failing a stated dealbreaker isn't a front-runner.
2. **Get a landed 3-year total from Vantage** — consumables at our actual volumes (send them last year's page counts with the mono/colour split), installation at all three sites, disposal certification, and their response SLA. Until that exists, Vantage doesn't have a comparable price and shouldn't be ranked.
3. **Get the other three framework suppliers from procurement** and run a scope-matched RFQ. Give all six the same inclusions list so this doesn't happen again.
4. **Book Castleford's site survey for a firm quote, or take them out of the ranked table** and hold them as "indicative, unquoted."
5. **Chase quote references and validity dates** for Vantage and Norbury and confirm both are still open.
6. **Add the uplift, exit, ownership and click-charge terms** to the pack.

If the board meeting can't move, the honest version of this paper is a one-page note saying: two comparable landed quotes exist (Norbury, Castleford-estimated), Norbury is cheaper of those two by £6.08 per device per month against a 4-hour SLA, Vantage has not yet quoted a comparable scope, and half the approved field is unpriced. That's a defensible thing to put in front of a board. The current ranking isn't.

## What I can't tell you

Whether Vantage is genuinely more expensive — that needs their landed quote, and I haven't invented one. What the three unapproached suppliers would bid. Whether the hardware specs are equivalent. And I couldn't verify any of the three figures against a source, because none was recorded.

Happy to redraft the paper around the corrected structure once the Vantage landed quote is in — or to write the scope-matched RFQ text for all six suppliers now, so the re-run is quick.
