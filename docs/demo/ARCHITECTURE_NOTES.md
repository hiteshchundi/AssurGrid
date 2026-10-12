# AssurGrid prototype architecture notes

## Slice 02 — Registry identity and integrity

The first domain migration adds two tables to the existing modular monolith. PostgreSQL protects application identity and organization relationships; the existing FastAPI and React health workflow is unchanged. SQLAlchemy Core describes tables without introducing ORM models. The migration contains its own definitions so future model edits cannot change an old migration.

- `organization`: UUID primary key, unique lowercase hyphenated slug, display name, explicit timezone, creation/update timestamps.
- `regulated_application`: UUID primary key, required organization FK, CI ID, name, system type, classification, criticality, lifecycle state, validation state, optional description/supplier/platform, and timestamps.
- `(organization_id, ci_id)` is unique. Its backing B-tree index supports organization/CI lookup and the organization FK; no redundant index is added before actual query needs exist.
- An organization with applications cannot be deleted. This prevents accidental removal of the application estate through a parent delete.
- Lifecycle and validation are separate required fields without assumed defaults. Governance health is not stored: policies and concrete obligations must exist before it can be derived.

Prototype choices: classifications are `GxP` and `Non-GxP`; criticality is `High`, `Medium`, or `Low`. CI IDs are case-sensitive, may include punctuation, and cannot contain whitespace. Slugs use lowercase letters/digits separated by hyphens. These are prototype input conventions, not regulatory requirements.

Timestamps use PostgreSQL `timestamptz`; PostgreSQL stores instants independently of display timezone. `created_at` and `updated_at` default to the transaction's current timestamp. Future mutation services must explicitly advance `updated_at` and write audit events atomically; no update API or audit-trail claim exists yet. Checks prevent an update timestamp before creation.

The organization timezone is required and nonblank. Its IANA validity must be checked by the future input/seed service before date-based rules are used. Primary owner FKs are deferred until identity tables exist; no fictional user table or unvalidated owner ID is introduced here.

## Verification and limitations

Integration tests start a disposable PostgreSQL 18 cluster using a private Unix socket. They apply Alembic from an empty database, reapply head with sample data present, exercise downgrade/re-upgrade only in the test database, compare schema metadata, and check relational constraints and transaction rollback. Test records are invented and discarded. No public data ingestion is implemented.

The schema alone does not enforce application-user permissions, create historical audit events, or prove regulatory compliance. Those require later slices. This remains a personal portfolio prototype with no formal validation package, compliant electronic signatures, or live enterprise integrations.

## Slice 03 — Reproducible synthetic registry

The generator uses an intentional catalog of 48 fictional applications and stable UUIDv5 IDs. No random dependency or source data is needed. A frozen organization-local date determines invented initialization timestamps, while lifecycle and validation values stay independent. The registry includes the seven required demo application identities, but no health, deadlines, findings, or other unimplemented domain facts are fabricated.

The seed is an explicit development command for a local database named `assurgrid_demo`. It requires confirmation, compares existing registry rows before writing, and inserts only missing exact seed records. A transaction and table write lock prevent partial datasets or concurrent writes during comparison. Edited rows and a changed seed date cause refusal rather than a silent rewrite; no reset/update/delete behavior exists.

CSV exports include synthetic source labels and a versioned manifest with the date, timezone, counts, and hashes. They are generated inspection artifacts, not an implemented CSV ingestion pipeline. Database descriptions retain the synthetic label; dedicated import/source tables arrive later. Seeds do not claim to produce business audit evidence.

Tests exercise the actual CLI twice against a disposable demo database, verify stable contents, reject altered datasets, and compare exports byte-for-byte with the checked-in snapshot. See [data instructions](../../mock-data/README.md) for safety boundaries and reproducible commands.
