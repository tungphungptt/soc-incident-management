import pytest

from app import accounts
from app.config import settings
from scripts.seed_demo_accounts import DEMO_ACCOUNTS, seed_demo_accounts
from scripts import seed_demo_accounts as seeder
from sqlalchemy import create_engine, MetaData, Table, Column, String, select
from app.workspace_schema import meta, profiles


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(accounts, 'ACCOUNT_DB', tmp_path / 'accounts.sqlite3')
    accounts.initialize()
    engine = create_engine('sqlite://')
    m = MetaData()
    employees = Table('nhan_vien_soc', m, Column('MaNV', String, primary_key=True))
    assigned = Table('su_co_nhan_vien_soc', m, Column('MaNV', String), Column('VaiTro', String))
    m.create_all(engine); meta.create_all(engine)
    with engine.begin() as c:
        for i, role in enumerate(accounts.ROLES):
            c.execute(employees.insert().values(MaNV=str(i)))
            if role != 'ADMIN':c.execute(assigned.insert().values(MaNV=str(i), VaiTro=role))
    monkeypatch.setattr(seeder, 'engine', engine)
    monkeypatch.setattr(seeder, 'get_table', {'nhan_vien_soc':employees,'su_co_nhan_vien_soc':assigned}.__getitem__)
    yield engine, employees
    engine.dispose()


def test_seed_is_idempotent_and_preserves_admin(store):
    original_admin = accounts.find_account(settings.admin_username)
    first = seed_demo_accounts('Demo@12345')
    assert len(first) == len(accounts.ROLES) == 7
    assert len(set(DEMO_ACCOUNTS.values())) == 7
    assert accounts.find_account(settings.admin_username) == original_admin
    with accounts.connect() as conn:
        conn.execute("UPDATE accounts SET role='SOC_L1', active=0 WHERE username='soc_manager'")
    second = seed_demo_accounts('Another@12345')
    assert first == second
    with accounts.connect() as conn:
        assert conn.execute('SELECT COUNT(*) FROM accounts').fetchone()[0] == 8
    for username, role in DEMO_ACCOUNTS.items():
        account = accounts.find_account(username)
        assert account['role'] == role
        assert account['active'] == 1
        assert account['password_hash'] != 'Another@12345'
        assert accounts.verify_password('Another@12345', account['password_hash'])
        assert not accounts.verify_password('Demo@12345', account['password_hash'])
    assert accounts.find_account(settings.admin_username) == original_admin


def test_short_password_does_not_change_accounts(store):
    with pytest.raises(ValueError):
        seed_demo_accounts('short')
    assert accounts.find_account('admin_demo') is None


def test_seven_distinct_links_are_idempotent(store):
    engine, _ = store
    first = seed_demo_accounts('Demo@12345')
    second = seed_demo_accounts('Demo@12345')
    assert first == second
    with engine.connect() as c:
        rows = c.execute(select(profiles)).mappings().all()
    assert len(rows) == len({r['employee_id'] for r in rows}) == 7


def test_missing_employee_fails_before_seeding_accounts(store):
    engine, employees = store
    with engine.begin() as c:c.execute(employees.delete())
    with pytest.raises(ValueError, match='No unlinked employee'):
        seed_demo_accounts('Demo@12345')
    assert accounts.find_account('admin_demo') is None
