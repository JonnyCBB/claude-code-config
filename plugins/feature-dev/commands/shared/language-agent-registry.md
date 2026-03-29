# Language-Agent Registry

This registry maps programming languages to their corresponding reviewer agents. Commands use this to dynamically select language-appropriate agents for code review and simplification.

## How to Use This Registry

1. **Detect language** from file extensions in scope
2. **Look up agents** in the Language Mappings table below
3. **Spawn appropriate agents** based on detected languages
4. **Fall back to general-code-reviewer** for unsupported languages

## Language Mappings

| Language ID  | File Extensions | Test Reviewer              | Code Simplification Reviewer              | Status    |
| ------------ | --------------- | -------------------------- | ----------------------------------------- | --------- |
| `java`       | `.java`         | `java-test-reviewer`       | `java-code-simplification-reviewer`       | Available |
| `python`     | `.py`           | `python-test-reviewer`     | `python-code-simplification-reviewer`     | Available |
| `typescript` | `.ts`, `.tsx`   | `typescript-test-reviewer` | `typescript-code-simplification-reviewer` | Available |
| `javascript` | `.js`, `.jsx`   | `typescript-test-reviewer` | `typescript-code-simplification-reviewer` | Available |

**Note**: JavaScript uses the TypeScript agents as they support both languages.

## Test File Detection

| Language ID  | Test File Patterns                                                        |
| ------------ | ------------------------------------------------------------------------- |
| `java`       | `*Test.java`, `*Tests.java`, `src/test/**/*.java`                         |
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

- `src/main/java/Service.java` → Java
- `frontend/src/App.tsx` → TypeScript

Agents to spawn:

- `java-test-reviewer`, `java-code-simplification-reviewer`
- `typescript-test-reviewer`, `typescript-code-simplification-reviewer`

## Fallback Behavior

| Scenario                             | Fallback Agent                     |
| ------------------------------------ | ---------------------------------- |
| Language not in registry             | `general-code-reviewer`            |
| No test reviewer available           | Skip test review for that language |
| No simplification reviewer available | `general-code-reviewer`            |

## Relationship with Domain Agents

Language agents and domain agents are **complementary**:

- **Language agents**: Focus on language-specific syntax, idioms, and testing patterns
- **Domain agents**: Focus on technology-specific patterns (ML frameworks, data annotations, etc.)

Commands should spawn **both** when applicable. For example, a Python file using ML frameworks should trigger:

- `python-code-simplification-reviewer` (language)
- `ml-pipeline-reviewer` (domain, if ML patterns detected)

## Maintenance

When adding a new language:

1. Create the test reviewer agent (e.g., `agents/go-test-reviewer.md`)
2. Create the code simplification reviewer agent (e.g., `agents/go-code-simplification-reviewer.md`)
3. Add a row to the Language Mappings table
4. Add test file patterns to the Test File Detection table
5. No command changes needed - commands reference this registry dynamically
