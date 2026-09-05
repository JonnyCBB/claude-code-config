# Test Anti-Patterns: Low-Value Tests to Avoid

## CRITICAL: These Tests Should Be Flagged as Redundant

When reviewing tests or recommending test coverage, the following patterns should be identified as **LOW-VALUE** and flagged for removal with **HIGH PRIORITY**. These tests add maintenance burden without catching real bugs.

## Anti-Pattern 1: Testing Language Implementation Details

Tests that verify programming language guarantees work correctly.

### Java Examples

**BAD - Testing enum methods**:

```java
@Test
void shouldReturnMusicVideoWhenFromValueCalledWithMusicVideo() {
    // Tests that Java enum fromValue() works - Java guarantees this
    assertThat(EntityType.fromValue("music_video")).isEqualTo(EntityType.MUSIC_VIDEO);
}

@Test
void shouldReturnCorrectValueForMusicVideoEntityType() {
    // Tests that getValue() returns what was set - language guarantee
    assertThat(EntityType.MUSIC_VIDEO.getValue()).isEqualTo("music_video");
}

@Test
void shouldThrowIllegalArgumentExceptionWhenFromValueCalledWithInvalidValue() {
    // Tests that your fromValue() throws for invalid input
    // ONLY valuable if the throwing behavior is business-critical
    assertThrows(IllegalArgumentException.class, () -> EntityType.fromValue("invalid"));
}
```

**Why it's bad**: These tests verify that Java enums work as Java enums. The language guarantees this behavior.

### Scala Examples

**BAD - Testing case class/object behavior**:

```scala
class EntityTypeTest extends PipelineSpec {
  "EntityType.MusicVideo" should "return correct value from sealed trait" in {
    // Tests that pattern matching works - language guarantee
    EntityType.MusicVideo.value shouldBe "music_video"
  }
}
```

### Python Examples

**BAD - Testing dict/enum lookups**:

```python
def test_should_return_music_video_from_enum():
    # Tests that Python enums work
    assert EntityType.MUSIC_VIDEO.value == "music_video"

def test_should_lookup_value_in_dict():
    # Tests that dict lookup works
    assert ENTITY_MAPPING["music_video"] == "Music Videos"
```

## Anti-Pattern 2: Replicating Static Configuration

Tests that duplicate the exact logic from production code, just asserting it again.

### Java Example

**BAD - Replicating filter logic**:

```java
@Test
void shouldExcludeMusicVideoFromAllowedEntityTypes() {
    // Production code:
    // Arrays.stream(EntityType.values())
    //     .filter(et -> !et.equals(EntityType.MUSIC_VIDEO))
    //     .toList();

    // This test just verifies the filter works
    Set<EntityType> allowedTypes = getAllowedEntityTypes();
    assertThat(allowedTypes).doesNotContain(EntityType.MUSIC_VIDEO);
}

@Test
void shouldExcludePlaylistFromAllowedEntityTypes() {
    // Same pattern - replicating configuration
    Set<EntityType> allowedTypes = getAllowedEntityTypes();
    assertThat(allowedTypes).doesNotContain(EntityType.PLAYLIST);
}
```

**Why it's bad**: If configuration changes in production, the test must change identically. The test provides no regression protection - it just documents what the config currently is.

### Scala Example

**BAD - Replicating filter configuration**:

```scala
class RecordTypeFilterTest extends PipelineSpec {
  "filterRecordTypes" should "exclude invalid record types from output" in {
    // If this is just verifying a static filter, it's low-value
    val result = filterRecordTypes(allTypes)
    result should not contain RecordType.Invalid
  }
}
```

### Python Example

**BAD - Replicating allowed values**:

```python
def test_should_exclude_deprecated_types():
    # Just verifying static config
    allowed = get_allowed_types()
    assert "deprecated_type" not in allowed
```

## Anti-Pattern 3: Testing Static Mappings

Tests that verify a switch/match statement returns its hardcoded value.

### Java Example

**BAD - Testing switch case output**:

```java
@Test
void shouldReturnMusicVideosStringForMusicVideoEntityType() {
    // Production: case MUSIC_VIDEO -> "Music Videos";
    // Test just asserts the same mapping
    assertThat(getEntityTypeStr(EntityType.MUSIC_VIDEO)).isEqualTo("Music Videos");
}

@Test
void shouldReturnTracksStringForTrackEntityType() {
    // Same pattern
    assertThat(getEntityTypeStr(EntityType.TRACK)).isEqualTo("Tracks");
}
```

**Why it's bad**: The mapping IS the specification. You're testing that your hardcoded value equals your hardcoded value.

### When IS Testing a Mapping Valuable?

If the mapping involves LOGIC beyond a simple lookup:

```java
// GOOD - Tests logic, not just mapping
@Test
void shouldReturnPluralizedDisplayNameBasedOnCount() {
    assertThat(getEntityTypeStr(EntityType.TRACK, 1)).isEqualTo("Track");
    assertThat(getEntityTypeStr(EntityType.TRACK, 5)).isEqualTo("Tracks");
}
```

## Anti-Pattern 4: Testing Framework/Library Behavior

Tests that verify third-party libraries work as documented.

**BAD**:

```java
@Test
void shouldSerializeToJsonCorrectly() {
    // Tests that Jackson serializes correctly - Jackson's tests cover this
    String json = objectMapper.writeValueAsString(entity);
    assertThat(json).contains("\"type\":\"music_video\"");
}

@Test
void shouldFilterListCorrectly() {
    // Tests that Java Stream filter() works
    List<Integer> result = list.stream().filter(x -> x > 5).toList();
    assertThat(result).doesNotContain(3);
}
```

**EXCEPTION - Integration points ARE valuable**:

```java
// GOOD - Tests YOUR configuration of the framework
@Test
void shouldSerializeWithCustomDateFormat() {
    // Tests that YOUR ObjectMapper is configured correctly
    // This catches configuration bugs
}
```

## What Makes a Test Valuable?

A test is valuable when it verifies **business logic with conditional behavior** that could realistically have bugs.

### Characteristics of Valuable Tests

1. **Multiple code paths**: The code makes decisions based on runtime state
2. **Complex transformations**: Data is transformed in ways that could have bugs
3. **Integration behavior**: How components interact together
4. **Error handling**: What happens when things go wrong
5. **Edge cases**: Boundary conditions, null handling, empty inputs

### Example: GOOD Tests

```java
// GOOD - Tests business logic with multiple conditions
@Test
void shouldUpRankPersonalPlaylistWhenUserHasRecentPlaysAndPersonalIntent() {
    // Multiple conditions: recent plays + personal intent + ownership
    // Complex logic that could have bugs
}

// GOOD - Tests integration between components
@Test
void shouldRetrySearchWhenApiReturnsTransientError() {
    // Tests retry behavior - real business logic
}

// GOOD - Tests edge case handling
@Test
void shouldReturnEmptyResultsWhenSearchQueryIsEmpty() {
    // Tests a boundary condition
}

// GOOD - Tests error propagation
@Test
void shouldWrapClientExceptionWithContextualMessage() {
    // Tests error handling behavior
}
```

## Decision Flowchart

When reviewing a test, ask:

1. **Is this testing language behavior?** (enum, dict, list operations) → LOW VALUE
2. **Is this testing static configuration?** (hardcoded filters, mappings) → LOW VALUE
3. **Is this testing framework behavior?** (Jackson, streams, etc.) → LOW VALUE
4. **Does this test business logic with conditional paths?** → VALUABLE
5. **Could this behavior realistically have bugs?** → VALUABLE
6. **Would a change in requirements change this behavior?** → VALUABLE

## Anti-Pattern 5 (Language-Agnostic): Weak Assertions

Tests that pass for almost any output, providing no real correctness verification.

### Examples

**BAD - Existence-only assertions**:

```java
@Test
void shouldFulfillUseCaseForInAppAioExperience() {
    FulfilmentResponse response = service.fulfil(request);

    // Only proves "something came back" — not that it's CORRECT
    assertThat(response.getResultsCount()).isGreaterThan(0);
    assertThat(response.getIntent()).isEqualTo(Intent.PLAY);
}
```

**GOOD - Feature-specific assertions**:

```java
@Test
void shouldFulfillUseCaseForInAppAioExperience() {
    FulfilmentResponse response = service.fulfil(request);

    // Verifies the feature-specific behavior (AIO flag) and response structure
    assertThat(response.getIsAiOverview()).isTrue();
    assertThat(response.getIntent()).isEqualTo(Intent.SEARCH);
    assertThat(response.getResults(0).getType()).isEqualTo(ResultType.SEARCH_TO_CHAT);
    assertThat(response.getResults(0).getUrisList()).isNotEmpty();
}
```

**Why it's bad**: `isGreaterThan(0)` passes even if the response is completely wrong. If the test is for a specific feature (like AIO), it should assert on that feature's key fields. Weak assertions give false confidence — the test "passes" but would still pass with a broken implementation.

### Weak Assertion Patterns to Flag

| Pattern                              | Why It's Weak                      | Better Alternative                           |
| ------------------------------------ | ---------------------------------- | -------------------------------------------- |
| `isGreaterThan(0)`                   | Passes for any non-empty result    | Assert on specific expected count or content |
| `isNotEmpty()` alone                 | Proves existence, not correctness  | Assert on specific elements                  |
| `isNotNull()` alone                  | Almost never fails                 | Assert on specific fields/values             |
| `hasSize(N)` alone                   | Correct count, wrong content       | Also assert on element content               |
| `isTrue()`/`isFalse()` on flag alone | Doesn't verify surrounding context | Assert on the behavior the flag represents   |

### When to Flag

Ask: "Would this assertion still pass if the implementation was subtly broken?"

- **YES** → Weak assertion — flag it
- **NO** → Adequate assertion

## Anti-Pattern 6: Indistinct Mock Objects

Tests that stub a method to return the same mock object used as a parameter, making the test unable to detect when the wrong one is passed.

### Example

**BAD — same object for stub and parameter**:

```java
@Mock private Context context;
@Mock private SearchRequest searchRequest;

@BeforeEach
void setUp() {
    // searchRequest mock is both the parameter AND the stub return value
    when(context.searchRequest()).thenReturn(searchRequest);
}

@Test
void should_callService_when_experimentEnabled() {
    darkloader.darkload(context, searchRequest);

    // This passes even if production code uses context.searchRequest()
    // instead of the searchRequest parameter (or vice versa)
    verify(service).process(eq(context), eq(searchRequest), any());
}
```

**GOOD — distinct objects expose mix-ups**:

```java
@Mock private Context context;
@Mock private SearchRequest searchRequest;
@Mock private SearchRequest contextSearchRequest;

@BeforeEach
void setUp() {
    when(context.searchRequest()).thenReturn(contextSearchRequest);
}

@Test
void should_callService_when_experimentEnabled() {
    darkloader.darkload(context, searchRequest);

    // Now the test verifies WHICH SearchRequest is actually passed
    verify(service).process(eq(context), eq(contextSearchRequest), any());
}
```

**Why it's bad**: If `context.searchRequest()` and the `searchRequest` parameter are the same mock object, the test cannot distinguish which one the production code actually uses. A bug where the wrong one is passed will go undetected.

**When to flag**: Any `setUp` or test method where a mock returned by a stub is the same object as a method parameter in the code under test.

## Summary Table

| Pattern                                                               | Value | Action                 |
| --------------------------------------------------------------------- | ----- | ---------------------- |
| Testing enum fromValue()/getValue()                                   | LOW   | Flag as redundant      |
| Testing static filter configuration                                   | LOW   | Flag as redundant      |
| Testing switch case mappings                                          | LOW   | Flag as redundant      |
| Testing framework behavior                                            | LOW   | Flag as redundant      |
| Weak assertions (isGreaterThan(0), isNotNull() alone)                 | LOW   | Flag for strengthening |
| Indistinct mock objects (same mock as stub return and parameter)      | LOW   | Flag for strengthening |
| Missing feature assertion (Anti-Pattern 8, `MissingFeatureAssertion`) | LOW   | Flag for strengthening |
| Test name / assertion mismatch (`TestNameAssertionMismatch`)          | LOW   | Flag for strengthening |
| Vague test naming (`VagueNaming`)                                     | LOW   | Flag for strengthening |
| Missing context in test names (`MissingContext`)                      | LOW   | Flag for strengthening |
| Testing conditional business logic                                    | HIGH  | Keep/recommend         |
| Testing integration behavior                                          | HIGH  | Keep/recommend         |
| Testing error handling                                                | HIGH  | Keep/recommend         |
| Testing edge cases with logic                                         | HIGH  | Keep/recommend         |

## Anti-Pattern 7: React/TypeScript Specific Anti-Patterns

### 7.1 Snapshot Testing (Discouraged)

**BAD - Snapshot tests**:

```typescript
test('renders correctly', () => {
  const tree = renderer.create(<MyComponent />).toJSON();
  expect(tree).toMatchSnapshot();
});

test('UserCard matches snapshot', () => {
  const { container } = render(<UserCard user={mockUser} />);
  expect(container).toMatchSnapshot();
});
```

**Why it's bad**:

- Hard to review in PRs (large diffs with no semantic meaning)
- Often fail for unimportant reasons (whitespace, class names)
- Don't test actual behavior
- Lead to "update snapshot" habit without review

**GOOD - Behavior testing**:

```typescript
test('displays user name when provided', () => {
  render(<UserCard user={{ id: '1', name: 'Alice' }} />);
  expect(screen.getByText('Alice')).toBeInTheDocument();
});

test('shows default avatar when user has no image', () => {
  render(<UserCard user={{ id: '1', name: 'Alice', imageUrl: null }} />);
  expect(screen.getByRole('img', { name: 'Default avatar' })).toBeInTheDocument();
});
```

### 7.2 Testing TypeScript Types

**BAD - Testing that types work**:

```typescript
test("User type has correct properties", () => {
  const user: User = { id: "1", name: "Alice" };
  expect(user.id).toBe("1");
  expect(user.name).toBe("Alice");
});

test("Config interface has required fields", () => {
  const config: Config = { apiUrl: "http://localhost", timeout: 5000 };
  expect(config.apiUrl).toBeDefined();
  expect(config.timeout).toBeDefined();
});

test("Status union type accepts valid values", () => {
  const status: Status = "active";
  expect(["active", "inactive", "pending"]).toContain(status);
});
```

**Why it's bad**: TypeScript compiler guarantees this at compile time. The test just proves TypeScript works, not that your code works.

### 7.3 Testing React Internals

**BAD - Testing internal state**:

```typescript
test("sets loading state", () => {
  const { result } = renderHook(() => useMyHook());
  act(() => result.current.fetchData());
  expect(result.current.isLoading).toBe(true);
});

test("updates internal count", () => {
  const { result } = renderHook(() => useCounter());
  act(() => result.current.increment());
  expect(result.current.count).toBe(1);
});
```

**GOOD - Testing user-visible behavior**:

```typescript
test('shows loading spinner while fetching', async () => {
  render(<MyComponent />);
  fireEvent.click(screen.getByRole('button', { name: 'Fetch' }));
  expect(screen.getByRole('progressbar')).toBeInTheDocument();
});

test('displays incremented value after clicking increment button', async () => {
  const user = userEvent.setup();
  render(<Counter />);

  await user.click(screen.getByRole('button', { name: 'Increment' }));

  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});
```

**Why it's bad**: Users don't interact with React state directly. Test what users see and do.

### 7.4 Testing Component Renders

**BAD - Testing that component renders without crashing**:

```typescript
test('renders without crashing', () => {
  render(<MyComponent />);
});

test('component mounts', () => {
  const { container } = render(<Dashboard />);
  expect(container).toBeTruthy();
});

test('renders children', () => {
  render(<Layout><div>child</div></Layout>);
  expect(screen.getByText('child')).toBeInTheDocument();
});
```

**Why it's bad**: If the component crashes, you'll know from your app breaking. These tests add noise without catching real bugs.

**GOOD - Testing meaningful behavior**:

```typescript
test('displays dashboard metrics when data loads', async () => {
  render(<Dashboard />);
  expect(await screen.findByText('Total Users: 1,234')).toBeInTheDocument();
});
```

### 7.5 Testing Props Are Passed Through

**BAD - Testing that props work**:

```typescript
test('passes className to container', () => {
  const { container } = render(<Card className="custom-class" />);
  expect(container.firstChild).toHaveClass('custom-class');
});

test('onClick prop is called', () => {
  const onClick = jest.fn();
  render(<Button onClick={onClick} />);
  fireEvent.click(screen.getByRole('button'));
  expect(onClick).toHaveBeenCalled();
});
```

**Why it's bad**: You're testing that React's prop system works. Test the EFFECT of those props on behavior.

**GOOD - Testing the effect of props**:

```typescript
test('applies disabled styling and prevents interaction when disabled', async () => {
  const user = userEvent.setup();
  const onClick = jest.fn();
  render(<Button disabled onClick={onClick}>Submit</Button>);

  const button = screen.getByRole('button');
  expect(button).toBeDisabled();
  expect(button).toHaveClass('btn-disabled');

  await user.click(button);
  expect(onClick).not.toHaveBeenCalled();
});
```

### When IS Testing a React Component Valuable?

Tests are valuable when they verify **user-facing behavior with logic**:

```typescript
// GOOD - Tests conditional logic
test('shows error message when form validation fails', async () => {
  const user = userEvent.setup();
  render(<LoginForm />);

  await user.click(screen.getByRole('button', { name: 'Login' }));

  expect(screen.getByText('Email is required')).toBeInTheDocument();
});

// GOOD - Tests async flow with error handling
test('displays error toast when API call fails', async () => {
  server.use(
    http.post('/api/login', () => HttpResponse.json({ error: 'Invalid' }, { status: 401 }))
  );
  const user = userEvent.setup();
  render(<LoginForm />);

  await user.type(screen.getByLabelText('Email'), 'test@example.com');
  await user.type(screen.getByLabelText('Password'), 'password');
  await user.click(screen.getByRole('button', { name: 'Login' }));

  expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials');
});

// GOOD - Tests complex interaction
test('filters results as user types in search box', async () => {
  const user = userEvent.setup();
  render(<SearchableList items={['Apple', 'Banana', 'Cherry']} />);

  await user.type(screen.getByRole('searchbox'), 'an');

  expect(screen.getByText('Banana')).toBeInTheDocument();
  expect(screen.queryByText('Apple')).not.toBeInTheDocument();
  expect(screen.queryByText('Cherry')).not.toBeInTheDocument();
});
```

## Anti-Pattern 8: Missing Feature Assertion

Sub-type: `MissingFeatureAssertion`

Tests for a new feature that fail to assert on the feature-specific behavior they were written to verify. The test "passes" but would still pass even if the feature were completely broken or missing. Integration tests are especially prone to this — they verify the request goes through, but not that the new feature flag, field, or behavior is actually present in the response.

When CHANGE_SCOPE shows a new field, flag, or behavior was added, any test for that feature MUST assert on the new addition. Existence-only checks (`isGreaterThan(0)`, `isNotEmpty()`, `isNotNull()`) are insufficient when the test name promises feature-specific behavior.

### Java Example

**BAD — feature-specific test missing the feature assertion**:

```java
@Test
void shouldFulfillUseCaseForInAppAioExperience() {
    FulfilmentResponse response = service.fulfil(request);

    // Only proves "something came back" — does NOT verify AIO behavior
    // If is_ai_overview was never set, this test still passes
    assertThat(response.getResultsCount()).isGreaterThan(0);
    assertThat(response.getIntent()).isEqualTo(Intent.PLAY);
}
```

**GOOD — asserts on the feature-specific field (`is_ai_overview`)**:

```java
@Test
void shouldFulfillUseCaseForInAppAioExperience() {
    FulfilmentResponse response = service.fulfil(request);

    // Verifies the AIO-specific feature: is_ai_overview flag, search-to-chat type
    assertThat(response.getIsAiOverview()).isTrue();
    assertThat(response.getIntent()).isEqualTo(Intent.SEARCH);
    assertThat(response.getResults(0).getType()).isEqualTo(ResultType.SEARCH_TO_CHAT);
    assertThat(response.getResults(0).getUrisList()).isNotEmpty();
}
```

**Why it's bad**: When CHANGE_SCOPE introduced `is_ai_overview`, the test for that feature must assert `getIsAiOverview()`. Otherwise the test gives false confidence — it would pass with a broken implementation that never sets the flag.

### When to Flag

- Test name describes a specific feature (e.g., `shouldFulfillUseCaseForInAppAioExperience`, `shouldEnableXyzWhenFlagOn`)
- CHANGE_SCOPE indicates a new field, flag, response shape, or behavior was added
- The test's assertions do not reference the new feature-specific element
- Especially common in integration / end-to-end tests where weak assertions hide missing coverage

## Test-Review Patterns

Canonical test-review patterns. These three patterns apply across all languages (Java, Scala, Python, TypeScript) and live ONCE in this file (Skill DRY — Reqs Success Criterion line 126). Per-language `testing-patterns.md` files contain short pointer stubs that delegate here for these patterns (alongside their language-unique testing content).

### Pattern: Align Assertions with Test Name

Sub-type: `TestNameAssertionMismatch`

Test assertions must faithfully verify what the test name promises. If the name says "shouldAddVideoFilterToHermesUrl", assertions MUST verify the URL contains the filter — not unrelated side effects like response size.

#### Java example

Before (misaligned — name says "ToUrl", but asserts on response):

```java
@Test
void shouldAddVideoFilterToHermesUrlWhenVideoOnlyIsTrue() {
    when(hermesClient.getPayload(any(), any(), any())).thenReturn(response);

    List<Track> result = service.search(query, /* videoOnly= */ true);

    // WRONG: tests response, not URL construction
    assertThat(result.size()).isEqualTo(1);
    assertThat(result.get(0).uri()).isEqualTo("urn:item:123");
}
```

After (aligned — captures and asserts on URL):

```java
@Test
void shouldAddVideoFilterToHermesUrlWhenVideoOnlyIsTrue() {
    ArgumentCaptor<String> urlCaptor = ArgumentCaptor.forClass(String.class);
    when(hermesClient.getPayload(any(), any(), any())).thenReturn(response);

    service.search(query, /* videoOnly= */ true);

    verify(hermesClient).getPayload(any(), any(), urlCaptor.capture());
    assertThat(urlCaptor.getValue()).contains("&track-type=video");
}
```

#### pytest example

Before (misaligned — name says "raises ValueError", but only checks return):

```python
def test_should_raise_value_error_when_query_is_empty():
    result = service.search("")
    assert result == []  # WRONG: tests return value, not the exception
```

After (aligned — verifies the promised exception):

```python
def test_should_raise_value_error_when_query_is_empty():
    with pytest.raises(ValueError, match="query must not be empty"):
        service.search("")
```

#### ScalaTest example

Before (misaligned — name says "filters out drafts", but only checks count):

```scala
"filterRecords" should "filter out draft records from output" in {
  val result = service.filterRecords(allRecords)
  result.size shouldBe 5  // WRONG: count alone does not verify "drafts excluded"
}
```

After (aligned — verifies drafts are absent):

```scala
"filterRecords" should "filter out draft records from output" in {
  val result = service.filterRecords(allRecords)
  result.map(_.status) should not contain RecordStatus.Draft
  all(result.map(_.status)) should be(RecordStatus.Published)
}
```

#### RTL example

Before (misaligned — name says "shows error toast", but only checks button state):

```typescript
test('shows error toast when API call fails', async () => {
  server.use(http.post('/api/login', () => HttpResponse.error()));
  const user = userEvent.setup();
  render(<LoginForm />);

  await user.click(screen.getByRole('button', { name: 'Login' }));

  // WRONG: tests button state, not the error toast
  expect(screen.getByRole('button', { name: 'Login' })).toBeEnabled();
});
```

After (aligned — verifies the error toast itself):

```typescript
test('shows error toast when API call fails', async () => {
  server.use(http.post('/api/login', () => HttpResponse.error()));
  const user = userEvent.setup();
  render(<LoginForm />);

  await user.click(screen.getByRole('button', { name: 'Login' }));

  expect(await screen.findByRole('alert')).toHaveTextContent(/login failed/i);
});
```

**Why**: A test name is a contract. If assertions verify different behavior than the name promises, future readers cannot trust the suite as documentation, and the test may pass while the named behavior is broken.

### Pattern: Descriptive Test Names

Sub-type: `VagueNaming`

Tests with vague names (`test1`, `testFindUser`, `findUserReturnsNull`) provide no documentation value and obscure intent. Names should describe expected behavior and triggering condition.

Recommended shape: `should[ExpectedBehavior]When[Condition]` (Java/Scala/TS) or `test_should_[expected]_when_[condition]` (pytest).

#### Java example

Before:

```java
@Test
void test1() { ... }

@Test
void testFindUser() { ... }

@Test
void findUserReturnsNull() { ... }
```

After:

```java
@Test
void shouldReturnUserWhenIdExists() { ... }

@Test
void shouldThrowNotFoundExceptionWhenIdDoesNotExist() { ... }

@Test
void shouldReturnEmptyListWhenNoUsersMatch() { ... }
```

#### pytest example

Before:

```python
def test_user(): ...
def test_find(): ...
def test_returns_none(): ...
```

After:

```python
def test_should_return_user_when_id_exists(): ...
def test_should_raise_not_found_when_id_does_not_exist(): ...
def test_should_return_empty_list_when_no_users_match(): ...
```

#### ScalaTest example

Before:

```scala
"UserService" should "work" in { ... }
"findUser" should "return something" in { ... }
```

After:

```scala
"findUser" should "return user when id exists" in { ... }
"findUser" should "raise NotFoundException when id does not exist" in { ... }
"listUsers" should "return empty list when no users match filter" in { ... }
```

#### RTL example

Before:

```typescript
test('login', () => { ... });
test('button works', () => { ... });
```

After:

```typescript
test('shows error message when form validation fails', () => { ... });
test('disables submit button while login request is pending', () => { ... });
```

### Pattern: Context-Specific Test Names

Sub-type: `MissingContext`

Even well-shaped names can be too generic. Include WHERE the behavior occurs, WHICH actor is involved, and the SPECIFIC type of result.

Pattern elements:

- Target location: `ToUrl`, `InRequest`, `ToDatabase`, `InResponseBody`
- Specific result types: `EmptyList`, `NullUser`, `ZeroCount`
- Specific actors: `SearchClient`, `PaymentGateway`, `UserRepository`

#### Java example

Before:

```java
@Test
void shouldAddFilterWhenVideoOnlyIsTrue() { ... }  // Filter where?

@Test
void shouldReturnEmptyWhenClientFails() { ... }    // Empty what? Which client?
```

After:

```java
@Test
void shouldAddVideoFilterToHermesUrlWhenVideoOnlyIsTrue() { ... }

@Test
void shouldReturnEmptyTrackListWhenSearchClientFailsRequest() { ... }
```

#### pytest example

Before:

```python
def test_should_add_filter_when_video_only(): ...
def test_should_return_empty_when_client_fails(): ...
```

After:

```python
def test_should_add_video_filter_to_hermes_url_when_video_only_is_true(): ...
def test_should_return_empty_track_list_when_search_client_fails_request(): ...
```

#### ScalaTest example

Before:

```scala
"search" should "add filter when videoOnly is true" in { ... }
"search" should "return empty when client fails" in { ... }
```

After:

```scala
"search" should "add video filter to Hermes URL when videoOnly is true" in { ... }
"search" should "return empty TrackList when SearchClient fails request" in { ... }
```

#### RTL example

Before:

```typescript
test('shows error when fails', () => { ... });
test('disables button when invalid', () => { ... });
```

After:

```typescript
test('shows InvalidCredentials error toast when LoginApi returns 401', () => { ... });
test('disables Submit button in LoginForm when email field is empty', () => { ... });
```
