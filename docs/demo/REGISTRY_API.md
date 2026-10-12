# Read-only registry API — Slice 04

This API is an opt-in, unauthenticated local development capability for synthetic data. It is disabled unless `APP_ENV=development` and `DEMO_REGISTRY_ORGANIZATION_ID` is set. The backend applies that organization ID to every registry query; clients cannot choose another organization. This is not user authorization. Slice 06 must replace the temporary scope dependency with authenticated membership/assignment checks before protected use.

## List applications

`GET /api/v1/applications`

| Query parameter | Contract |
| --- | --- |
| `search` | Optional, maximum 100 characters, trimmed; case-insensitive literal substring of name or CI ID. `%` and `_` are literal characters, not wildcards. |
| `classification` | Optional `GxP` or `Non-GxP` |
| `criticality` | Optional `High`, `Medium`, or `Low` |
| `lifecycle_state` | Optional `Implementation`, `Operational`, `Retirement`, or `Retired` |
| `validation_state` | Optional `Not Assessed`, `Validation Required`, `In Validation`, `Validated`, or `Remediation Required` |
| `page` | Integer 1–10000; default 1 |
| `page_size` | Integer 1–100; default 20 |

Filters combine with AND; search matches either name or CI. Unknown query keys, including `organization_id` and the not-yet-supported `health`, produce HTTP 422. Sort order is CI ID then UUID, ascending. There is no client-selected SQL sort expression.

HTTP 200 returns `{ "items": [...], "total": 48, "page": 1, "page_size": 20 }` for the first default seeded page. `total` is calculated from matching organization-scoped records, not hardcoded. Count and page come from one SQL statement and share a PostgreSQL snapshot. A page beyond the results has `items: []` with the same matching total. No matches yields `items: []` and `total: 0`.

## Application detail

`GET /api/v1/applications/{application_id}`

The path takes the internal UUID, not CI ID. Search by CI first to obtain the UUID. HTTP 200 returns the same application object used by the list. A valid UUID that is absent or belongs to another organization returns the identical HTTP 404 body: `{ "detail": "Application not found." }`. A malformed UUID returns HTTP 422.

Each application contains `id`, `organization_id`, `ci_id`, `name`, `system_type`, `description`, `gxp_classification`, `criticality`, `lifecycle_state`, `validation_state`, `supplier`, `platform`, `created_at`, and `updated_at`. UUIDs serialize as strings and timestamps as ISO 8601 values. Optional metadata can be null.

`business_owner_id`, `technical_owner_id`, and `quality_owner_id` currently return null because identity/ownership records do not exist yet. No owner names, assignments, or governance-health values are fabricated. Governance health will require the policy and obligation slices.

## Failure and write behavior

- Disabled/unconfigured scope: HTTP 503 with a safe explanation.
- Database failure: HTTP 503, `Application registry is temporarily unavailable.`; logs include only the exception class, not SQL/credentials.
- Invalid list inputs or path UUID: HTTP 422 when the registry is enabled.
- No matching list records: HTTP 200 with an empty list.
- Missing/out-of-scope detail: HTTP 404.
- POST/PATCH/DELETE are not implemented; HTTP 405 for these methods on the registry resources.

The endpoints issue reads only and do not modify rows or emit business audit events. Liveness/readiness routes retain their existing behavior. The seeded descriptions identify all application data as synthetic.
