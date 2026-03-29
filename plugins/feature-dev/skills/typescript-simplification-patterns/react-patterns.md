# React + TypeScript Patterns

Best practices for typing React components, hooks, and events.

## Component Typing

### Pattern: Regular Functions Over React.FC

Before (less preferred):
```typescript
const MyComponent: React.FC<Props> = ({ title }) => {
  return <h1>{title}</h1>;
};

// Issues with React.FC:
// - No longer includes implicit children (React 18+)
// - Makes generics awkward
// - Adds unnecessary complexity
```

After (preferred):
```typescript
interface Props {
  title: string;
  isActive?: boolean;
}

function MyComponent({ title, isActive = false }: Props) {
  return <h1 className={isActive ? 'active' : ''}>{title}</h1>;
}

// Or arrow function for simpler components
const Badge = ({ label }: { label: string }) => (
  <span className="badge">{label}</span>
);
```

**Why**: Regular functions are simpler, more flexible, and work better with generics.

### Pattern: Props Interface Naming

```typescript
// Use ComponentNameProps convention
interface UserCardProps {
  user: User;
  onSelect?: (user: User) => void;
}

function UserCard({ user, onSelect }: UserCardProps) {
  return (
    <div onClick={() => onSelect?.(user)}>
      {user.name}
    </div>
  );
}
```

## Hook Typing Patterns

### Pattern: useState

```typescript
// Let inference work for simple types
const [count, setCount] = useState(0);
const [name, setName] = useState('');
const [items, setItems] = useState<string[]>([]); // Empty array needs type

// Explicit for nullable types
const [user, setUser] = useState<User | null>(null);

// Explicit for complex initial values
const [config, setConfig] = useState<Config>(() => computeInitialConfig());
```

### Pattern: useRef

```typescript
// DOM element refs - initialize with null
const inputRef = useRef<HTMLInputElement>(null);
const divRef = useRef<HTMLDivElement>(null);
const buttonRef = useRef<HTMLButtonElement>(null);

// Mutable refs - use undefined or a value
const renderCount = useRef(0);
const intervalRef = useRef<NodeJS.Timeout | undefined>(undefined);

// Usage
function Form() {
  const inputRef = useRef<HTMLInputElement>(null);

  const focusInput = () => {
    inputRef.current?.focus();
  };

  return <input ref={inputRef} />;
}
```

### Pattern: Ref Mutations in useEffect, Not Render

Before:
```typescript
function ElementTracker() {
  const counters = useRef<Record<string, number>>({});

  // Bug: Resetting during render causes issues with React 18 concurrent features
  counters.current = {};

  return items.map(item => {
    counters.current[item.type] = (counters.current[item.type] || 0) + 1;
    return <div key={item.id}>{item.type}-{counters.current[item.type]}</div>;
  });
}
```

After:
```typescript
function ElementTracker({ items }: { items: Item[] }) {
  const counters = useRef<Record<string, number>>({});

  // Reset in useEffect when dependencies change
  useEffect(() => {
    counters.current = {};
  }, [items]);

  // Use useMemo for derived values during render
  const labeledItems = useMemo(() => {
    const counts: Record<string, number> = {};
    return items.map(item => {
      counts[item.type] = (counts[item.type] || 0) + 1;
      return { ...item, label: `${item.type}-${counts[item.type]}` };
    });
  }, [items]);

  return labeledItems.map(item => (
    <div key={item.id}>{item.label}</div>
  ));
}
```

**Why**: React 18's concurrent features (Suspense, transitions) may render components multiple times before committing. Mutating refs during render can cause inconsistent state. Side effects, including ref mutations, should happen in `useEffect`.

### Pattern: useCallback with Typed Events

```typescript
const handleClick = useCallback(
  (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    console.log('clicked');
  },
  []
);

const handleChange = useCallback(
  (event: React.ChangeEvent<HTMLInputElement>) => {
    setValue(event.target.value);
  },
  []
);
```

### Pattern: useMemo with Complex Types

```typescript
interface ProcessedData {
  items: Item[];
  total: number;
}

const processedData = useMemo<ProcessedData>(() => {
  return {
    items: data.filter(item => item.isActive),
    total: data.reduce((sum, item) => sum + item.value, 0)
  };
}, [data]);
```

### Pattern: Pre-compute Lookup Maps for O(1) Access

Before:
```typescript
// O(n²) - findIndex called for each item in the map
function CommentList({ comments, allComments }: Props) {
  return comments.map((comment, idx) => {
    const globalIndex = allComments.findIndex(c =>
      c.id === comment.id && c.timestamp === comment.timestamp
    );
    return (
      <CommentDisplay
        key={comment.id}
        comment={comment}
        index={globalIndex >= 0 ? globalIndex : idx}
      />
    );
  });
}
```

After:
```typescript
// O(n) - build map once, O(1) lookups
function CommentList({ comments, allComments }: Props) {
  const indexMap = useMemo(() => {
    const map = new Map<string, number>();
    allComments.forEach((c, idx) => {
      map.set(`${c.id}:${c.timestamp}`, idx);
    });
    return map;
  }, [allComments]);

  return comments.map((comment, idx) => {
    const key = `${comment.id}:${comment.timestamp}`;
    const globalIndex = indexMap.get(key) ?? idx;
    return (
      <CommentDisplay
        key={comment.id}
        comment={comment}
        index={globalIndex}
      />
    );
  });
}
```

**When to use**: Consider this pattern when:
- You have nested loops (`.map()` containing `.find()`, `.findIndex()`, `.includes()`)
- The outer collection has 50+ items
- Profiling shows render performance issues

**When to skip**: For small collections (<50 items), the overhead of creating a Map may not be worth it. Measure before optimizing.

## Event Handler Typing

### Pattern: Common Event Types

```typescript
// Click events
const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
  event.preventDefault();
};

// Input change events
const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
  setValue(event.target.value);
};

// Select change events
const handleSelectChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
  setSelected(event.target.value);
};

// Form submit events
const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
  event.preventDefault();
  // Process form
};

// Keyboard events
const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
  if (event.key === 'Enter') {
    submit();
  }
};

// Focus events
const handleFocus = (event: React.FocusEvent<HTMLInputElement>) => {
  event.target.select();
};
```

### Pattern: Inline vs Separate Handlers

```typescript
// Inline for simple, single-use handlers
<button onClick={() => setCount(c => c + 1)}>
  Increment
</button>

// Separate for complex or reused handlers
const handleSubmit = (event: React.FormEvent) => {
  event.preventDefault();
  // Complex logic
};

<form onSubmit={handleSubmit}>...</form>
```

## Context Typing Pattern

### Pattern: Create Context with Custom Hook

```typescript
interface UserContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  isLoading: boolean;
}

// Create with undefined initial value
const UserContext = createContext<UserContextType | undefined>(undefined);

// Provider component
function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchCurrentUser().then(user => {
      setUser(user);
      setIsLoading(false);
    });
  }, []);

  return (
    <UserContext.Provider value={{ user, setUser, isLoading }}>
      {children}
    </UserContext.Provider>
  );
}

// Custom hook with runtime check
function useUser(): UserContextType {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within UserProvider');
  }
  return context;
}

// Usage
function Profile() {
  const { user, isLoading } = useUser();
  if (isLoading) return <Spinner />;
  if (!user) return <LoginPrompt />;
  return <div>{user.name}</div>;
}
```

**Why**: The undefined check ensures the hook is only used within the provider.

## Children Prop Typing

### Pattern: ReactNode for Flexible Children

```typescript
// Most flexible - accepts anything renderable
interface Props {
  children?: React.ReactNode;
  title: string;
}

function Card({ title, children }: Props) {
  return (
    <div className="card">
      <h2>{title}</h2>
      {children}
    </div>
  );
}
```

### Pattern: PropsWithChildren Utility

```typescript
import { PropsWithChildren } from 'react';

interface BaseProps {
  title: string;
  variant?: 'primary' | 'secondary';
}

function Section({ title, variant = 'primary', children }: PropsWithChildren<BaseProps>) {
  return (
    <section className={variant}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
```

### Pattern: Render Props

```typescript
interface ListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
}

function List<T>({ items, renderItem }: ListProps<T>) {
  return (
    <ul>
      {items.map((item, index) => (
        <li key={index}>{renderItem(item, index)}</li>
      ))}
    </ul>
  );
}

// Usage
<List
  items={users}
  renderItem={(user) => <span>{user.name}</span>}
/>
```

## Generic Components

### Pattern: Generic List Component

```typescript
interface ListProps<T extends { id: string }> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  onSelect?: (item: T) => void;
}

function List<T extends { id: string }>({
  items,
  renderItem,
  onSelect
}: ListProps<T>) {
  return (
    <ul>
      {items.map(item => (
        <li key={item.id} onClick={() => onSelect?.(item)}>
          {renderItem(item)}
        </li>
      ))}
    </ul>
  );
}

// Usage with type inference
<List
  items={users}
  renderItem={user => <span>{user.name}</span>}
  onSelect={user => console.log(user.email)}
/>
```

### Pattern: Generic Arrow Function Component

```typescript
// Note: trailing comma needed in TSX to distinguish from JSX element
const Table = <T,>({ data, columns }: TableProps<T>) => {
  return (
    <table>
      {/* ... */}
    </table>
  );
};

// Or use extends to avoid the comma
const Select = <T extends string | number>({ options, value, onChange }: SelectProps<T>) => {
  return <select>{/* ... */}</select>;
};
```

## Discriminated Unions for Props

### Pattern: Mutually Exclusive Props

```typescript
interface BaseButtonProps {
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
}

interface LinkButtonProps extends BaseButtonProps {
  variant: 'link';
  href: string;
  onClick?: never; // Explicitly forbid
}

interface ActionButtonProps extends BaseButtonProps {
  variant: 'action';
  onClick: () => void;
  href?: never; // Explicitly forbid
}

type ButtonProps = LinkButtonProps | ActionButtonProps;

function Button(props: ButtonProps) {
  if (props.variant === 'link') {
    return (
      <a href={props.href} className={`btn-${props.size}`}>
        Link
      </a>
    );
  }
  return (
    <button onClick={props.onClick} className={`btn-${props.size}`}>
      Action
    </button>
  );
}

// Usage - TypeScript enforces correct props
<Button variant="link" href="/about" /> // OK
<Button variant="action" onClick={() => {}} /> // OK
<Button variant="link" onClick={() => {}} /> // Error!
```

### Pattern: Loading/Error/Success States

```typescript
type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; error: Error }
  | { status: 'success'; data: T };

function DataDisplay<T>({ state, renderData }: {
  state: AsyncState<T>;
  renderData: (data: T) => React.ReactNode;
}) {
  switch (state.status) {
    case 'idle':
      return <p>Ready to load</p>;
    case 'loading':
      return <Spinner />;
    case 'error':
      return <ErrorMessage error={state.error} />;
    case 'success':
      return <>{renderData(state.data)}</>;
  }
}
```

**Why**: Discriminated unions ensure exhaustive handling and type-safe access to state-specific properties.

## React 19 Patterns

### Pattern: use() API — Reading Promises with Suspense (React 19)

```typescript
import { use, Suspense } from 'react';

function Comments({ commentsPromise }: { commentsPromise: Promise<Comment[]> }) {
    const comments = use(commentsPromise);
    return comments.map(c => <p key={c.id}>{c.text}</p>);
}

// Usage:
<Suspense fallback={<div>Loading...</div>}>
    <Comments commentsPromise={fetchComments()} />
</Suspense>
```

### Pattern: use() for Conditional Context (React 19)

Replaces `useContext` in cases where you need to read context conditionally.

```typescript
import { use } from 'react';

function Heading({ children }: { children: React.ReactNode }) {
    if (children == null) return null;
    const theme = use(ThemeContext);  // Works after early return
    return <h1 style={{ color: theme.color }}>{children}</h1>;
}
```

**Why**: Unlike `useContext`, `use()` can be called inside conditionals and loops.

### Pattern: useActionState — Form Actions with Built-in Pending State (React 19)

```typescript
import { useActionState } from 'react';

async function updateName(prev: string | null, formData: FormData): Promise<string | null> {
    const error = await submitName(formData.get("name") as string);
    return error ?? null;
}

function NameForm() {
    const [error, submitAction, isPending] = useActionState(updateName, null);
    return (
        <form action={submitAction}>
            <input type="text" name="name" />
            <button disabled={isPending}>Update</button>
            {error && <p>{error}</p>}
        </form>
    );
}
```

### Pattern: ref as Prop — forwardRef No Longer Needed (React 19)

Before (React 18):
```typescript
const MyInput = forwardRef<HTMLInputElement, { placeholder: string }>(
    ({ placeholder }, ref) => {
        return <input placeholder={placeholder} ref={ref} />;
    }
);
```

After (React 19):
```typescript
function MyInput({ placeholder, ref }: { placeholder: string; ref?: React.Ref<HTMLInputElement> }) {
    return <input placeholder={placeholder} ref={ref} />;
}
```

**Why**: `forwardRef` will be deprecated. Function components now accept `ref` as a regular prop.

### Pattern: Context as Provider — Simplified Syntax (React 19)

Before:
```typescript
<ThemeContext.Provider value="dark">{children}</ThemeContext.Provider>
```

After (React 19):
```typescript
<ThemeContext value="dark">{children}</ThemeContext>
```

**Why**: `<Context.Provider>` will be deprecated. Use `<Context>` directly.

### Pattern: useOptimistic — Optimistic UI Updates (React 19)

```typescript
import { useOptimistic } from 'react';

function TodoList({ todos }: { todos: Todo[] }) {
    const [optimisticTodos, addOptimisticTodo] = useOptimistic(
        todos,
        (current: Todo[], newTodo: Todo) => [...current, { ...newTodo, sending: true }]
    );
    // ...
}
```

### Pattern: useFormStatus — Form Pending State Without Prop Drilling (React 19)

```typescript
import { useFormStatus } from 'react-dom';

function SubmitButton() {
    const { pending } = useFormStatus();
    return <button type="submit" disabled={pending}>Submit</button>;
}
```

### Pattern: Document Metadata — Replaces react-helmet (React 19)

```typescript
function BlogPost({ post }: { post: Post }) {
    return (
        <article>
            <title>{post.title}</title>
            <meta name="author" content="Alice" />
            <h1>{post.title}</h1>
        </article>
    );  // <title> and <meta> auto-hoist to <head>
}
