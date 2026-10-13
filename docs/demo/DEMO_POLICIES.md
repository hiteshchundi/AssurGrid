# Synthetic policy setup — Slice 07b

These are illustrative Northstar organization policies, not regulator-mandated review frequencies. They support later policy resolution and obligation demonstrations; they do not create obligations or governance health.

| Profile/version | Effective dates | Review frequencies in calendar months |
| --- | --- | --- |
| High GxP v1 | 2025-01-01 through 2026-06-30 | PCR 24, Access 3, ATR 3, Supplier 24 |
| High GxP v2 | From 2026-07-01 | PCR 12, Access 3, ATR 3, Supplier 24 |
| Medium GxP v1 | From 2025-01-01 | PCR 24, Access 6 |

All ten rules are mandatory with a 30-day due-soon threshold and a synthetic evidence-reference description. Effective end dates are exclusive in storage. The two profiles apply to GxP and their named criticality; no profile is fabricated for other classifications. Later resolution must report missing configuration where appropriate. Monthly ATR overrides remain future work.

From the repository root, with the backend environment activated:

```sh
python backend/scripts/seed_policies.py --dry-run
python backend/scripts/seed_policies.py --export mock-data/generated/policies.json
```

These commands require no database. Export deliberately replaces the named JSON file with deterministic bytes. The fixture uses stable UUIDv5 identities and frozen dates, so regeneration remains identical on a later day. Its invented creation timestamp is fixture initialization, not approval evidence.

To apply, first migrate to `0004_policy_schema` and seed the fictional registry. Set the same explicit local `assurgrid_demo` database URL as in the [registry instructions](../../mock-data/README.md), then run:

```sh
export ASSURGRID_ENV=development
python backend/scripts/seed_policies.py --apply --confirm-demo
```

The command requires an explicit process `DATABASE_URL`; it never loads `.env` implicitly. It checks the connected database name and the expected fictional organization. It compares all existing policy/control/rule rows before inserting missing exact fixtures, in one locked transaction. First run inserts 4 controls, 2 policies, 3 versions, and 10 rules; a repeat inserts zero. Edited or extra policy records cause refusal. It never updates or deletes records and is not a policy-editing utility.

Account credentials are neither needed nor read by this seed. No UI or API permission claim is made for this operator command. Authenticated policy history and application/date resolution are now available through the [policy API](POLICY_API.md). Publication/audit enforcement, overrides, obligations, and health calculations remain later work. The browser registry continues to show governance as unavailable.

## Inspect in the browser

After seeding and starting the API/frontend, sign in as Admin or Quality and open **Governance policies**. Open High-Criticality GxP to inspect both versions and their own review rules. From the registry, open LIMS and use **Applicable policy → Policy date → Inspect date**. Compare 2026-06-30 (PCR 24 months) and 2026-07-01 (PCR 12 months). A date before 2025-01-01 reports missing configuration. Owner/Viewer can inspect defaults on assigned application details; the administration catalog is restricted.

The date input initially uses the browser's calendar day as an editable suggestion. The result displays the submitted date and organization timezone; the API interprets that explicit date in the organization calendar. No due-date or health calculation happens in the browser. The chosen inspection date is local component state and resets on reload/application change.
