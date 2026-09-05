# Exemplar Answers

Good-vs-vague answer pairs, one per question dimension. The skill surfaces the matching pair inline whenever it asks an open-ended question — this teaches the user what kind of depth lands without lecturing them about "specificity".

A good answer is concrete, behavioral, and grounded in a real moment. A vague answer is abstract, opinion-shaped, or fluffy. Length is not the signal: the agent must call out cases where the vague answer is **long but shallow** so the user understands depth ≠ word count.

---

### Motivation / Problem

**Question asked**: "What's the hardest or most frustrating part of doing this today?"

**Vague answer**: "It's just kind of clunky and annoying."
_Why it's vague_: No specific behavior, no person, no moment. The agent cannot translate "clunky" into a behavior to fix.

**Good answer**: "Yesterday I had to copy six order numbers out of an email into a spreadsheet, then paste them one at a time into our system to look up status. It took 20 minutes and I missed one."
_Why it works_: Names the moment, the action, the count, the time, and the failure mode.

---

### Acceptance Criteria

**Question asked**: "Walk me through what should happen when a customer clicks the 'view orders' button."

**Vague answer**: "It should show their orders. Pretty simple. We just need a normal orders page like every other website has — list of orders, click into one, see the details, the usual stuff that makes sense, like Amazon or whatever, you know what I mean. It should just work."
_Why it's vague_: This is **long but shallow** — many words, zero observable behaviors. "The usual stuff" and "just work" defer every real decision back to the agent.

**Good answer**: "Show the last 30 days by default. Each order shows the date, total, and a status badge — 'Shipped', 'Delivered', 'Returned'. Click an order to see the items inside it. If they have more than 30 days of orders, there's a 'Show older' button at the bottom."
_Why it works_: Specifies defaults, fields, states, and the expansion path. Each clause becomes a GIVEN/WHEN/THEN downstream.

---

### Edge Cases / Failure Modes

**Question asked**: "What's the weirdest or worst version of this you've seen? What broke last time?"

**Vague answer**: "Sometimes it just doesn't work."
_Why it's vague_: No condition, no symptom, no frequency. Cannot become a test case.

**Good answer**: "Last Tuesday a customer's order had been refunded but the page still showed 'Shipped'. We figured out it was because the refund happened in our finance system, not the order system, and the page only reads from the order system."
_Why it works_: Identifies the cross-system inconsistency, the trigger event, and the data flow. Becomes a concrete failure mode the agent can design around.

---

### Success Criteria / Metrics

**Question asked**: "If we met again in 3 months and this was a huge success, what would have stopped happening in your day?"

**Vague answer**: "Things would just be better. We'd be more efficient and customers would be happier and we'd have a better system overall and stuff would be smoother. It would just feel like a win for the team."
_Why it's vague_: Long but shallow. "Better", "happier", "smoother" — none of these are measurable. The fluffy positivity hides the absence of a target.

**Good answer**: "I wouldn't get five Slack pings a day from support asking me to look up order status manually. The 'where is my order' contact rate would be down. New hires wouldn't need a week of shadowing to learn the workaround."
_Why it works_: Names a concrete behavior that should disappear, a metric that should drop, and an onboarding cost that should shrink.

---

### Scope (Essential / Nice-to-have / Out)

**Question asked**: "If we had to ship this in two weeks, what's the smallest version that still helps?"

**Vague answer**: "All of it, basically. Everything is important."
_Why it's vague_: Refuses to prioritize. Forces the agent to invent the cut line.

**Good answer**: "Read-only orders list with date and status is essential. Click-into-detail is essential. Filters by date are nice-to-have. Bulk export is out — nobody's asked for it."
_Why it works_: Three explicit tiers with reasoning. The agent can compose the scope table immediately.
