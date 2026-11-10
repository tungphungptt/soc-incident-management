"""Idempotent demo business data. Inserts reserved DEMO IDs; never resets edits."""
from datetime import datetime, timedelta
from calendar import monthrange
from sqlalchemy import select, and_, text
from app.db import engine, get_table
from app.accounts import find_account
from app.workspace_schema import profiles, payroll, bonus_policy, log
from scripts.migrate_workspaces import migrate
from scripts.migrate_business_rules import migrate as migrate_rules, BONUSES

DEMO_EMPLOYEES = {
    'soc_manager': ('DMNV01','SOC_MANAGER','Demo Manager'),
    'analyst_l1': ('DMNV02','SOC_L1','Demo Analyst L1'),
    'analyst_l2': ('DMNV03','SOC_L2','Demo Analyst L2'),
    'analyst_l3': ('DMNV04','SOC_L3','Demo Analyst L3'),
    'incident_responder': ('DMNV05','INCIDENT_RESPONDER','Demo Responder'),
    'threat_hunter': ('DMNV06','THREAT_HUNTER','Demo Hunter'),
}


def insert_missing(conn, table, values):
    condition=and_(*(table.c[c.name]==values[c.name] for c in table.primary_key))
    if not conn.execute(select(table).where(condition)).first():
        conn.execute(table.insert().values(**values))
        return True
    return False


def seed_business_data():
    for username in DEMO_EMPLOYEES:
        if not find_account(username):
            raise ValueError('Run seed_demo_accounts before business data: '+username)
    migrate()
    migrate_rules()
    now=datetime.utcnow()
    first=now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    months=[first]
    for _ in range(2): months.append((months[-1]-timedelta(days=1)).replace(day=1))
    states=['NEW','INVESTIGATING','CONTAINED','REMEDIATING','CLOSED']
    severities=['CRITICAL','HIGH','MEDIUM','LOW']
    with engine.begin() as conn:
        for username,(eid,role,name) in DEMO_EMPLOYEES.items():
            insert_missing(conn,get_table('nhan_vien_soc'),{'MaNV':eid,'CMT':eid,'HoTen':name,'NgaySinh':datetime(1995,1,1).date(),
                'SoDienThoai':'09000000'+eid[-2:],'Email':username+'@soc.example','SoNamKinhNghiem':5})
            insert_missing(conn,profiles,{'username':username,'employee_id':eid})
            for month in months:
                insert_missing(conn,payroll,{'employee_id':eid,'month':month.strftime('%Y-%m'),'base_salary':15000000+int(eid[-2:])*1000000})
        for sev,amount in BONUSES.items():
            insert_missing(conn,bonus_policy,{'severity':sev,'amount':amount})
        for i in range(3):
            insert_missing(conn,get_table('to_chuc'),{'MaTC':f'DMTC{i}','TenTC':f'Demo Organization {i+1}','DiaChi':'Demo lab',
                'LinhVucHoatDong':'Demo SOC','SoLuongNhanVien':100,'MucDoQuanTrong':'CRITICAL' if i==0 else 'HIGH'})
        for i in range(8):
            insert_missing(conn,get_table('tai_san'),{'MaTS':f'DMTS{i}','Ten':f'Demo endpoint {i+1}','LoaiTaiSan':'Server',
                'DiaChiIP':f'192.0.2.{i+10}','HeDieuHanh':'Linux','ViTri':'Demo lab','MucDoQuanTrong':'HIGH','MaTC':f'DMTC{i%3}'})
        for i in range(8):
            insert_missing(conn,get_table('ioc'),{'GiaTriIOC':f'threat-{i}.example','LoaiIOC':'Domain','Nguon':'Demo threat feed',
                'ThoiGianPhatHien':now-timedelta(days=i),'MucDoTinCay':['HIGH','MEDIUM','LOW'][i%3]})
        for i in range(4):
            insert_missing(conn,get_table('ky_thuat_mitre'),{'MaKyThuat':['T1059','T1110','T1566','T1053'][i],
                'TenKyThuat':['Command and Scripting Interpreter','Brute Force','Phishing','Scheduled Task/Job'][i],
                'ChienThuat':['Execution','Credential Access','Initial Access','Persistence'][i],'MoTa':'Demo reference technique'})
        inserted=0
        for i in range(40):
            key=f'DMINC{i:03}';state=states[i%5];sev=severities[i%4]
            if i<25:
                detected=now-timedelta(minutes=15 if i%3==0 else 3000+i*30)
            else:
                detected=months[1+(i%2)]+timedelta(days=i%20,hours=9)
            detected=detected.replace(microsecond=i*1000)
            if state=='CLOSED':
                duration=30 if i%2 else 1600
                if detected+timedelta(minutes=duration)>now:
                    detected=now.replace(microsecond=i*1000)-timedelta(minutes=duration+10)
            closed=detected+timedelta(minutes=30 if i%2 else 1600) if state=='CLOSED' else None
            row={'MaIncident':key,'ThoiGianBatDau':detected-timedelta(minutes=5),'ThoiGianPhatHien':detected,
                'ThoiGianXuLy':None,'ThoiGianDong':None,
                'MucDoNghiemTrong':sev,'TrangThai':'NEW','MoTa':f'[DEMO] Investigation scenario {i+1}: suspicious authentication and endpoint activity.',
                'DiemRuiRo':{'CRITICAL':95,'HIGH':75,'MEDIUM':45,'LOW':15}[sev]}
            if sev=='CRITICAL':row.update(MaChuyenGia='DMNV03',VaiTroChuyenGia='SOC_L2')
            if not insert_missing(conn,get_table('su_co'),row): continue
            inserted+=1
            unassigned=state=='NEW' and sev!='CRITICAL' and i%2==0
            if not unassigned:
                for username,(eid,role,name) in DEMO_EMPLOYEES.items():
                    insert_missing(conn,get_table('su_co_nhan_vien_soc'),{'MaIncident':key,'MaNV':eid,'VaiTro':role,'ViTri':'Incident participant',
                        'ThoiDiemThamGia':detected+timedelta(minutes=1)})
            asset=f'DMTS{i%7}'
            insert_missing(conn,get_table('tai_san_incident'),{'MaTS':asset,'MaIncident':key})
            if state=='NEW':insert_missing(conn,get_table('tai_san_incident'),{'MaTS':'DMTS7','MaIncident':key})
            for j in range(2):
                aid=f'DMCB{i:03}{j}'
                insert_missing(conn,get_table('canh_bao'),{'MaCanhBao':aid,'LoaiCanhBao':'Suspicious login','IPNguon':f'198.51.100.{i+1}',
                    'IPDich':f'192.0.2.{i%7+10}','ThoiGianPhatHien':detected,'NguonPhatHien':'Demo sensor',
                    'MucDoNghiemTrong':sev,'NoiDung':'[DEMO] Suspicious activity requires triage','MaIncident':key})
                insert_missing(conn,get_table('canh_bao_tai_san'),{'MaCanhBao':aid,'MaTS':asset})
                if state=='NEW':insert_missing(conn,get_table('canh_bao_tai_san'),{'MaCanhBao':aid,'MaTS':'DMTS7'})
            insert_missing(conn,get_table('incident_ioc'),{'MaIncident':key,'LoaiIOC':'Domain','GiaTriIOC':f'threat-{i%8}.example'})
            insert_missing(conn,get_table('su_co_ky_thuat_mitre'),{'MaIncident':key,'MaKyThuat':['T1059','T1110','T1566','T1053'][i%4]})
            if state!='NEW':
                insert_missing(conn,get_table('hanh_dong_xu_ly'),{'ThoiGianThucHien':detected+timedelta(minutes=6),'ThoiGian':detected+timedelta(minutes=6),
                    'HanhDong':'Collect Evidence','KetQua':'[DEMO] Evidence captured','MaIncident':key,'MaNV':'DMNV03','ThoiLuongPhut':10})
            if state in {'REMEDIATING','CLOSED'}:
                insert_missing(conn,get_table('hanh_dong_xu_ly'),{'ThoiGianThucHien':detected+timedelta(minutes=16),'ThoiGian':detected+timedelta(minutes=16),
                    'HanhDong':'Isolate Host','KetQua':'[DEMO] Endpoint isolated','MaIncident':key,'MaNV':'DMNV05','ThoiLuongPhut':5})
            try:
                for j in range(states.index(state)):
                    when=closed if j==3 else detected+timedelta(minutes=4+j*5)
                    conn.execute(text('SET @soc_actor_employee=:actor,@soc_actor_username=:username,@soc_change_time=:when'),
                        {'actor':['DMNV02','DMNV03','DMNV05','DMNV05'][j],'username':'seed_demo','when':when})
                    values={'TrangThai':states[j+1]}
                    if j==0:values['ThoiGianXuLy']=detected+timedelta(minutes=3)
                    if j==3:values['ThoiGianDong']=closed
                    t=get_table('su_co');conn.execute(t.update().where(t.c.MaIncident==key).values(**values))
            finally:
                conn.exec_driver_sql('SET @soc_actor_employee=NULL,@soc_actor_username=NULL,@soc_change_time=NULL')
        log(conn,{'username':'seed_demo'},'SEED_DEMO','DEMO',f'{inserted} new incidents; demo salary and bonus policy persisted')
    print(f'Demo data: inserted {inserted} incidents (40 reserved IDs); existing incidents preserved.')
    print('Salary and bonus values are DEMO records stored in the database, not real payroll.')


if __name__=='__main__':
    seed_business_data()
