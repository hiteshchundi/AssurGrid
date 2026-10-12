"""Identity boundaries verified against migrated, disposable PostgreSQL."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from alembic import command
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app.db.schema import application_access, browser_session, membership, regulated_application, user_account
from app.demo.registry import seed_registry
from .conftest import migration_config
from .test_registry_schema import insert_application, insert_organization


def account(connection, **overrides):
    values = dict(email="owner@example.test", display_name="Synthetic Owner", password_hash="test-only-placeholder")
    values.update(overrides)
    return connection.execute(user_account.insert().values(**values).returning(user_account.c.id)).scalar_one()


def identity(connection):
    org = insert_organization(connection)
    user = account(connection)
    connection.execute(membership.insert().values(organization_id=org, user_id=user, role="Application Owner"))
    return org, user


def session_values(org, user):
    now = datetime(2026, 10, 12, tzinfo=timezone.utc)
    return dict(organization_id=org, user_id=user, token_hash="a" * 64, csrf_token_hash="b" * 64,
                created_at=now, expires_at=now + timedelta(hours=8))


def test_registry_survives_identity_upgrade_and_downgrade(registry_connection):
    c = registry_connection
    config = migration_config(c)
    command.downgrade(config, "0002_application_registry")
    seed_registry(c, date(2026, 10, 12))
    before = c.execute(sa.select(regulated_application).order_by(regulated_application.c.id)).all()
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    assert c.execute(sa.select(sa.func.count()).select_from(user_account)).scalar_one() == 0
    account(c)
    command.downgrade(config, "0002_application_registry")
    assert c.execute(sa.select(regulated_application).order_by(regulated_application.c.id)).all() == before
    assert len(before) == 48
    command.upgrade(config, "head")


@pytest.mark.parametrize("email", ["Owner@example.test", " owner@example.test", "owner @example.test", "no-at", "a@@b"])
def test_noncanonical_email_rejected(registry_connection, email):
    with pytest.raises(IntegrityError):
        account(registry_connection, email=email)


def test_duplicate_email_rejected(registry_connection):
    account(registry_connection)
    with pytest.raises(IntegrityError):
        account(registry_connection)


@pytest.mark.parametrize("role", ["Admin", "Quality", "Application Owner", "Viewer"])
def test_provisional_roles_supported(registry_connection, role):
    org, user = identity(registry_connection)
    registry_connection.execute(membership.update().values(role=role))
    assert registry_connection.execute(sa.select(membership.c.role)).scalar_one() == role


def test_unknown_role_rejected(registry_connection):
    identity(registry_connection)
    with pytest.raises(IntegrityError):
        registry_connection.execute(membership.update().values(role="Superuser"))


@pytest.mark.parametrize("mismatch", ["application", "membership"])
def test_cross_organization_access_rejected(registry_connection, mismatch):
    c = registry_connection
    org, user = identity(c)
    other = insert_organization(c, slug="other-org")
    app = insert_application(c, other)
    with pytest.raises(IntegrityError):
        c.execute(application_access.insert().values(
            organization_id=other if mismatch == "membership" else org, user_id=user, application_id=app))


def test_valid_access_and_session_and_restrict_delete(registry_connection):
    c = registry_connection
    org, user = identity(c)
    app = insert_application(c, org)
    c.execute(application_access.insert().values(organization_id=org, user_id=user, application_id=app))
    c.execute(browser_session.insert().values(**session_values(org, user)))
    with pytest.raises(IntegrityError), c.begin_nested():
        c.execute(membership.delete())
    with pytest.raises(IntegrityError), c.begin_nested():
        c.execute(user_account.delete())
    with pytest.raises(IntegrityError), c.begin_nested():
        c.execute(application_access.insert().values(organization_id=org, user_id=user, application_id=app))


@pytest.mark.parametrize("field,value", [
    ("token_hash", "raw-token"), ("csrf_token_hash", "B" * 64),
    ("expires_at", datetime(2026, 10, 12, tzinfo=timezone.utc)),
    ("revoked_at", datetime(2026, 10, 11, tzinfo=timezone.utc)),
    ("user_id", uuid4()), ("organization_id", uuid4()),
])
def test_invalid_session_rejected(registry_connection, field, value):
    org, user = identity(registry_connection)
    values = session_values(org, user)
    values[field] = value
    with pytest.raises(IntegrityError):
        registry_connection.execute(browser_session.insert().values(**values))


def test_duplicate_session_token_rejected(registry_connection):
    org, user = identity(registry_connection)
    values = session_values(org, user)
    registry_connection.execute(browser_session.insert().values(**values))
    with pytest.raises(IntegrityError):
        registry_connection.execute(browser_session.insert().values(**values))
