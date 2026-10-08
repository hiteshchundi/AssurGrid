import os

import pytest
from fastapi.testclient import TestClient

# Tests never read developer secrets or require a running database.
os.environ["DATABASE_URL"] = "postgresql+psycopg://test:test@localhost:1/test?connect_timeout=1"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
