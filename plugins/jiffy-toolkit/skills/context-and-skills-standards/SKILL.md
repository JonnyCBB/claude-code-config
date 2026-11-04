---
name: context-and-skills-standards
description: >
  Reduce a skill (SKILL.md and its package) or a context file (CLAUDE.md, AGENTS.md) to its
  essence by removing what does not earn its place. Use when reviewing or auditing one, when one
  is being created or has grown, or when deciding whether a proposed instruction, file, script
  or command should exist at all. Produces a deletion list with a net line count.
---

# Context and skills standards

After this review the skill is smaller and does the same job. Every line that survives is one an
agent would visibly get wrong without.

**The default verdict on any line, file, script or skill is DELETE.** Keeping is what needs the
argument. A review that proposes only corrections has not done this job.

## The keep test

**Would an agent that never read this do something specific and observably wrong?**

If you cannot name the mistake, delete it. "It's useful context", "it's good practice" and "it
might help" all fail. So does "it's true" — truth is not the bar, behaviour change is.

## The removal ladder

Work top down and stop at the first rung that holds. A cut at a higher rung makes every lower rung
moot, and reviewing sentences inside a file you should be deleting is how this review wastes itself.

1. **Delete the whole skill.** The model already does this correctly, or another skill does, or it
   is one instance dressed up as a class of task. Run the task with it off before keeping it.
2. **Delete the whole file.** Nothing links to it; or it records how the skill came to be rather
   than how to use it (design history, rejected approaches, archives, legacy notes); or it is the
   skill's own evidence and citations, which an agent does not need in order to obey a rule.
3. **Delete the executable block, keep the fact.** A block is a block wherever it lives - a
   script file, a fenced command, or a bare command written inline. Moving one into the other is
   not a cut. The two tests are in **Executable blocks** below.
4. **Delete the section.** Overviews, architecture tours, directory listings, and anything
   restating what the model already does by default.
5. **Delete the sentence.** Restated numbers, duplicated meaning, rationale for the rule, hedges,
   and prose defending a decision nobody contested. Keep any sentence saying **how often** a thing
   is done - that is not rationale, it is the input to the placement question below.

Report the rung you cut at. If you only ever reach rung 5, say why the higher rungs did not hold.

## Executable blocks

- **A script file** is discharged by three things and nothing else: there is no agent at execution
  time (a hook, a CI or pre-commit gate); or the input does not fit in a context window, so an
  agent cannot do it at all; or it is test data under `evals/`. "Cleaner", "testable" and "it
  guards something irreversible" are statements about the script, not evidence about prose.
- **A command inside the markdown** gets a different test, because the agent can write that
  command anyway: **does the block carry a trap the reader could not infer?** An agent can write
  the query unaided. What it cannot guess is which fields lie and how - a check that renders a
  failed lookup as an answer, a status read from the wrong end of a pipeline. No such trap: ship
  the facts and drop the command. A real one: the block may stay, and that is the only thing that
  earns a command its fence.
- **Dropping the command is not licence to drop its values.** "The agent can write this" and "the
  agent can infer this" are the same sentence and only the first is true.
- **A trap can live between blocks rather than inside one** - shell state does not persist between
  an agent's tool calls, so a value one block sets is gone by the next. Check the sequence, not
  only each block.
- **Read a block for its effects before running it.** Reviewing a skill is not authority to act
  through it. If the block deploys, pushes, deletes, sends or spends, run only the half that
  inspects and stop. If you cannot tell from reading alone whether a command is read-only - an
  unfamiliar wrapper, an alias, a name that does not say what it does - treat it as effectful and
  leave it unrun. Where the effect cannot be separated from the check, record the block as
  unverified and say why.
- **Every block you keep must be executed** within that limit, against a real input, with the
  run's output kept as part of the review. An unrecorded claim of having run it is not evidence,
  so delete it instead.
- **Cutting a block moves the risk before it removes it.** Review attention pools on executable
  text: a fence reads as code and gets audited, prose reads as explanation and gets skimmed. So a
  file that has just lost its blocks should be read with the opposite attention to the pass that
  found the last defects, and prose that reasons about state - what the base is, what changed, what
  is clean - counts as executable in substance even unfenced. That prose is where the next defect
  will be.

## Before you delete a file or a section, look inside it for these

This is the step that stops the review doing damage, so do it every time. Any of the four can be
buried in material that otherwise deserves to go — a trap inside a rejected-approaches list, a
constraint inside an evidence table, a whole reference file whose only live content is one line.
**Fold it forward into the working instructions first, then delete.** This is the same test
**Executable blocks** applies to a command.

- A proprietary fact the model has no training coverage for: an internal API, a schema key, a flag,
  a command with its exact arguments, a threshold.
- Something learned at cost — a trap that would mislead anyone who has not done the digging.
  It survives even when it reads as an aside.
- A hard guardrail on an irreversible action.
- The one worked example that makes a procedure concrete.

When a cut is a judgement call, keep the line and say it was close. A wrong deletion is invisible
until an agent fails; a wrong retention costs tokens.

## Keeping something is not the same as keeping it here

The four classes above say *keep*. They do not say *keep in this file*. A procedure can survive
every rung and still be in the wrong place: one that fires quarterly costs its full length on every
unrelated task in between.

So after the deletion list, look at what you left behind. If a context file is now mostly
procedures that run a few times a year - releases, incident runbooks, onboarding, audits - name the
file each one belongs in instead: a skill, or `.claude/rules/*.md` where a glob scopes it. Leave a
one-line pointer behind. **This is not fold-forward**, which moves a fact within the same file.

## Two things worth checking that are easy to miss

- **A reference file nothing links to is unreachable, and will go stale unread.** A file reached
  only from another reference file is one level too deep and gets partially read. Do not assert the
  link counts — list them.
- **Compare reference mass to `SKILL.md` mass.** If references are larger, content was moved to
  satisfy a per-file line target rather than removed. `SKILL.md` at or under 500 non-blank lines,
  and reference mass no larger than it. Aim at moderate, not minimal: across skill benchmarks
  standard length beats both compact and comprehensive, so the target is "not comprehensive".

## Output

A deletion list, largest cut first. Per entry: the path, the rung, the line count, and **the
mistake an agent would make if you are wrong**. Then one line:

`net: -N lines of M (X%)`
`wrong file: N lines -> <where>` - omit if everything that survives belongs where it is

Count with `wc -l`, not by eye — running a shell command is not shipping a script. If nothing
should go, say `Lean already` and stop. Do not pad the list to look thorough; a deletion list with
filler is the defect it is reviewing.
