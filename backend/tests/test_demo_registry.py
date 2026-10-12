import csv
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from app.demo.registry import build_registry, export_registry, validate_target

ROOT = Path(__file__).resolve().parents[2]
AS_OF = date(2026, 10, 12)


def test_registry_is_reproducible_diverse_and_has_required_identities():
    org, apps = build_registry(AS_OF)
    assert (org, apps) == build_registry(AS_OF)
    assert len(apps) == len({row["ci_id"] for row in apps}) == len({row["id"] for row in apps}) == 48
    assert all(row["organization_id"] == org["id"] for row in apps)
    assert [row["ci_id"] for row in apps[:7]] == [
        "NSB-LIMS-001", "NSB-CDMS-002", "NSB-QMS-003", "NSB-MES-004",
        "NSB-SAFETY-005", "NSB-ERP-006", "NSB-ATR-007",
    ]
    assert all(row["lifecycle_state"] == "Operational" and row["validation_state"] == "Validated" for row in apps[:5])
    assert apps[5]["gxp_classification"] == "Non-GxP"
    assert {row["gxp_classification"] for row in apps} == {"GxP", "Non-GxP"}
    assert {row["criticality"] for row in apps} == {"High", "Medium", "Low"}
    assert len({row["lifecycle_state"] for row in apps}) == 4
    assert len({row["validation_state"] for row in apps}) == 5
    assert all("SYNTHETIC DEMO DATA" in row["description"] for row in apps)
    assert all("governance_health" not in row and row["created_at"] == row["updated_at"] for row in apps)
    assert org["created_at"].isoformat() == "2026-10-11T18:30:00+00:00"
    _, next_day = build_registry(AS_OF + timedelta(days=1))
    assert [row["id"] for row in apps] == [row["id"] for row in next_day]


def test_exports_match_checked_in_snapshot_and_manifest(tmp_path):
    export_registry(tmp_path, AS_OF)
    original = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    export_registry(tmp_path, AS_OF)
    assert original == {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    for filename, content in original.items():
        assert content == (ROOT / "mock-data" / "generated" / filename).read_bytes()
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    for filename, count in (("organizations.csv", 1), ("applications.csv", 48)):
        assert hashlib.sha256(original[filename]).hexdigest() == manifest["sha256"][filename]
        with (tmp_path / filename).open() as file:
            rows = list(csv.DictReader(file))
        assert len(rows) == count
        assert all(row["source_system"] == "SYNTHETIC" for row in rows)


@pytest.mark.parametrize("url,environment,confirmed", [
    ("postgresql+psycopg://localhost/assurgrid_demo", "production", True),
    ("postgresql+psycopg://localhost/assurgrid_demo", None, True),
    ("postgresql+psycopg://localhost/assurgrid_demo", "development", False),
    ("postgresql+psycopg://localhost/assurgrid", "development", True),
    ("postgresql+psycopg://remote.example/assurgrid_demo", "development", True),
    ("postgresql+psycopg://localhost/assurgrid_demo?host=remote.example", "development", True),
    ("postgresql+psycopg://localhost/assurgrid_demo?hostaddr=192.0.2.1", "development", True),
    ("postgresql+psycopg:///assurgrid_demo", "development", True),
    ("postgresql+psycopg:///assurgrid_demo?service=production", "development", True),
    ("sqlite:///assurgrid_demo", "development", True),
])
def test_apply_target_guard(url, environment, confirmed):
    with pytest.raises(ValueError):
        validate_target(url, environment, confirmed)


def test_dry_run_cli_has_no_database_dependency(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "backend/scripts/seed_demo.py"), "--as-of", str(AS_OF), "--dry-run"],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    assert "48 fictional applications" in result.stdout
    assert "as_of=2026-10-12" in result.stdout
    assert not list(tmp_path.iterdir())
