# Skill authoring traps

Facts that changed behaviour, kept out of `context-and-skills-standards` because none is a removal criterion. Read when writing or amending a skill, not when reviewing one for size.

## An embedded shell block is code, and reading it is not reviewing it

Execute every block against a real fixture in every input state: empty result, populated result, no input. An expert review of one change found four defects and still missed two that surfaced on execution (an unassigned variable in a second block; a degenerate input that reported as normal).

- **Each block must be self-contained.** Shell state does not persist between an agent's tool calls. If a later step needs a value, have the earlier step write it somewhere durable and read it back. (`bug-hunter-3000`'s `test_finder_dispatch_supplies_run_and_skill_dirs` exists because a dispatch passed neither dir, so finders invented paths.)
- **"Nothing found" must be distinguishable from "nothing to look at".** Collapsing them is how a check reports success without checking.

## Skills are markdown; the evidence

Set by Jonny 2026-09-07: not a prohibition but a burden of proof on the script (attempted and shown to fall short; "cleaner", "testable", "more reliable" do not count). A PR-watching skill was 11,346 lines: 447 `SKILL.md`, 683 references, 1,804 Python, 3,914 Python tests. Cut to markdown it is ~700 lines (`SKILL.md` 211) with every defect it had found kept as sentences. A mutation review showed those 3,914 test lines still let a CRITICAL fail-open through (green CI plus `CHANGES_REQUESTED` reported done); the same rule as prose is one sentence with no conjunct to drop. The largest source of defects was its own detection script (four false positives on its own diff, a dead guard twice, a catastrophic-backtracking regex), and much of it existed to guard hazards the scripts created. Put the burden-of-proof rule in every dispatch spec that creates or amends a skill, BEFORE the executable-prose rule, or an author optimises for the convenience of verification. Run the eval when unsure whether prose can carry something.

## A markdown file that executes is code

Per the TDD scope rule in `CLAUDE.md`. A scheduled monitoring skill had three CRITICAL/HIGH defects, all in `SKILL.md` and none in 215 tested lines of Python: a `bd` command using a nonexistent flag (every run failed silently at the filing step), a queue-key prefix collision that dropped a real request, and a heredoc delimiter collision that executed shell from a colleague's pasted message. The dangerous code is reliably the code nobody classified as code.

## Comparing two versions of a skill

Run old and new against the same fixture; never ask an agent to judge the text. Each trap below gives a confident wrong answer:

- **Do not ask both arms to produce the artifact that is the intervention** (requiring a coverage report, then asking both arms for one).
- **A null result can mean the comparison is shaped wrong.** Failures that appear only under parallel fan-out or a competing instruction do not reproduce in one clean run.
- **Read the baseline arm's commentary.** A baseline that independently proposes your change is stronger evidence than the score delta.
- **Attribute results per file.** Multi-file `grep` ordering does not reliably map to arms; getting it backwards inverts the conclusion.
- **`claude -p` returns only the final assistant message**, so a Stop hook replaces your result with the agent's reply to it (six runs came back "Nothing to file."). Have the agent `Write` its report to a named path and grade the file.
- **A `claude -p` subprocess reads this machine's whole auto-memory index**, so a "no standard" baseline is not clean. Arm ordering survives; gap magnitudes do not.

## Never run an eval prompt that reads as a live work order

A description-optimization run executed ~30 synthetic queries as real `claude -p` agents with full tools in the live `~/.claude` root. One fictional work order naming an invented hostname made an agent rewrite `~/.ssh/config` to alias a real host to a machine that never existed; it surfaced as a VPN-looking resolution failure. For any eval of an *action* skill:

- **Sandbox the project root or strip the tools.** A triggering test only needs to observe whether the skill activates.
- **Never use a plausible-but-fake identifier.** Use one that cannot be real (`vm-does-not-exist.invalid`).
- **Sweep for side effects afterwards by mtime**, and check obvious config files by name: `find <paths> -newermt "<eval start>" ! -newermt "<eval end>"`. A tool that edits config politely leaves a `.bak`; look for one before reconstructing by hand.

## Platform facts about skill frontmatter

Checked against Claude Code 2.1.263 with `strings`:

- **1,536 is not a hard description limit.** It is the skill-listing truncation, configurable via `skillListingMaxDescChars`.
- The binary's guidance: description "aim for under 200 characters, never more than **1,024**". The string is confirmed but no enforcing validator was located, so treat 1,024 as a stated ceiling, not a proven rejection threshold.
- `when_to_use` is appended to `description` in the listing; use it for trigger conditions.
- `paths` takes globs and limits auto-activation to matching files.
- Auto-compaction retains the first 5,000 tokens per skill, 25,000 across all skills.
- `.claude/rules/*.md` holds glob-scoped conditional rules, the home for a file-type or directory-specific instruction.

## Do not cite anything only you can open

Session names, run IDs and paths under `~/evidence/` look like evidence to a plugin user who has never seen your machine and function as decoration. Keep the measured figure as a fact; drop the pointer. Dates as change-history markers (`Added 2026-08-28`) are fine.
