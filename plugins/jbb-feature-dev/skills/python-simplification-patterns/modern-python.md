# Modern Python Features (3.10+)

## Type Hints (PEP 585, 604)

### Pattern: Built-in Generic Types (3.9+)

Before:
```python
from typing import List, Dict, Set, Tuple, Optional

def process(items: List[str]) -> Dict[str, int]:
    ...
```

After:
```python
def process(items: list[str]) -> dict[str, int]:
    ...
```

### Pattern: Union Types (3.10+)

Before:
```python
from typing import Union, Optional

def find(id: int) -> Optional[User]:
    ...

def handle(value: Union[str, int, float]) -> None:
    ...
```

After:
```python
def find(id: int) -> User | None:
    ...

def handle(value: str | int | float) -> None:
    ...
```

### Pattern: Type Alias

Before:
```python
from typing import Dict, List

UserData = Dict[str, List[int]]
```

After:
```python
type UserData = dict[str, list[int]]  # Python 3.12+
# Or for 3.10+:
UserData = dict[str, list[int]]
```

## Pattern Matching (3.10+)

### Pattern: Replace if-elif Chain

Before:
```python
def handle_status(status: str) -> str:
    if status == "active":
        return "User is active"
    elif status == "pending":
        return "Awaiting approval"
    elif status == "suspended":
        return "Account suspended"
    else:
        return "Unknown status"
```

After:
```python
def handle_status(status: str) -> str:
    match status:
        case "active":
            return "User is active"
        case "pending":
            return "Awaiting approval"
        case "suspended":
            return "Account suspended"
        case _:
            return "Unknown status"
```

### Pattern: Match with Guards

Before:
```python
def categorize(value: int) -> str:
    if value < 0:
        return "negative"
    elif value == 0:
        return "zero"
    elif value < 10:
        return "small"
    else:
        return "large"
```

After:
```python
def categorize(value: int) -> str:
    match value:
        case v if v < 0:
            return "negative"
        case 0:
            return "zero"
        case v if v < 10:
            return "small"
        case _:
            return "large"
```

### Pattern: Match with Destructuring

Before:
```python
def process_point(point: tuple) -> str:
    if len(point) == 2:
        x, y = point
        if x == 0 and y == 0:
            return "origin"
        elif x == 0:
            return f"on y-axis at {y}"
        elif y == 0:
            return f"on x-axis at {x}"
        else:
            return f"at ({x}, {y})"
    return "invalid"
```

After:
```python
def process_point(point: tuple[int, int]) -> str:
    match point:
        case (0, 0):
            return "origin"
        case (0, y):
            return f"on y-axis at {y}"
        case (x, 0):
            return f"on x-axis at {x}"
        case (x, y):
            return f"at ({x}, {y})"
```

### Pattern: Match on Type

Before:
```python
def serialize(value: object) -> str:
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, list):
        return "[" + ", ".join(serialize(v) for v in value) + "]"
    else:
        raise TypeError(f"Cannot serialize {type(value)}")
```

After:
```python
def serialize(value: object) -> str:
    match value:
        case str(s):
            return f'"{s}"'
        case bool(b):
            return "true" if b else "false"
        case int(n):
            return str(n)
        case list(items):
            return "[" + ", ".join(serialize(v) for v in items) + "]"
        case _:
            raise TypeError(f"Cannot serialize {type(value)}")
```

## Exception Groups (3.11+)

### Pattern: Handle Multiple Exceptions

Before:
```python
errors = []
for task in tasks:
    try:
        task.run()
    except Exception as e:
        errors.append(e)
if errors:
    raise Exception(f"Multiple errors: {errors}")
```

After:
```python
# Python 3.11+ with ExceptionGroup
errors = []
for task in tasks:
    try:
        task.run()
    except Exception as e:
        errors.append(e)
if errors:
    raise ExceptionGroup("Multiple task failures", errors)
```

## Dataclasses Enhancements

### Pattern: Slots for Memory Efficiency (3.10+)

Before:
```python
@dataclass
class User:
    id: int
    name: str
    email: str
```

After:
```python
@dataclass(slots=True)
class User:
    id: int
    name: str
    email: str
```

### Pattern: Keyword-Only Fields (3.10+)

```python
@dataclass(kw_only=True)
class Config:
    host: str
    port: int = 8080
    debug: bool = False
```

## Python 3.13 Features

### Pattern: TypeIs for Type Narrowing (PEP 742)

Preferred over TypeGuard for type narrowing:

```python
from typing import TypeIs

def is_str_list(val: list[object]) -> TypeIs[list[str]]:
    return all(isinstance(x, str) for x in val)
# Narrows in BOTH true and false branches (TypeGuard only narrows true branch)
```

### Pattern: Type Parameter Defaults (PEP 696)

```python
from typing import TypeVar, Generic

T = TypeVar('T', default=int)

class Container(Generic[T]):
    ...

x: Container[str]  # override default
y: Container        # uses int default
```

### Pattern: ReadOnly TypedDict (PEP 705)

```python
from typing import TypedDict, ReadOnly

class Config(TypedDict):
    name: ReadOnly[str]  # Type checkers flag mutations
    debug: bool          # Mutable
```

### Pattern: warnings.deprecated() Decorator (PEP 702)

```python
from warnings import deprecated

@deprecated("Use new_function() instead")
def old_function() -> None: ...
# Emits DeprecationWarning at runtime, type checkers also flag calls
```

### Pattern: copy.replace() -- Universal Replacement

```python
from copy import replace
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: int
    y: int

p2 = replace(Point(1, 2), x=3)  # Point(x=3, y=2)
# Also works with namedtuples, datetime objects, and any class with __replace__()
```

## Python 3.14 Features (Forward-Looking)

### Pattern: Deferred Evaluation of Annotations (PEP 649) (Python 3.14+)

Before:
```python
from __future__ import annotations  # Needed for forward references

class Tree:
    def children(self) -> list["Tree"]:  # Quoted forward reference
        ...
```

After (3.14+):
```python
# No import needed, no quoting needed
class Tree:
    def children(self) -> list[Tree]:  # Just works
        ...
```

### Pattern: Template Strings (PEP 750) (Python 3.14+)

```python
from string.templatelib import Template

name = "O'Brien"
template = t"SELECT * FROM users WHERE name = {name}"
# template is a Template object, NOT a string
# Enables safe processing before final rendering (SQL injection prevention, etc.)
```

### Pattern: Bracket-less Exception Handling (PEP 758) (Python 3.14+)

Before:
```python
try:
    connect()
except (TimeoutError, ConnectionRefusedError):
    print("Failed")
```

After (3.14+):
```python
try:
    connect()
except TimeoutError, ConnectionRefusedError:  # Parentheses optional without 'as'
    print("Failed")
# Still requires parentheses when using 'as':
# except (TimeoutError, ConnectionRefusedError) as e:
```
