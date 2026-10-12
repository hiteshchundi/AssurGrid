from datetime import date

import pytest
import sqlalchemy as sa

from app.db.schema import application_access, membership, user_account
from app.demo.identity import ACCOUNTS, seed_accounts
from app.demo.registry import seed_registry
from app.modules.auth.security import verify_password

PASSWORDS = {name: 'synthetic-test-only-password' for name, _, _ in ACCOUNTS}


def test_accounts_repeat_preserves_hashes_and_scopes(registry_connection):
    c = registry_connection
    seed_registry(c, date(2026, 10, 12))
    assert seed_accounts(c, PASSWORDS) == 4
    before = c.execute(sa.select(user_account).order_by(user_account.c.id)).all()
    assert seed_accounts(c, PASSWORDS) == 0
    assert before == c.execute(sa.select(user_account).order_by(user_account.c.id)).all()
    assert all(verify_password(PASSWORDS['admin'], row.password_hash) for row in before)
    assert set(c.execute(sa.select(membership.c.role)).scalars()) == {'Admin', 'Quality', 'Application Owner', 'Viewer'}
    assert c.execute(sa.select(sa.func.count()).select_from(application_access)).scalar_one() == 4


@pytest.mark.parametrize('change', ['password', 'role', 'active'])
def test_account_seed_refuses_edits(registry_connection, change):
    c = registry_connection
    seed_registry(c, date(2026, 10, 12))
    seed_accounts(c, PASSWORDS)
    passwords = dict(PASSWORDS)
    if change == 'password': passwords['admin'] = 'different-test-password'
    elif change == 'role': c.execute(membership.update().values(role='Viewer'))
    else: c.execute(user_account.update().values(active=False))
    with pytest.raises(ValueError), c.begin_nested(): seed_accounts(c, passwords)


def test_account_seed_requires_registry_and_passwords(registry_connection):
    with pytest.raises(ValueError): seed_accounts(registry_connection, PASSWORDS)
    with pytest.raises(ValueError): seed_accounts(registry_connection, {})
