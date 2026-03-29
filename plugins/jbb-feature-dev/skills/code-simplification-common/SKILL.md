---
name: code-simplification-common
description: Common code simplification patterns shared across languages (Java, Scala, Python). Covers naming conventions, structural patterns (DRY, SOLID), and comment quality. Use alongside language-specific simplification skills.
allowed-tools:
  - Read
---

# Common Code Simplification Patterns

Shared patterns applicable to Java, Scala, and Python code simplification.

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

A method should fit on one screen (~20 lines). If longer, extract sub-methods.

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
- `java-simplification-patterns` - Java streams, Optional, Java 21/25 features
- `scala-simplification-patterns` - Scala functional idioms
- `python-simplification-patterns` - Python comprehensions, async, modern syntax
