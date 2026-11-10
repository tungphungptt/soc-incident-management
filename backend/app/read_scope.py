"""Row-level read scope shared by workspace, CRUD and report endpoints."""
from fastapi import HTTPException
from sqlalchemy import select, exists, and_, or_, true, false
from .workspace_schema import profiles

RESTRICTED_ROLES = {'SOC_L2', 'INCIDENT_RESPONDER'}


def restricted(user):
    return user['role'] in RESTRICTED_ROLES


def assigned_ids(conn, user, resolve):
    employee = conn.execute(select(profiles.c.employee_id).where(
        profiles.c.username == user['username'])).scalar()
    if not employee:
        raise HTTPException(403, 'Tài khoản chưa có nhân viên được phân công sự cố.')
    assignments = resolve('su_co_nhan_vien_soc')
    return select(assignments.c.MaIncident).where(assignments.c.MaNV == employee)


def predicate(conn, user, table, resolve):
    if not restricted(user):
        return true()
    ids = assigned_ids(conn, user, resolve)
    if 'MaIncident' in table.c:
        return table.c.MaIncident.in_(ids)
    if table.name == 'tai_san':
        links = resolve('tai_san_incident')
        alerts = resolve('canh_bao')
        alert_assets = resolve('canh_bao_tai_san')
        return or_(exists(select(1).where(links.c.MaTS == table.c.MaTS, links.c.MaIncident.in_(ids))),
                   exists(select(1).select_from(alert_assets.join(alerts, alerts.c.MaCanhBao == alert_assets.c.MaCanhBao))
                          .where(alert_assets.c.MaTS == table.c.MaTS, alerts.c.MaIncident.in_(ids))))
    if table.name == 'canh_bao_tai_san':
        alerts = resolve('canh_bao')
        return exists(select(1).where(alerts.c.MaCanhBao == table.c.MaCanhBao, alerts.c.MaIncident.in_(ids)))
    if table.name == 'ioc':
        links = resolve('incident_ioc')
        return exists(select(1).where(links.c.MaIncident.in_(ids), links.c.LoaiIOC == table.c.LoaiIOC,
                                      links.c.GiaTriIOC == table.c.GiaTriIOC))
    if table.name == 'ky_thuat_mitre':
        links = resolve('su_co_ky_thuat_mitre')
        return exists(select(1).where(links.c.MaIncident.in_(ids), links.c.MaKyThuat == table.c.MaKyThuat))
    if table.name == 'nhan_vien_soc':
        links = resolve('su_co_nhan_vien_soc')
        return exists(select(1).where(links.c.MaIncident.in_(ids), links.c.MaNV == table.c.MaNV))
    return false()


def require_incident(conn, user, key, resolve):
    if not restricted(user):
        return
    table = resolve('su_co')
    if not conn.execute(select(table.c.MaIncident).where(
            table.c.MaIncident == key, predicate(conn, user, table, resolve))).first():
        raise HTTPException(403, 'Bạn chưa được phân công vào sự cố này.')
