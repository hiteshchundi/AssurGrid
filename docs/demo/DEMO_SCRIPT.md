> Slice 06c: first follow [demo account setup](DEMO_ACCOUNTS.md), then open `http://localhost:5173` and sign in. Admin and Quality see all 48 registry applications; Owner sees 3 and Viewer sees 1. Use Admin for the full registry walkthrough below. Reload preserves the session; Sign out returns to the login screen and revokes the session.


# Current AssurGrid demonstration

## Available through Slice 07b

1. Follow the root README to start PostgreSQL, apply migrations, and start FastAPI and Vite.
2. Open `http://localhost:5173/foundation`. The foundation page should show API and Database **Connected**. The navigation also opens the application registry.
3. Run `alembic -c backend/alembic.ini current` from the repository root with the backend environment activated. Expect `0004_policy_schema (head)`.
4. Run `python backend/scripts/seed_demo.py --as-of 2026-10-12 --dry-run`. Expect a visible **SYNTHETIC DEMO DATA** label, explicit date/timezone, one fictional organization, and 48 applications.
5. Inspect [applications.csv](../../mock-data/generated/applications.csv) and the [manifest](../../mock-data/generated/manifest.json). Identify `NSB-LIMS-001` as Operational / Validated and explain that its overdue PCR will be added in the obligation slice, not manufactured as a registry badge.
6. Follow the [safe seed instructions](../../mock-data/README.md) to populate a separate local `assurgrid_demo` database. Run the same seed date twice: expect 48 inserted applications, then zero additional applications.
7. Run the opt-in PostgreSQL integration-test command in the README. It demonstrates repeated seeding, rejection of changed records, duplicate-CI protection, invalid relationships/states, and independent lifecycle and validation values.
8. Follow [demo account setup](DEMO_ACCOUNTS.md), select the fictional organization in the API configuration, and restart FastAPI against the seeded demo database. Sign in at `http://localhost:5173` as Admin. Search `NSB-LIMS-001` to retrieve one result; filter classification `Non-GxP` to retrieve seven. The unfiltered default page contains 20 of 48 applications.
9. Open a registry application name. Expect distinct lifecycle and validation fields, unrecorded owners, and unavailable governance health. The backend detail endpoint requires the same authenticated session. A nonexistent or unauthorized UUID returns 404. See the [API contract](REGISTRY_API.md).
10. Open `http://localhost:5173/applications`. Expect 48 matching applications across three default pages. Search `NSB-LIMS-001` and apply filters, open its name, then use **Back to application registry**. The CI filter remains in the URL. Clear filters, choose Non-GxP, and apply: seven records should appear.
11. Inspect lifecycle, validation, and governance separately. Governance is explicitly unavailable until its domain logic exists; owners are not recorded. Seed timestamps are shown in the browser's timezone. All pages identify synthetic data.

12. Follow [policy setup](DEMO_POLICIES.md) to preview/export or explicitly seed the fictional policy fixtures. Repeat the seed: expect zero new records. Inspect the exported High GxP PCR rules: 24 months before July 1, 2026, and 12 months from that date. No policy page or automatic obligation calculation exists yet.

The tests use disposable synthetic records and leave no data in the development database. Registry access requires current session membership and role/application scope. Login/logout and account switching work; policy calculation and QA workflow remain pending.

## Intended story for later slices

Open a synthetic application that is Operational and Validated, then explain its Overdue governance health by drilling into the concrete PCR deadline, applied policy version, and evidence. Follow an implemented change through owner submission, separate QA review, closure, and visibly simulated outbound delivery. These steps are planned and must not be presented as working until their slices pass verification.
