"""Additive application data. Created only by the explicit migration command."""
from sqlalchemy import MetaData, Table, Column, String, Integer, DateTime, Text, Numeric

meta = MetaData()
profiles = Table('soc_account_profiles', meta,
    Column('username', String(100), primary_key=True), Column('employee_id', String(20), unique=True, nullable=False))
payroll = Table('soc_monthly_salary', meta,
    Column('employee_id', String(20), primary_key=True), Column('month', String(7), primary_key=True),
    Column('base_salary', Numeric(15, 2), nullable=False))
bonus_policy = Table('soc_bonus_policy', meta,
    Column('severity', String(20), primary_key=True), Column('amount', Numeric(15, 2), nullable=False))
audit = Table('soc_activity_log', meta,
    Column('id', Integer, primary_key=True, autoincrement=True), Column('username', String(100), nullable=False),
    Column('action', String(100), nullable=False), Column('target', String(150), nullable=False),
    Column('detail', Text), Column('created_at', DateTime, nullable=False))


def log(conn, user, action, target, detail=''):
    from datetime import datetime
    conn.execute(audit.insert().values(username=user['username'], action=action, target=target,
                                      detail=detail, created_at=datetime.utcnow()))
