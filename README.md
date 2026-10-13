# AssurGrid

AssurGrid is a personal portfolio prototype of a governance workspace for regulated computerized systems. It is being built to help Quality, Governance, and Application Owners answer: **what exists, what changed, what is due, what is missing, and where is the evidence?**

Application ownership, periodic compliance review (PCR) dates, changes, audit findings, and document references are often scattered across spreadsheets and enterprise tools. AssurGrid's intended workflow brings that information into an application-centered view, with traceable deadlines and drill-down from portfolio to application, activity, and evidence.

Lifecycle state, validation state, and ongoing governance health answer different questions. An application can be **Operational / Validated / Overdue** when its periodic review is late. The prototype will derive governance health from applicable obligations and organization-configured rules while preserving policy and activity history.

## Current implementation

**Working prototype: sign-in, role-scoped registry list/details, and foundation status.** The API checks current session, organization membership, and application access on every read. Admin/Quality see the fictional portfolio; Owner/Viewer see their assigned applications. Login/logout and session reload are integrated into the browser.

Registry seeding and four-category demo account setup are explicit local commands. No passwords are checked in or assigned automatically. Policy storage and an explicit reproducible policy seed are available. Authenticated policy history and application/date resolution APIs are available; policy editing, obligations, governance dashboard, and change/QA workflow remain planned. See the [policy API contract](docs/demo/POLICY_API.md). Governance is unavailable and business/technical/quality ownership is not recorded. See [demo account setup](docs/demo/DEMO_ACCOUNTS.md) and [Slice 06c verification](docs/demo/SLICE_06C_VERIFICATION.md).

## Prototype scope and data

AssurGrid is intended to provide oversight alongside authoritative change-management, quality, and document repositories. Replacing those systems, executing validation tests, authoring controlled documents, and generic project management are outside this prototype's scope.

All internal demo organization, application, owner, change, and document records are or will be invented, reproducible, and labeled **SYNTHETIC DEMO DATA**. No internal company or client records will be used. Any genuine public-reference dataset will remain separately identified with its source and retrieval metadata, outside application governance metrics.

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

The expected revision is `0004_policy_schema`. The original empty `0001_foundation` baseline is preserved. Migration `0002_application_registry` adds organization and application tables; `0003_identity` adds accounts, memberships, application access, and session storage without seed rows. Migration `0004_policy_schema` adds control definitions, policies, effective versions, and control rules, using PostgreSQL’s `btree_gist` extension to reject overlapping version periods. The migration role must be able to install that extension if absent. Migrations insert no policy rows; the separate [policy seed command](docs/demo/DEMO_POLICIES.md) creates the fictional fixtures. Alembic and FastAPI use the same environment settings. Upgrading preserves existing registry and account data. Downgrading 0004 removes policy tables only and retains the potentially shared extension. Downgrading 0003 removes identity data but preserves the registry; downgrading 0002 removes registry data too. Use downgrade only in a disposable database.

## 5. Start FastAPI

For the optional 48-application dataset, follow the [demo-data instructions](mock-data/README.md) to create and seed a separate `assurgrid_demo` database. Preview without a database using `python backend/scripts/seed_demo.py --as-of 2026-10-12 --dry-run`. No seed runs automatically during migration or API startup.

With the virtual environment activated, in a terminal at the repository root:

```sh
uvicorn app.main:app --reload --host localhost --port 8000
```

The liveness endpoint does not connect to PostgreSQL. Readiness uses a synchronous SQLAlchemy session to execute `SELECT 1` through psycopg. Connection failures return HTTP 503 and a safe JSON body, and log the exception type without credentials.

### Local authenticated registry API

The variables below configure the development login organization. After registry seeding, run the [demo account setup](docs/demo/DEMO_ACCOUNTS.md) before signing in. After seeding `assurgrid_demo`, keep its `DATABASE_URL` environment override and set the following before starting/restarting FastAPI:

```sh
export APP_ENV=development
export DEMO_REGISTRY_ORGANIZATION_ID=becdd76c-490f-52a1-9247-9f6a6845d774
uvicorn app.main:app --reload --host localhost --port 8000
```

This UUID identifies the fictional organization in `mock-data/generated/organizations.csv`. Login returns 503 if that scope is unset or `APP_ENV` is not `development`. Registry reads require an active session and authorized application scope; a missing session returns 401. Keep the password-login prototype local and use synthetic data only. The provisional role matrix does not finalize AG-04.

```sh
curl 'http://localhost:8000/api/v1/applications?search=NSB-LIMS-001'
curl 'http://localhost:8000/api/v1/applications?classification=Non-GxP&page_size=100'
```

Expect one LIMS result and seven non-GxP results from the frozen seed. Open `/api/v1/applications/{id}` using an item's UUID to inspect it. See the [registry API contract](docs/demo/REGISTRY_API.md) for fields, filters, status codes, and limitations.

## 6. Run backend tests

In another terminal at the root:

```sh
source backend/.venv/bin/activate
python -m pytest backend/tests
```

The four health tests isolate the database dependency. They verify liveness without database access, successful readiness, safe failure while liveness remains healthy, and configured-origin CORS. They do not need a running PostgreSQL server. Registry integration tests are skipped unless you explicitly provide PostgreSQL 18 binaries:

```sh
# macOS/Homebrew example; use your installed PostgreSQL 18 bin directory.
ASSURGRID_TEST_POSTGRES_BIN=/opt/homebrew/opt/postgresql@18/bin \
  python -m pytest backend/tests -x --tb=short
```

The integration fixture creates and stops its own temporary PostgreSQL cluster, listens only on a private Unix socket, and removes its temporary files afterward. It does not connect to the development database or use its credentials. These tests require a Unix-like environment with permission to start PostgreSQL and allocate shared memory. They verify migrations, sample insert/read, organization-scoped CI uniqueness, foreign keys, required fields, independent states, and transaction rollback. See [architecture notes](docs/demo/ARCHITECTURE_NOTES.md) and the [current demo steps](docs/demo/DEMO_SCRIPT.md).

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

Vite uses port 5173 with `strictPort` so it cannot silently switch away from the configured CORS origin. React Router redirects `/` to `/applications`, serves details at `/applications/:id`, and keeps health checks at `/foundation`. Registry filters and page numbers live in the URL and are preserved when returning from details. Without the optional API scope/seed setup, the registry shows an unavailable or empty state.

On `/foundation`, TanStack Query fetches liveness and readiness independently. Checks run on load, every ten seconds while the page is active, on window focus, and when clicking **Check again**. A five-second browser timeout bounds each check. Registry reads also time out after five seconds, refresh on request/focus as needed, and hide cached rows after a failed refresh.

The page distinguishes **Connected**, **Unavailable**, **Checking**, and **Unknown**. If the backend cannot be reached, database status is unknown rather than claiming a database diagnosis. A failed refetch takes precedence over cached healthy data.

## 9. Open the application

- Frontend: <http://localhost:5173>
- Registry: <http://localhost:5173/applications>
- Foundation status: <http://localhost:5173/foundation>
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
- `backend/migrations/`: Alembic configuration, original baseline, and registry migration
- `backend/tests/`: isolated API tests and disposable PostgreSQL integration tests
- `frontend/src/`: API helper, route, React entry point, minimal styles
- `infra/compose.yaml`: PostgreSQL only
- `prod-docs/`: preserved product and architecture source documents
- `docs/AG-03_Implementation_Report.md`: implementation and verification evidence
- `mock-data/`: synthetic registry snapshots, source manifest, and safe seed instructions

AG-04 and user-facing business workflows are not implemented. The registry schema, synthetic seed, and read-only API are the first domain slices.
