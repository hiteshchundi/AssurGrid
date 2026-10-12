"""Generate or insert the fictional AssurGrid registry; never reset a database."""

import argparse
from datetime import date, datetime
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from app.demo.registry import DEMO_TIMEZONE, build_registry, export_registry, seed_registry, validate_target


def main() -> int:
    parser = argparse.ArgumentParser(description="SYNTHETIC DEMO DATA: reproducible registry seed")
    parser.add_argument("--as-of", type=date.fromisoformat, default=datetime.now(ZoneInfo(DEMO_TIMEZONE)).date())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Print counts; no database or filesystem writes")
    mode.add_argument("--export-dir", type=Path, help="Write reproducible CSV fixtures and manifest; no database access")
    mode.add_argument("--apply", action="store_true", help="Insert into the explicitly confirmed local demo database")
    parser.add_argument("--confirm-demo", action="store_true", help="Confirm the target is a disposable synthetic demo database")
    args = parser.parse_args()
    _, applications = build_registry(args.as_of)
    print(f"SYNTHETIC DEMO DATA | as_of={args.as_of} | timezone={DEMO_TIMEZONE}")
    print(f"Planned dataset: 1 fictional organization, {len(applications)} fictional applications")
    try:
        if args.dry_run:
            print("Dry run only; no database connection or files written.")
        elif args.export_dir:
            export_registry(args.export_dir, args.as_of)
            print("Exported organizations.csv, applications.csv, and manifest.json.")
        else:
            # Require explicit process environment; never implicitly load the owner's .env.
            url = validate_target(os.environ.get("DATABASE_URL", ""), os.environ.get("ASSURGRID_ENV"), args.confirm_demo)
            engine = sa.create_engine(url)
            try:
                with engine.begin() as connection:
                    if connection.execute(sa.text("SELECT current_database()")).scalar_one() != "assurgrid_demo":
                        raise ValueError("Connected database must be assurgrid_demo.")
                    inserted = seed_registry(connection, args.as_of)
                print(f"Inserted: {inserted['organization']} organizations, {inserted['regulated_application']} applications.")
                print("Verified dataset: 1 organization, 48 applications. Existing matching records were preserved.")
            finally:
                engine.dispose()
    except ValueError as error:
        print(f"Refused: {error}")
        return 1
    except sa.exc.SQLAlchemyError as error:
        print(f"Database operation failed ({type(error).__name__}); no seed transaction was committed. Check connectivity and apply migrations first.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
