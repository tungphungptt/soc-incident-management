"""Insert missing October 2026 DEMO salaries for the seven linked accounts."""
from decimal import Decimal
from sqlalchemy import select, and_
from app.db import engine, get_table
from app.workspace_schema import profiles, payroll
from scripts.demo_safety import require_demo_engine
from scripts.seed_demo_accounts import DEMO_ACCOUNTS

MONTH = '2026-10'
# Explicit demonstration amounts, not inferred real employee pay.
DEMO_BASE_SALARIES = {
    'ADMIN': Decimal('12000000'), 'SOC_MANAGER': Decimal('25000000'),
    'SOC_L1': Decimal('12000000'), 'SOC_L2': Decimal('18000000'),
    'SOC_L3': Decimal('23000000'), 'INCIDENT_RESPONDER': Decimal('17000000'),
    'THREAT_HUNTER': Decimal('19000000'),
}


def seed_demo_salaries():
    require_demo_engine(engine)
    result = []
    with engine.begin() as conn:
        links = dict(conn.execute(select(profiles.c.username, profiles.c.employee_id)
                                  .where(profiles.c.username.in_(DEMO_ACCOUNTS))).all())
        employees = set(conn.execute(select(get_table('nhan_vien_soc').c.MaNV)).scalars())
        if set(links) != set(DEMO_ACCOUNTS) or len(set(links.values())) != 7 or not set(links.values()) <= employees:
            raise ValueError('Run seed_demo_accounts first: seven distinct valid employee links are required')
        for username, role in DEMO_ACCOUNTS.items():
            employee_id = links[username]
            key = and_(payroll.c.employee_id == employee_id, payroll.c.month == MONTH)
            amount = conn.execute(select(payroll.c.base_salary).where(key)).scalar_one_or_none()
            created = amount is None
            if created:
                amount = DEMO_BASE_SALARIES[role]
                conn.execute(payroll.insert().values(employee_id=employee_id, month=MONTH, base_salary=amount))
            result.append({'username': username, 'employee_id': employee_id,
                           'month': MONTH, 'base_salary': amount, 'created': created})
    return result


def main():
    try:
        rows = seed_demo_salaries()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print('DEMO salaries only; existing configured salaries are preserved.')
    print(f"{'username':<22} | {'employee_id':<15} | month   | base_salary")
    for row in rows:
        print(f"{row['username']:<22} | {row['employee_id']:<15} | {row['month']} | {row['base_salary']:.2f}")


if __name__ == '__main__':
    main()
