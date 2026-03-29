# Strategic Splitting Criteria

Use these criteria in Step 3 of the break-down-initiative skill to determine how to break a
PRD/RFC/epic into feature outlines.

---

## 1. Independent Subsystems

The primary criterion. If the document describes multiple independent subsystems, each
becomes a feature.

**Signal**: The document mentions distinct functional areas connected by "and" — e.g.,
"build a platform with chat, file storage, and billing."

**Example**: "Build a notification system with email, push, and in-app" -> 3 features
(email notifications, push notifications, in-app notifications), each cutting through
all layers independently.

**Counter-example**: "Add email notifications with templates and scheduling" -> 1 feature
(templates and scheduling are parts of the same subsystem, not independent).

## 2. Vertical Slice Principle

Each feature must cut through ALL integration layers end-to-end (data model, API, UI,
tests). Never split horizontally.

**Wrong**: Feature 1 = "all database tables", Feature 2 = "all API endpoints",
Feature 3 = "all UI pages"

**Right**: Feature 1 = "user login end-to-end (DB schema + API + login form + tests)",
Feature 2 = "user profile end-to-end (DB + API + profile page + tests)"

## 3. User Journey Boundaries

Different user journeys = different features. A user journey is a complete path a user
takes to accomplish a goal.

**Example**: "Onboarding flow" and "Settings page" are separate journeys -> 2 features.

**Example**: "Search results" and "Search filters" are part of the same journey
(searching) -> consider keeping as 1 feature unless they are independently demoable.

## 4. Domain Boundaries

Work crossing bounded context boundaries should be split at the boundary. Each domain
has its own data model, language, and rules.

**Example**: A feature touching both the "payments" domain and the "notifications" domain
should be split into two features at the domain boundary, with a clear API contract
between them.

## 5. HITL vs AFK Classification

Classify each feature to identify which block the pipeline:

**HITL (Human-In-The-Loop)** — needs a human decision before implementation:

- Architectural choices (build vs buy, technology selection)
- Design review required (UX decisions, branding)
- Third-party vendor selection
- Security/compliance review

**AFK (Away From Keyboard)** — fully automatable:

- Well-defined implementation with clear acceptance criteria
- Follows established patterns in the codebase
- No ambiguity about the approach

Prefer AFK. Only mark HITL when a genuine human decision is required that cannot be
resolved by the agent using decision-principles.

## Granularity Check

After drafting features, verify granularity:

- **Too coarse**: Feature description contains "and" connecting distinct behaviors, or
  estimated complexity is "large" (would need its own decompose pass).
- **Too fine**: Feature is a single function change or config tweak that doesn't warrant
  its own research/plan cycle. Merge with a related feature.
- **Right-sized**: Feature is independently demoable, has 2-5 acceptance criteria, and
  maps to an estimated complexity of trivial/small/standard.
