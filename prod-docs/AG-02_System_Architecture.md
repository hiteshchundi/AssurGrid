# AssurGrid — AG-02 System Design & Architecture

**Status:** Locked for V1  
**Project:** AssurGrid  
**Purpose:** Define the system architecture, technical boundaries, data responsibilities, integration model, deployment shape, and architectural constraints for AssurGrid before AG-03 Foundation Build.

---

## 1. Architectural Objective

AG-01 defined what AssurGrid must do as a regulated-computerized-system governance workspace.

AG-02 defines how the product will be implemented so that it remains:

- understandable,
- auditable,
- secure,
- historically traceable,
- configurable,
- maintainable,
- realistic for regulated-industry use,
- and simple enough to build and defend.

AssurGrid must avoid two failure modes:

1. becoming a toy CRUD dashboard with pharmaceutical terminology, and
2. becoming an over-engineered distributed system whose infrastructure exceeds the product's actual requirements.

The governing architecture principle is therefore:

> **Build the smallest architecture that can faithfully support AssurGrid's real domain requirements.**

---

## 2. Primary Architecture Decision

AssurGrid V1 will use a **modular monolith**.

This means:

- one deployable backend application,
- one primary relational database,
- one frontend application,
- but clearly separated business modules inside the codebase.

The backend is a monolith operationally, but modular structurally.

Example business modules include:

- identity,
- organizations,
- applications,
- governance,
- documents,
- audits,
- findings,
- CAPAs,
- changes,
- validation,
- notifications,
- integrations,
- audit trail.

Microservices are explicitly rejected for V1 because current requirements do not justify distributed-system complexity.

---

## 3. High-Level Architecture

```text
                         USER
                           │
                           ▼
                ┌────────────────────┐
                │   React Frontend   │
                │                    │
                │ React 19           │
                │ TypeScript         │
                │ Vite               │
                │ React Router       │
                │ TanStack Query     │
                └─────────┬──────────┘
                          │
                     HTTPS / JSON
                          │
                          ▼
                ┌────────────────────┐
                │   FastAPI API      │
                │                    │
                │ Authentication     │
                │ Authorization      │
                │ Validation         │
                │ Business Logic     │
                │ Transactions       │
                └─────────┬──────────┘
                          │
                       SQL
                          │
                          ▼
                ┌────────────────────┐
                │    PostgreSQL      │
                │                    │
                │ Applications       │
                │ Governance Rules   │
                │ Obligations        │
                │ Documents          │
                │ History            │
                │ Audit Trail        │
                │ Notifications      │
                └─────────┬──────────┘
                          │
              ┌───────────┴──────────┐
              │                      │
              ▼                      ▼
       Integration Layer       Worker / Scheduler
              │                      │
              ▼                      ▼
       External Systems        Due-date processing
       CSV initially           Notification generation
       APIs later              Background work
```

---

## 4. Repository Strategy

AssurGrid V1 will use one Git repository.

```text
assurgrid/
├── frontend/
├── backend/
├── docs/
├── mock-data/
├── docker-compose.yml
└── README.md
```

The purpose is simplicity and traceability.

AssurGrid is one product and should initially remain one navigable codebase.

---

## 5. Frontend Architecture

### 5.1 Technology Stack

The frontend stack is locked as:

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query

### 5.2 Responsibilities

React is responsible for presentation and user interaction.

React Router is responsible for application navigation.

TanStack Query is responsible for server-state fetching, caching, synchronization, mutations, and refresh behavior.

Normal React state is used for local UI state such as:

- dialog visibility,
- active tabs,
- temporary form state,
- sidebar state.

Redux is not required for V1.

### 5.3 Architectural Rule

> **The frontend presents business state; the backend determines authoritative business state.**

Examples of logic that must not be authoritative in the frontend:

- Due Soon calculation,
- Overdue calculation,
- governance-health calculation,
- authorization,
- policy applicability,
- completion validity,
- policy-version selection.

Frontend checks may improve UX, but they are never the sole enforcement mechanism.

### 5.4 Feature-Based Structure

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

---

## 6. Backend Architecture

### 6.1 Technology Stack

The backend stack is locked as:

- Python
- FastAPI
- PostgreSQL
- psycopg
- explicit SQL

The project intentionally avoids an ORM-first architecture.

This keeps database behavior visible and supports the DBW learning objective: SQL, joins, constraints, transactions, indexes, locking, execution plans, and query design must remain understandable.

### 6.2 Versioned API

The backend will expose a versioned REST/JSON API.

Initial namespace:

```text
/api/v1
```

Illustrative endpoints:

```text
GET    /api/v1/applications
GET    /api/v1/applications/{id}
POST   /api/v1/applications

GET    /api/v1/applications/{id}/obligations
GET    /api/v1/applications/{id}/documents

POST   /api/v1/governance/policies
POST   /api/v1/governance/obligations/{id}/complete
```

### 6.3 Backend Layers

The backend should separate:

```text
HTTP Request
     ↓
API Router
     ↓
Application / Service Layer
     ↓
Repository / Database Access
     ↓
PostgreSQL
```

Responsibilities:

**API router**
- HTTP concerns
- request parsing
- response formatting
- dependency injection
- authentication context

**Application/service layer**
- business use cases
- authorization decisions
- domain transitions
- orchestration
- transactions

**Repository/database access**
- SQL execution
- persistence
- query-specific mapping

**PostgreSQL**
- relational integrity
- uniqueness
- foreign keys
- transactional consistency
- durable storage

---

## 7. Backend Module Structure

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

Code should be organized around regulated business concepts rather than generic technical folders.

---

## 8. Database Architecture

PostgreSQL is not merely storage. It protects core truths.

Examples:

- an obligation must belong to an application,
- a document version must belong to a document,
- organization-scoped identifiers must satisfy appropriate uniqueness rules,
- required relationships must be protected with foreign keys,
- domain mutations requiring multiple database changes must use transactions.

### 8.1 Major Database Domains

```text
ORGANIZATION
│
├── Identity
├── Application Registry
├── Governance Configuration
├── Governance Execution
├── Quality Events
├── Documents
├── Integrations
├── Notifications
└── Audit / History
```

### 8.2 Central Domain Object

The regulated application/computerized system is the central longitudinal object.

Most operational information eventually relates back to an application.

AssurGrid must use its own internal application identifier.

External identifiers such as CI IDs are attributes/references, not the sole database identity.

---

## 9. Three Independent Application States

The following remain separate:

### Lifecycle State

Examples:

- Implementation
- Operational
- Retirement
- Retired

### Validation State

Examples:

- Not Assessed
- Validation Required
- In Validation
- Validated
- Remediation Required

### Governance Health

Examples:

- Current
- Due Soon
- Overdue
- Critical Attention

Lifecycle and validation state may be stored and historically tracked.

Governance Health is primarily derived from applicable governance obligations and their current state.

A system may therefore be:

```text
Lifecycle: Operational
Validation: Validated
Governance Health: Overdue
```

---

## 10. Governance Engine

The governance engine is a central architectural capability.

AssurGrid will distinguish between:

1. control definition,
2. governance policy,
3. policy version,
4. application override,
5. concrete obligation,
6. activity/completion,
7. evidence.

Conceptually:

```text
CONTROL DEFINITION
        ↓
POLICY
        ↓
POLICY VERSION
        ↓
APPLICATION OVERRIDE (optional)
        ↓
OBLIGATION
        ↓
ACTIVITY / COMPLETION
        ↓
EVIDENCE
```

### 10.1 Control Definition

Defines the type of governance requirement.

Examples:

- Periodic Review
- Audit Trail Review
- Access Review
- Supplier Review
- Backup / Restore Test
- Disaster Recovery Test

### 10.2 Policy

Defines organizational requirements.

Example:

```text
High-Criticality GxP
Periodic Review:
- every 12 months
- due soon at 30 days
```

### 10.3 Policy Version

Policies must not be silently overwritten.

Each material configuration change must create or preserve a historically identifiable version/effective state.

### 10.4 Application Override

An authorized user may override an inherited rule for a specific application when justified.

Example:

```text
Organization ATR frequency: Quarterly
LIMS ATR frequency: Monthly
Reason: Higher data-integrity risk
```

The override must be permission-controlled and traceable.

### 10.5 Governance Obligation

A policy is a reusable rule.

An obligation is a concrete requirement applied to a specific application.

Example:

```text
Policy:
PCR every 12 months

Obligation:
LIMS PCR due 31 October 2026
```

This distinction is mandatory.

An existing obligation must not silently disappear merely because a future policy changes.

---

## 11. Effective-Dated Configuration

Configuration must preserve historical truth.

Illustrative model:

```text
Policy Version 1
PCR = every 12 months
Effective from: 2025-01-01
Effective until: 2026-10-31

Policy Version 2
PCR = every 24 months
Effective from: 2026-11-01
```

AssurGrid must eventually be able to answer:

> Which policy/rule was effective on a historical date?

---

## 12. Derived State

The following should normally be derived rather than manually selected:

- Due Soon
- Overdue
- governance health
- time remaining
- overdue duration

Example:

```text
Due date: 31 October 2026
Due-soon threshold: 30 days
Current date: 6 October 2026
Remaining: 25 days
Derived status: Due Soon
```

Ordinary users should not be able to manually choose Due Soon or Overdue.

---

## 13. History vs Audit Trail

These are separate concepts.

### Domain History

Answers:

> What values or states existed over time?

Example:

```text
PCR frequency:
Version 1 = 12 months
Version 2 = 24 months
```

### Audit Trail

Answers:

> Who changed what, when, and why?

Example:

```text
Actor: Quality Manager 17
Action: POLICY_UPDATED
Timestamp: ...
Old value: 12 months
New value: 24 months
Reason: Revised corporate SOP
```

AssurGrid needs both.

---

## 14. Audit Event Model

Important mutations should create append-oriented audit events.

Conceptual fields:

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

Audit records are not ordinary editable business rows.

They represent trace evidence.

---

## 15. Transaction Boundaries

Related domain changes must be atomic when partial completion would create inconsistent regulated information.

Example: completing a PCR may require:

1. updating the obligation,
2. recording completion,
3. linking evidence,
4. recording actor and completion date,
5. writing audit event,
6. creating the next obligation.

These changes should occur within one database transaction where appropriate.

Conceptually:

```sql
BEGIN;

-- related domain changes
-- audit event
-- next obligation

COMMIT;
```

On failure:

```sql
ROLLBACK;
```

Atomicity is a core architecture requirement.

---

## 16. Document Architecture

AssurGrid is not initially a replacement for validated enterprise document repositories.

PostgreSQL will primarily store:

- document metadata,
- document type,
- application relationship,
- repository/source,
- repository identifier,
- version lineage,
- status,
- effective dates,
- provenance,
- external reference/link information.

### 16.1 Document Versioning

Documents must support historical lineage.

```text
Document
└── Version 1.0
└── Version 2.0
└── Version 3.0
```

The model must support questions such as:

> Which version was effective at a given historical date?

### 16.2 File Storage

Actual files owned by AssurGrid, if introduced later, should use object storage or equivalent file storage.

Large document binaries should not be made the central PostgreSQL document strategy.

---

## 17. Integration Architecture

External data must enter AssurGrid through a defined integration boundary.

```text
External Source
      ↓
Integration Adapter
      ↓
Import / Staging
      ↓
Validation
      ↓
Identity Matching
      ↓
Unified AssurGrid Model
```

Initial V1 integration mechanism:

- realistic CSV/mock-data imports.

Future integration mechanisms may include:

- enterprise APIs,
- scheduled synchronization,
- events,
- controlled manual entry.

Core AssurGrid modules must not directly depend on a specific external system implementation.

---

## 18. Staging and Import Processing

Imported data should not be blindly inserted into authoritative domain tables.

Preferred flow:

```text
CSV / external payload
        ↓
Import Batch
        ↓
Staging Rows
        ↓
Validation
        ↓
Application / CI matching
        ↓
Accepted / Rejected
        ↓
Core AssurGrid tables
```

Import processing should support:

- batch identity,
- received row count,
- accepted row count,
- rejected row count,
- validation errors,
- source information,
- timestamps.

---

## 19. Provenance

Externally sourced data must retain provenance.

Possible provenance information includes:

- source system,
- source record identifier,
- source update timestamp,
- AssurGrid import timestamp,
- synchronization timestamp,
- import batch,
- integration adapter/source type.

The purpose is to answer:

> Where did this value come from, when was it obtained, and what source record supports it?

---

## 20. Notification Architecture

Notifications are part of AssurGrid's operational value.

AssurGrid must support background evaluation of time-based conditions.

Conceptual flow:

```text
Scheduler
    ↓
Find approaching / overdue obligations
    ↓
Create notification
    ↓
Notification Outbox
    ↓
Worker
    ↓
Deliver
```

Initial delivery may be in-app.

Future delivery may include:

- email,
- digest,
- escalation.

AssurGrid should not introduce Kafka, Redis, or a dedicated message broker in V1 without a demonstrated need.

---

## 21. Transactional Outbox

Where a domain mutation must reliably produce a notification or other downstream action, the domain change and an outbox row should be committed together.

Example:

```text
BEGIN
- complete PCR
- write audit event
- create notification outbox record
COMMIT
```

A worker processes the outbox later.

This avoids losing a notification simply because an external delivery mechanism was temporarily unavailable.

---

## 22. Identity and Access Architecture

Authentication and authorization are separate.

### Authentication

Answers:

> Who is this user?

### Authorization

Answers:

> What is this user permitted to do?

The frontend may hide actions for usability, but backend authorization is mandatory.

No protected action is considered secure merely because the frontend hides a button.

Detailed roles, permission scopes, separation-of-duties rules, and auditability will be defined in AG-04.

---

## 23. Browser Authentication Direction

The default browser direction is:

- secure server-managed authentication,
- HttpOnly cookies,
- backend-enforced authorization.

The business user model should remain separate from a future enterprise identity provider.

The architecture should remain compatible with future enterprise SSO/OIDC options.

---

## 24. Organization Boundary

Major business entities should include organizational ownership from the beginning, typically through `organization_id`.

This does not mean building a full multi-tenant SaaS platform in V1.

It means avoiding a future schema redesign if multiple organizations or business boundaries must later be supported.

---

## 25. Environment and Configuration

At minimum, the system should support:

- Development
- Testing
- Production

Environment-specific secrets and configuration must not be hardcoded into source files.

Examples:

```text
DATABASE_URL
AUTH_SECRET
OBJECT_STORAGE_URL
EMAIL_API_KEY
```

---

## 26. Deployment Architecture

### Local Development

```text
Docker Compose
├── PostgreSQL
└── FastAPI

React/Vite development server
```

### Production Direction

```text
Internet
   │
   ├──────────────► React static frontend
   │
   └──────────────► FastAPI container
                         │
                         ▼
                  Managed PostgreSQL
```

Optional supporting services may later include:

- object storage,
- email provider,
- external APIs.

Hosting-provider choice is not part of the core domain architecture.

The application should remain provider-independent where practical.

---

## 27. Responsibility Boundaries

A useful mental model:

```text
DATABASE
protects truth

BACKEND
understands and enforces business behavior

FRONTEND
presents the system and enables interaction
```

### PostgreSQL owns

- relational integrity,
- uniqueness,
- foreign keys,
- non-null rules,
- appropriate basic checks,
- durable storage,
- transactional consistency.

### FastAPI/domain layer owns

- authorization,
- use-case orchestration,
- applicability decisions,
- state-transition rules,
- governance calculations,
- policy resolution,
- transaction boundaries.

### React owns

- rendering,
- user interaction,
- navigation,
- client-side experience.

---

## 28. Explicitly Rejected for V1

The following are rejected unless a later requirement justifies them:

- microservices,
- Kubernetes,
- Kafka,
- Redis as mandatory infrastructure,
- Redux,
- ORM-first database abstraction,
- storing all controlled-document binaries directly in PostgreSQL,
- hardcoded governance frequencies,
- frontend-only authorization,
- manually assigned Due Soon/Overdue state,
- one generic application status,
- rebuilding ServiceNow or document repositories,
- generic spreadsheet-in-browser design,
- unnecessary abstraction layers.

---

## 29. AG-02 Locked Decisions

The following decisions are locked for AssurGrid V1:

1. Modular monolith architecture.
2. One AssurGrid Git repository.
3. React 19 + TypeScript + Vite + React Router + TanStack Query.
4. TanStack Query for server state; normal React state for local UI state.
5. Python + FastAPI backend.
6. Versioned REST/JSON API under `/api/v1`.
7. PostgreSQL as the primary database.
8. psycopg + explicit SQL rather than ORM-first development.
9. Backend is authoritative for business rules.
10. PostgreSQL constraints and transactions protect core data integrity.
11. Regulated application is the central longitudinal business object.
12. Governance model: control definition → policy → policy version → optional override → obligation → activity/completion → evidence.
13. Lifecycle, validation, and governance health remain distinct.
14. Governance Health is derived.
15. Due Soon and Overdue are derived.
16. Policy changes preserve historical versions/effective periods.
17. Domain history and audit trail are separate capabilities.
18. Important related mutations use transactions.
19. Controlled-document binaries are not the core PostgreSQL storage strategy.
20. Document metadata, lineage, provenance, and references are first-class.
21. External-system integration uses adapters and staging.
22. CSV/mock imports are the first integration implementation.
23. External data retains provenance.
24. Notifications use database-backed scheduling/outbox patterns before introducing brokers.
25. Authentication and authorization are separate.
26. Backend authorization is mandatory.
27. Architecture remains compatible with future enterprise SSO/OIDC.
28. Major business entities are organization-scoped from the beginning.
29. Deployment is frontend + FastAPI + PostgreSQL, provider-independent where practical.
30. Premature distributed infrastructure is prohibited.

---

## 30. Governing Architecture Question

For every significant implementation decision, ask:

> **Does this design preserve AssurGrid's domain truth, traceability, configurability, and operational clarity without introducing complexity the product does not yet need?**

If the answer is no, challenge the design before implementation.

---

## 31. Next Stage

AG-02 is complete.

The next project stage is:

> **AG-03 — Foundation Build**

AG-03 should establish the repository, development environment, frontend shell, backend foundation, PostgreSQL connection, migration mechanism, basic health checks, and first vertical slice without prematurely implementing later governance features.
