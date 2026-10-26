# Governance demo walkthrough

Use only fictional records and evidence references. This is a shared synthetic sandbox.

1. Open the frontend. Choose **Quality**; explain that the persona switcher is a public demo feature, not enterprise authentication.
2. The overview answers “what needs attention?” Show overdue and due-soon counts and click a metric to filter the underlying review records. Dates are evaluated live in Asia/Kolkata, not stored as frozen status badges.
3. Open the application registry. Show 48 applications, search `NSB-LIMS-001`, then open Northstar Laboratory Information System.
4. Show **Operational / Validated** independently of **Overdue** governance. An application can remain validated while a recurring review is late.
5. Inspect its applicable policy. Compare June 30, 2026 with July 1, 2026. The High GxP PCR default changes from 24 to 12 calendar months, with the old version still visible in policy history.
6. In **Governance & review evidence**, identify an overdue review, its original due date, cadence, and pinned policy version. Deadline fixtures are illustrative seeded schedules, not genuine historical approval evidence.
7. Click **Record completion** on a review whose window has started. Enter a fictional reference such as `DEMO-PCR-LIMS-2026 v1.0` and meaningful synthetic review notes. Click **Save completion**.
8. Show the completed record, actor/time/reference/notes, unchanged old deadline, and next review. Reload to prove the evidence persists in PostgreSQL.
9. Sign out; choose **Application Owner**. Show only three assigned systems. Sign out; choose **Viewer**. Show one LIMS application and no completion controls. Server-side tests also verify rejected writes/hidden application IDs.
10. Open **Foundation status** to demonstrate the browser → API → SQLAlchemy → psycopg → PostgreSQL connection.

## Five-minute architecture explanation

React uses TanStack Query for server state. Browser calls stay on the Vercel origin; Vercel forwards `/api/*` to Render, preserving the HttpOnly session cookie and avoiding third-party cookie dependence. FastAPI checks the current session, membership, role, and application scope. SQLAlchemy sends synchronous queries through psycopg to PostgreSQL. Alembic manages schema changes. Completing a review and scheduling its successor share one database transaction.

Lifecycle, validation, and governance answer different questions. Policies define organization defaults. Each obligation preserves the concrete rule/version and requirements that created its schedule. Evidence completion is append-only through the API; this is not a database-enforced immutable ledger or an electronic signature.

## Local public-sandbox setup

Follow the root README for dependencies and PostgreSQL. Use a fresh dedicated database named `assurgrid_demo`. With its `DATABASE_URL` set and the backend environment activated:

```sh
export FRONTEND_ORIGIN=http://localhost:5173
export DEMO_REGISTRY_ORGANIZATION_ID=becdd76c-490f-52a1-9247-9f6a6845d774
export PUBLIC_DEMO_ENABLED=true
export APP_ENV=production
alembic -c backend/alembic.ini upgrade head
python backend/scripts/initialize_hosted_demo.py
uvicorn app.main:app --host localhost --port 8000
```

Start `pnpm dev` from `frontend/`. An unset or empty `VITE_API_BASE_URL` uses Vite's `/api` proxy; the documented explicit localhost API URL also works. Disabling public demo restores the original local-password workflow; hosted initialization is deliberately an explicit command.

## Before presenting

Open the frontend and foundation page at least two minutes beforehand. Render's free API sleeps after inactivity and may take about a minute to wake. Complete one disposable review beforehand to check persistence, then use another open review during the walkthrough. Other visitors can have already completed a shared fixture; completed evidence remains visible.

The free Render database created October 26, 2026 expires November 25, 2026. Recreate a fresh free sandbox and reseed before that date if needed. No recurring keep-alive, paid upgrade, real evidence upload, or company integration is configured.
