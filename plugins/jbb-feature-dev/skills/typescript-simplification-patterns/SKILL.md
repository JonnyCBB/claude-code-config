---
name: typescript-simplification-patterns
description: TypeScript/React code simplification patterns with before/after examples. Covers anti-patterns to avoid, modern TypeScript 5.0-5.8 features, React 18/19 patterns (use(), Actions, ref as prop), and conventions. Use when reviewing TypeScript/React code quality or identifying refactoring opportunities.
allowed-tools:
  - Read
---

# TypeScript Simplification Patterns

Concrete before/after code transformation examples for TypeScript and React simplification.

## Pattern Categories

- **[Anti-Patterns](anti-patterns.md)**: TypeScript anti-patterns to avoid (`any`, type assertions, non-null assertions)
- **[Modern TypeScript](modern-typescript.md)**: TypeScript 5.0-5.8 features (`satisfies`, `const` type parameters, inferred type predicates, iterator helpers, erasableSyntaxOnly)
- **[React Patterns](react-patterns.md)**: React 18/19 patterns (component typing, hooks, events, context, `use()`, Actions, ref as prop)
- **[Conventions](conventions.md)**: TypeScript/React conventions and guidelines
- **[Testing Patterns](testing-patterns.md)**: Jest, Vitest, RTL, and MSW testing patterns

## Quick Reference

### No `any` Type

Before:

```typescript
function processData(data: any) {
  return data.someProperty;
}
```

After:

```typescript
interface DataShape {
  someProperty: string;
}

function processData(data: DataShape) {
  return data.someProperty;
}
```

### Use `satisfies` for Configuration Objects

Before:

```typescript
const palette: Record<string, string | [number, number, number]> = {
  red: [255, 0, 0],
  green: "#00ff00",
};
// palette.green is string | [number, number, number]
palette.green.toUpperCase(); // Error!
```

After:

```typescript
const palette = {
  red: [255, 0, 0],
  green: "#00ff00",
} satisfies Record<string, string | [number, number, number]>;
// palette.green is specifically string
palette.green.toUpperCase(); // Works!
```

### Regular Functions Over React.FC

Before:

```typescript
const MyComponent: React.FC<Props> = ({ title }) => {
  return <h1>{title}</h1>;
};
```

After:

```typescript
interface Props {
  title: string;
}

function MyComponent({ title }: Props) {
  return <h1>{title}</h1>;
}
```

### Async/Await with Array Methods

Before:

```typescript
// forEach doesn't return a Promise!
await items.forEach(async (item) => {
  await processItem(item);
});
```

After:

```typescript
// Sequential processing
for (const item of items) {
  await processItem(item);
}

// Parallel processing
await Promise.all(items.map((item) => processItem(item)));
```

For complete patterns with detailed examples, see the category files above.

## Conventions Used in Examples

All examples follow these TypeScript conventions:

- **TypeScript Version**: 5.x (modern features enabled)
- **Strict Mode**: Enabled (`strict: true` in tsconfig.json)
- **No `any`**: Use `unknown` or specific types
- **Props Naming**: `ComponentNameProps` convention
- **Components**: Regular functions preferred over `React.FC`
- **Imports**: Named exports preferred, avoid default exports (except Next.js pages)

See the language-agnostic patterns in `code-simplification-common` for naming conventions and structural patterns (DRY, SOLID).
