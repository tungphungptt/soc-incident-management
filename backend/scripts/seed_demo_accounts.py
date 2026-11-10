"""Seed one demo account per existing role without modifying the real admin."""
import getpass
import os
import argparse

from app.accounts import ROLES, connect, initialize, password_hash
from app.config import settings
from app.db import engine, get_table
from app.workspace_schema import profiles
from sqlalchemy import select, func
from scripts.demo_safety import require_demo_engine

DEMO_ACCOUNTS = {
    'admin_demo': 'ADMIN',
    'soc_manager': 'SOC_MANAGER',
    'analyst_l1': 'SOC_L1',
    'analyst_l2': 'SOC_L2',
    'analyst_l3': 'SOC_L3',
    'incident_responder': 'INCIDENT_RESPONDER',
    'threat_hunter': 'THREAT_HUNTER',
}

ROLE_ALIASES = {
    'SOC Manager': 'SOC_MANAGER', 'SOC Analyst L1': 'SOC_L1',
    'SOC Analyst L2': 'SOC_L2', 'SOC Analyst L3': 'SOC_L3',
    'Incident Responder': 'INCIDENT_RESPONDER', 'Threat Hunter': 'THREAT_HUNTER',
}


def plan_profiles(conn):
    """Keep valid links; infer new business links from actual assignment roles."""
    employees = set(conn.execute(select(get_table('nhan_vien_soc').c.MaNV)).scalars())
    existing = dict(conn.execute(select(profiles.c.username, profiles.c.employee_id)).all())
    used = {eid for name, eid in existing.items() if name not in DEMO_ACCOUNTS}
    assigned = get_table('su_co_nhan_vien_soc')
    evidence = {}
    for eid, role, count in conn.execute(select(assigned.c.MaNV, assigned.c.VaiTro, func.count())
                                          .group_by(assigned.c.MaNV, assigned.c.VaiTro)):
        role = ROLE_ALIASES.get(role, role)
        evidence.setdefault(role, {})[eid] = evidence.get(role, {}).get(eid, 0) + count
    result = {}
    # Reserve every valid existing demo link before assigning any new employee.
    for name in DEMO_ACCOUNTS:
        if name in existing:
            if existing[name] not in employees or existing[name] in used:
                raise ValueError('Invalid or conflicting existing employee link: '+name)
            result[name] = existing[name]
            used.add(existing[name])
    for name, role in DEMO_ACCOUNTS.items():
        if name in result or role == 'ADMIN':
            continue
        candidates = evidence.get(role, {})
        available = sorted((eid for eid in candidates if eid in employees and eid not in used),
                           key=lambda eid: (-candidates[eid], eid))
        if not available:
            raise ValueError('No unlinked employee with assignment evidence for '+role)
        result[name] = available[0]
        used.add(available[0])
    if 'admin_demo' not in result:
        # There is no ADMIN role in the business employee schema. Use a separate
        # unlinked employee; do not invent a business assignment for the admin.
        available = sorted(employees-used)
        if not available:
            raise ValueError('Need a separate employee for admin_demo (at least 7 employees)')
        result['admin_demo'] = available[0]
    return result


def seed_demo_accounts(password: str):
    if len(password) < 10:
        raise ValueError('Demo password must have at least 10 characters')
    if len(DEMO_ACCOUNTS) != len(ROLES) or set(DEMO_ACCOUNTS.values()) != set(ROLES):
        raise ValueError('Demo accounts must cover every existing role exactly once')
    if {'admin', settings.admin_username} & DEMO_ACCOUNTS.keys():
        raise ValueError('A demo username conflicts with the protected admin account')
    require_demo_engine(engine)
    # Preflight MySQL before changing SQLite. The two stores have independent
    # transactions; retries preserve profile links and finish an interrupted run.
    with engine.begin() as business:
        links = plan_profiles(business)
        initialize()
        with connect() as conn:
            for username, role in DEMO_ACCOUNTS.items():
                conn.execute(
                    '''INSERT INTO accounts (username, password_hash, role, active)
                       VALUES (?, ?, ?, 1)
                       ON CONFLICT(username) DO UPDATE SET
                         password_hash=excluded.password_hash,
                         role=excluded.role,
                         active=1''',
                    (username, password_hash(password), role),
                )
            rows = [dict(conn.execute(
                'SELECT username, role, active FROM accounts WHERE username=?',
                (username,),
            ).fetchone()) for username in DEMO_ACCOUNTS]
        existing = set(business.execute(select(profiles.c.username)).scalars())
        for username, eid in links.items():
            if username not in existing:
                business.execute(profiles.insert().values(username=username, employee_id=eid))
        for row in rows:
            row['employee_id'] = links[row['username']]
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-data', action='store_true', help='Migrate schema and insert linked demo business records')
    args = parser.parse_args()
    # Avoid command-line passwords (visible in process lists) and plaintext files.
    password = os.environ.get('DEMO_ACCOUNT_PASSWORD')
    if password is None:
        password = getpass.getpass('Shared demo password (at least 10 characters): ')
    try:
        rows = seed_demo_accounts(password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"{'username':<22} | {'role':<20} | {'employee_id':<15} | status")
    print('-' * 76)
    for row in rows:
        print(f"{row['username']:<22} | {row['role']:<20} | {row['employee_id']:<15} | {'active' if row['active'] else 'inactive'}")
    if args.with_data:
        from scripts.seed_demo_data import seed_business_data
        seed_business_data()


if __name__ == '__main__':
    main()
