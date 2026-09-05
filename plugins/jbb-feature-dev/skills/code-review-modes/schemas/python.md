# Python Schemas

Verbatim per-mode block schemas for the `python-expert` agent. Source ranges
were lifted from the prior Python reviewer agents in this plugin's git history
(test-review and code-style-review schemas, respectively). The Python
test-review block uses `Function:` (not `Method/Function:`), drops the
`Test Data:` line that Java has, and adds an `Async: [Yes/No]` line to capture
the `@pytest.mark.asyncio` decision. On-disk space-form block names preserved
for downstream parser compatibility.

## Test-Review Schema

For EACH missing test, provide:

```
TEST NEEDED #[number]:
Priority: [Critical/High/Medium/Low]
Source File: [absolute/path/to/source_file.py]
Source Location: [Line numbers, e.g., Lines 45-67]
Function: [function_name() or ClassName.method()]
Test File: [absolute/path/to/test_file.py] (where test should be added)
Test Name: [test_should_behavior_when_condition]
Scenario: [What this test should verify]
Test Structure:
  - Arrange: [Setup required, fixtures needed]
  - Act: [Function call to test]
  - Assert: [Expected outcome]
Mocks Required: [List of dependencies to mock with spec]
Async: [Yes/No - needs @pytest.mark.asyncio]
Rationale: [Why this test is important]
```

For EACH redundant test, provide:

```
REDUNDANT TEST #[number]:
Test File: [absolute/path/to/test_file.py]
Test Location: [Line numbers]
Test Function: [test_function_name()]
Redundant With: [Reference to other test(s) covering same scenario]
Coverage Overlap: [What both tests are testing]
Recommendation: [Remove/Merge/Refactor]
Rationale: [Why this test is redundant]
```

For EACH quality issue, provide:

```
QUALITY ISSUE #[number]:
Type: [Naming/Structure/Mocking/Fixtures/Async/etc.]
Test File: [absolute/path/to/test_file.py]
Test Location: [Line numbers]
Test Function: [test_function_name()]
Current Issue: [Description of the problem]
Recommendation: [Specific improvement to make]
Example: [How it should look after improvement]
```

## Code-Style-Review Schema

For EACH issue found, provide:

```
ISSUE #[number]:
Type: [Imports/TypeHints/Naming/Complexity/Async/DRY/etc.]
Severity: [Critical/High/Medium/Low/Enhancement]
File: [absolute/path/to/file.py]
Location: [Line numbers, e.g., Lines 45-67]
Function/Class: [function_name() or ClassName]
Current Issue: [Description of the problem]
Recommendation: [Specific fix to apply]
Code Preview:
  Current: [relevant code snippet]
  Suggested: [how it should look after change]
Rationale: [Why this change improves the code]
```
