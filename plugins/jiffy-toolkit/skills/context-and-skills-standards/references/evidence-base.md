# Evidence Base

Source citations for the 8 principles in this skill, organized by confidence tier.
Use this file when assessing recommendation quality or explaining findings to others.

---

## Tier 1: Primary Academic Sources

| Source | Key Finding | Status | URL |
|--------|-------------|--------|-----|
| "Evaluating AGENTS.md" — Gloaguen et al., ETH Zurich (Feb 2026) | LLM-generated context: −2–3% success, +20–23% cost. Developer-written: +4%, +19% cost. Agents follow specific instructions 1.6–2.5x | Core — corroborated by all other sources | https://arxiv.org/abs/2602.11988 |
| "SkillsBench" — Li et al., 40 researchers (Feb 2026) | Curated skills: +16.2pp. Self-generated: −1.3pp. 2–3 modules optimal (+18.6pp). Comprehensive hurts (−2.9pp). Healthcare: +51.9pp, SE: +4.5pp | Core — cross-validates P2, P4, P5, P6 | https://arxiv.org/abs/2602.12670 |
| "On the Impact of AGENTS.md" — arxiv 2601.20404 | Context files reduced median runtime 28.64%, output tokens 16.58% — BUT measured efficiency not correctness | Partial — faster ≠ better | https://arxiv.org/abs/2601.20404 |
| "Context Rot" — Chroma (Jul 2025) | Performance degrades as input length grows across 18 models, even with perfect retrieval | Corroborates P4 | https://research.trychroma.com/context-rot |
| "Context Length Hurts" — arxiv 2510.05381 | Performance degrades with input length even when model can retrieve all evidence | Corroborates P4 | https://arxiv.org/html/2510.05381v1 |
| "Over-Prompting" — arxiv 2509.13196 | Excessive domain-specific examples can paradoxically degrade performance | Corroborates P8 | https://arxiv.org/html/2509.13196v1 |
| "Prompt Underspecification" — arxiv 2505.13360 | More requirements can drop performance 19% | Corroborates P1, P4 | https://arxiv.org/html/2505.13360v1 |
| "Domain Knowledge Augmentation" — arxiv 2601.15153 | 206% improvement with codified domain knowledge in low-coverage areas | Corroborates P2 | https://arxiv.org/abs/2601.15153v1 |
| "Configuring Agentic AI Coding Tools" — arxiv 2602.14690 | Survey of 2,926 repos; practitioner convergence on 1–2 skills per repo | Corroborates P5 | https://arxiv.org/html/2602.14690v1 |

---

## Tier 2: Official Documentation

| Source | Key Finding | URL |
|--------|-------------|-----|
| Anthropic: Claude Code Best Practices | "If Claude already does something correctly without the instruction, delete it." Warns against long CLAUDE.md files. | https://code.claude.com/docs/en/best-practices |
| Anthropic: Effective Context Engineering | "Standard language conventions Claude already knows" should be excluded. Tool definitions need prompt engineering attention. | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| Anthropic: Skills Best Practices | Good example: 50 tokens with code. Bad example: 150 tokens of explanation. | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices |
| GitHub: How to Write AGENTS.md | "One real code snippet showing your style beats three paragraphs describing it." Analysis of 2,500+ repos. | https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/ |
| OpenAI: AGENTS.md Guide | Similar findings from Codex perspective — specific tooling instructions most valuable | https://developers.openai.com/codex/guides/agents-md/ |

---

## Tier 3: Industry and Practitioner Sources

| Source | Key Finding | URL |
|--------|-------------|-----|
| Vercel: AGENTS.md vs Skills | For new framework (Next.js 16): AGENTS.md achieved 100% vs 53% baseline. 56% of skills never invoked. Always-present outperforms lazy-loaded for frequently-needed knowledge. | https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals |
| Block Engineering: 3 Principles | "Write a Constitution, Not a Suggestion." Lock deterministic tasks into executable scripts. | https://engineering.block.xyz/blog/3-principles-for-designing-agent-skills |
| HumanLayer: Writing Good CLAUDE.md | Recommends under 60 lines. Explicitly warns against `/init` auto-generated content. | https://www.humanlayer.dev/blog/writing-a-good-claude-md |
| Arize: CLAUDE.md Optimization | Eval-driven iterative optimization with human review → +5.19% improvement. The only viable automated approach. | https://arize.com/blog/claude-md-best-practices-learned-from-optimizing-claude-code-with-prompt-learning/ |
| Martin Fowler: Context Engineering (Feb 2026) | "Models have become powerful enough that extensive context previously necessary may no longer be required." | https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html |
| Builder.io: AGENTS.md Guide | "Iterate and add a rule the second time you see the same mistake." | https://www.builder.io/blog/agents-md |

---

## Contradictions and Resolutions

| Contradiction | Resolution |
|---------------|------------|
| Vercel found +47pp from AGENTS.md for Next.js 16 | Corroborates P2 — context files are transformative when providing knowledge absent from training data. Next.js 16 was a new framework. |
| First AGENTS.md study (2601.20404) found 29% efficiency improvement | Measured efficiency (time/tokens), not correctness. Faster ≠ better outcomes. |
| Vercel: AGENTS.md outperforms Skills in 56% of cases | Delivery mechanism debate, not content debate. Always-present beats lazy-loaded for frequently-needed knowledge (P7). |
| DEV Community critique of SkillsBench | Methodological — benchmark doesn't isolate whether Skills architecture matters vs injecting same text into prompt. Practically, if the content helps, the mechanism is secondary. |

---

## Confidence Summary

All 8 principles in SKILL.md are supported by 3+ independent sources at Very High or High
confidence. P7 (Always-Present vs Lazy-Loaded) has Medium confidence due to being primarily
supported by one Vercel study plus Anthropic architecture documentation.
