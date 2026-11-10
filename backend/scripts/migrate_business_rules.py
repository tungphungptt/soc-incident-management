"""Preserving, restartable MySQL migration. Stop the API while running DDL."""
from datetime import datetime
import json
from pathlib import Path
from sqlalchemy import inspect, text
from app.db import engine, metadata, TABLES
from scripts.sql_runner import statements

ROOT=Path(__file__).resolve().parents[2]
BONUSES={'CRITICAL':1000000,'HIGH':500000,'MEDIUM':200000,'LOW':100000}


def migrate():
    with engine.connect() as conn:
        bad=conn.execute(text("SELECT MaIncident FROM su_co s WHERE MucDoNghiemTrong='CRITICAL' AND NOT EXISTS (SELECT 1 FROM su_co_nhan_vien_soc a WHERE a.MaIncident=s.MaIncident AND a.VaiTro IN ('SOC_L2','SOC_L3'))")).scalars().all()
        closed=conn.execute(text("SELECT MaIncident FROM su_co s WHERE TrangThai='CLOSED' AND NOT EXISTS (SELECT 1 FROM hanh_dong_xu_ly a WHERE a.MaIncident=s.MaIncident)")).scalars().all()
        if bad or closed:
            raise RuntimeError(f'Existing invalid rows need explicit repair first. Critical: {bad}; CLOSED without action: {closed}')
        folder=ROOT/'backend'/'migration_backups'
        folder.mkdir(exist_ok=True)
        snapshot={name:[dict(r) for r in conn.execute(text(f'SELECT * FROM `{name}`')).mappings()] for name in TABLES+['soc_bonus_policy']}
        ddl={name:conn.exec_driver_sql(f'SHOW CREATE TABLE `{name}`').first()[1] for name in snapshot}
        backup=folder/(datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.json')
        backup.write_text(json.dumps({'ddl':ddl,'rows':snapshot},default=str,ensure_ascii=False),encoding='utf-8')
        print('Pre-migration backup:',backup)
    with engine.begin() as conn:
        inspector=inspect(conn)
        cols={c['name'] for c in inspector.get_columns('incident_ioc')}
        if 'LoaiIOC' not in cols:
            conn.exec_driver_sql('ALTER TABLE incident_ioc ADD COLUMN LoaiIOC VARCHAR(50) COLLATE utf8mb4_unicode_ci NULL')
        if inspector.get_pk_constraint('ioc')['constrained_columns']!=['LoaiIOC','GiaTriIOC']:
            conn.exec_driver_sql('UPDATE incident_ioc x JOIN ioc i ON i.GiaTriIOC=x.GiaTriIOC SET x.LoaiIOC=i.LoaiIOC WHERE x.LoaiIOC IS NULL')
            for fk in inspector.get_foreign_keys('incident_ioc'):
                if fk['referred_table']=='ioc':
                    conn.exec_driver_sql(f"ALTER TABLE incident_ioc DROP FOREIGN KEY `{fk['name']}`")
            conn.exec_driver_sql('ALTER TABLE ioc DROP PRIMARY KEY, ADD PRIMARY KEY (LoaiIOC,GiaTriIOC)')
        # Safe to resume if a previous DDL step was interrupted after changing the parent PK.
        missing=conn.exec_driver_sql('SELECT COUNT(*) FROM incident_ioc WHERE LoaiIOC IS NULL').scalar_one()
        if missing: raise RuntimeError('IOC type backfill incomplete; restore/review backup before continuing')
        inspector=inspect(conn)
        if inspector.get_pk_constraint('incident_ioc')['constrained_columns']!=['MaIncident','LoaiIOC','GiaTriIOC']:
            conn.exec_driver_sql('ALTER TABLE incident_ioc MODIFY LoaiIOC VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL, DROP PRIMARY KEY, ADD PRIMARY KEY (MaIncident,LoaiIOC,GiaTriIOC)')
        if not any(f['referred_table']=='ioc' for f in inspect(conn).get_foreign_keys('incident_ioc')):
            conn.exec_driver_sql('ALTER TABLE incident_ioc ADD CONSTRAINT fk_incident_ioc_pair FOREIGN KEY (LoaiIOC,GiaTriIOC) REFERENCES ioc(LoaiIOC,GiaTriIOC) ON UPDATE CASCADE ON DELETE CASCADE')
        cols={c['name'] for c in inspect(conn).get_columns('su_co')}
        if 'MaChuyenGia' not in cols:
            conn.exec_driver_sql('ALTER TABLE su_co ADD COLUMN MaChuyenGia VARCHAR(20) COLLATE utf8mb4_unicode_ci NULL, ADD COLUMN VaiTroChuyenGia VARCHAR(50) COLLATE utf8mb4_unicode_ci NULL')
        conn.exec_driver_sql("UPDATE su_co s JOIN (SELECT MaIncident, MIN(MaNV) AS MaNV FROM su_co_nhan_vien_soc WHERE VaiTro IN ('SOC_L2','SOC_L3') GROUP BY MaIncident) a ON a.MaIncident=s.MaIncident JOIN su_co_nhan_vien_soc b ON b.MaIncident=s.MaIncident AND b.MaNV=a.MaNV AND b.VaiTro IN ('SOC_L2','SOC_L3') SET s.MaChuyenGia=b.MaNV,s.VaiTroChuyenGia=b.VaiTro WHERE s.MucDoNghiemTrong='CRITICAL' AND s.MaChuyenGia IS NULL")
        if not any(f['constrained_columns']==['MaChuyenGia'] for f in inspect(conn).get_foreign_keys('su_co')):
            conn.exec_driver_sql('ALTER TABLE su_co ADD CONSTRAINT soc_critical_expert_employee FOREIGN KEY (MaChuyenGia) REFERENCES nhan_vien_soc(MaNV) ON UPDATE CASCADE ON DELETE RESTRICT')
        if 'DiemRuiRo' not in {c['name'] for c in inspect(conn).get_columns('to_chuc')}:
            conn.exec_driver_sql('ALTER TABLE to_chuc ADD COLUMN DiemRuiRo INTEGER NOT NULL DEFAULT 0')
        history={c['name']:c for c in inspect(conn).get_columns('lich_su_trang_thai')}
        if 'NguoiThucHien' not in history:
            conn.exec_driver_sql('ALTER TABLE lich_su_trang_thai ADD COLUMN NguoiThucHien VARCHAR(128) NULL')
        if not history['MaNV']['nullable']:
            conn.exec_driver_sql('ALTER TABLE lich_su_trang_thai MODIFY MaNV VARCHAR(20) COLLATE utf8mb4_unicode_ci NULL')
        # RESTRICT is concurrency-safe even when a DELETE races with assignment;
        # FK cascades do not invoke child triggers in MySQL.
        for table in ['su_co_nhan_vien_soc','hanh_dong_xu_ly','lich_su_trang_thai']:
            for fk in inspect(conn).get_foreign_keys(table):
                if fk['referred_table']=='nhan_vien_soc' and fk['options'].get('ondelete','RESTRICT')!='RESTRICT':
                    name=fk['name']
                    new_name=f'soc_{table}_employee_restrict'
                    conn.exec_driver_sql(f'ALTER TABLE `{table}` DROP FOREIGN KEY `{name}`, ADD CONSTRAINT `{new_name}` FOREIGN KEY (MaNV) REFERENCES nhan_vien_soc(MaNV) ON UPDATE CASCADE ON DELETE RESTRICT')
        constraints={r[0] for r in conn.exec_driver_sql("SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='su_co'")}
        if 'chk_incident_severity' not in constraints:
            conn.exec_driver_sql("ALTER TABLE su_co ADD CONSTRAINT chk_incident_severity CHECK (MucDoNghiemTrong IN ('CRITICAL','HIGH','MEDIUM','LOW'))")
        if 'chk_incident_state' not in constraints:
            conn.exec_driver_sql("ALTER TABLE su_co ADD CONSTRAINT chk_incident_state CHECK (TrangThai IN ('NEW','INVESTIGATING','CONTAINED','REMEDIATING','CLOSED'))")
        for severity,amount in BONUSES.items():
            conn.execute(text('INSERT INTO soc_bonus_policy (severity,amount) VALUES (:s,:a) ON DUPLICATE KEY UPDATE amount=:a'),{'s':severity,'a':amount})
    with engine.begin() as conn:
        for statement in statements(ROOT/'sql'/'triggers.sql'):
            conn.exec_driver_sql(statement)
        conn.exec_driver_sql('CALL soc_refresh_risk()')
        for name,old in snapshot.items():
            count=conn.exec_driver_sql(f'SELECT COUNT(*) FROM `{name}`').scalar_one()
            if name!='soc_bonus_policy' and count!=len(old):raise RuntimeError('Unexpected row-count change: '+name)
        old_types={r['GiaTriIOC']:r['LoaiIOC'] for r in snapshot['ioc']}
        expected={(r['MaIncident'],r.get('LoaiIOC') or old_types[r['GiaTriIOC']],r['GiaTriIOC']) for r in snapshot['incident_ioc']}
        actual={tuple(r) for r in conn.exec_driver_sql('SELECT MaIncident,LoaiIOC,GiaTriIOC FROM incident_ioc')}
        if expected!=actual:raise RuntimeError('IOC relationship preservation check failed')
    metadata.clear()
    print('Business rules installed; IOC references and row counts preserved; bonus policy corrected.')


if __name__=='__main__':migrate()
