# SYNTHETIC DEMO DATA

Every organization, application, supplier, platform, identifier, and timestamp in this directory is invented. Northstar Biopharma is a fictional organization for this prototype. These fixtures are not company records, vendor exports, evidence of regulated activity, or proof of compliance.

## Registry v1 — Slice 03

The fixed ordered catalog generates one organization and 48 distinct applications covering laboratory, clinical, quality, manufacturing, safety, regulatory, analytics, and internal enterprise systems. It includes GxP/non-GxP classifications, all four lifecycle states, all five validation states, and three criticality levels. No random generator is used: UUIDv5 identities derive from stable names and a fixed namespace.

The first seven CI IDs reserve the required demo identities: `NSB-LIMS-001`, `NSB-CDMS-002`, `NSB-QMS-003`, `NSB-MES-004`, `NSB-SAFETY-005`, `NSB-ERP-006`, and `NSB-ATR-007`. Their future overdue/due-soon, change, finding, document, and override stories are not implemented or inferred from these rows. No governance-health field is stored.

The registry command seeds registry tables only. Separate commands provide [synthetic accounts](../docs/demo/DEMO_ACCOUNTS.md) and [synthetic policies](../docs/demo/DEMO_POLICIES.md). Passwords are never exported. Owners, obligations, changes, audit events, imports, and public-reference records are absent. Seed rows are initialization fixtures, not simulated audit events.

## Inspect or regenerate without a database

From the repository root after installing backend dependencies:

```sh
source backend/.venv/bin/activate
python backend/scripts/seed_demo.py --as-of 2026-10-12 --dry-run
python backend/scripts/seed_demo.py --as-of 2026-10-12 --export-dir mock-data/generated
```

Dry run prints the chosen date and planned counts without connecting to a database or writing files. Export deliberately replaces only `organizations.csv`, `applications.csv`, and `manifest.json` in the chosen directory. Running export twice with the same date produces identical bytes. Omitting `--as-of` uses today's calendar date in `Asia/Kolkata` and prints it.

`generated/manifest.json` records the generator, seed version, explicit date/timezone, counts, and SHA-256 hashes of both CSV files. Every CSV row has `source_system=SYNTHETIC`. The database schema has no source column yet; the organization has a fictional name and reserved demo slug, and each application's description carries `SYNTHETIC DEMO DATA` and the seed version. No public data is included.

These CSVs are inspectable outputs from the generator. The seed inserts that same in-memory dataset; it does not parse external CSVs or bypass a claimed import-validation pipeline. External-data staging and provenance come in later slices.

## Apply only to a dedicated local demo database

The command requires all of the following: process environment `ASSURGRID_ENV=development`, an explicit `DATABASE_URL` targeting a loopback host or local Unix socket, database name `assurgrid_demo`, and `--confirm-demo`. It does not silently load `.env`. These guards reduce accidental writes; they are not production access controls. Never point a tunnel or production credentials at this command.

With the README's local PostgreSQL container running, create the separate database once:

```sh
docker compose --env-file .env -f infra/compose.yaml exec postgres \
  sh -c 'createdb -U "$POSTGRES_USER" assurgrid_demo'
```

In a dedicated terminal, activate the backend environment. Set the URL using your existing local credentials and port, changing the database name to `assurgrid_demo`. The following uses only the committed example values; a local setup using port 55433 must substitute that port:

```sh
source backend/.venv/bin/activate
export ASSURGRID_ENV=development
export DATABASE_URL='postgresql+psycopg://assurgrid:assurgrid_local@localhost:5432/assurgrid_demo?connect_timeout=3'
alembic -c backend/alembic.ini upgrade head
python backend/scripts/seed_demo.py --as-of 2026-10-12 --apply --confirm-demo
python backend/scripts/seed_demo.py --as-of 2026-10-12 --apply --confirm-demo
```

Expected: first run inserts one organization and 48 applications; second run inserts zero of each. Start FastAPI from this same terminal when it should use the demo database. Closing the terminal discards these environment overrides; the ordinary `.env` is unchanged.

The seed compares all existing registry rows with the expected dataset before inserting missing rows, inside one transaction with a registry write lock. Matching rows are preserved; additional, edited, or differently dated records cause refusal. It never updates, deletes, drops, or resets records. Reuse the original date for reruns. To demonstrate a different date, use a separately provisioned empty local demo database rather than erasing history. No reset command is provided.

## Field and date conventions

| Field | Meaning |
| --- | --- |
| `id`, `organization_id` | Stable synthetic UUIDs and organization FK |
| `ci_id` | Unique fictional CI within the demo organization |
| `name`, `system_type`, `description` | Fictional system purpose and visible synthetic label |
| `gxp_classification`, `criticality` | Explicit prototype classifications, not a real risk assessment |
| `lifecycle_state`, `validation_state` | Separate scenario dimensions, not evidence-backed real-world claims |
| `supplier`, `platform` | Fictional supplier and generic demo hosting description |
| `created_at`, `updated_at` | Invented equal timestamps at local midnight on `--as-of`, serialized in UTC |
| CSV `source_system` | Always `SYNTHETIC`; export metadata rather than a current DB column |

For `--as-of 2026-10-12`, local midnight is `2026-10-11T18:30:00+00:00`. No completion, approval, or due dates are invented at this slice. Changing `--as-of` preserves IDs but changes initialization timestamps, so an existing dataset is intentionally not overwritten.

## Verification

```sh
ASSURGRID_TEST_POSTGRES_BIN=/opt/homebrew/opt/postgresql@18/bin \
  python -m pytest backend/tests -p no:cacheprovider -x --tb=short
```

Use your installed PostgreSQL 18 binary directory. Tests create their own temporary cluster and verify two CLI runs, stable counts/identities/dates, no orphan applications, transaction rollback, partial matching-data completion, unsafe-target rejection, changed-data refusal, and exact CSV/manifest reproducibility. The ordinary no-database test run still checks fixture generation and target guards.

## Policy v1 — Slice 07b

`generated/policies.json` is a deterministic, separately labeled policy fixture: four controls, two profiles, three effective versions, and ten rules. It uses fixed fictional dates and UUIDv5 identifiers. Its initialization timestamp is invented and does not prove historical approval. This JSON is an inspection artifact, not an implemented import feed. The existing registry manifest covers its two CSV files only. See [policy setup and frequencies](../docs/demo/DEMO_POLICIES.md).
