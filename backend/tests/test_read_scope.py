"""Access tests with real SQL predicates and HTTP requests, no MySQL writes."""
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, DateTime
from sqlalchemy.pool import StaticPool
from app import accounts, main, workspaces
from app.workspace_schema import meta, profiles
from app.security import current_user


@pytest.fixture
def scoped_client(tmp_path, monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    m = MetaData()
    specs = {
        'su_co': ('MaIncident', 'ThoiGianBatDau ThoiGianPhatHien ThoiGianXuLy ThoiGianDong MucDoNghiemTrong TrangThai MoTa DiemRuiRo'),
        'nhan_vien_soc': ('MaNV', 'HoTen'), 'to_chuc': ('MaTC', 'TenTC'),
        'tai_san': ('MaTS', 'Ten MaTC'), 'canh_bao': ('MaCanhBao', 'MaIncident ThoiGianPhatHien'),
        'ioc': ('LoaiIOC GiaTriIOC', 'Nguon MucDoTinCay'),
        'ky_thuat_mitre': ('MaKyThuat', 'TenKyThuat'),
        'canh_bao_tai_san': ('MaCanhBao MaTS', ''),
        'tai_san_incident': ('MaTS MaIncident', ''),
        'incident_ioc': ('MaIncident LoaiIOC GiaTriIOC', ''),
        'su_co_ky_thuat_mitre': ('MaIncident MaKyThuat', ''),
        'su_co_nhan_vien_soc': ('MaIncident MaNV VaiTro', 'ViTri ThoiDiemThamGia'),
        'hanh_dong_xu_ly': ('MaHanhDong', 'MaIncident MaNV ThoiGianThucHien HanhDong KetQua'),
        'lich_su_trang_thai': ('MaLichSu', 'MaIncident MaNV ThoiDiemThayDoi TrangThaiCu TrangThaiMoi'),
    }
    tables = {}
    for name, (pk, rest) in specs.items():
        cols = []
        for key in (pk+' '+rest).split():
            typ = DateTime if key.startswith(('ThoiGian', 'ThoiDiem')) else Integer if key == 'DiemRuiRo' else String(100)
            cols.append(Column(key, typ, primary_key=key in pk.split()))
        tables[name] = Table(name, m, *cols)
    m.create_all(engine); meta.create_all(engine)
    monkeypatch.setattr(accounts, 'ACCOUNT_DB', tmp_path/'accounts.sqlite3')
    for mod in (main, workspaces):
        monkeypatch.setattr(mod, 'engine', engine)
        monkeypatch.setattr(mod, 'get_table', tables.__getitem__)
    now = datetime(2026, 10, 10)
    with engine.begin() as c:
        c.execute(profiles.insert(), [{'username':'subject','employee_id':'SELF'}])
        for key, employee in [('IN','SELF'), ('OUT','OTHER')]:
            c.execute(tables['nhan_vien_soc'].insert().values(MaNV=employee,HoTen=employee))
            c.execute(tables['su_co'].insert().values(MaIncident=key,ThoiGianPhatHien=now,TrangThai='CLOSED',MucDoNghiemTrong='LOW',DiemRuiRo=0,ThoiGianDong=now))
            c.execute(tables['su_co_nhan_vien_soc'].insert().values(MaIncident=key,MaNV=employee,VaiTro='SOC_L2'))
            c.execute(tables['tai_san'].insert().values(MaTS=key,Ten=key,MaTC='ORG'))
            c.execute(tables['tai_san_incident'].insert().values(MaTS=key,MaIncident=key))
            c.execute(tables['canh_bao'].insert().values(MaCanhBao=key,MaIncident=key,ThoiGianPhatHien=now))
            c.execute(tables['canh_bao_tai_san'].insert().values(MaCanhBao=key,MaTS=key))
            c.execute(tables['ioc'].insert().values(LoaiIOC='Domain',GiaTriIOC=key,Nguon='test',MucDoTinCay='HIGH'))
            c.execute(tables['incident_ioc'].insert().values(MaIncident=key,LoaiIOC='Domain',GiaTriIOC=key))
            c.execute(tables['ky_thuat_mitre'].insert().values(MaKyThuat=key,TenKyThuat=key))
            c.execute(tables['su_co_ky_thuat_mitre'].insert().values(MaIncident=key,MaKyThuat=key))
            c.execute(tables['hanh_dong_xu_ly'].insert().values(MaHanhDong=key,MaIncident=key,MaNV=employee,ThoiGianThucHien=now,HanhDong='Action',KetQua='OK'))
            c.execute(tables['lich_su_trang_thai'].insert().values(MaLichSu=key,MaIncident=key,MaNV=employee,ThoiDiemThayDoi=now,TrangThaiCu='NEW',TrangThaiMoi='CLOSED'))
        # A shared IOC must not reveal OUT through its list of incident IDs.
        c.execute(tables['incident_ioc'].insert().values(MaIncident='OUT',LoaiIOC='Domain',GiaTriIOC='IN'))
    user = {'username':'subject','role':'SOC_L2','active':1}
    main.app.dependency_overrides[current_user] = lambda: user
    with TestClient(main.app) as client:
        yield client, user, engine, tables
    main.app.dependency_overrides.clear(); engine.dispose()


@pytest.mark.parametrize('role', ['SOC_L2','INCIDENT_RESPONDER'])
def test_incident_and_child_reads_stay_in_assignment(scoped_client, role):
    c,user,engine,tables = scoped_client; user['role']=role
    base='/api/v1'
    assert c.get(base+'/workspace/incidents/OUT').status_code == 403
    data=c.get(base+'/workspace/incidents/IN').json()
    assert data['incident']['MaIncident']=='IN'
    assert [x['MaIncident'] for x in data['actions']]==['IN']
    assert data['same_ioc_incidents']==[]
    assert {r['MaIncident'] for r in c.get(base+'/workspace/incidents').json()}=={'IN'}
    for table in ['su_co','canh_bao','tai_san','hanh_dong_xu_ly','lich_su_trang_thai']:
        assert c.get(base+f'/tables/{table}/OUT').status_code==403
        assert c.get(base+f'/tables/{table}/IN').status_code==200
        result=c.get(base+f'/tables/{table}').json()
        assert result['total']==1
        assert c.get(base+f'/tables/{table}?search=OUT').json()['total']==0
    assert c.get(base+'/tables/incident_ioc').json()['total']==1
    intel=c.get(base+'/workspace/intelligence').json()
    assert [x['GiaTriIOC'] for x in intel['iocs']]==['IN']
    assert intel['iocs'][0]['incidents']==['IN']
    assert c.get(base+'/reports/incident-summary').json()['items'][0]['MaIncident']=='IN'
    assert c.get(base+'/dashboard').json()['metrics']['su_co']==1
    # Removing the assignment revokes reads on the next request, even with the same account.
    with engine.begin() as conn:conn.execute(tables['su_co_nhan_vien_soc'].delete().where(tables['su_co_nhan_vien_soc'].c.MaNV=='SELF'))
    assert c.get(base+'/workspace/incidents/IN').status_code==403
    assert c.get(base+'/tables/su_co/IN').status_code==403


@pytest.mark.parametrize('role', ['SOC_MANAGER','SOC_L1','SOC_L3','THREAT_HUNTER'])
def test_other_business_roles_keep_broad_reads(scoped_client,role):
    c,user,_,_=scoped_client;user['role']=role
    assert c.get('/api/v1/workspace/incidents/OUT').status_code==200
    assert c.get('/api/v1/tables/su_co/OUT').status_code==200


def test_admin_and_unlinked_account(scoped_client):
    c,user,_,_=scoped_client
    user['role']='ADMIN'
    assert c.get('/api/v1/workspace/incidents/IN').status_code==403
    user.update(role='SOC_L2',username='unlinked')
    assert c.get('/api/v1/workspace/incidents/IN').status_code==403
    assert c.get('/api/v1/tables/su_co').status_code==403
