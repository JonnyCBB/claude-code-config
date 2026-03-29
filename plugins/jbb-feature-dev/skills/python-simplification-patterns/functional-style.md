# Functional Style Patterns

## List Comprehensions vs Traditional Loops

### Pattern: Filter-Map

Before:
```python
result = []
for user in users:
    if user.is_active:
        result.append(user.email)
```

After:
```python
result = [user.email for user in users if user.is_active]
```

### Pattern: Nested Comprehension

Before:
```python
pairs = []
for x in xs:
    for y in ys:
        pairs.append((x, y))
```

After:
```python
pairs = [(x, y) for x in xs for y in ys]
```

**Note**: If comprehension exceeds one line or becomes hard to read, use a for loop instead.

### Pattern: Dictionary Comprehension

Before:
```python
user_map = {}
for user in users:
    user_map[user.id] = user.name
```

After:
```python
user_map = {user.id: user.name for user in users}
```

### Pattern: Set Comprehension

Before:
```python
unique_names = set()
for user in users:
    unique_names.add(user.name.lower())
```

After:
```python
unique_names = {user.name.lower() for user in users}
```

## Generator Expressions

### Pattern: Large Data Processing

Before:
```python
# Creates full list in memory
total = sum([len(line) for line in lines])
```

After:
```python
# Generator - memory efficient
total = sum(len(line) for line in lines)
```

### Pattern: First Match

Before:
```python
result = None
for item in items:
    if item.matches(criteria):
        result = item
        break
```

After:
```python
result = next((item for item in items if item.matches(criteria)), None)
```

## Functional Built-ins

### Pattern: any() / all()

Before:
```python
has_admin = False
for user in users:
    if user.role == "admin":
        has_admin = True
        break
```

After:
```python
has_admin = any(user.role == "admin" for user in users)
```

### Pattern: map() with Simple Transform

Before:
```python
names = []
for user in users:
    names.append(user.name.upper())
```

After:
```python
names = list(map(str.upper, (user.name for user in users)))
# Or more readable:
names = [user.name.upper() for user in users]
```

**Note**: Prefer list comprehension over map() for readability unless the function is already defined.

### Pattern: filter() Alternative

Before:
```python
active = list(filter(lambda u: u.is_active, users))
```

After:
```python
active = [u for u in users if u.is_active]
```

**Note**: List comprehension is more Pythonic than filter() with lambda.

## Walrus Operator (:=)

### Pattern: Assign and Check

Before:
```python
match = pattern.search(text)
if match:
    process(match.group(1))
```

After:
```python
if match := pattern.search(text):
    process(match.group(1))
```

### Pattern: While Loop with Assignment

Before:
```python
line = file.readline()
while line:
    process(line)
    line = file.readline()
```

After:
```python
while line := file.readline():
    process(line)
```

### Pattern: List Comprehension with Expensive Call

Before:
```python
results = []
for x in items:
    value = expensive_compute(x)
    if value > threshold:
        results.append(value)
```

After:
```python
results = [y for x in items if (y := expensive_compute(x)) > threshold]
```

**Caution**: Don't overuse walrus operator - readability comes first.

### Pattern: Filter None Values (3.14+)

Before:
```python
items = [1, None, 2, None, 3]
non_none = [x for x in items if x is not None]
```

After:
```python
import operator

items = [1, None, 2, None, 3]
non_none = list(filter(operator.is_not_none, items))  # [1, 2, 3]
```
