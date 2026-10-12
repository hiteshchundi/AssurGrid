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

## Slice 04 — Organization-scoped registry API

The applications module separates typed API contracts, HTTP handling, and explicit SQLAlchemy Core queries. Filters bind values as query parameters; search escapes SQL wildcard characters. One CTE-based query returns both the filtered total and requested page from a consistent snapshot, including counts for empty pages. Every list/detail query includes the server-selected organization ID.

The API is intentionally disabled unless a development organization scope is configured. Authentication is not implemented yet: any caller who can reach the enabled local API can read the selected scope. This temporary dependency must become authenticated session membership/assignment enforcement in Slice 06. No protected-production-use or finalized AG-04 claim is made.

Owner IDs are nullable response fields and return null until the user/assignment schema exists. Governance health is omitted until policies and concrete obligations support it. No new migration or data writes are included. PostgreSQL API tests cover actual seeded reads, pagination, filter combinations, literal/injection-shaped searches, missing IDs, cross-organization isolation, and safe failures.

## Slice 05 — Registry list and detail screens

The default route now opens the registry; foundation health remains accessible at `/foundation`. This registry-first entry is reversible when the attention dashboard arrives. TanStack Query owns server fetching and caching. Search/filter/page state lives in the URL, including the return link from an application. Forms apply filters explicitly, and counts/rows come only from the API.

The UI distinguishes loading, empty, invalid/missing record, and unavailable states; a failed refetch suppresses stale records. It provides a synthetic-data banner, semantic labels/table headings, keyboard controls, and a horizontally scrollable table on narrow screens. Governance is unavailable rather than a fake Current badge, and missing owner IDs are not converted into invented people. Timestamp presentation uses the browser timezone without calculating business status.

The React review covered hook order, stable row keys, label associations, focus indicators, direct imports, and use of TanStack Query rather than manual fetch effects. No dependencies were added. See [Slice 05 verification](SLICE_05_VERIFICATION.md) for actual browser checks.

## Slice 06a — Identity storage and relational constraints

Migration `0003_identity` prepares the storage needed to answer who belongs to an organization and which applications they may access. It adds `user_account`, `membership`, `application_access`, and `browser_session`. It does not enable login or change the current development API scope.

Accounts use unique lowercase, whitespace-free email identifiers, nonblank display names/password-hash fields, active flags, and timestamps. Email checks are a prototype canonicalization convention, not full email validation. The database cannot verify password hashing: the future login/seed service must generate real salted password hashes and never persist plaintext. No accounts, credentials, or sessions are seeded in this slice.

Membership has one role per organization/user pair: `Admin`, `Quality`, `Application Owner`, or `Viewer`. These names follow the provisional demo matrix, not a finalized AG-04 enterprise authorization model. Users can belong to multiple organizations. An active flag allows later suspension without deletion. Future request dependencies must resolve current account and membership activity and role on every request.

Application access references both the organization/user membership and the organization/application pair. A composite unique constraint on applications enables the latter FK, preventing cross-organization assignments. Access grants do not represent business, technical, or quality ownership; the API's owner fields remain null. Admin/Quality portfolio scope and owner/viewer assigned scope will be enforced by later services.

Sessions store unique 64-character lowercase hex token digests, CSRF digests, membership references, creation/expiry/revocation timestamps, and no copied role. Digest shape checks cannot prove cryptographic generation. The future authentication service must generate unpredictable tokens, hash them, enforce expiry/revocation, and set cookie/CSRF protections. Membership and account restrictions are not enforced by this storage alone. Identity FKs restrict deletion; future services must explicitly revoke/remove dependent rows as appropriate.

The migration is independent of live metadata. Upgrade preserves existing registry rows; downgrade removes the four identity tables and the added application unique constraint, preserving registry rows. No owner database or `.env` was changed. Existing reproducible exports remain unchanged. See [Slice 06a verification](SLICE_06A_VERIFICATION.md).

## Slice 06b — Backend sessions and registry authorization

The temporary anonymous development scope is replaced with a session principal. The applications repository applies organization scope plus an assignment EXISTS predicate for owners/viewers to both count/page and detail queries. Current role/activity comes from joined membership/account rows on every request. Login/logout persist session creation/revocation transactionally; plaintext tokens never enter storage. No schema change or seeded account is included. See [auth contract](AUTH_API.md) for endpoint behavior, verification, and the pending frontend/account setup.

## Slice 06c — Browser login and explicit demo identities

The login form establishes the HttpOnly session and reads the current principal through TanStack Query. Protected routes retain their requested application URL through sign-in. Session errors hide protected content, registry 401 responses clear cached records, and login/logout cancel queries and remove prior account data. Application query keys include user ID and role. The header exposes current role and sign-out; cookies carry authentication, while CSRF tokens are obtained with an Origin-checked POST and held only for the pending logout request.

The separate account CLI requires an explicitly confirmed local `assurgrid_demo` target and hidden interactive password prompts. Four stable UUID identities and the existing application CI IDs define reproducible access. Password hashes use random salts and are preserved on repeat runs, so credentials are intentionally not byte-reproducible. Edited identities, passwords, roles, activity, or extra access cause refusal rather than overwrite; missing expected records are inserted transactionally. No password exports or production account provisioning are implemented.

See [account setup](DEMO_ACCOUNTS.md) and [verification](SLICE_06C_VERIFICATION.md). No migration, owner database change, or registry fixture regeneration was needed.

## Slice 07a — Controls and effective policy storage

Migration `0004_policy_schema` adds `control_definition`, `governance_policy`, `policy_version`, and `policy_control_rule`. Controls and policies have organization-scoped stable keys. Versions carry their own classification/criticality applicability, version number, change reason, and effective calendar dates. Rules reference a specific version and control within the same organization, and store calendar-month frequency, due-soon days, whether completion is mandatory, and an optional evidence requirement description.

Effective periods use `[effective_from, effective_to)`: the start date is included and the end date excluded; null end means unbounded. A PostgreSQL GiST exclusion constraint rejects overlapping periods for the same policy, including open-ended periods and updates. The standard `btree_gist` extension supplies UUID equality for this constraint. The migration installs it if absent; deployment must permit installation. Downgrade intentionally retains the extension because other schemas may use it.

Composite foreign keys prevent cross-organization version/control references. Unique constraints protect version numbers and one rule per version/control. Checks require positive month frequency, nonnegative due-soon thresholds, valid applicability values, and nonblank reasons. Separate policy versions retain their separate rules: a new version does not rewrite the previous rule. Restricted deletes prevent removal of controls/versions still referenced by rules.

This is storage only: no publish/edit/delete endpoint, permission service, automatic applicability resolver, initial policy seed, override, obligation generator, or health calculation exists yet. Direct privileged SQL can still modify unreferenced history; version publication and immutable-history enforcement must be defined in the service slice before allowing business edits. Cross-policy applicability conflicts also require that resolver; the exclusion scope here is one policy's version timeline. Evidence is descriptive text for now, not a document-type FK or an accepted completion record. Calendar-month recurrence is stored without converting months to fixed days.

Upgrade and downgrade preserve existing registry and identity tables. The migration itself inserts no domain records. [Slice 07a verification](SLICE_07A_VERIFICATION.md) records the tests and manual checks. Demo policy seeding and authorized services follow separately; the UI continues to show governance as unavailable.
