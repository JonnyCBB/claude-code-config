# Testing Patterns

pytest patterns for Python, including async testing.

## Fixture Patterns

### Pattern: Use Fixtures Instead of setUp

Before:
```python
class TestUser(unittest.TestCase):
    def setUp(self):
        self.db = create_test_db()
        self.user = User(id=1, name="test")

    def tearDown(self):
        self.db.close()

    def test_save(self):
        self.user.save(self.db)
        assert self.db.get(1) == self.user
```

After:
```python
@pytest.fixture
def db():
    database = create_test_db()
    yield database
    database.close()

@pytest.fixture
def user() -> User:
    return User(id=1, name="test")

def test_save(db, user):
    user.save(db)
    assert db.get(1) == user
```

### Pattern: Fixture Scope

```python
@pytest.fixture(scope="session")
def expensive_resource():
    """Created once per test session."""
    return create_expensive_thing()

@pytest.fixture(scope="module")
def module_resource():
    """Created once per test module."""
    return create_thing()

@pytest.fixture  # Default: scope="function"
def fresh_resource():
    """Created fresh for each test."""
    return create_thing()
```

### Pattern: Fixture Factory

```python
@pytest.fixture
def make_user():
    """Factory fixture for creating users with custom attributes."""
    def _make_user(name: str = "test", role: str = "user") -> User:
        return User(id=uuid4(), name=name, role=role)
    return _make_user

def test_admin_permissions(make_user):
    admin = make_user(name="admin", role="admin")
    assert admin.can_delete()
```

## Parametrization

### Pattern: Basic Parametrize

Before:
```python
def test_is_even_2():
    assert is_even(2) == True

def test_is_even_3():
    assert is_even(3) == False

def test_is_even_4():
    assert is_even(4) == True
```

After:
```python
@pytest.mark.parametrize("value,expected", [
    (2, True),
    (3, False),
    (4, True),
    (0, True),
    (-2, True),
])
def test_is_even(value: int, expected: bool):
    assert is_even(value) == expected
```

### Pattern: Parametrize with IDs

```python
@pytest.mark.parametrize("input,expected", [
    pytest.param("hello", "HELLO", id="lowercase"),
    pytest.param("WORLD", "WORLD", id="uppercase"),
    pytest.param("MiXeD", "MIXED", id="mixed"),
])
def test_uppercase(input: str, expected: str):
    assert input.upper() == expected
```

### Pattern: Multiple Parametrize (Cartesian Product)

```python
@pytest.mark.parametrize("x", [1, 2])
@pytest.mark.parametrize("y", [10, 20])
def test_multiply(x: int, y: int):
    # Runs 4 tests: (1,10), (1,20), (2,10), (2,20)
    assert x * y == x * y
```

## Mocking Patterns

### Pattern: Mock with auto-spec

Before:
```python
def test_process(mocker):
    mock_client = mocker.Mock()  # No spec - can call anything
    mock_client.non_existent_method()  # No error!
```

After:
```python
def test_process(mocker):
    mock_client = mocker.Mock(spec=Client)  # Type-safe mock
    # mock_client.non_existent_method()  # Would raise AttributeError
```

### Pattern: Patch Object Method

```python
def test_fetch_data(mocker):
    mock_get = mocker.patch.object(
        requests, "get",
        return_value=mocker.Mock(json=lambda: {"data": "test"})
    )

    result = fetch_data("http://example.com")

    mock_get.assert_called_once_with("http://example.com")
    assert result == {"data": "test"}
```

### Pattern: Context Manager Mock

```python
def test_file_processing(mocker):
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="content"))

    result = read_file("test.txt")

    mock_open.assert_called_once_with("test.txt", "r")
    assert result == "content"
```

## Async Testing (pytest-asyncio)

### Pattern: Basic Async Test

```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch():
    result = await fetch_data("http://example.com")
    assert result["status"] == "ok"
```

### Pattern: Async Fixture

```python
import pytest_asyncio

@pytest_asyncio.fixture
async def async_client():
    client = AsyncClient()
    await client.connect()
    yield client
    await client.disconnect()

@pytest.mark.asyncio
async def test_with_client(async_client):
    result = await async_client.fetch("/api/data")
    assert result is not None
```

### Pattern: AsyncMock (Python 3.8+)

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_service(mocker):
    mock_fetch = AsyncMock(return_value={"data": "test"})
    mocker.patch("module.fetch_data", mock_fetch)

    result = await process_data()

    mock_fetch.assert_awaited_once()
    assert result["data"] == "test"
```

### Pattern: AsyncMock with Side Effects

```python
@pytest.mark.asyncio
async def test_retry_on_error(mocker):
    mock_fetch = AsyncMock(side_effect=[
        ConnectionError("First attempt fails"),
        {"data": "success"}  # Second attempt succeeds
    ])
    mocker.patch("module.fetch_data", mock_fetch)

    result = await fetch_with_retry()

    assert mock_fetch.await_count == 2
    assert result["data"] == "success"
```

## Test Naming Convention

### Pattern: Descriptive Test Names

Before:
```python
def test_user():
    ...

def test_error():
    ...
```

After:
```python
def test_should_return_user_when_id_exists():
    ...

def test_should_raise_not_found_when_id_missing():
    ...

def test_should_hash_password_when_creating_user():
    ...
```

## Arrange-Act-Assert Pattern

### Pattern: Clear AAA Structure

```python
def test_should_calculate_total_with_discount():
    # Arrange
    cart = ShoppingCart()
    cart.add_item(Item("Book", price=20.00))
    cart.add_item(Item("Pen", price=5.00))
    discount = Discount(percent=10)

    # Act
    total = cart.calculate_total(discount)

    # Assert
    assert total == 22.50  # (20 + 5) * 0.9
```

## Coverage Configuration

### Pattern: pyproject.toml Coverage Config

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
fail_under = 75
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

## ExceptionGroup Testing (pytest 8.4+)

### Pattern: Test ExceptionGroups with RaisesGroup

```python
import pytest

def test_exception_group():
    with pytest.RaisesGroup(ValueError, TypeError):
        raise ExceptionGroup("errors", [ValueError("bad"), TypeError("wrong")])

# Nested groups
def test_nested_groups():
    with pytest.RaisesGroup(pytest.RaisesGroup(ValueError)):
        raise ExceptionGroup("outer", [ExceptionGroup("inner", [ValueError()])])

# Allow unwrapped exceptions
def test_allow_unwrapped():
    with pytest.RaisesGroup(ValueError, allow_unwrapped=True):
        raise ValueError("just one")  # Not in a group, but allowed
```
