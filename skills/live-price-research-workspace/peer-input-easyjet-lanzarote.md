# Peer input — easyJet holidays, Lanzarote Feb 2027

**Received from another Claude session ("ezyprice2"), 28 Jul 2026 ~21:00 BST. NOT fed into the eval runs.**

Scenario: LGW → ACE, Sat 13 Feb 2027, 7 nights, 2 adults + 1 child (7), All Inclusive, 1 room.

## Headline

_*BlueBay Lanzarote, Costa Teguise, 3*, AI, One Bedroom Apartment — £2,247 party total_* (was £2,385, "Includes £137 off"). Per person £749. 35 AI results; sidebar range £2,247–£4,360.

Flights: LGW 07:30 → ACE 11:50 (Sat 13 Feb) · ACE 19:55 → LGW 23:55 (Sat 20 Feb).

Cheapest ten (party totals): BlueBay Lanzarote £2,247 · Monea Royal Monica £2,298 · Paradise Island £2,319 · Floresta Hotel £2,391 · HL Club Playa Blanca £2,415 · Beatriz Playa & Spa £2,466 · Beatriz Costa & Spa £2,485 · Sol Lanzarote £2,527 · Lanzarote Village £2,549 · Dream Bocayna Village £2,741.

## Inclusions — verified inside the booking funnel

- **Hold luggage: "3 x 23kg hold bag"**, outbound and return, status "Included", £0.
- Cabin: 3 × small under-seat bags only. Large cabin bag NOT included.
- **Transfers: "Shared — shuttle standard bus, approx. 45 mins", Included.** Private upgrade +£19pp.
- **Seats: NOT included and NOT quotable this far out** — "come back 30 days before your departure date". Cost unknown.
- ATOL protected, ABTA member.
- Basket: "Holiday package cost £2,247 / No taxes & charges due £0 / Total £2,247". No card fee, booking fee or tourist tax.
- Deposit £60pp = £180. Balance-due date unconfirmed.

## Source

https://www.easyjet.com/en/holidays/mixedresultlist?ibf=true&to=20-02-2027&from=13-02-2027&dst=ESLZ&sAccId=&geog=ES,ESLZ&flex=0&org=LGW&aa=0&rooms=2_1:7&page=1&take=10&orderBy=price&orderDirection=asc&m=0

## Why this is valuable beyond the number

**1. Triple corroboration.** Three independent lookups now agree:

|                         | Jet2 Bluebay | easyJet BlueBay |
| ----------------------- | ------------ | --------------- |
| Peer "jet2price"        | £2,028       | —               |
| Peer "ezyprice2"        | —            | £2,247          |
| Eval agent (with skill) | £2,028       | £2,247          |

Flight times match too (easyJet 07:30/19:55 in both).

**2. It closes a gap the eval agent logged.** That agent flagged: _"easyJet's '23kg bags' doesn't state 'per person' on the panel."_ This peer went into the funnel and read **"3 x 23kg hold bag"** — gap closed, and it confirms the child gets a full allowance.

**3. It found a reproducibility trap worth adding to the skill.** The All Inclusive board filter and the Per-person/Total toggle are **client-side state, not in the query string**. A shared URL will NOT reproduce the result — the recipient must re-tick the filter and re-flip the toggle. This has been added to `references/booking-engine-craft.md` §1.

## New unknown surfaced

Seat selection is not included on easyJet and cannot be priced until 30 days before departure. For a family of three wanting to sit together that is a real, currently unquantifiable cost — and it is not in any landed total on either side.
