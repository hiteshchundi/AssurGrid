"""Policy integrity checked against the migrated PostgreSQL schema."""
from datetime import date

from alembic import command
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app.db.schema import control_definition, governance_policy, policy_version, policy_control_rule, regulated_application, user_account
from app.demo.identity import ACCOUNTS, seed_accounts
from app.demo.registry import seed_registry
from .conftest import migration_config
from .test_registry_schema import insert_organization


def policy(connection, org, **overrides):
    values = dict(organization_id=org, policy_key="HIGH_GXP", name="Synthetic high-criticality GxP")
    values.update(overrides)
    return connection.execute(governance_policy.insert().values(**values).returning(governance_policy.c.id)).scalar_one()


def control(connection, org, **overrides):
    values = dict(organization_id=org, control_key="PCR", name="Periodic compliance review")
    values.update(overrides)
    return connection.execute(control_definition.insert().values(**values).returning(control_definition.c.id)).scalar_one()


def version(connection, org, policy_id, **overrides):
    values = dict(organization_id=org, policy_id=policy_id, version_number=1,
                  effective_from=date(2026, 1, 1), effective_to=date(2026, 7, 1),
                  gxp_classification="GxP", criticality="High", change_reason="Synthetic initial policy")
    values.update(overrides)
    return connection.execute(policy_version.insert().values(**values).returning(policy_version.c.id)).scalar_one()


def rule(connection, org, version_id, control_id, **overrides):
    values = dict(organization_id=org, policy_version_id=version_id, control_definition_id=control_id,
                  frequency_months=12, due_soon_days=30, mandatory=True, evidence_requirement="Synthetic review reference")
    values.update(overrides)
    return connection.execute(policy_control_rule.insert().values(**values).returning(policy_control_rule.c.id)).scalar_one()


def test_two_versions_select_exact_calendar_boundary_and_preserve_history(registry_connection):
    c = registry_connection
    org = insert_organization(c)
    pol, ctl = policy(c, org), control(c, org)
    first = version(c, org, pol)
    first_rule = rule(c, org, first, ctl)
    before = c.execute(sa.select(policy_control_rule).where(policy_control_rule.c.id == first_rule)).one()
    second = version(c, org, pol, version_number=2, effective_from=date(2026, 7, 1), effective_to=None,
                     change_reason="Synthetic revised frequency")
    rule(c, org, second, ctl, frequency_months=6)
    for day, expected in [(date(2026, 6, 30), first), (date(2026, 7, 1), second), (date(2030, 1, 1), second)]:
        result = c.execute(sa.select(policy_version.c.id).where(
            policy_version.c.policy_id == pol, policy_version.c.effective_from <= day,
            sa.or_(policy_version.c.effective_to.is_(None), policy_version.c.effective_to > day),
        )).scalar_one()
        assert result == expected
    assert c.execute(sa.select(policy_control_rule).where(policy_control_rule.c.id == first_rule)).one() == before


@pytest.mark.parametrize('start,end', [(date(2026, 1, 1), date(2026, 7, 1)),
    (date(2026, 6, 30), date(2027, 1, 1)), (date(2025, 1, 1), None)])
def test_overlapping_periods_rejected(registry_connection, start, end):
    c = registry_connection
    org = insert_organization(c)
    pol = policy(c, org)
    version(c, org, pol)
    with pytest.raises(IntegrityError) as error:
        version(c, org, pol, version_number=2, effective_from=start, effective_to=end)
    assert error.value.orig.sqlstate == '23P01'


def test_open_ended_period_and_overlap_update_rejected(registry_connection):
    c = registry_connection
    org = insert_organization(c)
    pol = policy(c, org)
    first = version(c, org, pol)
    version(c, org, pol, version_number=2, effective_from=date(2026, 7, 1), effective_to=None)
    with pytest.raises(IntegrityError), c.begin_nested():
        version(c, org, pol, version_number=3, effective_from=date(2030, 1, 1), effective_to=None)
    with pytest.raises(IntegrityError), c.begin_nested():
        c.execute(policy_version.update().where(policy_version.c.id == first).values(effective_to=date(2026, 7, 2)))


@pytest.mark.parametrize('field,value', [('version_number', 0), ('criticality', 'Urgent'), ('gxp_classification', 'Unknown'),
    ('change_reason', '  '), ('effective_to', date(2026, 1, 1)), ('effective_to', date(2025, 1, 1))])
def test_invalid_version_rejected(registry_connection, field, value):
    org = insert_organization(registry_connection)
    pol = policy(registry_connection, org)
    with pytest.raises(IntegrityError): version(registry_connection, org, pol, **{field:value})


@pytest.mark.parametrize('field,value', [('frequency_months', 0), ('frequency_months', -1), ('due_soon_days', -1),
    ('evidence_requirement', '  '), ('mandatory', None)])
def test_invalid_rule_rejected(registry_connection, field, value):
    c = registry_connection
    org = insert_organization(c)
    pol, ctl = policy(c, org), control(c, org)
    ver = version(c, org, pol)
    with pytest.raises(IntegrityError): rule(c, org, ver, ctl, **{field:value})


def test_cross_organization_references_rejected(registry_connection):
    c = registry_connection
    org = insert_organization(c)
    other = insert_organization(c, slug='other-org')
    pol, ctl = policy(c, org), control(c, org)
    other_pol, other_ctl = policy(c, other), control(c, other)
    ver = version(c, org, pol)
    other_ver = version(c, other, other_pol)
    with pytest.raises(IntegrityError), c.begin_nested(): version(c, other, pol)
    with pytest.raises(IntegrityError), c.begin_nested(): rule(c, org, ver, other_ctl)
    with pytest.raises(IntegrityError), c.begin_nested(): rule(c, org, other_ver, ctl)


def test_unique_keys_and_restricted_deletion(registry_connection):
    c = registry_connection
    org = insert_organization(c)
    pol, ctl = policy(c, org), control(c, org)
    ver = version(c, org, pol)
    rule(c, org, ver, ctl, due_soon_days=0, evidence_requirement=None)
    for action in [lambda: policy(c, org), lambda: control(c, org),
                   lambda: version(c, org, pol, effective_from=date(2027, 1, 1), effective_to=None),
                   lambda: rule(c, org, ver, ctl),
                   lambda: c.execute(governance_policy.delete()), lambda: c.execute(policy_version.delete()),
                   lambda: c.execute(control_definition.delete())]:
        with pytest.raises(IntegrityError), c.begin_nested(): action()


def test_policy_migration_preserves_registry_and_accounts(registry_connection):
    c = registry_connection
    config = migration_config(c)
    command.downgrade(config, '0003_identity')
    seed_registry(c, date(2026, 10, 12))
    seed_accounts(c, {name:'synthetic-test-password' for name, _, _ in ACCOUNTS})
    before_apps = c.execute(sa.select(regulated_application).order_by(regulated_application.c.id)).all()
    before_users = c.execute(sa.select(user_account).order_by(user_account.c.id)).all()
    command.upgrade(config, 'head')
    command.upgrade(config, 'head')
    assert c.execute(sa.select(sa.func.count()).select_from(governance_policy)).scalar_one() == 0
    command.downgrade(config, '0003_identity')
    assert c.execute(sa.select(regulated_application).order_by(regulated_application.c.id)).all() == before_apps
    assert c.execute(sa.select(user_account).order_by(user_account.c.id)).all() == before_users
    assert len(before_apps) == 48 and len(before_users) == 4
    command.upgrade(config, 'head')
