# Comment Format

Standard format for review comments. Each comment should be self-contained and written in a friendly, collegial tone — as if talking to a teammate.

## Format Template

```
<label> (<blocking|non-blocking>): <subject>

<explanation using "we" language>

**Suggestion**: <specific fix>
```

## Labels

| Label | When to use | Blocking? |
|-------|------------|-----------|
| `issue` | Specific problem that needs fixing | Usually blocking |
| `suggestion` | Proposes an improvement | Usually non-blocking |
| `nit` | Trivial preference, style choice | Always non-blocking |
| `question` | Seeking clarification, not requesting change | Non-blocking |
| `praise` | Something done well — aim for at least one per review | Non-blocking |

## Severity-to-Label Mapping

When converting code-review findings to PR comments:

| Finding Severity | Label | Decoration |
|-----------------|-------|------------|
| CRITICAL | `issue` | `(blocking)` |
| HIGH | `issue` | `(blocking)` |
| MEDIUM | `suggestion` | `(non-blocking)` |
| LOW | `nit` | `(non-blocking)` |
| ENHANCEMENT | `suggestion` | `(non-blocking)` |
| Positive finding | `praise` | — |

## Tone Rules

1. **Use "we" not "you"**: "Can we add a null check here?" not "You should add a null check"
2. **Questions not demands**: "Have we considered X?" not "Do X"
3. **Explain the why**: Include the impact or risk, not just the problem
4. **Be concrete**: Describe realistic failure scenarios, not theoretical ones
5. **One issue per comment**: Don't combine unrelated issues
6. **At least one praise per review**: Reinforce good patterns

## Examples

### Friendly issue (blocking)

```
issue (blocking): `processOrder()` doesn't check whether `order.items` is null before
iterating, but `OrderService.getOrder()` returns null items for cancelled orders.

If a cancelled order hits this path during batch reprocessing, we'd get a
NullPointerException that halts all subsequent orders in the batch.

**Suggestion**: Can we add a null guard before the loop?
`if (order.items == null) { return Collections.emptyList(); }`
```

### Friendly suggestion (non-blocking)

```
suggestion (non-blocking): This connection isn't closed in the error path, which could
lead to pool exhaustion under repeated failures.

Have we considered wrapping this in a try-with-resources block? That way we'd be safe
even if a new error path gets added later.
```

### Friendly nit

```
nit (non-blocking): Minor naming thought — `data` is pretty generic here. Something like
`userEvents` might make this easier to follow at a glance. Totally up to you though!
```

### Praise

```
praise: Nice use of the builder pattern here — keeps the construction readable even with
all these optional fields. The validation in `build()` is a great touch too.
```

### Question

```
question (non-blocking): I'm not sure I follow the intent here — are we intentionally
skipping retry for 4xx errors? If so, might be worth a brief comment explaining why,
since the retry logic for 5xx is right above.
```

## Security Variant

For security findings, the same friendly tone applies but be specific about the attack vector:

```
issue (blocking): The user-supplied `filename` parameter is passed directly to
`File.open()` without path traversal sanitization.

An attacker could supply `../../etc/passwd` to read files outside the uploads directory.
Can we validate the resolved path stays within the allowed base using
`Path.resolve().startsWith(allowedBase)`?
```

## Guidelines

- Be specific — reference exact variable names, method names, and line numbers
- Be concrete — describe realistic failure scenarios, not theoretical ones
- Be actionable — provide a fix, not just a complaint
- Be concise — focused paragraphs, not rambling
- Be kind — you're talking to a colleague, not filing a bug report
