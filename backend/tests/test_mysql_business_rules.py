"""Opt-in integration tests against migrated MySQL; every test rolls back.

Run: $env:SOC_TEST_MYSQL='1'; python -m pytest tests/test_mysql_business_rules.py -v
No DDL, database reset, or deletion of existing data is performed by these tests.
"""
import os
from datetime import datetime,timedelta
from uuid import uuid4
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from app.db import engine

pytestmark=pytest.mark.skipif(os.environ.get('SOC_TEST_MYSQL')!='1',reason='Set SOC_TEST_MYSQL=1 to test migrated MySQL with rollback')


@pytest.fixture
def sql():
    with engine.connect() as conn:
        tx=conn.begin()
        before=conn.execute(text('SELECT COUNT(*) FROM su_co')).scalar_one()
        def run(statement,**params):return conn.execute(text(statement),params)
        employee='NV-RULE-'+uuid4().hex[:8]
        run("INSERT INTO nhan_vien_soc (MaNV,CMT,HoTen,NgaySinh,SoDienThoai,Email,SoNamKinhNghiem) VALUES (:id,:id,'SQL verifier','1990-01-01','0900000000',:email,5)",id=employee,email=employee+'@test.example')
        try:yield run,employee
        finally:
            conn.exec_driver_sql('SET @soc_actor_employee=NULL,@soc_actor_username=NULL,@soc_change_time=NULL')
            tx.rollback()
            assert conn.execute(text('SELECT COUNT(*) FROM su_co')).scalar_one()==before


def new_incident(run,employee,severity='LOW',detected=None):
    key='RULE-'+uuid4().hex[:10]
    now=detected or datetime.utcnow()
    run('''INSERT INTO su_co(MaIncident,ThoiGianBatDau,ThoiGianPhatHien,MucDoNghiemTrong,TrangThai,MoTa,DiemRuiRo,MaChuyenGia,VaiTroChuyenGia)
           VALUES(:id,:now,:now,:severity,'NEW','Rollback SQL verification',0,:expert,:role)''',
        id=key,now=now,severity=severity,expert=employee if severity=='CRITICAL' else None,role='SOC_L2' if severity=='CRITICAL' else None)
    return key


def rejected(run,statement,code=1644,marker=None,**params):
    with pytest.raises(DBAPIError) as error:run(statement,**params)
    assert error.value.orig.args[0]==code
    if marker:assert marker in str(error.value.orig)


def test_direct_insert_critical_without_expert_is_rejected(sql):
    run,employee=sql
    rejected(run,"INSERT INTO su_co(MaIncident,ThoiGianBatDau,ThoiGianPhatHien,MucDoNghiemTrong,TrangThai,MoTa,DiemRuiRo) VALUES('RULE-NO-EXPERT',UTC_TIMESTAMP(),UTC_TIMESTAMP(),'CRITICAL','NEW','test',0)",marker='SOC_CRITICAL')
    assert run("SELECT COUNT(*) FROM su_co WHERE MaIncident='RULE-NO-EXPERT'").scalar_one()==0


def test_critical_expert_is_atomic_and_cannot_be_removed(sql):
    run,employee=sql;key=new_incident(run,employee,'CRITICAL')
    assert run("SELECT COUNT(*) FROM su_co_nhan_vien_soc WHERE MaIncident=:id AND VaiTro='SOC_L2'",id=key).scalar_one()==1
    rejected(run,'DELETE FROM su_co_nhan_vien_soc WHERE MaIncident=:id',id=key,marker='SOC_CRITICAL')
    rejected(run,"UPDATE su_co_nhan_vien_soc SET VaiTro='SOC_L1' WHERE MaIncident=:id",id=key,marker='SOC_CRITICAL')


def test_direct_severity_upgrade_requires_expert(sql):
    run,employee=sql;key=new_incident(run,employee)
    rejected(run,"UPDATE su_co SET MucDoNghiemTrong='CRITICAL' WHERE MaIncident=:id",id=key,marker='SOC_CRITICAL')
    assert run('SELECT MucDoNghiemTrong FROM su_co WHERE MaIncident=:id',id=key).scalar_one()=='LOW'


def test_close_requires_action_reopen_and_last_action_delete_blocked(sql):
    run,employee=sql;key=new_incident(run,employee)
    for state in ['INVESTIGATING','CONTAINED','REMEDIATING']:
        run('UPDATE su_co SET TrangThai=:state WHERE MaIncident=:id',state=state,id=key)
    rejected(run,"UPDATE su_co SET TrangThai='CLOSED' WHERE MaIncident=:id",id=key,marker='SOC_ACTION')
    assert run('SELECT COUNT(*) FROM lich_su_trang_thai WHERE MaIncident=:id',id=key).scalar_one()==3
    run("INSERT INTO hanh_dong_xu_ly(ThoiGianThucHien,ThoiGian,HanhDong,KetQua,MaIncident,MaNV,ThoiLuongPhut) VALUES(UTC_TIMESTAMP(6),UTC_TIMESTAMP(6),'Collect Evidence','test',:id,:employee,1)",id=key,employee=employee)
    run("UPDATE su_co SET TrangThai='CLOSED' WHERE MaIncident=:id",id=key)
    rejected(run,"UPDATE su_co SET TrangThai='NEW' WHERE MaIncident=:id",id=key,marker='SOC_CLOSED')
    rejected(run,'DELETE FROM hanh_dong_xu_ly WHERE MaIncident=:id',id=key,marker='SOC_ACTION')


def test_duplicate_assignment_and_employee_delete_are_blocked(sql):
    run,employee=sql;key=new_incident(run,employee,'CRITICAL')
    rejected(run,"INSERT INTO su_co_nhan_vien_soc(MaIncident,MaNV,VaiTro,ViTri) VALUES(:id,:employee,'SOC_L2','duplicate')",id=key,employee=employee,code=1062)
    rejected(run,'DELETE FROM nhan_vien_soc WHERE MaNV=:employee',employee=employee,marker='SOC_EMPLOYEE')


def test_direct_update_writes_one_history_with_actor(sql):
    run,employee=sql;key=new_incident(run,employee)
    run("SET @soc_actor_employee=:employee,@soc_actor_username='sql_verifier'",employee=employee)
    run("UPDATE su_co SET TrangThai='INVESTIGATING' WHERE MaIncident=:id",id=key)
    record=run('SELECT * FROM lich_su_trang_thai WHERE MaIncident=:id',id=key).mappings().one()
    assert record['TrangThaiCu']=='NEW' and record['TrangThaiMoi']=='INVESTIGATING'
    assert record['MaNV']==employee and record['NguoiThucHien']=='sql_verifier'
    run("UPDATE su_co SET DiemRuiRo=50 WHERE MaIncident=:id",id=key)
    assert run('SELECT COUNT(*) FROM lich_su_trang_thai WHERE MaIncident=:id',id=key).scalar_one()==1


def test_risk_updates_and_deduplicates_assets(sql):
    run,employee=sql;key=new_incident(run,employee)
    org='ORG-'+uuid4().hex[:8]
    run("INSERT INTO to_chuc(MaTC,TenTC,DiaChi,LinhVucHoatDong,SoLuongNhanVien,MucDoQuanTrong) VALUES(:org,'test','test','test',1,'HIGH')",org=org)
    for i in range(2):
        asset=org+str(i)
        run("INSERT INTO tai_san(MaTS,Ten,LoaiTaiSan,DiaChiIP,HeDieuHanh,ViTri,MucDoQuanTrong,MaTC) VALUES(:asset,'test','server','192.0.2.99','Linux','test','HIGH',:org)",asset=asset,org=org)
        run('INSERT INTO tai_san_incident(MaTS,MaIncident) VALUES(:asset,:id)',asset=asset,id=key)
    assert run('SELECT DiemRuiRo FROM to_chuc WHERE MaTC=:org',org=org).scalar_one()==1
    run("UPDATE su_co SET MucDoNghiemTrong='HIGH' WHERE MaIncident=:id",id=key)
    assert run('SELECT DiemRuiRo FROM to_chuc WHERE MaTC=:org',org=org).scalar_one()==5
    run('DELETE FROM tai_san_incident WHERE MaIncident=:id',id=key)
    assert run('SELECT DiemRuiRo FROM to_chuc WHERE MaTC=:org',org=org).scalar_one()==0


def test_critical_new_one_hour_violation_view(sql):
    run,employee=sql;key=new_incident(run,employee,'CRITICAL',datetime.utcnow()-timedelta(hours=2))
    violation=run('SELECT * FROM soc_critical_new_violations WHERE MaIncident=:id',id=key).mappings().one()
    assert violation['ViPham']==1 and violation['OverdueSeconds']>=3599
    run("UPDATE su_co SET TrangThai='INVESTIGATING' WHERE MaIncident=:id",id=key)
    assert run('SELECT COUNT(*) FROM soc_critical_new_violations WHERE MaIncident=:id',id=key).scalar_one()==0


def test_ioc_composite_identity_and_foreign_key(sql):
    run,employee=sql;key=new_incident(run,employee);value=uuid4().hex+'.example'
    for kind in ['Domain','URL']:
        run("INSERT INTO ioc(LoaiIOC,GiaTriIOC,Nguon,ThoiGianPhatHien,MucDoTinCay) VALUES(:kind,:value,'test',UTC_TIMESTAMP(),'HIGH')",kind=kind,value=value)
        run('INSERT INTO incident_ioc(MaIncident,LoaiIOC,GiaTriIOC) VALUES(:id,:kind,:value)',id=key,kind=kind,value=value)
    rejected(run,"INSERT INTO ioc(LoaiIOC,GiaTriIOC,Nguon,ThoiGianPhatHien,MucDoTinCay) VALUES('Domain',:value,'test',UTC_TIMESTAMP(),'HIGH')",value=value,code=1062)
    rejected(run,"INSERT INTO incident_ioc(MaIncident,LoaiIOC,GiaTriIOC) VALUES(:id,'Hash',:value)",id=key,value=value,code=1452)
    run("DELETE FROM ioc WHERE LoaiIOC='Domain' AND GiaTriIOC=:value",value=value)
    assert run('SELECT LoaiIOC FROM incident_ioc WHERE MaIncident=:id',id=key).scalar_one()=='URL'


def test_check_rejects_invalid_severity(sql):
    run,employee=sql;key=new_incident(run,employee)
    rejected(run,"UPDATE su_co SET MucDoNghiemTrong='UNRECOGNIZED' WHERE MaIncident=:id",id=key,code=3819)


def test_critical_expert_can_be_reassigned_without_gap(sql):
    run,employee=sql;key=new_incident(run,employee,'CRITICAL')
    # The same employee may hold another incident role, but not the same role twice.
    run("INSERT INTO su_co_nhan_vien_soc(MaIncident,MaNV,VaiTro,ViTri) VALUES(:id,:employee,'SOC_L3','expert replacement')",id=key,employee=employee)
    run("UPDATE su_co SET VaiTroChuyenGia='SOC_L3' WHERE MaIncident=:id",id=key)
    run("DELETE FROM su_co_nhan_vien_soc WHERE MaIncident=:id AND VaiTro='SOC_L2'",id=key)
    rejected(run,"DELETE FROM su_co_nhan_vien_soc WHERE MaIncident=:id AND VaiTro='SOC_L3'",id=key,marker='SOC_CRITICAL')


def test_history_without_application_actor_records_sql_user(sql):
    run,employee=sql;key=new_incident(run,employee)
    run("UPDATE su_co SET TrangThai='INVESTIGATING' WHERE MaIncident=:id",id=key)
    history=run('SELECT * FROM lich_su_trang_thai WHERE MaIncident=:id',id=key).mappings().one()
    assert history['MaNV'] is None
    assert history['NguoiThucHien']==run('SELECT USER()').scalar_one()


def test_existing_bonus_policy_matches_requirement(sql):
    run,employee=sql
    actual=dict(run('SELECT severity,amount FROM soc_bonus_policy').all())
    assert actual=={'CRITICAL':1000000,'HIGH':500000,'MEDIUM':200000,'LOW':100000}
