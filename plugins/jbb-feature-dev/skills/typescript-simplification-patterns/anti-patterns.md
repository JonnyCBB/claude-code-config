# TypeScript Anti-Patterns

Common TypeScript anti-patterns to avoid, with before/after examples.

## Anti-Pattern 1: Overusing the `any` Type

The most prevalent anti-pattern that defeats TypeScript's purpose.

### Pattern: Use Specific Types Instead of `any`

Before:
```typescript
function processData(data: any) {
  return data.someProperty; // No type safety
}

function handleResponse(response: any) {
  console.log(response.data.users[0].name); // Could crash at runtime
}
```

After:
```typescript
interface DataShape {
  someProperty: string;
}

function processData(data: DataShape) {
  return data.someProperty; // Type-safe
}

interface User {
  name: string;
}

interface ApiResponse {
  data: {
    users: User[];
  };
}

function handleResponse(response: ApiResponse) {
  console.log(response.data.users[0].name); // Type-safe
}
```

### Pattern: Use `unknown` for Truly Unknown Types

Before:
```typescript
function parseJSON(input: string): any {
  return JSON.parse(input);
}
```

After:
```typescript
function parseJSON(input: string): unknown {
  return JSON.parse(input);
}

// Caller must narrow the type
const result = parseJSON('{"name": "Alice"}');
if (typeof result === 'object' && result !== null && 'name' in result) {
  console.log((result as { name: string }).name);
}

// Or use a validation library like Zod
import { z } from 'zod';

const UserSchema = z.object({
  name: z.string(),
  email: z.string().email()
});

const user = UserSchema.parse(result); // Validated and typed
```

**Why**: `unknown` forces explicit type narrowing, catching errors at compile time.

### Pattern: Typed Catch Blocks (TypeScript 4.4+)

Before:
```typescript
try {
  await fetchData();
} catch (e: any) {
  setError(e.message); // Runtime crash if e isn't an Error
}
```

After:
```typescript
try {
  await fetchData();
} catch (e: unknown) {
  setError(e instanceof Error ? e.message : 'Unknown error');
}

// Or with a type guard for reuse
function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  return 'Unknown error';
}

try {
  await fetchData();
} catch (e: unknown) {
  setError(getErrorMessage(e));
}
```

**Why**: TypeScript 4.4+ supports `unknown` in catch clauses. This is now the recommended pattern as it forces explicit type checking before accessing error properties.

## Anti-Pattern 2: Overusing Type Assertions

Type assertions let you "lie" to TypeScript about types, bypassing safety.

### Pattern: Validate Instead of Assert

Before:
```typescript
const user = apiResponse as User; // Properties might be missing!

const element = event.target as HTMLInputElement;
element.value; // Could crash if not an input
```

After:
```typescript
// Use runtime validation
import { z } from 'zod';

const UserSchema = z.object({
  name: z.string(),
  email: z.string().email()
});

const user = UserSchema.parse(apiResponse); // Throws if invalid

// Use type guards for DOM elements
function isInputElement(target: EventTarget | null): target is HTMLInputElement {
  return target instanceof HTMLInputElement;
}

if (isInputElement(event.target)) {
  event.target.value; // Type-safe
}
```

### Pattern: Narrow Types with Type Guards

Before:
```typescript
function process(input: string | number | null) {
  const str = input as string; // Dangerous!
  return str.toUpperCase();
}
```

After:
```typescript
function process(input: string | number | null) {
  if (typeof input === 'string') {
    return input.toUpperCase(); // Narrowed to string
  }
  if (typeof input === 'number') {
    return input.toFixed(2); // Narrowed to number
  }
  return null;
}
```

**Why**: Type guards provide runtime safety while narrowing types correctly.

## Anti-Pattern 3: Non-null Assertions (`!` operator)

Tells TypeScript a value isn't null without checking.

### Pattern: Use Optional Chaining or Null Checks

Before:
```typescript
const element = document.getElementById('myId')!;
element.innerHTML = 'Hello'; // Will crash if element doesn't exist

const user = getUser()!;
console.log(user.name); // Could crash
```

After:
```typescript
// Optional chaining for simple access
document.getElementById('myId')?.innerHTML = 'Hello';

// Explicit null check when you need to use the value
const element = document.getElementById('myId');
if (element) {
  element.innerHTML = 'Hello';
}

// Early return pattern
const user = getUser();
if (!user) {
  throw new Error('User not found');
}
console.log(user.name); // TypeScript knows user is not null here
```

**Why**: Optional chaining and null checks handle missing values gracefully.

### Pattern: Guard Clauses for Optional Callbacks

Before:
```typescript
interface Props {
  items: Item[];
  onDelete?: (id: string) => void;
  onEdit?: (id: string, text: string) => void;
}

function ItemList({ items, onDelete, onEdit }: Props) {
  return (
    <ul>
      {items.map(item => (
        <li key={item.id}>
          {item.name}
          <button onClick={() => onDelete!(item.id)}>Delete</button>
          <button onClick={() => onEdit!(item.id, item.name)}>Edit</button>
        </li>
      ))}
    </ul>
  );
}
```

After:
```typescript
function ItemList({ items, onDelete, onEdit }: Props) {
  return (
    <ul>
      {items.map(item => (
        <li key={item.id}>
          {item.name}
          {onDelete && (
            <button onClick={() => onDelete(item.id)}>Delete</button>
          )}
          {onEdit && (
            <button onClick={() => onEdit(item.id, item.name)}>Edit</button>
          )}
        </li>
      ))}
    </ul>
  );
}
```

**Why**: Guard clauses eliminate the need for non-null assertions while also providing correct UI behavior—buttons only appear when handlers are provided.

## Anti-Pattern 4: forEach with Async Callbacks

Array.forEach doesn't return a Promise, so await does nothing.

### Pattern: Use for...of or Promise.all

Before:
```typescript
// This doesn't wait for operations to complete!
await items.forEach(async (item) => {
  await processItem(item);
});
console.log('Done!'); // Runs before processing completes
```

After:
```typescript
// Sequential processing (when order matters)
for (const item of items) {
  await processItem(item);
}
console.log('Done!'); // Runs after all items processed

// Parallel processing (when order doesn't matter)
await Promise.all(items.map(async (item) => processItem(item)));
console.log('Done!'); // Runs after all items processed
```

**Why**: `forEach` doesn't understand Promises. Use proper async patterns.

## Anti-Pattern 5: Implicit Return Confusion

Arrow functions with implicit returns can cause unexpected behavior.

### Pattern: Use Explicit Braces for Void Returns

Before:
```typescript
// Returns the result of setCount, which might cause issues
<NumberInput onChange={() => setCount(count + 1)} />

// Accidentally returns a Promise
button.addEventListener('click', () => fetch('/api/data'));
```

After:
```typescript
// Explicit void return with curly braces
<NumberInput onChange={() => { setCount(count + 1); }} />

// Explicit handling of async operations
button.addEventListener('click', () => {
  void fetch('/api/data'); // Explicitly ignore Promise
});

// Or handle the Promise properly
button.addEventListener('click', async () => {
  try {
    await fetch('/api/data');
  } catch (error) {
    console.error('Failed to fetch:', error);
  }
});
```

**Why**: Implicit returns can cause unexpected behavior, especially with event handlers.

## Anti-Pattern 6: Enum Misuse

Modern TypeScript has better alternatives to enums.

### Pattern: Use `as const` Objects

Before:
```typescript
enum Status {
  Active = 'ACTIVE',
  Inactive = 'INACTIVE',
  Pending = 'PENDING'
}

function setStatus(status: Status) {
  console.log(status);
}

setStatus(Status.Active);
```

After:
```typescript
const Status = {
  Active: 'ACTIVE',
  Inactive: 'INACTIVE',
  Pending: 'PENDING'
} as const;

type Status = typeof Status[keyof typeof Status];

function setStatus(status: Status) {
  console.log(status);
}

setStatus(Status.Active);
// Or use literal directly:
setStatus('ACTIVE');
```

**Why**: `as const` objects are more flexible, tree-shakeable, and don't have enum's runtime quirks.

### Pattern: Use Union Types for Simple Cases

Before:
```typescript
enum Direction {
  Up = 'UP',
  Down = 'DOWN',
  Left = 'LEFT',
  Right = 'RIGHT'
}
```

After:
```typescript
type Direction = 'UP' | 'DOWN' | 'LEFT' | 'RIGHT';
```

**Why**: Union types are simpler and don't generate runtime code.

## Anti-Pattern 7: Interface vs Type Misuse

Use the right tool for the job.

### Guidelines

**Use Interfaces for:**
- Object shapes, especially when extending or implementing
- Public API contracts that others might extend
- Declaration merging needs

```typescript
// Interface for object shapes
interface User {
  id: string;
  name: string;
}

// Interface extension
interface Admin extends User {
  permissions: string[];
}

// Implementation
class UserImpl implements User {
  constructor(public id: string, public name: string) {}
}
```

**Use Types for:**
- Unions and intersections
- Primitives and tuples
- Complex type transformations
- Function types

```typescript
// Union types
type Status = 'active' | 'inactive' | 'pending';

// Intersection types
type UserWithStatus = User & { status: Status };

// Function types
type Handler = (event: MouseEvent) => void;

// Mapped types
type Readonly<T> = { readonly [K in keyof T]: T[K] };

// Tuple types
type Point = [number, number];
```

**Why**: Each has strengths. Interfaces are better for extensibility; types are better for complex transformations.

## Anti-Pattern 8: Nested Ternaries

Deeply nested ternary operators reduce readability.

### Pattern: Extract Complex Conditionals

Before:
```typescript
// Hard to parse at a glance
<tr onClick={canExpandUp ? () => handleExpandUp() : canExpandDown ? () => handleExpandDown() : undefined}>

// Also hard to follow
const fontStyle = code === 1 ? 'italic' : code === 2 ? 'bold' : code === 3 ? 'underline' : undefined;
```

After:
```typescript
// Option 1: Extract to a variable
let rowClickHandler: (() => void) | undefined;
if (canExpandUp) {
  rowClickHandler = () => handleExpandUp();
} else if (canExpandDown) {
  rowClickHandler = () => handleExpandDown();
}
<tr onClick={rowClickHandler}>

// Option 2: Extract to a named function
function getFontStyle(code: number | undefined): 'italic' | 'bold' | 'underline' | undefined {
  if (code === 1) return 'italic';
  if (code === 2) return 'bold';
  if (code === 3) return 'underline';
  return undefined;
}
const fontStyle = getFontStyle(code);
```

**When to extract**: Consider extracting when:
- The ternary has 3+ branches
- The conditions are complex (not simple boolean checks)
- The ternary is used inline in JSX props

**When ternaries are fine**:
- Simple two-way conditionals: `isActive ? 'active' : 'inactive'`
- Short, readable expressions: `count > 0 ? count : 'none'`

## React 19 Typing Changes

Common typing changes when upgrading to `@types/react@19`.

```typescript
// 1. useRef requires an argument in @types/react@19
useRef();                          // Error
useRef(undefined);                 // Correct
useRef<HTMLDivElement>(null);      // Correct
// Bonus: all refs are now mutable (ref.current = value works)

// 2. Ref callbacks cannot implicitly return (to support cleanup functions)
<div ref={current => (instance = current)} />     // Error
<div ref={current => { instance = current; }} />   // Correct

// 3. ReactElement props default to unknown (was any)
type Example = ReactElement["props"]; // unknown in React 19 (was any)
```

**Migration**: Run the official codemod to handle these changes automatically:
```
npx types-react-codemod@latest preset-19 ./path-to-app
```
