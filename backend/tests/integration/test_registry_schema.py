"""Verify actual migrated PostgreSQL constraints, not a substitute database."""

from datetime import timedelta
from uuid import uuid4

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app.db.schema import metadata, organization, regulated_application
from .conftest import migration_config


def insert_organization(connection, **overrides):
    values = dict(slug="northstar-demo", display_name="Northstar Biopharma (fictional)", timezone="Asia/Kolkata")
    values.update(overrides)
    return connection.execute(organization.insert().values(**values).returning(organization.c.id)).scalar_one()


def insert_application(connection, organization_id, **overrides):
    values = dict(
        organization_id=organization_id, ci_id="NSB-LIMS-001",
        name="Synthetic Laboratory Information System", system_type="LIMS",
        gxp_classification="GxP", criticality="High",
        lifecycle_state="Operational", validation_state="Validated",
    )
    values.update(overrides)
    return connection.execute(
        regulated_application.insert().values(**values).returning(regulated_application.c.id)
    ).scalar_one()


def test_fresh_migration_and_repeat_upgrade_preserve_records(registry_connection):
    connection = registry_connection
    org_id = insert_organization(connection)
    app_id = insert_application(connection, org_id)
    command.upgrade(migration_config(connection), "head")
    row = connection.execute(sa.select(regulated_application).where(
        regulated_application.c.organization_id == org_id,
        regulated_application.c.id == app_id,
    )).mappings().one()
    assert row["lifecycle_state"] == "Operational"
    assert row["validation_state"] == "Validated"
    assert row["description"] is None
    assert row["supplier"] is None and row["platform"] is None
    assert row["created_at"].utcoffset() == timedelta(0)
    assert row["updated_at"] == row["created_at"]
    assert "governance_health" not in row and "status" not in row
    assert connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one() == "0003_identity"


def test_migration_matches_core_definitions(registry_connection):
    assert compare_metadata(MigrationContext.configure(registry_connection), metadata) == []


def test_downgrade_and_upgrade_in_disposable_database(registry_connection):
    config = migration_config(registry_connection)
    command.downgrade(config, "0001_foundation")
    assert sa.inspect(registry_connection).get_table_names() == ["alembic_version"]
    command.upgrade(config, "head")
    assert set(sa.inspect(registry_connection).get_table_names()) == {
        "alembic_version", "organization", "regulated_application",
        "user_account", "membership", "application_access", "browser_session",
    }


def test_ci_unique_within_organization_but_allowed_across_organizations(registry_connection):
    connection = registry_connection
    first = insert_organization(connection)
    second = insert_organization(connection, slug="second-fictional-org")
    assert insert_application(connection, first) != insert_application(connection, second)
    with pytest.raises(IntegrityError) as error, connection.begin_nested():
        insert_application(connection, first)
    assert error.value.orig.sqlstate == "23505"


def test_organization_slug_is_unique(registry_connection):
    insert_organization(registry_connection)
    with pytest.raises(IntegrityError) as error:
        insert_organization(registry_connection)
    assert error.value.orig.sqlstate == "23505"


def test_application_requires_existing_organization(registry_connection):
    with pytest.raises(IntegrityError) as error:
        insert_application(registry_connection, uuid4())
    assert error.value.orig.sqlstate == "23503"


def test_organization_with_applications_cannot_be_deleted(registry_connection):
    org_id = insert_organization(registry_connection)
    insert_application(registry_connection, org_id)
    with pytest.raises(IntegrityError) as error:
        registry_connection.execute(organization.delete().where(organization.c.id == org_id))
    assert error.value.orig.sqlstate == "23001"  # restrict_violation


@pytest.mark.parametrize("field,value", [
    ("ci_id", ""), ("ci_id", " NSB-LIMS-001"), ("ci_id", "NSB LIMS"),
    ("name", " \t"), ("system_type", ""), ("gxp_classification", "Unknown"),
    ("criticality", "Urgent"), ("lifecycle_state", "Validated"),
    ("validation_state", "Overdue"),
])
def test_invalid_application_values_rejected(registry_connection, field, value):
    org_id = insert_organization(registry_connection)
    with pytest.raises(IntegrityError) as error:
        insert_application(registry_connection, org_id, **{field: value})
    assert error.value.orig.sqlstate == "23514"


@pytest.mark.parametrize("field", [
    "organization_id", "ci_id", "name", "system_type", "gxp_classification",
    "criticality", "lifecycle_state", "validation_state",
])
def test_required_application_fields_reject_null(registry_connection, field):
    org_id = insert_organization(registry_connection)
    values = {field: None}
    if field == "organization_id":
        org_id = None
        values = {}
    with pytest.raises(IntegrityError) as error:
        insert_application(registry_connection, org_id, **values)
    assert error.value.orig.sqlstate == "23502"


@pytest.mark.parametrize("field,value", [
    ("slug", "Invalid Slug"), ("slug", ""), ("display_name", "\n\t"), ("timezone", ""),
])
def test_invalid_organization_values_rejected(registry_connection, field, value):
    with pytest.raises(IntegrityError) as error:
        insert_organization(registry_connection, **{field: value})
    assert error.value.orig.sqlstate == "23514"


@pytest.mark.parametrize("lifecycle,validation", [
    ("Implementation", "Not Assessed"),
    ("Operational", "Remediation Required"),
    ("Retired", "Validated"),
])
def test_lifecycle_and_validation_are_independent(registry_connection, lifecycle, validation):
    org_id = insert_organization(registry_connection)
    insert_application(registry_connection, org_id, lifecycle_state=lifecycle, validation_state=validation)


def test_failed_transaction_does_not_leave_partial_registry_data(registry_connection):
    with pytest.raises(IntegrityError), registry_connection.begin_nested():
        org_id = insert_organization(registry_connection)
        insert_application(registry_connection, org_id, validation_state="Overdue")
    assert registry_connection.execute(sa.select(sa.func.count()).select_from(organization)).scalar_one() == 0
    assert registry_connection.execute(sa.select(sa.func.count()).select_from(regulated_application)).scalar_one() == 0
