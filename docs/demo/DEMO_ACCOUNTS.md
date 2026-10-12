# Fictional demo accounts

First apply migrations and seed the 48-application registry using [existing instructions](../../mock-data/README.md). Use the same explicit local `assurgrid_demo` connection; this command does not load `.env` implicitly.

In an interactive terminal with the backend environment activated:

```sh
export ASSURGRID_ENV=development
# Set DATABASE_URL to your local assurgrid_demo database as in the registry instructions.
python backend/scripts/seed_accounts.py --confirm-demo
```

The command asks for a 12–256 character password for each account with hidden input. Choose demo-only passwords, retain them privately, and do not put them in commands, exports, or source files. No built-in password exists. Repeating setup requires the same passwords; existing hashes are preserved. Changed identities/credentials/roles or extra access cause a refusal and transaction rollback. This command is not a password-reset utility.

| Email | Role | Registry access |
| --- | --- | --- |
| admin@northstar.example.test | Admin | All 48 fictional applications |
| quality@northstar.example.test | Quality | All 48 fictional applications |
| owner@northstar.example.test | Application Owner | NSB-LIMS-001, NSB-CDMS-002, NSB-QMS-003 |
| viewer@northstar.example.test | Viewer | NSB-LIMS-001 |

All four accounts are synthetic. Application access does not populate business, technical, or quality ownership fields. The role matrix remains a provisional prototype choice.

Start the API with `APP_ENV=development`, the demo database URL, and `DEMO_REGISTRY_ORGANIZATION_ID=becdd76c-490f-52a1-9247-9f6a6845d774`. Start Vite with `VITE_API_BASE_URL=http://localhost:8000`; open `http://localhost:5173`, not the HTML file on disk. Use `localhost` consistently for the frontend and backend so SameSite cookies work. The configured `FRONTEND_ORIGIN` must match the browser origin.

Sign in with one account, inspect its count, open a permitted record, reload, and sign out. Then switch accounts to compare access. A logged-out or expired session returns to sign-in. The Foundation status route remains available without login. If the API is unavailable, the protected view hides records and offers a retry.

Password recovery, account administration, SSO, rate limiting, and production deployment hardening are outside this local demo. Production password login remains disabled. No changes to the owner's running database are made merely by checking out this slice.
