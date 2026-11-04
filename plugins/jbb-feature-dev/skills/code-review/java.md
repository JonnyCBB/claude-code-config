# Java rules

- Import every type; flag any inline fully-qualified name (`new pkg.Class()`, `(pkg.Class) x`, `pkg.Class var`), unless two imported types clash.
- Statically import individual methods (`toSet()`, test fixture factories) in source and test code; never wildcard imports.
- Use no language feature newer than the project's configured Java release.
