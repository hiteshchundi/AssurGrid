"""Scheduled-obligation relational boundaries in real PostgreSQL."""
from datetime import date
from uuid import uuid4

from alembic import command
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app.db.schema import governance_obligation as obligation, membership, policy_control_rule, user_account
from app.demo.identity import ACCOUNTS, seed_accounts
from app.demo.policies import identity, seed_policies
from app.demo.registry import build_registry, seed_registry
from .conftest import migration_config
from .test_identity_schema import account
from .test_registry_schema import insert_application, insert_organization

ORG, APPS = build_registry(date(2026,10,12))


@pytest.fixture
def obligations(registry_connection):
    c = registry_connection
    seed_registry(c,date(2026,10,12))
    seed_policies(c)
    return c


def insert(c, **overrides):
    values = dict(organization_id=ORG['id'], application_id=APPS[0]['id'],
        policy_control_rule_id=identity('rule/HIGH_GXP/2/PCR'), policy_version_id=identity('version/HIGH_GXP/2'),
        control_definition_id=identity('control/PCR'), window_start=date(2026,7,1), due_date=date(2027,7,1),
        frequency_months=12, due_soon_days=30, mandatory=True, evidence_requirement='Synthetic review reference',
        generation_key='a'*64)
    values.update(overrides)
    return c.execute(obligation.insert().values(**values).returning(obligation.c.id)).scalar_one()


def test_dates_rule_snapshots_and_optional_owner(obligations):
    c = obligations
    oid=insert(c)
    row=c.execute(sa.select(obligation).where(obligation.c.id==oid)).mappings().one()
    assert row['policy_version_id']==identity('version/HIGH_GXP/2')
    assert row['due_date']==date(2027,7,1) and row['assigned_owner_id'] is None
    assert row['superseded_by_id'] is None
    assert 'status' not in row and 'governance_health' not in row and 'overdue' not in row
    # Existing obligations retain their snapshots when source configuration is edited by privileged SQL.
    c.execute(policy_control_rule.update().where(policy_control_rule.c.id==row['policy_control_rule_id']).values(frequency_months=6))
    assert c.execute(sa.select(obligation.c.frequency_months)).scalar_one()==12


@pytest.mark.parametrize('field,value', [('due_date',date(2026,6,30)),('frequency_months',0),
    ('due_soon_days',-1),('mandatory',None),('generation_key','raw-key'),('generation_key','A'*64),
    ('evidence_requirement','  '),('policy_version_id',identity('version/HIGH_GXP/1')),
    ('control_definition_id',identity('control/ATR')),('organization_id',uuid4()),('application_id',uuid4())])
def test_invalid_obligation_rejected(obligations, field, value):
    with pytest.raises(IntegrityError):insert(obligations,**{field:value})


def test_generation_and_rule_window_uniqueness(obligations):
    c=obligations
    insert(c)
    with pytest.raises(IntegrityError),c.begin_nested():insert(c,generation_key='b'*64)
    with pytest.raises(IntegrityError),c.begin_nested():insert(c,window_start=date(2026,8,1))
    assert insert(c,generation_key='b'*64,window_start=date(2026,8,1))


def test_foreign_application_and_owner_rejected(obligations):
    c=obligations
    other=insert_organization(c,slug='other-org')
    foreign_app=insert_application(c,other)
    uid=account(c)
    c.execute(membership.insert().values(organization_id=other,user_id=uid,role='Application Owner'))
    with pytest.raises(IntegrityError),c.begin_nested():insert(c,application_id=foreign_app)
    with pytest.raises(IntegrityError),c.begin_nested():insert(c,assigned_owner_id=uid)
    with pytest.raises(IntegrityError),c.begin_nested():insert(c,assigned_owner_id=uuid4())
    c.execute(membership.insert().values(organization_id=ORG['id'],user_id=uid,role='Application Owner'))
    assert insert(c,assigned_owner_id=uid)
    with pytest.raises(IntegrityError),c.begin_nested():
        c.execute(membership.delete().where(membership.c.organization_id==ORG['id'],membership.c.user_id==uid))


def test_rule_references_and_supersession_restrict_deletion(obligations):
    c=obligations
    old=insert(c)
    replacement=insert(c,generation_key='b'*64,window_start=date(2027,7,1),due_date=date(2028,7,1))
    c.execute(obligation.update().where(obligation.c.id==old).values(superseded_by_id=replacement,supersession_reason='Synthetic justified replacement'))
    assert c.execute(sa.select(obligation.c.superseded_by_id).where(obligation.c.id==old)).scalar_one()==replacement
    with pytest.raises(IntegrityError),c.begin_nested():c.execute(obligation.delete().where(obligation.c.id==replacement))
    with pytest.raises(IntegrityError),c.begin_nested():c.execute(policy_control_rule.delete().where(policy_control_rule.c.id==identity('rule/HIGH_GXP/2/PCR')))


@pytest.mark.parametrize('kind',['self','different_app','different_control','missing_reason','reason_without_target'])
def test_invalid_supersession_rejected(obligations,kind):
    c=obligations
    old=insert(c)
    values=dict(superseded_by_id=old,supersession_reason='Synthetic replacement')
    if kind=='different_app':
        values['superseded_by_id']=insert(c,application_id=APPS[1]['id'],generation_key='b'*64)
    elif kind=='different_control':
        values['superseded_by_id']=insert(c,policy_control_rule_id=identity('rule/HIGH_GXP/2/ATR'),control_definition_id=identity('control/ATR'),generation_key='b'*64)
    elif kind=='missing_reason':
        values['superseded_by_id']=insert(c,window_start=date(2026,8,1),generation_key='b'*64)
        values['supersession_reason']=None
    elif kind=='reason_without_target':values['superseded_by_id']=None
    with pytest.raises(IntegrityError):c.execute(obligation.update().where(obligation.c.id==old).values(**values))


def test_migration_preserves_existing_policy_registry_accounts(registry_connection):
    c=registry_connection
    config=migration_config(c)
    command.downgrade(config,'0004_policy_schema')
    seed_registry(c,date(2026,10,12))
    seed_policies(c)
    seed_accounts(c,{name:'synthetic-test-password' for name,_,_ in ACCOUNTS})
    from app.db.schema import regulated_application
    tables=[regulated_application,user_account,policy_control_rule]
    before={t.name:c.execute(sa.select(t).order_by(t.c.id)).all() for t in tables}
    command.upgrade(config,'head')
    command.upgrade(config,'head')
    assert c.execute(sa.select(sa.func.count()).select_from(obligation)).scalar_one()==0
    insert(c)
    command.downgrade(config,'0004_policy_schema')
    assert {t.name:c.execute(sa.select(t).order_by(t.c.id)).all() for t in tables}==before
    command.upgrade(config,'head')
