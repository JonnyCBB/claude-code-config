# TypeScript/React Testing Patterns

Testing patterns for TypeScript and React using Jest, Vitest, React Testing Library, and MSW.

## Testing Libraries

| Library                      | Status                      | Use Case                          |
| ---------------------------- | --------------------------- | --------------------------------- |
| Jest + React Testing Library | Primary (USE on Tech Radar) | Component and integration testing |
| Vitest                       | Emerging                    | Used in newer projects, faster    |
| MSW (Mock Service Worker)    | Recommended                 | API mocking                       |
| user-event                   | Recommended                 | Realistic user interactions       |

## React Testing Library Patterns

### Pattern: Query Priority

Prefer queries that reflect how users interact with your app:

```typescript
// 1. Accessible queries (PREFER)
screen.getByRole("button", { name: "Submit" });
screen.getByLabelText("Email");
screen.getByPlaceholderText("Search...");
screen.getByText("Welcome");

// 2. Semantic queries
screen.getByAltText("User avatar");
screen.getByTitle("Close");

// 3. Test IDs (last resort)
screen.getByTestId("custom-element");
```

### Pattern: Basic Component Test

```typescript
import { render, screen } from '@testing-library/react';

describe('UserCard', () => {
  test('displays user name when provided', () => {
    // Arrange
    const user = { id: '1', name: 'Alice', email: 'alice@example.com' };

    // Act
    render(<UserCard user={user} />);

    // Assert
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
  });
});
```

### Pattern: User Interactions

Before (fireEvent):

```typescript
import { render, screen, fireEvent } from '@testing-library/react';

test('submits form on button click', () => {
  const onSubmit = jest.fn();
  render(<Form onSubmit={onSubmit} />);
  fireEvent.click(screen.getByRole('button', { name: 'Submit' }));
  expect(onSubmit).toHaveBeenCalled();
});
```

After (userEvent - more realistic):

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('submits form on button click', async () => {
  const user = userEvent.setup();
  const onSubmit = jest.fn();
  render(<Form onSubmit={onSubmit} />);

  await user.click(screen.getByRole('button', { name: 'Submit' }));

  expect(onSubmit).toHaveBeenCalled();
});

test('types in input field', async () => {
  const user = userEvent.setup();
  render(<SearchInput />);

  await user.type(screen.getByRole('textbox'), 'search query');

  expect(screen.getByRole('textbox')).toHaveValue('search query');
});
```

### Pattern: Async Testing with findBy

Before:

```typescript
// getBy fails immediately if element not found
test('shows data after loading', async () => {
  render(<DataComponent />);
  // This might fail if data hasn't loaded
  expect(screen.getByText('Data loaded')).toBeInTheDocument();
});
```

After:

```typescript
// findBy waits for element to appear
test('shows data after loading', async () => {
  render(<DataComponent />);

  // Waits up to 1000ms (configurable) for element
  expect(await screen.findByText('Data loaded')).toBeInTheDocument();
});

// With custom timeout
test('shows data after slow loading', async () => {
  render(<DataComponent />);

  expect(
    await screen.findByText('Data loaded', {}, { timeout: 3000 })
  ).toBeInTheDocument();
});
```

### Pattern: Custom Render with Providers

```typescript
// test-utils.tsx
import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';
import { UserProvider } from '@/contexts/UserContext';
import { ThemeProvider } from '@/contexts/ThemeContext';

interface CustomRenderOptions extends RenderOptions {
  user?: User | null;
  theme?: 'light' | 'dark';
}

function AllProviders({ children, user, theme }: {
  children: React.ReactNode;
  user?: User | null;
  theme?: 'light' | 'dark';
}) {
  return (
    <ThemeProvider theme={theme ?? 'light'}>
      <UserProvider initialUser={user ?? null}>
        {children}
      </UserProvider>
    </ThemeProvider>
  );
}

function customRender(
  ui: ReactElement,
  { user, theme, ...options }: CustomRenderOptions = {}
) {
  return render(ui, {
    wrapper: ({ children }) => (
      <AllProviders user={user} theme={theme}>
        {children}
      </AllProviders>
    ),
    ...options
  });
}

export * from '@testing-library/react';
export { customRender as render };
```

```typescript
// Component.test.tsx
import { render, screen } from '@/test-utils';

test('shows user name when logged in', () => {
  render(<UserGreeting />, { user: { id: '1', name: 'Alice' } });
  expect(screen.getByText('Hello, Alice')).toBeInTheDocument();
});
```

## Hook Testing Patterns

### Pattern: Testing Custom Hooks

```typescript
import { renderHook, act } from "@testing-library/react";

describe("useCounter", () => {
  test("increments counter", () => {
    const { result } = renderHook(() => useCounter(0));

    expect(result.current.count).toBe(0);

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });
});

describe("useDebounce", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("debounces value updates", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: "initial" } },
    );

    expect(result.current).toBe("initial");

    rerender({ value: "updated" });
    expect(result.current).toBe("initial"); // Still old value

    act(() => {
      jest.advanceTimersByTime(500);
    });

    expect(result.current).toBe("updated");
  });
});
```

### Pattern: Testing Hooks with Context

```typescript
describe('useUser', () => {
  test('returns user from context', () => {
    const user = { id: '1', name: 'Alice' };

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <UserProvider initialUser={user}>{children}</UserProvider>
    );

    const { result } = renderHook(() => useUser(), { wrapper });

    expect(result.current.user).toEqual(user);
  });
});
```

## MSW (Mock Service Worker) Patterns

### Pattern: Basic API Mocking

```typescript
// mocks/handlers.ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/users", () => {
    return HttpResponse.json([
      { id: "1", name: "Alice" },
      { id: "2", name: "Bob" },
    ]);
  }),

  http.get("/api/users/:id", ({ params }) => {
    return HttpResponse.json({ id: params.id, name: "Alice" });
  }),

  http.post("/api/users", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: "3", ...body }, { status: 201 });
  }),
];
```

```typescript
// mocks/server.ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

```typescript
// setupTests.ts
import { server } from "./mocks/server";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Pattern: Per-Test Handler Override

```typescript
import { server } from '@/mocks/server';
import { http, HttpResponse } from 'msw';

test('shows error message on API failure', async () => {
  // Override for this test only
  server.use(
    http.get('/api/users', () => {
      return HttpResponse.json(
        { message: 'Server error' },
        { status: 500 }
      );
    })
  );

  render(<UserList />);

  expect(await screen.findByText('Failed to load users')).toBeInTheDocument();
});
```

### Pattern: Testing Loading States

```typescript
import { http, HttpResponse, delay } from 'msw';

test('shows loading spinner while fetching', async () => {
  server.use(
    http.get('/api/users', async () => {
      await delay(100); // Simulate network delay
      return HttpResponse.json([]);
    })
  );

  render(<UserList />);

  expect(screen.getByRole('progressbar')).toBeInTheDocument();
  expect(await screen.findByText('No users found')).toBeInTheDocument();
  expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
});
```

## Mocking Patterns

### Pattern: Mock Modules

```typescript
// Jest
jest.mock("@/services/analytics", () => ({
  trackEvent: jest.fn(),
}));

// Vitest
vi.mock("@/services/analytics", () => ({
  trackEvent: vi.fn(),
}));
```

### Pattern: Mock Context

```typescript
test('logs out user when clicking logout', async () => {
  const logout = jest.fn();
  const user = userEvent.setup();

  render(
    <UserContext.Provider value={{ user: mockUser, logout }}>
      <Header />
    </UserContext.Provider>
  );

  await user.click(screen.getByRole('button', { name: 'Logout' }));

  expect(logout).toHaveBeenCalled();
});
```

### Pattern: Mock Window/Document

```typescript
describe("useMediaQuery", () => {
  const originalMatchMedia = window.matchMedia;

  beforeEach(() => {
    window.matchMedia = jest.fn().mockImplementation((query) => ({
      matches: query === "(min-width: 768px)",
      media: query,
      addListener: jest.fn(),
      removeListener: jest.fn(),
    }));
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
  });

  test("returns true for desktop viewport", () => {
    const { result } = renderHook(() => useMediaQuery("(min-width: 768px)"));
    expect(result.current).toBe(true);
  });
});
```

## Test Lifecycle Management

### Pattern: Setup and Teardown

```typescript
describe("UserService", () => {
  let service: UserService;

  beforeAll(() => {
    // Run once before all tests in this describe block
    server.listen();
  });

  beforeEach(() => {
    // Run before each test
    service = new UserService();
  });

  afterEach(() => {
    // Clean up after each test
    server.resetHandlers();
    jest.clearAllMocks();
  });

  afterAll(() => {
    // Clean up after all tests
    server.close();
  });
});
```

## Vitest-Specific Patterns

### Pattern: Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
    include: ["**/*.test.{ts,tsx}"],
  },
});
```

### Pattern: Vitest vs Jest Differences

```typescript
// Jest
jest.fn();
jest.mock();
jest.spyOn();
jest.useFakeTimers();

// Vitest (same API, different import)
import { vi } from "vitest";
vi.fn();
vi.mock();
vi.spyOn();
vi.useFakeTimers();
```

## Test Naming Convention

### Pattern: Descriptive Test Names

Before:

```typescript
test('component works', () => { ... });
test('handles error', () => { ... });
```

After:

```typescript
test('displays user name when user is logged in', () => { ... });
test('shows error message when API returns 500', () => { ... });
test('disables submit button while form is submitting', () => { ... });
```

### Pattern: Describe Block Organization

```typescript
describe('LoginForm', () => {
  describe('when form is valid', () => {
    test('enables submit button', () => { ... });
    test('calls onSubmit with credentials', () => { ... });
  });

  describe('when form has errors', () => {
    test('shows email validation error', () => { ... });
    test('shows password validation error', () => { ... });
    test('disables submit button', () => { ... });
  });

  describe('when submitting', () => {
    test('shows loading indicator', () => { ... });
    test('disables form inputs', () => { ... });
  });
});
```
