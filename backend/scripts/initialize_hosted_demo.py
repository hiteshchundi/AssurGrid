"""Initialize only the explicitly enabled, dedicated synthetic hosted sandbox."""
import secrets

from sqlalchemy import create_engine, select

from app.core.config import get_settings
from app.db.schema import user_account
from app.demo.identity import ACCOUNTS, seed_accounts
from app.demo.obligations import seed_obligations
from app.demo.policies import SNAPSHOT_DATE, seed_policies
from app.demo.registry import build_registry, seed_registry


def main():
    settings = get_settings()
    if not settings.public_demo_enabled:
        raise SystemExit("Refused: PUBLIC_DEMO_ENABLED must be explicitly enabled.")
    expected_org = build_registry(SNAPSHOT_DATE)[0]["id"]
    if settings.demo_registry_organization_id != expected_org:
        raise SystemExit("Refused: the hosted demo must use the fictional Northstar organization.")
    engine = create_engine(settings.database_url)
    try:
        with engine.begin() as connection:
            seed_registry(connection, SNAPSHOT_DATE)
            seed_policies(connection)
            if connection.execute(select(user_account.c.id).limit(1)).first() is None:
                # Passwords are random and discarded. Public sandbox entry uses explicit personas.
                seed_accounts(connection, {name: secrets.token_urlsafe(32) for name, _, _ in ACCOUNTS})
            count = seed_obligations(connection)
        print(f"SYNTHETIC DEMO DATA: initialized sandbox; {count} new obligations. Existing completions preserved.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
