from datetime import date
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.schema import control_definition, policy_control_rule
from app.db.session import get_session
from app.demo.identity import ACCOUNTS, seed_accounts
from app.demo.policies import identity, seed_policies
from app.demo.registry import build_registry, seed_registry
from app.main import app
from .test_policy_schema import policy, version
from .test_registry_schema import insert_application, insert_organization

ORG, APPS = build_registry(date(2026, 10, 12))
PASSWORD = 'synthetic-api-test-password'


@pytest.fixture
def policy_client(client, registry_connection):
    seed_registry(registry_connection, date(2026, 10, 12))
    seed_accounts(registry_connection, {name:PASSWORD for name, _, _ in ACCOUNTS})
    seed_policies(registry_connection)
    settings = Settings(_env_file=None, database_url='postgresql+psycopg://localhost:1/test',
                        frontend_origin='http://localhost:5173', app_env='development', demo_registry_organization_id=ORG['id'])
    app.dependency_overrides[get_settings] = lambda: settings
    def test_session():
        with Session(bind=registry_connection, join_transaction_mode='create_savepoint') as session:
            yield session
    app.dependency_overrides[get_session] = test_session
    return client


def login(client, name):
    result = client.post('/api/v1/auth/login', headers={'Origin':'http://localhost:5173'},
                         json={'email':f'{name}@northstar.example.test', 'password':PASSWORD})
    assert result.status_code == 200


def resolve(client, app_id, day='2026-10-12'):
    return client.get(f'/api/v1/applications/{app_id}/policy', params={'as_of':day})


def test_anonymous_cannot_read_policies_or_resolve(policy_client):
    for path in ['/api/v1/policies', f'/api/v1/policies/{identity("policy/HIGH_GXP")}',
                 f'/api/v1/applications/{APPS[0]["id"]}/policy?as_of=2026-10-12']:
        assert policy_client.get(path).status_code == 401


@pytest.mark.parametrize('account', ['admin','quality'])
def test_admin_quality_history_and_pagination(policy_client, account):
    c = policy_client
    login(c, account)
    first = c.get('/api/v1/policies', params={'page_size':1})
    assert first.status_code == 200 and first.headers['cache-control'] == 'no-store'
    assert first.json()['has_more'] and first.json()['items'][0]['policy_key'] == 'HIGH_GXP'
    assert c.get('/api/v1/policies', params={'page_size':1,'page':2}).json()['items'][0]['policy_key'] == 'MEDIUM_GXP'
    assert c.get('/api/v1/policies', params={'page':100}).json()['items'] == []
    history = c.get(f'/api/v1/policies/{identity("policy/HIGH_GXP")}').json()
    assert [v['version_number'] for v in history['versions']] == [1,2]
    assert history['versions'][0]['effective_to'] == history['versions'][1]['effective_from'] == '2026-07-01'
    pcr = [next(r for r in v['rules'] if r['control_key']=='PCR') for v in history['versions']]
    assert [r['frequency_months'] for r in pcr] == [24,12]
    assert all('governance_health' not in v for v in history['versions'])


@pytest.mark.parametrize('account', ['owner','viewer'])
def test_assigned_users_resolve_but_cannot_read_admin_history(policy_client, account):
    c = policy_client
    login(c, account)
    assert c.get('/api/v1/policies').status_code == 403
    assert c.get(f'/api/v1/policies/{identity("policy/HIGH_GXP")}').status_code == 403
    assert resolve(c, APPS[0]['id']).status_code == 200
    assert resolve(c, APPS[3]['id']).status_code == 404


def test_resolution_boundaries_missing_and_medium_profile(policy_client):
    c = policy_client
    login(c, 'admin')
    for day, num, frequency in [('2026-06-30',1,24),('2026-07-01',2,12)]:
        response = resolve(c, APPS[0]['id'], day)
        assert response.status_code == 200 and response.headers['cache-control']=='no-store'
        body = response.json()
        assert body['configuration']=='Resolved' and body['timezone']=='Asia/Kolkata'
        assert body['candidates'][0]['version_number']==num
        assert next(r for r in body['rules'] if r['control_key']=='PCR')['frequency_months']==frequency
    for app_id, day in [(APPS[0]['id'],'2024-12-31'),(APPS[5]['id'],'2026-10-12')]:
        body = resolve(c, app_id, day).json()
        assert body['configuration']=='Missing Configuration' and body['rules']==[]
    medium = next(a for a in APPS if a['gxp_classification']=='GxP' and a['criticality']=='Medium')
    body = resolve(c, medium['id']).json()
    assert body['candidates'][0]['policy_key']=='MEDIUM_GXP' and len(body['rules'])==2


def test_foreign_org_and_missing_ids_do_not_leak(policy_client, registry_connection):
    c = policy_client
    other = insert_organization(registry_connection, slug='other-org')
    foreign_app = insert_application(registry_connection, other)
    foreign_policy = policy(registry_connection, other)
    version(registry_connection, other, foreign_policy, effective_to=None)
    login(c,'admin')
    assert len(c.get('/api/v1/policies').json()['items'])==2
    for pid in (foreign_policy, uuid4()):
        response = c.get(f'/api/v1/policies/{pid}')
        assert response.status_code==404 and response.json()=={'detail':'Policy not found.'}
    for aid in (foreign_app, uuid4()):
        assert resolve(c, aid).status_code==404
    assert len(resolve(c,APPS[0]['id']).json()['candidates'])==1


def test_conflicting_profiles_fail_closed(policy_client, registry_connection):
    login(policy_client,'admin')
    duplicate = policy(registry_connection, ORG['id'], policy_key='SECOND_HIGH')
    version(registry_connection, ORG['id'], duplicate, effective_to=None)
    body = resolve(policy_client,APPS[0]['id']).json()
    assert body['configuration']=='Conflicting Configuration' and len(body['candidates'])==2 and body['rules']==[]


@pytest.mark.parametrize('change', ['inactive','empty'])
def test_unusable_configuration_does_not_resolve(policy_client, registry_connection, change):
    login(policy_client,'admin')
    if change=='inactive': registry_connection.execute(control_definition.update().values(active=False))
    else: registry_connection.execute(policy_control_rule.delete())
    body = resolve(policy_client,APPS[0]['id']).json()
    assert body['configuration']=='Missing Configuration' and body['rules']==[]


@pytest.mark.parametrize('params', [{}, {'as_of':'invalid'}, {'as_of':'2026-02-30'},
    {'as_of':'2026-10-12','organization_id':str(uuid4())}])
def test_resolution_input_rejected(policy_client, params):
    login(policy_client,'admin')
    assert policy_client.get(f'/api/v1/applications/{APPS[0]["id"]}/policy',params=params).status_code==422


def test_reads_do_not_allow_writes_or_bad_filters(policy_client):
    login(policy_client,'admin')
    assert policy_client.get('/api/v1/policies',params={'page_size':101}).status_code==422
    assert policy_client.get('/api/v1/policies',params={'organization_id':str(ORG['id'])}).status_code==422
    assert policy_client.get('/api/v1/policies/not-a-uuid').status_code==422
    assert policy_client.post('/api/v1/policies',json={}).status_code==405
    assert policy_client.patch(f'/api/v1/policies/{identity("policy/HIGH_GXP")}',json={}).status_code==405
