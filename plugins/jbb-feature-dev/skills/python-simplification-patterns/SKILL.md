---
name: python-simplification-patterns
description: This skill should be used when reviewing Python code for simplification opportunities, refactoring patterns, or identifying Pythonic improvements. Provides before/after examples covering functional style (comprehensions, generators), modern Python features (3.10-3.14 including TypeIs, deferred annotations, template strings), async patterns for LLM/AI work, pytest testing patterns (including RaisesGroup), and import conventions.
allowed-tools:
  - Read
---

# Python Simplification Patterns

Concrete before/after code transformation examples for Python simplification.

## Pattern Categories

- **[Functional Style](functional-style.md)**: List comprehensions, generators, functional patterns
- **[Modern Python](modern-python.md)**: Python 3.10-3.14 features (match, walrus, type unions, TypeIs, deferred annotations, template strings)
- **[Async Patterns](async-patterns.md)**: async/await best practices for LLM/AI work
- **[Testing Patterns](testing-patterns.md)**: pytest fixtures, parametrization, async testing
- **[Import Patterns](import-patterns.md)**: Top-level imports, avoiding inline imports

## Quick Reference

### List Comprehension vs For Loop

Before:

```python
result = []
for item in items:
    if item.is_valid:
        result.append(item.name)
```

After:

```python
result = [item.name for item in items if item.is_valid]
```

### Modern Type Hints (Python 3.10+)

Before:

```python
from typing import List, Dict, Optional, Union

def process(items: List[str]) -> Optional[Dict[str, int]]:
    ...

def handle(value: Union[str, int]) -> None:
    ...
```

After:

```python
def process(items: list[str]) -> dict[str, int] | None:
    ...

def handle(value: str | int) -> None:
    ...
```

### Imports at Top

Before:

```python
def process_file(path: str) -> str:
    from pathlib import Path  # BAD - inline import
    return Path(path).read_text()
```

After:

```python
from pathlib import Path

def process_file(path: str) -> str:
    return Path(path).read_text()
```

For complete patterns with detailed examples, see the category files above.

## Conventions Used in Examples

All examples follow these Python conventions:

- **Python Version**: 3.14 (minimum 3.12; 3.10 for basic modern syntax)
- **Package Manager**: UV
- **Linter/Formatter**: Ruff
- **Type Hints**: Required on all functions
- **Naming**: snake_case (variables/functions), SCREAMING_SNAKE_CASE (constants), PascalCase (classes)
- **Function Length**: ~10 lines max
- **Imports**: Always at top of file

See the language-agnostic patterns in `code-simplification-common` for naming conventions and structural patterns (DRY, SOLID).
