from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.main import app
from app.modules.auth.router import Principal, get_principal


def test_registry_requires_authentication(client):
    for path in ("/api/v1/applications", f"/api/v1/applications/{uuid4()}"):
        assert client.get(path).status_code == 401


@pytest.mark.parametrize("path", ["/api/v1/applications", f"/api/v1/applications/{uuid4()}"])
def test_registry_database_failure_has_safe_response(client, path, caplog):
    session = MagicMock()
    session.execute.side_effect = OperationalError("private SQL", {}, Exception("secret credentials"))
    app.dependency_overrides[get_principal] = lambda: Principal(uuid4(), uuid4(), "Admin", uuid4(), "a" * 64)
    app.dependency_overrides[get_session] = lambda: session
    response = client.get(path)
    assert response.status_code == 503
    assert response.json() == {"detail": "Application registry is temporarily unavailable."}
    assert "secret credentials" not in response.text + caplog.text
    assert "private SQL" not in response.text + caplog.text


@pytest.mark.parametrize("params", [
    {"page": 0}, {"page": 10001}, {"page": "invalid"}, {"page_size": 0}, {"page_size": 101},
    {"search": "x" * 101}, {"classification": "Unknown"}, {"criticality": "Urgent"},
    {"lifecycle_state": "Validated"}, {"validation_state": "Overdue"},
    {"organization_id": str(uuid4())}, {"health": "Current"},
])
def test_invalid_filters_are_rejected_without_queries(client, params):
    session = MagicMock()
    app.dependency_overrides[get_principal] = lambda: Principal(uuid4(), uuid4(), "Admin", uuid4(), "a" * 64)
    app.dependency_overrides[get_session] = lambda: session
    assert client.get("/api/v1/applications", params=params).status_code == 422
    session.execute.assert_not_called()


def test_invalid_application_id_and_mutation_methods(client):
    session = MagicMock()
    app.dependency_overrides[get_principal] = lambda: Principal(uuid4(), uuid4(), "Admin", uuid4(), "a" * 64)
    app.dependency_overrides[get_session] = lambda: session
    assert client.get("/api/v1/applications/not-a-uuid").status_code == 422
    assert client.post("/api/v1/applications", json={}).status_code == 405
    assert client.patch(f"/api/v1/applications/{uuid4()}", json={}).status_code == 405
    session.execute.assert_not_called()
