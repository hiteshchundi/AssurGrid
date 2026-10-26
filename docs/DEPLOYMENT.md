# Free interview hosting

Frontend: Vercel Hobby, project `assurgrid`, root `frontend`, Vite, Node 24, `pnpm install --frozen-lockfile`, `pnpm build`, output `dist`. Do not set `VITE_API_BASE_URL` for the hosted build; its default is same-origin. `frontend/vercel.json` forwards `/api/*` to `https://assurgrid-api.onrender.com` and serves the SPA for frontend deep links. Keep API responses uncached.

Backend: free Render Python web service `assurgrid-api` in Singapore, repository root as working directory, `pip install -e ./backend`, then `sh backend/scripts/start_hosted.sh`. This script upgrades Alembic, idempotently initializes the explicitly enabled synthetic sandbox, and executes Uvicorn on `0.0.0.0:$PORT`. Free Render has no separate pre-deploy hook, so initialization happens before the API binds its port.

The interview deployment uses the review branch `codex/interview-mvp-release`. Merge it into `main` after review, then update the Render branch/Blueprint to `main` for subsequent releases. Until then, the deployed MVP and original `main` are deliberately separate.

Database: dedicated free Render PostgreSQL 18 `assurgrid-demo`, database `assurgrid_demo`, same region as the API, public connections blocked. No company database is used.

## Backend configuration

| Variable | Value/source |
| --- | --- |
| `DATABASE_URL` | Render database's **Internal Database URL**; configure privately, never commit or paste into chat |
| `FRONTEND_ORIGIN` | Exact final frontend HTTPS origin, no path |
| `APP_ENV` | `production` |
| `PUBLIC_DEMO_ENABLED` | `true` for this dedicated synthetic sandbox only |
| `DEMO_REGISTRY_ORGANIZATION_ID` | `becdd76c-490f-52a1-9247-9f6a6845d774` |
| `PYTHON_VERSION` | `3.12.14` |

Standard Render `postgresql://` URLs are normalized to SQLAlchemy's `postgresql+psycopg://` driver. The same configuration is used for migrations and runtime access. Ordinary password login stays disabled in production. Demo entry authorizes only the four predefined synthetic personas in the fictional Northstar organization.

Configure Render's HTTP health check to `/api/v1/health/ready`. A deploy is successful only when it is **live** and the final frontend can enter the demo, load real database records, complete a review, reload evidence, and sign out. The Vercel project must allow public access to the intended interview URL rather than requiring your Vercel team login.

## Reproducible Blueprint option

`render.yaml` describes the same two free resources. It references the internal connection string with `fromDatabase`, so the secret is supplied by Render. Render can adopt resources with the matching names; inspect the resource IDs before applying a Blueprint to existing services. Set `FRONTEND_ORIGIN` to the verified Vercel origin when prompted. Keep the database and service free plans selected.

The YAML has been checked against Render's current published JSON schema. Platform-aware CLI/API validation should also be run when an authenticated Render CLI/API is available. Schema validation alone does not deploy resources.

## Free-tier limits and recovery

Render's free API sleeps after 15 minutes of inactivity and can take about a minute to wake. The frontend allows 75 seconds for requests; retries remain visible. Workspace free-instance hours are shared with other free services (including the existing `career-compass` service). No unrelated service is changed or upgraded.

The free database created October 26, 2026 expires **November 25, 2026**. Free storage is not a permanent hosting solution. To retain a free demo, create a replacement free database when eligible, update the API's private connection URL, and redeploy; migration/startup will recreate the fictional dataset. This loses previous synthetic completions unless separately exported. There is no automatic destructive reset.

Reference: [Render free limitations](https://render.com/docs/free), [Vercel external rewrites](https://vercel.com/docs/routing/rewrites).
