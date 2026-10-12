"""Create four demo role categories without saved/default passwords."""
import argparse
import getpass
import os
import sys

import sqlalchemy as sa

from app.demo.identity import ACCOUNTS, seed_accounts
from app.demo.registry import validate_target


def main() -> int:
    parser = argparse.ArgumentParser(description="Create fictional demo accounts using hidden password prompts")
    parser.add_argument("--confirm-demo", action="store_true")
    args = parser.parse_args()
    try:
        url = validate_target(os.environ.get("DATABASE_URL", ""), os.environ.get("ASSURGRID_ENV"), args.confirm_demo)
        if not sys.stdin.isatty():
            raise ValueError("Run account setup in an interactive terminal so passwords remain hidden.")
        passwords = {name: getpass.getpass(f"Password for {name}@northstar.example.test (12–256 characters): ") for name, _, _ in ACCOUNTS}
        engine = sa.create_engine(url)
        try:
            with engine.begin() as connection:
                if connection.execute(sa.text("SELECT current_database()")).scalar_one() != "assurgrid_demo":
                    raise ValueError("Connected database must be assurgrid_demo.")
                inserted = seed_accounts(connection, passwords)
            print(f"SYNTHETIC DEMO DATA: {inserted} accounts inserted; four role categories verified. No credentials exported.")
        finally:
            engine.dispose()
    except (ValueError, EOFError) as error:
        print(f"Refused: {error}")
        return 1
    except sa.exc.SQLAlchemyError as error:
        print(f"Database operation failed ({type(error).__name__}); no account transaction committed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
