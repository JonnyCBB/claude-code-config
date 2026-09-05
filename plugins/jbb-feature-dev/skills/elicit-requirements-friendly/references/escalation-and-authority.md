# Escalation and Authority Rules

Behavioral rules surfaced during the friendly interview. Three sections:

1. **Authority Rules** — when the agent should ask the user vs. decide silently and record the choice.
2. **Escalation Triggers** — what to do when the user gives multiple vague answers in a row.
3. **Decisions-Log Shape** — the format the agent uses when recording silent decisions in the requirements document's `## Technical Assumptions` section.

---

## Authority Rules

The agent has an enormous decision surface. Asking about every choice exhausts the user; deciding everything silently produces a doc the user can't trust. The friendly skill threads this needle with one heuristic:

**Ask when the answer changes the user's mental model of the product. Decide silently when it only changes implementation.**

In other words: ask when it affects UX (what the user sees, says, or does in the product). Decide otherwise — and write the decision into `## Technical Assumptions` so the user can rubber-stamp or push back later.

### Worked examples

| Decision                                                                 | Ask or decide?                                        | Why                                                                                            |
| ------------------------------------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Should login require a password, magic link, or both?                    | **Ask**                                               | UX-affecting. Changes how the user describes "logging in".                                     |
| Which auth library implements that pattern?                              | **Decide silently**                                   | Implementation. User does not perceive it.                                                     |
| What framework should the app use (React vs Vue vs Svelte)?              | **Decide silently**                                   | Implementation. The user doesn't pick.                                                         |
| What color is the primary action button?                                 | **Decide silently** initially, **show in plan recap** | The user can reject in mutual confirmation; no need to interrupt with a swatch picker.         |
| What's the format of the order ID shown on the page?                     | **Ask**                                               | UX-affecting. The user reads this number aloud to customers on calls.                          |
| What error code does the backend return on a refund mismatch?            | **Decide silently**                                   | Internal. User never sees it.                                                                  |
| Should the "view orders" button live in the header or in a left sidebar? | **Ask**                                               | UX-affecting placement.                                                                        |
| What retry policy does the backend use for transient failures?           | **Decide silently**                                   | Implementation, unless the user has stated reliability concerns; then surface as a recap line. |

### Default posture

If the agent is uncertain whether a decision is UX-affecting, prefer to ask once with a Recommended option. One extra question is cheaper than producing a doc that codifies the wrong default.

---

## Escalation Triggers

The friendly tone breaks when the user is genuinely stuck. The skill must detect this and pivot.

### Trigger condition

After **two** vague answers in a row on the same dimension, escalate. A vague answer is one the agent cannot translate into a behavior, a number, or a comparison. ("It just feels off." "Faster." "Like Amazon.") A second vague answer on the same dimension confirms the user does not have a sharper answer — pushing for a third extracts nothing and damages trust.

### Pivot routine

Switch from "next question" to "let's back up". Concretely:

1. Stop drilling. Acknowledge: _"Let's back up — I think I might be asking the wrong question."_
2. Read the running spec back so far in the user's language. ("Right now I'm hearing: a page where customers see their orders, with status badges, ordered by date.")
3. Ask the user to **describe or sketch what they're picturing**, not what they want. ("Could you describe what you'd see if this already existed and you opened it on Monday morning?")
4. Once the user re-engages with a concrete description, restart the dimension with a story prompt rather than the original question.

This pattern is borrowed from Bolt.new's "Discussion Mode escalation when build mode loops" — the principle is that looping on the same broken question is worse than admitting the question was wrong.

### What not to do

Do not say "your answers are insufficient" or any variant. Do not ask the same question with a synonym substituted (the user already knows the dimension; rephrasing does nothing). Do not threaten to give up.

---

## Decisions-Log Shape

Silent decisions made by the agent during Steps 1–4 must be recorded in the requirements doc's `## Technical Assumptions` section so the user can review them in Step 5 (mutual confirmation) and reject any that are wrong.

Each entry uses three fields:

- **Decision** — what was decided, in one short sentence.
- **Why** — the grounding evidence: code path, ticket, prior convention, or research-doc finding.
- **Reversibility** — `easy`, `medium`, or `hard`, plus a one-line note on what would need to change to flip it.

Example entry:

```
### Use the existing OrderService gRPC endpoint
- **Decision**: New "view orders" page reads from OrderService.GetOrdersForCustomer rather than reading the orders BigQuery table directly.
- **Why**: OrderService is already the read path for the mobile app (verified in code-search). Direct BigQuery reads would duplicate the access-control logic the service already enforces.
- **Reversibility**: easy — switching back to direct BigQuery reads is a small refactor; access-control logic would need re-implementation.
```

Reversibility scale:

- **easy**: changing the decision later is a small, isolated edit (one file, one config flag, one library swap).
- **medium**: changing it later means rewriting a feature or migrating data, but no cross-team coordination.
- **hard**: changing it later requires schema changes, public API changes, or coordination with another team.

The agent should err toward more entries rather than fewer — every silent decision the user did not weigh in on belongs in this log. Entries that were explicitly confirmed during the interview do **not** belong here; they belong in the body of the doc.
