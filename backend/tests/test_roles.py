import pytest
from fastapi.testclient import TestClient
from app import accounts
from app.main import app
from app.config import settings

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(accounts, 'ACCOUNT_DB', tmp_path / 'accounts.sqlite3')
    with TestClient(app) as client:
        yield client

def login(client, username, password):
    response = client.post('/api/v1/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return {'Authorization': 'Bearer ' + response.json()['access_token']}

def test_account_lifecycle_and_revocation(client):
    admin = login(client, settings.admin_username, settings.admin_password)
    assert client.get('/api/v1/auth/me', headers=admin).json()['role'] == 'ADMIN'
    assert client.post('/api/v1/accounts', headers=admin, json={'username':'analyst','password':'long-password','role':'SOC_L1'}).status_code == 201
    analyst = login(client, 'analyst', 'long-password')
    assert client.get('/api/v1/accounts', headers=analyst).status_code == 403
    assert client.post('/api/v1/accounts', headers=analyst, json={'username':'other','password':'long-password','role':'ADMIN'}).status_code == 403
    assert client.put('/api/v1/accounts/analyst', headers=admin, json={'role':'THREAT_HUNTER','active':True}).status_code == 200
    assert client.get('/api/v1/auth/me', headers=analyst).json()['role'] == 'THREAT_HUNTER'
    assert client.put('/api/v1/accounts/analyst', headers=admin, json={'role':'THREAT_HUNTER','active':False}).status_code == 200
    assert client.get('/api/v1/auth/me', headers=analyst).status_code == 401
    assert client.put('/api/v1/accounts/'+settings.admin_username, headers=admin, json={'role':'SOC_L1'}).status_code == 409

@pytest.mark.parametrize('role', list(accounts.ROLES))
def test_forbidden_actions_are_blocked_before_database_access(client, role):
    admin = login(client, settings.admin_username, settings.admin_password)
    client.post('/api/v1/accounts', headers=admin, json={'username':'subject','password':'long-password','role':role})
    headers = login(client, 'subject', 'long-password')
    for table in ['nhan_vien_soc', 'su_co', 'ioc', 'hanh_dong_xu_ly']:
        for action, method, suffix in [('read','GET',''),('create','POST',''),('update','PUT','/example'),('delete','DELETE','/example')]:
            if action not in accounts.permissions(role, table):
                kwargs = {'json': {}} if method in ('POST','PUT') else {}
                assert client.request(method, '/api/v1/tables/'+table+suffix, headers=headers, **kwargs).status_code == 403

def test_password_hashes_are_salted():
    first = accounts.password_hash('same-password')
    assert first != accounts.password_hash('same-password')
    assert accounts.verify_password('same-password', first)
    assert not accounts.verify_password('wrong-password', first)
