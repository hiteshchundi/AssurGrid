# Slice 07a — policy schema and integrity

Product purpose: preserve which organization policy version and review rules apply over a dated period, so later obligations can retain their governing policy reference.

What changed: four SQLAlchemy Core tables and independent Alembic migration `0004_policy_schema`; organization-bound foreign keys; stable control/policy keys; positive version/month frequencies; nonnegative due-soon thresholds; unique version/control rules; and a database exclusion constraint preventing overlapping versions of one policy. Periods are start-inclusive/end-exclusive, with optional unbounded end. Rules and applicability belong to individual versions.

Files changed:

- `backend/app/db/schema.py`
- `backend/migrations/versions/0004_policy_schema.py`
- `backend/tests/integration/test_registry_schema.py`
- `backend/tests/integration/test_policy_schema.py`
- `README.md`
- `docs/demo/ARCHITECTURE_NOTES.md`
- `docs/demo/SLICE_07A_VERIFICATION.md`

Database safety: migration adds four empty tables and installs `btree_gist` if absent. The migration role needs extension-install permission. Downgrade removes only these policy tables and keeps the potentially shared extension. No owner's database or `.env` was changed. Existing migrations are untouched.

Data changes: none outside disposable test fixtures. Tests create two fictional policy versions with different PCR frequencies, plus temporary registry/account records for preservation checks. These are not a deployed demo policy seed and do not imply mandated regulatory frequencies.

Exact verification command executed from repository root:

```sh
ASSURGRID_TEST_POSTGRES_BIN=/opt/homebrew/opt/postgresql@18/bin backend/.venv/bin/python -m pytest backend/tests -p no:cacheprovider -x --tb=short
```

Result: **150 passed** on disposable PostgreSQL 18, with 16 existing Starlette/httpx and Alembic deprecation warnings. New coverage verifies two adjacent effective versions, boundary-day selection, unchanged earlier rule contents, finite/open-ended overlap rejection on insert and update, invalid dates/reasons/classification/frequency/thresholds, cross-organization references, duplicate keys/rules, restricted deletion, and repeat upgrade/downgrade preserving all 48 applications and four demo accounts. Existing metadata comparison, login, CSRF, role scope, API, seed, and health tests pass.

`git diff --check` passes. `git status --short` and diff summary were reviewed; the owner's untracked build contract remains unstaged. No frontend files changed, so no frontend build or browser verification is claimed for this slice.

Manual check: in a disposable database, run `alembic -c backend/alembic.ini upgrade head` and `alembic -c backend/alembic.ini current`; expect `0004_policy_schema`. Inspect the four new empty policy tables. There is no new UI control to click; registry/login behavior is unchanged. Never use downgrade casually on policy data you need to retain.

Limitations: storage does not implement policy-edit permissions, audited publication, immutable published versions, cross-policy applicability conflict resolution, demo policy seeding, application overrides, calendar recurrence generation, or governance health. Those remain later slices. No policy-write API is exposed. Direct privileged SQL can still mutate historical rows; the upcoming service must enforce the versioning contract before exposing edits.

Suggested commit: `feat(policies): add versioned governance policy schema`.
