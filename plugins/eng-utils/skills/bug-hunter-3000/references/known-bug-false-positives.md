# Known Bug-Hunt False Positives

Hand-maintained, and deliberately so -- see the promotion procedure below. When
the intent-verifier or a human reviewer confirms a new false-positive pattern
during real use, add a row directly below, in the same 4-column format.

This table is read by `agents/bug-hunt-intent-verifier.md` during its evidence
search. A candidate matching a row is strong evidence toward
`INTENDED_SUPPORTED`, but never dispositive on its own.

## Promotion procedure

**Owner-triggered, curated by Jonny.** One curator, on purpose: it keeps table
quality high and asks the least of the reviewer, who only has to be right in a
thread rather than open a PR against a file they have never seen.

**The trigger.** A reviewer establishes that a behaviour this skill flagged was
intended. That is the whole bar -- it does not need a PR, a ticket, or a formal
sign-off. A reviewer saying so in a Slack thread, a PR comment, or a review call
is enough to start.

**What a row needs**, all five:

1. **Pattern** -- the general shape, written so it matches a _future_ candidate
   rather than only this one. A row naming one class name is nearly worthless.
2. **What the flag looked like** -- how this skill described it. This is what a
   future intent-verifier pattern-matches against.
3. **Why it is intended** -- the tier-1 or tier-2 evidence, not the reviewer's
   authority. "The spec defines this parameter" promotes; "a reviewer said so"
   does not, on its own.
4. **The date.**
5. **A link to where the reviewer said so** -- thread, PR comment, or ticket. A
   claim with no link is unverifiable a year later, which is exactly when someone
   will want to check it.

**Reason vocabulary.** Gosling's five rejection categories are available for the
"why" column where one fits: `UNVERIFIED`, `STRUCTURAL`, `PRE_EXISTING`,
`EXTERNAL_KNOWLEDGE`, `LOW_VALUE`. They are a shared shorthand, not a required
taxonomy -- prose is fine where none of the five fits.

**What does not go in this table.** Reviewer disagreement that was never settled.
A `DISPUTED` state was considered and dropped: if a reviewer pushes back and the
evidence does not actually establish intent, the finding stays as it is and the
disagreement lives in the thread. Promoting an unsettled dispute here would teach
the intent-verifier to suppress a class of finding on the strength of an opinion.

**Nor does a real finding that was described wrongly**, and the two are easy to
confuse when a reviewer says "that's not right". Ask which half they are rejecting.
If the behaviour is intended, it belongs here. If the behaviour is a defect and the
_headline_ misdescribed it, the fix is the headline -- adding a row would train the
intent-verifier to suppress a finding that deserved to survive. Measured: a reviewer
corrected a finding titled "Child-safety downranking is applied to adults, not to
children"; the downranking was real and did reach adults, and children were never
unprotected, so what was wrong was the sentence, not the finding.
`run-record-schema.md` holds the rule that prevents it.

**Why rows are worth adding at all.** FP-table rows are the only proxy this
skill has for trust-building actually happening. A reviewer who sees their
objection land in a file that changes future runs is being shown the skill
learns; one whose objection vanishes into a thread is not.

| Pattern                                                      | Bug-hunt's flag looks like                                                                                                | Why it's a false positive                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Added      |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| Caller-supplied identity substitution with no equality check | `targetUserId` silently overrides the authenticated caller's own ID; flagged as an authorization/identity-spoofing bypass | Intended behavior supporting Daily Mix sharing (viewing a mix someone else shared with you). Live reproduction correctly proves the substitution mechanism exists; the class javadoc and an adjacent config comment ("useful in situations where the requesting user is different from the user for which sequencing is done") independently confirm it is deliberate design, and a pre-existing passing test already modeled the mismatch as expected behavior. See `example-org/services#142045`. | 2026-07-17 |

<!-- Add new rows below this line, same 4-column format -->
