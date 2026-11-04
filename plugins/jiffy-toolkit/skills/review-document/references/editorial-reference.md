# Editorial Reference

Consolidated normative reference for document review agents (Prose Quality Reviewer, Structure Reviewer, Consistency Checker). Absorbs the full content of the editorial-standards source files: editorial-dimensions, decision-framework, document-type-standards, special-considerations, and references-and-resources.

## STE-informed Review

Use [ASD-STE100 Simplified Technical English (STE)](https://www.asd-ste100.org/about_STE.html)
clarity principles as the default for technical prose. This guidance is not the full standard or
its controlled dictionary. Do not report formal STE compliance unless you checked both.

For each relevant finding and suggested edit:

- Check that a briefing states the supported outcome and reader decision before the mechanism.
  For a tutorial, check the expected result before the steps. Keep reference documents easy to look
  up; do not force a narrative opening into every entry. Never invent an outcome absent from the source.
- Prefer short sentences with one main idea and direct verbs. Name the actor when known, and put
  conditions before the actions they control. Keep one action per instruction and show its expected result.
- Use one term per concept. Keep exact API names and other technical terms; explain unfamiliar ones
  at first use. Simplify the surrounding prose, not the identifier. Avoid idioms and abstract noun chains.
- Preserve exceptions, conditions, uncertainty, evidence limits, and source links. Do not edit code,
  commands, or quotations merely to match the prose style. Do not chase sentence-length or readability scores.
- Keep a natural tone. Suggest a concrete example where it would clarify the result; label an
  invented example as illustrative, not observed evidence.

For example, when supported by the source, suggest "Owners receive one notice per channel, not one
per rollout" before the explanation of channel grouping. Treat this move as restructuring under
the decision framework below, not as a mechanical edit. Flag a reader's likely misunderstanding,
not a style preference or an unverified dictionary violation. Write findings and summaries in the
same clear style.

## Editorial Dimensions

Evaluate documents across all 9 dimensions below. Each dimension is independent; reviewers should assess every dimension relevant to their role.

### 1. Content & Structure (Developmental/Substantive)

- Overall purpose and thesis clarity
- Logical organization and document flow
- Completeness of coverage for the document type
- Paragraph structure and transitions
- Appropriate level of detail for audience
- **Document type adherence**: Tutorial vs. How-to vs. Reference vs. Explanation (Diataxis framework)

### 2. Style & Language (Line Editing)

- Sentence-level clarity and conciseness (remove words that carry nothing; never a step, definition or example the reader needs)
- Word choice precision and appropriateness
- Active voice vs. passive voice balance
- Tone consistency and appropriateness for audience
- **Word choice, in this order.** First: is there a plainer word that does the same job with nothing
  lost? Use it. Second: is the harder word the actual name of the thing, or genuinely more precise?
  Keep it and define it on first use. Never leave a term unexplained on either branch, and never
  swap a precise term for a vaguer one to hit a score - that takes away the word the reader can
  search for. Whether the reader already owns the term decides how much glossing it needs, so this
  is a judgement about the audience, not about how technical the word looks.
- The two rules above are also stated, for the writing surface rather than the reviewing one, in
  the `explain` skill. If you change one, change both.
- **Readability: do not score it.** A grade-level formula is arithmetic over average word length and
  average sentence length and reads nothing else. It therefore penalises `idempotent` and
  `PilotDataAccess` in a document written for people who use those words daily, and rewards breaking
  one accurate sentence into two vague ones. Judge instead whether a reader in the stated audience
  could act on the document without looking anything up that the document could have told them.

### 3. Mechanics (Copy Editing)

- **Grammar**: Subject-verb agreement, tense consistency, pronoun references, parallel structure
- **Spelling**: Including proper nouns, technical terms, common homonym errors
- **Punctuation**: Commas, semicolons, apostrophes, quotation marks, serial commas
- **Capitalization**: Consistent heading case, proper nouns, UI elements
- **Number usage**: When to spell out vs. use numerals

### 4. Consistency

- Terminology and nomenclature (same concept = same word throughout)
- Formatting (headings, lists, code blocks, spacing)
- Point of view (1st, 2nd, or 3rd person)
- Tense (present vs. past)
- Style choices applied uniformly
- Hyphenation and compound words

### 5. Technical Writing Best Practices

- **Scannability**: Meaningful headings, bulleted/numbered lists, white space, bold keywords
- **Chunking**: Short paragraphs (one idea each), 50-75 character lines, visual hierarchy
- **Reading patterns**: Optimize for all four scanning behaviors:
  - **F-pattern**: Critical info in first 2 paragraphs, front-load headings with keywords
  - **Spotted pattern**: Bold key terms, use descriptive link text for scanners seeking specific items
  - **Layer-cake pattern**: Make headings self-explanatory and information-rich (readers may read only headings)
  - **Commitment pattern**: Rare full-read behavior; optimize for F-pattern anyway since commitment readers will read regardless
- **Plain language**: short sentences and a conversational tone, and the plainer word wherever it
  loses nothing. Plain language is about the sentences around a term of art, not about deleting the
  term of art.
- **Front-load the conclusion, and for anything a reader has to act on, open with the outcome rather
  than the mechanism.** This is the same rule `structure-reviewer` checks at step 8. Two cautions on
  where the support for it actually comes from, because both are widely miscited: "bottom line up
  front" is doctrine - the US Army writing standard requires it and cites no study, and the Nielsen
  Norman Group's inverted-pyramid article claims improved comprehension and cites no controlled
  study. And the F-pattern below is a **failure mode** those same authors call "bad for users and
  businesses", not a justification. The real support is the signalling and pre-training research
  (median d = 0.41 over 28 tests, and d = 0.75 over 16), and it reverses for high-expertise readers.
  Evidence and sources: `skills/sound-like-me/references/objective-first-example.md`.

### 6. Accessibility & Inclusivity

- Acronyms spelled out on first use
- Bias-free, inclusive language
- No culture-specific idioms or regional expressions
- Gender-neutral language where appropriate
- Every term the stated audience would not already know is explained where it first appears
- No reliance on color alone for meaning

### 7. Formatting & Visual Hierarchy

- Proper heading hierarchy (H1 to H2 to H3, no skipping levels)
- Consistent list formatting (numbered for sequences, bulleted for other lists)
- Code blocks properly formatted with syntax highlighting hints
- Appropriate use of bold, italic, code font
- Tables used appropriately for comparisons
- Images/diagrams referenced properly with alt text

### 8. Accuracy & Fact-Checking

- Technical accuracy of statements
- Currency of information (outdated references, deprecated APIs)
- Consistency with linked/referenced materials
- Proper citation of sources when needed

### 9. Clarity & Communication

- **One sentence = one idea** principle
- Ambiguous pronouns eliminated (pronouns >5 words from antecedent = flag)
- Specific, concrete language vs. vague generalizations
- User-centric language (focus on what user needs, not system capabilities)
- Assumptions made explicit

## Decision Framework

Use this 3-tier framework to determine whether to flag, cautiously flag, or preserve a given issue. This framework is critical for calibrator behavior: it defines the boundary between helpful editing and harmful over-editing.

### ALWAYS FLAG (Meaning-Neutral Improvements)

These changes carry no risk of altering the author's intent. Flag every occurrence.

1. **Grammar and mechanics errors** that obscure meaning
2. **Ambiguous pronouns** more than 5 words from their antecedent
3. **Inconsistent terminology** (same concept, different words)
4. **Passive voice** where active voice is clearer (unless intentionally formal/authoritative)
5. **Unnecessary words** that add no semantic value ("in order to" to "to")
6. **Complex words** with simpler synonyms when audience doesn't require precision
7. **Long sentences** with multiple independent ideas (should be split)
8. **Wall of text** lacking headings, lists, or visual hierarchy
9. **Spelling errors** and typos
10. **Missing serial commas** (unless style guide explicitly forbids)

### FLAG WITH CAUTION (Verify Meaning Preserved)

These changes improve readability but risk altering logical relationships or emphasis. Verify before flagging.

1. **Sentence restructuring** recommendations (ensure logical relationships maintained)
2. **Combining sentences** (ensure no context loss)
3. **Simplifying technical terms** (verify accuracy not compromised)
4. **Converting prose to lists** (ensure sequence/priority preserved)
5. **Moving content** (verify coherence and flow maintained)

### PRESERVE (High Risk of Changing Meaning/Intent)

These constructions are likely intentional. Do not flag unless clearly erroneous.

1. **Intentional passive voice** for emphasis, tone, or unknown actor
2. **Domain-specific jargon** when writing for expert audience
3. **Author's stylistic choices** that don't impair clarity (e.g., deliberate repetition for emphasis)
4. **Cultural or contextual expressions** that carry specific meaning
5. **Carefully chosen qualifiers** indicating uncertainty or nuance ("may", "might", "generally")
6. **Technical precision** required for scientific/legal accuracy
7. **Documented standards** (API names, brand names, proper nouns, established terms)
8. **Intentional complexity** appropriate for sophisticated audience

## Document Type Standards

Apply these per-type expectations in addition to the universal editorial dimensions above.

### RFCs (Request for Comments)

- Clear problem statement and proposed solution
- Alternatives considered section
- Security/privacy considerations
- Migration/rollout plan
- Success metrics defined

### README.md Files

- Clear project description and purpose
- Installation instructions
- Usage examples with code
- Prerequisites clearly stated
- Links to additional documentation

### Tutorials

- Clear learning objectives stated upfront
- Step-by-step instructions with expected outcomes
- Prerequisites and setup requirements
- Troubleshooting section
- Next steps or related resources

### API Documentation

- Complete resource descriptions
- All endpoints, methods, and parameters documented
- Request and response examples
- Authentication requirements clearly stated
- Error codes and handling guidance

## Special Considerations

### Multi-Cultural Audiences

- Flag idioms, regional expressions, culture-specific references
- Note US-centric assumptions (date formats, units, examples)
- Recommend inclusive examples and references

### Technical Accuracy

- Flag technical claims you can verify as incorrect
- Note areas where you cannot verify accuracy (suggest SME review)
- Recommend sources/links for technical assertions

### Regulatory/Compliance Documents

- Note when precision is legally required (preserve complex language)
- Flag ambiguities in specifications or requirements
- Recommend explicit language for contractual clarity

### AI-Generated Content Disclosure

With the EU AI Act provisions taking effect (August 2026 deadline for transparency obligations), documents should consider:

- Whether AI-assisted content requires disclosure under applicable regulations
- Labeling AI-generated or AI-assisted sections when required by organizational or regulatory policy
- Maintaining human editorial oversight and accountability for AI-assisted content
- Following evolving industry standards for AI content transparency

## References

### Authoritative Style Guides

- Google Developer Documentation Style Guide: https://developers.google.com/style
- Microsoft Writing Style Guide: https://learn.microsoft.com/en-us/style-guide/
- GitHub Documentation Style Guide: https://docs.github.com/en/contributing/style-guide-and-content-model/style-guide
- GitLab Documentation Style Guide: https://docs.gitlab.com/development/documentation/styleguide/
- Plain Language Guidelines: https://digital.gov/guides/plain-language
- Apple Style Guide: https://support.apple.com/guide/applestyleguide/welcome/web
- Red Hat Supplementary Style Guide (v7.1): https://redhat-documentation.github.io/supplementary-style-guide/

### Technical Writing Resources

- Google Technical Writing Courses: https://developers.google.com/tech-writing
  - Technical Writing One: Technical writing fundamentals
  - Technical Writing Two: Intermediate technical writing
  - Tech Writing for Accessibility: Writing accessible documentation
  - Technical Writing for Accessibility: Inclusive documentation practices
- Write the Docs: https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/
- Diataxis Documentation Framework: https://diataxis.fr/

### Editorial Standards

- Purdue OWL - Proofreading: https://owl.purdue.edu/owl/general_writing/the_writing_process/proofreading/
- UNC Writing Center - Editing and Proofreading: https://writingcenter.unc.edu/tips-and-tools/editing-and-proofreading/

### Readability Research

- Nielsen Norman Group - How Users Read on the Web: https://www.nngroup.com/articles/how-users-read-on-the-web/
- Nielsen Norman Group - F-Shaped Pattern: https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/
- Nielsen Norman Group - Readability: https://www.nngroup.com/articles/legibility-readability-comprehension/
- Nielsen Norman Group - Evolved Reading Patterns: https://www.nngroup.com/articles/text-scanning-patterns-eyetracking/
