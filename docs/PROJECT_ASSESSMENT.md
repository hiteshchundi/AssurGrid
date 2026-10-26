# AssurGrid build assessment — October 26, 2026

## What the requested prompt actually covers

`AG-03_Initial_Build_Prompt.md` specifies the foundation only: React → FastAPI → SQLAlchemy → psycopg → PostgreSQL, health endpoints, migrations, configuration, tests, and local startup documentation. It explicitly excludes business functionality and cloud deployment. The current hosted governance demo extends beyond that original milestone boundary.

The supplied local folder matched GitHub `main` at `ec1a351` before changes. It was an exported source folder without `.git`, rather than a working checkout. The README's referenced `AssurGrid_Prototype_Build.md` is missing on GitHub and locally.

## State on arrival

| Area | Assessment | Evidence |
| --- | --- | --- |
| AG-03 backend | Implemented | Versioned live/ready endpoints; independent liveness; safe readiness failure; typed settings; synchronous SQLAlchemy/psycopg; configured CORS |
| AG-03 database | Implemented | PostgreSQL-only Compose, named volume, Alembic baseline and subsequent real migrations |
| AG-03 frontend | Implemented | React 19, TypeScript, Vite, Router, TanStack Query, foundation status with error states |
| Developer setup | Implemented with stale descriptions | Environment examples, ignored secrets, startup instructions, prior implementation report |
| Identity and access | Local prototype implemented | Password hashing, database sessions, origin/CSRF checks, current membership checks, four roles |
| Application registry | Implemented | 48 synthetic systems; search/filter/pagination; details; application-level access scope |
| Governance policies | Read-only implemented | Effective-dated versions, rules, missing/conflicting resolution, policy catalog/history |
| Obligations | Schema only | Policy-linked schedule storage with no rows, API, calculation, completion, or browser workflow |
| Portfolio overview | Missing | Governance explicitly unavailable in the registry and application details |
| Hosting | Missing | No Render/Vercel configuration; production password login disabled; cross-site cookie design unsuitable for direct Vercel-to-Render browser calls |

AG-03's foundation functionality was already built. Calling the whole project “50% complete” would be misleading: AG-03 is a finished milestone, whereas the larger product has no approved comprehensive completion denominator. The remaining gap was a demonstrable governance workflow and hosting.

## Implemented governance demo

- Public sandbox entry using four explicitly synthetic personas, with ordinary production password login still disabled.
- Role-scoped overview and filterable overdue/due-soon/upcoming/completed reviews.
- Governance derived from open mandatory obligations, evaluated using the organization's calendar date/timezone. Missing schedules show **Not scheduled**, never an invented compliant state.
- Application-level schedules and evidence alongside independent lifecycle and validation states.
- Completion with required evidence reference and notes; actor/time retained; duplicate completion rejected; Viewer denied; Owner restricted to accessible systems.
- Atomic creation of the next review using the pinned policy snapshot and calendar-month cadence. Late completion does not erase the original deadline.
- Repeatable hosted fixture initialization, preserving completions across restarts.
- Vercel same-origin API forwarding to the Render backend and SPA deep-link fallback.
- Render free service/database configuration, startup migrations, and readiness path.

## What remains outside the current demo

Policy publication/editing, policy-change-driven schedule recalculation and overrides, real initial schedule anchors, business/technical/quality owner management, separate QA acceptance, document upload/version lineage, controlled electronic signatures, full audit trail, changes/findings/validation execution, CSV ingestion/reconciliation, outbound integrations, notifications, and enterprise SSO remain future work.

Deadline fixtures are frozen, fictional examples relative to October 26, 2026. They snapshot current illustrative policy rules; they do not claim those rules were historically in force at the beginning of every fabricated review window. Recurrence pins the recorded snapshot rather than applying future policy revisions. This limitation is explicit and avoids rewriting history under the guise of policy recalculation.

“Current” means no open mandatory scheduled review is due soon or overdue; it is not a compliance certification. **Not scheduled** requires applicability/configuration investigation, including retired, implementation, low-criticality, and Non-GxP systems in this deliberately partial fixture.

## Verification

The baseline frontend production build passed; 38 isolated backend tests passed with 161 PostgreSQL tests initially skipped. After obtaining PostgreSQL 18 binaries with `btree_gist`, the complete test suite passed: **216 tests**, no skipped tests. TypeScript and Vite production build passed. Render YAML passed validation against the current public Render JSON schema. Browser and deployed verification are recorded in the walkthrough/deployment report when completed.

The Compose engine is not installed on this machine, so the current database verification uses a disposable native PostgreSQL 18 socket-only cluster. Existing historical Compose verification remains in `AG-03_Implementation_Report.md`; it was not silently rerun or claimed here.
