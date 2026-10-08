# AG-03 — Locked Engineering Decisions

This file records the implementation decisions made during AG-03 so later AssurGrid work does not silently drift from the agreed foundation.

## Repository

- Use a single Git repository for the AssurGrid application.
- Frontend and backend live in the same repository.
- Do not create future business modules until they are actually required.

## Backend

- Language: Python
- Framework: FastAPI
- API prefix: `/api/v1`
- Initial endpoints:
  - `GET /api/v1/health/live`
  - `GET /api/v1/health/ready`
- Backend remains authoritative for future application-level authorization.
- `main.py` should remain small and focused on application assembly.

## Database

- Database engine: PostgreSQL
- Python driver: psycopg
- Database toolkit / ORM: SQLAlchemy
- Database access model: synchronous initially
- Connection pooling: managed through SQLAlchemy
- Migration tool: Alembic
- Initial database schema: `public`
- No real domain tables are created during AG-03.
- No fake/sample tables are created merely to prove connectivity.

## Local Development

- PostgreSQL runs through Docker Compose.
- Backend runs directly on the developer machine.
- Frontend runs directly on the developer machine.
- Do not containerize the full stack during AG-03.

## Configuration

- Use environment-based configuration.
- Use a typed settings layer such as `pydantic-settings`.
- Required configuration should fail loudly if missing.
- `.env` is local-only and ignored by Git.
- `.env.example` is committed with safe placeholders.

## Frontend

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query
- Frontend should consume the readiness endpoint and display foundation status.

## Security

- Frontend visibility is not security.
- Future RBAC enforcement belongs in the backend/application layer.
- PostgreSQL credentials and infrastructure security remain separate concerns.
- Do not implement login or RBAC during AG-03.

## CORS

- Explicitly allow the configured frontend origin.
- Avoid unrestricted wildcard origins as the production default.

## Testing

- Backend test framework: pytest
- At minimum, test the liveness endpoint during AG-03.

## Architecture Discipline

- Continue with the modular monolith architecture agreed in AG-02.
- Do not introduce microservices.
- Do not introduce async database access without evidence that AssurGrid needs it.
- Do not introduce speculative abstractions or generic folders without a concrete requirement.
- Favor the smallest clear implementation that satisfies the current chapter.
- Every file, dependency, and abstraction must have a reason to exist.

## Definition of Completion

AG-03 is considered complete only when the browser can successfully exercise this complete path:

```text
React
  → FastAPI
  → SQLAlchemy
  → psycopg
  → PostgreSQL
```

and the frontend can distinguish at least:

```text
API alive
Database reachable / not reachable
```
