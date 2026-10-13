from datetime import date
import os
from pathlib import Path
import subprocess
import sys

from alembic import command
import pytest
import sqlalchemy as sa

from app.db.schema import control_definition, governance_policy, policy_control_rule, policy_version, regulated_application
from app.demo.policies import TABLES, build_policies, identity, seed_policies
from app.demo.registry import seed_registry
from .conftest import migration_config


def snapshot(c):
    return {table.name:c.execute(sa.select(table).order_by(table.c.id)).all() for table in TABLES}


def test_repeat_seed_preserves_all_records_and_effective_boundary(registry_connection):
    c = registry_connection
    seed_registry(c, date(2026, 10, 12))
    registry = c.execute(sa.select(regulated_application).order_by(regulated_application.c.id)).all()
    assert seed_policies(c) == {'control_definition':4, 'governance_policy':2, 'policy_version':3, 'policy_control_rule':10}
    before = snapshot(c)
    assert all(count == 0 for count in seed_policies(c).values())
    assert snapshot(c) == before
    assert c.execute(sa.select(regulated_application).order_by(regulated_application.c.id)).all() == registry
    for day, months in [(date(2026, 6, 30), 24), (date(2026, 7, 1), 12)]:
        actual = c.execute(sa.select(policy_control_rule.c.frequency_months).join(
            policy_version, policy_version.c.id == policy_control_rule.c.policy_version_id,
        ).where(policy_version.c.policy_id == identity('policy/HIGH_GXP'),
                policy_control_rule.c.control_definition_id == identity('control/PCR'),
                policy_version.c.effective_from <= day,
                sa.or_(policy_version.c.effective_to.is_(None), policy_version.c.effective_to > day))).scalar_one()
        assert actual == months


@pytest.mark.parametrize('change', ['frequency', 'reason', 'control', 'extra'])
def test_changed_records_refused_without_partial_writes(registry_connection, change):
    c = registry_connection
    seed_registry(c, date(2026, 10, 12))
    seed_policies(c)
    # Remove one fixture rule to ensure refusal cannot insert it before all comparisons finish.
    c.execute(policy_control_rule.delete().where(policy_control_rule.c.id == identity('rule/MEDIUM_GXP/1/PCR')))
    if change == 'frequency': c.execute(policy_control_rule.update().values(frequency_months=99))
    elif change == 'reason': c.execute(policy_version.update().values(change_reason='Edited by owner'))
    elif change == 'control': c.execute(control_definition.update().values(active=False))
    else:
        org = build_policies()['governance_policy'][0]['organization_id']
        c.execute(governance_policy.insert().values(organization_id=org, policy_key='EXTRA', name='Synthetic extra policy'))
    before = snapshot(c)
    with pytest.raises(ValueError, match='changed or non-seed'): seed_policies(c)
    assert snapshot(c) == before


def test_missing_registry_refused_and_partial_fixture_repaired(registry_connection):
    c = registry_connection
    with pytest.raises(ValueError, match='Northstar'): seed_policies(c)
    assert all(not rows for rows in snapshot(c).values())
    seed_registry(c, date(2026, 10, 12))
    c.execute(control_definition.insert(), build_policies()['control_definition'][:1])
    assert seed_policies(c)['control_definition'] == 3
    assert all(count == 0 for count in seed_policies(c).values())


def test_policy_seed_rolls_back_with_caller(registry_connection):
    c = registry_connection
    seed_registry(c, date(2026, 10, 12))
    with pytest.raises(RuntimeError), c.begin_nested():
        seed_policies(c)
        raise RuntimeError('Simulated failure')
    assert all(not rows for rows in snapshot(c).values())


def test_actual_policy_cli_twice_and_refusal(registry_engine):
    with registry_engine.connect().execution_options(isolation_level='AUTOCOMMIT') as admin:
        admin.execute(sa.text('CREATE DATABASE assurgrid_demo'))
    url = registry_engine.url.set(database='assurgrid_demo')
    engine = sa.create_engine(url)
    try:
        with engine.begin() as c:
            command.upgrade(migration_config(c), 'head')
            seed_registry(c, date(2026, 10, 12))
        env = {**os.environ, 'ASSURGRID_ENV':'development', 'DATABASE_URL':url.render_as_string(hide_password=False)}
        script = Path(__file__).resolve().parents[2]/'scripts/seed_policies.py'
        args = [sys.executable, str(script), '--apply', '--confirm-demo']
        first = subprocess.run(args, env=env, capture_output=True, text=True)
        assert first.returncode == 0, first.stdout + first.stderr
        assert 'Inserted: 4 control_definition, 2 governance_policy, 3 policy_version, 10 policy_control_rule' in first.stdout
        with engine.connect() as c: before = snapshot(c)
        second = subprocess.run(args, env=env, capture_output=True, text=True)
        assert second.returncode == 0 and 'Inserted: 0 control_definition' in second.stdout
        with engine.begin() as c:
            assert snapshot(c) == before
            c.execute(policy_control_rule.update().values(due_soon_days=15))
        refused = subprocess.run(args, env=env, capture_output=True, text=True)
        assert refused.returncode == 1 and 'no policy data was overwritten' in refused.stdout
        with engine.connect() as c:
            assert set(c.execute(sa.select(policy_control_rule.c.due_soon_days)).scalars()) == {15}
    finally:
        engine.dispose()
        with registry_engine.connect().execution_options(isolation_level='AUTOCOMMIT') as admin:
            admin.execute(sa.text('DROP DATABASE assurgrid_demo'))
