from decimal import Decimal
import pytest
from sqlalchemy import create_engine, MetaData, Table, Column, String, select
from app.workspace_schema import meta, profiles, payroll
from scripts import seed_demo_salaries as seeder
from scripts.seed_demo_accounts import DEMO_ACCOUNTS


@pytest.fixture
def salary_store(monkeypatch):
    engine = create_engine('sqlite://')
    m = MetaData()
    employees = Table('nhan_vien_soc', m, Column('MaNV', String, primary_key=True))
    m.create_all(engine); meta.create_all(engine)
    with engine.begin() as c:
        for i, username in enumerate(DEMO_ACCOUNTS):
            eid = str(i)
            c.execute(employees.insert().values(MaNV=eid))
            c.execute(profiles.insert().values(username=username, employee_id=eid))
    monkeypatch.setattr(seeder, 'engine', engine)
    monkeypatch.setattr(seeder, 'get_table', lambda _: employees)
    yield engine
    engine.dispose()


def test_salaries_cover_all_demo_employees_and_preserve_customizations(salary_store):
    engine = salary_store
    first = seeder.seed_demo_salaries()
    assert len(first) == 7 and all(row['created'] for row in first)
    with engine.begin() as c:
        c.execute(payroll.update().where(payroll.c.employee_id == '0').values(base_salary=Decimal('123.45')))
    second = seeder.seed_demo_salaries()
    assert len(second) == 7 and not any(row['created'] for row in second)
    with engine.connect() as c:
        rows = c.execute(select(payroll)).mappings().all()
    assert len(rows) == 7 and {r['month'] for r in rows} == {'2026-10'}
    assert next(r for r in rows if r['employee_id']=='0')['base_salary'] == Decimal('123.45')


def test_missing_profile_does_not_partially_seed_payroll(salary_store):
    with salary_store.begin() as c:c.execute(profiles.delete().where(profiles.c.username=='analyst_l1'))
    with pytest.raises(ValueError, match='seven distinct'):
        seeder.seed_demo_salaries()
    with salary_store.connect() as c:assert c.execute(select(payroll)).first() is None
