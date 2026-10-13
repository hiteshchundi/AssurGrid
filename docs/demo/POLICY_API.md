# Policy reads and date resolution — Slice 07c

These read-only endpoints require the existing browser session. Organization scope and role come from current backend membership, never client query parameters. Successful responses use `Cache-Control: no-store`. The UI has no policy page yet.

## Organization policy catalog and history

`GET /api/v1/policies?page=1&page_size=20` requires Admin or Quality; Owner/Viewer receive 403. Page is 1–10000 and page size 1–100. Unknown query keys return 422. Response contains `items` (ID, key, name), `page`, `page_size`, and `has_more`. Ordering is policy key then UUID. No hardcoded count.

`GET /api/v1/policies/{policy_id}` requires Admin or Quality and returns the organization's policy identity, all stored versions ordered by version number, and each version's rules ordered by control key. Versions include effective dates, applicability classification/criticality, reason, and their own rule IDs. Rules include control identity/name/activity, calendar-month frequency, due-soon threshold, mandatory flag, and evidence requirement. Missing and foreign IDs both return `404 Policy not found.` An empty policy can have no versions. History includes inactive controls for truthful inspection.

These reads are organization-configuration administration access. Application Owner/Viewer can inspect the applicable configuration through their authorized application's endpoint instead.

## Resolve defaults for an application and date

`GET /api/v1/applications/{application_id}/policy?as_of=2026-10-12`

`as_of` is a required calendar date interpreted in the organization's timezone, returned explicitly. Unknown query keys and invalid/missing dates return 422. Admin/Quality can resolve any application in their organization; Owner/Viewer require an assignment. Missing, foreign, and unassigned application IDs return the same `404 Application not found.`

One database statement authorizes the application and reads matching policy versions/rules from a shared snapshot. A version matches the application's **currently recorded** classification/criticality and the requested date in its `[effective_from, effective_to)` interval; a null end is unbounded. This does not reconstruct historical application classification or lifecycle. No implicit current date or lifecycle-based applicability is invented.

Response includes application ID, date, timezone, `configuration`, explanation, candidate policy/version identities and dates, and rules:

| Configuration | Meaning | Rules returned |
| --- | --- | --- |
| Resolved | Exactly one version matches, with rules referencing active controls | That version's rules |
| Missing Configuration | No match, no rules, or an inactive referenced control | Empty |
| Conflicting Configuration | More than one policy version matches | Empty |

Candidates remain visible for explaining missing/conflicting configuration. No winner is chosen arbitrarily. With the synthetic seed, High GxP LIMS PCR resolves to 24 months on 2026-06-30 and 12 months on 2026-07-01. Medium GxP resolves its separate two-rule profile. Non-GxP and unconfigured classes report missing configuration.

The result is policy defaults, not governance health, concrete deadlines, accepted evidence, or an override decision. No `Current` status is inferred. Application overrides and obligation generation arrive later.

## Failures and writes

Missing/invalid/expired authentication returns 401. Catalog/history role denial returns 403. Malformed path UUIDs return 422. Database errors return a safe 503 without SQL or credentials. POST/PATCH/DELETE policy writes are not exposed (405); audited publication and immutable history enforcement remain future work. Reads create no business audit events or outbox records.

Manual inspection requires migrations, explicit registry/accounts/policy seeds, and an authenticated session. The automated integration tests run the real login flow and these endpoints against a disposable database. Browser policy presentation is a separate slice.
