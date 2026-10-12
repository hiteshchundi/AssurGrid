# Slice 06b — backend session authentication

Slice 06b replaced unauthenticated registry access with server-managed sessions. Slice 06c now adds the login screen and explicit [demo account setup](DEMO_ACCOUNTS.md). Foundation health remains public.

`POST /api/v1/auth/login` accepts only `email` and `password`. It requires the configured `FRONTEND_ORIGIN` in the Origin header, `APP_ENV=development`, and `DEMO_REGISTRY_ORGANIZATION_ID`. Active accounts must have active membership in that organization. The client cannot supply its own role or organization. Passwords use salted scrypt hashes; no plaintext password or raw session token is stored. Unknown users and incorrect passwords share the same 401 response, with a dummy password calculation for unknown accounts. Validation errors do not echo submitted passwords.

A successful login creates an eight-hour opaque session and returns `csrf_token`. Retain this token in memory for writes; do not put credentials in localStorage. The `assurgrid_session` cookie is HttpOnly, SameSite=Strict, scoped to `/api/v1`, and Secure when the configured frontend origin uses HTTPS. Re-login revokes the token previously carried by that browser. Other browser sessions remain independent.

`GET /api/v1/auth/me` returns user ID, organization ID, and the current membership role. Every protected call checks current account/membership activity, expiry, and revocation. `POST /api/v1/auth/logout` requires both the allowed Origin and the login response's token in `X-CSRF-Token`; it revokes the database session and deletes the cookie. Missing/invalid sessions return 401; rejected Origin/CSRF checks return 403. Database failures return a safe 503. Successful auth responses use `Cache-Control: no-store`.

Registry reads now derive organization scope from that session. Admin and Quality can read their organization's portfolio; Application Owner and Viewer can read only explicitly assigned applications. Both page counts and detail reads enforce this scope. Missing, foreign, and unassigned IDs return the same 404. Access assignment does not imply business/technical/quality ownership. No registry mutation endpoint is introduced, so role-based mutation tests await those endpoints. Future writes must use both role authorization and the shared CSRF check.

CORS allows credentials only for the existing configured frontend origin, with GET/POST and Accept, Content-Type, X-CSRF-Token. The frontend now sends credentialed requests and provides login/logout. `POST /api/v1/auth/csrf` requires a current session and trusted Origin and rotates the session CSRF digest, returning a fresh token with no-store. The UI obtains this token immediately before logout, including after reload; no token is stored in localStorage. Concurrent rotations from another tab can cause a safe 403; retry sign-out to obtain a fresh token. Production password login is disabled; this remains a localhost prototype with no login throttling, password recovery, SSO, or production authentication claim.

## Verification

Executed against an isolated PostgreSQL 18 cluster (no owner database changes):

```sh
ASSURGRID_TEST_POSTGRES_BIN=/opt/homebrew/opt/postgresql@18/bin backend/.venv/bin/python -m pytest backend/tests -p no:cacheprovider -x --tb=short
```

The suite covers real HTTP login/logout, session digests and cookies, invalid credentials, Origin/CSRF, replay after logout, re-login rotation, expiry, revocation, account/membership suspension, all four role scopes, live role/access changes, foreign/unassigned details, safe database errors, HTTPS cookie flags, and password-safe validation errors. Existing read API tests explicitly override the principal only to isolate query behavior; auth tests use real sessions and do not override authentication.

Manual verification requires a disposable test account created with `hash_password`; no account setup is silently applied. The automated integration fixture provides that account and tears it down. There is no browser check claimed for this backend-only slice. No migration or persistent demo data change is included.

Final result: **125 passed**, with 11 existing Starlette/httpx and Alembic deprecation warnings. `git diff --check` passes. The HTTPS test initially used a plain string in place of a validated URL; correcting that fixture produced the final passing run.

Changed files: `.env.example`, `README.md`, `backend/app/api/router.py`, `backend/app/main.py`, `backend/app/modules/applications/repository.py`, `backend/app/modules/applications/router.py`, `backend/app/modules/auth/__init__.py`, `backend/app/modules/auth/router.py`, `backend/app/modules/auth/security.py`, `backend/tests/integration/test_application_api.py`, `backend/tests/integration/test_auth_api.py`, `backend/tests/test_application_api.py`, `docs/demo/ARCHITECTURE_NOTES.md`, `docs/demo/DEMO_SCRIPT.md`, `docs/demo/REGISTRY_API.md`, and this report. The owner's untracked build contract remains untouched.

Suggested commit: `feat(auth): enforce session-based registry access`.
