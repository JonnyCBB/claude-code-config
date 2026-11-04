# Plugin self-containment: the check, and what the tree currently looks like

The rule is the "Plugins are self-contained" section of `CLAUDE.md`. This file is the procedure: run the check, triage the hits, compare with the baseline.

## Inside and outside

**Inside:** the plugin's own files, anything every Claude Code user has (`~/.claude/settings.json`, `~/.claude/projects/`, their own `CLAUDE.md`), a directory the plugin itself creates and writes, and public URLs. Name shipped files through `${CLAUDE_PLUGIN_ROOT}` or relative to the plugin, never `~/.claude/plugins/<name>/` (the install path is not guaranteed; one skill once stated the same file both ways two lines apart). A runtime output directory such as `~/.claude/thoughts/shared/verification/` is never under `${CLAUDE_PLUGIN_ROOT}` and may be named.

**Outside:** this repository's layout, `~/.claude/docs/`, `~/.claude/thoughts/`, the beads queue and every bead ID, the conductor, any home path not under `~/.claude/`, and **any other plugin**, whatever marketplace (`jbb-feature-dev` may not depend on `jiffy-toolkit`). `plugins/eng-utils/README.md` states this for MCP tool prefixes; read it before re-proposing a fix (PR #137 repointed the prefix and was reverted).

**Four ways to fix one; say which:** inline the substance (short rule); restate it generically when the outside file is only our instance of a general idea; generalise the mechanism and drop the instance; or cut it. Do not copy a long document in.

**An optional dependency (`gh`, `bd`, a sibling plugin) is fine if it is named and degrades in writing.** Unconditional breaks, and so does anonymising it ("if some de-AI-ing skill is installed" cannot be evaluated and costs the reader the name and flag they need when it is present).

## The check

One grep, 0.2s over the largest plugin. Set `PLUGIN` to a real plugin name:

```bash
PLUGIN=jiffy-toolkit
grep -rnE '~/\.claude/(docs/|thoughts/[^ ]*(20[0-9]{2}-[0-9]{2}|corpus)|plugins/[a-z])|~/src/|hq-' \
  "plugins/$PLUGIN/" | grep -v '~/\.claude/plugins/cache'
```

All plugins at once:

```bash
grep -rnE '~/\.claude/(docs/|thoughts/[^ ]*(20[0-9]{2}-[0-9]{2}|corpus)|plugins/[a-z])|~/src/|hq-' \
  plugins/ | grep -v '~/\.claude/plugins/cache'
```

**Never paste a `<name>` placeholder.** In bash `plugins/<name>/` is an input redirection: the command dies with exit 1 and no output, identical to a clean plugin (`grep` exits 1 on no-match and the trailing `grep -v` owns the pipeline status). **Keep the `grep -v` as a pipe:** the folded form `plugins/(?!cache)[a-z]` needs PCRE and fails under `/usr/bin/grep`, and pure-ERE folds leak the cache line or drop plugins starting with c (`codex`, `context7`, `crit`).

## Triage

Every hit is a candidate. The test: someone who installed this plugin and nothing else follows it; do they get something? About a quarter are fine (invented example filenames, placeholders like `2024-01-15_topic.md`). **"It is in a README" is not the heuristic:** 2 of 14 README hits on the baseline were genuine escapes, and 4 illustrative hits were outside READMEs.

**Eval and test fixtures are in scope but last.** A fixture under `evals/` or `tests/` naming the author's own document is a genuine escape (`claude plugin eval` is a real command), though not the same defect as a `SKILL.md` sending a live user to a dead end. Fixing one is authoring synthetic inputs, not de-pathing.

**The `thoughts` clause is narrowed to a dated filename or a corpus; do not widen it.** A plugin naming `~/.claude/thoughts/shared/research/` as a directory it writes is fine; naming one dated document inside it points at something only we have. Matching the bare directory takes 25 hits to 181, and the extra 156 are directories plugins create or search.

**Two classes the grep cannot see; check by eye:**

1. **Our own `CLAUDE.md` cited as where a rule lives** (`sweep-followups/SKILL.md:145`, `create-verification-skill/SKILL.md:48`). The user's `CLAUDE.md` has different contents.
2. **A sibling plugin named as a hard dependency.** `grep -rn 'jiffy-toolkit:' plugins/jbb-feature-dev/`, then read each hit for a stated fallback. `submit-pr/references/pr-prose-rules.md` says to skip it when absent (compliant); `create-my-mode-skill/SKILL.md` sequences two sibling skills with no fallback (not; `hq-hmi4b`).

**A shipped hook or script cannot degrade in writing.** It must exit 0 silently when its dependency is missing, evidenced by a test, not a sentence (`plugins/jbb-feature-dev/hooks/followup_capture.py` requires `bd`).

## Before reporting a clean result, plant a violation

```bash
cat > "plugins/$PLUGIN/CONTROL.md" <<'EOF'
a: ~/.claude/docs/x.md
b: ~/.claude/thoughts/shared/2026-08-01-x.md
c: ~/.claude/thoughts/shared/research/corpus/y/
d: cd ~/src/services-pilot
e: hq-plant9
f: ~/.claude/plugins/other-plugin/f.md
g: ~/.claude/plugins/cache/x            <- must NOT match
h: writes into ~/.claude/thoughts/shared/research/ (added 2026-08-01)   <- must NOT match
EOF
# rerun the check: expect a-f reported, g and h absent, then:
rm -f "plugins/$PLUGIN/CONTROL.md"
```

Line `h` matters most: it is the false positive the narrowing rejects (an output directory on a dated line).

## The master baseline

Master `d74df146`, 2026-09-08, plant step confirmed first: 62 candidates in 36 files; 16 illustrative and fine; **46 genuine escapes**, 2 since fixed (**44 remaining**). Re-measure rather than trusting this; the number should fall as the beads below drain.

| class | count | where it concentrates |
| --- | --- | --- |
| bead IDs cited as the record of a decision | 26 | one `eng-utils` skill, since deleted (12) |
| dated `~/.claude/thoughts/` documents | 25 | `sound-like-me` personas, `jbb-feature-dev` README examples |
| paths on one machine | 7 | `~/src/<other-repo>`, `~/evidence/` |
| absolute install paths | 4 | `design-approach`, `create-my-mode-skill` |
| `~/.claude/docs/` | 0 | - |

The zero is deliberate; the alternative stays in the pattern as a regression guard. Draining: `hq-7bw5q` (bead IDs), `hq-6s0zd` (paths). Whether the check becomes an enforced gate is `hq-flt0o`; a gate failing on all 46 today would be switched off, as `scripts/verify-plugin-setup.sh` already is while red (`hq-g8wea`).
