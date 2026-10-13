# Slice 07c — authorized policy history and application/date resolution

Product purpose: inspect which fictional review rules apply to an authorized application on a date, while retaining the previous policy version and exposing missing/conflicting configuration.

Changes: authenticated bounded catalog and version/rule history for Admin/Quality; application-scoped date resolution for all authorized roles; typed query/response contracts; safe 503 handling and no-store responses. Owner/Viewer cannot read the organization administration catalog/history. Resolution returns explicit missing/conflicting configuration with no rules when unusable. No policy-edit endpoint exists.

Files: `backend/app/api/router.py`; `backend/app/modules/policies/__init__.py`, `schemas.py`, `repository.py`, `router.py`; `backend/tests/integration/test_policy_api.py`; `backend/tests/test_policy_api.py`; `README.md`; `docs/demo/DEMO_POLICIES.md`, `DEMO_SCRIPT.md`, `ARCHITECTURE_NOTES.md`, `POLICY_API.md`, and this report.

Database/data changes: none. Tests seed temporary synthetic records in a disposable PostgreSQL 18 cluster. The owner's database, `.env`, and checked-in fixtures were not modified. No migration/dependency or frontend change.

Exact commands executed:

```sh
ASSURGRID_TEST_POSTGRES_BIN=/opt/homebrew/opt/postgresql@18/bin backend/.venv/bin/python -m pytest backend/tests -p no:cacheprovider -x --tb=short
git diff --check
```

Result: **178 passed**, 17 existing Starlette/httpx and Alembic deprecation warnings. New real-login integration checks cover 401, Admin/Quality history and pagination, Owner/Viewer 403 administration access with assigned resolution, foreign/missing/unassigned isolation, date-boundary frequency changes, Medium GxP applicability, missing/inactive/empty/conflicting configuration, invalid/unknown inputs, and unsupported writes. Unit checks verify safe database failures without credential/SQL disclosure. All previous tests remain passing.

Manual check: follow [policy setup](DEMO_POLICIES.md) and [API contract](POLICY_API.md). With an authenticated Admin session inspect High GxP history, then resolve LIMS for 2026-06-30 and 2026-07-01: expect PCR 24 and 12 months respectively. An assigned Viewer can resolve LIMS but receives 403 for the administration catalog. There is no new browser policy page and no browser verification claimed for this backend-only slice.

Security/data caveats: resolution uses the application's currently stored profile, not reconstructed historical attributes. It does not calculate due dates/health, apply overrides, publish policy, or enforce historical immutability for privileged direct SQL. Reads produce no business transitions or audit events. Future policy mutation requires audited publication and history protection.

Diff review: status and whitespace checks reviewed; the owner's untracked build contract remains unstaged. Suggested commit: `feat(policies): add scoped history and date resolution API`.
