"""Local persistent accounts, separate from the existing business schema."""
import hashlib
import hmac
import secrets
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from .config import settings

ACCOUNT_DB = Path(os.environ.get('SOC_ACCOUNT_DB') or (Path(__file__).resolve().parents[1] / 'accounts.sqlite3'))
ROLES = {
    'ADMIN': ('Admin', 'Quản lý tài khoản, cấp vai trò và khóa quyền truy cập.'),
    'SOC_MANAGER': ('SOC Manager', 'Giám sát tổng quan, quản lý nhân sự, phân công và báo cáo sự cố.'),
    'SOC_L1': ('SOC Analyst L1', 'Sàng lọc cảnh báo và ghi nhận sự cố ban đầu.'),
    'SOC_L2': ('SOC Analyst L2', 'Điều tra sự cố, phân tích IOC và ghi nhận kết quả xử lý.'),
    'SOC_L3': ('SOC Analyst L3', 'Điều tra chuyên sâu, phân tích kỹ thuật MITRE và hướng dẫn xử lý.'),
    'INCIDENT_RESPONDER': ('Incident Responder', 'Theo dõi sự cố và ghi nhận hành động cô lập, khắc phục, phục hồi.'),
    'THREAT_HUNTER': ('Threat Hunter', 'Phân tích IOC, kỹ thuật MITRE và liên kết dấu hiệu tấn công.'),
}
COMMON = {'su_co', 'canh_bao', 'tai_san', 'ioc', 'ky_thuat_mitre', 'canh_bao_tai_san', 'tai_san_incident', 'incident_ioc', 'su_co_ky_thuat_mitre', 'hanh_dong_xu_ly', 'lich_su_trang_thai'}
READS = {
    'SOC_L1': {'su_co', 'canh_bao', 'tai_san', 'ioc', 'canh_bao_tai_san', 'lich_su_trang_thai'},
    'SOC_L2': COMMON,
    'SOC_L3': COMMON,
    'INCIDENT_RESPONDER': {'su_co', 'canh_bao', 'tai_san', 'tai_san_incident', 'ioc', 'incident_ioc', 'hanh_dong_xu_ly', 'lich_su_trang_thai'},
    'THREAT_HUNTER': {'su_co', 'canh_bao', 'tai_san', 'ioc', 'ky_thuat_mitre', 'canh_bao_tai_san', 'tai_san_incident', 'incident_ioc', 'su_co_ky_thuat_mitre'},
}
WRITES = {
    'SOC_L1': {'su_co', 'canh_bao'},
    'SOC_L2': {'su_co', 'ioc', 'incident_ioc', 'hanh_dong_xu_ly'},
    'SOC_L3': {'su_co', 'ioc', 'ky_thuat_mitre', 'incident_ioc', 'su_co_ky_thuat_mitre', 'hanh_dong_xu_ly'},
    'INCIDENT_RESPONDER': {'su_co', 'hanh_dong_xu_ly'},
    'THREAT_HUNTER': {'ioc', 'ky_thuat_mitre', 'incident_ioc', 'su_co_ky_thuat_mitre'},
}

def permissions(role, table):
    if role == 'SOC_MANAGER':
        return ['read', 'create', 'update', 'delete']
    if role == 'ADMIN':
        return ['read', 'create', 'update', 'delete'] if table in {'to_chuc', 'tai_san', 'nhan_vien_soc'} else []
    if table not in READS.get(role, set()):
        return []
    actions = ['read']
    if table in WRITES.get(role, set()):
        actions += ['create', 'update']
    return actions

def password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return salt + ':' + digest

def verify_password(password, stored):
    salt, expected = stored.split(':')
    actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return hmac.compare_digest(actual, expected)

@contextmanager
def connect():
    conn = sqlite3.connect(ACCOUNT_DB)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def initialize():
    with connect() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS accounts (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1)')
        conn.execute('CREATE TABLE IF NOT EXISTS account_events (id INTEGER PRIMARY KEY, username TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL, detail TEXT, created_at TEXT NOT NULL)')
        if not conn.execute('SELECT 1 FROM accounts LIMIT 1').fetchone():
            conn.execute('INSERT INTO accounts VALUES (?, ?, ?, 1)', (settings.admin_username, password_hash(settings.admin_password), 'ADMIN'))

def account_event(conn, username, action, target, detail=''):
    conn.execute('INSERT INTO account_events (username, action, target, detail, created_at) VALUES (?, ?, ?, ?, ?)',
                 (username, action, target, detail, datetime.utcnow().isoformat()))

def find_account(username):
    with connect() as conn:
        row = conn.execute('SELECT * FROM accounts WHERE username=?', (username,)).fetchone()
    return dict(row) if row else None

def public_account(account):
    return {k: account[k] for k in ('username', 'role', 'active')}
