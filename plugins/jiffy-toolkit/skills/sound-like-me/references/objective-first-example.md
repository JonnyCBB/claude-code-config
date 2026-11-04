# Worked example: the objective goes first, in plain words

Evidence for the core section of the same name in `SKILL.md`. The four checks there are the
instruction and stand on their own; read this when you want the full case.

Same ask, same day, same author, two versions. One was sent back, the other was answered.

**The messages on this page are stand-ins.** The originals were real work messages and are not
reproduced. Every system, host and step name below is invented, swapped one for one, so each
stand-in keeps its original's shape, its count of named things, its em dashes, its Slack markup and
its typos. The first message breaks §14 repeatedly, and that is part of the evidence rather than
something to clean up. Under "What NOT to flag", secondhand text inside quotations is never
rewritten: leave these blocks exactly as they are.

## Version A, as posted (2026-08-28 15:38 BST)

> Hi @devbox-oncall! Could we add two hosts to the devbox sandbox allowlist? (Sorry about the
> scratched message above — I tagged the wrong goalie group.)
>
> *What we're trying to do:* run `orbit-agent-service`'s live verification on a devbox pod instead of a
> laptop. We measured it, and everything else already works — the full 8,360-test suite runs there in
> about 4 minutes, Docker and Postgres are fine, and the entire hermetic verification path passes end
> to end. The only thing that fails is the planner reaching Nimbus AI.
>
> *The ask* — two entries in `sandbox.network.allowedDomains` in `runner/fragments/20-sandbox.json`:
> • `us-central1-models.nimbuscloud.example` (and/or the `global-` variant — happy to take your steer)
> • `oauth2.nimbuscloud.example`
> Four `nimbuscloud.example` hosts are already allowlisted there (storage, logging,
> maven-mirror.storage-download, pubsub), so this is the same shape as what's in the file today
> rather than a new category.
>
> *Three questions rather than assumptions:*
> 1. Is a model API host a bigger ask than the ones granted before? We found several granted host
> additions and no refusals, but no prior _model API_ request — so this may have a different answer
> and we'd rather hear it than assume.
> 2. We understand it takes effect on the next image rebuild rather than on merge — roughly what's
> the turnaround in practice?
> 3. The cloud metadata server also isn't reachable from the sandbox. Even with those hosts open, will
> token minting work, or is that a second thing to sort out? Genuinely unsure, and it changes whether
> this is one request or two.
> Happy to open the PR ourselves if that's easier — just say which host variants you'd want.
>
> One last thing in the interest of being straight with you: we did find that `tox:*` is on
> `excludedCommands`, which would let us route around this entirely. We're deliberately not doing
> that — your own docs describe it as a hole in the sandbox, and asking seemed better than quietly
> bypassing a control you put there on purpose. Thanks :pray:

## The reply, in full (15:50 BST, 12 minutes later)

> can you explain in human language what you need and what you're trying to achieve?

## Version B, written by hand, which was answered (16:12 BST)

> Of course. When I dispatch a session to devbox to work on my repo, orbit-agent-service, I want it to
> do live verification to check that the changes that it's made actually works. To do this it needs
> to spin up a server and have a conversation with the orbit agent. We run our LLM calls through
> Nimbus AI so which is how the orbit agent responds (it uses a nimbus-flash model). On the devbox pod
> it can't reach Nimbus AI so we don't get actual agent responses.
>
> I want to unblock this so that we can get agent responses when running on devbox pods.
>
> I have no idea what the permission issues are and what needs to be done, hence the Claude generated
> message because I assumed it might make more sense. I was clearly wrong about that :sweat_smile:

## What separates them

**Identifier count.** Version A names 25 things: a subteam, a repo, a pod platform, a test count, a
timing, Docker, Postgres, a "hermetic verification path", a planner, Nimbus AI, a JSON field, a file
path, two requested hostnames and a variant, four already-allowlisted service names, a "model API
host", an image rebuild, a metadata server, token minting, a command pattern and another config key.
Version B names five, and a reader needs four of them. `nimbus-flash` is the one that could go.

**The objective was present in Version A, and second.** It sits under a bolded "What we're trying to
do", which is why position alone is not the fix. That sentence is built from identifiers and names a
mechanism (a pod instead of a laptop) rather than an outcome. Version B names the outcome: "get
agent responses when running on devbox pods".

**Six things asked for, not three.** Three numbered questions, an offer to open the PR, a request to
be told which host variants, and a "happy to take your steer" inside a bullet.

**Version B admits not knowing.** "I have no idea what the permission issues are." Version A
projected a complete diagnosis and handed over a finished fix. Handing over the problem lets the
person who owns the system choose the solution.

**Version A was also off-register.** `slack-longform` has effectively no em dashes, no backticks and
sparing bold, and carries a `TL;DR` more often than not; the measured rates are in
`persona-jbb-slack-longform.md` section 2, which is where they live. Version A carries **8 em dashes
against Version B's 0**, plus heavy backticks, four bold spans and no `TL;DR`, so it did not go
through this skill at the right register. Running it would have cleaned those tells and left the defect above untouched, which is
why the core section exists as a separate check rather than a 34th pattern.

---

## The positive exemplar: a message that worked as written

Everything above is a rescue. Version B is what the author wrote *after* being sent back, and it is
shaped like a clarification, so it teaches what to avoid rather than what to produce. This section is
the other half, added 2026-09-07: a message by the same author, to a different reader, that was
called **"pretty good"** and needed no rescue.

What the author said worked, in his words: the asks split into bullet points, an explanation pitched
high enough to be understandable, and the names of things kept in because the reader already knew the
domain.

### Version C, as posted and answered (2026-09-05 11:44 BST)

**A stand-in with invented names, keeping the original's Slack markup, the inconsistent numbering
on item 2 and the typo in the closing line.** Secondhand text is never rewritten; leave this block
exactly as it is.

> Hey hey :wave: got a few things I could use your help with on the Layout Pilot side, none of them urgent today.
>
> What I'm trying to get to is Orbit being able to do everything Layout Pilot can do. That was the whole point of the migration, and we're most of the way there now - Orbit can see all 14 of your workflows rather than just the 5 we had checked in, and I've unblocked two more of them from our side today. There are four things left that I can't fix myself.
>
> I've done our homework first, so none of these are me asking you to do something we could have done ourselves.
>
> 1. *Can we get something on StepSummary that says whether a step writes or only reads?*
> Right now it tells us the kind but not whether it mutates anything, so Orbit refuses every external-action step just to be safe. I measured it across all 14 workflows and 8 of the 9 external-action steps are reads (fetch-uri, resolve-asset-uris, validate-catalog). Exactly one genuinely writes, which is save-blueprint. So one blunt rule is blocking 6 of 14 workflows over that single write, and it also throws away the dry-run step you built, which is the one native rehearsal we'd actually want to use. A single boolean would close it permanently and mean we never have to guess.
>
> *2. Could archiveConfig be reachable through RunWorkflow or RunStep?*
>
> Orbit can't remove a shelf at all today. Removing one means archiving three configs, and archiveConfig already exists on PilotDataAccess - you call it twice internally - it's just not on either of the two RPCs Orbit has. As far as I can see that needs no new proto method.
>
> *3. This one's a question rather than an ask: does the runner auto-fill the shelf URI between composed steps?*
>
> In create-and-pin and create-shelf-and-add-to-hub an earlier step produces a URI that a later step needs, and Orbit can't know it before the run. I can't test whether you fill it in, because execute=false won't advance past a config-write step, so the only way to find out from my side is to do a real production write. I'm not going to do that just to answer a question. One sentence from you saves me a lot of guessing.
>
> *4. Could composed children carry their own input schema?*
>
> featured-item-candidate declares one top-level input and maps only that into its catalog child, but the child also requires a variantName and nothing surfaces that. Without a schema on the composed-child message I can't tell which of a child's inputs are unmapped without describing every child separately, which gets expensive on the planner path.
>
> Regardless of how you want to play these, I'm very happy to raise the PRs myself if you'd rather review than write - "_Claude said this, not me but I'm happy to ge Claude on it regardless if you prefer_ :joy: "
>
> No rush on any of it, I've got plenty to be getting on with. This is about unblocking the next stretch rather than today.

### What is NOT the variable, measured

Counted 2026-09-07 on the verbatim text of both messages, `wc -w` and `grep -o`. **Paragraphs are
runs of non-blank lines, not blank lines.** The first version of this table counted blank lines and
so was off by one on both rows, which put Version A at ~82 words per paragraph rather than ~65:

```bash
awk 'BEGIN{n=0;p=0} /^[[:space:]]*$/{p=0;next} {if(!p){n++;p=1}} END{print n}' <file>
```


| | Version A (sent back) | Version C (worked) |
| --- | --- | --- |
| Words | 327 | **513** |
| Distinct named things | 25 | **~29** |
| Paragraphs | 5 | 12 |
| Words per paragraph | ~65 | ~43 |
| Backticks (code font) | 18 | **0** |
| Em dashes | 8 | 0 |
| Separate things asked for | 6 | 4, each with a heading |

Counting rule for the middle row, so the number is checkable rather than asserted: a distinct named
thing is a proper name, a method, a field, a step, a file or a value that a reader could look up.
Version A's 25 are enumerated under "What separates them" above. Version C reaches **29 on the same
strict basis and 34 if generic nouns like "shelf" and "workflow" are counted**, so the direction holds
either way and only the exact figure moves.

**The message that worked is 57% longer and names more things.** Both directions matter, because the
obvious reading of Version A versus Version B - 25 identifiers against 5, and shorter - is that the
fix is to name less and write less. Version C refutes that directly. Neither brevity nor identifier
count is the variable, and a rule tuned on either will cut the wrong things.

**This was checked rather than assumed, twice.** Both runs are recorded below under "The two runs
that produced this section", because a rule justified by a measurement nobody can find is a
preference with a number attached.

### What IS the variable

1. **The first sentence names an outcome, in the reader's domain, not the writer's.** Version A's
   opening names a mechanism, as established above. Version C opens with "Orbit being able to do
   everything Layout Pilot can do", and Layout Pilot is the reader's own system. An outcome stated in
   your vocabulary is still a mechanism to them.

2. **Names are free when the reader owns them, and expensive when they do not.** Version C uses
   `StepSummary`, `archiveConfig`, `PilotDataAccess`, `save-blueprint`, `execute=false` and two dozen
   more without glossing any of them, because the reader wrote them. Version A's reader owned the
   sandbox and had never seen `orbit-agent-service`. **This is a property of the reader, not of the
   word**, and it is the correction the length figures force: check 2 asks whether *this* reader would
   have to look it up, never whether the word looks technical.

3. **Every identifier arrives after the claim it supports, never before.** Version C: "Orbit refuses
   every external-action step just to be safe. I measured it across all 14 workflows and 8 of the 9
   external-action steps are reads (fetch-uri, resolve-asset-uris, validate-catalog)." The reader
   knows why they are being told a list before they are given one. Version A does the reverse - the
   8,360-test suite, the 4 minutes, Docker, Postgres and the hermetic verification path all arrive
   before the reader has any reason to care.

4. **Each ask is its own heading, phrased as the question.** Four bold questions the reader can answer
   one at a time, in any order, and skip. Version A buried three questions in a numbered list after
   the ask, so there was no way to answer part of it.

5. **Each item is labelled with what kind of item it is.** "This one's a question rather than an ask"
   tells the reader they can settle it in one sentence. Nothing in Version A said which of its six
   requests were blocking.

6. **Say what you already did, and what you cannot do yourself.** "I've done our homework first" and
   "four things left that I can't fix myself" and "I can't test whether you fill it in, because
   `execute=false` won't advance past a config-write step." This is not throat-clearing: it tells the
   reader which parts are genuinely theirs.

7. **Urgency is stated, at both ends.** "None of them urgent today" and "No rush on any of it." Saying
   it twice is not redundancy in a message with four asks between the two statements.

8. **No code font, on this surface.** Version C sets zero identifiers in backticks and Version A
   sets eighteen. Code font on every name is what makes a message look like a configuration diff
   rather than a question from a colleague, and it is the cheapest of these to check. The rule is
   register-scoped rather than universal and the per-register rates live in check 7 of `SKILL.md`,
   not here; both messages on this page are Slack, which is why Version A's eighteen count against
   it.

### The confound, stated

Two messages, same author, different readers. Version A went to a platform team who did not own the
system it described; Version C went to a collaborator who owned every name in it. That difference is
real and it is exactly why point 2 above is phrased as a property of the reader.

It does not reach the length finding. No one argues that a stranger needs a *shorter* message than a
close collaborator, so the confound would predict the opposite of what was measured. The code-font
and claim-before-identifier findings are likewise independent of who the reader was.

---

## What the outside evidence says, and where it does not reach

Researched 2026-09-07 because the rule above was derived from two messages by one author, which is
not much. The literature broadly agrees with it and disagrees with the folklore around it. Sources
below were opened directly unless marked otherwise.

### Simplified Technical English does not conflict with keeping the precise word

This was the open question. It turns out there is nothing to reconcile.

- **ASD-STE100 exempts domain terminology from its controlled dictionary rather than deleting it.**
  Rule 1.1 permits three sources of words, not one: *"Approved in the dictionary - Technical nouns -
  Technical verbs."* Rule 1.8: *"Use technical nouns that are approved in your company, industry, or
  subject field."* Its own FAQ: a non-approved word used as part of a technical noun *"automatically
  becomes part of that technical noun ... and as such it is acceptable."*
  [Issue 9 specification](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf), and the
  [FAQ](https://www.asd-ste100.org/STE_faq.html)
- **Its answer to a long technical term is to gloss it in place.** Rule 2.2 tells you to write the
  term in full and then give a short form, and its worked example does exactly that with a ramp
  service door safety connector pin. A controlled-vocabulary standard reaching independently for
  keep-and-gloss is the strongest available check on check 2 in `SKILL.md`.
- **It disclaims this surface outright.** FAQ, verbatim: *"It is not intended for general-purpose
  writing, such as international correspondence."* The Issue 9 subtitle is "Standard for technical
  documentation". So it does not govern a Slack message either way.
- **Its own evidence is thinner than its reputation.** The Boeing comprehension study found the
  effect on one of two procedures - *"There were no significant effects for Procedure B"* - and the
  paired translation study was significant for Spanish and not for Chinese. The authors note there
  is *"no compliance standard for SE"*, so "written in STE" is not a well-defined treatment.
  [CLAW '96](https://mt-archive.net/90/CLAW-1996-Holmback.pdf)

**Conclusion: do not adopt STE, and do not cite it as authority.** It agrees with us where it
applies and says it does not apply here.

### Do not score readability. This is the best-evidenced item on the page.

- Grade-level formulas are arithmetic over average word and sentence length. The US federal AHRQ
  guidance says they *"can't tell you whether the words you are using are familiar to your readers"*
  and *"do not measure comprehension or reading ease"*.
  [AHRQ Tip 6](https://www.ahrq.gov/talkingquality/resources/writing/tip6.html)
- Reversing the word order of a sentence makes it unintelligible and **does not change its score**.
  [Schriver 2014, p. 61](https://www.karenschriverassociates.com/wp-content/uploads/2020/03/2-Schriver-Developing-Plain-Language-Principles-n-Guidelines.pdf)
- **The failure runs in exactly the direction that would hurt us.** Against lay readers' own
  difficulty ratings, Flesch-Kincaid correlated 0.30 and SMOG 0.10. Clinical notes scored about 33%
  *easier* than Wikipedia while readers rated them about 21% *harder*, and the authors attribute it
  to jargon and abbreviations: a short abbreviation lowers the score while raising real difficulty,
  so a long precise term the reader already knows is penalised for costing them nothing.
  [Zheng and Yu 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5355629/)
- 638 adults, eye-tracked over 3.7 million word tokens: readability formulas *"all have weak
  predictive power for reading facilitation"*, and are beaten by word frequency and surprisal.
  [Gruteke Klein et al., Computational Linguistics 2026](https://arxiv.org/pdf/2502.11150)

### The reader-conditional rule is the expertise reversal effect

Point 2 under "What IS the variable" was derived from two messages. Instructional-design research
reaches the same place from a different direction, and this is the closest thing to independent
corroboration on the page.

- **Integrating explanatory notes into a text helped low-competence readers and *harmed* knowledgeable
  ones** across five experiments - not because the glosses were wrong, but because they were *"difficult
  to ignore when integrated"*. [Yeung, Jin and Sweller 1998](https://pubmed.ncbi.nlm.nih.gov/9514686/),
  reported in
  [Kalyuga et al. 2003](https://mrbartonmaths.com/resourcesnew/8.%20Research/Explicit%20Instruction/The%20Expertise%20Reversal%20Effect.pdf)
- Naming the key elements before the detail is measured at **median d = 0.75 over 16 tests** - and
  splits hard by prior knowledge: low-knowledge d = 1.22 and 1.15, high-knowledge d = 0.11 and
  **-0.68**. Signalling structure is median d = 0.41 over 28 tests, with the same split (low-skill
  d = 0.42 and 0.65; high-skill d = -0.12 and -0.31).
- **So gloss for the reader who does not own the domain, and stop glossing for the reader who does.**
  That is not politeness, it is where the measured effect changes sign.

**State this honestly: nobody has run the exact comparison.** "Precise term plus a short gloss beats
a vaguer substitute" is a well-supported inference from the above, not a measured finding. The study
usually cited *against* defining jargon used hover tooltips rather than in-line glosses and says in
its own text *"we did not directly measure comprehension"*.
[Bullock et al. 2019](https://comm.osu.edu/sites/comm.osu.edu/files/PUS%202019-%20Bullock%20et%20al..pdf)

### Longer-and-structured beating shorter-and-dense is not just our two messages

- Structured abstracts run **21% to 35% longer** than traditional ones and are nonetheless judged
  easier to read, more informative, and are preferred by readers and authors.
  [Hartley 2004](https://pmc.ncbi.nlm.nih.gov/articles/PMC442180/)
- The counterweight, and it is a large effect: cutting genuinely **extraneous** material is median
  d = 0.86 over 23 comparisons. Note what was cut in those studies - background music, irrelevant
  anecdotes, decorative illustrations. Not explanations, and not reader-owned names.
- Nearest thing to a direct test for an agent reporting to a person (n = 559, **unrefereed
  preprint**): a full reasoning trace scored *worse* than both a summary and an answer alone, and
  produced the largest overconfidence. Summarise; do not dump.
  [arXiv 2605.25856](https://arxiv.org/html/2605.25856v1)

### Where the folklore outruns the evidence, so do not lean on these

- **"Bottom line up front is evidence-based."** The US Army writing standard requires it and cites no
  study; the Nielsen Norman Group's inverted-pyramid article claims improved comprehension and cites
  no controlled study. The support for front-loading comes from signalling and pre-training above,
  not from BLUF.
- **"The F-pattern proves you should front-load."** The Nielsen Norman Group describe the F-pattern as
  a failure mode - *"bad for users and businesses"*, and *"the default pattern when there are no
  strong cues"*. It is evidence that people scan badly, not that front-loading repairs comprehension.
- **"Users read only 20-28% of a page."** Real, but derived from dwell time on 2008 browsing data. It
  measures reading capacity, not comprehension, and supports no particular structure.
- **"Readability formulas are useless."** An overcorrection. The word-level research underneath them
  is sound and Schriver endorses it; it is the arithmetic combination that fails to measure
  comprehension.


## The two runs that produced this section

Recorded here rather than left in a pull request body, because a measurement that lives only in
scrollback cannot be re-checked or re-run.

### Run 1: does the old rule pass the message that succeeded?

Four editor agents, fresh, each given only the rule as it stood before this section existed plus
Version C, with **no indication that Version C had been praised**. The question asked was neutral:
what would you change.

**All four returned "revise before sending"** on a message its author was told was "pretty good".
Their proposed cuts, counted:

| What they proposed cutting | Editors proposing it |
| --- | --- |
| "I've done our homework first" | 4 of 4 |
| One of the two urgency statements | 4 of 4 |
| The offer to raise the pull requests | 3 of 4 |
| The reader-owned step names in item 1 | 2 of 4 |
| The opening, as a check 1 violation | 3 of 4 |

Five of the features the author named as what made the message work, proposed for deletion by editors
following the rule correctly. The rule was not being misread; it was underdetermined.

### Run 2: does the revised rule stop the cuts, on a message it has never seen?

Three editors per arm, six in total, all given a **held-out** message: same shape as Version C - long,
identifier-dense, reader owns the domain, several labelled asks, urgency at both ends - but a
different system, and **quoted in neither arm's rule text**. One arm read the old checks, the other
the revised ones. The candidate was byte-identical across arms.

| Feature at risk | Old rule proposed cutting | Revised rule proposed cutting |
| --- | --- | --- |
| Reader-owned identifier list | 2 of 3 | **0 of 3**, all three said keep |
| The "I've dug into each of these first" line | 2 of 3 | **0 of 3** |
| The offer to write the pull requests | 3 of 3 | **0 of 3** |
| Urgency stated at both ends | 2 of 3 | **0 of 3** |
| **Total cuts to protected features** | **9** | **0** |
| Flagged the objective-first defect | 3 of 3 | 3 of 3 |

**The last row is the control and it is the reason to trust the rest.** The revision did not soften
check 1: both arms caught the opening defect at the same rate. What changed is what else they
proposed. Every arm still returned "revise before sending", so the verdict is not the measurement -
the content of the revision is. The old rule strips content; the revised one reorders the opening and
fixes list markup.

### What these runs do not show

- **n is small.** Three per arm in run 2, four in run 1. Read the 9-to-0 as a direction, not an
  effect size, and note that six independent scorings of byte-identical input have returned 0 to 3
  blocking findings elsewhere in this repo, so a single arm is one draw.
- **Run 2's held-out message is synthetic**, written to carry the disputed features. It is a fair test
  of whether an editor cuts them and not evidence that any real reader preferred anything.
- **The revised rule was derived from Version C**, so run 2 checks that the principles transmit to a
  new case, not that they were right in the first place. What makes them right is the author saying so.
