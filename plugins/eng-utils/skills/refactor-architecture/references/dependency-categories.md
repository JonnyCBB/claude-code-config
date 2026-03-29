# Dependency Categories for Module Deepening

## Table of Contents

- [Introduction](#introduction)
- [Category 1: In-Process](#category-1-in-process)
- [Category 2: Local-Substitutable](#category-2-local-substitutable)
- [Category 3: Remote but Owned (Ports & Adapters)](#category-3-remote-but-owned-ports--adapters)
- [Category 4: True External (Mock)](#category-4-true-external-mock)
- [Key Testing Principle](#key-testing-principle)
- [Quick Reference Matrix](#quick-reference-matrix)

---

## Introduction

When classifying a refactoring candidate's dependencies, use these four categories to determine the testing and deepening strategy. Each category describes how a dependency relates to the module boundary and dictates what test infrastructure you need. Categories are ordered from easiest to deepest integration effort -- start by looking for in-process dependencies before reaching for mocks.

---

## Category 1: In-Process

### Definition

Pure computation and in-memory state with no I/O, no network calls, and no filesystem access. The dependency lives entirely within the same process and produces deterministic results.

### When it applies

- The dependency is a utility function, data transformer, or business logic calculator
- All inputs and outputs are plain data structures (no handles, connections, or streams)
- No `import` of networking, database, or filesystem libraries
- The function is side-effect free or mutates only local state

### Testing strategy

Merge the modules and test directly. No test doubles needed. Write boundary tests that call the deepened module's public interface and assert on returned values.

### Before/After example

**Before -- two shallow modules with a leaky abstraction:**

```
// Module: PriceCalculator
function calculatePrice(basePrice, discountPercent):
    return basePrice * (1 - discountPercent / 100)

// Module: OrderService
function createOrder(items):
    subtotal = sum(items.map(i => i.price))
    discount = lookupDiscountPercent(items)
    total = PriceCalculator.calculatePrice(subtotal, discount)
    tax = subtotal * TAX_RATE
    return Order(items, total + tax)
```

**After -- one deep module that hides the pricing logic:**

```
// Module: OrderService (deepened -- PriceCalculator merged in)
function createOrder(items):
    subtotal = sum(items.map(i => i.price))
    discount = lookupDiscountPercent(items)
    discountedSubtotal = subtotal * (1 - discount / 100)
    tax = discountedSubtotal * TAX_RATE
    return Order(items, discountedSubtotal + tax)

// Test
test "order applies bulk discount and tax":
    items = [Item(price=100), Item(price=200)]
    order = createOrder(items)
    assert order.total == expectedValue
```

---

## Category 2: Local-Substitutable

### Definition

Dependencies that require I/O but have a local, in-process test stand-in that behaves like the real thing. The stand-in is not a mock -- it is a real implementation running locally with the same query semantics.

### When it applies

- The dependency is a database, cache, or storage system with an embeddable or in-memory mode
- A lightweight local implementation exists that honors the same API contract
- Examples: PGLite for Postgres, SQLite for relational queries, in-memory filesystem, embedded database, embedded Redis, testcontainers
- The stand-in starts fast enough to run in a unit test suite (under 5 seconds)

### Testing strategy

Deepen the module so it owns the query logic internally. Run tests with the local stand-in started in the test setup. Assert on observable outcomes through the public interface -- not on SQL statements or cache keys.

### Before/After example

**Before -- shallow repository layer that leaks query details:**

```
// Module: UserRepository
function findActiveUsers(db):
    return db.query("SELECT * FROM users WHERE active = true")

// Module: UserService
function getActiveUserEmails():
    users = UserRepository.findActiveUsers(db)
    return users.map(u => u.email)
```

**After -- deep module that hides storage details:**

```
// Module: UserService (deepened -- repository merged in)
function getActiveUserEmails(storage):
    users = storage.query("SELECT email FROM users WHERE active = true")
    return users.map(u => u.email)

// Test (using PGLite / embedded database / embedded store)
test "returns emails of active users only":
    storage = startLocalStore()
    storage.insert(User(email="a@b.com", active=true))
    storage.insert(User(email="c@d.com", active=false))

    emails = getActiveUserEmails(storage)

    assert emails == ["a@b.com"]
    stopLocalStore(storage)
```

An embedded database lets you test read/write logic without a remote cluster:

```
store = EmbeddedDatabase.inMemory(schema)
store.put(key, value)
result = store.get(key)
assert result == value
```

---

## Category 3: Remote but Owned (Ports & Adapters)

### Definition

Dependencies that cross a network boundary to services your team or organization owns. You control both sides of the contract but cannot run the remote service locally.

### When it applies

- The dependency is a gRPC service, internal REST API, Kafka topic, or internal queue
- Your team owns (or can negotiate changes to) the remote service's contract
- Latency, retries, and partial failures are part of the real behavior
- No embeddable or in-memory stand-in exists for the remote service
- Examples: calls to internal gRPC services, Kafka consumers/producers, internal pub/sub

### Testing strategy

Define a port (interface) at the module boundary that describes what the module needs, not how the remote service works. Implement two adapters: an in-memory adapter for tests and a real HTTP/gRPC/queue adapter for production. The deep module owns all the business logic; transport is injected.

### Before/After example

**Before -- shallow module that mixes business logic with gRPC transport:**

```
// Module: RecommendationService
function getRecommendations(userId):
    profile = GrpcClient.call("user-profile-service", GetProfile(userId))
    history = GrpcClient.call("listening-history-service", GetHistory(userId))
    candidates = filterByGenre(history, profile.preferredGenres)
    return rankByRecency(candidates)
```

**After -- deep module with a port for the data it needs:**

```
interface UserDataPort:
    function getProfile(userId) -> Profile
    function getListeningHistory(userId) -> List<Track>

function getRecommendations(userId, userDataPort):
    profile = userDataPort.getProfile(userId)
    history = userDataPort.getListeningHistory(userId)
    return rankByRecency(filterByGenre(history, profile.preferredGenres))

// In-memory adapter (for tests)
class InMemoryUserDataAdapter implements UserDataPort:
    profiles = {}
    histories = {}
    function getProfile(userId): return profiles[userId]
    function getListeningHistory(userId): return histories[userId]

// Production adapter
class GrpcUserDataAdapter implements UserDataPort:
    function getProfile(userId): return grpcCall("user-profile-service", GetProfile(userId))
    function getListeningHistory(userId): return grpcCall("listening-history-service", GetHistory(userId))

test "recommends tracks matching preferred genres":
    adapter = InMemoryUserDataAdapter()
    adapter.profiles["user1"] = Profile(preferredGenres=["jazz"])
    adapter.histories["user1"] = [Track(genre="jazz", date=yesterday), Track(genre="metal", date=today)]
    recs = getRecommendations("user1", adapter)
    assert all(r.genre == "jazz" for r in recs)
```

Kafka consumers follow the same pattern: define a port for "message source," use an in-memory queue in tests, and inject the real Kafka consumer in production.

---

## Category 4: True External (Mock)

### Definition

Third-party services and APIs you do not own and cannot modify. The external party controls the contract, uptime, and behavior.

### When it applies

- The dependency is a third-party API (Stripe, Twilio, external partner APIs)
- You cannot change the remote service's contract or behavior
- The service has rate limits, authentication, or usage costs that make real calls impractical in tests

### Testing strategy

Inject the external dependency as a port, just like Category 3. The difference is that you mock the port implementation in tests because no local stand-in or owned adapter exists. Keep the mock minimal -- only model the behaviors your module actually depends on. Validate real integration separately in contract tests or a staging environment.

### Before/After example

**Before -- shallow module with payment logic scattered across layers:**

```
// Module: PaymentValidator
function validateCard(cardToken):
    return StripeSDK.validateToken(cardToken)

// Module: PaymentService
function processPayment(order, cardToken):
    isValid = PaymentValidator.validateCard(cardToken)
    if not isValid: raise InvalidCardError
    charge = StripeSDK.charge(cardToken, order.total)
    if charge.status == "failed": raise PaymentFailedError
    return Receipt(order.id, charge.id, order.total)
```

**After -- deep module with an injected payment gateway port:**

```
interface PaymentGatewayPort:
    function validateToken(token) -> bool
    function charge(token, amount) -> ChargeResult

function processPayment(order, cardToken, gateway):
    if not gateway.validateToken(cardToken): raise InvalidCardError
    charge = gateway.charge(cardToken, order.total)
    if charge.status == "failed": raise PaymentFailedError
    return Receipt(order.id, charge.id, order.total)

// Mock -- only models behaviors the module depends on
class MockPaymentGateway implements PaymentGatewayPort:
    shouldValidate = true
    chargeStatus = "succeeded"
    function validateToken(token): return shouldValidate
    function charge(token, amount): return ChargeResult(id="mock-123", status=chargeStatus)

test "returns receipt on successful payment":
    gateway = MockPaymentGateway()
    receipt = processPayment(Order(id="o1", total=50), "tok_valid", gateway)
    assert receipt.orderId == "o1" and receipt.amount == 50

test "raises error when charge fails":
    gateway = MockPaymentGateway(chargeStatus="failed")
    assertThrows PaymentFailedError:
        processPayment(Order(id="o1", total=50), "tok_valid", gateway)
```

---

## Key Testing Principle

**Replace, don't layer.** When you deepen a module, delete the shallow unit tests that tested the now-internal pieces individually. The boundary tests through the public interface replace them. Tests assert on observable outcomes (return values, side effects on injected ports, thrown errors) -- never on internal state, private method calls, or implementation details.

If you find yourself writing a test that reaches into the module to inspect internal variables, the module boundary is in the wrong place.

---

## Quick Reference Matrix

| Category            | I/O?      | Test Double         | Deepening Effort             | Example                      |
| ------------------- | --------- | ------------------- | ---------------------------- | ---------------------------- |
| In-process          | None      | None needed         | Merge and test directly      | Business logic, transformers |
| Local-substitutable | Local I/O | Real local stand-in | Start stand-in in test setup | Embedded database, PGLite    |
| Remote but owned    | Network   | In-memory adapter   | Define port + two adapters   | gRPC services, Kafka         |
| True external       | Network   | Mock                | Define port + mock           | Stripe, Twilio, partner APIs |

**Decision flow:**

1. Can you eliminate the dependency by merging? Use **In-process**.
2. Does a local stand-in exist? Use **Local-substitutable**.
3. Do you own the remote service? Use **Ports & Adapters**.
4. Otherwise, use **Mock**.
