# Slice 05 verification — 12 October 2026

Story: search/filter in React → scoped FastAPI registry endpoint → seeded PostgreSQL 18 → rendered list → application detail.

The API ran against a newly created disposable PostgreSQL cluster with the frozen 2026-10-12 synthetic dataset. Vite ran on localhost:5173 and the API on localhost:8000. The owner's development database and environment files were untouched. The temporary API/database were stopped after verification.

| Check | Observed result |
| --- | --- |
| `pnpm --dir frontend typecheck` | Passed |
| `pnpm --dir frontend build` | Passed, TypeScript and Vite production build |
| Open `/` | Redirected to `/applications`, 48 matching applications |
| Search `NSB-LIMS-001` and apply | One application, API HTTP 200 |
| Open LIMS detail by keyboard | Correct CI, Operational and Validated shown separately; governance unavailable |
| Back to registry | Search and page-size query parameters preserved |
| Clear, select Non-GxP, apply | Seven matching records, API HTTP 200 |
| Next page | Page 2 of 3, API request includes `page=2` |
| Search `NO-MATCH-XYZ` | Zero matches, actionable empty state |
| Open nonexistent UUID | API 404, visible Application not found message |
| Foundation route | API Connected and Database Connected; both endpoints returned 200 |
| Desktop 1280px / narrow 390px | Readable layouts; at 390px document width stayed 390px and table scrolls within its region |
| Browser console before deliberate failures | No warnings/errors observed |
| Stop temporary API, refresh registry | Clear unreachable message and zero visible tables; cached rows not shown as current |

Native/semantic browser interaction was used; no API responses were mocked. Server logs showed the corresponding real search, detail, classification, pagination, and health requests. The missing-record and stopped-server checks intentionally generated failed requests.

This slice adds no migrations, seed changes, authentication, or frontend-computed governance health. Loading and error handling are implemented; the loading state was not artificially delayed to claim a separate visual timing test. The registry still requires the explicit local demo scope from Slice 04.
