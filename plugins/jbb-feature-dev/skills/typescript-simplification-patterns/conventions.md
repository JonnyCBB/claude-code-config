# TypeScript/React Conventions

Guidelines for TypeScript and React development.

## TypeScript Requirements

### Mandatory Rules

1. **TypeScript is required** for all new web development
2. **No `any` types** - ESLint enforces strong typing
3. **Strict null checks enabled** - But full strict mode sometimes disabled for legacy code
4. **No experimental features** - Avoid decorators and experimental syntax

### Pattern: Enable Strict Mode

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true
  }
}
```

## React Component Guidelines

### Pattern: Functional Components with Hooks

Before (avoid):

```typescript
class UserProfile extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { isLoading: true };
  }

  componentDidMount() {
    this.fetchUser();
  }

  render() {
    return <div>{this.state.user?.name}</div>;
  }
}
```

After (preferred):

```typescript
interface UserProfileProps {
  userId: string;
}

function UserProfile({ userId }: UserProfileProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchUser(userId).then(setUser).finally(() => setIsLoading(false));
  }, [userId]);

  if (isLoading) return <Spinner />;
  return <div>{user?.name}</div>;
}
```

### Pattern: Flat Component Hierarchies

Before (avoid deep nesting):

```typescript
function App() {
  return (
    <Layout>
      <Wrapper>
        <Container>
          <Section>
            <Card>
              <Content>
                <UserName>{user.name}</UserName>
              </Content>
            </Card>
          </Section>
        </Container>
      </Wrapper>
    </Layout>
  );
}
```

After (prefer composition):

```typescript
function App() {
  return (
    <Layout>
      <UserCard user={user} />
    </Layout>
  );
}

function UserCard({ user }: { user: User }) {
  return (
    <Card>
      <CardTitle>{user.name}</CardTitle>
      <CardContent>{user.bio}</CardContent>
    </Card>
  );
}
```

### Pattern: State in URL

Before (React state):

```typescript
function SearchPage() {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<Filters>({});

  // State is lost on refresh, not shareable
}
```

After (URL state):

```typescript
import { useSearchParams } from "react-router-dom";

function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get("q") ?? "";
  const filters = parseFilters(searchParams);

  const updateQuery = (newQuery: string) => {
    setSearchParams((params) => {
      params.set("q", newQuery);
      return params;
    });
  };

  // State persists on refresh, is shareable via URL
}
```

## Naming Conventions

| Item             | Convention                  | Example                                       |
| ---------------- | --------------------------- | --------------------------------------------- |
| Components       | UpperCamelCase              | `UserProfile`                                 |
| Files            | Component name or index.tsx | `UserProfile.tsx` or `user-profile/index.tsx` |
| Variables        | lowerCamelCase              | `userName`                                    |
| Functions        | lowerCamelCase              | `getUserData`                                 |
| Constants        | CONSTANT_CASE               | `MAX_RETRIES`                                 |
| Types/Interfaces | UpperCamelCase              | `UserData`                                    |
| Props Interfaces | ComponentNameProps          | `UserProfileProps`                            |
| Hooks            | use + Verb/Noun             | `useUser`, `useFetch`                         |

### Pattern: File Naming

```
src/
├── components/
│   ├── UserCard/
│   │   ├── index.tsx          # Barrel export
│   │   ├── UserCard.tsx       # Component
│   │   ├── UserCard.test.tsx  # Tests
│   │   └── UserCard.styles.ts # Styles (if needed)
│   └── Button.tsx             # Simple components can be single file
├── hooks/
│   └── useUser.ts
└── utils/
    └── formatDate.ts
```

## Import Conventions

### Pattern: Named Exports Preferred

Before:

```typescript
// user.ts
export default function getUser() { ... }

// other.ts
import getUser from './user'; // Name can vary
import fetchUser from './user'; // Same import, different name
```

After:

```typescript
// user.ts
export function getUser() { ... }

// other.ts
import { getUser } from './user'; // Name is consistent
```

**Exception**: Next.js pages require default exports:

```typescript
// pages/index.tsx
export default function HomePage() {
  return <Home />;
}
```

### Pattern: Import Organization

```typescript
// 1. React and framework imports
import { useState, useEffect } from "react";
import { useRouter } from "next/router";

// 2. External library imports
import { z } from "zod";
import { format } from "date-fns";

// 3. Internal absolute imports
import { useUser } from "@/hooks/useUser";
import { UserService } from "@/services/user";

// 4. Relative imports
import { formatUserName } from "./utils";
import type { UserCardProps } from "./types";
```

## Testing Requirements

### Pattern: React Testing Library

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('UserCard', () => {
  test('displays user name when provided', () => {
    // Arrange
    const user = { id: '1', name: 'Alice' };

    // Act
    render(<UserCard user={user} />);

    // Assert
    expect(screen.getByText('Alice')).toBeInTheDocument();
  });

  test('calls onSelect when clicked', async () => {
    // Arrange
    const user = { id: '1', name: 'Alice' };
    const onSelect = jest.fn();

    // Act
    render(<UserCard user={user} onSelect={onSelect} />);
    await userEvent.click(screen.getByRole('button'));

    // Assert
    expect(onSelect).toHaveBeenCalledWith(user);
  });
});
```

### Key Testing Principles

1. **User-perspective testing** - Test from user's point of view
2. **Quality over quantity** - Focus on use cases, not coverage metrics
3. **No snapshot testing** - Not recommended (hard to review, brittle)
4. **Use data-testid sparingly** - Prefer accessible queries (getByRole, getByLabelText)

## Common Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── page.tsx
│   ├── layout.tsx
│   └── api/
├── components/             # Shared components
│   ├── Header/
│   │   ├── index.tsx
│   │   └── Header.test.tsx
│   └── index.ts           # Barrel exports
├── features/              # Feature modules
│   ├── Search/
│   │   ├── SearchPage.tsx
│   │   ├── SearchInput.tsx
│   │   └── index.ts
│   └── Player/
├── contexts/              # React contexts
│   ├── UserContext.tsx
│   └── index.ts
├── hooks/                 # Custom hooks
│   ├── useUser.ts
│   └── useDebounce.ts
├── services/              # API clients
│   └── userService.ts
├── types/                 # Shared types
│   └── user.ts
└── utils/                 # Utilities
    └── formatDate.ts
```
