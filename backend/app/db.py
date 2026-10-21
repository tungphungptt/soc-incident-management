from sqlalchemy import create_engine, MetaData
from sqlalchemy.exc import SQLAlchemyError
from .config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True,
    connect_args={"connect_timeout": 8},
)
metadata = MetaData()

TABLES = [
    "to_chuc", "nhan_vien_soc", "tai_san", "su_co", "canh_bao", "ioc",
    "ky_thuat_mitre", "canh_bao_tai_san", "tai_san_incident",
    "incident_ioc", "su_co_ky_thuat_mitre", "su_co_nhan_vien_soc",
    "hanh_dong_xu_ly", "lich_su_trang_thai",
]

def get_table(name: str):
    if name not in TABLES:
        raise KeyError(name)
    if name not in metadata.tables:
        metadata.reflect(bind=engine, only=[name], resolve_fks=False)
    if name not in metadata.tables:
        raise RuntimeError(f"Table '{name}' was not found in the connected database.")
    return metadata.tables[name]

def db_health():
    with engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1")
    return True
