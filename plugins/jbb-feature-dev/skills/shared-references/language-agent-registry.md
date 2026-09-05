# Language-Agent Registry

This registry maps programming languages to their corresponding expert agents. Commands use this to dynamically select language-appropriate agents for code review, code style, testing, and language-specific guidance.

## How to Use This Registry

1. **Detect language** from file extensions in scope
2. **Look up agents** in the Language Mappings table below
3. **Spawn appropriate agents** based on detected languages
4. **Fall back to `jbb-feature-dev:general-code-reviewer`** for unsupported languages

## Language Mappings

| Language ID  | File Extensions | Expert Agent                        | Status    |
| ------------ | --------------- | ----------------------------------- | --------- |
| `python`     | `.py`           | `jbb-feature-dev:python-expert`     | Available |
| `typescript` | `.ts`, `.tsx`   | `jbb-feature-dev:typescript-expert` | Available |
| `javascript` | `.js`, `.jsx`   | `jbb-feature-dev:typescript-expert` | Available |

**Note**: JavaScript uses the TypeScript expert as it supports both languages.

## Test File Detection

| Language ID  | Test File Patterns                                                        |
| ------------ | ------------------------------------------------------------------------- |
| `python`     | `test_*.py`, `*_test.py`, `tests/**/*.py`                                 |
| `typescript` | `*.test.ts`, `*.test.tsx`, `*.spec.ts`, `*.spec.tsx`, `__tests__/**/*.ts` |
| `javascript` | `*.test.js`, `*.test.jsx`, `*.spec.js`, `*.spec.jsx`, `__tests__/**/*.js` |

## Agent Selection Logic

When a command needs to select language-based agents:

1. **Identify files in scope** (e.g., from git diff, staged files, or explicit paths)
2. **Classify by extension** using the Language Mappings table
3. **For each detected language**, add corresponding agents to spawn list
4. **For unsupported languages**, use `general-code-reviewer` as fallback

### Example: Multi-Language Project

If scope contains:

- `frontend/src/App.tsx` → TypeScript

Agents to spawn:

- `jbb-feature-dev:typescript-expert`

## Fallback Behavior

| Scenario                  | Fallback Agent                          |
| ------------------------- | --------------------------------------- |
| Language not in registry  | `jbb-feature-dev:general-code-reviewer` |
| No expert agent available | `jbb-feature-dev:general-code-reviewer` |

## Relationship with Domain Agents

Language agents and domain agents are **complementary**:

- **Language agents**: Focus on language-specific syntax, idioms, and testing patterns
- **Domain agents**: Focus on technology-specific patterns (see `domain-agent-registry.md`)

Commands should spawn **both** when applicable. For example, a Python file training a model should trigger:

- `jbb-feature-dev:python-expert` (language)
- A relevant domain expert (e.g., `jbb-feature-dev:ml-pipeline-reviewer` if ML context detected)

## Maintenance

When adding a new language:

1. Create the expert agent (e.g., `agents/go-expert.md`)
2. Add a row to the Language Mappings table
3. Add test file patterns to the Test File Detection table
4. No command changes needed - commands reference this registry dynamically
