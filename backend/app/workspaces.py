from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.exc import IntegrityError

from .db import engine, get_table, TABLES
from .security import current_user
from .accounts import find_account, ROLES, permissions, connect as account_connection
from .config import settings
from .workspace_schema import profiles, payroll, bonus_policy, audit, log
from .read_scope import predicate as read_predicate, require_incident, restricted

router = APIRouter(prefix=settings.api_prefix)
SLA = {'CRITICAL': 60, 'HIGH': 240, 'MEDIUM': 720, 'LOW': 1440}
NEXT = {'NEW': 'INVESTIGATING', 'INVESTIGATING': 'CONTAINED', 'CONTAINED': 'REMEDIATING', 'REMEDIATING': 'CLOSED'}
TRANSITIONS = {'SOC_L1': {'NEW'}, 'SOC_L2': {'INVESTIGATING'}, 'SOC_L3': {'INVESTIGATING'},
               'INCIDENT_RESPONDER': {'CONTAINED', 'REMEDIATING'}, 'SOC_MANAGER': set(NEXT)}
ACTIONS = ['Block IP', 'Disable Account', 'Isolate Host', 'Kill Process', 'Reset Password', 'Collect Evidence', 'Scan Malware']
STAFF = set(ROLES) - {'ADMIN'}


def allow(user, roles=STAFF):
    if user['role'] not in roles:
        raise HTTPException(403, 'Bạn không có quyền thực hiện thao tác này.')


def rows(conn, name, user=None):
    table = get_table(name)
    query = select(table)
    if user is not None:
        query = query.where(read_predicate(conn, user, table, get_table))
    return [dict(r) for r in conn.execute(query).mappings()]


def employee(conn, user, required=True):
    value = conn.execute(select(profiles.c.employee_id).where(profiles.c.username == user['username'])).scalar()
    if not value and required:
        raise HTTPException(409, 'Tài khoản chưa liên kết hồ sơ nhân viên. Liên hệ Admin để gắn mã nhân viên.')
    return value


def assignments(conn, incident_id):
    t = get_table('su_co_nhan_vien_soc')
    return [dict(r) for r in conn.execute(select(t).where(t.c.MaIncident == incident_id)).mappings()]


def incident(conn, key, lock=False):
    t = get_table('su_co')
    query = select(t).where(t.c.MaIncident == key)
    if lock:
        query = query.with_for_update()
    row = conn.execute(query).mappings().first()
    if row is None:
        raise HTTPException(404, 'Không tìm thấy sự cố.')
    return dict(row)


def check_assigned(conn, user, key):
    if user['role'] in {'SOC_L2', 'INCIDENT_RESPONDER'}:
        own = employee(conn, user)
        if not any(a['MaNV'] == own for a in assignments(conn, key)):
            raise HTTPException(403, 'Bạn chưa được phân công vào sự cố này.')


def check_critical(conn, row):
    if row['MucDoNghiemTrong'] == 'CRITICAL' and not any(a['VaiTro'] in {'SOC_L2', 'SOC_L3'} for a in assignments(conn, row['MaIncident'])):
        raise HTTPException(409, 'Sự cố Critical phải có ít nhất một nhân viên L2 hoặc L3 tham gia.')


def sla(row, now=None):
    now = now or datetime.utcnow()
    due = row['ThoiGianPhatHien'] + timedelta(minutes=SLA.get(row['MucDoNghiemTrong'], 1440))
    stop = row.get('ThoiGianDong') if row['TrangThai'] == 'CLOSED' else now
    remaining = int((due - (stop or now)).total_seconds())
    return {'deadline': due.isoformat() + 'Z', 'remaining_seconds': remaining,
            'violated': remaining < 0, 'closed': row['TrangThai'] == 'CLOSED'}


def enrich(conn, row):
    aa = assignments(conn, row['MaIncident'])
    return {**row, 'sla': sla(row), 'assignees': aa, 'unassigned': not aa,
            'needs_expert': row['MucDoNghiemTrong'] == 'CRITICAL' and not any(a['VaiTro'] in {'SOC_L2','SOC_L3'} for a in aa)}


def unique_time(conn, table, column):
    now = datetime.utcnow()
    last = conn.execute(select(func.max(table.c[column]))).scalar()
    return max(now, last + timedelta(microseconds=1)) if last else now


def write_assignment(conn, key, employee_id, role, user):
    if role not in STAFF:
        raise HTTPException(422, 'Vai trò trong Incident không hợp lệ.')
    profile = conn.execute(select(profiles.c.username).where(profiles.c.employee_id == employee_id)).scalar()
    account = find_account(profile) if profile else None
    if not account or not account['active'] or account['role'] != role:
        raise HTTPException(409, 'Nhân viên cần tài khoản active có đúng vai trò được phân công.')
    t = get_table('su_co_nhan_vien_soc')
    condition = and_(t.c.MaIncident == key, t.c.MaNV == employee_id, t.c.VaiTro == role)
    if conn.execute(select(t).where(condition)).first():
        raise HTTPException(409, 'Nhân viên đã được phân công với vai trò này trong Incident.')
    conn.execute(t.insert().values(MaIncident=key, MaNV=employee_id, VaiTro=role, ViTri='Incident participant', ThoiDiemThamGia=datetime.utcnow()))
    log(conn, user, 'ASSIGN', key, f'{employee_id}: {role}')


@router.get('/workspace/staff')
def staff(user=Depends(current_user)):
    allow(user, set(ROLES))
    with engine.connect() as conn:
        employees = {r['MaNV']: r['HoTen'] for r in rows(conn, 'nhan_vien_soc')}
        result = []
        for r in conn.execute(select(profiles)).mappings():
            account = find_account(r['username'])
            if account and account['active']:
                result.append({'username': r['username'], 'employee_id': r['employee_id'], 'name': employees.get(r['employee_id']), 'role': account['role']})
        return result


class ProfileBody(BaseModel):
    employee_id: str


@router.put('/workspace/profiles/{username}')
def set_profile(username: str, body: ProfileBody, user=Depends(current_user)):
    allow(user, {'ADMIN'})
    if not find_account(username):
        raise HTTPException(404, 'Không tìm thấy tài khoản.')
    with engine.begin() as conn:
        nv = get_table('nhan_vien_soc')
        if not conn.execute(select(nv).where(nv.c.MaNV == body.employee_id)).first():
            raise HTTPException(404, 'Không tìm thấy nhân viên.')
        other = conn.execute(select(profiles).where(profiles.c.employee_id == body.employee_id, profiles.c.username != username)).first()
        if other:
            raise HTTPException(409, 'Hồ sơ này đã liên kết tài khoản khác.')
        conn.execute(profiles.delete().where(profiles.c.username == username))
        conn.execute(profiles.insert().values(username=username, employee_id=body.employee_id))
        log(conn, user, 'LINK_PROFILE', username, body.employee_id)
    return {'message': 'Đã liên kết nhân viên.'}


@router.get('/workspace/incidents')
def list_incidents(status: str | None = None, severity: str | None = None, mine: bool = False,
                   date_from: str | None = None, date_to: str | None = None, user=Depends(current_user)):
    allow(user)
    try:
        start = datetime.fromisoformat(date_from) if date_from else None
        end = datetime.fromisoformat(date_to) + timedelta(days=1) if date_to else None
    except ValueError:
        raise HTTPException(422, 'Ngày lọc không hợp lệ.')
    if start and end and start >= end:
        raise HTTPException(422, 'Ngày bắt đầu phải trước ngày kết thúc.')
    with engine.connect() as conn:
        own = employee(conn, user, required=mine and not restricted(user))
        result = []
        for row in rows(conn, 'su_co', user):
            if status and row['TrangThai'] != status or severity and row['MucDoNghiemTrong'] != severity:
                continue
            if start and row['ThoiGianPhatHien'] < start or end and row['ThoiGianPhatHien'] >= end:
                continue
            item = enrich(conn, row)
            if (mine or user['role'] in {'SOC_L2','INCIDENT_RESPONDER'}) and not any(a['MaNV'] == own for a in item['assignees']):
                continue
            result.append(item)
        return sorted(result, key=lambda r: (list(SLA).index(r['MucDoNghiemTrong']) if r['MucDoNghiemTrong'] in SLA else 4, r['ThoiGianPhatHien']))


@router.get('/workspace/incidents/{key}')
def detail(key: str, user=Depends(current_user)):
    allow(user)
    with engine.connect() as conn:
        require_incident(conn, user, key, get_table)
        row = incident(conn, key)
        own = employee(conn, user, required=False)
        can_work = user['role'] not in {'SOC_L2','INCIDENT_RESPONDER'} or any(a['MaNV']==own for a in assignments(conn,key))
        all_data = {n: rows(conn, n, user) for n in TABLES if n != 'su_co'}
        linked = lambda name: [r for r in all_data[name] if r.get('MaIncident') == key]
        asset_ids = {r['MaTS'] for r in linked('tai_san_incident')}
        iocs = {(r['LoaiIOC'],r['GiaTriIOC']) for r in linked('incident_ioc')}
        techniques = {r['MaKyThuat'] for r in linked('su_co_ky_thuat_mitre')}
        names = {r['MaNV']: r['HoTen'] for r in all_data['nhan_vien_soc']}
        timeline = [{'time':r['ThoiDiemThayDoi'], 'title':r['TrangThaiCu']+' → '+r['TrangThaiMoi'], 'employee':r.get('NguoiThucHien') or names.get(r['MaNV'],r['MaNV']) or 'SQL', 'kind':'status'} for r in linked('lich_su_trang_thai')]
        timeline += [{'time':r['ThoiGianThucHien'], 'title':r['HanhDong']+': '+r['KetQua'], 'employee':names.get(r['MaNV'],r['MaNV']), 'kind':'action','minutes':r.get('ThoiLuongPhut')} for r in linked('hanh_dong_xu_ly')]
        aa = [{**a, 'name':names.get(a['MaNV'])} for a in assignments(conn,key)]
        return {'incident':enrich(conn,row), 'alerts':linked('canh_bao'),
                'assets':[r for r in all_data['tai_san'] if r['MaTS'] in asset_ids],
                'iocs':[r for r in all_data['ioc'] if (r['LoaiIOC'],r['GiaTriIOC']) in iocs],
                'techniques':[r for r in all_data['ky_thuat_mitre'] if r['MaKyThuat'] in techniques] if 'read' in permissions(user['role'],'ky_thuat_mitre') else [],
                'participants':aa, 'actions':linked('hanh_dong_xu_ly'),
                'timeline':sorted(timeline,key=lambda r:r['time']),
                'same_ioc_incidents':sorted({r['MaIncident'] for r in all_data['incident_ioc'] if (r['LoaiIOC'],r['GiaTriIOC']) in iocs and r['MaIncident'] != key}),
                'can_work':can_work,
                'next_status':NEXT.get(row['TrangThai']) if can_work and row['TrangThai'] in TRANSITIONS.get(user['role'],set()) else None}


class NewIncident(BaseModel):
    description: str = Field(min_length=1, max_length=10000)
    severity: str
    alert_ids: list[str] = []
    expert_id: str | None = None


@router.post('/workspace/incidents', status_code=201)
def create_incident(body: NewIncident, user=Depends(current_user)):
    allow(user, {'SOC_MANAGER','SOC_L1','THREAT_HUNTER'})
    if body.severity not in SLA:
        raise HTTPException(422, 'Mức độ không hợp lệ.')
    with engine.begin() as conn:
        own = employee(conn,user)
        key='INC-'+uuid4().hex[:12]
        now=datetime.utcnow()
        row={'MaIncident':key,'ThoiGianBatDau':now,'ThoiGianPhatHien':now,'ThoiGianXuLy':None,'ThoiGianDong':None,
             'MucDoNghiemTrong':body.severity,'TrangThai':'NEW','MoTa':body.description,'DiemRuiRo':0}
        expert=None
        if body.severity=='CRITICAL':
            p=conn.execute(select(profiles).where(profiles.c.employee_id==body.expert_id)).mappings().first() if body.expert_id else None
            expert=find_account(p['username']) if p else None
            if not expert or not expert['active'] or expert['role'] not in {'SOC_L2','SOC_L3'}:
                raise HTTPException(409,'Sự cố Critical cần chọn chuyên gia L2/L3 hợp lệ.')
            if conn.dialect.name=='mysql':
                row.update(MaChuyenGia=body.expert_id,VaiTroChuyenGia=expert['role'])
        conn.execute(get_table('su_co').insert().values(**row))
        write_assignment(conn,key,own,user['role'],user)
        if body.expert_id and body.expert_id != own:
            p=conn.execute(select(profiles).where(profiles.c.employee_id==body.expert_id)).mappings().first()
            a=find_account(p['username']) if p else None
            if not a or a['role'] not in {'SOC_L2','SOC_L3'}:
                raise HTTPException(409,'Hãy chọn chuyên gia L2/L3 hợp lệ.')
            if not any(x['MaNV']==body.expert_id and x['VaiTro']==a['role'] for x in assignments(conn,key)):
                write_assignment(conn,key,body.expert_id,a['role'],user)
        check_critical(conn,row)
        cb=get_table('canh_bao'); old_keys=set()
        for alert_id in set(body.alert_ids):
            old=conn.execute(select(cb).where(cb.c.MaCanhBao==alert_id).with_for_update()).mappings().first()
            if not old:
                raise HTTPException(404,'Không tìm thấy cảnh báo đã chọn.')
            old_inc=incident(conn,old['MaIncident'],True)
            if old_inc['TrangThai'] != 'NEW':
                raise HTTPException(409,'Chỉ gom cảnh báo từ Incident NEW; giữ nguyên lịch sử sự cố đang xử lý.')
            old_keys.add(old['MaIncident'])
            conn.execute(cb.update().where(cb.c.MaCanhBao==alert_id).values(MaIncident=key))
        links=get_table('canh_bao_tai_san'); assets=set()
        if body.alert_ids:
            assets={r[0] for r in conn.execute(select(links.c.MaTS).where(links.c.MaCanhBao.in_(body.alert_ids)))}
        for aid in assets:
            conn.execute(get_table('tai_san_incident').insert().values(MaTS=aid,MaIncident=key))
        log(conn,user,'CREATE_INCIDENT',key,'Alerts: '+','.join(body.alert_ids))
    return {'id':key,'message':'Đã tạo sự cố.'}


class TransitionBody(BaseModel):
    status: str


class TriageBody(BaseModel):
    severity: str
    expert_id: str | None = None


@router.put('/workspace/incidents/{key}/triage')
def triage(key: str, body: TriageBody, user=Depends(current_user)):
    allow(user, {'SOC_MANAGER','SOC_L1'})
    if body.severity not in SLA: raise HTTPException(422,'Mức độ không hợp lệ.')
    with engine.begin() as conn:
        row=incident(conn,key,True)
        if row['TrangThai']!='NEW': raise HTTPException(409,'Chỉ phân loại mức độ cho Incident NEW.')
        if body.expert_id:
            p=conn.execute(select(profiles).where(profiles.c.employee_id==body.expert_id)).mappings().first()
            a=find_account(p['username']) if p else None
            if not a or a['role'] not in {'SOC_L2','SOC_L3'}:raise HTTPException(409,'Cần chuyên gia L2/L3 hợp lệ.')
            if not any(x['MaNV']==body.expert_id and x['VaiTro']==a['role'] for x in assignments(conn,key)):
                write_assignment(conn,key,body.expert_id,a['role'],user)
        row['MucDoNghiemTrong']=body.severity;check_critical(conn,row)
        t=get_table('su_co');conn.execute(t.update().where(t.c.MaIncident==key).values(MucDoNghiemTrong=body.severity))
        log(conn,user,'TRIAGE',key,body.severity)
    return {'message':'Đã cập nhật mức độ.'}


def validate_transition(role, old, new, critical_ok, action_count):
    if NEXT.get(old) != new:
        raise HTTPException(409,'Chuyển trạng thái không hợp lệ. Không thể mở lại sự cố đã đóng.')
    if old not in TRANSITIONS.get(role,set()):
        raise HTTPException(403,'Vai trò hiện tại không được chuyển trạng thái này.')
    if not critical_ok:
        raise HTTPException(409,'Sự cố Critical phải có nhân viên L2 hoặc L3 tham gia.')
    if new=='CLOSED' and action_count < 1:
        raise HTTPException(409,'Phải có ít nhất một hành động xử lý trước khi đóng sự cố.')


@router.post('/workspace/incidents/{key}/transition')
def transition(key: str, body: TransitionBody, user=Depends(current_user)):
    allow(user)
    with engine.begin() as conn:
        row=incident(conn,key,True); check_assigned(conn,user,key)
        own=employee(conn,user)
        aa=assignments(conn,key)
        critical_ok=row['MucDoNghiemTrong']!='CRITICAL' or any(a['VaiTro'] in {'SOC_L2','SOC_L3'} for a in aa)
        act=get_table('hanh_dong_xu_ly')
        action_count=conn.execute(select(func.count()).select_from(act).where(act.c.MaIncident==key)).scalar_one()
        validate_transition(user['role'],row['TrangThai'],body.status,critical_ok,action_count)
        if body.status=='INVESTIGATING' and not any(a['MaNV']==own for a in aa):
            write_assignment(conn,key,own,user['role'],user)
        now=datetime.utcnow(); values={'TrangThai':body.status}
        if body.status=='INVESTIGATING': values['ThoiGianXuLy']=now
        if body.status=='CLOSED': values['ThoiGianDong']=now
        mysql=conn.dialect.name=='mysql'
        if mysql: conn.execute(text('SET @soc_actor_employee=:employee, @soc_actor_username=:username, @soc_change_time=NULL'),{'employee':own,'username':user['username']})
        try:
            conn.execute(get_table('su_co').update().where(get_table('su_co').c.MaIncident==key).values(**values))
            if not mysql:
                history=get_table('lich_su_trang_thai')
                conn.execute(history.insert().values(ThoiDiemThayDoi=unique_time(conn,history,'ThoiDiemThayDoi'),TrangThaiCu=row['TrangThai'],TrangThaiMoi=body.status,MaIncident=key,MaNV=own))
        finally:
            if mysql: conn.exec_driver_sql('SET @soc_actor_employee=NULL, @soc_actor_username=NULL, @soc_change_time=NULL')
        log(conn,user,'TRANSITION',key,row['TrangThai']+' -> '+body.status)
    return {'message':'Đã chuyển trạng thái và ghi lịch sử.'}


class AssignmentBody(BaseModel):
    employee_id: str
    role: str


@router.post('/workspace/incidents/{key}/assign')
def assign(key: str, body: AssignmentBody, user=Depends(current_user)):
    allow(user, {'SOC_MANAGER'})
    with engine.begin() as conn:
        row=incident(conn,key,True)
        if row['TrangThai']=='CLOSED': raise HTTPException(409,'Không phân công sự cố đã đóng.')
        write_assignment(conn,key,body.employee_id,body.role,user)
        check_critical(conn,row)
    return {'message':'Đã phân công nhân viên.'}


@router.post('/workspace/incidents/{key}/escalate')
def escalate(key: str, body: AssignmentBody, user=Depends(current_user)):
    target={'SOC_L1':'SOC_L2','SOC_L2':'SOC_L3','SOC_L3':'INCIDENT_RESPONDER'}
    allow(user,set(target))
    if target[user['role']]!=body.role: raise HTTPException(403,'Sai vai trò chuyển cấp.')
    with engine.begin() as conn:
        row=incident(conn,key,True);check_assigned(conn,user,key)
        if row['TrangThai']=='CLOSED': raise HTTPException(409,'Không chuyển cấp sự cố đã đóng.')
        if user['role'] in {'SOC_L1','SOC_L2'} and row['TrangThai']!='INVESTIGATING': raise HTTPException(409,'Cần nhận xử lý và chuyển sang INVESTIGATING trước khi chuyển cấp.')
        if user['role']=='SOC_L3' and row['TrangThai']!='CONTAINED': raise HTTPException(409,'Cần CONTAINED trước khi giao ứng phó.')
        write_assignment(conn,key,body.employee_id,body.role,user)
        log(conn,user,'ESCALATE',key,body.role)
    return {'message':'Đã chuyển cấp và phân công.'}


class ActionBody(BaseModel):
    action: str
    result: str = Field(min_length=1,max_length=255)
    minutes: int = Field(ge=1,le=100000)


@router.post('/workspace/incidents/{key}/actions')
def add_action(key: str, body: ActionBody, user=Depends(current_user)):
    allow(user, {'SOC_MANAGER','SOC_L2','SOC_L3','INCIDENT_RESPONDER'})
    allowed=ACTIONS if user['role'] in {'SOC_MANAGER','INCIDENT_RESPONDER'} else ['Collect Evidence','Scan Malware']
    if body.action not in allowed: raise HTTPException(403,'Vai trò không được ghi hành động này.')
    with engine.begin() as conn:
        row=incident(conn,key,True); check_assigned(conn,user,key)
        if row['TrangThai'] in {'NEW','CLOSED'}: raise HTTPException(409,'Chỉ ghi hành động cho sự cố đang xử lý.')
        if user['role']=='INCIDENT_RESPONDER' and row['TrangThai'] not in {'CONTAINED','REMEDIATING'}: raise HTTPException(409,'Sự cố chưa đến giai đoạn ứng phó.')
        t=get_table('hanh_dong_xu_ly'); now=unique_time(conn,t,'ThoiGianThucHien')
        conn.execute(t.insert().values(ThoiGianThucHien=now,ThoiGian=now,HanhDong=body.action,KetQua=body.result,
            MaIncident=key,MaNV=employee(conn,user),ThoiLuongPhut=body.minutes))
        log(conn,user,'ACTION',key,body.action)
    return {'message':'Đã ghi hành động xử lý.'}


class AnalysisBody(BaseModel):
    description: str = Field(min_length=1)
    risk_score: int = Field(ge=0,le=100)


@router.put('/workspace/incidents/{key}/analysis')
def analysis(key: str, body: AnalysisBody, user=Depends(current_user)):
    allow(user, {'SOC_MANAGER','SOC_L3'})
    with engine.begin() as conn:
        row=incident(conn,key,True)
        if row['TrangThai']=='CLOSED': raise HTTPException(409,'Sự cố đã đóng, không thể sửa phân tích.')
        t=get_table('su_co');conn.execute(t.update().where(t.c.MaIncident==key).values(MoTa=body.description,DiemRuiRo=body.risk_score))
        log(conn,user,'ANALYSIS',key)
    return {'message':'Đã lưu phân tích.'}


class LinkBody(BaseModel):
    value: str
    kind: str
    ioc_type: str | None = None


@router.post('/workspace/incidents/{key}/links')
def link(key: str, body: LinkBody, user=Depends(current_user)):
    allow(user, {'SOC_MANAGER','SOC_L2','SOC_L3','THREAT_HUNTER'})
    if body.kind not in {'ioc','technique'}: raise HTTPException(422,'Loại liên kết không hợp lệ.')
    with engine.begin() as conn:
        row=incident(conn,key,True);check_assigned(conn,user,key)
        if row['TrangThai']=='CLOSED': raise HTTPException(409,'Không thay đổi liên kết của sự cố đã đóng.')
        table,column,ref,refcol=('incident_ioc','GiaTriIOC','ioc','GiaTriIOC') if body.kind=='ioc' else ('su_co_ky_thuat_mitre','MaKyThuat','ky_thuat_mitre','MaKyThuat')
        t=get_table(table); r=get_table(ref)
        condition=r.c[refcol]==body.value
        values={'MaIncident':key,column:body.value}
        existing_condition=and_(t.c.MaIncident==key,t.c[column]==body.value)
        if body.kind=='ioc':
            if not body.ioc_type: raise HTTPException(422,'Hãy chọn cả loại và giá trị IOC.')
            condition=and_(condition,r.c.LoaiIOC==body.ioc_type)
            existing_condition=and_(existing_condition,t.c.LoaiIOC==body.ioc_type)
            values['LoaiIOC']=body.ioc_type
        if not conn.execute(select(r).where(condition)).first():raise HTTPException(404,'Không tìm thấy IOC/Technique.')
        if conn.execute(select(t).where(existing_condition)).first():raise HTTPException(409,'Liên kết đã tồn tại.')
        conn.execute(t.insert().values(**values));log(conn,user,'LINK',key,body.kind+': '+str(body.ioc_type or '')+': '+body.value)
    return {'message':'Đã gắn liên kết.'}


class IOCBody(BaseModel):
    type: str
    value: str = Field(min_length=1,max_length=100)
    source: str = Field(min_length=1,max_length=100)
    confidence: str


@router.post('/workspace/iocs',status_code=201)
def create_ioc(body: IOCBody, user=Depends(current_user)):
    allow(user, {'SOC_MANAGER','SOC_L2','SOC_L3','THREAT_HUNTER'})
    if body.type not in {'IP','Domain','URL','Hash','Email'} or body.confidence not in {'HIGH','MEDIUM','LOW'}:
        raise HTTPException(422,'Loại IOC hoặc mức tin cậy không hợp lệ.')
    value=body.value.strip()
    if not value: raise HTTPException(422,'Giá trị IOC không được trống.')
    try:
        with engine.begin() as conn:
            t=get_table('ioc')
            if conn.execute(select(t).where(func.lower(t.c.GiaTriIOC)==value.lower(),func.lower(t.c.LoaiIOC)==body.type.lower())).first():
                raise HTTPException(409,'Cặp loại và giá trị IOC đã tồn tại. Hãy dùng IOC có sẵn để liên kết.')
            conn.execute(t.insert().values(GiaTriIOC=value,LoaiIOC=body.type,Nguon=body.source,MucDoTinCay=body.confidence,ThoiGianPhatHien=datetime.utcnow()))
            log(conn,user,'CREATE_IOC',value)
    except IntegrityError: raise HTTPException(409,'IOC đã tồn tại.')
    return {'message':'Đã tạo IOC.'}


@router.get('/workspace/intelligence')
def intelligence(kind: str='', value: str='', source: str='', confidence: str='', technique: str='', user=Depends(current_user)):
    allow(user)
    with engine.connect() as conn:
        iocs=[r for r in rows(conn,'ioc',user) if (not kind or r['LoaiIOC']==kind) and value.lower() in r['GiaTriIOC'].lower() and source.lower() in r['Nguon'].lower() and (not confidence or r['MucDoTinCay']==confidence)]
        tech=[r for r in rows(conn,'ky_thuat_mitre',user) if technique.lower() in (r['MaKyThuat']+' '+r['TenKyThuat']).lower()]
        if 'read' not in permissions(user['role'],'ky_thuat_mitre'): tech=[]
        links=rows(conn,'incident_ioc',user)
        for r in iocs:r['incidents']=sorted({x['MaIncident'] for x in links if x['GiaTriIOC']==r['GiaTriIOC'] and x['LoaiIOC']==r['LoaiIOC']})
        return {'iocs':iocs,'techniques':tech}


def month_value(month):
    month=month or datetime.utcnow().strftime('%Y-%m')
    if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',month):raise HTTPException(422,'Tháng cần có định dạng YYYY-MM.')
    return month


def employee_month(conn, employee_id, month, incidents, aa):
    assigned={a['MaIncident'] for a in aa if a['MaNV']==employee_id}
    participated=Counter(s['ThoiGianPhatHien'].strftime('%Y-%m') for s in incidents if s['MaIncident'] in assigned)
    closed=[s for s in incidents if s['MaIncident'] in assigned and s['TrangThai']=='CLOSED' and s['ThoiGianDong']]
    monthly=Counter(s['ThoiGianDong'].strftime('%Y-%m') for s in closed)
    selected=[s for s in closed if s['ThoiGianDong'].strftime('%Y-%m')==month]
    policy={r['severity']:r['amount'] for r in conn.execute(select(bonus_policy)).mappings()}
    salary=conn.execute(select(payroll.c.base_salary).where(payroll.c.employee_id==employee_id,payroll.c.month==month)).scalar()
    bonus=sum((policy.get(s['MucDoNghiemTrong'],Decimal(0)) for s in selected if not sla(s)['violated']),Decimal(0)) if len(policy)==4 else None
    average=sum((s['ThoiGianDong']-s['ThoiGianPhatHien']).total_seconds()/60 for s in selected)/len(selected) if selected else None
    return {'employee_id':employee_id,'month':month,'monthly':[{'month':m,'count':c} for m,c in sorted(monthly.items())],
            'participation_monthly':[{'month':m,'count':c} for m,c in sorted(participated.items())], 'participated_count':participated[month],
            'closed_count':len(selected),'average_minutes':round(average,1) if average is not None else None,
            'base_salary':salary,'bonus':bonus,'total':salary+bonus if salary is not None and bonus is not None else None,
            'note':'Thưởng cho sự cố CLOSED đúng SLA; mỗi nhân viên tham gia nhận mức theo chính sách đã lưu. Chưa có lương/chính sách thì hiển thị chưa cấu hình.'}


@router.get('/workspace/personal')
def personal(month: str | None=None, user=Depends(current_user)):
    allow(user)
    with engine.connect() as conn:
        own=employee(conn,user)
        return employee_month(conn,own,month_value(month),rows(conn,'su_co'),rows(conn,'su_co_nhan_vien_soc'))


class SalaryBody(BaseModel):
    employee_id: str
    month: str
    base_salary: Decimal = Field(ge=0,max_digits=15,decimal_places=2)


@router.put('/workspace/compensation')
def compensation(body: SalaryBody, user=Depends(current_user)):
    allow(user, {'SOC_MANAGER'})
    month=month_value(body.month)
    with engine.begin() as conn:
        t=get_table('nhan_vien_soc')
        if not conn.execute(select(t).where(t.c.MaNV==body.employee_id)).first():raise HTTPException(404,'Không tìm thấy nhân viên.')
        conn.execute(payroll.delete().where(payroll.c.employee_id==body.employee_id,payroll.c.month==month))
        conn.execute(payroll.insert().values(employee_id=body.employee_id,month=month,base_salary=body.base_salary))
        log(conn,user,'SALARY',body.employee_id,month)
    return {'message':'Đã lưu lương tháng.'}


@router.get('/workspace/audit')
def activity(user=Depends(current_user)):
    allow(user,{'ADMIN'})
    with engine.connect() as conn:
        result = [dict(r) for r in conn.execute(select(audit).order_by(audit.c.id.desc()).limit(300)).mappings()]
    with account_connection() as conn:
        result += [{**dict(r), 'created_at':datetime.fromisoformat(r['created_at'])} for r in conn.execute('SELECT * FROM account_events ORDER BY id DESC LIMIT 300')]
    return sorted(result,key=lambda r:r['created_at'],reverse=True)[:300]


@router.get('/workspace/reports')
def reports(month: str | None=None, user=Depends(current_user)):
    allow(user)
    month=month_value(month)
    with engine.connect() as conn:
        inc=rows(conn,'su_co',user); aa=rows(conn,'su_co_nhan_vien_soc',user); alerts=rows(conn,'canh_bao',user)
        assets=rows(conn,'tai_san',user); al=rows(conn,'canh_bao_tai_san',user); ai=rows(conn,'tai_san_incident',user)
        ti=rows(conn,'su_co_ky_thuat_mitre',user); ii=rows(conn,'incident_ioc',user)
        by_id={s['MaIncident']:s for s in inc}; by_asset={s['MaTS']:s for s in assets}
        selected_alerts={a['MaCanhBao'] for a in alerts if a['ThoiGianPhatHien'].strftime('%Y-%m')==month}
        hot=Counter(a['MaTS'] for a in al if a['MaCanhBao'] in selected_alerts)
        all_hot=Counter(a['MaTS'] for a in al)
        closed_assets={a['MaTS'] for a in ai if by_id[a['MaIncident']]['TrangThai']=='CLOSED'}
        hot_rows=[{**by_asset[k],'alert_count':v} for k,v in hot.most_common(10)]
        never=[{**by_asset[k],'alert_count':v} for k,v in all_hot.most_common() if v>=5 and k not in closed_assets]
        technique_counts=Counter(x['MaKyThuat'] for x in ti)
        ioc_counts=Counter((x['LoaiIOC'],x['GiaTriIOC']) for x in ii)
        same=[]
        for kind,value in ioc_counts:
            keys=sorted({x['MaIncident'] for x in ii if x['GiaTriIOC']==value and x['LoaiIOC']==kind})
            if len(keys)>1:same.append({'ioc':value,'type':kind,'incidents':keys,'count':len(keys)})
        result={'month':month,'top_assets':hot_rows,'never_closed_assets':never,
                'top_techniques':[{**r,'incident_count':technique_counts[r['MaKyThuat']]} for r in sorted(rows(conn,'ky_thuat_mitre',user),key=lambda r:-technique_counts[r['MaKyThuat']])[:10]],
                'top_iocs':[{**r,'incident_count':ioc_counts[(r['LoaiIOC'],r['GiaTriIOC'])]} for r in sorted(rows(conn,'ioc',user),key=lambda r:-ioc_counts[(r['LoaiIOC'],r['GiaTriIOC'])])[:10]],
                'same_ioc':sorted(same,key=lambda r:-r['count'])}
        if user['role'] in {'SOC_L1','INCIDENT_RESPONDER'}:
            result={k:v for k,v in result.items() if k in {'month','top_assets'}}
        if user['role']=='SOC_MANAGER':
            if conn.dialect.name=='mysql':
                result['critical_new_violations']=[dict(r) for r in conn.exec_driver_sql('SELECT * FROM soc_critical_new_violations').mappings()]
            assigned={a['MaIncident'] for a in aa}
            org_pairs={(by_asset[a['MaTS']]['MaTC'],a['MaIncident']) for a in ai}
            risk=[]
            for org in rows(conn,'to_chuc'):
                counts=Counter(by_id[key]['MucDoNghiemTrong'] for oid,key in org_pairs if oid==org['MaTC'])
                risk.append({**org,'critical':counts['CRITICAL'],'high':counts['HIGH'],'risk_score':sum(counts[s]*w for s,w in {'CRITICAL':10,'HIGH':5,'MEDIUM':2,'LOW':1}.items())})
            staff_report=[]
            for nv in rows(conn,'nhan_vien_soc'):
                count=len({a['MaIncident'] for a in aa if a['MaNV']==nv['MaNV'] and by_id[a['MaIncident']]['TrangThai'] in {'INVESTIGATING','CONTAINED','REMEDIATING'}})
                p=employee_month(conn,nv['MaNV'],month,inc,aa)
                staff_report.append({**nv,**p,'active_count':count,'overloaded':count>=settings.overload_threshold})
            result.update({'by_status':dict(Counter(s['TrangThai'] for s in inc)), 'by_severity':dict(Counter(s['MucDoNghiemTrong'] for s in inc)),
                'sla_violated':sum(sla(s)['violated'] for s in inc), 'unassigned_count':sum(s['MaIncident'] not in assigned for s in inc),
                'overdue':[enrich(conn,s) for s in inc if s['TrangThai'] in {'INVESTIGATING','CONTAINED','REMEDIATING'} and sla(s)['violated']],
                'organizations':sorted(risk,key=lambda r:-r['risk_score']), 'top_organizations':sorted(risk,key=lambda r:-r['risk_score'])[:10],
                'critical_high_organizations':sorted(risk,key=lambda r:-(r['critical']+r['high']))[:10],
                'employees':staff_report,'overload_threshold':settings.overload_threshold})
        return result
