"""Seed one demo account per existing role without modifying the real admin."""
import getpass
import os
import argparse

from app.accounts import ROLES, connect, initialize, password_hash
from app.config import settings

DEMO_ACCOUNTS = {
    'admin_demo': 'ADMIN',
    'soc_manager': 'SOC_MANAGER',
    'analyst_l1': 'SOC_L1',
    'analyst_l2': 'SOC_L2',
    'analyst_l3': 'SOC_L3',
    'incident_responder': 'INCIDENT_RESPONDER',
    'threat_hunter': 'THREAT_HUNTER',
}


def seed_demo_accounts(password: str):
    if len(password) < 10:
        raise ValueError('Demo password must have at least 10 characters')
    if len(DEMO_ACCOUNTS) != len(ROLES) or set(DEMO_ACCOUNTS.values()) != set(ROLES):
        raise ValueError('Demo accounts must cover every existing role exactly once')
    if {'admin', settings.admin_username} & DEMO_ACCOUNTS.keys():
        raise ValueError('A demo username conflicts with the protected admin account')
    initialize()
    # All seven changes commit together. Only these exact usernames are updated.
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
    print(f"{'username':<22} | {'role':<20} | status")
    print('-' * 57)
    for row in rows:
        print(f"{row['username']:<22} | {row['role']:<20} | {'active' if row['active'] else 'inactive'}")
    if args.with_data:
        from scripts.seed_demo_data import seed_business_data
        seed_business_data()


if __name__ == '__main__':
    main()
