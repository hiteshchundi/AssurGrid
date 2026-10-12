# AssurGrid

AssurGrid is a personal portfolio prototype of a governance workspace for regulated computerized systems. It is being built to help Quality, Governance, and Application Owners answer: **what exists, what changed, what is due, what is missing, and where is the evidence?**

Application ownership, periodic compliance review (PCR) dates, changes, audit findings, and document references are often scattered across spreadsheets and enterprise tools. AssurGrid's intended workflow brings that information into an application-centered view, with traceable deadlines and drill-down from portfolio to application, activity, and evidence.

Lifecycle state, validation state, and ongoing governance health answer different questions. An application can be **Operational / Validated / Overdue** when its periodic review is late. The prototype will derive governance health from applicable obligations and organization-configured rules while preserving policy and activity history.

## Current implementation

**AG-03 foundation only:** React displays API and database connection status using FastAPI health endpoints, synchronous SQLAlchemy/psycopg access, and PostgreSQL. Alembic has an empty baseline migration. The setup below runs this foundation.

The application registry, login, policies, obligations, governance dashboard, change/QA workflow, and demo dataset are planned; they are not implemented yet.

## Prototype scope and data

AssurGrid is intended to provide oversight alongside authoritative change-management, quality, and document repositories. Replacing those systems, executing validation tests, authoring controlled documents, and generic project management are outside this prototype's scope.

All future internal organization, application, owner, change, and document records will be invented, reproducible, and labeled **SYNTHETIC DEMO DATA**. No internal company or client records will be used. Any genuine public-reference dataset will remain separately identified with its source and retrieval metadata, outside application governance metrics.

This is not production-validated software and makes no regulatory certification or compliant electronic-signature claim. No live ServiceNow, Veeva, VQD, GCMS, or enterprise SSO integration exists. Planned CSV adapters and outbound updates will be explicitly simulated; example review frequencies and deadlines are fictional organization policies, not universal regulatory requirements.

## Build instructions and source of truth

The [prototype build contract](AssurGrid_CODEX_PROTOTYPE_BUILD.md) governs the incremental build order and approval gates alongside the owner's latest explicit instructions. Each small slice is implemented, checked, and reviewed before explicit approval to commit; pushing requires separate approval.

The existing foundation follows [AG-03 decisions](prod-docs/AG-03_Decisions.md), the [foundation build](prod-docs/AG-03_Foundation_Build.md), and the [initial build prompt](CODEX_AG-03_Initial_Build_Prompt.md). Preserve those implemented constraints and the locked [product philosophy](prod-docs/AG-00-product-philosophy.md), [product design](prod-docs/AG-01_Product_Design.md), and [architecture](prod-docs/AG-02_System_Architecture.md). The [older implementation specification](AssurGrid_Codex_Implementation_Spec.md) supplies non-conflicting engineering guidance. See the [AG-03 implementation report](docs/AG-03_Implementation_Report.md) for previous verification evidence.

## Prerequisites

- Python 3.11 or newer (`python3 --version`)
- Node.js 22.12 or newer, and pnpm 11.19.0 (`node --version`, `pnpm --version`)
- Docker with Docker Compose v2, with the Docker engine running (`docker compose version`)
- Git

On macOS, if Docker Desktop is installed without system-wide CLI links, make its bundled CLI available in the current terminal:

```sh
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
```

Install pnpm with `npm install --global pnpm@11.19.0` if needed. PostgreSQL runs through Compose; FastAPI and Vite run directly on your machine.

All commands below start from the repository root unless stated otherwise.

## 1. Create local environment files

```sh
cp .env.example .env
cp frontend/.env.example frontend/.env
```

These files are ignored by Git. The example credentials are disposable local development values. Keep `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`, and `DATABASE_URL` consistent. If a password contains special URL characters, percent-encode it in `DATABASE_URL` only.

`DATABASE_URL` must use `postgresql+psycopg://`. Its example sets a three-second driver connection timeout without changing SQLAlchemy pool defaults. `FRONTEND_ORIGIN` is the browser origin, without a path. `VITE_API_BASE_URL` is the backend origin; restart Vite when changing it.

The backend loads the root `.env` using a path relative to its settings module, independent of your working directory. Missing required settings fail validation at startup.

## 2. Start PostgreSQL

```sh
docker compose --env-file .env -f infra/compose.yaml up -d --wait
docker compose --env-file .env -f infra/compose.yaml ps
```

PostgreSQL 18 binds to localhost only. Its data is kept in the named `postgres_data` volume, mounted at `/var/lib/postgresql` for the PostgreSQL 18 image layout. If port 5432 is occupied, change `POSTGRES_PORT` and the port in `DATABASE_URL` together.

Changing PostgreSQL initialization credentials in `.env` does not change credentials in an already initialized volume.

## 3. Install backend dependencies

```sh
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -e 'backend[dev]'
```

The optional `dev` dependencies install pytest and the HTTP test client. `backend/pyproject.toml` lists the direct dependencies and compatibility ranges.

## 4. Apply migrations

```sh
alembic -c backend/alembic.ini upgrade head
alembic -c backend/alembic.ini current
```

The expected revision is `0001_foundation`. It is intentionally empty: only Alembic's tracking table is created in `public`. No business or sample tables exist. Alembic and FastAPI use the same environment settings.

## 5. Start FastAPI

With the virtual environment activated, in a terminal at the repository root:

```sh
uvicorn app.main:app --reload --host localhost --port 8000
```

The liveness endpoint does not connect to PostgreSQL. Readiness uses a synchronous SQLAlchemy session to execute `SELECT 1` through psycopg. Connection failures return HTTP 503 and a safe JSON body, and log the exception type without credentials.

## 6. Run backend tests

In another terminal at the root:

```sh
source backend/.venv/bin/activate
python -m pytest backend/tests
```

Tests isolate the database dependency. They verify liveness without database access, successful readiness, safe failure while liveness remains healthy, and configured-origin CORS. They do not need a running PostgreSQL server.

## 7. Install frontend dependencies

```sh
cd frontend
pnpm install --frozen-lockfile
```

## 8. Start Vite

From `frontend/`:

```sh
pnpm dev
```

Vite uses port 5173 with `strictPort` so it cannot silently switch away from the configured CORS origin. React Router serves the foundation page at `/`; TanStack Query fetches liveness and readiness independently. Checks run on load, every ten seconds while the page is active, on window focus, and when clicking **Check again**. A five-second browser timeout bounds each check.

The page distinguishes **Connected**, **Unavailable**, **Checking**, and **Unknown**. If the backend cannot be reached, database status is unknown rather than claiming a database diagnosis. A failed refetch takes precedence over cached healthy data.

## 9. Open the application

- Frontend: <http://localhost:5173>
- API documentation: <http://localhost:8000/docs>
- Liveness: <http://localhost:8000/api/v1/health/live>
- Readiness: <http://localhost:8000/api/v1/health/ready>

## 10. Verify health endpoints

From the root or any terminal:

```sh
curl -i http://localhost:8000/api/v1/health/live
curl -i http://localhost:8000/api/v1/health/ready
```

Liveness: HTTP 200 with `{"status":"ok"}`.

Readiness with PostgreSQL running: HTTP 200 with `{"status":"ready","database":"connected"}`.

To verify the failure path without deleting data:

```sh
docker compose --env-file .env -f infra/compose.yaml stop postgres
curl -i http://localhost:8000/api/v1/health/live
curl -i http://localhost:8000/api/v1/health/ready
```

Liveness stays HTTP 200; readiness returns HTTP 503 with `{"status":"not_ready","database":"unavailable"}`. The browser shows API connected and database unavailable. Restart PostgreSQL:

```sh
docker compose --env-file .env -f infra/compose.yaml start postgres
```

Wait for the next check, or click **Check again**. With SQLAlchemy's default pool, a connection left stale by a database restart can fail one check before the next check reconnects.

Stopping FastAPI instead should show API unavailable and database unknown. Restart it using step 5.

## Frontend checks

From `frontend/`:

```sh
pnpm typecheck
pnpm build
```

The build type-checks TypeScript and produces static files in `frontend/dist/`.

## Shutdown

Stop the frontend and backend with Ctrl+C, then from the root:

```sh
docker compose --env-file .env -f infra/compose.yaml down
```

The named volume survives shutdown. No shutdown command in this guide deletes database data.

## Runtime path

React asks FastAPI for readiness. FastAPI borrows a synchronous SQLAlchemy session. SQLAlchemy sends the explicit `SELECT 1` query through the psycopg PostgreSQL driver. PostgreSQL returns the result; FastAPI returns JSON; TanStack Query updates the status shown by React.

```text
Browser → React → FastAPI → SQLAlchemy → psycopg → PostgreSQL
```

## Layout

- `backend/app/`: application assembly, typed settings, health routes, database sessions
- `backend/migrations/`: Alembic configuration and empty baseline revision
- `backend/tests/`: isolated API tests
- `frontend/src/`: API helper, route, React entry point, minimal styles
- `infra/compose.yaml`: PostgreSQL only
- `prod-docs/`: preserved product and architecture source documents
- `docs/AG-03_Implementation_Report.md`: implementation and verification evidence

No AG-04 or business functionality is implemented.
