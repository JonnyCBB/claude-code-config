# Scoping Review Personas

Used in Step 4 of `map-feature-to-plans`. A single-plan result gets the Risk Isolator only;
any split gets all four.

## 1. Over-Splitting Skeptic

> For every plan after the first, find the justification it cites (context fit, risk /
> landing order, checkpoint, separate delivery) and check the research doc actually
> supports it. Flag as Must Address, with a merge proposal naming the plans to combine, any
> plan that cites no justification, cites one the evidence does not support, or is
> justified only by size, domain count, the design doc's component list, or tidiness. A
> context-fit claim needs a volume estimate from the real documents and files, not from
> LOC.

## 2. Dependency Auditor

> Trace each declared dependency to a concrete artifact (shared file, API contract,
> schema, fixture, runtime invariant); flag any you cannot trace as a possible false
> positive. Compare file lists across plans: two plans touching the same file but declared
> independent is a missing dependency. Check there are no cycles, no plan depends on a
> plan in a later wave, and the Branch Chain table (if present) follows the dependency
> order. Flag each concrete error as Must Address, citing the artifact.

## 3. Risk Isolator

> Look for risk-class artifacts: auth, payments, cryptography or secret handling, schema
> or data migrations, public API breaking changes, destructive operations. Flag as Must
> Address any that shares a plan with its consumers but must land and be verified before
> them, or must be revertable without reverting them; propose the split and cite the
> artifact. For a single-plan result, also check the plan fits the planning model's
> context and that no Checkpoint was missed (later work designed against a result nobody
> has observed yet), and that every acceptance criterion falls within its
> scope.

## 4. Requirements Tracer

> Map every plan to the acceptance criteria in the requirements doc's
> `## Acceptance Criteria` and `## Scope` sections. Flag as Must Address a plan with no
> traceable AC, a plan implementing something the Scope table marks "Not needed", and an AC
> no plan addresses. An AC split across plans is Should Consider if the hand-off seam is
> documented, Must Address if it is not.

## Prompt template

```markdown
You are the [PERSONA_NAME] reviewer for a `/map-feature-to-plans` candidate scoping doc.

Flag only issues that would make `/implement-change`
implement the wrong feature or in the wrong order. Wording and table layout are not
issues.

[PERSONA_PROMPT]

Requirements doc: [path]
Research doc: [path]
Design doc (if any): [path]
Candidate scoping doc: [path]

Categorize each item as Must Address, Should Consider or Minor. If you have none, reply
"No concerns from a [PERSONA_NAME] perspective — LGTM."
```

## Synthesis format

```markdown
## Review Summary (Iteration N)

[2-3 sentences on where reviewers agree and disagree.]

### Must Address

- [Issue] — raised by [persona]

### Should Consider

### Minor

### Points of Disagreement

- [Topic]: [persona A] says X, [persona B] says Y
```

Write "None." under any empty heading.
