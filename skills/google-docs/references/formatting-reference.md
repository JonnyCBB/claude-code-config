# Formatting Reference

## Markdown to Google Docs Translation

| Markdown         | Google Docs Style                           |
| ---------------- | ------------------------------------------- |
| `# Title`        | **Title** (not Heading 1)                   |
| `## Heading`     | Heading 1                                   |
| `### Subheading` | Heading 2                                   |
| `#### Minor`     | Heading 3                                   |
| `**bold**`       | Bold text                                   |
| `*italic*`       | Italic text                                 |
| `~~strike~~`     | Strikethrough                               |
| `` `code` ``     | Consolas font                               |
| `[link](url)`    | Hyperlink                                   |
| `- item`         | Bullet list                                 |
| `1. item`        | Numbered list                               |
| `> quote`        | Italic text (blockquote)                    |
| Tables           | Native tables with borders and grey headers |

The `#` heading is promoted to Google Docs **Title** style. All other levels shift up by one accordingly. This matches the convention that a markdown document has one `#` title and uses `##` for major sections.

## API Limitations

| Feature       | Status     | Workaround                                 |
| ------------- | ---------- | ------------------------------------------ |
| Create tabs   | Not in API | Create template via UI, copy via Drive API |
| Delete tabs   | Not in API | Manual via UI                              |
| Pageless mode | Not in API | None available                             |
| Rename tabs   | Not in API | Manual via UI                              |

## Tab Capabilities

- Can READ all tabs
- Can EDIT content in any tab
- CANNOT create new tabs (UI only)
- CANNOT delete tabs (UI only)
- CANNOT rename tabs (UI only)
