# Slice 06c — login, logout, and four demo account categories

Purpose: let a reviewer enter the fictional governance workspace and see only the applications authorized for their current role.

Changes: React login form, protected routes, role/sign-out header, credentialed fetches, session error handling, per-user/role query keys, cache removal on account changes, Origin-checked CSRF recovery after reload, and a separate interactive account seed command. No migration or dependency added. The owner's database/environment and checked-in registry exports were not modified.

Data: explicit seed creates four synthetic users/memberships and four application grants (Owner: three; Viewer: one). Admin/Quality portfolio access comes from backend roles. User IDs and assignments are stable; salted hashes are intentionally nondeterministic on first creation and preserved on repeat runs. Passwords are supplied privately by the operator, with no default or export.

Commands executed:

```sh
ASSURGRID_TEST_POSTGRES_BIN=/opt/homebrew/opt/postgresql@18/bin backend/.venv/bin/python -m pytest backend/tests -p no:cacheprovider -x --tb=short
pnpm --dir frontend typecheck
pnpm --dir frontend build
git diff --check
```

Backend: **131 passed**, 11 existing dependency deprecation warnings. Tests exercise account seed repeatability/hash preservation, all roles/grants, refusal of altered account/password/role, missing-registry/password guards, and CSRF recovery rotation/origin/logout. Existing authentication, schema, API, seed, and health checks still pass. Integration tests use a disposable PostgreSQL 18 cluster with no TCP listener. The initial assignment test caught CI suffixes that did not match the existing catalog; corrected to CDMS-002 and QMS-003 before the passing run.

Frontend: typecheck and production build pass. React review covered hook order, labeled inputs and autocomplete, pending/error states, direct imports, TanStack Query fetching, and no browser credential persistence. Registry authorization remains in the API. Browser verification found that clearing the entire query cache could delay session observer updates; preserving the session query while removing other cached data fixed the transition.

Browser → API → database → UI verified using temporary synthetic accounts in a separate disposable cluster:

- Anonymous entry redirects to sign-in; incorrect password shows a safe error.
- Owner login shows exactly 3 assigned applications; reload preserves the session.
- Sign-out after reload succeeds through CSRF recovery and removes protected content.
- Admin login shows 48 applications. Switching to Viewer shows only 1; prior Admin rows are absent.
- Viewer can open LIMS; a direct CDMS detail URL returns the not-found state.
- Login remains readable at 390×844, with labeled inputs and no horizontal overflow visible.
- Browser console reported no errors or warnings during these checks.

Manual reproduction: follow [demo account setup](DEMO_ACCOUNTS.md), then repeat those journeys. Login screen screenshot is saved with this chat. Quality scope is covered by backend tests; a separate Quality browser login is not claimed. The interactive CLI prompt itself was not exercised against the owner's database. A noninteractive invocation with an unreachable local demo URL correctly refused before connecting (exit 1), requiring hidden interactive input.

Limitations: no production authentication claim, rate limiting, password reset, or user administration. Session polling checks activity every ten seconds; backend authorization checks each protected request. No governance policies or health calculations added.

Changed files: backend `app/demo/identity.py`, `scripts/seed_accounts.py`, `app/modules/auth/router.py`, `tests/integration/test_demo_accounts.py`, `tests/integration/test_auth_api.py`; frontend `src/api/auth.ts`, `src/api/applications.ts`, `src/features/auth/Auth.tsx`, `src/features/applications/ApplicationRegistry.tsx`, `src/features/applications/ApplicationDetail.tsx`, `src/main.tsx`, `src/routes/AppLayout.tsx`, `src/styles/global.css`; `README.md`; demo `AUTH_API.md`, `ARCHITECTURE_NOTES.md`, `DEMO_SCRIPT.md`, `DEMO_ACCOUNTS.md`, and this report.

Suggested commit: `feat(auth): add browser login and synthetic demo accounts`.

Final logout regression: an isolated fresh API log contained 20 lines through the login/detail/logout journey, including one CSRF POST and one logout POST, with no request burst. Sign-in restored the previously requested CDMS detail URL. Temporary frontend/API processes were stopped and the preview database removed after verification.
