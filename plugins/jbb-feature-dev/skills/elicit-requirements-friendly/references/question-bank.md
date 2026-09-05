# Question Bank

Source material for the friendly interview. The skill draws from three sections:

1. **Story Prompts (Top 10)** — verbatim, story-based questions used during Step 4. Each prompt has a "use when" annotation so the agent can pick the right one for the moment.
2. **NFR Probes** — non-functional concerns asked in user-language (no jargon), used inline in Step 4 whenever a story surfaces a hint about performance, scale, reliability, accessibility, or privacy.
3. **Jargon Translation Table** — paired columns for translating internal/agent vocabulary into user-friendly phrasing. The skill must show the user-friendly phrase first and may add the technical term in parentheses for record-keeping.

These prompts are tested across PM/UX literature (Mom Test, JTBD switch interview, Continuous Discovery) and stay safe for non-technical users. Use them verbatim where possible — paraphrasing tends to leak jargon back in.

---

## Story Prompts (Top 10)

1. "Tell me about the last time you [did X]. Where were you, who was involved, what happened first?"
   _Use when_: opening the interview or starting a new dimension. Anchors the user in a real moment instead of a hypothetical.

2. "What did you actually do next? And then what?"
   _Use when_: the user gives a one-word or one-sentence story. Drills into sequence without sounding like an exam.

3. "What's the hardest or most frustrating part of that?"
   _Use when_: surfacing motivation. The pain point usually appears in the answer.

4. "What have you already tried to solve this? How's that working?"
   _Use when_: probing for prior workarounds. Reveals constraints and disqualifies dead-end approaches.

5. "Walk me through your current workaround, even the embarrassing parts."
   _Use when_: the user is hedging or polishing. Permission-to-be-honest framing.

6. "What was going on in your work that made you think 'I need something different' for the first time?"
   _Use when_: drawing out the JTBD switch moment. Maps the trigger.

7. "What almost stopped you from switching? What were you worried about?"
   _Use when_: surfacing non-functional concerns (security, retraining, data loss) without naming them.

8. "If we met again in 3 months and this was a huge success, what would have stopped happening in your day?"
   _Use when_: collecting success criteria. Reframes "what does success look like" away from "make it good".

9. "What's the weirdest or worst version of this you've seen? What broke last time?"
   _Use when_: collecting edge cases and reliability constraints without saying "edge case" or "SLO".

10. "You mentioned [solution] — what problem would that solve for you?"
    _Use when_: the user pitches a solution before stating the problem. Redirects upstream.

---

## NFR Probes (Non-Functional Requirements, in user-language)

Each probe maps to one non-functional dimension. Ask only the probes that are relevant to what the user just said — never run the full battery up-front.

- **Performance**: "How long would feel too long?"
- **Scale**: "How often do you do this on a normal day vs. a bad day?"
- **Reliability**: "Who feels the pain if this is wrong or down?"
- **Accessibility**: "Who else might use this — phone, screen reader, noisy room?"
- **Privacy**: "Who absolutely shouldn't see this?"

These avoid the words "latency", "throughput", "SLO", "WCAG", and "GDPR". The agent records the user's answer in the document under its proper non-functional category — but the user never has to learn the category name.

---

## Jargon Translation Table

When the user asks "what does that mean?" — or before the agent introduces a term that has a friendlier equivalent — translate. The agent's vocabulary is on the left; the user-friendly phrasing is on the right.

| Agent jargon                     | User-friendly phrasing                                         |
| -------------------------------- | -------------------------------------------------------------- |
| acceptance criteria              | how we'll know it's done                                       |
| NFR (non-functional requirement) | speed, reliability, privacy, and similar "feel" of the product |
| SLO (service level objective)    | how often it has to work without trouble                       |
| edge case                        | the weird situations where things go wrong                     |
| deployment strategy              | how and when we ship it                                        |
| scope mode                       | how much you want us to bite off — minimum, full, or ambitious |
| premise                          | whether the problem is worth solving in the first place        |
| stakeholder                      | someone who cares about this getting done                      |
| invariant                        | a rule that should always be true                              |
| regression                       | something that used to work but now doesn't                    |

The skill should default to user-friendly phrasing in conversation and parenthesize the technical term once when the term is genuinely useful for downstream consumers of the document.
