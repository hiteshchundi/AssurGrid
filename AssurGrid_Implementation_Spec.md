# AssurGrid — the implementation agent Implementation Specification

**Status:** Active Build Contract  
**Applies to:** AssurGrid V1 implementation  
**Source of truth:** AG-00 Product Philosophy, AG-01 Product Design, AG-02 System Design & Architecture  
**Purpose:** Tell the implementation agent exactly how to build AssurGrid incrementally without inventing architecture, skipping learning steps, or introducing unnecessary complexity.

---

# 1. the implementation agent Operating Principle

the implementation agent is an implementation assistant, not the product architect.

It must implement the decisions already made in the AssurGrid design documents.

the implementation agent must not silently redesign:

- the architecture,
- the technology stack,
- the domain model,
- the governance model,
- the permission model,
- the integration strategy,
- the storage strategy,
- or the project sequence.

If an implementation question is not covered by the source-of-truth documents, the implementation agent should choose the smallest reversible implementation that preserves the existing architecture and clearly flag the decision.

---

# 2. Build Philosophy

AssurGrid must be built incrementally.

The governing rule is:

> **Build only what the current milestone needs, understand every line, preserve architectural boundaries, and remove code that has no clear purpose.**

Do not generate a large finished application in one pass.

Do not scaffold speculative features for later chapters.

Do not introduce infrastructure simply because it is common in enterprise systems.

Every implementation step should be:

- small,
- runnable,
- testable,
- reviewable,
- understandable,
- and committed independently where practical.

---

# 3. Locked Technology Stack

the implementation agent must use:

## Frontend

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query

## Backend

- Python
- FastAPI
- psycopg
- explicit SQL

## Database

- PostgreSQL

## Local Environment

- Docker Compose where useful for PostgreSQL/backend services

Do not replace these technologies unless the source-of-truth architecture is explicitly revised.

---

# 4. Prohibited Architecture Changes

the implementation agent must not introduce the following unless specifically instructed:

- microservices,
- Kubernetes,
- Kafka,
- RabbitMQ,
- mandatory Redis,
- Redux,
- GraphQL,
- ORM-first persistence,
- serverless redesign,
- event-sourcing architecture,
- CQRS architecture,
- generic repository frameworks,
- speculative plugin systems,
- multiple backend services,
- unnecessary base classes,
- hidden magic abstractions,
- premature generic frameworks.

Prefer direct, readable implementation.

---

# 5. Repository Layout

Create and preserve this top-level structure:

```text
assurgrid/
├── frontend/
├── backend/
├── docs/
├── mock-data/
├── docker-compose.yml
└── README.md
```

Do not create multiple repositories.

---

# 6. Backend Structure

Use approximately:

```text
backend/
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   │
│   ├── modules/
│   │   ├── identity/
│   │   ├── organizations/
│   │   ├── applications/
│   │   ├── governance/
│   │   ├── documents/
│   │   ├── audits/
│   │   ├── findings/
│   │   ├── capas/
│   │   ├── changes/
│   │   ├── validation/
│   │   ├── notifications/
│   │   ├── integrations/
│   │   └── audit_trail/
│   │
│   └── api/
│       └── v1/
│
├── migrations/
├── tests/
└── pyproject.toml
```

Only create module folders when the current milestone needs them.

Do not create dozens of empty placeholder files.

---

# 7. Frontend Structure

Use approximately:

```text
frontend/
└── src/
    ├── app/
    │   ├── router/
    │   ├── providers/
    │   └── layout/
    │
    ├── features/
    │   ├── applications/
    │   ├── governance/
    │   ├── documents/
    │   ├── audits/
    │   ├── findings/
    │   ├── changes/
    │   ├── validation/
    │   ├── notifications/
    │   └── administration/
    │
    ├── shared/
    │   ├── ui/
    │   ├── api/
    │   ├── types/
    │   └── utils/
    │
    └── main.tsx
```

Again, only create what the current milestone requires.

---

# 8. Backend Layering Rules

The backend must respect:

```text
API Router
    ↓
Application / Service Layer
    ↓
Repository / SQL
    ↓
PostgreSQL
```

## API layer

Responsible for:

- HTTP semantics,
- request validation,
- response serialization,
- dependency injection,
- authentication context.

It should not contain large business workflows.

## Service/application layer

Responsible for:

- business use cases,
- permission decisions,
- state transitions,
- transaction orchestration,
- domain behavior.

## Repository/database layer

Responsible for:

- explicit SQL,
- persistence,
- loading data,
- query-specific mapping.

Do not hide SQL behind a generic ORM.

---

# 9. Database Rules

the implementation agent must treat PostgreSQL as an active integrity boundary.

Use database features where appropriate:

- primary keys,
- foreign keys,
- unique constraints,
- NOT NULL constraints,
- CHECK constraints,
- transactions,
- indexes based on actual query needs.

Do not implement all integrity only in Python.

Do not duplicate constraints unnecessarily in many layers unless the duplication improves UX while the database remains authoritative.

---

# 10. SQL Rule

Prefer readable explicit SQL.

Example style:

```sql
SELECT
    application_id,
    application_name,
    lifecycle_state,
    validation_state
FROM regulated_application
WHERE organization_id = %s;
```

SQL should be:

- named or organized clearly,
- parameterized,
- easy to inspect,
- covered by tests when behavior is important.

Never concatenate untrusted values into SQL strings.

---

# 11. Domain Model Constraints

AssurGrid must preserve these core distinctions:

```text
Lifecycle State
Validation State
Governance Health
```

They are not one status.

Governance Health is derived.

Do not add a generic `status` field that collapses these concepts.

---

# 12. Governance Model

the implementation agent must preserve this chain:

```text
Control Definition
        ↓
Policy
        ↓
Policy Version
        ↓
Application Override (optional)
        ↓
Governance Obligation
        ↓
Activity / Completion
        ↓
Evidence
```

Do not collapse policy and obligation into the same table/model.

A policy is a reusable rule.

An obligation is a concrete requirement for a particular application and due date.

---

# 13. Policy Versioning

Never silently overwrite historically important governance configuration.

Policy changes must support historical traceability.

The implementation must eventually preserve:

- old value,
- new value,
- effective timing,
- actor,
- reason,
- affected scope.

A policy change must not silently erase an already-created obligation.

---

# 14. Derived Status Rule

The following should normally be calculated by trusted backend logic:

- Current,
- Due Soon,
- Overdue,
- time remaining,
- overdue duration,
- governance health.

Do not make them ordinary manually editable fields.

---

# 15. Audit Trail

Important mutations must generate audit events.

Conceptual audit data:

```text
event_id
organization_id
actor_user_id
timestamp
action
entity_type
entity_id
before_value
after_value
reason
request_id
source
```

Audit events are append-oriented.

Do not expose ordinary edit/delete operations for historical audit events.

---

# 16. History vs Audit

Do not treat history and audit trail as identical.

History answers:

> What values/states existed over time?

Audit answers:

> Who changed what, when, and why?

Implementation should preserve both concepts where the domain requires them.

---

# 17. Transaction Rule

Any use case that would leave inconsistent regulated information if partially saved must use a transaction.

Example:

```text
Complete obligation
+ record completion
+ link evidence
+ create audit event
+ create next obligation
```

These changes should commit together when they form one business operation.

Use:

```sql
BEGIN;
...
COMMIT;
```

and rollback on failure.

---

# 18. Document Rules

AssurGrid is not initially a replacement document-management repository.

PostgreSQL stores:

- metadata,
- document identity,
- type,
- application relationship,
- repository reference,
- version lineage,
- dates,
- provenance.

Do not store all enterprise controlled-document PDFs directly in PostgreSQL.

If AssurGrid later owns file attachments, use an object-storage abstraction.

---

# 19. Integration Rules

All external integrations must pass through an integration boundary.

Do not let application-domain code directly call a ServiceNow-specific client.

Use:

```text
External Source
      ↓
Adapter
      ↓
Import / Staging
      ↓
Validation
      ↓
Matching
      ↓
Core Domain
```

Initial implementation should use realistic CSV/mock data before enterprise APIs.

---

# 20. Provenance Rule

Externally sourced records must retain provenance.

At minimum, design for:

- source system,
- source record ID,
- import/sync timestamp,
- source update timestamp where available,
- import batch.

Never make imported values appear indistinguishable from manually entered authoritative AssurGrid data without a source trace.

---

# 21. Authentication and Authorization

Authentication asks:

> Who is the user?

Authorization asks:

> What may the user do?

Frontend controls are not security.

Every protected mutation must be authorized on the backend.

Detailed RBAC will be finalized in AG-04.

Until then:

- keep authorization hooks/boundaries clean,
- avoid hardcoding broad permissive logic deep in modules,
- do not invent the final role matrix.

---

# 22. Organization Scope

Major business entities should be designed with organization ownership from the beginning.

Usually this means an `organization_id` relationship.

Do not build full SaaS billing, tenant administration, or complex tenant provisioning.

The goal is structural future-proofing, not product expansion.

---

# 23. Notifications

Use a simple database-backed notification model first.

For reliable post-transaction work, use an outbox-style pattern.

Do not introduce Kafka, RabbitMQ, or Redis-based job infrastructure without an actual need.

---

# 24. Testing Expectations

Each milestone should include tests appropriate to the behavior being added.

Prioritize:

- business-rule tests,
- database constraint tests,
- transaction behavior,
- authorization behavior,
- API behavior,
- import validation.

Avoid chasing superficial coverage percentages.

Test what would materially hurt the product if broken.

---

# 25. Migration Discipline

All schema changes must be reproducible.

Do not manually alter a local database in a way that is not represented in migrations.

A fresh developer should be able to:

1. clone the repository,
2. configure environment,
3. start PostgreSQL,
4. apply migrations,
5. run the app.

---

# 26. Configuration and Secrets

No secrets in source control.

Use environment configuration for values such as:

```text
DATABASE_URL
AUTH_SECRET
OBJECT_STORAGE_URL
EMAIL_API_KEY
```

Provide safe `.env.example` documentation without real secrets.

---

# 27. Logging

Implement basic structured/application logging.

Do not over-engineer centralized observability in early milestones.

Logs should be useful for:

- startup failures,
- database errors,
- API errors,
- import failures,
- background processing,
- unexpected exceptions.

Never log secrets or sensitive authentication material.

---

# 28. Error Handling

Errors should be explicit and useful.

Do not use broad `except Exception: pass`.

Expected domain errors should become clear API responses.

Unexpected errors should be logged and return safe server errors.

Do not leak stack traces or secrets to end users.

---

# 29. API Versioning

Use:

```text
/api/v1
```

for public backend routes from the beginning.

Do not scatter unversioned routes across the application.

---

# 30. AG-03 Implementation Order

the implementation agent should implement AG-03 in small vertical steps.

## Step 1 — Repository Foundation

Create:

```text
assurgrid/
├── frontend/
├── backend/
├── docs/
├── mock-data/
├── docker-compose.yml
└── README.md
```

Do not add business features yet.

## Step 2 — PostgreSQL Development Service

Configure PostgreSQL for local development.

Requirements:

- environment-driven credentials,
- persistent local volume,
- health check where useful,
- no production secrets.

## Step 3 — FastAPI Skeleton

Create the smallest working backend.

Required behavior:

```text
GET /api/v1/health
```

returns a simple health response.

No business modules yet except what is needed structurally.

## Step 4 — Database Connection

Add psycopg connection handling.

Add:

```text
GET /api/v1/health/database
```

or equivalent internal health verification.

Keep implementation simple and explicit.

## Step 5 — Migration Mechanism

Introduce a migration tool/process suitable for explicit SQL.

The schema must become reproducible.

Do not create the full future schema yet.

## Step 6 — React/Vite Foundation

Create React + TypeScript frontend.

Add:

- application shell,
- router,
- TanStack Query provider,
- minimal layout.

Do not build final visual polish.

## Step 7 — Frontend-to-Backend Connection

Display backend health state from the frontend.

This proves:

```text
React
  ↓
FastAPI
  ↓
PostgreSQL
```

is wired correctly.

## Step 8 — First Vertical Business Slice

Implement only the minimum Application Registry slice.

Example:

```text
organization
regulated_application
```

Add:

- migration,
- explicit SQL,
- API endpoint,
- frontend list view,
- test data,
- tests.

This should become the first real end-to-end domain path.

---

# 31. Do Not Skip Ahead

During AG-03, the implementation agent must not implement in advance:

- full governance engine,
- full RBAC,
- document lineage,
- CAPA workflows,
- notification scheduling,
- integration framework,
- audit dashboards,
- complex application health calculations.

Those belong to later chapters.

Only create boundaries required to avoid obvious rework.

---

# 32. Incremental Delivery Contract

For each implementation step, the implementation agent should return:

1. what changed,
2. why it changed,
3. files added/modified,
4. any database migration,
5. how to run it,
6. how to verify it,
7. tests added,
8. architectural decisions made,
9. anything intentionally deferred.

Do not dump unexplained code.

---

# 33. Learning Contract

The project owner is learning the system deeply.

Therefore the implementation agent should prefer:

- clear naming,
- explicit logic,
- small functions,
- visible SQL,
- straightforward data flow.

Avoid clever code.

Avoid abstractions that make the implementation harder to explain.

Every important implementation should be defensible during technical review.

---

# 34. Change Discipline

If the implementation agent believes an architectural change is necessary:

1. do not silently implement it,
2. explain the conflict,
3. state the smallest proposed change,
4. explain its consequences,
5. wait for the architecture source of truth to be updated before treating the new design as permanent.

---

# 35. Quality Gate for Every Milestone

Before calling a milestone complete, verify:

- Does it run?
- Can a fresh database be created?
- Are migrations reproducible?
- Is SQL parameterized?
- Are important constraints in the database?
- Is business logic in the backend rather than React?
- Are module boundaries still clear?
- Are unnecessary dependencies avoided?
- Are tests meaningful?
- Can the project owner explain what was built?

If not, the milestone is not complete.

---

# 36. V1 Architectural North Star

the implementation agent must continually preserve this mental model:

```text
PostgreSQL protects truth
        ↓
FastAPI enforces business behavior
        ↓
React presents and enables interaction
```

And this governance chain:

```text
POLICY
    ↓
POLICY VERSION
    ↓
OBLIGATION
    ↓
ACTIVITY / COMPLETION
    ↓
EVIDENCE
    ↓
AUDIT TRAIL
```

---

# 37. Final Constraint

AssurGrid must become a product whose implementation can be understood and defended line by line.

When choosing between:

```text
clever + abstract + difficult to explain
```

and:

```text
simple + explicit + correct
```

choose the second unless a demonstrated requirement forces otherwise.
