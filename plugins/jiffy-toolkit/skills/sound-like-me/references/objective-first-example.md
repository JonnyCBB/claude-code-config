# Worked example: the objective goes first, in plain words

Evidence for the core section of the same name in `SKILL.md`. The four checks there are the
instruction and stand on their own; read this when you want the full case.

Same ask, same day, same author, two versions. One was sent back, the other was answered.
Thread: https://your-workspace.slack.com/

**Both messages below are verbatim, including the em dashes, the Slack markup and the typo in the
second one.** The first message breaks §14 repeatedly, and that is part of the evidence rather than
something to clean up. Under "What NOT to flag", secondhand text inside quotations is never
rewritten: leave these two blocks exactly as they are.

## Version A, as posted (2026-08-28 15:38 BST)

> Hi @honk-goalie! Could we add two hosts to the agent-runtime sandbox allowlist? (Sorry about the
> scratched message above — I tagged the wrong goalie group.)
>
> *What we're trying to do:* run `seal-agent-service`'s live verification on a Honk pod instead of a
> laptop. We measured it, and everything else already works — the full 8,360-test suite runs there in
> about 4 minutes, Docker and Postgres are fine, and the entire hermetic verification path passes end
> to end. The only thing that fails is the planner reaching Vertex AI.
>
> *The ask* — two entries in `sandbox.network.allowedDomains` in `runner/fragments/20-sandbox.json`:
> • `us-central1-aiplatform.googleapis.com` (and/or the `global-` variant — happy to take your steer)
> • `oauth2.googleapis.com`
> Four `googleapis.com` hosts are already allowlisted there (storage, logging,
> maven-central.storage-download, pubsub), so this is the same shape as what's in the file today
> rather than a new category.
>
> *Three questions rather than assumptions:*
> 1. Is a model API host a bigger ask than the ones granted before? We found several granted host
> additions and no refusals, but no prior _model API_ request — so this may have a different answer
> and we'd rather hear it than assume.
> 2. We understand it takes effect on the next image rebuild rather than on merge — roughly what's
> the turnaround in practice?
> 3. The GCE metadata server also isn't reachable from the sandbox. Even with those hosts open, will
> token minting work, or is that a second thing to sort out? Genuinely unsure, and it changes whether
> this is one request or two.
> Happy to open the PR ourselves if that's easier — just say which host variants you'd want.
>
> One last thing in the interest of being straight with you: we did find that `tox:*` is on
> `excludedCommands`, which would let us route around this entirely. We're deliberately not doing
> that — your own docs describe it as a hole in the sandbox, and asking seemed better than quietly
> bypassing a control you put there on purpose. Thanks :pray:
> *Sent using* @slack-mcp

## The reply, in full (15:50 BST, 12 minutes later)

> can you explain in human language what you need and what you're trying to achieve?

## Version B, written by hand, which was answered (16:12 BST)

> Of course. When I dispatch a session to honk to work on my repo, seal-agent-service, I want it to
> do live verification to check that the changes that it's made actually works. To do this it needs
> to spin up a server and have a conversation with the seal agent. We run our LLM calls through
> Vertex AI so which is how the seal agent responds (it uses a gemini-flash model). On the honk pod
> it can't reach Vertex AI so we don't get actual agent responses.
>
> I want to unblock this so that we can get agent responses when running on honk pods.
>
> I have no idea what the permission issues are and what needs to be done, hence the Claude generated
> message because I assumed it might make more sense. I was clearly wrong about that :sweat_smile:

## What separates them

**Identifier count.** Version A names 25 things: a subteam, a repo, a pod platform, a test count, a
timing, Docker, Postgres, a "hermetic verification path", a planner, Vertex AI, a JSON field, a file
path, two requested hostnames and a variant, four already-allowlisted service names, a "model API
host", an image rebuild, a metadata server, token minting, a command pattern and another config key.
Version B names five, and a reader needs four of them. `gemini-flash` is the one that could go.

**The objective was present in Version A, and second.** It sits under a bolded "What we're trying to
do", which is why position alone is not the fix. That sentence is built from identifiers and names a
mechanism (a pod instead of a laptop) rather than an outcome. Version B names the outcome: "get
agent responses when running on honk pods".

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
