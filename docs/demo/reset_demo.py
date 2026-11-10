"""Build an isolated MySQL demo from scratch; never target the project DB.

Run with backend/.venv/Scripts/python.exe docs/demo/reset_demo.py --help.
Connection credentials come from DATABASE_URL or backend/.env, never guesses.
"""
import argparse
import getpass
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'backend'))
from scripts.demo_safety import validate_demo_database_name
from scripts.sql_runner import statements

STAGES = ('schema', 'seed', 'migrate_workspaces', 'migrate_business_rules',
          'seed_demo_accounts', 'seed_demo_salaries')


def read_sql(path, target):
    result = []
    for sql in statements(path):
        if re.match(r'^USE\s+', sql, re.I):
            sql = 'USE `'+target+'`'
        if re.search(r'\bsoc_incident_management\s*\.', sql, re.I):
            raise ValueError('SQL file contains a project database reference: '+str(path))
        result.append(sql)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default='soc_schema_test', help='Name must contain test or demo')
    parser.add_argument('--reset-existing', action='store_true', help='Explicitly replace ONLY the named demo database and its dedicated SQLite accounts')
    parser.add_argument('--dry-run', action='store_true', help='Validate target and SQL files without connecting or changing anything')
    args = parser.parse_args(argv)
    # Validate before loading credentials, prompting, connecting or doing DDL.
    try:
        target = validate_demo_database_name(args.database)
        schema = read_sql(ROOT/'docs/sql/02_schema_proposed.sql', target)
        seed = read_sql(ROOT/'docs/sql/03_seed_proposed.sql', target)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    accounts_root = (ROOT/'backend/migration_backups/demo_accounts').resolve()
    account_file = (accounts_root/target/'accounts.sqlite3').resolve()
    if not account_file.is_relative_to(accounts_root) or account_file == (ROOT/'backend/accounts.sqlite3').resolve():
        parser.error('Refusing unsafe SQLite account path')
    print('Target:', target, flush=True)
    print('Order:', ' -> '.join(STAGES), flush=True)
    print('Dedicated SOC_ACCOUNT_DB:', account_file, flush=True)
    if args.dry_run:
        print('Dry run: no connection, no files written, no database changes.')
        return 0

    from dotenv import dotenv_values
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    raw_url = os.environ.get('DATABASE_URL') or dotenv_values(ROOT/'backend/.env').get('DATABASE_URL')
    if not raw_url:
        parser.error('Set DATABASE_URL or configure backend/.env; no connection credentials were found')
    try:
        url = make_url(raw_url).set(database=target)
        if url.get_backend_name() != 'mysql':
            parser.error('A MySQL DATABASE_URL is required')
    except Exception as exc:
        parser.error('Invalid MySQL connection URL ('+type(exc).__name__+')')
    password = os.environ.get('DEMO_ACCOUNT_PASSWORD')
    if password is None:
        password = getpass.getpass('Demo account password (at least 10 characters): ')
    if len(password) < 10:
        parser.error('Demo account password must have at least 10 characters; nothing was reset')

    env = dict(os.environ, DATABASE_URL=url.render_as_string(hide_password=False),
               SOC_ACCOUNT_DB=str(account_file), DEMO_ACCOUNT_PASSWORD=password,
               ADMIN_USERNAME='demo_bootstrap_admin', ADMIN_PASSWORD=secrets.token_urlsafe(32),
               PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    # No default/project database on the administrative connection.
    admin = create_engine(url._replace(database=None), isolation_level='AUTOCOMMIT',
                          connect_args={'connect_timeout': 8})
    try:
        with admin.connect() as conn:
            lock = 'soc_demo_reset_'+target
            if conn.execute(text('SELECT GET_LOCK(:name,0)'), {'name': lock}).scalar() != 1:
                raise RuntimeError('Another reset is running for '+target)
            try:
                exists = conn.execute(text('SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=:db'), {'db': target}).scalar()
                if (exists or account_file.exists()) and not args.reset_existing:
                    raise ValueError('Demo database/accounts already exist; pass --reset-existing to replace only '+target)
                # The name has already passed the strict identifier allowlist.
                if exists:
                    conn.exec_driver_sql('DROP DATABASE `'+target+'`')
                conn.exec_driver_sql('CREATE DATABASE `'+target+'` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
                account_file.parent.mkdir(parents=True, exist_ok=True)
                # Delete only this script-managed SQLite file/sidecars, not folders.
                for suffix in ('', '-wal', '-shm', '-journal'):
                    path = Path(str(account_file)+suffix)
                    if path.exists():
                        if path.resolve().parent != account_file.parent:
                            raise ValueError('Refusing SQLite path outside dedicated demo folder')
                        path.unlink()
                demo = create_engine(url, connect_args={'connect_timeout': 8})
                try:
                    for title, sqls in [('schema', schema), ('seed', seed)]:
                        print('Running:', title, flush=True)
                        with demo.begin() as db:
                            assert db.exec_driver_sql('SELECT DATABASE()').scalar() == target
                            for sql in sqls:
                                if sql.upper() in ('START TRANSACTION', 'COMMIT'):
                                    continue
                                db.execute(text(sql))
                    for module in ('migrate_workspaces', 'migrate_business_rules', 'seed_demo_accounts', 'seed_demo_salaries'):
                        print('Running:', module, flush=True)
                        subprocess.run([sys.executable, '-B', '-m', 'scripts.'+module],
                                       cwd=ROOT/'backend', env=env, check=True)
                    with demo.connect() as db:
                        counts = {name: db.exec_driver_sql('SELECT COUNT(*) FROM `'+name+'`').scalar()
                                  for name in ('su_co', 'soc_account_profiles', 'soc_monthly_salary')}
                    print('Ready:', target, counts, flush=True)
                    print('Start backend with DATABASE_URL pointing to '+target+' and SOC_ACCOUNT_DB='+str(account_file), flush=True)
                finally:
                    demo.dispose()
            finally:
                conn.execute(text('SELECT RELEASE_LOCK(:name)'), {'name': lock})
    finally:
        admin.dispose()
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        raise SystemExit('Reset failed: '+str(exc)) from exc
