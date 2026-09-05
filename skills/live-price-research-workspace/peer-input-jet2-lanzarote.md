# Peer input — Jet2holidays, Lanzarote Feb 2027

**Received from another Claude session ("jet2price"), 28 Jul 2026. Deliberately NOT fed into the eval runs — see note at the bottom.**

Scenario: LGW → ACE, Sat 13 Feb 2027, 7 nights, 2 adults + 1 child (7), All Inclusive.

## Headline

Bookable. 38 AI packages. Cheapest _*Bluebay Lanzarote, 3*, Costa Teguise — £2,028 party total_*.

| Hotel                     | Rating | Resort                | Party total |
| ------------------------- | ------ | --------------------- | ----------- |
| Bluebay Lanzarote         | 3*     | Costa Teguise         | £2,028      |
| Relaxia Olivina           | 3*+    | Playa de los Pocillos | £2,086      |
| HL Club Playa Blanca      | 3*+    | Playa Blanca          | £2,094      |
| Floresta Apartments       | 3*+    | Playa de los Pocillos | £2,100      |
| Hotel Beatriz Playa & Spa | 3*     | Matagorda             | £2,108      |

## Inclusions (verbatim from the hotel page)

"Return flights London Gatwick / (3) 10kg hand luggage / (3) 22kg baggage / All Inclusive / (1) One Bedroom apartment / Coach transfers / ATOL Protected"

The `(3)` confirms the child's 22kg hold bag is included. **This is a landed total** — bags and transfers in.

## Flights

LGW 12:20 → ACE 16:35, Sat 13 Feb 2027
ACE 17:30 → LGW 21:30, Sat 20 Feb 2027

Both civilised. No red-eye.

## Free Child Place

Applies to all five: child's package cost £0, but still gets flight, 22kg + 10kg bags, transfer and AI board. This is why the total is 2 × pp (£1,014 × 2 = £2,028), not 3 × pp — the per-person-times-party-size trap.

## February date axis (party totals, same spec)

2nd £1,396 · 4th £1,468 · 6th £1,548 · 7th £1,500 · 9th £1,514 · 11th £1,722 · **13th £2,028** · 14th £2,008 · 16th £1,618 · 18th £1,434 · 20th £1,430 · 21st £1,416 · 23rd £1,416 · 25th £1,374 · 27th £1,432 · 28th £1,398

Route runs Tue/Thu/Sat/Sun only. 13–14 Feb is the half-term peak, roughly £600 above adjacent weeks.

## Trap the peer caught

Jet2's "holiday calendar" endpoint runs `applyDiscount=false`, so it shows higher per-person figures (e.g. £1,101 for 13 Feb) with no Free Child Place applied. The search-results totals are the correct ones. Textbook silent-parameter problem — see `references/booking-engine-craft.md` §7.

## Sources

- Results: https://www.jet2holidays.com/search/results?airport=7&date=13-02-2027&duration=7&occupancy=r2c7&destination=154&boardbasis=5&sortorder=1&page=1
- Cheapest hotel: https://www.jet2holidays.com/beach/canary-islands/lanzarote/costa-teguise/bluebay-lanzarote?duration=7&airport=7&date=13-02-2027&occupancy=r2c7&board=5&oflight=1532591&iflight=1532594&rooms=17608

## Gaps stated by the peer

- No explicit balance-due date shown pre-checkout (deposit £180, then 4 × £369, final £372).

## Why this is NOT in the eval

The Lanzarote brief is an **eval fixture I invented** to test the skill, not a real trip. Feeding externally-supplied answers into either the with-skill or baseline run would destroy the comparison — the whole point is to observe how each agent conducts the research itself. Kept here as a separate reference only.
