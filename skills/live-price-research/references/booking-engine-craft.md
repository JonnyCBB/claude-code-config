# Booking-engine craft

Practical techniques for pulling real prices out of live booking and quote engines. Everything here was learned by hitting it; each item costs an hour or more to rediscover.

## Contents

1. [Find the URL template first](#1-find-the-url-template-first)
2. [The four DOM traps](#2-the-four-dom-traps)
3. [Per-person vs total, and why ×3 sometimes lies](#3-per-person-vs-total-and-why-3-sometimes-lies)
4. [Whole-axis views: the biggest time saver](#4-whole-axis-views-the-biggest-time-saver)
5. [Bot protection and flaky UI](#5-bot-protection-and-flaky-ui)
6. [Identity and naming](#6-identity-and-naming)
7. [Silent parameter resets](#7-silent-parameter-resets)

---

## 1. Find the URL template first

Drive the search form **once** through the UI, then read the resulting URL. Almost every engine encodes the full query in the address bar. Once you have the template, every subsequent search is a single navigation instead of a dozen clicks — and it's reproducible, which matters because the user needs to verify your numbers.

Do this deliberately at the start rather than discovering it later. Note which parameter controls each variable, then vary one at a time.

Real examples of the shapes you'll meet:

```
# passengers encoded with child ages inline
?rooms=2-6              # 2 adults, one child aged 6
?rooms=2_1:6            # 2 adults, 1 child, aged 6
?adults=2&children=1&childAges=6

# entity ids rather than names
?masterId=390037        # a specific hotel
?units[]=203206:HOTEL   # a specific hotel
?units[]=000851:DESTINATION
?locationIds=82&dst=EGHR
```

**Get entity IDs from the autocomplete.** Type the name into the site's search box, click the suggestion, then read the ID that appears in the URL. That's usually far faster than hunting through result pages, and it disambiguates similarly-named entities.

Watch for **non-obvious internal codes**. Durations, board types and similar are often not the literal number: one engine used `duration=7115` for 7 nights and `9115` for 9, but `11115` silently fell back to 7 rather than erroring. When you swap a value, **verify the page reflects what you asked for** before trusting the number.

### Not everything lives in the URL

Some state is held client-side and never reaches the query string. Board-basis filters and per-person/total toggles are the usual offenders: the page shows what you selected, the address bar doesn't.

This matters in two directions, and the second one is easy to miss:

- **For you:** reloading your own "template" silently drops the filter, so you start reading unfiltered or per-person numbers without noticing.
- **For whoever you hand the URL to:** they open it and see something different from what you reported. Your provenance link doesn't reproduce your figure, and your work looks wrong even though it wasn't.

So after building a template, **reload it in a fresh tab and confirm it still reproduces the same result**. Where a filter or toggle turns out to be client-side, say so alongside the URL — "open this, then tick All Inclusive and switch the toggle to Total price" — rather than presenting the link as self-sufficient.

## 2. The four DOM traps

When prices are visibly on screen but your extraction returns nothing, it's almost always one of these. Diagnose before writing more selectors.

### content-visibility: auto

The site marks off-screen sections as skippable for rendering. `innerText` and text-extraction tools then return **only what is currently painted**. The page looks full; the text is nearly empty.

_Tell:_ `document.body.innerText.length` is small (a few thousand chars) despite a long page. Text you can see in a screenshot is absent from extraction.

_Response:_ don't fight it. Prefer a detail/entity page that renders fully, or scroll-and-capture in increments. Bulk-scraping a list in this state isn't viable.

### Virtualised lists

Only a handful of rows exist in the DOM at any moment; scrolling recycles them.

_Tell:_ a "247 results" header but three matching elements in the DOM.

_Response:_ accumulate into a persistent object across scroll steps (`window.__acc = window.__acc || {}`), scrolling in increments with a real pause — 800–1200ms — between each. Scrolling faster than the site renders collects nothing. Better still, use per-entity pages and skip the list.

### Shadow DOM

Cards render inside shadow roots, invisible to ordinary queries.

_Tell:_ `document.querySelectorAll('*')` finds zero elements containing text you can see; `document.querySelectorAll('select')` returns 0 on a page with obvious dropdowns.

_Response:_ walk shadow roots recursively (`el.shadowRoot`), or fall back to screenshots. Custom form controls in shadow DOM often have **no underlying `<select>`**, so `form_input` and value-setting both fail — keyboard interaction or clicking the rendered option is the way, and sometimes neither works. If a control genuinely can't be set, do not take a quote with the wrong value; record it as a gap.

### Cross-origin iframes

Results render in a frame you can't read.

_Tell:_ main-document text is a shell; `document.querySelectorAll('iframe').length` is non-trivial; `contentDocument` access throws or is empty.

_Response:_ screenshots, or find the same data on a first-party page.

## 3. Per-person vs total, and why ×3 sometimes lies

Engines display per-person or party-total, often with a toggle that **persists across navigations in one session but not another**. Mixing the two silently is a large, easy error.

Always establish which you're reading, and re-check after navigating. State it in your notes for every figure.

`total = pp × party size` holds _only_ when everyone pays the same. It breaks whenever there's a free or discounted place:

> Observed: `£1621pp` with `£3241 total` for a party of three — because the child was free, so the total was two adults. Multiplying by three would have overstated it by ~£1,600.

**Prefer the displayed total.** Where you must derive it, verify the arithmetic against a known-good case first, and flag any card advertising a free/discounted place as needing individual attention.

## 4. Whole-axis views: the biggest time saver

Many engines expose an entire axis in one response:

- **Month price calendars** on entity pages — every departure/start date at once
- **Price-band grids** — a week or month of options
- **Duration selectors** that re-price the whole calendar

One load can replace an entire axis of searches. Find these deliberately: open a single entity page and look for a calendar, grid, or matrix before planning any loop.

**Capture the whole view, always.** Storing only the cells your current output needs is the mistake that makes a wrong option-space unrecoverable — see the main skill.

## 5. Bot protection and flaky UI

**Device-verification interstitials** ("Verifying your device…", "Checking your browser") usually clear themselves in ~5 seconds. Wait and re-read. If an actual challenge is presented that requires solving, stop and tell the user — do not attempt to bypass it.

**Modals close on stray clicks.** Chaining several clicks blind is unreliable because each one shifts the layout. When a dialog is involved, act one step at a time and re-screenshot. Clicking the trigger while a panel is already open usually _closes_ it — a common cause of "my clicks did nothing".

**Custom dropdowns** resist automation in a predictable order of preference:

1. `form_input` with a ref — works when it's a real `<select>`
2. Setting `.value` and dispatching `change`/`input` events
3. Click to open, then click the rendered option (screenshot first for coordinates)
4. Click, then arrow keys and Enter

Long option lists (ages, durations) often need scrolling _within_ the dropdown, and scroll granularity rarely lands where you want. Closing and reopening resets to the top, which is frequently faster than nudging.

**Session state differs between browsers.** A toggle set in one browser doesn't apply in another. If switching mid-task, re-verify display settings or you'll mix units.

## 6. Identity and naming

The same property or product is listed under different names by different providers, and genuinely different things share names.

Observed in one small dataset: `Beach Albatros Resort` / `Beach Albatros Aqua Park` were the same place under two names, while `Titanic Royal`, `Titanic Palace`, `Titanic Resort & Aqua Park` and `Titanic Beach & Spa` were four different hotels. A same-name entity also existed in a completely different city.

**Record the exact listed name alongside your canonical name**, and confirm identity with a second signal — address, review count, facility count, or a URL slug — before treating two listings as the same thing. Getting this wrong silently corrupts a comparison in a way that's very hard to spot later.

## 7. Silent parameter resets

Engines quietly override what you asked for. Seen repeatedly:

- **Flexibility toggles** defaulting to ±3 days, returning prices for dates you didn't request
- **Duration snapped** to the nearest supported value
- **Board/spec filters dropped** when another parameter changed
- **Sort order reset** on pagination

After every search, **read back the applied parameters from the page** — dates, duration, party, spec — and confirm they match the request before recording anything. A price for the wrong configuration is worse than no price, because it looks valid.

Result counts are a useful canary: if a filter you applied doesn't change the count, it probably didn't apply.
