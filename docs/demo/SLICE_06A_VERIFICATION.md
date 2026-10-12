# Slice 06a verification

Purpose: prepare organization-bound identity and application access without claiming authentication is implemented.

Changed files: `backend/app/db/schema.py`, `backend/migrations/versions/0003_identity.py`, `backend/tests/integration/test_registry_schema.py`, `backend/tests/integration/test_identity_schema.py`, `README.md`, `docs/demo/ARCHITECTURE_NOTES.md`, and this report.

Command run from repository root:

```sh
ASSURGRID_TEST_POSTGRES_BIN=/opt/homebrew/opt/postgresql@18/bin backend/.venv/bin/python -m pytest backend/tests -p no:cacheprovider -x --tb=short
```

Result: **114 passed** on PostgreSQL 18.6. Eleven warnings are existing Starlette/httpx and Alembic configuration deprecations exercised by the suite.

Coverage includes fresh/repeated migration, metadata comparison, upgrade/downgrade preservation of all 48 seeded applications, canonical/unique emails, the four provisional roles, rejection of unknown roles, cross-organization access and absent membership rejection, valid session/access creation, restricted deletion, duplicate grants/session tokens, malformed digest fields, and invalid expiry/revocation chronology. The complete existing registry, API, seed, and health suite also passes.

The test fixture creates and removes an isolated PostgreSQL cluster with a private Unix socket and no TCP listener. Only temporary invented test identities are inserted. The owner's database and environment files were not changed; no new dependency or frontend change is included.

Manual inspection: in a disposable database, apply `alembic -c backend/alembic.ini upgrade head`, then run `alembic -c backend/alembic.ini current`; expect `0003_identity`. Inspect the four new identity tables, which start empty. There is no new UI to click and no browser validation claimed for this schema-only slice.

`git diff --check` passes. Login, account seeding, cookie/CSRF behavior, logout invalidation, and backend authorization remain Slice 06b work. The development read API remains unauthenticated when enabled.
