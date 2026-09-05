# Quality Check Dimensions

Six scoring dimensions used by the `quality-checker` agent to evaluate deduplicated review findings. Each dimension is scored 1-5.

---

## 1. Coverage

**Does the review address all significant changes in the diff?**

| Score         | Anchor                                                                               |
| ------------- | ------------------------------------------------------------------------------------ |
| 1 (Poor)      | Major changed files or logic paths not addressed; large sections of the diff ignored |
| 2             | Some significant changes examined but notable gaps remain                            |
| 3             | Most significant changes addressed; minor gaps in coverage                           |
| 4             | Nearly all significant changes examined; only trivial items missed                   |
| 5 (Excellent) | Every significant change examined; no meaningful gap in coverage                     |

---

## 2. Depth

**Do findings demonstrate understanding of code behavior and context?**

| Score         | Anchor                                                                                                |
| ------------- | ----------------------------------------------------------------------------------------------------- |
| 1 (Poor)      | Surface-level pattern matches only; findings restate what code does without explaining why it matters |
| 2             | Some reasoning present but mostly pattern-based; limited engagement with surrounding code             |
| 3             | Moderate depth; most findings explain impact but don't always trace full logic paths                  |
| 4             | Strong depth; findings reference surrounding code and explain consequences                            |
| 5 (Excellent) | Traces logic paths, references surrounding code and call sites, explains systemic impact              |

---

## 3. Actionability

**Can the PR author act on each finding without ambiguity?**

| Score         | Anchor                                                                                         |
| ------------- | ---------------------------------------------------------------------------------------------- |
| 1 (Poor)      | Vague with no concrete recommendation; author cannot determine what change is needed           |
| 2             | Some recommendations present but incomplete or ambiguous                                       |
| 3             | Most findings have recommendations; a few require author to infer the fix                      |
| 4             | Nearly all findings have specific, implementable recommendations                               |
| 5 (Excellent) | Every finding has a specific, implementable recommendation; no ambiguity about required action |

---

## 4. Accuracy

**Are the claims in each finding correct?**

| Score         | Anchor                                                                                 |
| ------------- | -------------------------------------------------------------------------------------- |
| 1 (Poor)      | Multiple incorrect claims about code behavior, types, or control flow                  |
| 2             | Some findings contain factual errors; correctness is inconsistent                      |
| 3             | Most claims are correct; isolated errors that don't undermine the finding's core point |
| 4             | Nearly all findings factually correct; minor imprecisions only                         |
| 5 (Excellent) | All findings factually correct and verified against the actual code in the diff        |

---

## 5. Noise

**Is the signal-to-noise ratio high?**

| Score         | Anchor                                                                                  |
| ------------- | --------------------------------------------------------------------------------------- |
| 1 (Poor)      | Most findings are nitpicks, duplicates, or items a linter would catch; low unique value |
| 2             | Many low-value findings dilute the review; signal hard to locate                        |
| 3             | Moderate signal; some noise present but substantive findings exist                      |
| 4             | High signal; occasional low-value finding but easily identified                         |
| 5 (Excellent) | Every finding adds unique value not catchable by automated tools; no redundancy         |

---

## 6. Factual Verification

**Are references to APIs, libraries, and patterns correct and current?**

| Score         | Anchor                                                                                             |
| ------------- | -------------------------------------------------------------------------------------------------- |
| 1 (Poor)      | References non-existent APIs, wrong method signatures, or deprecated patterns presented as current |
| 2             | Several external references are incorrect or outdated                                              |
| 3             | Most references correct; occasional imprecision in API details                                     |
| 4             | Nearly all external references verifiable and current; minor version differences only              |
| 5 (Excellent) | All external references verifiable and current; no fabricated or deprecated API usage              |

---

## Removal Criteria

A finding should be flagged for removal only when it has a clear quality defect in:

- **Accuracy**: Makes an incorrect claim about code behavior
- **Noise**: Is a nitpick, duplicate, or catchable by a linter with no unique insight
- **Factual Verification**: References a non-existent API or deprecated pattern

Low scores on Coverage, Depth, or Actionability are aggregate signals — they do not trigger per-finding removal.
