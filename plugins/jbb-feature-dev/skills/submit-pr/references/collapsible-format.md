# Collapsible Format

Reference for `<details>/<summary>` formatting guidelines in PR descriptions.

---

## When to Use

Use `<details>/<summary>` collapsible sections for:

- API/gRPC request and response examples
- CLI commands with multi-line output (more than 5 lines)
- Code snippets demonstrating usage
- Verification scripts
- Detailed test results or data tables
- Manual verification evidence

---

## When NOT to Use

Do not use collapsible sections for:

- Short examples (fewer than 5 lines) that fit inline
- Critical information that all reviewers must see
- Simple bullet points or one-liner examples

---

## Syntax Template

```html
<details>
<summary><strong>Descriptive Title Here</strong></summary>

Content here...

</details>
```

**Rules:**
1. Always bold the summary text using `<strong>` tags
2. Add a blank line after the opening `<summary>` tag and before the closing `</details>` tag
3. Use descriptive summaries that tell reviewers what they will find inside
4. Include both input and output when showing commands or requests

---

## Good Summary Examples

| Content Type | Good Summary |
|--------------|--------------|
| API test | `API Response Verification` |
| gRPC call | `gRPC Request/Response Details` |
| CLI command | `CLI Command Output` |
| Script | `Verification Script` |
| Multiple tests | `Test Results (5 cases)` |
| Before/after | `Before and After Comparison` |
| Verification | `Verification Results: PASS` |
