# Slice 07b — reproducible synthetic policies

Product purpose: provide historically identifiable fictional review rules for later policy resolution and dated obligations.

Changes: deterministic generator, JSON export, and explicit insert-only seed for 4 controls, 2 profiles, 3 versions, and 10 rules. High GxP PCR changes from 24 to 12 calendar months at 2026-07-01; Medium GxP has a different control/frequency set. No policy APIs, health values, or obligations are introduced.

Files changed: `backend/app/demo/policies.py`, `backend/scripts/seed_policies.py`, `backend/tests/test_demo_policies.py`, `backend/tests/integration/test_policy_seed.py`, `mock-data/generated/policies.json`, `mock-data/README.md`, `README.md`, `docs/demo/DEMO_SCRIPT.md`, `docs/demo/DEMO_POLICIES.md`, `docs/demo/ARCHITECTURE_NOTES.md`, and this report.

Database changes: no migration. Seed is an explicit operator action against a confirmed local `assurgrid_demo` database. Existing policy rows are compared under table locks before any insert; edited/extra records cause refusal. No update/delete/reset behavior. The owner's database and `.env` were not modified.

Data changes: checked-in synthetic JSON fixture with stable IDs and frozen dates. Existing registry CSV exports are unchanged. The fixture records invented initialization time, not historical approval evidence. No passwords or real enterprise/public data are included.

Commands actually executed:

```sh
backend/.venv/bin/python backend/scripts/seed_policies.py --dry-run
backend/.venv/bin/python backend/scripts/seed_policies.py --export mock-data/generated/policies.json
ASSURGRID_TEST_POSTGRES_BIN=/opt/homebrew/opt/postgresql@18/bin backend/.venv/bin/python -m pytest backend/tests -p no:cacheprovider -x --tb=short
git diff --check
```

Result: **160 passed**, 17 existing Starlette/httpx and Alembic deprecation warnings. PostgreSQL tests use a disposable private socket-only cluster. New checks verify repeat seed preservation, actual CLI apply twice, refusal of edited data, missing-parent guard, partial matching dataset completion, caller rollback, boundary-day version/frequency selection, and byte-identical export matching the checked-in artifact. Existing registry, identity, auth, CSRF, and schema tests pass.

Manual check: run the dry-run command and expect 4/2/3/10 planned counts. Inspect `mock-data/generated/policies.json`; compare both High GxP PCR versions. To exercise database writes, follow [policy setup](DEMO_POLICIES.md) in a disposable demo database, run apply twice, then expect zero additional rows. There is no new UI control and no browser verification claimed for this backend/data slice.

Security/data caveats: this operator seed is not an authenticated policy-edit API. Permission tests, policy resolution, audited publication/immutable history, application overrides, obligations, and governance calculations remain separate slices. Frequencies are fictional organization choices.

Diff review: working status and whitespace checks reviewed. The owner's untracked build contract remains unstaged. Suggested commit: `feat(data): seed reproducible synthetic governance policies`.
