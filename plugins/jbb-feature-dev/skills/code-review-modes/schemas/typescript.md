# TypeScript Schemas

Verbatim per-mode block schemas for the `typescript-expert` agent. Source
ranges were lifted from the prior TypeScript reviewer agents in this plugin's
git history (test-review and code-style-review schemas, respectively).
The TypeScript test-review block uses `Component/Function:` (not Method or
Function), and the nested example code uses **escaped triple-backticks**
(`\`\`\`typescript`) so the outer markdown fence renders the example as
literal source. On-disk space-form block names preserved for downstream parser
compatibility.

## Test-Review Schema

For EACH missing test, provide:

```
TEST NEEDED #[number]:
Priority: [Critical/High/Medium/Low]
Source File: [absolute/path/to/Component.tsx]
Source Location: [Line numbers, e.g., Lines 45-67]
Component/Function: [ComponentName or functionName()]
Test File: [absolute/path/to/Component.test.tsx] (where test should be added)
Test Name: [displaysBehaviorWhenCondition]
Scenario: [What user-visible behavior this test should verify]
Test Structure:
  - Arrange: [Setup required - providers, mocks, initial state]
  - Act: [User interaction or trigger]
  - Assert: [Expected user-visible outcome]
Mocks Required: [MSW handlers, jest.mock, etc.]
Example Code:
\`\`\`typescript
test('displays error message when submission fails', async () => {
  // Arrange
  server.use(
    http.post('/api/submit', () => HttpResponse.json({ error: 'Failed' }, { status: 500 }))
  );
  const user = userEvent.setup();

  // Act
  render(<MyComponent />);
  await user.click(screen.getByRole('button', { name: 'Submit' }));

  // Assert
  expect(await screen.findByText('Submission failed')).toBeInTheDocument();
});
\`\`\`
Rationale: [Why this test is important]
```

For EACH redundant test, provide:

```
REDUNDANT TEST #[number]:
Test File: [absolute/path/to/Component.test.tsx]
Test Location: [Line numbers]
Test Name: [testName]
Anti-Pattern Type: [Snapshot/TypeTest/InternalState/StaticMapping/etc.]
Current Code:
\`\`\`typescript
[The test code]
\`\`\`
Issue: [Why this test is low-value]
Recommendation: [Remove/Replace with behavior test]
Replacement (if applicable):
\`\`\`typescript
[Better test code]
\`\`\`
```

For EACH quality issue, provide:

```
QUALITY ISSUE #[number]:
Type: [Naming/AsyncHandling/QueryPriority/MissingProvider/etc.]
Test File: [absolute/path/to/Component.test.tsx]
Test Location: [Line numbers]
Test Name: [testName]
Current Issue: [Description of the problem]
Recommendation: [Specific improvement to make]
Example: [How it should look after improvement]
```

## Code-Style-Review Schema

For EACH issue found, provide:

```
ISSUE #[number]:
Type: [TypeSafety/ModernTS/ReactPattern/AsyncPattern/ComponentStructure/Testing/etc.]
Severity: [Critical/High/Medium/Low/Enhancement]
File: [absolute/path/to/file.tsx]
Location: [Line numbers, e.g., Lines 45-67]
Function/Component: [functionName() or ComponentName]
Current Issue: [Description of the problem]
Recommendation: [Specific fix to apply]
Code Preview:
  Current: [relevant code snippet]
  Suggested: [how it should look after change]
Rationale: [Why this change improves the code]
```
