# PR Prose Rules

Read this reference when generating a PR description. It owns STE composition and evidence protection.
When installed, the optional `jiffy-toolkit:sound-like-me` skill owns Jonny's PR writing voice and prose cleanup.
Without it or its `github-pr-body` persona, use the clear-writing rules below and report the missing voice support outside the PR body.

## Objective Before Code

State the objective and problem from user input, requirements, tickets, or commit context. Never invent motivation.
Keep behavior summaries that connect the objective to verification, even when the diff also shows that behavior.
Omit mechanical file inventories, import lists, version-change lists, and duplicate implementation detail.
Explain a dependency change or design tradeoff only when the available evidence supplies its reason.

Follow the repository template or the structure in `pr-description-template.md`.
Keep the visible body proportional to the change. Move long evidence into collapsibles; never delete required scenarios to shorten it.
Always state important verification limits, even for a small change.

## STE With Jonny's PR Voice

Apply ASD-STE100 Simplified Technical English (STE) to every PR description.
When `jiffy-toolkit:sound-like-me` and its persona are available, also apply `sound-like-me --register=github-pr-body`.
STE uses short sentences and clear, direct words.

1. Draft the factual objective and evidence using `pr-description-template.md`.
2. Use instructions of at most 20 words and descriptions of at most 25 words per sentence.
   Use active voice, one idea per sentence, and one word for one meaning. Define jargon on first use.
3. If available, load `jiffy-toolkit:sound-like-me` and its `github-pr-body` persona. Apply it in embedded mode.
   Otherwise, continue with this reference's STE and prose-cleanup rules; do not invent persona advice or block submission.
   Retain Jonny's natural voice when available, but prioritize clear prose, required structure, and complete evidence over conflicting persona advice.
   Keep repository headings and required verification sections even when the persona suggests different headings or a shorter body.
4. Preserve exact identifiers, commands, URLs, quoted output, and verbatim transcripts.
   Do not rewrite or delete evidence to satisfy sentence limits, vocabulary scans, or personal voice.
5. Keep the persona diagnostic line out of the PR body. It is a caller diagnostic, not reviewer content.

## Prose Cleanup

Describe behavior rather than narrating edits to named files.
Use concrete verbs. Cut filler, inflated significance, AI vocabulary, and inline-header bullet lists.
Use as many bullets as the change needs. Do not force groups of three.
Do not add empty Future Work, Notes, or Additional Context sections.
Keep genuine limits and unverified claims in Testing & Verification instead of hiding them to shorten the body.

## Post-Generation Audit

1. Can a reviewer understand the objective and evidence before reading code?
2. Does each required scenario include exact inputs, expected results, observed results, reproduction steps, and limits?
3. Does the evidence match this repository, branch, objective, and submitted change? Mark missing or stale evidence unverified.
4. Does authored prose follow STE and, when available, Jonny's PR voice, without invented facts or motivation?
5. Do required headings and every scenario survive the rewrite? Keep transcripts and identifiers exact.
6. Remove routine CI totals and generic success claims. Keep behavioral unit-test evidence when it explains the objective.
7. Replace author-only pointers with inlined facts or reviewer-accessible links. Preserve paths inside verbatim evidence and add portable setup separately.
8. Scan authored prose for AI vocabulary, filler, file-edit narration, and unnecessary repetition. Leave exact evidence unchanged.
9. If motivation remains unknown, ask in interactive mode. In non-interactive mode, state factual behavior and mark the missing context.

Follow the evidence format and visible-body budget in `pr-description-template.md`; do not maintain another copy here.
