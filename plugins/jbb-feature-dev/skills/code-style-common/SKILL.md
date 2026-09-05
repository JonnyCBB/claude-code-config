---
name: code-style-common
description: >
  Common code style patterns shared across languages (Java, Scala, Python, TypeScript). Covers
  naming conventions, structural patterns (DRY, SOLID), and comment quality. Loaded
  automatically alongside language-specific code style skills during code review.
  Not typically invoked directly by users.
allowed-tools:
  - Read
---

# Common Code Style Patterns

Shared patterns applicable to Java, Scala, Python, and TypeScript code style.

## Pattern Categories

- **[Naming Conventions](naming-conventions.md)**: Methods, classes, variables, constants
- **[Structural Patterns](structural-patterns.md)**: DRY, SOLID, method length, class cohesion
- **[Comment Quality](comment-quality.md)**: WHY not WHAT, self-documenting code
- **[Test Anti-Patterns](test-anti-patterns.md)**: Low-value tests to avoid (enum tests, static config tests, mapping tests)

## Quick Reference

### Naming: Verb-Noun Pattern for Methods

Before:

```
userData()           // Noun only - is this a getter? A processor?
processData()        // Vague verb
handle()             // Too generic
```

After:

```
findUserById()       // Clear action + target
validateOrderItems() // Specific action
sendNotification()   // Explicit behavior
```

### Structural: Method Length

A method should fit on one screen (~20 lines). If longer, extract sub-methods. (Python applies a deliberately stricter ~10-line convention; see `python-code-style`.)

Before:

```
void processOrder(Order order) {
    // 50 lines of validation, calculation, notification...
}
```

After:

```
void processOrder(Order order) {
    validateOrder(order);
    calculateTotals(order);
    applyDiscounts(order);
    sendConfirmation(order);
}
```

For complete patterns with detailed examples, see the category files above.

## Conventions Used in Examples

Examples in this skill use language-agnostic pseudocode or Java/Scala syntax. When language-specific, the following conventions apply:

**Java/Scala:**

- **Static imports**: Common utilities like `checkNotNull()`, `checkArgument()` assume static imports
- **Modern Java**: Examples use Java 16+ features like `.toList()` where applicable
- **Streams over loops**: Prefer functional stream operations over explicit iteration

**Python:**

- **snake_case**: Variables and functions use snake_case (not camelCase)
- **Modern Python**: Examples assume Python 3.10+ for type unions and pattern matching
- **Comprehensions over loops**: Prefer list/dict comprehensions over explicit iteration

See the language-specific skills for complete conventions:

- `java-code-style` - Java streams, Optional, Java 21/25 features
- `scala-code-style` - Scala functional idioms
- `python-code-style` - Python comprehensions, async, modern syntax
- `typescript-code-style` - TypeScript 5.x features, React 18/19 patterns, RTL/Vitest testing
