# AG-03 implementation report

Date: 8 October 2026.

## Scope and source precedence

Implemented the foundation described by `CODEX_AG-03_Initial_Build_Prompt.md`, `prod-docs/AG-03_Foundation_Build.md`, and `prod-docs/AG-03_Decisions.md`. These milestone-specific documents supersede the older specification where it asks for a registry slice, different health routes, direct psycopg-only access, or placeholder directories.

The owner explicitly requested replacing every folder in the existing GitHub repository and starting anew. The prior DBE curriculum, schema, seed, and placeholder folders are removed. On the owner's subsequent explicit request, the published `main` branch starts from a single fresh root commit containing AG-03; its reachable history does not include the prior commits. All seven supplied local Markdown source documents remain unchanged.

## Files created

- Root `.env.example`.
- `backend/pyproject.toml` and five package `__init__.py` files.
- `backend/app/main.py`: FastAPI assembly and explicit CORS.
- `backend/app/core/config.py`: required typed settings, root environment-file loading, psycopg URL and frontend-origin validation.
- `backend/app/api/router.py` and `backend/app/api/routes/health.py`: versioned liveness/readiness contracts.
- `backend/app/db/session.py`: lazy synchronous engine, default connection pooling, request-scoped session cleanup, empty schema metadata.
- `backend/alembic.ini`, `backend/migrations/env.py`, `backend/migrations/script.py.mako`, and `backend/migrations/versions/0001_foundation.py`: online/offline migration infrastructure and an empty baseline.
- `backend/tests/conftest.py` and `backend/tests/test_health.py`: four isolated API tests.
- `infra/compose.yaml`: PostgreSQL 18, required credentials, localhost port binding, health check, named volume.
- `frontend/package.json`, `frontend/pnpm-lock.yaml`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/index.html`, and `frontend/.env.example`.
- `frontend/src/main.tsx`, `frontend/src/vite-env.d.ts`, `frontend/src/api/health.ts`, `frontend/src/routes/FoundationStatus.tsx`, and `frontend/src/styles/global.css`.
- This report.

## Files modified and removed

The existing root README and `.gitignore` are replaced with current AG-03 instructions and exclusions. All previous tracked folders and `.editorconfig` are removed at the owner's request. Supplied source documents are newly added to Git without edits.

Real `.env` files, Python virtual environments, caches, dependency directories, and generated frontend assets are excluded from Git.

## Dependencies

Backend: FastAPI, Uvicorn, SQLAlchemy 2.0, psycopg 3 with binary distribution, Alembic, pydantic-settings. Development: pytest and httpx.

Frontend: React 19, React DOM 19, React Router 7, TanStack Query 5. Tooling: TypeScript 5.9, Vite 8, React Vite plugin 6, React type declarations, pnpm 11.19.0. The committed pnpm lockfile records exact resolved versions.

Each dependency serves the required foundation; no business modules or cloud dependencies were added. SQL remains explicit (`SELECT 1`), despite using SQLAlchemy for connection and session management.

## Commands and validation

Commands used ordinary project paths except for bundled Python/Node/pnpm executables available on the build machine. Network installation and local server commands required sandbox approval.

| Check / command | Result |
| --- | --- |
| Read supplied source documents; inspect remote Git tree/history | Completed before replacement |
| `python3 -m venv backend/.venv` | Passed |
| `python -m pip install -e 'backend[dev]'` | Passed after enabling package-registry access |
| `python -m pytest backend/tests` | 4 passed |
| `pnpm install` | Passed; lockfile generated |
| `pnpm run build` | TypeScript and production build passed |
| `initdb`, `pg_ctl start`, `createdb` | Isolated native PostgreSQL 18 cluster created under `/private/tmp`, port 55432 |
| `alembic -c backend/alembic.ini upgrade head` | Passed on PostgreSQL |
| `alembic -c backend/alembic.ini current` | `0001_foundation (head)` |
| `alembic -c backend/alembic.ini downgrade base`, then `upgrade head` | Passed on PostgreSQL |
| PostgreSQL catalog query | Only `public.alembic_version`; no domain tables |
| Uvicorn startup | Passed |
| Vite startup | Passed on configured port 5173 |
| Chrome → React → FastAPI → SQLAlchemy → psycopg → PostgreSQL | Both API and database displayed Connected; server recorded HTTP 200 for both checks |
| Stop temporary PostgreSQL and check again | API Connected, database Unavailable; readiness HTTP 503, liveness HTTP 200 |
| Restart temporary PostgreSQL and check again | Both Connected again |
| Stop FastAPI and check again | API Unavailable, database Unknown, visible failure notice despite prior cached healthy data |
| Docker Desktop installation | Installed from the official Homebrew-downloaded installer; Docker engine 29.8.2 and Compose 5.5.1 start successfully |
| `docker compose --env-file .env -f infra/compose.yaml config --quiet` | Passed |
| `docker compose --env-file .env -f infra/compose.yaml up -d --wait` | PostgreSQL container healthy on localhost port 55433 |
| Alembic upgrade, current, downgrade, re-upgrade against Docker PostgreSQL | Passed; `0001_foundation (head)` |
| Docker-backed API checks and browser | Liveness and readiness HTTP 200; API and database Connected |
| `docker compose ... down` while FastAPI remains running | Liveness HTTP 200; readiness HTTP 503; browser API Connected and database Unavailable |
| `docker compose ... up -d --wait` after container removal | Existing Alembic revision retained without rerunning migrations; readiness and browser recover |
| Named-volume inspection | `assurgrid_postgres_data` mounted at `/var/lib/postgresql`; saved migration revision matches before and after recreation |

The installed Starlette test client emits a deprecation warning for httpx. All four tests pass; the warning does not affect runtime behavior.

Browser testing exposed an initial liveness query returning `undefined`, which TanStack Query rejects. The helper was corrected to return the validated `{status: 'ok'}` data before the successful checks above.

## Exact local commands

Follow these from the repository root, using separate terminals for the backend and frontend:

```sh
cp .env.example .env
cp frontend/.env.example frontend/.env
docker compose --env-file .env -f infra/compose.yaml up -d --wait
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -e 'backend[dev]'
alembic -c backend/alembic.ini upgrade head
python -m pytest backend/tests
uvicorn app.main:app --reload --host localhost --port 8000
```

Frontend terminal:

```sh
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

Open <http://localhost:5173>. Verify APIs:

```sh
curl -i http://localhost:8000/api/v1/health/live
curl -i http://localhost:8000/api/v1/health/ready
```

The README includes shutdown, outage/recovery checks, and frontend build commands.

## Assumptions and implementation choices

- Use the existing remote default branch, `main`, with one fresh root commit and a force-with-lease update, as explicitly requested by the owner. Replace the branch tree and reachable history together rather than publishing an intermediate empty repository.
- The empty Alembic baseline is migration infrastructure, not a fake domain table.
- Preserve the existing local `prod-docs/` location instead of moving source documents.
- Fetch liveness and readiness independently through TanStack Query to distinguish an API failure from a database failure.
- Expected readiness HTTP 503 is valid health data, so the page can display a known database outage. Network failures display database Unknown.
- Use SQLAlchemy defaults without pool tuning; a stale pooled connection may fail one check following a database restart, then recover on the next poll.
- PostgreSQL 18 is supported according to the [PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/); use its [official container mount layout](https://github.com/docker-library/docs/blob/master/postgres/README.md).

## Docker verification completion

Docker Desktop was installed during the follow-up session. Homebrew's system-wide linking step required administrator access and failed, so the official downloaded app was copied to `/Applications/Docker.app`. Docker's bundled CLI is available at `/Applications/Docker.app/Contents/Resources/bin/docker`; add that directory to PATH when no system-wide CLI link exists. Startup initially failed while installing optional Rosetta emulation; disabling that optional setting allowed the native Apple Silicon engine to start.

Port 5432 was already occupied. The ignored local `.env` now consistently uses port 55433 for `POSTGRES_PORT` and `DATABASE_URL`; the committed example retains its portable default of 5432. Existing services were not stopped.

The full Docker-backed request path, migration lifecycle, failure/recovery behavior, and named-volume persistence have now been verified. Data persistence was proved using the existing Alembic tracking row, without creating fake tables or test domain data. Earlier native PostgreSQL checks remain recorded above as prior evidence.

The normal local run instructions remain unchanged. No implementation deviation from the mandated stack or milestone scope remains.

No production deployment, authentication, users, roles, audit trail, registry, governance, documents, notifications, integrations, jobs, or fake data are implemented.

## Runtime request path

React asks FastAPI whether the foundation is ready. FastAPI obtains a synchronous SQLAlchemy session, which borrows a connection from its pool. SQLAlchemy sends `SELECT 1` using psycopg. PostgreSQL returns the value. FastAPI sends a small JSON result, and TanStack Query updates React's displayed database status. A separate liveness request establishes whether the API itself is usable.

```text
React → FastAPI → SQLAlchemy → psycopg → PostgreSQL
```
