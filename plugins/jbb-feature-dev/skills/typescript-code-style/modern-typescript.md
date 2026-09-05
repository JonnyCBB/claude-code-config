# Modern TypeScript Features (5.x)

Modern TypeScript features that improve type safety and developer experience.

## TypeScript 4.9+: Satisfies Operator

Validates type while preserving specific inferred types.

### Pattern: Configuration Objects with `satisfies`

Before:
```typescript
const palette: Record<string, string | [number, number, number]> = {
  red: [255, 0, 0],
  green: '#00ff00'
};
// palette.green is string | [number, number, number]
palette.green.toUpperCase(); // Error! Could be array
```

After:
```typescript
const palette = {
  red: [255, 0, 0],
  green: '#00ff00'
} satisfies Record<string, string | [number, number, number]>;
// palette.green is specifically string
palette.green.toUpperCase(); // Works!
// palette.red is specifically [number, number, number]
palette.red[0]; // Works! Type is number
```

**Why**: `satisfies` validates the type while preserving literal inference.

### Pattern: Route Configuration

Before:
```typescript
const routes: Record<string, { path: string; auth: boolean }> = {
  home: { path: '/', auth: false },
  dashboard: { path: '/dashboard', auth: true }
};
// routes.home.path is just "string", not "/"
```

After:
```typescript
const routes = {
  home: { path: '/', auth: false },
  dashboard: { path: '/dashboard', auth: true }
} satisfies Record<string, { path: string; auth: boolean }>;
// routes.home.path is "/"
// routes.dashboard.auth is true (literal)
```

## TypeScript 5.0: Const Type Parameters

Preserves literal types without `as const`.

### Pattern: Generic Functions with Literal Preservation

Before:
```typescript
function getRoutes<T extends readonly string[]>(routes: T) {
  return routes;
}
// Must use as const
const routes = getRoutes(['home', 'about'] as const);
// Type: readonly ["home", "about"]
```

After:
```typescript
function getRoutes<const T extends readonly string[]>(routes: T) {
  return routes;
}
// No as const needed!
const routes = getRoutes(['home', 'about']);
// Type: readonly ["home", "about"]
```

**Why**: The `const` modifier on type parameters preserves literal types automatically.

### Pattern: Factory Functions

Before:
```typescript
function createConfig<T extends object>(config: T): T {
  return config;
}
const config = createConfig({ mode: 'dark', size: 'large' } as const);
```

After:
```typescript
function createConfig<const T extends object>(config: T): T {
  return config;
}
const config = createConfig({ mode: 'dark', size: 'large' });
// config.mode is 'dark' (literal), not string
```

## TypeScript 5.4: NoInfer Utility Type

Prevents inference from specific type parameters.

### Pattern: Default Values Without Type Pollution

Before:
```typescript
function createState<T>(initial: T, defaultValue: T): T {
  return initial ?? defaultValue;
}
// defaultValue contributes to T inference, potentially widening it
createState(42, 0); // T is number (good)
createState(42 as const, 0); // T is 42 | 0 (unexpected)
```

After:
```typescript
function createState<T>(initial: T, defaultValue: NoInfer<T>): T {
  return initial ?? defaultValue;
}
// defaultValue doesn't contribute to T inference
createState(42, 0); // T is number
createState(42 as const, 0); // Error! 0 is not 42
```

**Why**: `NoInfer<T>` prevents type widening from secondary parameters.

### Pattern: Fallback Values

```typescript
function coalesce<T>(value: T | null, fallback: NoInfer<T>): T {
  return value ?? fallback;
}

const result = coalesce('hello', 'default'); // T inferred from first arg only
```

## TypeScript 5.5: Inferred Type Predicates

TypeScript automatically infers type guards in many cases.

### Pattern: Automatic Type Guard Inference

Before:
```typescript
// Had to write explicit type predicate
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

const values: (string | number)[] = ['a', 1, 'b', 2];
const strings = values.filter(v => typeof v === 'string');
// Type: (string | number)[] - NOT narrowed in TS < 5.5
```

After:
```typescript
// Type predicate automatically inferred in TS 5.5+
function isString(value: unknown) {
  return typeof value === 'string';
} // Predicate `value is string` inferred automatically!

const values: (string | number)[] = ['a', 1, 'b', 2];
const strings = values.filter(v => typeof v === 'string');
// Type: string[] - Properly narrowed in TS 5.5+
```

**Why**: Less boilerplate for type guards; filter() now narrows types automatically.

### Pattern: Filter Out Nullish Values

Before:
```typescript
const items: (string | undefined)[] = ['a', undefined, 'b'];
const defined = items.filter((x): x is string => x !== undefined);
```

After (TS 5.5+):
```typescript
const items: (string | undefined)[] = ['a', undefined, 'b'];
const defined = items.filter(x => x !== undefined);
// Type: string[] - Automatically narrowed!
```

## Type Inference Best Practices

### Pattern: Annotate at Boundaries, Let Inference Work

Before (over-annotated):
```typescript
const numbers: number[] = [1, 2, 3];
const doubled: number[] = numbers.map((n: number): number => n * 2);
const sum: number = doubled.reduce((a: number, b: number): number => a + b, 0);
```

After:
```typescript
const numbers = [1, 2, 3]; // Inferred as number[]
const doubled = numbers.map(n => n * 2); // Inferred correctly
const sum = doubled.reduce((a, b) => a + b, 0); // Inferred as number

// DO annotate at module boundaries
export function processNumbers(input: number[]): number[] {
  return input.map(n => n * 2);
}
```

**Why**: Excessive annotations add noise. TypeScript's inference is excellent for local variables.

### Pattern: Use Utility Types

```typescript
interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

// Partial - all properties optional (for updates)
type UpdateUserDto = Partial<User>;

// Pick - select specific properties
type UserPreview = Pick<User, 'id' | 'name'>;

// Omit - exclude specific properties (for creation)
type CreateUserDto = Omit<User, 'id' | 'createdAt'>;

// Readonly - immutable version
type ImmutableUser = Readonly<User>;

// Record - typed object
type UsersByRole = Record<string, User[]>;

// Required - make all properties required
type CompleteUser = Required<Partial<User>>;
```

### Pattern: Generic Constraints

```typescript
interface Identifiable {
  id: string;
}

// Constrain T to have an id property
function updateEntity<T extends Identifiable>(
  entity: T,
  updates: Partial<Omit<T, 'id'>>
): T {
  return { ...entity, ...updates };
}

// Using keyof for property access
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { name: 'Alice', age: 30 };
const name = getProperty(user, 'name'); // Type: string
const age = getProperty(user, 'age'); // Type: number
```

## TypeScript 5.6: Safety Improvements

### Disallowed Truthy/Nullish Checks

Catches common bugs where expressions are always truthy or always nullish.

```typescript
// Error: This kind of expression is always truthy.
if (/0x[0-9a-f]/) {
    // Forgot to call .test()
}

// Error: Right operand of ?? is unreachable (operator precedence)
const x = value < options.max ?? 100;

// Error: This kind of expression is always truthy.
if (x => 0) {
    // Used arrow function syntax instead of comparison >=
}
```

**Note**: Certain literals like `true`, `false`, `0`, `1` remain allowed since patterns like `while (true)` are idiomatic.

### Iterator Helper Methods

Functional operations on generators, enabling composable lazy iteration.

```typescript
function* positiveIntegers() {
    let i = 1;
    while (true) yield i++;
}

const first5Even = positiveIntegers()
    .map(x => x * 2)
    .take(5)
    .toArray();
// [2, 4, 6, 8, 10]
```

Available methods: `.map()`, `.filter()`, `.take()`, `.drop()`, `.flatMap()`, `.reduce()`, `.toArray()`, `.forEach()`, `.some()`, `.every()`, `.find()`.

## TypeScript 5.7: Stricter Checks

### Never-Initialized Variable Checks

```typescript
function foo() {
    let result: number;
    // Forgot to assign in some branch

    function printResult() {
        console.log(result);
        // ^ Error: Variable 'result' is used before being assigned.
    }
}
```

**Why**: Previously TypeScript took an "optimistic" view for variables accessed in nested functions. Now it catches this.

## TypeScript 5.8: Node.js Compatibility

### `--erasableSyntaxOnly`

Ensures code uses only erasable TypeScript constructs for Node.js type-stripping.

```typescript
// Disallowed with --erasableSyntaxOnly:
enum Status { Active }                    // Error: generates runtime code
class Point { constructor(public x: number) {} } // Error: parameter property

// Use instead:
const Status = { Active: 'ACTIVE' } as const;
type Status = typeof Status[keyof typeof Status];

class Point {
    x: number;
    constructor(x: number) { this.x = x; }
}
```

**Why**: Node.js 23.6+ supports running TypeScript directly by stripping types. This flag ensures all TS constructs can be cleanly erased.

### Granular Return-Branch Checks

```typescript
declare const cache: Map<string, unknown>;

function getUrlObject(urlString: string): URL {
    return cache.has(urlString) ?
        cache.get(urlString) :  // unknown (from Map)
        urlString;              // Error! string is not URL
    // Previously passed because the union collapsed to 'any'
}
```

**Why**: Each branch of a conditional return is now checked individually, preventing `any` from one branch swallowing errors in another.
