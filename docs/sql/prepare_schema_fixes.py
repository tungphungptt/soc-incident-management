"""Generate new proposals without changing the source schema or seed."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/sql'
schema=(OUT/'01_schema.sql').read_text(encoding='utf-8')
# No evidence of a structural SQL failure: retain column definitions and TODOs.
schema=re.sub(r'^DROP TABLE IF EXISTS \w+;\n','',schema,flags=re.M)
schema=schema.replace('-- Chọn database đích trước khi chạy. File này KHÔNG được tự động thực thi.',
                      '-- Chỉ dùng cho database thử mới/trống soc_schema_test; không tự thực thi.')
schema=schema.replace('-- CẢNH BÁO: DROP bên dưới xóa dữ liệu 18 bảng MySQL nếu thực thi file.',
                      '-- Bản đề xuất không có DROP; bảng đã tồn tại sẽ gây lỗi thay vì xóa dữ liệu.')
schema='-- Đề xuất đã giữ nguyên kiểu cột của 01_schema.sql vì MySQL kiểm chứng thành công.\nUSE soc_schema_test;\n'+schema
(OUT/'02_schema_proposed.sql').write_text(schema,encoding='utf-8')
seed=(ROOT/'database-data/seed_soc_incident_management.sql').read_text(encoding='utf-8')
seed=seed.replace('USE soc_incident_management;','USE soc_schema_test;')
def fix_ioc(match):
    pairs=re.findall(r"\('([^']*)', '([^']*)'\)",match.group(1))
    assert pairs
    # Only use values already present in the supplied seed; no synthetic IOC type.
    rows=[]
    for incident,value in pairs:
        assert "'" not in incident+value and '\\' not in incident+value
        rows.append("SELECT '%s' AS MaIncident, '%s' AS GiaTriIOC"%(incident,value))
    return ('INSERT INTO incident_ioc (MaIncident, LoaiIOC, GiaTriIOC)\n'
            'SELECT v.MaIncident, i.LoaiIOC, v.GiaTriIOC FROM (\n'+
            '\nUNION ALL\n'.join(rows)+'\n) v JOIN ioc i ON i.GiaTriIOC=v.GiaTriIOC;')
seed,n=re.subn(r'INSERT INTO `incident_ioc` \(`MaIncident`, `GiaTriIOC`\) VALUES\s*(.*?);',fix_ioc,seed,flags=re.S)
assert n==4
roles={'SOC Manager':'SOC_MANAGER','SOC Analyst L1':'SOC_L1','SOC Analyst L2':'SOC_L2',
       'SOC Analyst L3':'SOC_L3','Incident Responder':'INCIDENT_RESPONDER','Threat Hunter':'THREAT_HUNTER'}
def fix_roles(match):
    block=match.group(0)
    for old,new in roles.items():block=block.replace("'"+old+"'","'"+new+"'")
    return block
seed=re.sub(r'INSERT INTO `su_co_nhan_vien_soc`.*?;',fix_roles,seed,flags=re.S)
header='''-- BẢN ĐỀ XUẤT: seed lịch sử, chỉ dành cho soc_schema_test mới/trống.
-- Thứ tự: schema -> seed này -> migrate_workspaces -> migrate_business_rules.
-- Không chạy khi triggers workflow đã được cài; không tắt FOREIGN_KEY_CHECKS.
-- Chuyển tên vai trò theo ROLES trong backend, giữ nguyên người được phân công.
-- IOC lấy loại từ bảng ioc; xác nhận mỗi giá trị seed chỉ có một loại.
-- Migration business_rules backfill chuyên gia Critical từ phân công L2/L3.
-- Không tự bịa thời lượng, người thực hiện hay lương chưa có trong seed.
-- Không tạo tài khoản SQLite hoặc liên kết profile giả.
'''
(OUT/'03_seed_proposed.sql').write_text(header+seed,encoding='utf-8')
print('Created 02_schema_proposed.sql and 03_seed_proposed.sql')
