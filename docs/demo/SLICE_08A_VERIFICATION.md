# Slice 08a — scheduled-obligation storage

Product purpose: preserve a concrete application review window and due date with the exact governing rule/version and a snapshot of its requirements.

Changes: SQLAlchemy Core table and migration `0005_obligation_schema`; same-organization application/member references; a composite rule/version/control FK; snapshot fields; calendar-date checks; unique generation and rule-window keys; and a reasoned same-application/control supersession reference. No persisted overdue or health state.

Files changed:

- `backend/app/db/schema.py`
- `backend/migrations/versions/0005_obligation_schema.py`
- `backend/tests/integration/test_registry_schema.py`
- `backend/tests/integration/test_obligation_schema.py`
- `README.md`
- `docs/demo/DEMO_SCRIPT.md`
- `docs/demo/ARCHITECTURE_NOTES.md`
- `docs/demo/SLICE_08A_VERIFICATION.md`

Database/data safety: migration adds one empty table and a composite unique constraint on existing rule columns. The constraint includes the rule primary key, so existing valid policy data cannot contain duplicates that violate it. Downgrade removes this table/constraint and preserves registry, identity, and policy tables. The owner's database, `.env`, and demo exports were not changed. All inserted obligations exist only in disposable tests.

Exact commands executed:

```sh
ASSURGRID_TEST_POSTGRES_BIN=/opt/homebrew/opt/postgresql@18/bin backend/.venv/bin/python -m pytest backend/tests -p no:cacheprovider -x --tb=short
git diff --check
```

Result: **199 passed**, with 22 existing Starlette/httpx and Alembic configuration deprecation warnings. PostgreSQL 18 tests use a disposable private socket-only cluster. New checks verify exact rule/version/control linkage, snapshot retention, optional same-org member assignment, foreign/missing application/member rejection, date/frequency/threshold/key checks, duplicate protection, supersession target/reason/self-link restrictions, restricted deletes, repeat upgrade, and downgrade preserving existing records. The suite's metadata comparison and all previous API/auth/seed tests pass.

Manual check: in a disposable database apply `alembic -c backend/alembic.ini upgrade head`, then `alembic -c backend/alembic.ini current`; expect `0005_obligation_schema`. Inspect the empty `governance_obligation` table and its constraints. There is no new UI action, and no frontend build/browser verification claimed for this schema-only slice.

Limitations: no generator, obligation seed, read/write API, accepted completion/evidence, calendar recurrence calculation, or derived health. Appropriate owner role/activity/assignment checks and cycle-free/audited supersession require future services. Direct privileged SQL can still edit records; no published immutable-history claim is made. No obligations are automatically erased or replaced by a policy change.

Diff review: status and whitespace checks reviewed. The owner's untracked build contract remains unstaged. Suggested commit: `feat(obligations): add policy-linked scheduled obligation storage`.
