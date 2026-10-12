# Current AssurGrid demonstration

## Available through Slice 03

1. Follow the root README to start PostgreSQL, apply migrations, and start FastAPI and Vite.
2. Open `http://localhost:5173`. The foundation page should show API and Database **Connected**. This is the only application screen available.
3. Run `alembic -c backend/alembic.ini current` from the repository root with the backend environment activated. Expect `0002_application_registry (head)`.
4. Run `python backend/scripts/seed_demo.py --as-of 2026-10-12 --dry-run`. Expect a visible **SYNTHETIC DEMO DATA** label, explicit date/timezone, one fictional organization, and 48 applications.
5. Inspect [applications.csv](../../mock-data/generated/applications.csv) and the [manifest](../../mock-data/generated/manifest.json). Identify `NSB-LIMS-001` as Operational / Validated and explain that its overdue PCR will be added in the obligation slice, not manufactured as a registry badge.
6. Follow the [safe seed instructions](../../mock-data/README.md) to populate a separate local `assurgrid_demo` database. Run the same seed date twice: expect 48 inserted applications, then zero additional applications.
7. Run the opt-in PostgreSQL integration-test command in the README. It demonstrates repeated seeding, rejection of changed records, duplicate-CI protection, invalid relationships/states, and independent lifecycle and validation values.

The tests use temporary synthetic records and leave no data in the development database. The explicit seed command creates the registry dataset only in the selected demo database. There is no registry screen, login, policy calculation, or QA workflow to demonstrate yet.

## Intended story for later slices

Open a synthetic application that is Operational and Validated, then explain its Overdue governance health by drilling into the concrete PCR deadline, applied policy version, and evidence. Follow an implemented change through owner submission, separate QA review, closure, and visibly simulated outbound delivery. These steps are planned and must not be presented as working until their slices pass verification.
