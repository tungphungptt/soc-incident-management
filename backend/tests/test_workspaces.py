from datetime import datetime, timedelta
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, Integer, Text, select
from sqlalchemy.pool import StaticPool
from app import accounts, workspaces, main
from app.workspace_schema import meta, profiles, payroll, bonus_policy
from app.security import current_user


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    m=MetaData()
    def table(name, cols):
        return Table(name,m,*[Column(key,typ,primary_key=pk) for key,typ,pk in cols])
    s=String(255)
    tables={}
    tables['su_co']=table('su_co',[(x,DateTime if x.startswith('ThoiGian') else Integer if x=='DiemRuiRo' else s,x=='MaIncident') for x in ['MaIncident','ThoiGianBatDau','ThoiGianPhatHien','ThoiGianXuLy','ThoiGianDong','MucDoNghiemTrong','TrangThai','MoTa','DiemRuiRo']])
    tables['nhan_vien_soc']=table('nhan_vien_soc',[('MaNV',s,True),('HoTen',s,False)])
    tables['su_co_nhan_vien_soc']=table('su_co_nhan_vien_soc',[(x,DateTime if x=='ThoiDiemThamGia' else s,x in {'MaIncident','MaNV','VaiTro'}) for x in ['MaIncident','MaNV','VaiTro','ViTri','ThoiDiemThamGia']])
    tables['hanh_dong_xu_ly']=table('hanh_dong_xu_ly',[(x,DateTime if x.startswith('ThoiGian') else Integer if x=='ThoiLuongPhut' else s,x=='ThoiGianThucHien') for x in ['ThoiGianThucHien','ThoiGian','HanhDong','KetQua','MaIncident','MaNV','ThoiLuongPhut']])
    tables['lich_su_trang_thai']=table('lich_su_trang_thai',[(x,DateTime if x=='ThoiDiemThayDoi' else s,x=='ThoiDiemThayDoi') for x in ['ThoiDiemThayDoi','TrangThaiCu','TrangThaiMoi','MaIncident','MaNV']])
    tables['tai_san_incident']=table('tai_san_incident',[('MaTS',s,True),('MaIncident',s,True)])
    tables['canh_bao']=table('canh_bao',[('MaCanhBao',s,True),('MaIncident',s,False)])
    tables['canh_bao_tai_san']=table('canh_bao_tai_san',[('MaCanhBao',s,True),('MaTS',s,True)])
    tables['ioc']=table('ioc',[('GiaTriIOC',s,True),('LoaiIOC',s,True),('Nguon',s,False),('ThoiGianPhatHien',DateTime,False),('MucDoTinCay',s,False)])
    tables['incident_ioc']=table('incident_ioc',[('MaIncident',s,True),('LoaiIOC',s,True),('GiaTriIOC',s,True)])
    m.create_all(engine);meta.create_all(engine)
    monkeypatch.setattr(accounts,'ACCOUNT_DB',tmp_path/'accounts.sqlite3')
    monkeypatch.setattr(workspaces,'engine',engine)
    monkeypatch.setattr(workspaces,'get_table',lambda n:tables[n])
    monkeypatch.setattr(main,'engine',engine)
    monkeypatch.setattr(main,'get_table',lambda n:tables[n])
    users={role:{'username':role.lower(),'role':role,'active':1} for role in workspaces.STAFF}
    monkeypatch.setattr(workspaces,'find_account',lambda username:next((v for v in users.values() if v['username']==username),None))
    with engine.begin() as conn:
        for role,u in users.items():
            conn.execute(profiles.insert().values(username=u['username'],employee_id=role))
            conn.execute(tables['nhan_vien_soc'].insert().values(MaNV=role,HoTen=role))
    current=dict(users['SOC_L1'])
    main.app.dependency_overrides[current_user]=lambda:current
    with TestClient(main.app) as client:
        yield client,current,engine,tables,users
    main.app.dependency_overrides.clear();engine.dispose()


@pytest.mark.parametrize('role,old,new',[
    ('SOC_L1','NEW','INVESTIGATING'),('SOC_L2','INVESTIGATING','CONTAINED'),('SOC_L3','INVESTIGATING','CONTAINED'),
    ('INCIDENT_RESPONDER','CONTAINED','REMEDIATING'),('INCIDENT_RESPONDER','REMEDIATING','CLOSED'),
    ('SOC_MANAGER','NEW','INVESTIGATING'),('SOC_MANAGER','REMEDIATING','CLOSED')])
def test_valid_transition_rules(role,old,new):
    workspaces.validate_transition(role,old,new,True,1)


@pytest.mark.parametrize('role,old,new,expert,actions',[
    ('SOC_L1','INVESTIGATING','CONTAINED',True,1),('THREAT_HUNTER','NEW','INVESTIGATING',True,1),
    ('SOC_MANAGER','CLOSED','NEW',True,1),('SOC_MANAGER','NEW','CLOSED',True,1),
    ('SOC_MANAGER','NEW','INVESTIGATING',False,1),('INCIDENT_RESPONDER','REMEDIATING','CLOSED',True,0)])
def test_invalid_transitions(role,old,new,expert,actions):
    with pytest.raises(HTTPException): workspaces.validate_transition(role,old,new,expert,actions)


def test_transactional_lifecycle_and_history(workspace):
    c,user,engine,t,users=workspace
    result=c.post('/api/v1/workspace/incidents',json={'description':'test investigation','severity':'HIGH'})
    assert result.status_code==201
    key=result.json()['id']
    assert c.post(f'/api/v1/workspace/incidents/{key}/transition',json={'status':'INVESTIGATING'}).status_code==200
    assert c.post(f'/api/v1/workspace/incidents/{key}/transition',json={'status':'CLOSED'}).status_code==409
    user.update(users['SOC_MANAGER'])
    for role in ['SOC_L2','INCIDENT_RESPONDER']:
        assert c.post(f'/api/v1/workspace/incidents/{key}/assign',json={'employee_id':role,'role':role}).status_code==200
    assert c.post(f'/api/v1/workspace/incidents/{key}/assign',json={'employee_id':'SOC_L2','role':'SOC_L2'}).status_code==409
    user.update(users['SOC_L2'])
    assert c.post(f'/api/v1/workspace/incidents/{key}/actions',json={'action':'Block IP','result':'blocked','minutes':5}).status_code==403
    assert c.post(f'/api/v1/workspace/incidents/{key}/actions',json={'action':'Collect Evidence','result':'captured','minutes':5}).status_code==200
    assert c.post(f'/api/v1/workspace/incidents/{key}/transition',json={'status':'CONTAINED'}).status_code==200
    user.update(users['INCIDENT_RESPONDER'])
    for state in ['REMEDIATING','CLOSED']:
        assert c.post(f'/api/v1/workspace/incidents/{key}/transition',json={'status':state}).status_code==200
    assert c.post(f'/api/v1/workspace/incidents/{key}/transition',json={'status':'NEW'}).status_code==409
    with engine.connect() as conn:
        history=conn.execute(select(t['lich_su_trang_thai'])).mappings().all()
        assert len(history)==4
        assert [h['TrangThaiMoi'] for h in history]==['INVESTIGATING','CONTAINED','REMEDIATING','CLOSED']
        assert history[-1]['MaNV']=='INCIDENT_RESPONDER'


def test_critical_creation_rolls_back_without_expert(workspace):
    c,user,engine,t,users=workspace
    result=c.post('/api/v1/workspace/incidents',json={'description':'critical test','severity':'CRITICAL'})
    assert result.status_code==409
    with engine.connect() as conn:
        assert not conn.execute(select(t['su_co'])).first()
        assert not conn.execute(select(t['su_co_nhan_vien_soc'])).first()
    result=c.post('/api/v1/workspace/incidents',json={'description':'critical test','severity':'CRITICAL','expert_id':'SOC_L2'})
    assert result.status_code==201


def test_crud_cannot_bypass_workflow(workspace):
    c,user,*_=workspace
    assert c.put('/api/v1/tables/su_co/any',json={'TrangThai':'CLOSED'}).status_code==409
    assert c.post('/api/v1/tables/su_co',json={}).status_code==409


def test_ioc_duplicate_and_personal_isolation(workspace):
    c,user,engine,t,users=workspace
    user.update(users['THREAT_HUNTER'])
    body={'type':'Domain','value':'test.example','source':'test','confidence':'HIGH'}
    assert c.post('/api/v1/workspace/iocs',json=body).status_code==201
    assert c.post('/api/v1/workspace/iocs',json=body).status_code==409
    month=datetime.utcnow().strftime('%Y-%m')
    with engine.begin() as conn:
        conn.execute(payroll.insert().values(employee_id='THREAT_HUNTER',month=month,base_salary=123))
        conn.execute(payroll.insert().values(employee_id='SOC_MANAGER',month=month,base_salary=999999))
    personal=c.get('/api/v1/workspace/personal?employee_id=SOC_MANAGER').json()
    assert personal['employee_id']=='THREAT_HUNTER'
    assert personal['base_salary']==123
    assert personal['total'] is None


def test_sla_closed_stops_clock():
    detected=datetime(2026,1,1)
    row={'ThoiGianPhatHien':detected,'TrangThai':'CLOSED','MucDoNghiemTrong':'CRITICAL','ThoiGianDong':detected+timedelta(minutes=30)}
    assert not workspaces.sla(row,datetime(2027,1,1))['violated']
    row['ThoiGianDong']=detected+timedelta(hours=2)
    assert workspaces.sla(row)['violated']


def test_group_alerts_and_assignment_scope(workspace):
    c,user,engine,t,users=workspace
    original=c.post('/api/v1/workspace/incidents',json={'description':'source','severity':'LOW'}).json()['id']
    with engine.begin() as conn:
        for aid in ['alert1','alert2']:
            conn.execute(t['canh_bao'].insert().values(MaCanhBao=aid,MaIncident=original))
            conn.execute(t['canh_bao_tai_san'].insert().values(MaCanhBao=aid,MaTS='asset1'))
    response=c.post('/api/v1/workspace/incidents',json={'description':'grouped','severity':'HIGH','alert_ids':['alert1','alert2']})
    assert response.status_code==201
    grouped=response.json()['id']
    with engine.connect() as conn:
        assert {r.MaIncident for r in conn.execute(select(t['canh_bao']))}=={grouped}
        assert conn.execute(select(t['tai_san_incident'])).first().MaTS=='asset1'
    user.update(users['SOC_L2'])
    assert c.get('/api/v1/workspace/incidents').json()==[]
    assert c.post('/api/v1/workspace/incidents/'+grouped+'/actions',json={'action':'Collect Evidence','result':'test','minutes':1}).status_code==403


def test_admin_cannot_delete_assigned_employee(workspace):
    c,user,engine,t,users=workspace
    c.post('/api/v1/workspace/incidents',json={'description':'preserve employee','severity':'LOW'})
    user.update({'username':'admin_test','role':'ADMIN','active':1})
    assert c.delete('/api/v1/tables/nhan_vien_soc/SOC_L1').status_code==409
    assert c.get('/api/v1/workspace/incidents').status_code==403


def test_close_requires_action_without_recording_history(workspace):
    c,user,engine,t,users=workspace
    key=c.post('/api/v1/workspace/incidents',json={'description':'cannot close','severity':'HIGH'}).json()['id']
    user.update(users['SOC_MANAGER'])
    for state in ['INVESTIGATING','CONTAINED','REMEDIATING']:
        assert c.post(f'/api/v1/workspace/incidents/{key}/transition',json={'status':state}).status_code==200
    assert c.post(f'/api/v1/workspace/incidents/{key}/transition',json={'status':'CLOSED'}).status_code==409
    with engine.connect() as conn:
        assert len(conn.execute(select(t['lich_su_trang_thai'])).all())==3
        assert conn.execute(select(t['su_co'].c.TrangThai).where(t['su_co'].c.MaIncident==key)).scalar()=='REMEDIATING'


def test_monthly_compensation_deduplicates_participant_roles(workspace):
    c,user,engine,t,users=workspace
    now=datetime.utcnow()
    month=now.strftime('%Y-%m')
    with engine.begin() as conn:
        conn.execute(t['su_co'].insert().values(MaIncident='salary-case',ThoiGianBatDau=now-timedelta(minutes=30),
            ThoiGianPhatHien=now-timedelta(minutes=30),ThoiGianXuLy=now-timedelta(minutes=25),ThoiGianDong=now,
            MucDoNghiemTrong='HIGH',TrangThai='CLOSED',MoTa='test',DiemRuiRo=20))
        for role in ['SOC_L1','SOC_L2']:
            conn.execute(t['su_co_nhan_vien_soc'].insert().values(MaIncident='salary-case',MaNV='SOC_L1',VaiTro=role,ViTri='participant',ThoiDiemThamGia=now))
        conn.execute(payroll.insert().values(employee_id='SOC_L1',month=month,base_salary=1000))
        for severity,amount in {'CRITICAL':1000000,'HIGH':500000,'MEDIUM':200000,'LOW':100000}.items():
            conn.execute(bonus_policy.insert().values(severity=severity,amount=amount))
    response=c.get('/api/v1/workspace/personal?month='+month)
    assert response.status_code==200
    result=response.json()
    assert result['closed_count']==1
    assert result['bonus']==500000 and result['total']==501000
    assert result['average_minutes']==30
    assert result['participated_count']==1


def test_ioc_identity_is_type_and_value(workspace):
    c,user,engine,t,users=workspace
    user.update(users['THREAT_HUNTER'])
    key=c.post('/api/v1/workspace/incidents',json={'description':'typed IOC','severity':'LOW'}).json()['id']
    value='shared.example'
    for kind in ['Domain','URL']:
        body={'type':kind,'value':value,'source':'test','confidence':'HIGH'}
        assert c.post('/api/v1/workspace/iocs',json=body).status_code==201
        assert c.post('/api/v1/workspace/iocs',json=body).status_code==409
        linked={'kind':'ioc','value':value,'ioc_type':kind}
        assert c.post(f'/api/v1/workspace/incidents/{key}/links',json=linked).status_code==200
        assert c.post(f'/api/v1/workspace/incidents/{key}/links',json=linked).status_code==409
    assert c.post(f'/api/v1/workspace/incidents/{key}/links',json={'kind':'ioc','value':value}).status_code==422
    with engine.connect() as conn:
        assert len(conn.execute(select(t['ioc'])).all())==2
        assert len(conn.execute(select(t['incident_ioc'])).all())==2
