from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.schema import organization, regulated_application
from app.db.session import get_session
from app.demo.registry import build_registry, seed_registry
from app.main import app
from app.modules.auth.router import Principal, get_principal
from .test_registry_schema import insert_application, insert_organization

AS_OF = date(2026, 10, 12)
ORG, APPLICATIONS = build_registry(AS_OF)


@pytest.fixture
def registry_client(client, registry_connection):
    seed_registry(registry_connection, AS_OF)
    app.dependency_overrides[get_principal] = lambda: Principal(uuid4(), ORG["id"], "Admin", uuid4(), "a" * 64)
    settings = Settings(
        _env_file=None, database_url="postgresql+psycopg://test:test@localhost:1/test",
        frontend_origin="http://localhost:5173", app_env="development",
        demo_registry_organization_id=ORG["id"],
    )
    app.dependency_overrides[get_settings] = lambda: settings
    def test_session():
        with Session(bind=registry_connection, join_transaction_mode="create_savepoint") as session:
            yield session
    app.dependency_overrides[get_session] = test_session
    yield client


def test_list_is_paginated_stable_and_has_honest_fields(registry_client):
    pages = [registry_client.get("/api/v1/applications", params={"page": page}).json() for page in (1, 2, 3)]
    assert [len(page["items"]) for page in pages] == [20, 20, 8]
    assert all(page["total"] == 48 and page["page_size"] == 20 for page in pages)
    rows = [row for page in pages for row in page["items"]]
    assert len({row["id"] for row in rows}) == 48
    assert [row["ci_id"] for row in rows] == sorted(row["ci_id"] for row in rows)
    for row in rows:
        assert row["organization_id"] == str(ORG["id"])
        assert row["business_owner_id"] is None and row["technical_owner_id"] is None and row["quality_owner_id"] is None
        assert "governance_health" not in row
        assert "SYNTHETIC DEMO DATA" in row["description"]
    empty = registry_client.get("/api/v1/applications", params={"page": 4}).json()
    assert empty == {"items": [], "total": 48, "page": 4, "page_size": 20}


@pytest.mark.parametrize("params,total", [
    ({"classification": "Non-GxP"}, 7), ({"criticality": "High"}, 18),
    ({"lifecycle_state": "Implementation"}, 12), ({"validation_state": "Remediation Required"}, 5),
    ({"search": "clinical"}, 3), ({"search": " nsb-lims-001 "}, 1),
    ({"search": "nothing matches"}, 0), ({"search": "%"}, 0), ({"search": "_"}, 0),
    ({"search": "' OR 1=1 --"}, 0),
    ({"search": "LIMS", "classification": "GxP", "criticality": "High", "lifecycle_state": "Operational", "validation_state": "Validated"}, 1),
    ({"search": "LIMS", "classification": "Non-GxP"}, 0),
])
def test_registry_filters(registry_client, params, total):
    response = registry_client.get("/api/v1/applications", params={**params, "page_size": 100})
    assert response.status_code == 200
    assert response.json()["total"] == total
    assert len(response.json()["items"]) == total


def test_detail_matches_list_and_unknown_id_is_not_found(registry_client):
    item = registry_client.get("/api/v1/applications", params={"search": "NSB-LIMS-001"}).json()["items"][0]
    response = registry_client.get(f"/api/v1/applications/{item['id']}")
    assert response.status_code == 200
    assert response.json() == item
    assert item["lifecycle_state"] == "Operational" and item["validation_state"] == "Validated"
    assert item["created_at"] == "2026-10-11T18:30:00Z"
    assert registry_client.get(f"/api/v1/applications/{uuid4()}").status_code == 404


def test_other_organization_cannot_leak_through_search_count_or_detail(registry_client, registry_connection):
    other_org = insert_organization(registry_connection, slug="other-test-org")
    foreign_id = insert_application(registry_connection, other_org)  # Same CI, different organization.
    assert registry_client.get("/api/v1/applications").json()["total"] == 48
    found = registry_client.get("/api/v1/applications", params={"search": "NSB-LIMS-001"}).json()
    assert found["total"] == 1 and found["items"][0]["id"] != str(foreign_id)
    foreign = registry_client.get(f"/api/v1/applications/{foreign_id}")
    missing = registry_client.get(f"/api/v1/applications/{uuid4()}")
    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json() == {"detail": "Application not found."}
    assert registry_client.get("/api/v1/applications", params={"organization_id": str(other_org)}).status_code == 422
    assert registry_client.get(f"/api/v1/applications/{foreign_id}", params={"organization_id": str(other_org)}).status_code == 404


def test_empty_registry(registry_client, registry_connection):
    registry_connection.execute(regulated_application.delete())
    registry_connection.execute(organization.delete())
    assert registry_client.get("/api/v1/applications").json() == {"items": [], "total": 0, "page": 1, "page_size": 20}


def test_search_is_bound_as_data_and_page_and_count_use_one_statement(registry_client, registry_connection):
    statements = []
    def capture(connection, cursor, statement, parameters, context, executemany):
        if "filtered_applications" in statement:
            statements.append((statement, parameters))
    event.listen(registry_connection, "before_cursor_execute", capture)
    try:
        needle = "' OR 1=1 --"
        assert registry_client.get("/api/v1/applications", params={"search": needle}).status_code == 200
        assert len(statements) == 1
        sql, parameters = statements[0]
        assert needle not in sql and needle in parameters.values()
        assert ORG["id"] in parameters.values()
    finally:
        event.remove(registry_connection, "before_cursor_execute", capture)
