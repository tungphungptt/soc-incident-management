"""Explicit idempotent migration for role workspaces (MySQL 8)."""
from sqlalchemy import inspect, text
from app.db import engine, metadata
from app.workspace_schema import meta


def migrate():
    meta.create_all(engine)
    with engine.begin() as conn:
        inspector = inspect(conn)
        for column in ('ThoiGianXuLy', 'ThoiGianDong'):
            definition = next(c for c in inspector.get_columns('su_co') if c['name'] == column)
            if not definition['nullable']:
                conn.execute(text(f'ALTER TABLE su_co MODIFY COLUMN {column} DATETIME NULL'))
        cols = {c['name'] for c in inspector.get_columns('su_co_nhan_vien_soc')}
        if 'ThoiDiemThamGia' not in cols:
            conn.execute(text('ALTER TABLE su_co_nhan_vien_soc ADD COLUMN ThoiDiemThamGia DATETIME NULL'))
        if inspector.get_pk_constraint('su_co_nhan_vien_soc')['constrained_columns'] != ['MaIncident', 'MaNV', 'VaiTro']:
            conn.execute(text('ALTER TABLE su_co_nhan_vien_soc DROP PRIMARY KEY, ADD PRIMARY KEY (MaIncident, MaNV, VaiTro)'))
        cols = {c['name'] for c in inspector.get_columns('hanh_dong_xu_ly')}
        if 'ThoiLuongPhut' not in cols:
            conn.execute(text('ALTER TABLE hanh_dong_xu_ly ADD COLUMN ThoiLuongPhut INTEGER NULL'))
        conn.execute(text('ALTER TABLE hanh_dong_xu_ly MODIFY ThoiGianThucHien DATETIME(6) NOT NULL'))
        conn.execute(text('ALTER TABLE lich_su_trang_thai MODIFY ThoiDiemThayDoi DATETIME(6) NOT NULL'))
    metadata.clear()
    print('Workspace migration complete. Existing rows and admin account preserved.')


if __name__ == '__main__':
    migrate()
