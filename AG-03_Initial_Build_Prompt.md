# AssurGrid AG-03 Initial Foundation Build Prompt

You are implementing **AG-03 — Foundation Build** for AssurGrid.

Treat the accompanying AG-03 documentation and decisions file as the source of truth.

Your task is to create the smallest professional, understandable, runnable AssurGrid foundation that proves the full end-to-end path:

```text
Browser
  → React
  → FastAPI
  → SQLAlchemy
  → psycopg
  → PostgreSQL
```

Do **not** build beyond the scope of AG-03.

---

## Product Context

AssurGrid is intended to become a governance platform for regulated computer systems, including GxP-oriented application governance, recurring obligations, validation information, document metadata, auditability, RBAC, and integrations.

However, **none of those business features belong in this build**.

This build exists only to establish a clean foundation.

---

## Mandatory Technical Decisions

Use the following stack exactly unless an implementation blocker makes a change unavoidable:

### Backend

- Python
- FastAPI
- SQLAlchemy
- psycopg
- PostgreSQL
- Alembic
- pydantic-settings
- pytest
- Synchronous database access

### Frontend

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query

### Local development

- PostgreSQL through Docker Compose
- Backend runs directly on the host machine
- Frontend runs directly on the host machine

### Architecture

- Single repository
- Modular monolith direction
- No microservices
- No async SQLAlchemy
- No speculative abstractions

---

## Strict Scope Restrictions

Do not implement any of the following:

- Login
- Logout
- Authentication
- Users
- Roles
- Permissions
- RBAC
- Audit trail
- Application Registry
- Governance policies
- Governance obligations
- PCR logic
- Validation logic
- Document management
- Notifications
- Dashboards
- Integrations
- Background jobs
- Message queues
- Redis
- Celery
- Kubernetes
- Production cloud deployment
- Production observability stack
- Multiple PostgreSQL schemas
- Fake business/domain tables
- Sample CRUD modules

Do not generate placeholder modules for future functionality.

If a file exists only because a framework template generated it and AssurGrid does not need it, remove it.

---

## Repository Structure

Create a clear structure similar to:

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
├── .env.example
├── .gitignore
└── README.md
```

You may simplify this structure if a directory would otherwise be empty.

Do not create empty folders simply to match the diagram.

---

## Backend Requirements

### 1. FastAPI application

Create the FastAPI application with a small `main.py`.

`main.py` should primarily:

- create the FastAPI app
- register CORS middleware
- include the main API router

Do not place database queries or business logic in `main.py`.

### 2. API prefix

Use:

```text
/api/v1
```

### 3. Liveness endpoint

Implement:

```text
GET /api/v1/health/live
```

Expected successful response:

```json
{
  "status": "ok"
}
```

This endpoint must not require PostgreSQL.

### 4. Readiness endpoint

Implement:

```text
GET /api/v1/health/ready
```

It must verify PostgreSQL connectivity using SQLAlchemy and a minimal query such as:

```sql
SELECT 1;
```

A successful response should make it obvious that both API and database are usable.

Choose a small JSON contract, for example:

```json
{
  "status": "ready",
  "database": "connected"
}
```

If PostgreSQL cannot be reached, return an appropriate non-success readiness response without crashing the FastAPI process.

Keep this implementation simple and readable.

### 5. SQLAlchemy

Configure SQLAlchemy using synchronous access.

Use SQLAlchemy's connection pooling defaults unless there is a clear reason to adjust them.

Do not add custom pool tuning at this stage.

### 6. psycopg

Use psycopg as the PostgreSQL driver.

The SQLAlchemy connection URL should explicitly use the psycopg dialect/driver form where appropriate.

### 7. Database session infrastructure

Create the minimum necessary database engine/session infrastructure.

Do not create repository/service abstractions just to wrap a single health query.

### 8. Configuration

Use `pydantic-settings` or a comparably typed settings approach.

At minimum support:

```text
DATABASE_URL
FRONTEND_ORIGIN
```

Configuration should come from environment variables / `.env` for local development.

Do not hardcode credentials or environment-specific URLs inside Python source.

### 9. Alembic

Configure Alembic correctly against the same database configuration.

No real domain table is required yet.

The project should support normal migration commands such as upgrade to head.

Do not invent a fake model just to generate an initial business migration.

### 10. Tests

Use pytest.

At minimum test:

```text
GET /api/v1/health/live
```

Verify HTTP 200 and the expected response body.

If practical without unnecessary complexity, add a readiness test that isolates database dependency cleanly. Do not over-engineer this.

---

## PostgreSQL / Docker Compose Requirements

Create a Docker Compose configuration for PostgreSQL only.

Use a current supported PostgreSQL image.

Expose the database for local backend access.

Use environment variables or clearly local development defaults appropriate for a developer machine.

Persist database data using a named Docker volume.

Do not add frontend or backend containers during AG-03.

Do not add pgAdmin unless specifically requested later.

---

## Frontend Requirements

### 1. React application

Use React 19 + TypeScript + Vite.

Remove default Vite demo content that is not useful to AssurGrid.

### 2. Router

Install and configure React Router.

Only a minimal route structure is needed.

A single home/foundation-status route is acceptable.

### 3. TanStack Query

Install and configure TanStack Query.

Use it to fetch the backend readiness endpoint.

Do not manually recreate server-state fetching with custom `useEffect` plumbing.

### 4. Minimal UI

Create a calm, simple AssurGrid foundation screen.

No elaborate design system is required yet.

The page should display something equivalent to:

```text
AssurGrid

Foundation status

API       Connected
Database  Connected
```

When the readiness call fails, the page should visibly communicate that the backend/database is unavailable rather than silently failing.

Keep the UI minimal and professional.

Do not build dashboards, sidebars, admin navigation, or fake application cards.

### 5. API access

Create a small frontend API layer or helper for the health request.

Do not scatter raw backend URLs throughout components.

Use environment-based frontend configuration if a backend base URL is needed.

---

## CORS Requirements

Configure FastAPI CORS using the configured frontend origin.

Typical local development origin:

```text
http://localhost:5173
```

Do not configure unrestricted wildcard origins as the default solution.

---

## Environment Files

Create a committed `.env.example` that documents required local configuration without real secrets.

Example variables:

```text
DATABASE_URL=postgresql+psycopg://assurgrid:assurgrid@localhost:5432/assurgrid
FRONTEND_ORIGIN=http://localhost:5173
```

If the frontend needs a variable such as `VITE_API_BASE_URL`, include it in the appropriate example environment file.

Make sure real `.env` files are ignored by Git.

---

## README Requirements

Create or update the root README so a developer can run the entire AG-03 foundation from a fresh clone.

The README should explain, in order:

1. Prerequisites
2. How to create local environment files
3. How to start PostgreSQL with Docker Compose
4. How to install backend dependencies
5. How to run Alembic migrations
6. How to start FastAPI
7. How to run backend tests
8. How to install frontend dependencies
9. How to start the Vite frontend
10. Which URLs to open
11. How to test `/api/v1/health/live`
12. How to test `/api/v1/health/ready`

Keep instructions precise and copy-paste friendly.

---

## Coding Style / Architecture Constraints

Prefer boring, explicit code over clever abstractions.

Avoid creating these unless a concrete implementation need appears:

```text
services/
repositories/
managers/
helpers/
utils/
factories/
interfaces/
```

Do not implement patterns merely because they are common in enterprise tutorials.

The user is learning the system deeply and must be able to understand and defend every important line.

Whenever choosing between two implementations of similar quality, prefer the one that is:

1. easier to read
2. easier to explain
3. easier to debug
4. less abstract
5. still production-respectable

---

## Build Sequence

Implement in this order unless a technical dependency requires a small adjustment:

1. Inspect the existing repository before changing anything.
2. Preserve any existing AssurGrid documentation and decisions.
3. Create/clean the repository structure.
4. Initialize backend dependencies.
5. Add typed configuration.
6. Create FastAPI application.
7. Add liveness endpoint.
8. Add PostgreSQL Docker Compose service.
9. Configure SQLAlchemy + psycopg.
10. Add readiness endpoint.
11. Configure Alembic.
12. Verify migrations can run.
13. Add backend tests.
14. Initialize React + TypeScript + Vite.
15. Add React Router.
16. Add TanStack Query.
17. Configure frontend API access.
18. Configure CORS.
19. Build minimal AssurGrid foundation status page.
20. Verify the browser can call readiness successfully.
21. Remove unnecessary generated files and demo code.
22. Update README with exact run instructions.
23. Run tests and relevant build/type-check commands.

---

## Validation Checklist

Before considering the task complete, verify all of the following:

### Backend

- FastAPI starts successfully.
- `/api/v1/health/live` returns HTTP 200.
- `/api/v1/health/ready` succeeds when PostgreSQL is running.
- `/api/v1/health/ready` reports failure appropriately when PostgreSQL is unavailable.
- SQLAlchemy uses psycopg.
- No async database code exists.
- Configuration is environment-based.
- Alembic is functional.
- pytest test(s) pass.

### Database

- PostgreSQL starts with Docker Compose.
- Database data persists through a named volume.
- No fake business tables exist.
- Only the normal `public` schema is required.

### Frontend

- Vite starts successfully.
- React can call the backend.
- TanStack Query performs the readiness request.
- The page clearly shows healthy/unhealthy foundation state.
- No default Vite demo UI remains.
- No fake AssurGrid business features are present.

### Repository

- `.env` files are ignored.
- `.env.example` files document required variables.
- README run instructions work.
- No speculative architecture or placeholder modules were introduced.

---

## Required Implementation Handoff

After implementation, provide a concise implementation report containing:

1. Files created
2. Files modified
3. Dependencies added
4. Commands run
5. Tests/build checks run and their results
6. Exact commands the user should run locally
7. Any assumptions made
8. Any deviations from this specification, with justification

Also explain the runtime request path in plain English:

```text
React
  → FastAPI
  → SQLAlchemy
  → psycopg
  → PostgreSQL
```

Do not proceed into AG-04 or any business functionality.

Stop once AG-03's Definition of Done is satisfied.
