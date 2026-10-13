from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError

from app.db.session import get_session
from app.main import app
from app.modules.auth.router import Principal, get_principal


@pytest.mark.parametrize('path', ['/api/v1/policies', f'/api/v1/policies/{uuid4()}',
    f'/api/v1/applications/{uuid4()}/policy?as_of=2026-10-12'])
def test_safe_database_failure(client, path, caplog):
    session=MagicMock()
    session.execute.side_effect=OperationalError('private SQL',{},Exception('private credentials'))
    app.dependency_overrides[get_principal]=lambda:Principal(uuid4(),uuid4(),'Admin',uuid4(),'a'*64)
    app.dependency_overrides[get_session]=lambda:session
    response=client.get(path)
    assert response.status_code==503
    assert response.json()=={'detail':'Policy configuration is temporarily unavailable.'}
    assert 'private' not in response.text+caplog.text
