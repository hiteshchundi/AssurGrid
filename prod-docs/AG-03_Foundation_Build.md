# AG-03 — Foundation Build

## Purpose

AG-03 turns AssurGrid from an architecture on paper into a running software system.

The goal of this chapter is **not** to build product features. The goal is to establish the smallest professional foundation on which later AssurGrid modules can safely grow.

By the end of AG-03, the following end-to-end path must work:

```text
Browser
  ↓
React frontend
  ↓ HTTP
FastAPI backend
  ↓
SQLAlchemy
  ↓
psycopg
  ↓
PostgreSQL
```

The frontend must be able to verify that the API is running and that the API can reach PostgreSQL.

---

## Scope

AG-03 includes only foundational infrastructure:

- Monorepo structure
- FastAPI backend bootstrapping
- React + TypeScript frontend bootstrapping
- PostgreSQL for local development
- SQLAlchemy database integration
- psycopg PostgreSQL driver
- Alembic migrations
- Environment-based configuration
- CORS configuration
- Liveness and readiness health endpoints
- Minimal frontend shell
- One thin end-to-end health-check vertical slice
- Initial backend test setup

AG-03 explicitly does **not** include:

- Login
- Logout
- Users
- Roles
- Permissions / RBAC
- Audit trail
- Application Registry
- Governance policies
- Governance obligations
- PCR tracking
- Validation status logic
- Documents
- Notifications
- Dashboards
- External integrations
- Production observability
- Microservices

---

## Architectural Principle: Vertical Slice First

Do not build the entire frontend first and then attempt to connect it to a finished backend.

Do not build the entire backend first and only later discover how the UI actually needs to consume data.

Instead, prove one thin path through the entire stack:

```text
React
  ↓
FastAPI
  ↓
SQLAlchemy
  ↓
psycopg
  ↓
PostgreSQL
```

This is the first AssurGrid vertical slice.

The initial slice does not need business functionality. It only needs to prove that every major layer can communicate correctly.

---

## Repository Strategy

AssurGrid will initially use a single Git repository containing both frontend and backend.

This is a monorepo in the simple sense that related application components live in one repository.

Recommended starting structure:

```text
assurgrid/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── db/
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── app/
│   │   ├── components/
│   │   ├── routes/
│   │   └── styles/
│   └── package.json
├── infra/
│   └── compose.yaml
├── docs/
├── .gitignore
└── README.md
```

Do not create empty future modules such as `identity`, `audit`, `governance`, `notifications`, or `integrations` yet.

Every file and folder should exist because the current implementation needs it.

---

## Backend Foundation

The backend uses:

- Python
- FastAPI
- SQLAlchemy
- psycopg
- PostgreSQL
- Alembic
- pytest
- pydantic-settings

### `main.py`

`backend/app/main.py` should remain small.

Its responsibility is to assemble the application, register middleware, and include routers.

It must not become a container for business logic, database queries, authorization rules, or unrelated utilities.

Conceptually:

```python
app = FastAPI()
app.include_router(api_router)
```

---

## API Versioning

The initial API prefix is:

```text
/api/v1
```

Initial endpoints:

```text
GET /api/v1/health/live
GET /api/v1/health/ready
```

Versioning is introduced now because it is cheap at the beginning and protects future consumers from breaking changes later.

---

## Liveness and Readiness

### Liveness

Endpoint:

```text
GET /api/v1/health/live
```

Purpose:

> Is the FastAPI process alive?

This endpoint must not depend on PostgreSQL.

Example response:

```json
{
  "status": "ok"
}
```

### Readiness

Endpoint:

```text
GET /api/v1/health/ready
```

Purpose:

> Is the application capable of serving requests that require PostgreSQL?

The endpoint should execute a minimal query such as:

```sql
SELECT 1;
```

Interpretation:

```text
FastAPI alive + PostgreSQL reachable = ready
FastAPI alive + PostgreSQL unreachable = alive but not ready
```

---

## PostgreSQL Access Stack

The database stack is:

```text
FastAPI application
  ↓
SQLAlchemy
  ↓
psycopg
  ↓
PostgreSQL
```

### psycopg

psycopg is the PostgreSQL database driver.

It understands how Python communicates with the PostgreSQL server using PostgreSQL's protocol.

### SQLAlchemy

SQLAlchemy is the database toolkit / ORM layer used by the application.

It helps with:

- SQL execution
- Connection management
- Connection pooling
- Transactions
- Mapping database records to Python objects where useful
- Schema metadata

SQLAlchemy must not be treated as a curtain hiding PostgreSQL. Important SQL behavior should remain understandable and defensible.

---

## Synchronous Database Access

AG-03 will use synchronous SQLAlchemy database access.

Do not introduce asynchronous SQLAlchemy, `AsyncSession`, `asyncpg`, or async database plumbing at this stage.

Reason:

- Current product requirements do not justify the complexity.
- Synchronous access is easier to learn, inspect, and debug.
- The architecture can be revisited later if real workload evidence justifies asynchronous database access.

Principle:

> Do not pay complexity today for hypothetical scale tomorrow.

---

## Connection Pooling

Opening a new PostgreSQL connection for every database operation is wasteful.

SQLAlchemy should manage a reusable pool of database connections.

Conceptually:

```text
POOL
├── Connection A — available
├── Connection B — in use
├── Connection C — available
└── Connection D — available
```

A request borrows a connection, performs database work, and returns the connection to the pool.

Important distinction:

```text
connection ≠ transaction
```

A connection is the communication channel to PostgreSQL.

A transaction is a logical unit of database work performed using a connection.

---

## SQLAlchemy Session

A SQLAlchemy `Session` is the application's unit for interacting with the database.

It coordinates database work such as:

- Queries
- Persistence operations
- Connection use
- Transaction boundaries

A future business operation may look conceptually like:

```python
with session.begin():
    create_application(...)
    create_audit_record(...)
```

If both actions are in one transaction, they should either both succeed or both roll back.

This is where database transaction concepts learned in DBW become directly relevant to AssurGrid.

---

## Database Migrations

Alembic will be configured before the first real AssurGrid domain table is created.

A migration is a version-controlled description of how the database schema changes from one version to the next.

Example sequence:

```text
Migration 001 — create applications
Migration 002 — add GxP classification
Migration 003 — add criticality
```

Benefits:

- Explicit schema history
- Repeatable schema evolution
- Reviewable database changes
- Consistent environments
- Version-controlled migration scripts

Important limitation:

> Alembic does not automatically guarantee zero data loss.

A destructive or poorly designed migration can still delete or corrupt data. Migration scripts must be reviewed and tested.

---

## No Fake Domain Tables

Do not create placeholder tables such as:

```text
test_table
dummy_users
sample_items
```

just to prove that PostgreSQL works.

Database connectivity is proven through the readiness health check using `SELECT 1`.

Alembic setup proves the migration system is functional.

The first real table should appear only when a real AssurGrid domain requirement justifies it.

---

## Configuration

Runtime-specific settings must not be hardcoded in source files.

Use environment-based configuration through `pydantic-settings` or an equivalent clear settings layer.

Expected settings include values such as:

```text
DATABASE_URL
FRONTEND_ORIGIN
```

The application should fail clearly when required configuration is missing.

### `.env`

Contains actual local configuration and potentially secrets.

It must not be committed to Git.

### `.env.example`

Contains safe placeholders showing developers which configuration variables are required.

It should be committed.

Example:

```text
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/assurgrid
FRONTEND_ORIGIN=http://localhost:5173
```

---

## Local Development Environment

Use Docker Compose for PostgreSQL only during AG-03.

Recommended local arrangement:

```text
React frontend  — runs directly
FastAPI backend — runs directly
PostgreSQL      — Docker Compose
```

Do not containerize everything yet.

This keeps Python and frontend development easy to inspect and debug while making PostgreSQL reproducible.

---

## Frontend Foundation

The frontend stack is:

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query

### React

Used to build the visible UI and reusable components.

### TypeScript

Used for static type checking and more explicit data contracts.

### Vite

Used for frontend development server, build tooling, module handling, and hot reload.

### React Router

Used for client-side page routing.

### TanStack Query

Used for server-state fetching, caching, loading states, errors, and refetching.

Do not manually reproduce these behaviors with excessive `useEffect` logic.

---

## Backend Owns Business Authorization

Frontend visibility is not security.

A user can inspect and manipulate browser-side code.

Therefore:

```text
Frontend:
What should this user see?

Backend:
What is this user actually allowed to do?
```

The backend must become the authoritative enforcement point for application-level authorization when RBAC is introduced later.

Database-level security still matters, but AssurGrid user permissions are primarily an application/backend concern.

---

## CORS

During local development, the frontend and backend will likely use different origins, for example:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
```

FastAPI must explicitly allow the configured frontend origin.

Do not use unrestricted `*` origins as the default production strategy.

Allowed origins should come from configuration.

---

## First End-to-End Slice

The first AssurGrid UI may be intentionally simple.

Example:

```text
AssurGrid

Foundation status

API       Connected
Database  Connected
```

The important behavior is the full request path:

```text
React
  ↓ GET /api/v1/health/ready
FastAPI
  ↓
SQLAlchemy
  ↓
psycopg
  ↓
PostgreSQL
  ↓ SELECT 1
FastAPI
  ↓ JSON response
React
```

Once this works, AssurGrid is a functioning end-to-end system.

---

## Initial Backend Structure

A minimal backend may look like:

```text
app/
├── main.py
├── api/
│   ├── router.py
│   └── routes/
│       └── health.py
├── core/
│   └── config.py
└── db/
    ├── engine.py
    └── session.py
```

Do not introduce generic abstraction folders such as:

```text
services/
repositories/
managers/
helpers/
utils/
factories/
interfaces/
```

unless a real requirement appears that clearly justifies them.

---

## PostgreSQL Schema Strategy

AG-03 will use:

```text
Database: assurgrid
Schema: public
```

Do not create separate database schemas such as:

```text
identity
governance
audit
integration
registry
```

at this stage.

Application-level modularity does not automatically require multiple PostgreSQL schemas.

---

## Logging

Use straightforward application logging from the beginning.

The backend should provide useful logs for events such as:

- Application startup
- Configuration errors
- Database connection failure
- Request failure
- Migration failure

Do not introduce a production observability stack yet.

Advanced capabilities such as structured logging, request IDs, metrics, and monitoring belong to a later production-readiness phase.

---

## Testing Foundation

Use pytest for backend testing.

At minimum, AG-03 should contain a meaningful test that proves the liveness endpoint works.

Example expectation:

```text
GET /api/v1/health/live
→ HTTP 200
→ {"status": "ok"}
```

The goal is not test quantity.

The goal is to establish testing as a normal part of AssurGrid from its first executable version.

---

## Build Order

Implement AG-03 in roughly this sequence:

1. Initialize repository structure.
2. Initialize backend Python project.
3. Create FastAPI application.
4. Add configuration management.
5. Add `/api/v1/health/live`.
6. Create local PostgreSQL development database with Docker Compose.
7. Configure SQLAlchemy and psycopg.
8. Add `/api/v1/health/ready` using `SELECT 1`.
9. Configure Alembic.
10. Verify migration lifecycle.
11. Add backend health test.
12. Initialize React + TypeScript + Vite frontend.
13. Add React Router.
14. Add TanStack Query.
15. Configure frontend-to-backend API access.
16. Configure CORS.
17. Build minimal AssurGrid application shell.
18. Call `/api/v1/health/ready` from React.
19. Prove the complete Browser → API → PostgreSQL round trip.
20. Remove unnecessary generated code and abstractions.

---

## Definition of Done

AG-03 is complete only when all of the following are true:

| Requirement | Expected |
|---|---|
| React starts locally | ✅ |
| FastAPI starts locally | ✅ |
| PostgreSQL starts through Docker Compose | ✅ |
| Frontend can call backend | ✅ |
| Backend can query PostgreSQL | ✅ |
| `/api/v1/health/live` works | ✅ |
| `/api/v1/health/ready` works | ✅ |
| Configuration is not hardcoded | ✅ |
| Secrets are excluded from Git | ✅ |
| `.env.example` exists | ✅ |
| Alembic is configured and usable | ✅ |
| Initial backend test passes | ✅ |
| Repository structure is understandable | ✅ |
| No fake domain tables exist | ✅ |
| No premature business modules exist | ✅ |
| Every major dependency has a clear reason | ✅ |

---

## Learning Model

The complete request path should be understood as:

```text
React
"What does the user want?"

↓

FastAPI
"Is the request valid, allowed, and what should the application do?"

↓

SQLAlchemy
"How should Python work with the database?"

↓

psycopg
"How does Python communicate with PostgreSQL?"

↓

PostgreSQL
"How is the data actually stored, read, locked, versioned, and changed?"
```

DBW concepts become relevant primarily once work reaches PostgreSQL:

- Connections
- Transactions
- Commit / Rollback
- MVCC
- Snapshots
- Locks
- Blocking
- Deadlocks
- Isolation
- Query execution

AG-03 is therefore the first point where the DBW learning track and AssurGrid implementation begin to materially converge.

---

## Practical Session Decision

AG-03 requires a practical implementation session.

This chapter is specifically about creating the executable foundation, so implementation is not optional.

The practical session must result in a working:

```text
Browser
  ↓
React
  ↓
FastAPI
  ↓
SQLAlchemy
  ↓
psycopg
  ↓
PostgreSQL
```

pipeline.

The practical remains attached to AG-03 and does not alter the AG chapter numbering.
