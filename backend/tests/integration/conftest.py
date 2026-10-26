"""Opt-in supported PostgreSQL tests in a disposable, socket-only local cluster."""

import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


def migration_config(connection):
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.attributes["connection"] = connection
    return config


@pytest.fixture(scope="session")
def registry_engine():
    binary_dir = os.environ.get("ASSURGRID_TEST_POSTGRES_BIN")
    if not binary_dir:
        pytest.skip("Set ASSURGRID_TEST_POSTGRES_BIN to run disposable PostgreSQL integration tests")
    binaries = Path(binary_dir)
    version = subprocess.run(
        [str(binaries / "postgres"), "--version"], check=True, capture_output=True, text=True,
    ).stdout
    if not any(f"(PostgreSQL) {major}." in version for major in (17, 18)):
        pytest.fail("Integration tests require PostgreSQL 17 or 18 binaries")

    # A short, private socket path avoids OS path limits and any developer server.
    with TemporaryDirectory(prefix="ag-test-", dir="/tmp") as directory:
        root = Path(directory)
        data = root / "data"
        socket = root / "socket"
        socket.mkdir(mode=0o700)
        subprocess.run(
            [str(binaries / "initdb"), "-D", str(data), "-U", "assurgrid_test",
             "--auth-local=trust", "--auth-host=reject", "--encoding=UTF8", "--locale=C"],
            check=True, capture_output=True, text=True,
        )
        pg_ctl = [str(binaries / "pg_ctl"), "-D", str(data)]
        engine = None
        try:
            subprocess.run(
                [*pg_ctl, "-l", str(root / "postgres.log"), "-o",
                 f"-h '' -k {socket} -c timezone=UTC", "-w", "start"],
                check=True, capture_output=True, text=True,
            )
            engine = create_engine(URL.create(
                "postgresql+psycopg", username="assurgrid_test", database="postgres",
                query={"host": str(socket)},
            ))
            with engine.begin() as connection:
                command.upgrade(migration_config(connection), "head")
            yield engine
        finally:
            if engine is not None:
                engine.dispose()
            if (data / "postmaster.pid").exists():
                subprocess.run([*pg_ctl, "-m", "fast", "-w", "stop"], check=True, capture_output=True)


@pytest.fixture
def registry_connection(registry_engine):
    with registry_engine.connect() as connection:
        transaction = connection.begin()
        try:
            yield connection
        finally:
            transaction.rollback()
