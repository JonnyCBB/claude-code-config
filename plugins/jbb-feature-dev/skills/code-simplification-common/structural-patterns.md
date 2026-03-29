# Structural Patterns

## DRY (Don't Repeat Yourself)

### Pattern: Extract Duplicated Code

Before:
```
void processUserOrder(User user, Order order) {
    log.info("Processing order {} for user {}", order.getId(), user.getId());
    validateUser(user);
    validateOrder(order);
    // ... processing logic
    log.info("Completed order {} for user {}", order.getId(), user.getId());
}

void processGuestOrder(Guest guest, Order order) {
    log.info("Processing order {} for guest {}", order.getId(), guest.getEmail());
    validateGuest(guest);
    validateOrder(order);
    // ... same processing logic duplicated
    log.info("Completed order {} for guest {}", order.getId(), guest.getEmail());
}
```

After:
```
void processOrder(Customer customer, Order order) {
    log.info("Processing order {} for {}", order.getId(), customer.getIdentifier());
    customer.validate();
    validateOrder(order);
    executeOrderProcessing(order);
    log.info("Completed order {} for {}", order.getId(), customer.getIdentifier());
}
```

## Single Responsibility Principle

A class should have only one reason to change.

### Pattern: Split Multi-Responsibility Classes

Before:
```
class OrderService {
    void createOrder(Order order) { ... }
    void validateOrder(Order order) { ... }
    void sendOrderEmail(Order order) { ... }      // Email responsibility
    void generateOrderPdf(Order order) { ... }    // PDF generation responsibility
    void calculateShipping(Order order) { ... }   // Shipping calculation
}
```

After:
```
class OrderService {
    private final OrderValidator validator;
    private final NotificationService notifications;
    private final ShippingCalculator shipping;

    void createOrder(Order order) {
        validator.validate(order);
        // ... core order logic
        notifications.sendOrderConfirmation(order);
    }
}
```

## Method Length: Fit on One Screen

Methods should be ~20 lines or less. If longer, extract sub-methods.

### Pattern: Extract Logical Blocks

Before:
```
void processOrder(Order order) {
    // Validation block (10 lines)
    if (order == null) throw new IllegalArgumentException("Order cannot be null");
    if (order.getItems().isEmpty()) throw new IllegalArgumentException("Order must have items");
    for (Item item : order.getItems()) {
        if (item.getQuantity() <= 0) throw new IllegalArgumentException("Invalid quantity");
        if (item.getPrice() < 0) throw new IllegalArgumentException("Invalid price");
    }

    // Calculation block (15 lines)
    BigDecimal subtotal = BigDecimal.ZERO;
    for (Item item : order.getItems()) {
        subtotal = subtotal.add(item.getPrice().multiply(BigDecimal.valueOf(item.getQuantity())));
    }
    BigDecimal tax = subtotal.multiply(TAX_RATE);
    BigDecimal shipping = calculateShipping(order);
    BigDecimal total = subtotal.add(tax).add(shipping);
    order.setTotal(total);

    // Notification block (10 lines)
    String email = order.getCustomer().getEmail();
    String subject = "Order Confirmation #" + order.getId();
    String body = generateEmailBody(order);
    emailService.send(email, subject, body);
    smsService.send(order.getCustomer().getPhone(), "Order confirmed: " + order.getId());
}
```

After:
```
void processOrder(Order order) {
    validateOrder(order);
    calculateTotals(order);
    sendNotifications(order);
}

private void validateOrder(Order order) {
    checkNotNull(order, "Order cannot be null");
    checkArgument(!order.getItems().isEmpty(), "Order must have items");
    order.getItems().forEach(this::validateItem);
}

private void calculateTotals(Order order) {
    BigDecimal subtotal = calculateSubtotal(order);
    BigDecimal tax = subtotal.multiply(TAX_RATE);
    BigDecimal shipping = calculateShipping(order);
    order.setTotal(subtotal.add(tax).add(shipping));
}

private void sendNotifications(Order order) {
    emailService.sendOrderConfirmation(order);
    smsService.sendOrderConfirmation(order);
}
```

## Cyclomatic Complexity: Limit Nesting

Avoid deeply nested conditionals (max 3 levels).

### Pattern: Early Returns / Guard Clauses

Before:
```
String processRequest(Request request) {
    if (request != null) {
        if (request.isValid()) {
            if (request.hasPermission()) {
                if (request.getType() == RequestType.STANDARD) {
                    return handleStandard(request);
                } else {
                    return handleSpecial(request);
                }
            } else {
                return "No permission";
            }
        } else {
            return "Invalid request";
        }
    } else {
        return "Null request";
    }
}
```

After:
```
String processRequest(Request request) {
    if (request == null) return "Null request";
    if (!request.isValid()) return "Invalid request";
    if (!request.hasPermission()) return "No permission";

    return request.getType() == RequestType.STANDARD
        ? handleStandard(request)
        : handleSpecial(request);
}
```

## Magic Numbers and Strings

Replace literals with named constants.

Before:
```
if (retryCount > 3) { ... }
if (status.equals("ACTIVE")) { ... }
Thread.sleep(5000);
```

After:
```
private static final int MAX_RETRY_ATTEMPTS = 3;
private static final String STATUS_ACTIVE = "ACTIVE";
private static final Duration RETRY_DELAY = Duration.ofSeconds(5);

if (retryCount > MAX_RETRY_ATTEMPTS) { ... }
if (status.equals(STATUS_ACTIVE)) { ... }
Thread.sleep(RETRY_DELAY.toMillis());
```

## Side Effects in Functional Operations Anti-Pattern

Operations like filter, map, and flatMap (Java/Scala streams, Python comprehensions/generators) should be pure — no logging, metric increments, mutations, or I/O. Side effects make pipelines hard to follow, break parallelism assumptions, and mix "what to keep" with "what to observe."

Before (any language):
```
// Filtering AND counting AND logging in one pass
results = items.filter(item -> {
    if (!isValid(item)) {
        counter.increment();     // Side effect!
        log.warn("Invalid: {}", item);  // Side effect!
        return false;
    }
    return true;
});
```

After:
```
// Step 1: Classify (pure)
validItems = items.filter(isValid);

// Step 2: Observe (separate)
int blockedCount = items.size() - validItems.size();
counter.increment(blockedCount);
```

**Applies to**: Java `.filter()`/`.map()`, Scala `.filter`/`.map`/`.collect`, Python list comprehensions and generator expressions.

**When to flag**: Any filter/map/flatMap containing counter increments, log statements, database calls, HTTP requests, or variable mutations.

## Trust Your Framework

Don't re-implement concerns the framework already provides. Common violations:
- Manually managing gRPC `Context` attach/detach when the framework (e.g., Apollo) handles context propagation
- Writing custom retry/backoff logic when the HTTP client or gRPC channel provides it
- Implementing thread pool management when the DI container manages executor lifecycles
- Adding manual request tracing when the framework instruments it automatically

Before:
```
// Manual gRPC context management
Context previous = context.attach();
try {
    return stub.call(request);
} finally {
    context.detach(previous);
}
```

After:
```
// Framework handles context propagation — just make the call
return stub.call(request);
```

**When to flag**: Boilerplate that wraps framework calls with manual lifecycle management. Check the framework's documentation or existing code in the repo to confirm what's already handled.

## Boolean Parameter Anti-Pattern

Avoid methods with boolean parameters that change behavior.

Before:
```
void processOrder(Order order, boolean sendEmail, boolean calculateTax, boolean applyDiscount) {
    // Which combination does what?
}

// Caller:
processOrder(order, true, false, true);  // Unclear what this means
```

After:
```
void processOrder(Order order, OrderOptions options) {
    if (options.shouldSendEmail()) sendEmail(order);
    if (options.shouldCalculateTax()) calculateTax(order);
    if (options.shouldApplyDiscount()) applyDiscount(order);
}

// Caller:
processOrder(order, OrderOptions.builder()
    .sendEmail(true)
    .applyDiscount(true)
    .build());
```

## Dead Code

Remove unused code completely. Don't comment it out.

Before:
```
void processOrder(Order order) {
    // Old implementation - keeping for reference
    // if (order.isLegacy()) {
    //     return processLegacyOrder(order);
    // }

    return processModernOrder(order);
}
```

After:
```
void processOrder(Order order) {
    return processModernOrder(order);
}
```

**Rationale**: Version control (git) preserves history. Commented code becomes outdated and confusing.
