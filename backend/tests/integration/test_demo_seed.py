from datetime import date, timedelta
import os
from pathlib import Path
import subprocess
import sys

from alembic import command
import pytest
import sqlalchemy as sa

from app.db.schema import organization, regulated_application
from app.demo.registry import build_registry, seed_registry
from .conftest import migration_config

AS_OF = date(2026, 10, 12)


def test_seed_twice_keeps_ids_counts_dates_and_no_orphans(registry_connection):
    connection = registry_connection
    assert seed_registry(connection, AS_OF) == {"organization": 1, "regulated_application": 48}
    before = connection.execute(sa.select(regulated_application).order_by(regulated_application.c.ci_id)).all()
    assert seed_registry(connection, AS_OF) == {"organization": 0, "regulated_application": 0}
    assert connection.execute(sa.select(regulated_application).order_by(regulated_application.c.ci_id)).all() == before
    assert connection.execute(sa.select(sa.func.count()).select_from(organization)).scalar_one() == 1
    assert len(before) == 48
    assert connection.execute(sa.text(
        "SELECT count(*) FROM regulated_application a LEFT JOIN organization o ON o.id = a.organization_id WHERE o.id IS NULL"
    )).scalar_one() == 0


@pytest.mark.parametrize("change", ["application", "organization", "as_of"])
def test_seed_refuses_to_overwrite_existing_changes(registry_connection, change):
    connection = registry_connection
    seed_registry(connection, AS_OF)
    if change == "application":
        connection.execute(regulated_application.update().values(name="Edited by owner"))
    if change == "organization":
        connection.execute(organization.update().values(display_name="Edited organization"))
    before = connection.execute(sa.select(regulated_application)).all()
    with pytest.raises(ValueError, match="changed records"):
        seed_registry(connection, AS_OF + timedelta(days=1) if change == "as_of" else AS_OF)
    assert connection.execute(sa.select(regulated_application)).all() == before


def test_non_demo_database_records_are_left_alone(registry_connection):
    connection = registry_connection
    connection.execute(organization.insert().values(slug="existing-org", display_name="Existing test record", timezone="UTC"))
    with pytest.raises(ValueError, match="non-seed"):
        seed_registry(connection, AS_OF)
    assert connection.execute(sa.select(organization.c.slug)).scalars().all() == ["existing-org"]
    assert connection.execute(sa.select(sa.func.count()).select_from(regulated_application)).scalar_one() == 0


def test_seed_fills_partial_matching_dataset(registry_connection):
    org, apps = build_registry(AS_OF)
    registry_connection.execute(organization.insert(), org)
    registry_connection.execute(regulated_application.insert(), apps[:7])
    assert seed_registry(registry_connection, AS_OF) == {"organization": 0, "regulated_application": 41}


def test_seed_transaction_rolls_back_as_a_unit(registry_connection):
    with pytest.raises(RuntimeError), registry_connection.begin_nested():
        seed_registry(registry_connection, AS_OF)
        raise RuntimeError("Simulated failure before caller commits")
    assert registry_connection.execute(sa.select(sa.func.count()).select_from(organization)).scalar_one() == 0
    assert registry_connection.execute(sa.select(sa.func.count()).select_from(regulated_application)).scalar_one() == 0


def test_actual_cli_applies_twice_and_refuses_changed_date(registry_engine):
    # registry_engine always points at the test fixture's freshly created private cluster.
    with registry_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as admin:
        admin.execute(sa.text("CREATE DATABASE assurgrid_demo"))
    url = registry_engine.url.set(database="assurgrid_demo")
    engine = sa.create_engine(url)
    try:
        with engine.begin() as connection:
            command.upgrade(migration_config(connection), "head")
        env = {**os.environ, "ASSURGRID_ENV": "development", "DATABASE_URL": url.render_as_string(hide_password=False)}
        script = Path(__file__).resolve().parents[2] / "scripts/seed_demo.py"
        args = [sys.executable, str(script), "--apply", "--confirm-demo", "--as-of"]
        first = subprocess.run([*args, str(AS_OF)], env=env, capture_output=True, text=True)
        assert first.returncode == 0, first.stdout + first.stderr
        assert "Inserted: 1 organizations, 48 applications" in first.stdout
        second = subprocess.run([*args, str(AS_OF)], env=env, capture_output=True, text=True)
        assert second.returncode == 0, second.stdout + second.stderr
        assert "Inserted: 0 organizations, 0 applications" in second.stdout
        refused = subprocess.run([*args, str(AS_OF + timedelta(days=1))], env=env, capture_output=True, text=True)
        assert refused.returncode == 1
        assert "no data was overwritten" in refused.stdout
        with engine.connect() as connection:
            assert connection.execute(sa.select(sa.func.count()).select_from(regulated_application)).scalar_one() == 48
    finally:
        engine.dispose()
        with registry_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as admin:
            admin.execute(sa.text("DROP DATABASE assurgrid_demo"))
