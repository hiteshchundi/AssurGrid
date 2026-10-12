"""Real sessions and scope checks through HTTP against disposable PostgreSQL."""
from datetime import timedelta

import pytest
from pydantic import HttpUrl
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.schema import application_access, browser_session, membership, user_account
from app.db.session import get_session
from app.main import app
from app.modules.auth.router import COOKIE, now
from app.modules.auth.security import hash_password, token_hash
from .test_identity_schema import account
from .test_registry_schema import insert_application, insert_organization

ORIGIN = {"Origin": "http://localhost:5173"}


@pytest.fixture
def auth_client(client, registry_connection):
    c = registry_connection
    org = insert_organization(c)
    user = account(c, password_hash=hash_password("fictional-test-password"))
    c.execute(membership.insert().values(organization_id=org, user_id=user, role="Viewer"))
    assigned = insert_application(c, org)
    hidden = insert_application(c, org, ci_id="NSB-OTHER-002")
    other = insert_organization(c, slug="other-org")
    foreign = insert_application(c, other)
    c.execute(application_access.insert().values(organization_id=org, user_id=user, application_id=assigned))
    settings = Settings(_env_file=None, database_url="postgresql+psycopg://test:test@localhost:1/test",
                        frontend_origin="http://localhost:5173", app_env="development", demo_registry_organization_id=org)
    app.dependency_overrides[get_settings] = lambda: settings
    def test_session():
        with Session(bind=c, join_transaction_mode="create_savepoint") as session:
            yield session
    app.dependency_overrides[get_session] = test_session
    return client, c, user, assigned, hidden, foreign, settings


def login(client, **overrides):
    body = dict(email="owner@example.test", password="fictional-test-password")
    body.update(overrides)
    return client.post("/api/v1/auth/login", json=body, headers=ORIGIN)


def test_login_cookie_digests_scope_and_logout(auth_client):
    client, c, user, assigned, hidden, foreign, _ = auth_client
    assert client.get("/api/v1/applications").status_code == 401
    response = login(client)
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie and "Path=/api/v1" in cookie
    token = client.cookies.get(COOKIE)
    csrf = response.json()["csrf_token"]
    stored = c.execute(sa.select(browser_session)).mappings().one()
    assert stored["token_hash"] == token_hash(token) and stored["csrf_token_hash"] == token_hash(csrf)
    assert token not in str(stored) and csrf not in str(stored)
    assert client.get("/api/v1/auth/me").json()["role"] == "Viewer"
    page = client.get("/api/v1/applications").json()
    assert page["total"] == 1 and page["items"][0]["id"] == str(assigned)
    for denied in (hidden, foreign):
        assert client.get(f"/api/v1/applications/{denied}").status_code == 404
    assert client.post("/api/v1/auth/logout", headers=ORIGIN).status_code == 403
    assert client.post("/api/v1/auth/logout", headers={**ORIGIN, "X-CSRF-Token": csrf}).status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.set(COOKIE, token, path="/api/v1")
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("role,total", [("Admin", 2), ("Quality", 2), ("Application Owner", 1), ("Viewer", 1)])
def test_roles_and_scope_resolved_each_request(auth_client, role, total):
    client, c, *_ = auth_client
    assert login(client).status_code == 200
    c.execute(membership.update().values(role=role))
    assert client.get("/api/v1/auth/me").json()["role"] == role
    assert client.get("/api/v1/applications").json()["total"] == total
    c.execute(application_access.delete())
    assert client.get("/api/v1/applications").json()["total"] == (2 if role in ("Admin", "Quality") else 0)


@pytest.mark.parametrize("invalidation", ["account", "membership", "expiry", "revocation"])
def test_invalid_sessions_rejected(auth_client, invalidation):
    client, c, *_ = auth_client
    login(client)
    if invalidation == "account":
        c.execute(user_account.update().values(active=False))
    elif invalidation == "membership":
        c.execute(membership.update().values(active=False))
    elif invalidation == "expiry":
        c.execute(browser_session.update().values(created_at=now()-timedelta(hours=9), expires_at=now()-timedelta(hours=1)))
    else:
        c.execute(browser_session.update().values(revoked_at=now()))
    assert client.get("/api/v1/applications").status_code == 401


def test_invalid_credentials_origins_and_client_role(auth_client):
    client, c, *_ = auth_client
    bad = login(client, password="wrong")
    unknown = login(client, email="nobody@example.test")
    assert bad.status_code == unknown.status_code == 401 and bad.json() == unknown.json()
    assert login(client, role="Admin").status_code == 422
    assert client.post("/api/v1/auth/login", json={"email":"owner@example.test", "password":"fictional-test-password"}).status_code == 403
    assert c.execute(sa.select(sa.func.count()).select_from(browser_session)).scalar_one() == 0
    csrf = login(client).json()["csrf_token"]
    assert client.post("/api/v1/auth/logout", headers={"Origin":"https://evil.example", "X-CSRF-Token":csrf}).status_code == 403
    assert client.get("/api/v1/auth/me").status_code == 200


def test_relogin_revokes_old_token_and_production_login_disabled(auth_client):
    client, c, *_, settings = auth_client
    login(client)
    old = client.cookies.get(COOKIE)
    login(client)
    assert old != client.cookies.get(COOKIE)
    assert c.execute(sa.select(browser_session.c.revoked_at).where(browser_session.c.token_hash == token_hash(old))).scalar_one() is not None
    settings.app_env = "production"
    assert login(client).status_code == 503


def test_https_cookie_and_validation_do_not_echo_password(auth_client):
    client, c, *_, settings = auth_client
    settings.frontend_origin = HttpUrl("https://localhost:5173")
    response = client.post("/api/v1/auth/login", headers={"Origin":"https://localhost:5173"},
                           json={"email":"owner@example.test", "password":"fictional-test-password"})
    assert response.status_code == 200 and "Secure" in response.headers["set-cookie"]
    assert response.headers["cache-control"] == "no-store"
    secret = "test-sensitive-value" * 30
    invalid = login(client, password=secret)
    assert invalid.status_code == 422 and secret not in invalid.text


def test_database_errors_are_safe(auth_client, caplog):
    from unittest.mock import MagicMock
    from sqlalchemy.exc import OperationalError
    client, *_ = auth_client
    session = MagicMock()
    session.execute.side_effect = OperationalError("private SQL", {}, Exception("private credentials"))
    app.dependency_overrides[get_session] = lambda: session
    response = login(client)
    assert response.status_code == 503
    assert "private" not in response.text + caplog.text
    session.rollback.assert_called_once()


def test_csrf_recovery_requires_origin_and_rotates_token(auth_client):
    client, *_ = auth_client
    old = login(client).json()['csrf_token']
    assert client.post('/api/v1/auth/csrf').status_code == 403
    response = client.post('/api/v1/auth/csrf', headers=ORIGIN)
    assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
    new = response.json()['csrf_token']
    assert new != old
    assert client.post('/api/v1/auth/logout', headers={**ORIGIN, 'X-CSRF-Token':old}).status_code == 403
    assert client.post('/api/v1/auth/logout', headers={**ORIGIN, 'X-CSRF-Token':new}).status_code == 204
    assert client.post('/api/v1/auth/csrf', headers=ORIGIN).status_code == 401
