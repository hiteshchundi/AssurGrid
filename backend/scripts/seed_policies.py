"""Preview/export or explicitly insert fictional policy fixtures into a local demo DB."""
import argparse
import os
from pathlib import Path

import sqlalchemy as sa

from app.demo.policies import build_policies, export_policies, seed_policies
from app.demo.registry import validate_target


def main() -> int:
    parser = argparse.ArgumentParser(description="SYNTHETIC DEMO DATA: illustrative organization policies")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--export", type=Path, help="Write deterministic JSON; no database access")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-demo", action="store_true")
    args = parser.parse_args()
    print("SYNTHETIC DEMO DATA — illustrative organization policies, not regulatory requirements.")
    print("Planned: " + ", ".join(f"{len(rows)} {name}" for name, rows in build_policies().items()))
    try:
        if args.dry_run:
            print("Dry run only; no database or filesystem changes.")
        elif args.export:
            export_policies(args.export)
            print("Exported deterministic fictional policy JSON.")
        else:
            url = validate_target(os.environ.get("DATABASE_URL", ""), os.environ.get("ASSURGRID_ENV"), args.confirm_demo)
            engine = sa.create_engine(url)
            try:
                with engine.begin() as connection:
                    if connection.execute(sa.text("SELECT current_database()")).scalar_one() != "assurgrid_demo":
                        raise ValueError("Connected database must be assurgrid_demo.")
                    inserted = seed_policies(connection)
                print("Inserted: " + ", ".join(f"{count} {name}" for name, count in inserted.items()))
            finally:
                engine.dispose()
    except ValueError as error:
        print(f"Refused: {error}")
        return 1
    except sa.exc.SQLAlchemyError as error:
        print(f"Database operation failed ({type(error).__name__}); no policy transaction committed. Apply migrations first.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
