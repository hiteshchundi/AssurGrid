# Slice 07d — read-only policy inspection

Product purpose: show which review rules apply to an authorized application on a chosen date and allow Quality/Admin to inspect earlier policy versions.

Changes: policy catalog/history pages, role-aware navigation, an Applicable policy section on application detail, typed/runtime-checked credentialed API reads, explicit date submission, and login return-to-policy support. Missing/conflicting configuration shows its explanation without resolved rules. Lifecycle, validation, and unavailable governance health remain separate.

Files: `frontend/src/api/policies.ts`, `frontend/src/features/policies/PolicyViews.tsx`, `frontend/src/features/applications/ApplicationDetail.tsx`, `frontend/src/features/auth/Auth.tsx`, `frontend/src/main.tsx`, `frontend/src/routes/AppLayout.tsx`, `frontend/src/styles/global.css`; `README.md`; `docs/demo/ARCHITECTURE_NOTES.md`, `DEMO_POLICIES.md`, `DEMO_SCRIPT.md`, `POLICY_API.md`, and this report.

Database/data changes: none. Browser verification used a separate disposable PostgreSQL cluster seeded with fictional registry, accounts, and policies. The owner's database, environment files, and generated fixtures were not changed. No new dependency or backend modification.

Commands executed:

```sh
pnpm --dir frontend typecheck
pnpm --dir frontend build
git diff --check
```

All pass. Production output: 76 modules, JS 326.14 kB (100.05 kB gzip), CSS 8.09 kB (2.38 kB gzip). Backend suite was not rerun for this frontend-only slice; the immediately preceding Slice 07c passed 178 tests, including policy authorization and resolution.

Real browser → API → database → UI checks:

- Anonymous policy deep link redirects to login and returns to the catalog after Admin sign-in.
- Admin catalog shows both seeded profiles; High GxP history shows versions 1 and 2, with PCR 24 and 12 calendar months.
- LIMS date inspection resolves v1 on 2026-06-30 and v2 on 2026-07-01, changing PCR 24 → 12.
- 2024-12-31 shows Missing Configuration and no rules.
- Viewer can inspect assigned LIMS policy defaults; the policy navigation link is absent and direct catalog navigation shows an access-required message.
- At 390×844, the date form remains usable and document width/scroll width both equal 390. Rule tables scroll within their region. The viewport override was reset.
- Browser console returned no errors/warnings. Server logs confirm successful catalog, history, and application-policy reads.

React review: hooks remain unconditional; fetching is through TanStack Query; keys scope by user/role/resource/date; runtime guards validate responses; labels/table headings/row keys are present; pending/error states avoid stale policy presentation; roles and rule resolution remain backend-authoritative. No fabricated health values or editing controls.

Manual check: follow [policy setup](DEMO_POLICIES.md), sign in as Admin, open Governance policies and High GxP. Open LIMS, compare the two boundary dates, then sign in as Viewer to compare access. The date starts with the browser calendar day and is interpreted by the API in the displayed organization timezone. Inspection date resets on reload.

Limitations: no publication/editing, obligation generation, deadlines, overrides, or health aggregation. Conflicting configuration is rendered by the same typed result path and is covered by prior backend tests; a conflicting dataset was not injected in this browser run. No API-outage/browser error injection claimed.

Diff review: status and whitespace checks reviewed. Owner's untracked build contract remains unstaged. Suggested commit: `feat(policies): add read-only policy inspection screens`.
