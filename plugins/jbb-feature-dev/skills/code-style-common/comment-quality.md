# Comment Quality

## WHY, Not WHAT

Comments should explain reasoning, not describe what the code does.

### Pattern: Explain Intent

Before:
```
// Loop through users
for (User user : users) {
    // Check if user is active
    if (user.isActive()) {
        // Add to result list
        result.add(user);
    }
}
```

After:
```
// Filter to active users only - inactive users are pending deletion
// and should not appear in search results (see JIRA-1234)
List<User> activeUsers = users.stream()
    .filter(User::isActive)
    .toList();
```

## Self-Documenting Code

Clear naming reduces the need for comments.

### Pattern: Replace Comments with Clear Names

Before:
```
// Calculate the total price including tax and shipping
double calc(Order o) {
    double st = 0;  // subtotal
    for (Item i : o.items) {
        st += i.p * i.q;  // price * quantity
    }
    double t = st * 0.08;  // tax at 8%
    double s = st > 100 ? 0 : 5.99;  // free shipping over $100
    return st + t + s;
}
```

After:
```
Money calculateTotalPrice(Order order) {
    Money subtotal = calculateSubtotal(order);
    Money tax = calculateTax(subtotal);
    Money shipping = calculateShipping(subtotal);
    return subtotal.add(tax).add(shipping);
}

private Money calculateTax(Money subtotal) {
    return subtotal.multiply(TAX_RATE);
}

private Money calculateShipping(Money subtotal) {
    return subtotal.isGreaterThan(FREE_SHIPPING_THRESHOLD)
        ? Money.ZERO
        : STANDARD_SHIPPING_COST;
}
```

## Inaccurate Comments

Comments that describe intended behavior rather than actual behavior. Unlike outdated comments (which were once accurate), these were never correct — often introduced when copying patterns from other classes without verifying the comment still applies.

Before:
```
private void fireCounterfactualComparison(...) {
    try {
      // Execute the comparison in a separate gRPC context to detach it
      // from the incoming request and make it a fire-and-forget.
      io.grpc.Context.current()
          .fork()
          .run(() -> {
              // ... chains futures ...
              .toCompletableFuture()
              .join();  // Actually blocks the calling thread!
          });
```

After (option 1 — fix the comment):
```
private void fireCounterfactualComparison(...) {
    try {
      // Execute the comparison in a forked gRPC context. The join() call
      // blocks until both primary and counterfactual complete, so request
      // latency = max(primary, counterfactual).
      io.grpc.Context.current()
          .fork()
          .run(() -> {
```

After (option 2 — fix the code to match the intent):
```
private void fireCounterfactualComparison(...) {
    try {
      // Fire-and-forget: chain the comparison without blocking
      CompletionStage<SearchResponse> counterfactualResponse = ...;
      primaryResponse
          .thenCombine(counterfactualResponse, ...)
          .exceptionally(...);
      // No join() — let the combined future complete independently
```

**When to flag**: Comments containing terms like "fire-and-forget", "non-blocking", "async", or "independent" near code that blocks (`join()`, `get()`, `await`), or vice versa. Also flag when copying a pattern from another class — verify the accompanying comments match the new context.

## Outdated Comments

Outdated comments are worse than no comments.

Before:
```
// Returns the user's full name (first + last)
String getUserDisplayName(User user) {
    // Actually now returns nickname if set, otherwise email
    return user.getNickname() != null
        ? user.getNickname()
        : user.getEmail();
}
```

After:
```
String getUserDisplayName(User user) {
    return user.getNickname() != null
        ? user.getNickname()
        : user.getEmail();
}
```

Or if context is needed:
```
/**
 * Returns the user's preferred display name.
 * Falls back to email if no nickname is set.
 */
String getUserDisplayName(User user) {
    return Optional.ofNullable(user.getNickname())
        .orElse(user.getEmail());
}
```

## TODO Hygiene

TODOs should have owners or ticket references.

Before:
```
// TODO: fix this later
// TODO: refactor
// TODO: handle edge case
```

After:
```
// TODO(jsmith): Handle pagination - JIRA-5678
// TODO(@team-platform): Migrate to new API before Q3 deprecation
```

Or better: Create a ticket and remove the TODO.

## API Documentation

Public APIs need clear contracts.

### Pattern: Document Contracts, Not Implementation

Before:
```
/**
 * This method finds a user. It queries the database
 * using a SELECT statement with the id parameter.
 * Then it maps the ResultSet to a User object.
 */
User findById(Long id);
```

After:
```
/**
 * Finds a user by their unique identifier.
 *
 * @param id the user's unique identifier, must not be null
 * @return the user if found
 * @throws UserNotFoundException if no user exists with the given id
 * @throws IllegalArgumentException if id is null
 */
User findById(Long id);
```
