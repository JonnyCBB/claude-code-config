# Architectural Friction Patterns

## Table of Contents

1. [Introduction](#introduction)
2. [Friction Patterns](#friction-patterns)
   1. [Scattered Concept](#1-scattered-concept)
   2. [Shallow Module](#2-shallow-module)
   3. [God Class / Module](#3-god-class--module)
   4. [Tight Coupling](#4-tight-coupling)
   5. [Feature Envy](#5-feature-envy)
   6. [Missing Abstraction](#6-missing-abstraction)
   7. [Leaky Abstraction](#7-leaky-abstraction)
   8. [Untested Integration Seam](#8-untested-integration-seam)
3. [Quantitative Signals](#quantitative-signals)
   1. [Files-per-Concept](#files-per-concept)
   2. [Context Window Budget](#context-window-budget)
   3. [Module Depth Score](#module-depth-score)

---

## Introduction

During Phase 1 (Understand), explore the codebase organically and classify friction points using these patterns. The friction you encounter IS the signal — do not follow rigid heuristics, but use these patterns to name and quantify what you find. Each pattern includes a detection heuristic an agent can execute directly and a measurable severity threshold.

---

## Friction Patterns

### 1. Scattered Concept

**Description:** A single domain concept is spread across many files or directories instead of being cohesive in one location. This forces an agent (or developer) to gather context from many places to understand one idea.

**Detection heuristic:**
1. Identify the core concept name (e.g., `Payment`, `UserSession`, `Playlist`).
2. Run: `grep -rl "ConceptName" src/ | wc -l`
3. Inspect whether the matched files live in different directories: `grep -rl "ConceptName" src/ | xargs dirname | sort -u | wc -l`
4. Check if there is a single authoritative module or if logic is duplicated across matches.

**Severity signal:** Files-per-concept > 5, or directories-per-concept > 3.

**Example:** A `Subscription` concept has its validation in `api/validators/`, its persistence in `db/models/`, its business rules in `services/billing/`, its serialization in `api/serializers/`, its events in `events/subscription/`, and its caching in `cache/subscription.py`. Changing subscription logic requires touching 6+ files across 6 directories.

---

### 2. Shallow Module

**Description:** A module's interface is nearly as complex as its implementation, providing little abstraction value. Callers must understand almost everything the module does internally.

**Detection heuristic:**
1. Count public methods in the module: `grep -c "public\|export\|def [^_]" <module_file>`
2. Count total implementation lines (excluding blanks and comments).
3. Compute average lines per public method.
4. Check if private/internal helper count is lower than public method count.

**Severity signal:** More public methods than private methods, OR public method count > 10 with < 50 lines of implementation each.

**Example:** A `StringUtils` module exposes 25 public methods, each 3-8 lines long. Every caller must know which specific method to call because the module provides no higher-level abstraction — it is just a bag of trivially short functions.

---

### 3. God Class / Module

**Description:** One module accumulates too many responsibilities, becoming the hub that everything depends on and the bottleneck for every change.

**Detection heuristic:**
1. Check file length: `wc -l <module_file>`
2. Count imports/dependencies: `grep -c "^import\|^from\|^require\|^use " <module_file>`
3. Count public methods: `grep -c "public\|export\|def [^_]" <module_file>`
4. Check how many other modules import this one: `grep -rl "import.*ModuleName" src/ | wc -l`

**Severity signal:** File exceeds 500 lines, AND has > 20 imports, AND exposes > 15 public methods.

**Example:** An `ApplicationManager` class handles user authentication, request routing, database connections, caching, logging configuration, and health checks. It is 1200 lines long, imported by 40 other modules, and every new feature requires modifying it.

---

### 4. Tight Coupling

**Description:** Two or more modules cannot change independently because they reference each other directly, creating circular or bidirectional dependencies.

**Detection heuristic:**
1. For each module A, list its imports: `grep "^import\|^from\|^require" <module_A>`
2. For each imported module B, check if B imports A: `grep "ModuleA" <module_B>`
3. Build a dependency graph and look for cycles. Shortcut: `grep -r "import.*ModuleA" src/ | grep -v "ModuleA"` cross-referenced against A's own imports.
4. Check for shared mutable state between modules.

**Severity signal:** Module A imports module B AND module B imports module A (circular dependency). Any cycle of length 2+ qualifies.

**Example:** `OrderService` imports `InventoryService` to check stock levels, while `InventoryService` imports `OrderService` to get pending order counts. Neither can be tested, deployed, or reasoned about in isolation.

---

### 5. Feature Envy

**Description:** A module accesses another module's data more than its own, suggesting the logic belongs in the other module instead.

**Detection heuristic:**
1. In the target module, count references to its own internal state (local fields, variables, self-references).
2. Count references to external modules' data (other module's fields, getters, properties).
3. Compute the ratio: `external_accesses / (external_accesses + local_accesses)`.
4. Look for chains like `other.getFoo().getBar().getValue()` which amplify the signal.

**Severity signal:** More than 60% of data accesses in a method or module target external modules.

**Example:** A `ReportGenerator` module reads 12 fields from `UserProfile`, 8 fields from `OrderHistory`, and only 2 of its own configuration fields. The report logic should live closer to the data it consumes, or the data should be passed via a dedicated DTO.

---

### 6. Missing Abstraction

**Description:** Multiple modules duplicate structurally similar logic without a shared interface or base implementation, causing changes to fan out across all copies.

**Detection heuristic:**
1. Search for structurally similar patterns: look for modules with similar method signatures or similar control flow.
2. Compare method names across files: `grep -h "def \|function \|public.*(" src/**/*.{py,java,ts} | sort | uniq -c | sort -rn | head -20`
3. Look for repeated error handling, validation, or transformation patterns across 3+ files.
4. Check if a shared interface or abstract base class exists for these modules — if not, this pattern is confirmed.

**Severity signal:** 3 or more modules share similar structural patterns (same method signatures, same control flow shape) without a shared interface.

**Example:** Three modules — `CsvExporter`, `JsonExporter`, `XmlExporter` — each implement `validate()`, `transform()`, and `write()` with nearly identical control flow but no shared `Exporter` interface. Adding a new export format requires copying one of them and hoping you replicate the implicit contract correctly.

---

### 7. Leaky Abstraction

**Description:** A module's implementation details bleed through its public interface, forcing callers to understand internals to use it correctly.

**Detection heuristic:**
1. Inspect public method signatures for internal types (e.g., database-specific objects, framework internals, implementation-specific config).
2. Check if callers pass implementation-specific parameters (connection strings, internal flags, retry configs that should be encapsulated).
3. Look for documentation or comments that say "you must call X before Y" or "only works when Z is configured" — these indicate leaked internal sequencing.
4. Search for callers that catch implementation-specific exceptions: `grep -r "catch.*SQLException\|catch.*HttpError" src/`

**Severity signal:** Callers need implementation knowledge to use the module correctly — visible as internal types in public signatures, required call ordering not enforced by the API, or implementation-specific exceptions in caller code.

**Example:** A `CacheService` exposes a `get(key, redisOptions)` method where `redisOptions` is a Redis-specific configuration object. Every caller must know the underlying cache is Redis. Swapping to Memcached requires changing every caller.

---

### 8. Untested Integration Seam

**Description:** A boundary between modules lacks tests, leaving the contract between them unverified. Bugs cluster at these seams because assumptions on each side diverge silently.

**Detection heuristic:**
1. Identify module boundaries: find public interfaces, API endpoints, service clients, or adapter layers.
2. Search for tests that exercise these boundaries: `grep -rl "ModuleA.*ModuleB\|integration\|contract" test/`
3. Check if boundary modules have corresponding test files: for each `src/adapters/FooAdapter`, look for `test/adapters/FooAdapterTest`.
4. Look for mocks that replace the boundary entirely — heavy mocking at a seam often means the real integration is untested.

**Severity signal:** A module boundary has zero tests that exercise both sides together, OR the only tests mock out the other side entirely.

**Example:** `PaymentGateway` calls `FraudDetectionService` via an internal API. Both modules have unit tests, but no test sends a real (or realistic) request from `PaymentGateway` through `FraudDetectionService`. When the fraud service changes its response format, payments silently fail in production.

---

## Quantitative Signals

Use these three metrics to measure overall codebase navigability for an AI agent. They complement the friction patterns above by providing aggregate health indicators.

### Files-per-Concept

Measure how many files an agent must open to fully understand one domain concept.

- **How to measure:** `grep -rl "ConceptName" src/ | wc -l`
- **Target:** 3 or fewer files per concept.
- **Interpretation:** If a single concept touches 8 files, an agent must load all 8 into context, trace their relationships, and reconcile potentially inconsistent representations. Consolidation directly improves navigability.

### Context Window Budget

Measure whether all files relevant to a typical task fit within a reasonable portion of the context window.

- **How to measure:** Identify the files needed for one representative task, then sum their sizes: `wc -c $(cat relevant-files.txt) | tail -1`. Convert bytes to approximate tokens (1 token ~ 4 bytes).
- **Target:** All relevant files for a single task fit within 40% of the context window (~400K tokens, or ~1.6MB of source code).
- **Interpretation:** If a routine task requires loading files that exceed this budget, the codebase forces an agent to work with incomplete context. Refactoring to reduce file sizes or consolidate related logic directly improves task success rates.

### Module Depth Score

Measure the ratio of public interface size to total implementation size. Deeper modules are easier to use because they hide more complexity.

- **How to measure:** For a module, count public methods (P) and total implementation lines (L). Depth = L / P. A module with 3 public methods and 500 lines has depth 167. A module with 15 public methods and 200 lines has depth 13.
- **Target:** Depth score > 50 for core modules.
- **Interpretation:** Higher depth means the module absorbs more complexity behind a simple interface. Low-depth modules (shallow modules) push complexity onto their callers and force agents to understand more code to accomplish tasks.
