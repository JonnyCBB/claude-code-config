---
name: implement-plan
description: Execute approved implementation plans with progress tracking. Use when the user has an approved plan file and wants to begin implementation.
argument-hint: [plan-path] [--non-interactive]
---

# Implement Plan

You are tasked with implementing an approved technical plan from `~/.claude/thoughts/shared/plans/`. These plans contain phases with specific changes and success criteria.

## Mode Detection

Parse `$ARGUMENTS` for flags and input:

- If `$ARGUMENTS` contains `--non-interactive`: Set NON_INTERACTIVE mode
  - A plan path argument is REQUIRED
  - Handle plan/code mismatches autonomously:
    - Do NOT stop implementation
    - Log each mismatch to `~/.claude/thoughts/shared/implementation_mismatches/YYYY-MM-DD-description.md`
    - Use `~/.claude/skills/decision-principles/SKILL.md` to choose the best resolution
    - Continue implementation using best judgment
  - Handle guideline conflicts autonomously:
    - Apply guideline fixes without asking for approval
    - Log all guideline-driven changes in the mismatch file
  - Run automated success criteria after each phase without stopping
- If `$ARGUMENTS` does not contain `--non-interactive`: Behave exactly as before (interactive mode)

## Getting Started

When given a plan path:

- Read the plan completely and check for any existing checkmarks (- [x])
- Read the original ticket and all files mentioned in the plan
- **Read files fully** - never use limit/offset parameters, you need complete context
- Think deeply about how the pieces fit together
- Create a todo list to track your progress
- **Detect domains in the plan for proactive guidance:**
  - Follow the detection procedure in `skills/shared-references/domain-agent-registry.md` (file triggers first, then content signals)
  - Identified domains can be consulted proactively if implementation questions arise
  - **Output for user:**
    ```
    ## Domains Detected in Plan
    - ✓ [Domain]: Found "[pattern]" → [agent-name] available for guidance
    - ✗ [Domain]: Not detected
    ```
- Start implementing if you understand what needs to be done

If no plan path provided, ask for one.

## Implementation Philosophy

Plans are carefully designed and represent agreed-upon specifications. Your job is to:

- **Implement what the plan specifies** - not a simplified version, not your interpretation
- Implement each phase fully before moving to the next
- Verify your work makes sense in the broader codebase context
- Update checkboxes in the plan as you complete sections

### Code Specifications Are Binding

When the plan includes full code implementations (classes, methods, etc.), treat these as **specifications that MUST be implemented exactly as written**. You may:

- Fix obvious typos or syntax errors
- Adjust import statements to match actual package locations
- Add missing annotations required by the framework

You may NOT:

- Simplify the implementation
- Remove features or functionality
- Replace the design with a "simpler" approach
- Skip implementing parts you find complex

### Handling Mismatches (MANDATORY)

If you encounter ANY situation where the plan cannot be implemented as written:

**If in NON_INTERACTIVE mode:**

Do NOT stop. Instead:

1. Create `~/.claude/thoughts/shared/implementation_mismatches/` directory if it doesn't exist
2. Log the mismatch with:
   - Phase, what plan specifies vs actual situation, impact
   - Resolution decision, principle applied, rationale
   - Options considered
3. Apply the decision-principles workflow (safety → evidence → simplicity → scope)
4. Implement the chosen resolution and continue

**If in interactive mode (default):**

**STOP IMMEDIATELY. Do not continue implementing.**

Present the issue clearly to the user:

```
IMPLEMENTATION BLOCKED - Mismatch Detected

Phase: [N]
Plan specifies: [what the plan says - be specific]
Actual situation: [what you found in the codebase]
Impact: [what cannot be implemented as a result]

Options I see:
1. [option 1]
2. [option 2]

Which approach should I take?
```

**WAIT for user response before continuing.**

Do NOT rationalize, simplify, or "adapt" your way around mismatches.

## Verification Approach

After implementing a phase:

- Run the success criteria checks
- Fix any issues before proceeding
- Update your progress in both the plan and your todos
- Check off completed items in the plan file itself using Edit

## If You Get Stuck

When something isn't working as expected:

- First, make sure you've read and understood all the relevant code
- Consider if the codebase has evolved since the plan was written
- Use the web-search-researcher subagent for information that is not in the repo
- If the code uses an unfamiliar framework, use web-search-researcher for its docs
- **Spawn detected domain experts proactively**
- **STOP and present the mismatch clearly - ask for guidance before continuing**

Use sub-tasks sparingly - mainly for targeted debugging or exploring unfamiliar territory.

**CRITICAL: Never "work around" a problem by implementing something different than the plan specifies. If you can't implement what's in the plan, STOP and ask.**

## Resuming Work

If the plan has existing checkmarks:

- Trust that completed work is done
- Pick up from the first unchecked item
- Verify previous work only if something seems off

## After implementation

Once you've finished the implementation, ensure changes adhere to existing coding guidelines/standards:

- Use the built-in **Explore** agent to find coding standards/guidelines files
- Compare the implemented code changes with the guidelines

**If in NON_INTERACTIVE mode:**

- Apply all guideline fixes autonomously
- Log each guideline change to the mismatch file under a `## Guideline Changes` section
- Run all automated success criteria to verify no regressions

**If in interactive mode (default):**

- If there are conflicts, present them to the user along with proposed changes
- WAIT for user approval before making changes
- If any changes are made, run all automated success criteria
