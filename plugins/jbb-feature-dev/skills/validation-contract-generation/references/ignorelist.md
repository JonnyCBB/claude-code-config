# Ignorelist — Trivial File Patterns

Patterns for files that should be excluded from amendment detection during contract verification. Changes to these files are considered trivial and do not require new or updated verification assertions. The validator agent uses these patterns to avoid flagging routine housekeeping changes as unverified scope.

---

## Version Control

- `.gitignore`
- `.gitattributes`

## Lockfiles

- `*.lock`
- `Cargo.lock`
- `go.sum`
- `package-lock.json`
- `yarn.lock`

## Documentation

- `*.md`
- `CHANGELOG*`
- `LICENSE*`
- `README*`
- `docs/**`

## CI Configuration

- `.circleci/*`
- `.github/workflows/*`
- `.gitlab-ci.yml`

## Formatting Configuration

- `.editorconfig`
- `.eslintrc*`
- `.flake8`
- `.prettierrc*`

---

## Aggregate Bash Regex

A single pipe-separated regex for programmatic use (e.g., filtering `git diff` output):

```bash
IGNORELIST_REGEX='\.gitignore$|\.gitattributes$|\.lock$|Cargo\.lock$|go\.sum$|package-lock\.json$|yarn\.lock$|\.md$|CHANGELOG|LICENSE|README|docs/|\.circleci/|\.github/workflows/|\.gitlab-ci\.yml$|\.editorconfig$|\.eslintrc|\.flake8$|\.prettierrc'
```
