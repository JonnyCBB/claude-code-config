# Import Patterns

Python imports should ALWAYS be at the top of the file.

## Core Rule

**All imports must be at the top of the file, never inside functions.**

## Correct Pattern

```python
# Standard library imports (alphabetical)
import asyncio
import json
from pathlib import Path

# Third-party imports (alphabetical)
import aiohttp
from pydantic import BaseModel

# Local imports (alphabetical)
from mypackage.models import User
from mypackage.utils import helper


def process_data(path: str) -> dict:
    """All imports already available at module level."""
    return json.loads(Path(path).read_text())
```

## Anti-Pattern: Inline Imports

```python
# BAD - import inside function
def process_data(path: str) -> dict:
    import json  # WRONG
    from pathlib import Path  # WRONG
    return json.loads(Path(path).read_text())
```

## Import Order (PEP 8 + isort/Ruff)

```python
# 1. Standard library
import os
import sys
from collections import defaultdict
from pathlib import Path

# 2. Third-party packages
import aiohttp
import pytest
from pydantic import BaseModel

# 3. Local/project imports
from mypackage import config
from mypackage.models import User
```

## Rare Exceptions (Use Sparingly)

### Exception 1: Circular Import Avoidance

```python
# Only when refactoring is not possible
def get_related_model():
    from mypackage.models import RelatedModel  # Breaks circular import
    return RelatedModel
```

**Better solution**: Refactor to eliminate circular dependency.

### Exception 2: Optional Dependencies

```python
# At module level, not inside function
try:
    import optional_package
    HAS_OPTIONAL = True
except ImportError:
    HAS_OPTIONAL = False

def use_optional():
    if not HAS_OPTIONAL:
        raise RuntimeError("optional_package required")
    return optional_package.do_thing()
```

### Exception 3: Heavy Import for CLI Startup

```python
# Only for CLI tools where startup time matters
# Still prefer top-level imports when possible
def run_heavy_feature():
    import heavy_ml_library  # Deferred to avoid slow CLI startup
    return heavy_ml_library.process()
```

## Type Checking Imports

### Pattern: TYPE_CHECKING Block

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Only imported during type checking, not at runtime
    from expensive_module import ExpensiveClass

def process(item: ExpensiveClass) -> None:
    ...
```

**Note**: This is acceptable because it doesn't affect runtime behavior.

## Ruff Configuration for Imports

```toml
[tool.ruff.lint]
select = [
    "I",    # isort
    "F401", # unused imports
    "F811", # redefinition of unused name
]

[tool.ruff.lint.isort]
known-first-party = ["mypackage"]
force-single-line = false
```
