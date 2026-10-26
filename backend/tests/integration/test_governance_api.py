"""Actual PostgreSQL evidence, role scope, CSRF, and schedule progression."""
from datetime import date

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.schema import governance_obligation, obligation_completion, membership
from app.db.session import get_session
from app.demo.registry import build_registry, seed_registry
from app.demo.policies import SNAPSHOT_DATE, seed_policies
from app.demo.identity import ACCOUNTS, seed_accounts
from app.demo.obligations import seed_obligations
from app.main import app

ORIGIN = {"Origin": "http://localhost:5173"}


@pytest.fixture
def sandbox(client, registry_connection):
    c = registry_connection
    seed_registry(c, SNAPSHOT_DATE)
    seed_policies(c)
    seed_accounts(c, {name: "synthetic-test-password" for name, _, _ in ACCOUNTS})
    count = seed_obligations(c)
    assert count > 0 and seed_obligations(c) == 0
    settings = Settings(_env_file=None, database_url="postgresql+psycopg://test:test@localhost:1/test",
                        frontend_origin="http://localhost:5173", app_env="production", public_demo_enabled=True,
                        demo_registry_organization_id=build_registry(SNAPSHOT_DATE)[0]["id"])
    app.dependency_overrides[get_settings] = lambda: settings
    def sessions():
        with Session(bind=c, join_transaction_mode="create_savepoint") as session:
            yield session
    app.dependency_overrides[get_session] = sessions
    return client, c, settings


def enter(client, persona="quality"):
    response = client.post("/api/v1/auth/demo", json={"persona": persona}, headers=ORIGIN)
    assert response.status_code == 200
    return response.json()["csrf_token"]


def test_demo_is_explicit_and_origin_protected(sandbox):
    client, c, settings = sandbox
    assert client.post("/api/v1/auth/demo", json={"persona": "quality"}).status_code == 403
    assert client.post("/api/v1/auth/demo", json={"persona": "unknown"}, headers=ORIGIN).status_code == 422
    settings.public_demo_enabled = False
    assert client.post("/api/v1/auth/demo", json={"persona": "quality"}, headers=ORIGIN).status_code == 503
    settings.public_demo_enabled = True
    enter(client)
    assert client.get("/api/v1/auth/me").json()["role"] == "Quality"
    # Hosted public sandbox does not enable arbitrary password login in production.
    assert client.post("/api/v1/auth/login", headers=ORIGIN,
                       json={"email": "quality@northstar.example.test", "password": "synthetic-test-password"}).status_code == 503


@pytest.mark.parametrize("persona,total", [("admin", 48), ("quality", 48), ("owner", 3), ("viewer", 1)])
def test_portfolio_and_filter_scope(sandbox, persona, total):
    client, _, _ = sandbox
    enter(client, persona)
    result = client.get("/api/v1/governance").json()
    assert len(result["applications"]) == total
    assert sum(result["counts"].values()) == len(result["items"])
    assert all(item["application_id"] in {a["id"] for a in result["applications"]} for item in result["items"])
    filtered = client.get("/api/v1/governance?status=Overdue").json()
    assert all(item["status"] == "Overdue" for item in filtered["items"])
    assert client.get("/api/v1/governance?status=invalid").status_code == 422


def test_completion_persists_evidence_and_preserves_deadline(sandbox):
    client, c, _ = sandbox
    csrf = enter(client)
    item = client.get("/api/v1/governance").json()["items"][0]
    path = f'/api/v1/governance/{item["id"]}/complete'
    evidence = {"evidence_reference": "DEMO-PCR-001 v1.0", "notes": "Synthetic review completed; no issues found."}
    assert client.post(path, json=evidence, headers=ORIGIN).status_code == 403
    response = client.post(path, json=evidence, headers={**ORIGIN, "X-CSRF-Token": csrf})
    assert response.status_code == 201, response.text
    assert client.post(path, json=evidence, headers={**ORIGIN, "X-CSRF-Token": csrf}).status_code == 409
    result = client.get(f'/api/v1/governance?application_id={item["application_id"]}').json()
    completed = next(row for row in result["items"] if row["id"] == item["id"])
    assert completed["status"] == "Completed" and completed["due_date"] == item["due_date"]
    assert completed["evidence_reference"] == evidence["evidence_reference"]
    successor = next(row for row in result["items"] if row["id"] == response.json()["next_obligation_id"])
    assert successor["window_start"] == item["due_date"]
    assert successor["policy_version_id"] == item["policy_version_id"]
    assert successor["due_date"] > item["due_date"]
    assert c.execute(sa.select(sa.func.count()).select_from(obligation_completion)).scalar_one() == 1
    assert seed_obligations(c) == 0  # restarting cannot erase progress or duplicate schedules


def test_viewer_cannot_complete_and_hidden_obligation_is_not_found(sandbox):
    client, _, _ = sandbox
    csrf = enter(client, "quality")
    all_items = client.get("/api/v1/governance").json()["items"]
    csrf = enter(client, "viewer")
    visible = client.get("/api/v1/governance").json()["items"]
    assert client.post(f'/api/v1/governance/{visible[0]["id"]}/complete',
        json={"evidence_reference":"demo", "notes":"demo"}, headers={**ORIGIN,"X-CSRF-Token":csrf}).status_code == 403
    csrf = enter(client, "owner")
    accessible = {row["id"] for row in client.get("/api/v1/governance").json()["items"]}
    hidden = next(row for row in all_items if row["id"] not in accessible)
    assert client.get(f'/api/v1/governance?application_id={hidden["application_id"]}').status_code == 404
    assert client.post(f'/api/v1/governance/{hidden["id"]}/complete',
        json={"evidence_reference":"demo", "notes":"demo"}, headers={**ORIGIN,"X-CSRF-Token":csrf}).status_code == 404
