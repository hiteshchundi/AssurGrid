from unittest.mock import MagicMock

from sqlalchemy.exc import OperationalError

from app.db.session import get_session
from app.main import app


def test_liveness_does_not_open_database(client):
    def forbidden_session():
        raise AssertionError("Liveness must not access PostgreSQL")

    app.dependency_overrides[get_session] = forbidden_session
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_connected(client):
    session = MagicMock()
    session.execute.return_value.scalar_one.return_value = 1
    app.dependency_overrides[get_session] = lambda: session
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "connected"}
    assert str(session.execute.call_args.args[0]) == "SELECT 1"


def test_database_failure_preserves_liveness_and_hides_details(client):
    session = MagicMock()
    session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("private credential"))
    app.dependency_overrides[get_session] = lambda: session
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unavailable"}
    assert "private credential" not in response.text
    assert client.get("/api/v1/health/live").status_code == 200


def test_cors_allows_only_configured_origin(client):
    allowed = client.get("/api/v1/health/live", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    denied = client.get("/api/v1/health/live", headers={"Origin": "https://other.example"})
    assert "access-control-allow-origin" not in denied.headers
